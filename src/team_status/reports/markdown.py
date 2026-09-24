"""Shared formatting for generated Markdown documents."""

import re
from collections import Counter

from ..models import EffortStatus, WeeklyReport


def literal(value: str) -> str:
    """Keep metadata as visible text, not Markdown syntax or HTML."""
    return re.sub(r"([\\`*_{}\[\]()#+.!<>|~-])", r"\\\1", " ".join(value.splitlines()))


def overview_context(report: WeeklyReport) -> dict:
    """Compute portfolio values independently of their presentation."""
    counts = Counter(item.effort.status for item in report.efforts)
    return {
        "counts": {
            status.value.replace("_", " ").title(): counts[status] for status in EffortStatus
        },
        "funding": sum(item.effort.funding_total for item in report.efforts),
        "staffing": sum(
            member.commitment
            for item in report.efforts
            if item.effort.status == EffortStatus.ACTIVE
            for member in item.effort.team
        ),
    }
