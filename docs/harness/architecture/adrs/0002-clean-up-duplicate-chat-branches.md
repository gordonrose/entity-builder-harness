<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0002-clean-up-duplicate-chat-branches
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the 0002 Clean Up Duplicate Chat Branches architecture decision.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
-->

# 0002 Clean Up Duplicate Chat Branches

Status: accepted
Date: 2026-06-15

## Context

New chat startup can already clean up empty `chat/*` branches and their matching
`commitLogs` directories. A branch is currently considered empty only when it
has no commits beyond the base branch.

Some chat branches are not empty by commit count, but their commits have been
recreated by a later chat branch. Keeping those older branches creates stale
session branches whose work is already represented by the newer branch.

## Decision

New chat startup cleanup may delete older `chat/*` branches whose branch-only
commits are patch-equivalent to commits already present on the current later
chat branch.

The cleanup remains conservative:

- Never delete the current branch.
- Only consider local `chat/*` branches.
- Preserve any branch with branch-only commits that are not duplicated by the
  later chat branch.
- Delete a matching grouped or legacy `commitLogs` session directory only when
  its session metadata names the same branch.
- Keep dry-run mode available for previewing branch and log deletion.

## Consequences

New chat startup can remove stale chat branches that are pure duplicates of
later work, reducing branch and commit-log clutter without requiring manual
cleanup.

The cleanup script becomes more powerful than an empty-branch check, so
duplicate detection must remain deterministic, patch-based, and biased toward
preserving branches when equivalence is unclear.
