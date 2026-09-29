# Per-person weekly updates

Status: implemented with NTID identity; verification recorded in the implementation plan.

## Purpose and agreed behavior

Each person on an effort's team owns a separate weekly Markdown file. Reports
collect those contributions under the effort and attribute each one without
summarizing or rewriting the authored sections. Every listed team member is
expected to submit for active efforts, regardless of commitment fraction. The
lead is expected to submit only when also listed on the team.

Missing submissions are warnings. Malformed data and duplicate submissions are
errors. Every update requires an author and a per-person file. Team membership and effort status come from the checked-out Git
revision; historical reproduction requires the appropriate revision.

## Source format

New submissions live at
`efforts/<effort-id>/status/<YYYY-MM-DD>/<contributor>.md`.
For example, the fictional contributor file `status/2026-09-21/alex.md` begins:

```yaml
---
week: 2026-09-21
author:
  name: Alex Example
  ntid: alex
---
```

Reuse `Person`: name is required and NTID (`ntid`) is optional. The five current
H2 sections and all current Markdown validation rules remain. The week directory
must match front matter. The filename is a nonempty lowercase slug chosen by the
contributor, not an identity credential; front matter determines identity.
Documentation recommends a stable filename derived from the NTID or name.

## Identity and completeness

Use the same identity rule for staffing and submissions: case-folded NTID
when present, otherwise stripped, case-folded name, with distinct key namespaces.
Do not fall back to name when only one side supplies an NTID; documentation
instructs contributors to copy their person metadata from the team roster.

Duplicate author identity within an effort/week is an error. Duplicate team identities are also errors because responsibility
and staffing would otherwise be ambiguous. Errors identify the relevant files.

Keep contributions from authors outside the current roster. They do not satisfy
another person's obligation. This supports past contributors without invalidating
historical updates against today's roster and allows voluntary lead contributions.

For the requested week, warn once per missing member of each active effort.
If an active effort has an empty team and no submission, retain the existing
effort-level missing-update warning. If the team is nonempty, individual warnings
replace the redundant effort-level warning. Inactive efforts have no missing
submission warnings. Staffing above 100% remains a warning as before.

Validate all stored updates, including historical duplicates, but calculate
missing-submission warnings only for the requested week.

## Contracts and data flow

Person metadata uses `ntid` for leads, team members, customer contacts, and
authors. Never infer identifiers from names or GitLab usernames.

Keep `WeekMetadata` focused on the week so `WeeklyReport` does not acquire an
author field through inheritance. `SubmissionMetadata` requires `author: Person`.
`WeeklyStatus` extends it with the existing section mapping.

Change `Repository.updates` values to lists of `WeeklyStatus`, keyed by effort and
week. Retain source paths during loading for duplicate diagnostics. Discover per-person files and report malformed Markdown paths instead of silently skipping
them. `status.py` handles format, path, and section validation; `repository.py`
handles discovery, duplicate identities, completeness, and staffing.

Replace `ReportEffort.update` with `updates: list[WeeklyStatus]`, using an empty
list for no submissions. Bump the output `WeeklyReport.schema_version` from 1 to 2
because this changes JSON consumers. Effort YAML remains version 1. The summary
builder orders efforts as today and contributions by normalized identity. Renderers read only `WeeklyReport`.

Export schemas from the canonical Pydantic models. The primary weekly front-matter
schema requires an author for every submission. Regenerate report and input schemas with `task schema`.
Document the JSON version change and new collection field for downstream users.

## Presentation

Email Markdown and HTML group by effort, then author, then the five sections.
Display the authored name and optional NTID as escaped metadata.

Slides show effort metadata once, followed by each contributor's five sections.
Every contribution slide, including continuation slides, displays attribution.
Account for the author label in pagination space; oversized content or metadata
must fail explicitly rather than truncate. Preserve existing Markdown safety
handling, empty-section text, and missing-update text for an empty updates list.
Portfolio totals count efforts and staffing once, independent of submissions.

## Scope and verification

Update the contributor template, README, repository design contract, renderer
documentation, and fictional examples. Keep all example authors and content under
`examples/`; do not invent or alter the real portfolio. No UI, delivery,
credentials, AI summaries, or automatic source migration is included.

Behavioral tests cover two contributors on one effort/week; author metadata and
week/path validation; identity normalization; duplicate submissions and roster
identities; partial and wholly missing submissions; inactive and empty-team
efforts; lead-only and outside-roster contributions; rejection of single-file paths and missing authors;
historical validation; deterministic ordering; and unchanged staffing totals.

Report tests verify JSON version 2, author attribution, preservation of every
contributor's sections, escaping, empty and missing content, and slide continuation
attribution. Regenerate schemas, run schema consistency checks and `task check`,
and build the fictional example reports. Visually inspect representative email
and exported slides with multiple authors and a continued section.

## Implementation record

Implemented under `docs/superpowers/plans/2026-09-24-per-person-weekly-updates.md`.
That plan records tests, review findings, and visual verification. The source
parser validates file depth relative to the actual effort status directory so
nested directories named `status` cannot bypass layout checks.
