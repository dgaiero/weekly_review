# Team Status

Track team efforts in GitLab using YAML metadata and a Markdown update per person per week.
Includes validation, a normalized JSON report, Markdown slide and email generators,
HTML email, Marp PowerPoint export, JSON schemas, tests, Taskfile commands,
GitLab CI, and OpenCode guidance. Email delivery and the browser UI are future work.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Task](https://taskfile.dev/docs/installation), then run:

```sh
task setup
task check
task slides:setup
task demo
```

The demo writes report artifacts, including PowerPoint, to
`examples/build/demo/2026-W39/` from fictional data under `examples/`.
It requires Node.js 22+, pnpm 11.19.0, and Chrome, Edge, or Firefox for the
PowerPoint export. The live `efforts/` directory starts empty.

Task is optional: `uv sync --locked`, `uv run pytest`, and
`uv run team-status --help` provide the underlying commands. Python 3.12 is
pinned in `.python-version`; uv can install it automatically.

## Add an effort

Copy `templates/effort.yaml` to `efforts/<effort-id>/effort.yaml`. Replace the
ID, name, lead, and other metadata. The ID must match the directory name.
The template and examples include a schema directive for validation and completion
with the [Red Hat YAML extension for VS Code](https://github.com/redhat-developer/vscode-yaml).
Schema paths are relative to the YAML file. After copying the template into
`efforts/<effort-id>/effort.yaml`, change its first line to:

```yaml
# yaml-language-server: $schema=../../schema/effort.schema.json
```

Use fractions for commitment (`0.25` = 25% FTE) and ISO dates (`2026-09-23`).
Funding is a list of sources with nonnegative whole-unit amounts; totals are
calculated. Set an effort's `currency` to a three-letter uppercase currency code
(for example, `currency: USD` or `currency: EUR`); omitted values default to USD.
All funding sources within an effort use that currency. Reports label amounts
with the code and show separate portfolio totals per currency, without conversion.
Start/end dates can be null
while an effort is proposed. Prefer a merge request for metadata changes.

Use `links` for effort resources such as repositories and SharePoint sites.
Each link requires a nonempty `name` and an HTTP(S) `url`; `description` is
optional and may be omitted or null. Internal hostnames are supported.
Omitting `links` defaults to an empty list. Links are included in report JSON.

```yaml
links:
  - name: GitLab repository
    url: https://gitlab.example.com/team/project-alpha
    description: Source code and issues
  - name: SharePoint
    url: https://example.sharepoint.com/sites/project-alpha
```

## Small and one-off efforts

Use one shared `efforts/small-efforts/` folder for work that does not need its
own effort metadata. Copy `templates/effort.yaml` into that folder, set
`id: small-efforts`, choose a name and the actual lead, and set:

```yaml
status: active
reporting: optional
```

Each contributor uses the normal five-section weekly template at
`efforts/small-efforts/status/YYYY-Www/<contributor>.md`. Name each small item
in the bullets and reuse that name when following up in another week. Multiple
items share one submission per person per week. See the fictional
[small-efforts example](examples/efforts/small-efforts/effort.yaml).

`reporting` accepts `required` (the default) or `optional`. Optional reporting
suppresses missing-update warnings for both roster members and an empty roster;
contributors submit only when they have something to report. All submitted files,
including historical updates, still undergo normal validation. Reports retain
the effort and its authored updates; a quiet week still shows no update submitted.

List team commitments only when there is an actual allocation to this shared
effort. Active allocations still count toward staffing warnings; do not duplicate
time allocated to another effort. Promote an item to its own folder when it needs
independent staffing, funding, milestones, or sustained risk tracking. Small items
are tracked in authored weekly text, without a separate task-status register.

## Submit a weekly update

Every person listed in an active effort's `team` submits their own weekly file
unless the effort sets `reporting: optional`.
Copy `templates/weekly-status.md` to
`efforts/<effort-id>/status/2026-W39/<contributor>.md`. Use a lowercase slug for
the filename, preferably based on your NTID or name. Set `week` to match the
directory and copy your `author` metadata from the effort's team roster:

```yaml
---
week: 2026-W39
author:
  name: Your Name
  ntid: your-ntid
---
```

The filename does not determine identity. Matching uses case-insensitive NTID
when present, otherwise the trimmed, case-insensitive name. `ntid` is optional,
but omit it only when your roster entry also omits it: a name-only submission
does not match a roster member with an NTID. Fill in the five sections; empty
sections or `None.` are valid. The lead submits only if listed on the team,
although voluntary contributions from others are accepted.
Use ISO weeks, whose year can differ from the calendar year near New Year's Day.

These files can be created directly in GitLab's web editor. Contributors do not
need Python or a local clone. Your team chooses whether updates require an MR.

```sh
task validate -- --week 2026-W39
task build -- --week 2026-W39
```

Reports are written to `build/2026-W39/`. Each missing active-effort team member's
required submission and active staff allocation above 100% warn without failing CI.
An active effort with required reporting, an empty team, and no update receives
an effort-level warning.
Invalid metadata, duplicate team identities or author submissions,
dates, weeks, duplicate YAML keys, and missing/duplicate sections fail validation.
All historical Markdown files are checked; older updates never fill a missing week.
For reproducible historical reports, check out the original source commit first.

Legacy `status/2026-W39.md` updates remain readable, with optional author metadata.
Unattributed legacy text appears as "Legacy update — author not recorded" and
does not fulfill an individual's submission requirement. Legacy and per-person
files may coexist; reports include both. Duplicate author identities for the
same effort/week are errors across either layout, including historical weeks.
Expected contributors come from the team roster in the checked-out Git revision.

### Migrating existing metadata and report consumers

Person metadata now uses `ntid` instead of `gitlab` for leads, team members,
customer contacts, and authors. Replace old fields with the correct NTID, or omit
the optional identifier. GitLab usernames are not automatically treated as NTIDs;
the old `gitlab` field is rejected. Effort YAML keeps `schema_version: 1`.

JSON reports now use `schema_version: 2`. Each effort has an `updates` list instead
of `update`; an empty list means no submission. Each update contains `week`,
`author` (null for unattributed legacy content), and `sections`. Contributions
are ordered by normalized identity, with unattributed legacy content first.

## PowerPoint and email

Each build produces these reviewable files from the same validated weekly report:

| File | Purpose |
| --- | --- |
| `report.json` | Complete normalized data |
| `slides.md` | Marp Markdown, with explicit slide boundaries and theme |
| `email.md` | Continuous weekly report in Markdown |
| `email.html` | Email body with inline styles |

The deck includes portfolio totals, reporting warnings, effort metadata, and the
five authored sections from each contributor, with attribution on every contribution
slide. The email groups the same weekly content by effort and author in a continuous
layout. Empty sections say "Not provided." Missing updates say "No update submitted"
and never borrow content from another week. No AI summary is generated.

To export PowerPoint, install Node.js 22+, pnpm 11.19.0, and Chrome, Edge, or Firefox:

```sh
task slides:setup
task demo
task slides:html -- examples/build/demo/2026-W39/slides.md
```

The demo calls `task pptx` after building its reports. To export another deck,
run `task pptx -- path/to/slides.md`.
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
describes required-author front matter only; `schema/legacy-weekly-status.schema.json`
describes optional-author legacy front matter. Markdown headings and source paths
are validated by the parser. `task check` verifies schema consistency via tests.

## GitLab CI

Pushes and merge requests run lint, tests, schema consistency, and validation.
Scheduled and manually launched pipelines on the default branch also publish a
Markdown, JSON, and HTML email artifacts, followed by a PowerPoint render job.
Set `REPORT_WEEK=2026-W39` to select a week; otherwise the
current UTC ISO week is used. Create your Friday schedule in GitLab and choose
its timezone. Artifacts expire after 90 days; retain finalized reports separately
if you need a permanent archive.

The CI environment follows the [uv GitLab integration guidance](https://docs.astral.sh/uv/guides/integration/gitlab/)
and installs the checked-in dependency lockfile. Both runner images bootstrap
Task 3.51.1 using the [documented package installers](https://taskfile.dev/docs/installation).
All workflow commands then run through Taskfile: `task setup`, `task ci:check`,
`task build`, and `task slides:pptx:ci`. The CI check adds schema regeneration
and a Git diff check to `task check`; the PowerPoint task handles the official
Marp container's staging directory and file ownership. GitLab runner
execution is verified separately after pushing to a configured project.

No automatic email sending or snapshot tags are configured. Renderers consume
`WeeklyReport`, keeping authored data and presentation separate. See
[the renderer boundary](src/team_status/reports/README.md).

Contribution slides group all five sections for one person within an effort, using
compact headings and spacing. Short updates fit on one slide; longer updates
continue at paragraph or bullet boundaries, repeating the effort, author, and
section heading. Effort metadata remains separate. No authored text is summarized.
The `slide-contribution.md.j2` template and `contribution` theme class control
this layout; its pagination budget is separate from portfolio and metadata slides.
