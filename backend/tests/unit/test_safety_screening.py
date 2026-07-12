from app.opportunities.models import SafetyScreeningStatus
from app.opportunities.safety_screening import screen_opportunity


def test_clean_opportunity_is_screened_clear() -> None:
    result = screen_opportunity(
        title="Inventory Sync Platform Rebuild",
        description="Replace a legacy inventory sync job with a real-time platform.",
        external_url=None,
        budget_min=40000,
        budget_max=65000,
    )
    assert result.status == SafetyScreeningStatus.CLEAR
    assert result.flags == []


def test_suspicious_payment_phrase_is_flagged() -> None:
    result = screen_opportunity(
        title="Wire Transfer Only Required",
        description="Payment will be made via wire transfer only.",
        external_url=None,
        budget_min=None,
        budget_max=None,
    )
    assert result.status == SafetyScreeningStatus.FLAGGED
    assert result.flags == ["suspicious_payment_terms"]


def test_urgency_pressure_phrase_is_flagged() -> None:
    result = screen_opportunity(
        title="Immediate Start Required",
        description="We need someone who can start today only.",
        external_url=None,
        budget_min=None,
        budget_max=None,
    )
    assert result.status == SafetyScreeningStatus.FLAGGED
    assert result.flags == ["urgency_pressure_language"]


def test_known_bad_domain_is_flagged() -> None:
    result = screen_opportunity(
        title="Great opportunity",
        description="Standard project.",
        external_url="https://www.totally-legit-jobs.example/job/123",
        budget_min=None,
        budget_max=None,
    )
    assert result.status == SafetyScreeningStatus.FLAGGED
    assert result.flags == ["known_bad_domain"]


def test_ordinary_domain_is_not_flagged() -> None:
    result = screen_opportunity(
        title="Great opportunity",
        description="Standard project.",
        external_url="https://www.upwork.com/jobs/~123",
        budget_min=None,
        budget_max=None,
    )
    assert result.status == SafetyScreeningStatus.CLEAR
    assert result.flags == []


def test_invalid_budget_range_is_flagged() -> None:
    result = screen_opportunity(
        title="Odd budget",
        description="Standard project.",
        external_url=None,
        budget_min=10000,
        budget_max=5000,
    )
    assert result.status == SafetyScreeningStatus.FLAGGED
    assert result.flags == ["invalid_budget_range"]


def test_multiple_heuristics_all_flag_together() -> None:
    result = screen_opportunity(
        title="Urgent, Start Today",
        description="Pay via western union, cash only, gift card accepted.",
        external_url=None,
        budget_min=10000,
        budget_max=5000,
    )
    assert result.status == SafetyScreeningStatus.FLAGGED
    assert result.flags == [
        "suspicious_payment_terms",
        "urgency_pressure_language",
        "invalid_budget_range",
    ]


def test_matching_is_case_insensitive() -> None:
    result = screen_opportunity(
        title="WIRE TRANSFER ONLY",
        description=None,
        external_url=None,
        budget_min=None,
        budget_max=None,
    )
    assert result.status == SafetyScreeningStatus.FLAGGED
    assert result.flags == ["suspicious_payment_terms"]


def test_no_description_does_not_crash() -> None:
    result = screen_opportunity(
        title="Plain title",
        description=None,
        external_url=None,
        budget_min=None,
        budget_max=None,
    )
    assert result.status == SafetyScreeningStatus.CLEAR
