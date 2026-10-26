<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.script.inventory-deploy-control.readme
version: 1
status: active
created_on: "2026-10-06"
updated_on: "2026-10-26"
layer: 04.deploy
domain: deployment.governance
disciplines:
- architecture
- sre
kind: capability-readme
purpose: Explain the read-only deploy-control inventory and its limits.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.script.inventory-deploy-control
  path: scripts/04.deploy/inventory-deploy-control/script.sh
-->
# Delivery Control Inventory

The existing inventory command is the authoritative delivery census. It scans
physical repository source files independently of indexes, then reconciles
workflows, commands, programs, image definitions, targets, scopes, provider
bindings and templates with existing declarations and check owners.

```bash
npm run deploy:control:inventory
bash scripts/04.deploy/inventory-deploy-control/script.sh --check --json
```

The default and compatibility `--delivery` views use the same report. `--check`
exits nonzero for missing registration, an unbound consumer, an incomplete
requirement chain or a malformed declaration. A source reference alone does
not prove a delivery chain. `--root` selects a disposable test repository.

The JSON report records the source revision and hashes of the actual working
tree inputs, all discovered entrypoints, their authoritative owners, requirement
chains and selected proof commands. Each requirement scope includes the discovered
execution entrypoints, package definitions, provider templates and identity sources,
runtime requirements, evidence classes, acceptance/recovery commands and explicit
stage applicability. Scope counts are not execution-route counts. Named package
`start`, `serve` and `service` commands and their executable sources require a chain. The Markdown view is generated from that
same report. Reports are output only; redirect them to the current session's
log directory when retaining evidence. They are observations, never a second
registry. The historical top-level directory census has been replaced rather
than retained as a weaker success path.

Consequential `aws-mutation` effects take precedence over test/regression names
and fixture locations. Public package commands trace literal interpreter calls,
the governed-script wrapper and same-package `npm run`/`run-script` aliases.
Every consequential implementation needs its own existing requirement chain;
one bound command cannot cover an additional unbound command. Inline provider
commands must use an existing declared script owner; they cannot borrow a route
from an adjacent command. Dynamic, cyclic
or unsupported delivery wrappers fail with an explicit relationship finding.
This bounded tracing does not execute or interpret arbitrary shell programs.
Genuine local fixtures retain their non-operational classification.

The delivery-coverage workflow requires unrestricted `pull_request` coverage.
An empty/null event configuration is supported; path, branch and event-type
restrictions are rejected because no restricted coverage contract is currently
governed. Trigger presence alone does not prove automatic enforcement.

Source coverage is distinct from executed local tests, finished-image tests,
CI execution and current provider observations. The inventory grants no provider
authority and never treats historical acceptance records as fresh live proof.

The repository selector runs this check for every selection. Supported builders,
publication workflows and provider adapters also enforce it before consequential
work. The regression suite uses actual CLI calls with a synthetic second target
and refuses unregistered entrypoints before a fake compiler or Docker can run.

Read-only: no provider reads, secret access, image build or network connection.
The command includes uncommitted source files and does not rewrite evidence.
