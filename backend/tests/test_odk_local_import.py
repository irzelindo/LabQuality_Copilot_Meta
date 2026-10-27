import pytest
from sqlalchemy import func, select

from app.backup import create_backup
from app.config import settings
from app.database import session_factory
from app.demo import PILOT
from app.import_odk_pilot import run
from app.models import AssessmentRoot, Instrument, Laboratory, User
from app.schemas import AssessmentIn


def test_local_odk_import_previews_backs_up_and_does_not_duplicate(client, monkeypatch, tmp_path, capsys):
    from app import import_odk_pilot as importer

    cfg = settings()
    cfg.odk_url, cfg.odk_email, cfg.odk_password = "https://odk.example", "test@example.invalid", "test-only"
    with session_factory()() as db:
        admin = db.scalar(select(User).where(User.email == "admin@labquality.local"))
        db.add(Instrument(organization_id=admin.organization_id, code=PILOT["instrument_code"],
            version=PILOT["instrument_version"], name="Piloto SLIPTA", scoring_rule="sum_applicable_v1",
            criteria=[{key: criterion[key] for key in ("code", "section", "title", "maximum", "critical")}
                      for criterion in PILOT["criteria"]]))
        db.commit()

    records = [AssessmentIn(source=f"odk:1:{PILOT['form_id']}", external_id=f"uuid:test-{i}",
        laboratory_code="LAB01" if i < 5 else "LAB02", instrument_code=PILOT["instrument_code"],
        instrument_version=PILOT["instrument_version"], assessment_date="2026-09-19",
        answers={"1.1": {"value": 1, "comment": "Observação do teste."}}) for i in range(9)]
    metadata = [{"laboratory_name": "Laboratório Um" if i < 5 else "Laboratório Dois"} for i in range(9)]
    monkeypatch.setattr(importer, "fetch_odk_with_metadata", lambda _: (records, metadata))
    backups = []

    def backup(_):
        created = create_backup(tmp_path / "backups")
        backups.append(created)
        return created

    monkeypatch.setattr(importer, "create_backup", backup)
    run(1, 9, "admin@labquality.local", apply=False, register_missing=False)
    assert "por cadastrar" in capsys.readouterr().out
    assert backups == []
    with session_factory()() as db:
        assert db.scalar(select(func.count()).select_from(AssessmentRoot).where(AssessmentRoot.source == records[0].source)) == 0
        assert db.scalar(select(func.count()).select_from(Laboratory).where(Laboratory.code.like("LAB0%"))) == 0

    run(1, 9, "admin@labquality.local", apply=True, register_missing=True)
    assert "9 novas" in capsys.readouterr().out
    assert len(backups) == 1 and (backups[0] / "database.sqlite").is_file()
    run(1, 9, "admin@labquality.local", apply=True, register_missing=False)
    assert "9 inalteradas" in capsys.readouterr().out
    with session_factory()() as db:
        assert db.scalar(select(func.count()).select_from(AssessmentRoot).where(AssessmentRoot.source == records[0].source)) == 9
        assert db.scalar(select(func.count()).select_from(Laboratory).where(Laboratory.code.like("LAB0%"))) == 2


def test_local_odk_import_refuses_changed_count(client, monkeypatch):
    from app import import_odk_pilot as importer

    cfg = settings()
    cfg.odk_url, cfg.odk_email, cfg.odk_password = "https://odk.example", "test@example.invalid", "test-only"
    monkeypatch.setattr(importer, "fetch_odk_with_metadata", lambda _: ([], []))
    with pytest.raises(ValueError, match="Esperadas 9 submissões"):
        run(1, 9, "admin@labquality.local", apply=True, register_missing=True)
