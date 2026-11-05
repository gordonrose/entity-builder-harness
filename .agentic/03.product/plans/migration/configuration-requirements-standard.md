<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.migration.configuration-requirements-standard
version: 2
status: active
created_on: "2026-11-01"
updated_on: "2026-11-04"
layer: 03.product
domain: configuration
disciplines: [architecture, agentic]
kind: migration-plan
purpose: Convert legacy configuration requirements into one canonical product standard without changing runtime behaviour.
portability: {class: source-only, targets: []}
used_by:
- id: shared.plan.diagnostics-backlog
  path: .agentic/shared/plans/implementation/diagnostics-backlog.md
-->
# Configuration requirements standard migration

## Authority and boundaries

The user approved DIAG-002, specifically using an existing artifact type,
`standard`, not a new rules document type or rules namespace. Started
2026-11-01T23:00:46+00:00 (Europe/Dublin). Preserve all five requirement IDs and
their must/must-not clauses, guidance, scope and provenance. Presentation,
document identity, metadata and the self-location statement change explicitly.
This does not implement DIAG-003, migrate other rulesets, change runtime code,
resume a goal, install dependencies, commit or run cloud/container operations.

## Mapping and compatibility

- Old: `docs/03.product/rules/platform/concerns/config-runtime-settings.yml`.
- New: `.agentic/03.product/standards/config-runtime-settings.md`.
- Old metadata ID: `harness.architecture.rules.concerns.config-runtime-settings`.
- New metadata ID: `product.standard.config-runtime-settings`.
- Preserve the five `config-runtime-settings.*` requirement IDs.
- Compatibility: `pointer`. The old YAML becomes a deprecated human-readable
  pointer with no rules body and no promise that old rulebook parsers can use it
  as a ruleset. It retains its historical metadata identity only for the pointer.
  Current consumers must point at the new standard.

## Reference inventory and planner evidence

Ran the existing plan-artifact-path-migration.sh with the exact old/new paths
before changing references. It reported old_exists=yes, new_exists=no and 71
old-path references, including session history. Its unbounded historical-line
output is not duplicated here. A bounded exact-path search corroborated the
following buckets; counts are discovery evidence, not semantic adoption proof.

| Bucket | Treatment |
| --- | --- |
| Manifest | Register the new document under standards; remove the old concern-ruleset entry. |
| Product implementation workflow | Link the standard for configuration work and identify remaining docs rules as legacy. |
| Product layer README | List the new standard in the existing source-of-truth index. |
| Document-placement standard | Route authoritative expectations to standards and ordered procedures to workflows; docs explain them. No new document category. |
| Check catalog and repository-contract tests | Preserve diagnostic selection for the new location; add current-owner and stale-binding counterexamples. |
| Core README and infra related-reference | Link the new standard, without changing runtime or deployment policy. |
| Teaching course | Update current-source links and add a migration note; retain original file markers, snapshot hashes and before/after evidence. |
| Harness rulebook state | Update current artifact locations/classification; retain historical creation notes. |
| Dormant RAG policy, recognition sources and prototype map | Retain as dormant debt. The pointer is not parser compatibility; activation requires migration/rebuild under separate authority. |
| Derivation/retirement reports, session history and backlog background | Preserve historical evidence. |

The general migration checker needs --allow-active-old-path for this approved
pointer and retained evidence; that flag alone does not establish correctness.
Focused tests separately reject the old path in current manifest/catalog owners.

## Planned changes and gates

Finish canonical standard/pointer and all connected references before tests.
Use the existing repository_contracts_test.py owner, reached through the retained
smoke-test.py focused unittest interface. Planned cases: canonical standard and
pointer/manifest/workflow ownership, rejection of a deliberately stale manifest,
and diagnostic selection with a stale-catalog counterexample. Run only those
cases plus the existing affected diagnostic-selection case. Compare all five
requirements mechanically against the captured pre-migration document.

<!-- deterministic-check: allow reason="This bounded migration plan selects existing automated gates; deciding which retained references are intentional requires human review, not another orchestration script." -->
Then run scoped metadata/YAML/link checks and the existing migration checker
with --plan and --allow-active-old-path. Review the retained-reference inventory.
No broad selector regression, package runtime, payload, dormant RAG or deployment
checks are needed here; broader integration proof stays at the stable batch
boundary as directed by the user. Direct focused tests are not registered-suite
receipts. Finish with dated backlog/session outcomes, not another broad pass.

## Recovery and ADR disposition

No deletion or Git operation is planned. Preserve the original structured body
in the in-memory conversion baseline until the preservation check passes; Git
and the historical course retain earlier evidence. If conversion fails, repair
the new document/pointer from that baseline without discarding unrelated work.
This applies the established standard type and owner layer rather than creating
a namespace or bootstrap promise, so no additional ADR is needed.

## Outcome

Completed 2026-11-01. The canonical artifact is an active standard; the old YAML
is a deprecated pointer, not a second requirements body. All five requirement
IDs, titles, summaries, guidance and 35 normative clauses passed comparison with
the pre-conversion baseline. No runtime source or diagnostic catalog changed.

Actual focused proof:

- Existing smoke-test.py focused interface: new ownership and selector-binding
  cases plus test_actual_diagnostic_paths_select_focused_checks all passed
  (three tests, 109.109 seconds). The two new cases passed again after the
  placement-guidance assertions were added (0.324 seconds).
- Metadata headers passed for 14 affected artifacts; YAML parsing, whitespace,
  balanced Markdown fences, all 89 local links/anchors across seven guidance
  documents and the changed course-index current-source link passed.
- Existing check-artifact-path-migration.sh passed in 7.328 seconds with this
  plan and the approved pointer allowance. Retained exact-path references were
  reviewed: historical coverage note, course snapshot/index labels, negative
  test literals, backlog/plan evidence and dormant RAG records. Current manifest,
  workflow and check-catalog owners no longer bind to the legacy path.

The first metadata pass rejected a missing deprecated_on date on the pointer;
the date was supplied and the full scoped header check passed. No check was
weakened to accept it. No full selector regression, product runtime, image,
cloud, deployment, installation or dormant RAG operation ran. Broader integration
regression remains deferred to the stable batch boundary. This does not close
DIAG-003's runtime/adoption policy gaps or claim old parser compatibility.
