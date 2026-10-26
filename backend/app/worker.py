import argparse
import logging
import smtplib
import time
from datetime import timedelta
from email.message import EmailMessage
import httpx
from sqlalchemy import select, update
from .ai import execute_ai
from .config import settings
from .database import session_factory
from .integrations import fetch_odk
from .models import AIExecution, Action, Job, Notification, Register, User, now
from .schemas import ODKIn
from .security import EDITORS, laboratory_ids, role
from .services import import_assessments, notify

logger = logging.getLogger("labquality.worker")


def dispatch_email(db, notification, actor):
    recipient = db.get(User, notification.user_id)
    if (not recipient or not recipient.active or (notification.laboratory_id and
            notification.laboratory_id not in laboratory_ids(db, recipient))):
        notification.email_status = "cancelled"
        return
    if notification.email_status != "queued":
        return
    cfg = settings()
    message = EmailMessage()
    message["Subject"] = "LabQuality Copilot — nova notificação"
    message["From"] = cfg.smtp_from
    message["To"] = recipient.email
    message["Message-ID"] = f"<{notification.id}@labquality.local>"
    # Email contains no assessment findings, attachments, or sensitive evidence.
    message.set_content("Tem uma nova notificação no LabQuality Copilot. Inicie sessão para consultar os detalhes.")
    notification.email_status = "sending"
    db.commit()
    try:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=20) as smtp:
            if cfg.smtp_starttls:
                import ssl
                smtp.starttls(context=ssl.create_default_context())
            if cfg.smtp_username:
                smtp.login(cfg.smtp_username, cfg.smtp_password)
            smtp.send_message(message)
        notification.email_status = "sent"
    except Exception:
        notification.email_status = "uncertain"
        db.commit()
        raise


def fail_expired(db):
    expired = db.scalars(select(Job).where(Job.status == "running", Job.started_at < now() - timedelta(minutes=10)))
    for job in expired:
        job.status = "failed"
        job.error = "O trabalhador foi interrompido ou a execução excedeu dez minutos. Solicite nova execução."
        job.finished_at = now()
        if job.kind == "ai":
            run = db.get(AIExecution, job.entity_id)
            if run:
                run.status, run.error = "failed", job.error
        elif job.kind == "email":
            notification = db.get(Notification, job.entity_id)
            if notification and notification.email_status == "sending":
                notification.email_status = "uncertain"
    db.commit()


def process_one() -> bool:
    with session_factory()() as db:
        candidate = db.scalar(select(Job.id).where(Job.status == "queued", Job.available_at <= now()).order_by(Job.created_at).limit(1))
        if not candidate:
            return False
        claimed = db.execute(update(Job).where(Job.id == candidate, Job.status == "queued").values(
                            status="running", started_at=now(), attempts=Job.attempts + 1))
        db.commit()
        if claimed.rowcount != 1:
            return True
        job = db.get(Job, candidate)
        try:
            user = db.get(User, job.actor_id)
            if not user or not user.active or user.organization_id != job.organization_id:
                raise ValueError("O acesso do requerente foi revogado.")
            if job.kind == "ai":
                role(user, EDITORS | {"verifier"})
                execute_ai(db, db.get(AIExecution, job.entity_id), user)
            elif job.kind == "odk":
                role(user, {"admin", "manager"})
                records = fetch_odk(ODKIn.model_validate(job.payload))
                result = import_assessments(db, user, records) if records else {"created": 0, "unchanged": 0}
                job.payload = {"request": job.payload, "result": result}
            elif job.kind == "email":
                dispatch_email(db, db.get(Notification, job.entity_id), user)
            else:
                raise ValueError("Tipo de tarefa desconhecido.")
            job.status, job.finished_at = "completed", now()
            db.commit()
        except Exception as error:
            db.rollback()
            job = db.get(Job, candidate)
            if isinstance(error, httpx.HTTPStatusError):
                message = f"O serviço externo respondeu HTTP {error.response.status_code}. Verifique acessos e limites."
            elif isinstance(error, httpx.TimeoutException):
                message = "O serviço externo excedeu o tempo de resposta."
            elif isinstance(error, ValueError):
                message = str(error)[:500]
            else:
                message = "A execução falhou. Consulte os registos do trabalhador."
            job.status, job.error, job.finished_at = "failed", message, now()
            if job.kind == "ai":
                run = db.get(AIExecution, job.entity_id)
                run.status, run.error = "failed", message
            db.commit()
            logger.warning("job_failed id=%s kind=%s exception=%s", candidate, job.kind, type(error).__name__)
        return True


def due_reminders():
    from .api import today
    with session_factory()() as db:
        for model in (Action, Register):
            for row in db.scalars(select(model).where(model.status != "closed", model.due_date < today())):
                owner = db.get(User, row.owner_id)
                if owner and owner.active and row.laboratory_id in laboratory_ids(db, owner):
                    notify(db, owner, owner.id, row.laboratory_id, f"overdue:{model.__tablename__}:{row.id}:{today()}",
                           "Prazo ultrapassado: " + row.title, "Reveja o prazo e registe o progresso na aplicação.")
        db.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    last_housekeeping = 0
    while True:
        try:
            if time.monotonic() - last_housekeeping > 3600:
                with session_factory()() as db:
                    fail_expired(db)
                due_reminders()
                last_housekeeping = time.monotonic()
            worked = process_one()
        except Exception:
            logger.exception("Worker iteration failed")
            worked = False
        if args.once:
            return
        if not worked:
            time.sleep(2)


if __name__ == "__main__":
    main()
