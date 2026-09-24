# Working on Team Status

Read README.md and docs/design.md before changing repository contracts.
Use Python, uv, Pydantic, and Taskfile. Run `task check` before concluding work.
Run `task schema` when models change and include the generated schemas.

Effort YAML and weekly Markdown are authored source data. Never invent progress,
funding, owners, risks, or commitments. Preserve weekly Markdown in reports.
Missing updates and total staffing above 100% are warnings; malformed data is an error.
Renderers consume WeeklyReport; they must not read effort files independently.
Keep examples under examples/, separate from the real efforts/ portfolio.

Do not introduce a UI, automatic email delivery, AI summarization, or GitLab
credentials without an explicit task. The default development model/provider
is configured by each developer in OpenCode, not pinned in this repository.
