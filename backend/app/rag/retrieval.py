import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.models import KnowledgeChunk
from app.tenancy.repository import scoped_to_tenant


@dataclass(frozen=True)
class SearchResult:
    chunk_id: uuid.UUID
    source_type: str
    source_id: uuid.UUID
    chunk_text: str
    classification: str | None
    distance: float


async def search(
    db: AsyncSession,
    *,
    query_embedding: list[float],
    tenant_id: uuid.UUID,
    workspace_id: uuid.UUID | None = None,
    actor_permissions: frozenset[str],
    limit: int = 10,
) -> list[SearchResult]:
    """Tenant- AND permission/classification-filtered vector similarity
    search (BE5.3, Blueprint §57's AV-002: filter by more than tenant
    alone). A caller without `company.manage` never sees a
    `confidential`-classified chunk, even within their own tenant --
    permission-level isolation, not just tenant-level.
    """
    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)

    stmt = scoped_to_tenant(
        select(KnowledgeChunk, distance.label("distance")), KnowledgeChunk, tenant_id
    )
    if workspace_id is not None:
        stmt = stmt.where(KnowledgeChunk.workspace_id == workspace_id)
    if "company.manage" not in actor_permissions:
        stmt = stmt.where(KnowledgeChunk.classification.is_distinct_from("confidential"))

    stmt = stmt.order_by(distance).limit(limit)

    result = await db.execute(stmt)
    return [
        SearchResult(
            chunk_id=chunk.id,
            source_type=chunk.source_type,
            source_id=chunk.source_id,
            chunk_text=chunk.chunk_text,
            classification=chunk.classification,
            distance=float(chunk_distance),
        )
        for chunk, chunk_distance in result.all()
    ]
