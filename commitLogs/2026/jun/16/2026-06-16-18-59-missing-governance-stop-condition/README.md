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
latest_commit_at_utc: 2026-06-16T21:15:32Z
latest_commit_sha: c99c38e
chat_duration: 11783s (00:03:16:23)
estimated_tokens: 1409 estimated from session log
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
- Add a detailed harness standard for missing governance rather than a hook, because unexpectedness is judgment-heavy and hooks should be reserved for deterministic lifecycle triggers.
- Wire the missing-governance standard into capability resolution and harness-change workflow discovery without duplicating the full rule.

## Activity Log

### 2026-06-16T17:59:09Z - Session started

Initial intent: Task: Add a repo-wide harness governance principle that missing governance is a stop condition. If an agent encounters a necessary action, recovery path, workaround, or substitution that is not governed by the current workflow, gate, script, or standard, it must stop, explain the governance gap, and ask whether to update the harness instead of improvising.

### 2026-06-16T20:31:39Z - Added router-level governance principle

Updated `AGENTS.md` so missing governance is an explicit stop condition. Ran targeted deterministic process drift validation on `AGENTS.md` and adjusted wording so the check passed without an allow marker.

### 2026-06-16T21:01:24Z - Added detailed harness standard

Added `.agentic/harness/standards/missing-governance-stop-condition.md` and indexed it from `.agentic/harness/README.md`. The standard defines missing governance, the stop response, examples, one-off exception logging, and when hooks are appropriate.

### 2026-06-16T21:09:26Z - Wired standard into workflow discovery

Updated `.agentic/shared/workflows/capability-resolution-workflow.md` and `.agentic/harness/workflows/change-harness.md` so agents know where to look when a required action is not governed by the selected workflow, gate, script, or standard.


### 2026-06-16T20:45:29Z - Commit recorded

Commit: `5b26b1b`

Message: Add missing governance stop condition

Summary: Added a repo-wide missing-governance stop condition to AGENTS.md and recorded ADR 0012 for the operating principle.

ADR impact: ADR 0012 accepted


### 2026-06-16T21:07:38Z - Commit recorded

Commit: `2b978eb`

Message: Add missing governance standard

Summary: Added a harness standard that defines missing governance, the required blocked response, examples, one-off exceptions, and hook guidance.

ADR impact: ADR 0012 elaborated


### 2026-06-16T21:15:32Z - Commit recorded

Commit: `c99c38e`

Message: Wire missing governance standard into workflows

Summary: Linked capability resolution and harness-change workflow to the missing-governance standard so agents can find it when a required action is not governed.

ADR impact: ADR 0012 reinforced

## Commits



- Commit: `5b26b1b`
  Time UTC: 2026-06-16T20:45:29Z
  Message: Add missing governance stop condition
  Summary: Added a repo-wide missing-governance stop condition to AGENTS.md and recorded ADR 0012 for the operating principle.
  ADR impact: ADR 0012 accepted


- Commit: `2b978eb`
  Time UTC: 2026-06-16T21:07:38Z
  Message: Add missing governance standard
  Summary: Added a harness standard that defines missing governance, the required blocked response, examples, one-off exceptions, and hook guidance.
  ADR impact: ADR 0012 elaborated


- Commit: `c99c38e`
  Time UTC: 2026-06-16T21:15:32Z
  Message: Wire missing governance standard into workflows
  Summary: Linked capability resolution and harness-change workflow to the missing-governance standard so agents can find it when a required action is not governed.
  ADR impact: ADR 0012 reinforced

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0012-treat-missing-governance-as-stop-condition.md
Reason: This chat added a durable repo-wide agent operating rule and rejected ordinary engineering improvisation as a fallback for missing harness governance.

## Session Metrics

Raised at UTC: 2026-06-16T17:59:09Z
Latest commit at UTC: 2026-06-16T21:15:32Z
Latest commit SHA: c99c38e
Chat duration: 11783s (00:03:16:23)
Estimated tokens: 1409 estimated from session log

## Notes

- None recorded yet.
