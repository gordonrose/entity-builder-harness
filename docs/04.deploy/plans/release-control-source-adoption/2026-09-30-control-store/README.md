<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.review.release-control.control-store.2026-09-30
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record exact local durable operation-control conformance and its remaining production boundaries.
portability: {class: internal, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Local durable operation controls — acceptance record

Status: accepted as a source-only delivery unit. All 83 focused tests and
independent review passed. Fresh public conformance passed ten cases. Combined
clean verification passed 1,645 tests in 46 suites and 56 metadata headers.

The implementation extends the existing Operational Realization Gate with
immutable intent, atomic resource-scope leases, durable fencing generations,
validated journal transitions and full typed evidence content. Resource identity
is independent of release identity. Unknown effects block another release, and
expired owners may only reconcile. Cleanup must have current evidence before
scope release. Stale, unavailable, corrupted or incorrectly bound evidence fails.

The [exact receipt](conformance-result.json) records ten cases, seven real child
processes and three deliberate process kills. Those prove persisted intent,
effect/evidence retention, rollback of uncommitted writes, competing claims and
revisions, reconciliation-only expiry, cross-release conflict, persistent fencing,
clock rollback refusal and missing-evidence refusal. The public command created
only its own unique private directory and returned exit 0 with empty stderr.

Seven helper/CLI/wrapper files and four loaded schemas are digest-bound. Independent
review identified and repaired the initial omission of wrapper bytes; a mutation
regression now checks every added wrapper. The common source-result consumer
refuses source-analysis, release-eligibility and operation-authorization uses.

This is a local reference store under trusted host, clock, filesystem and same-UID
assumptions. SQLite runtime and DELETE/FULL mode are observed. Tests prove process
interruption, not host reboot, power loss, distributed consensus, encrypted cloud
storage or independent authenticity. Hashes detect corruption, not malicious
replacement by a trusted host. Fixture policy is not a production retention/RPO
or lease policy. In-flight provider requests cannot be cancelled by a local fence.

The earlier boundary-test failure was a wrong test API call and has been repaired;
all twenty public-boundary cases now pass. The actual store schema remains bound
and incompatible modes/schema/boot identities are refused without automatic
migration. Private fixture databases remain outside Git for inspection.

Next: connect this protocol to the existing finite container engine and establish
real interruption reconciliation. Caller coverage proceeds in the same source
batch. AWS stores/adapters, target preflight and production qualification remain
open. PostgreSQL Stage 6 remains paused; all release/operation authority is blocked.
