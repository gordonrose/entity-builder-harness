<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.plan.core-module-architecture-config-proof
version: 5
status: active
created_on: "2026-11-01"
updated_on: "2026-11-02"
layer: 03.product
domain: architecture
disciplines: [architecture, security, agentic]
kind: implementation-plan
purpose: Record the approved Core config architecture, connected implementation and verification.
portability: {class: source-only, targets: []}
used_by:
- id: product.readme
  path: .agentic/03.product/README.md
-->
# Core module architecture: config proof

The original move maps below record the November 1 proof, not today's private
paths. The authorised [follow-on plan](configuration-ownership-and-loading.md#phase-b--responsibility-based-folders-and-config-reference-refactor)
groups report contracts under `contract/reporting/` and domain work under
`reading/`, `validation/` and `reporting/`. The exact catalogue assembly exception
now targets `config/contract/reporting/diagnostics.ts`; no broader private-import
permission is granted. Historical evidence below remains evidence of its inputs.

## Status, objective and approval boundary

Status: complete for this config architecture and consumer-context proof.
Section 5 records actual verification and its limits; this is not whole-branch
integration, container qualification or deployment approval.
Goal: prove a manageable Core module structure with distinct public exports,
contracts and capabilities, and prove that a real consumer supplies the context
needed to understand its failures. Make the responsibility guidance and
proportionate enforcement reusable for future Core, Platform, adapter and
entrypoint work. Config is the first proof, not authority to migrate all modules.

The existing [product architecture standard](../../standards/public-module-structure.md)
owns structure; the [safe diagnostic standard](../../../shared/standards/require-safe-diagnostic-record.md#context-and-consumer-obligations)
owns diagnostic quality. This plan maps their application, not competing rules
or another runtime manifest. Sections 1–4 below are prepared for review.
Section 5 records agreement and proof. On November 1 the user approved the exact
structural layout and then explicitly directed completion without further design
approval requests. This authorizes bounded choices needed to finish both tracks;
it does not authorize Git publication, installations, deployment or unrelated
backlog implementation. Final proof remains required.

Discovery baseline: 2026-11-01, recorded chat worktree on the October 27 branch.
Eight current TypeScript files expose 42 public names through config's index.
One additional file-level export, `readConfigSource`, is internal to the module.
There are 14 top-level private declarations and six named nested helper/method
locations accounted for below. Overload signatures count once, not as capabilities.

The previous DIAG-008 work already made the index export-only and added a
shared syntax checker. At this plan's discovery baseline, six registered focused
checks had passed but broader verification was incomplete, and a selector-fixture
review hash had become stale after lifecycle preparation. That historical proof
is preserved, not counted as proof of the new layout. Section 5 records the new
implementation's source-matched verification; the old broad goal was not reopened.

## Scope and non-goals

Track A, after layout approval, covers config internals, exact consumers affected
by path changes, its README, the existing module checker/Core boundary tests,
appropriate dependency fixtures and existing review/catalog bindings. Preserve
all public names, signatures, result/error shapes, accepted inputs, read/getter
counts, custom traversal semantics, diagnostic identities and report ordering.

Track B is a separately identified consumer-context proof using core-server
database startup configuration and its existing certificate-source read boundary.
Inventory existing context, report construction, preservation and delivery first;
then implement the bounded context path under the user's completion direction.
Reuse existing definitions; do not alter configuration results, diagnostic
record schemas or accepted configuration to resemble teaching examples.

The chat's illustrative `CONFIGURATION_FAILED`, `kind`, `affectedSettings` and
`notChecked` responses are teaching examples, not approved exports or report
schemas. Do not introduce them, convert thrown source failures to returned
failures, continue after a thrown read, or change collection limits merely to
match the examples. Preserve old result paths; where richer information is
needed, propose a compatible, explicitly owned reporting path and reader proof.

Do not implement DIAG-001's port constraint, new validators, Zod, provider
integrations, unrelated backlog items or other module migrations. DIAG-004's
reason-list redesign remains separate; any necessary dependency must be named
and approved before starting it. No mandatory transport, persistence folder,
service wrapper or module manifest. No dependency installation, Git staging,
commit/push, container/cloud/deployment operation is authorized by this plan.

## 1. Every public export and its responsibility

Paths in this section are relative to `packages/core/src/config/`.
The table maps the original flat-file baseline to implemented destinations.
All names stay available
through `@kanbien/core/config`; internal file exports are not automatically public.

| Baseline file / public name | Responsibility | Implemented owner |
| --- | --- | --- |
| types.ts: `EnvironmentName` | Description of checked environment-name text. | contract/types.ts |
| types.ts: `SecretReference` | Description of checked secret-reference text, not a secret value. | contract/types.ts |
| types.ts: `ConfigValue` | Supported simple supplied-value kinds. | contract/types.ts |
| types.ts: `ConfigRecord` | Named collection supplied by a caller. | contract/types.ts |
| types.ts: `ConfigErrorCode` | Existing outer reader/schema error identities. | contract/errors.ts |
| types.ts: `ConfigSource` | Interface for obtaining one named value. | contract/types.ts |
| types.ts: `ConfigSchema` | Caller-provided parse-operation interface. | contract/types.ts |
| types.ts: `ConfigError` | Existing returned failure representation. | contract/errors.ts |
| source.ts: `recordConfigSource` | Copy supplied values and expose name-based reads. | domain/source.ts |
| value-readers.ts: `configError` | Package caller-provided issue/diagnostic evidence into the existing error shape. | contract/errors.ts |
| value-readers.ts: `environmentName` | Check environment-name grammar and apply the existing type label. | domain/value-readers.ts |
| value-readers.ts: `secretReference` | Check provider-neutral reference grammar, without retrieving a secret. | domain/value-readers.ts |
| value-readers.ts: `requiredConfigValue` | Require one source value to be present. | domain/value-readers.ts |
| value-readers.ts: `optionalConfigValue` | Read an optional value without adding defaults. | domain/value-readers.ts |
| value-readers.ts: `stringConfigValue` | Require a supplied string, without trimming/conversion. | domain/value-readers.ts |
| value-readers.ts: `numberConfigValue` | Require an actual finite number, without text conversion. | domain/value-readers.ts |
| value-readers.ts: `booleanConfigValue` | Require an actual boolean; false remains present. | domain/value-readers.ts |
| issues.ts: `configIssueReasons` | Retained original shared reason names. | contract/setting-issues.ts |
| issues.ts: `configValueIssueReasons` | Existing extended list retained unchanged in track A; DIAG-004 owns its redesign. | contract/setting-issues.ts |
| issues.ts: `ConfigIssueReason` | Type permitting the existing combined names. | contract/setting-issues.ts |
| issues.ts: `ConfigSettingIssue` | Logical setting/reason report shape. | contract/setting-issues.ts |
| issues.ts: `ConfigCheckIssue` | Generic indexed report shape, not an automatic diagnosis. | contract/setting-issues.ts |
| issues.ts: `ConfigCheckFailure` | Collector report-list/overflow shape, not itself proof an operation failed. | contract/setting-issues.ts |
| issues.ts: `ConfigRelationshipIssue` | Failed must-differ comparison report shape. | contract/setting-issues.ts |
| issues.ts: `createConfigIssueCollector` | Validate/copy/collect reports already found by a caller. | domain/issue-collection.ts |
| schema.ts: `ConfigSettingRule` | Supported checking-instruction representation. | contract/types.ts |
| schema.ts: `ConfigSettingDefinition` | Logical name/source/rule instruction shape. | contract/types.ts |
| schema.ts: `ConfigSettingsFailure` | Ordinary declared-check failure representation. | contract/errors.ts |
| schema.ts: `ConfigSettingRelationship` | Declared must-differ instruction shape. | contract/types.ts |
| schema.ts: `ConfigSettingsRelationshipFailure` | Combined individual/comparison failure representation. | contract/errors.ts |
| schema.ts: `parseConfigJsonObject` | Interpret supplied JSON text as an object with value-safe reasons. | domain/json-object.ts |
| schema.ts: `validateConfigSettings` | Check declarations, read/validate values and compare valid participants. | domain/settings.ts |
| diagnostics.ts: `coreConfigPrimitiveDiagnostic` | Versioned permitted report for existing primitive failures. | contract/diagnostics.ts |
| diagnostics.ts: `CoreConfigReader` | Permitted reader classifications. | contract/diagnostics.ts |
| diagnostics.ts: `coreConfigSourceDiagnostic` | Versioned unknown-cause source invocation report. | contract/diagnostics.ts |
| diagnostics.ts: `coreConfigDeclarationDiagnostic` | Versioned invalid checking-instruction report. | contract/diagnostics.ts |
| diagnostics.ts: `coreConfigRelationshipDeclarationDiagnostic` | Versioned invalid comparison-instruction report. | contract/diagnostics.ts |
| diagnostics.ts: `coreConfigDiagnosticDefinitions` | Explicit collection of the four existing definitions. | contract/diagnostics.ts |
| diagnostics.ts: `coreConfigPrimitiveRecord` | Checked construction against its existing report definition. | contract/diagnostics.ts |
| diagnostics.ts: `coreConfigSourceRecord` | Checked construction of an observed source invocation failure. | contract/diagnostics.ts |
| source-observation.ts: `configSourceReadFailureReasons` | Existing provider-neutral source-read reason names; failed access does not diagnose contents. | contract/sourcing-issues.ts |
| source-observation.ts: `ConfigSourceReadFailureReason` | Type restricting those shared names. | contract/sourcing-issues.ts |

`index.ts` remains at its current public path and only changes re-export targets.
The 42 names above are the complete public inventory, including forwarded types.

### Every private helper and supporting declaration

| Current location / name | Responsibility and proposed treatment |
| --- | --- |
| source.ts: `readConfigSource` | Module-internal exported helper; domain/source.ts calls the supplied getter and attaches existing source evidence without changing thrown identity. Do not expose it publicly. |
| source.ts: returned `get` arrow | domain/source.ts reads the captured snapshot; remains part of recordConfigSource, not another service. |
| value-readers.ts: `readRequiredConfigValue` | domain/value-readers.ts checks presence after the shared read. |
| value-readers.ts: `missingConfigError` | contract/errors.ts constructs the existing known missing failure after the reader establishes absence; internal export only if needed. |
| value-readers.ts: `invalidConfigTypeError` | contract/errors.ts constructs the existing wrong-type/non-finite failure from reader-established evidence. |
| value-readers.ts: `invalidConfigValueError` | contract/errors.ts builds the legacy validation issue and optional diagnostic companion. |
| value-readers.ts: `configValueType` | Private contract/errors.ts helper describes actual kinds for legacy error parameters; does not choose acceptance policy. |
| value-readers.ts: `environmentNamePattern` | domain/value-readers.ts keeps the current spelling rule beside its actual check. |
| value-readers.ts: `secretReferencePattern` | domain/value-readers.ts keeps the current reference grammar beside its check. |
| schema.ts: `nativeDeclarationSome` | domain/settings.ts retains the native traversal identity used to avoid fabricated locations. |
| schema.ts: `applyDeclarationSome` | domain/settings.ts retains the captured Reflect.apply operation. |
| schema.ts: `declarationSome` | domain/settings.ts preserves the existing receiver/custom traversal semantics. |
| schema.ts: `declarationPosition` | domain/settings.ts permits positions only when supported by native traversal evidence. |
| schema.ts: local `observeDeclaration` | Stays inside validateConfigSettings; captures first established declaration failure. |
| schema.ts: local `observeRelationship` | Stays inside validateConfigSettings; captures first established comparison-declaration failure. |
| schema.ts: per-item `issue` arrow | Stays in domain/settings.ts's checking loop; appends that item's established problem in order. |
| schema.ts: `rejectDeclaration` | Stays in domain/settings.ts; rejects an invalid checking instruction with the existing error and diagnostic. |
| schema.ts: `rejectRelationshipDeclaration` | Stays in domain/settings.ts; same responsibility for invalid comparison instructions. |
| issues.ts: collector `add` method | domain/issue-collection.ts preserves shape checks, copied/frozen reports, ordering and the existing 32-report bound. |
| issues.ts: collector `finish` method | Same capability returns a frozen snapshot and explicit overflow, without closing/resetting the collector. |
| diagnostics.ts: `classification` | Private contract/diagnostics.ts fact shared by existing definitions; not new recovery policy. |

Anonymous traversal callbacks remain with the named operation they implement:
declaration identity mapping/checking, comparison identity/pair checking and issue
shape iteration. They are not new public capabilities or separate files. Temporary
loop variables and captured report buffers stay local to those operations.

## 2. Necessary splits and approved layout

Necessary splits: issues definitions versus report collection; schema declaration
types versus applying instructions versus JSON interpretation; returned-error
construction versus choosing whether an input is acceptable. Diagnostic definition
builders remain with their definitions because they enforce that representation,
not the truth of a caller's observation. Do not invent another reporting service.

```text
packages/core/src/config/
  index.ts
  README.md
  contract/
    types.ts                Shared input/source and checking instructions
    setting-issues.ts       Supplied-value/comparison problems and report shapes
    sourcing-issues.ts       Observations about failures obtaining information
    errors.ts               Existing returned failure types and construction
    diagnostics.ts          Four definitions and their checked constructors
  domain/
    source.ts               Snapshot source and shared invocation boundary
    value-readers.ts        Individual-value and named-reference checks
    settings.ts             Caller-declared checks and comparisons
    json-object.ts          Supplied JSON-object parsing
    issue-collection.ts     Bounded report collection
```

This is eleven TypeScript files rather than the current eight: three extra
cohesive owners, not a folder/file per function. No nested indexes are needed.
The two issue files answer different questions: what is wrong with information
obtained, versus why obtaining it failed. The errors file describes an operation's
returned failure using its existing representation; it is not a second sourcing
reason list. Keep the current legacy ValidationIssue-based errors distinct from
newer ConfigSettingIssue reports unless a separate compatible migration is agreed.

Capability split review: source owns snapshot access and the invocation boundary;
value-readers owns individual reads/naming checks; settings owns declaration
application and comparisons; JSON parsing is independently called by credential
loading; issue-collection is independently used by observability checking. These
are proposed cohesive groups, not mandatory names/counts for future modules.
The collector validates report shape but cannot establish its reason is true;
JSON parsing does not obtain the source or validate credential policy.

| Additional responsibility | Config applicability decision |
| --- | --- |
| Transport/HTTP mapping | Not applicable: callers invoke functions; concrete HTTP/queue translation stays outside Core. |
| Database persistence | Not applicable: no database operation; source.get is a supplied dependency, not Core-owned storage. |
| integration.ts/service wrapper | Track A needs none; track B may bind context through an existing construction path. Add a wrapper only for demonstrated connecting work. |
| Reference implementation folder | Not needed: recordConfigSource is an existing real capability, not a fake provider. Test substitutes stay in existing fixtures. |
| Diagnostics/privacy | Applicable through contract definitions and actual domain predicates; source failures remain unknown-cause observations. |
| Dependency/effect accounting | Applicable: supplied getters/custom methods can throw or have effects; retain exact invocation/receiver behavior. |
| Catalog registration | Existing package root diagnostic-catalog.ts selects definitions; config does not import that aggregate. |
| Generated contract export | Existing packages/core/contracts/diagnostics.v1.json remains derived and meaning-equivalent. No second editable schema. |
| Module manifest | Not needed: retain package.json public exports/dependencies, existing catalog and review owners. |
| Documentation and tests | Existing module README and Core/consumer fixtures, updated for actual implementation locations. |

## 3. Allowed dependencies and connected consumer changes

```text
Other modules -> config/index.ts -> selected contract and domain exports
                                    |
                         domain -> contract -> upstream Core foundations

No contract -> domain, no internal -> own index, no file-import cycles.
```

Contract types can use contract issue shapes. Error construction can use contract
types, diagnostic constructors and upstream Core validation helpers. Domain
readers can use domain/source plus contract errors/diagnostics/types. Domain
settings uses its contract types/reports and existing upstream diagnostic helpers.
JSON parsing and issue collection need their owning contracts, not source reading.

Avoid a type-only cycle when ConfigSchema in contract/types.ts references
ConfigError in contract/errors.ts. The error builders do not need a reverse
types.ts import: propose widening only their private/internal value-description
parameters (`invalidConfigTypeError` and `configValueType`) from ConfigValue to
unknown, retaining the existing guarded typeof/null/finite-number logic. This
is an explicit internal typing adjustment, not a changed public signature or
runtime check; include it in layout review and public compatibility proof.

Use existing supported upstream Core interfaces, including the public shared
export for attachCoreDiagnosticRecord, rather than new private reach-through.
Do not add Platform/provider, fs/environment, HTTP or application dependencies.
Do not infer that an injected getter is effect-free or rewrite its error policy.

The package's diagnostic-catalog.ts is one explicitly named assembly exception:
it may import config/contract/diagnostics directly to select pure definitions,
as it currently imports config/diagnostics. That does not permit another module
to import config's private domain files or make config import the aggregate.
Changing the shared diagnostics framework itself is not presumed necessary.
Identify an actual missing mechanism and obtain the required change agreement
before expanding track B into that shared framework.

### Track B: context ownership and actual reporting path

At the final internal reporting boundary, account for operation, logical item or
source, phase, observed condition, established effect/outcome, remaining unknowns
and the next permitted investigation where applicable. Not every fact belongs
in every Core record: names can be defined by its catalog, supplied in validated
Platform context, or resolved through a code-owned investigation declaration.
Do not add a generic arbitrary-text context bag or a second schema registry.

| Owner | Existing source and responsibility |
| --- | --- |
| Shared mechanism | packages/core/src/diagnostics/{definition,record,schema}.ts: closed definitions and construction/parsing. Do not teach it target configuration. |
| Config contract/capability | The mapped config files own reusable reasons/report shapes and the checks that establish them, without startup, filesystem or provider selection. |
| Reusable configuration reporting | platform/config/src/diagnostics.ts: declared setting/source selections, bounded reports and relationship evidence. |
| Reporting contract | platform/contracts/src/diagnostics.ts: required capability/operation/stage context and registered catalogs; currently operation/capability are strings, not per-operation allowed selections. |
| Internal delivery | platform/observability/src/diagnostics.ts and diagnostic-log.ts: validation and logger delivery with failure isolation; syntax-valid context does not establish truthful context. |
| Concrete binding/observation | kanbien-core-server-persistence-configuration.ts: current logical names, environment binding, certificate read observation and diagnostic projection. Provider-neutral construction belongs upstream; actual OS read evidence is interpreted at this existing read boundary. |
| Startup consumer | kanbien-core-server-persistence.main.ts: calls configuration, IAM and certificate checks before pool construction, and startupFailed supplies the existing startup output. Check this early path, not only the later Platform reporter. |

Proposed proof boundary: database startup preparation, including its existing
source-read branch. Preserve IAM/TLS policy, call order, exit behavior and pool
construction/cleanup. Do not migrate other startup/task programs except exact
consumers required by an agreed shared interface change; inventory them first.
Do not expand into the retiring kanbien-platform deployment target or live work.

Before track B coding, map each failure alternative to the required context,
its supplying owner and its actual reporting consumer. Required typed context
and runtime validation must reject omissions/inappropriate bindings where they
can be established; caller tests must catch a valid-looking but wrong identity
or stage. Bind fixed context once where useful, not on every ad-hoc report.
Inventory before proposing files: existing helpers may already suffice.

Current gaps to assess, not claims of newly passing proof:

- Core primitive reports identify reader/reason but not a named setting; target
  declared-setting reports already carry their logical setting identities.
- Generic source-threw evidence is unknown-cause; the target file reader can
  distinguish selected OS codes without retaining error text or actual paths.
- Platform validates reporting context shape/stage but not every operation's
  legitimate capability/operation/stage combination.
- Source exceptions preserve identity and stop work; there is no approved
  universal checked/notChecked result. Report only prevented checks actually
  established at the caller, without changing iteration or claiming completion.

Track B cannot be closed by merely matching these fields to a schema. Prove the
real caller's failure handling before dependent work and the report delivered
at startup. Reporting failure must preserve the business result and never replay
operations. Preserve profile opt-outs and public response boundaries.

### Harness and backlog reconciliation

The public-module standard owns responsibility/dependency separation. The shared
safe-diagnostic standard owns useful, truthful, safe context. Its coverage
workflow owns inventory, implementation/review and proof selection. AGENTS stays
a router; READMEs explain and link, not prescribe parallel requirements.

- DIAG-002 remains open: authoritative configuration requirements still have a
  legacy docs location. Record the needed harness-owner migration; do not amend
  that legacy ruleset or claim relocating it is part of this source rearrangement.
- DIAG-003 is extended with consumer context ownership, validated assembly,
  required interfaces and actual caller/delivery counterexamples. Track B proves
  one bounded use, not all of DIAG-003's repository-wide checking policy.
- DIAG-004 remains open: shared names and version-specific allowed selections
  are separate. Any changed fields/reasons need explicit compatibility handling;
  no global-list widening or inferred approval of example response formats.
- DIAG-008 records the earlier export-only extraction and historical six focused
  passes separately from this expanded architecture/context proof. Its original
  cleanup is now complete with the new source-matched proof in section 5 and
  the session journal; it is not authority to close DIAG-003 or unrelated work.
- DIAG-001 and DIAG-005–007 remain independent; no implementation is inferred.

### Current consumer inventory and disposition

- **Public callers unchanged:** Platform config/contracts/runtime/testing,
  server/worker startup, observability/CloudWatch config, PostgreSQL config and
  credentials/IAM, smoke app, and core-server configuration/IAM composition.
  Preserve their public imports and result handling; run their affected proof
  rather than edit them solely because implementation files moved.
- **Actual source-path change:** packages/core/src/diagnostic-catalog.ts.
  Update its explicit definition import; prove identical selected definitions
  and unchanged generated JSON, including old supported reader agreement.
- **Core tests:** config-runtime, config-types, diagnostic-record runtime/types,
  foundation-diagnostics runtime/types, compatibility canaries and
  core-boundaries.test.mjs. Preserve public imports; add assertions for the new
  dependency directions and sensitive-value/behavior preservation where missing.
- **Governance and tooling:** existing module checker and its fixtures/README,
  existing selector catalog and owning repository-contract fixtures, affected
  reviews.v1.json source paths/hashes/definition references, public structure
  standard and current task plan. Extend existing controls, not a parallel gate.
- **Human teaching links:** config README and the active course guide's current
  source links. Historical course snapshot paths/counts and earlier commit logs
  remain labelled history; do not rewrite snapshots to pretend the old layout
  never existed. Update a current-path link separately where appropriate.
- **No independent content change:** package.json exports, generated diagnostic
  JSON meanings, existing reason lists, target environment bindings, SQL, provider
  behavior, imported workbench tooling and dormant RAG material.

Repeat the source/reference census immediately before implementation. Classify
active references versus historical evidence; do not assume these examples cover
future files added after this proposal. At this baseline only index.ts is Git-
tracked among the eight current config files; it stays in place. The seven
untracked files contain recorded work and are not disposable. Do not delete any
until the approved destinations preserve their content and references. If any
path becomes committed before implementation, apply the owning path-migration
workflow/plan requirements; no commit permission is inferred from this goal.

## 4. Tests, workflow gates and time measurement

All commands below are planned after layout approval unless explicitly labelled
as observed evidence. Do not run broad suites to qualify this proposal's prose.

| Proof | Existing owner / planned assertion |
| --- | --- |
| Complete public interface | config-types.test.ts plus a 42-name before/after compiler export/signature comparison; retain overloads, brands, generics and old public imports. |
| Source/readers/errors | config-runtime.test.ts and foundation-diagnostics-runtime.test.ts: copy isolation; absent versus null/empty/0/false; finite numeric values without conversion; exact errors and same thrown identity/getter counts. |
| Declared checks | Same Core owners: declaration rejection before reads, text/integer grammar, all ordinary issues, valid-participant comparisons, error ordering and custom map/some behavior. |
| Collector/JSON | config-runtime.test.ts and diagnostic-record-runtime.test.ts: malformed/canary input, dense safe reports, frozen snapshots, existing bound/overflow and JSON reason distinctions. |
| Diagnostic meaning | foundation runtime/types and diagnostic-record runtime/types: exact code/version/detail, truthful unknown source cause, companions, raw/frozen thrown values and no native message/value leakage. |
| Caller preservation | platform/config tests, including evidence-runtime.test.ts, plus selected startup/composition consumers; preserve handling before dependent work. |
| Structure/dependencies | Existing module-structure fixtures and Core boundary test: accept intended edges; reject contract->domain, own-index back-import, new cycles, external private-domain access and index implementation. Explicit catalog import remains permitted. |
| Catalog/readers | Existing diagnostic-catalog-readers unit; no changed exported meaning, stale JSON or retired identity under the same version. |

Track B adds real-context proof, not replacement snapshots for the teaching
examples. In existing Core tests, cover single/multiple successful checks and
setting failures, preserved thrown reads and mixed established/prevented work
where current behavior supports it. Keep the old first-error/collection rules.
In Platform config's runtime/types and evidence-runtime tests, cover the agreed
required context, permitted operation bindings, exact upstream evidence and
rejected inappropriate/malformed context. Use existing contracts/observability
runtime and type tests only where those interfaces/delivery paths change.

In scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/
configuration-test.mjs and observability-runtime-test.mjs, exercise the actual
startup consumer with single/multiple setting failures, positively classified
and unclassified source failures, wrong-but-well-formed identity/stage, downstream
pool non-invocation and synthetic sensitive canaries. Extend the same fixture
owner for startup failure delivery, reporter failure isolation and any approved
context-binding API. Confirm the exact test location during the track B contract
review; these are planned assertions, not existing or newly passed evidence.

Focus by changed owner: module-index-structure and its regression, core-runtime,
platform-config-runtime and diagnostic-catalog-readers for track A; add
platform-contracts-runtime, platform-observability-runtime and persistence-composition
for track B when affected. Use the existing check catalog's prerequisites and
exact final impact plan for target/payload obligations, not an invented aggregate.
If a required fixture lacks a registered unit, identify the gap before coding
and extend the existing catalog/owning fixture rather than bypass the runner.

Required bounded counterexamples: reintroducing implementation in the index;
a contract importing domain; a capability importing its own index; another module
reaching into private config domain; removal/renaming of a public export; altered
missing/non-finite classification or custom traversal/read count; leaked synthetic
secret text. Each must fail its specific assertion, not merely change a snapshot.
Dependency checks do not prove that a file has a useful responsibility; record
that architectural judgement separately in the existing source review.

### Execution sequence after approval

1. Record the approved track A layout and initial source/API/catalog identities.
   Finish consumer discovery and any applicable path-migration plan before editing.
2. Inventory track B's actual failure/context/reporting paths. Under the user's
   completion direction, implement a bounded compatible path using existing
   schemas; document choices rather than ask repeated design approval.
3. Implement the agreed connected source, dependency fixtures, catalog/review
   and README changes. Finish lifecycle metadata before recording final hashes.
4. Perform consolidated parent self-review of all affected files and predicates;
   close its corrections together. No source/verification input remains editable
   by a contributing agent at the final proof boundary.
5. Use narrow exploratory tests while developing. Before final proof, prepare
   the exact final task paths with the existing before-verification command,
   validate the impact plan and confirm source-review freshness. Preparation
   must precede final testing: if it changes a source header, reconcile that
   review first rather than testing stale inputs. Then run registered focused
   proof:

   ```bash
   bash scripts/repo/check-selection/script.sh --checks module-index-structure module-index-structure-regression core-runtime platform-config-runtime diagnostic-catalog-readers --execute-local --json
   ```

   Include affected track B registered units listed above in that final focus,
   after their prerequisites. Do not start one final pass while another required
   implementation batch remains unfinished or any contributor edits its inputs.
   Run check-selection-repository-contracts only when its owning catalog/fixture
   inputs actually change; do not repeat it for unchanged code merely to reprint
   evidence. Follow the trusted selector's matching-input requirements for reuse.
6. With focused proof passed and the prepared/reviewed inputs still frozen, use
   impact-selected local checks for the combined result. Applicable target/payload
   checks include persistence-composition and platform-shell-payload; inspect the
   actual final plan for additional consumers. Do not run container/live stages
   without their separately required authority or claim local proof is live proof.
7. Audit both agreed tracks, responsibility map, real code, consumers, tests and
   explained limits. Close the goal only when the config proof and reusable
   governance are implemented and verified; agreement alone is not completion.

Record actual UTC start/end and command elapsed times in the existing session
README, distinguishing inventory/design, edits, metadata/review, focused proof,
impact planning, broader proof, waits and rework. Report checker cost separately
from existing suite cost. A failed or invalidated pass remains recorded; do not
reset hashes, weaken checks or create another time-journal system here.

## 5. Agreement, completed proof and limits

The user approved the exact eleven-file layout before source moves, then directed
completion without further design approvals. Both identified tracks are complete.

| Requirement | Current implementation and actual proof |
| --- | --- |
| Complete responsibility map | Section 1 maps all 42 public names and private helpers; actual files follow section 2. Declaration comparison preserved 55 named declarations, with only the two recorded internal parameter-type adjustments. |
| Useful contracts/capabilities | Five contract files and five domain files plus the export-only index; section 2 gives concrete not-applicable reasons instead of empty folders, services or manifests. |
| Compatibility | Nine registered focused checks passed. All 42 public names/signatures remain; Core and Platform config diagnostic JSON bytes are unchanged. Existing reader, declaration, collector, source-throw and historical diagnostic tests passed. |
| Dependency direction and future adoption | Existing AST checker, Core boundary test and independent future-module fixtures passed: contract/domain direction, own-index imports, cycles, private imports and the exact catalog exception. Selector input/selection regression passed. |
| Actual context and delivery | Pure Platform contract binding snapshots required context and selected definitions; Observability uses the same validation. Actual server startup fixes startup attribution, preserves error/diagnostic/exit, rejects before pool creation and isolates failed output. Runtime/type and real consumer fixtures passed. |
| Reusable governance | Existing product structure, safe-diagnostic and coverage-workflow owners require responsibility/context accounting and proportionate proof. Semantic ownership and diagnostic truth still require source review; no universal automatic completeness claim. |
| Connected consumers | The broader registered run passed all 28 selected entries: 22 commands executed and six matching focused results reused. Nested aggregates reused their member proofs without rerunning them. Compiled payload, Platform/product consumers and adapter/connection fixtures passed. |
| Reconciliation | Current README/course links and 343 source-review hashes were checked. DIAG-008's original cleanup is done; DIAG-002, the remaining DIAG-003 policy, DIAG-004 and unrelated backlog work remain open. |

Final focused proof took 501.158 seconds. Broader consumer proof ran from
2026-11-01T21:18:46.636Z to 2026-11-01T21:31:33.334Z; runner elapsed time was
766.406 seconds, with zero findings. Commands, individual timings, counterexample
coverage and activity/rework are recorded in the
[session journal](../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/README.md).

The full impact plan has 118 bindings because initial review-ledger adoption
also selects the earlier diagnostics project's owners. That plan was inspected
without findings. Source-reviewed affected-consumer units provide this bounded
goal's broader proof; explicit unit verification does not replace the full impact
gate before a later integration/merge. The unrelated project's outstanding
qualification and all 18 package/deploy/acceptance bindings remain unclaimed.
No installation, container, cloud, deployment, staging, commit or push occurred.

These final edits record outcomes only. Run scoped documentation/header/link
checks for closeout; do not rerun broad runtime suites merely to record their
results. Runtime/source/check contracts remain frozen. This record does not
claim that later documentation edits preserve a whole-branch cache identity.
