# Chat Session: 2026-06-15-21-53 i-want-to-update-my-harness-so-that-whenever-a-new-chat-is-s

<!-- agentic-session
id: 2026-06-15-21-53-i-want-to-update-my-harness-so-that-whenever-a-new-chat-is-s
task: i want to update my harness so that whenever a new chat is started, commits that are purely duplicates of later commits are also deleted
branch: chat/2026-06-15-21-53-i-want-to-update-my-harness-so-that-whenever-a-new-chat-is-s
layer: shared
mode: implementation
workflow: .agentic/shared/workflows/change-shared-process.md
status: ready
raised_at_utc: 2026-06-15T20:53:08Z
latest_commit_at_utc: 2026-06-15T21:43:43Z
latest_commit_sha: 01e6d8c
chat_duration: 3035s (00:00:50:35)
estimated_tokens: 1445 estimated from session log
-->

## Initial Intent

i want to update my harness so that whenever a new chat is started, commits that are purely duplicates of later commits are also deleted

## Branch

`chat/2026-06-15-21-53-i-want-to-update-my-harness-so-that-whenever-a-new-chat-is-s`

## Session Log

- Session started.
- Branch created.
- Commit log initialized.

## Questions Asked

- Asked: Do we need an ADR for duplicate chat branch cleanup?
  Response: Yes. The change expands startup cleanup from empty branch deletion
  to patch-equivalent duplicate branch deletion, which is a durable harness
  safety policy.

## Issues Raised

- Raised: The active chat branch did not contain the shared workflow and commit
  gates named by its session metadata.
  Resolution: Merge the prior shared-process chat branch first, then update the
  commit workflow so future agents repair this prerequisite branch state before
  trying to commit the current task.

## Decisions Made

- Decision: Record an ADR before implementing duplicate chat branch cleanup.
  Rationale: The cleanup policy controls when chat branches and matching
  commit logs may be deleted, so future agents need the safety constraints and
  rationale preserved.
- Decision: The shared commit workflow must verify prerequisite workflow and
  gate files exist on the current branch before committing.
  Rationale: A chat branch can be created from an older harness state while its
  session metadata points at newer shared-process files; the commit path should
  repair that branch state first instead of bypassing missing gates.
- Decision: Use an executable prerequisite gate instead of duplicating
  mechanical file-existence rules in prose.
  Rationale: The harness should deterministically check that the declared
  workflow, before-commit checklist, and referenced gate scripts exist, while
  prose remains responsible for the approval rule around merge/cherry-pick
  repair.
- Decision: Add a deterministic-process drift gate for harness process commits.
  Rationale: When harness updates add operational prose that could be handled
  by a script or gate, the harness should flag it before commit and require the
  agent to propose a scripted check or an explicit allow marker for
  human-governed prose.

## Activity Log

### 2026-06-15T20:53:08Z - Session started

Initial intent: i want to update my harness so that whenever a new chat is started, commits that are purely duplicates of later commits are also deleted

### 2026-06-15T21:05:00Z - ADR added

Summary: Added ADR 0002 to define conservative cleanup of older chat branches
whose branch-only commits are patch-equivalent to later chat work.

### 2026-06-15T21:12:00Z - Prerequisite workflow merged

Summary: Merged the prior shared-process chat branch so this branch contains
the declared workflow, before-commit checklist, ADR docs, and commit gate
scripts required by its session metadata.

### 2026-06-15T21:15:00Z - Commit workflow updated

Summary: Updated the shared process workflow and before-commit checklist to
require prerequisite shared-process files to be merged or cherry-picked before
committing when a chat branch predates those files.


### 2026-06-15T21:23:22Z - Commit recorded

Commit: `140da35`

Message: document duplicate chat branch cleanup policy

Summary: Added ADR 0002 for duplicate chat branch cleanup and updated the shared commit workflow to repair missing prerequisite workflow/gate files before committing.

ADR impact: ADR 0002 records the cleanup policy; workflow update enforces prerequisite branch repair before future commits.

### 2026-06-15T21:32:00Z - Prerequisite gate scripted

Summary: Added an executable commit-prerequisite check, wired it into the
before-commit preparation gate, and replaced duplicated prose checks in the
workflow and checklist with the script invocation plus approval policy.


### 2026-06-15T21:43:43Z - Commit recorded

Commit: `01e6d8c`

Message: script shared commit prerequisite checks

Summary: Added check-commit-prerequisites.sh, replaced prerequisite prose with the script call, and wired it into chat session preparation before commit.

ADR impact: No new ADR; this mechanizes the prerequisite branch-state workflow policy already recorded in the session.

### 2026-06-15T21:42:00Z - Deterministic drift gate added

Summary: Added ADR 0003 and a suggestion-only drift checker with staged,
commit, path, and whole-harness modes. Wired staged checking into commit
preparation so new process prose is reviewed before commit completion.

## Commits

- Planned commit: add ADR for duplicate chat branch cleanup.
  Summary: Add ADR 0002 documenting the policy and safety constraints for
  deleting older duplicate chat branches during new chat startup.
- Planned commit: update shared commit prerequisite workflow.
  Summary: Require shared-process prerequisite files to be present on the
  current branch before committing, and repair the branch state first when they
  are missing.


- Commit: `140da35`
  Time UTC: 2026-06-15T21:23:22Z
  Message: document duplicate chat branch cleanup policy
  Summary: Added ADR 0002 for duplicate chat branch cleanup and updated the shared commit workflow to repair missing prerequisite workflow/gate files before committing.
  ADR impact: ADR 0002 records the cleanup policy; workflow update enforces prerequisite branch repair before future commits.
- Planned commit: script shared commit prerequisite checks.
  Summary: Add `check-commit-prerequisites.sh`, call it from the preparation
  gate, and replace checklist/workflow file-existence prose with the executable
  check.


- Commit: `01e6d8c`
  Time UTC: 2026-06-15T21:43:43Z
  Message: script shared commit prerequisite checks
  Summary: Added check-commit-prerequisites.sh, replaced prerequisite prose with the script call, and wired it into chat session preparation before commit.
  ADR impact: No new ADR; this mechanizes the prerequisite branch-state workflow policy already recorded in the session.
- Planned commit: add deterministic process drift gate.
  Summary: Add ADR 0003, create `check-deterministic-process-drift.sh`, wire
  staged drift checking into commit preparation, and document broader audit
  modes for harness process prose.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0003-review-process-prose-for-deterministic-gates.md
Reason: This change establishes a durable harness self-review policy for replacing scriptable operational prose with deterministic gates or explicit allow markers.

## Session Metrics

Raised at UTC: 2026-06-15T20:53:08Z
Latest commit at UTC: 2026-06-15T21:43:43Z
Latest commit SHA: 01e6d8c
Chat duration: 3035s (00:00:50:35)
Estimated tokens: 1445 estimated from session log

## Notes

- None recorded yet.
