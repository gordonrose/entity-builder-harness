<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.readme
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Education Articles.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Education Articles

Public article artifacts should use one folder per article.

Preferred structure:

```text
docs/education/articles/<article-id>/
  article.md
  source-packet.md
  reader-world-research-packet.md
  editor-brief.md
  opening-lab.md
  writer-notes.md
  editor-review.md
  revision-log.md
  scene-cards/
    001-<scene>.md
```

The public article body belongs in `article.md` only. Source packets, notes,
reviews, and revision history stay beside it.

Use `example-ledger.md` to avoid reusing major anecdotes or examples across
articles. A prior article's main anecdote should not become a later article's
opening, main evidence, or primary bridge.

Legacy flat article files may remain until they are next revised through the
source-packet pipeline.
