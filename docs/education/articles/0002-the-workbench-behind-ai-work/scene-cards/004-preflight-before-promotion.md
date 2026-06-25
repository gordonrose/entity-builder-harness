<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0002-the-workbench-behind-ai-work.scene-cards.004-preflight-before-promotion
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: 'Document Scene Card: Preflight Before Promotion.'
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Scene Card: Preflight Before Promotion

## Source

`commitLogs/2026/jun/16/2026-06-16-22-23-main-refresh-recovery-design/README.md`
and `commitLogs/2026/jun/16/2026-06-16-22-32-govern-local-convergence/README.md`

## What Happened

The harness moved branch refresh and local convergence into a governed path:
classify dirty state, checkpoint if needed, rehearse the merge in a temporary
worktree, verify local convergence, and promote only after the result is known.

## Human Pressure

The author wanted a way to absorb main changes without turning the active chat
worktree into an experiment.

## Visible Objects

- dirty-state classifier
- temporary preflight worktree
- local convergence verifier
- chat branch
- local `main`

## Why It Matters

Preflight is the practical answer to "just trust the agent." It lets the system
try the risky thing somewhere observable before changing the active path.

## Use In Article

Mechanism section.
