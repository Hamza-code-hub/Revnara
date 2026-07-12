import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.opportunities.models import OpportunityStatus, SafetyScreeningStatus


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    website: str | None
    industry: str | None
    region: str | None
    research_brief: str | None
    research_generated_at: datetime | None


class ContactCreate(BaseModel):
    name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None
    title: str | None = None


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    name: str
    email: str | None
    phone: str | None
    title: str | None


class OpportunityCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    requirements: str | None = None
    budget_min: float | None = Field(default=None, ge=0)
    budget_max: float | None = Field(default=None, ge=0)
    budget_currency: str | None = None
    client_name: str | None = None


class OpportunityImportLinkCreate(BaseModel):
    """FE6.3: the human-native Upwork-link intake -- stores/displays the
    link only. No code path here ever calls an Upwork API or automates a
    browser (BE6.2's note, verified by a negative test)."""

    url: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    budget_min: float | None = Field(default=None, ge=0)
    budget_max: float | None = Field(default=None, ge=0)
    budget_currency: str | None = None
    client_name: str | None = None


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID | None
    source_id: uuid.UUID
    title: str
    description: str | None
    requirements: str | None
    budget_min: float | None
    budget_max: float | None
    budget_currency: str | None
    status: OpportunityStatus
    safety_screening_status: SafetyScreeningStatus
    safety_screening_flags: list[str] | None


class CsvImportRowError(BaseModel):
    row_number: int
    error: str


class CsvImportResult(BaseModel):
    created: list[OpportunityRead]
    errors: list[CsvImportRowError]


# Sprint 7 (Qualification, Team Matching & Pipeline UI) schemas.


class QualificationResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    opportunity_id: uuid.UUID
    score: int
    reasons: list[str]
    evidence: list[str]
    missing_info: list[str]


class TeamMatchResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    opportunity_id: uuid.UUID
    recommended_team_member_ids: list[uuid.UUID]
    delivery_risk: str
    estimated_weekly_cost: float | None
    estimated_cost_currency: str | None
    gaps: list[str]
    reasons: list[str]
    evidence: list[str]


class OpportunityStatusUpdate(BaseModel):
    status: OpportunityStatus


class QualificationOverride(BaseModel):
    """BE7.6: overriding a score always requires a stated reason -- there
    is no endpoint shape that allows a bare silent edit."""

    score: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1)


class TeamMatchOverride(BaseModel):
    recommended_team_member_ids: list[uuid.UUID]
    reason: str = Field(min_length=1)
