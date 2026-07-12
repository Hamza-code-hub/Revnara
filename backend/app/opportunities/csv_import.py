import csv
import io
from dataclasses import dataclass

REQUIRED_COLUMNS = frozenset({"title"})


@dataclass(frozen=True)
class ParsedRow:
    row_number: int
    title: str
    description: str | None
    requirements: str | None
    budget_min: float | None
    budget_max: float | None
    budget_currency: str | None
    client_name: str | None


@dataclass(frozen=True)
class RowError:
    row_number: int
    error: str


@dataclass(frozen=True)
class CsvParseResult:
    rows: list[ParsedRow]
    errors: list[RowError]


def _parse_optional_float(raw_row: dict[str, str], field_name: str) -> float | None:
    value = (raw_row.get(field_name) or "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number, got {value!r}") from exc


def parse_opportunities_csv(content: str) -> CsvParseResult:
    """BE6.4: schema check, per-row error reporting, partial-success
    handling -- a malformed row is reported and skipped, never silently
    dropped and never failing rows that parsed fine. A fully malformed
    file (no header, or missing a required column) rejects cleanly with
    zero rows imported, rather than guessing at a best-effort partial
    read.
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        return CsvParseResult(
            rows=[], errors=[RowError(row_number=0, error="CSV file has no header row")]
        )

    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        return CsvParseResult(
            rows=[],
            errors=[
                RowError(
                    row_number=0,
                    error=f"Missing required column(s): {', '.join(sorted(missing))}",
                )
            ],
        )

    rows: list[ParsedRow] = []
    errors: list[RowError] = []

    for index, raw_row in enumerate(reader, start=2):  # row 1 is the header
        title = (raw_row.get("title") or "").strip()
        if not title:
            errors.append(RowError(row_number=index, error="title is required"))
            continue

        try:
            budget_min = _parse_optional_float(raw_row, "budget_min")
            budget_max = _parse_optional_float(raw_row, "budget_max")
        except ValueError as exc:
            errors.append(RowError(row_number=index, error=str(exc)))
            continue

        rows.append(
            ParsedRow(
                row_number=index,
                title=title,
                description=(raw_row.get("description") or "").strip() or None,
                requirements=(raw_row.get("requirements") or "").strip() or None,
                budget_min=budget_min,
                budget_max=budget_max,
                budget_currency=(raw_row.get("budget_currency") or "").strip() or None,
                client_name=(raw_row.get("client_name") or "").strip() or None,
            )
        )

    return CsvParseResult(rows=rows, errors=errors)
