import csv
import io

from conftest import login


def test_applicable_scoring_excludes_justified_na_and_keeps_revisions(client):
    login(client)
    instrument = client.post("/api/v1/instruments", json={
        "code": "CHECK-TEST", "version": "1", "name": "Checklist de teste",
        "scoring_rule": "sum_applicable_v1",
        "criteria": [
            {"code": "A1", "section": "Documentos", "title": "Controlo documental", "maximum": 2},
            {"code": "A2", "section": "Documentos", "title": "Registo aplicável", "maximum": 3},
            {"code": "B1", "section": "Processos", "title": "Verificação do processo", "maximum": 2},
        ],
    })
    assert instrument.status_code == 201, instrument.text
    record = {
        "source": "unit", "external_id": "with-na", "laboratory_code": "SUL",
        "instrument_code": "CHECK-TEST", "instrument_version": "1", "assessment_date": "2026-10-26",
        "answers": {"A1": {"value": 2}, "A2": {"not_applicable": True, "comment": "Serviço fora do âmbito."},
                    "B1": {"value": 1}},
    }
    result = client.post("/api/v1/imports/assessments", json={"assessments": [record]})
    assert result.status_code == 200, result.text
    original_id = result.json()["assessment_ids"][0]
    detail = client.get("/api/v1/assessments/" + original_id).json()
    score = detail["score"]
    assert (score["obtained"], score["maximum"], score["full_maximum"]) == (3, 4, 7)
    assert score["not_applicable"] == 1 and score["percentage"] == 75 and score["coverage"] == 100
    assert score["sections"]["Documentos"]["percentage"] == 100
    assert score["sections"]["Documentos"]["maximum"] == 2
    assert score["sections"]["Processos"]["percentage"] == 50
    assert {finding["criterion_code"] for finding in detail["findings"]} == {"B1"}
    repeated = client.post("/api/v1/imports/assessments", json={"assessments": [record]}).json()
    assert repeated["unchanged"] == 1 and repeated["assessment_ids"] == [original_id]
    assert client.post(f"/api/v1/assessments/{original_id}/finalize", json={"version": detail["version"]}).status_code == 200
    record["answers"]["A2"] = {"value": 3}
    record["reason"] = "Revisão documentada da aplicabilidade."
    revised = client.post("/api/v1/imports/assessments", json={"assessments": [record]})
    assert revised.status_code == 200 and revised.json()["revised"] == 1
    current = client.get("/api/v1/assessments/" + revised.json()["assessment_ids"][0]).json()
    assert (current["score"]["obtained"], current["score"]["maximum"]) == (6, 7)
    assert current["score"]["not_applicable"] == 0
    assert client.get("/api/v1/assessments/" + original_id).json()["score"]["percentage"] == 75


def test_na_requires_justification_and_applicable_instrument(client):
    login(client)
    existing = client.get("/api/v1/assessments").json()["items"][0]
    assert "not_applicable" not in client.get("/api/v1/assessments/" + existing["id"]).json()["answers"]["C01"]
    base = {"source": "unit", "external_id": "bad-na", "laboratory_code": "SUL",
            "instrument_code": "DEMO-QMS", "instrument_version": "1.0", "assessment_date": "2026-10-26",
            "answers": {"C01": {"not_applicable": True, "comment": "Não aplicável."}}}
    assert client.post("/api/v1/imports/assessments", json={"assessments": [base]}).status_code == 422
    base["answers"]["C01"]["comment"] = ""
    assert client.post("/api/v1/imports/assessments", json={"assessments": [base]}).status_code == 422
    base["answers"]["C01"] = {"value": 0, "not_applicable": True, "comment": "Não aplicável."}
    assert client.post("/api/v1/imports/assessments", json={"assessments": [base]}).status_code == 422


def test_tabular_na_and_zero_applicable_denominator(client):
    login(client)
    created = client.post("/api/v1/instruments", json={
        "code": "NA-TEST", "version": "1", "name": "Applicability test", "scoring_rule": "sum_applicable_v1",
        "criteria": [{"code": "N1", "section": "S", "title": "Item one", "maximum": 2},
                     {"code": "N2", "section": "S", "title": "Item two", "maximum": 3}],
    })
    assert created.status_code == 201
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["source", "external_id", "laboratory_code", "instrument_code",
                                             "instrument_version", "assessment_date", "criterion_code", "value", "comment"])
    writer.writeheader()
    meta = {"source": "csv", "external_id": "all-na", "laboratory_code": "SUL", "instrument_code": "NA-TEST",
            "instrument_version": "1", "assessment_date": "2026-10-26"}
    writer.writerow({**meta, "criterion_code": "N1", "value": "NA", "comment": "Não se aplica ao laboratório."})
    writer.writerow({**meta, "criterion_code": "N2", "value": "N/A", "comment": "Serviço não oferecido."})
    upload = lambda: client.post("/api/v1/imports/file", files={"file": ("na.csv", out.getvalue().encode(), "text/csv")})
    result = upload()
    assert result.status_code == 200, result.text
    detail = client.get("/api/v1/assessments/" + result.json()["assessment_ids"][0]).json()
    assert detail["score"]["full_maximum"] == 5
    assert detail["score"]["maximum"] == 0 and detail["score"]["not_applicable"] == 2
    assert detail["score"]["percentage"] is None and not detail["score"]["complete"]
    assert detail["score"]["sections"]["S"]["percentage"] is None
    assert client.post(f"/api/v1/assessments/{detail['id']}/finalize", json={"version": detail["version"]}).status_code == 422
    assert upload().json()["unchanged"] == 1
