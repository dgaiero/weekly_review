"""Load report templates from the installed package, independent of cwd."""

from datetime import date

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from .markdown import author_label, literal

_environment = Environment(
    loader=PackageLoader("team_status.reports", "templates"),
    autoescape=select_autoescape(enabled_extensions=("html.j2",)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


def week_label(value: str) -> str:
    monday = date.fromisoformat(value)
    return f"Week of {monday.strftime('%B')} {monday.day}, {monday.year}"


_environment.filters["week_label"] = week_label
_environment.filters["literal"] = literal
_environment.filters["author_label"] = author_label


def render(template: str, **context: object) -> str:
    return _environment.get_template(template).render(**context)
