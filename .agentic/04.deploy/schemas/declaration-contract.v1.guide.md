<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.declaration-contract.v1.guide
version: 1
status: draft
created_on: "2026-10-06"
updated_on: "2026-10-26"
layer: 04.deploy
domain: deployment.declaration-coverage
disciplines:
- agentic
- architecture
- security
- sre
kind: guide
purpose: Explain how to write a bounded declaration contract and interpret declaration coverage results.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.schema.declaration-contract.v1
  path: .agentic/04.deploy/schemas/declaration-contract.v1.schema.yml
-->
# Declaration Contract v1 Guide

A declaration contract is a compact map of what one bounded deployable
capability needs. It is not a duplicate target profile and it is not live
evidence. It connects a requirement to the code that needs it, the local
declaration that supplies it, and the proofs that must later confirm it.

Start with a small scope. For example, a platform-shell server baseline can
cover its runtime image, immutable package identity, HTTP/health boundary,
required app configuration, and rollback declaration. It must explicitly
exclude PostgreSQL, workers, relay, queues, and other dependencies until they
receive their own requirement chains.

Every requirement needs one stable ID and one owner. `declarations` answer
where the repository states the expectation. `local_proofs` show the source is
internally consistent. `target_proofs` name the future safe read that Target
Alignment will use. `package_proofs` and `run_proofs` are required when source
declaration alone cannot prove the package or live behavior.

A contract is covered only within its own scope. Adding a new environment
variable, image input, database dependency, queue, identity, network path, or
recovery requirement means updating the contract or declaring that a different
scope owns it.

Proof fields use stable IDs in `scripts/repo/check-selection/checks.yml`, with
stage and exact target-profile applicability. The physical delivery census
finds these contracts and the shared selector runs their applicable checks;
registration is not limited to the newer scope-index format.

A local-only profile uses `deploy/local-target-profile/v1` and declares
`execution: {kind: local, publication: none, provider_deployment: none}`.
Its bounded scope may mark deploy/acceptance stages inapplicable with explicit
reasons. It still needs local proofs and actual finished-image qualification
for a supported image. Hosted retirement never retires an active local image
implicitly; a retained artifact can have both historical and current consumers.
