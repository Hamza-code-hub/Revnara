import uuid

from pydantic import BaseModel

# Message shape per docs/Revnara_Implementation_Plan.md §11: tenant_id,
# workspace_id, task_id, task_type, resource_id, idempotency_key -- no
# full documents/secrets/credentials in the message. EmbeddingTask is the
# one exception that carries chunk_text (BE5.4 permits this: it's the
# already-extracted, already-chunked *content* to embed, not a secret or
# a full raw document).


class DocumentTask(BaseModel):
    tenant_id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    task_id: uuid.UUID
    task_type: str = "parse_document"
    resource_id: uuid.UUID  # files.id
    idempotency_key: str


class EmbeddingTask(BaseModel):
    tenant_id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    task_id: uuid.UUID
    task_type: str = "embed_chunk"
    resource_id: uuid.UUID  # the source row's id (file/portfolio_item/case_study)
    idempotency_key: str
    source_type: str
    chunk_index: int
    chunk_text: str
    classification: str | None = None


class KnowledgeSearchRequest(BaseModel):
    query: str
    limit: int = 10


class KnowledgeSearchResultItem(BaseModel):
    chunk_id: uuid.UUID
    source_type: str
    source_id: uuid.UUID
    chunk_text: str
    classification: str | None
    distance: float
