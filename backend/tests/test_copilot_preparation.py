import json
import httpx
import pytest
from sqlalchemy import select
from app.config import settings
from app.database import session_factory
from app.models import Document, Finding, Instrument, User
from app.schemas import RecommendationResult
from app.ai import parse_response, validate_grounding
from app.grounding import criterion_key
from app.import_odk_pilot import leaf, to_assessment
from app.worker import process_one
from conftest import login
from test_workflows import fake_meta


def south(client):
    return next(a for a in client.get("/api/v1/assessments").json()["items"]
                if a["laboratory_code"] == "SUL" and a["assessment_date"] == "2026-10-01")


def test_preparation_reports_missing_key_and_preserves_all_records(client):
    login(client)
    a = south(client)
    response = client.get("/api/v1/ai/readiness/" + a["id"])
    assert response.status_code == 200
    check = response.json()
    assert check["blockers"] == ["model_key"]
    assert check["source_count"] > 0 and check["selected_count"] == 3
    assert "content" not in check["sources"][0]
    assert client.get("/api/v1/assessments").json()["total"] == 9


def test_draft_or_wrong_criterion_never_satisfies_preparation(client):
    login(client)
    a = south(client)
    with session_factory()() as db:
        for document in db.scalars(select(Document)):
            document.status = "draft"
        admin = db.scalar(select(User).where(User.role == "admin"))
        db.add(Document(organization_id=admin.organization_id, code="UNRELATED", revision=1,
            title="Unrelated source", content="An unrelated published procedure that must not cover this finding.",
            criterion_codes=["OTHER"], author_id=admin.id, status="published"))
        db.commit()
    settings().model_api_key = "test-only"
    check = client.get("/api/v1/ai/readiness/" + a["id"]).json()
    assert check["blockers"] == ["published_sources"]
    assert check["source_count"] == 0 and check["uncovered_ids"]
    assert client.post("/api/v1/ai/runs", json={"assessment_id": a["id"]}).status_code == 422


def test_sources_after_twenty_unrelated_documents_still_retrieved(client):
    login(client)
    a = south(client)
    with session_factory()() as db:
        admin = db.scalar(select(User).where(User.role == "admin"))
        for i in range(25):
            db.add(Document(organization_id=admin.organization_id, code=f"AAA{i:02}", revision=1,
                title="Irrelevant document", content="Unrelated published document with an explicit different criterion.",
                criterion_codes=["OTHER"], author_id=admin.id, status="published"))
        db.commit()
    check = client.get("/api/v1/ai/readiness/" + a["id"]).json()
    assert check["source_count"] and not check["uncovered_ids"]
    assert not any(s["code"].startswith("AAA") for s in check["sources"])


def test_foreign_finding_and_partner_cannot_read_or_run(client):
    login(client)
    a = south(client)
    with session_factory()() as db:
        fid = db.scalar(select(Finding.id).where(Finding.assessment_id != a["id"]))
    assert client.get("/api/v1/ai/readiness/" + a["id"], params={"finding_ids": fid}).status_code == 422
    settings().model_api_key = "test-only"
    assert client.post("/api/v1/ai/runs", json={"assessment_id": a["id"], "finding_ids": [fid]}).status_code == 422
    login(client, "parceiro@labquality.local")
    assert client.get("/api/v1/ai/readiness/" + a["id"]).status_code == 403


def test_more_than_five_findings_is_not_silently_truncated(client):
    login(client)
    a = south(client)
    settings().model_api_key = "test-only"
    assert client.post("/api/v1/ai/runs", json={"assessment_id": a["id"], "finding_ids": ["x"] * 6}).status_code == 422


def pack():
    return {"pack_version": "slipta-sources-v1", "provenance": {"pdf_sha256": "sample-test-hash"},
            "documents": [{"code": "SLIPTA-V3-1.1", "title": "Reference for legal identity",
                           "content": "External checklist reference prepared for independent review.",
                           "criterion_codes": ["1.1", "p2_s1_1_1"]}]}


def test_pack_preview_idempotence_and_independent_review(client):
    admin = login(client)
    before = len(client.get("/api/v1/documents").json())
    assert client.post("/api/v1/reference-packs?dry_run=true", json=pack()).json()["created"] == 1
    assert len(client.get("/api/v1/documents").json()) == before
    result = client.post("/api/v1/reference-packs", json=pack()).json()
    assert result["created"] == 1
    assert client.post("/api/v1/reference-packs", json=pack()).json()["unchanged"] == 1
    d = next(d for d in client.get("/api/v1/documents").json() if d["id"] == result["document_ids"][0])
    assert d["status"] == "draft" and d["author_id"] == admin["id"]
    reviewed = client.post(f"/api/v1/documents/{d['id']}/transition", json={"status": "review", "version": d["version"]}).json()
    assert client.post(f"/api/v1/documents/{d['id']}/transition", json={"status": "approved", "version": reviewed["version"]}).status_code == 403


def test_completed_report_is_scoped_and_escapes_model_text(client, monkeypatch):
    login(client)
    a = south(client)
    settings().model_api_key = "test-only"
    def transport(url, **kwargs):
        assert json.loads(kwargs["json"]["input"][1]["content"])["output_language"] == "en"
        response = fake_meta(url, **kwargs)
        data = response.json()
        result = json.loads(data["output"][0]["content"][0]["text"])
        result["summary"] = "<script>unsafe()</script>"
        data["output"][0]["content"][0]["text"] = json.dumps(result)
        return httpx.Response(200, request=httpx.Request("POST", url), json=data)
    monkeypatch.setattr("app.ai.httpx.post", transport)
    queued = client.post("/api/v1/ai/runs", json={"assessment_id": a["id"], "language": "en"}).json()
    assert client.get(f"/api/v1/ai/runs/{queued['id']}/report.html").status_code == 409
    process_one()
    response = client.get(f"/api/v1/ai/runs/{queued['id']}/report.html")
    assert response.status_code == 200 and "quality-actions-v2" in response.text
    assert "<script>" not in response.text and "&lt;script&gt;" in response.text
    assert "default-src 'none'" in response.headers["content-security-policy"]
    login(client, "parceiro@labquality.local")
    assert client.get(f"/api/v1/ai/runs/{queued['id']}/report.html").status_code == 403


def test_withdrawn_source_blocks_worker_and_export(client, monkeypatch):
    login(client)
    a = south(client)
    settings().model_api_key = "test-only"
    queued = client.post("/api/v1/ai/runs", json={"assessment_id": a["id"]}).json()
    with session_factory()() as db:
        for doc in db.scalars(select(Document)):
            doc.status = "withdrawn"
        db.commit()
    monkeypatch.setattr("app.ai.httpx.post", lambda *a, **kw: pytest.fail("No network call is allowed without sources"))
    process_one()
    run = client.get("/api/v1/ai/runs/" + queued["id"]).json()
    assert run["status"] == "failed"
    assert client.get(f"/api/v1/ai/runs/{queued['id']}/report.html").status_code == 409


def test_incomplete_provider_response_rejected():
    with pytest.raises(ValueError, match="incompleta"):
        parse_response({"status": "incomplete", "output": []})
    assert criterion_key("p2_s12_12_24_calculate") == "12.24"
    assert criterion_key("C04") != criterion_key("4.1")


def test_odk_missing_and_na_answers_never_become_zero_or_full_points():
    instrument = {"form_id": "slipta", "version": "test", "items": [{
        "code": "1.1", "field": "p2_s1_1_1", "answer_fields": ["p2_s1_1_1"],
        "score_field": "p2_s1_1_1_calculate", "maximum": 2}]}
    row = {"__id": "uuid:one", "profile": {"tf_numero_laboratorio": "SUL", "df_data_auditoria_actual": "2026-10-01"},
           "section": {"p2_s1_1_1": "na", "p2_s1_1_1_calculate": 0}}
    result = to_assessment(row, instrument, 1)
    assert result.answers["1.1"].value is None and "Não aplicável" in result.answers["1.1"].comment
    row["section"]["p2_s1_1_1"] = "sim"
    del row["section"]["p2_s1_1_1_calculate"]
    assert to_assessment(row, instrument, 1).answers["1.1"].value is None
    row["section"]["p2_s1_1_1_calculate"] = 2
    assert to_assessment(row, instrument, 1).answers["1.1"].value == 2
    with pytest.raises(ValueError, match="ambíguo"):
        leaf({"a": {"field": 1}, "b": {"field": 2}}, "field")
