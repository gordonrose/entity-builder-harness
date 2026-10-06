<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.providers.readme
version: 1
status: active
layer: 04.deploy
domain: deployment.provider-adapters
disciplines:
- agentic
- architecture
kind: documentation
purpose: Reserve the provider-adapter boundary for deployment governance without moving active provider-specific controls.
portability:
  class: source-only
  targets: []
used_by:
- id: deploy.layer.readme
  path: .agentic/04.deploy/README.md
- id: deploy.plan.migration.aws-provider-neutral-transition
  path: .agentic/04.deploy/plans/migration/aws-provider-neutral-transition.md
-->
# Deployment Provider Adapters

Provider adapters will live here only after their migration or adoption plan is
approved. The current AWS adapter boundary remains `.agentic/aws/`; do not
copy, move, or replace it from this directory during the transition bootstrap.
