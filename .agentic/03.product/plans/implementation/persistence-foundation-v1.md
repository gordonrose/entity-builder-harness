<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.plan.persistence-foundation-v1
version: 30
status: active
layer: 03.product
domain: persistence
disciplines:
- architecture
- security
- sre
- requirements
kind: implementation-plan
purpose: Deliver a provider-neutral persistence foundation and prove its bounded DynamoDB/SQS transactional-outbox path on the Kanbien staging platform-smoke target.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.architecture.plan.platform-runtime-implementation
  path: .agentic/03.product/plans/implementation/platform-runtime-implementation.md
- id: product.plan.production-reference-target-baseline
  path: .agentic/03.product/plans/implementation/production-reference-target-baseline.md
- id: product.workflow.platform-runtime-implementation
  path: .agentic/03.product/workflows/platform-runtime-implementation.md
-->
# Persistence Foundation v1

## Purpose

Deliver the first reusable persistence foundation for the platform, then prove
the most important consistency path on `kanbien/staging`:

```text
harmless smoke state change
  + bounded record-change entry
  + durable outbox obligation
             │ one atomic DynamoDB transaction
             ▼
outbox relay ──> SQS Standard queue ──> duplicate-safe worker ──> durable result
```

The goal is not merely to demonstrate that a record can be saved. It is to
prove that a state change cannot be committed while its required later work is
silently lost, and that a retry or duplicate message cannot perform that work
twice.

This is the executable delivery plan for the persistence direction already
recorded in the [platform runtime plan](platform-runtime-implementation.md)
and the [production reference target baseline](production-reference-target-baseline.md).
Those documents remain the architectural constraints; this document owns the
ordered implementation and evidence path.

## Status And Authority

This plan authorises repository planning and local implementation work. It does
not by itself authorise AWS mutation. Every CloudFormation, IAM, ECS, DynamoDB,
or SQS change must first pass the applicable `04.deploy` planning and approved
AWS-execution workflow, including an inspected change set and explicit current
approval.

The initial live proof is intentionally bounded, harmless, EU-only, and
cost-aware. It may not carry customer, tenant, personal, medical, document,
prompt, transcript, credential, token, or raw request data.

### Implementation progress

- **2026-09-23 — Phase 1a complete:** the existing Core persistence module was
  split into named concurrency, error, pagination, repository, transaction,
  and in-memory-helper files. Its public barrels and behaviour remain
  compatible, and the Core type, runtime, and boundary checks pass.
- **2026-09-23 — Phase 1b complete:** Core now provides immutable, versioned
  outbox routing facts and a bounded record-change lineage envelope. Runtime
  and type tests prove their validation rules, while Core's boundary test
  confirms that provider vocabulary has not leaked in.
- **2026-09-24 — Phase 1c complete:** Core now provides a database-neutral
  logical-record lifecycle contract. It retains a reviewed retention-policy
  reference with a deletion marker and recovery boundary, can determine
  legal-hold-aware purge eligibility without deleting anything, and has closed
  restore and validation errors. Core runtime/type checks prove deletion,
  restoration, stale restoration rejection, and the existing bounded
  `deleted`/`restored` lineage actions.
- **2026-09-23 — Phase 2a complete:** `platform/persistence` now provides
  provider-neutral in-memory outbox, processing, and lineage ports. Its
  deterministic tests prove pending-to-leased-to-published transitions,
  duplicate recognition, lease expiry, fence advancement, stale-fence
  rejection, and append-only lineage behaviour.
- **2026-09-23 — Phase 2b complete:** `PlatformPersistenceAtomicWriter` now
  names the adapter seam that gives a transaction-aware product repository,
  lineage fact, and outbox obligation one atomic boundary. A validated mutation
  requires matching stable-record and causation facts. The in-memory Core
  repository explicitly rejects a transaction handle because it cannot make
  the durable promise.
- **2026-09-23 — Phase 2c complete:** the provider-neutral outbox relay now
  claims one due entry, maps it to the existing Core queue-send envelope using
  only the stable outbox ID, and marks it published only after queue
  acceptance. A failed send remains recoverable after lease expiry; local
  tests prove the reclaim receives a higher attempt and fence.
- **2026-09-23 — Phase 2d complete:** an explicitly configured worker shell
  now validates a stable outbox envelope, claims durable processing before its
  handler runs, completes it before reporting success, releases it before a
  retry, and records terminal failure before dead-lettering. Completed
  successful duplicates skip the handler; a completed terminal failure skips
  the handler but preserves its non-success dead-letter outcome. Local tests
  prove each path.
- **2026-09-24 — Phase 2e complete:** persistence emits a narrow,
  provider-neutral transition-observer port. `platform/observability` supplies
  a profile-governed implementation that writes only allowlisted capability,
  action, execution-context, outcome, and bounded error-class facts. Its
  fixed transition names become distinct log/trace names and metric series;
  correlation is permitted only in log envelopes, never metric labels or trace
  attributes. Relay
  and durable-worker local tests prove the emitted facts contain no outbox ID,
  payload, tenant, fence, or attempt. No profile has yet been selected by a
  real smoke capability or staging composition.
- **2026-09-24 — Phase 3a complete:**
  `platform/adapters/aws/persistence/dynamodb` now validates injected target
  configuration and maps Core/Platform outbox, processing, and lineage records
  into one private DynamoDB table model. Recording-client tests prove the due
  query, conditional lease/fence changes, terminal markers, append-only
  lineage, bounded provider error mapping, and the two-fact DynamoDB
  transaction. The adapter has no environment lookup and no live AWS resource
  was changed.
- **2026-09-24 — Phase 4a complete:** `apps/platform-smoke` now owns a
  harmless create-once work-item acceptance capability. It receives an injected
  `PlatformPersistenceAtomicWriter`, passes its transaction only to the
  app-owned repository port, and stages matching lineage/outbox facts. Its
  local proof verifies the same transaction scope is used and a duplicate
  creates no outbox obligation. The registered `async_acceptance` profile is
  provider-neutral and allowlisted. No AWS resource was changed.
- **2026-09-24 — Phase 3b complete:** the DynamoDB adapter now implements
  `PlatformPersistenceAtomicWriter`. Target composition can stage a
  product-owned DynamoDB transaction item only through the short-lived
  transaction it receives from the writer. The writer requires both at least
  one participant write and one validated platform mutation before it sends
  one `TransactWriteItems` request. Recording-client tests prove the resulting
  three-write transaction and prove an incomplete request sends nothing.
- **2026-09-24 — Phase 4b complete:** Kanbien staging composition now selects
  the DynamoDB atomic writer and supplies the smoke app's narrow work-item
  repository. A compiled-runtime proof invokes the app capability through that
  composition against a recording client and verifies one three-write command:
  work-item state, lineage, and outbox. The target composition owns the
  work-item row and its create-once condition; the app and reusable adapter
  remain provider- and schema-neutral.
- **2026-09-24 — Phase 5a complete:** source-only target infrastructure now
  defines one dedicated, on-demand DynamoDB table and the two adapter-required
  indexes. It uses server-side encryption, point-in-time recovery, deletion
  protection, retain-on-delete policies, and explicit staging configuration.
  It intentionally grants no new workload access and does not configure a
  live capability until a server, relay, or worker composition uses it.
- **2026-09-24 — Phase 4c and Phase 5b complete:** the smoke app now exposes
  its bounded acceptance route only when a product composition injects the
  provider-neutral persistence seam. The Kanbien staging entrypoint selects
  that seam from target configuration; the server route accepts no business
  payload, uses the safe request identifier as its idempotency identity, and
  requires its own create permission. The source target grants its server task
  only `dynamodb:TransactWriteItems` for the one persistence table. Local app,
  product, static-infrastructure, and compiled-image checks prove that wiring;
  no AWS resource, Cognito scope, or task definition was deployed.
- **2026-09-24 — delivery-policy source reconciliation complete:** the
  `platform-short-idempotent-work.v1` target source now consistently defines a
  30-second expected execution budget inside a 120-second SQS visibility
  window, with five total delivery attempts before the retained DLQ. The
  target profile, queue resource, worker task configuration, sealed-runtime
  fixture, and static policy gate agree. This changes no live AWS resource;
  the next governed CloudFormation change set must inspect and apply it before
  live proof relies on these values.
- **2026-09-24 — Phase 3c complete:** the AWS SQS adapter now implements the
  Core object-payload `Queue.send` port as well as receive, acknowledge, and
  release. It serialises the stable Core envelope—including causation and
  idempotency facts—into the SQS body. On delivery it reconstructs identity
  from that body, never from SQS `MessageId` or `ReceiptHandle`. Runtime,
  type, boundary, and sealed-image checks prove the source-only adapter slice.
  No target composes a relay sender yet and no AWS resource changed.
- **2026-09-24 — Phase 4d source composition complete:** the smoke app now
  registers the exact `platform-smoke.work-item.accepted` job type produced by
  its outbox fact. A local vertical test proves accepted outbox fact -> relay
  -> Core queue envelope -> durable worker completion -> duplicate skip. The
  target adds a one-pass relay entrypoint plus opt-in DynamoDB worker-processing
  composition. Each derives a per-process lease owner from its container
  hostname and validates that its durable lease remains shorter than SQS
  visibility. The sealed runtime check proves all three target entrypoints can
  start from compiled output without contacting AWS.
- **2026-09-24 — Phase 5c source deployment definition complete:** the
  target now declares the selected non-secret persistence configuration for the
  worker, a dedicated one-pass relay ECS task definition, separate relay and
  worker identities, non-public network groups, and isolated application and
  collector log destinations. The server retains only its one atomic write;
  the relay can query the due index, read/lease an outbox record, and send to
  the source queue; the worker can receive/settle a message and record only
  its processing state. The target metric catalogue now declares the bounded
  relay and worker persistence-transition series, using only the approved
  low-cardinality labels. Static infrastructure and sealed-runtime checks
  prove source consistency. There is no CloudFormation deployment, ECS relay
  run, worker scale-up, Cognito scope change, queue message, or DynamoDB
  record in AWS.
- **2026-09-24 — Phase 5d source identity-proof control complete:** the
  staging target now declares one separately bounded write-only Cognito machine
  client, the reviewed `platform-shell/smoke.write` mapping, and a lifecycle
  that keeps the client untrusted by the service until a later reviewed target
  configuration deployment. Focused source commands provision only that scope,
  client, and target-owned secret, or execute exactly one no-body work-item
  acceptance request. Both fail closed on arbitrary inputs and emit only safe
  identifiers or safe status/latency facts. Local policy tests exercise fake
  AWS responses and a temporary post-deployment target fixture. No Cognito
  resource, secret, server deployment, or persistence write was changed in
  AWS.
- **2026-09-24 — Foundation deployment complete:** a reviewed additive
  Foundation change set created the DynamoDB persistence table, required
  indexes, relay identity/log/network boundary, and narrowly scoped server,
  worker, relay, and deployment-role permissions. Post-deployment inspection
  verified table protections, no relay ingress, preserved queue configuration,
  and public-server/zero-worker steady state. It did not register a new
  service task definition, run a relay task, scale a worker, change Cognito,
  or write a persistence item.
- **2026-09-24 — Service change set reviewed:** the available, unexecuted
  change set adds only a dormant relay task definition, revises the public
  server and worker task definitions, and updates each existing ECS service to
  point at its corresponding revision. It does not replace either service,
  start a relay, scale the worker, or change Cognito. A task-definition
  replacement is normal ECS revision registration, whereas executing the
  service change set would begin the public-server rollout and remains a
  separately approved action.
- **2026-09-24 — Service deployment complete:** the reviewed service change
  set was executed and the stack reached `UPDATE_COMPLETE`. The public server
  completed its rolling update with the selected immutable image, a healthy
  target, public liveness success, and the existing protected-read smoke
  success. The worker task definition is deployed but remains at zero; the
  relay task definition exists but has not run. This proves deployment safety,
  not write acceptance or durable delivery.
- **2026-09-24 — Write identity provisioned and reconciled:** a staging
  preflight found the single reviewed `smoke.write` scope, isolated confidential
  client, and target-owned secret already provisioned. The target record now
  retains only safe references and confirms that the server does not yet trust
  the client. No secret value or token was read, and no persistence write,
  relay run, or worker scale-up occurred.
- **2026-09-24 — Write-client allowlist deployment complete:** the reviewed
  two-resource server change set replaced only its task-definition revision
  and updated the existing server service without replacement. It completed
  healthy while the worker stayed at zero and both queues stayed empty. The
  isolated client is now trusted only by the exact server allowlist; no token
  or write was requested during deployment.
<!-- deterministic-check: allow reason="This is historical staging evidence, not an executable procedure; the target profile and static verifier own its machine-checkable facts." -->
- **2026-09-24 — Atomic-acceptance proof stopped safely:** the one approved
  no-body acceptance returned `503` in 229 milliseconds and an aggregate-only
  table check proved that no atomic transaction committed. The relay was not
  run and the worker remained at zero. Read-only inspection confirmed the
  active table/indexes, task configuration, and `TransactWriteItems` task-role
  permission; CloudTrail has no DynamoDB data event from which to recover the
  prior provider error. The route had converted the safe failure into an HTTP
  response without preserving its stable error class for its observability
  profile. `PlatformResponse.observability.errorClass` now provides that
  profile-governed, non-transport remediation and is covered by contract and
  server runtime tests. The separately reviewed remediation deployment is
  complete; one fresh approval for a replacement acceptance request remains
  required.
- **2026-09-24 — Safe-failure remediation deployment complete:** the
  scan-clean, attested immutable image containing the private error-class seam
  was deployed through a reviewed five-resource service change set. The server
  is healthy with a protected-read `200`; the worker remains at zero and both
  queues remain empty. This proves the remediation is live, not that the
  earlier failed write or later outbox stages succeeded.
- **2026-09-24 — Replacement acceptance stopped safely:** the one separately
  authorised replacement no-body request returned `503` in 148 milliseconds.
  Aggregate-only postconditions proved no record committed, both queues stayed
  empty, the server remained `1/1`, and the worker remained `0/0`. The
  remediated server revision was healthy, but no matching structured server
  request was observed. This is a bounded pre-server/ingress diagnostic
  candidate, not a conclusion about a provider failure. The live programme
  therefore stops before relay or worker action; a third write would be an
  unapproved new state change.
- **2026-09-25 — Non-mutating admission diagnostic planned:** a read-only
  ingress inspection confirmed the dedicated host rule, host-scoped WAF,
  ALB-only server ingress, and public liveness route. The shared ALB has no
  access logs, so enabling them would collect unrelated legacy-host traffic
  and is deliberately out of scope. Before any fresh state change, the smoke
  app therefore adds one no-body `POST /smoke/work-items/admission` route. It
  requires the existing narrow write permission but returns `204` before the
  repository, atomic writer, DynamoDB, outbox, queue, relay, or worker are
  involved. Its fixed runner can execute only once after a reviewed immutable
  deployment and healthy-server check. A pass proves the authenticated request
  reaches the application boundary; it does not claim a persistence commit.
- **2026-09-25 — Admission diagnostic deployment complete:** the scan-clean,
  attested immutable image was published from `main`, then a reviewed service
  change set made only three normal ECS task-definition revisions and two
  in-place service references. The stack returned to `UPDATE_COMPLETE`, the
  server to healthy `1/1`, the worker to `0/0`, queues to empty, and all five
  alarms to `OK`; public liveness and the protected-read smoke returned `200`.
  The non-mutating admission route is therefore deployed and may execute once.

### Durable-delivery contract boundary

The next implementation slice uses the following ownership split:

- Core owns immutable, versioned `OutboxEntry` routing facts and the safe,
  append-oriented `RecordChange` envelope. Neither contract accepts a raw
  payload, an unbounded metadata object, or before/after record values.
- `platform/persistence` owns the mutable outbox/processing states, attempts,
  leases, fences, and terminal completion records. Those are runtime
  coordination mechanics, not portable product facts.
- A future adapter persists both contract families atomically where required.
  The smoke app supplies the work-item meaning and stable idempotency identity.
- Core owns the generic lifecycle state machine, not a universal lifecycle
  policy. Every real entity still declares its own recovery, retention,
  legal-hold, field-classification, and authorised purge rules.

## What “Robust” Means Here

Persistence v1 is robust when it has clear ownership, explicit failure
semantics, repeatable tests, least-privilege infrastructure, and live evidence
for the selected smoke use case. It does **not** mean that every future Entity
Builder entity has already selected DynamoDB, a schema, a retention period, or
a repository implementation.

The result is a reusable foundation with two deliberately separate outcomes:

| Outcome | Complete when | It does not claim |
| --- | --- | --- |
| Persistence foundation | Database-neutral contracts, platform coordination rules, adapter boundaries, tests, and documentation are implemented. | A generic repository framework or a final database choice for every product entity. |
| Staging smoke proof | One harmless state/outbox/lineage transaction is relayed and processed safely on AWS with reviewed evidence. | Continuous business-event delivery, real tenant data, or a final scheduler design. |

Real product entities will later choose their own schema, queries, migrations,
tenant boundaries, classification, retention, restore rules, and business
transitions. A future relational adapter is an additive, governed path; it
must not quietly replace this narrow smoke reference.

## Two-tranche completion programme — 2026-09-24

The phrase “complete persistence” needs a truthful boundary. This programme
closes the reusable foundation and one live, production-shaped reference path;
it does not invent future entity schemas or make a low-cost smoke target claim
continuous business-event availability.

### Tranche 1 — bounded live transactional-outbox proof

1. **Complete:** deploy and health-check the immutable server image containing
   the fixed, non-mutating write-admission route. Execute its one no-body
   diagnostic only after that check. Stop if it does not return `204`; do not
   infer an ingress cause and do not issue another state-changing request.
2. If and only if that diagnostic succeeds, perform **one** fresh no-body
   acceptance request with a new fixed opaque request identity. The two prior
   requests remain proved non-commits and are never retried under their
   original proof identities.
3. Record only safe status, rounded duration, aggregate transaction outcome,
   and target-health facts. Stop before relay/worker work if acceptance does
   not return its declared success status.
4. Run one governed Fargate relay task, derived solely from the reviewed
   service/foundation outputs. It may publish at most the one due outbox fact,
   emits no envelope or task identifier, and must exit successfully.
5. Use a separate governed persistence-worker proof to scale the already
   deployed worker from zero to one, settle that one relay-created delivery,
   wait through the bounded telemetry flush, and return it to zero in a
   `finally` path. It must not enqueue a second direct-SQS fixture.
6. Verify aggregate-only postconditions: public server still healthy, worker
   desired/running zero, source/DLQ empty, the due index has no remaining
   deliverable work, and the one processing completion is present. Record the
   relay/worker transition metric observation separately from queue settlement.

The runner commands accept no target, task definition, network, queue URL,
payload, client, token, scope, identity, or request-body argument. They fail
closed on account/region/lifecycle/precondition drift and never print or retain
provider responses, task IDs, records, messages, secrets, headers, or bodies.

**Current result — diagnostic deployed, execution pending.** The two earlier
acceptance requests remain safe non-commits. A read-only ingress inspection and
the completed immutable-image rollout now establish that the public host,
WAF, ALB-only ingress, healthy `1/1` server, zero worker, empty queues, and
five alarms are all in their expected states. The next work is exactly one
non-mutating admission request; no fresh persistence write, relay, or worker
action is permitted unless that request returns `204` and its safe evidence is
recorded.

### Tranche 2 — reusable persistent-record foundation

Tranche 2 completes the reusable **contract** required before a future feature
can choose its own repository and data model:

1. Add a database-neutral logical-record lifecycle contract: active/deleted
   state, deletion marker, restoration window, retention-policy reference,
   legal-hold-aware purge eligibility, and closed validation/error semantics.
   It supplies decisions and invariants; it never performs an unreviewed
   physical deletion.
2. Keep the existing `RecordChange` direct-cause lineage as the only generic
   row-change record. Tests must prove delete/restore actions use the same
   bounded lineage vocabulary and no arbitrary before/after values can leak
   into it.
3. Document the feature adoption checklist: a product must select its entity
   schema, tenant boundary, authorised readers, expected-version rules,
   recovery window, retention/erasure/legal-hold policy, migration path, and
   repository query shape before it obtains an adapter transaction.
4. Re-run Core, platform, DynamoDB-adapter, smoke-app, compiled-runtime, and
   static target-policy checks. This makes the platform safe to consume; it
   deliberately does **not** select a universal retention period or physically
   purge customer data.

**Current result — complete locally.** The Core lifecycle contract records a
policy reference in the deleted state, distinguishes active/deleted rows,
calculates the restoration boundary, makes legal hold an explicit input to
purge eligibility, and exposes no physical-delete operation. Its runtime and
type tests cover the lifecycle transitions and demonstrate that deletion and
restoration use the pre-existing bounded `RecordChange` vocabulary.

### Explicit boundary after both tranches

After both tranches succeed, `Persistence Foundation v1` is complete when a reviewer
can see a tested, provider-neutral contract boundary, a selected AWS adapter,
least-privilege staging resources, and one safe end-to-end transaction →
outbox → queue → duplicate-safe worker completion. The next platform layer is
the separately planned scheduler/operational-availability slice. A continuous
relay is not silently enabled here because its cadence, delivery-latency SLO,
availability posture, and recurring Fargate cost are material target decisions
that the present low-cost smoke proof does not define.

At present, the **reusable foundation is complete locally**, but the **live
reference proof remains incomplete** because Tranche 1 has reached its
non-mutating admission gate. No plan text or readiness record may call the
persistence solution fully production-proven until that diagnostic and one
newly authorised acceptance-to-worker path pass.

## The Terms Used In This Plan

| Term | Meaning | Not the same thing as |
| --- | --- | --- |
| Transaction | A boundary in which all required writes succeed together or none do. | A sequence of independent saves that happen to be close together. |
| Concurrency token | A version supplied with an update; the store rejects a stale version instead of losing a newer update. | A worker lease or worker fence. |
| Record lifecycle | Whether a product record is active, logically deleted, restored, or eligible for governed purge. | The physical removal of a row immediately after a delete request. |
| Change lineage | A protected, append-oriented fact saying which safe record revision changed because of which direct event or message. | A full copy of every historical row or an audit log. |
| Outbox record | A durable obligation to publish a later message after a state change commits. | Proof that a destination has received or processed the message. |
| Processing claim | A durable statement that one worker may currently process one stable delivery identity. | A queue acknowledgement. |
| Lease and fence | A time-bounded claim plus a monotonically increasing number that prevents an expired worker from writing after a newer claimant. | Optimistic concurrency for an ordinary interactive entity update. |

## Decisions Already Locked

- The smoke storage provider is DynamoDB on demand in `eu-west-1`; this is a
  cost-aware reference proof, not the future Entity Builder data-store choice.
- The first transport is SQS Standard with a DLQ using
  `platform-short-idempotent-work.v1`.
- Its semantics are at-least-once delivery, no ordering assumption, idempotent
  processing, a 30-second normal execution budget, two-minute visibility,
  five total delivery attempts, exponential backoff with jitter, seven-day
  main-queue retention, fourteen-day DLQ retention, and manual reviewable
  recovery.
- The smoke workload contains only opaque test-safe identifiers, bounded
  status/attempt facts, and safe timestamps.
- The existing platform queue, worker, SQS producer/consumer adapter, observability profiles,
  logs, metrics, traces, alarms, and DLQ policies are reused. This plan must
  not create a second queue or telemetry model.

## Scope And Non-Goals

### In scope

1. Split the existing broad Core persistence file into semantically named
   database-neutral modules with a deliberate public barrel.
2. Add only the reusable persistence contracts justified by the smoke proof:
   transactions, concurrency, paging, persistence errors, outbox records,
   processing claims, safe lineage envelopes, and lifecycle-policy seams.
3. Implement provider-neutral platform coordination for transaction/outbox
   orchestration, relay claims, worker completion claims, and configuration
   validation.
4. Implement the DynamoDB adapter that translates those contracts without
   leaking DynamoDB vocabulary into Core, app code, or generic platform code.
5. Add one harmless `platform-smoke` persistence workflow and its local,
   negative, concurrency, duplicate, and recovery tests.
6. Define the staging CloudFormation, IAM, target-profile, readiness, alarm,
   runbook, and evidence changes required for a controlled live proof.

### Explicitly out of scope

- a final entity database or data model;
- product user, tenant, group, customer, medical, or document data;
- a generic active-record, ORM, or one-size-fits-all repository framework;
- automatic DLQ resolution or queue-wide purge/redrive;
- a general event fan-out bus, FIFO ordering promise, or exactly-once claim;
- a new always-on scheduler module; and
- a claim that the controlled smoke proof is continuous production delivery.

## Ownership And File Structure

The structure follows the repository’s scanability rule: each file owns one
recognisable topic, while `index.ts` is a small deliberate public export list.

| Layer | Planned location | Owns | Must not own |
| --- | --- | --- | --- |
| Core | `packages/core/src/persistence/` | Provider-neutral nouns and ports. | SDK imports, table keys, app schemas, IAM, or deployment values. |
| Platform | `platform/persistence/` | Generic coordination mechanics and policy validation. | DynamoDB calls, SQS calls, entity business rules, or tenant policy. |
| AWS adapter | `platform/adapters/aws/persistence/dynamodb/` | DynamoDB transaction/condition/query/error translation. | Product record meaning, environment selection, or CloudFormation. |
| Smoke app | `apps/platform-smoke/src/persistence/` | The harmless work-item state and its declared workflow. | AWS SDK calls, table configuration, or generic claim mechanics. |
| Target/infra | `infra/04.deploy/03.product/targets/kanbien/staging/` | Resource definitions, IAM, encryption, retention, selected values, and readiness evidence. | App business behaviour or database-neutral contracts. |

### Core decomposition

The existing `packages/core/src/persistence/index.ts` will be split without a
behavioural rewrite first:

```text
packages/core/src/persistence/
  README.md          # purpose, ownership, and import guidance
  concurrency.ts     # ConcurrencyToken and expected-version save options
  errors.ts          # PersistenceError codes and constructors
  pagination.ts      # PageRequest, Page, totals, and validation
  transactions.ts    # Transaction and UnitOfWork contracts
  repository.ts      # small provider-neutral Repository convention
  in-memory.ts       # current deterministic local reference implementation
  outbox.ts          # immutable, versioned durable-delivery facts
  lineage.ts         # bounded record-change facts
  index.ts           # intentional public exports only
```

The implemented `outbox.ts` and `lineage.ts` contain only safe immutable
facts. Processing claims remain Platform coordination, while lifecycle policy
remains an explicit seam until a real product owns its recovery and retention
rules.

### Platform and adapter decomposition

```text
platform/persistence/
  README.md                 # responsibility and composition diagram
  errors.ts                 # provider-neutral coordination failures
  observability.ts          # closed no-payload transition observer port
  types.ts                  # attempts, leases, fences, and state shapes
  outbox.ts                 # relay-facing outbox coordination contract
  relay.ts                  # one-entry Core queue-send composition
  processing.ts             # durable claim/lease/fence mechanics
  lineage.ts                # safe change-lineage validation and envelopes
  transaction.ts            # atomic writer and mutation validation seam
  index.ts                  # deliberate public exports only

platform/adapters/aws/persistence/dynamodb/
  README.md                 # DynamoDB mapping, limitations, and configuration
  configuration.ts          # adapter-specific validation of injected values
  transactions.ts           # TransactWrite translation
  outbox-store.ts           # pending-work query and conditional state changes
  processing-store.ts       # conditional claims/completion markers
  errors.ts                 # DynamoDB-to-platform error mapping
  index.ts                  # adapter composition exports only
```

`platform/persistence` can depend on Core and the existing provider-neutral
queue/worker surfaces. It must never import the DynamoDB SDK. The DynamoDB
adapter is selected only from an approved target composition root.

## Required Behaviour And Invariants

1. A smoke work-item state change, its minimal change-lineage entry, and its
   outbox entry share one explicit transaction. A partial result is failure.
2. An outbox record is first a `pending` delivery obligation. It is not marked
   `published` until the queue provider accepts the send.
3. A relay may crash after SQS accepts a send but before it stores the
   `published` marker. The retry may therefore send a duplicate; this is
   expected and must be harmless.
4. A worker claims the stable outbox identity before its work. It writes the
   terminal work state, completion marker, and safe evidence before it deletes
   the SQS message.
5. A claimant must complete before its lease expires. A stale lease holder
   must also be unable to write after a newer claimant. The conditional claim
   increments a fence value, and terminal writes require both an unexpired
   lease and the current fence.
6. Ordinary entity update concurrency and restartable-worker fencing are
   different controls. A normal update uses an entity revision only when the
   product’s mutable state can conflict; it does not acquire a worker fence.
7. Unknown metadata, raw payloads, raw records, secrets, credentials, request
   bodies, prompts, transcripts, and provider error payloads are rejected from
   the lineage and observability paths.
8. Target-owned non-secret configuration supplies selected limits, resource
   references, retention, and retry values. Generic code does not hard-code
   target values, service names, ARNs, regions, or table names.
9. DynamoDB TTL is only a best-effort expiry mechanism. It does not replace a
   product retention, restore, legal-hold, or privacy-erasure decision.

## Bounded Smoke Data Model

The exact physical key encoding is an adapter implementation detail, but the
following logical records and access patterns must be documented and tested
before infrastructure is created.

| Logical record | Safe contents | Required access path | Prohibited contents |
| --- | --- | --- | --- |
| Smoke work item | opaque work ID, state, revision, created/updated time, bounded attempt facts | get by stable work ID | real entity data, tenant data, names, documents, payloads |
| Change lineage entry | entity kind/reference, revision, action, direct cause, correlation ID, allowlisted field names/outcomes | find revisions by work ID or direct cause | complete before/after row copies or unbounded diffs |
| Outbox entry | stable outbox ID, work reference, delivery policy ID, pending/lease/published state, attempt/fence/times | find due pending outbox entries | business payload, credentials, raw request data |
| Processing record | stable outbox ID, claim/fence/lease, terminal disposition, safe completion facts | claim and read completion by outbox ID | worker secrets or raw provider responses |

The outbox message body should contain only the versioned message kind, stable
outbox ID, correlation ID, direct cause, and other explicitly classified
allowlisted routing facts. The worker retrieves durable state through the
adapter; it does not rely on a rich mutable business payload in SQS.

### State transitions

```text
transaction: work accepted + lineage written + outbox pending
outbox: pending -> leased(fence N) -> published
processing: unclaimed -> claimed(fence N) -> completed(succeeded | terminal-failure)
                                  |
                                  -> retry-eligible -> claimed(fence N + 1)
```

Every arrow must have a conditional precondition. For example, a lease-expiry
retry may claim `pending` work with a new fence, but an old claimant using the
old fence or an expired lease cannot complete it later.

## Product Lifecycle And Lineage Foundation

The smoke item gives the platform a concrete proof, but it must not decide the
future product lifecycle. The reusable contract must support a product later
declaring:

- logical deletion metadata: deletion time, actor/executing system, tenant
  where applicable, and policy-relevant reason;
- normal reads/lists/search/exports that deliberately exclude deleted records;
- a separately authorised restore during a configured recovery window;
- reviewable purge or anonymisation subject to retention, privacy erasure,
  residency, and legal hold; and
- append-oriented change lineage with a direct cause, classified allowlisted
  diffs or protected revisions, tenant isolation, and independent access and
  retention policy.

These are contracts and validation seams in v1. No generic platform code may
invent a product’s recovery window, delete meaning, unique-key semantics,
legal hold, or sensitive-field history policy.

## Delivery Sequence

### Phase 0 — Reconcile and design before code

1. Confirm this plan remains consistent with the persistence rule, runtime
   plan, reference target baseline, SQS delivery policy, observability
   profiles, and current staging target profile.
2. Write a capability-to-owner map and the logical DynamoDB key/query design.
3. Define all states, legal transitions, conditional predicates, bounded
   error taxonomy, safe telemetry fields, and test matrix before provider code.
4. Record the target configuration keys and their single owner. Stop if a
   value would be editable independently in the app, generic platform,
   adapter, infrastructure, and target profile.

Exit criterion: a reviewer can explain the transaction, duplicate, crash,
lease, DLQ, lineage, and deletion paths without referring to an AWS SDK.

### Phase 1 — Stabilise Core persistence contracts

1. Move existing Core persistence declarations into the topical files listed
   above and retain compatibility through `index.ts` exports.
2. Preserve and extend type/runtime tests for concurrency tokens, paging,
   errors, explicit transaction behaviour, and the in-memory reference store.
3. Add the smallest provider-neutral immutable outbox and lineage contracts
   needed by the bounded smoke workflow. Keep mutable claims in Platform and
   leave logical deletion/restoration as an explicit lifecycle-policy seam
   until a real product owns the necessary recovery and retention rules.
   Reject unconstrained maps and raw payload shapes at the contract edge.
4. Add the package README with a file-by-file guide, valid imports, and
   prohibited provider/product imports.

Exit criterion: Core is still usable without a server, AWS credentials, or a
database and contains no DynamoDB/SQS/CloudFormation vocabulary.

### Phase 2 — Add provider-neutral platform coordination

1. Create `platform/persistence` with semantic files and a small barrel.
   **Complete locally.**
2. Implement the deterministic outbox and processing-claim state machines,
   stale-fence protection, and append-oriented lineage storage. **Complete
   locally.** The explicit transaction/outbox contract seam is also complete:
   it requires a transaction-aware repository rather than allowing an
   in-memory false positive. Add relay-policy validation only when it can
   compose with the existing queue and worker abstractions without duplicating
   either one.
3. Compose with the existing queue and worker abstractions rather than
   duplicating their delivery, retry, trace, metric, or shutdown behaviours.
   **Complete locally:** the relay composes only with Core's queue-send port
   and leaves a failed send as a durable, lease-expiry-recoverable obligation.
   An explicitly configured worker shell validates that its queue-message ID,
   idempotency key, and payload agree on one `outboxEntryId`; it claims that
   identity before the handler, records success before its existing successful
   outcome is acknowledged, releases it before the existing retry path, and
   records terminal failure before the existing dead-letter path. A redelivery
   of that terminal record does not repeat business work, but remains a
   non-success outcome so the provider's own DLQ/redrive policy still applies.
   Concrete transport selection and acknowledgement remain outside generic
   platform code.
4. Define the operational profile for each transition: safe structured log
   facts, metric name/labels, trace spans, audit profile where warranted, and
   explicitly excluded data. **Complete locally:** persistence exposes only a
   no-payload transition-observer port; `platform/observability` supplies the
   profile-governed implementation. A future smoke capability must register
   and select its profile, and target composition must add the corresponding
   reviewed metric series before these local signals become live evidence.

Exit criterion: the mechanics can run against a deterministic fake store and
fake queue, and provider selection remains outside generic platform code.

### Transition-observability policy

The persistence package may emit only these closed operational facts:

| Transition family | Examples | Permitted evidence |
| --- | --- | --- |
| Outbox relay | due-work lookup failure, claim, active lease, queue-send failure, publication marker, published | Fixed event name; profile-allowlisted capability/action/execution context/outcome/error class; optional correlation only in logs. |
| Durable worker processing | envelope rejection, claim, active lease, duplicate success/terminal failure, completion, retry release, terminal settlement | The same bounded fields; no queue receipt, outbox ID, payload, tenant, fence, attempt, record subject, or provider object. |

Each transition produces a distinct fixed log/trace name and metric series,
such as `platform.persistence.outbox.claimed` and
`platform.persistence.outbox.claimed.outcome`. It does **not** add a free-form
`transition` metric label. This makes metric catalogues reviewable and prevents
the transition vocabulary from becoming an unbounded dimension.

Transition counters are diagnostic evidence, not an SLO by themselves. The
future smoke profile may separately declare truthful end-to-end or job timing
objectives once the selected adapter provides real start/finish evidence.

### Phase 3 — Build the DynamoDB adapter

1. Add `platform/adapters/aws/persistence/dynamodb` with explicit injected
   configuration and no environment-variable lookup scattered through its
   modules.
2. Translate Core transactions into DynamoDB transactional writes, expected
   versions into conditional expressions, and known provider failures into
   bounded platform errors.
3. Implement a due-pending outbox query, conditional lease/fence claim,
   published marker, processing claim, and completion marker.
4. Document key shape, index requirements, consistency assumptions, DynamoDB
   transaction limits, TTL limitations, and error mapping in the adapter
   README.
5. Use test doubles/recording clients for deterministic adapter contract
   tests; no live AWS account is required for this phase.

**Phase 3 implementation note (2026-09-24):** the completed adapter supplies
the reusable records/stores and one DynamoDB `TransactWriteItems` operation for
the two platform-owned immutable facts. It does not pretend to implement the
future smoke entity repository, because no generic platform layer can know a
product record's schema, expected-version field, or lifecycle rules. Phase 4
must supply that narrow smoke-specific transaction participant; only then can
the plan claim one transaction for state + lineage + outbox.

**Phase 3b implementation note (2026-09-24):** the adapter now supplies the
generic physical transaction coordinator without learning any product schema.
Its provider-local staging function accepts exactly one DynamoDB transaction
operation from target composition and refuses an operation outside its active
scope. It also refuses to send if a participant write or a validated platform
mutation is missing. Phase 4b supplies the narrow smoke repository that turns
the app's `accepted` work-item state into that participant write.

Exit criterion: a contract test can prove the adapter emits the intended
transaction and conditional operations, and no DynamoDB type escapes its
public platform contract.

### Phase 4 — Add the harmless smoke workflow

1. Add one explicit smoke capability that creates a test-safe work item with a
   stable idempotency identity.
2. Use the platform seam to atomically persist work, lineage, and outbox.
3. Add a relay entrypoint that processes only due smoke outbox entries, and a
   worker handler that retrieves the durable record and writes its terminal
   result before acknowledgement.
   The concrete queue translation must preserve the original `outboxEntryId`
   and causation across send and receive; a provider-assigned delivery ID or
   receipt handle must never become the durable processing identity.
4. Add a controlled duplicate-delivery test and an authorised inspection path
   that returns safe statuses/identifiers only.

**Phase 4a implementation note (2026-09-24):** the app-owned semantic
capability and transaction request are complete. It has a create-once
repository port, a registered allowlisted observability profile, and local
tests that prove a repository receives the atomic writer's exact transaction
scope and a rejected duplicate stages no durable outbox fact. This is not yet
a live DynamoDB proof: Phase 4b supplies the transaction-aware smoke
repository and target composition, while Phase 5 must select and provision the
real target resources.

**Phase 4b implementation note (2026-09-24):**
`infra/04.deploy/03.product/entrypoints/kanbien-platform-persistence.ts`
composes the selected DynamoDB adapter with the app-owned repository port. It
defines only the harmless `SMOKE-WORK-ITEM` row, a stable ID, `accepted`
state, revision, timestamp, and a create-once condition. The generic adapter
still owns the transaction mechanics; app code still owns the meaning; neither
layer receives a target table name from application code. The compiled image
payload check calls the acceptance capability through this composer using a
recording client and proves that the one command contains the product row,
lineage fact, and outbox obligation.

This is deliberately a source proof, not a duplicate-result claim. DynamoDB
may cancel a transaction for several reasons, so the generic adapter currently
maps that provider failure to a bounded store-operation error. Phase 6 must add
a focused cancellation/conditional-conflict test before product code relies on
a more precise create-once outcome from a real table.

**Phase 4d implementation note (2026-09-24):** the app now registers the
same `platform-smoke.work-item.accepted` message type that its immutable outbox
fact declares. The local app proof uses that staged outbox fact to relay a
minimal Core envelope, runs the registered handler through durable processing,
then repeats the exact envelope. The second delivery returns
`durable-skipped`, does not run the handler again, and finds one completed
processing record. This is a full local delivery-path proof, but the in-memory
outbox and processing stores are test doubles; it is not a live DynamoDB/SQS
proof.

The target source also includes one bounded relay entrypoint and an optional
worker processing seam. Neither creates a continuous process by itself. The
relay completes at most one due record per invocation; a later target decision
must choose and prove a scheduler or continuously running service. The worker
only selects durable processing when the target supplies its DynamoDB
configuration and a lease shorter than SQS visibility. Source-defined task
definitions, selected configuration, task roles, and non-public network/log
destinations now exist for both components, but no AWS resource has been
changed for either component.

Exit criterion: the smoke app declares business meaning only; it does not know
table keys, conditional expressions, SQS SDK calls, or IAM values.

### Phase 5 — Define target resources and deployment configuration

This phase is source-only until a separate AWS plan and approval are complete.

1. Add a focused CloudFormation composition fragment beneath the existing
   `cloudformation/foundation/` structure for the persistence/outbox store and
   compose it through the existing Foundation template.
2. Provision only the selected smoke DynamoDB table, required indexes, server,
   relay, and worker access roles, server-side encryption, point-in-time
   recovery, deletion protection/retention posture, and
   least-privilege log/metric permissions justified by the design.
3. Reuse `foundation/work-queues.yml` for main queue/DLQ resources; add only
   the narrowly needed relay/worker grants and alarms.
4. Put non-secret selected values and resource references in the staging
   target profile; deployment code resolves those values into CloudFormation
   and task definitions. Secrets are never put in a target profile.
5. Extend readiness verification so no persistence capability is marked ready
   merely because the table exists.

The precise recovery, backup, TTL, and capacity values require a reviewed AWS
plan and cost check. The plan must document their recovery objective and must
not present DynamoDB TTL as a guaranteed purge deadline.

Exit criterion: static infrastructure checks, template validation, IAM scope
review, and a no-surprise change-set review all pass before live mutation.

**Phase 5a implementation note (2026-09-24):** the target now has a
source-defined `PlatformPersistenceTable` with exactly the physical access
paths the selected adapter needs: primary `PK`/`SK`, `OutboxDueIndex` over
`DueKey`/`DueSort`, and `LineageCauseIndex` over `CauseKey`/`CauseSort`. It is
on-demand and standard-class for low starting cost, encrypted at rest, protected
against accidental deletion, retained by CloudFormation, and covered by
point-in-time recovery. It deliberately has no TTL setting: DynamoDB TTL is
best-effort technical expiry and cannot implement a restore, legal-hold, or
retention policy.

The matching target-profile entry is configuration only. No ECS task receives
the table name yet and no new DynamoDB IAM action is granted, because neither
the server acceptance route, relay process, nor durable worker lookup is
composed yet. Granting those permissions early would create unused access and
would make a source resource look like a live capability. The next phase must
add each role only with the smallest action set justified by its actual
component.

**Phase 5b implementation note (2026-09-24):** the source now composes the
first real component: an authenticated, no-business-payload smoke acceptance
route. The app derives its stable work-item ID and direct cause from the
request ID, so a caller may safely retry the same request identity without
inventing a second work item. Its `platform-smoke.persistence.work-item:create`
permission is separate from read access. Product composition receives only the
app-facing atomic-writer/repository seam; the staging entrypoint alone selects
the DynamoDB client and validated table/index configuration.

The staging server role receives exactly `dynamodb:TransactWriteItems` against
the selected table—no scan, query, get, update, delete, queue, or administrative
permission. The target profile declares the required `platform-shell/smoke.write`
scope mapping but explicitly records that Cognito has not been changed. The
route, IAM statement, and configuration therefore remain source-composed and
not deployed until a reviewed AWS change set and separately scoped write-token
setup are approved.

**Phase 5c implementation note (2026-09-24):** source deployment definition
now selects the concrete relay and durable-worker configuration shape. The
worker service receives only table/index references and a 90-second durable
lease inside the existing 120-second queue visibility window. The new relay
task definition has no ECS service, inbound port, health check, or schedule;
an approved future `ecs run-task` command is the first intended invocation.
Its task role may query only `OutboxDueIndex`, get/update only outbox records,
and send only to the source queue. The worker has no due-query or send
authority, while the public server keeps no relay, processing, or SQS
authority. The target metric catalogue declares bounded transition evidence
for the relay and worker, but makes no claim that AWS has received it.

The next reviewed change set must apply these source definitions, inspect the
resulting resource and IAM diff, configure the reviewed Cognito write scope,
and then prove the bounded live sequence. It must not turn the relay into an
unreviewed continuously running process.

### Phase 6 — Local and integration proof

The following cases require deterministic tests before deployment:

| Case | Expected result |
| --- | --- |
| State write fails | No lineage or outbox record is visible. |
| Outbox write fails | No new work state is visible. |
| Stale entity version | Conflict is returned; newer state remains intact. |
| Relay crashes after queue acceptance | Lease expiry permits retry; duplicate delivery is safe. |
| Duplicate SQS delivery | One durable completion; no duplicated terminal side effect. |
| Stale worker completion | Older fence is rejected after a newer claim. |
| Worker crashes before acknowledgement | Queue redelivery reaches durable state safely. |
| Retry budget is exhausted | Item reaches DLQ/quarantine with a linked safe evidence record. |
| Controlled recovery | Operator can correlate original outbox/work/claim and record close, escalation, or controlled retry. |
| Unsafe field supplied | Contract rejects it before normal telemetry or lineage persistence. |

### Phase 7 — Controlled staging proof

Once the AWS plan is separately approved:

1. Apply the reviewed Foundation/service change set and inspect the actual
   deployed resource, encryption, index, IAM, queue, DLQ, alarm, and task
   configuration.
2. Submit one controlled harmless smoke work item.
3. Read back only allowlisted operational facts proving the atomic write.
4. Run the bounded relay and worker path, then prove one terminal durable
   result, expected metrics/traces, and safe logs.
5. Deliberately exercise duplicate delivery, a recoverable relay interruption,
   and a controlled terminal failure/DLQ path. Record evidence without raw
   payloads.
6. Return workers/relay to their declared dormant or steady-state target and
   inspect queues/tasks/cost controls afterward.

The initial proof may use an explicitly approved one-shot relay task. It is
not evidence of a continuous scheduler. Continuous outbox delivery requires a
later, explicit choice between an always-running relay service and a governed
scheduler/event-trigger design, including its availability and cost evidence.

### Phase 8 — Evidence, handover, and readiness

1. Add source and live evidence to the target profile/readiness record using
   safe identifiers, timestamps, commit/image references, and result
   summaries—never message bodies or credentials.
2. Add a compact runbook: normal flow, alarm meaning, inspection commands,
   DLQ quarantine/recovery sequence, rollback boundary, and who may perform a
   controlled retry.
3. Add package/adapter READMEs, the teaching-handbook update, and a commit-log
   summary that distinguishes local proof from target proof.
4. Update the production-reference capability matrix only to the proven
   level. Do not promote entity persistence or continuous scheduling based on
   a harmless one-shot smoke flow.

## Configuration Authority

| Decision | Single owner | Consumers |
| --- | --- | --- |
| Delivery policy semantics | Provider-neutral Core/platform contract | app declaration, relay, worker, tests |
| DynamoDB/SQS mapping and validation | AWS adapter | target composition |
| Table/index names, queue references, retention, backup, encryption and IAM selection | staging target profile plus CloudFormation source | deployment renderer and task composition |
| Smoke work-item state meaning and stable idempotency identity | `apps/platform-smoke` | platform persistence seam |
| Product entity schema, retention, restore, holds, and field-diff classification | future owning app/product | Core/platform contracts and selected adapter |

## Security, Residency, and Operations

- The first proof is constrained to `eu-west-1` and must not introduce a
  cross-boundary replica, archive, provider, or operator workflow.
- DynamoDB encryption at rest, TLS in transit, scoped task roles, no public
  table access, and no credentials in source/logs are mandatory target checks.
- Table/resource access follows role purpose: server writes an accepted work
  item; relay reads/leases/publishes its outbox state; worker claims/completes
  only its declared records; no broad administration role is used at runtime.
- Store, queue, trace, metric, log, audit, and change-lineage records have
  different purposes. Safe references may correlate them; copying a raw record
  into all of them is prohibited.
- DLQ access is restricted operational access. A message is diagnosed against
  durable records first; it is not automatically purged or blindly replayed.
- Alarms cover table errors/throttling, relay/worker failure, queue age/depth,
  DLQ depth, and missing expected evidence where a declared operational profile
  requires it. Alarm thresholds and response owners are target policy, not
  adapter constants.

## Definition Of Done

This plan is complete only when all of the following are true:

- Core persistence is split into documented, tested semantic modules with a
  deliberate barrel and no provider leakage.
- The reusable contract and platform mechanics cover explicit transactions,
  concurrency, safe outbox state, claims/leases/fences, bounded lineage, and
  lifecycle-policy seams without pretending to own product policy.
- The DynamoDB adapter is tested for transaction construction, condition
  handling, error mapping, configuration validation, and boundary isolation.
- The smoke app proves atomic state/lineage/outbox write, relay recovery,
  duplicate-safe worker completion, stale-fence rejection, retry/DLQ handling,
  and safe observability in local tests.
- The staging target has a reviewed, least-privilege, encrypted, observable,
  cost-aware deployment configuration with source validation and a reviewed
  change set.
- A controlled live proof produces durable, safe evidence for the declared
  smoke flow and records remaining limitations honestly.
- The production reference baseline distinguishes this proof from unbuilt real
  entity persistence, real tenant data, product retention/migration/restore,
  and continuous scheduler/relay operation.

## Deferred Decisions And Promotion Gates

The following are deliberately not guessed in persistence v1. Each needs a
real product requirement and a governed change before it may be represented as
an available platform default:

1. The primary persistence provider for real Entity Builder entities.
2. Product schema migrations, relational constraints, reporting/search
   patterns, data migration, and restore procedures.
3. Per-entity tenant keys, data classifications, retention windows, legal
   hold, purge/anonymisation, and authorised restore policy.
4. High-availability, multi-region recovery, throughput, and recovery
   objectives beyond the low-cost smoke reference.
5. Continuous outbox dispatch topology and the reusable scheduler module.
6. Automated, agent-assisted DLQ investigation or remediation.

## Related Artifacts

- `docs/03.product/rules/platform/concerns/persistence-files-storage.yml`
  owns the cross-cutting persistence/files/storage rule.
- `packages/core/src/queues/` and `platform/workers/` own the existing
  provider-neutral asynchronous vocabulary and worker lifecycle.
- `platform/adapters/aws/queue/sqs/` owns the SQS translation boundary.
- `infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/work-queues.yml`
  owns the existing target queue/DLQ resource fragment.
- `.agentic/aws/workflows/plan-aws-change.md` and
  `.agentic/aws/workflows/execute-approved-aws-change.md` govern later cloud
  planning and mutation.
