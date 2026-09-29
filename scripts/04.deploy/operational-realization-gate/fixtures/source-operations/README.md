<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.fixture.source-operations.readme
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Explain inert source fixtures and operation contract mutation tests.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.test.operation-contracts-cli
  path: scripts/04.deploy/operational-realization-gate/test_operation_contracts_cli.py
-->
# Operation source fixtures

`cli-source/` is copied into a temporary source root by the public-command
tests. Its workflow and scripts are inspected as text only. No action is
downloaded and no inspected command is executed.

The fixture contains a literal package caller, local module dependency and
mutable external action reference. Tests independently discover its subjects,
generate pending caller and operation declarations, and mark reviewed test
declarations explicitly. Complete source accounting retains unresolved behavior
and rejects both release eligibility and operation authority.

Negative mutations remove or duplicate contracts, change arguments, add or edit
dependencies, alter action inputs/context, corrupt source documents and submit
unsupported authority claims. Collector tests separately exercise build member
changes, cycles, unsafe paths, symlinks and unsupported dependency grammar.
These tests prove the source accounting boundary; they are not artifact/runtime
qualification or a current target release specification.
