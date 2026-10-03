<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.workflows.chat-commit
  version: 2
  status: active
  layer: 00.chat
  domain: chat
  disciplines:
  - agentic
  kind: workflow
  purpose: Document Chat Commit Workflow.
  portability:
    class: required
    targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
  used_by:
  - id: repo.agents
    path: AGENTS.md
-->
# Chat Commit Workflow

## Purpose

Own chat task commits, session-log commit recording, and narrow session
bookkeeping checkpoints.

## Required Gates

Before committing approved task work, follow:

```txt
.agentic/00.chat/checklists/before-commit.md
```

## Rules

- Use the current branch session log as the first source of truth.
- Treat `.agentic/00.chat/checklists/before-commit.md` as the authority for
  task-commit approval, write location, staging scope, transcript metrics,
  checkpoint commits, and destructive-action boundaries.
- Do not duplicate before-commit checklist rules in this workflow.

## Preservation Before Session End

Before ending, handing off, or changing workspaces with approved task work,
record the branch, exact HEAD, worktree, remaining paths, checks and next step
in the session log. Include auxiliary recovery ownership and proof gaps.
Use the before-commit checklist for authorized local task checkpoints, then
record the commit and checkpoint the session log. A bookkeeping-only commit
does not preserve uncommitted task source. No merge or push is implied.

Keep verified private preservation copies outside temporary worktrees: use
`scripts/00.chat/export/worktree/script.sh --output <new-durable-zip>` for
working files, and a new Git bundle for checkpoint refs when needed. Preserve
required ignored evidence and source transcripts separately; exports exclude
ignored files and Git history. Use new destinations without overwriting prior
copies; record locations, SHA-256 values, archive readability and bundle
verification in the session log. Keep private transcripts out of published Git.

A failed check does not justify discarding source or bypassing commit gates.
Preserve a verified archive and record the failure when a commit is blocked.
Missing working source uses [transcript draft recovery](recover-transcript-draft.md).
Do not report preservation complete until the recorded copies cover remaining
task paths and can be read independently of the temporary worktree.

## Script Locations

Use canonical `scripts/00.chat/` capabilities named by the checklist. Retired
`scripts/shared/` paths are not a recovery or checkpoint alternative.
