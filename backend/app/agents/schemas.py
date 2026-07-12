import uuid

from pydantic import BaseModel

# Message shape per docs/Revnara_Implementation_Plan.md §11 and DB8.2:
# references + task input text only -- no prompts (the agent's system
# prompt is built fresh from its AgentDefinition, never carried in the
# message) or secrets. `task_input` is legitimate task content, the same
# exception app/rag/schemas.py's EmbeddingTask makes for chunk_text.


class AgentTask(BaseModel):
    tenant_id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    task_id: uuid.UUID
    agent_id: str
    task_input: str
    query: str
    idempotency_key: str
    created_by: uuid.UUID | None = None
