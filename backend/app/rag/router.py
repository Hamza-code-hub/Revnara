import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.rag.embeddings import EmbeddingProvider, OpenAIEmbeddingProvider
from app.rag.retrieval import search
from app.rag.schemas import KnowledgeSearchRequest, KnowledgeSearchResultItem
from app.tenancy.context import TenantContext
from app.tenancy.middleware import resolve_tenant_context

router = APIRouter(tags=["rag"])


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    return OpenAIEmbeddingProvider(api_key=settings.model_provider_api_key)


def _check_tenant(organization_id: uuid.UUID, tenant: TenantContext) -> None:
    if organization_id != tenant.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch.")


@router.post(
    "/organizations/{organization_id}/knowledge/search",
    response_model=list[KnowledgeSearchResultItem],
)
async def search_knowledge(
    organization_id: uuid.UUID,
    payload: KnowledgeSearchRequest,
    tenant: TenantContext = Depends(resolve_tenant_context),
    db: AsyncSession = Depends(get_db_session),
    embedder: EmbeddingProvider = Depends(get_embedding_provider),
) -> list[KnowledgeSearchResultItem]:
    """FE5.1's debug-only "Company Brain search preview" widget calls this
    -- any active member can search (read access, same as listing company
    brain entities), the `company.manage` check only gates what's
    returned (retrieval.search's classification filter), not who can
    call this endpoint at all.
    """
    _check_tenant(organization_id, tenant)

    [query_embedding] = await embedder.embed([payload.query])
    results = await search(
        db,
        query_embedding=query_embedding,
        tenant_id=organization_id,
        actor_permissions=tenant.permissions,
        limit=payload.limit,
    )
    return [
        KnowledgeSearchResultItem(
            chunk_id=r.chunk_id,
            source_type=r.source_type,
            source_id=r.source_id,
            chunk_text=r.chunk_text,
            classification=r.classification,
            distance=r.distance,
        )
        for r in results
    ]
