<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.plan.configuration-reason-selection
version: 2
status: active
created_on: "2026-11-01"
updated_on: "2026-11-02"
layer: 03.product
domain: configuration
disciplines: [architecture, security, agentic]
kind: plan
purpose: Complete DIAG-004 with shared reason names and fixed per-diagnostic selections while preserving every existing report contract.
portability: {class: source-only, targets: []}
used_by:
- id: shared.plan.diagnostics-backlog
  path: .agentic/shared/plans/implementation/diagnostics-backlog.md
-->
# Configuration reason selection — DIAG-004

The completed November 1 inventory below retains its historical file paths and
proof. The [subsequent folder refactor](configuration-ownership-and-loading.md#phase-b--responsibility-based-folders-and-config-reference-refactor)
moves setting/sourcing/error/diagnostic contracts to `contract/reporting/`, JSON
checking to `domain/validation/` and reporting operations to `domain/reporting/`.
No reason selections or retained definition versions change in that refactor.

## Authority, decisions and invariants

User authorised implementation. Inventory started 2026-11-01T23:42:33+00:00
(Europe/Dublin). Do not create a goal, move files, install dependencies or run
deployments/cloud operations. Retiring kanbien-platform runtime/deployment work
stays excluded; unchanged declarations may be read by the existing exporter.

Add configReasonNames, a frozen named collection of the existing twelve general
configuration reason strings, to Core's existing setting-issues contract. Derive
ConfigIssueReason from its values. Retain the existing two tuple exports with
their exact eight/twelve entries and order as fixed compatibility surfaces;
do not add a third progressively larger global list or freeze/change mutation
semantics of the old runtime arrays. Only the new named collection grows.

Platform's optional reasons argument retains an explicit private v1 selection,
not either exported compatibility tuple or Object.values of all shared names.
Core-server supplies capability-owned explicit selections to its existing
configuration/IAM/administrator/relationship definitions. Existing codes,
versions, enum order, fields, type union and accepted inputs remain unchanged.
Custom capability reasons remain supported; unrelated worker/provider reasons
are not moved into a global Core bucket. New reason acceptance by an existing
diagnostic requires a new definition version retaining the old definition;
the existing Core defineDiagnostic supports that, so no extra builder API is
needed for this refactor.

## Whole-repository discovery and file-by-file closure inventory

Exact-name/builder discovery covered packages, Platform, apps/products, infra,
scripts and .agentic, excluding Git/dependencies/build caches from searching.
Historical sessions/course snapshots were also classified separately rather
than rewritten. Indirect catalog assembly, generated exports, parser/selector
and task/readiness/startup consumers were traced through their existing owners.

| File or connected path | Decision and proving boundary |
| --- | --- |
| packages/core/src/config/contract/setting-issues.ts | Add named collection and derive type; retain exact compatibility tuples. Core diagnostic runtime/type fixtures. |
| packages/core/src/config/index.ts | Add only named-collection export; preserve all existing names. Public export/type/README checks. |
| packages/core/src/config/domain/json-object.ts | No body change: type-only consumer retains the same twelve-string union and exact emitted reasons. Core JSON/diagnostic tests. |
| packages/core/src/config/contract/diagnostics.ts and packages/core/src/diagnostic-catalog.ts | No change: independently explicit Core definitions/catalog assembly, not the growing list. Export byte check. |
| platform/config/src/diagnostics.ts | Bind fixed private compatibility selection; custom arguments/results remain supported. Real compiled helper injected with grown-name/legacy-array counterexamples. |
| platform/config/src/index.ts | Existing re-exports remain valid; no new Platform public API. Type/runtime and catalog checks. |
| platform/config/tests/platform-config-runtime.test.ts | Replace normal extended-list use with explicit selection; keep intentional legacy/default tests and add real-helper growth counterexample. |
| platform/config/tests/platform-config-types.test.ts | Prove named reasons and existing custom/default calls remain type compatible; relationship declarations unchanged. |
| packages/core/tests/diagnostic-record-runtime.test.ts | Pin both legacy tuples, new collection/immutability and retained/new-version parsing. |
| packages/core/tests/config-types.test.ts | Named collection/type readonly and unknown-name counterexamples. |
| platform/adapters/aws/persistence/postgresql/src/config.ts | No body change: ConfigIssueReason union is unchanged; numeric/source classification stays exact. PostgreSQL type check and existing target cases. |
| platform/adapters/aws/persistence/postgresql/src/credentials.ts | No body change: same union and actual username/password predicates. Target credential fixture and adapter types. |
| infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts | Explicit local v1 selections for existing definitions, with exact historical enum contents/order. Actual target fixture/catalog export. |
| platform/workers/src/configuration-diagnostics.ts | No change: already supplies a capability-owned explicit closed selection, including reasons not general Core config meanings. Worker catalog bytes/real parser. |
| infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.ts | No change: explicit custom selection and retained public builder compatibility. Export compilation/parsing only; no retiring-target runtime/deployment qualification. |
| scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs | Add grown-name injection against actual compiled target and literal published catalog; retain all actual caller/credential/source/context fixtures. |
| scripts/repo/diagnostic-coverage/smoke-test.py | Extend existing compatibility test for enum widening and bounded whole-growing-list regression; run focused configuration/IAM/credentials/relationship TS/Python reader cases. |
| scripts/repo/diagnostic-coverage/compatibility.mjs | Unchanged preservation predicate; do not weaken it. Focused widening/version tests exercise it. |
| scripts/repo/diagnostic-coverage/export-catalogs.mjs and tsconfig.json | No implementation changes expected. Compile then --check only; actual exporter checks all selected downstream catalogs. |
| scripts/repo/diagnostic-coverage/runtime_contract.py and deployment task readers | No change: generated selected definitions remain identical. Existing literal cross-language/task cases prove agreement. |
| All seventeen */contracts/*diagnostics*.json files | Must remain byte-for-byte identical. No snapshot refresh/new production reason/version. |
| packages/core/src/config/README.md | Explain single named vocabulary, fixed compatibility surfaces, per-version selections and updated public export count/type notation. Use README-writing skill. |
| Shared diagnostic standard/workflow | Canonical evolution rule distinguishes adding a name from widening an existing identity. No new harness vocabulary/AGENTS duplication. |
| scripts/repo/diagnostic-coverage/reviews.v1.json | Refresh only reviewed changed-source owners; preserve adoption statuses and remaining debt. |
| Historical architecture plan, lessons and session evidence | Retain as dated structural/snapshot history, not current vocabulary guidance. Update backlog/session outcomes only. |

## Connected implementation and proof sequence

Finish the connected source, tests, docs and source review before final focused
proof. Use fixture-only future names rather than inventing a new production
reason. Verify fixed defaults and actual target selections do not change when
the imported named collection and compatibility lists grow in the fixture.
Replacing an explicit selection with the entire collection must fail exact
definition/canonical compatibility assertions.

Focused proof: Core type check and diagnostic/config runtime files; Platform
config type check/runtime file; PostgreSQL types for unchanged union consumers;
catalog export compilation and existing --check (never refresh); selected
compatibility and configuration/IAM/credential/relationship reader tests; actual
target configuration fixture using its existing composition build and payload preparation. Check metadata,
links, source-matched adoption and unchanged catalog hashes. No full runtime or
selector aggregate, container, cloud, deployment or dormant-RAG work; broader
integration remains at the stable batch boundary under user direction.

## Outcome

Completed locally 2026-11-01. All inventory rows above are reconciled: changed
runtime owners are Core's contract/public export, Platform's fixed defaults and
core-server's explicit selections. Tests, harness guidance and README are updated.
The type-only JSON/PostgreSQL consumers retain the identical twelve-string type
and actual emitted reasons. Existing explicit worker/retiring-target declarations,
catalog assembly, exporter, compatibility checker and readers need no source
change: the generated contracts and literal reader proofs below establish why.
Historical architecture/teaching/session snapshots remain dated history.

Passing focused proof (not the full registered aggregates):

- Core: tsc -p packages/core/tsconfig.check.json; tsc -p
  packages/core/tsconfig.runtime-test.json; diagnostic-record-runtime.test.js and
  config-runtime.test.js in .cache/packages-core-runtime/tests. Pins both old
  tuples, new frozen names/type, old/new-version records and actual JSON checks.
- Platform: tsc -p platform/config/tsconfig.check.json; tsc -p
  platform/config/tsconfig.runtime-test.json; compiled platform-config-runtime
  fixture. Actual helper injection grows the shared names AND old tuples without
  changing default or relationship definitions; a new explicit identity accepts
  the fixture-only reason. Custom capability reasons and public defaults remain.
- PostgreSQL: tsc -p platform/adapters/aws/persistence/postgresql/tsconfig.check.json.
  Its value/credential runtime predicates are unchanged; the actual target fixture
  exercises their existing accepted/rejected paths rather than only helper mocks.
- Catalogs: tsc -p scripts/repo/diagnostic-coverage/tsconfig.json; existing
  export-catalogs.mjs --compiled-root .cache/diagnostic-catalog-export --check
  passed. Independently compared all seventeen files to pre-edit SHA-256 values:
  byte-for-byte unchanged, with no generated output refresh or weakened guard.
- Target: existing composition build.sh --out-dir <temporary>/compiled, existing
  build-core-server-persistence-image/prepare-runtime.mjs --compiled-root, then
  configuration-test.mjs with host NODE_PATH. Passed all 561 existing pre-pool
  rejected-entrypoint cases, plus growth injection against the actual target and
  literal published catalog. No database, Docker or cloud call was needed.
- ReaderTests: reason_growth_requires_explicit_selection_and_a_new_version,
  committed_versions_cannot_be_changed_or_removed,
  iam_diagnostics_survive_existing_task_readers,
  administrator_credentials_survive_reader_without_disclosure,
  administration_relationship_records_survive_strict_readers,
  real_typescript_parser_and_python_agree. All six passed in 2.268 seconds.
- Existing artifact checker passed six changed governed headers. README proof
  passed 61 links/anchors, 12 owning-file walkthroughs and all 44 public sections.
  Source-matched diagnostic adoption passed with no findings. Refreshed exactly
  four changed runtime hashes across their three existing owners; retained all
  existing statuses and debt. Scoped whitespace proof passed.

No production name/code/version, input/output behavior or public export was
removed or widened. No diagnostic generated catalog changed. Guidance remains in
the existing shared standard/workflow, not README policy or a new registry.
Broader integration stays at the user-selected stable batch boundary; direct
focused passes are not represented as aggregate receipts or live deployment proof.

## Time journal and effectiveness

- 23:42:33 UTC: inventory started; examined all direct and indirect consumers,
  compatibility behavior and existing tests before source edits.
- By 23:50:35 UTC: connected implementation and fixture changes drafted;
  exploratory Platform type check passed. Completed canonical evolution guidance
  and the bounded README update before the final runtime pass.
- By 23:53:08 UTC: five independent focused groups confirmed passed: Core,
  Platform, PostgreSQL types, catalog export and real target configuration.
  Builds ran concurrently; these are observed completion times, not claimed
  per-process durations. Source review/hash refresh happened before adoption.
- By 23:53:44 UTC: six literal/compatibility reader tests and metadata, catalog
  hashes, README and whitespace proof confirmed passed. Backlog/session closure
  records follow; no runtime inputs change during closure.
- Rework: one generated multi-hunk patch was rejected atomically because of an
  out-of-order redundant context hunk; removed it and applied the intended patch.
  No runtime test failed and no snapshot was regenerated. Tool output from the
  target/adoption commands was larger than useful; future runs should capture
  output and print the verdict/last summary instead of entire reports.
- Bounded scope avoided broad suites, runtime/deployment work for the retiring
  target and speculative changes to type-only consumers. Retained old lists
  deliberately for public compatibility; they are not the future extension path.
