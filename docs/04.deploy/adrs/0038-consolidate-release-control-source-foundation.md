<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.architecture.adr.0038-consolidate-release-control-source-foundation
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: adr
purpose: Record the source-only release-control foundation and its strict separation from deployment qualification and authority.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# ADR 0038: Consolidate the Release-Control Source Foundation

## Status

Accepted for the six locally verified source-only delivery slices. Operational
execution, hosted activation and provider qualification remain separate work.

## Context

Existing deployment checks describe overlapping source, artifact and target
facts. Their individual success does not prove complete release coverage.
The approved IaaS plan calls for one composition model and operation engine,
with existing commands migrated through compatible interfaces.

## Decision

Extend `scripts/04.deploy/operational-realization-gate` as the public capability.
Versioned closed local schemas bind immutable release definitions to all
seventeen ordered acceptance gates. Independent collectors observe repository
inputs, callers and bounded build dependencies; reviewed declarations reconcile
those observations rather than replace discovery.

Unsupported semantics, stale identities and incomplete coverage remain explicit
blocking findings. Source-analysis success and local synthetic artifact
accounting cannot establish release eligibility, compiler provenance, runtime
qualification or operation authority. The source-result consumer admits only
known successful producers after fresh in-process recomputation and rejects
authority purposes.

Retain earlier command behavior and historical review snapshots. Existing
deployment paths migrate one operation family at a time with equivalence and
caller evidence; this checkpoint does not activate or replace those paths.

Use a verified Python distribution lock and disposable environment for source
checks. This establishes the Python validation environment only. Complete
application build reproduction additionally requires pinned Node, npm,
TypeScript and package dependencies, genuine compiler output and runtime proof.
The prepared GitHub source-validation workflow requires its own first hosted
acceptance run and separately approved publication/required-check activation.

## Consequences

The six source slices can be versioned and reviewed independently of external
deployment authority. Tests establish behavior within their documented source
boundaries. Local receipts and synthetic fixtures retain explicit limits.

Whole-estate adoption, durable authenticated evidence, leases/journals, provider
adapters and live target qualification remain open. The existing reconciliation
requirements in ADRs 0035 and 0036 continue to apply. All future execution paths
must enforce the common authority decision rather than infer permission from
a successful process exit.

The implementation plan and dated review candidates record exact verification,
remaining findings and the next delivery unit.

