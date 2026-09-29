"""Normalize validated repository data for downstream renderers."""

from team_status.models import ReportEffort, WeeklyReport
from team_status.repository import Repository


def build_report(repository: Repository, week: str) -> WeeklyReport:
    if repository.errors:
        raise ValueError("cannot build report from an invalid repository")
    return WeeklyReport(
        week=week,
        efforts=[
            ReportEffort(
                effort=effort,
                updates=sorted(
                    repository.updates.get((effort.id, week), []),
                    key=lambda update: update.author.identity,
                ),
            )
            for effort in repository.efforts
        ],
        warnings=repository.warnings,
    )
