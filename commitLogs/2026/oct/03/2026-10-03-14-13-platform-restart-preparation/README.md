# Chat Session: 2026-10-03-14-13 platform-restart-preparation

<!-- agentic-session
id: 2026-10-03-14-13-platform-restart-preparation
task: Platform restart preparation
branch: chat/2026-10-03-14-13-platform-restart-preparation
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-10-03-14-13-platform-restart-preparation-1557440518
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-10-03T13:13:18Z
transcript_provider: codex
transcript_path: /home/owner/.codex/sessions/2026/10/03/rollout-2026-10-03T14-17-23-01a101e9-8669-7583-884f-752384e25131.jsonl
transcript_bytes: 577333
transcript_source: codex path: /home/owner/.codex/sessions/2026/10/03/rollout-2026-10-03T14-17-23-01a101e9-8669-7583-884f-752384e25131.jsonl
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-10-03T14:05:04Z
latest_commit_sha: b103f1d6
chat_duration: 3106s (00:00:51:46)
estimated_chat_tokens: 144334 estimated from chat transcript bytes (577333 bytes; source: codex path: /home/owner/.codex/sessions/2026/10/03/rollout-2026-10-03T14-17-23-01a101e9-8669-7583-884f-752384e25131.jsonl)
estimated_chat_cost: unavailable; no pricing profile selected
estimated_chat_cost_basis: unavailable; set CHAT_COST_PROFILE or CHAT_COST_PRICING_FILE
-->

## Initial Intent

Platform restart preparation

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made



- Decision: Continue Platform restart preparation with a documentation-only review candidate.
  Rationale: The user authorizes reconciliation, investigation and the smallest restart change for review. Current branch and main are at 2309e676; bootstrap dirt is only this session README and the governed bookkeeping-only gate passes. Inspect preserved repositories and backups read-only. Prepare only factual source-status corrections and session evidence under the existing document-placement and change-harness workflows; retain baseline gates and the replacement proposal. No commits, pushes, branch deletion, AWS changes, deployment or replacement implementation are authorized.


- Decision: Accept documentation corrections and checkpoint local preservation work.
  Rationale: The user requests durable preservation of review edits and scheduler evidence, isolated checkpointed scheduler recovery, and a routine preventing uncommitted temporary-worktree loss. This authorizes local staging/checkpoint commits for those scopes. Preserve original files and refs. No convergence-programme execution, AWS change, deployment, push, merge to main or destructive cleanup is authorized. Establish the missing governed recovery procedure before replaying transcript operations.


- Decision: Govern isolated scheduler reconstruction and durable session preservation.
  Rationale: The new recover-transcript-draft workflow supplies the previously missing recovery procedure; chat-commit adds durable preservation before handoff. Reserve auxiliary branch chat/2026-10-03-scheduler-draft-recovery at exact base 8052929cb947ef3a0199a338a997f8cc8ede3aac in the restart repository, with AGENTIC_CHAT_WORKTREE_ROOT=/home/owner/projects/entity-builder-scheduler-recovery-2026-10-03/worktrees. Private evidence/bundles go in the same new durable root. Original repository/refs/worktree registration and all prior backups remain untouched. Recovery restores the historical draft, not integration or deployment authority.

## Context Hygiene



- Summary: Preserved-work reconciliation is complete; scheduler working files are missing but substantial transcript evidence exists.
  Durable evidence: The Restart reconciliation section records branch hashes, 13-file archive equality, transcript path/hash and recovery limits. The convergence plan is the accepted factual correction. Local main remains 2309e676 and all gates are retained. Future transcript reconstruction requires an isolated governed procedure; no deployment is authorized.

## Activity Log

### 2026-10-03T13:13:18Z - Session started

Initial intent: Platform restart preparation


### 2026-10-03T13:20:55Z - Decision

Decision: Continue Platform restart preparation with a documentation-only review candidate.

Rationale: The user authorizes reconciliation, investigation and the smallest restart change for review. Current branch and main are at 2309e676; bootstrap dirt is only this session README and the governed bookkeeping-only gate passes. Inspect preserved repositories and backups read-only. Prepare only factual source-status corrections and session evidence under the existing document-placement and change-harness workflows; retain baseline gates and the replacement proposal. No commits, pushes, branch deletion, AWS changes, deployment or replacement implementation are authorized.


### 2026-10-03T13:28:45Z - Sub-agent activity recorded

Agent: trace_scheduler_draft

Status: completed

Delegation mode: sub-agent

Fallback used: no

Scope: Scheduler/date-time evidence discovery


### 2026-10-03T13:28:46Z - Sub-agent activity recorded

Agent: reconcile_platform

Status: completed

Delegation mode: sub-agent

Fallback used: no

Scope: Preserved platform source reconciliation


### 2026-10-03T13:28:46Z - Sub-agent activity recorded

Agent: review_restart_scope

Status: completed

Delegation mode: sub-agent

Fallback used: no

Scope: Independent smallest restart scope review


### 2026-10-03T13:28:46Z - ADR disposition

ADR needed: no

Reason: Factual reconciliation and review-scope corrections only; no durable architecture, gate or deployment policy is adopted.


### 2026-10-03T13:52:18Z - Decision

Decision: Accept documentation corrections and checkpoint local preservation work.

Rationale: The user requests durable preservation of review edits and scheduler evidence, isolated checkpointed scheduler recovery, and a routine preventing uncommitted temporary-worktree loss. This authorizes local staging/checkpoint commits for those scopes. Preserve original files and refs. No convergence-programme execution, AWS change, deployment, push, merge to main or destructive cleanup is authorized. Establish the missing governed recovery procedure before replaying transcript operations.


### 2026-10-03T13:52:19Z - Context hygiene

Summary: Preserved-work reconciliation is complete; scheduler working files are missing but substantial transcript evidence exists.

Durable evidence: The Restart reconciliation section records branch hashes, 13-file archive equality, transcript path/hash and recovery limits. The convergence plan is the accepted factual correction. Local main remains 2309e676 and all gates are retained. Future transcript reconstruction requires an isolated governed procedure; no deployment is authorized.


### 2026-10-03T13:53:10Z - Commit recorded

Commit: `4001c18e`

Message: docs(platform): checkpoint restart reconciliation and missing draft evidence

Summary: Preserve accepted convergence-plan corrections and the detailed scheduler transcript investigation on the local session branch; no source integration or deployment.

ADR impact: No architecture or gate change.


### 2026-10-03T14:01:50Z - Decision

Decision: Govern isolated scheduler reconstruction and durable session preservation.

Rationale: The new recover-transcript-draft workflow supplies the previously missing recovery procedure; chat-commit adds durable preservation before handoff. Reserve auxiliary branch chat/2026-10-03-scheduler-draft-recovery at exact base 8052929cb947ef3a0199a338a997f8cc8ede3aac in the restart repository, with AGENTIC_CHAT_WORKTREE_ROOT=/home/owner/projects/entity-builder-scheduler-recovery-2026-10-03/worktrees. Private evidence/bundles go in the same new durable root. Original repository/refs/worktree registration and all prior backups remain untouched. Recovery restores the historical draft, not integration or deployment authority.


### 2026-10-03T14:03:53Z - ADR disposition

ADR needed: no

Reason: This extends existing commit/export primitives with a narrow missing-draft recovery procedure and session-end preservation; it adopts no new runtime, deployment or storage architecture.


### 2026-10-03T14:04:26Z - Sub-agent activity recorded

Agent: review_restart_scope

Status: completed

Delegation mode: sub-agent

Fallback used: no

Scope: Preservation and transcript-recovery governance


### 2026-10-03T14:04:26Z - Sub-agent activity recorded

Agent: reconcile_platform

Status: completed

Delegation mode: sub-agent

Fallback used: no

Scope: Preserved storage and tenant-authority source review


### 2026-10-03T14:05:04Z - Commit recorded

Commit: `b103f1d6`

Message: feat(chat): preserve session work and govern transcript draft recovery

Summary: Add narrow isolated historical draft recovery and durable session-end preservation using existing gates; record source-review blockers without integration or deployment.

ADR impact: No new runtime or deployment architecture.

## Sub-Agent Activity



### 2026-10-03T13:28:45Z - trace_scheduler_draft

Status: completed
Delegation mode: sub-agent
Fallback used: no
Scope: Scheduler/date-time evidence discovery
Files touched: none
Checks run: Local refs/reflog/index, historical session evidence, durable archive inventory and targeted original transcript inspected read-only.
Git actions: Read-only Git inspection; no mutations.
Blockers: none
Next step: none
Summary: Original uncommitted draft is absent from Git/worktree; substantial task-specific transcript evidence located with plan, successful patches, lockfile diff and historical check results. Exact final source remains unverified.


### 2026-10-03T13:28:46Z - reconcile_platform

Status: completed
Delegation mode: sub-agent
Fallback used: no
Scope: Preserved platform source reconciliation
Files touched: none
Checks run: Branch ancestry, path comparisons and byte/hash checks; no historical runtime tests rerun.
Git actions: Read-only Git inspection; no mutations.
Blockers: none
Next step: none
Summary: Storage/data governance and tenant authority remain unintegrated preserved commits; PostgreSQL source is already on baseline; all 13 dirty planning files match preserved archive and hashes.


### 2026-10-03T13:28:46Z - review_restart_scope

Status: completed
Delegation mode: sub-agent
Fallback used: no
Scope: Independent smallest restart scope review
Files touched: none
Checks run: Read-only review of stale claims, restored source context and scope boundaries.
Git actions: Read-only Git inspection; no mutations.
Blockers: none
Next step: none
Summary: Recommended narrow convergence-plan factual corrections and session evidence; retained all gates and excluded programme implementation.


### 2026-10-03T14:04:26Z - review_restart_scope

Status: completed
Delegation mode: sub-agent
Fallback used: no
Scope: Preservation and transcript-recovery governance
Files touched: .agentic/00.chat/workflows/{recover-transcript-draft.md,chat-commit.md,README.md}
Checks run: Scoped metadata, deterministic-process drift, relative links and whitespace passed; root reviewed procedure and added isolated offline dependency setup.
Git actions: none
Blockers: none
Next step: none
Summary: Added the narrow recovery workflow, workflow index entry and durable preservation routine under current user authorization.


### 2026-10-03T14:04:26Z - reconcile_platform

Status: completed
Delegation mode: sub-agent
Fallback used: no
Scope: Preserved storage and tenant-authority source review
Files touched: none
Checks run: Read-only exact-commit source and path-overlap review; parent independently inspected storage and worker paths; historical tests not rerun.
Git actions: none
Blockers: none
Next step: none
Summary: Block integration as-is: storage state/permission/telemetry/profile-reference gaps and default worker authorizer failure loses queue disposition.

## Commits



- Commit: `4001c18e`
  Time UTC: 2026-10-03T13:53:10Z
  Message: docs(platform): checkpoint restart reconciliation and missing draft evidence
  Summary: Preserve accepted convergence-plan corrections and the detailed scheduler transcript investigation on the local session branch; no source integration or deployment.
  ADR impact: No architecture or gate change.


- Commit: `b103f1d6`
  Time UTC: 2026-10-03T14:05:04Z
  Message: feat(chat): preserve session work and govern transcript draft recovery
  Summary: Add narrow isolated historical draft recovery and durable session-end preservation using existing gates; record source-review blockers without integration or deployment.
  ADR impact: No new runtime or deployment architecture.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This extends existing commit/export primitives with a narrow missing-draft recovery procedure and session-end preservation; it adopts no new runtime, deployment or storage architecture.

## Session Metrics

Raised at UTC: 2026-10-03T13:13:18Z
Latest commit at UTC: 2026-10-03T14:05:04Z
Latest commit SHA: b103f1d6
Chat duration: 3106s (00:00:51:46)
Estimated chat tokens: 144334 estimated from chat transcript bytes (577333 bytes; source: codex path: /home/owner/.codex/sessions/2026/10/03/rollout-2026-10-03T14-17-23-01a101e9-8669-7583-884f-752384e25131.jsonl)
Estimated chat cost: unavailable; no pricing profile selected
Estimated chat cost basis: unavailable; set CHAT_COST_PROFILE or CHAT_COST_PRICING_FILE

## Notes

- None recorded yet.

## Restart reconciliation — 3 October 2026

Scope: reconcile preserved platform work, investigate the missing scheduler/date-time
draft, and prepare the smallest restart change for review. The user explicitly
excludes deployment, AWS changes, branch deletion and replacement-programme
implementation. Task changes stay in this chat-owned worktree. No commit or
publication is requested.

Local branch and integration main both point to recovery merge
`2309e67683bf7d6c0e4dbb841e72de5d4c5f9a64`. This is a local observation, not a
fresh remote or AWS check. The historical recovery report's earlier unmerged
status is retained as historical evidence. The restored `platform/`,
`packages/core/`, `infra/` and `scripts/04.deploy/` source matches baseline
`0da085b50aac2b13dfb15aaac9351efea860926e` exactly.

Prompt-level ownership: read-only source reconciliation followed by factual
documentation corrections under
`.agentic/01.harness/workflows/change-harness.md` and its artifact/document
standards. Session handling remains under chat-start. No durable chat layer,
mode or implementation workflow is assigned. The initial strict cleanliness
check reported dirty because of this staged bootstrap README; the documented
`--allow-session-bookkeeping` check returned `bookkeeping-only`, and the
write-location check returned `chat-worktree`. Session-folder rename was a no-op.

### Preserved work inventory

The original repository remains
`/home/owner/projects/entity-builder-harness-001`, with local main at
`8052929cb947ef3a0199a338a997f8cc8ede3aac`. Its old main is not a restart
integration source. Durable recovery storage remains
`/home/owner/projects/entity-builder-recovery-2026-10-03/`.

| Workstream | Verified local state | Restart treatment |
| --- | --- | --- |
| Data governance / storage | Original `agent/data-governance-storage-foundation` at `542ca1700563dbba8a00fbf1ed911a4f55370c10`: one unintegrated commit, 77 paths. Against restart HEAD, 52 paths are absent and 25 differ; the commit object is not imported in this clone. | Preserve combined Core vocabulary/files split, platform data-governance/storage and persistence/observability seams. Review before selecting integration; historical tests were not rerun. S3, scanner/DLP, browser upload, archive restore and target mapping remain deferred. |
| Tenant execution authority | Original `agent/tenant-access-control-operationalization` at `e8810937b944efd8c821a08660d10ea195a2d362`: one unintegrated commit, 38 paths. Six are absent and 32 differ here; commit object not imported. | Preserve contracts, opt-in worker enforcement, security records and tests. Provider revocation, durable audit and target proof remain deferred. The branch also preserves the tenant-operationalization and platform-capability-catalog plans absent from this clone. |
| PostgreSQL recovery | `d8270e340f4e5b45b237a7e2ca7b8b7aedf0e24b` is an ancestor of restart HEAD. Its two relational-smoke controller/check files match restored baseline. | No source commit to recover. Stage 6 / recovery-4 remains unproved in recorded evidence; earlier bootstrap/recovery labels are consumed. No task was rerun and no live readiness is claimed. |
| Feature/platform consumption | Original root retains five modified tracked files and eight untracked files. All 13 byte-match both the recovery archive and recorded SHA-256 values. | Preserve and review as a complete governance draft. No copying into this worktree or piecemeal requirement changes. |
| Operational-realization gate | Current standard/workflow/compiler source matches restored baseline. Historical candidate `99dc7470` is not an ancestor of baseline; its hash alone does not prove integration. The September review records its source as superseded by main. | Credit existing gate source, retain all effective gates and inspect any proposed delta; do not merge the old candidate blindly. |
| Scheduler/date-time | Branch remains at its creation base; working source is absent. Original transcript contains substantial recovery evidence, described below. | Preserve evidence; do not call the branch an available source candidate or reconstruct during this preparation. |

PostgreSQL evidence:
[Stage 6 record](../../../../../docs/aws/kanbien-staging-postgresql-relational-reference-v1-stage6-evidence.md).
The existing whole-route prerequisite remains effective until separately approved
supersession; the replacement proposal does not change it.

The 13 original dirty files are:

```text
.agentic/03.product/README.md
.agentic/03.product/plans/implementation/product-harness-foundation.md
.agentic/03.product/workflows/README.md
.agentic/03.product/workflows/platform-runtime-implementation.md
package.json
.agentic/03.product/standards/feature-platform-consumption-decision-record.v1.md
.agentic/03.product/standards/platform-feature-consumption-matrix.v1.md
.agentic/03.product/templates/README.md
.agentic/03.product/templates/feature-platform-consumption-decision-record.v1.template.md
.agentic/03.product/workflows/feature-platform-consumption-decision-record.md
scripts/03.product/README.md
scripts/03.product/verify-platform-consumption-matrix/README.md
scripts/03.product/verify-platform-consumption-matrix/script.sh
```

Archive and hash inventory:
`/home/owner/projects/entity-builder-recovery-2026-10-03/evidence/entity-builder-recovery-evidence-2026-10-03/{root-uncommitted-files.tar,local-starting-state.json}`.
No original refs, working files or backups were imported, repaired or removed.
Other old worktree registrations and unusable directories were left untouched;
this review cannot certify missing working files or work on other machines.

### Scheduler/date-time investigation

The [27 September workstream review](../../../sep/27/2026-09-27-23-15-publish-deployment-reliability-plan/README.md)
records 78 uncommitted paths. The [3 October starting-state evidence](../2026-10-03-09-44-controlled-recovery-to-0da085b5/recovery-evidence/local-starting-state.json)
already records `/tmp/entity-builder-scheduler-time-platform` absent.
Its original branch `agent/scheduler-time-platform` still points to
`8052929cb947ef3a0199a338a997f8cc8ede3aac`; its reflog has only branch
creation on 26 September. Its surviving worktree index contains 1,485 entries
and no staged delta from HEAD. No committed reusable scheduler/date-time draft
was identified in the inspected local refs/history. The existing synthetic
monitoring scheduler is a different feature.

Substantial source evidence survives in the task-specific transcript:

```text
/home/owner/.codex/sessions/2026/09/26/rollout-2026-09-26T18-33-02-01a0dec7-0ed7-78b0-87d3-98dafe1375f3.jsonl
SHA-256: 9e4fa845fb68c4550e7452fbf0523283cbc7d577b7055d07a9fe3a9edb3b777f
```

| Transcript location | Evidence and limit |
| --- | --- |
| Line 222 | Untruncated 255-line capture of missing `.agentic/03.product/plans/implementation/platform-scheduler-v1.md`, including completion criteria. No filesystem copy found. |
| Patch calls throughout | 47 calls, 43 successful and four failed. Successful calls touch 78 distinct paths including transient/reverted config; 66 paths have full add-file content. This does not prove the final dirty tree has been recovered. |
| Lines 300, 717, 730, 1002 | Failed patch calls: any later recovery must reconcile them against subsequent successful changes, not replay them as completed edits. |
| Line 1253 | Final dirty status, package/export changes and an untruncated 79-line lockfile diff. An offline lockfile refresh occurred outside patch calls. |
| Lines 1217–1267 | Historical scheduler, EventBridge adapter, Core, time, contracts and production-build pass reports. No current rerun or independent completeness proof. |
| Line 1274 | Final handoff explicitly leaves the source draft uncommitted; durable worker terminal-outcome integration and live activation remain deferred. |

Draft surfaces named in this evidence include `packages/core/src/time/`,
`packages/core/src/scheduling/`, `platform/time/`, `platform/scheduler/`,
`platform/contracts/src/scheduling.ts`,
`platform/adapters/aws/scheduler/eventbridge/`, and
`docs/04.deploy/plans/kanbien-staging-scheduler-eventbridge-sqs-plan.md`.
These paths describe the missing draft, not files restored by this chat.

Conclusion: missing working source with substantial transcript recovery evidence.
The available evidence does not establish when or why the worktree disappeared,
nor exact final byte completeness. No patches were replayed and no missing
implementation was recreated. The root archive covers the 13 planning files,
not the scheduler draft.

A later recovery needs a named isolated transcript-reconstruction procedure or
recorded one-off exception under the missing-governance standard. The existing
active-path importer expects a present source tree and treats missing paths as
deletions, so it is unsuitable here. The prior source-recovery exception explicitly
does not establish precedent. This is a future recovery boundary, not a blocker
to the authorized investigation and documentation correction.

### Smallest restart review candidate

The sole task-document change is
[the convergence plan](../../../../../docs/04.deploy/plans/kanbien-staging-platform-foundation-convergence-v1.md):
replace stale source positions, credit preserved/integrated work, condition
scheduler review on verified recovery, and mark later phases as proposals.
Gate definitions, runtime/source implementations, historical recovery documents,
replacement proposal and deployment artifacts remain unchanged.

No source branch import, dependency installation, deployment, AWS call, commit,
push, history rewrite, branch deletion or cleanup was performed. Source-only
review can follow independently; any integration/reconstruction needs its own
bounded review. HTTP delivery and unfinished PostgreSQL remain separate later
decisions, with no readiness claim from this local inspection.

### Validation and preservation result

- Artifact metadata headers: passed, 969 files.
- Generated recognition sources: both current; no regeneration needed.
- Recognition validation: passed, 7 sources and 2,219 terms.
- Relative Markdown links in the two changed documents: all 13 resolve.
- Programme G0–G6 definitions: byte-identical to HEAD.
- Both staged and unstaged whitespace checks passed after removing trailing
  whitespace introduced by the ADR bookkeeping helper.
- Independent final diff review found no blocking issues and recommended no
  further task-file changes.
- Before/after read-only snapshots of the original repository and restart
  integration root match for HEAD, all refs, registered worktrees, index bytes,
  full dirty status and dirty-file SHA-256 values. The chat worktree's HEAD,
  refs, worktree registrations and existing index bytes also remain unchanged.
  Only this README and the convergence plan differ in its working tree.
- The original scheduler transcript SHA-256 was independently rechecked and
  matches the value above. No transcript content was rewritten or replayed.

The original-repository refs inventory SHA-256 is
`65c2233e6b053fb6f5dee7882f53674b308365dd521b428401f4ea63595b7bf2`;
the restart-repository refs inventory SHA-256 is
`453d76f966f1f52dbedf37de00f1c3901243c5bce854e1f7078969d24c8ca690`.
Both hash the output of
`git for-each-ref --format='%(refname) %(objectname)'`, including newlines.

Runtime tests were not rerun for this documentation-only change. Historical
source-check claims remain historical. No task commit was created; the original
staged bootstrap README is retained, and preparation edits remain unstaged for
review. The review candidate is complete; source recovery, integration and any
deployment remain future work requiring their own scope.

## Preservation and recovery continuation

The owner's follow-up accepts the factual corrections and requests durable
checkpointing, isolated scheduler reconstruction and review of preserved source.
It does not approve execution of the convergence programme. Earlier statements
that no commit/reconstruction was authorized describe the investigation phase.

Accepted documentation is committed as `4001c18e`, with session bookkeeping at
`dcb5fa9c`. A private complete-history Git bundle was created and verified at
`/home/owner/projects/entity-builder-scheduler-recovery-2026-10-03/bundles/restart-review-dcb5fa9c.bundle`.
SHA-256: `9ad2b06f95f27907b576e43f63ffd852129ed2ef92f0531d84417ed91dc65d38`.
The parent directory is private and outside `/tmp`; original/ref/dirty-file
snapshots are in its `snapshots/` directory. This is local durability, not an
off-machine backup. No original files, refs or backups were overwritten.

The new `recover-transcript-draft.md` workflow supplies the missing recovery
procedure, and `chat-commit.md` now requires verified durable preservation before
handoff. These reuse existing commit gates, export and bundle mechanisms; no new
deployment control or background service is introduced. The root cause of the
old worktree disappearance remains unknown. Checkpoints protect committed source
even if its worktree disappears; explicit evidence copies protect untracked inputs.

### Preserved-source review

Read-only review of original commits `542ca170` and `e8810937` recommends **no
integration as-is**. Historical tests were not rerun and no implementation was
imported or repaired. Parent inspection corroborated the storage boundary and
worker-disposition findings; this is source review, not live-exposure evidence.

| Priority / commit | Source location in preserved commit | Finding and required treatment before integration |
| --- | --- | --- |
| P1 / `542ca170` | `platform/storage/src/transfer.ts:10`, `index.ts:5` | Public raw state transitions bypass the legal-hold wrapper and accept quarantine approval without scan evidence. Enforce prerequisites at the shared transition boundary; test attempts to bypass hold/scan decisions. |
| P1 / `542ca170` | `platform/storage/src/access.ts:5` | Delivery grants ignore current handling permission and compare grant expiry with upload expiry. Require fresh authorization/current time and bounded delivery lifetime. |
| P1 / `542ca170` | `platform/storage/src/observability.ts:3` | Object spread forwards arbitrary extra properties into telemetry. Construct and validate an explicit safe-field allowlist; test content/URL/identity extras. |
| P2 / `e8810937` | `platform/workers/src/worker.ts:103,137`, `queue.ts:29` | The default queue removes a message before authorization; thrown/invalid authorizer results return without retry or dead-letter disposition. Preserve a recoverable disposition and test provider failure/malformed results. |
| P2 / `542ca170` | `platform/data-governance/src/resolution.ts:19` | Unknown profile references are copied into allowed policy; the unknown-reference denial only handles invalid current time. Validate the reference binding or keep that claimed stage incomplete. |

Storage's changed paths overlap subsequent baseline changes at `package.json`,
its historical session README and the architecture handbook. Tenant authority
overlaps the platform runtime plan and handbook. The two preserved branches
overlap at `package-lock.json` and the handbook. These are path comparisons, not
a performed merge test. Do not replace whole manifests/lockfiles from old branches.

### Restart approach disposition

Recommend a separately reviewed operation-specific HTTP restart scope, preserving
identity, actual-image, target configuration, rollback and outcome proof. The
replacement proposal remains a proposal. This continuation changes only chat
preservation/recovery instructions; it does not supersede the broad deployment
gates or authorize runtime repairs or cloud operations. The minimum deployment
instruction change still needs review against the exact clauses listed in the
replacement proposal before any route is executed. PostgreSQL follows HTTP;
scheduler/storage integration remains separate and subject to source review.
