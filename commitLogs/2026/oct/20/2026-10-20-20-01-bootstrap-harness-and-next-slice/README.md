# Chat Session: 2026-10-20-20-01 bootstrap-harness-and-next-slice

<!-- agentic-session
id: 2026-10-20-20-01-explain-the-deployment-harness-from-local-source-to-containe
task: Explain the deployment harness from local source to container image and running infrastructure
branch: chat/2026-10-20-20-01-explain-the-deployment-harness-from-local-source-to-containe
worktree: /home/owner/projects/.chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-10-20-20-01-explain-the-deployment-harness-from-local-source-to-containe-3545020505
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-10-20T19:01:17Z
transcript_provider:
transcript_path:
transcript_bytes:
transcript_source:
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

Explain the deployment harness from local source to container image and running infrastructure

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- Asked to integrate the other chat's committed work through `3bfce6a8` into
  this recorded worktree and continue focused harness updates. User approved:
  "Yes, bring in 3bfce6a8 and continue here". This grants this local integration
  and task edits, not a new commit, push or cloud mutation.

## Issues Raised

- The initial successful release and A-to-B-to-A rehearsal were already proved,
  but active workflow indexes still pointed to pre-migration paths. Generic
  Deploy/Run authority remained in the old combined location.
- Acceptance dry-run coverage missed an actual write failure: the writer used
  the custody validator's compact report instead of the full validated receipt.
  Generated acceptance metadata was also incomplete.
- Completed verifier evidence can be reused, but pending/running/concurrent
  invocations are not automatically reconciled. Instructions now require
  observing the original operation before another effect.
- The full metadata check exposed six existing missing `used_by` declarations
  on first-slice scripts; fixed those headers without changing script behaviour.

## Decisions Made

- Preserve this chat's recorded worktree and branch. Fast-forward from
  `73be76d2` to the approved `3bfce6a8` (52 existing commits); no merge commit,
  new commit, push or original-chat worktree modification.
- Keep one generic Deploy workflow, one Run workflow and one AWS-specific
  procedure. Plans track outstanding work; active workflows and controls govern
  operation. Preserve the established bootstrap boundary.
- Use existing logs, receipts and provider operation references for uncertain
  results. Do not add an execution-journal subsystem.
- Recommend investigating a minimal application persistence slice next:
  private record creation/retrieval surviving container replacement. Provider,
  resources, cost, access and failure/recovery design remain to be selected.

## Context Hygiene

- Carry forward the lifecycle map, fixed AWS workflow and accepted-release
  regression suite as current instructions/evidence. Retired-path and metadata
  audits passed; raw investigation output is not needed. Persistence remains
  the next investigated slice, with provider selection unresolved. The existing
  accepted release and rehearsal evidence are unchanged by this task.

## Activity Log

### 2026-10-20T19:01:17Z - Session started

Initial intent: Explain the deployment harness from local source to container image and running infrastructure

## Sub-Agent Activity

- `existing_provider_path`: inspected existing controls, repaired acceptance
  writes and isolated failure-path tests, then reviewed exact AWS workflow
  commands and report handoffs.
- `build_package_trace`: investigated existing persistence/security/audit
  capabilities, reviewed generic Deploy/Run instructions, and repaired six
  missing consumer metadata links.

## Commits

- None recorded yet.

## Main Refresh Conflicts

- Approved integration used the other chat's local commit `3bfce6a8`, not main.
  Refresh classification found only current-session bookkeeping and no incoming
  overlap; fast-forward completed without conflicts.

## ADR Disposition

ADR needed: no
ADR path: docs/04.deploy/adrs/0037-use-lifecycle-first-deployment-authority-paths.md
Reason: The Deploy/Run migration completes the approved lifecycle-path model.
The next provider/resource choice has not been made by this task.

## Session Metrics

Raised at UTC: 2026-10-20T19:01:17Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- 2026-10-21: Reviewed the supplied latest-chat attachment, existing release
  evidence, lifecycle controls and migration plan. Renamed this session folder
  through the governed command; session ID, branch and worktree remain stable.
- Moved generic update instructions to `50-deploy` and accepted-release standard
  to `60-run`; added the Run handoff and updated active indexes/recognition.
  Expanded the existing AWS procedure with exact entrypoints, early readiness,
  separate authorities, qualified source/digest custody, distroless/private-image
  lessons, acceptance, restoration and interrupted-operation handling.
- Acceptance now retains exactly the validated custody document, rejects
  malformed proof, produces full v3 metadata and atomically replaces the local
  record. Tests exercise real writes against a temporary record, invalid proof,
  a replaced receipt and failed fsync/replace. The real accepted baseline and
  rehearsal evidence are unchanged.
- Validation: bootstrap control and release-contract suite, target declaration
  validator/suite, runnable-program contract suite and package-custody workflow
  suite passed. Both moved-path checks passed; a 19-pattern retirement audit
  found no stale active references. All 1,163 artifact headers and all 24 changed
  Markdown links passed. Generated recognition sources were regenerated and
  checked. Strict artifact index/coverage, deterministic-process drift and
  governed-script command drift checks also passed. The command-drift check
  caught direct invocations in the new AWS examples; these now use the governed
  runner, preserving the authority requirements stated by each phase.
- No AWS inspection/mutation, GitHub dispatch, image publication or deployment
  was performed during the harness update.
- 2026-10-21: User requested "can we commit and merge to main?" This authorizes
  staging these reviewed task paths, committing them, the required non-rewriting
  refresh from local main and local promotion. No remote push is requested.
  Local main was clean at `fbee1083`; the chat was at `3bfce6a8` with the reviewed
  harness changes. Commit summary: complete Deploy/Run authority and command
  guidance, repair accepted-release recording, and capture the next-slice
  investigation. Required checks passed in the preceding implementation turn;
  commit-boundary gates will run on the exact staged changes.
