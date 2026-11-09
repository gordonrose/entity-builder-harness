<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.migration.core-shared-time-tests
version: 2
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: testing
disciplines: [agentic, architecture]
kind: migration-plan
purpose: Extract Core shared time tests by capability and proof type while preserving cases and runner failure semantics.
portability: {class: source-only, targets: []}
used_by:
- id: product.tests.readme
  path: .agentic/03.product/tests/README.md
-->
# Core shared time test layout

This records the earlier time pilot. File references now resolve to the current
locations after the [coordinated migration](product-test-layout.md); statements
about the original mixed fixture and pilot verification describe that earlier
stage, not the current contents of the result-only files.

## Scope and compatibility

Apply the approved capability/theme/test-type layout to time only. Extract
date parsing/conversion, fixed-clock and request-context runtime cases from
`packages/core/tests/shared/contract/unit/results-runtime.test.ts` into
`packages/core/tests/shared/time/unit/{date-time,clock,request-context}-runtime.test.ts`.
Extract time/clock/context compile-pass and compile-fail cases from
`packages/core/tests/shared/contract/type-level/results-types.test.ts` into
`packages/core/tests/shared/time/type-level/time-types.test.ts`.

The two source files remain executable for their remaining identity, JSON,
message, result and UUID cases. Compatibility choice: retained source paths
with comments pointing to the extracted tests; no forwarding imports that
would execute the same assertions twice. This is a section extraction, not
retirement of either file. No contract cases or empty contract folder are added.

Before editing, the migration planners were started for the runtime source to
the new date-time path, and the type source to the new type-level path. The
initial observations establish both sources present and both targets absent.
Active consumers are the Core runner/compiler, shared README and shared
diagnostic-review test references. Historical session references remain intact.
Full-path reference scans are supplemented by the README's relative links.

## Implementation and proof owners

- Add the product layout standard and link it from the testing index. The
  shared taxonomy still owns type IDs; `type-level/` spells its `type_level`
  test type on disk, not a new taxonomy type.
- Make the existing Core runner discover source runtime tests recursively and
  map each to its compiled counterpart. Retain deterministic order, child
  failure status, fail-fast behaviour and rejection of zero runtime tests.
  Ignore stale compiled-only files and never execute type-level fixtures.
  Missing compiled output must fail rather than silently omit a source case.
- Extend runtime compiler inclusion to nested runtime tests. The existing
  check compiler already includes nested type fixtures and remains unchanged.
- Add disposable runner unit regressions under `tests/test-infrastructure/unit/`, executed
  by the same recursive runner. They exercise flat/nested discovery, ordering,
  stale-output exclusion, missing output, no tests and child failure propagation.
- Preserve existing shared diagnostic review status, sources and hashes. Add
  extracted test references to its existing test list without upgrading adoption.
  All changed executable files are test infrastructure under `tests/`, excluded
  from runtime diagnostic adoption; no operational diagnostic vocabulary changes.

No runtime package implementation, public API, dependency, npm command, Platform
or app test folder, cloud resource or deployment configuration changes.

## Validation and recovery

Before extraction, capture all 37 assertion call expressions and 11 negative
type expectations from the two shared test files. Compare their combined
multisets with the retained plus extracted files after moving; review fixture
and import dependencies as well. Runtime tables must retain all ten input rows.

Run the two migration checks with this plan and `--allow-active-old-path` for
the retained-source pointers. Validate metadata, links, whitespace and the
selector impact plan. Run focused runner regressions, then the registered
`core-runtime` unit on stable inputs. Type checking must include the extracted
negative fixtures; runtime proof must use current compilation, not cached JS.
Report the existing feature diagnostic-review debt separately from this slice.

Recovery moves only the extracted statements back into the retained source
files, restores their imports/references and the runner/compiler discovery,
and removes only this slice's files. Use the pre-edit content and assertion
inventory, preserve unrelated edits and do not reset the worktree or delete
the shared cache. Old compiled files are harmless because discovery is source-led.

ADR disposition: no ADR needed for this bounded internal test-layout convention;
it changes no product ownership layer, public namespace or compatibility promise.
No commit is authorised. Validation outcomes are recorded below after execution.

## Results

- Initial planners passed: runtime source had 13 full-path references and type
  source 12; the two destination paths had zero. The only active full-path
  consumer was the existing diagnostic review; other matches were session
  history. Relative README links were reviewed separately. Sources remain
  supported for non-time cases, and their diagnostic references remain valid.
- Assertion multiset comparison passed: all 37 original assertion expressions
  and all 11 negative type expectations remain across retained/extracted files.
  The ten-row date tables and bodies were preserved exactly. Local imports,
  fixture dependencies and type-only exclusion were reviewed explicitly.
- Both path migration checks passed with this plan and retained-source
  compatibility. Three artifact headers, 50 local document links/metadata
  consumers, JavaScript syntax and whitespace checks passed.
- Focused current-source compilation and five disposable runner fixture groups
  passed. Final registered `core-runtime` executed and passed with no findings;
  this includes Core type checks, recursive runtime compilation/execution and
  boundary checks. It was not a reused receipt.
- The impact selector plan passed with no planning findings. Broader selected
  integration/container/provider/acceptance obligations were not executed or
  claimed complete. The structural diagnostic scan still reports the same 23
  pre-existing unreviewed entity-smoke/product sources and no Core test findings.
  No source hashes or diagnostic adoption status were upgraded.
- Remaining Core groups and Platform/app layouts are intentionally unmigrated.
  No production code, npm command, external environment or cloud state changed.

## Follow-up: explicit test-infrastructure name

User-approved rename: `packages/core/tests/testing` becomes
`packages/core/tests/test-infrastructure`. Retire the old folder with no alias
or forwarding wrapper. The single runner unit fixture moves byte-for-byte;
the recursive compiler and source-led runner already support the destination.
No imports, test semantics, runner code, configuration or runtime diagnostics
change. Update this plan's active path and the shared README's relative link;
retain historical session notes. No public namespace or ADR change is needed.

The path planner runs before the move; a bounded relative-path search supplements
its full-path inventory. Validate byte identity, absence of active old references,
the existing migration checker, metadata, links and whitespace, and the registered
Core check. Recovery moves the same file back and restores only these pointers;
no cache cleanup, source hash refresh, commit or unrelated edit is authorised.

<!-- deterministic-check: allow reason="historical rename results report completed verification, not a new executable condition" -->
Rename results: source file SHA-256 is unchanged; the old empty directories
were removed, the new path exists, and migration validation found no active
old full-path references outside this plan. All 29 shared README links, the
plan header and whitespace passed. The registered `core-runtime` check executed
and passed with no findings, including the renamed runner regression. This
does not change the wider feature diagnostic debt or imply deployment proof.
