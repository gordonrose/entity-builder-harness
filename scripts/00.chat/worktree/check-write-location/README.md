<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.worktree.check-write-location.readme
  version: 1
  status: active
  layer: 00.chat
  domain: worktree
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain how chat work is kept inside chat-owned worktrees rather than the
    root integration worktree.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.worktree.check-write-location
    path: scripts/00.chat/worktree/check-write-location/script.sh
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
-->
# Check Write Location

`script.sh` verifies that task work is happening in the chat-owned worktree for
the current `chat/*` branch.

The root worktree is the integration console. It is where completed chat work is
reviewed, merged, and coordinated. Task edits should happen in the sibling
worktree created for that chat branch.

## Mental Model

Each chat branch has one canonical worktree path. If an agent edits from the
root integration worktree, it can mix task work with local integration state. If
an agent edits a chat branch from an unexpected worktree, the harness can no
longer rely on its branch-to-directory ownership model.

This gate protects that invariant before write-heavy or commit-boundary work.

## Checks

The script verifies:

- the current repository path is not the primary/root worktree, unless explicit
  root maintenance is allowed
- the current branch is a `chat/*` branch
- the current path matches the canonical chat worktree path for that branch

On success it prints:

```txt
chat-worktree
```

## Root Maintenance Escape Hatch

Root maintenance is allowed only when explicit:

```bash
AGENTIC_ALLOW_ROOT_WRITE=1 bash scripts/00.chat/worktree/check-write-location/script.sh
```

or:

```bash
bash scripts/00.chat/worktree/check-write-location/script.sh --allow-root-maintenance
```

This is for intentional root/integration maintenance, not ordinary task work.

## What This Does Not Do

- It does not move files into the chat worktree.
- It does not create the chat worktree.
- It does not switch branches.
- It does not decide that root work is safe.
- It does not commit anything.

## Compatibility

The old shared path remains available:

```bash
scripts/00.chat/worktree/check-write-location/script.sh
```

That file is now a compatibility wrapper around the canonical implementation.
