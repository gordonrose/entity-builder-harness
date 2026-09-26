<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.architecture.adr.0034-use-private-target-owned-cloudformation-artifact-stores
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- security
- sre
kind: adr
purpose: Record how a target supplies oversized reviewed CloudFormation templates without reusing unrelated storage.
portability:
  class: source-only
  targets:
  - kanbien/staging
used_by:
- id: aws.plan.kanbien-staging-postgresql-relational-reference-v1
  path: docs/aws/kanbien-staging-postgresql-relational-reference-v1-deployment-plan.md
- id: product.plan.postgresql-relational-persistence-reference-v1
  path: .agentic/03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md
-->
# ADR 0034: Use a Private Target-Owned CloudFormation Artifact Store

## Status

Accepted for the `kanbien/staging` platform-shell target.

## Context

The platform-shell Foundation is a deterministic composition of focused
CloudFormation source files. Its rendered form is larger than CloudFormation's
51,200-byte inline-template limit. A change set therefore needs an S3 template
URL.

The account contains no suitable staging-owned deployment-artifact bucket.
The existing buckets belong to CloudTrail, the legacy site, or other
environments. Reusing one would blur resource ownership, lifecycle, access
review, cost attribution, and evidence boundaries.

## Decision

Create a separate, target-owned CloudFormation stack named
`kanbien-staging-platform-shell-deployment-artifacts`. It owns only the bucket
`kanbien-staging-platform-shell-cfn-artifacts-337159794548` and the bucket's
TLS-only deny policy.

The bucket must:

- block every public-access route and enforce bucket-owner object ownership;
- use default SSE-S3 encryption and deny non-TLS transport;
- grant no principal through its bucket policy;
- use `RetainExceptOnCreate`: remove an empty initial-creation rollback, but
  retain the established bucket if its stack is later deleted; and
- expire objects under `change-sets/` after 30 days and abort incomplete
  multipart uploads after one day.

Only deterministic, non-secret rendered CloudFormation templates may use the
bucket. Product data, database records, credentials, tokens, endpoint data,
request/response bodies, logs, and arbitrary uploaded artifacts are outside
its purpose.

The artifact store is a separate bootstrap stack, not a Foundation fragment:
the bucket must exist before CloudFormation can retrieve the rendered
Foundation template. Each artifact-store and Foundation change set remains a
separate reviewable AWS action.

## Consequences

The target gains a small S3 cost and a one-time bootstrap deployment, both far
below the approved relational-reference cost ceiling. It gains a clear,
target-scoped home for future oversized, reviewed platform-shell templates.

This does not give GitHub Actions or application tasks storage access. Future
automation needs an independently reviewed, least-privilege identity and must
remain constrained to the approved bucket and prefix. The artifact store is
not a general artifact repository, a runtime object store, or a secret store.
