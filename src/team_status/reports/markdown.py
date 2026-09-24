"""Shared formatting for generated Markdown documents."""

import re
from collections import Counter

from ..models import EffortStatus, Person, WeeklyReport


def author_label(author: Person | None) -> str:
    if author is None:
        return "Legacy update — author not recorded"
    return f"{author.name} (NTID: {author.ntid})" if author.ntid else author.name


def literal(value: str) -> str:
    """Keep metadata as visible text, not Markdown syntax or HTML."""
    return re.sub(r"([\\`*_{}\[\]()#+.!<>|~&-])", r"\\\1", " ".join(value.splitlines()))


def overview_context(report: WeeklyReport) -> dict:
    """Compute portfolio values independently of their presentation."""
    counts = Counter(item.effort.status for item in report.efforts)
    funding: dict[str, int] = {}
    for item in report.efforts:
        currency = item.effort.currency
        funding[currency] = funding.get(currency, 0) + item.effort.funding_total
    return {
        "counts": {
            status.value.replace("_", " ").title(): counts[status] for status in EffortStatus
        },
        "funding": dict(sorted(funding.items())) if funding else {"USD": 0},
        "staffing": sum(
            member.commitment
            for item in report.efforts
            if item.effort.status == EffortStatus.ACTIVE
            for member in item.effort.team
        ),
    }
