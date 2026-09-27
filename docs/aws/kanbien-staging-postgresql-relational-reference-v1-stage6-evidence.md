<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.evidence.kanbien-staging-postgresql-relational-reference-v1-stage6
version: 2
status: draft
layer: 04.deploy
domain: persistence.operations
disciplines:
- security
- sre
kind: evidence-record
purpose: Record only safe evidence for the Kanbien staging PostgreSQL relational Stage 6 proof.
portability:
  class: target-specific
  targets:
  - kanbien/staging
-->
# Kanbien staging PostgreSQL relational Stage 6 evidence

## Current state

Stage 5 is complete: the Foundation database boundary is private, encrypted,
TLS-required, and has the documented loopback-only database egress correction.
The initial Stage 6 bootstrap label was consumed by a non-zero task result;
no migration, smoke record, queue delivery, worker, or restore stage was
started. Task identifiers, task logs, and provider details were deliberately
not retained in this evidence.

The recovery source moves PostgreSQL default-privilege ownership to the
migration identity and makes both running and stopped fixed task labels
single-use. `recovery-1` did not replay the initial label, but its bootstrap
also ended non-successfully; its derived-stream diagnostic returned only the
safe generic workload-failure marker. No later stage ran. The next immutable
image emits a fixed allowlisted bootstrap failure class, and defines one new
`recovery-2` label set. The recovery rollout guard accepts only revisions of
existing task definitions and existing in-place service references; it rejects
all resource additions, removals, IAM, database, queue, routing, and listener
changes.

The bootstrap-only recovery and its continuation are deliberately separate
commands. The continuation is available only after the one recovery bootstrap
has a successful terminal result; it verifies that predecessor in memory and
never starts bootstrap again. Its migration, relay, worker, restore, and
cleanup labels remain single use.

The corrected `recovery-1` bootstrap was deployed through the reviewed
service-only rollout and then exited non-successfully. Its diagnostic derived
the standard stream name in memory and found only the safe generic
workload-failure marker. No later stage started. The next source revision emits
an allowlisted bootstrap failure class while keeping raw task metadata,
identifiers, and logs private. It does not permit a replay.

When ECS omits the attached stream name, the diagnostic may derive the one
standard awslogs stream name from the consumed task only in memory. It reads
that exact stream before falling back to terminal metadata and never records or
emits the derived name.

Continuous reconciliation also distinguishes expired artifact-stack drift
evidence from an artifact mismatch. The read-only GitHub role reports an
expired fact but cannot refresh it; the administrator-only artifact assessor
can detect and poll the one fixed stack and records only an in-sync verdict.
No refreshed evidence is claimed here until that assessment and the following
reconciliation have both passed.

## Required live evidence fields

| Field | Allowed value shape |
| --- | --- |
| Source commit and immutable image | Commit SHA and image digest only. |
| Foundation/service change review | Named resource categories and replacement/no-replacement verdict only. |
| Preflight | Account/region verdict, server `1/1`, worker `0/0`, queue aggregate totals, stack health. |
| Bootstrap/migration/relay/worker | Stage name and success/failure verdict only. |
| Queue completion | Aggregate source and DLQ counts only. |
| Restore | Created/available/verified/cleaned duration categories; no instance or endpoint identifier. |
| Post-proof | Server/worker aggregate counts, queue totals, alarm state, cost/budget posture. |
| Residual limits | Single-AZ reference, no product data, no HA/RPO/RTO claim, RLS deferred. |

## Forbidden evidence

Never record or attach credentials, secret ARNs/values, headers, token data,
endpoints, connection strings, SQL, bind values, task identifiers, task logs,
record fields, queue messages, snapshot identifiers, or raw AWS responses.
