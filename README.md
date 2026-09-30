# Team Status

Track team efforts in GitLab using YAML metadata and a Markdown update per person per week.
Includes validation, a normalized JSON report, Markdown slide and email generators,
HTML email, Marp PowerPoint export, JSON schemas, tests, Taskfile commands,
GitLab CI, and OpenCode guidance. SMTP email delivery is supported; the browser UI is future work.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Task](https://taskfile.dev/docs/installation), Node.js 22+, and pnpm 11.19.0,
then run:

```sh
task setup
task check
task demo
```

`task setup` installs both Python dependencies and Node slide tools. Use
`task python:setup` or `task slides:setup` to install either separately.

The demo writes report artifacts, including PowerPoint, to
`examples/build/demo/2026-09-21/` from fictional data under `examples/`.
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
`efforts/small-efforts/status/YYYY-MM-DD/<contributor>.md`. Name each small item
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
`efforts/<effort-id>/status/2026-09-21/<contributor>.md`. Use a lowercase slug for
the filename, preferably based on your NTID or name. Set `week` to match the
directory and copy your `author` metadata from the effort's team roster:

```yaml
---
week: 2026-09-21
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
Use the Monday starting the reporting week, in YYYY-MM-DD format.
Other weekdays and ISO week numbers are rejected. Quoted and unquoted YAML dates
are accepted. Reports display a heading such as “Week of September 21, 2026”.

These files can be created directly in GitLab's web editor. Contributors do not
need Python or a local clone. Your team chooses whether updates require an MR.

```sh
task validate -- --week 2026-09-21
task build-week -- --week 2026-09-21
```

Reports are written to `build/2026-09-21/`. Each missing active-effort team member's
required submission and active staff allocation above 100% warn without failing CI.
An active effort with required reporting, an empty team, and no update receives
an effort-level warning.
Invalid metadata, duplicate team identities or author submissions,
dates, weeks, duplicate YAML keys, and missing/duplicate sections fail validation.
All historical Markdown files are checked; older updates never fill a missing week.
For reproducible historical reports, check out the original source commit first.

Each update requires an author and the per-person directory layout above.
Duplicate author identities for the same effort/week are errors, including
historical weeks. Expected contributors come from the team roster in the
checked-out Git revision.

JSON reports use `schema_version: 2`. Each effort has an `updates` list;
an empty list means no submission. Each update contains `week`, a required
`author`, and `sections`. Contributions are ordered by normalized identity.

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
task slides:html -- examples/build/demo/2026-09-21/slides.md
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
system. The CI SMTP job sends this generated HTML with `email.md` as the
plain-text alternative. Outlook/Gmail-specific rendering is not tested.
Generated files are overwritten by the next build; persist lasting changes in
effort files or the [Jinja report templates](src/team_status/reports/templates/).
Edit `email.md.j2` for email structure, `email.html.j2` for its HTML wrapper,
and `email-styles.json` for inline element styles. Slide layout and theme live in
`slide.md.j2` and `slides.md.j2`. Rebuild reports after editing templates.

## Development

```sh
task test       # behavioral tests
task lint       # lint check (use -- --fix to apply fixes)
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
describes required-author front matter. Markdown headings and source paths
are validated by the parser. `task check` verifies schema consistency via tests.

## GitLab CI

Pushes and merge requests run separate audit, lint, format, type, package build,
test, and validation/schema jobs. CI formatting checks do not rewrite files.
Scheduled and manually launched pipelines on the default branch also generate
weekly reports, render PowerPoint, PDF, and HTML slides, and deploy GitLab Pages.
Pages opens the latest generated slide deck at `index.html`; the same site also
contains `email.html`, `slides.pdf`, `slides.pptx`, and the Markdown/JSON sources.
Each deployment replaces the previous site; it is not a weekly archive.
Set `REPORT_WEEK=2026-09-21` to select a week; otherwise the
Monday of the current UTC week is used. Create your Friday schedule in GitLab and choose
its timezone. Artifacts expire after 90 days; retain finalized reports separately
if you need a permanent archive.

The CI environment follows the [uv GitLab integration guidance](https://docs.astral.sh/uv/guides/integration/gitlab/)
and installs the checked-in dependency lockfile. Both runner images bootstrap
Task 3.51.1 using the [documented package installers](https://taskfile.dev/docs/installation).
Workflow commands run through Taskfile. `task build` builds wheel/sdist packages;
`task build-week` generates the weekly report. `weekly-slides` calls
`task slides:html`, `task slides:ppt` (an alias for `slides:pptx`), and
`task slides:pdf` directly in the checkout. The tasks default to `pnpm exec marp`;
CI sets `MARP_CMD=docker-entrypoint` to use the container's installed Marp and
runs it as the job user, without a separate rendering directory. The Pages job
requires exactly one rendered week under `build/` and copies it to `public/`
directly in `.gitlab-ci.yml`.

| Job | GitLab report or downloadable artifact |
| --- | --- |
| `test` | JUnit test results, Cobertura coverage annotations, coverage percentage, HTML test and coverage reports |
| `lint`, `format`, `type` | GitLab Code Quality JSON, including merge request findings |
| `audit` | Raw uv vulnerability audit JSON; findings fail the job |
| `dependency-scanning` | Native dependency scanning report and CycloneDX SBOMs for dependency/license displays |
| `build` | Wheel and source distribution under `dist/` |
| `weekly-report`, `weekly-slides` | Authored weekly reports and rendered slides |
| `pages` | Published site under `public/` |

Diagnostic artifacts upload even when their checks fail. `task test:report`
generates the test artifacts locally under `test_out/`. Coverage must still meet
the threshold in `pyproject.toml`; reporting does not suppress check failures.
The uv audit JSON is a downloadable artifact, not a GitLab security report.

Native dependency and license reporting uses GitLab's
[Dependency-Scanning.v2 template](https://docs.gitlab.com/user/application_security/dependency_scanning/dependency_scanning_sbom/)
with the committed Python and pnpm lockfiles. This configuration targets GitLab
19.x with Ultimate for the security/license UI. Self-managed instances must
synchronize package metadata. GitLab's template owns the scanner and report
schemas; its default advisory job failure policy is retained, while `audit`
remains a required check. See
[CycloneDX license scanning](https://docs.gitlab.com/user/compliance/license_scanning_of_cyclonedx_files/).
GitLab runner execution, native report ingestion, and Pages deployment must be
verified after pushing to a configured project; local checks cannot verify them.

No snapshot tags are configured. Renderers consume
`WeeklyReport`, keeping authored data and presentation separate. See
[the renderer boundary](src/team_status/reports/README.md).

Contribution slides group all five sections for one person within an effort, using
compact headings and spacing. Short updates fit on one slide; longer updates
continue at paragraph or bullet boundaries, repeating the effort, author, and
section heading. Effort metadata remains separate. No authored text is summarized.
The `slide-contribution.md.j2` template and `contribution` theme class control
this layout; its pagination budget is separate from portfolio and metadata slides.

## Automatic SMTP email

`weekly-email` automatically sends the generated report on scheduled and manually
launched default-branch pipelines, after `weekly-report` succeeds. It consumes
that job's artifacts directly and does not wait for slide rendering or Pages.
Push and merge request pipelines do not send email. Missing configuration fails
the job instead of silently skipping delivery.

Configure these GitLab CI/CD variables (do not commit credentials):

| Variable | Value |
| --- | --- |
| `SMTP_HOST` | Required SMTP hostname |
| `SMTP_PORT` | Defaults to 587 for STARTTLS, 465 for implicit TLS |
| `SMTP_SECURITY` | `starttls` (default) or `ssl`; certificates are verified |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | Both set for authentication, or both omitted for a relay |
| `EMAIL_FROM` | Required single bare mailbox address |
| `EMAIL_TO` | Required comma-separated bare mailbox addresses |

Store credentials as masked, protected variables and protect the default branch.
The runner must be able to reach the SMTP service. The subject includes the week
from the artifact directory; the HTML and Markdown bodies are sent unchanged.
`task email:send` runs the same delivery locally using environment variables and
exactly one report under `build/`; it sends a real message.

The job has no automatic retries. Retrying the job or starting another reporting
pipeline sends again. A transport failure or partial recipient rejection can
happen after some recipients have received the message; inspect delivery before
retrying. Success means the SMTP server accepted the message, not confirmation
of inbox delivery. Tests use mocked SMTP connections.
