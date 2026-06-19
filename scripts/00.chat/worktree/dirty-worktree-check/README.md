<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain clean, dirty, and session-bookkeeping-only worktree checks.
domain: worktree
portability: llm-workbench-required
used_by:
  - scripts/00.chat/worktree/dirty-worktree-check/script.sh
  - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
-->

# Dirty Worktree Check

`script.sh` reports whether the current worktree is clean enough for the next
governed step.

It is intentionally small: it answers one question before startup, refresh,
commit, or promotion workflows continue.

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

Other dirty state is ambiguous. This helper stops workflows before they
accidentally continue across unreviewed or unrelated changes.

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
