<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.plan.postgresql-relational-persistence-reference-v1
version: 6
status: draft
layer: 03.product
domain: persistence
disciplines:
- architecture
- security
- sre
- requirements
kind: implementation-plan
purpose: Define an additive, low-cost AWS PostgreSQL relational reference for the platform without changing the completed DynamoDB/SQS smoke reference or selecting a database for every future entity.
portability:
  class: source-only
  targets: []
used_by:
- id: product.plan.persistence-foundation-v1
  path: .agentic/03.product/plans/implementation/persistence-foundation-v1.md
- id: product.plan.production-reference-target-baseline
  path: .agentic/03.product/plans/implementation/production-reference-target-baseline.md
- id: harness.architecture.plan.platform-runtime-implementation
  path: .agentic/03.product/plans/implementation/platform-runtime-implementation.md
-->
# PostgreSQL Relational Persistence Reference v1

## Status and purpose

This is a draft plan, not an instruction to create an RDS instance. It
turns the next persistence question into a reviewable programme:

> Can `kanbien/staging` provide one secure, low-cost, relational PostgreSQL
> reference that a future product can choose deliberately, without changing
> the completed DynamoDB/SQS smoke proof or pretending that every future entity
> belongs in PostgreSQL?

The answer will be useful even if a future capability later chooses a different
store. It establishes the boundary between reusable persistence mechanics,
provider translation, target infrastructure, and product-owned data meaning.

## What this plan does and does not decide

| This plan does | This plan does not do |
| --- | --- |
| Defines a proposed AWS PostgreSQL reference, its adapter boundary, migration/recovery approach, security posture, operational proof, and decision gates. | Choose PostgreSQL for every future entity, search index, event stream, object, cache, or analytics workload. |
| Proves a harmless relational smoke slice with opaque test identifiers only. | Create customer, user, tenant, medical, document, or Entity Builder records. |
| Preserves atomic state, change-lineage, outbox, idempotency, lease, and fence semantics where the relational provider implements them. | Move provider SDKs, SQL drivers, connection strings, schemas, or migration files into `packages/core` or generic `platform/persistence`. |
| Specifies how a future product can use product-owned schemas and repositories safely. | Supply a generic CRUD/repository framework or a schema generator. |
| Makes backup/restore and tenant-isolation evidence explicit before product data. | Reuse the legacy-site RDS instance, its credentials, or its availability as evidence for this target. |

The completed [Persistence Foundation v1](persistence-foundation-v1.md) remains
the source of truth for the provider-neutral concepts and the bounded
DynamoDB/SQS proof. This plan is an additive sibling, not a rewrite.

## The simple model

A future capability needs four different things. Treating them as one thing is
what makes persistence hard to reason about:

```text
Product capability                     Platform / provider boundary              Target
------------------                     ---------------------------              ------
invoice schema, queries,      -->     transaction + PostgreSQL adapter   -->   RDS, network,
business transitions,                 migration execution boundary,            credentials, backups,
field classifications                 safe telemetry                            alarms, cost controls
```

- **Product** decides what an `Invoice` means, which fields exist, who may
  access it, and what a valid state change is.
- **Platform** supplies reusable mechanics: a transaction boundary, safe error
  mapping, safe telemetry, and approved seams for outbox, lineage, and
  concurrency.
- **The PostgreSQL adapter** translates those mechanics to a concrete driver
  and PostgreSQL behaviour.
- **The target** provisions and configures the database safely. It is where
  region, network, encryption, credentials, backups, cost, and alarms belong.

An application repository sits at the product edge. It converts an
application's meaningful query or state change into calls through this
boundary. It is not a hidden second database and it is not a reason for
platform code to learn an application's table names.

## Proposed initial direction, subject to approval gates

The following is the recommended low-cost starting position. Each item must be
confirmed from current AWS availability, cost, and target evidence immediately
before implementation; none is silently applied because it appears here.

| Concern | Proposed initial direction | Reason | Promotion / reconsideration trigger |
| --- | --- | --- | --- |
| Managed engine | Amazon RDS for PostgreSQL in `eu-west-1`, not Aurora initially. | A conventional relational engine with lower initial operational and standing-cost complexity. | Higher availability, read scale, or connection pressure may justify Multi-AZ, RDS Proxy, or Aurora later. |
| Availability | Single-AZ, cost-capped reference with explicit backups and restore exercise. | The current target is a low-volume integration proof, not a high-availability product service. | A stated RPO/RTO, paying tenants, or an availability SLO requires a separate HA decision. |
| Network | No public database endpoint; database subnet group and security group allow only the selected workload security groups. | The public ALB is an HTTP entry point, not a database network. | None; public database access requires an exceptional, separately approved design. |
| Encryption | RDS storage encryption and TLS-required application connections. | Protects stored data and traffic between workload and database. | Customer-managed key, rotation, or cross-account needs are separate key-management decisions. |
| Credentials | One least-privilege migration identity and a distinct runtime identity, delivered by the target secret mechanism. | DDL authority and runtime data authority have different risk. | IAM database authentication or a managed rotation workflow may replace password credentials only after proof. |
| Data scope | An isolated `platformsmoke` database and `platform_smoke` schema using opaque synthetic identifiers. | Keeps the proof harmless and makes cleanup/retention reviewable. The database name is RDS-compatible; the reviewed migration creates the underscored schema later. | A product obtains its own governed schema, data classification, and retention decision. |
| Queue relationship | Reuse the provider-neutral outbox/worker contracts; choose a distinct, clearly named relational-smoke delivery path if isolation cannot be proved on the existing queue. | The database choice must not change queue semantics or contaminate the completed proof. | A real product selects its own delivery policy and queue topology. |
| Query access | Parameterised values only; controlled, static SQL identifiers; bounded timeouts and connection pool. | Prevents SQL injection and protects a small database from connection exhaustion. | A product may choose an ORM/query builder behind the same boundaries after review. |

## Stage 1 target decision — 2026-09-26

Stage 1's read-only inspection passed. It did not create, update, read, or
reuse a database credential, endpoint, record, or legacy resource. The target
selection is recorded in the [staging deployment plan](../../../../docs/aws/kanbien-staging-postgresql-relational-reference-v1-deployment-plan.md)
and its [threat-model decision](../../../../docs/aws/kanbien-staging-postgresql-relational-reference-v1-threat-model.md).

The selected v1 reference is:

- a new `db.t4g.micro` Amazon RDS for PostgreSQL `17.11` instance in
  `eu-west-1`, with `20 GiB` GP3 storage and an explicit `30 GiB` autoscaling
  ceiling;
- its own database subnet group over the existing two private subnets, its own
  security group, parameter group, generated credentials, tags, and alarms;
- private-only, encrypted, single-AZ, seven-day automated backup retention,
  deletion protection, and TLS enforced with the `postgres17` parameter family
  and `rds.force_ssl=1`; and
- explicit application-predicate tenant isolation for the initial reference.
  PostgreSQL row-level security is deliberately deferred until a future design
  proves an unforgeable per-transaction tenant context and non-bypass runtime
  role.

The current public-subnet ECS placement does not make the database public.
The new database endpoint remains private. The later change set must add only
TCP `5432` egress from the existing server, worker, and one-pass relay security
groups to the new database security group, and only matching inbound rules on
that new group. It must not broaden CIDR egress, alter ALB ingress, move the
workloads, or touch the legacy database security group.

At the inspected public on-demand rates, the selected instance is
`$0.017/hour` and GP3 storage is `$0.127/GiB-month`: approximately `$14.95`
per 730-hour month at `20 GiB`, or `$16.22` at the `30 GiB` ceiling, before
variable transfer, exceptional retained snapshots, or tax. The existing
service-tag-scoped `$25/month` budget therefore remains the tighter alerting
guardrail and the selected recurring capacity remains below the user's
`€50/month` ceiling. No manual snapshot retention, Multi-AZ, RDS Proxy,
Aurora, enhanced monitoring, Performance Insights, or database-engine log
export is in scope for v1. Engine-log export is deliberately absent because
PostgreSQL engine logs can include query text; safe application telemetry,
RDS metrics, and RDS event notifications provide the v1 operational signals.

## Non-negotiable design rules

1. **No provider leakage.** `packages/core` and `platform/persistence` remain
   database-neutral. No `pg`, RDS, SQL, or connection-string import belongs
   there.
2. **No generic data model.** Apps/products own their tables, migrations,
   repositories, query shape, field classification, and lifecycle policy.
3. **No dynamic SQL from request input.** Parameters carry values; table,
   column, ordering, and migration identifiers come only from reviewed static
   source or a constrained generated manifest.
4. **One state transition, one transaction.** Where a product transition needs
   a lineage fact and outbox obligation, all required relational writes commit
   together or none commits.
5. **Tenant isolation is deliberate.** A tenant-scoped table has an explicit
   `tenant_id`, tenant-first access predicates and indexes, and an isolation
   test. Database row-level security is evaluated as a defence-in-depth option;
   it cannot replace application authorisation or be enabled without a trusted
   database-principal/context design.
6. **Migration authority is separate.** Runtime code cannot apply arbitrary
   DDL on startup. Ordered, append-only, forward-compatible migrations run
   through a deliberate release/migration execution path.
7. **A backup is not recovery evidence.** The reference is not complete until a
   safe restore rehearsal proves an expected schema and harmless record can be
   recovered without overwriting the live database.
8. **Telemetry is not a data exfiltration route.** Logs, metrics, traces,
   alerts, and evidence contain operation name/category, duration, outcome,
   bounded counts, and safe error class only—never SQL text, values, rows,
   credentials, connection strings, or raw provider responses.

## Proposed source layout

The layout follows the repository's scanability rule: topic files own one
responsibility; the package `index.ts` is a deliberate public barrel.

```text
platform/adapters/aws/persistence/postgresql/
├── README.md                    # Provider boundary, configuration, safety, tests
├── package.json                 # Adapter package identity and export boundary
├── src/
│   ├── config.ts                # Validates selected non-secret configuration
│   ├── connection.ts            # Builds bounded, TLS-required database access
│   ├── errors.ts                # Maps driver failures to stable persistence errors
│   ├── transactions.ts          # Implements the approved transaction boundary
│   ├── outbox.ts                # Implements relational outbox persistence semantics
│   ├── processing.ts            # Implements durable claim/lease/fence semantics
│   ├── lineage.ts               # Implements bounded record-change persistence
│   ├── migrations.ts            # Executes an approved migration manifest only
│   ├── records.ts               # Keeps row conversion and statement construction private
│   ├── telemetry.ts             # Emits safe provider-neutral observations
│   └── index.ts                 # Deliberate public exports only
└── tests/                       # Adapter, integration, boundary, and safety tests

infra/04.deploy/03.product/targets/kanbien/staging/
├── cloudformation/foundation/relational-persistence.yml
├── cloudformation/foundation/relational-persistence-access.yml
└── cloudformation/service/relational-persistence-workloads.yml
```

The exact split may change after an infrastructure inspection, but the
responsibility split must remain: resource/network/encryption/backup resources,
access roles, and workload configuration must not become one unscannable
template.

## Stage 2 adapter evidence — 2026-09-26

Stage 2 passed without creating or modifying an AWS resource. The new
`@kanbien/platform-adapter-aws-persistence-postgresql` package contains only
provider translation and is isolated beneath
`platform/adapters/aws/persistence/postgresql/`.

The deterministic package checks prove that it:

- rejects unsafe non-secret configuration without echoing a secret reference;
- requires certificate-verified TLS, bounded pool/connection/idle/statement
  timeouts, and a reviewed schema identifier before connection;
- keeps values parameterised and rejects unsafe relation identifiers;
- maps PostgreSQL outcomes to fixed error categories without returning raw
  provider detail;
- rolls back a failed transaction, commits a successful one, and emits only
  bounded telemetry fields;
- requires a product DML participant plus a validated lineage/outbox mutation
  before one atomic PostgreSQL commit; and
- keeps `pg`, SQL, RDS, credential handling, and row encoding out of Core and
  generic `platform/persistence`.

The local tests use a recording pool, not a database. Therefore they prove
adapter semantics and source boundaries only. A disposable live PostgreSQL
instance is still required for Stage 3 before this can count as relational
behaviour evidence.

## Stage 3 local-fixture evidence — 2026-09-26

Stage 3 passed. It uses a narrowly bounded `platform_smoke` PostgreSQL
composition and an opt-in local command:

```text
npm run platform:adapter:aws:persistence:postgresql:integration
```

The command compiles the integration suite, starts one generated-name Docker
container on loopback with temporary storage, passes its generated password
through a mode-`0600` temporary environment file rather than command-line
arguments, runs the proof, and removes both exact temporary resources in all
outcomes. It never reads AWS credentials, contacts an AWS resource, uses a
developer database, prints a secret, or changes the completed DynamoDB/SQS
reference.

The test proves the Stage 3 behaviours against a real engine when it can run:

- ordered migration application and changed-checksum fail-closed behaviour;
- the smoke app's state + lineage + outbox atomic transition and rollback;
- an optimistic update rejected by a stale revision;
- tenant-A predicate reads, updates, deletes, and counts returning the same
  zero-result shape for opaque tenant-B requests;
- outbox and worker lease reclaims increasing a fence and rejecting stale
  publish/completion attempts; and
- one provider-neutral outbox relay accepting a minimal queue envelope before
  its published marker, with no data-bearing telemetry fields.

The integration compilation, normal adapter checks, fixture availability guard,
and disposable real-engine invocation passed. The fixture created only its
generated loopback Docker database and removed its exact temporary resources at
the end of the test. No AWS resource, shared database, real record, or
long-lived credential was used. Stage 4 may now define and validate the AWS
target source; it still may not create an RDS resource until its reviewed
change-set gate passes.

## Stage 4 source-definition checkpoint — 2026-09-26

Stage 4 source now has four focused Foundation fragments:

- `relational-persistence.yml` owns the private subnet group, no-egress
  database security group, `postgres17` TLS parameter group, encrypted RDS
  instance, and generated target-owned credential references;
- `relational-access.yml` owns the exact three TCP-5432 workload paths and the
  separate bootstrap, migration, and runtime task roles;
- `relational-workload-configuration.yml` owns one non-secret configuration
  reference. Endpoint metadata remains attached to target-owned secrets, so it
  is not published in source or normal deployment evidence; and
- `relational-operations.yml` owns RDS CPU, storage, and connection alarms and
  scoped RDS events through the existing alarm destination.

The existing server, worker, and relay task roles receive neither the runtime
credential nor the relational configuration in this stage. Their network paths
are deliberately ready for the later bounded proof, but they cannot become a
database client merely because the target is deployed. A recovery verifier has
no standing role in v1: the restore rehearsal creates and removes its own
isolated recovery boundary under a separate controlled procedure, avoiding a
permanent high-privilege recovery identity.

`scripts/04.deploy/verify-platform-shell-postgresql-reference/script.sh`
statically verifies the resource shape, no-public/no-CIDR network boundary,
TLS/encryption/backups/deletion policy, generated-secret policy, IAM scope,
non-secret configuration, and alarm boundary. It is included in the wider
platform infrastructure check. These checks passed locally. No AWS resource,
secret, change set, or live database has been created by this checkpoint.

<!-- deterministic-check: allow reason="the reviewed live AWS change-set contents cannot be decided by a local source check; the static verifier narrows its expected boundary first" -->
The rendered Foundation is larger than CloudFormation's 51,200-byte inline
limit. The remaining Stage 4 route is therefore deliberately two-step: first
review and apply the isolated target-owned deployment-artifact store (one
private encrypted S3 bucket and its TLS-only deny policy), then upload the
deterministic non-secret rendered template beneath its bounded
`change-sets/` prefix. Only then may the `kanbien-dev` profile create one named
Foundation-stack change set using the new private-subnet input. The Foundation
change set must contain only the reviewed additive relational resources and
must not be executed in Stage 4.

## Contracts and ownership

| Concern | Owner | Required boundary |
| --- | --- | --- |
| Transaction, optimistic concurrency, pages, lifecycle, lineage, outbox, idempotency vocabulary | `packages/core` | Existing provider-neutral contracts; extend only for a demonstrated reusable gap. |
| Transaction/outbox orchestration and approved persistence seams | `platform/persistence` | No provider SDK or SQL import. |
| Connection, PostgreSQL commands, error mapping, migration execution, provider telemetry | `platform/adapters/aws/persistence/postgresql` | Adapter contracts and integration tests. |
| Product schema, repository, query, migration content, field sensitivity, retention, business state transition | Future app/product capability | Product tests, authorisation checks, and migration review. |
| RDS, VPC/subnets/security groups, secret reference, IAM, backups, alarms, budgets, deployment configuration | `infra/04.deploy` target | Reviewed change set, least-privilege inspection, live evidence. |

### Migration contract

The first relational migration capability must have these properties:

- Migration files are ordered, immutable after application, and carry a stable
  identifier plus a checksum/manifest entry.
- A deployment runs **expand → migrate/backfill → contract** across compatible
  releases; it does not drop or rename a live column in the same release that
  changes callers.
- The migration runner records only safe migration identifier, checksum,
  applied timestamp, tool version, and outcome. It stores no SQL text or data
  values in ordinary observability records.
- The runtime role has no schema-alter permission. The migration identity has
  only the schema/database authority it requires.
- A failed migration stops promotion and preserves diagnostic evidence without
  attempting an improvised destructive rollback. Recovery uses a reviewed
  forward repair or a separately governed restore plan.

### Tenant and row access contract

The initial harmless reference may use two opaque synthetic tenant identifiers
solely to prove isolation. Before real tenant data, every tenant-scoped
repository operation must receive a verified tenant scope from the existing
authorisation boundary, include it in reads/writes, and prove that a request
for tenant A cannot read, update, delete, or infer tenant B's rows.

Row-level security (RLS) is a candidate second control, not a checkbox. It is
safe only when the runtime connection has a non-bypass role and an unforgeable
per-transaction tenant context. The first implementation must either prove
that design end-to-end or keep RLS explicitly deferred while the application
predicate/isolation tests provide the selected enforcement. It must never claim
RLS merely because a table has a `tenant_id` column.

## Required observability and operations

The PostgreSQL adapter must use the existing observability profile system, not
invent a second log vocabulary. Its profile has to declare the safe fields it
may emit for:

| Operation | Required safe signals | Must not emit |
| --- | --- | --- |
| Connection/pool | outcome, wait/duration bucket, acquisition timeout class, bounded pool counts | hostnames, user names, connection strings, certificates |
| Transaction | operation category, outcome, duration, rollback/error class, safe row-count bucket | SQL text, bind values, row contents |
| Migration | migration identifier, checksum status, outcome, duration | migration body, schema data, credentials |
| Outbox/worker state | stable opaque work/outbox identity where profile permits, attempt/fence bucket, outcome | queue body, record values, tenant or user PII |
| Backup/restore rehearsal | rehearsal identifier, safe object count/checksum result, duration, outcome | database contents, snapshot identifiers if policy marks them restricted |

The target design must define alarms and runbooks for at least:

- unavailable database / failed dependency readiness;
- storage headroom, connection saturation, and persistent database error rate;
- backup failure or a missed restore-rehearsal policy; and
- migration failure or schema-version incompatibility.

Thresholds, destinations, retention, and escalation owner belong in the
target's alert policy and configuration records, not in adapter source.

## Six-stage delivery programme

The six stages below are the build route for this reference. A stage can add
source files and local tests, but it does not authorise the AWS mutation in the
following stage. Each stage finishes with a documented inspection so that a
later discovery cannot silently contaminate the wrong layer.

### Stage 1 — decide the relational reference and inspect the target

**Objective:** turn the proposed direction into an exact, reviewable target
design before adding a driver or cloud resource.

1. Perform read-only inspection of the `kanbien/staging` VPC, subnets, security
   groups, workload roles, CloudWatch destinations, budget posture, existing
   legacy RDS boundary, and current AWS engine/version availability.
2. Record the initial engine/version family, supported RDS CA/TLS approach,
   instance and storage cost ceiling, backup retention, deletion-protection
   posture, database subnet group, approved workload security groups,
   credential-delivery method, and isolated restore destination strategy.
3. Decide whether the first reference will prove PostgreSQL row-level security
   (RLS) or defer it explicitly while proving application predicate isolation.
4. Write a short threat-model decision record covering public exposure,
   injection, tenant escape, credential access, destructive migration,
   unavailable database, data recovery, and evidence redaction.
5. Update the staging target profile and readiness documents with references
   only; do not add secret values or create resources.

**Repository output:** a PostgreSQL AWS change plan, target-profile selections,
and a threat-model/readiness record beneath the existing `infra/04.deploy` and
`docs/aws` ownership boundaries.

**Pass:** a reviewer can name every proposed resource, network path, role,
cost cap, rollback boundary, and non-goal.

**Stop:** public exposure, legacy-resource reuse, cross-region movement,
unbounded standing cost, unclear credential ownership, unavailable supported
engine/TLS combination, or a permission broader than the stated roles.

### Stage 2 — build the provider adapter and prove it locally

**Objective:** implement PostgreSQL translation without leaking it into Core,
generic platform persistence, or a product capability.

1. Inspect existing Core and `platform/persistence` seams. Add a Core contract
   only for a demonstrated provider-neutral semantic gap; never add types that
   merely rename a driver API.
2. Create `platform/adapters/aws/persistence/postgresql/` as its own workspace
   package with a README and deliberate public barrel.
3. Add the scanable adapter topics: `config`, `connection`, `errors`,
   `transactions`, `outbox`, `processing`, `migrations`, and `telemetry`.
4. Validate non-secret configuration at startup. Require the selected TLS
   policy, bounded connection-pool and operation timeouts, and an explicit
   secret reference; reject unsafe or missing values before connecting.
5. Map PostgreSQL/driver outcomes to stable persistence errors. Do not allow
   raw SQL, bind values, row data, provider payloads, or connection details to
   cross the public error or telemetry boundary.
6. Add package-level README entries, boundary tests, type tests, and adapter
   tests for configuration redaction, parameterised-value handling, error
   mapping, transaction rollback, and safe observation fields.

**Repository output:** a provider-specific adapter only at
`platform/adapters/aws/persistence/postgresql/`; any demonstrated generic
contract adjustment plus its tests; no application schema or AWS template.

**Pass:** package, unit, type, boundary, injection-resistance, and redaction
checks pass with no `pg`, RDS, SQL, or connection-string import above the
adapter.

**Stop:** a product table name, business state, raw SQL, provider SDK, or
credential detail appears in Core or generic `platform/persistence`.

### Stage 3 — prove the relational semantics and smoke capability locally

**Objective:** prove the semantics against a disposable PostgreSQL instance,
then use one harmless platform-smoke capability to join the adapter to the
existing server, worker, and observability boundaries.

1. Add a disposable local PostgreSQL fixture. It must create and destroy an
   isolated synthetic database/schema and use neither AWS credentials nor a
   developer's long-lived database.
2. Add an ordered migration manifest/history table and prove that an applied
   migration with a changed checksum fails closed.
3. Use only opaque synthetic tenant and record identifiers to prove:
   atomic state + lineage + outbox writes; rollback leaves no partial records;
   stale optimistic-concurrency updates are rejected; expired claims cannot
   complete behind a higher fence; and tenant A cannot read/update/delete or
   infer tenant B data.
4. Add one narrowly named relational platform-smoke route/job—not a generic
   repository framework. Its product-facing schema belongs to the smoke app;
   the adapter remains unaware of its business meaning.
5. Declare its configuration, timeout, delivery, observability, and, where
   needed, audit profiles. Prove that no request body, SQL, row, tenant/user
   PII, secret, or queue body enters normal telemetry or audit extras.
6. Reuse the provider-neutral queue/worker contracts and the durable
   completion-before-SQS-acknowledgement ordering. Do not enable continuous
   relay polling as part of local proof.

**Repository output:** adapter integration tests, local fixture, smoke-app
composition/tests, target-composition configuration schema, and updated
package READMEs/handbook evidence.

**Pass:** the local relational smoke flow proves transactions, migration
immutability, concurrency, lease/fence safety, synthetic tenant isolation,
outbox relay compatibility, and safe observability.

**Stop:** any real record/credential is required for tests; the feature changes
the completed DynamoDB proof; or a supposedly local test uses a shared target.

### Stage 4 — define and validate the staging infrastructure, without mutation

**Objective:** make the RDS target source-defined, scanable, least-privilege,
observable, cost-bounded, and reviewable before it exists.

1. Add focused CloudFormation fragments for relational resources,
relational-access policy, and relational workload configuration. Do not place
database/network/access/logging concerns into one monolithic template.
2. Define an isolated RDS PostgreSQL reference with private accessibility,
database subnet group, selected workload-only security-group ingress,
encrypted storage, selected TLS parameter group, backups, deletion protection,
and safe database log exports.
3. Define separate migration and runtime task roles, each with the smallest
AWS secret-access permission needed. Configure separate database authorities;
the runtime authority must not perform arbitrary DDL.
4. Add target configuration references, CloudWatch alarms/runbooks, tags,
budget alerts, readiness checks, and an explicit restore/rollback procedure.
5. Add static infrastructure and source-boundary tests. Create and inspect an
exact CloudFormation change set, but do not execute it in this stage. When the
rendered template exceeds the AWS inline limit, first create and review a
separate private artifact-store stack rather than reusing an unrelated bucket.

**Repository output:** `infra/04.deploy` target fragments, least-privilege IAM
documents, verification scripts/tests, target profile/readiness records, and a
deployment plan. No secrets values or live resource IDs belong in source.

**Pass:** the artifact-store change set contains only its encrypted private
bucket and TLS-only policy; the later Foundation change set contains only
reviewed relational resources and workload configuration. Neither may alter
legacy site, DNS, default ALB routing, existing Cognito clients, unreviewed
secrets, DynamoDB smoke table, or existing queue proof.

**Stop:** an unexpected replacement/deletion, broader IAM, public endpoint,
absent rollback/restore route, missing cost control, or sensitive value in
source/evidence.

### Stage 5 — deploy once and prove the security/configuration boundary

**Objective:** after a separately approved AWS change, prove that the target
matches the reviewed source before putting a smoke record into it.

<!-- deterministic-check: allow reason="this is a human-reviewed AWS deployment and security-evidence sequence; later target-specific scripts may automate individual checks but cannot decide whether the reviewed change set remains within the approved authority" -->
1. Apply only the reviewed change set through the governed AWS workflow.
2. Verify the service and any approved one-shot migration task are healthy;
   confirm the applied migration manifest/checksum with safe aggregate facts.
3. Verify RDS has no public access, uses encryption and selected TLS, and is
   reachable only from the approved workload path. Prove an unapproved path
   cannot connect without retaining endpoint, account, credential, or provider
   diagnostics in evidence.
4. Verify the separation of runtime and migration authority, target-owned
   alarms, backup/deletion-protection settings, log access boundaries, and
   current cost/budget state.
5. Record safe deployment evidence and stop before any state-changing smoke
   request if a rollout is unhealthy, a cost/configuration differs, or access
   is broader than planned.

**Repository output:** a reviewed deployment-evidence record and updated
readiness state. No new business data and no continuous worker/relay service.

**Pass:** live health/ready, private-network, least-privilege, encryption/TLS,
migration, alarm, and cost checks pass with no sensitive values in evidence.

### Stage 6 — one controlled delivery, recovery rehearsal, and handoff

**Objective:** prove the full relational route and its recovery path at the
same bounded scope, then state its exact operational limits.

1. With a distinct, bounded approval, run one fixed harmless relational smoke
   request. It may create only approved opaque state, lineage, and outbox facts.
2. Run at most one governed relay and one self-terminating worker path. Require
   durable completion before queue acknowledgement and inspect only aggregate
   terminal state: no due outbox record, empty source/DLQ queue, no lingering
   worker service, expected synthetic record count, and alert state.
3. Exercise the planned failure/duplicate control locally or in the approved
   bounded route so that retry, idempotency, lease/fence, and terminal queue
   handling have evidence appropriate to their risk.
4. Run a separately controlled restore rehearsal into an isolated recovery
   destination. Verify only schema version, migration state, synthetic
   record/count/checksum, recovery duration, and no impact on the live
   reference.
5. Publish a readiness/evidence record naming source commit/image, target,
   configuration version, restore exercise, alarms/notification proof, owner,
   cost posture, residual limitations, and next review date. Mark the
   reference complete only at this bounded scope.

**Pass:** terminal queue/outbox state, duplicate/retry protection, migration
state, restore result, alert receipt, rollback/runbook evidence, and target
health all pass.

**Stop:** non-empty final queue, unsafe evidence, unexpected cost or
configuration, unhealthy rollout, incorrect tenant isolation, an unplanned
destructive action, or uncertain restore scope.

The following remain separate product decisions after Stage 6: which entities
use PostgreSQL, actual schema and retention policy, legal hold/erasure, data
residency exceptions, human/tenant authorisation source, availability
objectives, continuous outbox dispatch, reporting/search, and cross-region
design.

## Definition of done

This plan is complete only when all of the following are true:

- Provider-neutral boundaries remain clean and tested; PostgreSQL code exists
  only in the approved adapter package and target implementation.
- The PostgreSQL adapter has configuration, connection/TLS, transaction,
  concurrency, outbox/processing, migration, error, and telemetry tests.
- A local disposable integration proof covers atomicity, rollback, stale
  concurrency, lease/fence behaviour, migration immutability, and synthetic
  tenant isolation.
- The staging target is private, encrypted, least-privilege, observable,
  cost-bounded, backup-enabled, and source-defined through reviewed IaC.
- A single harmless relational smoke flow has terminal end-to-end evidence
  without unsafe data in records, logs, metrics, traces, alerts, or docs.
- A controlled restore rehearsal proves recovery without overwriting the live
  reference, and its operating/runbook evidence names its limits.
- The production-reference baseline is updated to distinguish this relational
  reference from real entity-data onboarding and high-availability production
  service.

## Related artifacts

- [Persistence Foundation v1](persistence-foundation-v1.md) — reusable
  provider-neutral persistence foundation and completed DynamoDB/SQS reference.
- [Production Reference Target Baseline](production-reference-target-baseline.md)
  — capability maturity and the boundary between smoke proof and product data.
- [Platform Runtime Implementation Plan](platform-runtime-implementation.md)
  — enduring ownership boundaries and target-composition rules.
- `docs/03.product/rules/platform/concerns/persistence-files-storage.yml` —
  persistence/files/storage ownership rules.
- `.agentic/aws/workflows/plan-aws-change.md` and
  `.agentic/aws/workflows/execute-approved-aws-change.md` — later AWS planning
  and execution governance.
