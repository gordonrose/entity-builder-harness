<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.plan.diagnostics-backlog
version: 26
status: active
created_on: "2026-11-01"
updated_on: "2026-11-05"
layer: 06.shared
domain: diagnostics
disciplines: [architecture, security, sre, agentic]
kind: plan
purpose: Keep agreed future diagnostic work and its completion criteria in one repository backlog.
portability: {class: source-only, targets: []}
used_by:
- id: shared.workflow.maintain-diagnostics-backlog
  path: .agentic/shared/workflows/maintain-diagnostics-backlog.md
-->
# Diagnostics backlog

This is the canonical backlog for future diagnostic work requested by the user
or confirmed during the agreed diagnostic review.
Recording a task does not authorize implementation, resume the completed initial
adoption project, or reopen its goal. Existing project decisions and evidence
remain in their original records.

Use the [maintenance workflow](../../workflows/maintain-diagnostics-backlog.md)
and [entry template](../../templates/diagnostics-backlog-entry.md) when asked to
update this backlog. Keep active task predicate inventories and runtime
diagnostic definitions with their existing owners; this backlog does not copy
either of them.

## Entries

## DIAG-001 — Reuse one upstream database destination port constraint

Status: done

### 1. ID

DIAG-001

### 2. Date/time raised

2026-11-01T10:40:55+00:00 (Europe/Dublin).

This is the backlog recording time. The issue was discovered earlier in the
same teaching conversation; that message's exact timestamp was not recorded.

### 3. Summary

Replace separately declared database port bounds with one reusable upstream
constraint consumed by both target configuration parsing and PostgreSQL adapter
validation. Keep deployment-specific environment bindings in the target.

### 4. Background

During our step-by-step diagnostics course, the assistant showed how the old
combined configuration check had been replaced with individual setting
declarations. The user asked why the port declaration still lived in the target
file rather than being reused. We inspected the code together and confirmed
that the target declares an integer range of 1 to 65535, while the PostgreSQL
adapter independently repeats those bounds. Text rules for host, database,
schema and authentication references are already shared, but the port constraint
was not factored in the same way.

The target's choice of environment variable belongs locally; the reusable
constraint does not. The earlier work made diagnostics more precise, but its
tests and architecture review did not establish that this rule had one owner.
This is a confirmed ownership and duplication gap, not evidence that currently
valid database ports fail. The user asked to record it as the first backlog
task, not to implement the correction during the course.

### 5. User stories

- As a Core configuration maintainer, I need a named, immutable,
  provider-neutral destination port constraint in `packages/core/src/config/`,
  exposed through `packages/core/src/config/index.ts`, so consumers reuse one
  authoritative range without importing deployment or AWS code. Select its
  precise module/name during implementation; reuse the existing constraint and
  validation machinery instead of creating another validation framework.
- As a core-server target maintainer, I need
  `infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts`
  to bind `database.port` and `PERSISTENCE_POSTGRES_PORT` to that shared rule,
  while `platform/adapters/aws/persistence/postgresql/src/config.ts` checks its
  already-numeric input against the same constraint. This prevents the two
  paths from drifting without confusing environment parsing with numeric
  adapter validation. Existing callers, error codes, safe reasons and setting
  names must remain compatible; supplied values must stay out of diagnostics.
- As an agent making future configuration changes, I need the existing
  diagnostic review workflow to distinguish reusable constraints from concrete
  source bindings, and fixtures to catch independent copies of the constraint,
  so the same incomplete factoring is not accepted again. The relevant owners
  are `.agentic/shared/workflows/verify-diagnostic-coverage.md`, Core config
  tests, PostgreSQL adapter tests and the core-server composition tests.

### 6. Acceptance criteria

#### Code

- [x] One Core-owned destination port constraint defines the accepted integer
  range. It has no dependency on PostgreSQL, AWS, Platform runtime or environment
  variable names, and its exported declaration cannot be mutated by a consumer.
- [x] The target declaration and adapter numeric check both use that constraint;
  neither independently redeclares its minimum/maximum as validation policy.
  Actual environment bindings and program-specific required-setting selection
  remain in target composition.
- [x] Existing source-text parsing, numeric validation, accepted/rejected values,
  result/error identity, diagnostic codes/versions/reasons, issue ordering and
  privacy are preserved. Reusing the range must not force numeric adapter input
  through an environment-text parser or broaden existing accepted spellings.
- [x] Inspect other port declarations for applicability and record the decision
  in this task's implementation inventory. Do not replace every occurrence of
  65535 blindly, change an unrelated listener policy, or start excluded
  platform-shell deployment/AWS work. Preserve any supported listener port-0
  behavior; this is a database destination constraint, not a universal port rule.
- [x] Update affected public exports, dependency/test setup, code-owned
  documentation and source-matched reviews only where the actual change needs
  them. Preserve package dependency direction and existing diagnostic contracts.

#### Harness

- [x] Add the missing reusable-constraint-versus-source-binding question to the
  existing diagnostic responsibility/source-review workflow. Require the change
  inventory to identify the constraint owner and relevant consumers, with an
  explicit applicability decision for superficially similar rules.
- [x] Source review demonstrates that both current consumers use that owner,
  and that fixture assertions would reject a return to independently copied
  bounds. Keep the rule in its owning workflow; do not duplicate it in AGENTS,
  introduce a second runtime vocabulary, or treat a prose requirement as proof
  of executable enforcement.

#### Regression fixtures

- [x] Extend `packages/core/tests/config-runtime.test.ts` and
  `packages/core/tests/config-types.test.ts` as applicable to prove the public
  constraint, boundaries, immutability and supported use by existing readers.
- [x] Extend
  `platform/adapters/aws/persistence/postgresql/tests/postgresql-persistence-adapter-runtime.test.ts`
  and
  `scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs`
  with independent expectations for valid boundaries 1 and 65535 and rejected
  0, 65536 and non-integers. Retain missing/wrong-type/source-text grammar
  distinctions, exact safe diagnostics and existing positive cases.
- [x] Include an assertion of the actual shared rule binding plus a bounded
  counterexample that would fail if either consumer reverted to an independent
  rule. Merely checking that both accept today's two endpoints is insufficient:
  two copied rules could pass that test. Choose the smallest behavior/wiring
  fixture that demonstrates this sensitivity; do not add a broad source-regex
  gate or an unrelated optimization campaign.
- [x] Following the user's explicit verification-scope revision, complete
  narrow runtime proof for Core config, the PostgreSQL adapter and the actual
  target configuration fixture, with current type/source review and unchanged
  diagnostic catalogs. Record actual outcomes. Broader registered integration
  and payload checks are deferred to a stable batch/integration boundary, not
  claimed as passed by these direct tests. No live deployment is needed or
  authorized for shared rule ownership.

Evidence and update history:

- 2026-11-01T10:40:55+00:00 (Europe/Dublin): recorded by the parent assistant at
  the user's request after reviewing the sub-agent's backlog workflow/template.
  Confirmed source locations are the target's `definitions` mapping and the
  adapter's `integerIssue(input.port, 1, 65_535)` check. All implementation and
  regression criteria above are planned and unchecked; no port code was changed.

- 2026-11-01T22:15:42+00:00 (UTC): user authorised DIAG-001. The bounded
  file/consumer/predicate inventory, Core constraint design, other-port
  applicability decisions and exact focused/broader checks are recorded in the
  session journal before runtime edits. Criteria remain unchecked until proof.


- 2026-11-01T22:52:22+00:00 (Europe/Dublin): completed DIAG-001 under the
  user's revised narrow-verification scope. Core's frozen destination-port rule
  is public and used by both consumers; the harness owns placement/reuse rules
  and the README explains them. Core config runtime passed (17.496 seconds
  including compilation); the two existing PostgreSQL adapter/diagnostic tests
  passed (20.057 seconds including compilation); the target configuration
  fixture passed 561 rejected-entrypoint cases before pool creation (21.227
  seconds including compilation/preparation). These three groups ran in parallel.
  Both consumer fixtures passed their substituted-bounds counterexamples.
  Earlier focused type checks passed; current adoption review passed with no
  findings, all four changed runtime source hashes match their reviews, and
  both affected diagnostic catalog files are byte-for-byte unchanged. Full
  integration/payload checks remain deferred; the cancelled selector is not a
  passing receipt. See the [session evidence](../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/README.md).

## DIAG-002 — Move configuration requirements into the agentic harness

Status: done

### 1. ID

DIAG-002

### 2. Date/time raised

2026-11-01T13:20:34+00:00 (Europe/Dublin).

This is the backlog recording time. The issue was discovered in the preceding
teaching discussion; that message's exact timestamp was not recorded.

### 3. Summary

Make the existing `standard` artifact type under `.agentic/03.product/standards/`
the authoritative home of configuration requirements,
instead of `docs/03.product/rules/platform/concerns/config-runtime-settings.yml`.
Correct the conflicting document-placement guidance and connected references
so future work does not extend governance requirements under `docs/` again.

### 4. Background

While the user and assistant were discussing when code should use Core's
configuration helpers, the assistant cited the configuration rules under
`docs/` as requirements. The user pointed out that this contradicts the agreed
separation: the agentic harness owns requirements, code implements them, tests
verify them, and documentation explains them.

Inspection confirmed that the document-placement standard says governance
belongs under `.agentic/`, but also explicitly puts structured rulesets under
`docs/`. The harness manifest still lists the configuration rules at that old
location, and check selection refers to it. The diagnostics work added a new
mandatory diagnostic requirement to the existing ruleset without resolving
this conflict. This is a confirmed governance-placement gap, not evidence that
the runtime configuration checks have stopped working.

The user asked to record the correction for later work. Moving files, changing
requirements or expanding into a repository-wide rules migration is not
authorized by this backlog entry.

### 5. User stories

- As an agent changing configuration code, I need one authoritative set of
  requirements under `.agentic/03.product/`, so I can find the rules in the
  harness rather than treating explanatory documentation as policy. Migrate
  `docs/03.product/rules/platform/concerns/config-runtime-settings.yml` through
  `.agentic/01.harness/workflows/migrate-artifact-paths.md`. Choose and record
  its precise canonical destination during implementation. Owner: product
  governance, with harness governance owning the migration procedure.
- As a harness maintainer, I need
  `.agentic/01.harness/standards/document-artifact-placement.md` to distinguish
  authoritative requirements from explanatory material consistently, and
  `.agentic/01.harness/manifest.yml` plus
  `scripts/repo/check-selection/checks.yml` to reference the canonical owner.
  Inspect the known references in `.agentic/01.harness/state/` and distinguish
  active consumers from historical records before changing them. This prevents
  an agent from following the old placement instruction again.
- As a maintainer reading module READMEs or human guides, I need explanations
  to link to the harness requirements rather than maintain a competing copy.
  Preserve existing configuration and diagnostic behavior, identifiers,
  privacy requirements and useful explanatory material. Review active links
  and affected metadata/tooling consumers; do not rebuild dormant RAG machinery
  or migrate unrelated rulesets as an incidental part of this task.

### 6. Acceptance criteria

#### Code and connected consumers

- [x] One canonical product-harness artifact owns the existing configuration
  requirements. Preserve their meaning; explicitly review any necessary wording
  change rather than silently weakening or expanding them during the move.
- [x] Update active manifest, metadata, workflow and check-selection references
  affected by this move. Preserve artifact identity where supported by the
  migration workflow. Any temporary pointer at the old path identifies the
  canonical owner and does not retain a second authoritative rule body.
- [x] Runtime implementation changes are not needed merely to relocate these
  requirements. Preserve Core/Platform/target validation behavior, public
  exports, diagnostic codes and versions, and deployed interfaces. If an actual
  code correction is discovered, record it separately rather than smuggling it
  into this placement task.

#### Harness

- [x] Remove the conflicting placement instruction that sends authoritative
  structured rules into `docs/`. Clearly distinguish governance requirements
  under `.agentic/<owner-layer>/` from explanations and historical material
  under `docs/`; keep AGENTS as a router rather than copying the new policy there.
- [x] Follow the existing path-migration workflow and record the bounded
  consumer inventory, canonical path, compatibility decisions and treatment
  of historical/dormant references. Do not turn this into an automatic migration
  of every legacy rule or re-enable dormant RAG checks.
- [x] Review demonstrates that future configuration requirement changes are
  directed to the harness owner. Be explicit about which controls are written
  guidance and which are executable checks; a location change alone does not
  prove that every necessary runtime validation call exists.

#### Regression fixtures

- [x] Add or update the smallest owning placement/reference fixture to accept
  the canonical harness location and reject the old `docs/` path being used as
  the authoritative configuration ruleset. Include a counterexample that points
  an active consumer back to the old owner. Select the exact fixture during
  implementation; this proof is planned, not already implemented.
- [x] Extend affected selector cases in
  `scripts/repo/check-selection/smoke-test.sh` as needed to prove that edits at
  the new canonical path retain the required diagnostic checks. A stale old-path
  binding must not let such edits bypass selection.
- [x] Verify artifact metadata, relative links and reference continuity using
  existing owning checks, including the header checker with scoped `--paths`.
  After review and focused proof, use proportionate impact-selected local
  checks. Record actual results before closing the task; no live deployment,
  runtime test campaign or dormant corpus rebuild is required just for prose
  relocation.

Evidence and update history:

- 2026-11-01T13:20:34+00:00 (Europe/Dublin): recorded at the user's request.
  Confirmed the placement standard's structured-ruleset exception, active
  manifest/selector references and the diagnostics addition in the old ruleset.
  All migration and regression criteria above are planned and unchecked. No
  requirement, source file or owning path was migrated by this update.
- 2026-11-01T19:32:36+00:00 (Europe/Dublin): the user supplied the Core
  architecture goal amendment. Confirmed this remains the requirements-placement
  task, distinct from DIAG-003's checking/context policy and the config layout
  proof. Existing shared standards/workflow now clarify context ownership; that
  does not relocate the legacy ruleset or complete this task.


- 2026-11-01T23:06:38+00:00 (Europe/Dublin): implemented the user-approved
  correction as `kind: standard`, not a new rule type or rules directory.
  Canonical owner: `.agentic/03.product/standards/config-runtime-settings.md`.
  All five requirement IDs and 35 must/must-not clauses, summaries and guidance
  were mechanically compared with the pre-conversion document and preserved.
  Workflow, manifest/standard classification, current state references, selector
  binding, infra reference and current teaching/README links now name the standard.
  The old YAML is a deprecated human-readable pointer with no rules body; it is
  not a promise of compatibility with old ruleset parsers. Historical evidence
  and dormant RAG references remain recorded, without rebuild or activation.
  Three focused repository-contract cases passed, including stale manifest and
  catalog counterexamples; the two new cases passed again after review. Scoped
  metadata, YAML, 89 Markdown links/anchors, teaching navigation and migration
  checks passed. The migration checker uses the approved pointer allowance;
  the focused assertions separately reject stale current owner bindings.
  No product runtime, container, deployment or broad suite ran. Full integration
  regression remains at the stable batch boundary. See the
  [migration plan](../../../../.agentic/03.product/plans/migration/configuration-requirements-standard.md)
  for the reference inventory, limitations and actual proof. DIAG-003 is separate.

## DIAG-003 — Govern configuration checking and prove it cannot be bypassed

Status: done

### 1. ID

DIAG-003

### 2. Date/time raised

2026-11-01T13:29:49+00:00 (Europe/Dublin).

This is the backlog recording time. The missing policy was discussed with the
user immediately before this entry; that message's exact time was not recorded.

### 3. Summary

Define when code must reuse Core configuration checks directly or through an
existing checked-loading function, how it must handle their results, and how
the harness verifies that responsibility. Require each consuming operation's
necessary diagnostic context, its supplying owners and a checked reporting path.
Add focused checks and behaviour
fixtures without requiring a meaningless Core import in every file.

### 4. Background

While reading the Core configuration README, the user asked when a file must
call `@kanbien/core/config` and how the harness ensures it does. The assistant
inspected the configuration rules, shared diagnostic standard, review workflow
and executable adoption check. The repo already requires early validation,
safe detailed failures and reviewed tests. Its adoption check verifies source
review freshness and proof references, not whether every necessary validation
call executes or whether its returned failure is handled.

The discussion distinguished code receiving unchecked information from code
receiving checked configuration. A direct-import rule would miss unused imports
and ignored results, while incorrectly rejecting callers of higher-level checking
functions. The user asked to explain the current rules and unimplemented parts
in the README, and record the missing harness work separately.

DIAG-002 owns relocating the existing requirements into `.agentic/`. This entry
owns completing their configuration-checking policy and proportionate proof;
moving the old file alone does not complete it. DIAG-001 separately owns the
shared database port constraint. No implementation of any entry is authorized
by recording this task.

### 5. User stories

- As an agent adding a service or configuration reader, I need the canonical
  product-harness configuration requirements to name who obtains/checks the
  information and who consumes the checked result. Define direct Core reuse,
  legitimate higher-level checking functions, specialised validators and
  justified exceptions. Extend the owner established by DIAG-002 rather than
  adding new requirements to the legacy file under `docs/`. Connect it through
  `.agentic/03.product/workflows/platform-runtime-implementation.md` and
  `.agentic/shared/workflows/verify-diagnostic-coverage.md` without duplicating
  the policy in AGENTS or the module README.
- As a runtime maintainer, I need each used configuration input's requirement,
  optional/default/conditional treatment, checked-value path and failure handling
  identified in the existing change inventory. Core's checking functions in
  `packages/core/src/config/` remain reusable implementation, while application
  meaning and concrete source names remain with their owners. Existing target
  consumers and specialised security checks must not gain redundant imports,
  altered acceptance rules or blanket repeated validation.
- As a harness maintainer, I need narrow executable controls and owning
  behaviour tests that detect bypasses the code can actually demonstrate.
  Inspect `scripts/repo/diagnostic-coverage/script.py`, its `smoke-test.py`,
  existing dependency/configuration checks and
  `scripts/repo/check-selection/checks.yml` for reuse before adding machinery.
  Record which guarantees remain review judgements rather than claiming a
  scanner understands every possible data path. Select precise implementation
  and fixture owners during planning; do not build a second review registry.
- As a reviewer, I need each configuration change to distinguish the consumer's
  requirements from reusable checking work, identify existing helpers, and explain
  reuse or a justified difference. Similar-looking checks may have different
  accepted inputs or defaults; repeated checks at separate entry points do not
  justify independently maintained copies of the same shared constraint.
- As a consuming-module maintainer, I need the operation's required diagnostic
  context declared in its code-owned contract/construction path, with fixed
  context bound during assembly where useful. Core establishes reusable facts;
  Platform adds workload context/delivery; adapters interpret provider evidence;
  entrypoints supply actual bindings and execution context. Inspect
  `platform/config/src/diagnostics.ts`, `platform/contracts/src/diagnostics.ts`,
  `platform/observability/src/diagnostics.ts` and the real caller before choosing
  changes. Typed and runtime requirements must replace reliance on every caller
  remembering prose, without a universal all-optional context bag or a mandatory
  wrapper for modules that need no connecting work.

### 6. Acceptance criteria

#### Code and connected consumers

- [x] The inventory identifies supported configuration-loading/checking code,
  relevant downstream consumers and specialised checks. Use existing Core
  helpers where applicable, directly or through a named checking function;
  document actual exceptions. A Core import alone is not evidence of a check.
- [x] Every used supplied input in the affected scope has an explicit rule and
  required/optional/default/conditional treatment. Successful consumers use
  checked values; failures are handled before the dependent operation and retain
  exact safe setting/reason reports. Ignored extra inputs are not represented
  as validated information or used through an unchecked fallback.
- [x] Preserve existing accepted values, defaults, diagnostic identities,
  privacy and public interfaces unless a separate change is explicitly approved.
  Inventory existing gaps before deciding migrations; do not launch a repo-wide
  runtime rewrite merely to introduce this policy.
- [x] For the affected responsibility, map attempted operation, logical setting
  or source, failure step, observed condition, known outcome/effect, uncertainty
  and applicable next investigation to their supplying owners and reporting
  consumers. Reuse existing records/context or a governed code-owned lookup;
  do not require Core to know startup/request/job context or fabricate facts.
- [x] Required interfaces and runtime declaration/context checks reject missing
  or inappropriate context where deterministically established. Validate fixed
  bindings before dependent work where practical; preserve original workload
  results and opt-outs when reporting fails. Never expose arbitrary submitted
  values, exception text or physical source paths through the new context.
- [x] Distinguish setting problems from sourcing observations and checks that
  could not run. Preserve existing source throws, continuation and collection
  behavior unless explicitly approved. Teaching response examples, including
  `CONFIGURATION_FAILED` and `notChecked`, are not approved API definitions.

#### Harness

- [x] Put the explicit policy in its `.agentic/03.product/` owner, coordinating
  with DIAG-002. The existing diagnostic workflow requires the applicable
  configuration responsibility and checked-result evidence in its current
  inventory/review, not in a parallel tracking system.
- [x] Require an ownership/reuse decision in that inventory: name the requirement
  owner, the existing shared checker considered, and either its use or the exact
  reason a separate implementation is needed. Distinguish supplied text from
  already-numeric values, whitespace/number spellings, optional/default behavior,
  first-error versus collected reports and checks at independent entry points.
  Do not force all consumers through schema.ts or treat matching reason names
  as evidence that their checks are interchangeable.
- [x] Specify which source languages and runtime locations each mechanical rule
  covers. Catch clearly prohibited configuration access where deterministically
  identifiable, while accepting legitimate loaders, higher-level checking
  functions, tests and consumers of checked values. Do not require TypeScript
  imports in shell/Python or self-package imports inside Core; document their
  applicable checking paths instead.
- [x] Reuse owning gates and registered checks where possible. Clearly separate
  automatic findings, behaviour-test proof and architectural review judgement.
  No passing import scan, fresh review hash or schema-valid diagnostic is
  described as universal proof that checking cannot be bypassed.
- [x] Update `packages/core/src/config/README.md` with canonical rule links and
  actual enforcement limits. Remove a “not yet implemented” label only for the
  specific policy/control whose implementation and proof have been completed.
- [x] Apply the existing safe-diagnostic context section through the existing
  coverage inventory, not another form/manifest. Record which promises are
  enforced by TypeScript, runtime construction, actual caller/delivery tests or
  architectural review. Do not claim syntax-valid operation strings establish
  that the operation/stage/item combination is correct.

#### Regression fixtures

- [x] A valid direct caller and a valid higher-level caller pass. A consumer
  that only receives checked configuration passes without a token Core import.
  A specialised security checker remains valid without being forced through
  the generic configuration schema.
- [x] Relevant fixtures reject an unused-import/no-check path, a check whose
  failure is ignored, and a caller using original unchecked input after a check.
  Demonstrate failure before the dependent connection/start operation, not just
  that an error object can be constructed.
- [x] Cover a required input omitted from checking instructions, an extra item
  left unchecked but later used, permitted defaults/optional inputs and
  conditional requirements. Retain multiple independent failures, safe exact
  reasons and sensitive-value exclusion. Test the actual caller path; a helper
  test alone does not establish its caller used the helper.
- [x] Fixtures for any new narrow access check prove both prohibited access
  rejection and permitted loader/wrapper usage. Use bounded counterexamples to
  show the assertions catch their intended bypasses; avoid a broad import-regex
  rule or a new general-purpose program-analysis framework.
- [x] Review and proving cases cover both legitimate common-helper reuse and a
  justified local rule. A consolidation counterexample that changes accepted
  number spellings, whitespace, defaults or report meaning must fail the relevant
  behaviour assertions. Do not claim review freshness checks prove absence of
  duplicated implementation or correctness of architectural judgement.
- [x] Use affected existing Core, Platform and target behaviour tests, owning
  harness smoke tests and proportionate registered selection. Exact fixture
  edits and commands are planned during implementation; none are claimed to
  exist or pass merely because they are named here. Record focused and selected
  proof before closing, with no live deployment required for this policy task.
- [x] Through the real configured caller, reject missing required context and
  inappropriate operation/item/stage bindings, including well-formed but wrong
  attribution. Prove correct context survives wrappers and reaches the actual
  approved internal/startup reporter without sensitive canaries; reporting
  failure must not replace the result or invoke dependent work/replay.
- [x] Cover single/multiple setting successes and failures, source failures and
  mixed established/prevented checks where supported. Prove unknown source cause
  stays unknown rather than becoming missing-value or permission-denied. Keep
  exact supported first-error/collection/read behavior unless separately approved.

Evidence and update history:

- 2026-11-01T13:29:49+00:00 (Europe/Dublin): recorded at the user's request.
  The module README now distinguishes existing requirements, their current
  locations, structural review checks and proposed controls marked “not yet
  implemented.” All implementation and regression criteria above remain planned
  and unchecked. No runtime source, gate, policy or ruleset was changed here.
- 2026-11-01T16:14:28+00:00 (Europe/Dublin): after the requested read-only
  sub-agent inspection, added the explicit generic-check-versus-consumer-rule
  review decision, reasons for justified local checks and behaviour-preservation
  counterexamples. Related concrete findings are DIAG-001 and DIAG-005–007;
  original raised time and open status are unchanged.
- 2026-11-01T19:32:36+00:00 (Europe/Dublin): incorporated the user's architecture
  amendment with required context, supplying owners, validated construction and
  caller/delivery counterexamples. The owning shared standards/workflow now
  express these duties; per-operation runtime enforcement remains planned. The
  config architecture plan's track B proves one consumer, not completion of this
  whole policy task. No new response shape or runtime change is claimed.


- 2026-11-01T23:32:35+00:00 (Europe/Dublin): completed the bounded policy
  and proof scope in [the implementation plan](../../../../.agentic/03.product/plans/implementation/configuration-checking-adoption.md).
  Configuration standard/workflow now require per-used-input treatment, a named
  checking owner/reuse decision, checked-result consumption and actual caller/
  context proof. Existing module-structure checking now rejects recognised Node
  environment access outside its explicit TS/TSX loader boundaries; supported
  syntax, language/path limits and review duties are documented. Both registered
  gate inputs and selection include the configuration policy; no new registry,
  checker suite or production API was introduced. AST fixtures, four focused
  wiring tests, Core config/foundation tests, Platform config caller tests,
  actual target configuration/caller tests and Platform context type/runtime
  tests passed. The target fixture retains 561 existing rejected-entrypoint
  cases and adds checker-call/failure/checked-value/omitted-input proof through
  the real server caller, plus listener-versus-destination parsing comparisons.
  Metadata, 94 local links/anchors, unchanged catalog hashes and diagnostic
  adoption review passed. Existing context/throw/opt-out semantics were reused,
  not replaced. All historical paths are not thereby universally bypass-proof:
  arbitrary data flow, unscanned languages and future responsibility decisions
  still require the documented review and actual caller proof. No broad suite,
  container, cloud or deployment ran; integration proof remains at the stable
  batch boundary. DIAG-004 and DIAG-005–007 remain open.

## DIAG-004 — Separate shared reason names from each diagnostic's allowed reasons

Status: done

### 1. ID

DIAG-004

### 2. Date/time raised

2026-11-01T13:40:30+00:00 (Europe/Dublin).

This is the backlog recording time. The issue was discussed in the preceding
teaching exchange; that message's exact timestamp was not recorded.

### 3. Summary

Replace the growing-list compatibility workaround with shared reason names and
an explicit, stable selection of allowed reasons for each diagnostic code and
version. Adding a reason name must not silently change existing definitions or
require another general-purpose extended list.

### 4. Background

While reading the explanation of `issues.ts`, the user asked why new reasons
were added through `configValueIssueReasons` instead of the original
`configIssueReasons`. The assistant traced the original list into Platform's
default configuration diagnostic definitions. Expanding that list would change
the allowed reasons of those definitions without changing their code/version.
The second list avoids that immediate problem, but expanding it later could
repeat the same problem for definitions that use it.

The user rejected continually adding extended lists as unmanageable and chose
the scalable direction: share reason names, but let each diagnostic version
explicitly select the reasons it accepts. Existing compatibility protections
remain necessary. This is a design correction, not evidence that existing
reports are unreadable or that adding a name automatically emits new reports.

### 5. User stories

- As a Core configuration maintainer, I need reason names in
  `packages/core/src/config/issues.ts` and their public exports in `index.ts`
  to grow without indirectly changing every diagnostic that references them.
  Keep shared names in runtime code; select the exact representation during
  implementation. Do not create a new harness vocabulary or one global bucket
  for unrelated capability reasons.
- As a Platform maintainer, I need `platform/config/src/diagnostics.ts` to bind
  an explicit allowed selection to each diagnostic code/version rather than
  inherit a list that future additions silently widen. Inventory its default
  and custom consumers, including
  `infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts`,
  before choosing the additive API migration. Preserve current callers or plan
  an explicit compatible transition, not an unannounced export removal.
- As a maintainer completing this migration, I need a repository-wide inventory
  of direct imports, re-exports, inferred types, helper defaults and indirect
  consumers of the affected reason names and definitions. Trace each affected
  path through Core, Platform, adapters, apps/products, target composition,
  catalog generation, readers, tooling, fixtures and documentation. Update every
  affected file in the same migration, or record the evidence that it can remain
  unchanged; the named examples here are not an exhaustive migration file list.
- As an agent extending diagnostics, I need
  `.agentic/shared/workflows/verify-diagnostic-coverage.md` and the owning
  diagnostic standard to explain that new names and changes to an existing
  diagnostic's accepted reasons are different operations. Core owns reusable
  names; capabilities own their report definitions; the harness governs their
  evolution. Tests and the existing catalog compatibility check must catch
  accidental changes to retained versions.

### 6. Acceptance criteria

#### Code

- [x] Before implementation, search the whole repo for the affected exports and
  definition builders, then inspect their indirect callers and generated/read
  paths. Record the resulting file-by-file consumer inventory in the existing
  implementation plan or session record, including required changes and justified
  no-change decisions. Discovery must not stop at literal import matches.
- [x] Introduce the scalable representation and migrate the affected consumers:
  adding a shared name alone leaves all existing code/version definitions
  unchanged. A definition selects its allowed reasons explicitly; do not solve
  each later addition with another extended global list or a versioned list
  containing every reason in the repo.
- [x] Preserve current diagnostic codes, versions, exact allowed details and
  reader behavior. When an existing diagnostic needs a genuinely additional
  accepted reason, introduce a new version and retain the previous one; a new
  diagnostic can select its own reasons under its own identity.
- [x] Retain supported public exports or provide a reviewed additive migration.
  Any old lists retained for caller compatibility stay fixed and are described
  as compatibility surfaces, not the pattern for future vocabulary growth.
- [x] Update affected runtime/type tests, generated exports, readers and
  source-matched reviews only as required by the actual migration. Preserve
  setting/reason accuracy, privacy and business behavior. Update the config
  README to distinguish the implemented replacement from retained compatibility.
- [x] Reconcile every inventoried file before completion: no supported caller,
  wrapper, type, selected catalog, reader, fixture, active harness reference or
  documentation is left relying incorrectly on the replaced design. A retained
  compatibility list or unchanged historical artifact is deliberate and explained,
  not an omitted migration. Preserve historical evidence; do not bulk-rewrite
  unrelated diagnostics or alter imported/upstream-owned files without authority.

#### Harness

- [x] The existing diagnostic evolution guidance requires explicit reason
  selection per definition and distinguishes adding a name from widening a
  retained diagnostic. Put requirements in their `.agentic/` owner, not docs
  or AGENTS. Coordinate rule ownership with DIAG-002 where applicable.
- [x] Retain `scripts/repo/diagnostic-coverage/compatibility.mjs` and exporter
  protections against changing a committed definition under the same identity.
  Do not weaken compatibility checks or refresh snapshots to conceal a change.
  This task replaces the workaround, not the preservation requirement.

#### Regression fixtures

- [x] Extend `packages/core/tests/diagnostic-record-runtime.test.ts`, relevant
  Core type tests and `platform/config/tests/platform-config-runtime.test.ts`
  to show a new shared reason leaves retained definitions unchanged, is rejected
  by definitions that did not select it, and is accepted by an explicitly
  selecting new diagnostic/version.
- [x] Compatibility fixtures reject widening an existing code/version, accept
  an additive version while retaining the old one, and prove old literal reports
  still parse unchanged. Include a bounded counterexample demonstrating that
  reintroducing an entire growing-list reference would fail the assertions.
- [x] Exercise actual target consumers and generated TypeScript/Python reader
  agreement where affected. Use existing registered focused checks and final
  proportionate impact selection after review. All new tests and migration
  steps are planned; no live deployment is needed merely to prove definition
  stability, and none is authorized by recording this task.
- [x] Map each inventoried consumer to the relevant type, behaviour, catalog,
  reader or reference proof, or an explicit reason no executable check applies.
  Cover both direct and indirect callers with representative real-path tests;
  passing only the two edited helper files' tests is not sufficient. All required
  connected changes and focused proofs are complete before broad verification.

Evidence and update history:

- 2026-11-01T13:40:30+00:00 (Europe/Dublin): recorded during the agreed diagnostic
  review after the user selected the scalable approach. Confirmed both runtime
  lists, Platform's default-list parameter and existing exact-definition
  compatibility checks. All implementation criteria remain unchecked. No source,
  diagnostic definition, reader, exported catalog or harness rule changed here.
- 2026-11-01T13:47:46+00:00 (Europe/Dublin): user clarifies that the migration must
  update every affected file across the repo, not only the shared lists. Added
  explicit whole-repo discovery, indirect-consumer tracing, file-by-file closure
  and consumer-to-proof mapping. Original raised time and open status retained;
  this update does not claim the migration inventory or implementation is done.
- 2026-11-01T19:32:36+00:00 (Europe/Dublin): reconciled the architecture amendment.
  The proposed setting-issues.ts/sourcing-issues.ts separation does not change
  existing allowed reasons. Required context fields/combinations and diagnostic
  reason selections must evolve with explicit compatibility and reader proof,
  not silently widen retained definitions during a structural move. DIAG-004
  remains open and separate; no reason-list redesign or generated export change
  is claimed by this update.

- 2026-11-01T23:53:44+00:00 (Europe/Dublin): completed DIAG-004 locally.
  [Implementation inventory and proof](../../../03.product/plans/implementation/configuration-reason-selection.md)
  reconcile every direct/indirect consumer, including explicit no-change decisions.
  Core now exports frozen configReasonNames; ConfigIssueReason derives from its
  values. The old eight/twelve-entry exports stay fixed for compatibility.
  Platform defaults and core-server v1 definitions select reasons explicitly.
  Current ownership is config/contract/setting-issues.ts after the earlier
  structural migration; the historical discovery path above is retained.
  Focused Core/Platform runtime and types, PostgreSQL types, actual target fixture
  (561 existing pre-pool rejections plus growth assertions), catalog --check and
  six compatibility/TypeScript/Python reader tests passed. All seventeen catalog
  files are byte-for-byte unchanged. Existing standard/workflow now govern
  vocabulary versus definition evolution; README covers all 44 public exports.
  Metadata, links, source-matched reviews/adoption and scoped whitespace passed.
  No broad suites, installation, Docker, cloud/deployment or Git mutation ran;
  broader integration remains at the stable batch boundary. DIAG-005–007 remain open.

## DIAG-005 — Share request-rate limiter number checks and diagnostic construction

Status: done

### 1. ID

DIAG-005

### 2. Date/time raised

2026-11-01T16:14:28+00:00 (Europe/Dublin).

This is the recording time. The finding was discovered during the preceding
sub-agent inspection; its exact discovery time was not recorded.

### 3. Summary

Give the two request-rate limiters one security-owned implementation of their
equivalent positive-whole-number check and safe diagnostic construction. Keep
caller-specific configuration items, defaults and limiting behaviour local.

### 4. Background

During the diagnostics walkthrough, the user questioned whether Core's generic
checks and consumer-owned checks led to duplicated work. At the user's request,
a sub-agent inspected configuration code without editing it. The parent checked
the relevant source excerpts and explained the findings to the user.

Platform's in-memory limiter and its DynamoDB adapter each implement
`assertPositiveInteger()`, with the same distinction between wrong type,
non-finite, fractional and non-positive inputs and the same security reports.
They differ in which configuration items they accept: the in-memory limiter
also has bucket-capacity configuration. The user asked to record the follow-up.
This is repeated implementation, not proof that either limiter currently fails.

### 5. User stories

- As a Platform security maintainer, I need the equivalent check/reporting work
  in `platform/security/src/rate-limiting.ts` owned once under
  `platform/security/src/`, with an appropriate public export through its
  `index.ts`, so corrections do not have to be maintained twice. Choose the
  precise helper location/API during implementation; reuse existing security
  definitions rather than creating new diagnostic identities unnecessarily.
- As the DynamoDB limiter maintainer, I need
  `platform/adapters/aws/security/dynamodb-rate-limiter/src/index.ts` to use
  that shared operation while retaining its own configuration names, defaults,
  reading/conversion and provider calls. Trace all affected callers and export,
  package-boundary, test and review consumers before editing.
- As an agent reviewing this change, I need DIAG-003's ownership/reuse rule
  applied to the actual equivalent operation. These inputs are already numbers;
  do not route them through Core's text parser or broaden the task into unrelated
  security policy or the retiring platform target.

### 6. Acceptance criteria

#### Code

- [x] Both implementations use one Platform-security-owned check/report builder.
  The caller supplies its permitted logical field and local context; Core does
  not acquire rate-limit-specific meanings or provider dependencies.
- [x] Preserve valid inputs, validation/call order, first failure, RangeError
  class/messages and primary/related diagnostic codes, versions, details and
  order. Preserve all existing field mappings, including in-memory bucket
  capacity; supplied values and provider errors do not enter diagnostic detail.
- [x] Preserve limiting algorithms, defaults and numeric environment conversion.
  Update all actually affected exports, consumers, tests, package boundaries and
  source-matched reviews together; no client or network operation is introduced
  into the shared configuration check.

#### Harness

- [x] Apply the ownership/reuse criteria under DIAG-003: record the shared
  security owner, both consumers and remaining intentional differences. Add any
  security-specific instruction only to its existing harness owner; do not copy
  the general rule into AGENTS, docs or another checklist.
- [x] Review demonstrates actual shared-helper use, not just matching outputs
  from two independent implementations. Use the smallest suitable wiring proof
  or bounded counterexample; a new broad clone-detection gate is not required.

#### Regression fixtures

- [x] Extend affected tests in `platform/security/tests/`, particularly
  `configuration-predicate-diagnostics-runtime.test.ts`, and
  `platform/adapters/aws/security/dynamodb-rate-limiter/tests/dynamodb-rate-limiter-runtime.test.ts`.
  Prove valid positive integers and exact failures for wrong type, fractions,
  zero/negative values, NaN and infinities through both real caller paths.
- [x] Preserve existing environment-number spellings and defaults in the adapter;
  prove rejection before the dependent construction/provider work, unchanged
  errors and safe diagnostic details. Include the caller-specific field cases.
- [x] Prove the shared binding as well as behavioural preservation, then run
  affected registered security/adapter checks and proportionate selected local
  checks after review. All new fixture work is planned; no cloud operation or
  live deployment is authorized or needed for this consolidation.

Evidence and update history:

- 2026-11-01T16:14:28+00:00 (Europe/Dublin): recorded at the user's request from
  the read-only inspection and parent source review. All criteria are planned;
  neither limiter nor any harness rule was changed by this entry.

- 2026-11-02T00:08:15+00:00 (Europe/Dublin): completed DIAG-005 locally.
  [Implementation and proof](../../../03.product/plans/implementation/shared-rate-limit-configuration.md)
  record the security-owned numeric predicate/report/assertion, both real callers,
  environment-conversion preservation and complete consumer inventory. Adapter
  implementation now lives in src/rate-limiter.ts; its export-only index retains
  all eleven public names, and only its obsolete legacy allowance was removed.
  Both registered checks passed: platform-security-runtime (25.573253 s) and
  security-shared-rate-limit-diagnostics (30.997610 s), runner total 78.879848 s.
  Existing numeric/field/default/first-error/call-order/environment tests remain;
  new actual caller substitutions reject copied checks and ignored shared failure.
  Errors and primary/related diagnostic literals are unchanged, with no values in
  detail; the security catalog is byte-identical. Existing Platform workflow owns
  security-specific reuse guidance; README updates explain the new helpers.
  Metadata, module structure, adoption, links, API/body hashes and whitespace
  passed. No broad suites, cloud/deployment, installation or Git mutation.
  DIAG-006 and DIAG-007 remain separate/open.

## DIAG-006 — Assess and share equivalent required-text configuration readers

Status: open

### 1. ID

DIAG-006

### 2. Date/time raised

2026-11-01T16:14:28+00:00 (Europe/Dublin).

This is the recording time. The preceding inspection found this repetition;
its exact discovery time was not recorded.

### 3. Summary

Assess whether Cognito and DynamoDB rate-limiter required-text readers should
reuse an existing helper or a small shared operation. Preserve their present
acceptance rules and separate reports; do not create a larger abstraction merely
to remove a few repeated lines.

### 4. Background

The user requested a sub-agent inspection after discussing generic and local
configuration checks. That inspection, checked against the source by the parent,
found equivalent `requiredEnv()` reading/acceptance logic in two adapters.
Both accept nonempty strings and distinguish absent values from empty strings.
Both currently accept whitespace-only strings. Their error/report identities
differ because the adapters own different failures.

The parent recommended this as a smaller consolidation candidate, not an urgent
runtime defect. The user asked to record it. Replacing these readers with Core's
stricter text schema would change behaviour, so a decision on sharing must first
establish equivalent inputs, results and failure handling.

### 5. User stories

- As an adapter maintainer, I need the reading/checking work in
  `platform/adapters/aws/auth/cognito/src/index.ts` and
  `platform/adapters/aws/security/dynamodb-rate-limiter/src/index.ts` compared
  with existing Core/Platform configuration helpers, so shared mechanics have
  one owner where that genuinely reduces maintenance. Identify the precise
  shared owner and dependency impact during planning, rather than assuming
  adapters should import each other's private readers.
- As a caller, I need adapter-specific error codes, messages and diagnostics
  retained locally, with missing/empty distinctions, read order and accepted
  strings unchanged. A later whitespace-policy change is a separate decision.
- As a reviewer, I need an evidence-backed choice to extract/reuse or retain
  the small local readers, applying DIAG-003's reuse criteria. Any no-change
  outcome must explain the cost/benefit and must not be labelled an implemented
  consolidation.

### 6. Acceptance criteria

#### Code

- [ ] Record the existing helpers considered, current behaviour and dependency
  costs. Choose an equivalent shared operation if justified; otherwise document
  why retaining these small local functions is preferable. This is an assessment
  task with a possible no-change outcome, not a mandatory new helper.
- [ ] If consolidating, migrate both real adapters and all affected exports,
  callers, tests and review records. Keep local reporting ownership and preserve
  nonempty-string acceptance, missing versus empty, whitespace-only acceptance,
  messages, diagnostic identities and source access behaviour. No raw supplied
  value is newly included in reports and no provider work is added.

#### Harness

- [ ] Use DIAG-003's documented reuse-versus-local decision. Record why Core's
  stricter text validation is or is not applicable; do not force equivalent-looking
  inputs through a helper with different behaviour or duplicate requirements
  under docs. No separate gate or blanket import rule is needed for two readers.

#### Regression fixtures

- [ ] If consolidating, extend
  `platform/adapters/aws/auth/cognito/tests/cognito-adapter-runtime.test.ts` and
  `platform/adapters/aws/security/dynamodb-rate-limiter/tests/dynamodb-rate-limiter-runtime.test.ts`
  for absent, empty, whitespace-only and ordinary strings through actual callers.
  Assert exact local failure identities and that rejected required input does
  not reach dependent provider work. A replacement that silently trims/rejects
  previously accepted text must fail the compatibility expectations.
- [ ] Verify affected dependency boundaries and shared-helper use, then complete
  focused and proportionate selected local checks. For a no-code-change decision,
  record the reviewed source/test evidence and why new executable fixtures are
  not applicable; do not claim an extraction or newly passed runtime proof.
  All implementation/tests are planned; no cloud activity is authorized.

Evidence and update history:

- 2026-11-01T16:14:28+00:00 (Europe/Dublin): recorded at the user's request as a
  secondary improvement candidate. The functions and differing report owners
  were inspected, not modified. Assessment, implementation and test outcomes
  remain uncompleted.

## DIAG-007 — Assess sharing the server and worker environment-copying operation

Status: open

### 1. ID

DIAG-007

### 2. Date/time raised

2026-11-01T16:14:28+00:00 (Europe/Dublin).

This is the recording time. The preceding inspection found this repetition;
its exact discovery time was not recorded.

### 3. Summary

Assess whether one small Platform-owned helper should copy supplied values for
the environment names selected by server and worker startup. Leave their
different permitted names and configuration policies with their respective
owners; retain the local loops if extraction would add unnecessary complexity.

### 4. Background

The requested sub-agent inspection found that server and worker each implement
`configRecordFromEnv()`: iterate permitted names plus caller-supplied additional
names, copy defined values and omit absent ones. The parent inspected both
functions and explained that their copying work repeats while their selected
names legitimately differ.

The user asked to record the recommended follow-up. This is small, low-priority
maintenance repetition, not proof that startup configuration is broken. Copying
values is also not the same as validating them, so this task must not imply
that sharing the loop gives every copied value a validation requirement.

### 5. User stories

- As a Platform maintainer, I need the loops in
  `platform/server/src/configuration/runtime.ts` and
  `platform/workers/src/main.ts` assessed for a shared configuration-loading
  helper, so a common operation can have one owner if the benefit warrants it.
  Inspect existing `platform/config/src/` and Core source-copying contracts;
  choose any helper home/API during implementation without adding environment
  loading to Core or merging the two callers' permitted-name lists.
- As a server or worker caller, I need configured values, extra-name handling,
  omission of absent values, empty-string preservation, access order and later
  validation/default/reporting behaviour unchanged. Inventory affected package
  exports, dependencies, startup consumers and tests before editing.
- As an agent making this decision, I need DIAG-003's reuse criteria applied
  proportionately, with an explicit no-change option if a shared helper causes
  more complexity than the small repeated loops. Do not expand into shell
  readers, imported tools or the retiring platform target.

### 6. Acceptance criteria

#### Code

- [ ] Record the benefit/dependency assessment and choose shared copying or a
  justified no-change outcome. Do not introduce a new configuration framework
  or present copying as validation.
- [ ] If extracting, both server and worker use the shared operation but retain
  their own selected names. Preserve additional-key handling, copied values,
  omitted undefined entries, empty strings, source access behaviour and public
  results. Update every affected consumer/export/dependency/review together.

#### Harness

- [ ] Use DIAG-003's distinction between reusable mechanics and consumer-owned
  requirements to review the decision. No new domain rule or executable gate
  is needed merely for a copying helper; any applicable governance change stays
  in the existing harness owner, not duplicated in AGENTS or docs.

#### Regression fixtures

- [ ] If extracting, extend relevant server and worker configuration/startup
  fixtures, including `platform/server/tests/configuration-runtime.test.ts` and
  `platform/workers/tests/platform-workers-process-runtime.test.ts`, to verify
  each caller's selected names, extra names, absent and empty values, exclusion
  of unrelated keys and unchanged downstream configuration/diagnostics.
- [ ] Show both real startup paths use the shared operation and preserve their
  distinct lists. Run affected boundary/focused tests and proportionate selected
  local checks only after the connected change is reviewed. For a no-code-change
  outcome, record evidence and why new executable fixtures are not applicable;
  do not claim a refactor or runtime proof that was not performed. All future
  checks are planned; no live deployment is required or authorized here.

Evidence and update history:

- 2026-11-01T16:14:28+00:00 (Europe/Dublin): recorded at the user's request as a
  low-priority assessment, not mandatory extraction. The existing loops remain
  unchanged; no implementation, harness gate or new fixture was introduced.

## DIAG-008 — Make the Core config index expose functionality, not implement it

Status: done

### 1. ID

DIAG-008

### 2. Date/time raised

2026-11-01T17:04:07+00:00 (Europe/Dublin).

This is the recording time. The preceding teaching discussion identified the
mixed responsibilities; its exact discovery time was not recorded.

### 3. Summary

Move configuration implementations and type definitions out of
`packages/core/src/config/index.ts` into appropriately named files. Keep
`index.ts` as the public export list, preserve existing imports and behaviour,
and establish the same separation in the owning agentic architecture guidance.

### 4. Background

While reviewing the config README with the assistant, the user could not clearly
distinguish `index.ts` from `issues.ts`. Inspection showed that `index.ts` both
implements readers, checks, source copying and error construction, and exposes
functions and types from the other files. Explaining it as a public entrance
alone would therefore misrepresent what the current code actually does.

The user proposed that a module's public index should only expose functionality,
with implementation in dedicated files. The assistant agreed, and the user
requested a backlog task for the structural cleanup. This is a clarity and
responsibility-separation correction, not a finding that existing checks are
broken. Earlier architecture plans already describe export-only indexes for
other modules; reconcile that guidance rather than creating competing rules.

### 5. User stories

- As a Core maintainer, I need the implementations and public types currently
  declared in `packages/core/src/config/index.ts` moved into named files within
  the same module, so the index shows what callers can use rather than how it
  works. Choose a small, cohesive file layout during implementation; do not
  create one file per function or change the roles of `issues.ts`, `schema.ts`,
  `diagnostics.ts` and `source-observation.ts` merely to rearrange the module.
- As an existing caller, I need `@kanbien/core/config` and supported public
  exports to remain unchanged. Inventory direct and indirect imports, package
  exports, tests, diagnostic review records and any source-path-sensitive tools.
  Update affected consumers together; internal files such as `schema.ts`, which
  currently imports `ConfigSource` from `./index`, should use the actual owning
  file where appropriate without introducing circular runtime dependencies.
- As an agent making future changes, I need the owning `.agentic/03.product/`
  architecture guidance to require public indexes to contain exports only, with
  implementation and declarations in dedicated files. Select the exact existing
  owner and proportionate check during implementation; do not make a README or
  AGENTS the authoritative rule. Apply the policy to future work without silently
  authorizing cleanup of every existing index in the repo.
- As a learner, I need `packages/core/src/config/README.md` updated to describe
  the resulting files, moved exports, examples and diagram accurately, following
  the README-writing skill. Preserve its plain-language explanations and public
  usage examples; distinguish implementation locations from import locations.

### 6. Acceptance criteria

#### Code and connected consumers

- [x] Record a bounded file/consumer inventory and cohesive destination layout
  before editing. Config's public `index.ts` contains only export declarations;
  move its functions, private helpers, constants and type/interface definitions
  to appropriate files without adding startup work or changing dependencies.
- [x] Preserve all supported exported names and import paths, runtime behaviour,
  type relationships, source-copying behaviour, errors and diagnostic identities,
  details, privacy and ordering. This structural task does not change validation
  policy, reason lists or database port bounds; DIAG-001 and DIAG-004 own those
  separate changes.
- [x] Reconcile affected internal imports, package/test setup, source-matched
  reviews and documentation. The README explains the new layout rather than
  claiming implementation still lives in the index. Do not rewrite historical
  evidence or unrelated modules as an incidental part of this task.

#### Harness

- [x] Establish one authoritative rule in the owning agentic architecture
  standard: public module indexes expose functionality; dedicated files own
  implementations and declarations. Route relevant implementation/review work
  to that owner, reconcile existing guidance, and record any deliberate exception
  explicitly rather than silently allowing mixed responsibilities.
- [x] Reuse an existing structure/boundary check if suitable, or add the smallest
  owning check needed to reject implementation in governed public indexes.
  Identify coverage and treatment of legacy indexes explicitly; a filename alone
  must not trigger an unapproved repo-wide refactor. Distinguish executable
  enforcement from review judgement; no broad new architecture framework.

#### Regression fixtures

- [x] Preserve and run affected public-import/type and behaviour cases in
  `packages/core/tests/config-types.test.ts`, `config-runtime.test.ts` and
  `diagnostic-record-runtime.test.ts`, plus actual affected consumer tests.
  Verify unchanged successful and failed reads, source exceptions and diagnostic
  records through the existing public import, not only private destination files.
- [x] The owning structure-check fixtures accept a valid export-only index and
  reject implementation moved back into a governed index. Keep ordinary
  implementation files valid and test any approved legacy/exception handling.
  Exact check/fixture paths are selected during planning; none are claimed to
  exist or pass by recording this task.
- [x] After connected edits and source review, pass focused tests, then the
  proportionate registered checks selected for the final changed paths. Record
  actual proof before closure; no dependency installation, deployment or cloud
  operation is authorized by this backlog entry.

Evidence and update history:

- 2026-11-01T17:04:07+00:00 (Europe/Dublin): recorded at the user's request
  after the index-versus-issues walkthrough. Confirmed mixed implementation and
  export responsibilities in the current index and the schema's type import.
  This entry records planned cleanup and prevention only; all criteria remain
  unchecked and no runtime or harness policy was changed.
- 2026-11-01T19:32:36+00:00 (Europe/Dublin): reconciled earlier implementation
  evidence rather than rewriting the original recording note. The index is now
  export-only; implementations/types are in flat types.ts, source.ts and
  value-readers.ts files, with schema's internal type import corrected. The
  shared syntax checker and 23 pinned legacy allowances are implemented; other
  modules were not refactored. Six registered focused checks passed earlier:
  module-index-structure, module-index-structure-regression, core-runtime,
  platform-config-runtime, diagnostic-catalog-readers and
  check-selection-repository-contracts. These are historical results, not proof
  of the newly proposed layout. Broader impact proof was not completed, and the
  selector-fixture source review became stale after lifecycle metadata changed;
  reconcile it after source review/preparation before final proof. Status is
  in-progress, not done; acceptance criteria are not blanket-checked.
  The expanded config architecture/context proof is mapped separately in
  [its implementation plan](../../../03.product/plans/implementation/core-module-architecture-config-proof.md).
  Complete layout and changed response formats still require agreement. This
  update changes no runtime source, review hash, diagnostic contract or fixture.

- 2026-11-01T21:33:07+00:00 (UTC): original DIAG-008 cleanup completed. The
  approved config contract/domain layout and its complete responsibility map
  are recorded in the linked implementation plan. All 42 public names/signatures
  and existing behavior are preserved; source reviews are fresh (343 source
  bindings, zero stale). Nine new registered focused checks passed, followed by
  28 affected-consumer entries (22 executed, six reused); nested aggregates reused
  their members. The export-only/dependency fixtures reject regressions in config
  and an independent future module. Actual startup context/delivery proof belongs
  to the separately identified expanded goal, not a redefinition of this entry.
  See the session journal for commands, durations and outcome-only closeout checks.
  The full diagnostics-project impact gate, container/live proof and remaining
  DIAG-002/003/004 work are not closed by this task. Historical evidence above
  remains historical; no installation, cloud operation or Git publication.

## DIAG-009 — Retire PostgreSQL's redundant configuration compatibility file

Status: done — local retirement completed on 2026-11-03.

### 1. ID

DIAG-009

### 2. Date/time raised

2026-11-03T08:51:50+00:00 (Europe/Dublin).

This is the backlog recording time. The preceding explanation and inspection
occurred in this conversation; their exact message timestamps were not recorded.

### 3. Summary

Remove `platform/adapters/aws/persistence/postgresql/src/config.ts` after
redirecting its remaining internal consumers to the existing configuration
owners. Preserve the adapter's public package exports and all checking,
diagnostic and runtime behaviour.

### 4. Background

During the configuration walkthrough, the user asked why each database adapter
still has a configuration file alongside its new configuration folder. The
assistant explained that these files forward imports to the moved code; they
do not provide a second checker. The user then asked whether they could be
removed, starting with PostgreSQL, and requested this backlog entry after the
read-only inspection.

PostgreSQL's `src/config.ts` contains only re-exports from
`src/configuration/index.ts`. Nine source files still depend on it. The package
manifest exposes only the main package entry, not a `/config` subpath, and no
other active executable deep-file consumer was found in the inspected runtime,
infra and tooling roots. This supports retiring the internal bridge after a
fresh consumer check; it is not proof about unknown code outside this repo.
Documentation, teaching links and the diagnostic review ledger also name it.

The earlier ownership refactor deliberately retained imports to limit that
slice's changes. This follow-up retires that bridge explicitly; it does not
redo the configuration implementation or imply the completed checks were
worthless. DynamoDB removal is being discussed separately and is not included
automatically. Recording this task does not authorise deleting either file.

### 5. User stories

- As a PostgreSQL adapter maintainer, I need `src/index.ts` to expose the same
  public names directly from `src/configuration/index.ts`; `connection.ts`,
  `outbox.ts`, `processing.ts`, `lineage.ts`, `credentials.ts`,
  `rds-iam-authentication.ts`, `records.ts` and `migrations.ts` to use that same
  configuration submodule interface. Its implementation still belongs in the
  contract/domain files. The first proposed direct-private-file mapping was
  corrected against the existing module boundary before final verification.
  All these paths are within
  `platform/adapters/aws/persistence/postgresql/src/`. Then the redundant
  `config.ts` can be removed without leaving a competing implementation or
  another forwarding file under a different name.
- As a caller of `@kanbien/platform-adapter-aws-persistence-postgresql`, I need
  the same exported names, function identities within the resulting package,
  types and results. Inventory direct/indirect imports, source-sensitive tests,
  package/build inputs and actual core-server composition before deleting the
  bridge. Do not alter dependencies, SQL, credentials, TLS, validation rules,
  diagnostic definitions/catalogues or deployment values for this cleanup.
- As a learner, I need active links and explanations corrected in the adapter
  `README.md`, `src/configuration/README.md`, `packages/core/src/config/README.md`
  and the affected current-source links in
  `docs/education/lesson-plans/diagnostics-repository-walkthrough/file-index.md`
  and `lessons/064-persistence-postgresql-src.md`. Preserve clearly historical
  snapshot attribution and session evidence rather than rewriting history.
- As an agent making future refactors, I need compatibility bridges justified
  by actual callers/contracts and given an explicit retain-or-retire decision
  in the existing plan. Apply the owning
  [module structure standard](../../../03.product/standards/public-module-structure.md)
  and [path migration workflow](../../../01.harness/workflows/migrate-artifact-paths.md),
  updating only affected review records in
  `scripts/repo/diagnostic-coverage/reviews.v1.json`. A wrapper should not become
  permanent solely because no one revisited its purpose.

### 6. Acceptance criteria

#### Code and connected consumers

- [x] Record current callers/public contracts and the nine source-file changes
  above in the existing implementation plan before editing. Recheck for newly
  added or computed imports; absence from a text search alone is not proof.
- [x] Redirect all actual consumers, then remove the bridge. No active runtime
  import or emitted declaration depends on `src/config.ts` or `config.js`.
  Preserve the supported package-root API and configuration implementation;
  do not widen this into DynamoDB, index design or retiring-target migration.
- [x] Reconcile live documentation links, source-sensitive fixtures and the
  deleted/changed review bindings. Keep historical evidence explicitly
  historical. Existing diagnostic JSON remains byte-identical because this
  task changes import paths, not diagnostic meanings.

#### Harness

- [x] Reconcile the existing module-structure standard's compatibility guidance
  so refactors record why a bridge remains, its supported consumers and its
  retirement condition. Reuse an existing equivalent instruction if present;
  otherwise add a bounded clarification to that owner, not AGENTS, a README,
  new registry or a blanket automatic bridge-deletion rule.
- [x] The migration/reference review covers public package exports, internal
  imports, generated output, review ownership and active explanatory links.
  Record retirement/compatibility disposition and recovery; do not claim a
  source scanner can prove that unknown external consumers do not exist.

#### Regression fixtures

- [x] Compile to fresh temporary output with the old source absent. Old cached
  `config.js` must not conceal a missed import. Existing adapter runtime/type
  and dependency-boundary tests pass through the retained package root; public
  exports/types and accepted/rejected results remain unchanged.
- [x] An intentionally stale `./config` import must fail the fresh compilation
  or import-resolution proof. Use existing fixtures/a bounded temporary case,
  not a new general-purpose compatibility checker.
- [x] Freshly compile the actual core-server persistence composition and run
  its existing configuration fixture. Preserve the existing diagnostic and
  failure-before-dependent-work assertions; no Docker/database/cloud run is
  required just to establish import continuity.
- [x] Finish connected changes and source review before final focused units.
  Existing registered candidates are `postgresql-connection-diagnostics` and
  `module-index-structure`; reconcile their actual coverage with the final
  changed paths. Broader integration/package/live proof remains at the agreed
  stable-batch/owning stages. Execution evidence and its limits are recorded below.

Evidence and update history:

- 2026-11-03T08:51:50+00:00 (Europe/Dublin): recorded at the user's request
  following the read-only PostgreSQL bridge inspection. Confirmed nine source
  consumers, package-root-only exports and active documentation/review paths.
  All acceptance criteria remain unchecked. No adapter, harness rule, fixture,
  package, deployment or Git state was changed by recording this entry.



- 2026-11-03T09:23:56+00:00: local implementation and final proof complete.
  Nine source callers now use the supported configuration submodule index;
  the sibling bridge is removed. Existing checker/requirements/assembly bodies,
  public names/types and all diagnostic catalogue bytes remain unchanged.
  Fresh adapter and actual core-server builds, adapter runtime/boundary proof,
  explicit retired-file resolution failure and 561 target rejection-before-pool
  cases passed. Final registered PostgreSQL/DynamoDB/structure units all passed
  once on 50 frozen inputs with no concurrent changes. Existing standard now
  requires compatibility purpose, consumers and retirement conditions; boundary
  fixtures reject this bridge's return and unresolved relative references.
  The migration helper still flags clearly historical task/course attribution;
  eight reviewed documentary matches across both removals are recorded in the
  implementation plan, not claimed as a green helper result. Active current-
  source links resolve. Broader integration remains at its agreed boundary.
  The original two files are recoverable from the temporary task snapshot
  `/tmp/config-bridge-retirement-KbjvSK/before.tar`; no user work was discarded.

## DIAG-010 — Retire DynamoDB's redundant configuration compatibility file

Status: done — local retirement completed on 2026-11-03.

### 1. ID

DIAG-010

### 2. Date/time raised

2026-11-03T09:11:33+00:00 (Europe/Dublin).

This is the recording time; the preceding explanation did not record its own
exact discovery timestamp.

### 3. Summary

Remove the forwarding configuration file after redirecting its callers to the
existing configuration contracts and checker. Preserve the public package API.

### 4. Background

While learning about the PostgreSQL configuration folder, the user noticed that
an older forwarding file still sat beside it. The assistant found the equivalent
DynamoDB arrangement after its configuration-folder migration. The user asked
for both removals locally. These files do not implement additional checking;
keeping them without a supported consumer makes ownership harder to follow.

### 5. User stories

- As an adapter maintainer, use `src/configuration/index.ts` for adapter type imports and
  public re-exports, preserving the configuration submodule boundary, rather
  than a second forwarding file beside the folder.
- As a package consumer, retain the same root exports, types, accepted/rejected
  inputs and diagnostic packets. Do not widen DynamoDB's supported use cases.
- As a reviewer, see the actual public API exercised by fixtures and accurate
  README/current-source links, without erasing historical snapshots.

### 6. Acceptance criteria

Code and connected consumers:

- [x] Remove only the adapter's obsolete `src/configuration.ts`; redirect its
  root exports and five internal type consumers. Keep the existing checker,
  contract files, package manifest, database operations and diagnostics unchanged.
- [x] Update the runtime fixture's old-file aliases to package-root aliases;
  keep root/grouped identity and compatible-type proof and every existing
  validation/diagnostic assertion. Update active documentation and review hashes.
- [x] Keep N01B persistence/index policy, retiring-target adoption and CloudWatch
  work deferred. A folder import `./configuration` can still resolve the folder;
  do not mistake that for dependence on the removed file.

Harness:

- [x] Apply the same bounded compatibility-bridge guidance as DIAG-009 in the
  existing public-module standard. Do not add another registry or new AGENTS rule.
- [x] Reconcile existing diagnostic review ownership and retain partial/deferred
  dispositions; no unchecked blanket adoption or unreviewed hash reset.

Regression fixtures:

- [x] Fresh temporary compilation contains `configuration/index.js`, but not
  the removed sibling `configuration.js`. An explicit retired-file import fails
  while real public exports and all existing runtime/boundary assertions pass.
- [x] Existing boundary fixtures prevent the sibling shim from returning and
  reject unresolved relative source imports. Public types compile unchanged.
- [x] Complete connected changes/review before final registered focused units:
  `dynamodb-persistence-runtime` and the shared `module-index-structure` check.
  Broader integration remains at the agreed stable-batch boundary.

Evidence and update history:

- 2026-11-03: recorded and authorised alongside DIAG-009. Implementation sequence,
  consumer inventory, checks and timings are kept in the configuration ownership
  implementation plan. At recording, criteria were planned; completion evidence follows.

- 2026-11-03T09:23:56+00:00: local implementation complete. Root exports and five
  adapter type consumers now use configuration/index; the sibling file is gone.
  Runtime fixture uses the actual package-root aliases, retains compatible-type
  and checker-identity proof and all previous diagnostic assertions. Fresh
  compilation and runtime/boundary tests passed; explicit configuration.js
  resolution fails while the retained folder index resolves. Final registered
  DynamoDB/structure proof passed alongside PostgreSQL; fifty frozen task and
  catalogue states were unchanged. Harness, README/current-source links and
  affected review hashes reconciled without changing review status/debt.
  The same historical-reference-helper limitation as DIAG-009 is recorded,
  not bypassed. N01B, DIAG-006/007, CloudWatch and retiring-target work remain
  deferred. No dependency, index policy, diagnostic or database operation changed.

## DIAG-011 — Share optional diagnostic delivery without centralising diagnoses

Status: done — bounded local consolidation completed on 2026-11-04.

### 1. ID

DIAG-011

### 2. Date/time raised

2026-11-04T14:16:37+00:00 (Europe/Dublin).

This is the recording time. The preceding review took place in this conversation;
its exact discovery timestamp was not recorded.

### 3. Summary

Provide one Core-owned mechanism for attempting optional diagnostic delivery and
containing receiver failures. Keep diagnostic meanings, approved definitions,
evidence selection and operation context with their existing owners.

### 4. Background

After the SQS configuration slice, the user asked whether all the new work was
really specific to the adapter. The assistant inspected SQS reporting alongside
Core queue and Platform config, persistence and observability helpers. They
repeat handling of immediate reporting exceptions and later rejected results.
The user and assistant agreed to share that mechanism, not merge their different
diagnostic meanings or introduce a new reporting framework. The user authorised
recording and implementing this correction locally.

### 5. User stories

- As a Core maintainer, I need named implementation in
  `packages/core/src/diagnostics/reporting/delivery.ts`, exposed through
  its public index, so compatible modules do not independently maintain optional
  delivery mechanics. Existing `record.ts` remains the owner of record validation
  and approved evidence selection. Delivery alone does not validate contents.
- As an adapter or Platform maintainer, I need SQS configuration reporting,
  Platform config validation, Platform persistence observers and Platform's
  optional reporter wrapper to reuse that mechanism. Preserve original results,
  error identity, record order, callback receivers, opt-outs and supported return
  values. Leave SQS limits, diagnostic definitions and context local. Preserve
  Platform's separate confirmed/unavailable log-write status observation.
- As an agent adding diagnostics, I need the existing safe-diagnostic standard
  to require this reuse, with actual caller fixtures rejecting a return to local
  copied delivery. Do not add a blanket import scanner or a second registry.
  The pinned legacy Core queue index is an assessed existing consumer, not an
  authority to change its implementation allowance or refactor the whole module.

### 6. Acceptance criteria

#### Code and connected consumers

- [x] Implement shared single/list delivery, preserving the receiver's returned
  value for existing wrappers while containing synchronous and asynchronous
  reporting failures. List delivery continues after a receiver failure, does not
  await, retry, log raw errors or change the original operation outcome.
- [x] Migrate the compatible named callers, retaining their definition checks,
  evidence selection, independent source companions, context and original return/
  throw behaviour. Record justified no-change cases, including Core queue's
  pinned index and Platform's status-bearing sink-completion observer.
- [x] Public exports, package compilation, affected source reviews and bounded
  README explanations agree. No diagnostic definition/JSON, configuration policy,
  dependency, target wiring, worker policy or deployment change is introduced.

#### Harness

- [x] The existing safe-diagnostic standard owns the reuse requirement and its
  limits. Review requires an explicit reason for different delivery semantics;
  schema checks and source hashes are not claimed to detect all duplication.

#### Regression fixtures

- [x] Shared runtime/type tests cover exact call order, return identity, receiver
  binding, immediate throws, native/rejected/shadowed promises, other thenables,
  absent receivers and continuation. No unhandled reporting rejection escapes.
- [x] Actual SQS and Platform config/persistence/observability caller tests prove
  shared-helper use and unchanged original results, selected records/context and
  privacy. A substituted shared delivery helper must affect those real callers;
  merely matching outputs from independent copies is insufficient.
- [x] Complete connected source review before final focused registered checks;
  record timings and final frozen inputs in the existing session journal. Broad
  integration remains at the agreed stable-batch boundary. No install, Docker,
  cloud operation, deployment or Git mutation is authorised by this entry.

Evidence and update history:

- 2026-11-04T14:16:37+00:00 (Europe/Dublin): recorded and authorised following
  the reporting-ownership walkthrough. Inventory, predicates and activity are in
  the session journal; implementation and verification criteria remain planned.
- 2026-11-04T14:23:56+00:00 (Europe/Dublin): the initial domain/reporting path
  activated structural adoption of the legacy diagnostics module, exposing its
  existing definition-to-own-index cycle. Apply the standard's bounded older-
  module treatment: the new capability lives in a cohesive reporting/delivery.ts
  file; no pinned implementation or structural allowance is changed. This is
  not a claim that the legacy diagnostics module has completed structural adoption.
- 2026-11-04T14:33:48+00:00 (Europe/Dublin): local implementation and proof
  complete. The shared single/list helpers are public; SQS configuration,
  Platform config validation, persistence observation/option resolution and the
  optional Platform reporter wrapper delegate to them. The pinned Core queue
  implementation and status-bearing log completion remain deliberate no-change
  cases, not claims of repository-wide removal of all duplicate delivery code.
  The owning standard and two README explanations are updated. All seven final
  registered units passed once on 19 frozen paths: core-runtime,
  diagnostic-catalog-readers, module-index-structure, platform-config-runtime,
  platform-observability-runtime, platform-persistence-runtime, sqs-queue-runtime.
  All 20 catalogues are unchanged; adoption and full impact planning have zero
  findings. The session journal records exact timings, corrections, commands and
  evidence at /tmp/diag011-delivery-CtawIw. Broader integration stays deferred;
  no installation, container/cloud operation, deployment or Git mutation ran.

## DIAG-012 — Make diagnostic construction and selection loss explicit

Status: done

2026-11-05T01:39:29+00:00 (UTC): the bounded implementation, imported-tool
reconciliation and final local verification are complete. All 53 registered
checks passed (32 executed and 21 reused against matching inputs in the resumed
pass). The [consolidated review](governed-diagnostic-coverage.md#consolidated-reconciliation--2026-11-05)
records actual consumers, proof anchors and observation limits; the
[session verification record](../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/README.md#diag-012-final-local-verification--2026-11-05)
records exact check identities and timings. This closes reason/packet preservation
and processing-loss safeguards in the agreed scope, not DIAG-013 sink delivery,
private SDK observations that are not exposed, universal OS-failure interception,
upstream installation, container qualification or deployment acceptance.

2026-11-04T21:36:10+00:00 (UTC): implementation approved after the requested
checkpoint commit `e94628adbb5f09e8b25b18fcb4deb9336990bf89`.
The expanded prepared scope remains controlling; no implementation completion
or new runtime proof is claimed by this status change.

### 1. ID

DIAG-012

### 2. Date/time raised

2026-11-04T19:38:47+00:00 (UTC).

### 3. Summary

First, trace each supported failure reason from the operation's actual result
through to the diagnostic received by its error-handling caller, and fix any
broken connection. A valid supported reason must produce the correct diagnostic,
not undefined, a misleading generic explanation, or the wrong item attribution.

Second, make genuinely unexpected failures while preparing or preserving that
diagnostic explicit. That fallback is a secondary safeguard, not a substitute
for making ordinary supported failure cases work. Keep sensitive information
out and preserve original workload outcomes. DIAG-013 owns reporting delivery.

The user expanded this task on 2026-11-04 to include CloudWatch, DynamoDB and
imported-tool diagnostics. The controlling
[preparation and implementation sequence](governed-diagnostic-coverage.md#diag-012-preparation-and-expanded-scope--2026-11-04)
names the file groups, imported-source census, normal-failure traces, tests,
approval boundary and completion gates. Earlier deferral notes below remain
historical. Implementation was subsequently authorised and is now complete within
the bounded scope and proof recorded above; no further go-ahead is outstanding.

### 4. Background

During this chat's repository-wide diagnostic review, the user asked whether
known reasons could still disappear. The assistant inspected the shared pipeline
and existing consumers. Core's constructor returns an explicit
DIAGNOSTIC_RECORD_INVALID result, but Events/Audit and Runtime wrappers can
reduce construction failure to absent evidence. Core evidence selection also
returns absence for both missing evidence and rejected/unregistered evidence.
Those safety rejections are valid; their indistinguishable outcome is the gap.

A current-source exploratory probe preserved a normal event reason, then
injected failure into its record builder and observed undefined despite supplying
the known reason. This demonstrates a fault-handling weakness, not evidence that
ordinary valid event diagnoses currently fail. Frozen/primitive error attachment
also requires checking an independent observer path before declaring loss.
The [audit inventory](governed-diagnostic-coverage.md#remaining-work-audit--2026-11-04)
records the evidence and limits. No runtime changes were authorised here.

In the subsequent discussion, the user clarified that the original concern was
an operation correctly returning a supported reason but its diagnostic becoming
undefined. The assistant had overemphasised failures of diagnostic processing
itself. The user asked to correct this entry: normal reason-to-diagnostic
coverage comes first, and fault-handling comes second. The earlier injected
failure probe does not establish whether all normal supported reasons survive.
At that point, the inventory and real-caller tests remained to be completed;
the total number of broken mappings or affected operations had not been established.
The dated completion record above now links their bounded reconciliation and proof.

### 5. User stories

- As an investigating agent, I need every supported failure in the agreed
  operation scope to retain its exact safe meaning and relevant item/operation
  context in the resulting diagnostic. Start from actual checks and returned
  failures, not only a shared reason-name list or existing diagnostic catalogue.
  A name being available globally does not make it applicable to every operation.
  Record the per-operation trace in the existing audit/implementation inventory,
  not a second runtime mapping registry.
- As a capability maintainer, I need missing mappings, incompatible definition
  selections, incorrect item attribution, loss of precise reasons and discarded
  packets corrected at their owning code. Inspect checker results, mapping
  functions, selected code/version definitions, wrappers, catalogue registration
  and the actual error-handling caller together. For the configuration reference,
  start with PostgreSQL's configuration requirements, Core config checking,
  Platform loading and
  `infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts`;
  then trace the structured result used by the real startup/task caller.
  Core diagnostics owns representation, not PostgreSQL or task-specific meaning.
- As an investigating agent, I need an explicit, bounded diagnostic-processing
  outcome when known safe facts cannot be made into or selected as a record,
  rather than confusing that with no failure. Core owns
  `packages/core/src/diagnostics/record.ts`, `definition.ts`, `schema.ts`
  and public exports; capability owners still own the original diagnosis.
  Select an additive compatible interface during implementation, not a new
  global catalogue of every capability's reasons.
- As a maintainer of code that calls diagnostic functions, I need callers
  updated wherever they would discard the original reason, resulting packet or
  diagnostic-processing failure. Initial examples include
  `packages/core/src/events/observations.ts`,
  `packages/core/src/audit/observations.ts`,
  `platform/runtime/src/diagnostics.ts`,
  `platform/config/src/domain/validation.ts` and
  `platform/adapters/aws/persistence/dynamodb/src/observations.ts`.
  These examples are not the entire scope. Check the other relevant callers
  identified by the audit and explain whether each needs changing or already
  handles the result correctly. Review
  `packages/core/src/shared/diagnostics.ts` with those actual callers:
  attachment failure must not change throw identity, and an independently
  delivered record must not be falsely reported as lost.
- As a maintainer of strict readers, I need unknown definitions, hostile
  accessors, malformed fields and oversized evidence to remain rejected.
  Do not disclose rejected values, automatically select unrelated catalogues,
  remove bounds, or construct a recursive diagnostic failure cascade.
- As a CloudWatch consumer, I need configuration, recording and exposed SDK
  lifecycle reasons preserved through the adapter and Platform observability
  into the actual caller/reporter input. Owners are the adapter's
  configuration.ts, lifecycle-observation.ts and index.ts, with Platform-owned
  configuration/metric/lifecycle definitions and reporting boundaries. A failed
  export remains a failure observation even if flush resolves; hidden SDK
  failures must not be assigned invented causes or described as observed.
- As a DynamoDB consumer, I need configuration failures to identify the same
  field in both ordinary error details and the diagnostic, including both index
  names. Trace current command, cancellation, stored-attribute and reconciliation
  observations through the actual stores and results. The adapter owns provider
  interpretation; Platform persistence owns shared definitions. This includes
  the previously deferred oversized-index attribution correction, not new index
  design, full loading redesign or live database interchangeability.
- As a workbench user, I need established command failure reasons to survive
  child/parent parsing without exposing rejected values or native output.
  Inspect the 55 imported executables and five maintenance commands named in
  the preparation; update connected consumers, preserving successful protocols,
  exit codes, permissions, partial effects and operation ordering. A proposed
  local diagnostic exception is part of the implementation sign-off, not
  authority to change upstream repositories or reset installation hashes.

### 6. Acceptance criteria

#### Code and connected consumers

- [x] Establish the bounded operation inventory before fixing mappings. For
  every supported failure alternative, name the actual triggering check/input,
  returned reason and item, mapping function, diagnostic code/version and detail,
  selected catalogue/reader, wrappers and final error-handling caller. Include
  supported combinations and source failures where applicable. Record adequate,
  broken, intentionally different, deferred or still-unproved paths explicitly;
  do not claim repo-wide completeness from a sample of modules.
- [x] Reconcile the expanded CloudWatch, DynamoDB and imported-tool paths in
  the controlling preparation. Assign actual migrate/no-change/observation-limit
  dispositions with proof. Earlier deferral labels do not exclude these diagnostic
  paths now; unrelated integration, index design, remote delivery and deployment
  work retain their separate ownership.
- [x] Fix each demonstrated broken connection so ordinary supported failures
  produce and retain the correct diagnostic. A generic fallback must not replace
  a precise supported reason merely to make a test pass. Establish whether the
  defect is in the producer, mapping, definition selection, registration or
  caller before choosing the owning change; do not loosen strict readers to
  accept arbitrary reasons or unrelated records.
- [x] For every proposed fix, record its owning layer/file and why: Core owns
  reusable checking/record mechanisms, capabilities own their meanings,
  adapters own service-specific interpretation, and entrypoints supply concrete
  selection/bindings/context. Follow the
  [module structure standard](../../../03.product/standards/public-module-structure.md#dependency-direction-and-diagnostic-ownership);
  do not fix a dependency's missing rule with an entrypoint-owned copy or place
  service-specific meanings in shared Core diagnostics.
- [x] Record the shared mechanism considered and whether to reuse it or retain
  a genuinely different local mapping. Correct shared defects once and prove
  affected callers, rather than copying fixes across adapters or forcing
  different behaviours through one universal mapper.
- [x] Keep accepted shapes, reusable constraints and diagnostic meanings with
  their contracts; checking/mapping work with the relevant implementation;
  public indexes export-only. Follow responsibility-based folder organisation
  for touched/new work without refactoring unrelated legacy modules. Runtime
  definitions remain authoritative; generated JSON, selected readers and
  affected documentation are reconciled, not edited into competing definitions.
- [x] Keep supported reason meanings and item/operation attribution intact.
  Preserve declared first-failure versus collected-report behaviour and bounds;
  any legitimate truncation remains explicit. Do not invent continuation,
  diagnoses for checks that never ran, or a new validation policy.
- [x] Trace retained compatibility helpers that intentionally return undefined
  to their actual callers. Where production uses a structured-result alternative,
  prove that wiring; do not remove a supported compatibility interface or label
  it a production loss solely because its return type permits undefined.
- [x] Inventory actual constructor/selector/attachment results and downstream
  consumers; distinguish safe absence, explicit opt-out, rejection and processing
  failure. Do not classify every undefined return as a defect.
- [x] Provide and consume explicit safe outcomes for demonstrated loss paths,
  with additive compatibility where needed. Preserve existing record identities,
  ordinary accepted/rejected inputs, original return/throw identity and work
  ordering. Do not assert an unobserved operation cause or effect.
- [x] Preserve independently valid source/companion evidence. If the full
  original detail cannot safely survive, make that unavailability explicit
  without bypassing validation or copying raw detail.
- [x] Reconcile every affected owner/export/caller/test/catalogue reader; record
  justified no-change consumers. Generated catalogue changes follow existing
  versioning rules only if new definitions are actually required. Fix a mapping
  or registration error without gratuitously changing definitions. If an owning
  definition genuinely needs an additional allowed reason, add a version and
  retain supported historical readers rather than silently widening it.

#### Harness

- [x] Make the existing safe-diagnostic standard and coverage workflow require
  normal reason-to-diagnostic coverage before fallback proof. A new/changed
  supported checker reason must identify its definition/mapping, affected
  wrappers/catalogues and real-caller assertion. Reuse the current inventory
  and registered fixtures; no new global reason registry or blanket import rule.
  Instruction update completed on 2026-11-04 in the standard's
  [supported reason preservation](../../standards/require-safe-diagnostic-record.md#supported-reason-preservation)
  section and the existing coverage workflow. This checks off the instruction
  change only, not runtime adoption or the planned behaviour fixtures.
- [x] Extend the existing safe-diagnostic standard and coverage workflow to
  distinguish deliberate exclusion from diagnostic-processing loss, and require
  the corresponding fault-injection consumer assertion. Preserve privacy,
  original workload outcome and no-replay requirements; no new registry or
  blanket catch/undefined ban.
- [x] Update only reviewed ownership records with actual proof; a passing source
  hash check is not a semantic completeness claim.

#### Regression fixtures

- [x] For each inventoried supported reason, supply an ordinary input that
  genuinely triggers the operation's check, call the real checking/loading
  path, and assert the exact diagnostic code, version, reason and applicable
  item/operation context at the error-handling caller. The normal-path tests
  must not depend on replacing the diagnostic builder with a throwing stub.
  Existence of some error or some diagnostic is insufficient proof.
- [x] Cover successful inputs without spurious failure diagnostics, distinct
  failure alternatives and supported multiple failures. Preserve report order,
  first-error policy and sensitive-value exclusion. Verify dependent work is
  prevented where the existing operation contract requires it.
- [x] Demonstrate that these assertions catch a missing mapping, wrong item,
  precise-to-generic reduction, dropped packet or omitted selected definition
  where that boundary applies. Use bounded counterexamples in existing fixtures,
  not a repo-wide mutation campaign. Unknown/untrusted records must still fail
  strict selection; the correction is to register supported owners correctly.
- [x] Extend existing Core diagnostic-record/foundation and events/audit runtime
  fixtures: normal exact reason, forced builder failure, unselected code/version,
  malformed/accessor evidence, companion preservation and frozen/primitive
  original errors. Assert both the original workload outcome and visible safe
  diagnostic-processing outcome at the real caller.
- [x] Extend affected Platform config/runtime and adapter tests according to
  the reconciled caller inventory. Include synthetic sensitive canaries and
  verify no recursive reporting, replay or raw rejected-field disclosure.
- [x] Prove both DynamoDB index-length alternatives and table attribution,
  real command/store/decoder recipients, CloudWatch exposed failure alternatives
  and export-failure-with-resolved-flush. Test imported producer and parser
  together, including missing versus unreadable observations, safe child failure,
  partial effects and unchanged successful output. Verify actual dispatcher
  membership and portable generated consumers; fixture files alone are not proof.
- [x] Narrow tests first; final affected registered units once after connected
  review and freeze. The audit's exploratory probe alone was not completion;
  the registered final proof above now qualifies the implementation. Broad/live
  proof retains its existing boundaries.

Evidence and update history:

- 2026-11-04T19:38:47+00:00 (UTC): raised from the authorised read-only runtime
  audit and documentation task. Shared-path source and current-source probe
  support the finding. DIAG-013 separately owns delivery outcomes; DIAG-004
  reason-name evolution and DIAG-011 optional-delivery consolidation stay done.
- 2026-11-04T19:59:33+00:00 (UTC): user requested the scope correction after
  distinguishing ordinary supported-reason loss from unexpected diagnostic
  processing failure. Normal check-result → exact diagnostic → real caller
  coverage is now primary; processing-failure visibility remains secondary.
  Added per-operation inventory, mapping/definition/registration/caller repair,
  normal-input regression and harness criteria. Preserved the original raised
  time, open status, historical evidence and DIAG-013 delivery boundary. Existing
  CloudWatch, N01B, imported-tool and deployment deferrals remain unchanged.
  Documentation update only; no runtime fix or new test pass is claimed.
- 2026-11-04T20:10:47+00:00 (UTC): user authorised strengthening the task and
  existing harness instructions against the agreed configuration principles.
  Added explicit ownership, reuse and module-organisation acceptance criteria.
  The safe-diagnostic standard now owns normal supported-reason preservation;
  the coverage workflow applies it in the existing inventory and source review,
  and no longer directs every fix to add/change a diagnostic definition.
  Only the corresponding instruction criterion is complete. Runtime corrections,
  caller proof and remaining acceptance criteria stay open; DIAG-013 and existing
  deferrals are unchanged. No AGENTS, runtime, catalogue or new gate changes.
- 2026-11-04T20:24:07+00:00 (UTC): first recorded preparation clock after the
  user explicitly included CloudWatch, DynamoDB and imported-tool work and
  requested a plan before implementation approval. The preparation section in
  the controlling plan supersedes those diagnostic deferrals, records concrete
  source/consumer groups, tests, imported ownership and staged proof. N01B's
  oversized-index attribution correction is included; its index design/loading
  redesign is not. DIAG-013 delivery status and deployment proof remain separate.
  This is not an exhaustive per-reason audit or implementation completion.

## DIAG-013 — Expose diagnostic reporting outcomes without changing workload results

Status: open — implementation deferred to the logging and telemetry maturity work.

### 1. ID

DIAG-013

### 2. Date/time raised

2026-11-04T19:38:47+00:00 (UTC).

### 3. Summary

Make diagnostic handoff/rejection/unavailability observable through the real
caller path, while preserving optional reporting, original business outcomes,
privacy and deliberate opt-outs. Do not claim local handoff proves remote receipt.

### 4. Background

The user asked whether repo-wide diagnostics could still disappear after a
reason was obtained. The assistant's current-source probe showed that the shared
delivery helper returns undefined both for a successful void receiver and for
a receiver that throws. Platform's reporter already returns written/rejected/
unavailable, but reportPlatformDiagnostic discards that status. Both resolved
and rejected asynchronous logger results receive unavailable rather than a
separate observable completion state.

These behaviours are intentionally preserved by DIAG-011 and its existing
isolation tests. They are not a failed consolidation. The missing capability is
visibility into diagnostic delivery failure; adding it must not accidentally
make application success depend on logging or use the failed logger recursively.
The audit also distinguishes local status from deferred collector/backend proof.

### 5. User stories

- As an investigating agent, I need the caller or an approved independent
  observation surface to distinguish accepted handoff, rejected input and
  unavailable/unconfirmed delivery, rather than treating a void wrapper return
  as confirmation. Owners:
  `packages/core/src/diagnostics/reporting/delivery.ts`,
  `platform/contracts/src/diagnostics.ts` and
  `platform/observability/src/diagnostics.ts`.
- As a runtime maintainer, I need compatible handling by the actual users in
  Core/Platform config, SQS configuration reporting, Persistence observation,
  Runtime, Server, Workers, Health and core-server startup/task reporting.
  The [audit consumer map](governed-diagnostic-coverage.md#connected-consumer-map-for-the-shared-corrections)
  names initial paths. Inspect indirect observers and return values before
  choosing an additive status/callback interface; do not blindly replace every
  optional observer or expand retiring-target deployment work.
- As a service maintainer, I need reporting exceptions contained, no automatic
  retries or work replay, unchanged result/error identity, and no raw exception
  or rejected-record contents in any fallback. Omitted/disabled reporters stay
  valid where the operation contract permits them; required composition must
  establish its reporter before dependent work where applicable.

### 6. Acceptance criteria

#### Code and connected consumers

- [ ] Define precise local outcome semantics and where the final caller can
  inspect them. Preserve existing supported helper return values and reporter
  contracts or introduce an additive API; no silent compatibility replacement.
- [ ] Do not discard the existing reporter's rejection/unavailable outcome in
  required observation paths. Distinguish asynchronous unconfirmed work from
  confirmed local failure/completion where the actual interface supports that
  observation. A void logger return is at most its local contract's acceptance,
  not evidence of remote durability.
- [ ] Propagate outcomes through real connected callers, with explicit valid
  opt-out/no-change decisions. Check missing reporter/invalid context/catalogue
  before work where statically configured; preserve original outcomes if
  reporting fails later.
- [ ] Bound any independent failure notification and prevent recursive reporting
  through the same failing sink. Do not add a durable queue, retries, watchdog,
  dependency, cloud operation or blanket stderr fallback as an incidental fix.
  If a reliable recipient is absent, expose uncertainty rather than promise
  delivery that cannot be guaranteed.
- [ ] Reconcile source/test/catalogue/doc consumers as applicable. CloudWatch
  supported failure preservation and unavailable SDK evidence are now assessed
  in DIAG-012; backend delivery remains separate proof, not something local
  helper tests establish.

#### Harness

- [ ] Amend the existing optional-delivery section of the safe-diagnostic
  standard and existing coverage workflow to require an explicit optional
  versus required observation decision and proof of outcome consumption.
  Preserve DIAG-011's shared mechanism and no-replay/isolation principles.
- [ ] Review must name the actual recipient and the proof level: construction,
  handoff, local completion, or remote receipt. No new broad scanner/framework,
  duplicated policy in AGENTS, or status-based claim of universal delivery.

#### Regression fixtures

- [ ] Extend `packages/core/tests/diagnostic-delivery-runtime.test.ts`,
  its type/caller fixture and
  `platform/observability/tests/diagnostics-runtime.test.ts` for successful
  void, sync throw, returned rejection/unavailability, resolved/rejected/pending
  asynchronous results, bad context/catalogue, omitted/disabled receiver and
  independent companion delivery. Verify original work, no unhandled rejection,
  no recursion/replay and sensitive-canary exclusion.
- [ ] At least one actual core-server startup/task consumer and each changed
  shared caller must observe the intended safe outcome; checking helper outputs
  alone is insufficient. Unknown/unregistered records must still be excluded.
- [ ] Execute only affected focused units after connected review; freeze before
  one final batch and retain the broad/live deferrals. Existing audit probe is
  exploratory evidence, not implementation acceptance or remote qualification.

Evidence and update history:

- 2026-11-04T19:38:47+00:00 (UTC): raised from current source and the passing
  exploratory probe. DIAG-011 remains done for its agreed consolidation scope;
  this is a new visibility requirement. DIAG-012 owns earlier construction/
  selection handling; existing telemetry and deployment plans own remote proof.

- 2026-11-05T17:36:46+00:00 (Europe/Dublin): recorded the user's agreed
  deferral to the next logging/telemetry maturity review before this session's
  commit. That work must establish receiving responsibilities, confirmation
  levels, optional/required reporting and independent failure visibility before
  implementing DIAG-013. This remains a requirement of that follow-on, not a
  completion claim. Production qualification is a separate authorised handoff.

## DIAG-014 — Govern diagnostic improvements when development uncovers a failure

Status: done — bounded harness procedure and reviewed proof completed on 2026-11-05.

### 1. ID

DIAG-014

### 2. Date/time raised

2026-11-05T13:04:10+00:00 (Europe/Dublin).

This is the backlog recording time; the preceding discussion's exact timestamp
was not recorded.

### 3. Summary

Make discovering an inadequately explained failure an explicit trigger in the
existing development workflow: establish what happened, reuse or correct the
appropriate diagnostic, prove that the explanation reaches its intended caller,
and record anything outside the authorised work. This is agent-led improvement
of repository code, not an application rewriting itself while running.

### 4. Background

After reviewing what DIAG-012 changed, the user asked whether an agent encountering
a failure not yet described by the repo could improve future diagnostics as part
of its work. The user wants those improvements to follow the ownership, safe
reporting, file organisation and testing practices already established, rather
than create another ad hoc reporting mechanism.

Existing diagnostic governance already covers many of these duties. The gap to
address is an explicit discovery trigger and bounded repair sequence connecting
them. Not every poorly explained failure needs a new diagnostic: an existing
reason may have been dropped, the wrong definition selected, or the evidence may
not establish a cause. Missing runtime definitions do not by themselves mean
governance is missing; existing governance can authorise how to define them.

DIAG-012 remains completed for its recorded repairs. DIAG-013 separately covers
visibility into reporting/delivery outcomes. This task does not reopen either
scope or claim that every possible failure can be detected automatically.

### 5. User stories

- As an agent working on an authorised change, I need
  `.agentic/shared/workflows/verify-diagnostic-coverage.md` to explain what to do
  when a failure has no accurate diagnostic: inspect evidence, check existing
  definitions and connected callers, then reuse, repair, extend or record a gap.
- As a module maintainer, I need the existing
  `.agentic/shared/standards/require-safe-diagnostic-record.md` and
  `.agentic/03.product/standards/public-module-structure.md` to remain the owners
  of reporting and organisation requirements. Corrections must use the relevant
  module's existing contract/domain/reporting structure and shared Core helpers;
  adapters supply provider evidence and entrypoints compose, rather than owning
  reusable rules. Public indexes remain gateways.
- As the user, I need necessary in-scope corrections completed without repeated
  approval, but unrelated enhancements, upstream-owned changes and compatibility
  decisions outside the agreed scope recorded or escalated. The task plan and
  activity journal should show the discovery, decision, affected files and proof.
- As a future investigator, I need tests proving that a supported failure's
  actual reason reaches the receiving caller without exposing sensitive values,
  inventing a cause, changing the operation's result or repeating its work.

### 6. Acceptance criteria

#### Code and connected consumers

- [x] Define the decision sequence explicitly: establish observed facts; reuse an
  existing suitable definition; fix broken mapping/selection/propagation where
  applicable; add or version an owner-defined diagnostic only when necessary;
  retain honest uncertainty when evidence cannot establish the cause.
- [x] Future corrections trace the operation's result through construction,
  selection and the actual receiving caller. They preserve precise supported
  reasons and valid context; a generic processing-failure record is not a
  substitute for an available operation diagnosis. Do not claim remote delivery
  from a local construction or handoff test.
- [x] Require runtime definitions to remain authoritative, reconcile affected
  readers and generated catalogues, and preserve historical contracts or follow
  their explicit versioning rules. Do not introduce a parallel registry or
  duplicate rules in adapters, entrypoints or JSON.
- [x] This task does not predetermine a production defect or authorise a repo-wide
  migration. Select a bounded representative proof during implementation; keep
  runtime self-modification, automatic deployment, replay and unrelated feature
  work out of scope.

#### Harness

- [x] Extend the existing
  [diagnostic coverage workflow](../../workflows/verify-diagnostic-coverage.md)
  with the discovery trigger, decision sequence, connected-consumer review and
  evidence requirements. Add a short corresponding duty to the
  [safe diagnostic standard](../../standards/require-safe-diagnostic-record.md),
  linking rather than duplicating the procedure.
- [x] Reconcile the existing
  [completion standard](../../standards/require-change-completion.md) only where
  needed: necessary newly discovered corrections reopen the relevant task's
  review/proof before closure. Ordinary authorised corrections continue;
  incompatible, upstream-owned, genuinely ungoverned or extra-permission work is
  recorded/escalated, while independent authorised work continues.
- [x] Preserve the existing
  [module structure standard](../../../03.product/standards/public-module-structure.md).
  No new universal folder framework, registry, blanket scanner or mandatory full
  suite per discovery. Distinguish mechanical checks from the human/agent judgement
  needed to establish whether an explanation is accurate and complete.
- [x] Require a concise discovery/decision/proof record in the existing task plan
  and activity journal. Use this backlog for deferred work, not a second tracking
  system. Recording a gap must not silently mark necessary in-scope work complete.

#### Regression fixtures

- [x] Review representative scenarios for an existing usable definition, a dropped
  known reason, a genuinely new supported failure, insufficient evidence, and an
  out-of-scope or permission-bound change. Record expected actions and distinguish
  scenario-review evidence from executable test results.
- [x] For the bounded implementation proof, reuse a suitable actual-caller test
  or extend it where necessary
  that fails with the previous absent, wrong or unjustifiably generic diagnosis
  and passes with the correct code, version and allowed context. Include the
  corresponding successful case, sensitive canaries, unchanged operation outcome
  and no repeated work. Helper-only assertions are insufficient.
- [x] Extend existing harness fixtures only where mechanical enforcement changes;
  a prose-string match is not proof that the agent correctly diagnosed a failure.
  Name exact affected tests during planning. Run narrow tests during development
  and the proportionate registered checks at the stable-batch boundary, reusing
  valid unchanged evidence rather than repeatedly running broad suites.

Evidence and update history:

- 2026-11-05T13:04:10+00:00 (Europe/Dublin): recorded at the user's request
  following the DIAG-012 walkthrough and discussion of governed diagnostic
  improvement during development. This update changes the backlog only; no
  runtime behaviour, harness instructions or regression fixtures were changed.

- 2026-11-05T13:33:38+00:00 (Europe/Dublin): implemented the
  [discovery procedure](../../workflows/verify-diagnostic-coverage.md#when-work-uncovers-an-inadequately-explained-failure),
  a linked duty in the safe-record standard and a completion-standard
  cross-reference. Five scenarios and counterexamples were self-reviewed in the
  session journal's DIAG-014 section. This is process guidance with reviewed
  examples, not a claim of automatic semantic enforcement.
  In line with the approved implementation proposal, clarified the fixture
  criterion to permit reusing existing adequate proof: Events' real-operation
  tests already assert exact records at the caller, successes, original effects,
  no replay and private-canary exclusion. No runtime or mechanical enforcement
  change justified a duplicate fixture.
  Registered `core-runtime` passed by validated matching-receipt reuse (8.960 s,
  zero test execution); final preparation, metadata, process/command drift,
  relative links and scoped whitespace checks passed. Preparation needed local
  receipt-write permission and two explained judgement annotations; the journal
  retains those failed attempts and corrections. Only the three instruction
  documents, this backlog and the existing session journal changed for DIAG-014.
  DIAG-013 and broader integration/deployment remain outside this task.
