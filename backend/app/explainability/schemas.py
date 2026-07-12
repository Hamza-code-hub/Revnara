import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ExplainabilityRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    decision: str
    inputs: dict[str, Any]
    evidence: list[str]
    rules_applied: list[str]
    confidence: float
    missing_data: list[str]
    created_at: datetime


class OverrideRecordRead(BaseModel):
    """FE7.2b: what powers the opportunity detail view's "adjusted by
    [person]" indicator -- `created_by`/`created_at` are the actor and
    timestamp (see OverrideRecord's docstring for why there's no
    separate actor column)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    field: str
    original_value: Any
    new_value: Any
    reason: str
    created_by: uuid.UUID | None
    created_at: datetime
