import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.opportunities.models import Client, Opportunity, OpportunityStatus


async def generate_research_brief(db: AsyncSession, *, tenant_id: uuid.UUID, client: Client) -> str:
    """BE6.5b: a deterministic aggregation, not an LLM agent -- Sprint 6
    runs before Sprint 8's model gateway exists, so this compiles a
    structured brief from permitted, already-available sources only: the
    client record itself and this tenant's own opportunity history with
    them. No browsing/scraping of any kind. Upgraded to a real
    synthesizing Research Agent in Sprint 8.5 once the model gateway
    exists (Blueprint §29 agent #4, §37 Client Research).
    """
    result = await db.execute(
        select(Opportunity)
        .where(Opportunity.tenant_id == tenant_id, Opportunity.client_id == client.id)
        .order_by(Opportunity.created_at.desc())
    )
    history = list(result.scalars().all())

    won = sum(1 for o in history if o.status == OpportunityStatus.WON)
    lost = sum(1 for o in history if o.status == OpportunityStatus.LOST)

    lines = [f"Client: {client.name}"]
    if client.industry:
        lines.append(f"Industry: {client.industry}")
    if client.region:
        lines.append(f"Region: {client.region}")
    if client.website:
        lines.append(f"Website: {client.website}")

    if history:
        plural = "y" if len(history) == 1 else "ies"
        lines.append(
            f"Prior engagement history: {len(history)} opportunit{plural} on file "
            f"({won} won, {lost} lost)."
        )
        for opportunity in history[:5]:
            # `.status` round-trips as a plain str once reloaded from the
            # DB (the column is a plain String, not a SQLAlchemy Enum), so
            # `.value` isn't always available -- OpportunityStatus is a
            # StrEnum, whose str() already equals its `.value` either way.
            lines.append(f"  - {opportunity.title} ({opportunity.status})")
    else:
        lines.append("No prior engagement history on file with this client.")

    return "\n".join(lines)
