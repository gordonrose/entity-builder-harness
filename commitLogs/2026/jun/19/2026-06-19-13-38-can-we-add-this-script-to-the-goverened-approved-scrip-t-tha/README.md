# Chat Session: 2026-06-19-13-38 can-we-add-this-script-to-the-goverened-approved-scrip-t-tha

<!-- agentic-session
id: 2026-06-19-13-38-can-we-add-this-script-to-the-goverened-approved-scrip-t-tha
task: can we add this script to the goverened approved scrip t that doesn't need manual approval? bash scripts/shared/git/checkpoint-chat-session-log.sh
branch: chat/2026-06-19-13-38-can-we-add-this-script-to-the-goverened-approved-scrip-t-tha
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-19-13-38-can-we-add-this-script-to-the-goverened-approved-scrip-t-tha-567146558
layer: chat
mode: implementation
workflow: .agentic/00.chat/workflows/chat-commit.md
status: ready
raised_at_utc: 2026-06-19T12:38:12Z
codex_session_log_path:
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

can we add this script to the goverened approved scrip t that doesn't need manual approval? bash scripts/shared/git/checkpoint-chat-session-log.sh

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- User asked whether `scripts/shared/git/checkpoint-chat-session-log.sh` could
  be added to the governed approved scripts that do not need repeated manual
  approval.
- User asked whether the harness was malfunctioning after a recent chat still
  requested approval for that direct command.
- User asked for a remediation plan, risk review, step-by-step execution, and
  gate-wiring decision.

## Issues Raised

- The governed runner already allowed `checkpoint-chat-session-log.sh`, but
  active workflow/checklist examples still taught agents to run the helper
  directly.
- The stale direct command examples could trigger repeated manual approval and
  bypass the intended vendor permission path.
- A broad checker could create false positives by flagging implementation
  scripts, smoke tests, or historical ADR examples that are not active
  agent-facing instructions.

## Decisions Made

- Approval-sensitive governed scripts shown as active agent-facing commands
  should route through `scripts/shared/harness/run-governed-script.sh
  --approved-action`.
- `--approved-action` does not grant approval by itself; it records that the
  current workflow and chat already contain approval for the action class.
- Direct script calls remain allowed inside implementation scripts, smoke
  tests, fixture setup, and historical or explanatory prose when they are not
  active instructions to an agent.
- Add a deterministic command-drift checker and wire it into the chat
  before-commit preparation gate.

## Activity Log

### 2026-06-19T12:38:12Z - Session started

Initial intent: can we add this script to the goverened approved scrip t that doesn't need manual approval? bash scripts/shared/git/checkpoint-chat-session-log.sh

### 2026-06-19T15:02:30Z - Governed script command drift remediation

Reviewed the governed runner, vendor permission files, and active harness
workflow/checklist examples. Patched active agent-facing command examples for
approval-sensitive governed scripts to use the governed runner, added a
standard rule for future artifacts, added a deterministic drift checker with
smoke coverage, and wired the checker into the before-commit preparation gate.

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: The change enforces the existing governed-script permission model and
  command-shape policy in workflows, standards, and deterministic checks without
  introducing a new harness architecture decision.

## Session Metrics

Raised at UTC: 2026-06-19T12:38:12Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- No commit has been created yet. User granted permission to run commit-boundary
  preparation steps, but task commit still requires explicit commit approval.
