# Chat Session: 2026-06-16-22-23 main-refresh-recovery-design

<!-- agentic-session
id: 2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro
task: Task: Explore and design a governed main-refresh recovery process for chat branches, including the specific case where session bookkeeping or generated commit log summaries block merging updated main. I want to understand the Git mechanics, including stash, before deciding the governed recovery path. The goal is not to improvise a fix, but to define a deterministic harness approach with scripts where appropriate.Session context:We added a repo-wide principle that missing governance is a stop condition:- AGENTS.md now says missing governance must stop before acting.- ADR 0012 records the decision.- .agentic/harness/standards/missing-governance-stop-condition.md defines the detailed standard.- capability-resolution-workflow.md and change-harness.md now point to that standard.Motivating failure:In another chat, main had been updated. The agent tried to refresh a chat branch. Git refused because local session bookkeeping / commitLogs/README.md overlapped with main. The agent then used git stash, merged main, popped the stash, hit a commitLogs/README.md conflict, regenerated the summary, and resolved it. That may have been technically reasonable, but it was not governed by the workflow, so it was wrong for this harness.Files to inspect:- .agentic/shared/workflows/main-updated.md- .agentic/shared/workflows/change-shared-process.md- .agentic/harness/standards/missing-governance-stop-condition.md- scripts/shared/git/main-update-status.sh- scripts/shared/git/dirty-worktree-check.sh- scripts/shared/chat/generate-commit-log-summary.sh- scripts/shared/git/check-write-location.sh- scripts/shared/git/check-commit-prerequisites.sh- scripts/shared/git/checkpoint-chat-session-log.shQuestions to answer before implementing:1. What are the exact Git states involved when main changes and a chat branch has local session bookkeeping?2. What does stash actually do here, including tracked files, untracked files, index state, conflicts on pop, and stash retention?3. When is stash appropriate, and when is it too broad or risky for this harness?4. Can we avoid stash for the generated commit log summary case?5. What deterministic scripts would make this safe over time?6. What should the workflow do when the case is outside the deterministic path?7. What should be recorded in the session log?Desired output:First, teach me the Git mechanics in plain language, especially stash.Then propose a governed recovery design for main-updated.md.Prefer deterministic scripts for repeatable checks/actions.Do not implement until I approve the design.Potential design direction:- The workflow should stop when dirty state blocks refresh unless the dirty state is explicitly classified as recoverable session bookkeeping.- Add a script that inspects the dirty state and classifies it, instead of relying on agent judgment.- For generated commitLogs/README.md, prefer a deterministic regenerate-and-verify path if safe.- For stash, either prohibit it by default or govern it tightly with exact scope, message, stash id recording, apply/pop behavior, conflict handling, and retain/drop rules.- If the recovery is not covered, use the missing-governance blocked response and ask whether to update the harness.Mode:Start in discovery/planning. Do not edit files until explicitly granted write permission.
branch: chat/2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-1280776195
layer: harness
mode: planning
workflow: .agentic/harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-16T21:23:03Z
latest_commit_at_utc: 2026-06-17T13:49:47Z
latest_commit_sha: 67839a4
chat_duration: 59204s (00:16:26:44)
estimated_tokens: 3518 estimated from session log
-->

## Initial Intent

Task: Explore and design a governed main-refresh recovery process for chat branches, including the specific case where session bookkeeping or generated commit log summaries block merging updated main. I want to understand the Git mechanics, including stash, before deciding the governed recovery path. The goal is not to improvise a fix, but to define a deterministic harness approach with scripts where appropriate.Session context:We added a repo-wide principle that missing governance is a stop condition:- AGENTS.md now says missing governance must stop before acting.- ADR 0012 records the decision.- .agentic/harness/standards/missing-governance-stop-condition.md defines the detailed standard.- capability-resolution-workflow.md and change-harness.md now point to that standard.Motivating failure:In another chat, main had been updated. The agent tried to refresh a chat branch. Git refused because local session bookkeeping / commitLogs/README.md overlapped with main. The agent then used git stash, merged main, popped the stash, hit a commitLogs/README.md conflict, regenerated the summary, and resolved it. That may have been technically reasonable, but it was not governed by the workflow, so it was wrong for this harness.Files to inspect:- .agentic/shared/workflows/main-updated.md- .agentic/shared/workflows/change-shared-process.md- .agentic/harness/standards/missing-governance-stop-condition.md- scripts/shared/git/main-update-status.sh- scripts/shared/git/dirty-worktree-check.sh- scripts/shared/chat/generate-commit-log-summary.sh- scripts/shared/git/check-write-location.sh- scripts/shared/git/check-commit-prerequisites.sh- scripts/shared/git/checkpoint-chat-session-log.shQuestions to answer before implementing:1. What are the exact Git states involved when main changes and a chat branch has local session bookkeeping?2. What does stash actually do here, including tracked files, untracked files, index state, conflicts on pop, and stash retention?3. When is stash appropriate, and when is it too broad or risky for this harness?4. Can we avoid stash for the generated commit log summary case?5. What deterministic scripts would make this safe over time?6. What should the workflow do when the case is outside the deterministic path?7. What should be recorded in the session log?Desired output:First, teach me the Git mechanics in plain language, especially stash.Then propose a governed recovery design for main-updated.md.Prefer deterministic scripts for repeatable checks/actions.Do not implement until I approve the design.Potential design direction:- The workflow should stop when dirty state blocks refresh unless the dirty state is explicitly classified as recoverable session bookkeeping.- Add a script that inspects the dirty state and classifies it, instead of relying on agent judgment.- For generated commitLogs/README.md, prefer a deterministic regenerate-and-verify path if safe.- For stash, either prohibit it by default or govern it tightly with exact scope, message, stash id recording, apply/pop behavior, conflict handling, and retain/drop rules.- If the recovery is not covered, use the missing-governance blocked response and ask whether to update the harness.Mode:Start in discovery/planning. Do not edit files until explicitly granted write permission.

## Branch

`chat/2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro`

## Worktree

`/tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-1280776195`

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked



- Asked: Whether the harness now governs non-generated LLM or automatic conflict resolution
  Response: No. Normal source, docs, scripts, and workflow conflicts still require stopping unless a future governed resolver path or one-off exception is approved.

## Issues Raised

- None recorded yet.

## Decisions Made



- Decision: Generated commit log summary uses restore and regenerate
  Rationale: commitLogs/README.md is derived evidence; when verified reproducible, it can be restored before refresh and regenerated after main is integrated instead of being stashed.


- Decision: Main refresh uses checkpoint then preflight promotion
  Rationale: Normal repo work should become an explicit chat checkpoint before refresh; the merge from main is rehearsed in a temporary worktree and promoted only after a clean result and approval.


- Decision: Stash is excluded from default main refresh
  Rationale: The stash stack is shared by repo worktrees and risks cross-chat contamination unless a future governed stash capability records scope, identity, apply/drop behavior, and conflicts.


- Decision: Conflict resolution remains blocked outside governed classes
  Rationale: The harness can now govern clean refreshes, generated summary recovery, checkpointed work, preflight promotion, and later cleanup; LLM or automatic resolution of normal repo conflicts remains missing governance and should stop.

## Activity Log

### 2026-06-16T21:23:03Z - Session started

Initial intent: Task: Explore and design a governed main-refresh recovery process for chat branches, including the specific case where session bookkeeping or generated commit log summaries block merging updated main. I want to understand the Git mechanics, including stash, before deciding the governed recovery path. The goal is not to improvise a fix, but to define a deterministic harness approach with scripts where appropriate.Session context:We added a repo-wide principle that missing governance is a stop condition:- AGENTS.md now says missing governance must stop before acting.- ADR 0012 records the decision.- .agentic/harness/standards/missing-governance-stop-condition.md defines the detailed standard.- capability-resolution-workflow.md and change-harness.md now point to that standard.Motivating failure:In another chat, main had been updated. The agent tried to refresh a chat branch. Git refused because local session bookkeeping / commitLogs/README.md overlapped with main. The agent then used git stash, merged main, popped the stash, hit a commitLogs/README.md conflict, regenerated the summary, and resolved it. That may have been technically reasonable, but it was not governed by the workflow, so it was wrong for this harness.Files to inspect:- .agentic/shared/workflows/main-updated.md- .agentic/shared/workflows/change-shared-process.md- .agentic/harness/standards/missing-governance-stop-condition.md- scripts/shared/git/main-update-status.sh- scripts/shared/git/dirty-worktree-check.sh- scripts/shared/chat/generate-commit-log-summary.sh- scripts/shared/git/check-write-location.sh- scripts/shared/git/check-commit-prerequisites.sh- scripts/shared/git/checkpoint-chat-session-log.shQuestions to answer before implementing:1. What are the exact Git states involved when main changes and a chat branch has local session bookkeeping?2. What does stash actually do here, including tracked files, untracked files, index state, conflicts on pop, and stash retention?3. When is stash appropriate, and when is it too broad or risky for this harness?4. Can we avoid stash for the generated commit log summary case?5. What deterministic scripts would make this safe over time?6. What should the workflow do when the case is outside the deterministic path?7. What should be recorded in the session log?Desired output:First, teach me the Git mechanics in plain language, especially stash.Then propose a governed recovery design for main-updated.md.Prefer deterministic scripts for repeatable checks/actions.Do not implement until I approve the design.Potential design direction:- The workflow should stop when dirty state blocks refresh unless the dirty state is explicitly classified as recoverable session bookkeeping.- Add a script that inspects the dirty state and classifies it, instead of relying on agent judgment.- For generated commitLogs/README.md, prefer a deterministic regenerate-and-verify path if safe.- For stash, either prohibit it by default or govern it tightly with exact scope, message, stash id recording, apply/pop behavior, conflict handling, and retain/drop rules.- If the recovery is not covered, use the missing-governance blocked response and ask whether to update the harness.Mode:Start in discovery/planning. Do not edit files until explicitly granted write permission.


### 2026-06-17T11:52:39Z - Decision

Decision: Main refresh uses checkpoint then preflight promotion

Rationale: Normal repo work should become an explicit chat checkpoint before refresh; the merge from main is rehearsed in a temporary worktree and promoted only after a clean result and approval.


### 2026-06-17T11:52:39Z - Decision

Decision: Stash is excluded from default main refresh

Rationale: The stash stack is shared by repo worktrees and risks cross-chat contamination unless a future governed stash capability records scope, identity, apply/drop behavior, and conflicts.


### 2026-06-17T11:52:39Z - ADR disposition

ADR needed: no

Reason: This updates the existing main-updated workflow and scripts to make the already-discussed recovery strategy executable; no new cross-cutting architecture decision beyond the workflow change is introduced.


### 2026-06-17T13:48:55Z - Question

Asked: Whether the harness now governs non-generated LLM or automatic conflict resolution

Response: No. Normal source, docs, scripts, and workflow conflicts still require stopping unless a future governed resolver path or one-off exception is approved.


### 2026-06-17T13:49:47Z - Commit recorded

Commit: `67839a4`

Message: Harden main refresh recovery workflow

Summary: Adds dirty-state classification, generated-summary verification, preflight main refresh promotion, and smoke tests for the governed recovery flow.

ADR impact: No new ADR; implements the planned main-updated workflow hardening.

## Commits



- Commit: `67839a4`
  Time UTC: 2026-06-17T13:49:47Z
  Message: Harden main refresh recovery workflow
  Summary: Adds dirty-state classification, generated-summary verification, preflight main refresh promotion, and smoke tests for the governed recovery flow.
  ADR impact: No new ADR; implements the planned main-updated workflow hardening.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This updates the existing main-updated workflow and scripts to make the already-discussed recovery strategy executable; no new cross-cutting architecture decision beyond the workflow change is introduced.

## Session Metrics

Raised at UTC: 2026-06-16T21:23:03Z
Latest commit at UTC: 2026-06-17T13:49:47Z
Latest commit SHA: 67839a4
Chat duration: 59204s (00:16:26:44)
Estimated tokens: 3518 estimated from session log

## Notes

- None recorded yet.
