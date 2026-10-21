<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.readme
version: 1
status: active
created_on: "2026-10-06"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.governance
disciplines:
- agentic
kind: documentation
purpose: Define the home for provider-neutral deployment standards.
portability:
  class: source-only
  targets: []
used_by:
- id: deploy.layer.readme
  path: .agentic/04.deploy/README.md
-->
# Provider-Neutral Deployment Standards

Provider-neutral standards live in their primary lifecycle phase under the
placement standard below; cross-phase authority remains here. Provider-specific
requirements remain in their active provider governance surface.

Current standards:

- `deployment-artifact-placement-and-naming.md`: decides whether new deployment
  facts, instructions, or executable checks belong in `infra/`, `.agentic/`,
  or `scripts/`, then requires a lifecycle-aware path and a clear action or
  requirement name.
- [Require runnable program contract](../20-build/standards/require-runnable-program-contract.md): declares the reviewed source boundary for
  a runnable program, its package candidate, and safe qualification evidence.
- `declaration-coverage.md`, `delivery-access-coverage.md`, and `package-qualification.md`: define declaration, delivery, and package evidence requirements.
- [Require fresh safe target evidence](../00-target-alignment/standards/require-fresh-safe-target-evidence.md) and `provider-async-conditions.md`: define target comparison and condition handling.
- [Require immutable package custody](../40-package/standards/require-immutable-package-custody.md): defines package identity and qualification evidence.
- [Retain accepted release for restoration](../60-run/standards/retain-accepted-release-for-restoration.md): defines retained baseline and bounded restoration rules.
