# Repository contract

Git is the source of truth. Each effort has a `efforts/<id>/effort.yaml`
config file and per-person `status/YYYY-Www/<contributor>.md` report files.
Legacy `status/YYYY-Www.md` files remain supported.
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
- Effort `links` defaults to an empty list. Each entry requires a nonempty `name`
  and an HTTP(S) `url` (including internal hostnames), with optional nullable
  `description`. Invalid links are errors. Links retain their input order and
  are included in normalized report JSON through the effort metadata.
- Dates are ISO dates with end on or after start. Unknown end dates may be null.
- Funding amounts are nonnegative integer whole currency units. Each effort has
  a `currency` field, defaulting to `USD`, shared by all its funding sources.
  Codes must contain exactly three uppercase ASCII letters; no currency registry
  lookup is performed. Effort totals are derived, never entered. Reports label
  amounts with their currency code and group portfolio totals by currency in
  alphabetical order, without conversion. An empty portfolio shows `0 USD`.
- Commitment is a fraction of FTE between 0 and 1 per person. Active-effort totals
  above 1 warn; case-folded NTID is the identity when present, otherwise stripped,
  case-folded name. Identifier and name identities use separate namespaces.
  Duplicate team identities are errors. The shared Person contract uses `ntid`
  for leads, team members, customer contacts, and authors; `gitlab` is rejected.
- Weekly Markdown begins with YAML front matter containing a valid ISO week.
  New files require `author: {name: ..., ntid: ...}` (`ntid` optional), a lowercase
  slug filename, and a week matching their parent directory. Legacy files have
  optional authors and a week matching the filename. Unsupported Markdown path
  depths are errors. The five template H2 sections occur once each;
  empty sections are allowed. Fenced-code headings are content, not sections.
- Effort `reporting` accepts `required` (default) or `optional`. The additive field
  retains effort schema version 1 and report schema version 2. It is included in
  normalized report metadata. A shared `small-efforts` folder can use optional
  reporting for one-off work, with named items in ordinary weekly Markdown.
- All stored updates are validated, including historical author duplicates.
  Each active-effort team member with required reporting is expected to submit,
  regardless of commitment.
  Missing requested-week submissions warn once per person; inactive efforts and
  efforts with optional reporting do not warn. Empty-team active efforts with
  required reporting and no submission retain the effort-level warning.
  Optional reporting does not change staffing totals, input validation, or report
  inclusion; quiet weeks still have an empty updates list.
  The lead has an obligation only when listed in the team. Previous
  weeks and unattributed updates never satisfy individual obligations.
- Author matching uses the same identity rule as staffing; there is no fallback
  to name when only one side has an NTID. Outside-roster contributions remain
  valid and do not fulfill another person's obligation. Duplicate authors for
  an effort/week are errors, even across legacy and new paths, with both paths
  included in diagnostics. Both layouts may coexist without dropping content.
- Report schema version 2 includes all effort metadata and the selected week's
  `updates` list (empty when no submission); each update has nullable `author`,
  with warnings. Ordering is stable. Historical reports use metadata from the
  checked-out Git revision; checking out a snapshot is required for reproduction.
  Contributions sort by normalized identity, with unattributed legacy content
  first. Effort input remains version 1; migrating `gitlab` to `ntid` requires
  explicit correct identifiers rather than inferred usernames.
- Invalid input prevents report generation. Validation errors include source paths.

## Boundaries

`models.py` owns machine contracts, including separate new and legacy front-matter
models; `WeekMetadata` itself has no author field. `status.py` owns weekly Markdown parsing.
`repository.py` loads validated inputs and computes warnings. `reports/summary.py`
assembles WeeklyReport. `cli.py` handles arguments and output files.
Renderers consume WeeklyReport, never crawl source files themselves. Packaged Jinja
templates own Markdown layouts and the HTML email wrapper. Email groups by effort,
author, and section; slides repeat author attribution on every continuation and
reserve room for the label. Unattributed text is labeled "Legacy update — author
not recorded". Python computes totals once per effort,
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

Contribution slides group all five sections for one person within an effort, using
compact headings and spacing. Short updates fit on one slide; longer updates
continue at paragraph or bullet boundaries, repeating the effort, author, and
section heading. Effort metadata remains separate. No authored text is summarized.
The `slide-contribution.md.j2` template and `contribution` theme class control
this layout; its pagination budget is separate from portfolio and metadata slides.
