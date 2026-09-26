<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.kanbien-staging-postgresql-relational-reference-v1
version: 6
status: draft
layer: 04.deploy
domain: persistence.operations
disciplines:
- architecture
- security
- sre
kind: change-plan
purpose: Define the inspected, additive, low-cost AWS deployment route for the Kanbien staging PostgreSQL relational reference.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: product.plan.postgresql-relational-persistence-reference-v1
  path: .agentic/03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
-->
# Kanbien Staging PostgreSQL Relational Reference v1: Deployment Plan

## Status and boundary

This is a Stage 1 target decision, Stage 2/3 local evidence record, and Stage
4 source-definition/change-set plan. It does not
authorise a CloudFormation execution by itself. The explicit current-chat
programme approval permits progression only after each earlier stage passes;
the later AWS action must still use the governed change-set workflow and stop
on a public endpoint, legacy-resource reuse, broader access, cost drift,
unhealthy rollout, unsafe evidence, or destructive action.

The target is `kanbien/staging` in `eu-west-1`. It is an additive relational
reference for opaque platform-smoke facts. It does not replace the completed
DynamoDB/SQS reference, select PostgreSQL for all product data, or alter the
legacy site, DNS, default ALB routing, Cognito, existing secrets, or a
non-staging target.

## Stage 1 read-only evidence

The 2026-09-26 inspection established only the following safe facts:

| Concern | Result | Decision enabled |
| --- | --- | --- |
| Private network | Two private subnets exist in separate availability zones and have no default internet route. | Create a new database subnet group over those subnets; do not reuse the legacy database subnet-group resource. |
| Legacy boundary | Two legacy PostgreSQL instances exist; one is in an unhealthy encryption-credential state. | Do not modify, read from, restore over, use as a prerequisite, or reuse either legacy instance, its credentials, group, or availability. |
| RDS capacity | The account has capacity for a new instance; PostgreSQL `17.11` on `db.t4g.micro` is currently orderable in the region. | Select a new RDS PostgreSQL 17.11 reference, not Aurora. |
| TLS | The `postgres17` family supports a dynamic `rds.force_ssl` setting and the selected RDS CA is available. | Create a dedicated parameter group with `rds.force_ssl=1`; clients verify `rds-ca-rsa2048-g1`. |
| Workload network | Server, worker, and relay groups currently permit DNS and HTTPS only. | Add precisely scoped TCP 5432 egress only to the new database group; no CIDR-based database egress. |
| Cost | Current on-demand catalogue rates are `$0.017/hour` for the instance and `$0.127/GiB-month` for GP3. | The planned capacity is about `$14.95/month` at 20 GiB, `$16.22/month` at its 30 GiB ceiling, before variable charges. |

The platform-shell tag-scoped `$25/month` budget already alerts through the
existing SNS destination. The new reference must carry that same `service`
tag. This is an alerting guardrail, not a promise that AWS will automatically
stop a workload; the planned capacity is deliberately below both that tighter
guardrail and the authorised `€50/month` recurring-cost ceiling.

AWS bills backup, retained snapshot, transfer, and tax according to actual
use. The reference therefore uses seven-day automated backups, no intentional
manual-snapshot retention, no cross-region copy, no Multi-AZ, no RDS Proxy,
no Aurora, no Enhanced Monitoring, and no Performance Insights in v1. A
restore clone is temporary and checked for deletion only under its separately
controlled restore procedure.

## Exact proposed resource set

### Template-transport prerequisite

The rendered Foundation exceeds CloudFormation's 51,200-byte inline-template
limit. Before the relational Foundation change set can be created, the
separate `kanbien-staging-platform-shell-deployment-artifacts` stack must be
reviewed and applied. It may contain only a target-owned S3 bucket and its
TLS-only bucket policy. The bucket is private, encrypted with SSE-S3, blocks
all public access, enforces bucket-owner ownership, grants no principal in its
policy, uses `RetainExceptOnCreate` to clean up an initial failed creation but
retain an established bucket, and expires `change-sets/` objects after 30 days.

This is deployment transport, not relational persistence: it stores a
generated CloudFormation template only, never a database row, credential,
request, response, endpoint, token, or application document. It is a separate
bootstrap stack so there is no circular dependency—the bucket must exist before
CloudFormation can fetch the larger Foundation template. It does not alter the
legacy site, DNS, ALB, Cognito, DynamoDB/SQS proof, or any existing bucket.

After its reviewed deployment, only the one generated Foundation template is
uploaded over TLS under `change-sets/`, and the relational change set references
that object. The object is not committed, and its content is the deterministic
rendering of committed source. The planned lifecycle storage cost is negligible
relative to the authorised RDS reference bound.

The Stage 4 CloudFormation change set may contain only this named relational
unit and its direct supporting resources:

| Group | Proposed resource | Protection/boundary |
| --- | --- | --- |
| Network | New DB subnet group using the two existing private subnets; new relational DB security group. | RDS is `PubliclyAccessible: false`; inbound TCP 5432 is limited to the explicitly approved platform server, worker, relay, migration, and recovery-verifier groups. |
| Database | One new `db.t4g.micro` single-AZ RDS PostgreSQL 17.11 instance, GP3 20 GiB with 30 GiB maximum. | Storage encryption, seven-day backups, deletion protection, snapshot-on-replacement/deletion policies, no public endpoint. |
| TLS | One new `postgres17` DB parameter group. | `rds.force_ssl=1`; the adapter rejects absent TLS verification. |
| Credentials | New target-owned generated references: initial bootstrap, migration, and runtime. | No existing secret is altered; no secret value, endpoint, connection string, token, request, or row goes into source or evidence. |
| Workload access | Separate bootstrap, migration, and runtime task roles plus narrow additions to the existing workload security groups. | Existing tasks receive no relational secret/configuration in this stage. Runtime SQL authority is DML-only after bootstrap; migration authority is reserved for the one-shot migration path; no role has a generic secret wildcard or arbitrary DDL at runtime. |
| Operations | RDS metric alarms, RDS event subscription, runbook and tag-scoped budget use. | Existing SNS destination only; metrics/events and safe application telemetry, not database engine-log export. |

The one necessary change to pre-existing workload security groups is **not**
an open database path: each server, worker, and relay group receives one
stateful egress rule, TCP 5432, whose destination is the new relational DB
security group. The new DB group receives matching source-group rules. The
service's ALB ingress, existing DNS/HTTPS rules, public routing, and all
legacy groups remain unchanged.

## Credential and database-authority sequence

AWS IAM decides who may retrieve a secret; PostgreSQL decides what a retrieved
database role may do. Both layers are needed.

1. RDS creates an initial administrator credential in a new target-owned
   Secrets Manager reference. It is accessible only to an isolated bootstrap
   execution path.
2. A one-time bootstrap task creates distinct PostgreSQL migration and runtime
   roles from target-owned generated secret references, then grants only the
   reviewed schema capabilities.
3. Later migration work uses the migration role and ordered checked migration
   manifest. The normal server, worker, and relay use only the runtime role.
4. Runtime database authority excludes `CREATE`, `ALTER`, `DROP`, ownership
   changes, and access outside the smoke schema. The application never sends
   arbitrary SQL identifiers or SQL sourced from a request.

The initial reference defers PostgreSQL RLS. It instead proves tenant-first
application predicates and cross-tenant rejection with two opaque synthetic
tenant identifiers. RLS may be added only when a later design establishes a
non-bypass runtime role and trusted per-transaction tenant context.

## Stage 2 local adapter evidence

Stage 2 is complete. The new PostgreSQL adapter is isolated at
`platform/adapters/aws/persistence/postgresql/` and has passed its type,
declaration-build, deterministic runtime, and import-boundary checks. Its
recording-pool tests prove strict non-secret configuration/TLS validation,
parameterised values, safe error/telemetry reduction, commit/rollback, and
the one transaction seam for a product DML statement plus lineage/outbox facts.

This is not a database, AWS, migration, tenant-isolation, delivery, or restore
proof. No RDS resource or credential has been created or used in this stage.
Those live semantics remain Stage 3 onward.

## Stage 3 local relational-smoke checkpoint

The source for the disposable local relational proof is now present. It is
deliberately separate from AWS deployment and from the completed DynamoDB/SQS
smoke path:

- `platform/adapters/aws/persistence/postgresql/tests/run-disposable-integration.mjs`
  owns the exact generated Docker container, mode-`0600` temporary credential
  file, loopback-only port, bounded readiness wait, and exact cleanup;
- `postgresql-persistence-adapter-integration.test.ts` runs the real engine
  assertions without printing rows, SQL values, tenant identifiers, passwords,
  endpoints, or queue bodies; and
- `infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence.ts`
  keeps the harmless smoke table and its static insert statement at target
  composition, not in the reusable adapter.

The command is `npm run
platform:adapter:aws:persistence:postgresql:integration`. Its production pool
constructor is not weakened: the local fixture injects a non-TLS pool only
inside the test because a disposable loopback container has no trusted
certificate. The staging RDS connection remains `verify-full` TLS and is
proved only in Stage 5.

On 2026-09-26, the exact command completed successfully after local
dependencies were restored from the committed lockfile. The fixture created
only its generated loopback Docker database, then removed its exact temporary
container and credential file. The evidence is a passed real-engine semantic
proof—not AWS evidence: no RDS resource, target credential, endpoint, shared
database, or product record was used. Stage 4 may now define and validate the
source target and produce a reviewed change set.

## Stage 4 source-definition checkpoint

The source is now rendered from four responsibility-focused Foundation
fragments: relational resources, relational access, relational workload
configuration, and relational operations. The one RDS database is private,
encrypted, single-AZ, backed up for seven days, deletion-protected, snapshot
protected on deletion/replacement, and uses `rds.force_ssl=1`. It has no
database-engine log export because query text could reach those logs.

The target uses one RDS-compatible database name, `platformsmoke`; the harmless
`platform_smoke` schema remains migration-owned. It creates generated Secrets
Manager references rather than source values, and only task roles created for
the later bootstrap/migration/runtime path can retrieve their respective
references. Existing server, worker, and relay roles are intentionally not
expanded in this stage.

The static verifier and full foundation policy check passed locally. Because
the Foundation is larger than CloudFormation's inline request limit, Stage 4
first reviewed and applied the separate two-resource deployment-artifact store.
Its privacy, encryption, ownership, TLS-only, and bounded-retention controls
were verified after creation. The final relational Foundation change set used
`PrivateSubnetIds` as the only new deployment input and retained the previous
value for every existing Foundation parameter.

The relational change set is `AVAILABLE` and remains unexecuted. It has 22
additions and one non-replacement `AlarmTopicPolicy` modification for the
same-account RDS SNS publication path. No RDS instance, relational secret, or
Foundation change set has been applied. The next action is Stage 5's governed
application of this reviewed change set followed by live-boundary verification.

### Mandatory reconciliation boundary

Before the Foundation change set can be executed, run the target's
`pre-foundation-change-set` reconciliation. It fail-closes on a mismatch
between declared source and live AWS state: expected account, stack status and
drift, artifact-store hardening, or tag-scoped budget. It additionally compares
the whole change set to the reviewed 22-addition/one-modification allowlist.

The same target has a separate scheduled read-only reconciliation workflow.
It does not deploy, read secrets, retrieve endpoints, or print provider
responses. A failure is an operational blocker, not a reason to loosen the
check or proceed with a stale review.

## Observability, recovery, and rollback

The adapter emits only its approved provider-neutral observability fields.
RDS metric alarms cover availability/dependency readiness, CPU, free storage,
and connection pressure; RDS events report backup and failure categories to
the existing alarm destination. Engine logs are not exported in v1 because
they can contain raw query text. No SQL text, bind value, endpoint, tenant
identifier, row, credential, provider payload, or snapshot identifier belongs
in normal logs, metrics, traces, alerts, evidence, or commits.

The restore rehearsal restores a selected snapshot to a new, isolated,
private recovery instance with a new, recovery-only security group. It never
replaces the live reference. The verifier checks only expected migration
version, safe record-count/checksum, duration, and live-reference non-impact.
Any cleanup action is assessed as a planned destructive step against the
exact disposable identifier; it is not implicit in normal deployment.

An application/image rollout failure rolls the ECS service back to its prior
task definition. A migration failure stops promotion for reviewed forward
repair; it never attempts an improvised schema rollback. A database recovery
uses the isolated restore procedure—not a destructive restore-over-live
operation.

## Stage gates after this decision

| Next stage | Required proof before moving on |
| --- | --- |
| 2: adapter | PostgreSQL driver remains isolated under its AWS adapter, with redaction, injection-resistance, configuration, error, and transaction tests. |
| 3: local relational smoke | Disposable local PostgreSQL proves atomicity, migration checksum immutability, concurrency, lease/fence, tenant predicates, safe telemetry, and outbox compatibility. |
| 4: source-defined target | Static tests and an exact change set contain only the resources listed above. |
| 5: deployment boundary | A fresh pre-execution reconciliation passes, then live private/encrypted/TLS/access/role/alarm/cost facts match reviewed source before a smoke record is created. |
| 6: bounded delivery and restore | One harmless relational transaction and one queue delivery reach terminal state; an isolated restore proves recovery without live impact. |

## Source references

- [PostgreSQL Relational Persistence Reference v1](../../.agentic/03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md)
- [Threat-model decision](kanbien-staging-postgresql-relational-reference-v1-threat-model.md)
- [Private target-owned CloudFormation artifact store](../04.deploy/adrs/0034-use-private-target-owned-cloudformation-artifact-stores.md)
- [Existing persistence v1 deployment plan](kanbien-staging-platform-shell-persistence-v1-deployment-plan.md)
- [AWS RDS PostgreSQL pricing](https://aws.amazon.com/rds/postgresql/pricing/)
