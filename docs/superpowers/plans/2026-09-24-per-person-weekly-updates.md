# Per-person Weekly Updates Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Collect attributed weekly files from every active-effort team member using NTID identity.

**Architecture:** Pydantic owns person and report contracts. The parser validates both source layouts; the repository collects contributions and warnings; renderers consume the normalized report only.

**Tech Stack:** Python 3.12, uv, Pydantic, pytest, Jinja, MarkdownIt, Taskfile, Marp.

**Spec:** `docs/superpowers/specs/2026-09-24-per-person-weekly-updates-design.md`

## Global Constraints

- Missing submissions and staffing above 100% are warnings; malformed data is an error.
- Preserve authored Markdown and historical unattributed files.
- Use `ntid` throughout Person metadata; never infer real NTIDs from GitLab usernames.
- Report version 2 replaces `update` with `updates`; effort YAML stays version 1.
- Keep fictional source content under examples and leave the real portfolio untouched.

## Review Focus

- A missing NTID must not match a roster member with an NTID by name (task 1).
- Historical and deeply misplaced Markdown must not evade validation (task 1).
- Duplicate authors must identify both source files, including mixed layouts (task 1).
- Author metadata must not inject Markdown or slide directives (task 2).
- Every continued slide must retain attribution with room for its label (task 2).

### Task 1: Source contracts and collection

Files: `src/team_status/{models,status,repository}.py`, `src/team_status/reports/summary.py`, `tests/test_contributions.py`.

Interfaces: `parse_status(path: Path) -> WeeklyStatus`; `load_repository(root: Path, week: str) -> Repository`; `build_report(repository: Repository, week: str) -> WeeklyReport`. Repository values become lists; report entries expose `updates`.

- [x] Add tests writing real temporary effort/status files with two authors, asserting normalized report content and completeness warnings. Cover the identity, duplicate, malformed path, legacy, inactive, empty-team, and staffing cases in the spec.
- [x] Run `uv run pytest tests/test_contributions.py -q` and verify expected failures.
- [x] Rename the Person identifier, centralize identity, validate duplicate roster entries, and add separate legacy/new metadata models. Parse nested paths with required author and root legacy paths with optional author.

```python
class SubmissionMetadata(WeekMetadata):
    author: Person


class LegacyStatusMetadata(WeekMetadata):
    author: Person | None = None


class WeeklyStatus(LegacyStatusMetadata):
    sections: dict[str, str]
```

- [x] Recursively discover Markdown beneath each status directory; parser rejects unsupported depths and mismatched weeks. Collect lists with duplicate-author source tracking. Compute missing warnings from roster identities and sort normalized contributions in the summary builder.
- [x] Run task 1 tests; expect all passing.

### Task 2: Attributed reports and schemas

Files: `src/team_status/reports/{slides,markdown}.py`, report templates, `src/team_status/cli.py`, `tests/test_reports.py`, `tests/test_repository.py`, `schema/*.json`.

Interfaces: consume `ReportEffort.updates: list[WeeklyStatus]`; keep public renderer signatures unchanged. Add shared author label formatting and pass attribution separately to the slide template.

- [x] Update integration tests for `updates` and NTID. Add tests covering every author/section in email and slides, escaped attribution, continued slides, excessive author length, and schema export parity.
- [x] Run `uv run pytest tests/test_reports.py tests/test_repository.py -q`; verify failures from the old renderer/schema contracts.
- [x] Render each contribution in order and display name plus optional NTID, or the legacy attribution label. Reserve slide content lines for attribution and repeat it on each page. Keep totals computed once per effort.

```python
for update in item.updates:
    for section in SECTIONS:
        add(name, update.sections[section], section, author_label(update.author))
```

- [x] Export required-author and legacy optional-author input schemas plus report version 2; run `task schema`.
- [x] Run the full pytest suite and verify generated schemas match checked-in files.

### Task 3: Documentation, examples, and final verification

Files: README, `docs/design.md`, renderer README, contributor templates, fictional examples, this plan/spec.

- [x] Document submission paths, responsibilities, identity matching, legacy behavior, and input/report migration.
- [x] Add two fictional attributed example files and retain the legacy example to demonstrate coexistence; use explicit fictional NTIDs.
- [x] Run `task check`, `git diff --check`, and build example artifacts. Export slides and inspect representative email and multi-author/continued slides.
- [x] Review the complete change against the spec, resolve important findings, and record verification here.

## Execution record

- User requested implementation after reviewing the NTID spec. Execute locally without another approval handoff; preserve the existing spec edit. Baseline: 27 tests passed in the preceding turn.
- Task 1 produces the collection consumed by task 2; both use `updates`, optional legacy author, and report version 2. No interface conflict.

- Task 1 complete: initial contribution suite failed against the old NTID/collection contract, then all contribution cases passed. Path validation now uses the actual status root; two nested-directory regressions passed after reproducing their failures.
- Task 2 complete: old renderers/schema export failed the new integration tests; attributed email, slide continuation, schema export/parity, and CLI builds now pass. Escaped ampersands after reproducing the reviewer’s literal-author regression.
- Task 3 complete: templates, migration documentation, fictional NTID roster and two contributions added; original legacy Markdown retained. `task schema` regenerated all schemas. `task check`: 62 tests passed, lint/format and portfolio validation passed. `git diff --check` passed.
- `task demo` passed outside the sandbox (restricted pnpm registry-signature verification failed first). JSON, Markdown, HTML email, and PowerPoint example artifacts regenerated. Visually inspected email in Safari and extracted PowerPoint images for both authors and a temporary continued contribution.
- Independent review found no additional important issues; its ampersand-attribution finding was fixed and tested. Implementation remains uncommitted in the existing workspace as requested work for review; no merge or push performed.
