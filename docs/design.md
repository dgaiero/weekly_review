# Repository contract

Git is the source of truth. Each effort has a `efforts/<id>/effort.yaml`
config file and a `status/YYYY-Www.md` report file.
Pydantic is the canonical schema; exported JSON
schemas support future editors. People can edit templates in GitLab without
installing the CLI. Python 3.12+, uv, Taskfile, and OpenCode support development.

The repository implements metadata and weekly parsing, validation, JSON schema
export, and a normalized weekly report. Report generators produce separate Marp
slide Markdown and email Markdown. Marp exports image-based PowerPoint, and
markdown-it-py renders email HTML with raw HTML disabled and inline styles.
A future static browser editor, email delivery, and snapshot tag automation
are separate increments.

## Validation and reporting

- IDs are lowercase slugs and match directory names; duplicate IDs are errors.
- Status: proposed, active, on_hold, completed, cancelled.
- Dates are ISO dates with end on or after start. Unknown end dates may be null.
- Funding amounts are nonnegative integer whole currency units. Use one agreed
  currency across the repository; multi-currency conversion is outside this version.
  The total is derived, never entered.
- Commitment is a fraction of FTE between 0 and 1 per person. Active-effort totals
  above 1 warn; GitLab username is the identity when present, otherwise normalized name.
- Weekly Markdown begins with YAML front matter containing a valid ISO week.
  Its filename and week must agree. The five template H2 sections occur once each;
  empty sections are allowed. Fenced-code headings are content, not sections.
- All stored updates are validated. Missing requested-week updates for active
  efforts warn. Previous weeks are never silently substituted.
- Reports include all effort metadata and the selected week's update or null,
  with warnings. Ordering is stable. Historical reports use metadata from the
  checked-out Git revision; checking out a snapshot is required for reproduction.
- Invalid input prevents report generation. Validation errors include source paths.

## Boundaries

`models.py` owns machine contracts. `status.py` owns weekly Markdown parsing.
`repository.py` loads validated inputs and computes warnings. `reports/summary.py`
assembles WeeklyReport. `cli.py` handles arguments and output files.
Renderers consume WeeklyReport, never crawl source files themselves. Packaged Jinja
templates own Markdown layouts and the HTML email wrapper; Python computes totals,
converts Markdown, and paginates slides. HTML templates autoescape values, Markdown
metadata uses the literal filter, and authored Markdown remains data rather than
template source. Undefined template values fail explicitly. The slide
generator paginates paragraphs and list items using conservative text budgets;
oversized blocks fail explicitly. Visual review is still required for unusual
Markdown, images, tables, and theme changes. Authored slide separators and Marp
comments are neutralized so only the generator controls slide boundaries.

CI checks pushes and merge requests. Scheduled reports run on the default branch,
accept REPORT_WEEK, and publish JSON, Markdown, HTML, and PPTX artifacts.
Default week is the current UTC
ISO week. Configure the Friday schedule and timezone in GitLab. No credentials,
external communications, automatic Git writes, or model calls are needed.
