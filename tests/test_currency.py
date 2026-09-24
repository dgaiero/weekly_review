import json

import pytest
from pydantic import ValidationError

from team_status.models import Effort, ReportEffort, WeeklyReport
from team_status.reports.email import email_html, email_markdown
from team_status.reports.slides import slides_markdown


def effort(amount=1000, **metadata):
    return Effort(
        schema_version=1,
        id="test",
        name="Test",
        status="proposed",
        lead={"name": "Lead"},
        dates={},
        funding=[{"source": "Test", "amount": amount}],
        **metadata,
    )


@pytest.mark.parametrize("currencies", [({}, "USD"), ({"currency": "EUR"}, "EUR")])
def test_currency_survives_json_and_labels_all_reports(currencies):
    metadata, code = currencies
    report = WeeklyReport(
        week="2026-W39", warnings=[], efforts=[ReportEffort(effort=effort(**metadata))]
    )
    assert json.loads(report.model_dump_json())["efforts"][0]["effort"]["currency"] == code
    for output in (email_markdown(report), slides_markdown(report)):
        assert f"Total funding: 1,000 {code}" in output
        assert f"1,000 {code}" in email_html(output)
    assert f"- Funding: 1,000 {code}" in slides_markdown(report)


def test_portfolio_totals_group_matching_currencies():
    report = WeeklyReport(
        week="2026-W39",
        warnings=[],
        efforts=[
            ReportEffort(effort=effort(1000)),
            ReportEffort(effort=effort(2000, currency="EUR")),
            ReportEffort(effort=effort(3000, currency="USD")),
        ],
    )
    for output in (email_markdown(report), slides_markdown(report)):
        totals = [line for line in output.splitlines() if line.startswith("- Total funding:")]
        assert totals == ["- Total funding: 2,000 EUR", "- Total funding: 4,000 USD"]


def test_empty_portfolio_displays_zero_usd():
    report = WeeklyReport(week="2026-W39", warnings=[], efforts=[])
    assert "Total funding: 0 USD" in email_markdown(report)
    assert "Total funding: 0 USD" in slides_markdown(report)


@pytest.mark.parametrize("currency", ["", "US", "USDD", "$", "usd", "123", None])
def test_malformed_currency_is_rejected(currency):
    with pytest.raises(ValidationError, match="currency"):
        effort(currency=currency)
