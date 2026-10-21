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

Add standards here only when they apply across providers. Provider-specific
requirements remain in their active provider governance surface during the
transition.

Current standards:

- `deployment-artifact-placement-and-naming.md`: decides whether new deployment
  facts, instructions, or executable checks belong in `infra/`, `.agentic/`,
  or `scripts/`, then requires a lifecycle-aware path and a clear action or
  requirement name.
- `runnable-program-candidates.md`: declares the reviewed source boundary for
  a runnable program, its package candidate, and safe qualification evidence.
- `declaration-coverage.md`, `delivery-access-coverage.md`, and `package-qualification.md`: define declaration, delivery, and package evidence requirements.
- `target-alignment-preflight.md` and `provider-async-conditions.md`: define fresh target comparison and provider-controlled condition handling.
- `accepted-release-and-recovery.md`: defines retained immutable baseline and bounded restoration rules.
