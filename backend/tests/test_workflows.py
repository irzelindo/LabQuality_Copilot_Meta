import csv
import io
import json
import httpx
import pytest
from sqlalchemy import select
from app.config import settings
from app.database import session_factory
from app.demo import sample_assessments
from app.models import Document, Laboratory, Organization, User
from app.schemas import RecommendationResult
from app.security import passwords
from app.ai import parse_response, validate_grounding
from app.worker import process_one
from conftest import PASSWORD, login


def test_login_csrf_and_http_only_session(client):
    assert client.get("/api/v1/dashboard").status_code == 401
    assert client.post("/api/v1/auth/login", headers={"X-LabQuality-Client": ""}, json={"email": "a", "password": "x"}).status_code == 403
    assert client.post("/api/v1/auth/login", headers={"Origin": "https://untrusted.example"}, json={"email": "a", "password": "x"}).status_code == 403
    response = client.post("/api/v1/auth/login", json={"email": "admin@labquality.local", "password": PASSWORD})
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    assert "password_hash" not in response.text
    assert client.get("/api/health").json()["status"] == "ok"


def test_expected_scores_and_critical_gap_stays_visible(client):
    login(client)
    dashboard = client.get("/api/v1/dashboard").json()
    assert dashboard["assessment_count"] == 9
    assert dashboard["network_percentage"] == 63.33
    assert [x["percentage"] for x in dashboard["series"]] == [61.67, 61.67, 63.33]
    labs = {x["code"]: x for x in dashboard["laboratories"]}
    assert labs["SUL"]["percentage"] == 80
    assert labs["SUL"]["trend"] == "improving"
    assert labs["CENTRO"]["trend"] == "declining"
    assert labs["NORTE"]["trend"] == "stable"
    assert dashboard["critical_count"] >= 1
    filtered = client.get("/api/v1/dashboard", params={"laboratory_id": labs["SUL"]["id"], "start": "2026-10-01"}).json()
    assert filtered["assessment_count"] == 1 and filtered["network_percentage"] == 80


def test_reimport_idempotency_revision_and_immutability(client):
    login(client)
    records = [r.model_dump(mode="json") for r in sample_assessments()]
    result = client.post("/api/v1/imports/assessments", json={"assessments": records})
    assert result.status_code == 200, result.text
    assert result.json()["unchanged"] == 9
    original_id = result.json()["assessment_ids"][0]
    original = client.get(f"/api/v1/assessments/{original_id}").json()
    response = client.post(f"/api/v1/assessments/{original_id}/finalize", json={"version": original["version"]})
    assert response.status_code == 200
    records[0]["answers"]["C01"]["value"] = 2
    records[0]["reason"] = "Correcção confirmada na origem."
    result = client.post("/api/v1/imports/assessments", json={"assessments": records[:1]}).json()
    assert result["revised"] == 1
    current = client.get(f"/api/v1/assessments/{result['assessment_ids'][0]}").json()
    old = client.get(f"/api/v1/assessments/{original_id}").json()
    assert current["revision"] == 2 and current["score"]["obtained"] == 10
    assert old["score"]["obtained"] == 9 and old["status"] == "finalized" and not old["current"]
    assert client.get("/api/v1/assessments").json()["total"] == 9


def test_invalid_batch_rolls_back_and_preview_writes_nothing(client):
    login(client)
    record = sample_assessments()[0].model_dump(mode="json")
    record["external_id"] = "new-draft"
    preview = client.post("/api/v1/imports/assessments?dry_run=true", json={"assessments": [record]})
    assert preview.status_code == 200 and preview.json()["created"] == 1
    assert client.get("/api/v1/assessments").json()["total"] == 9
    invalid = json.loads(json.dumps(record))
    invalid["external_id"] = "invalid"
    invalid["answers"]["C01"]["value"] = 99
    assert client.post("/api/v1/imports/assessments", json={"assessments": [record, invalid]}).status_code == 422
    assert client.get("/api/v1/assessments").json()["total"] == 9


def test_missing_values_do_not_imply_a_complete_score(client):
    login(client)
    record = sample_assessments()[0].model_dump(mode="json")
    record["external_id"] = "incomplete"
    del record["answers"]["C01"]
    imported = client.post("/api/v1/imports/assessments", json={"assessments": [record]}).json()
    detail = client.get("/api/v1/assessments/" + imported["assessment_ids"][0]).json()
    assert detail["score"]["percentage"] is None and detail["score"]["coverage"] == 90
    assert client.post(f"/api/v1/assessments/{detail['id']}/finalize", json={"version": detail["version"]}).status_code == 422


def test_scope_isolation_and_immediate_revocation(client):
    login(client)
    all_labs = client.get("/api/v1/laboratories").json()
    north = next(x for x in all_labs if x["code"] == "NORTE")
    north_assessment = client.get("/api/v1/assessments", params={"laboratory_id": north["id"]}).json()["items"][0]
    users = client.get("/api/v1/users").json()
    quality = next(x for x in users if x["role"] == "quality")
    login(client, quality["email"])
    assert client.get(f"/api/v1/assessments/{north_assessment['id']}").status_code == 404
    assert len(client.get("/api/v1/laboratories").json()) == 1
    token = client.cookies.get("lq_session")
    login(client)
    assert client.patch(f"/api/v1/users/{quality['id']}/access", json={"role": "quality", "active": True, "laboratory_ids": []}).status_code == 200
    client.cookies.clear()
    client.cookies.set("lq_session", token)
    assert client.get("/api/v1/laboratories").json() == []


def test_other_organization_never_visible_and_partner_is_aggregate_only(client):
    login(client)
    with session_factory()() as db:
        other = Organization(name="Other institution")
        db.add(other); db.flush()
        lab = Laboratory(organization_id=other.id, code="PRIVATE", name="Private lab")
        db.add(lab); db.flush()
        foreign_id = lab.id
        db.commit()
    assert client.get("/api/v1/dashboard", params={"laboratory_id": foreign_id}).status_code == 404
    login(client, "parceiro@labquality.local")
    dashboard = client.get("/api/v1/dashboard").json()
    assert "critical_findings" not in dashboard and "prolonged_actions" not in dashboard
    for path in ["assessments", "documents", "findings", "actions", "users", "ai/runs", "audit", "reports/assessments.csv"]:
        assert client.get("/api/v1/" + path).status_code == 403, path


def test_action_evidence_verification_and_optimistic_version(client):
    login(client, "qualidade@labquality.local")
    action = client.get("/api/v1/actions").json()[0]
    response = client.post(f"/api/v1/actions/{action['id']}/transition", json={"status": "in_progress", "version": action["version"]})
    assert response.status_code == 200, response.text
    active = response.json()
    assert client.post(f"/api/v1/actions/{action['id']}/transition", json={"status": "in_verification", "version": action["version"]}).status_code == 409
    assert client.post(f"/api/v1/actions/{action['id']}/transition", json={"status": "in_verification", "version": active["version"]}).status_code == 422
    file_response = client.post(f"/api/v1/actions/{action['id']}/evidence", files={"file": ("record.txt", b"Evidence from a fictional equipment check.", "text/plain")})
    assert file_response.status_code == 201, file_response.text
    evidence = file_response.json()
    assert "storage_key" not in evidence
    assert client.get(f"/api/v1/evidence/{evidence['id']}/download").content.startswith(b"Evidence")
    active = client.post(f"/api/v1/actions/{action['id']}/transition", json={"status": "in_verification", "version": active["version"]}).json()
    own_verify = client.post(f"/api/v1/actions/{action['id']}/verify", json={"result": "effective", "comment": "Eficácia confirmada.", "version": active["version"], "evidence_ids": [evidence["id"]]})
    assert own_verify.status_code == 403
    login(client, "verificador@labquality.local")
    verified = client.post(f"/api/v1/actions/{action['id']}/verify", json={"result": "effective", "comment": "Registos e eficácia verificados.", "version": active["version"], "evidence_ids": [evidence["id"]]})
    assert verified.status_code == 200 and verified.json()["status"] == "closed"
    assert len(verified.json()["verifications"]) == 1


def test_documents_require_separate_approval_and_publish_retires_old_version(client):
    login(client)
    payload = {"code": "NEW-PROC", "title": "New controlled procedure", "content": "This fictional procedure describes a reproducible check.", "criterion_codes": ["C04"]}
    document = client.post("/api/v1/documents", json=payload).json()
    document = client.post(f"/api/v1/documents/{document['id']}/transition", json={"status": "review", "version": document["version"]}).json()
    assert client.post(f"/api/v1/documents/{document['id']}/transition", json={"status": "approved", "version": document["version"]}).status_code == 403
    login(client, "verificador@labquality.local")
    approved = client.post(f"/api/v1/documents/{document['id']}/transition", json={"status": "approved", "version": document["version"]})
    assert approved.status_code == 200
    published = client.post(f"/api/v1/documents/{document['id']}/transition", json={"status": "published", "version": approved.json()["version"]})
    assert published.status_code == 200


def test_csv_upload_and_export_filters(client):
    login(client)
    row = sample_assessments()[0].model_dump(mode="json")
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["source", "external_id", "laboratory_code", "instrument_code", "instrument_version", "assessment_date", "criterion_code", "value"])
    writer.writeheader()
    for code, answer in row["answers"].items():
        writer.writerow({**{k: row[k] for k in ["source", "external_id", "laboratory_code", "instrument_code", "instrument_version", "assessment_date"]}, "criterion_code": code, "value": answer["value"]})
    response = client.post("/api/v1/imports/file", files={"file": ("assessments.csv", out.getvalue().encode(), "text/csv")})
    assert response.status_code == 200 and response.json()["revised"] == 1
    repeated = client.post("/api/v1/imports/file", files={"file": ("assessments.csv", out.getvalue().encode(), "text/csv")})
    assert repeated.status_code == 200 and repeated.json()["unchanged"] == 1
    data = client.get("/api/v1/reports/assessments.csv?start=2026-10-01").text
    assert len(list(csv.reader(io.StringIO(data)))) == 4


def fake_meta(url, **kwargs):
    assert url == "https://api.meta.ai/v1/responses"
    assert kwargs["json"]["max_output_tokens"] == 9000
    assert kwargs["json"]["reasoning"] == {"effort": "low"}
    context = json.loads(kwargs["json"]["input"][1]["content"])
    finding = next(f for f in context["findings"] if f["criterion_code"] == "C04")
    source = next(s for s in context["sources"] if "C04" in s["criterion_codes"])
    assert finding["allowed_source_ids"] == [source["id"]]
    result = {"summary": "Proposta fundamentada para revisão humana.", "insufficient_evidence": False,
              "recommendations": [{"title": "Investigar e regularizar o registo", "justification": "O achado indica um registo em falta.",
                "priority": "critical", "steps": ["Investigar a causa com a equipa.", "Rever os registos e atribuir uma verificação."],
                "completion_criterion": "Registo completo e revisão independente documentada.", "finding_ids": [finding["id"]],
                "citations": [{"source_id": source["id"], "quote": source["content"][:100]}]}]}
    return httpx.Response(200, request=httpx.Request("POST", url), json={"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(result)}]}], "usage": {"input_tokens": 100, "output_tokens": 100}})


def test_ai_is_unavailable_without_key_and_validates_real_adapter_contract(client, monkeypatch):
    login(client)
    assessments = client.get("/api/v1/assessments").json()["items"]
    assessment = next(a for a in assessments if a["laboratory_code"] == "SUL" and a["assessment_date"] == "2026-10-01")
    assert client.post("/api/v1/ai/runs", json={"assessment_id": assessment["id"]}).status_code == 503
    settings().model_api_key = "test-key-not-a-real-credential"
    monkeypatch.setattr("app.ai.httpx.post", fake_meta)
    queued = client.post("/api/v1/ai/runs", json={"assessment_id": assessment["id"]})
    assert queued.status_code == 202
    assert process_one()
    execution = client.get("/api/v1/ai/runs/" + queued.json()["id"]).json()
    assert execution["status"] == "completed", execution
    assert len(execution["result"]["recommendations"]) == 1
    assert execution["usage"]["input_tokens"] == 100
    assert len(client.get("/api/v1/actions").json()) == 1
    users = client.get("/api/v1/users").json()
    owner = next(u for u in users if u["role"] == "quality")
    payload = {"index": 0, "owner_id": owner["id"], "due_date": "2026-12-01", "title": "Proposta revista por uma pessoa", "description": "Investigar a causa e verificar o registo."}
    accepted = client.post(f"/api/v1/ai/runs/{execution['id']}/accept", json=payload)
    assert accepted.status_code == 201, accepted.text
    assert client.post(f"/api/v1/ai/runs/{execution['id']}/accept", json=payload).status_code == 409
    assert len(client.get("/api/v1/actions").json()) == 2


def test_grounding_rejects_invented_quotes():
    result = RecommendationResult.model_validate({"summary": "Example result", "insufficient_evidence": False, "recommendations": [
        {"title": "Example action", "justification": "An example justification.", "priority": "high", "steps": ["Review the record"],
         "completion_criterion": "The record was reviewed.", "finding_ids": ["f1"], "citations": [{"source_id": "d1", "quote": "This quote was invented by the model."}]}]})
    with pytest.raises(ValueError, match="citação"):
        validate_grounding(result, {"findings": [{"id": "f1", "criterion_code": "C04"}], "sources": [{"id": "d1", "criterion_codes": ["C04"], "content": "Real source text."}]})


def test_grounding_rejects_a_valid_quote_from_an_unrelated_procedure():
    result = RecommendationResult.model_validate({"summary": "Proposta a validar.", "insufficient_evidence": False,
        "recommendations": [{"title": "Verificar equipamento", "justification": "Há um achado de equipamento.",
            "priority": "high", "steps": ["Investigar a causa."],
            "completion_criterion": "Registo de verificação revisto.", "finding_ids": ["f-c04"],
            "citations": [{"source_id": "d-capa", "quote": "Investigue a causa do achado antes de escolher a acção."}]}]})
    context = {"findings": [{"id": "f-c04", "criterion_code": "C04", "allowed_source_ids": ["d-eqp"]}],
               "sources": [{"id": "d-eqp", "criterion_codes": ["C04"], "content": "Registe a verificação do equipamento."},
                           {"id": "d-capa", "criterion_codes": ["C05"],
                            "content": "Investigue a causa do achado antes de escolher a acção."}]}
    with pytest.raises(ValueError, match="não se aplica"):
        validate_grounding(result, context)


def test_incomplete_meta_response_is_reported_without_creating_proposals(client, monkeypatch):
    login(client)
    settings().model_api_key = "test-key-not-a-real-credential"
    assessment = next(a for a in client.get("/api/v1/assessments").json()["items"]
                      if a["laboratory_code"] == "SUL" and a["assessment_date"] == "2026-10-01")
    def incomplete(url, **kwargs):
        return httpx.Response(200, request=httpx.Request("POST", url), json={
            "status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
            "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"summary":"texto truncado'}]}]})
    monkeypatch.setattr("app.ai.httpx.post", incomplete)
    run_id = client.post("/api/v1/ai/runs", json={"assessment_id": assessment["id"]}).json()["id"]
    before = len(client.get("/api/v1/actions").json())
    assert process_one()
    run = client.get("/api/v1/ai/runs/" + run_id).json()
    assert run["status"] == "failed" and "limite de tokens" in run["error"]
    assert run["result"] == {} and len(client.get("/api/v1/actions").json()) == before


def test_malformed_meta_text_has_a_safe_actionable_error():
    with pytest.raises(ValueError, match="JSON incompleto ou inválido"):
        parse_response({"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": '{"summary":"unfinished'}]}]})
