# Per-person weekly updates

Status: proposed written spec; conversational requirements approved.

## Purpose and agreed behavior

Each person on an effort's team owns a separate weekly Markdown file. Reports
collect those contributions under the effort and attribute each one without
summarizing or rewriting the authored sections. Every listed team member is
expected to submit for active efforts, regardless of commitment fraction. The
lead is expected to submit only when also listed on the team.

Missing submissions are warnings. Malformed data and duplicate submissions are
errors. Existing historical single-file updates remain readable without invented
attribution. Team membership and effort status come from the checked-out Git
revision; historical reproduction requires the appropriate revision.

## Source format

New submissions live at
`efforts/<effort-id>/status/<YYYY-Www>/<contributor>.md`.
For example, the fictional contributor file `status/2026-W39/alex.md` begins:

```yaml
---
week: 2026-W39
author:
  name: Alex Example
  gitlab: alex
---
```

Reuse `Person`: name is required and GitLab username is optional. The five current
H2 sections and all current Markdown validation rules remain. The week directory
must match front matter. The filename is a nonempty lowercase slug chosen by the
contributor, not an identity credential; front matter determines identity.
Documentation recommends a stable filename derived from the username or name.

Legacy `status/YYYY-Www.md` files retain their existing format and filename/week
validation. They may omit author; omitted attribution is represented as null.
An explicit author is permitted on a legacy file and follows the same identity
and duplicate rules as a new submission. New directory-format files require an
author. No existing source files are automatically migrated.

## Identity, completeness, and compatibility decisions

Use the existing staffing identity rule everywhere: case-folded GitLab username
when present, otherwise stripped, case-folded name, with distinct key namespaces.
Do not fall back to name when only one side supplies a username; documentation
instructs contributors to copy their person metadata from the team roster.

Duplicate author identity within an effort/week is an error, even across legacy
and new paths. Duplicate team identities are also errors because responsibility
and staffing would otherwise be ambiguous. Errors identify the relevant files.

Keep contributions from authors outside the current roster. They do not satisfy
another person's obligation. This supports past contributors without invalidating
historical updates against today's roster and allows voluntary lead contributions.

For the requested week, warn once per missing member of each active effort.
An unattributed legacy update does not satisfy anyone's individual obligation.
If an active effort has an empty team and no submission, retain the existing
effort-level missing-update warning. If the team is nonempty, individual warnings
replace the redundant effort-level warning. Inactive efforts have no missing
submission warnings. Staffing above 100% remains a warning as before.

Legacy and new files may coexist in a week; include all valid contributions,
placing an unattributed legacy contribution first. Never infer that legacy text
was superseded. Validate all stored updates, including historical duplicates,
but calculate missing-submission warnings only for the requested week.

## Contracts and data flow

Keep `WeekMetadata` focused on the week so `WeeklyReport` does not acquire an author
field through inheritance. Add separate front-matter models for required-author
submissions and legacy optional-author updates. `WeeklyStatus` carries week,
optional author, and the existing section mapping; null author supports legacy
content only at the source parser boundary.

Change `Repository.updates` values to lists of `WeeklyStatus`, keyed by effort and
week. Retain source paths during loading for duplicate diagnostics. Discover both
supported layouts and report malformed Markdown paths instead of silently skipping
them. `status.py` handles format, path, and section validation; `repository.py`
handles discovery, duplicate identities, completeness, and staffing.

Replace `ReportEffort.update` with `updates: list[WeeklyStatus]`, using an empty
list for no submissions. Bump the output `WeeklyReport.schema_version` from 1 to 2
because this changes JSON consumers. Effort YAML remains version 1. The summary
builder orders efforts as today and contributions by normalized identity, with
unattributed legacy content first. Renderers read only `WeeklyReport`.

Export schemas from the canonical Pydantic models. The primary weekly front-matter
schema requires author for new submissions; provide a separate legacy front-matter
schema for historical files. Regenerate report and input schemas with `task schema`.
Document the JSON version change and new collection field for downstream users.

## Presentation

Email Markdown and HTML group by effort, then author, then the five sections.
Display the authored name and optional GitLab username as escaped metadata.
Label null-author content as "Legacy update — author not recorded".

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
efforts; lead-only and outside-roster contributions; legacy and mixed layouts;
historical validation; deterministic ordering; and unchanged staffing totals.

Report tests verify JSON version 2, author attribution, preservation of every
contributor's sections, escaping, empty and missing content, and slide continuation
attribution. Regenerate schemas, run schema consistency checks and `task check`,
and build the fictional example reports. Visually inspect representative email
and exported slides with multiple authors and a continued section.

## Review and next step

The behavior above implements the approved conversational requirements. Identity
edge cases, mixed-layout handling, schema versioning, and presentation details
are explicit design decisions for review. After written-spec approval, prepare
the implementation plan under the brainstorming workflow.
