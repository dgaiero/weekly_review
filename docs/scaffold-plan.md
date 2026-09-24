# Scaffold implementation plan

1. Define a Python package, development tooling, and executable CLI tests.
   Test valid reports, data bounds, duplicate YAML keys, missing updates,
   overallocations, malformed Markdown, fenced headings, and missing roots.
2. Implement Pydantic contracts, safe YAML ingestion, Markdown section parsing,
   repository validation, and normalized report assembly.
3. Add templates, an isolated example repository, schema exports, Taskfile,
   GitLab CI, and OpenCode project guidance.
4. Run the full tests, lint/format checks, package build, and example workflow.

Keep the production portfolio empty. Preserve authored Markdown verbatim in
the normalized report. Do not infer accomplishments or carry stale updates.
