import csv
import io
import httpx
from datetime import date
from fastapi import HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .api import ACTOR, DB, record, router, today
from .models import *
from .schemas import *
from .security import *
from .services import *
from .connection_checks import check_connection
from .demo import PILOT
from typing import Literal


def documents_for(db, user):
    ids = laboratory_ids(db, user)
    return select(Document).where(Document.organization_id == user.organization_id,
            (Document.laboratory_id.is_(None)) | (Document.laboratory_id.in_(ids)))


@router.post("/system/connections/{service}/check")
def check_service_connection(service: Literal["model", "odk", "email"], user: User = ACTOR):
    role(user, {"admin"})
    return check_connection(service)


@router.get("/documents")
def documents(db: Session = DB, user: User = ACTOR):
    require_details(user)
    return [record(d) for d in db.scalars(documents_for(db, user).order_by(Document.code, Document.revision.desc()).limit(500))]


@router.post("/documents", status_code=201)
def add_document(body: DocumentIn, db: Session = DB, user: User = ACTOR):
    role(user, EDITORS)
    if body.laboratory_id:
        require_lab(db, user, body.laboratory_id)
    else:
        role(user, {"admin"})
    scope_key = body.laboratory_id or "organization"
    last_revision = db.scalar(select(func.max(Document.revision)).where(Document.organization_id == user.organization_id,
                       Document.scope_key == scope_key, Document.code == body.code)) or 0
    row = Document(organization_id=user.organization_id, scope_key=scope_key, revision=last_revision + 1,
                   author_id=user.id, **body.model_dump())
    db.add(row)
    db.flush()
    audit(db, user, "document.revision_created", row)
    return record(row)


@router.post("/documents/{document_id}/transition")
def transition_document(document_id: str, body: StateIn, db: Session = DB, user: User = ACTOR):
    require_details(user)
    row = get_scoped(db, Document, document_id, user)
    ensure_version(row, body.version)
    allowed = {"draft": {"review"}, "review": {"approved", "withdrawn"},
               "approved": {"published", "withdrawn"}, "published": {"withdrawn"}}
    if body.status not in allowed.get(row.status, set()):
        raise HTTPException(409, "Transição documental inválida.")
    if body.status == "review":
        role(user, EDITORS)
    else:
        role(user, APPROVERS)
        if row.author_id == user.id and body.status == "approved":
            raise HTTPException(403, "A aprovação deve ser feita por outra pessoa.")
    if body.status == "approved":
        row.reviewer_id = user.id
    if body.status == "withdrawn" and len(body.comment) < 5:
        raise HTTPException(422, "Indique o motivo da retirada.")
    if body.status == "published":
        previous = db.scalars(select(Document).where(Document.organization_id == user.organization_id,
                   Document.scope_key == row.scope_key, Document.code == row.code, Document.status == "published").with_for_update())
        for old in previous:
            if old.revision >= row.revision:
                raise HTTPException(409, "Já existe uma versão publicada mais recente.")
            old.status = "withdrawn"
            audit(db, user, "document.superseded", old, {"replacement_id": row.id})
    row.status = body.status
    audit(db, user, "document.transition", row, {"status": body.status, "comment": body.comment})
    db.flush()
    return record(row)


@router.get("/registers")
def registers(kind: str | None = None, laboratory_id: str | None = None, db: Session = DB, user: User = ACTOR):
    require_details(user)
    labs = laboratory_ids(db, user)
    if laboratory_id:
        require_lab(db, user, laboratory_id)
        labs = [laboratory_id]
    query = select(Register).where(Register.organization_id == user.organization_id, Register.laboratory_id.in_(labs))
    if kind:
        query = query.where(Register.kind == kind)
    return [record(r) for r in db.scalars(query.order_by(Register.due_date).limit(1000))]


@router.post("/registers", status_code=201)
def add_register(body: RegisterIn, db: Session = DB, user: User = ACTOR):
    role(user, EDITORS)
    require_lab(db, user, body.laboratory_id)
    eligible_owner(db, user, body.owner_id, body.laboratory_id)
    data = body.model_dump()
    data["due_date"] = body.due_date.isoformat()
    row = Register(organization_id=user.organization_id, **data)
    db.add(row)
    db.flush()
    audit(db, user, "register.created", row)
    notify(db, user, row.owner_id, row.laboratory_id, f"register:{row.id}:assigned", row.title, "Foi-lhe atribuído um registo para acompanhamento.")
    return record(row)


@router.post("/registers/{register_id}/transition")
def transition_register(register_id: str, body: StateIn, db: Session = DB, user: User = ACTOR):
    role(user, EDITORS | {"verifier"})
    row = get_scoped(db, Register, register_id, user)
    ensure_version(row, body.version)
    transitions = {"open": {"in_progress"}, "in_progress": {"closed"}, "closed": {"open"}}
    if body.status not in transitions.get(row.status, set()):
        raise HTTPException(409, "Transição inválida.")
    if body.status in {"open", "closed"} and len(body.comment) < 5:
        raise HTTPException(422, "Registe o resultado da revisão.")
    row.status = body.status
    audit(db, user, "register.transition", row, {"status": row.status, "comment": body.comment})
    db.flush()
    return record(row)


@router.get("/notifications")
def notifications(db: Session = DB, user: User = ACTOR):
    if user.role == "partner":
        return []
    labs = laboratory_ids(db, user)
    query = select(Notification).where(Notification.user_id == user.id, Notification.organization_id == user.organization_id,
              (Notification.laboratory_id.is_(None)) | (Notification.laboratory_id.in_(labs)))
    return [record(n) for n in db.scalars(query.order_by(Notification.created_at.desc()).limit(100))]


@router.post("/notifications/{notification_id}/read")
def read_notification(notification_id: str, db: Session = DB, user: User = ACTOR):
    row = get_scoped(db, Notification, notification_id, user)
    if row.user_id != user.id:
        raise HTTPException(404, "Notificação não encontrada.")
    row.read = True
    return {"ok": True}


@router.get("/audit")
def audit_events(offset: int = 0, db: Session = DB, user: User = ACTOR):
    role(user, {"admin", "manager", "verifier"})
    if offset < 0:
        raise HTTPException(422, "Página inválida.")
    query = select(AuditEvent).where(AuditEvent.organization_id == user.organization_id)
    if user.role != "admin":
        query = query.where(AuditEvent.laboratory_id.in_(laboratory_ids(db, user)))
    rows = list(db.scalars(query.order_by(AuditEvent.created_at.desc()).offset(offset).limit(100)))
    return [{**record(a), "actor_name": db.get(User, a.actor_id).name} for a in rows]


@router.get("/dashboard")
def dashboard(laboratory_id: str | None = None, start: date | None = None, end: date | None = None,
              db: Session = DB, user: User = ACTOR):
    assessments = current_assessments(db, user, laboratory_id, start.isoformat() if start else None, end.isoformat() if end else None)
    labs = [laboratory_id] if laboratory_id else laboratory_ids(db, user)
    by_lab = {}
    by_date = {}
    missing = 0
    for a in assessments:
        s = score(a, db.get(Instrument, a.instrument_id))
        by_lab.setdefault(a.laboratory_id, []).append((a, s))
        day = by_date.setdefault(a.assessment_date, {"date": a.assessment_date, "values": [], "instruments": set(), "assessments": 0, "incomplete": 0})
        day["instruments"].add(a.instrument_id)
        day["assessments"] += 1
        if s["percentage"] is None:
            missing += 1
            day["incomplete"] += 1
        else:
            day["values"].append(s["percentage"])
    lab_rows = []
    latest_ids = []
    for lab_id in labs:
        lab = db.get(Laboratory, lab_id)
        items = by_lab.get(lab_id, [])
        comparable = [s for a, s in items if s["complete"]]
        latest = items[0] if items else None
        if latest:
            latest_ids.append(latest[0].id)
        same_instrument = [s for a, s in items[1:] if latest and a.instrument_id == latest[0].instrument_id and s["complete"]]
        percentage = latest[1]["percentage"] if latest else None
        difference = round(percentage - same_instrument[0]["percentage"], 2) if percentage is not None and same_instrument else None
        lab_rows.append({"id": lab.id, "code": lab.code, "name": lab.name, "region": lab.region, "assessments": len(items),
                         "latest_date": latest[0].assessment_date if latest else None, "percentage": percentage,
                         "maximum": latest[1]["maximum"] if latest else None,
                         "full_maximum": latest[1]["full_maximum"] if latest else None,
                         "not_applicable": latest[1]["not_applicable"] if latest else 0,
                         "change": difference, "trend": "improving" if difference is not None and difference > 0 else
                         "declining" if difference is not None and difference < 0 else "stable" if difference == 0 else "unavailable",
                         "coverage": latest[1]["coverage"] if latest else 0,
                         "series": [{"date": a.assessment_date, "percentage": s["percentage"]} for a, s in reversed(items)]})
    latest_percentages = [r["percentage"] for r in lab_rows if r["percentage"] is not None]
    latest_instruments = {db.get(Assessment, assessment_id).instrument_id for assessment_id in latest_ids}
    comparable = len(latest_instruments) <= 1
    actions = list(db.scalars(select(Action).where(Action.organization_id == user.organization_id, Action.laboratory_id.in_(labs))))
    open_actions = [a for a in actions if a.status != "closed"]
    closed = [a for a in actions if a.status == "closed" and a.closed_at]
    critical = list(db.scalars(select(Finding).where(Finding.assessment_id.in_(latest_ids), Finding.critical.is_(True))))
    unresolved = []
    for finding in critical:
        linked = [a for a in actions if a.finding_id == finding.id]
        if not linked or any(a.status != "closed" for a in linked):
            unresolved.append(finding)
    section_stats = {}
    for items in by_lab.values():
        if not items:
            continue
        for name, value in items[0][1]["sections"].items():
            instrument = db.get(Instrument, items[0][0].instrument_id)
            label = name if comparable else f"{instrument.code} v{instrument.version} · {name}"
            entry = section_stats.setdefault(label, [])
            if value["percentage"] is not None:
                entry.append(value["percentage"])
    series = []
    for d in sorted(by_date):
        entry = by_date[d]
        values = entry.pop("values")
        instruments_in_day = entry.pop("instruments")
        series.append({**entry, "percentage": round(sum(values) / len(values), 2) if values and len(instruments_in_day) == 1 else None})
    mean_resolution = round(sum((a.closed_at - a.created_at).total_seconds() / 86400 for a in closed) / len(closed), 2) if closed else None
    result = {"laboratory_count": len(labs), "evaluated_laboratories": len(by_lab), "assessment_count": len(assessments),
              "incomplete_assessments": missing, "network_percentage": round(sum(latest_percentages) / len(latest_percentages), 2) if latest_percentages and comparable else None,
              "comparable": comparable,
              "instrument_versions": [db.get(Instrument, i).code + " " + db.get(Instrument, i).version for i in sorted(latest_instruments)],
              "network_denominator": len(latest_percentages), "aggregation": "mean_of_latest_complete_result_per_laboratory_in_period",
              "open_actions": len(open_actions), "overdue_actions": sum(a.due_date < today() for a in open_actions),
              "closed_actions": len(closed), "mean_resolution_days": mean_resolution,
              "critical_count": len(unresolved), "laboratories": lab_rows, "series": series,
              "sections": sorted([{"section": k, "percentage": round(sum(v) / len(v), 2) if v else None, "coverage": len(v)} for k, v in section_stats.items()],
                                  key=lambda x: x["percentage"] if x["percentage"] is not None else -1),
              "filters": {"laboratory_id": laboratory_id, "start": start, "end": end}, "as_of": today()}
    if user.role != "partner":
        result["critical_findings"] = [record(f) for f in unresolved]
        result["prolonged_actions"] = [{"id": a.id, "title": a.title, "days_open": (now() - a.created_at).days, "due_date": a.due_date} for a in sorted(open_actions, key=lambda a: a.created_at)[:10]]
    return result


@router.get("/reports/assessments.csv")
def export_assessments(laboratory_id: str | None = None, start: date | None = None, end: date | None = None,
                       db: Session = DB, user: User = ACTOR):
    require_details(user)
    rows = current_assessments(db, user, laboratory_id, start.isoformat() if start else None, end.isoformat() if end else None)
    out = io.StringIO()
    out.write("\ufeff")
    writer = csv.writer(out)
    writer.writerow(["assessment_id", "laboratory", "date", "instrument", "instrument_version", "revision", "status", "obtained", "maximum", "percentage", "coverage", "full_maximum", "not_applicable"])
    def safe(value):
        s = str(value)
        return "'" + s if s.startswith(("=", "+", "-", "@", "\t", "\r")) else s
    for a in rows:
        instrument = db.get(Instrument, a.instrument_id)
        s = score(a, instrument)
        writer.writerow([safe(v) for v in [a.id, db.get(Laboratory, a.laboratory_id).name, a.assessment_date, instrument.code,
                         instrument.version, a.revision, a.status, s["obtained"], s["maximum"], s["percentage"] if s["percentage"] is not None else "", s["coverage"], s["full_maximum"], s["not_applicable"]]])
    if rows:
        audit(db, user, "report.exported", rows[0], {"rows": len(rows), "laboratory_id": laboratory_id, "start": str(start), "end": str(end)})
    return Response(out.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="labquality-assessments.csv"'})


@router.get("/system/status")
def system_status(db: Session = DB, user: User = ACTOR):
    from .config import settings
    cfg = settings()
    return {"version": "0.1.0", "ai_configured": bool(cfg.model_api_key), "model": cfg.model_id,
            "email_configured": cfg.smtp_configured, "odk_configured": bool(cfg.odk_url and cfg.odk_email and cfg.odk_password),
            "storage": "private_local_volume", "demo_instrument": "SLIPTA-ODK-PILOT 2026.10 — 151 items, provisional 365-point rubric; no official stars"}


@router.post("/integrations/odk/sync", status_code=202)
def queue_odk(body: ODKIn, db: Session = DB, user: User = ACTOR):
    from .config import settings
    role(user, {"admin", "manager"})
    cfg = settings()
    if not (cfg.odk_url and cfg.odk_email and cfg.odk_password):
        raise HTTPException(503, "Configure a ligação ODK no servidor.")
    job = Job(organization_id=user.organization_id, actor_id=user.id, kind="odk", entity_id=user.id, payload=body.model_dump())
    db.add(job)
    db.flush()
    audit(db, user, "odk.sync_requested", job)
    return {"job_id": job.id, "status": job.status}


@router.post("/integrations/odk/preview")
def preview_odk(body: ODKIn, db: Session = DB, user: User = ACTOR):
    """Read ODK submissions without writing them or exposing the full questionnaire."""
    from .config import settings
    from .integrations import fetch_odk_with_metadata
    role(user, {"admin"})
    cfg = settings()
    if not (cfg.odk_url and cfg.odk_email and cfg.odk_password):
        raise HTTPException(503, "Configure a ligação ODK no servidor.")
    if body.instrument_code != PILOT["instrument_code"] or body.instrument_version != PILOT["instrument_version"]:
        raise HTTPException(422, "A pré-validação está disponível para o instrumento piloto SLIPTA.")
    instrument = db.scalar(select(Instrument).where(Instrument.organization_id == user.organization_id,
        Instrument.code == body.instrument_code, Instrument.version == body.instrument_version,
        Instrument.published.is_(True)))
    if not instrument:
        raise HTTPException(422, "Publique primeiro o instrumento piloto SLIPTA desta versão.")
    try:
        records, metadata = fetch_odk_with_metadata(body)
    except httpx.HTTPStatusError as error:
        code = error.response.status_code
        if code in (401, 403):
            raise HTTPException(422, "O ODK recusou o acesso ao projecto ou formulário. Confirme as permissões da conta.") from error
        if code == 404:
            raise HTTPException(422, "O projecto ou formulário ODK não foi encontrado. Confirme o ID do projecto e o XML ID.") from error
        raise HTTPException(502, "O servidor ODK não conseguiu responder à pré-validação.") from error
    except httpx.RequestError as error:
        raise HTTPException(502, "Não foi possível estabelecer ligação ao ODK. Confirme a rede e o endereço.") from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    known = {lab.code for lab in db.scalars(select(Laboratory).where(Laboratory.organization_id == user.organization_id))}
    groups: dict[str, dict] = {}
    for row, details in zip(records, metadata):
        group = groups.setdefault(row.laboratory_code, {"code": row.laboratory_code,
            "names": set(), "submissions": 0, "first_date": row.assessment_date.isoformat(),
            "last_date": row.assessment_date.isoformat(), "missing_scores": 0, "registered": row.laboratory_code in known})
        if details["laboratory_name"]:
            group["names"].add(details["laboratory_name"])
        group["submissions"] += 1
        group["first_date"] = min(group["first_date"], row.assessment_date.isoformat())
        group["last_date"] = max(group["last_date"], row.assessment_date.isoformat())
        group["missing_scores"] += sum(answer.value is None and not answer.not_applicable for answer in row.answers.values())
    laboratories = [{**group, "names": sorted(group["names"])[:5]} for group in sorted(groups.values(), key=lambda item: item["code"])]
    mapped = any(answer.value is not None or answer.not_applicable
        for row in records for answer in row.answers.values())
    ready = bool(records) and mapped and all(group["registered"] for group in laboratories)
    changes = None
    if ready:
        transaction = db.begin_nested()
        try:
            result = import_assessments(db, user, records)
            changes = {key: result[key] for key in ("created", "revised", "unchanged")}
        finally:
            transaction.rollback()
    return {"submissions": len(records), "laboratories": laboratories,
        "ready": ready, "changes": changes,
        "source": f"odk:{body.project_id}:{body.form_id}",
        "message": ("Nenhum dos 151 campos de pontuação/NA foi reconhecido. Confirme a versão do formulário ODK."
            if records and not mapped else "Pré-validação sem importação. Confirme os laboratórios e as respostas antes da análise Meta.")}


@router.get("/integrations/odk/subscription")
def odk_subscription(db: Session = DB, user: User = ACTOR):
    role(user, {"admin"})
    row = db.scalar(select(ODKSyncConfig).where(ODKSyncConfig.organization_id == user.organization_id))
    return {"project_id": row.project_id, "form_id": row.form_id, "active": row.active,
            "next_run_at": row.next_run_at} if row else None


@router.post("/integrations/odk/subscription")
def configure_odk_subscription(body: ODKSubscriptionIn, db: Session = DB, user: User = ACTOR):
    from .config import settings
    role(user, {"admin"})
    cfg = settings()
    if not (cfg.odk_url and cfg.odk_email and cfg.odk_password):
        raise HTTPException(503, "Configure a ligação ODK no servidor.")
    instrument = db.scalar(select(Instrument).where(Instrument.organization_id == user.organization_id,
        Instrument.code == PILOT["instrument_code"], Instrument.version == PILOT["instrument_version"],
        Instrument.published.is_(True)))
    if not instrument:
        raise HTTPException(422, "Publique primeiro o instrumento piloto SLIPTA desta versão.")
    row = db.scalar(select(ODKSyncConfig).where(ODKSyncConfig.organization_id == user.organization_id))
    if not row:
        row = ODKSyncConfig(organization_id=user.organization_id, project_id=body.project_id,
            form_id=PILOT["form_id"], actor_id=user.id, active=body.active, next_run_at=now())
        db.add(row)
    else:
        row.project_id, row.actor_id, row.active = body.project_id, user.id, body.active
        row.next_run_at = now()
    db.flush()
    audit(db, user, "odk.subscription_updated", row, {"project_id": body.project_id, "active": body.active})
    return {"project_id": row.project_id, "form_id": row.form_id, "active": row.active,
            "next_run_at": row.next_run_at}


@router.get("/jobs")
def jobs(db: Session = DB, user: User = ACTOR):
    role(user, {"admin", "manager"})
    query = select(Job).where(Job.organization_id == user.organization_id)
    if user.role != "admin":
        query = query.where(Job.actor_id == user.id)
    return [record(j, {"payload"}) for j in db.scalars(query.order_by(Job.created_at.desc()).limit(100))]
