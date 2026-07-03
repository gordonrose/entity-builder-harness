<!-- agentic-artifact:
schema: agentic-artifact/v2
id: shared.workflows.change-shared-process
version: 1
status: active
layer: 06.shared
domain: process
disciplines:
- agentic
kind: workflow
purpose: Govern changes to cross-layer shared process.
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

# Change Shared Process Workflow

## Use When

Use this when a request changes cross-layer git, commit, merge, handoff,
deployment, release, or context-preservation process.

Chat lifecycle changes belong to `.agentic/00.chat/`.

## Required Gates

Before editing files:

```bash
bash scripts/00.chat/worktree/dirty-worktree-check/script.sh --allow-session-bookkeeping
```

`bookkeeping-only` is acceptable after explicit write permission for the chat.
<!-- deterministic-check: allow reason="workflow defines exact blocked response around dirty-worktree gate output" -->
If dirty, respond exactly:

```txt
Blocked: dirty worktree. Confirm proceed? Layer: shared. Mode: <mode>. Workflow: .agentic/shared/workflows/change-shared-process.md
```

Do not edit files while blocked.

## Rules

- Use the current branch session log as the first source of truth.
- Keep `AGENTS.md` as a router; put procedure in shared workflows, checklists,
  gates, or scripts.
- Prefer deterministic scripts for repeatable checks.
- Do not create a task commit, push, delete branches, rewrite history, discard
  work, overwrite work, or perform destructive actions without explicit user
  approval.
- Chat task work must run in the chat-owned worktree recorded in the current
  session log. The root worktree is the local integration console and must not
  receive task edits, staging, formatting, or commits.
- After explicit write permission for the chat, routine session bookkeeping may
  be staged without another prompt when limited to the current chat session log.
- Preserve unrelated user changes in a dirty worktree.
- Before any commit, complete `.agentic/00.chat/checklists/before-commit.md`.

## Chat Harness Delegation

Shared-process changes still run inside the chat harness. Before writing, run:

```bash
bash scripts/00.chat/worktree/check-write-location/script.sh
```

<!-- deterministic-check: allow reason="ensure-chat-worktree enforces worktree creation and verification; workflow states when agents should invoke it" -->
If a session log exists but its worktree is missing, recreate or verify it with:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/worktree/ensure-chat-worktree/script.sh <session-log>
```

The chat-owned worktree has its own files and index. Stage only approved
repository-relative paths inside that worktree. The root worktree remains the
local convergence console.

Do not duplicate chat lifecycle, commit recording, transcript metrics,
bookkeeping checkpoint, or commit-log deletion rules here. Use the canonical
before-commit checklist for those gates:

```
.agentic/00.chat/checklists/before-commit.md
```
