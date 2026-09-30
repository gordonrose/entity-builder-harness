<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.review.release-control.finite-recovery.2026-09-30
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record exact local inert container interruption recovery and its remaining production boundaries.
portability: {class: internal, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Durable finite-fixture recovery — acceptance record

Status: accepted as a source-only delivery unit. Focused verification passed
198 tests (90 recovery/boundary and 108 shared Engine regressions); independent
review passed 31 public/conformance tests. Fresh integrated real proof passed
eight cases with seven killed/reopened processes. Final clean verification
passed 1,735 tests in 51 suites and 58 metadata headers, exit 0.

The implementation connects the existing local operation store to the shared
container Engine. Full immutable attempt identity commits with operation intent.
Every create, start, inspect, log and cleanup reservation commits before its
bounded Engine call. A lost response consumes its budget; it is never silently
retried. A replacement controller uses the current lease/fence and exact image,
name, ownership token and observed ID. Only matching observations can advance
that operation. Known terminal completion and fresh owned cleanup precede closure.

Eight scenarios cover normal completion and process interruption after intent,
create reservation, create effect, start effect, terminal observation, cleanup
effect and cleanup verification. Seven scenarios must close. The unconfirmed
create reservation must remain unknown even when an independent lookup finds no
resource; this is the correct refusal to infer dispatch outcome or replay it.
The conformance additionally verifies exact owned resource absence for every case.

The public command accepts only the already qualified source-owned full-image
pin, checks historical qualification/source bindings before Engine creation and
independently inspects image metadata and payload. It does not build or pull.
The source/import closure, shell and Python wrappers, fixture, lock and versioned
schemas are digest-bound. A changed implementation cannot reopen an older store
silently. A plain local-control store is rejected before a writable open.

Review repaired unsafe ordering after an unresolved cleanup, stale observations,
per-subcommand deadline reset and incompatible store adoption. A real scratch
attempt exceeded the unchanged action deadline during repeated validation; bounded
immutable-content validation caching removed that cost. Current clock, fence,
lease, revision and resource checks remain live. The failed attempt and earlier
passing receipts remain preserved in scratch as history. Final public review also
required success revalidation and the shell wrapper's byte binding; negative tests
cover both. The final integrated real run supersedes those earlier source bindings.

The store and fixture are local single-host references. This does not prove host
reboot/power loss, distributed locking, production policy, authenticated cloud
storage, provider cancellation, AWS permissions/bootstrap or product task effects.
An existing local image is required; no cross-host acquisition/reproduction is
claimed. All source/release/operation/qualification authority stays blocked,
semantic verification is absent and product-profile updates are empty. Common
result consumption rejects aggregate and per-attempt receipts for every purpose.

Next: derive package exports and runtime projections from manifest/source identity
and actual compiler emission. Remaining source semantics, production supply-chain
materials and stores, AWS adapters/preflight, orchestration and approved live target
qualification remain open. PostgreSQL Stage 6 stays paused.

The first complete run passed every test but failed a missing documentation
metadata link. After that documentation-only repair, the exact metadata check
and a complete clean rerun both passed. Bound source and real receipt bytes
were unchanged. Failed-run history is retained in the verification summary.
