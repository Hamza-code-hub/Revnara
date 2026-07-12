import pytest

from app.opportunities.models import OpportunityStatus
from app.opportunities.pipeline import is_legal_transition


@pytest.mark.parametrize(
    ("current", "new"),
    [
        (OpportunityStatus.INTAKE, OpportunityStatus.SCREENING),
        (OpportunityStatus.SCREENING, OpportunityStatus.QUALIFYING),
        (OpportunityStatus.QUALIFYING, OpportunityStatus.QUALIFIED),
        (OpportunityStatus.QUALIFIED, OpportunityStatus.MATCHED),
        (OpportunityStatus.MATCHED, OpportunityStatus.PROPOSING),
        (OpportunityStatus.PROPOSING, OpportunityStatus.APPROVED),
        (OpportunityStatus.APPROVED, OpportunityStatus.SUBMITTED),
        (OpportunityStatus.SUBMITTED, OpportunityStatus.WON),
        (OpportunityStatus.SUBMITTED, OpportunityStatus.LOST),
    ],
)
def test_legal_forward_transitions(current: OpportunityStatus, new: OpportunityStatus) -> None:
    assert is_legal_transition(current, new) is True


@pytest.mark.parametrize(
    "current",
    [
        OpportunityStatus.INTAKE,
        OpportunityStatus.SCREENING,
        OpportunityStatus.QUALIFYING,
        OpportunityStatus.QUALIFIED,
        OpportunityStatus.MATCHED,
        OpportunityStatus.PROPOSING,
        OpportunityStatus.APPROVED,
        OpportunityStatus.SUBMITTED,
    ],
)
def test_can_disqualify_from_any_non_terminal_stage(current: OpportunityStatus) -> None:
    assert is_legal_transition(current, OpportunityStatus.DISQUALIFIED) is True


@pytest.mark.parametrize(
    "terminal",
    [OpportunityStatus.WON, OpportunityStatus.LOST, OpportunityStatus.DISQUALIFIED],
)
def test_terminal_statuses_have_no_way_out(terminal: OpportunityStatus) -> None:
    for candidate in OpportunityStatus:
        assert is_legal_transition(terminal, candidate) is False


def test_cannot_skip_stages() -> None:
    assert is_legal_transition(OpportunityStatus.INTAKE, OpportunityStatus.WON) is False
    assert is_legal_transition(OpportunityStatus.SCREENING, OpportunityStatus.QUALIFIED) is False
    assert is_legal_transition(OpportunityStatus.QUALIFIED, OpportunityStatus.SUBMITTED) is False


def test_cannot_move_backward() -> None:
    assert is_legal_transition(OpportunityStatus.QUALIFIED, OpportunityStatus.SCREENING) is False
    assert is_legal_transition(OpportunityStatus.MATCHED, OpportunityStatus.QUALIFYING) is False
