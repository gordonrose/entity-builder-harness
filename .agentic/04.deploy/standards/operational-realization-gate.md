<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: deploy.standard.operational-realization-gate
  version: 6
  status: active
  created_on: "2026-09-27"
  updated_on: "2026-11-27"
  layer: 04.deploy
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
  - id: deploy.workflow.operational-realization-gate
    path: .agentic/04.deploy/workflows/operational-realization-gate.md
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

## Ownership and Applicability

The [shared change-completion standard](../../shared/standards/require-change-completion.md)
owns cross-layer completion principles. This deployment standard owns the
realization contract, proof levels and ordered deployment gates. Lifecycle
standards refine the evidence required at their stage; their checks implement
this authority rather than redefining completion.

Provider-specific inspection, mutation, permission and applicability procedures
remain in the active provider governance surface indexed by
[provider ownership](../providers/README.md). An operation-specific exception
must cite its provider-owned applicability rule and recorded approvals; an
exception never grants execution authority or weakens an applicable executable
gate. Without that record, the normal requirements below apply.

## End-to-end live-delivery authority

<!-- deterministic-check: allow reason="interpreting the user's task and matching its intended effects requires judgment; existing exact-plan controllers enforce the concrete execution boundary" -->
An explicit instruction to execute an end-to-end live deployment authorizes
the complete named delivery, not merely planning it. Resolve the repository,
publication destination, target/scope and provider account/region from that
instruction and established context. Record the original request and its limits
in the existing session/change record before starting. Ask only for genuinely
missing scope information; do not defer authority discovery until publication.

Within that boundary, approval covers necessary task edits, checks, local
checkpoints, normal governed integration/push, build, qualification, publication,
declared deployment/setup, verification, acceptance and declared conditional
recovery. This includes required in-scope corrections and their requalification
and republication. It does not authorize unrelated work. Existing explicit user
restrictions remain binding unless the user changes them. A request only to plan,
explain, implement locally or test locally does not authorize live delivery.

Do not ask again at each stage, after an interruption, or solely because an
image digest, source checkpoint or plan hash becomes available. Review the actual
generated plan against the recorded task authority, record the exact derived
binding and use the existing approval inputs/controllers. Distinguish the user's
task approval from the agent's later plan review; never claim the user reviewed
a hash they were not shown. A corrected candidate requires new qualification
and matching plans, not another prompt when its effects remain within scope.

All source, package, live-state, change-shape, ownership and recovery gates still
apply. Declared disposable proof-resource cleanup may be included in the
delivery boundary; it requires positive ownership and original successful proof
before deletion. A different target/account, broader permissions, shared-resource
changes outside the declared delivery, source-data deletion, history rewriting,
discarding unrelated work or new ungoverned recovery is not implied authority.
Stop only that affected operation and resolve the actual missing authority or
governance; continue independent authorized work. Reconcile uncertain effects
without replay. Authentication or other unavailable external prerequisites may
require user help, but do not revoke the existing task approval.
This rule does not override platform-enforced or tool-level permission controls.

Carry the original authority, explicit restrictions, current source/receipt/plan
bindings and remaining steps through session logs, handoffs and compaction.
Assistant-written summaries must not invent narrower "local-only" permission;
"no AWS changes performed" reports an outcome, not an authorization limit.
Consult the original user request if a summary conflicts with it.

Review examples: "deploy this named release end to end" covers its normal
commit/push/publication and reviewed declared execution without another prompt;
"prepare a deployment plan" does not. A new hash for the same approved delivery
requires revalidation, not renewed consent; an unplanned shared-network change
requires a scope decision. These are instruction-review cases, not executable
evidence of agent compliance or permission to bypass a controller.

## Required Realization Contract

Every capability that can mutate a live target, perform a migration, execute a
background job, or require a recovery action must have a versioned realization
contract before execution. The existing
[v1 template and schema](../../01.harness/templates/operational-realization-contract.v1.guide.md)
retain their compatible paths and admission behaviour. Select
[v2](../schemas/operational-realization-contract.v2.guide.md) for explicit
synchronous unit-to-unit connections or workloads without direct storage.
Declare empty connection/store lists explicitly rather than invent a dependency.
Direct store declarations must match the unit's own connections; a service call
does not confer its callee's storage authority. This standard owns both
versions' deployment semantics; all proof levels, ordered gates, safety and
provider approval requirements below remain mandatory.

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

## Bounded disposable-restore change shape

Ordinary contracts continue to forbid delete, replace and permission broadening.
Only v2 may explicitly declare `change_shape.disposable_restore_cleanup`, with
exactly four true fields: `original_readback_required`,
`positive_ownership_required`, `explicit_execution_approval_required` and
`preserve_source_and_shared_resources`. Its allowed classes must be exactly
`[delete]`; forbidden classes exactly `[create, update, replace, broaden-permission]`.
Malformed or partial opt-ins fail closed. Existing v1 admission is unchanged.

The exact alternative terminal-failure variant replaces
`original_readback_required` with `original_terminal_failure_required` and
`no_unresolved_dependents_required`, both true. The other three fields and
delete-only classes stay unchanged. It requires separately authorized cleanup,
authenticated original failure and complete owned resources; unknown outcomes
remain blocked and this variant cannot establish successful recovery acceptance.

This declaration permits validation of the truthful cleanup shape, not execution.
An applicable provider-owned rule and actual controller must separately require
the original successful readback, positive disposable-resource ownership and
explicit concrete execution approval, protecting source and shared resources.
All eight gates, input-bound evidence and actual normalized change counts still
apply. The compiler cannot establish those provider facts from booleans. The
currently approved provider case is solely the entity-smoke isolated restore
under its [applicability rule](../../aws/standards/operational-realization-applicability.md#entity-smoke-disposable-restore-cleanup).

## Proof Levels

Proof levels are ordered. A higher level can satisfy a lower requirement.

1. `declared` — reviewed source declares the fact.
2. `locally-proven` — a clean, disposable local environment exercises it.
3. `live-read-proven` — a safe, read-only target inspection confirms it.
4. `live-execution-proven` — a bounded real operation proves it.

`unknown` is never an acceptable actual or required proof state. It is a
deliberate stop signal in a contract and is rejected by the compiler.

## Proof applicability by change

Use the existing scope, capability and realization declarations to distinguish
what changed before selecting proof. Record the reasoning in the existing
change inventory, not a new registry. This classification guides connected
implementation and evidence selection; it does not itself add a schema field,
grant an exception or weaken an executable requirement.

| Change | Required assessment |
| --- | --- |
| New or materially changed platform/infrastructure capability | Qualify the new execution, access, state and recovery behaviour at its owning boundary. Expose reusable capability inputs and proof bindings for later consumers, not a workload-named copy of the machinery. |
| New feature/app/workload using qualified capability | Identify matching reusable capability evidence and prove the new workload's actual package, configuration, permissions, migrations and meaningful operation. A shared engine or passing old workload is not proof that this workload works. |
| Update within an existing qualified route | Invalidate evidence for changed inputs and affected dependencies; reuse only still-matching evidence through its owning reader. Always obtain the fresh target/operation observations required by the gates. |
| Removal, retirement or changed isolation/ownership | Prove affected callers, permissions, data-retention and recovery consequences. Source removal is not authority to delete remote resources or erase accepted history. |

For each selected obligation, name its existing owner, current input binding,
whether execution or valid retained proof supplies it, and the invalidation
conditions. Changes to migrations, permissions, runtime, state semantics or
recovery can invalidate capability proof as well as workload proof. Review the
actual affected boundary, not just the changed filename. Reusing a capability
must neither trigger a full infrastructure rehearsal solely because a feature
has a new name nor substitute capability proof for its new workload obligations.

First-acceptance replacement/restore requirements remain effective. Persistence
and entity-smoke ordinary updates use their acceptance schema's `ordinary_update`
policy and the shared immutable-input comparator. Fresh deployed identity,
migration state, effective access, meaningful operation and readiness are never
replaced by recovery history. Reuse requires exact validated accepted-predecessor
custody and unchanged declared recovery inputs, contracts and database incarnation.
Absent or unverifiable bindings require requalification; old records are not
retroactively upgraded. Changed-capability execution remains separately selected,
not an implicit effect of collection. Other routes keep their declared proof sets.
Any further selective policy must migrate its declaration, validator, collector
and tests together. These local controls do not establish live delivery timing.

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

## Executable evidence reuse

Normalized gate and component evidence carries `input_sha256`, computed by the
compiler's `evidence_bindings(contract, facts)` helper. Component bindings cover
the declared outgoing dependency closure and exact runtime artifact digests.
The artifact gate binds artifact declarations and exact digests, qualification
configuration declarations, workload artifact/configuration composition, and
its declared qualification check. Source validation binds the full reviewed
contract; later operational gates also bind runtime artifact identities. A
permission-only change therefore preserves the actual artifact gate receipt,
including its original timestamp, while requiring affected structural and
operational checks again. Changed package bytes, entrypoint, configuration or
workload composition invalidates that receipt. Adapters retain
qualified immutable evidence rather than replacing its timestamps with now.

The core requires each gate's declared check ID and chronological current-state
stage evidence. Fresh structural revalidation may consume older immutable proof
when its stage-specific input identity still matches.
At live stages, live-read, change-set and execution-preflight observations, the
change summary, and non-artifact component observations expire after 900 seconds;
future observations beyond 60 seconds are rejected. Historical source, artifact
and semantic-integration proof does not expire solely with age when its relevant
inputs still match. Provider adapters remain responsible for obtaining actual
current target/configuration/permission facts and exact artifact identity. A
locally constructed fixture proves only these compiler boundaries.
