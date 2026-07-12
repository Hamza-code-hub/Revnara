from app.company.models import Skill
from app.opportunities.models import Opportunity


def opportunity_text(opportunity: Opportunity) -> str:
    """The combined title/description/requirements text that
    qualification.py and team_matching.py both scan for known skill
    names -- kept in one place so the two engines stay consistent about
    what "the opportunity's text" means."""
    combined = f"{opportunity.title} {opportunity.description or ''}"
    return f"{combined} {opportunity.requirements or ''}"


def detect_required_skills(text: str, tenant_skills: list[Skill]) -> list[Skill]:
    """Deterministic keyword match (same phrase-matching philosophy as
    safety_screening.py's v1 heuristics): a tenant skill is "required" by
    an opportunity if its name literally appears in the opportunity's
    text. This can only ever detect skills the tenant already has a name
    for in their own catalog -- it can't discover a skill the client
    wants that isn't in `skills` at all. That's a known v1 limitation,
    not an oversight: it's the same "flag for human judgement rather
    than guess" posture used throughout Sprint 6.
    """
    lowered = text.lower()
    return [skill for skill in tenant_skills if skill.name.lower() in lowered]
