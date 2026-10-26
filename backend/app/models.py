from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Integer, JSON, ForeignKey, DateTime, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uid() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Identity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Scoped(Identity):
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)


class Organization(Identity, Base):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(200))


class Laboratory(Scoped, Base):
    __tablename__ = "laboratories"
    __table_args__ = (UniqueConstraint("organization_id", "code"),)
    code: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(200))
    region: Mapped[str] = mapped_column(String(100), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Scoped, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(30))
    laboratory_ids: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class LoginSession(Identity, Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class Instrument(Scoped, Base):
    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("organization_id", "code", "version"),)
    code: Mapped[str] = mapped_column(String(60))
    version: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    criteria: Mapped[list] = mapped_column(JSON)
    scoring_rule: Mapped[str] = mapped_column(String(40), default="sum_fixed_v1")
    published: Mapped[bool] = mapped_column(Boolean, default=True)


class AssessmentRoot(Scoped, Base):
    __tablename__ = "assessment_roots"
    __table_args__ = (UniqueConstraint("organization_id", "source", "external_id"),)
    source: Mapped[str] = mapped_column(String(200))
    external_id: Mapped[str] = mapped_column(String(200))
    head_revision: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}


class Assessment(Scoped, Base):
    __tablename__ = "assessments"
    __table_args__ = (UniqueConstraint("root_id", "revision"),)
    root_id: Mapped[str] = mapped_column(ForeignKey("assessment_roots.id"), index=True)
    laboratory_id: Mapped[str] = mapped_column(ForeignKey("laboratories.id"), index=True)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"))
    revision: Mapped[int] = mapped_column(Integer)
    assessment_date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30), default="review")
    source_revision: Mapped[str] = mapped_column(String(200), default="")
    checksum: Mapped[str] = mapped_column(String(64))
    answers: Mapped[dict] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(Text, default="")
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}


class Finding(Scoped, Base):
    __tablename__ = "findings"
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    laboratory_id: Mapped[str] = mapped_column(ForeignKey("laboratories.id"), index=True)
    criterion_code: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(Text)
    critical: Mapped[bool] = mapped_column(Boolean, default=False)


class Action(Scoped, Base):
    __tablename__ = "actions"
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id"), index=True)
    laboratory_id: Mapped[str] = mapped_column(ForeignKey("laboratories.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    cause: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    due_date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30), default="proposed")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}


class Evidence(Scoped, Base):
    __tablename__ = "evidence"
    action_id: Mapped[str] = mapped_column(ForeignKey("actions.id"), index=True)
    laboratory_id: Mapped[str] = mapped_column(ForeignKey("laboratories.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(100))
    storage_key: Mapped[str] = mapped_column(String(64))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(Text, default="")
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))


class Verification(Scoped, Base):
    __tablename__ = "verifications"
    action_id: Mapped[str] = mapped_column(ForeignKey("actions.id"), index=True)
    verifier_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    result: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str] = mapped_column(Text)
    evidence_ids: Mapped[list] = mapped_column(JSON)


class Document(Scoped, Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("organization_id", "scope_key", "code", "revision"),)
    laboratory_id: Mapped[str | None] = mapped_column(ForeignKey("laboratories.id"), nullable=True)
    scope_key: Mapped[str] = mapped_column(String(36), default="organization")
    code: Mapped[str] = mapped_column(String(60))
    revision: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(250))
    content: Mapped[str] = mapped_column(Text)
    criterion_codes: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}


class Register(Scoped, Base):
    __tablename__ = "registers"
    laboratory_id: Mapped[str] = mapped_column(ForeignKey("laboratories.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    due_date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30), default="open")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}


class Notification(Scoped, Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("user_id", "event_key"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    laboratory_id: Mapped[str | None] = mapped_column(ForeignKey("laboratories.id"), nullable=True)
    event_key: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(300))
    message: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    email_status: Mapped[str] = mapped_column(String(30), default="disabled")


class AuditEvent(Scoped, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    operation: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80))
    laboratory_id: Mapped[str | None] = mapped_column(ForeignKey("laboratories.id"), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class ImportRun(Scoped, Base):
    __tablename__ = "import_runs"
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    source: Mapped[str] = mapped_column(String(200))
    result: Mapped[dict] = mapped_column(JSON)


class AIExecution(Scoped, Base):
    __tablename__ = "ai_executions"
    laboratory_id: Mapped[str] = mapped_column(ForeignKey("laboratories.id"), index=True)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"))
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(40), default="quality-actions-v1")
    sources: Mapped[list] = mapped_column(JSON, default=list)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    accepted: Mapped[dict] = mapped_column(JSON, default=dict)
    usage: Mapped[dict] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}


class Job(Scoped, Base):
    __tablename__ = "jobs"
    kind: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    entity_id: Mapped[str] = mapped_column(String(36))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error: Mapped[str] = mapped_column(Text, default="")


class ODKSyncConfig(Scoped, Base):
    __tablename__ = "odk_sync_configs"
    __table_args__ = (UniqueConstraint("organization_id"),)
    project_id: Mapped[int] = mapped_column(Integer)
    form_id: Mapped[str] = mapped_column(String(200))
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime, default=now)
