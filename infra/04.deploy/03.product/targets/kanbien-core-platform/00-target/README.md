<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.targets.kanbien-core-platform.readme
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines:
- architecture
- security
- sre
kind: target-guide
purpose: Explain the repository declaration for the isolated Kanbien core-platform target and its accepted bootstrap release.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.command.core-platform-target-declaration
  path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh
-->
# Kanbien Core Platform Target

This target has a private foundation and one accepted bootstrap runtime. It is
not proof that a future candidate is aligned: each mutation requires fresh
alignment and the routed release workflow.

`target-profile.yml` records the accepted-baseline state. The durable identity
of that release lives in
`../20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml`.
The static declaration checker proves the repository facts are complete; only
fresh read-only provider evidence may report an update or restoration aligned.

- `../10-foundation/` owns shared target facilities and the outstanding cost condition.
- `../20-scopes/bootstrap-runtime/` owns the workload, private verifier, retained
  accepted release, safe configuration names, and excluded concerns.
- `../40-package-custody/github-actions/` records the package-publication route. It does
  not grant deployment authority.

Do not place secrets, raw provider responses, or uncontrolled runtime facts in
these declarations.
