from pathlib import Path

from team_status.reports.summary import build_report
from team_status.repository import load_repository


def example_report(week="2026-W39"):
    return build_report(load_repository(Path("examples"), week), week)


def test_email_preserves_updates_and_renders_markdown():
    from team_status.reports.email import email_html, email_markdown

    report = example_report()
    markdown = email_markdown(report)
    assert "Completed System A integration." in markdown
    assert "Hardware delivery delayed two weeks." in markdown
    html = email_html(markdown)
    assert "<li" in html
    assert "style=" in html
    assert "2026-W39" in html


def test_email_distinguishes_missing_and_empty_updates():
    from team_status.reports.email import email_markdown

    report = example_report("2026-W40")
    assert "No update submitted for 2026-W40" in email_markdown(report)
    report = example_report()
    report.efforts[0].update.sections["Accomplishments"] = ""
    assert "Not provided." in email_markdown(report)


def test_email_does_not_interpret_metadata_as_markup_or_execute_html():
    from team_status.reports.email import email_html, email_markdown

    report = example_report()
    report.efforts[0].effort.name = "<script>alert(1)</script> **Alpha**"
    report.efforts[0].update.sections["Progress Overview"] = (
        "<script>alert(2)</script> [bad](javascript:alert(3))"
    )
    html = email_html(email_markdown(report))
    assert "<script>" not in html
    assert 'href="javascript:' not in html
    assert "<strong>Alpha</strong>" not in html
    assert "&lt;script&gt;" in html


def test_slides_include_metadata_and_all_sections():
    from team_status.reports.slides import slides_markdown

    result = slides_markdown(example_report())
    assert result.startswith("---\nmarp: true\n")
    assert "Jane Smith" in result
    assert "350,000" in result
    assert "Completed System A integration." in result
    assert "Help / Decisions Needed" in result


def test_slides_paginate_without_dropping_bullets():
    from team_status.reports.slides import slides_markdown

    report = example_report()
    report.efforts[0].update.sections["Accomplishments"] = "\n".join(
        f"- Completed item {i}: " + "useful detail " * 7 for i in range(30)
    )
    result = slides_markdown(report)
    assert "continued" in result
    for i in range(30):
        assert f"Completed item {i}:" in result


def test_authored_separators_and_comments_cannot_control_slides():
    from team_status.reports.slides import slides_markdown

    report = example_report()
    report.efforts[0].update.sections["Accomplishments"] = (
        "First\n\n---\n\n<!-- _backgroundColor: red -->\n\nLast"
    )
    result = slides_markdown(report)
    assert "<!-- _backgroundColor" not in result
    assert "First\n\n---" not in result


def test_oversized_slide_block_fails_with_actionable_error():
    import pytest

    from team_status.reports.slides import slides_markdown

    report = example_report()
    report.efforts[0].update.sections["Progress Overview"] = "Detail " * 600
    with pytest.raises(ValueError, match="split"):
        slides_markdown(report)
