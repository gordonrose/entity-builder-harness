<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.threat-model.kanbien-staging-postgresql-relational-reference-v1
version: 2
status: draft
layer: 04.deploy
domain: persistence.security
disciplines:
- architecture
- security
- sre
kind: decision-record
purpose: Record the Stage 1 threat-model decisions for the additive Kanbien staging PostgreSQL relational reference.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: aws.plan.kanbien-staging-postgresql-relational-reference-v1
  path: docs/aws/kanbien-staging-postgresql-relational-reference-v1-deployment-plan.md
-->
# Kanbien Staging PostgreSQL Relational Reference v1: Threat Model

## Decision

The v1 relational reference is a new, private, encrypted, single-AZ RDS
PostgreSQL target for opaque smoke facts only. It is separate from the
completed DynamoDB/SQS proof and from all legacy RDS resources. The control
objective is to establish a trustworthy provider boundary before any business
entity, personal data, document, customer, or medical data is allowed near it.

## Threats and selected controls

| Threat | Selected control | What is deliberately not claimed |
| --- | --- | --- |
| Public database exposure | `PubliclyAccessible: false`, a new subnet group over private subnets, no internet-facing DB rule, and source-group-only port 5432 access. | The public ALB, public ECS task placement, or WAF is not a database control. |
| SQL injection | Parameterised values only; static reviewed SQL identifiers and migration manifest; no request-derived identifiers or arbitrary query endpoint. | An ORM alone does not make a query safe. |
| Tenant escape | Explicit `tenant_id`, tenant-first predicates/indexes, and synthetic cross-tenant read/update/delete/inference tests. | A `tenant_id` column alone is not isolation. PostgreSQL RLS is deferred. |
| Credential misuse | New target-owned generated secret references; distinct bootstrap, migration, and runtime database roles; secret-specific AWS permissions. | Existing secret values, legacy credentials, or wildcard Secrets Manager permission are not reused. |
| Destructive schema change | Append-only checked migration manifest; separate migration path; expand/migrate/contract releases; runtime DDL denied. | Startup code never self-migrates and a failed migration does not cause an improvised rollback. |
| Database unavailability | RDS status, connection, CPU, and storage alarms; safe dependency readiness; documented rollout rollback. | Single-AZ v1 is not a high-availability service. |
| Data loss or unrecoverable backup | Seven-day automated backup retention, deletion protection, snapshot-on-replacement/deletion, and isolated restore rehearsal. | A configured backup is not treated as restore evidence. |
| Telemetry exfiltration | Approved safe operation/outcome/duration/count/error-class fields only; database-engine log export disabled. | SQL, bind values, rows, endpoints, connection strings, secrets, raw RDS responses, and snapshot identifiers are never routine observability fields. |
| Deployment-template exposure or substitution | A separate target-owned private, encrypted S3 artifact store blocks public access, enforces bucket ownership, denies non-TLS transport, grants no policy principal, and expires reviewed template objects. | An artifact bucket is not a data store, authorization boundary, or permission to upload product data, credentials, or arbitrary templates. |
| Cost surprise | Micro single-AZ capacity, 30 GiB storage ceiling, no optional high-cost features, service-tag-scoped `$25/month` alert budget, and later cost inspection. | An alert does not automatically terminate billable resources; unplanned retained snapshots and transfers remain monitored risks. |

## Residual risks and promotion triggers

- The v1 instance is a low-cost reference, not an RPO/RTO or HA commitment.
- The existing workloads run in public subnets, although their security groups
  restrict ingress and the database itself remains private. A later
  private-subnet/NAT-or-endpoint architecture is a separate runtime topology
  decision.
- PostgreSQL RLS, IAM database authentication, managed secret rotation,
  customer-managed KMS keys, cross-region recovery, connection pooling proxy,
  reporting replicas, and data-residency exceptions are out of scope until a
  product requires them and their controls are proven.
- A real product must supply its own schema, classification, lifecycle,
  retention, erasure/legal-hold, authorisation, and query review. This plan
  creates no permission to store product data in the reference.

## Verification rules

Stages 2–6 must stop if the final design introduces a public database path,
legacy dependency, non-parameterised query value, provider detail outside the
adapter, raw sensitive evidence, broader secret/IAM authority, an unexpected
recurring-cost class, unhealthy rollout, cross-tenant access, or an uncertain
restore target. A passed test does not waive any later gate.
