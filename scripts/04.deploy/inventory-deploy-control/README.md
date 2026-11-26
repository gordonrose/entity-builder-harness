<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.script.inventory-deploy-control.readme
version: 4
status: active
created_on: "2026-10-06"
updated_on: "2026-11-26"
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

## Script topology inventory

```bash
bash scripts/04.deploy/inventory-deploy-control/script.sh --topology --json
```

`--topology` is a separate, read-only planning view for the `scripts/` tree. It
derives a unit's current path, metadata owner, role, literal callers, effects,
scope, overlapping neighbours, objective-oriented destination and provisional
retain/move/merge/remove disposition from repository source and existing
artifact metadata. JSON contains every classified source unit; the default
Markdown view is a compact count and finding summary. It does not create an
alternative registry, validate a structural migration, or infer approval to
move a live route. `--topology` therefore cannot be combined with `--check`.

Roles and destinations are filename/path heuristics, not audited conclusions.
For example, the projector can label `source-transition.py` for removal even
though runtime code still reads its historical custody functions. Its caller
list combines literal source strings with metadata references; neither alone
proves a live executable call. Its suffix set also omits `.jsx`, unlike the
complete source audit. Do not copy those proposed dispositions into a migration.

Use the [source-backed audit and exact P4 proposal](../../helpers/audit.md#p4-current-disposition-and-proposed-folder-manifest--2026-11-25)
to establish responsibility, callers, retained risks and proposed destinations.
The approved 173-source deployment relocation and its 31 Markdown companions
are locally implemented; final qualification and publication remain pending.
The source count is unchanged. This inventory discovers the canonical paths
from the checkout and existing declarations; it does not need a second list of
legacy owners. The catalogue remains useful for finding candidates. Any further
moves still need destination approval and the existing migration workflow. Tests and fixtures
remain proof assets, not operations merely because they sit beside one.

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

For each declared route, proof IDs also trace their reachable catalog `members`
recursively. The census validates exact member command-file existence, unique
nonempty member lists, unknown references, cycles, command-header effect
agreement and parent/member stage/effect
boundaries. It then follows those command bodies, including extracted policies.
It does not traverse the entire catalog, directory inputs or conditional focused
prerequisites as delivery lineage, and does not execute any proof command.
Catalog membership changes select the owning inventory regression through the
catalog's declared census consumer. The real-repository smoke check requires
full `covered` status with no findings, not merely a correctly shaped report.

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
