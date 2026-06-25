<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.architecture.adr.readme
  version: 1
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: adr
  purpose: Document Education Architecture Decision Records.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Education Architecture Decision Records

This directory records durable decisions about the education layer: audience,
pedagogy, public voice, content strategy, and recurring educational artifact
shape.

Use these ADRs when a decision changes how repo work becomes teaching material.
Do not use them for routine taste tweaks, one-off article edits, or temporary
feedback. Put those in `.agentic/education/profiles/` or
`.agentic/education/feedback/`.

## Records

- [0001 Orient AI Hype Audiences Without Humiliation](0001-orient-ai-hype-audiences-without-humiliation.md)
- [0002 Use Article Editor Agent Before Public Article Drafting](0002-use-article-editor-agent-before-public-article-drafting.md)
- [0003 Separate Article Editor And Writer Agents](0003-separate-article-editor-and-writer-agents.md)
- [0004 Require Source Packets For Public Articles](0004-require-source-packets-for-public-articles.md)
- [0005 Require Reader-World Research For Public Articles](0005-require-reader-world-research-for-public-articles.md)
