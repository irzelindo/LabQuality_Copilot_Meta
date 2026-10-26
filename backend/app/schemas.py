from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Schema):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class LabIn(Schema):
    code: str = Field(min_length=1, max_length=60, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=200)
    region: str = Field(default="", max_length=100)


class UserIn(Schema):
    name: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["admin", "coordinator", "manager", "quality", "assessor", "verifier", "partner"]
    laboratory_ids: list[str] = Field(default_factory=list, max_length=1000)

    @field_validator("email")
    @classmethod
    def email_shape(cls, value):
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Email inválido")
        return value.lower()


class AccessUpdate(Schema):
    role: Literal["admin", "coordinator", "manager", "quality", "assessor", "verifier", "partner"]
    active: bool
    laboratory_ids: list[str] = Field(max_length=1000)


class PasswordChange(Schema):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=12, max_length=128)


class Criterion(Schema):
    code: str = Field(min_length=1, max_length=60)
    section: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=2, max_length=1000)
    maximum: int = Field(ge=1, le=100)
    critical: bool = False


class InstrumentIn(Schema):
    code: str = Field(min_length=1, max_length=60)
    version: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    criteria: list[Criterion] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def unique_codes(self):
        if len({c.code for c in self.criteria}) != len(self.criteria):
            raise ValueError("Os códigos dos critérios devem ser únicos.")
        return self


class Answer(Schema):
    value: int | None = Field(default=None, ge=0, le=100)
    comment: str = Field(default="", max_length=5000)


class AssessmentIn(Schema):
    source: str = Field(default="manual", min_length=1, max_length=200)
    external_id: str = Field(min_length=1, max_length=200)
    source_revision: str = Field(default="", max_length=200)
    laboratory_code: str = Field(min_length=1, max_length=60)
    instrument_code: str = Field(min_length=1, max_length=60)
    instrument_version: str = Field(min_length=1, max_length=40)
    assessment_date: date
    answers: dict[str, Answer] = Field(max_length=1000)
    reason: str = Field(default="", max_length=2000)


class AssessmentBatch(Schema):
    assessments: list[AssessmentIn] = Field(min_length=1, max_length=500)


class VersionIn(Schema):
    version: int = Field(ge=1)


class StateIn(VersionIn):
    status: str = Field(min_length=1, max_length=30)
    comment: str = Field(default="", max_length=5000)


class ActionIn(Schema):
    finding_id: str
    title: str = Field(min_length=3, max_length=300)
    description: str = Field(default="", max_length=10000)
    cause: str = Field(default="", max_length=5000)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    owner_id: str
    due_date: date


class ActionEdit(VersionIn):
    title: str = Field(min_length=3, max_length=300)
    description: str = Field(max_length=10000)
    cause: str = Field(max_length=5000)
    priority: Literal["low", "medium", "high", "critical"]
    owner_id: str
    due_date: date


class VerifyIn(VersionIn):
    result: Literal["effective", "ineffective"]
    comment: str = Field(min_length=5, max_length=5000)
    evidence_ids: list[str] = Field(min_length=1, max_length=100)


class DocumentIn(Schema):
    laboratory_id: str | None = None
    code: str = Field(min_length=1, max_length=60)
    title: str = Field(min_length=3, max_length=250)
    content: str = Field(min_length=20, max_length=100000)
    criterion_codes: list[str] = Field(default_factory=list, max_length=1000)


class RegisterIn(Schema):
    laboratory_id: str
    kind: Literal["risk", "occurrence", "competency", "equipment"]
    title: str = Field(min_length=3, max_length=250)
    description: str = Field(default="", max_length=10000)
    owner_id: str
    due_date: date
    details: dict = Field(default_factory=dict, max_length=30)


class AIRunIn(Schema):
    assessment_id: str


class Citation(Schema):
    source_id: str
    quote: str = Field(min_length=15, max_length=2000)


class Recommendation(Schema):
    title: str = Field(min_length=3, max_length=300)
    justification: str = Field(min_length=10, max_length=4000)
    priority: Literal["low", "medium", "high", "critical"]
    steps: list[str] = Field(min_length=1, max_length=10)
    completion_criterion: str = Field(min_length=10, max_length=2000)
    finding_ids: list[str] = Field(min_length=1, max_length=10)
    citations: list[Citation] = Field(min_length=1, max_length=10)


class RecommendationResult(Schema):
    summary: str = Field(min_length=3, max_length=5000)
    insufficient_evidence: bool
    recommendations: list[Recommendation] = Field(max_length=10)


class AcceptRecommendation(Schema):
    index: int = Field(ge=0, le=9)
    owner_id: str
    due_date: date
    title: str = Field(min_length=3, max_length=300)
    description: str = Field(min_length=5, max_length=10000)


class ODKIn(Schema):
    project_id: int = Field(ge=1)
    form_id: str = Field(min_length=1, max_length=200)
    stable_id_field: str = Field(min_length=1, max_length=200)
    laboratory_code_field: str = Field(min_length=1, max_length=200)
    assessment_date_field: str = Field(min_length=1, max_length=200)
    revision_field: str = Field(default="__system.updatedAt", max_length=200)
    instrument_code: str
    instrument_version: str
    criterion_fields: dict[str, str] = Field(min_length=1, max_length=1000)
