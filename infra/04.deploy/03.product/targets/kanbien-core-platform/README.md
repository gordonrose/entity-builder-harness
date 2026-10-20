<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.03-product.targets.kanbien-core-platform.readme
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-20"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines:
- architecture
- security
- sre
kind: target-guide
purpose: Explain the repository declaration for the planned isolated Kanbien core-platform target.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.command.core-platform-target-declaration
  path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh
-->
# Kanbien Core Platform Target

This is a repository declaration for the planned `kanbien-core-platform`
target. It is not an AWS environment, a selected account, a deployable
workflow, or proof that any target is aligned.

The target begins from an absent baseline. `target-profile.yml` lists the
facts that must be selected by the E0 read-only inspection before a target
mutation can be proposed. The static declaration checker may report
`repository-declaration-complete`; only later read-only provider evidence may
report `live-target-aligned`.

- `foundation/` owns shared target facilities and their unresolved E0 facts.
- `scopes/bootstrap-runtime/` owns the first workload, its private verifier,
  safe configuration names, and its excluded concerns.
- `pipelines/github-actions/` records the future delivery-route requirements.
  It does not create a workflow or grant publication or deployment authority.

Do not add values for account identifiers, regions, resource names, endpoints,
roles, secrets, network identifiers, or provider responses here before the
approved E0 inspection selects them.
