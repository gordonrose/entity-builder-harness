<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflows.readme
version: 1
status: active
created_on: "2026-10-06"
updated_on: "2026-10-21"
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

Provider-neutral workflows live in their primary lifecycle phase under the
[placement standard](../standards/deployment-artifact-placement-and-naming.md).
This index also lists the cross-phase authority retained here. AWS-specific
execution authority remains under `.agentic/aws/` during the transition.

Current workflows:

- [Prove runnable program builds](../20-build/workflows/prove-runnable-program-builds.md): reviews a program's declaration before
  package construction, without building or publishing a package.
- `declaration-coverage.md`: ensures a deployable change has a bounded target declaration.
- [Publish immutable package with custody](../40-package/workflows/publish-immutable-package-with-custody.md): governs package evidence without deployment authority.
- [Compare declared requirements with live target](../00-target-alignment/workflows/compare-declared-requirements-with-live-target.md): governs fresh local-to-target comparison.
- [Review and execute target update](../50-deploy/workflows/review-and-execute-target-update.md): deploys a reviewed candidate and hands its evidence to Run.
- [Verify, accept or restore release](../60-run/workflows/verify-accept-or-restore-release.md): owns live proof, accepted-baseline recording and bounded recovery.
