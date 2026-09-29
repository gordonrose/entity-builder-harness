<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.fixture.operational-realization-source-coverage
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines: [architecture, security, sre]
  kind: fixture
  purpose: Provide static local task sources for discovery and source coverage mutation tests.
  portability: {class: reusable, targets: [entity-builder]}
  used_by:
  - id: deploy.test.operational-realization-source-coverage
    path: scripts/04.deploy/operational-realization-gate/test_source_coverage.py
-->
# Source coverage fixture

The synthetic query service and finite loading job contain distinct immutable
image references and commands, with configuration, identity and secret-reference
bindings. A static import represents an externally owned warehouse reference.
The composition tests map it to a separate provider and allow only inspection
and consumption, while the task itself remains release-managed.

These sources exercise discovery without executing a command, resolving
credentials, connecting to a warehouse or qualifying provider behavior.

Tests copy this directory into a temporary source root, create a reviewed
composition and adoption ledger from the initial observations, and then introduce
unlisted executables, sidecars, secret bindings and source changes independently.
A ledger template remains pending until the test explicitly reviews it. Mutable
fixture variants stay outside this directory.

Run `python3 -B -m unittest discover -s
scripts/04.deploy/operational-realization-gate -p test_source_coverage.py -v`
from the repository root to reproduce the positive CLI compilation and negative
mutations. The ordinary combined `deployment:realization:check` also runs them.
