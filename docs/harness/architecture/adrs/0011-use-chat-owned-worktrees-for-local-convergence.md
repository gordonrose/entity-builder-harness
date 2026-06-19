<!-- agentic-artifact:
owner: harness
kind: adr
purpose: Record the chat-owned worktree model for local convergence and normal task work.
domain: architecture
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-start.md
  - .agentic/00.chat/checklists/before-commit.md
-->

# 0011 Use Chat-Owned Worktrees For Local Convergence

Status: accepted
Date: 2026-06-16

## Context

The harness previously isolated commit-boundary commands in reusable worktrees
while normal chat edits could still happen in the root repository worktree. This
allowed an isolated worktree to advance a chat branch while the root worktree
kept stale staged entries and unrelated local residue. The result was confusing:
the branch history recorded commits, but the user-facing workspace still looked
dirty.

The harness also needs to support multiple chats working in parallel on one
device. In that model, each chat is closer to a local developer-like actor than
to a single command running in one shared checkout.

## Decision

Treat the root repository worktree as the local integration console. Task work
for a chat must happen in that chat's canonical chat-owned worktree, created
from the chat branch and recorded in the session metadata.

New chat startup creates:

- a `chat/*` branch
- a deterministic chat-owned worktree
- a session log that links the session id, branch, and worktree

Commit preparation runs:

```bash
bash scripts/00.chat/worktree/check-write-location/script.sh
```

to prevent task commits from the root integration worktree. Branch freshness is
reported with:

```bash
bash scripts/00.chat/main-refresh/check-chat-is-current-with-main/script.sh
```

Completed chat work passes through a local merge verification workflow before
promotion into local `main`.

## Consequences

This makes each chat's files, index, branch, and session log independently
owned, reducing cross-chat contamination and stale-index surprises. It also
creates a local equivalent of a feature-branch/PR queue: many chat branches can
exist, but local merge into `main` remains explicit.

The model is stricter than the prior commit-boundary-only helper. Agents must
run task commands from the chat worktree, not the root repo. Existing transition
states may still require manual reconciliation before the root worktree can be
treated as a clean integration console.

If useful edits are made outside the chat-owned worktree, treat that as
recovery, not normal commit flow. Import only explicit approved paths with:

```bash
bash scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh \
  --session-log <session-log> \
  --source-worktree <active-worktree> \
  -- <path>...
```

The recovery import refuses ambiguous paths and a dirty target chat worktree so
existing session work is not hidden by the import.
