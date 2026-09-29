# Per-person Weekly Updates Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Collect attributed weekly files from every active-effort team member using NTID identity.

**Architecture:** Pydantic owns person and report contracts. The parser validates the per-person source layout; the repository collects contributions and warnings; renderers consume the normalized report only.

**Tech Stack:** Python 3.12, uv, Pydantic, pytest, Jinja, MarkdownIt, Taskfile, Marp.

**Spec:** `docs/superpowers/specs/2026-09-24-per-person-weekly-updates-design.md`

## Global Constraints

- Missing submissions and staffing above 100% are warnings; malformed data is an error.
- Preserve authored Markdown in valid attributed submissions.
- Use `ntid` throughout Person metadata; never infer real NTIDs from GitLab usernames.
- Report version 2 replaces `update` with `updates`; effort YAML stays version 1.
- Keep fictional source content under examples and leave the real portfolio untouched.

## Review Focus

- A missing NTID must not match a roster member with an NTID by name (task 1).
- Historical and deeply misplaced Markdown must not evade validation (task 1).
- Duplicate authors must identify both source files (task 1).
- Author metadata must not inject Markdown or slide directives (task 2).
- Every continued slide must retain attribution with room for its label (task 2).

### Task 1: Source contracts and collection

Files: `src/team_status/{models,status,repository}.py`, `src/team_status/reports/summary.py`, `tests/test_contributions.py`.

Interfaces: `parse_status(path: Path) -> WeeklyStatus`; `load_repository(root: Path, week: str) -> Repository`; `build_report(repository: Repository, week: str) -> WeeklyReport`. Repository values become lists; report entries expose `updates`.

- [x] Add tests writing real temporary effort/status files with two authors, asserting normalized report content and completeness warnings. Cover the identity, duplicate, malformed path, missing author, inactive, empty-team, and staffing cases in the spec.
- [x] Run `uv run pytest tests/test_contributions.py -q` and verify expected failures.
- [x] Rename the Person identifier, centralize identity, validate duplicate roster entries, and require author metadata for every update. Parse per-person paths and reject unsupported layouts.

```python
class SubmissionMetadata(WeekMetadata):
    author: Person


class WeeklyStatus(SubmissionMetadata):
    sections: dict[str, str]
```

- [x] Recursively discover Markdown beneath each status directory; parser rejects unsupported depths and mismatched weeks. Collect lists with duplicate-author source tracking. Compute missing warnings from roster identities and sort normalized contributions in the summary builder.
- [x] Run task 1 tests; expect all passing.

### Task 2: Attributed reports and schemas

Files: `src/team_status/reports/{slides,markdown}.py`, report templates, `src/team_status/cli.py`, `tests/test_reports.py`, `tests/test_repository.py`, `schema/*.json`.

Interfaces: consume `ReportEffort.updates: list[WeeklyStatus]`; keep public renderer signatures unchanged. Add shared author label formatting and pass attribution separately to the slide template.

- [x] Update integration tests for `updates` and NTID. Add tests covering every author/section in email and slides, escaped attribution, continued slides, excessive author length, and schema export parity.
- [x] Run `uv run pytest tests/test_reports.py tests/test_repository.py -q`; verify failures from the old renderer/schema contracts.
- [x] Render each contribution in order and display name plus optional NTID. Reserve slide content lines for attribution and repeat it on each page. Keep totals computed once per effort.

```python
for update in item.updates:
    for section in SECTIONS:
        add(name, update.sections[section], section, author_label(update.author))
```

- [x] Export the required-author input schema plus report version 2; run `task schema`.
- [x] Run the full pytest suite and verify generated schemas match checked-in files.

### Task 3: Documentation, examples, and final verification

Files: README, `docs/design.md`, renderer README, contributor templates, fictional examples, this plan/spec.

- [x] Document submission paths, responsibilities, identity matching, and input/report contracts.
- [x] Add two fictional attributed example files ; use explicit fictional NTIDs.
- [x] Run `task check`, `git diff --check`, and build example artifacts. Export slides and inspect representative email and multi-author/continued slides.
- [x] Review the complete change against the spec, resolve important findings, and record verification here.

## Maintenance note

The source format now uses Monday dates and requires attributed per-person
updates throughout the input and report contracts. The plan above reflects that
current format. See `docs/design.md` for the repository contract.
