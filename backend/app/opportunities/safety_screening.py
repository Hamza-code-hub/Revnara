from dataclasses import dataclass
from urllib.parse import urlparse

from app.opportunities.models import SafetyScreeningStatus

# Deterministic, rule-based only (BE6.3) -- per Blueprint §6.1's
# "Deterministic Control, Probabilistic Intelligence", this is explicitly
# NOT a model call. These specific phrase/domain lists are illustrative
# starting points, not tuned against real historical scam data (none
# exists yet) -- see this sprint's Risks & Mitigations: ship flagged ->
# human review by default when uncertain, tune thresholds after pilot
# data arrives.
_SUSPICIOUS_PAYMENT_PHRASES = (
    "wire transfer only",
    "western union",
    "moneygram",
    "gift card",
    "pay upfront before work",
    "no contract needed",
    "cash only",
    "cryptocurrency only",
)

_URGENCY_PRESSURE_PHRASES = (
    "urgent, start today",
    "immediate start required",
    "today only",
    "must start immediately",
)

_KNOWN_BAD_DOMAINS = frozenset(
    {
        "totally-legit-jobs.example",
        "quick-cash-gigs.example",
    }
)


@dataclass(frozen=True)
class ScreeningResult:
    status: SafetyScreeningStatus
    flags: list[str]


def screen_opportunity(
    *,
    title: str,
    description: str | None,
    external_url: str | None,
    budget_min: float | None,
    budget_max: float | None,
) -> ScreeningResult:
    """Runs every deterministic heuristic and combines the result --
    `pending_screening` -> `screened_clear`/`screened_flagged` (BE6.3).
    Any single triggered heuristic flags the whole opportunity; flags are
    kept (not just a boolean) so a human reviewer sees exactly why.
    """
    flags: list[str] = []
    combined_text = f"{title} {description or ''}".lower()

    if any(phrase in combined_text for phrase in _SUSPICIOUS_PAYMENT_PHRASES):
        flags.append("suspicious_payment_terms")

    if any(phrase in combined_text for phrase in _URGENCY_PRESSURE_PHRASES):
        flags.append("urgency_pressure_language")

    if external_url:
        domain = urlparse(external_url).netloc.lower().removeprefix("www.")
        if domain in _KNOWN_BAD_DOMAINS:
            flags.append("known_bad_domain")

    if budget_min is not None and budget_max is not None and budget_min > budget_max:
        flags.append("invalid_budget_range")

    status = SafetyScreeningStatus.FLAGGED if flags else SafetyScreeningStatus.CLEAR
    return ScreeningResult(status=status, flags=flags)
