# Chat Session: 2026-06-20-14-44 tighten-promotion-refresh-to-use-preflight-for-diverged-chat

<!-- agentic-session
id: 2026-06-20-14-44-tighten-promotion-refresh-to-use-preflight-for-diverged-chat
task: tighten promotion refresh to use preflight for diverged chat branches
branch: chat/2026-06-20-14-44-tighten-promotion-refresh-to-use-preflight-for-diverged-chat
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-20-14-44-tighten-promotion-refresh-to-use-preflight-for-diverged-chat-3673595137
layer: shared
mode: implementation
workflow: .agentic/shared/workflows/change-shared-process.md
status: ready
raised_at_utc: 2026-06-20T13:44:33Z
codex_session_log_path: /home/owner/.codex/sessions/2026/06/20/rollout-2026-06-20T09-19-18-019ee41c-e2b4-7bb2-a38c-bd5bb063dab4.jsonl
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

tighten promotion refresh to use preflight for diverged chat branches

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.
- Corrected the auto-classified mode from execution to implementation because
  this chat changes promotion-refresh workflow guidance.

## Questions Asked

- None recorded yet.

## Issues Raised

- The prior merge-to-main flow used the direct promotion-refresh instructions
  from `chat-promote-to-main.md`, even though the dedicated refresh workflow
  prefers preflight for branches with task commits.

## Decisions Made

- Promotion refresh for `blocked-behind` and `blocked-diverged` chat branches
  should use the rehearsed preflight refresh flow before mutating the active
  chat branch.

## Activity Log

### 2026-06-20T13:44:33Z - Session started

Initial intent: tighten promotion refresh to use preflight for diverged chat branches

### 2026-06-20T13:45:34Z - Promotion refresh guidance tightened

Updated `.agentic/00.chat/workflows/chat-promote-to-main.md` so
`blocked-behind` and `blocked-diverged` promotion refresh routes through the
rehearsed preflight refresh flow in `chat-refresh-from-main.md` instead of
teaching a direct merge into the active chat branch.

Verification:

- `bash scripts/01.harness/check-deterministic-process-drift.sh --paths .agentic/00.chat/workflows/chat-promote-to-main.md`
- `bash scripts/00.chat/migration/audit-chat-layer-migration/script.sh`

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: Workflow clarification only; this aligns existing promotion guidance
with the already-governed rehearsed refresh/preflight capability.

## Session Metrics

Raised at UTC: 2026-06-20T13:44:33Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.
