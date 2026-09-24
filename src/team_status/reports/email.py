"""Email Markdown and HTML, without delivery or inferred summaries."""

import json
from importlib.resources import files

from markdown_it import MarkdownIt
from markupsafe import Markup

from ..models import WeeklyReport
from ..status import SECTIONS
from .markdown import overview_context
from .templating import render


def email_markdown(report: WeeklyReport) -> str:
    return render(
        "email.md.j2", report=report, sections=SECTIONS, overview=overview_context(report)
    )


def email_html(markdown: str) -> str:
    """Render a simple email body with inline styles and raw HTML disabled."""
    parser = MarkdownIt("commonmark", {"html": False})
    tokens = parser.parse(markdown)
    styles = json.loads(
        files("team_status.reports")
        .joinpath("templates/email-styles.json")
        .read_text(encoding="utf-8")
    )

    def style_tokens(items):
        for token in items:
            if token.tag in styles:
                token.attrSet("style", styles[token.tag])
            if token.children:
                style_tokens(token.children)

    style_tokens(tokens)
    content = parser.renderer.render(tokens, parser.options, {})
    title = markdown.splitlines()[0].lstrip("# ") if markdown else "Weekly Status"
    # Only parser-produced HTML is trusted; template autoescaping handles the title.
    return render("email.html.j2", title=title, content=Markup(content))
