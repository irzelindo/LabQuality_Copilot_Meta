import pytest
from sqlalchemy import func, select

from app.ai import assessment_readiness, build_context
from app.database import session_factory
from app.demo import PILOT
from app.import_slipta_sources import SOURCES, import_sources, source_bodies
from app.models import Assessment, Document, Instrument, Organization, User
from app.schemas import AssessmentIn
from app.services import import_assessments
from conftest import login


def test_source_files_cover_exact_criteria_and_import_once_as_drafts(client):
    bodies = source_bodies()
    assert {code for body in bodies for code in body.criterion_codes} == {
        criterion["code"] for criterion in PILOT["criteria"]
    }
    assert sum(len(body.criterion_codes) for body in bodies) == 151
    assert len({body.code for body in bodies}) == len(SOURCES) == 12
    assert all("https://aslm.org/" in body.content and body.laboratory_id is None for body in bodies)

    with session_factory()() as db:
        admin = db.scalar(select(User).where(User.email == "admin@labquality.local"))
        assert all(status == "new" for _, status in import_sources(db, admin, apply=False))
        assert db.scalar(select(func.count()).select_from(Document).where(
            Document.organization_id == admin.organization_id,
            Document.code.in_([source.code for source in SOURCES]))) == 0
        assert all(status == "new" for _, status in import_sources(db, admin, apply=True))
        db.commit()

    with session_factory()() as db:
        admin = db.scalar(select(User).where(User.email == "admin@labquality.local"))
        assert all(status == "unchanged" for _, status in import_sources(db, admin, apply=True))
        rows = list(db.scalars(select(Document).where(Document.organization_id == admin.organization_id,
                                                   Document.code.in_([source.code for source in SOURCES]))))
        assert len(rows) == 12
        assert all(row.status == "draft" and row.revision == 1 and row.scope_key == "organization"
                   and row.author_id == admin.id for row in rows)

    login(client)
    doc = next(row for row in client.get("/api/v1/documents").json() if row["code"] == SOURCES[0].code)
    doc = client.post(f"/api/v1/documents/{doc['id']}/transition",
                      json={"status": "review", "version": doc["version"]}).json()
    assert client.post(f"/api/v1/documents/{doc['id']}/transition",
                       json={"status": "approved", "version": doc["version"]}).status_code == 403
    login(client, "verificador@labquality.local")
    doc = client.post(f"/api/v1/documents/{doc['id']}/transition",
                      json={"status": "approved", "version": doc["version"]}).json()
    assert client.post(f"/api/v1/documents/{doc['id']}/transition",
                       json={"status": "published", "version": doc["version"]}).status_code == 200


def test_conflicting_revision_blocks_whole_batch_and_other_org_is_independent(client):
    with session_factory()() as db:
        admin = db.scalar(select(User).where(User.email == "admin@labquality.local"))
        db.add(Document(organization_id=admin.organization_id, scope_key="organization",
                        code=SOURCES[1].code, revision=1, title="Outro texto", content="A rever",
                        criterion_codes=["3.6"], status="published", author_id=admin.id))
        db.commit()
        with pytest.raises(ValueError, match="revisão diferente"):
            import_sources(db, admin, apply=True)
        assert db.scalar(select(func.count()).select_from(Document).where(
            Document.organization_id == admin.organization_id, Document.code == SOURCES[0].code)) == 0

        other = Organization(name="Outra instituição")
        db.add(other)
        db.flush()
        other_admin = User(organization_id=other.id, email="other@example.org", name="Outra admin",
                           role="admin", active=True, laboratory_ids=[], password_hash="unused")
        db.add(other_admin)
        db.flush()
        assert all(status == "new" for _, status in import_sources(db, other_admin, apply=True))
        db.commit()
        assert db.scalar(select(func.count()).select_from(Document).where(
            Document.organization_id == other.id, Document.code.in_([source.code for source in SOURCES]))) == 12


def test_meta_can_select_applicable_sources_across_all_twelve_sections(client):
    with session_factory()() as db:
        admin = db.scalar(select(User).where(User.email == "admin@labquality.local"))
        import_sources(db, admin, apply=True)
        docs = list(db.scalars(select(Document).where(Document.organization_id == admin.organization_id,
                                                  Document.code.in_([source.code for source in SOURCES]))))
        for doc in docs:
            doc.status = "published"  # Selection test; transition rules are exercised above.
        db.add(Instrument(organization_id=admin.organization_id, code=PILOT["instrument_code"],
                          version=PILOT["instrument_version"], name="Piloto SLIPTA",
                          scoring_rule="sum_applicable_v1",
                          criteria=[{key: c[key] for key in ("code", "section", "title", "maximum", "critical")}
                                    for c in PILOT["criteria"]]))
        db.flush()
        codes = ["11.2" if source.code == "SLIPTA-SEC-11-2023" else source.criterion_codes[0]
                 for source in SOURCES]
        imported = import_assessments(db, admin, [AssessmentIn(
            source="odk:1:slipta_v3_2023_mozambique", external_id="uuid:all-sections",
            laboratory_code="SUL", instrument_code=PILOT["instrument_code"],
            instrument_version=PILOT["instrument_version"], assessment_date="2026-09-19",
            answers={code: {"value": 0, "comment": "Verificação por concluir."} for code in codes})])
        db.flush()
        assessment = db.get(Assessment, imported["assessment_ids"][0])
        context = build_context(db, admin, assessment)
        readiness = assessment_readiness(db, admin, assessment)
        assert readiness["findings_count"] == readiness["applicable_findings_count"] == 12
        assert readiness["uncovered_criteria"] == [] and readiness["ready"]
        assert all(finding["allowed_source_ids"] for finding in context["findings"])
        assert "SLIPTA-SEC-12-2023" in {source["code"] for source in context["sources"]}
        assert len(context["sources"]) <= 12
