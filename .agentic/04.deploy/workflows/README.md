<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflows.readme
version: 1
status: active
created_on: "2026-10-06"
updated_on: "2026-10-20"
layer: 04.deploy
domain: deployment.governance
disciplines:
- agentic
kind: documentation
purpose: Define the home for provider-neutral deployment workflows.
portability:
  class: source-only
  targets: []
used_by:
- id: deploy.layer.readme
  path: .agentic/04.deploy/README.md
-->
# Provider-Neutral Deployment Workflows

Add only workflows that apply independently of a specific target provider.
AWS-specific execution authority remains under `.agentic/aws/` during the
transition.

Current workflows:

- `runnable-program-candidates.md`: reviews a program's declaration before
  package construction, without building or publishing a package.
- `declaration-coverage.md`: ensures a deployable change has a bounded target declaration.
- `package-custody-and-promotion.md`: governs immutable package evidence without deployment authority.
- `target-alignment-preflight.md`: governs fresh local-to-target comparison before a target mutation.
- `release-update-and-recovery.md`: governs the provider-neutral update and restoration sequence for an accepted scope release.
