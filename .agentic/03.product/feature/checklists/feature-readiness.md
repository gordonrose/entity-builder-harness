<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.feature.checklist.readiness
version: 2
status: active
created_on: "2026-11-06"
updated_on: "2026-11-15"
layer: 03.product
domain: feature-governance
disciplines: [architecture, backend, sre]
kind: checklist
purpose: Make product-feature readiness claims observable before advancing proof stages.
portability: {class: source-only, targets: []}
used_by:
- id: product.feature.workflow.create
  path: .agentic/03.product/feature/workflows/create-feature.md
-->
# Feature readiness checklist

## Feature boundary

- [ ] Owning app, product, feature name, operations, exclusions, and public mount consumer are recorded.
- [ ] The existing plan records the [shared reuse assessment](../../../shared/standards/require-change-completion.md#reuse-simplicity-and-normal-delivery), including older conflicting callers/rules and the delivery impact; any new scope or machinery has an explicit ownership/isolation reason.
- [ ] The feature has one intentional public index and the platform imports only the public app mount.
- [ ] Contract, transport, domain, and persistence responsibilities are separated where the feature has those concerns.
- [ ] The local README reflects actual files, exports, call flow, and limits.

## Behaviour and safety

- [ ] Runtime schemas validate feature attributes before business work.
- [ ] Feature errors expose stable caller-facing code/message meaning.
- [ ] Diagnostics expose bounded code/detail/classification without raw causes or private values.
- [ ] Each domain use case has a named service owner and no implicit retry or replay occurs after an uncertain persistence outcome.

## Persistence

- [ ] The feature uses public Core/Platform persistence contracts, not an AWS SDK or target-specific dependency.
- [ ] The app owns an ordered migration reference; the deployment scope owns migration execution.
- [ ] Archive is separate from logical deletion.
- [ ] Restore-window, retention, legal-hold, and purge-eligibility behaviour is tested or explicitly out of scope.

## Proof and advancement

- [ ] Focused feature and composition checks cover accepted and rejected paths.
- [ ] Check-selector output for changed paths is recorded.
- [ ] Package, target, and live-AWS claims name their declaration and proof receipts; absent stages are reported as absent.
- [ ] Applicable proof distinguishes capability qualification from workload delivery under the [realization standard](../../../04.deploy/standards/operational-realization-gate.md#proof-applicability-by-change); retained proof is input-matched, and unimplemented selective reuse remains a gap.
- [ ] Any delivery-time claim follows [budget accounting](../../../shared/testing/standards/test-execution.md#delivery-budget-accounting); absent end-to-end timing is reported as not established, not a pass.
- [ ] Cloud mutation occurred only under the owning 04.deploy/AWS workflow and explicit authority.
