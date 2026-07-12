from app.opportunities.models import OpportunityStatus

# BE7.5: the legal pipeline moves. A human can always disqualify from any
# non-terminal stage (a deal can die at any point), but can only ever move
# forward one stage at a time otherwise -- no `intake` -> `won` jumps.
# `won`/`lost`/`disqualified` are terminal: nothing transitions out of them.
_FORWARD_TRANSITIONS: dict[OpportunityStatus, set[OpportunityStatus]] = {
    OpportunityStatus.INTAKE: {OpportunityStatus.SCREENING},
    OpportunityStatus.SCREENING: {OpportunityStatus.QUALIFYING},
    OpportunityStatus.QUALIFYING: {OpportunityStatus.QUALIFIED},
    OpportunityStatus.QUALIFIED: {OpportunityStatus.MATCHED},
    OpportunityStatus.MATCHED: {OpportunityStatus.PROPOSING},
    OpportunityStatus.PROPOSING: {OpportunityStatus.APPROVED},
    OpportunityStatus.APPROVED: {OpportunityStatus.SUBMITTED},
    OpportunityStatus.SUBMITTED: {OpportunityStatus.WON, OpportunityStatus.LOST},
    OpportunityStatus.WON: set(),
    OpportunityStatus.LOST: set(),
    OpportunityStatus.DISQUALIFIED: set(),
}

_TERMINAL_STATUSES = frozenset(
    {OpportunityStatus.WON, OpportunityStatus.LOST, OpportunityStatus.DISQUALIFIED}
)


def is_legal_transition(current: OpportunityStatus, new: OpportunityStatus) -> bool:
    if current in _TERMINAL_STATUSES:
        return False
    if new == OpportunityStatus.DISQUALIFIED:
        return True
    return new in _FORWARD_TRANSITIONS.get(current, set())
