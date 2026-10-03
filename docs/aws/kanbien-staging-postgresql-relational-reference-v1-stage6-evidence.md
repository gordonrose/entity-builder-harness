<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.evidence.kanbien-staging-postgresql-relational-reference-v1-stage6
version: 3
status: draft
layer: 04.deploy
domain: persistence.operations
disciplines:
- security
- sre
kind: evidence-record
purpose: Record only safe evidence for the Kanbien staging PostgreSQL relational Stage 6 proof.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.run-platform-shell-postgresql-relational-smoke.readme
  path: scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/README.md
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
single-use. Recoveries 1 and 2 ended non-successfully without starting later
stages. Recovery 3 safely classified its failure as input validation: the
RDS-managed master credential shape supplies credentials, while the approved
target-owned migration connection supplies the endpoint. The corrected source
combines those two approved inputs without logging either, and defines one new
`recovery-4` label set. Its regression check requires that exact
credentials-only-master path. The recovery rollout guard accepts only revisions
of existing task definitions and existing in-place service references; it
rejects all resource additions, removals, IAM, database, queue, routing, and
listener changes.

The bootstrap-only recovery and its continuation are deliberately separate
commands. The continuation is available only after the one recovery bootstrap
has a successful terminal result; it verifies that predecessor in memory and
never starts bootstrap again. Its migration, relay, worker, restore, and
cleanup labels remain single use.

No consumed label may be replayed. The next run is a new immutable candidate,
then a new service-only rollout, then exactly one bootstrap under
`recovery-4`. Migration, relay, worker, restore, and cleanup remain unavailable
unless that bootstrap has a successful terminal result.

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

## Pre-execution source preparation — 2026-10-03

The scoped Stage 6 applicability amendment has been adopted for source
preparation only. The relational and candidate controllers now retain safe,
finite attempt receipts across a local process restart; unknown submissions and
timeout cleanup obligations block retries, and a completed checkpoint is not
replayed during continuation. Local controller, adapter, real-engine,
compiled-image, and infrastructure checks passed. The restore verifier now
requires migration checksum, work-item, published-outbox, and completed-worker
state together.

A fresh read-only boundary check could validate the source policy but could not
use the configured AWS identity. It did not obtain current account, database,
network, health, drift, cost, or recovery-4 facts. No AWS mutation, image
publication, deployment, or Stage 6 task ran. Recovery-4 remains unreconciled;
recovery-5 is source-qualified only and requires final execution approval after
fresh target reconciliation.

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
