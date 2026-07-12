import uuid
from dataclasses import dataclass, field

from app.company.models import Skill, TeamMember
from app.opportunities.models import Opportunity
from app.opportunities.skill_detection import detect_required_skills, opportunity_text

_MAX_RECOMMENDED_MEMBERS = 3
_DEFAULT_WEEKLY_HOURS_CAP = 40


@dataclass(frozen=True)
class TeamMatchCandidate:
    team_member_id: uuid.UUID
    name: str
    skill_fit: float
    matched_skill_names: list[str]


@dataclass(frozen=True)
class TeamMatchResultData:
    recommended_team_member_ids: list[uuid.UUID]
    delivery_risk: str
    estimated_weekly_cost: float | None
    estimated_cost_currency: str | None
    gaps: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


def match_team(
    *, opportunity: Opportunity, tenant_skills: list[Skill], team_members: list[TeamMember]
) -> TeamMatchResultData:
    """BE7.3: matches active team members' skills against the same
    deterministic skill-detection used by qualification.py, computes a
    per-candidate skill-fit ratio, and derives delivery risk from whether
    every detected required skill is actually covered by the recommended
    team -- never a hidden/opaque "best guess," always traceable to
    which skills matched which members (Blueprint §38/§69).
    """
    required_skills = detect_required_skills(opportunity_text(opportunity), tenant_skills)

    if not required_skills:
        return TeamMatchResultData(
            recommended_team_member_ids=[],
            delivery_risk="high",
            estimated_weekly_cost=None,
            estimated_cost_currency=None,
            gaps=[],
            reasons=["No required skills could be detected from the opportunity's text."],
            evidence=[],
        )

    required_skill_names = {skill.name for skill in required_skills}

    candidates: list[TeamMatchCandidate] = []
    for member in team_members:
        if not member.is_active:
            continue
        member_skill_names = {skill.name for skill in member.skills}
        matched = sorted(required_skill_names & member_skill_names)
        if matched:
            candidates.append(
                TeamMatchCandidate(
                    team_member_id=member.id,
                    name=member.name,
                    skill_fit=len(matched) / len(required_skill_names),
                    matched_skill_names=matched,
                )
            )

    candidates.sort(key=lambda c: c.skill_fit, reverse=True)
    recommended = candidates[:_MAX_RECOMMENDED_MEMBERS]

    covered_skill_names = {name for c in recommended for name in c.matched_skill_names}
    gaps = sorted(required_skill_names - covered_skill_names)

    if not recommended:
        delivery_risk = "high"
    elif gaps:
        delivery_risk = "medium"
    else:
        delivery_risk = "low"

    recommended_ids = {c.team_member_id for c in recommended}
    rated_members = [
        member
        for member in team_members
        if member.id in recommended_ids and member.hourly_rate is not None
    ]
    estimated_weekly_cost: float | None = None
    estimated_cost_currency: str | None = None
    if rated_members:
        total_cost = 0.0
        for member in rated_members:
            hourly_rate = member.hourly_rate
            if hourly_rate is None:
                continue
            weekly_hours = min(
                member.weekly_availability_hours or _DEFAULT_WEEKLY_HOURS_CAP,
                _DEFAULT_WEEKLY_HOURS_CAP,
            )
            total_cost += float(hourly_rate) * weekly_hours
        estimated_weekly_cost = total_cost
        estimated_cost_currency = next((m.currency for m in rated_members if m.currency), None)

    reasons = [f"Required skills detected: {', '.join(sorted(required_skill_names))}."]
    if recommended:
        reasons.append(
            f"Recommended {len(recommended)} team member(s) covering "
            f"{len(covered_skill_names)}/{len(required_skill_names)} required skill(s)."
        )
    else:
        reasons.append("No active team member has any of the required skills.")
    if gaps:
        reasons.append(f"Skill gap(s) with no team member coverage: {', '.join(gaps)}.")

    evidence = [f"{c.name}: matched {', '.join(c.matched_skill_names)}" for c in recommended]

    return TeamMatchResultData(
        recommended_team_member_ids=[c.team_member_id for c in recommended],
        delivery_risk=delivery_risk,
        estimated_weekly_cost=estimated_weekly_cost,
        estimated_cost_currency=estimated_cost_currency,
        gaps=gaps,
        reasons=reasons,
        evidence=evidence,
    )
