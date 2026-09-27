# Chat Session: 2026-09-27-21-30 enforce-candidate-image-platform-and-rev

<!-- agentic-session
id: 2026-09-27-21-30-let-s-do-1
task: let's do 1
branch: chat/2026-09-27-21-30-let-s-do-1
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-09-27-21-30-let-s-do-1-2646609566
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-09-27T20:30:32Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-09-27T21:17:03Z
latest_commit_sha: e86f10e9
chat_duration: 2791s (00:00:46:31)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

let's do 1

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- A reviewed candidate image was accepted by source, scan, and change-set
  checks but failed only when ECS attempted to retrieve it. The safe evidence
  category was artifact distribution; the provider did not expose a reliable
  narrower cause through the permitted evidence boundary.

## Decisions Made

- Prevent the known recurrence class at publication time: the staging image
  contract is `linux/amd64`, the build wrapper forces that platform, and the
  deployment workflow pulls the exact immutable digest and verifies both its
  platform and its OCI source-revision label before it can continue.
- Retain a separate provider-neutral Operational Realization v2 programme for
  the full runtime-graph and private-execution proof. It is not represented as
  an already-complete operational proof.


- Decision: Promoted the verified deployment-hardening closure to origin/main
  Rationale: The isolated promotion worktree passed the workflow verifier and full infrastructure static suite; origin/main was fetched and proved equal to source commit 6a435b15 after a normal fast-forward push.

## Context Hygiene

- Durable evidence is the staging target profile, workflow verifier, immutable
  publication assertion, and the two deployment plans. Raw ECS stop reasons,
  task identifiers, ECR responses, and task logs were deliberately excluded.

## Activity Log

### 2026-09-27T20:30:32Z - Session started

Initial intent: let's do 1

### 2026-09-27 - Candidate image publication closure

- Performed read-only target inspection. Four candidate tasks failed before
  application startup with an artifact-distribution category; the live service
  remained on its prior completed deployment.
- Added a fixed `linux/amd64` build contract and immutable-digest platform and
  source-revision verification in the staging deployment workflow.
- Validated the deployment-workflow verifier, infrastructure static suite,
  shell syntax, and whitespace checks locally. No AWS resource was changed in
  this source-validation stage.


### 2026-09-27T21:17:03Z - Commit recorded

Commit: `e86f10e9`

Message: fix(deploy): verify published runtime image contract

Summary: Force the reviewed linux/amd64 image platform and verify immutable digest platform plus source revision before staging deployment continuation; record the provider-neutral realization follow-up.

ADR impact: no ADR; recorded in deployment plans


### 2026-09-27T21:18:22Z - Decision

Decision: Promoted the verified deployment-hardening closure to origin/main

Rationale: The isolated promotion worktree passed the workflow verifier and full infrastructure static suite; origin/main was fetched and proved equal to source commit 6a435b15 after a normal fast-forward push.

## Sub-Agent Activity

- Independent evidence audit: verified the source/payload seals already cover
  the PostgreSQL bootstrap entrypoint; an initial contrary claim was rejected
  after direct source inspection.
- Independent AWS evidence audit: classified the stopped candidate tasks as
  artifact-distribution failures without retaining raw provider responses.

## Commits



- Commit: `e86f10e9`
  Time UTC: 2026-09-27T21:17:03Z
  Message: fix(deploy): verify published runtime image contract
  Summary: Force the reviewed linux/amd64 image platform and verify immutable digest platform plus source revision before staging deployment continuation; record the provider-neutral realization follow-up.
  ADR impact: no ADR; recorded in deployment plans

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: The bounded `linux/amd64` publication fact and the longer Operational
Realization v2 delivery decision are recorded in the reviewed deployment plans;
this commit does not choose a new platform architecture.

## Session Metrics

Raised at UTC: 2026-09-27T20:30:32Z
Latest commit at UTC: 2026-09-27T21:17:03Z
Latest commit SHA: e86f10e9
Chat duration: 2791s (00:00:46:31)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- The next live action, if approved, is a new immutable candidate publication
  through the hardened workflow. It must not replay the terminal recovery
  label or modify the active service until its publication proof passes.
