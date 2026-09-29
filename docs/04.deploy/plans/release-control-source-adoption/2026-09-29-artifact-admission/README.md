<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.review.release-control.artifact-admission.2026-09-29
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record cryptographic artifact-evidence verification, producer compatibility and remaining authority gates.
portability: {class: internal, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Artifact evidence admission — acceptance record

Status: accepted source delivery unit. Focused tests, real cryptographic
conformance and final clean verification passed: 1,455 tests across 38 suites,
plus 51 metadata headers. See [verification summary](verification-summary.json).

This delivery unit extends the existing Operational Realization Gate with a
maintained offline attestation verifier, pinned executable and trusted-root
bytes, exact artifact/source/workflow bindings, and required provenance, SBOM
and scan evidence. Its production policy binds the existing publication
workflow identity; the workflow producer has not yet been migrated.

Acceptance includes a genuinely signed public conformance bundle, successful
verification through the pinned executable, and negative signature/payload,
identity/source/subject/predicate, freshness, unsafe-output, tool failure and
policy-completeness cases. Synthetic identities or fixtures cannot qualify a
production artifact. Caller-supplied verified flags and unsigned saved scan
counts are not trusted evidence. Registry manifest and configuration/image
identities must remain distinct.

Existing policy denies CRITICAL and HIGH findings and selects the official
repository, branch and workflow. Production scan freshness/scanner rules must
be explicit reviewed inputs; missing values block admission. Tests may use
clearly labelled fixture policy, without adopting it as production policy.

A supply-chain verification result establishes only its stated evidence scope.
It does not grant operation authority or waive another acceptance stage.
Publication and the first hosted production-attestation run remain separately
approved work.

The exact [conformance receipt](conformance-result.json) records one authentic
public signature accepted and eleven altered identity, subject, artifact,
signature, certificate, payload or timestamp cases rejected. This exercises
the pinned real offline verifier; it does not establish production admission.
The public fixture and its license/source are documented beside the fixture.

Current provenance expects the existing legacy publisher's two image bases. The
qualified local payload path uses a locked host compiler and one active runtime
base. The next producer integration must model these different observed
materials explicitly and publish the tested image without rebuilding it.
Existing generated provenance does not establish that material closure, and
unsigned saved scan counts cannot satisfy the authenticated scan requirement.
The signed SBOM check proves shape and subject binding, not independent
component completeness.

Production scanner assurance and freshness remain reviewed policy inputs.
Tests do not choose them for the owner. Next: observed build-material producer
integration, remaining source/contracts and durable operation controls.
