<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.fixture.cloudformation-references.readme
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Describe inert CloudFormation reference fixtures and their structural-only proof boundary.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.test.release-control-cloudformation-inventory
  path: scripts/04.deploy/release-control/discovery/test_cloudformation_inventory.py
-->
# Structural reference fixture

`template.yml` is an inert source grammar fixture. Its queue/role declarations
exercise explicit and implicit dependencies, parameter and pseudo-parameter
substitution, condition selection, both branches, and an output reference.
It is never sent to a provider and does not claim valid complete AWS properties
or runnable deployment behavior. Adversarial mutations and composed-fragment
fixtures are built in temporary directories by `test_cloudformation_inventory.py`.
