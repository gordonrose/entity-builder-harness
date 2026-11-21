<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.migration.owner-specific-test-requirements
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: testing
disciplines: [agentic, architecture]
kind: migration-plan
purpose: Relocate existing Core, Platform and app testing requirements without changing test execution.
portability: {class: source-only, targets: []}
used_by:
- id: product.tests.readme
  path: .agentic/03.product/tests/README.md
-->
# Owner-specific test requirements

## Approved scope

Extract the existing three product-layer test taxonomies, plus the existing
Platform and app testing rules, into owner-specific standards under
`.agentic/03.product/tests/`. Preserve every parsed taxonomy row and moved rule,
including rule IDs, categories, evidence requirements and substitute limits.
Retain the legacy layer files for their remaining architecture requirements,
with references to the canonical testing standards.

| Retained source file | Extracted content | Canonical destination |
| --- | --- | --- |
| `docs/03.product/rules/core/layers/packages-core.yml` | `test_taxonomy` | `.agentic/03.product/tests/core/standards/test-requirements.yml` |
| `docs/03.product/rules/platform/layers/platform.yml` | `test_taxonomy` and `platform.testing-proves-the-contract` | `.agentic/03.product/tests/platform/standards/test-requirements.yml` |
| `docs/03.product/rules/apps/layers/apps.yml` | `test_taxonomy` and `apps.tests-prove-wiring-and-contracts` | `.agentic/03.product/tests/app/standards/test-requirements.yml` |

## Compatibility and reference inventory

This is a section extraction, not retirement of the three source files.
Compatibility choice: retained source documents with pointers to the extracted
standards. Existing consumers of their other architecture rules retain those
paths. No executable YAML include or automatic pointer-following is claimed.

The existing taxonomy checker reads `layer_test_taxonomy_scope.layer_files`
from `docs/06.shared/rules/concerns/ci-quality.yml`. Replace only the three
product-owned entries with the new canonical files. All seven configured
taxonomy owners remain covered; vocabulary, shared policies and checker
implementation are unchanged. The checker stays dormant in ordinary checks.

Planner commands were started for each source/destination pair before edits:
`bash scripts/01.harness/plan-artifact-path-migration.sh <source> <destination>`.
The initial observations confirmed all three source paths exist and all three
destinations are absent. Reference-bucket outcomes and verification results are
recorded below after the scans finish.

The direct consumers to reconcile are the legacy layer references, shared CI
taxonomy scope and product governance index. Broader architecture/rule-pack,
bootstrap and historical references to the retained layer paths remain valid.
Dormant RAG provenance and generated recognition material are not regenerated.
New standards retain the corresponding source's portability declaration.

## Exclusions

No test source, fixture, runner, TypeScript configuration, npm command,
check-selector registration, CI hook, runtime code or deployment surface moves
or changes. Shared test vocabulary, diagnostic verification, change completion
and live deployment proof retain their existing owners. New test-writing rules
and actual test-folder migration are separate later slices.

This is documentation and requirement placement only: no executable predicate,
diagnostic vocabulary, mutation or reporter changes. No source-review hash
refresh is required for unchanged executable files.

## Validation and recovery

Compare parsed source/destination taxonomies and moved rule objects against
the pre-edit snapshot, prove those bodies are absent from their source files,
and compare all unrelated YAML fields and shared CI policies.
Run the existing taxonomy checker with its self-test explicitly; its configured
file-list change does not activate it in normal verification.
Validate affected metadata headers, file links and whitespace. Run the migration
checker for each source/destination pair with this plan and
`--allow-active-old-path`: retained architecture files intentionally have valid
active callers. Review pointers and section equivalence independently because
the path checker does not interpret YAML sections.

Recovery restores extracted sections and the three scope entries from the
pre-edit source or Git history, then removes only this slice's new standards
and index. Preserve unrelated uncommitted work; do not reset the worktree.

ADR disposition: no ADR needed. This adds a narrow home within the existing
product owner, retaining layer boundaries, source paths and bootstrap promises.
No commit or public export is part of this slice.

## Results

- Reference planners passed before source edits. Source-reference counts were
  Core 157, Platform 177 and app 97; each destination initially had zero
  references. Their workflow, script, architecture, history and other references
  remain valid through retained layer documents. The raw inventories include
  large historical evidence records; only the bounded disposition is retained
  here. No dormant retrieval or bootstrap pipeline was executed.
- Extracted 4 Core, 4 Platform and 5 app taxonomy rows. Parsed comparison with
  the pre-edit Git source passed for every row and both moved rule objects.
  Source files no longer contain these bodies. All unrelated parsed layer
  fields are unchanged apart from version and the new canonical reference.
- Shared CI vocabulary, categories, substitute limits and other policies match
  their original parsed values. Exactly three of seven scope paths changed.
- The existing taxonomy checker and its self-test passed before and after the
  extraction for all seven owners. No script implementation or automatic
  invocation was changed.
- All three migration checks passed with the documented retained-source
  compatibility option; destinations exist and active old-path callers remain
  intentional. README/plan links and standard consumer references passed.
- Ten affected artifact headers passed, as did whitespace. Self-review checked
  the complete source/destination diff and README against actual ownership:
  no new test-writing policy, runner behaviour or test-folder convention is
  claimed. Runtime suites are not required for this requirements-only move.
