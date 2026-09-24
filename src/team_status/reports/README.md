# Report renderers

`summary.build_report(repository, week)` returns the normalized `WeeklyReport`.
The CLI serializes this to `build/<week>/report.json`, then emits `slides.md`,
`email.md`, and `email.html` from that same object.

`slides.py` creates Marp Markdown. `email.py` creates email Markdown and renders
HTML with inline styles. `markdown.py` holds shared metadata escaping and totals.
Marp CLI is pinned separately in package.json and pnpm-lock.yaml; `task pptx`
exports a reviewed Markdown file. Each report entry contains complete effort
metadata, a derived funding total, and an `updates` list for the exact requested
week (empty when missing). JSON uses schema version 2. Each contribution contains
nullable `author` metadata, using `name` and optional `ntid`, plus its five sections.
Surface missing updates explicitly; never summarize them as no progress.

Email groups contributions under effort and author headings. Slides show effort
metadata once and repeat the author on every contribution slide, including
continuations. The summary builder orders contributions by normalized identity,
with unattributed legacy text first; renderers preserve that order. Legacy text
is labeled "Legacy update — author not recorded". Totals remain per effort.

Standard PowerPoint export contains slide images. The Markdown remains editable.
Pagination uses conservative character and line budgets and rejects oversized
blocks. Review rendered slides for more complex content; the generator is not
a browser layout engine. Email-client-specific testing remains separate from
HTML preview verification.

## Editing report templates

Layouts live in `templates/` inside this package, separate from the repository's
contributor templates. They are included in installed distributions and loaded
independently of the current working directory.

- `email.md.j2`: continuous email structure and authored sections.
- `email.html.j2`: HTML wrapper, title, and outer inline styles.
- `email-styles.json`: inline styles applied to Markdown-generated HTML elements.
- `slides.md.j2`: Marp front matter, theme CSS, and slide boundaries.
- `slide-title.md.j2` and `slide.md.j2`: title and content slide layouts.
- `overview.md.j2`, `effort-metadata.md.j2`, `warnings.md.j2`, and
  `missing-update.md.j2`: shared content fragments.

Rebuild after editing. Keep Markdown whitespace intentional: blank lines separate
blocks, and two trailing spaces create a hard line break. Use `| literal` for
metadata in Markdown; leave authored section Markdown intact. HTML templates
use autoescaping; only HTML produced by the Markdown parser is marked trusted.
Authored content is never evaluated as Jinja source. Missing template variables
raise an error through `StrictUndefined`.

Python retains validation, portfolio calculations, Markdown conversion, and slide
pagination. Contribution slides use a separate compact content budget with room
for the effort title and author label; excessive labels fail explicitly. Layout
edits that change slide capacity may also require adjusting pagination budgets
and reviewing the rendered deck.

Contribution slides group all five sections for one person within an effort, using
compact headings and spacing. Short updates fit on one slide; longer updates
continue at paragraph or bullet boundaries, repeating the effort, author, and
section heading. Effort metadata remains separate. No authored text is summarized.
The `slide-contribution.md.j2` template and `contribution` theme class control
this layout; its pagination budget is separate from portfolio and metadata slides.
