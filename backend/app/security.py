import hashlib
import secrets
from datetime import timedelta
from fastapi import Cookie, Depends, HTTPException
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import AuditEvent, Laboratory, LoginSession, User, now

passwords = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = passwords.hash("not-a-real-account-password")
EDITORS = {"admin", "manager", "quality", "assessor"}
APPROVERS = {"admin", "manager", "verifier"}
ROLES = {"admin", "coordinator", "manager", "quality", "assessor", "verifier", "partner"}


def role(user: User, allowed: set[str]):
    if user.role not in allowed:
        raise HTTPException(403, "O seu perfil não permite esta operação.")


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(48)
    db.add(LoginSession(user_id=user.id, token_hash=token_hash(token), expires_at=now() + timedelta(hours=settings().session_hours)))
    return token


def current_user(lq_session: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> User:
    if not lq_session:
        raise HTTPException(401, "Inicie sessão.")
    session = db.scalar(select(LoginSession).where(LoginSession.token_hash == token_hash(lq_session), LoginSession.expires_at > now()))
    user = db.get(User, session.user_id) if session else None
    if not user or not user.active:
        raise HTTPException(401, "A sessão expirou ou o acesso foi revogado.")
    return user


def laboratory_ids(db: Session, user: User) -> list[str]:
    query = select(Laboratory.id).where(Laboratory.organization_id == user.organization_id, Laboratory.active.is_(True))
    if user.role not in {"admin", "coordinator", "partner"}:
        query = query.where(Laboratory.id.in_(user.laboratory_ids))
    return list(db.scalars(query))


def require_lab(db: Session, user: User, lab_id: str):
    if lab_id not in laboratory_ids(db, user):
        raise HTTPException(404, "Laboratório não encontrado.")


def get_scoped(db: Session, model, record_id: str, user: User):
    row = db.get(model, record_id)
    if not row or row.organization_id != user.organization_id:
        raise HTTPException(404, "Registo não encontrado.")
    if hasattr(row, "laboratory_id") and row.laboratory_id:
        require_lab(db, user, row.laboratory_id)
    return row


def require_details(user: User):
    if user.role == "partner":
        raise HTTPException(403, "O perfil de parceiro tem acesso apenas aos indicadores agregados.")


def audit(db: Session, user: User, operation: str, entity, details: dict | None = None):
    db.add(AuditEvent(organization_id=user.organization_id, actor_id=user.id, operation=operation,
                      entity_type=entity.__tablename__, entity_id=entity.id,
                      laboratory_id=getattr(entity, "laboratory_id", None), details=details or {}))


def user_out(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role,
            "laboratory_ids": user.laboratory_ids, "active": user.active}
