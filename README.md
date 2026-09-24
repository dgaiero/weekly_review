# Team Status

Track team efforts in GitLab using YAML metadata and a Markdown update per week.
Includes validation, a normalized JSON report, Markdown slide and email generators,
HTML email, Marp PowerPoint export, JSON schemas, tests, Taskfile commands,
GitLab CI, and OpenCode guidance. Email delivery and the browser UI are future work.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Task](https://taskfile.dev/docs/installation), then run:

```sh
task setup
task check
task demo
```

The demo writes report artifacts to `build/demo/2026-W39/` from fictional data under
`examples/`. The live `efforts/` directory starts empty.

Task is optional: `uv sync --locked`, `uv run pytest`, and
`uv run team-status --help` provide the underlying commands. Python 3.12 is
pinned in `.python-version`; uv can install it automatically.

## Add an effort

Copy `templates/effort.yaml` to `efforts/<effort-id>/effort.yaml`. Replace the
ID, name, lead, and other metadata. The ID must match the directory name.
Use fractions for commitment (`0.25` = 25% FTE) and ISO dates (`2026-09-23`).
Funding is a list of sources with nonnegative whole-unit amounts; totals are
calculated. Agree on one currency for the portfolio. Start/end dates can be null
while an effort is proposed. Prefer a merge request for metadata changes.

## Submit a weekly update

Copy `templates/weekly-status.md` to
`efforts/<effort-id>/status/2026-W39.md`. Set the front matter `week` to match
the filename and fill in the five sections. Empty sections or `None.` are valid.
Use ISO weeks, whose year can differ from the calendar year near New Year's Day.

These files can be created directly in GitLab's web editor. Contributors do not
need Python or a local clone. Your team chooses whether updates require an MR.

```sh
task validate -- --week 2026-W39
task build -- --week 2026-W39
```

Reports are written to `build/2026-W39/`. Missing active-effort updates and
active staff allocation above 100% warn without failing CI. Invalid metadata,
dates, weeks, duplicate YAML keys, and missing/duplicate sections fail validation.
All historical Markdown files are checked; older updates never fill a missing week.
For reproducible historical reports, check out the original source commit first.

## PowerPoint and email

Each build produces these reviewable files from the same validated weekly report:

| File | Purpose |
| --- | --- |
| `report.json` | Complete normalized data |
| `slides.md` | Marp Markdown, with explicit slide boundaries and theme |
| `email.md` | Continuous weekly report in Markdown |
| `email.html` | Email body with inline styles |

The deck includes portfolio totals, reporting warnings, effort metadata, and the
five authored sections. The email includes the same weekly content in a continuous
layout. Empty sections say "Not provided." Missing updates say "No update submitted"
and never borrow content from another week. No AI summary is generated.

To export PowerPoint, install Node.js 22+, pnpm 11.19.0, and Chrome, Edge, or Firefox:

```sh
task slides:setup
task demo
task pptx -- build/demo/2026-W39/slides.md
task slides:html -- build/demo/2026-W39/slides.md
```

Marp writes `slides.pptx` and `slides.html` beside the Markdown. The HTML slide
preview does not require a browser installation. PPTX export does. For a browser
in a nonstandard location, add `--browser-path '/path/to/browser'` to the export
command. CI uses the pinned official Marp container with its bundled browser.

**PowerPoint slides are rendered images.** Edit `slides.md` and export again;
the default export does not provide editable PowerPoint text or shapes.
[Marp documents the trade-off and experimental editable export](https://github.com/marp-team/marp-cli#powerpoint-pptx).

Long sections paginate at paragraph and bullet boundaries. An oversized indivisible
block fails with an instruction to split it, rather than dropping text. Pagination
uses a conservative text budget, so review rendered slides before distribution,
especially after adding tables, images, long code blocks, or custom styling.

Email HTML uses a simple table wrapper and inline styles. Raw HTML in authored
Markdown is escaped. Preview `email.html`, then use it as the body in your sending
system. Outlook/Gmail-specific rendering and sending are not tested or configured.
Generated files are overwritten by the next build; persist lasting changes in
effort files or the [Jinja report templates](src/team_status/reports/templates/).
Edit `email.md.j2` for email structure, `email.html.j2` for its HTML wrapper,
and `email-styles.json` for inline element styles. Slide layout and theme live in
`slide.md.j2` and `slides.md.j2`. Rebuild reports after editing templates.

## Development

```sh
task test       # behavioral tests
task lint       # lint and formatting check
task format     # apply formatting
task schema     # regenerate JSON schemas after model changes
task check      # all local checks
```

OpenCode loads the project `opencode.json` and `AGENTS.md`. Run `opencode` from
this directory and use your own provider/model configuration. There are no
provider credentials or automated model calls in this project. See the
[OpenCode configuration documentation](https://opencode.ai/docs/config/).

The architecture and validation rules are in [docs/design.md](docs/design.md).
Pydantic models are the canonical contract. `schema/weekly-status.schema.json`
describes front matter only; Markdown headings are validated by the parser.

## GitLab CI

Pushes and merge requests run lint, tests, schema consistency, and validation.
Scheduled and manually launched pipelines on the default branch also publish a
Markdown, JSON, and HTML email artifacts, followed by a PowerPoint render job.
Set `REPORT_WEEK=2026-W39` to select a week; otherwise the
current UTC ISO week is used. Create your Friday schedule in GitLab and choose
its timezone. Artifacts expire after 90 days; retain finalized reports separately
if you need a permanent archive.

The CI environment follows the [uv GitLab integration guidance](https://docs.astral.sh/uv/guides/integration/gitlab/)
and installs the checked-in dependency lockfile. CI invokes the same Python
commands as Taskfile, without requiring Task in the runner image. GitLab runner
execution is verified separately after pushing to a configured project.

No automatic email sending or snapshot tags are configured. Renderers consume
`WeeklyReport`, keeping authored data and presentation separate. See
[the renderer boundary](src/team_status/reports/README.md).
