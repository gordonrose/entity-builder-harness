# Chat Session: 2026-06-16-00-50 any-adrs-based-on-our-existing-harness-that-we-should-probab

<!-- agentic-session
id: 2026-06-16-00-50-any-adrs-based-on-our-existing-harness-that-we-should-probab
task: any ADRs based on our existing harness that we should probably codify?
branch: chat/2026-06-16-00-50-any-adrs-based-on-our-existing-harness-that-we-should-probab
layer: harness
mode: discovery
workflow: .agentic/harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-15T23:50:41Z
latest_commit_at_utc: 2026-06-15T23:54:50Z
latest_commit_sha: d8de467
chat_duration: 249s (00:00:04:09)
estimated_tokens: 621 estimated from session log
-->

## Initial Intent

any ADRs based on our existing harness that we should probably codify?

## Branch

`chat/2026-06-16-00-50-any-adrs-based-on-our-existing-harness-that-we-should-probab`

## Session Log

- Session started.
- Branch created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made

- Decision: Add ADR for bootstrap dirty-worktree preflight
  Rationale: Startup captures inherited dirty state before workflow loading, and future agents need to understand why that blocked response bypasses normal chat-start inspection.

- Decision: Add ADR for session metadata as routing authority
  Rationale: The harness relies on durable session metadata to keep layer, mode, workflow, and gates stable after chat startup.

- Decision: Add ADR for explicit write permission with narrow bookkeeping exception
  Rationale: The harness needs a documented trust boundary that permits routine session bookkeeping after write approval without broadening task or git permissions.

## Activity Log

### 2026-06-15T23:50:41Z - Session started

Initial intent: any ADRs based on our existing harness that we should probably codify?

### 2026-06-15T23:53:19Z - ADRs added

Added ADRs for bootstrap dirty-worktree preflight, session metadata routing authority, and explicit write permission with a narrow bookkeeping exception.


### 2026-06-15T23:54:50Z - Commit recorded

Commit: `d8de467`

Message: docs(harness): codify harness process ADRs

Summary: Added accepted ADRs for bootstrap dirty-worktree preflight, session metadata routing authority, and explicit write permission with a narrow bookkeeping exception.

ADR impact: ADRs added: 0005, 0006, 0007.

## Commits



- Commit: `d8de467`
  Time UTC: 2026-06-15T23:54:50Z
  Message: docs(harness): codify harness process ADRs
  Summary: Added accepted ADRs for bootstrap dirty-worktree preflight, session metadata routing authority, and explicit write permission with a narrow bookkeeping exception.
  ADR impact: ADRs added: 0005, 0006, 0007.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0005-preserve-bootstrap-dirty-worktree-before-workflow-loading.md
Reason: The chat codified three durable harness process decisions in ADRs 0005, 0006, and 0007 to explain existing startup safety, routing, and write-permission behavior.

## Session Metrics

Raised at UTC: 2026-06-15T23:50:41Z
Latest commit at UTC: 2026-06-15T23:54:50Z
Latest commit SHA: d8de467
Chat duration: 249s (00:00:04:09)
Estimated tokens: 621 estimated from session log

## Notes

- None recorded yet.
