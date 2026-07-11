import pytest
from pydantic import ValidationError

from app.company.schemas import (
    CaseStudyCreate,
    PortfolioItemCreate,
    SkillCreate,
    TeamMemberCreate,
)


def test_skill_create_rejects_an_empty_name() -> None:
    with pytest.raises(ValidationError):
        SkillCreate(name="")


def test_skill_create_accepts_a_valid_name() -> None:
    skill = SkillCreate(name="Flutter", category="Frontend")
    assert skill.name == "Flutter"


def test_team_member_create_rejects_a_negative_hourly_rate() -> None:
    with pytest.raises(ValidationError):
        TeamMemberCreate(name="Alex Rivera", hourly_rate=-10)


def test_team_member_create_rejects_an_empty_name() -> None:
    with pytest.raises(ValidationError):
        TeamMemberCreate(name="")


def test_team_member_create_rejects_availability_hours_over_a_week() -> None:
    with pytest.raises(ValidationError):
        TeamMemberCreate(name="Alex Rivera", weekly_availability_hours=200)


def test_team_member_create_accepts_valid_values() -> None:
    member = TeamMemberCreate(name="Alex Rivera", hourly_rate=95.0, weekly_availability_hours=30)
    assert member.hourly_rate == 95.0


def test_portfolio_item_create_rejects_an_empty_title() -> None:
    with pytest.raises(ValidationError):
        PortfolioItemCreate(title="")


def test_case_study_create_rejects_an_empty_title() -> None:
    with pytest.raises(ValidationError):
        CaseStudyCreate(title="")
