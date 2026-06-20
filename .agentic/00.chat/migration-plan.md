<!-- agentic-artifact:
owner: 00.chat
kind: migration-plan
purpose: Track migration from legacy chat lifecycle paths to canonical 00.chat paths.
domain: migration
portability: llm-workbench-required
used_by:
  - scripts/00.chat/migration/audit-chat-layer-migration/script.sh
  - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
-->

# 00.chat Migration Plan

## Purpose

Guide future chats as chat lifecycle governance finishes moving from
compatibility paths into `.agentic/00.chat/`.

The goal is controlled migration, not a big-bang rename. Legacy paths may stay
in historical references, but operative chat lifecycle governance belongs in
`.agentic/00.chat/`.

## Current Canonical Surfaces

- Layer overview: `.agentic/00.chat/README.md`
- Workflow index: `.agentic/00.chat/workflows/README.md`
- Before-commit checklist: `.agentic/00.chat/checklists/before-commit.md`
- Main refresh conflict type standard:
  `.agentic/00.chat/standards/main-refresh-conflict-types.md`
- Reporting skill: `.agentic/00.chat/skills/session-summary.md`
- Public chat commands: `package.json` `chat:*` scripts

## Migrated Workflow Ownership

- Chat startup: `.agentic/00.chat/workflows/chat-start.md`
- Chat task commits: `.agentic/00.chat/workflows/chat-commit.md`
- Refresh from main: `.agentic/00.chat/workflows/chat-refresh-from-main.md`
- Promote to main: `.agentic/00.chat/workflows/chat-promote-to-main.md`
- Cleanup: `.agentic/00.chat/workflows/chat-cleanup.md`
- Reporting: `.agentic/00.chat/workflows/chat-reporting.md`

## Retired Compatibility Paths

These old shared paths are retired. Historical references may mention them, but
operative instructions, audits, and package scripts should point to the
canonical chat layer:

- `.agentic/shared/workflows/chat-start-interview.md`
- `.agentic/shared/workflows/main-updated.md`
- `.agentic/shared/workflows/local-convergence.md`
- `.agentic/shared/checklists/before-commit.md`
- `.agentic/shared/workflows/default.md`
- `.agentic/harness/workflows/default.md`

Script compatibility wrappers under `scripts/shared/chat/` and
`scripts/shared/git/` have been retired. Keep historical references for audit
context, but operative instructions and package scripts should point to
canonical `scripts/00.chat/...` capability paths.

## Migration Rules

- Move ownership prose before moving executable paths.
- Keep retired workflow/checklist paths absent unless an active session recovery
  explicitly requires a governed restore.
- Preserve exact blocked responses when changing workflow ownership.
- Keep scripts deterministic; do not replace scriptable gates with prose.
- Maintain focused smoke tests for startup, classification, refresh, commit,
  reporting, and cleanup behavior before moving scripts.
- Do not migrate destructive cleanup commands without dry-run and explicit
  approval gates.
- Do not reintroduce tracked aggregate `commitLogs/README.md`.

## Completed Migration Queue

1. Added canonical chat lifecycle workflows under `.agentic/00.chat/workflows/`.
2. Added chat-layer command, cleanup, reporting, and conflict-recording package
   scripts in `package.json`.
3. Migrated chat lifecycle implementation paths to canonical
   `scripts/00.chat/...` capabilities and retired old `scripts/shared/chat/`
   and `scripts/shared/git/` wrappers.
4. Added audit coverage for the chat-layer package script surface.
5. Kept focused smoke tests for startup, classification, refresh, commit,
   reporting, cleanup, commands, and package scripts.
6. Audited active session metadata and retired redundant shared chat lifecycle
   pointers, duplicate before-commit compatibility checklist, and placeholder
   default workflows.
7. Added governed cleanup for temporary preflight branches and worktrees when a
   rehearsed main refresh is applied. The apply helper removes the promoted
   preflight branch/worktree, removes clean stale sibling preflights that are
   already ancestors of the promoted chat branch, and reports unsafe stale
   preflights without deleting them.
8. Narrowed `.agentic/shared/workflows/change-shared-process.md` so it keeps
   shared-process ownership and chat harness entry gates, while delegating
   chat lifecycle commit recording, transcript metrics, bookkeeping checkpoint,
   and commit-log deletion rules to `.agentic/00.chat/checklists/before-commit.md`.
9. Added a deterministic main-refresh conflict classifier based on the conflict
   type standard and the first recorded main-refresh recovery evidence.
10. Added a preflight conflict audit verification gate that compares conflict
    paths with `## Main Refresh Conflicts` entries before applying a resolved
    preflight refresh.

## Deferred Migration Queue

No deferred migration items remain. Future conflict types or verification
expansions should be added only when new main-refresh recovery evidence exposes
a gap in the current standard or scripts.

Do not treat deferred items as permission to improvise. Complete them only when
their stated evidence, policy, or workflow precondition exists.

## Audit

Run:

```bash
bash scripts/00.chat/migration/audit-chat-layer-migration/script.sh
```

The audit reports required canonical files, retired compatibility paths that
should stay absent, and remaining retired compatibility references in
source/process files. It also inventories policy references to the retired
aggregate summary so future chats can tell intentional "do not recreate this"
guidance apart from generated-artifact regression. It does not treat historical
session logs as migration blockers.
