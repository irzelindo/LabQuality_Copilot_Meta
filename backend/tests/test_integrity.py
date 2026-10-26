import json
import sqlite3
from pathlib import Path
import httpx
import pytest
from sqlalchemy import select
from app.backup import create_backup, restore_backup
from app.config import settings
from app.database import session_factory
from app.models import Document, Instrument, Notification, Organization, User
from app.schemas import ODKIn
from app.integrations import fetch_odk
from app.worker import process_one
from conftest import login
from test_workflows import fake_meta


def test_backup_and_restore_database_and_attachment(client, tmp_path):
    login(client)
    action = client.get("/api/v1/actions").json()[0]
    evidence = client.post(f"/api/v1/actions/{action['id']}/evidence", files={"file": ("evidence.txt", b"Original fictional evidence")}).json()
    backup = create_backup(tmp_path / "backups")
    target = restore_backup(backup, tmp_path / "restored")
    with sqlite3.connect(target / "database.sqlite") as db:
        row = db.execute("SELECT storage_key, sha256 FROM evidence WHERE id=?", [evidence["id"]]).fetchone()
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert (target / "storage" / row[0]).read_bytes() == b"Original fictional evidence"
    with pytest.raises(ValueError, match="vazio"):
        restore_backup(backup, target)
    (backup / "storage" / row[0]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="integridade"):
        restore_backup(backup, tmp_path / "other-restore")


def test_mixed_instruments_disable_network_comparison(client):
    login(client)
    instrument = client.post("/api/v1/instruments", json={"code": "OTHER", "version": "1", "name": "Different rubric", "criteria": [{"code": "X", "section": "Different section", "title": "A different criterion", "maximum": 10}]}).json()
    response = client.post("/api/v1/imports/assessments", json={"assessments": [{"source": "other", "external_id": "north-new", "laboratory_code": "NORTE", "instrument_code": "OTHER", "instrument_version": "1", "assessment_date": "2026-10-20", "answers": {"X": {"value": 10}}}]})
    assert response.status_code == 200, response.text
    dashboard = client.get("/api/v1/dashboard").json()
    assert dashboard["comparable"] is False and dashboard["network_percentage"] is None
    assert len(dashboard["instrument_versions"]) == 2


def test_ai_filters_foreign_documents_and_redacts_withdrawn_sources(client, monkeypatch):
    login(client)
    with session_factory()() as db:
        admin = db.scalar(select(User).where(User.role == "admin"))
        other = Organization(name="Foreign private organization"); db.add(other); db.flush()
        db.add(Document(organization_id=other.id, scope_key="organization", code="SECRET", revision=1,
                        title="Private reference", content="PRIVATE_FOREIGN_TEXT_SHOULD_NEVER_BE_SENT", status="published", author_id=admin.id, criterion_codes=["C04"]))
        db.commit()
    settings().model_api_key = "not-a-real-key"
    def checked_meta(url, **kwargs):
        assert "PRIVATE_FOREIGN_TEXT" not in json.dumps(kwargs["json"])
        return fake_meta(url, **kwargs)
    monkeypatch.setattr("app.ai.httpx.post", checked_meta)
    assessments = client.get("/api/v1/assessments").json()["items"]
    assessment = next(a for a in assessments if a["laboratory_code"] == "SUL" and a["assessment_date"] == "2026-10-01")
    run_id = client.post("/api/v1/ai/runs", json={"assessment_id": assessment["id"]}).json()["id"]
    assert process_one()
    run = client.get("/api/v1/ai/runs/" + run_id).json()
    assert run["status"] == "completed"
    doc = next(d for d in client.get("/api/v1/documents").json() if d["code"] == "DEMO-EQP-01")
    withdrawn = client.post(f"/api/v1/documents/{doc['id']}/transition", json={"status": "withdrawn", "version": doc["version"], "comment": "Fonte retirada para revisão."})
    assert withdrawn.status_code == 200
    redacted = client.get("/api/v1/ai/runs/" + run_id).json()
    assert redacted["status"] == "sources_changed" and redacted["result"] == {} and redacted["sources"] == []


def test_revoked_actor_cannot_execute_queued_analysis(client, monkeypatch):
    quality = login(client, "qualidade@labquality.local")
    settings().model_api_key = "not-a-real-key"
    assessment = client.get("/api/v1/assessments").json()["items"][0]
    run_id = client.post("/api/v1/ai/runs", json={"assessment_id": assessment["id"]}).json()["id"]
    def forbidden_call(*args, **kwargs):
        pytest.fail("An external call was attempted after access revocation")
    monkeypatch.setattr("app.ai.httpx.post", forbidden_call)
    login(client)
    assert client.patch(f"/api/v1/users/{quality['id']}/access", json={"role": "quality", "active": False, "laboratory_ids": []}).status_code == 200
    assert process_one()
    assert client.get("/api/v1/ai/runs/" + run_id).json()["status"] == "failed"


def test_partner_role_change_removes_private_notifications(client):
    quality = login(client, "qualidade@labquality.local")
    assert client.get("/api/v1/notifications").json()
    token = client.cookies.get("lq_session")
    login(client)
    client.patch(f"/api/v1/users/{quality['id']}/access", json={"role": "partner", "active": True, "laboratory_ids": []})
    client.cookies.clear(); client.cookies.set("lq_session", token)
    assert client.get("/api/v1/notifications").json() == []


def test_odk_nested_field_mapping_preserves_explicit_identity(monkeypatch):
    settings().odk_url = "https://odk.example"
    settings().odk_email = "test@example.invalid"
    settings().odk_password = "not-real"
    class MockClient:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, url):
            return httpx.Response(200, request=httpx.Request("GET", url), json={"value": [{"stable": "root-submission", "meta": {"revision": "2"}, "site": {"code": "SUL"}, "date": "2026-10-01", "scores": {"C01": 2}}]})
    monkeypatch.setattr("app.integrations.httpx.Client", MockClient)
    records = fetch_odk(ODKIn(project_id=1, form_id="demo", stable_id_field="stable", laboratory_code_field="site.code",
        assessment_date_field="date", revision_field="meta.revision", instrument_code="DEMO-QMS", instrument_version="1.0", criterion_fields={"C01": "scores.C01"}))
    assert records[0].external_id == "root-submission" and records[0].source_revision == "2"
    assert records[0].answers["C01"].value == 2
