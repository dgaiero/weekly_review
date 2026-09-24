"""Generate Marp Markdown with explicit, bounded slide content."""

from markdown_it import MarkdownIt

from ..models import WeeklyReport
from ..status import SECTIONS
from .markdown import literal, overview_context
from .templating import render


def safe_content(text: str) -> str:
    # Authored thematic breaks must not become slide boundaries. HTML comments
    # could be interpreted as Marp directives even when raw HTML is disabled.
    text = text.replace("<!--", "&lt;!--")
    lines = text.splitlines()
    for token in MarkdownIt().parse(text):
        if token.type == "hr" and token.map:
            lines[token.map[0]] = r"\-\-\-"
    return "\n".join(lines)


def pages(text: str, context: str) -> list[str]:
    """Paginate paragraphs and top-level list items without rewriting their words.

    Conservative text budgets are not a font-measurement engine. Oversized
    indivisible blocks fail visibly; the source must be split before export.
    """
    text = safe_content(text or "Not provided.")
    lines = text.splitlines()
    tokens = MarkdownIt().parse(text)
    starts = {0, len(lines)}
    for token in tokens:
        if token.map and (
            token.level == 0 or (token.type == "list_item_open" and token.level == 1)
        ):
            starts.add(token.map[0])
    bounds = sorted(starts)
    chunks = ["\n".join(lines[a:b]).strip() for a, b in zip(bounds, bounds[1:], strict=False)]
    result, current = [], []
    weight = 0
    for chunk in filter(None, chunks):
        cost = sum(max(1, (len(line) + 69) // 70) for line in chunk.splitlines()) + 1
        if cost > 11 or len(chunk) > 850:
            raise ValueError(
                f"{context}: content block is too long for a slide; "
                "split it into shorter paragraphs or bullets"
            )
        if current and (weight + cost > 11 or len("\n\n".join(current + [chunk])) > 850):
            result.append("\n\n".join(current))
            current, weight = [], 0
        current.append(chunk)
        weight += cost
    if current:
        result.append("\n\n".join(current))
    return result or ["Not provided."]


def slides_markdown(report: WeeklyReport) -> str:
    slides = [render("slide-title.md.j2", report=report)]

    def add(title: str, content: str, subtitle: str = ""):
        if len(title) > 95 or len(subtitle) > 100:
            raise ValueError("slide title is too long; split or shorten the effort name")
        for index, page in enumerate(pages(content, title)):
            slides.append(
                render(
                    "slide.md.j2",
                    title=title,
                    subtitle=subtitle,
                    continued=index > 0,
                    content=page,
                )
            )

    add("Portfolio", render("overview.md.j2", overview=overview_context(report)))
    if report.warnings:
        add("Reporting notes", render("warnings.md.j2", report=report))
    for item in report.efforts:
        effort = item.effort
        name = literal(effort.name)
        add(name, render("effort-metadata.md.j2", effort=effort))
        if item.update is None:
            add(name, render("missing-update.md.j2", report=report))
        else:
            for section in SECTIONS:
                add(name, item.update.sections[section], section)
    return render("slides.md.j2", slides=slides)
