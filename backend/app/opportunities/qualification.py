from dataclasses import dataclass, field

from app.company.models import Skill
from app.opportunities.models import Opportunity
from app.opportunities.skill_detection import detect_required_skills, opportunity_text

# Deterministic, rule-based scoring (BE7.1) per Blueprint §38 -- explicitly
# not a model call, same "Deterministic Control, Probabilistic
# Intelligence" posture as Sprint 6's safety_screening.py. These phrase
# lists and point weights are illustrative starting points, tuned further
# once real historical qualification/override data exists (Sprint 25's
# learning loop).
_URGENCY_PHRASES = (
    "asap",
    "urgent",
    "immediately",
    "within 24 hours",
    "start today",
    "rush",
)

_BUDGET_POINTS = 40
_SKILL_POINTS = 40
_TIMELINE_POINTS = 20


@dataclass(frozen=True)
class QualificationScore:
    score: int
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    missing_info: list[str] = field(default_factory=list)


def _score_budget(opportunity: Opportunity) -> tuple[int, list[str], list[str], list[str]]:
    reasons: list[str] = []
    evidence: list[str] = []
    missing_info: list[str] = []

    has_min = opportunity.budget_min is not None
    has_max = opportunity.budget_max is not None

    if has_min and has_max:
        points = _BUDGET_POINTS
        reasons.append("Full budget range specified.")
        currency = opportunity.budget_currency or ""
        evidence.append(
            f"Budget: {currency} {opportunity.budget_min}-{opportunity.budget_max}".strip()
        )
    elif has_min or has_max:
        points = _BUDGET_POINTS // 2
        reasons.append("Only partial budget information specified.")
        missing_info.append("Budget range is incomplete (only one of min/max given).")
    else:
        points = 0
        reasons.append("No budget information specified.")
        missing_info.append("No budget information provided.")

    return points, reasons, evidence, missing_info


def _score_skills(
    opportunity: Opportunity, tenant_skills: list[Skill]
) -> tuple[int, list[str], list[str], list[str]]:
    reasons: list[str] = []
    evidence: list[str] = []
    missing_info: list[str] = []

    if not tenant_skills:
        missing_info.append("No skills catalog defined for this organization yet.")
        reasons.append("Cannot assess skill fit -- no skills catalog on file.")
        return 0, reasons, evidence, missing_info

    detected = detect_required_skills(opportunity_text(opportunity), tenant_skills)

    if not detected:
        missing_info.append(
            "No known skills detected in the opportunity's text -- may need manual skill tagging."
        )
        reasons.append("No matching skills detected in opportunity description/requirements.")
        return 0, reasons, evidence, missing_info

    reasons.append(f"Detected {len(detected)} known skill(s) relevant to this opportunity.")
    evidence.append(f"Detected skills: {', '.join(sorted(s.name for s in detected))}")
    return _SKILL_POINTS, reasons, evidence, missing_info


def _score_timeline(opportunity: Opportunity) -> tuple[int, list[str], list[str]]:
    combined_text = opportunity_text(opportunity).lower()
    if any(phrase in combined_text for phrase in _URGENCY_PHRASES):
        return (
            0,
            ["Urgent timeline language detected -- may strain delivery capacity."],
            ["Urgency phrase detected in opportunity text."],
        )
    return _TIMELINE_POINTS, ["No urgent timeline pressure detected."], []


def qualify_opportunity(
    *, opportunity: Opportunity, tenant_skills: list[Skill]
) -> QualificationScore:
    """BE7.1: combines three independent, explicit rule components into a
    single 0-100 score, always paired with reasons/evidence/missing-info
    so the result is a *recommendation a human can inspect*, never an
    opaque number (Blueprint §38, §69 explainability)."""
    budget_points, budget_reasons, budget_evidence, budget_missing = _score_budget(opportunity)
    skill_points, skill_reasons, skill_evidence, skill_missing = _score_skills(
        opportunity, tenant_skills
    )
    timeline_points, timeline_reasons, timeline_evidence = _score_timeline(opportunity)

    return QualificationScore(
        score=budget_points + skill_points + timeline_points,
        reasons=[*budget_reasons, *skill_reasons, *timeline_reasons],
        evidence=[*budget_evidence, *skill_evidence, *timeline_evidence],
        missing_info=[*budget_missing, *skill_missing],
    )
