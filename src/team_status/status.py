"""Parse front matter and preserve Markdown within the five weekly sections."""

import re
from pathlib import Path

from markdown_it import MarkdownIt

from .models import LegacyStatusMetadata, SubmissionMetadata, WeeklyStatus
from .yaml_io import load_yaml

SECTIONS = (
    "Progress Overview",
    "Accomplishments",
    "Risks / Blockers / Mitigations",
    "Next Week",
    "Help / Decisions Needed",
)


def parse_status(path: Path, *, status_root: Path | None = None) -> WeeklyStatus:
    if status_root is None:
        status_root = path.parent if path.parent.name == "status" else path.parent.parent
    parts = path.relative_to(status_root).parts
    if status_root.name != "status" or len(parts) not in (1, 2):
        raise ValueError("status path must be status/<week>.md or status/<week>/<contributor>.md")
    if len(parts) == 1:
        metadata_model = LegacyStatusMetadata
        path_week = path.stem
        location = "filename"
    else:
        metadata_model = SubmissionMetadata
        path_week = path.parent.name
        location = "week directory"
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path.stem):
            raise ValueError("contributor filename must be a lowercase slug")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("expected YAML front matter starting with ---")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("unclosed YAML front matter") from exc
    metadata = metadata_model.model_validate(load_yaml("\n".join(lines[1:end])))
    if path_week != metadata.week:
        raise ValueError(f"status {location} must match front matter week")
    body = lines[end + 1 :]
    tokens = MarkdownIt().parse("\n".join(body))
    headings = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h2" and token.level == 0:
            headings.append((tokens[index + 1].content, token.map))
    sections = {}
    for index, (title, span) in enumerate(headings):
        if title not in SECTIONS:
            raise ValueError(f"unknown weekly section: {title}")
        if title in sections:
            raise ValueError(f"duplicate weekly section: {title}")
        stop = headings[index + 1][1][0] if index + 1 < len(headings) else len(body)
        sections[title] = "\n".join(body[span[1] : stop]).strip()
    missing = set(SECTIONS) - sections.keys()
    if missing:
        raise ValueError(f"missing required sections: {', '.join(sorted(missing))}")
    if headings and any(line.strip() for line in body[: headings[0][1][0]]):
        raise ValueError("weekly content must be inside the required sections")
    return WeeklyStatus(week=metadata.week, author=metadata.author, sections=sections)
