import pytest
from sqlalchemy import func, select

from app.database import session_factory
from app.import_slipta_sources import SOURCES, import_sources, source_bodies
from app.models import Document, Organization, User
from conftest import login


def test_source_files_cover_exact_criteria_and_import_once_as_drafts(client):
    bodies = source_bodies()
    assert {code for body in bodies for code in body.criterion_codes} == {
        "1.5", "2.5", "2.9", "3.6", "3.10", "11.1", "12.6", "12.11", "12.14", "12.23"
    }
    assert len({body.code for body in bodies}) == len(SOURCES) == 3
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
        assert len(rows) == 3
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
            Document.organization_id == other.id, Document.code.in_([source.code for source in SOURCES]))) == 3
