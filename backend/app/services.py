import hashlib
import json
from datetime import date
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .models import Assessment, AssessmentRoot, Finding, ImportRun, Instrument, Job, Laboratory, Notification, User
from .schemas import AssessmentIn
from .security import audit, laboratory_ids, require_lab


def score(assessment: Assessment, instrument: Instrument) -> dict:
    sections = {}
    answered = 0
    total = 0
    maximum = 0
    for criterion in instrument.criteria:
        section = sections.setdefault(criterion["section"], {"obtained": 0, "maximum": 0, "answered": 0, "items": 0})
        value = assessment.answers.get(criterion["code"], {}).get("value")
        maximum += criterion["maximum"]
        section["maximum"] += criterion["maximum"]
        section["items"] += 1
        if value is not None:
            answered += 1
            total += value
            section["obtained"] += value
            section["answered"] += 1
    complete = answered == len(instrument.criteria)
    for item in sections.values():
        item["percentage"] = round(item["obtained"] / item["maximum"] * 100, 2) if item["answered"] == item["items"] else None
    return {"obtained": total, "maximum": maximum, "answered": answered, "items": len(instrument.criteria),
            "coverage": round(answered / len(instrument.criteria) * 100, 2),
            "complete": complete, "percentage": round(total / maximum * 100, 2) if complete else None, "sections": sections}


def ensure_version(entity, expected: int):
    if entity.version != expected:
        raise HTTPException(409, "O registo foi alterado. Actualize a página antes de guardar.")


def eligible_owner(db: Session, actor: User, owner_id: str, lab_id: str) -> User:
    owner = db.get(User, owner_id)
    if not owner or not owner.active or owner.organization_id != actor.organization_id or owner.role in {"partner", "coordinator"}:
        raise HTTPException(422, "Responsável inválido.")
    if lab_id not in laboratory_ids(db, owner):
        raise HTTPException(422, "O responsável não tem acesso ao laboratório.")
    return owner


def notify(db: Session, actor: User, owner_id: str, lab_id: str, event_key: str, title: str, message: str):
    existing = db.scalar(select(Notification).where(Notification.user_id == owner_id, Notification.event_key == event_key))
    if existing:
        return
    notification = Notification(organization_id=actor.organization_id, user_id=owner_id, laboratory_id=lab_id,
                                event_key=event_key, title=title, message=message,
                                email_status="queued" if settings().smtp_host else "disabled")
    db.add(notification)
    db.flush()
    if settings().smtp_host:
        db.add(Job(organization_id=actor.organization_id, actor_id=actor.id, kind="email", entity_id=notification.id))


def import_assessments(db: Session, user: User, records: list[AssessmentIn]) -> dict:
    prepared = []
    seen = set()
    for idx, row in enumerate(records):
        key = (row.source, row.external_id)
        if key in seen:
            raise HTTPException(422, f"Avaliação duplicada no ficheiro, registo {idx + 1}.")
        seen.add(key)
        lab = db.scalar(select(Laboratory).where(Laboratory.organization_id == user.organization_id, Laboratory.code == row.laboratory_code))
        if not lab:
            raise HTTPException(422, f"Laboratório desconhecido no registo {idx + 1}.")
        require_lab(db, user, lab.id)
        instrument = db.scalar(select(Instrument).where(Instrument.organization_id == user.organization_id, Instrument.code == row.instrument_code,
                                                        Instrument.version == row.instrument_version, Instrument.published.is_(True)))
        if not instrument:
            raise HTTPException(422, f"Instrumento/versão desconhecido no registo {idx + 1}.")
        criteria = {c["code"]: c for c in instrument.criteria}
        if set(row.answers) - set(criteria):
            raise HTTPException(422, f"Critérios desconhecidos no registo {idx + 1}.")
        for code, answer in row.answers.items():
            if answer.value is not None and answer.value > criteria[code]["maximum"]:
                raise HTTPException(422, f"Pontuação acima do máximo para {code}, registo {idx + 1}.")
        answers = {c: row.answers[c].model_dump() if c in row.answers else {"value": None, "comment": ""} for c in criteria}
        content = {"laboratory_id": lab.id, "instrument_id": instrument.id, "date": row.assessment_date.isoformat(), "answers": answers}
        checksum = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        prepared.append((row, lab, instrument, answers, checksum))
    result = {"created": 0, "revised": 0, "unchanged": 0, "assessment_ids": []}
    for row, lab, instrument, answers, checksum in prepared:
        root = db.scalar(select(AssessmentRoot).where(AssessmentRoot.organization_id == user.organization_id,
                         AssessmentRoot.source == row.source, AssessmentRoot.external_id == row.external_id).with_for_update())
        previous = db.scalar(select(Assessment).where(Assessment.root_id == root.id, Assessment.revision == root.head_revision)) if root else None
        if previous and (previous.laboratory_id != lab.id or previous.instrument_id != instrument.id):
            raise HTTPException(409, "A identidade externa já pertence a outro laboratório ou instrumento. Use uma nova identidade.")
        if previous and previous.checksum == checksum:
            result["unchanged"] += 1
            result["assessment_ids"].append(previous.id)
            continue
        if not root:
            root = AssessmentRoot(organization_id=user.organization_id, source=row.source, external_id=row.external_id, head_revision=0)
            db.add(root)
            db.flush()
        root.head_revision += 1
        assessment = Assessment(organization_id=user.organization_id, root_id=root.id, laboratory_id=lab.id, instrument_id=instrument.id,
                                revision=root.head_revision, assessment_date=row.assessment_date.isoformat(), answers=answers,
                                checksum=checksum, source_revision=row.source_revision, author_id=user.id,
                                reason=row.reason or ("Actualização recebida da origem." if previous else "Importação inicial."))
        db.add(assessment)
        db.flush()
        for criterion in instrument.criteria:
            answer = answers[criterion["code"]]
            if answer["value"] is not None and answer["value"] < criterion["maximum"]:
                db.add(Finding(organization_id=user.organization_id, laboratory_id=lab.id, assessment_id=assessment.id,
                               criterion_code=criterion["code"], title=criterion["title"], critical=criterion.get("critical", False)))
        audit(db, user, "assessment.revised" if previous else "assessment.imported", assessment,
              {"root_id": root.id, "revision": assessment.revision})
        result["revised" if previous else "created"] += 1
        result["assessment_ids"].append(assessment.id)
    run = ImportRun(organization_id=user.organization_id, actor_id=user.id, source=records[0].source if records else "", result=result)
    db.add(run)
    db.flush()
    result["import_run_id"] = run.id
    return result


def current_assessments(db: Session, user: User, laboratory_id: str | None = None, start: str | None = None, end: str | None = None):
    labs = laboratory_ids(db, user)
    if laboratory_id:
        require_lab(db, user, laboratory_id)
        labs = [laboratory_id]
    query = select(Assessment).join(AssessmentRoot, AssessmentRoot.id == Assessment.root_id).where(
        Assessment.organization_id == user.organization_id, Assessment.laboratory_id.in_(labs),
        Assessment.revision == AssessmentRoot.head_revision)
    if start:
        date.fromisoformat(start)
        query = query.where(Assessment.assessment_date >= start)
    if end:
        date.fromisoformat(end)
        query = query.where(Assessment.assessment_date <= end)
    return list(db.scalars(query.order_by(Assessment.assessment_date.desc(), Assessment.created_at.desc())))
