from app.company.models import Skill
from app.opportunities.models import Opportunity
from app.opportunities.qualification import qualify_opportunity


def _opportunity(**overrides: object) -> Opportunity:
    defaults: dict[str, object] = {
        "title": "Website redesign",
        "description": "Rebuild the marketing site.",
        "requirements": None,
        "budget_min": None,
        "budget_max": None,
    }
    defaults.update(overrides)
    return Opportunity(**defaults)  # type: ignore[arg-type]


def _skill(name: str) -> Skill:
    return Skill(name=name)  # type: ignore[call-arg]


def test_full_budget_range_scores_full_budget_points() -> None:
    opportunity = _opportunity(budget_min=1000, budget_max=2000)
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=[])
    assert "Full budget range specified." in result.reasons
    assert not any("budget" in m.lower() for m in result.missing_info)


def test_partial_budget_scores_half_points_and_flags_missing_info() -> None:
    opportunity = _opportunity(budget_min=1000, budget_max=None)
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=[])
    assert any("partial" in r.lower() for r in result.reasons)
    assert any("budget" in m.lower() for m in result.missing_info)


def test_no_budget_scores_zero_and_flags_missing_info() -> None:
    opportunity = _opportunity()
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=[])
    assert "No budget information provided." in result.missing_info


def test_no_skills_catalog_flags_missing_info() -> None:
    opportunity = _opportunity(description="Needs Flutter and FastAPI expertise.")
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=[])
    assert any("no skills catalog" in m.lower() for m in result.missing_info)


def test_detected_skills_score_full_skill_points_with_evidence() -> None:
    opportunity = _opportunity(description="Needs Flutter and FastAPI expertise.")
    skills = [_skill("Flutter"), _skill("FastAPI"), _skill("Kubernetes")]
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=skills)
    assert any("Detected skills: FastAPI, Flutter" in e for e in result.evidence)
    assert not any("skills" in m.lower() and "no known" in m.lower() for m in result.missing_info)


def test_no_matching_skills_detected_flags_missing_info() -> None:
    opportunity = _opportunity(description="Needs COBOL expertise.")
    skills = [_skill("Flutter"), _skill("FastAPI")]
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=skills)
    assert any("no known skills detected" in m.lower() for m in result.missing_info)


def test_urgent_timeline_language_lowers_score_without_missing_info() -> None:
    opportunity = _opportunity(description="This is urgent, must start today only.")
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=[])
    assert any("urgent timeline" in r.lower() for r in result.reasons)
    # Urgency is a known negative signal, not an information gap.
    assert not any("timeline" in m.lower() for m in result.missing_info)


def test_no_urgency_scores_full_timeline_points() -> None:
    opportunity = _opportunity(description="Standard delivery timeline expected.")
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=[])
    assert "No urgent timeline pressure detected." in result.reasons


def test_best_case_scores_one_hundred() -> None:
    opportunity = _opportunity(
        description="Needs Flutter expertise.", budget_min=1000, budget_max=2000
    )
    skills = [_skill("Flutter")]
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=skills)
    assert result.score == 100


def test_worst_case_scores_zero() -> None:
    opportunity = _opportunity(description="This is urgent, must start today only.")
    result = qualify_opportunity(opportunity=opportunity, tenant_skills=[])
    assert result.score == 0
