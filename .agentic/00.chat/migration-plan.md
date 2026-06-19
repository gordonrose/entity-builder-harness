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

Guide future chats as chat lifecycle governance moves from compatibility paths
into `.agentic/00.chat/`.

The goal is controlled migration, not a big-bang rename. Legacy paths may stay
in place as compatibility shims while active sessions still reference them.

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

## Compatibility Paths

These paths may remain for existing references, but they must point to or defer
to the canonical chat layer:

- `.agentic/shared/workflows/chat-start-interview.md`
- `.agentic/shared/workflows/main-updated.md`
- `.agentic/shared/workflows/local-convergence.md`
- `.agentic/shared/checklists/before-commit.md`

Script compatibility wrappers under `scripts/shared/chat/` and
`scripts/shared/git/` have been retired. Keep historical references for audit
context, but operative instructions and package scripts should point to
canonical `scripts/00.chat/...` capability paths.

## Migration Rules

- Move ownership prose before moving executable paths.
- Keep old workflow/checklist paths as compatibility pointers until no active
  session metadata or scripts rely on them.
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

## Deferred Migration Queue

1. Audit session metadata to determine when legacy workflow paths can be
   retired.
2. Add governed cleanup for temporary preflight branches and worktrees once the
   desired retention policy is explicit.
3. Review whether `change-shared-process.md` should keep chat lifecycle notes
   or narrow itself to cross-layer process only.
4. Add a conflict classifier script after the conflict type standard has been
   exercised by at least one main-refresh recovery.
5. Add a verification gate that compares unresolved or resolved preflight
   conflict paths with `## Main Refresh Conflicts` entries before promotion.

Do not treat deferred items as permission to improvise. Complete them only when
their stated evidence, policy, or workflow precondition exists.

## Audit

Run:

```bash
bash scripts/00.chat/migration/audit-chat-layer-migration/script.sh
```

The audit reports required canonical files, remaining workflow/checklist
compatibility paths, and remaining legacy shared workflow references in
source/process files. It also inventories policy references to the retired
aggregate summary so future chats can tell intentional "do not recreate this"
guidance apart from generated-artifact regression. It does not treat historical
session logs as migration blockers.
