<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.declaration-coverage.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.declaration-coverage
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Reserve the offline capability home for declaration-contract coverage validation.
portability:
  class: source-only
  targets: []
used_by:
- id: deploy.workflow.declaration-coverage
  path: .agentic/04.deploy/workflows/declaration-coverage.md
-->
# Declaration Coverage

This capability is not executable yet.

Its first script will validate a declaration contract offline: required fields,
unique requirement IDs, declared source paths, proof-command references, and
explicit scope exclusions. It will not call a provider, inspect AWS, read a
secret, or mutate a target.

Read the Declaration Coverage workflow and standard before implementing the
validator.
