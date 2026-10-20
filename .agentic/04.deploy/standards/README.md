<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.standards.readme
version: 1
status: active
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

- `runnable-program-candidates.md`: declares the reviewed source boundary for
  a runnable program, its package candidate, and safe qualification evidence.
