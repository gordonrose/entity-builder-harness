<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.reference.estate-caller-reconciliation
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: reference
purpose: Define bounded aggregate caller proof, unresolved implementation boundaries and pending adoption migration.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.script.release-control.estate-caller-inventory
  path: scripts/04.deploy/release-control/discovery/estate_caller_inventory.py
-->
# Estate caller reconciliation

This extension connects independently collected source observations to the
existing caller parser. It accounts for literal root-package commands and the
complete established Python dispatch wrapper grammar. It preserves the raw
inventory, unresolved child implementations, tool/action behavior and review
obligations. It cannot grant release eligibility or operation authority.

## Contracts and compatibility

`estate-caller-inventory/v1` aggregates every independently discovered root
`package.json` command and every YAML workflow under `.github/workflows/`.
It records source-bound roots, nodes, edges, observation links and structural
proofs. The original workflow-selected `caller-inventory/v1` mode is unchanged.

Package bodies keep the source inventory's observation identity. Separate
`package-invocation` nodes represent calls with and without automatic lifecycle
hooks. An automatic `precheck` call does not acquire its own `preprecheck` hook;
an explicit `npm run precheck` call retains its lifecycle. Both contexts can
coexist without merging their effects. Cycles remain findings.

`estate-caller-reconciliation/v1` reports raw, structurally resolved and remaining
source findings separately. A source-level `opaque-executable` finding resolves
only when every observation producing that finding has a current machine proof.
The result independently retains unknown graph boundaries. Other finding codes
are never waived by this unit.

`source-adoption-migration/v1` creates an all-pending candidate and a complete
added/changed/unchanged/removed delta. Existing owner and disposition text remains
a proposal. Even previously reviewed unchanged rows return to pending. Removed
paths stay in the delta and historical ledger; nothing is deleted or retired.
The standalone historical ledger schema remains compatible, while the embedded
candidate schema permits only `review_status: pending`.

## What the proof establishes

A literal command proof requires the complete bounded command block, source
identity, argument digest, caller edges and lifecycle context. A dispatch proof
requires the entire supported four-line wrapper body, repository-root dispatch,
exact Python target, argument forwarding and every incoming/outgoing edge.
An appended command or substituted interpreter prevents that proof.

The supported shell text uses printable ASCII with ASCII tabs and newlines.
Non-shell Unicode whitespace and control separators are rejected. Raw commands,
parameters, tokens and source text are never copied to normalized evidence.

Only repository-local npm configuration absence is inspected. User/global npm
configuration, effective environment, actual working directory and tool identity
remain runtime/tool obligations. Source context accounting does not prove the
effective environment of a later execution.

A proved wrapper does not prove its Python child. A reached file does not prove
its implementation. Test names, directories, metadata, SHA pins and reviewed
labels are not classification or execution evidence. Workflow conditions,
unsupported contexts, unknown arguments, actions, arbitrary scripts and external
tools remain blocking. Package export/compiler proof is outside this unit.

## Freshness and admission boundary

`discover_estate_callers(root)` independently recollects the estate, observes
callers with component-safe file reads, checks sources/configuration again and
binds collector implementation bytes. Concurrent changes prevent structural
proofs. Collection limits produce explicit failure rather than partial success.

`reconcile_estate(root, inventory=None)` always recollects the caller graph. The
optional internal source snapshot must match that fresh collection. There is no
saved-graph, receipt-file, declaration or reviewed-allowlist input. Loaded helper
and schema bytes are bound before and after reconciliation. A self-hashed edited
JSON graph cannot be supplied as proof.

`source_coverage.compile_coverage(..., source_root=root)` consumes this fresh
reconciliation internally, removes only proved structural issues and adds all
remaining caller boundaries. Adoption and composition checks still apply.
Omitting `source_root` retains the original conservative compiler behavior.
The public command must supply the current root; it must not accept uploaded
reconciliation results as a shortcut.

## Existing wrapper integration contract

Integration belongs in the existing Operational Realization Gate wrapper; do
not create a second command framework. The intended additions are:

- `--estate-callers --source-root ROOT`: call `reconcile_estate(ROOT)` and emit
  normalized JSON. Return 1 while structural findings remain, otherwise 0 for
  this source-analysis scope only.
- `--adoption-migration --source-root ROOT --previous-adoption-ledger FILE`:
  independently discover ROOT, load the previous proposal, call
  `migrate_adoption(inventory, previous)`, and emit the pending candidate/delta.
  Return 1 because review remains pending. Never overwrite the previous ledger.
- Existing `--coverage`: pass `source_root` into the compiler, retaining every
  existing release/composition/adoption argument and check.

Reject conflicting mode flags and unsupported arguments before work. The existing
source-result consumer admits only a structurally accounted caller result after
fresh trusted recomputation, for `source-analysis` alone. Adoption migration is
an all-pending proposal and is deliberately rejected by the consumer. Release
and operation uses must fail regardless of either command's exit status. CLI
errors use a fixed closed safe envelope. Public CLI, consumer and canonical
verification are required before accepting this delivery unit.

## Focused verification

```bash
python3 -B -m unittest discover \
  -s scripts/04.deploy/release-control/discovery \
  -p test_estate_caller_inventory.py
python3 -B -m unittest discover \
  -s scripts/04.deploy/operational-realization-gate \
  -p test_estate_caller_coverage.py
python3 -B -m unittest discover \
  -s scripts/04.deploy/operational-realization-gate \
  -p test_adoption_migration.py
```

The mutations cover omitted roots, lifecycle/context confusion, appended wrapper
commands, missing children, stale source/helper/schema bindings, false test-only
labels, owner-review promotion and fabricated evidence. Compatibility verification
must include the existing selected-workflow caller suite and source compiler
suite, then the canonical wrapper and result-consumption checks after integration.

## Remaining delivery queue

After this unit, bind package exports to genuine compiler emission/source
relationships, extend supported implementation/import and workflow/action
semantics, and model the remaining provider-parameter, image and YAML boundaries.
Actual owners, retirement and compatibility decisions require their own reviewed
evidence. Reaching a file or classifying an intake row cannot supply that evidence.
Whole-estate closure and every later runtime/provider gate remain open.
