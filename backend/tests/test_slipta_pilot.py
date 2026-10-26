import httpx
import pytest
from sqlalchemy import select
from pathlib import Path

from app.ai import build_context
from app.config import settings
from app.database import session_factory
from app.demo import PILOT, DEMO_NAME, pilot_assessments, refresh_demo
from app.integrations import fetch_odk
from app.models import Assessment, AssessmentRoot, Instrument, Job, Organization, User
from app.schemas import ODKIn
from app.services import import_assessments, score
from app.worker import schedule_odk, process_one
from conftest import PASSWORD, login


def pilot_request():
    return ODKIn(project_id=15, form_id=PILOT["form_id"], stable_id_field="ignored",
        laboratory_code_field="ignored", assessment_date_field="ignored",
        instrument_code=PILOT["instrument_code"], instrument_version=PILOT["instrument_version"])


def set_nested(row, path, value):
    parts = path.split(".")
    for part in parts[:-1]:
        row = row.setdefault(part, {})
    row[parts[-1]] = value


def odk_row():
    row = {"__id": "uuid:pilot-1", "__system": {"updatedAt": "2026-10-20T08:00:00Z"}}
    set_nested(row, PILOT["laboratory_code_field"], "SUL")
    set_nested(row, PILOT["assessment_date_field"], "2026-10-20")
    for criterion in PILOT["criteria"]:
        set_nested(row, criterion["odk"]["score"], criterion["maximum"])
        for field in criterion["odk"]["na"]:
            set_nested(row, field, "sim")
    return row


def test_refresh_replaces_only_demo_and_preserves_nine_moments(client):
    with session_factory()() as db:
        other = Organization(name="Instituição real")
        db.add(other)
        db.commit()
        refresh_demo(db, PASSWORD)
        db.commit()
        assert db.get(Organization, other.id)
        org = db.scalar(select(Organization).where(Organization.name == DEMO_NAME))
        assessments = list(db.scalars(select(Assessment).where(Assessment.organization_id == org.id)))
        assert len(assessments) == 9
        instrument = db.scalar(select(Instrument).where(Instrument.organization_id == org.id))
        assert instrument.scoring_rule == "sum_applicable_v1"
        assert len(instrument.criteria) == 151
        assert sum(item["maximum"] for item in instrument.criteria) == 365
        assert len({(a.laboratory_id, a.assessment_date) for a in assessments}) == 9
        assert all(score(a, instrument)["complete"] for a in assessments)
        assert all(a.reason.startswith("Cenário simulado") for a in assessments)
        actor = db.scalar(select(User).where(User.organization_id == org.id, User.role == "admin"))
        latest = next(a for a in assessments if a.assessment_date == "2026-10-20")
        context = build_context(db, actor, latest)
        assert context["findings"] and context["findings"][0]["allowed_source_ids"]
        assert "Cenário simulado" in context["findings"][0]["description"]
        result = import_assessments(db, actor, pilot_assessments())
        assert result["unchanged"] == 9 and result["created"] == result["revised"] == 0
        db.rollback()
    login(client)
    dashboard = client.get("/api/v1/dashboard").json()
    assert dashboard["assessment_count"] == 9
    assert dashboard["network_percentage"] == pytest.approx(71.23, abs=0.1)
    listing = client.get("/api/v1/assessments").json()
    assert listing["total"] == 9
    assert all(item["instrument_code"] == PILOT["instrument_code"] for item in listing["items"])
    sample = Path(__file__).resolve().parents[2] / "frontend/public/demo/slipta-pilot-assessments.csv"
    imported = client.post("/api/v1/imports/file", files={"file": (sample.name, sample.read_bytes(), "text/csv")})
    assert imported.status_code == 200, imported.text
    assert imported.json()["unchanged"] == 9


def test_refresh_refuses_non_demo_submissions(client):
    with session_factory()() as db:
        actor = db.scalar(select(User).where(User.email == "admin@labquality.local"))
        db.add(AssessmentRoot(organization_id=actor.organization_id, source="odk:15:real", external_id="protected"))
        db.commit()
        with pytest.raises(ValueError, match="não demonstrativas"):
            refresh_demo(db, PASSWORD)
        db.rollback()
        assert db.scalar(select(Organization).where(Organization.name == DEMO_NAME))


def test_odk_pilot_na_comments_identity_and_polling(client, monkeypatch):
    settings().odk_url, settings().odk_email, settings().odk_password = "https://odk.example", "test@example.invalid", "test-secret"
    with session_factory()() as db:
        refresh_demo(db, PASSWORD)
        db.commit()
    login(client)
    row = odk_row()
    selected = PILOT["criteria"][0]
    for path in selected["odk"]["na"]:
        set_nested(row, path, "na")
    set_nested(row, selected["odk"]["score"], 0)
    set_nested(row, selected["odk"]["comment"][0], "Não se aplica ao escopo documentado.")
    class FakeClient:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def get(self, url): return httpx.Response(200, request=httpx.Request("GET", url), json={"value": [row]})
    monkeypatch.setattr("app.integrations.httpx.Client", FakeClient)
    records = fetch_odk(pilot_request())
    assert len(records) == 1 and records[0].answers[selected["code"]].not_applicable
    assert records[0].answers[selected["code"]].value is None
    set_nested(row, selected["odk"]["comment"][0], "")
    with pytest.raises(ValueError, match="sem justificação"):
        fetch_odk(pilot_request())
    set_nested(row, selected["odk"]["comment"][0], "Não se aplica ao escopo documentado.")
    compound = next(c for c in PILOT["criteria"] if len(c["odk"]["na"]) > 1)
    set_nested(row, compound["odk"]["na"][0], None)
    assert fetch_odk(pilot_request())[0].answers[compound["code"]].value is None
    set_nested(row, compound["odk"]["na"][0], "sim")
    with session_factory()() as db:
        actor = db.scalar(select(User).where(User.email == "admin@labquality.local"))
        first = import_assessments(db, actor, records)
        assert first["created"] == 1
        assert import_assessments(db, actor, records)["unchanged"] == 1
        db.commit()
    row["__system"]["updatedAt"] = "2026-10-21T08:00:00Z"
    set_nested(row, selected["odk"]["na"][0], "parcial")
    with session_factory()() as db:
        actor = db.scalar(select(User).where(User.email == "admin@labquality.local"))
        changed = import_assessments(db, actor, fetch_odk(pilot_request()))
        assert changed["revised"] == 1
        db.commit()
    response = client.post("/api/v1/integrations/odk/subscription", json={"project_id": 15, "active": True})
    assert response.status_code == 200, response.text
    login(client, "gestor@labquality.local")
    assert client.post("/api/v1/integrations/odk/subscription", json={"project_id": 99}).status_code == 403
    login(client)
    schedule_odk()
    with session_factory()() as db:
        jobs = list(db.scalars(select(Job).where(Job.kind == "odk", Job.entity_id != "")))
        assert len(jobs) == 1 and jobs[0].status == "queued"
    assert process_one()
    with session_factory()() as db:
        jobs = list(db.scalars(select(Job).where(Job.kind == "odk")))
        assert jobs[0].status == "completed"
    schedule_odk()
    with session_factory()() as db:
        assert len(list(db.scalars(select(Job).where(Job.kind == "odk")))) == 1
