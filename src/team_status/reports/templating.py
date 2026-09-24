"""Load report templates from the installed package, independent of cwd."""

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from .markdown import literal

_environment = Environment(
    loader=PackageLoader("team_status.reports", "templates"),
    autoescape=select_autoescape(enabled_extensions=("html.j2",)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)
_environment.filters["literal"] = literal


def render(template: str, **context: object) -> str:
    return _environment.get_template(template).render(**context)
