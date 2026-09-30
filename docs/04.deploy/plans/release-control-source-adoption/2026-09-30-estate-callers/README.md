<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.review.release-control.estate-callers.2026-09-30
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record fresh aggregate caller proof, pending adoption migration and explicit unresolved boundaries.
portability: {class: internal, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Aggregate caller coverage — acceptance record

Status: accepted as a source-only delivery unit. Focused, compatibility and
independent public-boundary review passed. Exact same-source public outputs
matched independent recomputation. Canonical clean verification passed 1,645
tests in 46 suites and 56 metadata headers.

The existing realization gate now aggregates all root package command and workflow
callers. Complete literal command bodies and dispatch wrappers have source-bound
structural proofs. Npm lifecycle contexts remain distinct; a wrapper does not
prove the Python child it invokes. Existing workflow-selected caller mode remains
compatible. Existing `--coverage` recollects and consumes this proof internally.

The [inventory](source-inventory.json), [graph](caller-graph.json),
[reconciliation](reconciliation-result.json), [migration result](adoption-migration-result.json)
and [candidate](adoption-candidate.json) share one unchanged source snapshot.
The graph has 175 roots, 602 nodes and 522 edges, with 169 literal command-body
proofs and 19 complete dispatch-wrapper proofs. Source findings are partitioned:
240 raw, exactly 20 structurally resolved, 220 remaining. The additional 350 graph
boundary findings identify a different scope and must not be added to or confused
with the source-file finding count. Every unresolved implementation/tool/action
boundary stays blocking; this is not whole-estate closure.

The current scan covers 403 sources. Compared with the original 273-row ledger,
the new proposal has 130 added, 21 changed, 252 unchanged and zero removed rows.
All 403 current rows are pending; unchanged owner/disposition text is only a
proposal. Historical ledger bytes are unchanged. No source was retired, deleted,
excluded or given owner approval by this unit.

Both public modes returned exit 1 with empty stderr, as required for the actual
unresolved source graph and pending review proposal. Their outputs exactly match
independent fresh recomputation. A complete synthetic fixture can return source
analysis success; every release, operation and qualification permission remains
blocked. The common consumer accepts an accounted structural result only after
fresh trusted recomputation and full closed-schema checks. Adoption migration is
explicitly unconsumable as a completed receipt, even after a self-hash update.
Nested caller evidence in an existing coverage receipt requires matching inventory
identity and an accounted structural result. Existing legacy internal receipts
retain their previous checks.

Focused checks: 66 collector/reconciliation/migration tests; 24 public CLI tests;
45 consumer tests; 19 consumer CLI tests. The latter two include pre-existing
compatibility cases. Existing source coverage passed 34 tests and selected-workflow
caller collection passed 31. The verification summary records exact identities;
combined canonical acceptance passed with the frozen implementation.

The initial scratch reports came from different parent snapshots and were not
accepted. These retained reports were regenerated together after the final CLI/schema
hardening and registry correction. The earlier same-source attempt remains
preserved outside Git; these final documents share the new frozen source identity.
No raw command text, credentials, logs or private scratch stores are retained.

Next: finish finite-engine interruption reconciliation, then source coverage of
actual package-export/compiler relationships and remaining implementation/action
semantics. Ownership/retirement review, production artifact evidence, AWS stores
and adapters, orchestration and approved target qualification remain open.
