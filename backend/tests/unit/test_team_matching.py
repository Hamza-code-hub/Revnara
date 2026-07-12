import uuid

from app.company.models import Skill, TeamMember
from app.opportunities.models import Opportunity
from app.opportunities.team_matching import match_team


def _opportunity(**overrides: object) -> Opportunity:
    defaults: dict[str, object] = {
        "title": "Website redesign",
        "description": "Needs Flutter and FastAPI expertise.",
        "requirements": None,
    }
    defaults.update(overrides)
    return Opportunity(**defaults)  # type: ignore[arg-type]


def _skill(name: str) -> Skill:
    return Skill(name=name)  # type: ignore[call-arg]


def _member(
    name: str, *, skills: list[Skill], is_active: bool = True, **overrides: object
) -> TeamMember:
    member = TeamMember(
        id=uuid.uuid4(), name=name, is_active=is_active, **overrides
    )  # type: ignore[arg-type]
    member.skills = skills
    return member


def test_no_detected_skills_returns_high_risk_with_no_recommendation() -> None:
    opportunity = _opportunity(description="Needs COBOL expertise.")
    result = match_team(opportunity=opportunity, tenant_skills=[], team_members=[])
    assert result.recommended_team_member_ids == []
    assert result.delivery_risk == "high"


def test_full_coverage_by_one_member_is_low_risk() -> None:
    flutter = _skill("Flutter")
    fastapi = _skill("FastAPI")
    opportunity = _opportunity()
    member = _member("Alex", skills=[flutter, fastapi])

    result = match_team(
        opportunity=opportunity, tenant_skills=[flutter, fastapi], team_members=[member]
    )
    assert result.recommended_team_member_ids == [member.id]
    assert result.delivery_risk == "low"
    assert result.gaps == []


def test_partial_coverage_is_medium_risk_with_gaps() -> None:
    flutter = _skill("Flutter")
    fastapi = _skill("FastAPI")
    opportunity = _opportunity()
    member = _member("Alex", skills=[flutter])

    result = match_team(
        opportunity=opportunity, tenant_skills=[flutter, fastapi], team_members=[member]
    )
    assert result.recommended_team_member_ids == [member.id]
    assert result.delivery_risk == "medium"
    assert result.gaps == ["FastAPI"]


def test_no_member_has_any_required_skill_is_high_risk() -> None:
    flutter = _skill("Flutter")
    fastapi = _skill("FastAPI")
    kubernetes = _skill("Kubernetes")
    opportunity = _opportunity()
    member = _member("Alex", skills=[kubernetes])

    result = match_team(
        opportunity=opportunity, tenant_skills=[flutter, fastapi, kubernetes], team_members=[member]
    )
    assert result.recommended_team_member_ids == []
    assert result.delivery_risk == "high"


def test_inactive_members_are_never_recommended() -> None:
    flutter = _skill("Flutter")
    opportunity = _opportunity(description="Needs Flutter expertise.")
    member = _member("Alex", skills=[flutter], is_active=False)

    result = match_team(opportunity=opportunity, tenant_skills=[flutter], team_members=[member])
    assert result.recommended_team_member_ids == []


def test_recommendation_is_capped_and_sorted_by_skill_fit() -> None:
    flutter = _skill("Flutter")
    fastapi = _skill("FastAPI")
    opportunity = _opportunity()

    full_fit = _member("Full Fit", skills=[flutter, fastapi])
    half_fit_a = _member("Half Fit A", skills=[flutter])
    half_fit_b = _member("Half Fit B", skills=[fastapi])
    no_fit = _member("No Fit", skills=[])

    result = match_team(
        opportunity=opportunity,
        tenant_skills=[flutter, fastapi],
        team_members=[half_fit_a, no_fit, full_fit, half_fit_b],
    )
    assert result.recommended_team_member_ids[0] == full_fit.id
    assert no_fit.id not in result.recommended_team_member_ids
    assert len(result.recommended_team_member_ids) == 3


def test_estimated_cost_uses_hourly_rate_and_availability_cap() -> None:
    flutter = _skill("Flutter")
    opportunity = _opportunity(description="Needs Flutter expertise.")
    member = _member(
        "Alex", skills=[flutter], hourly_rate=100, currency="USD", weekly_availability_hours=50
    )

    result = match_team(opportunity=opportunity, tenant_skills=[flutter], team_members=[member])
    # Capped at 40 hours/week even though availability is 50.
    assert result.estimated_weekly_cost == 4000.0
    assert result.estimated_cost_currency == "USD"


def test_no_rated_members_leaves_cost_unset() -> None:
    flutter = _skill("Flutter")
    opportunity = _opportunity(description="Needs Flutter expertise.")
    member = _member("Alex", skills=[flutter], hourly_rate=None)

    result = match_team(opportunity=opportunity, tenant_skills=[flutter], team_members=[member])
    assert result.estimated_weekly_cost is None
