<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.shared.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: source-material-readme
purpose: Define the shared deploy source-material track for cross-target deployment concerns.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.source-material.readme
  path: docs/04.deploy/source-material/README.md
-->
# Shared Deploy Source Material

Use this track for deploy knowledge reused by multiple targets.

Examples include GitHub release control, AWS identity boundaries, deployment
observability, rollback expectations, stale corpus handling, and production
stop conditions.

Do not put target-specific deployment details here unless they apply to more
than one deploy track.
