<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.architecture.adr.0035-require-fail-closed-staging-deployment-reconciliation
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- architecture
- security
- sre
kind: adr
purpose: Require live declared-state reconciliation before Kanbien staging infrastructure mutation and on a continuing cadence.
portability:
  class: source-only
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.reconcile-platform-shell-staging
  path: scripts/04.deploy/reconcile-platform-shell-staging/script.py
- id: aws.plan.kanbien-staging-postgresql-relational-reference-v1
  path: docs/aws/kanbien-staging-postgresql-relational-reference-v1-deployment-plan.md
-->
# ADR 0035: Require Fail-Closed Staging Deployment Reconciliation

## Status

Accepted for `kanbien/staging` platform-shell infrastructure changes.

## Context

Source review alone did not establish that repository declarations and live
AWS configuration still agreed at mutation time. Small mismatches—such as a
budget identifier that has changed independently—caused avoidable retries and
made a reviewed change set less trustworthy than it appeared.

## Decision

Every staging infrastructure mutation must be preceded by a fresh,
non-provisioning reconciliation check. The check verifies the selected AWS
account, declared stack state and drift, artifact-store hardening, and the
target budget. A Foundation change-set execution additionally requires an
exact reviewed resource-change allowlist. The command fails closed and emits
only safe check identifiers and verdicts.

The same controls run from a separate main-branch GitHub Actions workflow at a
bounded cadence. Its dedicated OIDC role has only the read/detection actions
needed for those checks. It has no stack mutation, secret retrieval, database,
ECS, Cognito, or deployment permissions.

## Consequences

A planned deployment may be blocked by drift or a source/live discrepancy.
That delay is intentional: resolution is a separate reviewed change, not an
ad-hoc correction inside a deployment attempt. Drift detection has limits—it
checks properties CloudFormation manages and supports—so provider-specific
live boundary checks and post-deployment evidence remain required.
