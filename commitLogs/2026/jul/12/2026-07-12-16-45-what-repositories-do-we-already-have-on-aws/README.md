# Chat Session: 2026-07-12-16-45 what-repositories-do-we-already-have-on-aws

<!-- agentic-session
id: 2026-07-12-16-45-what-repositories-do-we-already-have-on-aws
task: what repositories do we already have on AWS?
branch: chat/2026-07-12-16-45-what-repositories-do-we-already-have-on-aws
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-12-16-45-what-repositories-do-we-already-have-on-aws-2778004660
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-07-12T15:45:55Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-07-12T16:27:22Z
latest_commit_sha: c342692
chat_duration: 2487s (00:00:41:27)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

what repositories do we already have on AWS?

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

- Selected `platform-shell` as the planning-only ECR repository name for the
  Kanbien staging product platform shell.
- Selected the recommended tag/provenance policy: deployable staging images
  must be built from pushed `origin/main`, use immutable tags shaped as
  `staging-<YYYYMMDD>-<short-sha>-run<github-run-id>`, deploy by digest, record
  minimum staging provenance evidence, and keep SBOM plus attestation as
  blockers before public exposure.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Platform shell ECR repository and image provenance planning decisions are captured in deploy readiness and AWS inventory evidence.

## Context Hygiene

- Kept the slice planning-only: live AWS access was read-only, no ECR
  repository was created, no image was built or pushed, and no secret values
  were requested or recorded.
- Fast-forwarded the chat worktree from local `main` before editing so the
  ECR/tag policy updates were applied on top of the worker-capable platform
  shell target plan.

## Activity Log

### 2026-07-12T15:45:55Z - Session started

Initial intent: what repositories do we already have on AWS?

### 2026-07-12T15:57:08Z - Recorded platform shell ECR repository-name decision

- Live read-only ECR inventory found `rag-rulebook-service` and
  `kanbien/service-platform`; no existing platform shell ECR repository was
  found.
- Recorded `platform-shell` as the selected product platform shell ECR
  repository name while keeping repository creation and image provenance
  blocked pending governed AWS mutation.

### 2026-07-12T16:16:26Z - Recorded tag/provenance policy decision

- Recorded pushed `origin/main` as the official deployable build source.
- Recorded immutable ECR tags, digest-based deploy references, base-image digest
  pinning, and minimum first-staging evidence requirements.
- Kept SBOM and attestation as readiness blockers before public exposure rather
  than first-staging implementation requirements.


### 2026-07-12T16:20:39Z - Decision

Decision: Record RAG knowledge disposition: covered

Rationale: Platform shell ECR repository and image provenance planning decisions are captured in deploy readiness and AWS inventory evidence.


### 2026-07-12T16:27:22Z - Commit recorded

Commit: `c342692`

Message: Plan platform shell image provenance

Summary: Recorded Kanbien staging platform-shell ECR repository naming and image tag/provenance readiness policy without AWS mutation.

ADR impact: No new ADR; covered by existing platform runtime and AWS runtime-family decisions.

## Sub-Agent Activity

- None recorded yet.

## Commits



- Commit: `c342692`
  Time UTC: 2026-07-12T16:27:22Z
  Message: Plan platform shell image provenance
  Summary: Recorded Kanbien staging platform-shell ECR repository naming and image tag/provenance readiness policy without AWS mutation.
  ADR impact: No new ADR; covered by existing platform runtime and AWS runtime-family decisions.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This slice records target-profile planning choices for an ECR
repository name and image provenance policy under existing platform runtime and
AWS runtime-family decisions; it does not introduce a new architecture decision
or mutate AWS.

## Session Metrics

Raised at UTC: 2026-07-12T15:45:55Z
Latest commit at UTC: 2026-07-12T16:27:22Z
Latest commit SHA: c342692
Chat duration: 2487s (00:00:41:27)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- None recorded yet.

## RAG Knowledge Disposition

Status: covered
Reason: Platform shell ECR repository and image provenance planning decisions are captured in deploy readiness and AWS inventory evidence.
Evidence:
- infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
- docs/aws/inventory/kanbien-staging-platform-shell-target-inspection.md
Corpus gaps:
- None.
