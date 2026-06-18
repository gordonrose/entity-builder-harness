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
latest_commit_at_utc: 2026-06-18T14:31:29Z
latest_commit_sha: a773de6
chat_duration: 148106s (01:17:08:26)
estimated_tokens: 9571 estimated from session log
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


- Decision: Create 00.chat layer and retire tracked aggregate summary
  Rationale: Chat lifecycle governance should move into .agentic/00.chat over time, and commitLogs/README.md should not be maintained as a tracked generated artifact; session summaries are generated on request from source session logs.


- Decision: Route chat lifecycle to 00.chat
  Rationale: AGENTS.md and routing policy now treat .agentic/00.chat as the owner for chat lifecycle while .agentic/shared remains cross-layer process and compatibility workflow space.


- Decision: Add concrete 00.chat workflow entrypoints
  Rationale: The chat layer now has workflow files for start, refresh, commit, promote, cleanup, and reporting; each delegates to compatibility paths until a future migration promotes it to full implementation.


- Decision: Align classifier with chat layer
  Rationale: Capability resolution now lists chat as an allowed layer, and the startup classifier routes chat lifecycle tasks to .agentic/00.chat workflow entrypoints with fixtures covering cleanup, refresh, reporting, and promotion.


- Decision: Route chat startup through 00.chat
  Rationale: AGENTS.md now uses .agentic/00.chat/workflows/chat-start.md as the canonical chat-start entrypoint, and the chat worktree session smoke test verifies new sessions classify to the chat layer workflow.


- Decision: Promote chat commit governance into 00.chat
  Rationale: Added .agentic/00.chat/checklists/before-commit.md as the canonical chat commit checklist, promoted chat-commit.md to describe commit and checkpoint rules directly, and kept the shared checklist as a compatibility path.


- Decision: Promote main refresh governance into 00.chat
  Rationale: Moved active chat branch refresh rules from .agentic/shared/workflows/main-updated.md into .agentic/00.chat/workflows/chat-refresh-from-main.md and left the shared path as a compatibility pointer.


- Decision: Promote local convergence governance into 00.chat
  Rationale: Moved chat branch promotion rules from .agentic/shared/workflows/local-convergence.md into .agentic/00.chat/workflows/chat-promote-to-main.md and left the shared path as a compatibility pointer.


- Decision: Add chat cleanup/reporting governance and migration plan
  Rationale: Promoted cleanup and reporting workflow rules inside .agentic/00.chat, added .agentic/00.chat/migration-plan.md for later chats, and added scripts/shared/chat/audit-chat-layer-migration.sh to inspect canonical files and remaining compatibility references.


- Decision: Finish chat-start migration and clear legacy workflow references
  Rationale: Promoted chat-start.md to own startup governance directly, reduced chat-start-interview.md to a compatibility pointer, updated classifier fallback to .agentic/00.chat/workflows/chat-start.md, and made commit prerequisites rely on the canonical chat checklist.

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


### 2026-06-17T14:17:14Z - Decision

Decision: Create 00.chat layer and retire tracked aggregate summary

Rationale: Chat lifecycle governance should move into .agentic/00.chat over time, and commitLogs/README.md should not be maintained as a tracked generated artifact; session summaries are generated on request from source session logs.


### 2026-06-17T14:17:14Z - ADR disposition

ADR needed: yes

ADR path: docs/harness/architecture/adrs/0013-create-chat-layer-and-on-demand-session-summary.md

Reason: Creates a new chat lifecycle layer and reverses the prior tracked aggregate summary decision.


### 2026-06-17T14:21:28Z - Commit recorded

Commit: `6f2318d`

Message: Create chat layer and retire aggregate summary

Summary: Adds .agentic/00.chat as the chat lifecycle owner, retires tracked commitLogs/README.md, and makes session summaries on-demand.

ADR impact: ADR 0013 records the layer and reporting decision.


### 2026-06-17T14:23:40Z - Decision

Decision: Route chat lifecycle to 00.chat

Rationale: AGENTS.md and routing policy now treat .agentic/00.chat as the owner for chat lifecycle while .agentic/shared remains cross-layer process and compatibility workflow space.


### 2026-06-17T14:29:39Z - Commit recorded

Commit: `64957c3`

Message: Route chat lifecycle to chat layer

Summary: Adds the chat layer to routing, names .agentic/00.chat as chat lifecycle owner, and reframes shared workflows as cross-layer compatibility space.

ADR impact: ADR 0013 covers the chat layer ownership decision.


### 2026-06-17T14:31:56Z - Decision

Decision: Add concrete 00.chat workflow entrypoints

Rationale: The chat layer now has workflow files for start, refresh, commit, promote, cleanup, and reporting; each delegates to compatibility paths until a future migration promotes it to full implementation.


### 2026-06-17T14:59:21Z - Commit recorded

Commit: `90a6d57`

Message: Add chat workflow entrypoints

Summary: Adds concrete .agentic/00.chat workflow entrypoints for chat start, refresh, commit, promote, cleanup, and reporting while delegating to legacy compatibility paths.

ADR impact: ADR 0013 covers chat lifecycle ownership; this commit adds migration entrypoints.


### 2026-06-17T15:01:38Z - Decision

Decision: Align classifier with chat layer

Rationale: Capability resolution now lists chat as an allowed layer, and the startup classifier routes chat lifecycle tasks to .agentic/00.chat workflow entrypoints with fixtures covering cleanup, refresh, reporting, and promotion.


### 2026-06-17T15:47:02Z - Commit recorded

Commit: `e7e7adb`

Message: Align classifier with chat layer

Summary: Updates capability resolution and task classification so chat lifecycle requests route to .agentic/00.chat workflow entrypoints.

ADR impact: ADR 0013 covers chat layer ownership; this commit aligns executable classification.


### 2026-06-17T15:49:11Z - Decision

Decision: Route chat startup through 00.chat

Rationale: AGENTS.md now uses .agentic/00.chat/workflows/chat-start.md as the canonical chat-start entrypoint, and the chat worktree session smoke test verifies new sessions classify to the chat layer workflow.


### 2026-06-17T15:53:54Z - Decision

Decision: Promote chat commit governance into 00.chat

Rationale: Added .agentic/00.chat/checklists/before-commit.md as the canonical chat commit checklist, promoted chat-commit.md to describe commit and checkpoint rules directly, and kept the shared checklist as a compatibility path.


### 2026-06-17T15:58:54Z - Decision

Decision: Promote main refresh governance into 00.chat

Rationale: Moved active chat branch refresh rules from .agentic/shared/workflows/main-updated.md into .agentic/00.chat/workflows/chat-refresh-from-main.md and left the shared path as a compatibility pointer.


### 2026-06-17T15:59:31Z - Decision

Decision: Promote local convergence governance into 00.chat

Rationale: Moved chat branch promotion rules from .agentic/shared/workflows/local-convergence.md into .agentic/00.chat/workflows/chat-promote-to-main.md and left the shared path as a compatibility pointer.


### 2026-06-17T15:59:52Z - Commit recorded

Commit: `2552120`

Message: Promote chat commit checklist

Summary: Adds the canonical .agentic/00.chat before-commit checklist, promotes chat-commit.md to own commit/checkpoint rules, and keeps the shared checklist as a compatibility path.

ADR impact: covered by existing chat layer ADR


### 2026-06-17T15:59:57Z - Commit recorded

Commit: `4ac93a8`

Message: Promote chat main refresh workflow

Summary: Moves active chat branch refresh governance into .agentic/00.chat/workflows/chat-refresh-from-main.md and leaves main-updated.md as a compatibility pointer.

ADR impact: covered by existing chat layer ADR


### 2026-06-17T16:00:02Z - Commit recorded

Commit: `38c0d20`

Message: Promote chat main promotion workflow

Summary: Moves local convergence and chat-to-main promotion governance into .agentic/00.chat/workflows/chat-promote-to-main.md and leaves local-convergence.md as a compatibility pointer.

ADR impact: covered by existing chat layer ADR


### 2026-06-17T21:27:58Z - Decision

Decision: Add chat cleanup/reporting governance and migration plan

Rationale: Promoted cleanup and reporting workflow rules inside .agentic/00.chat, added .agentic/00.chat/migration-plan.md for later chats, and added scripts/shared/chat/audit-chat-layer-migration.sh to inspect canonical files and remaining compatibility references.


### 2026-06-17T21:42:26Z - Decision

Decision: Finish chat-start migration and clear legacy workflow references

Rationale: Promoted chat-start.md to own startup governance directly, reduced chat-start-interview.md to a compatibility pointer, updated classifier fallback to .agentic/00.chat/workflows/chat-start.md, and made commit prerequisites rely on the canonical chat checklist.


### 2026-06-17T22:05:29Z - Commit recorded

Commit: `4995429`

Message: Finish chat start workflow migration

Summary: Promotes chat-start.md to own startup governance directly, reduces chat-start-interview.md to a compatibility pointer, updates classifier fallback to the chat layer workflow, and clears legacy shared workflow references from the migration audit.

ADR impact: covered by existing chat layer ADR


### 2026-06-18T13:48:16Z - Main refresh conflict recorded

Path: `.agentic/shared/workflows/local-convergence.md`

Type: `ownership-migration-conflict`

Mode: deterministic

Action: kept shared compatibility pointer and migrated verifier-based governance into .agentic/00.chat/workflows/chat-promote-to-main.md


### 2026-06-18T13:50:44Z - Main refresh conflict recorded

Path: `.agentic/shared/workflows/main-updated.md`

Type: `ownership-migration-conflict`

Mode: deterministic

Action: kept shared compatibility pointer; migrated valid preflight promotion cleanup guidance into .agentic/00.chat/workflows/chat-refresh-from-main.md; did not migrate obsolete commitLogs/README.md generated-summary recovery because ADR 0013 retires that tracked artifact


### 2026-06-18T13:53:55Z - Main refresh conflict recorded

Path: `commitLogs/README.md`

Type: `retired-artifact-delete-modify-conflict`

Mode: deterministic

Action: kept deletion because ADR 0013 retires tracked commitLogs/README.md and on-demand summaries remain available through the chat reporting workflow and generator script


### 2026-06-18T13:57:29Z - Main refresh conflict recorded

Path: `scripts/shared/chat/generate-commit-log-summary.sh`

Type: `retired-artifact-generator-conflict`

Mode: deterministic

Action: kept on-demand stdout and explicit --output behavior, added safe --print alias, and continued blocking --output commitLogs/README.md; did not restore --write or --check for the retired tracked artifact


### 2026-06-18T14:02:44Z - Main refresh conflict recorded

Path: `scripts/shared/git/classify-main-refresh-dirty-state.sh`

Type: `retired-artifact-policy-script-conflict`

Mode: deterministic

Action: kept classifier behavior that only recognizes clean, current-session-bookkeeping, repo-work, and unsupported-dirty; did not preserve generated-commitlog-summary or --check behavior for the retired artifact


### 2026-06-18T14:03:16Z - Main refresh conflict recorded

Path: `scripts/shared/git/smoke-test-main-refresh-dirty-classifier.sh`

Type: `retired-artifact-policy-script-conflict`

Mode: deterministic

Action: kept smoke coverage for clean, current-session-bookkeeping, repo-work, and unsupported-dirty; did not preserve generated-commitlog-summary expectation


### 2026-06-18T14:27:28Z - Main refresh conflict recorded

Path: `scripts/shared/git/preflight-main-refresh.sh`

Type: `script-add-add-conflict`

Mode: deterministic

Action: kept main-side stricter preflight branch-name sanitization without changing the governed preflight capability


### 2026-06-18T14:27:35Z - Main refresh conflict recorded

Path: `scripts/shared/git/promote-preflight-refresh.sh`

Type: `script-add-add-conflict`

Mode: deterministic

Action: kept main-side validation requiring preflight branch shape, exactly one clean preflight worktree, promoted commit verification, worktree removal, branch deletion, and structured output


### 2026-06-18T14:27:41Z - Main refresh conflict recorded

Path: `scripts/shared/git/smoke-test-main-refresh-preflight.sh`

Type: `script-add-add-conflict`

Mode: deterministic

Action: kept main-side expanded smoke coverage aligned with stricter promotion behavior


### 2026-06-18T14:31:29Z - Commit recorded

Commit: `a773de6`

Message: Allow automatic promotion of tested preflight

Summary: Records the governed main-refresh conflict taxonomy and audit trail, resolves the preflight merge conflicts, and adds automatic promotion for clean tested preflight results.

ADR impact: covered by ADR 0013 and main-refresh conflict standard

## Commits



- Commit: `67839a4`
  Time UTC: 2026-06-17T13:49:47Z
  Message: Harden main refresh recovery workflow
  Summary: Adds dirty-state classification, generated-summary verification, preflight main refresh promotion, and smoke tests for the governed recovery flow.
  ADR impact: No new ADR; implements the planned main-updated workflow hardening.


- Commit: `6f2318d`
  Time UTC: 2026-06-17T14:21:28Z
  Message: Create chat layer and retire aggregate summary
  Summary: Adds .agentic/00.chat as the chat lifecycle owner, retires tracked commitLogs/README.md, and makes session summaries on-demand.
  ADR impact: ADR 0013 records the layer and reporting decision.


- Commit: `64957c3`
  Time UTC: 2026-06-17T14:29:39Z
  Message: Route chat lifecycle to chat layer
  Summary: Adds the chat layer to routing, names .agentic/00.chat as chat lifecycle owner, and reframes shared workflows as cross-layer compatibility space.
  ADR impact: ADR 0013 covers the chat layer ownership decision.


- Commit: `90a6d57`
  Time UTC: 2026-06-17T14:59:21Z
  Message: Add chat workflow entrypoints
  Summary: Adds concrete .agentic/00.chat workflow entrypoints for chat start, refresh, commit, promote, cleanup, and reporting while delegating to legacy compatibility paths.
  ADR impact: ADR 0013 covers chat lifecycle ownership; this commit adds migration entrypoints.


- Commit: `e7e7adb`
  Time UTC: 2026-06-17T15:47:02Z
  Message: Align classifier with chat layer
  Summary: Updates capability resolution and task classification so chat lifecycle requests route to .agentic/00.chat workflow entrypoints.
  ADR impact: ADR 0013 covers chat layer ownership; this commit aligns executable classification.


- Commit: `2552120`
  Time UTC: 2026-06-17T15:59:52Z
  Message: Promote chat commit checklist
  Summary: Adds the canonical .agentic/00.chat before-commit checklist, promotes chat-commit.md to own commit/checkpoint rules, and keeps the shared checklist as a compatibility path.
  ADR impact: covered by existing chat layer ADR


- Commit: `4ac93a8`
  Time UTC: 2026-06-17T15:59:57Z
  Message: Promote chat main refresh workflow
  Summary: Moves active chat branch refresh governance into .agentic/00.chat/workflows/chat-refresh-from-main.md and leaves main-updated.md as a compatibility pointer.
  ADR impact: covered by existing chat layer ADR


- Commit: `38c0d20`
  Time UTC: 2026-06-17T16:00:02Z
  Message: Promote chat main promotion workflow
  Summary: Moves local convergence and chat-to-main promotion governance into .agentic/00.chat/workflows/chat-promote-to-main.md and leaves local-convergence.md as a compatibility pointer.
  ADR impact: covered by existing chat layer ADR


- Commit: `4995429`
  Time UTC: 2026-06-17T22:05:29Z
  Message: Finish chat start workflow migration
  Summary: Promotes chat-start.md to own startup governance directly, reduces chat-start-interview.md to a compatibility pointer, updates classifier fallback to the chat layer workflow, and clears legacy shared workflow references from the migration audit.
  ADR impact: covered by existing chat layer ADR


- Commit: `a773de6`
  Time UTC: 2026-06-18T14:31:29Z
  Message: Allow automatic promotion of tested preflight
  Summary: Records the governed main-refresh conflict taxonomy and audit trail, resolves the preflight merge conflicts, and adds automatic promotion for clean tested preflight results.
  ADR impact: covered by ADR 0013 and main-refresh conflict standard

## Main Refresh Conflicts



- Path: `.agentic/shared/workflows/local-convergence.md`
  Type: `ownership-migration-conflict`
  Mode: deterministic
  Reason: chat branch converted the legacy shared workflow to a compatibility pointer while main improved the legacy workflow with verifier-based local convergence governance
  Action: kept shared compatibility pointer and migrated verifier-based governance into .agentic/00.chat/workflows/chat-promote-to-main.md
  Preflight branch: `agentic/preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-/20260617221026`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro--20260617221026`
  Files changed by resolution: .agentic/shared/workflows/local-convergence.md; .agentic/00.chat/workflows/chat-promote-to-main.md
  Checks: pending: deterministic process drift and diff check after conflict resolution


- Path: `.agentic/shared/workflows/main-updated.md`
  Type: `ownership-migration-conflict`
  Mode: deterministic
  Reason: chat branch converted the legacy shared refresh workflow to a compatibility pointer while main improved the legacy workflow with generated-summary recovery and preflight cleanup guidance
  Action: kept shared compatibility pointer; migrated valid preflight promotion cleanup guidance into .agentic/00.chat/workflows/chat-refresh-from-main.md; did not migrate obsolete commitLogs/README.md generated-summary recovery because ADR 0013 retires that tracked artifact
  Preflight branch: `agentic/preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-/20260617221026`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro--20260617221026`
  Files changed by resolution: .agentic/shared/workflows/main-updated.md; .agentic/00.chat/workflows/chat-refresh-from-main.md
  Checks: pending: deterministic process drift and diff check after conflict resolution


- Path: `commitLogs/README.md`
  Type: `retired-artifact-delete-modify-conflict`
  Mode: deterministic
  Reason: chat branch retired the tracked aggregate commit log summary while main modified the generated artifact
  Action: kept deletion because ADR 0013 retires tracked commitLogs/README.md and on-demand summaries remain available through the chat reporting workflow and generator script
  Preflight branch: `agentic/preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-/20260617221026`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro--20260617221026`
  Files changed by resolution: commitLogs/README.md
  Checks: pending: commit log deletion gate and diff check after conflict resolution


- Path: `scripts/shared/chat/generate-commit-log-summary.sh`
  Type: `retired-artifact-generator-conflict`
  Mode: deterministic
  Reason: main preserved generator behavior for tracked commitLogs/README.md while chat branch retired that artifact and made summaries on-demand
  Action: kept on-demand stdout and explicit --output behavior, added safe --print alias, and continued blocking --output commitLogs/README.md; did not restore --write or --check for the retired tracked artifact
  Preflight branch: `agentic/preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-/20260617221026`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro--20260617221026`
  Files changed by resolution: scripts/shared/chat/generate-commit-log-summary.sh; .agentic/00.chat/standards/main-refresh-conflict-types.md
  Checks: pending: generator smoke test, shell syntax, and diff check


- Path: `scripts/shared/git/classify-main-refresh-dirty-state.sh`
  Type: `retired-artifact-policy-script-conflict`
  Mode: deterministic
  Reason: main added generated-commitlog-summary dirty-state recoverability for commitLogs/README.md while chat branch retired that tracked artifact
  Action: kept classifier behavior that only recognizes clean, current-session-bookkeeping, repo-work, and unsupported-dirty; did not preserve generated-commitlog-summary or --check behavior for the retired artifact
  Preflight branch: `agentic/preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-/20260617221026`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro--20260617221026`
  Files changed by resolution: scripts/shared/git/classify-main-refresh-dirty-state.sh; .agentic/00.chat/standards/main-refresh-conflict-types.md
  Checks: pending: dirty classifier smoke test, shell syntax, and diff check


- Path: `scripts/shared/git/smoke-test-main-refresh-dirty-classifier.sh`
  Type: `retired-artifact-policy-script-conflict`
  Mode: deterministic
  Reason: main added smoke coverage for generated-commitlog-summary while chat branch retired commitLogs/README.md as an active tracked artifact
  Action: kept smoke coverage for clean, current-session-bookkeeping, repo-work, and unsupported-dirty; did not preserve generated-commitlog-summary expectation
  Preflight branch: `agentic/preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-/20260617221026`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro--20260617221026`
  Files changed by resolution: scripts/shared/git/smoke-test-main-refresh-dirty-classifier.sh
  Checks: pending: dirty classifier smoke test, shell syntax, and diff check


- Path: `scripts/shared/git/preflight-main-refresh.sh`
  Type: `script-add-add-conflict`
  Mode: deterministic
  Reason: both sides added the governed preflight refresh script and main tightened branch-name sanitization
  Action: kept main-side stricter preflight branch-name sanitization without changing the governed preflight capability
  Preflight branch: `agentic/preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-/20260617221026`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro--20260617221026`
  Files changed by resolution: scripts/shared/git/preflight-main-refresh.sh
  Checks: pending: preflight smoke test, shell syntax, and diff check


- Path: `scripts/shared/git/promote-preflight-refresh.sh`
  Type: `script-add-add-conflict`
  Mode: deterministic
  Reason: both sides added the governed preflight promotion script and main added stricter validation plus cleanup
  Action: kept main-side validation requiring preflight branch shape, exactly one clean preflight worktree, promoted commit verification, worktree removal, branch deletion, and structured output
  Preflight branch: `agentic/preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-/20260617221026`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro--20260617221026`
  Files changed by resolution: scripts/shared/git/promote-preflight-refresh.sh
  Checks: pending: preflight smoke test, shell syntax, and diff check


- Path: `scripts/shared/git/smoke-test-main-refresh-preflight.sh`
  Type: `script-add-add-conflict`
  Mode: deterministic
  Reason: both sides added preflight smoke coverage and main expanded coverage for dirty preflight refusal, cleanup, and non-preflight branch rejection
  Action: kept main-side expanded smoke coverage aligned with stricter promotion behavior
  Preflight branch: `agentic/preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro-/20260617221026`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-06-16-22-23-task-explore-and-design-a-governed-main-refresh-recovery-pro--20260617221026`
  Files changed by resolution: scripts/shared/git/smoke-test-main-refresh-preflight.sh
  Checks: pending: preflight smoke test, shell syntax, and diff check

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0013-create-chat-layer-and-on-demand-session-summary.md
Reason: Creates a new chat lifecycle layer and reverses the prior tracked aggregate summary decision.

## Session Metrics

Raised at UTC: 2026-06-16T21:23:03Z
Latest commit at UTC: 2026-06-18T14:31:29Z
Latest commit SHA: a773de6
Chat duration: 148106s (01:17:08:26)
Estimated tokens: 9571 estimated from session log

## Notes

- None recorded yet.
