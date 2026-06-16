# Chat Session: 2026-06-16-18-59 missing-governance-stop-condition

<!-- agentic-session
id: 2026-06-16-18-59-task-add-a-repo-wide-harness-governance-principle-that-missi
task: Task: Add a repo-wide harness governance principle that missing governance is a stop condition. If an agent encounters a necessary action, recovery path, workaround, or substitution that is not governed by the current workflow, gate, script, or standard, it must stop, explain the governance gap, and ask whether to update the harness instead of improvising.
branch: chat/2026-06-16-18-59-task-add-a-repo-wide-harness-governance-principle-that-missi
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-16-18-59-task-add-a-repo-wide-harness-governance-principle-that-missi-974428227
layer: harness
mode: implementation
workflow: .agentic/harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-16T17:59:09Z
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_tokens:
-->

## Initial Intent

Task: Add a repo-wide harness governance principle that missing governance is a stop condition. If an agent encounters a necessary action, recovery path, workaround, or substitution that is not governed by the current workflow, gate, script, or standard, it must stop, explain the governance gap, and ask whether to update the harness instead of improvising.

## Branch

`chat/2026-06-16-18-59-task-add-a-repo-wide-harness-governance-principle-that-missi`

## Worktree

`/tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-16-18-59-task-add-a-repo-wide-harness-governance-principle-that-missi-974428227`

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- The motivating example was an ungoverned stash-based merge recovery in another chat. The issue was not stash itself, but ordinary engineering judgment substituting for missing harness governance.

## Decisions Made

- Add the missing-governance principle as a short always-loaded safety invariant in `AGENTS.md`.
- Keep the router-level principle general rather than adding Git-specific recovery procedure.

## Activity Log

### 2026-06-16T17:59:09Z - Session started

Initial intent: Task: Add a repo-wide harness governance principle that missing governance is a stop condition. If an agent encounters a necessary action, recovery path, workaround, or substitution that is not governed by the current workflow, gate, script, or standard, it must stop, explain the governance gap, and ask whether to update the harness instead of improvising.

### 2026-06-16T20:31:39Z - Added router-level governance principle

Updated `AGENTS.md` so missing governance is an explicit stop condition. Ran targeted deterministic process drift validation on `AGENTS.md` and adjusted wording so the check passed without an allow marker.

## Commits

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0012-treat-missing-governance-as-stop-condition.md
Reason: This chat added a durable repo-wide agent operating rule and rejected ordinary engineering improvisation as a fallback for missing harness governance.

## Session Metrics

Raised at UTC: 2026-06-16T17:59:09Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated tokens:

## Notes

- None recorded yet.
