<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.architecture.adr.0040-selected-release-control-store-and-executor
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: adr
purpose: Record the user-approved selected shared-control operating policy while separating source implementation from AWS activation and operation authority.
portability: {class: internal, targets: [kanbien/staging]}
used_by:
- id: deploy.plan.iaas-release-control-mvp
  path: docs/04.deploy/plans/iaas-release-control-mvp.md
-->
# ADR 0040: Selected shared-control store and executor

## Status

Accepted for source implementation on 2026-09-30 by explicit user approval of the
[operating policy](../plans/iaas-release-control-mvp-control-policy-proposal.md).
AWS creation, hosted activation and individual operations remain unapproved.

## Context

ADR 0039 proves local conformance only. The staging MVP also requires different
hosts to agree on one writer, preserve attempted operations and recover after an
interrupted request. A local SQLite database or workflow concurrency convention
cannot establish that shared state. The current candidate and relational paths
must ultimately use the same control boundary.

## Decision

Extend the existing Operational Realization Gate, journal/action machinery and
AWS adapters. Select one protected-main/staging GitHub executor, a dedicated
DynamoDB operation store and private versioned S3 evidence store in eu-west-1.
Use a separate narrowly scoped controller role; preserve existing publisher and
passive reconciliation roles. Keep WSL compile/plan/inspection capabilities.
No permanent controller service or general high-availability system is selected.

The linked policy supplies the accepted retention, encryption, recovery,
authority, lease and spending limits. Its spending figures are ceilings, not
price estimates. Exact CloudFormation, IAM trust/access, current costs and
bootstrap/change-set scope require review before separate execution approval.
Initial activation must prove shared-store conformance before effect permissions
are added. A policy approval is never a particular operation's authority token.

Retain local v1 record readers and tests unchanged. Introduce explicitly
versioned selected-operation contracts and reuse pure binding, transition,
reservation and evidence rules. Source conformance stays unauthorized. Supported
candidate/relational/hosted callers must converge on the same execution decision;
there is no direct fallback when that boundary is unavailable.

## Consequences

Persist an immutable effect reservation before dispatch. A database lease fences
journal updates but cannot cancel an AWS request or old valid credentials.
Takeover therefore permits reconciliation only while earlier ownership or
provider effects remain unresolved. No successful subprocess or local receipt
can supply authority. Restoring storage invalidates old ownership generations
and requires reconciliation before re-enablement.

This decision does not prove a backend, hosted executor, source/live equivalence,
provider operation or recovery rehearsal. The complete M4 and M5 acceptance
criteria remain open until their source, local and specifically approved live
checks pass. The full 17-gate matrix and source-result refusals are retained.
