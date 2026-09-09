# Chat Session: 2026-09-09-20-04 record-the-bounded-dynamodb-production-reference-decision-fo

<!-- agentic-session
id: 2026-09-09-20-04-record-the-bounded-dynamodb-production-reference-decision-fo
task: Record the bounded DynamoDB production-reference decision for the smoke-platform proof.
branch: chat/2026-09-09-20-04-record-the-bounded-dynamodb-production-reference-decision-fo
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-09-09-20-04-record-the-bounded-dynamodb-production-reference-decision-fo-865966666
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-09-09T19:04:33Z
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

Record the bounded DynamoDB production-reference decision for the smoke-platform proof.

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked



- Asked: How should a queue relay and worker handle duplicates, stale processors, and dead-letter recovery?
  Response: Use provider-neutral delivery policies, durable idempotency, leases/fencing for restartable work, completion before acknowledgement, and restricted linked DLQ recovery.

## Issues Raised



- Raised: The last worker and DLQ learning chunks had been explained but not yet written to the durable records.
  Resolution: Added them to the handbook, both implementation plans, and the session log before continuing.

## Decisions Made

- Selected DynamoDB on-demand in the initial EU reference region as the future
  storage provider for one bounded, harmless `platform-smoke` transactional
  state/outbox proof. It is a low-cost operational reference selection, not a
  general Entity Builder persistence decision.
- At the initial DynamoDB decision point, kept the relay's queue/event
  transport, DynamoDB adapter/table design, AWS infrastructure, and future
  entity persistence explicitly unselected. No AWS resource change is
  authorised by either decision.
- Selected SQS Standard with a DLQ as the future relay transport for the
  bounded smoke proof. The approved `platform-short-idempotent-work.v1`
  direction has a 30-second execution budget, two-minute visibility period,
  five delivery attempts, bounded exponential backoff with jitter, seven-day
  main retention, fourteen-day DLQ retention, and manual DLQ recovery.
- For the future relay/worker proof, recorded that an outbox record is marked
  published only after provider acceptance; duplicate publish after a relay
  crash is expected and must be made harmless by durable worker idempotency.
  A worker records durable completion before acknowledging its queue message,
  uses conditional lease/fencing state, and treats the DLQ as a restricted
  quarantine with manual, linked recovery rather than a purge or blanket
  replay mechanism.
- Apps will declare a named provider-neutral delivery policy and business
  idempotency/transition meaning. Platform workers own generic lease/fencing
  mechanics. Ordinary entity edits remain revision-based unless an explicitly
  scoped restartable workflow needs exclusive processing.

## Context Hygiene



- Summary: The durable carry-forward is the bounded DynamoDB plus SQS Standard/DLQ smoke-proof direction, its named delivery policy, and the relay/worker/DLQ safety rules.
  Durable evidence: Production-reference baseline, platform-runtime implementation plan, handbook lessons 78-83, and this session log.

## Activity Log

### 2026-09-09T19:04:33Z - Session started

Initial intent: Record the bounded DynamoDB production-reference decision for the smoke-platform proof.

### 2026-09-09T19:04:33Z - Bounded reference selection recorded

Updated the production-reference baseline, platform-runtime implementation
plan, and architecture-learning handbook. The plans now distinguish the
future non-business smoke work-item/outbox/evidence proof from real entity
persistence, and retain a separate queue/relay provider decision. No runtime
source, provider adapter, infrastructure resource, or AWS state changed.

### 2026-09-09T19:04:33Z - Initial SQS delivery direction recorded

Updated the same plans and handbook with the selected SQS Standard/DLQ
transport, generic-versus-target configuration boundary, and short idempotent
work defaults. The future adapter, target profile, queue resources, and AWS
mutation remain deferred.

### 2026-09-09T22:12:50Z - Worker and DLQ safeguards recorded

Updated the production-reference baseline, platform-runtime implementation
plan, and learning handbook with the required relay ordering, worker
claim/complete/acknowledgement order, duplicate and stale-lease protection,
failure classification, and restricted DLQ recovery model. No runtime source,
provider adapter, infrastructure resource, or AWS state changed.

### 2026-09-09T22:12:50Z - Coordination ownership recorded

Updated both implementation plans and the learning handbook to distinguish
app-declared delivery and business semantics from platform-owned generic
lease/fencing mechanics. The record also preserves revision-based concurrency
as the default for ordinary entity updates. No runtime source, provider
adapter, infrastructure resource, or AWS state changed.


### 2026-09-09T22:58:02Z - Question

Asked: How should a queue relay and worker handle duplicates, stale processors, and dead-letter recovery?

Response: Use provider-neutral delivery policies, durable idempotency, leases/fencing for restartable work, completion before acknowledgement, and restricted linked DLQ recovery.


### 2026-09-09T22:58:02Z - Issue

Raised: The last worker and DLQ learning chunks had been explained but not yet written to the durable records.

Resolution: Added them to the handbook, both implementation plans, and the session log before continuing.


### 2026-09-09T22:58:02Z - Context hygiene

Summary: The durable carry-forward is the bounded DynamoDB plus SQS Standard/DLQ smoke-proof direction, its named delivery policy, and the relay/worker/DLQ safety rules.

Durable evidence: Production-reference baseline, platform-runtime implementation plan, handbook lessons 78-83, and this session log.


### 2026-09-09T22:58:03Z - ADR disposition

ADR needed: no

Reason: The DynamoDB/SQS selection is a bounded draft smoke-reference decision in the existing production-reference baseline, not an implemented cross-product standard or irrevocable provider architecture decision.


### 2026-09-09T22:58:03Z - Commit summary

Commit: docs(platform): record smoke queue reliability decisions

Summary: Record the bounded DynamoDB/SQS smoke-proof direction, relay and worker safety rules, DLQ recovery constraints, and platform-versus-app coordination ownership.

ADR impact: No ADR: bounded draft reference-target decision recorded in existing plans; no production implementation, AWS resource, or provider standard is approved.

## Sub-Agent Activity

- None recorded yet.

## Commits



- Commit: docs(platform): record smoke queue reliability decisions
  Summary: Record the bounded DynamoDB/SQS smoke-proof direction, relay and worker safety rules, DLQ recovery constraints, and platform-versus-app coordination ownership.
  ADR impact: No ADR: bounded draft reference-target decision recorded in existing plans; no production implementation, AWS resource, or provider standard is approved.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: The DynamoDB/SQS selection is a bounded draft smoke-reference decision in the existing production-reference baseline, not an implemented cross-product standard or irrevocable provider architecture decision.

## Session Metrics

Raised at UTC: 2026-09-09T19:04:33Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.
