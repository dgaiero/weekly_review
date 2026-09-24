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
    report.efforts[0].updates[0].sections["Accomplishments"] = ""
    assert "Not provided." in email_markdown(report)


def test_email_does_not_interpret_metadata_as_markup_or_execute_html():
    from team_status.reports.email import email_html, email_markdown

    report = example_report()
    report.efforts[0].effort.name = "<script>alert(1)</script> **Alpha**"
    report.efforts[0].updates[0].sections["Progress Overview"] = (
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
    report.efforts[0].updates[0].sections["Accomplishments"] = "\n".join(
        f"- Completed item {i}: " + "useful detail " * 7 for i in range(30)
    )
    result = slides_markdown(report)
    assert "continued" in result
    for i in range(30):
        assert f"Completed item {i}:" in result


def test_authored_separators_and_comments_cannot_control_slides():
    from team_status.reports.slides import slides_markdown

    report = example_report()
    report.efforts[0].updates[0].sections["Accomplishments"] = (
        "First\n\n---\n\n<!-- _backgroundColor: red -->\n\nLast"
    )
    result = slides_markdown(report)
    assert "<!-- _backgroundColor" not in result
    assert "First\n\n---" not in result


def test_oversized_slide_block_fails_with_actionable_error():
    import pytest

    from team_status.reports.slides import slides_markdown

    report = example_report()
    report.efforts[0].updates[0].sections["Progress Overview"] = "Detail " * 600
    with pytest.raises(ValueError, match="split"):
        slides_markdown(report)


def attributed_report():
    from team_status.models import Effort, ReportEffort, WeeklyReport, WeeklyStatus
    from team_status.status import SECTIONS

    effort = Effort(
        schema_version=1,
        id="test",
        name="Test effort",
        status="active",
        lead={"name": "Lead"},
        dates={},
        funding=[{"source": "Test", "amount": 100}],
    )
    return WeeklyReport(
        week="2026-W39",
        warnings=[],
        efforts=[
            ReportEffort(
                effort=effort,
                updates=[
                    WeeklyStatus(
                        week="2026-W39",
                        author={"name": name, "ntid": ntid},
                        sections={section: f"{name}'s **{section}**." for section in SECTIONS},
                    )
                    for name, ntid in [("Alex", "alex"), ("Jane", "jane")]
                ],
            )
        ],
    )


def test_every_contributor_is_attributed_in_all_reports():
    from team_status.reports.email import email_html, email_markdown
    from team_status.reports.slides import slides_markdown
    from team_status.status import SECTIONS

    report = attributed_report()
    email = email_markdown(report)
    slides = slides_markdown(report)
    for name, ntid in [("Alex", "alex"), ("Jane", "jane")]:
        assert f"{name} (NTID: {ntid})" in email_html(email)
        for section in SECTIONS:
            text = f"{name}'s **{section}**."
            assert text in email
            page = next(page for page in slides.split("\n\n---\n\n") if text in page)
            assert name in page and ntid in page
    assert email.count("Total funding: 100 USD") == 1
    assert slides.count("Total funding: 100 USD") == 1


def test_short_updates_keep_all_sections_on_one_slide_per_contributor():
    from team_status.reports.markdown import author_label, literal
    from team_status.reports.slides import slides_markdown
    from team_status.status import SECTIONS

    report = example_report()
    deck = slides_markdown(report).split("\n\n---\n\n")
    for update in report.efforts[0].updates:
        label = literal(author_label(update.author))
        contribution_slides = [page for page in deck if label in page]
        assert len(contribution_slides) == 1
        for section in SECTIONS:
            assert section in contribution_slides[0]
            for line in update.sections[section].splitlines():
                assert line in contribution_slides[0]


def test_continued_slides_repeat_author_and_preserve_all_bullets():
    from team_status.reports.slides import slides_markdown

    report = attributed_report()
    report.efforts[0].updates[0].sections["Accomplishments"] = "\n".join(
        f"- Finished {i}: " + "some detail " * 6 for i in range(20)
    )
    result = slides_markdown(report)
    continued = [
        page for page in result.split("\n\n---\n\n") if "(continued)" in page and "Finished" in page
    ]
    assert continued
    assert all("Alex" in page and "alex" in page for page in continued)
    assert all(f"Finished {i}:" in result for i in range(20))


def test_author_metadata_is_literal_and_oversized_attribution_fails():
    import pytest

    from team_status.reports.email import email_html, email_markdown
    from team_status.reports.slides import slides_markdown

    report = attributed_report()
    author = report.efforts[0].updates[0].author
    author.name = "**Alex** <script>"
    author.ntid = "<!-- _backgroundColor: red -->"
    html = email_html(email_markdown(report))
    assert "<strong>Alex</strong>" not in html and "<script>" not in html
    slides = slides_markdown(report)
    assert "<!-- _backgroundColor" not in slides
    author.name = "Long name " * 30
    with pytest.raises(ValueError, match="author"):
        slides_markdown(report)


def test_legacy_attribution_is_explicit():
    from team_status.reports.email import email_markdown
    from team_status.reports.slides import slides_markdown

    report = attributed_report()
    report.efforts[0].updates[0].author = None
    for text in [email_markdown(report), slides_markdown(report)]:
        assert "Legacy update — author not recorded" in text


def test_author_entities_are_displayed_literally():
    from markdown_it import MarkdownIt

    from team_status.reports.email import email_html, email_markdown
    from team_status.reports.slides import slides_markdown

    report = attributed_report()
    report.efforts[0].updates[0].author.name = "Alex &copy;"
    for html in [email_html(email_markdown(report)), MarkdownIt().render(slides_markdown(report))]:
        assert "Alex &amp;copy;" in html
        assert "Alex ©" not in html
