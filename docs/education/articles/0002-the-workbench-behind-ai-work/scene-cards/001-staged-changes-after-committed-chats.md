<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0002-the-workbench-behind-ai-work.scene-cards.001-staged-changes-after-committed-chats
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: 'Document Scene Card: Staged Changes After Committed Chats.'
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Scene Card: Staged Changes After Committed Chats

## Source

`commitLogs/2026/jun/16/2026-06-16-14-19-local-chat-worktree-strategy/README.md`

## What Happened

The author had committed chat work, but the root checkout still showed about 15
staged changes. The workspace looked as if the work had not been committed even
though the chat branch had moved forward.

## Human Pressure

The author needed to know whether work was safe, duplicated, stale, or simply
visible from the wrong place.

## Visible Objects

- staged entries
- root worktree
- chat branch
- isolated worktree
- session log

## Why It Matters

The scene makes the article concrete immediately. It turns "AI workflow
governance" into a normal working fear: the tool says one thing, the record says
another, and now someone has to decide what is safe.

## Use In Article

Opening scene.
