import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillCreate(BaseModel):
    name: str = Field(min_length=1)
    category: str | None = None


class SkillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    category: str | None = None


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str | None


class TeamMemberCreate(BaseModel):
    name: str = Field(min_length=1)
    title: str | None = None
    email: str | None = None
    bio: str | None = None
    hourly_rate: float | None = Field(default=None, ge=0)
    currency: str | None = None
    weekly_availability_hours: int | None = Field(default=None, ge=0, le=168)
    skill_ids: list[uuid.UUID] = []


class TeamMemberUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    title: str | None = None
    email: str | None = None
    bio: str | None = None
    hourly_rate: float | None = Field(default=None, ge=0)
    currency: str | None = None
    weekly_availability_hours: int | None = Field(default=None, ge=0, le=168)
    is_active: bool | None = None
    skill_ids: list[uuid.UUID] | None = None


class TeamMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    title: str | None
    email: str | None
    bio: str | None
    hourly_rate: float | None
    currency: str | None
    weekly_availability_hours: int | None
    is_active: bool
    skills: list[SkillRead] = []


class PortfolioItemCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    client_name: str | None = None
    technologies: str | None = None
    project_url: str | None = None
    completed_at: datetime | None = None
    classification: str | None = None


class PortfolioItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    client_name: str | None = None
    technologies: str | None = None
    project_url: str | None = None
    completed_at: datetime | None = None
    classification: str | None = None


class PortfolioItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    client_name: str | None
    technologies: str | None
    project_url: str | None
    completed_at: datetime | None
    classification: str | None


class CaseStudyCreate(BaseModel):
    portfolio_item_id: uuid.UUID | None = None
    title: str = Field(min_length=1)
    summary: str | None = None
    content: str | None = None
    outcome_metrics: str | None = None
    classification: str | None = None


class CaseStudyUpdate(BaseModel):
    portfolio_item_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=1)
    summary: str | None = None
    content: str | None = None
    outcome_metrics: str | None = None
    classification: str | None = None


class CaseStudyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    portfolio_item_id: uuid.UUID | None
    title: str
    summary: str | None
    content: str | None
    outcome_metrics: str | None
    classification: str | None


class OrganizationProfileUpdate(BaseModel):
    """PATCH body for the company-profile fields living on Organization
    itself -- see app/organizations/models.py's Sprint 4 comment for why
    there's no separate company_profiles table."""

    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    founded_year: int | None = None
