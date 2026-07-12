from app.opportunities.csv_import import parse_opportunities_csv


def test_valid_rows_parse_correctly() -> None:
    csv_content = (
        "title,description,budget_min,budget_max,budget_currency,client_name\n"
        "Website redesign,Rebuild the marketing site,5000,8000,USD,Acme Corp\n"
        "Data migration,,,,,\n"
    )
    result = parse_opportunities_csv(csv_content)

    assert result.errors == []
    assert len(result.rows) == 2
    first = result.rows[0]
    assert first.row_number == 2
    assert first.title == "Website redesign"
    assert first.description == "Rebuild the marketing site"
    assert first.budget_min == 5000.0
    assert first.budget_max == 8000.0
    assert first.budget_currency == "USD"
    assert first.client_name == "Acme Corp"

    second = result.rows[1]
    assert second.title == "Data migration"
    assert second.budget_min is None
    assert second.client_name is None


def test_missing_title_is_reported_per_row_not_fatal() -> None:
    csv_content = "title,description\nValid Row,Has a title\n,No title here\n"
    result = parse_opportunities_csv(csv_content)

    assert len(result.rows) == 1
    assert result.rows[0].title == "Valid Row"
    assert len(result.errors) == 1
    assert result.errors[0].row_number == 3
    assert "title is required" in result.errors[0].error


def test_invalid_budget_is_reported_per_row_not_fatal() -> None:
    csv_content = "title,budget_min\nGood row,1000\nBad row,not-a-number\n"
    result = parse_opportunities_csv(csv_content)

    assert len(result.rows) == 1
    assert result.rows[0].title == "Good row"
    assert len(result.errors) == 1
    assert result.errors[0].row_number == 3
    assert "budget_min must be a number" in result.errors[0].error


def test_missing_header_row_rejects_cleanly() -> None:
    result = parse_opportunities_csv("")

    assert result.rows == []
    assert len(result.errors) == 1
    assert "no header row" in result.errors[0].error


def test_missing_required_column_rejects_cleanly() -> None:
    result = parse_opportunities_csv("description\nsomething\n")

    assert result.rows == []
    assert len(result.errors) == 1
    assert "Missing required column" in result.errors[0].error
    assert "title" in result.errors[0].error


def test_whitespace_only_title_is_treated_as_missing() -> None:
    csv_content = "title\n   \n"
    result = parse_opportunities_csv(csv_content)

    assert result.rows == []
    assert len(result.errors) == 1
    assert "title is required" in result.errors[0].error
