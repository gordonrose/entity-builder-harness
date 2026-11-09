<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.feature.workflow.create
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: feature-governance
disciplines: [architecture, backend, security, agentic]
kind: workflow
purpose: Govern creation of a bounded app feature and its handoff to product and deployment proof.
portability: {class: source-only, targets: []}
used_by:
- id: product.feature.skill.create
  path: .agentic/03.product/feature/skills/create-feature.md
-->
# Create a product feature

Use this workflow for a real app feature, especially one that validates input, persists state, or is intended to become a deployable product capability. Use the platform-runtime workflow only for platform-shell work and `apps/platform-smoke`; it does not govern this work.

Follow [feature boundary](../standards/feature-boundary.md), the shared [change-completion standard](../../../shared/standards/require-change-completion.md), and [diagnostic coverage](../../../shared/workflows/verify-diagnostic-coverage.md).

## Required inputs

- owning app and product;
- feature name and bounded business capability;
- explicit in-scope operations and exclusions;
- selected persistence capability and its current availability evidence, if it persists data;
- intended proof level: local, package, target alignment, or live AWS;
- public app-mount and product-composition consumers.

## Procedure

1. Record the capability, exclusions, consumers, public contract, lifecycle decisions, persistence dependency, and intended proof in the feature plan or current session record. Do not assume that a local persistence seam is a deployable target.
2. Inspect the selected Core lifecycle contract, Platform persistence port, provider adapter, current product manifest, and target scope. Reuse existing owners. If any required capability is unavailable or its owner is unclear, stop and record the gap.
3. Create the feature using the boundary standard: contracts first, then transport adaptation, domain services, persistence mapping/migrations, and the deliberate public index. Add the local README from actual source.
4. Define safe feature diagnostics at the decision boundary and stable feature errors for callers. Preserve normal operation outcomes; diagnostics do not retry, replay, or turn a failed mutation into a successful one.
5. Connect the feature only through its app’s public mount and product composition. Prove platform code has no import of feature internals.
6. Add focused tests for each operation and meaningful alternative: validation, archive, logical deletion, restore window, purge eligibility, and repository mapping. Include sensitive-data canaries where diagnostics cross a boundary.
7. If the package/runtime/deployment scope changes, use 04.deploy declaration coverage before claiming package, target, or AWS readiness. Add scope requirements and proof references; do not create an ungoverned deploy path.
8. Use the repository check selector for changed paths, then run the selected local checks. Record the distinct local, package, target, and live outcomes.

## Stop conditions

Stop and report a governance gap when:

- an app would import an AWS adapter, target profile, cloud SDK, or deployment manifest;
- a platform module would import a feature-private file;
- hard deletion lacks retention/legal-hold eligibility;
- a feature needs an unselected database, target scope, secret, AWS mutation, or migration-execution path;
- a required package, target, or live proof has no declaration/check chain;
- a request expands into auth, authz, tenancy, public ingress, logging, or telemetry without a separately selected scope.

## Output

Report the feature’s public boundary, files, contract/lifecycle decisions, proof actually completed at each stage, and every remaining gap. A local pass is never described as AWS qualification.
