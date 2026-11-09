<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.migration.core-shared-uuid-tests
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: testing
disciplines: [agentic, architecture]
kind: migration-plan
purpose: Extract UUID unit and type-level tests and prove existing generation failure behaviour without changing runtime contracts.
portability: {class: source-only, targets: []}
used_by:
- id: product.tests.readme
  path: .agentic/03.product/tests/README.md
-->
# Core shared UUID test migration

This records the earlier UUID pilot. File references now resolve to the current
locations after the [coordinated migration](product-test-layout.md); statements
about retained mixed fixtures and pilot verification describe that earlier
stage, not the current contents of the result-only files.

## Scope and compatibility

Extract UUID parsing and real-system generation cases from
`packages/core/tests/shared/contract/unit/results-runtime.test.ts` into
`packages/core/tests/shared/uuid/unit/uuid-runtime.test.ts` and
`packages/core/tests/shared/uuid/unit/generator-runtime.test.ts`.
Extract UUID/generator type fixtures from
`packages/core/tests/shared/contract/type-level/results-types.test.ts` into
`packages/core/tests/shared/uuid/type-level/uuid-types.test.ts`.
Retain the source files for their other cases, with comments pointing to the
new groups. Compatibility is retained paths plus pointers, not forwarding
imports or duplicate execution. Run a planner for each extraction destination;
classify old references as active diagnostic review/README or session history.

The existing recursive runtime runner and compiler already cover these paths;
the no-emit checker already covers nested type fixtures. No runner, compiler,
npm command, dependency, production implementation, public export or diagnostic
definition changes. Type-level proofs do not require an empty contract folder.
The shared README and product testing index gain bounded explanatory links.

## Consumer and predicate inventory

The tests use the public shared barrel. Current implementations belong to
`packages/core/src/shared/uuid/{uuid,generator,contracts}.ts`; diagnostic
builders and versioned definitions remain in `shared/diagnostics/`. Capture
their hashes and existing test source before editing. Keep old parsing and
real-system success assertions and type fixtures, adding the following proof:

- Parsing: accepted versions 1–5, supported variants, case normalization,
  rejected empty/malformed/whitespace/version/variant values; exact
  `INVALID_UUID` error and `core.shared.uuid-invalid/v1` reason `invalid-format`.
- Generation success: controlled valid output reaches the caller normalized,
  with exactly one invocation. The existing real-system smoke remains, without
  claims about entropy or uniqueness.
- Invalid generated output: `UUID_GENERATION_FAILED`, exact
  `core.shared.uuid-generation-failed/v1` reason `generated-value-invalid`,
  preserved `core.shared.uuid-invalid/v1` companion, one invocation and no
  rejected value in structured records.
- Thrown dependency: same failure code, reason `generation-threw`, original
  cause identity and no retry. Missing/non-callable Crypto capability follows
  the same observed invocation-failure contract; do not invent an environment
  cause. Exact records exclude synthetic sensitive strings.
- Compile-time: accepted UUID results and synchronous generators; rejection
  of plain/null/other-branded values, invalid input and incorrect generator
  return shapes. Preserve old fixtures and result narrowing.

Temporarily replace the ambient Crypto property only inside synchronous test
fixtures; restore its exact original descriptor in `finally`, including when
an assertion throws. Cases run in an isolated script process. No production
injection interface or global runtime behaviour is changed for testability.

## Review and validation

<!-- deterministic-check: allow reason="review guidance combines existing executable proof with judgement about retained assertions and bounded counterexamples" -->
Run focused current-source compilation, UUID runtime cases and type checking.
Compare old assertion expressions/type fixtures with their retained/extracted
locations and review new cases against public source. Demonstrate bounded
diagnostic-reason/companion counterexamples in disposable compiled copies if
needed; never mutate the active source or compiled test inputs for this proof.

Update the existing partial shared review's test references and its specific
UUID failure-coverage debt after focused proof; retain status, source hashes
and unrelated debt. Test files remain excluded from runtime adoption. No
whole-shared or remote delivery adoption is implied.

Validate migration paths with this plan and `--allow-active-old-path` because
the mixed source files retain other cases. Check metadata, links, whitespace,
impact selection and the structural diagnostic census. Review stable inputs,
then run registered `core-runtime` for final Core type/runtime/boundary proof.
Record wider outstanding checks honestly; this is not AWS or commit readiness.

Recovery restores only the extracted source blocks/imports and corresponding
links/review entries from the captured pre-edit content, preserving other dirty
work. Do not reset the worktree, clean shared caches or create a compatibility
wrapper. ADR not required: no public contract or owner-layer boundary changes.

## Results

- All three reference planners passed before extraction; sources existed and
  destination files were absent. Scans found 14 runtime-source and 13 type-source
  full-path references including this plan and session history. The existing
  diagnostic review remains an active consumer of the retained mixed files;
  new test links supplement it. Relative README links were reviewed separately.
- Retention comparison passed for all 19 pre-existing assertion expressions in
  the mixed files, their five negative type expectations and the original UUID
  generator type fixture. The new groups add 24 assertion expressions, with
  table-driven version/variant and rejection cases and seven UUID negative
  type cases. All three UUID production file hashes are unchanged.
- Current-source focused Core type checking and both UUID runtime files passed.
  In disposable compiled copies, the baseline passed; mislabelling the invalid
  generation reason, dropping the validation companion and invoking generation
  twice each failed its owning assertion. Temporary copies were cleaned without
  editing active source or compiled inputs.
- Final registered `core-runtime` executed and passed with no findings. This
  includes recursive runtime discovery/execution, compile-pass/compile-fail type
  fixtures and Core boundary checks. All three retained-source migration checks,
  two artifact headers, 46 Markdown links and whitespace checks passed.
- Impact planning passed with no findings and selected the Core proof. Its wider
  integration/deployment obligations were not executed or claimed complete.
  The structural diagnostic census still reports the same 23 earlier feature/
  product findings and none in Core. The specific UUID failure-coverage gap is
  closed; the shared review remains partial and retains broader proof limits.
- README updates explain the new locations and exercised boundaries using the
  README skill. No runtime implementation, contract, diagnostic definition,
  source hash, runner, compiler, npm command, commit or cloud state changed.
