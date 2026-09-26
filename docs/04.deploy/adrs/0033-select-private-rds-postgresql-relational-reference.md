<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.architecture.adr.0033-select-private-rds-postgresql-relational-reference
version: 1
status: active
layer: 04.deploy
domain: persistence.operations
disciplines:
- architecture
- security
- sre
kind: adr
purpose: Record the target choice and operational boundary for the first Kanbien staging PostgreSQL relational persistence reference.
portability:
  class: source-only
  targets:
  - kanbien/staging
used_by:
- id: product.plan.postgresql-relational-persistence-reference-v1
  path: .agentic/03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md
- id: aws.plan.kanbien-staging-postgresql-relational-reference-v1
  path: docs/aws/kanbien-staging-postgresql-relational-reference-v1-deployment-plan.md
-->
# ADR 0033: Select a Private RDS PostgreSQL Relational Reference

## Status

Accepted for `kanbien/staging` reference proof. Source-defined deployment and
operational proof remain separately gated.

## Context

The completed DynamoDB/SQS persistence proof establishes provider-neutral
transactional outbox and worker mechanics. It intentionally does not select a
database for future relational product data.

The platform also needs one low-cost relational reference to prove PostgreSQL
adapter boundaries, transactions, migrations, tenant predicates, recovery,
and operational controls. The target must not disrupt the existing DynamoDB
smoke proof, public staging site, or legacy RDS resources.

Stage 1 read-only inspection found two private subnets in separate availability
zones, current regional support for PostgreSQL 17.11 on `db.t4g.micro`, and an
existing platform-shell tag-scoped `$25/month` alert budget. It also found two
legacy PostgreSQL instances, one unhealthy. Neither is a valid dependency for
the new reference.

## Decision

Create a separate Amazon RDS for PostgreSQL 17.11 reference in `eu-west-1`
when Stages 2–4 have passed and its reviewed CloudFormation change set is
executed.

The reference will use:

- one `db.t4g.micro` single-AZ instance with encrypted GP3 storage, allocated
  at 20 GiB and capped at 30 GiB;
- a new database subnet group over the existing private subnets, a new
  database security group, and `PubliclyAccessible: false`;
- a dedicated `postgres17` parameter group with `rds.force_ssl=1`, with client
  verification of the selected RDS CA;
- seven-day automated backups, deletion protection, snapshot-on-replacement or
  deletion, an isolated restore rehearsal, and no restore-over-live path;
- target-owned generated bootstrap, migration, and runtime credentials, with
  separate PostgreSQL DDL and DML roles; and
- RDS metrics/events and profile-governed application telemetry, but no
  database-engine log export in v1.

The existing server, worker, and relay security groups may receive only a
stateful TCP 5432 egress rule to the new database security group. That group
may receive matching source-group-only inbound rules. No CIDR-based database
path, legacy group change, public endpoint, ALB/DNS/default-route alteration,
or Cognito change is part of this decision.

The initial proof uses tenant-first application predicates and isolation tests.
PostgreSQL row-level security is deferred until a trusted per-transaction
tenant context and non-bypass database role are designed and proven.

## Consequences

The estimated fixed RDS capacity is about `$14.95/month` at 20 GiB and
`$16.22/month` at the 30 GiB storage ceiling, before variable transfer,
retained-snapshot, and tax charges. This is below both the existing tighter
`$25/month` service-tag budget alert and the authorised `€50/month` new
recurring-cost ceiling. It does not make the budget an automatic stop control.

Provider code remains under
`platform/adapters/aws/persistence/postgresql/`. Core and generic platform
persistence remain SQL- and driver-neutral. Product capabilities will still
own their schemas, queries, migrations, classifications, retention, and
authorisation semantics.

The rendered Foundation uses the private target-owned CloudFormation artifact
store decided in [ADR 0034](0034-use-private-target-owned-cloudformation-artifact-stores.md)
when it exceeds AWS's inline template limit. That transport store remains
separate from database data and from the relational Foundation resource set.

The reference is not highly available, does not establish customer-data
residency or product-data approval, and does not authorise a generic CRUD
framework. Future HA, RLS, IAM database authentication, secret rotation,
customer-managed keys, cross-region recovery, or a move of workloads into
private subnets require a separate decision.
