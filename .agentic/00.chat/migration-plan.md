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
- Reporting skill: `.agentic/00.chat/skills/session-summary.md`

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
- `scripts/shared/chat/`
- `scripts/shared/git/`

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

## Later-Chat Work Queue

1. Add or expand smoke tests for cleanup and reporting workflows.
2. Consider chat-layer script aliases under `scripts/00.chat/` or
   `scripts/chat/`, keeping `scripts/shared/` wrappers for compatibility.
3. Audit session metadata to determine when legacy workflow paths can be
   retired.
4. Add governed cleanup for temporary preflight branches and worktrees once the
   desired retention policy is explicit.
5. Review whether `change-shared-process.md` should keep chat lifecycle notes
   or narrow itself to cross-layer process only.

## Audit

Run:

```bash
bash scripts/shared/chat/audit-chat-layer-migration.sh
```

The audit reports required canonical files, compatibility paths, and remaining
legacy shared workflow references in source/process files. It also inventories
policy references to the retired aggregate summary so future chats can tell
intentional "do not recreate this" guidance apart from generated-artifact
regression. It does not treat historical session logs as migration blockers.
