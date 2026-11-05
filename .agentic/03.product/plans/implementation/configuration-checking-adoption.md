<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.plan.configuration-checking-adoption
version: 2
status: active
created_on: "2026-11-01"
updated_on: "2026-11-04"
layer: 03.product
domain: configuration
disciplines: [architecture, security, agentic]
kind: plan
purpose: Complete DIAG-003 policy and bounded configuration access/caller proof without changing runtime semantics.
portability: {class: source-only, targets: []}
used_by:
- id: shared.plan.diagnostics-backlog
  path: .agentic/shared/plans/implementation/diagnostics-backlog.md
-->
# Configuration checking adoption — DIAG-003

## Authority and scope

User requested implementation. Inventory started 2026-11-01T23:15:27+00:00
(Europe/Dublin). No new goal, deployment, installation or broad runtime rewrite.
Apply the configuration standard and existing diagnostic/context obligations.
This task establishes policy for new/changed work and bounded executable proof;
it does not assert all historical code paths are universally bypass-proof.

## Existing ownership and predicate inventory

| Responsibility and existing source | Preservation / proof disposition |
| --- | --- |
| Core config domain/source, settings and value-readers | Reuse for supported simple text/numeric rules; retain snapshot, grammar, throw identity, collection limit and independent issue order. Core config runtime and foundation diagnostics fixtures already prove these facts. |
| Platform config/index.ts | Checked higher-level schema wrapper; first failure returns before later schemas, throws preserve identity and selected source evidence, optional reporter cannot change the result. Extend its actual caller fixture, not its public API. |
| Platform server configuration/runtime.ts | Existing listener defaults and accepted numeric spellings are deliberately different from destination-port parsing. Keep local checker; never force this through the destination constraint. |
| Platform worker/runtime, observability/configuration | Existing optional/default/conditional selections keep their own meaning. Injected environment bags are not presumed checked; their owner must account for used values. No incidental parser consolidation. |
| Platform security certificate/TLS checks | Specialised validators stay with security. Existing target configuration fixture covers them without a generic Core import requirement. |
| PostgreSQL config.ts and core-server target configuration | Shared destination constraint already adopted. Target binds source names, uses checked values and numeric adapter guard; keep all defaults, purposes and errors unchanged. Extend the actual compiled target/caller fixtures. |
| Platform contracts/diagnostics.ts and target startup binding | Required typed fields/runtime construction plus fixed startup attribution already exist. Existing type fixtures reject missing context; actual target fixture rejects wrong item/override and proves delivery/output-failure isolation. Strengthen assertions where needed, no new all-optional context object. |
| Module-structure checker and adoption checker | Existing AST discovery/commit check can own a narrow environment-access rule. Diagnostic adoption enforces review freshness, not data-flow truth; no second registry. |

### Context facts for the reference operation

Core/target records identify logical setting or source, exact condition and
read/validation step. The target's fixed binding supplies persistence/startup
attribution; the main startup failure reporter establishes startup rejection
and exit status before token/pool work. Raw values, provider text and physical
paths stay excluded. A thrown read retains unknown cause rather than inventing
missing/permission-denied. Existing definitions and guarded source inspection
provide the permitted next investigation; they do not authorize retry/mutation.
Core must not acquire request/job/target context. Existing contracts and tests
are reused rather than inventing new response fields such as notChecked.

## Narrow access control design

Extend the existing module-structure AST checker, its fixtures and command guide.
Discover TS/TSX in the current package/platform/app/product source roots. Reject
recognised direct Node environment access in Core and ordinary app/product/
Platform implementation. Permit the existing two Platform process entrypoints,
Platform config loaders and target/infra boundaries. Test files remain excluded.
Consumers of injected sources/checked values and specialised validators require
no token import. No new general-purpose program analysis, baseline or registry.

Precisely document supported direct syntax, aliases and exclusions in the
standard/command guide; structural findings do not prove checked-result usage.
Python/shell/tooling use their existing governed loaders and explicit checks,
not TypeScript import requirements. Unknown aliases/data flow remain source
review responsibilities. Never print offending source text or secret keys.

## Implementation and fixture batch

- Extend the existing configuration standard with responsibility, per-used-input
  required/optional/default/conditional treatment, reuse decision, checked-result
  consumption, failure-before-work and context/proof obligations. Link it from
  the existing diagnostic workflow; explain actual controls/limits in READMEs.
- Extend checker fixtures with prohibited direct access, import/require aliases,
  approved loaders, checked/wrapper callers, security checks, future modules,
  safe findings and real discovery. Retain existing structure/dependency tests.
- In the existing target fixture, load trusted compiled consumers with fixture-only
  checker substitutions: forced failure must stop the actual server before pool,
  token or later checks; changed checked value must reach its consumer; omitted
  declaration must be rejected; extras must not become checked configuration.
  Existing invalid/multiple/conditional/source/context cases remain intact.
- Extend existing Platform config caller tests for required/optional/default and
  conditional contracts, first-error stopping, original throw identity and
  reporting failure isolation. Use real helpers, not production framework changes.
- Refresh only the reviewed checker source hash under its existing support owner;
  keep existing runtime reviews and diagnostic catalogs unchanged.

## Verification sequence

Finish all code, consumers, documentation and self-review before final proof.
Use the existing module-index structure check/regression (small AST fixtures),
specific Core config/foundation runtime files, Platform config runtime file,
Platform context type/runtime fixtures and actual target configuration fixture.
Fresh target compilation may supply those compiled dependencies; use existing
package test builds for test files. No full Core/Platform runtime aggregate,
selector regression, image/container qualification or live operation. Direct
focused commands do not create registered aggregate receipts. Broader integration
proof stays at the stable batch boundary under the user's explicit direction.

Check metadata/links and diagnostic-adoption freshness, then reconcile every
DIAG-003 criterion with actual proof before marking done. If a runtime gap is
found, repair its real owner in scope or leave the relevant criterion open;
do not relabel it as an optional enhancement or claim a source scan proves it.

## Outcome

Completed with focused proof on 2026-11-01. This is policy plus bounded controls
and reference caller proof, not a universal data-flow or historical-adoption claim.

### Input and criterion reconciliation

| Criteria | Actual owner/proof |
| --- | --- |
| Code 1–3: inventory, used inputs and compatibility | Base target host/name/schema use existing provider text rules; port uses the Core destination constraint; server/migration/restore select runtime reference while administration selects administrator reference. All are required for their selected purpose. Pool/timeouts are existing code-owned constants, not unchecked source fallbacks. Target fixture tests purposes, defaults, omitted declarations, checked-port replacement and extra exclusion. No production parser changed. |
| Code 4–6: context and sourcing | Existing Core diagnostics establish setting/source facts; target binding supplies persistence/startup; actual startup output and exit status establish rejection before dependent work. Code-owned persistenceConfigurationBindings supplies the permitted logical-to-source lookup. No secrets, physical paths, assumed permission cause or mutation/replay authority are added. Core foundation, Platform context and real target fixtures prove original throws, fixed attribution, item rejection, reporter isolation and no token/pool work. |
| Harness 1–6 | Canonical configuration standard, linked diagnostic workflow, precise command-guide scope/limits and source-matched reviews use the existing inventories/gates. Actual source scan passes. Existing two gate identities now include policy in both cache inputs and routing; four focused repository contract cases prove wiring. |
| Fixture 1–4 | Core direct helpers and Platform checked-schema caller pass. Wrapper fixture covers optional MODE default, conditional ENDPOINT and optional LABEL, consumes checked values and excludes EXTRA. Actual target checker-call count rejects no-check implementations; forced failure stops the real main before authentication; a changed checked port reaches that main's next consumer. Omitting each base declaration is rejected. AST fixtures cover prohibited access, approved loaders/wrappers/checked consumers/security and a newly discovered app file. |
| Fixture 5 | Real listener checks accept hexadecimal, exponent and surrounding-whitespace spellings and explicit listener port 0; the same text is rejected by destination parsing. A naive parser consolidation would fail these assertions. No listener policy changed. |
| Fixture 6–8 | Existing actual target fixture retains 561 rejected-entrypoint cases, conditional purposes, multiple setting failures, source/certificate failures, unknown causes, fixed context delivery and output-failure isolation. New actual-main substitutions add eight caller runs. Core config/foundation and Platform context fixtures retain source interruption/collection and wrong-context/item cases. No new continuation format was introduced. |

### Actual verification and timing

- Existing module-structure command and AST smoke fixtures passed. Four focused
  repository-contract tests passed in 0.765 seconds, without full repository plans.
- Core runtime compilation plus config/foundation files passed in 16.420 seconds.
  Platform config compilation plus its caller runtime file passed in 13.923
  seconds; these ran in parallel with the target group.
- Corrected target/context group passed in 23.936 seconds: fresh target build,
  existing runtime preparation, configuration fixture, Platform contracts type
  check/runtime compilation and diagnostic-context-runtime.test.js. Final
  acceptance review added the required real-parser contrast; reran only the
  affected target fixture/build/preparation, passing in 10.884 seconds.
- Source-matched diagnostic adoption passed with no findings. Eleven affected
  artifact headers, 94 local links/anchors across six guidance documents and
  unchanged Core/Platform config catalog SHA-256 comparisons passed. Broader
  registered integration/aggregate receipts are not claimed by these direct
  tests; full suites, images, containers and live operations were not run.

### Corrections retained honestly

The first target invocation omitted host node_modules from NODE_PATH while
adding disposable workspace shims, so an existing OTel package could not resolve.
Corrected the invocation, installed nothing and retried only that group. The
adoption gate caught the changed repository-contract test's stale existing
review; reviewed its DIAG-002/003 changes and refreshed that exact owner, without
waiving proof. A combined documentation patch had a stale no-op context and was
rejected atomically; corrected the patch before applying it. During fixture
review, changed optional LABEL consumption to use the actual checked result.
These are recorded process/fixture corrections, not production API failures.
