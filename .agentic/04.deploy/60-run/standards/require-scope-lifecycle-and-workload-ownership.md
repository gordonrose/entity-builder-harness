<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.scope-lifecycle-and-workload-ownership
version: 1
status: active
created_on: "2026-10-23"
updated_on: "2026-10-23"
layer: 04.deploy
domain: deployment.scope-lifecycle
disciplines: [security, sre]
kind: standard
purpose: Require explicit scope lifecycle, exclusive active workload ownership, and governed successor transitions.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.govern-scope-lifecycle
  path: .agentic/04.deploy/60-run/workflows/govern-scope-lifecycle.md
- id: deploy.workflow.verify-health-failure-and-recovery
  path: .agentic/04.deploy/60-run/workflows/verify-health-failure-and-recovery.md
-->
# Require Scope Lifecycle and Workload Ownership

Every new-framework target scope is listed in its canonical lifecycle index
with a lifecycle state, canonical declaration/binding paths, and the exact
bound workload identities it owns. Exactly one active scope owns any workload
identity at a time.

An active scope is the current release authority for its workloads. A candidate
may overlap its active predecessor only while being prepared and proved; it is
not release authority. An accepted-historical scope retains declarations and
evidence for audit and governed recovery, but is not an active deployment
owner.

Changing lifecycle state does not mutate a provider. A candidate failure leaves
its predecessor active. Candidate activation, or later reversion, follows the
applicable release/recovery workflow with fresh alignment, required evidence,
and explicit provider-mutation authority. Never use an index edit to claim a
restoration occurred.

Legacy exceptions identify retiring reference workloads only. They cannot
cover a directory in the new-framework scope index and cannot hide a missing
scope declaration, binding, lifecycle, or ownership claim.
