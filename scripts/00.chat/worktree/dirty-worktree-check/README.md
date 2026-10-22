<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.script.worktree.dirty-worktree-check.readme
  version: 1
  status: active
  created_on: "2026-06-19"
  updated_on: "2026-10-22"
  layer: 00.chat
  domain: worktree
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain clean, dirty, and session-bookkeeping-only worktree checks.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.worktree.dirty-worktree-check
    path: scripts/00.chat/worktree/dirty-worktree-check/script.sh
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
-->
# Dirty Worktree Check

`script.sh` classifies the current worktree. Its output is evidence for the
calling workflow, which decides whether its specific operation can proceed.
It does not impose a confirmation gate on ordinary inspection or authorized
task edits.

## Modes

Default mode:

```bash
bash scripts/00.chat/worktree/dirty-worktree-check/script.sh
```

Outputs:

- `clean` and exits `0` when there are no Git changes
- `dirty` and exits non-zero when any tracked, staged, or untracked file is
  dirty

Session-bookkeeping mode:

```bash
bash scripts/00.chat/worktree/dirty-worktree-check/script.sh --allow-session-bookkeeping
```

This mode allows dirt only when all dirty paths are the current chat session log.
It prints `bookkeeping-only` and exits `0` in that case.

## Mental Model

Dirty state is not always bad. Sometimes the only dirty file is the session log
after a task commit has been recorded. That is expected bookkeeping and can be
checkpointed separately.

Task edits also normally make a worktree dirty. Follow the existing-change
guidance in `.agentic/00.chat/workflows/chat-start.md#existing-changes` to preserve
that work and resolve concrete overlaps. Merge, refresh, and cleanup retain
their operation-specific safeguards.

## What This Does Not Do

- It does not clean the worktree.
- It does not stage files.
- It does not commit session bookkeeping.
- It does not decide whether unrelated dirt is safe.
- It does not inspect file contents beyond identifying dirty paths.

## Compatibility

The old shared path remains available:

```bash
scripts/00.chat/worktree/dirty-worktree-check/script.sh
```

That file is now a compatibility wrapper around the canonical implementation.
