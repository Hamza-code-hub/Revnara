import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.organizations.models import MemberStatus


class OrganizationCreate(BaseModel):
    name: str


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    # Sprint 4 (Company Brain) profile fields -- see
    # app/organizations/models.py's Organization docstring comment.
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    founded_year: int | None = None


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    created_at: datetime


class OrganizationCreateResponse(BaseModel):
    organization: OrganizationRead
    workspace: WorkspaceRead


class MembershipRead(BaseModel):
    organization_id: uuid.UUID
    organization_name: str
    role_name: str
    workspace_id: uuid.UUID | None
    status: MemberStatus


class MeResponse(BaseModel):
    user_id: uuid.UUID
    email: str | None
    memberships: list[MembershipRead]


class MemberRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    email: str | None
    role_name: str
    status: MemberStatus
    invited_email: str | None


class InvitationCreate(BaseModel):
    email: EmailStr
    role_name: str


class MemberRoleUpdate(BaseModel):
    role_name: str
