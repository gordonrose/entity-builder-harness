<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.standard.operational-realization-gate
  version: 2
  status: active
  layer: 01.harness
  domain: deployment.realization
  disciplines:
  - architecture
  - security
  - sre
  kind: standard
  purpose: Require complete, provider-neutral proof of a deployable capability before a live mutation or recovery attempt.
  portability:
    class: reusable
    targets:
    - entity-builder
  used_by:
  - id: harness.workflow.operational-realization-gate
    path: .agentic/01.harness/workflows/operational-realization-gate.md
  - id: deploy.script.operational-realization-gate
    path: scripts/04.deploy/operational-realization-gate/script.py
-->
# Operational Realization Gate

## Purpose

An implementation is not operational merely because its source, infrastructure
template, image, or unit tests are individually valid. A deployable capability
is operational only when its complete execution graph has been declared and
evidenced: artifact through execution, identity, configuration, connections,
state, asynchronous work, telemetry, and recovery.

This standard prevents live discovery from becoming the first integration test.
It is provider-neutral. Cloud providers, container runtimes, database engines,
and queue products are represented only by separately maintained adapters that
produce normalized facts. They never appear in the generic contract or core
verifier.

## Bounded PostgreSQL Stage 6 Applicability

The [Kanbien/staging PostgreSQL restart plan](../../aws/plans/implementation/postgresql-stage6-restart-2026-10-03.md)
provides an operation-scoped alternative only after the user explicitly adopts
this applicability change and approves its concrete execution plan. Saving a
draft or applying this instruction change alone grants no execution authority.
Until both approvals exist, the normal requirements below remain effective.

For that approved slice only, its reviewed operation/evidence matrix replaces
whole-route generic contract/compiler migration and full-estate programme
completion as prerequisites. It must cover every actual dependency of the
selected PostgreSQL operation: reviewed source, immutable image and entrypoint,
adapter/target compatibility, identity, safe configuration shapes, TLS/network,
database semantics, queue completion, observability, cost and bounded recovery.
Evidence from a healthy HTTP process does not qualify a relational task.

Existing executable gates remain binding, including applicable realization,
reconciliation, change-shape and candidate/task preflights. A required failure
pauses the affected operation and its dependants while its outcome is reconciled
and relevant code/configuration is repaired within the approved allowance.
Rerun affected checks, prove proportionate prevention, qualify a changed image
and resume from the first incomplete checkpoint. Do not close out merely to
report an ordinary failure that can be safely repaired within that authority.
No failed check is bypassed or manufactured into a pass.

The concrete approval must include the plan's source/configuration repair,
image-publication, reattempt, time, cost and owned-recovery allowances. Passing
source review and renewed operation bindings within them do not require a new
human execution approval per repair. Existing controllers must enforce the
supported identities, checkpoint semantics and cumulative limits before this
route is executable; instruction prose alone is insufficient. Scheduler,
storage, tenant authority and the replacement programme remain deferred.

Preserve consumed labels, terminal outcomes, uncertain-outcome reconciliation,
rollback/restore and verified cleanup. Reuse unchanged artifact evidence only
with unchanged relevant bindings and valid freshness; a failed attempt remains
terminal. A new attempt need not imply a new image, but must use an explicitly
reviewed, supported identity and recovery route within approved limits. Count
all failed or possibly accepted submissions across new labels/images/chats.
Escalate exhausted limits, new effects, broader permissions, persistent-data
repair outside the approved manifest, or inability to reconcile and recover
safely. Expressly approved cleanup of positively owned disposable restores and
reviewed rollback use their recovery allowance without redundant reapproval;
other destructive actions need separate authority.

For every material failure record evidence, cause and earlier-check gap,
correction/verification, proportionate prevention with proof, and resumed
outcome or precise blocker in existing Stage 6/session records. At closeout
provide both PostgreSQL acceptance evidence and those completed records.
Keep evidence safe and append-only. Other capabilities use the normal
contract/compiler route; generic schemas and compiler guarantees are unchanged.

## Required Realization Contract

Every capability that can mutate a live target, perform a migration, execute a
background job, or require a recovery action must have a versioned
`operational-realization-contract/v1` before execution. Use the template and
schema in this directory's sibling template area.

The contract must declare all of the following.

| Area | Required declaration |
| --- | --- |
| Artifact | Immutable artifact reference, expected entrypoint, and runtime payload assertions. |
| Execution | Every execution unit and its exact artifact, identity, configuration, connections, stores, channels, telemetry profile, and recovery plan. |
| Authority | Separate machine identities and the narrowly named permissions each unit requires. |
| Configuration | Names and safe shapes only: required fields, allowed types, and sensitivity classification; never values. |
| Connections | Every network or local connection, TLS expectation, and authorized source/destination relationship. |
| State | Every state store and its engine semantics, transaction/concurrency requirements, and lifecycle boundary. |
| Async | Every channel, producer/consumer relationship, idempotency boundary, delivery acknowledgement, and terminal handling. |
| Lifecycle | Explicit states, permitted transitions, terminal states, and a labelled non-replay recovery policy. |
| Observability | Safe telemetry, audit, health, and evidence requirements for each unit. |
| Change shape | Allowed and forbidden operation classes, expected review, rollback, and recovery shape. |
| Assumptions | A stable ID, safe statement, required proof level, and actual proof level for every non-obvious dependency. |

An execution unit may not depend on an implied service or setting. Each such
relationship must be an explicit edge between declared nodes. The compiler
rejects unknown nodes and missing dependency edges.

## Proof Levels

Proof levels are ordered. A higher level can satisfy a lower requirement.

1. `declared` — reviewed source declares the fact.
2. `locally-proven` — a clean, disposable local environment exercises it.
3. `live-read-proven` — a safe, read-only target inspection confirms it.
4. `live-execution-proven` — a bounded real operation proves it.

`unknown` is never an acceptable actual or required proof state. It is a
deliberate stop signal in a contract and is rejected by the compiler.

## Mandatory Gate Sequence

The following sequence is fixed. Evidence is append-only and safe: it records
contract IDs, check IDs, verdicts, timestamps, and aggregate counts, never
secret values, opaque provider responses, request bodies, headers, endpoints,
task identifiers, rows, or queue messages.

1. **source** — validate source boundaries, declarations, and deterministic
   checks in a clean checkout.
2. **artifact** — build the real immutable artifact and inspect the actual
   entrypoint, runtime payload, permissions, provenance, and scan results.
3. **semantic-integration** — exercise real engine and lifecycle semantics in
   a disposable environment.
4. **live-read** — compare normalized read-only target facts with the
   contract.
5. **change-set** — compare a normalized provider change summary with the
   allowed and forbidden operation shape.
6. **execution-preflight** — exercise the exact deployed execution boundary
   without business-state mutation.
7. **controlled-execution** — perform the one bounded, labelled approved live
   operation.
8. **recovery** — execute only a separately labelled, reviewed recovery path
   after a terminal outcome; it is never an implicit replay.

No live mutation may begin until evidence for every preceding gate passes.
Recovery is a mutation too: it requires all preceding gates, a terminal prior
attempt, a new immutable attempt label, and explicit cleanup/rollback facts.

## Provider Adapter Boundary

The core compiler accepts only `operational-realization-normalized-facts/v1`
and `operational-realization-normalized-change-summary/v1`. Facts contain
only exact allowlisted fields: generic component IDs and kinds, stable check
IDs, UTC timestamps, passed gate/component verdicts, and the reviewed
recovery predecessor/new-attempt relationship. Change summaries contain only
a stable check ID, UTC timestamp, and declared aggregate operation counts.
Unknown fields and unsafe field names are rejected. The documents use generic
categories such as `artifact`, `identity`, `connection`, `state-store`,
`async-channel`, `execution-unit`, and `operation-class`.

Provider adapters are separately named, outside this core. Their job is to:

- inspect or plan with a provider's SDK or CLI;
- redact and normalize provider facts;
- prove each declared component binding, including artifact, identity,
  configuration, connection, state store, and channel, rather than only
  asserting a gate verdict;
- prove their own permission boundary; and
- pass only normalized facts/change counts to the generic compiler.

The generic contract, compiler, fixtures, and core documentation must not
mention provider resource types or import provider adapter code. A static
boundary check enforces this.

## Recovery and Retry Rules

The lifecycle must include `succeeded`, `failed`, and `stopped` terminal
states. A terminal attempt cannot transition back to `running`. Automatic,
unlabelled, or in-place replay is prohibited. A recovery attempt must have a
new immutable label, explicit failed/stopped predecessor, entry condition,
maximum attempt count, safe cleanup action, and evidence requirement. The
adapter proves the label is new in the target; the generic core validates the
safe normalized assertion and prevents in-place reuse.

## Compliance

Run `npm run deployment:realization:check` before requesting a live change.
Run `npm run deployment:realization:test` when changing the compiler,
template, schema, or fixtures. A target-specific execution workflow must cite
the realization contract and retain the gate evidence before it performs a
provider mutation.
