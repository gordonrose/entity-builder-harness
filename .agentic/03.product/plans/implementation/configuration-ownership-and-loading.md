<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.plan.configuration-ownership-and-loading
version: 19
status: active
created_on: "2026-11-02"
updated_on: "2026-11-04"
layer: 03.product
domain: configuration
disciplines: [architecture, security, agentic]
kind: plan
purpose: Sequence configuration ownership, loading, responsibility-based folders and module-local diagnostic catalogues while preserving contracts and recording focused proof.
portability: {class: source-only, targets: []}
used_by:
- id: product.readme
  path: .agentic/03.product/README.md
-->
# Configuration ownership and loading

## Status and authority

2026-11-04 scope reconciliation: the user has included DynamoDB and CloudWatch
diagnostic work in DIAG-012 preparation. Its
[controlling scope](../../../shared/plans/implementation/governed-diagnostic-coverage.md#diag-012-preparation-and-expanded-scope--2026-11-04)
now owns the oversized-index ordinary-error attribution correction and existing
configuration-reason propagation. This supersedes those diagnostic deferrals
in N01B and the CloudWatch notes below, without reopening completed A–C/N01A
work or claiming new runtime proof. New index requirements, full DynamoDB
loading redesign, broader observability functionality and live qualification
remain separate. DIAG-012 implementation still awaits approval.

Plan recorded at the user's request on 2026-11-02. Implementation authorised by
the user's subsequent execution prompt; work began at 20:39:43 UTC on that date.
The selection/composition extension is included. Only local source, test,
harness/documentation changes and focused checks/temporary compilation are
authorised: no installation, Docker, cloud, deployment or Git mutation.
The checkboxes track implementation gates; actual executed outcomes and scope
limits are recorded under Completion evidence. The original nine stages (Phase A)
are closed at the authorised local boundary, with broader integration deferred.
The user initially requested a planning-only responsibility-folder extension
(Phase B) on 2026-11-02. The later execution authority below supersedes that
planning-only state; Phase A evidence is not relabelled as B/C proof.
The subsequent execution prompt authorises Phases B and C locally. Work began
2026-11-02 at 21:56:27 UTC. The original no-installation, no-Docker/cloud/deploy
and no-Git-mutation limits remain. Implement and inspect B before C; execute
their overlapping final registered units once on the combined stable inputs,
not twice merely to close adjacent phase checklists. B's intermediate catalogue
byte comparison remains separate from C's additive export proof.

| Phase | Status | Scope |
| --- | --- | --- |
| A — ownership, loading and startup selection | Complete locally | Original nine stages and their recorded evidence |
| B — responsibility-based folders and harness adoption | Complete locally | Bounded config reference refactor and existing standard/check updates below |
| C — module-local diagnostic catalogue reference | Complete locally | Config-owned generated JSON and public access, retaining the whole-Core catalogue |

The [supported-consumer inventory](#supported-configuration-consumer-inventory--2026-11-03)
records the subsequent scoping review. It does not reopen A–C. The user later
authorised N01A only; its execution and proof are tracked below. Other correction
scopes and deferred work are not automatically authorised by the inventory.

Recorded chat worktree:
`/home/owner/projects/.chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-10-27-08-24-walk-through-core-server-persistence-observability-step-by-s-1803338414`.
Use it explicitly for commands; preserve the existing unrelated changes.

## Problem and intended outcome

A database connection needs information such as a host, database name and port.
Today the target startup code does too much of the work of deciding what the
dependency requires. Meanwhile, Platform config mostly coordinates existing
checks and creates diagnostic reports; it does not yet provide the common
process for obtaining and checking a dependency's required information.

The outcome is one clear owner for each job:

| Job | Owner |
| --- | --- |
| Declare required operations and their meaning, independently of a service | The consuming Platform or feature module |
| Translate those operations into service-specific requests and stored representations | The adapter or module-specific storage implementation |
| Describe reusable requirements, check individual values and relationships, and build generic config reports | `packages/core/src/config/` |
| Define what a dependency needs and assemble its checked configuration | The dependency's capability or adapter; provider-specific requirements stay in that adapter |
| Coordinate obtaining information, checking it and assembling the result | `platform/config/` |
| Actually obtain information from an environment, file or external provider | The appropriate existing supplied reader or provider adapter |
| Choose concrete environment names, resource references and target policy | The target's configuration-loading code |
| Select a supported implementation for a given capability/module | Target configuration |
| Connect that selection to its requirements and constructor | Dedicated target composition code |
| Decide whether startup can continue and start the components | The entrypoint |
| Compile and package the supported implementation and wiring | Build process; compiled output is not the authoritative translation source |
| Validate and construct the common diagnostic packet | `packages/core/src/diagnostics/` |
| Deliver the packet | The existing reporting/logging path |

The representative path is PostgreSQL configuration for
`kanbien-core-platform/core-server-persistence`, including server, migration,
administration and restore purposes. The dependency declares its requirements;
the target says where their values come from; Platform coordinates the work;
Core performs the reusable checks. An entrypoint receives checked configuration
or its established failure, rather than reconstructing dependency rules.

### Implementation selection and composition

The module declares an operation such as finding eligible notifications. Its
service-specific implementation translates that operation into database work;
the target chooses and connects a supported implementation. Business policy
stays with the module even when an adapter enforces that policy in an atomic
database operation. A generic service client must not accumulate every feature's
storage rules. Actual index structures belong to the relevant storage
implementation; infrastructure creates compatible resources and supplies names.

For the first delivery, selection happens at startup and remains fixed for that
process. A change requires restart/redeployment, not live switching. The build
packages supported implementations; it does not author their translations or
precompute requests whose arguments only exist at runtime. Excluding unused
implementations at build time is a separate, deferred optimisation.

Deliver the selection mechanism with the existing PostgreSQL reference only.
Omitted selection preserves today's PostgreSQL choice; an explicit unsupported
choice fails, with no fallback. Settle the exact optional selection input and
fixed identifier in stage 1 without introducing a new mandatory environment
variable or changing existing deployment values. Resolve selection before reading
implementation-specific configuration or creating a client. Platform config
receives the selected requirements/readers/assembly; it does not own a provider
registry or instantiate services. Target composition uses explicit code-owned
imports and mappings, never arbitrary import paths supplied through configuration.

This mechanism and additional interchangeable implementations are distinct
deliverables. The existing DynamoDB outbox implementation and PostgreSQL
acceptance-record implementation are not established substitutes for each other.
A later implementation must fulfil the same operations and guarantees and pass
the shared behavioural contract tests before it becomes a selectable alternative.
Configuration selection neither migrates stored data nor establishes parity.

## Boundaries and compatibility

- Preserve supported public imports, exported names and signatures, accepted
  spellings, defaults, read/call order, first-failure selection, thrown failures
  and diagnostic identities, versions, accepted details and output shapes.
- Keep the existing registered `ConfigSchema` path supported. Do not build a
  second competing framework or pretend that all existing callers are migrated.
- Distinguish an invalid supplied value from inability to obtain it. Do not
  invent a cause from an unknown exception or silently fall back after failure.
- The decision that input is invalid must not depend on diagnostic delivery
  succeeding. Preserve existing failure envelopes and throwing behaviour.
- Do not change SQL, privileges, credentials, token acquisition, TLS/certificate
  handling, connection lifecycles, deployment values or environment contracts.
  The bounded addition is an optional implementation selection preserving the
  existing default; its exact source/default/failure contract is captured in stage 1.
- No speculative source providers, provider registry, new transport/service/
  manager layers, installation, cloud operations or deployments are part of this
  implementation. Deployment qualification remains separate work.
- A bounded target-owned mapping for supported implementations is in scope; a
  universal service-switching framework, live switching, DynamoDB migration,
  feature-parity implementation or build-output optimisation is not.
- Inventory other consumers and mark each migrated, compatible unchanged or
  explicit follow-up. Do not turn the reference migration into a repo-wide rewrite.
- Do not reopen completed DIAG-001–005/008. DIAG-006/007 remain separate deferred
  work; this plan does not authorise them.

## File map

`[n]` means planned new file/folder; `[u]` means an existing file expected to be
updated. Unmarked files are retained participants, not promised edits. Confirm
the exact consumer inventory in stage 1 before moving source. Public `index.ts`
files expose names only; contracts describe requirements/results, while domain
files perform the work. Do not split every function into its own file.

```text
packages/core/
├── package.json
├── contracts/diagnostics.v1.json                 # preserve historical definitions
├── src/
│   ├── diagnostic-catalog.ts
│   ├── config/
│   │   ├── index.ts [u]                          # exports only
│   │   ├── README.md [u]
│   │   ├── contract/
│   │   │   ├── types.ts [u]                     # reusable requirements; compatibility
│   │   │   ├── constraints.ts
│   │   │   ├── setting-issues.ts
│   │   │   ├── sourcing-issues.ts
│   │   │   ├── errors.ts
│   │   │   └── diagnostics.ts
│   │   └── domain/
│   │       ├── source.ts
│   │       ├── value-readers.ts
│   │       ├── settings.ts [u]
│   │       ├── json-object.ts
│   │       ├── issue-collection.ts
│   │       └── diagnostic-reporting.ts [n]      # generic builders moved from Platform
│   └── diagnostics/
│       ├── index.ts
│       ├── definition.ts
│       ├── schema.ts
│       └── record.ts
└── tests/
    ├── config-types.test.ts [u]
    ├── config-runtime.test.ts [u]
    ├── diagnostic-record-types.test.ts [u]
    └── diagnostic-record-runtime.test.ts [u]

platform/config/
├── package.json
├── README.md [u]
├── tsconfig.json
├── tsconfig.check.json
├── tsconfig.runtime-test.json
├── contracts/diagnostics.v1.json [u]              # only justified new loading definitions
├── src/
│   ├── index.ts [u]                             # exports only
│   ├── diagnostics.ts [u]                       # compatibility exports, not copies
│   ├── contract/ [n]
│   │   ├── loading.ts [n]
│   │   ├── validation.ts [n]
│   │   ├── errors.ts [n]
│   │   └── diagnostics.ts [n]
│   └── domain/ [n]
│       ├── loading.ts [n]
│       ├── source-resolution.ts [n]
│       └── validation.ts [n]                    # existing runner moved unchanged
└── tests/
    ├── platform-config-types.test.ts [u]
    ├── platform-config-runtime.test.ts [u]
    ├── evidence-runtime.test.ts [u]
    ├── configuration-loading-runtime.test.ts [n]
    ├── platform-config-boundaries.test.mjs
    └── run-runtime-tests.mjs

platform/adapters/aws/persistence/postgresql/
├── package.json
├── README.md [u]
├── tsconfig.json
├── tsconfig.check.json
├── tsconfig.runtime-test.json
├── tsconfig.integration-test.json
├── assets/rds-eu-west-1-bundle.crt
├── src/
│   ├── index.ts [u]
│   ├── metadata.ts [n]                          # old adapter identity, moved out of index
│   ├── config.ts [u]                            # compatibility exports
│   ├── configuration/ [n]                       # subject submodule, not a new layer
│   │   ├── index.ts [n]
│   │   ├── README.md [n]
│   │   ├── contract/ [n]
│   │   │   ├── types.ts [n]
│   │   │   ├── requirements.ts [n]
│   │   │   └── errors.ts [n]
│   │   └── domain/ [n]
│   │       ├── validation.ts [n]
│   │       └── assembly.ts [n]
│   ├── connection.ts
│   ├── credentials.ts
│   ├── rds-iam-authentication.ts
│   ├── errors.ts
│   ├── observations.ts
│   ├── migrations.ts
│   ├── transactions.ts
│   ├── records.ts
│   ├── lineage.ts
│   ├── outbox.ts
│   ├── processing.ts
│   └── telemetry.ts
└── tests/
    ├── postgresql-persistence-adapter-runtime.test.ts [u]
    ├── postgresql-diagnostics.test.ts [u]
    ├── postgresql-persistence-adapter-boundaries.test.mjs
    ├── postgresql-persistence-adapter-integration.test.ts
    ├── run-runtime-tests.mjs
    ├── run-local-integration-tests.mjs
    └── run-disposable-integration.mjs
```

Core diagnostics' existing `index.ts` has a legacy structural allowance. This
plan does not reorganise that engine or claim that it is export-only; add no
new implementation there. Remove Platform config's allowance once its own
index is cleaned up, rather than refreshing its legacy hash.

Target participants, all under `infra/04.deploy/03.product/entrypoints/`:

```text
kanbien-core-server-persistence-composition.ts [n]  # selection, requirements and construction wiring
kanbien-core-server-persistence-configuration.ts [u]
kanbien-core-server-persistence.main.ts [u]        # only necessary startup wiring
kanbien-core-server-persistence-migration.main.ts
kanbien-core-server-persistence-administration.main.ts
kanbien-core-server-persistence-restore-verifier.main.ts
kanbien-core-server-persistence-iam-authentication.ts
kanbien-core-server-persistence-postgresql.ts
kanbien-core-server-persistence-runtime-credential.ts
kanbien-core-server-persistence-role-credential.ts
kanbien-core-server-persistence-verifier.main.ts
kanbien-core-server-persistence.app.ts            # inspect consuming operation contract
kanbien-core-server-persistence-diagnostics.ts [u] # bounded selection diagnostics if needed
kanbien-core-server-persistence-operation-diagnostics.ts
kanbien-core-server-persistence.tsconfig.json [u]  # only if compilation inputs need adjustment
contracts/diagnostics.v1.json [u]                  # only justified additive definitions
contracts/kanbien-core-server-persistence-operation-diagnostics.v1.json
```

Keep the mains unchanged where the target's existing wrappers permit it. Inspect
the target's `20-scopes/core-server-persistence/10-workload-binding/workload-binding.yml`
and `30-provider-realization/aws/cloudformation/core-server-persistence.yml`
under `infra/04.deploy/03.product/targets/kanbien-core-platform/` as the actual
environment-binding context, not as permission to change deployment behaviour.
The new composition file is the target's bounded wiring owner, not a home for
queries or business rules. Existing PostgreSQL translation stays in its named
implementation files. Avoid cycles: configuration loading must not import the
startup constructor wiring that itself depends on the loaded configuration.

Governance and proof participants:

```text
.agentic/03.product/standards/config-runtime-settings.md [u]
.agentic/03.product/standards/public-module-structure.md [u]
.agentic/03.product/workflows/platform-runtime-implementation.md [u]
.agentic/shared/workflows/verify-diagnostic-coverage.md [u]
scripts/repo/module-structure/check.mjs
scripts/repo/module-structure/legacy.v1.json [u]
scripts/repo/module-structure/smoke-test.mjs [u]
scripts/repo/diagnostic-coverage/reviews.v1.json [u]
scripts/repo/diagnostic-coverage/compatibility.mjs
scripts/repo/diagnostic-coverage/export-catalogs.mjs
scripts/repo/diagnostic-coverage/smoke-test.py [u]
scripts/repo/check-selection/checks.yml
scripts/repo/check-selection/script.sh
scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/
├── configuration-test.mjs [u]
├── build.sh
├── fixture-runtime.mjs
└── smoke-test.sh
```

Do not edit `checks.yml` unless inspection demonstrates an actual missing input.
The plan, session record and relevant backlog references are bookkeeping surfaces,
not additional policy owners or new review registries.

## Sequential implementation and gates

### 1. Establish the implementation contract and baseline

- [x] Inventory all direct/indirect callers, public exports and internal imports.
  Include `./config` users in connection, records, migrations, lineage, outbox,
  processing, credentials and IAM authentication; avoid root-index import cycles.
- [x] Record current results for all four target purposes: supplied source names,
  value types, defaults, requirements, policy, failure envelopes and diagnostics.
- [x] Specify the new loading input/result with examples: dependency requirements,
  target source bindings, supplied readers, selected policy and dependency-owned
  assembly of accepted values. Retain current bound `ConfigSettingDefinition`.
- [x] Capture compatibility assertions before moving source. Identify which
  readers throw, which return failure and which values must never be reported.
- [x] Inventory the consuming module's exact operation contract and guarantees,
  supported implementations and per-implementation configuration requirements.
  Distinguish Platform persistence contracts from the target acceptance-record
  contract; do not assume their existing adapters are interchangeable.
- [x] Record the startup selection input, fixed supported identifier, unchanged
  default, immutable-per-process lifetime and unsupported-selection outcome.
  Identify the target composition owner, constructor signatures and build inputs.
- [x] Gate: inventory and exact contract written below; no material behavioural
  decision left for an implementer to improvise. Baseline decisions follow below.

### 2. Establish reusable Core config contracts

- [x] Extend `contract/types.ts`, `domain/settings.ts` and public exports to allow
  requirements independent of concrete environment names. Reuse existing rules
  and shared constraints, not a second port-rule declaration.
- [x] Preserve old bound definitions/readers; add focused type and runtime cases.
- [x] Gate: a dependency can declare requirements without target source names,
  while old callers retain their supported inputs and outputs.

### 3. Move generic diagnostic reporting to Core config

- [x] Move generic field, relationship and source-read report builders into
  `config/domain/diagnostic-reporting.ts`; expose them through Core config.
- [x] Retain Platform compatibility exports. Keep one implementation, existing
  names, reason selections/order, code/version/detail shapes and classification.
- [x] Keep the Core diagnostic packet engine unchanged. Check literal old packets
  and malformed/sensitive input cases, not only successful construction.
- [x] Gate: generic config reporting has one Core owner and old imports still work.

### 4. Give PostgreSQL ownership of its configuration requirements

- [x] Create the `configuration/contract/` and `configuration/domain/` split
  shown above. Move current direct validation without changing its semantics.
- [x] Declare PostgreSQL requirements once, referencing shared Core constraints;
  keep target policy separate. Assemble its usable config only from checked values.
- [x] Expose requirements and checked-configuration assembly for target selection;
  retain actual operation translations outside config contracts and build scripts.
- [x] Keep `src/config.ts` as a compatibility export bridge and preserve direct
  numeric input behaviour, identifier/login helpers and existing error contract.
- [x] Gate: upstream requirements/assembly are reusable, all affected old imports
  resolve and no unrelated SQL/connection implementation moved for uniformity.

### 5. Implement Platform's common loading process

- [x] Implement the planned loading contracts, source resolution and coordinator.
  Accept requirements, bindings/policy, supplied readers and checked assembly;
  do not import PostgreSQL, AWS SDKs or concrete environment variable names.
- [x] Move the existing registered-schema runner into `domain/validation.ts` with
  unchanged results, diagnostic observation and throwing behaviour; index exports only.
- [x] Test declaration/binding problems separately from invalid supplied values
  and unavailable sources. No silent fallback, invented exception cause or
  assumption that every legacy failure now returns `ok: false`.
- [x] Keep provider selection and client construction outside Platform config.
  Its loading input describes the already selected implementation's requirements;
  it must not demand configuration for unselected implementations.
- [x] Gate: the common process is provider-neutral, the existing schema route
  still works and checked values are the only values passed to assembly.

### 6. Migrate the actual target path

- [x] Add `kanbien-core-server-persistence-composition.ts` as the bounded owner
  connecting the module's required operations to the supported PostgreSQL
  implementation, its requirements and constructor. Select via the agreed optional
  target input; omit it to retain existing behaviour. Reject unsupported explicit
  values before implementation-specific reads, token work or client construction.
- [x] Make `kanbien-core-server-persistence-configuration.ts` select concrete
  sources, purpose and target policy, then use adapter requirements and the
  Platform process rather than reconstructing dependency rules.
- [x] Preserve startup failure/report context, defaults and specialised existing
  IAM/credential/TLS operations for server, migration, administration and restore.
- [x] Extend the actual compiled-target fixture to force shared success/failure
  results: prove consumers use returned checked values, do not bypass shared
  checks, and stop before token/pool/dependent work when required input fails.
- [x] Ensure the real startup receives the selected constructor's returned
  implementation, not a separate hard-coded instance. Keep the selection fixed
  for the process; use explicit imports rather than user-controlled module paths.
- [x] Confirm the existing build compiles/packages the new composition and its
  supported implementation. Adjust only necessary compile inputs; no new build
  generator, request-generation step or requirement to package a second provider.
- [x] Gate: the real target, not merely an invented fixture, follows this path
  with its original default behaviour. Explicit selection and failure are proved;
  no DynamoDB switchability or cross-provider parity is claimed.

### 7. Reconcile governance, documentation and all connected changes

- [x] Update the existing owning standards/workflows with the ownership division,
  dependency requirement reuse and export-only index expectations. No copied
  normative policy in READMEs and no new gate/registry for the same obligation.
- [x] Include operation ownership, service-specific translation, target selection,
  composition and build output in those existing standards. Require every future
  selectable implementation to prove the same behavioural contract and guarantees;
  do not treat configuration shape or the label "persistence" as parity evidence.
- [x] Use the README skill for the changed module guides: concrete input/output,
  file responsibilities and diagrams; label current examples versus future reuse.
- [x] Remove the cleaned Platform index allowance. Add narrow existing-check
  fixtures against local dependency-rule copies, unchecked-value use and bypasses.
- [x] Reconcile every inventoried consumer, update only affected review records
  with exact source hashes, and preserve existing debt/status honestly.
- [x] Complete one consolidated source review and correction batch before final
  expensive proof. Freeze inputs; confirm no agent is still editing them.
- [x] Gate: all connected implementation, consumers, fixtures and corrections
  are complete. Do not use broad verification to discover unfinished design work.

### 8. Run final focused proof, then identify broader batch obligations

- [x] During edits run only the smallest affected tests/type checks needed for
  feedback. After stage 7, run the registered final units once on stable inputs:

  ```bash
  bash scripts/repo/check-selection/script.sh --checks module-index-structure module-index-structure-regression core-runtime platform-config-runtime postgresql-connection-diagnostics diagnostic-catalog-readers --execute-local --json
  ```

  These are static/module checks, the affected package checks and catalog-reader
  proof. `postgresql-connection-diagnostics` uses the existing PostgreSQL adapter
  package check, not its disposable database integration suite.

- [x] Run the existing focused compiled-target configuration fixture. Build with
  `core-server-persistence-composition/build.sh --out-dir <temporary>/compiled`,
  prepare using `scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs --compiled-root <temporary>/compiled`,
  then run `core-server-persistence-composition/configuration-test.mjs` with that
  compiled directory and `NODE_PATH` pointing to this worktree's `node_modules`.
  The composition paths here are under `scripts/04.deploy/lifecycle/20-build/`.
  Use a disposable directory; no Docker, dependency installation or cloud activity.
- [x] Cover port text `"443"`, missing, `"-20"` and `" "`, plus each affected
  requirement, existing spellings, defaults, relationships, four purposes,
  source-read failures, throw/read/first-failure order and malformed declarations.
- [x] Cover safe diagnostic fields with sensitive-value canaries, literal packet
  compatibility, public exports and boundaries, source-versus-content diagnosis,
  actual shared implementation use and returned checked-value consumption.
- [x] In the existing focused target fixture, cover omitted/default selection,
  explicit supported selection and unsupported selection; prove only selected
  requirements are read and the selected constructor's result reaches the module.
  Instrument reads/constructors to detect premature calls, bypasses and fallback.
  Use fixture-only alternatives if necessary to exercise routing mechanics; these
  do not add production providers or demonstrate cross-provider behaviour.
- [x] Prove distinct safe diagnostics for unsupported implementation, missing or
  invalid selected configuration, source-read failure and later service-operation
  failure. Unknown selection text and supplied values must not be echoed. Preserve
  historical diagnostic definitions; genuinely new selection evidence is additive.
- [x] Extract or reuse the bounded behavioural assertions for the consuming
  operation contract from existing tests. Run them against the reference and make
  them the acceptance obligation for future alternatives; do not build an unused
  multi-provider test framework or imply a second provider has passed.
- [x] Use catalog export `--check` and existing cross-language reader proof.
  Pure moves must not rewrite old catalog definitions; justify any genuinely
  new loading definitions separately from historical versions.
- [x] Inspect the non-executing impact selection; record the exact additional
  integration obligations for the stable batch boundary, with reasons. Do not
  weaken selection inputs or imply focused proof satisfies an unrun broader gate.
- [x] Gate: evidence linked for each criterion; retain failures. If source changes
  after freezing, reopen affected review/preparation/proof only, not every unchanged test.

### 9. Close with evidence and remaining limits

- [x] Reconcile all consumers and checkboxes against actual source/test evidence.
- [x] Account explicitly for owners of operations, translations, target selection,
  wiring and build output. Demonstrate the selectable reference and preserved
  default; list additional providers/parity, data migration and build-time exclusion
  as separate work, not missing hidden deliverables or completed functionality.
- [x] Record elapsed activity, command durations, corrections, API/catalog
  compatibility and explicitly outstanding broader or deployment qualification.
- [x] Update this plan and the session log. Claim completion of this bounded
  adoption only, not universal repo adoption or deployed-environment safety proof.
- [x] Gate: all in-scope criteria passed or an explicit scope decision recorded;
  no automatic transition into a deferred backlog item.

## Baseline and consumer decisions — to complete in stage 1

| Consumer / responsibility | Current inputs and behaviour | Decision / affected files | Evidence |
| --- | --- | --- | --- |
| Core public config API | Bound API retained; added ConfigSettingRequirement, validateConfigRequirements and generic reports | Existing callers unchanged; new helpers tested | Core config exploration passed; final registered proof pending |
| Platform registered schemas and report exports | Runner body unchanged; six Core helper aliases | Server/workers and old callers unchanged; new loader tested | Body comparison, loader fixture, export identity; final proof pending |
| PostgreSQL direct configuration and internal helpers | Direct validator body unchanged; ./config bridge retains names | Connection/records/migrations/lineage/outbox/processing/credentials/IAM keep imports | Adapter exploratory type check; extended runtime proof pending |
| Target server / migration / administration / restore | Purpose policy and diagnostic attribution retained | Shared wrapper migrated; main uses selected constructors | 561 rejection cases and selection/constructor fixture passed exploratorily |
| Required operation contract, supported selection and target/build wiring | Existing .app.ts KanbienCorePersistenceRuntime; PostgreSQL only | New composition; build follows imports unchanged | Temporary target compilation 19.617 s; runtime identity/cleanup assertions passed |
| Other callers discovered by repository search | Existing bound config and generic helper signatures unchanged | Retiring target and other adapters retain compatibility imports | Source/export review; Core catalog unchanged |

The decisions below identify exact exports and compatibility. Newly discovered
consumers reopen the affected review, not an unrelated migration.

### Implementation contract and baseline decisions

- Core: retain `validateConfigSettings` overloads and all existing readers and
  return/throw shapes. Add `ConfigSettingRequirement` (setting/rule, no source)
  and `validateConfigRequirements`; the old bound definition extends the same
  instruction. The new helper delegates to the existing checker with logical
  names as source keys, preserving its predicate/relationship/source diagnostics.
- Platform: `loadPlatformConfiguration` accepts requirements, exact logical-name
  source bindings, an injected `ConfigSource`, optional relationships and a
  result-returning assembly function. Binding/declaration errors have a fixed
  diagnostic-bearing TypeError before any read. Value failures retain Core's
  existing shape; source/assembly throws retain identity. No providers or client
  factories enter this module. The registered-schema runner moves unchanged.
- PostgreSQL: retain every existing `config.ts`/root export, numeric direct-input
  behaviour and first-failure order. Adapter owns five source-independent text
  requirements, its existing patterns and the checked-config assembly function.
  Purpose policy stays target-owned. Internal `./config` imports retain a bridge.
  Root `adapterMetadata` must move to a named file to make this changed index
  export-only; remove its obsolete allowance too, not a refreshed hash.
- Target: `PERSISTENCE_IMPLEMENTATION` is optional; absent means `postgresql`.
  Explicit wrong-type, blank, padded or unsupported selections fail before
  snapshotting/reading database configuration. Never echo selection text. A new
  additive target diagnostic records only fixed reason/phase/effect. Existing
  configuration codes and five-setting diagnostic order remain unchanged.
- Target configuration chooses administrator versus authentication reference;
  the adapter always calls that requirement `authentication.reference`. Remap
  administrator field findings at the target reporting boundary, not in Core.
  Pool size remains server=4/other=1; connection=5000, idle=10000; statement=
  migration/administration 240000, restore 30000, server 5000 ms; TLS unchanged.
- Composition owns selection, exported adapter requirements/assembly and the
  existing server persistence constructor; main must use its returned instance.
  Migration/admin/restore keep their established wrappers and effects. No second
  provider or changes to deployment YAML are needed for this optional input.
- Consumer inventory: Core tests/public config callers retain the old API;
  Platform server/workers retain registered-schema exports; all generic reporting
  callers retain Platform exports; target server/migration/admin/restore use the
  common wrapper. Retiring kanbien-platform and other existing adapter callers
  receive compatibility exports only, with no deployment/runtime rewrite.
- Predicate proof: four port cases and all existing field/purpose matrices;
  malformed bindings fail before reads; source throws preserve identity and
  selected source evidence; assembly receives only returned checked values;
  ignored failures/omitted requirements are rejected by direct and real compiled
  caller fixtures. Exact existing catalogs are captured before edits; new
  definitions must be additive. Actual behavioural test results are pending.

## Progress, timing and drift controls

At each stage record: start/end timestamps with timezone, files examined/changed,
activity, exact commands and durations, result/evidence, mistakes/corrections and
avoidable repetition. Separate measured durations from estimates. Planned checks
are not passed checks; no retrospective invented timing or cached-pass claims.
Update the current stage before moving on and keep the checklist consistent.

| Time (UTC; Dublin is UTC+00 on this date) | Activity | Result / evidence |
| --- | --- | --- |
| 2026-11-02 19:53:01 | Planning checkpoint: confirmed recorded worktree, read current Platform exports and reviewed scoped governance | Plan being recorded; implementation and runtime proof not started |
| 2026-11-02 19:55:36 | Reviewed the written sequence against the agreed ownership and scope; checked planning artifacts | Two artifact headers, 15 relative links, nine ordered stages with no completion claims, 14 existing proof/binding paths and six registered check names passed; scoped whitespace check passed. No runtime tests ran. |
| 2026-11-02 20:35:45 | Began the user-authorised plan extension for implementation selection and composition | Added ownership, optional startup selection, PostgreSQL-only first delivery, target composition file, stage criteria and focused proof; implementation remains unstarted. |
| 2026-11-02 20:37:14 | Planning-only verification and scope review | Artifact header, eight relative links, nine ordered uncompleted stages, scope labels and whitespace passed. Reviewed default compatibility, selection-before-read/construction, no-fallback and no-parity-claim boundaries. No runtime tests or implementation work ran. |
| 2026-11-02 20:39:43 | Implementation started: governance, current callers and public/error contracts inspected | Nine relevant source snapshots and three catalog hashes retained in session memory; existing dirty work preserved. One initial status/read command was unnecessarily large; subsequent reads are scoped. Baseline decisions above establish stage 1. |

| 2026-11-02 20:45:14 | Core/Platform/adapter and target composition connected | Existing Platform/target exploratory type checks passed; old imports retained. |
| 2026-11-02 20:48:32 | Focused fixture compilation and guides | Generic inference corrected; temporary target compile passed in 19.617 s. |
| 2026-11-02 20:50:33 | Derived catalog preparation | Existing exporter added only loading-declaration/selection definitions; early caller test correctly rejected stale export before generation. |
| 2026-11-02 20:58:24 | Consolidated review and corrections | Core config, adapter type and 561-case target exploration passed; constructor result use proved; prior review debt retained. |

| 2026-11-02 21:07:33 | Final focused verification complete | All six registered units passed in 311.110 s wrapper time; fresh target compile/package/fixture passed; no source edits after freeze. |
| 2026-11-02 21:09:43 | Broader obligation capture | Non-executing selector planned with no findings; exact deferred identifiers retained below. |

Append implementation activities here; keep the session README as the session
index and summary, not a duplicate detailed activity journal. Summarise command
reports instead of flooding the conversation with full JSON.

Stop and record a deviation before changing behaviour, public diagnostic contracts,
deployment policy or scope. Resolve genuine missing authority/governance; do not
invent provider machinery or ask again about already settled ownership. No new
goal, subagent, installation, Git action or deployment is implied by this plan.
Broader verification follows the stable batch boundary, not every source edit.

## Governing references and related work

- [Configuration standard](../../standards/config-runtime-settings.md)
- [Public module structure](../../standards/public-module-structure.md)
- [Platform runtime implementation workflow](../../workflows/platform-runtime-implementation.md)
- [Diagnostic coverage workflow](../../../shared/workflows/verify-diagnostic-coverage.md)
- [Change-completion standard](../../../shared/standards/require-change-completion.md)
- [Existing Core config architecture proof](core-module-architecture-config-proof.md)
- [Diagnostics backlog](../../../shared/plans/implementation/diagnostics-backlog.md)
- [Session record](../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/README.md)

These remain the policy and historical-evidence owners. This plan sequences the
bounded change; it does not replace them or reopen their completed tasks.

## Consolidated source review — implementation handoff

Self-review by the implementing assistant, 2026-11-02, before final preparation.
No subagent was used and no other agent is editing this task's inputs.

- Reviewed the 48 task paths against the consumer/predicate inventory. Original
  PostgreSQL direct validation and Platform registered-schema runner bodies compare
  exactly after import moves. Core diagnostic export bytes are unchanged.
  The two catalog additions retain all historical definitions.
- Corrected assembly policy projection so extras cannot replace checked values.
  Actual helper/caller substitutions reject bypass and ignored checked results.
  Selection tests prove rejection before database reads and selected runtime identity.
- Moved the reason-growth counterexample to the actual new Core implementation:
  testing only a compatibility re-export would no longer establish that guarantee.
  Added malformed requirement rejection, Python literal-reader proof and protection
  against re-pinning cleaned indexes.
- Direct numeric adapter input remains distinct from Core text input. Whitespace,
  default, first-error and throw behaviour is retained. After successful selection
  the target still snapshots the supplied environment as before; extras are not
  requirements and are not passed to assembly.
- The cohesive metadata.ts move removes PostgreSQL's mixed-index allowance along
  with Platform config's; it adds no provider framework.
- No edits were needed to the packet engine or its tests, PostgreSQL protocol
  fixture, existing evidence fixture, build script, tsconfig, package manifests,
  dependency lockfile or deployment YAML. Retained files remain proof participants.
- Cheap preparation: 99 README/plan links and anchors, structural checks (42 indexes,
  20 allowances, 3 adopted modules), diagnostic adoption and scoped whitespace passed.
  Existing diagnostic debt/status is retained; source hashes are not semantic proof.
- Review corrections were completed before final focused verification. Exploration
  found a generic inference type issue, corrected with default never, and an early
  caller test correctly rejected its not-yet-regenerated catalog. No assertion was
  weakened. Legacy fixture/adoption output was noisy; final reports are summarised.

### Stable-batch and external proof boundary

After focused proof inspect the full selector plan without executing broader
integration commands, recording the exact obligations below. No Docker, install,
deployment, provider calls, publication or Git mutation is authorised. Local
focused success is not deployed-environment qualification.

## Completion evidence — 2026-11-02

Phase A local implementation is complete. Its nine stages are closed at the explicitly
authorised local boundary; the broader integration and external obligations below
remain outstanding for their separate batch/workflow. No deployed-safety claim.

| Final proof | Outcome | Measured command seconds |
| --- | --- | --- |
| core-runtime | passed | 47.246876 |
| diagnostic-catalog-readers | passed | 48.400937 |
| module-index-structure-regression | passed | 12.315425 |
| module-index-structure | passed | 3.905116 |
| platform-config-runtime | passed | 45.675958 |
| postgresql-connection-diagnostics | passed | 82.712298 |
| Fresh target compilation | passed | 13.973 |
| Temporary runtime packaging | passed | 0.332 |
| Real compiled configuration/caller fixture | passed, including 561 existing rejected-startup cases | 2.268 |

Registered runner: 310.427752 s total, 240.256610 s command execution;
48.412121 s runtime identity, 8.687168 s planning, 6.169620 s fingerprinting,
6.304273 s receipt validation and 0.598102 s other overhead. Wrapper 311.110 s.
All six units executed once in the final stage; none reused. Prior exploratory
checks were deliberately narrower and are not substituted for these receipts.

Verification preparation passed in 66.028 s, including eleven artifact headers.
The final diagnostic adoption check had no findings and retained all 190 legacy
debt entries. The 99 guide/plan links/anchors and 116 retained named exports
passed. PostgreSQL direct validator and registered-schema runner bodies are
unchanged; Core catalog bytes and both historical catalog subsets are unchanged.

Private latest-report path at completion:
`/home/owner/projects/entity-builder-harness-restart/.git/worktrees/chat_2026-10-27-08-24-walk-through-core-server-persistence-observability-step-by-s-1803338414/agentic-local-checks/latest-report.json`.
SHA-256: `6c246a48905a6ca4dd5261b84ee4cadeced858b3c4a2558ce46683a090f12531`.
This pointer is mutable; keyed trusted local receipts, not a copied JSON
report or a documentation claim, govern subsequent verification reuse.

### Deferred full-impact obligations

The non-executing selector returned planned with no findings: 118 bound entries
(117 distinct check identifiers), no executions.
The duplicate acceptance-route entry retains its separate bound context; do not
collapse scope-sensitive obligations merely because their identifiers match.
The six already-passed units above appear pending in that planning-only view:
this is not a failed rerun and does not invalidate their executed receipts.

Broader local/aggregate/static obligations, reserved for the stable batch boundary:

```text
acceptance-route-regression
acceptance-route
artifact-placement-regression
aws-runtime-alignment-regression
bootstrap-acceptance-regression
bootstrap-payload-regression
bootstrap-target-controls-regression
chat-commit-metrics-regression
chat-export-regression
chat-local-merge-regression
chat-main-refresh-regression
chat-session-preparation-regression
check-selection-mechanics
check-selection-repository-contracts
harness-header-regression
harness-lifecycle-metadata-regression
check-selection-regression
cloudwatch-observability-runtime
collector-package-custody-regression
container-boundaries-regression
core-dependency-boundary
core-package-custody-regression
persistence-composition
platform-shell-payload
core-target-declaration-regression
delivery-access-contract-regression
delivery-inventory-regression
deployment-operation-diagnostics-regression
diagnostic-adoption
platform-contracts-runtime
platform-health-runtime
platform-observability-runtime
platform-persistence-runtime
platform-runtime-runtime
platform-security-runtime
platform-smoke-runtime
platform-testing-runtime
platform-workers-runtime
diagnostic-base-runtime
kanbien-platform-runtime
platform-server-runtime
diagnostic-runtime-contracts
dynamodb-persistence-runtime
ecs-fargate-runtime
foundation-budget-regression
harness-agent-validator-regression
harness-artifact-migration-regression
harness-index-regression
observability-mvp-declaration-regression
package-custody-regression
persistence-diagnostic-mapping-regression
persistence-payload-regression
persistence-provider-regression
provider-condition-evidence-regression
restore-connection-diagnostics
runnable-program
runtime-credential-lifecycle-regression
scope-inventory
secret-dependency-declaration-regression
security-cognito-diagnostics
security-shared-rate-limit-diagnostics
shell-artifact-active-drift-assessment-check
shell-artifact-store-policy
shell-candidate-preflight-regression
shell-controlled-smoke-check
shell-deployment-reconciliation-check
shell-deployment-reconciliation-policy-check
shell-drift-detection-boundary-check
shell-foundation-active-drift-assessment-check
shell-infrastructure-policy
shell-ingress-smoke-check
shell-metric-coverage-policy-check
shell-negative-authz-client-check
shell-negative-authz-smoke-check
shell-persistence-admission-probe-check
shell-persistence-delivery-proof-check
shell-persistence-smoke-check
shell-persistence-write-client-check
shell-postgresql-reference-regression
shell-postgresql-relational-smoke-check
shell-rate-limit-smoke-check
shell-synthetic-scheduler-check
shell-worker-smoke-check
shell-infrastructure
shell-metric-coverage-check
shell-package-source
shell-postgresql-live-boundary-check
shell-publication
shell-release-evidence-regression
shell-service-active-drift-assessment-check
sqs-queue-runtime
target-alignment-regression
task-classification-fixtures
```

Container/network/live obligations requiring separate authority/workflow:

```text
bootstrap-container
persistence-container
postgresql-disposable-diagnostics
shell-image-smoke
bootstrap-target-alignment
persistence-target-alignment
shell-runtime-alignment
bootstrap-acceptance
persistence-acceptance
shell-deployment-reconciliation
shell-ingress-smoke
shell-metric-coverage
shell-negative-authz-smoke
shell-persistence-delivery-proof
shell-persistence-smoke
shell-postgresql-relational-smoke
shell-rate-limit-smoke
shell-worker-smoke
```

These are preserved selector outputs, not a directive to expand this slice into
retiring-target migration or imported-workbench changes. Applicable combined-result
integration owners reconcile them at the batch boundary. No selector inputs were
narrowed or checks weakened. Relevant aggregate obligations include persistence-
composition, platform-shell-payload and diagnostic-runtime-contracts; the direct
target fixture is focused proof, not a claim that those full aggregates ran.

### Activity review

Implementation began 20:39:43 UTC; all runtime/focused evidence was confirmed
by 21:07:33 UTC. Broad impact recording and documentation closeout followed.
The plan's README skill influenced plain-language inputs/results, file ownership,
diagrams and explicit scope limits, not runtime policy duplication.

Necessary work: preserving compatibility while moving owners, actual-caller
counterexamples, documentation/governance and one final affected-unit pass.
Avoidable work: two orchestration quoting errors before execution, an early
fixture before catalog regeneration, verbose legacy output and a truncated
impact summary requiring a second non-executing plan read (67.470 s then
46.058 s). Future runs should generate artifacts before dependent fixtures
and print only check identifiers/status/timings at the first capture. No runtime
suite was repeated solely for document closeout. Initial narrow type inference
and policy-projection corrections are recorded above, not concealed as scope growth.

## Phase B — responsibility-based folders and config reference refactor

### Status, objective and limits

Planned on 2026-11-02 at 21:46:26 UTC after the teaching discussion. Implementation
authorised at 21:56:27 UTC. This is an additional bounded phase, not a reopening or rejection
of Phase A's completed ownership work. Existing passing receipts describe their
old inputs; they are not automatic evidence for source moved in this phase.

Make the existing module-structure standard require useful grouping by work
responsibility for new substantial modules and relevant structural refactoring.
Contracts describe supported inputs, rules and reports; domain files perform
the work. Config is the first reference using reading, validation and reporting
groups. These describe technical module responsibilities, not permission to put
product business workflows in Core.

Preserve public imports, exports, types, values, errors, diagnostics, source
effects, read/first-failure order, privacy and observer isolation. This phase
changes organisation, not configuration policy or failure behaviour. Do not
reimplement Phase A's loader/selection, add providers or refactor other modules.
Module-local JSON exports remain a separate proposal: keep the combined JSON
catalogues, format, definitions and generated bytes unchanged in this phase.

### Agreed destination layout and move inventory

Paths below are relative to `packages/core/src/config/`. New folders are marked
`[n]`; files within them are existing files moved, not new implementations.
Keep the single existing public index; no subfolder needs its own public index.

```text
config/
├── index.ts                         [update re-exports only]
├── README.md                        [update guide and links]
├── contract/
│   ├── types.ts                     [retain; update error-type import]
│   ├── constraints.ts               [retain]
│   └── reporting/ [n]
│       ├── setting-issues.ts        [move from contract/]
│       ├── sourcing-issues.ts       [move from contract/]
│       ├── errors.ts                [move from contract/]
│       └── diagnostics.ts           [move from contract/]
└── domain/
    ├── reading/ [n]
    │   ├── source.ts                [move from domain/]
    │   └── value-readers.ts         [move from domain/]
    ├── validation/ [n]
    │   ├── settings.ts              [move from domain/]
    │   └── json-object.ts           [move from domain/]
    └── reporting/ [n]
        ├── issue-collection.ts      [move from domain/]
        └── diagnostic-reporting.ts [move from domain/]
```

Reading a required string can remain a combined read/check operation. Classify
by cohesive responsibility, not a rule that every function may do only one
step. Reporting here collects findings and constructs packets; it does not
deliver logs. Keep error/issue-specific types with their owners rather than
moving every type into `types.ts`. Constraints remain declarations, not checkers.

### B1. Record the reference baseline and update the owning harness

- [x] Inspect the current tree/diffs and map every moved export and direct
  private-path consumer before moving files. Follow the existing governed path
  migration procedure where applicable; preserve unrelated/staged/untracked work.
- [x] Capture public API, representative successful/failing results, source throw
  identity/read order and generated catalogue hashes. Extend this plan's existing
  inventory rather than create a second ledger or reinterpret historical logs.
- [x] Update `.agentic/03.product/standards/public-module-structure.md` as the
  canonical owner: group substantial modules by cohesive responsibility; retain
  contract/domain separation and export-only public indexes. Require a placement
  rationale, not identical folder names or empty folders in every module.
- [x] Explain applicability: start new substantial modules with the grouping;
  improve affected grouping during structural refactors; assess ordinary fixes
  without forcing whole-module migrations; permit small modules to use named files.
- [x] Update `.agentic/03.product/workflows/platform-runtime-implementation.md`
  to require the responsibility/file/consumer map and compatibility proof before
  implementation. Reuse the shared completion standard's existing link to module
  structure; do not copy the requirement into AGENTS, a new skill or another standard.
- [x] Gate: layout, consumer inventory, compatibility baseline and governing
  expectation are explicit. No new runtime policy or extra public module invented.

### B2. Prove existing structural enforcement handles nested groups

- [x] Extend `scripts/repo/module-structure/smoke-test.mjs` with nested-folder
  positive and negative fixtures. Prove valid imports work and contract-to-domain
  dependencies, private external imports, own-public-index imports and cycles
  remain rejected at the deeper paths, including supported type-only edges.
- [x] Inspect `scripts/repo/module-structure/check.mjs`; retain existing recursive
  discovery where it already works. Do not add a new manifest or infer meaningful
  architectural grouping merely from names such as reading or reporting.
- [x] Move its exact Core-catalog private-import exception from
  `config/contract/diagnostics.ts` to `config/contract/reporting/diagnostics.ts`.
  Test the permitted assembly edge and rejected unrelated private edges; do not
  broaden the exception to the reporting folder or all module contracts.
- [x] Extend `packages/core/tests/core-boundaries.test.mjs` only as needed for
  actual nested reference coverage, preserving its current restrictions.
- [x] Gate: fixtures prove structural guarantees survive nesting. Source review,
  not the checker, assesses whether the chosen grouping is understandable.

### B3. Move config files and reconcile every active consumer

- [x] Apply the ten-file move map above without changing implementation bodies
  except necessary imports. Correct dependencies at their owners; avoid forwarding
  shims at old private paths unless inventory proves a supported compatibility need.
- [x] Update `packages/core/src/config/index.ts` and internal imports. Retain
  `@kanbien/core/config` and all supported names; introduce no subfolder index logic.
- [x] Update `packages/core/src/diagnostic-catalog.ts` to the new exact diagnostic
  owner path. Update actual TypeScript/generator inputs only where direct old
  references exist; wildcard compilation is not a reason for gratuitous edits.
- [x] Update affected fixture imports, `require.resolve` calls and injected
  dependency specifiers, especially Core's actual moved-helper reason-growth test.
  A green test of an obsolete shim is not proof of the relocated implementation.
- [x] Search active source, test and governance references; reconcile exact
  review `sources`, `definitions`, test paths and hashes in
  `scripts/repo/diagnostic-coverage/reviews.v1.json`. Keep prior status/debt and
  retain historical session evidence as history rather than rewriting old claims.
- [x] Gate: public callers remain unchanged, active references resolve and the
  source/counterexample tests exercise actual new owners. No provider or target
  rewrite is introduced merely because a Core private path moved.

### B4. Explain the layout and complete consolidated review

- [x] Use the existing README-writing skill for the bounded config guide update:
  file map, per-file responsibilities, diagrams, examples and links. Explain
  validation success as well as failure, reporting versus delivery and the
  combined work in value-readers. Keep normative rules in the owning standard.
- [x] Review moved bodies, public exports, cycles, private edges, active references,
  diagnostic identity and generated bytes against B1. Consolidate corrections
  before final proof; update affected review records with exact reviewed bytes.
- [x] Record actual commands, timings and correction causes in the existing
  activity journal. Confirm nobody is still editing verification inputs, then
  run the existing scoped metadata/preparation process and freeze source.
- [x] Gate: all connected changes and review corrections are complete before
  final focused execution; planned assertions are still labelled as planned.

### B5. Verify narrowly, then record the broader batch boundary

- [x] During editing run only affected direct config/type/structural fixtures.
  After B4, execute the existing registered units once on stable inputs:

  ```bash
  bash scripts/repo/check-selection/script.sh --checks core-runtime platform-config-runtime module-index-structure module-index-structure-regression diagnostic-catalog-readers --execute-local --json
  ```

- [x] Run the existing compiled-target configuration fixture using the same
  temporary compilation/packaging procedure documented in Phase A stage 8.
  Retain successful configuration, exact failure reasons/order, all existing
  rejected-startup cases, checked-value consumption and source/observer behaviour.
- [x] Prove unchanged named exports/types and generated catalogue bytes. Use the
  exporter in `--check` mode; moving source alone must not rewrite definitions,
  versions or JSON. New nested-path structural fixtures must reject the stated
  counterexamples rather than merely inspect the expected folder names.
- [x] Validate changed metadata, README links/anchors, active path references,
  review freshness and scoped whitespace. A later source correction reopens only
  affected review/preparation/proof, not unchanged suites automatically.
- [x] Inspect the complete impact plan without executing broader checks. Record
  its identifiers/statuses/timings compactly on first capture. Defer broader
  integration to the existing stable-batch boundary without weakening selection.
  PostgreSQL's full adapter unit is not an automatic extra run for a Core-only
  move; add affected proof if inventory establishes a changed adapter boundary.
- [x] Gate: all local criteria have actual evidence; preserve any failures and
  distinguish direct fixture, registered-unit, integration and external proof.

### B6. Close the reference and future-adoption obligation

- [x] Confirm the new standard applies to future substantial modules and relevant
  refactoring across Core, Platform, adapters and app modules, with documented
  limits for small modules and unrelated fixes. No repo-wide retrofit is claimed.
- [x] Reconcile the full move/consumer inventory, proof and remaining obligations;
  update this phase and the existing session summary. Do not overwrite Phase A's
  completed evidence or imply it ran against the new paths.
- [x] Gate: the reference demonstrates responsibility-based organisation with
  preserved behaviour and executable boundary protection. Module-local JSON is
  covered by Phase C; observability adoption and deferred DIAG work remain separate.

### Phase B activity and evidence

| Time (UTC) | Activity | Evidence/status |
| --- | --- | --- |
| 2026-11-02 21:46:26 | User requested incorporation of the agreed folder/harness work into this plan | Plan-only extension; six follow-on stages pending. No source, harness implementation or runtime test started. |
| 2026-11-02 21:48:10 | Planning-only validation | Artifact header, 13 relative links, six ordered pending follow-on stages, preservation of completed Phase A evidence and scoped whitespace passed. No runtime suites ran. |
| 2026-11-02 21:56:27 | User authorised B and C implementation | Verified recorded worktree/session and inspected existing dirty task files. Captured 18-file source/API/catalogue baseline; whole-Core SHA-256 2f7e1ce7faa198e5a7893205f727f5b6bcc8721fae51c42596e9bd9cb2e11f70. |
| 2026-11-02 22:08:05 | Implementation and direct fixtures | Ten moved bodies compare equal after import normalisation and removal of C's one additive declaration. Nested fixtures passed; one temporary Core compilation/config test passed. Initial cache compilation lacked the cross-worktree write permission and failed to emit; corrected by compiling to disposable /tmp output. |

#### B/C consumer inventory and migration disposition

All ten moved files are currently untracked implementation from this existing
chat, not committed artifact-path contracts. The committed-artifact migration
workflow therefore does not require a separate migration artifact for these
private source moves. This plan retains their exact move map. Old private paths
are retired after references are reconciled; supported public imports remain.
Recovery, if required, is a scoped inverse move preserving bodies and imports,
not a Git reset or discard. No durable public namespace/layer rename needs an ADR.

Direct B consumers: config's public index, contract/types.ts, all moved files'
relative imports, packages/core/src/diagnostic-catalog.ts, config-runtime.test.ts
(including injected reason-growth imports), module-structure/check.mjs's exact
exception, its smoke-test.mjs fixtures, config README paths/anchors and diagnostic
review source/definition paths. No external runtime caller imports these private
paths. Existing public runtime/type tests preserve successful values, exact
failures, source throw identity/read order and observer behaviour. Verify moved
bodies unchanged after normalising necessary import paths.

C consumers: config diagnostics/index, Core catalogue assembly and package.json;
export-catalogs.mjs's export-enumerating shim; core-boundaries.test.mjs's module
export classification; config runtime/type tests; existing smoke-test.py reader
and compatibility fixtures; generator/check-input and review ownership. The
core-server persistence payload preparer and Platform test shims select explicit
TypeScript module lists, not all manifest exports: they do not need a new JSON
dependency or changes. Add JSON asset proof through the existing exporter and a
disposable package fixture; retain a separate fresh target compile/package/caller
fixture for B's actual runtime compatibility. No container/image build is needed.

Final registered units, once after both implementations and consolidated review:
core-runtime, platform-config-runtime, module-index-structure,
module-index-structure-regression and diagnostic-catalog-readers. Platform config
remains an affected real public consumer even though its shim needs no edit.
Broader impact selection is recorded but not executed in this task.

Relevant existing owners: [module structure standard](../../standards/public-module-structure.md),
[runtime workflow](../../workflows/platform-runtime-implementation.md),
[change completion](../../../shared/standards/require-change-completion.md),
[path migration workflow](../../../01.harness/workflows/migrate-artifact-paths.md)
and [README skill](../../../shared/skills/write-readme.md).

## Phase C — module-local diagnostic catalogues, with config as the reference

### Status, objective and limits

Planned at the user's request on 2026-11-02; implementation now authorised.
Complete Phase B's file moves before this phase uses their destination paths.
Neither Phase A's checks nor this planning validation prove Phase C works.

The purpose is to let somebody working on config read and consume config's
diagnostic catalogue beside its definitions, without searching the whole-Core
JSON file. TypeScript definitions remain authoritative; JSON is a generated
copy for tools that cannot import those definitions. Never maintain both by hand.

This is a bounded config reference, not a simultaneous migration of every Core
module. Keep `packages/core/contracts/diagnostics.v1.json` for existing readers
and whole-Core use. Its complete content and ordering must remain byte-identical
through this phase. Do not remove other modules from it or change diagnostic
codes, definition versions, allowed reasons, delivery limits or runtime behaviour.

### Intended files and responsibilities

Paths below describe the result after Phase B. `[n]` means new; `[u]` means an
existing file requiring a bounded update. Unmarked participants are retained.

```text
packages/core/
├── package.json [u]                         public JSON asset address
├── contracts/diagnostics.v1.json            retained whole-Core export
├── src/
│   ├── diagnostic-catalog.ts [u]            retain complete Core assembly
│   └── config/
│       ├── index.ts [u]                     re-export the named module catalogue
│       ├── README.md [u]                    explain ownership and public access
│       └── contract/reporting/
│           ├── diagnostics.ts [u]           existing definitions; named catalogue
│           └── diagnostics.v1.json [n]      generated config-only export
└── tests/
    ├── core-boundaries.test.mjs [u]         distinguish JSON assets from TS modules
    ├── config-runtime.test.ts [u]          module selection/export assertions
    └── config-types.test.ts [u]            public catalogue type assertions

scripts/repo/diagnostic-coverage/
├── export-catalogs.mjs [u]                  existing generator, one local output
├── runtime_contract.py                     retain aggregate-reader compatibility
└── existing reader/export tests [u]         exact affected files recorded in C1
```

C1 must confirm these existing test owners after Phase B, not create a duplicate
suite to fit this tree. Only update the type fixture if the new export needs it.
Update affected packaging fixtures/shims, review records and check inputs where
the inventory establishes a dependency; do not edit every consumer pre-emptively.

The named TypeScript export is `coreConfigDiagnosticCatalog`, alongside the
existing `coreConfigDiagnosticDefinitions`, from `@kanbien/core/config`.
Keep the catalogue object in the existing `contract/reporting/diagnostics.ts`:
no additional file solely for that constant and no logic in `index.ts`.
Choose its catalogue identity consistently with the existing catalogue schema;
that identity must not rename individual diagnostic definitions.

Provide the stable JSON package address
`@kanbien/core/config/diagnostics.v1.json`, mapped through `package.json` to the
local generated file. Consumers must not need a private source-directory path.
The JSON retains the existing `core/diagnostic-catalog-export/v1` format and
delivery metadata. The filename's `v1` describes the export format, not a rule
that every diagnostic inside it has definition version 1.

Generation stays in `scripts/repo/diagnostic-coverage/export-catalogs.mjs`.
Config's `domain/reporting/` builds runtime reports; it must not become a home
for static export generation. Both JSON outputs derive from the same executable
definition objects; do not introduce a second independently maintained registry.

### C1. Inventory consumers and capture compatibility baselines

- [x] Confirm Phase B implementation/inspection is complete and record the actual destination paths; shared final verification follows C.
  Snapshot the whole-Core JSON bytes, public exports, catalogue ordering and
  existing supported reader behaviour before edits.
- [x] Identify generator inputs, catalogue-reader tests, review records, package
  boundaries and local compilation/payload shims affected by the new JSON export.
  Record exact affected files and commands here before implementation proceeds.
- [x] Inspect `packages/core/tests/core-boundaries.test.mjs` and generator package
  shims: they currently assume non-root package exports are TypeScript modules.
  Inspect other export-enumerating consumers, including
  `scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs`.
  Record which actually need changes; inspection does not authorise image builds.
- [x] Gate: scope and baseline are explicit; no other-module migration, new
  framework or runtime/deployment behaviour change is required for this reference.

### C2. Expose the local catalogue and package asset

- [x] Add the named config catalogue using its existing definition objects;
  retain existing exports. Re-export it from the public config index only.
- [x] Add the JSON package subpath. Update affected export classification and
  nested-path handling without weakening TypeScript module boundary checks.
- [x] Make affected temporary compilation and package fixtures handle JSON
  deliberately. TypeScript does not automatically copy an unimported JSON asset;
  prove the public address resolves in the actual tested package/payload layout.
  Do not make every runtime load a catalogue it does not use.
- [x] Gate: public TypeScript and JSON access work without private-path imports;
  existing runtime imports and named exports remain compatible.

### C3. Generate local JSON without changing the aggregate

- [x] Extend the existing generator to emit the config-local file from the named
  module catalogue, retaining the existing whole-Core output and all definitions.
  Reconcile config's contribution to `src/diagnostic-catalog.ts` without unrelated
  assembly refactoring or ordering changes.
- [x] Preserve existing schema, delivery limits and conflict validation. Add
  counterexamples for stale local JSON, omitted/extra module definitions and
  conflicting definition identities using the existing exporter fixtures.
- [x] Prove two successive generations are deterministic/no-op and that the
  whole-Core file is byte-identical to C1. `--check` must detect local drift.
- [x] Gate: one authoritative definition set produces both views; generated
  JSON is not an independently authored policy or duplicate source of truth.

### C4. Reconcile readers, governance and explanations

- [x] Test a bounded existing generic/Python reader against the config-local
  catalogue. Retain aggregate-reader compatibility and historical restrictions:
  unknown versions, fields and reasons must remain rejected, not silently allowed.
- [x] Extend the existing safe-diagnostic-record standard and diagnostic-coverage
  workflow with module-owned definitions, generated exports, public access,
  freshness and compatibility obligations. Reconcile the public-module-structure
  standard where placement/export rules need clarification; do not duplicate policy.
- [x] Use the existing README skill to explain the local TypeScript definitions,
  local generated JSON and retained aggregate, with actual import examples and
  links to their governing rules. Update affected review paths/hashes and check
  inputs; historical session evidence stays historical.
- [x] Gate: future adopted modules have a governed repeatable pattern. Applying
  it elsewhere is separate scoped work, not a claim all modules are migrated.

### C5. Review once, verify stable inputs and close the reference

- [x] During development run only changed direct exporter/reader/package fixtures.
  Complete connected changes and review corrections, confirm no agent is editing
  verification inputs, then freeze source for the final focused pass.
- [x] Run `diagnostic-catalog-readers`, `core-runtime` and the affected
  `module-index-structure` / `module-index-structure-regression` registered units
  once against stable inputs. Include `platform-config-runtime` when C1 establishes
  a changed consumer boundary. Record exact executed commands and actual timings.
- [x] Run the affected local package/compiled-payload fixture identified in C1:
  prove named catalogue access, JSON subpath resolution and included JSON bytes.
  This is temporary local proof, not permission for Docker, installation or deploy.
- [x] Check generated freshness, exact config-only membership, aggregate byte
  identity, old reader acceptance and invalid-record rejection. Check changed
  metadata, links, review freshness and scoped whitespace.
- [x] Inspect and record broader impact selection without executing it; retain
  broader integration at the existing stable-batch boundary. A correction reruns
  affected proof only; do not repeat unchanged suites automatically.
- [x] Update phase status and the existing activity/session summary with actual
  results and deferred obligations. Preserve Phase A and B evidence as evidence
  of their own inputs. No runtime or future-module completion claims without proof.
- [x] Gate: config is the verified reference; aggregate compatibility and safety
  restrictions remain intact, and the next module can adopt the pattern without
  a new catalogue framework or mandatory folder retrofit.

### Phase C activity and evidence

| Time (UTC) | Activity | Evidence/status |
| --- | --- | --- |
| 2026-11-02 21:52:19 | User requested the module-local catalogue extension | Plan-only Phase C added after Phase B; implementation and runtime verification not started. |
| 2026-11-02 21:55:12 | Planning validation and file-owner correction | Header, 16 relative links, ordered pending B/C stages and scoped whitespace passed. Corrected the proposed test inventory to the existing config-runtime.test.ts and config-types.test.ts; no runtime suites ran. |
| 2026-11-02 22:08:05 | New catalogue fixtures and compatibility | Existing exporter compiled/generated successfully. Local-reader fixture passed; disposable exporter/package fixture passed in 13.764 s after supplying existing NODE_PATH. Initial fixture setup failed because relocated target imports could not find pg; no installation or live connection occurred. Retained 52 public names, added only coreConfigDiagnosticCatalog; whole-Core JSON remains byte-identical. |
| 2026-11-02 22:13:53 | Preparation and orchestration correction | Initial preparation passed in 103.137 s but changed sourcing-issues.ts's artifact header (version/date only), making its reviewed hash stale. An orchestration mistake launched final checks despite the failed identity assertion. Stopped that controller/children after 56.285 s; core-runtime had started, but there was no completed report/receipt. This interrupted attempt is not passing evidence. |
| 2026-11-02 22:16:04 | Metadata review corrected; independent target proof passed | Reviewed the metadata-only difference and corrected its one hash; affected preparation reopened. Independent disposable target compilation 28.874 s, package preparation 0.300 s and actual configuration fixture 2.056 s passed, including 561 pre-pool rejection cases and selection/default/constructor assertions. No database/provider invocation occurred. |

Final closeout at 2026-11-02 22:28:24 UTC: B/C complete locally. Five registered
checks and fresh target proof passed. Documentation-only validation passed for
17 artifact headers, 93 links/anchors, completed phase gates, current reviewed
source hashes, unchanged aggregate bytes and scoped whitespace. No runtime
suite was repeated for closeout.

#### Consolidated B/C source review

Reviewer: parent/self-review; no implementation delegated. Reviewed all ten
body-preserving moves, public index/types, assembly exception, generator/package
asset handling, actual export-enumerating consumers, review transfers and guide
links. C1 resolves the exact new proof owners to the two methods in existing
`scripts/repo/diagnostic-coverage/smoke-test.py`:
`ReaderTests.test_config_local_catalogue_preserves_aggregate_and_reader_boundaries`
and `ReaderTests.test_config_export_generation_assets_staleness_and_conflicts`.
No new registered suite or runtime vocabulary framework is introduced.

Material counterexamples and rejecting proof:

| Incorrect result | Existing/extended assertion |
| --- | --- |
| Nested contracts reach domain or an external caller reaches private reporting | Independent nested positive/negative graphs, exact finding on the external caller, exact assembly exception |
| A copied/moved helper stops preserving v1 reasons | Actual moved compiled helper is re-evaluated with fixture-only vocabulary growth in config-runtime.test.ts |
| A public name disappears or runtime checks change | TypeScript export comparison retains 52 names; normalised ten-body comparison; existing config/foundation runtime/types and fresh target caller fixture |
| JSON export is advertised but omitted from the compiled package | Disposable fixture resolves both public exports, compares JSON bytes and rejects private-path access |
| Local JSON drifts, loses a definition or contains an extra one | Exact four-code/membership assertions and omitted/extra/missing-file --check counterexamples |
| Conflicting identities cause partial snapshot rewrite | Duplicate code/version fixture returns conflict and preserves the stale sentinel plus aggregate bytes |
| Local selection weakens reader/privacy boundaries | Four literal record samples accepted locally and by aggregate; unknown version/reason/private field and native-reader cross-family samples rejected |

Corrections closed before final proof: temporary dependency resolution, exact
failure attribution in a nested fixture, old current-source guide links and
the actual test-file inventory. Four existing review owners now name the moved
sources/definitions with reviewed hashes; their statuses and prior debt remain.
Historical architecture/DIAG plans carry a current-location note rather than
rewriting earlier proof. The no-change payload decision remains explicit in
the B/C consumer inventory. The planned preparation, focused units, fresh target
proof and non-executing full-impact inspection are complete as recorded below.
Broader integration remains deferred.

### B/C completion evidence — 2026-11-02

Both phases are complete at the authorised local boundary. No source changed
after the successful identity guard and completed final pass. Plan/session
closeout is documentation-only; Phase A's evidence is retained separately.

| Final registered proof | Result | Command seconds |
| --- | --- | --- |
| core-runtime | passed | 34.532633 |
| diagnostic-catalog-readers | passed | 43.208833 |
| module-index-structure-regression | passed | 5.007696 |
| module-index-structure | passed | 6.579147 |
| platform-config-runtime | passed | 46.707050 |

Completed runner: 186.663996 s (187.219586 s wrapper); 136.035359 s command
execution, 31.188536 s runtime identity and the remainder planning/fingerprinting/
receipt overhead. All five executed; none reused. The earlier interrupted
56.285 s attempt remains recorded above, not represented as a passing run.
Affected re-preparation passed in 49.574225 s after its one metadata hash repair.

Captured final report: `/tmp/config-bc-final-b2uBsd/report.json`, SHA-256
`85a0148b2c3f088af0957b5e80fe2ff8c0cc352fb302ac6f4eac302ecdf162ea`.
Temporary target proof: `/tmp/config-bc-target-1ixWi2`; compilation 28.873930 s,
packaging 0.300350 s, actual configuration fixture 2.056123 s, all passed.
These temporary paths are local evidence pointers, not portable/trusted receipts.
The registered runner's private source-bound receipts govern future reuse.

The public API retains 52 existing config names and adds only the module
catalogue. All ten implementation bodies are preserved apart from necessary
imports, C's additive catalogue declaration and the source-observation artifact
header's version/date. The whole-Core JSON retains SHA-256
`2f7e1ce7faa198e5a7893205f727f5b6bcc8721fae51c42596e9bd9cb2e11f70`.
The new local JSON contains exactly four config definitions. Generator freshness,
determinism, public TypeScript/JSON resolution, compiled asset inclusion,
conflicting identity rejection, historical reader support, privacy and narrow
native-reader rejection passed in the existing extended fixtures.
Final adoption passed: 552 discovered, 106 adopted, 256 reviewed partial/support,
190 unchanged legacy debt, no findings. Guide/plan link and anchor checks passed.

Full-impact planning covered all 37 current task paths: 118 bound rows and 117
distinct check IDs, no findings. The affected correction plan selected 100 rows
and introduced no new check keys; neither plan executed a command. The full
identifier set is identical to Phase A's recorded complete impact set above;
retain its two differently bound acceptance-route rows. Outside the completed
five units there are 113 rows/112 IDs for the separate stable batch/owning stages,
including PostgreSQL's full adapter unit. Some may have eligible older trusted
receipts; that is not a claim they ran for B/C. No broad/local aggregate, image,
container or live check was executed or weakened here.

Activity review: implementation began 21:56:27 UTC and focused runtime proof was
confirmed by 22:25:17 UTC. Necessary work was the ten-file move/import reconciliation,
additive catalogue/package/generator handling, bounded negative fixtures,
governance/guides, source review and focused proof. Avoidable work included the
missing dependency path in the first disposable fixture, patch-context/quoting
errors before execution, verbose inspection output and the failed-guard fall-through.
The latter cost the interrupted 56.285 s plus affected 49.574 s re-preparation;
the successful runner now places the guard and launch in the same failing-fast
operation. No repeated completed runtime suites or new harness framework were
introduced to address that orchestration error.

No dependency installation, Docker, cloud operation, deployment, staging, commit,
push or discarded user work. Other modules, CloudWatch and deferred DIAG tasks
were not migrated. README skill use shaped the file map, plain-language catalogue
examples and policy references; the governing requirements remain in the harness.

Existing governance owners to reconcile during implementation:
[safe diagnostic record standard](../../../shared/standards/require-safe-diagnostic-record.md),
[diagnostic coverage workflow](../../../shared/workflows/verify-diagnostic-coverage.md)
and [module structure standard](../../standards/public-module-structure.md).

## Deferred configuration capabilities — recorded 2026-11-03

**Status: deferred; no implementation authorised by this section.** The user
asked to retain these seven areas so they are not forgotten. They are not
additional phases of the completed A–C work, and do not become prerequisites
for closing its agreed configuration and diagnostic scope. Listing an area is
not a finding that it is broken, a promise to build it, or an assertion that
none of its mechanisms already exist.

Select one bounded area when a real workload needs it. First inspect what the
repo already provides; record the use case, affected files and consumers,
compatibility decisions, exact tests and required permissions before work starts.
Keep the ownership division above: Core supplies reusable contracts/checks,
Platform coordinates the common process, adapters implement provider operations,
and targets choose concrete bindings and policies. Entrypoints start components;
they do not invent dependency requirements. Public indexes remain export-only.

### F01 — New service integrations

- **Need:** a capability needs a service that is not currently supported, such
  as S3. This is not a commitment to add S3 or make every service interchangeable.
- **Future work:** identify the capability's required operations; put the
  service-specific configuration requirements and checked assembly in its
  adapter, reuse Platform loading, and add target-owned source bindings and
  composition. Inventory the actual files after choosing the service, not now.
- **Proof before completion:** required/missing/blank/invalid inputs, source
  failure, safe diagnostic context, no client construction after invalid input,
  and adapter behaviour against the capability's contract. Package and live
  provider proof require their own authorised stages.

### F02 — Obtaining secrets from external sources

- **Need:** a selected workload must obtain a credential that existing startup
  injection or workload identity does not already supply adequately.
- **Future work:** assess that specific need before proposing a universal
  secret-fetching service. Use the appropriate provider adapter for access;
  keep loading coordination in Platform and access/resource choices in the
  target. Reconcile the existing
  [security follow-on plan's secret lifecycle work](security-capabilities-follow-on.md#secret-lifecycle)
  and its linked declaration standard, rather than creating a competing owner.
- **Proof before completion:** allowed/denied access, missing source, timeout,
  malformed response, cancellation where supported and explicit cache/refresh
  behaviour. Distinguish inability to obtain a secret from invalid contents;
  exclude secret values and raw provider payloads from diagnostics and logs.

### F03 — Configuration changes while the application is running

- **Need:** a workload must adopt a changed value without restarting.
- **Future work:** identify which values may change and which still require a
  restart. Define how a complete replacement is checked and adopted, what
  happens to work already running, and how a rejected or failed update affects
  the previously accepted configuration. Do not silently add a watcher to the
  current startup-only loading process.
- **Proof before completion:** invalid replacement, simultaneous updates,
  partially obtained configuration, consistent reads during adoption, update
  failure and shutdown. Tests must establish whether the old configuration
  remains active; a diagnostic alone does not establish that guarantee.

### F04 — Automatic secret rotation

- **Need:** credentials must be replaced without unacceptable interruption or
  continued use of revoked credentials. Loading a secret once is not rotation.
- **Future work:** extend the existing
  [secret lifecycle workstream](security-capabilities-follow-on.md#secret-lifecycle)
  with an approved replacement/overlap/revocation policy, credential renewal,
  connection replacement and recovery. Keep provider changes with deployment
  owners. F02/F03 are dependencies only if the selected design needs them.
- **Proof before completion:** old/new credential overlap, failed renewal,
  partial rotation, concurrent connections, urgent revocation and recovery;
  prove actual provider behaviour separately from local fake-provider tests.

### F05 — Tenant-specific configuration

- **Need:** different customers or organisations need different values without
  one customer's information or configuration affecting another's work.
- **Future work:** establish a trusted tenant identity, permitted overrides,
  default/override order, storage and cache separation, and update/version rules.
  Reconcile the existing
  [tenant-isolation workstream](security-capabilities-follow-on.md#tenant-isolation)
  and its linked authorization seams; do not treat a caller-supplied tenant
  name as proof that the caller may access that tenant's configuration.
- **Proof before completion:** two-tenant reads/updates, spoofed tenant choice,
  missing context, cache separation, background handoffs, denied access and
  diagnostics that disclose neither another tenant's values nor secret material.

### F06 — Live switching between database implementations

- **Need:** a workload must change its database implementation while running.
  This is different from the implemented startup selection, whose only
  supported reference remains PostgreSQL with the preserved default.
- **Future work:** first establish equivalent capability operations and
  guarantees. Then decide data migration, writes already underway, transaction
  boundaries, connection draining, recovery and reversal. Existing DynamoDB
  code is not evidence of interchangeability or migrated data.
- **Proof before completion:** shared behaviour-contract tests, data
  reconciliation, concurrent work during transition, partial migration,
  interrupted switching and recovery without lost or duplicate effects.
  Startup selection alone cannot satisfy these criteria.

### F07 — New infrastructure and deployments

- **Need:** an approved capability or separately scheduled qualification needs
  resources, permissions or rollout work outside local source implementation.
- **Future work:** use the existing `04.deploy` and applicable AWS owners for
  target declarations, bindings, provisioning, package qualification, rollout,
  rollback and recovery. Identify exact target/file/check inventories when the
  slice is selected. Keep the already deferred A–C verification obligations
  above separate from proposals for new infrastructure.
- **Proof before completion:** stage-specific declaration, package/container,
  access, startup, diagnostic delivery and recovery evidence as applicable.
  Local compilation is not deployment proof. Existing deployment/runtime scope
  remains harness and kanbien-core-server; do not reintroduce the retiring
  kanbien-platform target. No cloud or deployment operation is authorised here.

### Resumption and acceptance

- [ ] Select a demonstrated need and a bounded workstream; record whether the
  outcome is implementation, reuse of an existing mechanism, or no change.
- [ ] Reconcile existing plans/standards and inventory the actual source,
  consumers, harness guidance, diagnostic definitions and fixtures affected.
- [ ] Record compatibility and security policies, focused tests and the later
  stable-batch/package/live verification boundary. Obtain any new authority.
- [ ] Complete connected changes and review corrections before final checks;
  apply the existing
  [change-completion standard](../../../shared/standards/require-change-completion.md)
  and [diagnostic workflow](../../../shared/workflows/verify-diagnostic-coverage.md).
- [ ] Close only the selected workstream with evidence and explicit limits;
  do not automatically advance into the other deferred areas.

### Planning activity journal

| UTC | Activity | Outcome |
| --- | --- | --- |
| 2026-11-03 05:42 | Reconciled the user's seven deferred areas with completed A–C boundaries and existing security/deployment owners | Planning only; one existing plan updated. Scoped metadata, seven-workstream/pending-status checks, five links/anchors and whitespace passed. No runtime suites, source/test changes, deployment or Git operations. |

## Supported configuration consumer inventory — 2026-11-03

### Scope and evidence limits

User requested this bounded inventory, not implementation of every finding.
Reviewed existing runtime configuration readers, checked-loading callers and
startup option validators under `packages/core/src`, `platform/**/src`,
`apps/**/src`, `products/**/src` and the product target entrypoints. Discovery
combined filenames, Core/Platform config API callers, environment access and
constructor/validator inspection; filename matching alone was not the boundary.
The package tree currently has only `packages/core/package.json`.

The rows are responsibility families, not a claim that each exported function
was independently audited. Build-tool configuration, shell/Python tooling,
deployment execution, ordinary per-request data and provider-operation options
not used as startup configuration are outside this inventory. Future services
and the seven deferred capabilities above are not existing consumers to migrate.

Each row has one disposition. **Already compliant** means the named boundary
has an existing appropriate checking path and identified proof, not that all
future inputs or live deployments are proven. **Intentionally different** means
its different rules or specialised owner are valid; it need not import the
generic loader merely to satisfy a pattern. **Needs correction** records a
specific implementation or policy/proof gap. **Deferred or retiring** retains
the existing user boundary without concealing a claimed migration.

Proof paths below are existing test sources inspected for relevant assertions;
they were not executed in this scoping task. Earlier executed evidence for A–C
and DIAG-003/005 remains in this plan and its linked owning plans. No fresh
runtime pass, universal bypass-proofness or deployment proof is claimed.

### Disposition register

All paths in the register and correction scopes are repository-relative.

| ID | Consumer / responsibility | Disposition | Files and supporting proof / next action |
| --- | --- | --- | --- |
| C01 | Core reusable checking and reporting | Already compliant | `packages/core/src/config/contract/types.ts`, `contract/constraints.ts`, `contract/reporting/`, `domain/reading/`, `domain/validation/`, `domain/reporting/`; `packages/core/tests/config-runtime.test.ts`, `config-types.test.ts` and A–C proof above. Keep public exports and per-definition allowed reasons. |
| C02 | Platform loading and registered-schema coordination | Already compliant | `platform/config/src/domain/loading.ts`, `source-resolution.ts`, `validation.ts` and their `contract/` files; `platform/config/tests/configuration-loading-runtime.test.ts`, `platform-config-runtime.test.ts`, `evidence-runtime.test.ts`. These coordinate supplied readers/checkers; they are not a universal remote-fetch service. |
| C03 | PostgreSQL dependency requirements and core-server base loading | Already compliant | `platform/adapters/aws/persistence/postgresql/src/configuration/contract/requirements.ts`, `domain/validation.ts`, `domain/assembly.ts`, compatibility `src/config.ts`; target `kanbien-core-server-persistence-configuration.ts`, `-composition.ts` and `-postgresql.ts` under `infra/04.deploy/03.product/entrypoints/`. Existing `scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs` proves checked-value consumption, purposes, selection and rejection before pool/token work. A–C records actual local proof. Task-specific controls are separately C14. |
| C04 | App-owned schema and server/worker startup schema gates | Already compliant | `apps/platform-smoke/src/app.mount.ts`, `platform/runtime/src/registry.ts`, `platform/server/src/index.ts`, `platform/workers/src/worker.ts`; `apps/platform-smoke/tests/configuration-validation-diagnostics-runtime.test.ts`, server and worker `tests/startup-configuration-diagnostics-runtime.test.ts`. App checks `PLATFORM_SMOKE_APP_NAME` through Core; hosts reject failed registered schemas before lifecycle/listening/polling. Existing `ConfigSchema` support remains intentional compatibility. |
| C05 | HTTP listener, CORS lists, health exposure and release selection | Intentionally different | `platform/server/src/configuration/runtime.ts`, `platform/server/src/verification/release.ts`, `platform/server/src/main.ts`; `platform/server/tests/configuration-runtime.test.ts`, `configuration-omissions-runtime.test.ts`. Preserve defaults, fallback diagnostics, numeric text spellings and explicit process-option port 0. The strict database destination-port rule is not equivalent. Environment-copy duplication is C19. |
| C06 | HTTP transport limits and their relationships | Intentionally different | `platform/server/src/transport.ts`; `platform/server/tests/transport-configuration-diagnostics-runtime.test.ts`. This owns request sizes, timeouts and headers-timeout <= request-timeout, with typed options, defaults and exact failure records. Do not move HTTP-specific policy into generic Core config. |
| C07 | Worker durable-processing lease guard | Already compliant locally | N05: `platform/workers/src/worker.ts` consumes the shared `platform/persistence/src/leasing` check and snapshots its accepted duration before polling. `configuration-diagnostics.ts` preserves the existing worker report. Startup and retry-configuration runtime fixtures prove rejection, single reads and shared-check use; final worker/persistence units passed. |
| C08 | In-memory rate-limiter numeric configuration | Already compliant | `platform/security/src/rate-limiting.ts`, `rate-limit-configuration.ts`; `platform/security/tests/configuration-predicate-diagnostics-runtime.test.ts`. DIAG-005 already shares the applicable numeric guard, proves actual caller use, defaults, RangeErrors and precise companion records. Do not redo it or silently tighten accepted integers. |
| C09 | PostgreSQL credentials, IAM selection, administration identity separation and certificate/TLS checks | Intentionally different | `platform/adapters/aws/persistence/postgresql/src/credentials.ts`, `rds-iam-authentication.ts`; `platform/security/src/certificates.ts`; target `kanbien-core-server-persistence-configuration.ts`, `-iam-authentication.ts`, `-role-credential.ts`, `-runtime-credential.ts`; existing composition `configuration-test.mjs`, plus `platform/security/tests/security-certificates-runtime.test.ts`. Provider rules and security content checks stay with those owners; target-owned path restrictions and distinct-username policy are not universal Core rules. No credential fetching or rotation redesign. |
| C10 | ALB client-address trust configuration | Intentionally different | `platform/adapters/aws/runtime/ecs-fargate/src/index.ts`; `tests/ecs-fargate-adapter-runtime.test.ts` in that adapter. The required ingress mode is provider-specific and rejects unsupported choices. Configuration of that trust does not prove deployed network restrictions. |
| C11 | Private HTTP persistence verifier inputs | Intentionally different | `infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.ts`, `-operation-diagnostics.ts`; composition `runtime-test.mjs`. Mode, private URL, record identity and fact checks are verifier-specific; their closed observations distinguish the rejected item. Do not force verification-operation inputs into the database schema. |
| C12 | DynamoDB persistence configuration | Deferred or retiring | N01A's required-field/type safety, contract/domain structure and compatibility are complete locally with the proof below. Remaining N01B index-specific rules, full configuration migration and affected client/store adoption stay deferred to persistence; no retiring-target migration. |
| C13 | SQS publisher/worker configuration and environment loader | Already compliant locally for the new path; legacy compatibility retained | N02 implemented `platform/adapters/aws/queue/sqs/src/configuration/` and guarded sender/worker factories with Core checks and Platform loading/composition proof. Existing constructors/environment factory retain documented historical behavior for supported callers; retiring targets are not migrated. See N02 execution for exact ownership, source/delivery and public catalogue proof. |
| C14 | Core-server migration/restore task-specific switches and expected-record inputs | Already compliant locally (N03) | Platform persistence `src/maintenance/` owns requirements, reference-proof formats and two safe reports. Target configuration binds existing source names; migration/restore consume checked instructions and preserve their original envelopes/defaults/effects. See N03 execution and its focused proof; engine/container/live qualification remains deferred. |
| C15 | Direct JWT verifier configuration | Already compliant locally (N04) | `platform/security/src/jwt-configuration/` owns checked startup instructions and safe reports; `jwt.ts` consumes the checked result. Cognito's caller is in `platform/adapters/aws/auth/cognito/src/cognito.ts`, exposed by its export-only index. N04 completion records constructor, signed-token, caller, type, catalogue and reader proof; live deployment remains separate. |
| C16 | Worker retry and outbox-relay startup policy options | Already compliant locally | N05 complete: worker-owned retry configuration and persistence-owned lease duration, checked-value consumption by actual worker/relay/lease callers, safe new diagnostics, public generated catalogues and governed tests. All six final units passed. Due-time scheduling, future expiry arithmetic and live coordination are not claimed by numeric/configuration proof. |
| C17 | Cognito environment reader and permission JSON parsing | Deferred or retiring | `platform/adapters/aws/auth/cognito/src/index.ts`; `tests/cognito-adapter-runtime.test.ts`. DIAG-006's reader-reuse assessment remains deferred. Existing missing/empty/JSON-entry diagnostics and security-owned claim/permission semantics remain; no generic strict-text replacement or broad Cognito rewrite authorised. Its direct JWT dependency is recorded in N04 without reopening DIAG-006. |
| C18 | DynamoDB rate-limiter environment reader | Deferred or retiring | `platform/adapters/aws/security/dynamodb-rate-limiter/src/rate-limiter.ts`; `tests/dynamodb-rate-limiter-runtime.test.ts`. Its numeric guard already reuses C08; text-source reuse remains deferred DIAG-006. Required-text checks accept whitespace-only strings unlike the strict generic text rule: preserve that distinction pending a deliberate compatibility decision. |
| C19 | Server/worker copying of permitted environment names | Deferred or retiring | `platform/server/src/configuration/runtime.ts`, `platform/workers/src/main.ts`; existing server configuration and worker process tests. DIAG-007 remains deferred. Copying defined values for app schemas is not itself validation and is not a defect merely because both loops exist. |
| C20 | Observability and CloudWatch configuration | Deferred or retiring | `platform/observability/src/configuration.ts`, `metric-series-configuration.ts`; `platform/adapters/aws/observability/cloudwatch/src/configuration.ts`, `index.ts`; `infra/04.deploy/03.product/entrypoints/kanbien-platform-observability.ts`. Keep with later observability work. The last helper is imported by core-server persistence despite its legacy filename: do not remove it as a retiring-only source. |
| C21 | Retiring kanbien-platform target wiring | Deferred or retiring | `products/kanbien-platform/src/`, target-only `infra/04.deploy/03.product/entrypoints/kanbien-platform-*.ts` consumers and their target bindings, except shared sources such as C20. Record existing callers for compatibility; do not migrate their runtime/deployment wiring. Reusable adapters C12/C13/C17/C18 are not retired merely because this target uses them. |
| C22 | Runtime contexts, fixed feature flags and test dependency injection | Intentionally different | `platform/runtime/src/contexts.ts`, `platform/contracts/src/flags.ts`, `platform/testing/src/index.ts`, `platform/workers/src/main.ts`; `platform/runtime/tests/context-diagnostics-runtime.test.ts`, `platform-runtime-runtime.test.ts`, `platform/testing/tests/config-evidence-runtime.test.ts`. These pass supplied readers/checked dependencies or fixed flags; they do not declare a new external dependency or promise dynamic config validation. Test helpers are not production secret loaders. |

### Bounded correction scopes — implementation not started

#### N01 — DynamoDB: bounded input safety; persistence/index work deferred

`dynamoDbPersistenceConfiguration()` iterates only `Object.entries(input)`.
An omitted `region` is never checked; a supplied non-string reaches `.trim()`
and can throw rather than produce a configuration rejection. Unknown extra
fields participate in checking and are spread into the accepted object.
For an oversized index, the diagnostic names the index but ordinary
`error.details.path` is always `tableName`. The existing configuration-specific
test checks a valid object and one empty region, not this matrix.

**Scope correction agreed with the user on 2026-11-03:** the earlier N01 proposal
bundled persistence/index migration into configuration cleanup. Split it into
N01A (the bounded slice below) and N01B (deferred until the persistence slice).
Recording the proposal did not authorise execution. The later user request
authorises N01A only; its current status and evidence are tracked below.

**N01A checks the shape of today's configuration only:** are the four fields
already required by the public type present, and are their supplied values
text? It does not decide which indexes should exist or what their definitions
should be. See the exact file, compatibility and verification map below.

**N01B belongs to the persistence slice:** decide required persistence
operations/lookups, the implementation's index definitions and their rules,
and infrastructure bindings. Apply the new configuration standards when that
work declares, loads, validates and reports the required configuration. Defer
the full DynamoDB requirements/assembly migration, its client/store/target
adoption, index-specific boundary tests, and the known oversized-index
`details.path` mismatch to that same slice. Existing index checks stay in place
meanwhile; deferral neither removes them nor marks their known gap complete.
There is no new table/index, retiring-target migration, data migration,
PostgreSQL interchangeability or database switching in N01A.

##### N01A proposed outcome and compatibility decisions

Status: **complete at the authorised local boundary on 2026-11-03**.
Work began at 06:32 UTC in the recorded worktree. Only N01A is selected;
final focused proof was confirmed at 06:50 UTC. N01B and N02–N05 remain
unimplemented. Existing local-only/no-installation,
no-Docker/cloud/deploy and no-Git-mutation boundaries remain in force.

| Case | Proposed outcome |
| --- | --- |
| Complete configuration with all four declared fields as strings | Run the existing blank/length checks and return the existing success/failure shape. Preserve accepted values, surrounding spaces, first-error order for these inputs and current copying behaviour. Do not trim accepted values. |
| Required field absent or undefined | Return `ok: false` with the existing adapter error code and a new exact `missing` diagnostic; do not skip the field. This intentionally closes an acceptance hole such as omitted region. |
| Required field supplied as a number, null, boolean, array or object | Return `ok: false` with exact `wrong-type` evidence instead of letting `.trim()` throw. No conversion to text. |
| Entire configuration is null, an array or another non-object value | Return `ok: false` with logical field `configuration` and `wrong-shape`; do not invent an individual missing field. The public TypeScript input signature remains unchanged. |
| More than one required-field presence/type failure | Return the first in the declared order: region, tableName, outboxDueIndexName, lineageCauseIndexName. These malformed/incomplete inputs gain a defined safety preflight; this is not a new aggregate-error API. |
| Empty or spaces-only supplied text | Preserve the current blank rejection and existing v1 diagnostic. No new index validation rule. |
| Additional properties | Do not introduce an allowlist, strip them, or change their legacy checking/copying behaviour in this slice. Extra-property policy and complete arbitrary-object hardening remain explicit later work. |
| A property accessor or other source operation throws | Preserve the original thrown failure; do not diagnose its cause as missing or wrong-type without that evidence. No secret value or arbitrary exception text in the new records. |

Apply the common presence/type guard to the four existing fields, including
index-name fields, solely because today's public contract already requires
them to be text. This is distinct from declaring new index requirements.
No new index length/format/existence rule, index boundary-test campaign or
index resource work is included. If the user wants even that common guard
deferred for index-name fields, revise this proposal before sign-off.

Reuse applicable existing Core config readers/reason names. Retain the existing
adapter's blank-text behaviour instead of forcing it through the stricter
generic text rule. No Core API, Platform loading framework, source provider,
adapter-wide migration or new public loading API is required here. The bounded
configuration-only structural refactor below is included: deferring persistence
behaviour does not justify a different separation of contracts and capabilities.
The complete source-independent requirements/assembly path remains N01B.

##### N01A agreed organisational correction

The user requested this planning correction on 2026-11-03. Use the same
contract/domain responsibility separation as PostgreSQL, without copying files
for capabilities not included in this slice. This supersedes the earlier
"no new source folders" proposal. That correction initially authorised only
the plan edit; the later implementation request authorised N01A's source moves
and bounded behaviour correction. Completion evidence is recorded below.

```text
platform/adapters/aws/persistence/dynamodb/src/
├── index.ts                            # retained public exports
├── configuration.ts [u]                # compatibility re-exports only
└── configuration/ [n]
    ├── index.ts [n]                    # exports only
    ├── contract/ [n]
    │   ├── types.ts [n]                # existing configuration input/result value
    │   └── errors.ts [n]               # existing configuration failure shape
    └── domain/ [n]
        └── validation.ts [n]           # checker and its cohesive private helper
```

Map every existing declaration explicitly:

- `DynamoDbPersistenceConfiguration` moves from `configuration.ts` to
  `configuration/contract/types.ts`; retain its four readonly string fields.
- `DynamoDbPersistenceConfigurationError` moves to
  `configuration/contract/errors.ts`; retain its public shape and optional
  diagnostic field. Error-specific types belong with error contracts.
- `dynamoDbPersistenceConfiguration()` and private `configurationField()` move
  together to `configuration/domain/validation.ts`. Add the approved safety
  correction there; do not split each small helper into another file.
- The new `configuration/index.ts` deliberately re-exports the existing public
  function and two types. Keep imports, definitions and executable logic out
  of that index. Validation depends directly on its owning contracts, not
  through its own public index; contracts do not depend on validation.
- Existing `configuration.ts` becomes a compatibility re-export of those same
  names. Existing adapter `src/index.ts` and private callers such as `client.ts`
  can keep their current `./configuration` imports. Keep one implementation,
  not a legacy checker alongside a new checker.

No configuration requirements/assembly/source-provider files are added merely
to match PostgreSQL's file count. Their actual capabilities remain N01B.
Diagnostic definitions retain the Platform persistence owner below; the move
does not create a second adapter-local definition or catalogue.

##### N01A diagnostic ownership

`persistence.configuration-invalid` v1 currently permits only `blank` and
`too-long`. Keep that definition and all its existing records unchanged.
N01A adds one additive, code-owned `persistence.configuration-input-invalid` v1
definition in the existing Platform persistence catalogue. It identifies only
a finite logical field (region/store/outbox-index/lineage-index/configuration)
and the applicable presence/type/shape reason. Reuse shared configuration
reason names; the actual predicates establish which reason is true.

Retain the existing outer error code
`PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID`, `defaultMessage`,
`details` and optional diagnostic field. For the newly handled malformed cases,
`details.path` and the diagnostic must identify the same declared field; the
whole-input case uses a fixed configuration reference. Exclude actual values,
table/index names, arbitrary property names and raw exception messages.
Register/export the new definition through existing owners and regenerate the
existing JSON projection; do not create an adapter-specific parallel catalogue
or move the combined Core catalogue.

##### N01A expected file changes

`[u]` means update an existing file after sign-off; `[n]` means a proposed new
file. Four new source files implement the configuration-only structure above;
the rest of the adapter is not being reorganised.

| File | Planned change |
| --- | --- |
| `[u] platform/adapters/aws/persistence/dynamodb/src/configuration.ts` | Replace moved declarations with compatibility re-exports; preserve all existing names/imports and use one underlying checker. |
| `[n] platform/adapters/aws/persistence/dynamodb/src/configuration/index.ts` | Export the checker and its public types only; no implementation or initialisation logic. |
| `[n] platform/adapters/aws/persistence/dynamodb/src/configuration/contract/types.ts` | Own the existing configuration type without changing its four required string fields. |
| `[n] platform/adapters/aws/persistence/dynamodb/src/configuration/contract/errors.ts` | Own the existing error type and its diagnostic reference, keeping the public failure shape. |
| `[n] platform/adapters/aws/persistence/dynamodb/src/configuration/domain/validation.ts` | Own the moved checker/private helper plus narrow required-field/type preflight; preserve existing blank/length checks and index behaviour. |
| `[u] platform/adapters/aws/persistence/dynamodb/tests/dynamodb-persistence-adapter-runtime.test.ts` | Extend the real checker tests with the matrix and exact records below; prove old/new export identity and retained type/import resolution; retain all existing storage-operation assertions. |
| `[u] platform/persistence/src/diagnostics.ts` | Add the one closed presence/type/shape definition and constructor; include it in the existing catalogue without altering v1 definitions. |
| `[u] platform/persistence/src/index.ts` | Export the additive diagnostic API only; no implementation logic. |
| `[u] platform/persistence/tests/platform-persistence-runtime.test.ts` | Prove the new record's accepted fields/reasons and rejection of undeclared or sensitive detail; preserve historical definition assertions. |
| `[u] platform/persistence/contracts/diagnostics.v1.json` | Regenerate using the existing catalogue exporter; historical definitions remain unchanged. |
| `[u] platform/adapters/aws/persistence/dynamodb/README.md` | Explain the bounded guarantee and the persistence/index work still deferred, using the existing README skill. It explains policy; it does not become the requirements owner. |
| `[u] scripts/repo/diagnostic-coverage/reviews.v1.json` | Update only affected existing source-bound owner records after review; preserve unrelated review/debt statuses. |
| `[u] .agentic/03.product/plans/implementation/configuration-ownership-and-loading.md` | Track sign-off, actual scope, timing, corrections and proof; do not close N01B. |

Retained participants, **not planned edits**: adapter `src/index.ts`, `client.ts`,
`outbox-store.ts`, `processing-store.ts`, `lineage-store.ts`, `transactions.ts`,
`records.ts`, `observations.ts`, package dependencies and current test runner;
Core config/diagnostics, Platform config and all target/infra sources. Review
actual diagnostic readers for additive-catalogue compatibility and all imports
of the existing configuration module before moves. The compatibility shim is
why client/store sources need no mechanical migration; temporary compilation
must prove those retained imports resolve. Existing source globs already cover
nested TypeScript files; confirm before changing any build/test configuration.
If a required affected consumer falls outside this map, record the exact gap
and revise the scope rather than silently expand into N01B.

##### N01A sequential work and tests, after sign-off

1. Capture current source/catalogue baselines and the existing owner records;
   confirm there are no conflicting edits. Record the signed-off matrix and
   declaration/import map above; follow the existing artifact-path migration
   workflow for the structural move. Keep public paths as compatibility shims.
2. Extend the existing adapter test with literal expected results independent
   of the production predicates. Cover each declared field missing/undefined,
   wrong-type values, malformed whole inputs, deterministic first failure,
   existing valid/blank behaviour, preserved extra-property behaviour and an
   original throwing accessor. Assert the exact outer code, logical field,
   reason and absence of synthetic private canaries. Do not add index-specific
   255/256 or resource-definition tests in this slice.
3. Move the existing declarations into the mapped contracts/domain files,
   establish the export-only index and compatibility shim, then add the
   diagnostic definition/export/tests and checker correction. Prove legacy
   `configuration.ts`, the new configuration index and the adapter's package
   root expose the same function, with the existing types still resolvable.
   Use narrow temporary compilation and the affected compiled test files
   while developing. Exercise the actual exported checker, not a replacement
   helper or a test-only imitation of production startup.
4. Complete documentation, generated output, affected review records and
   consolidated source review before final proof. Review counterexamples:
   omitted region incorrectly accepted, a number causing `.trim()` to throw,
   wrong field/reason and a value leaking into output must fail assertions.
5. Run final registered focused units once on stable inputs:

   ```bash
   bash scripts/repo/check-selection/script.sh --checks dynamodb-persistence-runtime platform-persistence-runtime diagnostic-catalog-readers module-index-structure --execute-local --json
   ```

   <!-- deterministic-check: allow reason="task-specific selection and scheduling of existing registered units requires source-impact judgment; the existing selector owns execution, identity and receipt reuse" -->
   These are existing units. Do not separately rerun their package aggregates
   merely to obtain a second pass. The existing structure check covers the new
   export-only index; no new structural checker or regression framework is
   proposed. Record the exact result and elapsed time;
   planned commands are not current proof. Catalogue freshness and diagnostic
   adoption/review checks follow their existing owners on the affected paths.
6. Validate metadata, links and whitespace, and obtain the non-executing
   exact-path impact plan. Preserve additional integration/package/live
   obligations for the recorded stable-batch/owning stage, not per edit.
7. Close only N01A with exact evidence and remaining limitations. No caller
   migration is included: the client factory still accepts its typed options,
   so this slice does **not** prove every production caller checks them or
   stops startup on failure. N01B must prove that actual loading/adoption path.

Record UTC start/end and measured command durations in this plan's activity
journal, distinguishing inspection, implementation, review, preparation and
verification. Retain mistakes and affected retries; do not rerun unchanged
suites. No installation, Docker, cloud, deployment or Git mutation is part of
the proposed slice.

##### N01B persistence handoff — deferred, not lost

- [ ] Establish module-owned persistence operations and required lookup
  guarantees; adapter-owned translation and actual index structures follow.
- [ ] Decide index-name/format/length/existence requirements and infrastructure
  bindings under those owners; do not define them in an entrypoint.
- [ ] Declare reusable dependency configuration requirements and checked
  assembly, reuse Platform loading/Core checks, and adopt it in selected
  non-retiring composition with checked-result and failure-before-work proof.
- [ ] Reconcile extra-property policy, legacy acceptance/order and the known
  oversized-index `details.path` mismatch; add the corresponding index-specific
  tests and safe diagnostics as part of that persistence change.
- [ ] Preserve supported imports and versioned diagnostic readers; separate
  local adapter proof from separately authorised resource/deployment proof.

N01B is not an instruction to make DynamoDB selectable as PostgreSQL or to
migrate the retiring kanbien-platform target.

#### N02 — SQS: separate reusable requirements from concrete source names

Status: implemented and locally verified 2026-11-04; see the N02 execution
record below. The following describes the retained legacy boundary; new work
uses the added strict source-independent path.

The environment loader embeds `PLATFORM_WORKER_SQS_*` names and local text/
integer reading; there is no source-independent requirements/assembly path
equivalent to PostgreSQL's. The existing constructors already check queue
address, region and numeric ranges; retain their provider-owned meanings.
`Number(raw)` accepts text spellings that strict Core integer text rejects,
including blank text as zero for the zero-minimum timing settings. The SDK
constructors can also create the client before downstream option checks.

Scope: a bounded adapter-owned requirements/assembly path, compatible old
exports, target-owned bindings for any adopted non-retiring caller and explicit
construction-order policy. Do not rewrite the retiring SQS target consumer or
silently tighten legacy spellings/read order/throw behaviour. Reconcile existing
SQS diagnostic records and failed-source attribution, not a new queue framework.

Focused proof: missing/blank text, existing numeric spellings, wait 0/20/21,
visibility 0/43200/43201, exact setting/reason, checked values, source failures
and no SDK construction after rejected input on the new loading path. Preserve
existing producer/worker behaviour in `sqs-adapter-runtime.test.ts`. Any change
to legacy constructor side effects needs an explicit compatibility disposition.

#### N03 — Core-server task controls: retain the exact reason for rejection

Status: implemented and locally verified 2026-11-04; see the N03 execution
record below. Other N items and deferred deployment work are not included.

Before N03, migration rejected an unsupported `PERSISTENCE_MIGRATION_OPERATION` with a task
code but no supplied diagnostic identifying that switch. Restore's combined
guard similarly collapses unsupported diagnostic mode and absent/invalid
expected record ID/digest. Base database/IAM/certificate checks are already
structured and must not be redone.

Scope (revised by the user's N03 ownership discussion): Platform-owned task
requirements and safe bounded reasons; target-owned environment bindings,
actual entrypoint propagation and existing task reader/schema consumers.
Keep operation meanings, omitted defaults, connection-only mode, output
envelopes, exit status, call order and rejection before pool/probe/query work.
Do not emit record IDs, digests, credentials, raw values or physical paths.

Focused proof: omitted/accepted/unsupported migration switch; omitted/accepted/
unsupported restore mode; record-ID and digest failures separately; exact
diagnostic attribution and public output safety; no downstream operation on
rejection. Extend composition `configuration-test.mjs` and
`restore-diagnostic-test.mjs` rather than run a live migration or restore.

#### N04 — JWT configuration: establish and check the startup contract

Status: **implemented and verified locally**. The user agreed the configuration rules
during the walkthrough and requested this detailed planning update on
2026-11-04, then explicitly authorised local implementation. Work began at
16:57:58 UTC; final proof was confirmed at 17:30:57 UTC. Deployment and broad
integration authority remain unchanged; their proof is not claimed here.
This section supersedes the original unscoped N04 paragraph, not earlier proof.

##### Responsibility and actual gap

`createJwksJwtVerifier()` in `platform/security/src/jwt.ts` already checks token
signatures, issuer, required claims and times. It accepts verifier instructions
without a corresponding construction-time guard. A supplied numeric `NaN`
clock tolerance can therefore reach time comparisons unchecked. Token-failure
and key-fetch diagnostics do not establish that those instructions were valid.

The constructor must check its instructions before returning a usable verifier.
Platform security owns these requirements; Cognito translates its provider
configuration into them; target composition chooses concrete identities and
sources. Core supplies applicable generic checks, bounded issue collection,
record construction/selection and optional delivery, not authentication policy.
Do not add token policy to Core queues/config or define it in an entrypoint.

##### Agreed rules and compatibility

| Input | Construction-time treatment |
| --- | --- |
| `clockSkewSeconds` omitted (`undefined`) | Retain the 60-second default. |
| Supplied clock tolerance | Require an actual finite number at least zero; accept zero, negative zero and non-negative fractions. No new maximum is invented. Reject negative values, NaN, infinities and non-numbers; do not stringify or apply the integer parser. |
| `issuer` | Require text that is neither empty nor whitespace-only and has no surrounding whitespace. Preserve exact identity comparison: no trimming, lowercasing, trailing-slash removal or universal URL requirement. The existing `"issuer"` test identifier remains valid. |
| `jwksUri`, either fetching path | Require nonempty/nonblank text without surrounding whitespace; preserve its exact contents for the selected fetcher. |
| Built-in network fetching | Additionally require a well-formed absolute HTTPS address. No automatic plain-HTTP/local exemption. This checks configuration syntax/scheme, not reachability, trusted destination, redirects or key contents. |
| Supplied fetching implementation | Require a callable `fetch` member. Do not impose HTTPS/URL syntax on its source identifier; trusted implementation code owns any additional source-format rules. This is not a fetcher chosen by an incoming token/request. |
| `requiredClaims` omitted | Retain no additional requirements; built-in signature/issuer/expiry/subject checks still apply. An explicitly empty list remains valid. |
| Supplied claim requirements | Require a list of rule objects. Each rule needs a nonempty/nonblank claim name without surrounding whitespace and exactly one comparison form: `equals` or `oneOf`. |
| `equals` | Require a supported scalar: text, finite number or boolean. Preserve zero, false, empty expected text and exact comparisons; do not coerce or trim expected values. |
| `oneOf` | Require a nonempty list of supported scalars. Report the rule position and offending value position, not the submitted name/value. Do not silently deduplicate or merge distinct rules. |
| Clock omitted | Retain the existing system-clock default. |
| Supplied clock | Require a callable `now` member. Do not invoke it during construction. |

These are deliberate new rejection rules, not a behaviour-neutral file move.
Treat explicit `null` for optional typed inputs as a supplied invalid value,
not omission: this tightens previous nullish defaults and belongs in the
compatibility tests. Valid values/defaults and successful factory signatures
stay unchanged. Required text distinguishes missing, wrong type, empty, blank
and surrounding whitespace. No construction probe may call the clock, fetch
keys, process a token, schedule retries or contact a provider.

Inspecting current source/callers found HTTPS identifiers in all existing uses.
Supplied fetchers in security/Cognito tests return keys from memory; no current
plain-HTTP/file-source caller was found in the inspected runtime/test roots.
The public custom-fetcher contract still accepts a string, so that search is
not authority to narrow it to web addresses or make claims about external users.

Read instructions into checked, stable configuration, preserving method
receivers and callable dependencies' internal state. Do not validate a copy and
then continue using mutable unchecked option fields. Explicitly test mutation
of the original requirement list/options after construction. Do not freeze a
caller-owned dependency object or call it speculatively. Startup member reads
needed for these new checks are intentional; a throwing accessor is a sourcing
failure, not proof of missing/invalid contents. Preserve unexpected thrown
values rather than indiscriminately translating them into configuration errors.

##### Files, public boundaries and dependency direction

`[n]` means new and `[u]` updated, all **planned**. This is a bounded extraction
of JWT contract declarations, not a whole Platform security reorganisation.

```text
platform/security/
  package.json                                      [u] public local JSON asset
  README.md                                         [u] bounded ownership explanation
  src/
    index.ts                                        [u] re-exports only
    jwt.ts                                          [u] check instructions, then verify tokens
    jwt-contract.ts                                 [n] existing JWT interfaces/types, one owner
    diagnostics.ts                                  [u] register new selected definitions
    README.md                                       [u] current source/file map
    jwt-configuration/                              [n]
      index.ts                                      [n] re-exports only
      README.md                                     [n] concrete examples and responsibilities
      contract/
        requirements.ts                             [n] security-owned rules/defaults
        reporting/
          errors.ts                                 [n] recognised fixed configuration failure
          diagnostics.ts                            [n] closed diagnostic and local catalogue
          diagnostics.v1.json                       [n] generated, never separately authored
      domain/
        validation.ts                               [n] check/snapshot inputs; no dependency calls
  tests/
    jwt-configuration-runtime.test.ts                [n] predicates and constructor integration
    jwt-configuration-types.test.ts                  [n] public contract compatibility
    platform-security-runtime.test.ts               [u] accepted token behaviour
    security-operation-diagnostics-runtime.test.ts   [u] configuration versus token/key failures

platform/adapters/aws/auth/cognito/
  src/index.ts                                      [u] retained public exports only
  src/cognito.ts                                    [n] existing implementation extracted intact
  tests/cognito-adapter-runtime.test.ts              [u] real factory/environment caller proof
  tests/cognito-adapter-types.test.ts                [n] retained public signatures
  tests/run-runtime-tests.mjs                        [u only if new asset/import shim requires it]
```

`jwt-contract.ts` owns the existing JWT options/claim/key/fetcher/verifier types,
which `jwt.ts` continues to expose for compatible internal imports and the
public security index exposes without signature changes. Both validation and
verification depend on that contract; it imports neither implementation. This
avoids a contract importing the `jwt.ts` capability or a validation/verification
cycle. The new module's requirements use these existing types; do not maintain
a second independent model. Successful checked configuration may use an inferred
or derived internal type, not another manually copied public interface.

Cognito's existing mixed index is a pinned legacy allowance. Because this slice
must change its factory error handling, plan its bounded implementation extraction
instead of refreshing a pin to bless changed logic. Preserve all existing public
exports and helpers, including `cognitoIssuer` and `cognitoJwksUri`; update internal
imports and remove only its now-stale allowance in
`scripts/repo/module-structure/legacy.v1.json`. No other legacy allowance changes.
Review the extraction under the existing path-migration/structure workflow.

Connected planned owners:

- `scripts/repo/diagnostic-coverage/export-catalogs.mjs`: export the module-local
  catalogue through the existing generator, retaining the aggregate selection.
- `scripts/repo/diagnostic-coverage/smoke-test.py`: public JSON packaging,
  deterministic generation, old/new reader and fixed-version compatibility cases.
- `platform/security/contracts/diagnostics.v1.json`: generated aggregate gains
  the new definition; every existing code/version remains identical. Reader
  families do not automatically widen to security configuration codes.
- `scripts/repo/diagnostic-coverage/reviews.v1.json`: source-reviewed bindings
  and precise tests/checks; retain unrelated partial/deferred debt.
- Existing configuration/module/safe-diagnostic standards already own generic
  checking, role separation, explicit reason selection and shared delivery.
  Add only a bounded JWT configuration paragraph to
  `.agentic/03.product/standards/config-runtime-settings.md` naming this checked
  constructor path and the supported custom/default-fetcher distinction. Do
  not duplicate authentication rules into AGENTS or a README. Runtime contracts
  remain authoritative for the values/diagnostic schema.
- This plan and the existing session README own progress, scope, timing and
  consolidated review. No new tracking registry or parallel implementation plan.

No Core implementation expansion is currently planned. Reuse Core config's text
and finite-number readers where acceptance matches and its existing bounded
issue collector. Callable members, URI policy and nested claim requirements are
security-owned checks. Never force finite fractional numbers through an integer
rule or convert arbitrary supplied objects into text to use a generic checker.
<!-- deterministic-check: allow reason="deciding whether a missing mechanism is genuinely shared requires architectural and source-impact judgment; this slice makes no Core implementation change" -->
Only extend Core if implementation proves a genuinely shared missing mechanism;
record that necessity before changing the scoped file inventory.

##### Failure, diagnostic and caller contract

Proposed new identity: `security.jwt-configuration-invalid`, definition version 1.
Its owner is Platform security, not Core's shared reason vocabulary. Detail has
fixed `phase: verifier-construction`, `effect: verifier-not-created`, a bounded
list of issues and explicit `truncated`. Use Core's existing 32-issue collector,
not a new arbitrary limit or unbounded diagnostic payload. Continue independent
checks where safe, without proceeding past a source throw or claiming unperformed
checks ran. Success returns checked configuration, not a successful connection.

Each issue uses explicit code-owned logical settings, such as issuer, key-source,
clock-tolerance, required-claims, required-claim.name, required-claim.comparison,
required-claim.value, clock.now and key-fetcher.fetch. Select existing shared
reason names where appropriate and security-specific names for distinguishable
non-finite/negative, scheme, ambiguous comparison and non-callable conditions.
The executable contract must enumerate the exact allowed alternatives before
tests/JSON generation; it must not inherit a growing list of all shared reasons.

For nested rules, Core issue `index` identifies the rule; `attributeIndex`
identifies the value within `oneOf`. Define their applicability explicitly:
a missing/malformed whole list has no invented rule position. No supplied claim
name/value, issuer, address, token, raw exception or physical source name appears
in diagnostic detail. No new unproved authentication/authorization conclusion.

- `createJwksJwtVerifier()` retains its successful verifier return type. A
  recognised invalid-configuration result becomes a fixed `TypeError` carrying
  the approved diagnostic, proposed message/code
  `PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID`. This is not
  `PLATFORM_SECURITY_INVALID_TOKEN`, and does not extend token-result errors to
  disguise a construction failure. Use an owned constructor/type guard, not
  arbitrary exception-message matching to identify the recognised error.
- Direct Cognito factories preserve that recognised construction failure and
  diagnostic. The environment factory converts only this owned error into its
  existing `PLATFORM_ADAPTER_AWS_COGNITO_CONFIG_INVALID` failed result, retaining
  its code, defaultMessage/details structure and safe logical attribution.
  Existing environment/JSON parse failures retain their original precedence.
  Other thrown values keep their existing propagation; no catch-all relabelling.
- Attach the diagnostic so existing public `securityFailureDiagnosticRecord` /
  `securityDiagnosticRecordsFrom` can retain it after catalogue registration.
  Preserve startup handling through the available approved reporter. No new
  mandatory reporter service or source-fetching abstraction is introduced.
  Optional delivery uses DIAG-011's Core mechanism, not another copied promise
  handler. Returning/throwing a diagnostic does not prove it was logged.
- Target auth wiring in the retiring kanbien-platform target is not migrated.
  Local direct/Cognito caller fixtures prove failure propagation; any claim of
  actual target startup delivery needs its own authorised target proof.

##### Sequential implementation, tests and gates (completed locally)

1. **Baseline/inventory:** re-read exact source, callers, exports, pinned Cognito
   implementation and all affected tests/shims; snapshot original files, public
   type signatures and all catalogue bytes. List every changed path and predicate
   in this plan/session. Reconcile any new compatibility discovery before edits.
2. **Contracts first:** extract JWT declarations with unchanged public aliases;
   implement security-owned rules, diagnostic/error constructors and local
   catalogue. Confirm no contract-to-capability or own-index cycle. Do not build
   a whole JWT module framework or add empty folders.
3. **Checker/constructor:** implement stable checked instructions and bind them
   into the actual verifier. Add exact rule/default tests, failure diagnostics,
   source-throw and later-mutation proof. Keep valid token behaviour unchanged.
4. **Cognito integration:** perform the bounded index extraction; translate only
   recognised failures in the environment factory. Test direct factories and
   existing environment/permission parsing, then extend the actual local server
   fixture to establish that failed configuration cannot produce a usable hook.
5. **Connected changes:** update generator/JSON/public asset, caller shims and
   public type tests; scoped harness/README explanations and source reviews.
   Apply the README skill when authoring, not comment-per-declaration expansion.
6. **Consolidated review:** close all required corrections and map each material
   guarantee to a counterexample. Prepare metadata once, confirm no editing
   agents, freeze exact inputs and obtain nonexecuting full-impact selection.
7. **Final focused batch once:** use existing registered units
   `platform-security-runtime`, `security-cognito-diagnostics`,
   `diagnostic-catalog-readers` and `module-index-structure`. Add
   `module-index-structure-regression` only if the checker/allowance-removal
   regression itself is changed; do not run every repository suite by default.
   Other affected integration/payload obligations stay at the agreed stable
   batch boundary. No dependency install, Docker/cloud/deploy or Git mutation.
8. **Close honestly:** compare frozen inputs and retained definitions, record
   actual commands/results, source-review corrections, non-applicability and
   remaining integration/live limits. Mark N04 implemented only with that proof.

During development compile only affected code/tests to fresh temporary CommonJS
output using the existing package tsconfigs and local TypeScript compiler.
Reuse existing runtime-runner package shims, but execute only the new JWT
configuration and affected existing security/Cognito files for exploratory
proof. No dependency downloads. Final registered units provide complete affected
package type/build/runtime/boundary proof; exploratory runs are not reusable
trusted receipts. Do not rerun unchanged suites for each adjacent file change.

Minimum predicate/caller assertions:

- Clock tolerance: omitted -> 60; 0/fraction/positive accepted; null/text/boolean/
  NaN/infinities/negative rejected with exact logical item/reason. Signed-token
  boundary cases prove default and supplied tolerance are actually used, not
  merely accepted by a helper.
- Issuer/source: missing/type/empty/blank/surrounding whitespace separately;
  non-URL issuer accepted; exact comparison retained. Default fetcher rejects
  malformed/non-HTTPS source before any fetch; custom source identifier stays
  exact and is not rejected merely for being non-URL.
- Claims: omitted/empty requirements accepted; scalar 0/false/empty text valid;
  exact/oneOf success and token mismatch retained. Reject whole-list/entry/name/
  comparison/value errors, both/neither comparison forms and empty oneOf, with
  exact rule/value positions. Prove independent failures, overflow/truncation
  and no submitted names/values in reports.
- Dependencies: missing defaults and valid supplied dependencies; malformed
  supplied objects/methods reject before any clock/fetch call. Preserve receiver
  identity and later stateful behaviour. A callable method alone does not prove
  its future results, a valid returned date or network success; do not claim it.
- Real integration: substitute the checker to prove the real verifier consumes
  its checked snapshot, rejects its failed result and never uses an unchecked
  fallback. Test both direct Cognito calls and the environment caller's precise
  result translation; unrelated throws/source failures must not become invalid
  contents. Keep existing environment/permission failure order and token tests.
- Reporting/readers: exact new packet and runtime extraction; optional sink
  throws/rejections cannot replace the construction failure. Malformed/private
  fields and synthetic secret canaries reject; old records stay readable,
  same-version mutation fails, local/aggregate membership and public JSON asset
  resolution use fresh output. Narrow deployment readers remain narrow.

##### Activity and measurement

Implementation inventory: the planned tree and connected owners above are the
bounded task paths. Also update the existing security runtime runner's Core
config shim, Cognito's boundary fixture for checked package-local imports,
security's public asset boundary fixture and the exporter's disposable fixture
manifest list. These are required consumers, not new capabilities. Existing
JWT/security definitions stay immutable; only the security aggregate and new
local JSON may gain the new definition. Migration disposition: Cognito index
remains its public export surface; implementation moves to cognito.ts. Existing
jwt.ts remains substantive verification code with compatible type re-exports.
No namespace/compatibility removal warrants a new ADR. Reference planner output
and recoverable originals: /tmp/N04-jwt-J6xLkt/{cognito-reference-plan.txt,before.tar}.
Record active source/test references through supported exports, retaining
historical course/session paths. No whole-module or retiring-target migration.

Record UTC timestamps in the existing session journal for investigation,
implementation, corrections, exploratory proof, source review, preparation,
final verification and closeout. Separate human discussion/waiting from execution.
Record check IDs, child durations and runner planning/fingerprint/runtime/receipt
overhead without double-counting. Record failed attempts and why each affected
rerun was necessary; no new time-tracking framework. This planning update runs
only scoped document metadata/link/structure/whitespace checks, not runtime suites.

##### Implementation review — 2026-11-04

At the final handoff, stages 1–5 and the consolidated self-review were complete;
preparation and registered verification were still pending. The reviewer is the implementing parent
agent, with no delegated editors. The exact 31-path inventory is recorded in
/tmp/N04-jwt-J6xLkt/paths.json. The existing platform-security-runtime and
security-operation-diagnostics runtime files required no edits and remain
regression proof, rather than being changed merely to match the proposed tree.

The checker reuses Core text/number reading and bounded issue collection without
moving token policy into Core. Empty and blank text remain distinct. Fractions
are valid tolerance values, so an integer parser would be incorrect. Checked
options and claim lists are snapshots; dependency methods are captured once with
their receiver preserved, without calling or freezing the original dependencies.
The constructor uses that checked result. Cognito translates only errors created
by the owned constructor, not exceptions sharing its message. Source/property
getter exceptions still propagate unchanged: this slice does not invent a
source-failure diagnosis, prove future clock values or harden network redirects.

Reviewed counterexamples and rejecting assertions cover invalid configuration
reaching verification, ignoring the checked result, later option/list mutation,
premature dependency calls, lost receivers, scalar coercion, tolerance defaults
and boundaries, malformed claim comparisons, spoofed exceptions, secret-bearing
records, and incorrect nested issue positions. Bounded helper substitution tests
exercise the actual constructor, rather than only testing a disconnected helper.

Exploratory runtime/type/boundary tests passed for security and Cognito. Fresh
catalogue generation and focused reader/asset fixtures passed. All 95 previous
security definitions compare exactly; the aggregate gains one definition and its
local public JSON asset. The other 19 catalogue files remain byte-identical.
Fourteen unchanged Cognito helper bodies match the recorded original. All 20
README links resolve. Adoption reports no findings (574 sources: 123 adopted,
261 partial/support, 190 existing legacy debt). Structure reports no findings
(46 indexes, 19 legacy allowances, seven role-based modules). Removing Cognito's
obsolete mixed-index allowance did not change another allowance or the checker.

Corrections were closed before final verification: the generic Core issue type
needed runtime-checked record construction without widening the closed schema;
the focused Python methods belong to ReaderTests, not DiscoveryTests; the broad
internal reader already accepts security records, whereas the narrow config and
operation readers must reject this code. Reader behaviour was not broadened to
satisfy the fixture. One sandbox-rejected cache write and two atomic patch-context
failures made no source changes; the affected invocation/document update alone
was corrected. None is reported as a passing verification.

Final focused units are platform-security-runtime, security-cognito-diagnostics,
diagnostic-catalog-readers and module-index-structure. Prepare metadata, freeze
the reviewed inputs, then execute those units once. Full impact planning remains
nonexecuting; broad integration and live target/deployment proof stay deferred.
No Core implementation, retiring target, dependency installation or cloud action
was added. The README skill informed the source-backed ownership explanations,
worked examples and explicit limits.

##### Final local proof and remaining boundary

All eight stages are complete for N04. Preparation passed in 41.998 seconds;
the initial preparation stopped on the plan's human-judgment condition, which
was annotated before retrying preparation. No final runtime suite had started.
The nonexecuting impact plan recorded 118 obligations with zero findings and
executed none. It is not authority or evidence for their broader execution.

The single final registered invocation was:

```bash
bash scripts/repo/check-selection/script.sh --checks platform-security-runtime security-cognito-diagnostics diagnostic-catalog-readers module-index-structure --execute-local --json
```

All four units executed and passed, without a retry or reused receipt:
catalogue/readers 36.585872 s; structure 1.962985 s; security runtime 25.329374 s;
Cognito diagnostics 25.919910 s. Runner elapsed was 119.512648 s, including
89.798141 s command execution, 5.928789 s planning, 2.355269 s fingerprints,
18.826091 s runtime identity, 2.525665 s receipt validation and 0.078718 s other
overhead. These are disjoint buckets, not additional elapsed time.

All 31 frozen task hashes matched after verification. All 95 original security
definitions remain exactly equal; only the new configuration definition was
added, and the other 19 catalogue files remain byte-identical. The comparison
helper initially addressed definitions at the export root rather than under
catalog; only that read-only comparison was corrected and repeated. No source
or runtime fixture changed after the frozen pass. Final adoption has no findings
with the reviewed counts above. Evidence is in /tmp/N04-jwt-J6xLkt/
{preparation-final.log,final-focused.json,final-focused.stderr.log,
final-adoption.json,frozen-inputs.json,paths.json,catalogues-before.tar}.

Default tolerance and supported valid-token behaviour are preserved. Rejecting
invalid construction inputs is the intentional policy tightening documented
above. No dependency installation, Docker/cloud/deployment, staging, commit or
push occurred. Outcome-only updates to this plan/session do not require repeating
unchanged runtime suites. N05, other inventory work, broad integration, actual
target startup delivery and live provider qualification are not completed by N04.

#### N05 — Worker retry / relay: make policy assumptions explicit at startup

Status: **complete locally**, 2026-11-04 18:50 UTC. Started 18:16:35 UTC.
The user agreed the three responsibilities, ownership/layout, diagnostic and
verification proposal, then requested recording and implementation together.

Agreed predicates: omitted maxAttempts defaults to three; supplied limits must
be actual finite positive whole numbers. Null is rejected rather than defaulted.
Omitted retryBackoffMs retains attempt * 1000; a supplied member must be callable.
Invoke it once only when retry is needed. Its returned delay must be an actual
finite nonnegative number, including fractions and zero. Invalid return throws
an owned fixed error/record before queue.retry; callback throws retain identity
and existing boundary diagnosis. Existing handler/settlement order is preserved.
Lease duration is required, finite, positive and whole in milliseconds; no new
default or maximum. Platform persistence owns this rule and workers reuse it.

New owners: platform/workers/src/configuration/ and
platform/persistence/src/leasing/, each with an export-only index.ts, README.md,
contract/requirements.ts, contract/reporting/{diagnostics.ts,errors.ts,
diagnostics.v1.json}, and domain/validation/ (worker startup.ts and retry-delay.ts;
persistence duration.ts). Existing public package indexes re-export only.
Worker worker.ts and persistence relay.ts/types.ts consume checked results;
their diagnostics.ts files compose new local definitions into existing catalogues.
No new Core implementation or change to the pinned Core queues index. Assess
queueAttempt through its public import; never copy its unsafe params into reports.

New identities: platform-worker.retry-configuration-invalid,
platform-worker.retry-delay-invalid, persistence.relay-configuration-invalid,
all version 1. Old code/version definitions remain fixed. Startup records name
logical field/reason and creation prevented; delay records state retry was not
submitted, with prior job/settlement effects not erased. Existing worker durable
lease and persistence local-rejection records retain their shapes/reasons.
Caller reporting supplies capability/operation/stage through existing internal
reporters; direct constructor errors retain the record even without a sink.
No raw option, message, getter exception or dependency identifier is copied.

Compatibility disposition: worker creation retains its Result shape and existing
mount/schema failure precedence. Relay success still returns a relay; invalid
configuration now throws a fixed typed error carrying its owned record, before
clock/store/queue work. Read duration and retry options once and retain checked
values; update affected getter-count fixtures deliberately to prove snapshots.
Getter throws preserve original identity, not a false invalid-content diagnosis.
Lease construction still uses its existing failure code/record/message/params for
ordinary inputs, now based on the same value that was checked. Future expiry
arithmetic and coordination semantics remain separate from numeric validation.

Affected consumers: worker startup/configuration and delivery fixtures; persistence
lease/store/relay and observer fixtures; DynamoDB outbox/processing callers of
nextPlatformPersistenceLease; smoke app relay caller; public types and package
boundaries. Existing PostgreSQL integration/retiring target relay imports retain
their public API, with broad/live proof deferred. No target edits planned.
Update workers/persistence package.json JSON exports, aggregate JSON, existing
exporter and reader/asset fixtures, review ledger, scoped READMEs and the owning
configuration standard. No new registry or checker framework.

Sequence: (1) shared lease contract/checker and consumers; (2) worker configuration
and actual retry boundary; (3) exact runtime/type/consumer tests; (4) generated
exports/readers/harness/docs; (5) consolidated review and corrections; (6) metadata
preparation, frozen inputs and one final registered focused batch; (7) closeout.
Use narrow worker/persistence test files during development. Final units:
platform-workers-runtime, platform-persistence-runtime, dynamodb-persistence-runtime,
platform-smoke-runtime, diagnostic-catalog-readers, module-index-structure.
Impact planning is nonexecuting; broad integration remains at the stable batch.

Counterexamples to reject: invalid option bypassing construction; calculator
invoked early or twice; changed original options bypassing validation; invalid
delay reaching queue.retry; duplicate sends/retries; swallowed source exception;
reporter failure changing operation outcome; copied duration rule instead of
shared use; old catalogue mutation or private/stale/missing local JSON exports.
Record exact tests and source-matched review before final proof. Baseline and
timing evidence: /tmp/N05-worker-leases-SxbeZ1. No parallel editing agents.

Consolidated self-review, 2026-11-04 18:39 UTC: the parent reviewed the complete
N05 source delta against this inventory. Required corrections are closed:
preserve eager reads of unrelated worker options while snapshotting only checked
inputs; observe relay expiry before the publication step clears its lease; use
existing catalogue owners (`platform-worker`, `persistence`) matching code
prefixes. Public constructors and old definitions remain; nonnumeric legacy
lease error params now use fixed `invalid`, avoiding arbitrary object coercion.
New modules follow contract/reporting and domain/validation ownership with
export-only indexes. Existing broad worker/persistence files remain bounded
legacy consumers, not an unrequested structural rewrite.

Counterexample proof: `retry-configuration-runtime.test.ts` rejects invalid
startup before queue selection, early/double calculator invocation, unchecked
calculator results reaching retry, rereading mutable values, reporter exceptions
changing the result, secret canaries in records, and ignored checked return
values (test-only checker substitution). Existing delivery fixtures preserve raw
calculator throws and settlement behavior. `leasing-configuration-runtime.test.ts`
proves all invalid duration categories, rejection before dependencies, one send,
one duration read and shared-check/result use by relay/lease creation; the worker
fixture proves its shared lease dependency. Updated legacy getter fixtures now
assert the explicitly agreed single-read contract. Type fixtures preserve public
input and readonly-output shapes.

The changed cross-language reader fixture and disposable packaging fixture pass:
three new identities, local/combined parity, public JSON resolution, private-path
rejection, actual reporter delivery and stale/missing/duplicate asset rejection.
Baseline comparison found all 265 prior definitions unchanged; only the two
existing aggregate catalogues gain the new definitions. README skill review
covers both new modules' files/exports/examples and existing parent links; links
resolve. Source-matched diagnostic adoption validation passes. Final registered
verification remains pending below; exploratory passes are not its replacement.

Activity: 18:16–18:24 ownership, baseline, implementation and first fixtures;
18:24–18:39 connected tests, catalogue/docs and consolidated corrections.
Avoidable work: initial fixture type assumptions and a missing durable message
identity; an exploratory test filter typo selected the whole worker runner and
stopped on the unrelated-getter regression; that filter was corrected before
later runs. The packaging fixture initially hid subprocess stderr; it now
surfaces the actual assertion. These were development corrections, not repeated
final verification. No broad integration batch has been run.

Final proof, 18:42–18:50 UTC: scoped lifecycle/header/process-drift/command-drift
preparation and nonexecuting impact planning passed. One registered six-unit
batch passed without corrections or reruns. All 41 frozen task files matched
their pre-verification hashes afterward. Only this outcome record and the session
journal are changed after that comparison; no runtime inputs are changed.

| Registered unit | Result | Command seconds |
| --- | --- | ---: |
| diagnostic-catalog-readers | Passed | 78.815 |
| dynamodb-persistence-runtime | Passed | 51.275 |
| module-index-structure | Passed | 3.549 |
| platform-persistence-runtime | Passed | 57.941 |
| platform-smoke-runtime | Passed | 82.421 |
| platform-workers-runtime | Passed | 138.857 |

Final selector wall time was 487.537 seconds (8m08s): 412.858 seconds executing
commands and 74.679 seconds planning, identifying runtimes, fingerprinting and
validating receipts. None of the old receipts matched these changed inputs;
each selected unit executed once. Total work to this outcome was approximately
34 minutes, including implementation, exploratory corrections, documentation,
preparation and final proof. Safe local evidence is in
`/tmp/N05-worker-leases-SxbeZ1/{preparation.log,final.log,paths.json,frozen.json}`;
trusted receipts remain in the existing worktree-private check cache. This
durable summary records the outcomes if temporary files are later removed.
No install, Docker, cloud, deployment, stage, commit or push was performed.
Broader integration remains deferred to the recorded stable-batch boundary.

Deferred scheduling follow-up (confirmed, not implemented by N05):
platform/workers/src/queue.ts stores delayMs but next() immediately shifts the
next entry. A future worker/queue slice must define due-time scheduling, clock,
ordering and idle semantics; prove no early delivery, due delivery, zero delay,
multiple delayed jobs and restart/provider behaviour where supported. Update
owning queue/worker contracts, harness guidance and fixtures together. N05 tests
requested delay values only and must not claim elapsed-time scheduling proof.

Pre-implementation finding (resolved by the bounded changes above): the worker
checked its durable-processing lease, but `maxAttempts` was selected with
`?? 3` without a startup validity check. `retryBackoffMs` is a callback whose
future result cannot be proven by reading configuration at startup. Relay takes
numeric `leaseDurationMs` and passes it to a later claim operation without its
own constructor check; store-level handling depended on operation/state and was
not a single startup contract.

Scope: decide the owning constraints and where checked inputs are guaranteed;
add missing startup checks for fixed numeric policy, or demonstrate and test an
existing enforced checked-input contract. Validate a backoff callback's returned
delay at use, without invoking it early merely to satisfy startup validation.
Preserve retry defaults, delivery/lease semantics and observation isolation;
changed rejection behaviour needs a compatibility disposition.

Focused proof: default/valid/invalid attempt limits and relay lease, failure
before queue/store work, invalid/throwing backoff result at the actual boundary,
accepted retry timing and no duplicate effects. Extend the existing worker and
persistence runtime tests, not the retiring target or a new scheduler.

### Recommended sequence and verification boundary

1. The register and N01A were reviewed with the user; keep C17–C21 deferred.
   The subsequent execution request selects N01A, not all of N01–N05.
2. Implement the authorised N01A boundary and organisation. N01B remains with
   the later persistence slice; N01A is not the full DynamoDB reference
   migration. N03 remains a separately selectable core-server diagnostic slice.
3. Scope N02, N04 and N05 separately in this same plan as selected. Reuse
   relevant existing guards rather than automatically route every local check
   through a stricter generic parser. Do not build the F01–F07 capabilities.
4. During an approved implementation, use its named existing test files and
   temporary local compilation for development. Close connected changes and
   review corrections first. Final registered units are selected from the
   existing check catalogue after the actual file set is known; run a shared
   unit once per stable input identity, not once per register row.
5. Preserve the existing broader stable-batch/package/live obligations and
   permissions. No broad suites, Docker, installation, cloud operations or
   deployment are required merely to record this inventory.

### Inventory activity journal

| UTC | Activity | Outcome |
| --- | --- | --- |
| 2026-11-03 05:45–05:51 | Read-only source/caller/test review across supported runtime roots; reconciled DIAG-006/007, observability and retiring-target boundaries | Identified 22 responsibility families and five bounded correction scopes. Existing proof identified, not rerun. Some over-broad search output was truncated; followed with targeted source/test reads. One unmatched test filename glob was corrected by listing actual files; no test command ran. |
| 2026-11-03 05:51 | Recorded inventory, compatibility decisions needed and focused proof expectations | One existing plan updated; implementation of N01–N05 remains unstarted. Focused verification passed: one metadata header, 22 unique dispositions (5 compliant, 7 intentionally different, 5 need correction, 5 deferred/retiring), five correction scopes, 48 explicit owner/test paths, all 22 plan links/anchors and whitespace. No runtime suite or implementation change. |
| 2026-11-03 06:08 | Applied the user's persistence/index deferral and mapped N01A for sign-off | Split N01 into proposed input-safety N01A and deferred persistence/index N01B. Nine existing planned files and final focused units identified; no new source folders or caller migration. Scoped metadata, pending/deferred status, nine path checks, all 22 plan links/anchors and whitespace passed. No implementation or runtime tests started. |
| 2026-11-03 06:31 | Corrected N01A's proposed organisation at the user's request | Superseded the earlier no-new-folder choice with four mapped contract/domain/index files and the existing configuration compatibility shim; source scope remains configuration-only and N01B remains deferred. Added import/export/type compatibility proof and the existing structure unit. Scoped metadata, nine existing/four proposed path checks, pending sign-off, 22 links/anchors and whitespace passed. Only this plan changed; no source moves or runtime suites. |

### N01A execution and source-review handoff

The user's implementation request authorises the revised organisation and the
N01A outcome matrix. Implementation began 2026-11-03 06:32 UTC. This is a
configuration-only refactor/safety correction, not the N01B loading adoption.
The 13-path change is the exact expected file inventory above. All pre-existing
dirty source is retained; baseline copies are in `/tmp/dynamodb-N01A-LFuV6r`.

Migration disposition: the old configuration path is a retained re-export
wrapper; no path was deleted. The governed planner found 19 exact old-path
references and one new-path reference before edits, including plan/review,
education and historical evidence. Historical references are not rewritten.
The adapter public index plus client/outbox/processing/lineage/transaction
imports retain the old wrapper. Temporary compilation proves them together.
Recovery is the scoped inverse of the four declaration moves plus restoration
of this task's additive edits from the baseline, preserving unrelated work;
it is not an authorised reset. No durable namespace/public-path change needs
a new ADR; this applies the existing module-structure decision.

| Predicate / responsibility | Owning definition and actual proof |
| --- | --- |
| Whole input is null, an array or a non-object | Adapter guard establishes wrong-shape; new `persistence.configuration-input-invalid@1` identifies only configuration. Actual exported checker tests all these alternatives. |
| Each declared property is absent/undefined | Core string reader returns CONFIG_MISSING from the captured entries; adapter binds the fixed field and missing reason. Four-field omission/undefined and empty-object assertions reject the former acceptance hole. |
| Each declared property has a non-string value | Core string reader establishes wrong-type without coercion. Null, numbers, non-finite numbers, booleans, arrays, objects, symbols, bigint and functions have exact value-free error assertions. |
| Several presence/type failures | Fixed four-field order determines first failure. This is the approved malformed-input preflight, not aggregation or a changed blank-string order. |
| Existing blank and accepted text | Existing blank v1 is retained, including empty/whitespace text and supplied-property first-error order. Accepted padded strings, extra copying and unknown-extra legacy failure remain explicitly tested. |
| Original input accessor throws or has read effects | Original Object.entries boundary stays outside reclassification. Identity and eleven accepted getter reads match the old sequence. Core reads only a captured map; content coercion is not invoked. |
| Shared checker actually used and its output handled | Compiled actual validation module with fixture-only Core reader substitutions proves all four calls, failure handling and checked text reaching the next blank check. Independent literal outputs reject ignored failure, wrong field/reason and value disclosure. |
| Diagnostic construction and retention | Platform owns one additive definition selecting shared names explicitly; its constructor/parser rejects undeclared detail. Existing configuration v1 still rejects missing. Existing selected catalogue supplies generic readers; no new production sink, target binding or operation-reader widening. |
| Public and private imports | Root, legacy configuration and grouped index expose the same function. Both type paths remain assignable; all client/store sources compile unchanged. New index only re-exports. |

The code/version identifies configuration checking; the finite field identifies
the attempted item and reason. Rejected configuration is established, but no
database availability, deployed source location or startup outcome is inferred.
N01A returns a safe record rather than adding a sink; the future actual caller
must provide workload context and handle rejection under N01B. No source-fetch
failure is inferred from a thrown accessor. Extra-field/global object hardening,
index-specific policy/error-path correction and actual client adoption remain
explicit debt, not claims of completion.

Consolidated self-review closed at 06:44 UTC: reviewed all declaration moves,
real public/private consumers, exact predicate/diagnostic alternatives, inherited
behaviour, generated output, partial review dispositions and README examples.
Counterexample sensitivity is established by literal results and actual helper
substitution: skipped/ignored Core checking, incorrect checked text, missing
region accepted, wrong attribution and private detail cannot satisfy the tests.
No required correction remains; there is no contributing agent editing inputs.
Normal preparation precedes the final four registered units; broad checks stay
at the separate stable-batch boundary.

| UTC / duration | Activity | Result |
| --- | --- | --- |
| 2026-11-03 06:32 | Read scoped governance, read the README skill/standard/template, inspected consumers and captured baselines | N01A only; no package installation, Docker, cloud, deployment or Git mutation. |
| 15.55 s / 13.50 s | Parallel temporary DynamoDB / Platform persistence compilation | Both passed. |
| 0.83 s / 0.49 s | Actual compiled DynamoDB test / affected Platform persistence runtime file | Both passed; not registered receipts. |
| 8.47 s / 0.62 s | Temporary catalogue compilation / existing exporter | Passed; 41 prior persistence definitions unchanged, exactly one additive definition. |
| 8.82 s / 0.79 s | Added actual Core reader-use fixture, recompiled and reran only affected DynamoDB test | Passed; intentional changed-test rerun, not a repeat of unchanged proof. |
| 2026-11-03 06:44 | Diagnostic adoption and consolidated source review | 556 discovered, 106 adopted, 260 partial/support, 190 unchanged legacy debt; no findings. Source review closed before final preparation. |
| 0.88 s | First preparation attempt | Metadata passed; process-drift check flagged task-specific reuse/scheduling prose as a scriptable sequence. Added the existing supported judgment marker, not a new script or weakened runtime check. No runtime suite started; preparation must rerun on the corrected plan. |

Avoidable work: the planner's historical references included huge embedded
evidence lines, producing unnecessary output; retain just its disposition
summary here. One generated review-ledger patch used unsupported unified hunk
headers and was rejected without changing files; corrected before applying.
No runtime assertion was loosened and no failed runtime test is relabelled.

### N01A completion evidence — 2026-11-03

- [x] Configuration declarations moved to the agreed contract/domain owners;
  old/root/new-index imports expose the same function and compatible types.
- [x] Required-field/type/shape corrections and safe exact reports implemented;
  existing accepted/blank/getter/extra-property behaviour retained as scoped.
- [x] Actual Core-reader call, ignored-failure and checked-text substitutions
  pass in the existing adapter test, alongside all previous storage assertions.
- [x] Existing diagnostic v1 remains unchanged; one additive input definition
  registered and generated through the existing exporter. All 41 prior
  persistence definitions are identical. Of 18 captured catalogue files, only
  `platform/persistence/contracts/diagnostics.v1.json` changed content.
- [x] Consolidated source review, partial owner-record reconciliation,
  adoption and metadata preparation completed before the final run.
- [x] README skill applied; success and full missing-region example executed
  against the actual public export. Four README links and 22 plan links/anchors
  passed. Governed migration check passed with the retained wrapper.
- [x] All four final registered focused units passed; all 13 frozen task-file
  hashes matched before and after execution. Outcomes-only plan/session entries
  are recorded after that comparison, not edits during verification.
- [x] Broader impact/qualification remains explicit; N01B is still deferred.

| Final registered check | Outcome | Command elapsed seconds |
| --- | --- | --- |
| diagnostic-catalog-readers | passed, executed | 23.925316 |
| dynamodb-persistence-runtime | passed, executed | 26.002716 |
| module-index-structure | passed, executed | 1.966187 |
| platform-persistence-runtime | passed, executed | 23.044635 |

Final runner elapsed 105.054401 s (105.21 s wrapper), command execution
74.938854 s, runtime identity 19.771614 s and fingerprinting 2.228551 s.
All four executed once in this final pass; none reused. Temporary direct tests
above are exploratory proof, not trusted registered receipts. No broad suite
or container/live check ran. Report: `/tmp/dynamodb-N01A-LFuV6r/final-focus.json`;
keyed private runner receipts, not this temporary pointer, govern future reuse.

Corrected preparation passed in 36.24 s after the recorded 0.88 s prose-gate
failure. Its exact 13-path non-executing impact plan has zero findings and
95 distinct check rows/IDs: 87 local, 3 package, 2 deploy and 3 acceptance.
Only the four focused local units were executed here. The other 83 local units
remain for the separate stable-batch boundary and eight later-stage units
remain with their owning stages/permissions. Their selection neither authorises
retiring-target work nor establishes their proof. No obligation was removed
to make the focused result pass.

Local N01A closure does not mean DynamoDB configuration adoption is complete:
index requirements, the oversized-index error-path mismatch, extra-property
policy and actual caller/client loading remain N01B. No index-specific rule,
SQL, resource, dependency, client/store wiring or deployment was changed.
The only new source files are the four planned configuration files; the session
record is additional outcomes-only bookkeeping. No staging, commit, push,
installation, Docker, cloud, deployment or discarded user work occurred.


## DIAG-009 and DIAG-010 — retire redundant configuration bridges

Local implementation authorised by the user on 2026-11-03. Both old paths have
**retired** disposition: PostgreSQL `platform/adapters/aws/persistence/postgresql/src/config.ts`
and DynamoDB `platform/adapters/aws/persistence/dynamodb/src/configuration.ts`.
Their existing configuration folders remain canonical. Package manifests expose
only the root; no supported public subpath is removed. No ADR is required:
public contracts, layer layout and bootstrap surfaces stay unchanged.

### Sequence and bounded inventory

1. Record DIAG-010 and the approved two-file retirement; capture task baselines.
2. Redirect PostgreSQL's nine consumers to configuration/index. Configuration
   is an adopted submodule: sibling adapter files must use its interface, not
   private contract/domain paths. Within configuration, owners remain direct.
3. Redirect DynamoDB's root exports to configuration/index and five internal
   type consumers (client, outbox-store, processing-store, lineage-store and
   transactions) to configuration/index. Retire its sibling file.
4. Update root/type identity fixtures, relative-import/retired-file regression
   checks, existing compatibility guidance, README explanations/current-source
   links and source-bound review entries. Preserve historical snapshots and
   partial/deferred review dispositions. No validation predicate changes.
5. Review connected changes; compile both adapters and the actual core-server
   composition into separate fresh temporary directories. Run existing adapter
   runtime/boundary fixtures, fresh removed-file resolution counterexamples and
   the existing target configuration fixture. No live database is involved.
6. Freeze after corrections/preparation; run the three registered focused units
   once. Record outcomes and timings afterwards. Broader integration/package/live
   checks remain at the separate stable-batch/owning stages.

Canonical owners are configuration/contract/{types,errors,requirements}.ts and
configuration/domain/{validation,assembly}.ts for PostgreSQL; DynamoDB uses its
existing contract/{types,errors}.ts and domain/validation.ts. Public root indexes
only redirect exports. No implementation, diagnostic code/version/detail, source
binding, default, SQL, TLS, credential, index policy or dependency changes.
DynamoDB's folder import remains resolvable; only its explicit sibling file is
retired. Existing root adapter metadata is untouched, not silently refactored.

Reference buckets: executable imports/tests and source-bound reviews are active;
README and education current-source links are active; original lesson snapshots
and commitLogs are historical evidence. Earlier phase records describe their
then-retained wrappers, not a continuing compatibility promise. The source
snapshot in `/tmp/config-bridge-retirement-KbjvSK` is local recovery evidence;
no Git state or user work is discarded. Restore only this task's changes if a
correction is required, never reset the entire dirty worktree.

<!-- deterministic-check: allow reason="task-specific selection and scheduling of existing registered units requires source-impact judgment; the existing selector owns execution, identity and receipt reuse" -->
Final focused units: `postgresql-connection-diagnostics`,
`dynamodb-persistence-runtime`, `module-index-structure`. No separate unchanged
catalogue runtime suite is necessary if canonical definitions, exports and all
18 captured JSON catalogue contents remain identical. Existing adoption and
metadata/path checks still apply; focused success does not imply live proof.

### Activity journal

| UTC / duration | Activity | Outcome |
| --- | --- | --- |
| 2026-11-03 09:07–09:16 | Re-established session, scoped retirement consumers, read migration/README guidance and recorded DIAG-010 | Two local shim retirements only; no new service or diagnostic behaviour. |


Retirement review: all fifteen changed adapter source files differ from their
captured baseline only in import/export module specifiers. Both implementation
folders, configuration predicates and return construction are byte-identical.
Review statuses/debt remain unchanged; only affected source hashes and retired
source membership change. Public names/types and root-only package exports stay
unchanged. README skill applied to bounded explanation/link updates; original
course filenames, snapshots and session history remain evidence, not active
import instructions.

| UTC / duration | Activity | Outcome |
| --- | --- | --- |
| 09:15 / 2.62 s | Both boundary fixtures and module structure check | Boundary fixtures passed; structure check correctly rejected fourteen private submodule imports. Corrected callers to the supported configuration index, not a checker exception. |
| 14.28 / 13.88 / 14.78 s | Exploratory PostgreSQL, DynamoDB and target compiles | Passed; import-path correction followed, so these are not final source-matched proof. Fresh current-source proof follows. |
| 1.84 s | Structure check after correction | No findings; no legacy-index allowance changed. |

Avoidable work: the first caller mapping overlooked the already-enforced
configuration submodule boundary. The narrow structure check caught it before
final verification. Two guessed inspection paths did not exist; no tests or
source changes were hidden by those read-only command failures. The existing
migration helper recognises commitLogs as history but not course snapshot
markers or original task records: record those false positives explicitly rather
than deleting evidence or allowing an executable compatibility wrapper.


### Connected review and focused development proof

- Fresh current-source PostgreSQL/DynamoDB compilation passed in 13.19/13.56 s;
  actual core-server persistence compilation passed in 14.35 s. Both removed
  sibling JavaScript files are absent; explicit old-file resolution fails with
  MODULE_NOT_FOUND, while configuration/index resolves and the real public
  runtime fixtures pass (2.23 s together), including PostgreSQL driver/TLS tests.
- Existing target configuration fixture passed: 561 rejection-before-pool cases,
  migration deadline and TLS authority. Its first invocation lacked the existing
  payload-shim preparation and failed at module resolution (0.23 s), not at a
  runtime assertion. Applied the existing prepare-runtime command to temporary
  output, reran only this affected fixture, and passed in 1.30 s. No install.
- Diagnostic adoption passed: 554 discovered, 106 adopted, 258 partial/support,
  190 unchanged legacy-debt sources; no findings. Exactly two removed sources
  account for the lower count; no review status or debt was erased.
- Both migration planners ran with output redirected. The migration checker
  reports six PostgreSQL and two DynamoDB references, all reviewed historical
  task/lesson attribution, not executable imports or broken current links.
  The path standard explicitly permits clearly historical evidence. The helper
  only recognises commitLogs and rulebook retirements as history, so its literal
  old-path scan is not green; do not claim it passed or use the wrapper allowance.
  The eight locations are configuration-reason-selection line 71; backlog's
  original DIAG-001 story and DIAG-009 removal summary; the initial coverage
  inventory; file-index's two historical labels; and lessons 064/067 course-file
  markers. Current-source links now point to live configuration indexes.
- Consolidated review closed: original source bodies and root export names are
  unchanged; no new dependency/cycle/private-import exception; fresh public and
  real target callers work; review hashes match only reviewed imports. No agent
  is editing these inputs. Complete lifecycle preparation before one final
  registered focused pass. Historical helper limitation is recorded, not hidden.


### DIAG-009/010 local completion — 2026-11-03

- [x] Both redundant sibling forwarding files retired; fifteen actual source
  files redirect imports/exports through the supported configuration indexes.
  Only module specifiers changed. Public names/types, configuration behaviour,
  SQL, TLS, credentials, defaults, dependencies and all 18 catalogue bytes stay.
- [x] Existing public runtime/type, relative-source boundary and retired-file
  fixtures pass; actual core-server configuration fixture passes with fresh
  temporary output. No cached JavaScript can satisfy the explicit removed-file
  counterexample. Boundary fixtures prevent either sibling bridge returning.
- [x] Existing harness standard explains bridge purpose/consumers/retirement;
  active README/course links follow current owners. README skill kept these
  bounded and source-backed, preserving original snapshot attribution.
- [x] Affected source-bound reviews reconciled; adopted/partial/deferred statuses
  retained. Adoption passed with 554 discovered and no findings.
- [x] Preparation and final focused proof completed on stable inputs. All 50
  captured states, including two absences and 18 catalogue hashes, matched after
  final execution. This outcomes-only record and backlog/session closure follow
  that comparison; source/tests/reviews/standard are not being edited afterwards.

| Final registered unit | Result | Seconds |
| --- | --- | --- |
| dynamodb-persistence-runtime | passed, executed | 25.539478 |
| module-index-structure | passed, executed | 2.049846 |
| postgresql-connection-diagnostics | passed, executed | 25.079245 |

Runner elapsed 74.844953 s (74.98 s wrapper), command execution 52.668569 s,
runtime identity 13.345055 s and fingerprinting 1.176673 s. All three executed
once in this final pass, none reused. Evidence:
`/tmp/config-bridge-retirement-KbjvSK/final-focused.json`; existing keyed runner
receipts, not this temporary pointer, govern future trusted reuse.

Preparation first rejected the two deliberately deleted paths as missing input
(0.93 s, no lifecycle edits applied). Re-ran the existing metadata helper on the
30 surviving task files, retaining both deletions in the task inventory and
explicit fresh-output proof: preparation passed in 39.77 s. Six artifact headers,
deterministic-process and governed-command checks passed. Its non-executing
impact report has no findings, 101 rows/100 unique IDs: 90 local, 4 package,
3 deploy and 4 acceptance rows. Only the three focused units above executed;
other obligations remain at the stable-batch/owning stages, not waived or passed.
Sixteen affected configuration links resolve; scoped whitespace checks pass.

Local completion is at 09:23:56 UTC, following the 09:07 start. Thirty-two task
paths plus outcomes-only session logging changed; two of the paths are approved
removals. Avoidable work was the initial private-submodule import mapping,
missing fixture-shim preparation, deleted-path metadata inputs and excessive
inspection output from single-line JSON. These were tooling/planning corrections,
not failing assertions weakened to make proof pass. No broad suite was repeated.

The existing migration helper's six PostgreSQL/two DynamoDB historical-marker
findings remain explicitly non-green as described above. Existing path governance
permits clearly historical evidence; no executable old reference, broken current
link or public compatibility obligation remains, and no checker exception was
introduced. Both removed files are in the temporary before.tar snapshot. N01B,
DIAG-006/007, CloudWatch and retiring-target work stay deferred. No installation,
Docker/cloud/deployment, staging/commit/push or discarded existing work occurred.


## N03 execution — Platform maintenance instructions, 2026-11-04

Authorised by “please implement”; started 09:18:27 UTC in the recorded October
27 worktree. Local source/tests/harness/docs only: no installation, Docker,
cloud/deployment or Git mutation. No subagent requested or contributing.
Snapshots: /tmp/N03-maintenance-eoSjqP/{before,catalogues-before}.tar. Preserve
all existing work. This is not a restart of an earlier goal.

### Sequence, owners and consumers (before runtime edits)

1. Core config: add finite-choice instruction, canonical unsupported-value name
   and shared checking. Fixed legacy lists/definitions stay fixed. Malformed
   programmer choice declarations need one additive bounded diagnostic rather
   than widening old declaration contracts or reading source values first.
2. Platform persistence: maintenance/index.ts and README.md;
   contract/instructions.ts, acceptance-proof.ts, reporting/diagnostics.ts;
   domain/validation/instructions.ts. Own apply/connection choices, defaults,
   conditional requirements and the narrow existing reference-proof format.
   Legacy core-persistence prefix is not a universal application-record rule;
   exact expected ID/fingerprint remain supplied by the target.
3. Target configuration binds logical inputs, uses the existing Platform loader
   through the maintenance checker and selects definitions. Migration/restore
   entrypoints consume checked instructions, preserving DB sequence/envelopes.
4. Add two definitions to Platform/selected target catalogues; generated local
   reporting JSON plus supported package JSON subpath, retaining aggregates.
   Existing generator and readers only; no parallel vocabulary/registry.
5. Finish actual-caller/reader/asset fixtures, README/harness updates and reviewed
   source hashes before final focused verification. No SQL/table/engine rewrite,
   apps package, storage-selection framework or deferred N01B/JWT/SQS/worker work.

Consumers: ConfigSettingRule users (Core checker/type/runtime tests, immutable
constraints, PostgreSQL IAM rules, target config), Platform maintenance/root
indexes and catalogue assembly, existing runtime/compilation discovery,
configuration serializer, both task entrypoints, Python runtime_contract.py and
migration/restore/deployment readers, catalogue compatibility/export/public JSON
asset fixtures and actual compiled core-server payload. Base DB/IAM/TLS unchanged.

### Predicate and compatibility inventory

| Boundary | Established facts and alternatives | Definition / proof |
| --- | --- | --- |
| migration.operation | Omitted defaults apply; wrong-type, blank, surrounding-whitespace, unsupported-value reject before pool. | persistence.migration-instructions-invalid v1; direct and real-entrypoint tests. |
| verification.mode | Only connection explicitly accepted; undefined/non-text/blank/surrounding-whitespace retain absent/default treatment. Usable unsupported string rejects without invented record requirements. | persistence.verification-instructions-invalid v1; defaults/mode/verdict tests. |
| verification.expected-record-id | Record mode: missing, wrong-type, blank, surrounding-whitespace, invalid-format. Connection mode ignores validity. | Same verification definition; checked-value/actual-caller tests. |
| verification.expected-fingerprint | Same five reasons; retain exactly 64 lowercase hex. Aggregate independent ID/fingerprint issues in order. | Same definition; combined and sensitive-canary fixtures. |
| Source throws | Neither missing nor invalid contents inferred; preserve throw identity and read order/counts. No invented source continuation. | Existing source observations plus getter fixtures. |
| Delivery | Task code/version identifies attempted instruction validation, item/reason identifies predicate; rejection-before-work known, provider state not inferred. | Selected runtime definitions → task serializer → generated target catalogue → actual Python reader; no supplied values/source keys in detail. |
| Shared declarations | Invalid choice definitions fail before source reads with bounded metadata, not user-input blame. | Core declaration tests; old versions/default selections unchanged. |

Fifteen normal failures: four migration, one mode, five each ID/fingerprint.
Permit only appropriate field/reason combinations. Migration control read stays
after base/IAM/CA. Restore reads mode after base, authentication before expected
ID then fingerprint; certificate check remains before reporting invalid controls.
Preserve original mode projection on early base failures. Accepted instructions
must carry checked values, not reread original environment values.

### Gates and verification

- [x] Scope, consumer/predicate inventory and baselines recorded before edits.
- [x] Shared choice rule and focused Core runtime/type proof.
- [x] Maintenance contracts, fifteen failures, defaults, exact safe records.
- [x] Actual caller wiring, checked use, preserved observations/effects.
- [x] Local/combined JSON, public asset resolution and reader preservation.
- [x] Connected docs/harness/reviews complete; consolidated self-review closed.
- [x] Metadata preparation, adoption, frozen final focused verification.

<!-- deterministic-check: allow reason="task-specific selection and stable-batch scheduling require source-impact judgment; existing registered units own execution and receipt reuse" -->
Development uses temporary compilation and only affected test files. Final
registered candidates: core-runtime, platform-persistence-runtime,
diagnostic-catalog-readers, module-index-structure, persistence-composition,
restore-connection-diagnostics. Confirm overlap/order against actual catalog
before one stable final batch. Full non-executing impact is still recorded;
broader integration/package/live obligations remain at their owning boundary.
Maintenance *-runtime test is covered by existing compilation/discovery; no new
runner. README skill governs source-backed guides. No dependencies installed.

| UTC / duration | Activity | Outcome |
| --- | --- | --- |
| 09:18:27–09:22 | Governance, caller/test wiring and source baselines | Recorded worktree confirmed; ownership split preserved. Initial attempt to print complete catalogue JSON exceeded tool output; switched to archive plus small hashes, no source edit or test affected. |
| 09:22–09:38 | Connected Core/Platform/target implementation and focused development proof | Core runtime, maintenance runtime, both source compilations, generation, reader selection, module structure and persistence boundaries passed. All 15 normal failures covered. Initial Python invocation named the wrong test class; corrected to the existing focused test selector. Two patch-context attempts failed without edits and were corrected. |
| 09:38–09:44 | Actual compiled caller and cleanup proof; correction | Existing migration/restore cleanup fixtures exposed duplicate catalogue registration introduced by this slice. Kept runtime owner catalogues disjoint and added a separate combined task reader export; did not weaken reporter validation or cleanup assertions. An attempted exporter run against the narrower target compilation lacked workers and rewrote temporary package shims; reran complete catalogue compilation separately and restored payload preparation before both actual caller fixtures passed. No active-worktree package/install change. |
| 09:44–09:50 | Documentation, governance, catalogue and type review | README skill used for a full maintenance guide and bounded Core/Platform updates. Added task-ownership/check-use requirements to the harness standard, explicit public type proof and local JSON freshness counterexamples. Type checks passed. All previous code/version definitions across the 18 baseline JSON files remain byte-equivalent as parsed definitions; only the expected four exports changed, with a new local maintenance asset. Link review caught and corrected one excess parent-directory component. |

### Consolidated review before final verification

The reported normal failures retain the existing broad task codes/envelopes and
stop before new work. Default mode and apply selection, source access/throw
identity, returned checked values, independent own/source cleanup evidence,
conditional expected-record requirements, pattern bounds and secret exclusion
have focused tests. Definitions constrain vocabulary; producer tests—not the
schema cross-product alone—establish the fifteen truthful field/reason pairs.
The optional checker is trusted composition code, not an untrusted validation
bypass. Existing catalogue definitions remain unchanged; the new choice-schema
diagnostic reports programmer declaration faults, separately from user input.

Final review correction: the complete Core canonical-reason assertion in
`packages/core/tests/diagnostic-record-runtime.test.ts` and package identity
assertion in `foundation-diagnostics-runtime.test.ts` were missed by the initial
consumer inventory. Both are now explicitly updated for the additive reason
and declaration diagnostic; historical reason-list assertions remain unchanged.
The second omission surfaced after the first correction, causing one avoidable
Core-only rerun. After correcting both expected lists, direct foundation proof
exposed an actual compatibility regression: the added choice branches reread
the rule getter/discriminant for existing rules. Cache the already-read kind
at each existing decision boundary instead; retain the original getter-count
assertion and add accepted-text kind-read proof. All three affected Core test
files now pass directly. No SQL, task, catalogue definition or response change
was needed for this correction.

All six other registered units passed in the first frozen batch. After the
shared-checker correction, rerun its five actual consuming units: Core runtime,
Platform config, Platform persistence, catalogue readers and target composition.
The passed module-structure and restore-controller Python units have unchanged
relevant structure/catalogue/controller inputs and are not rerun. Do not claim
their previous broad input fingerprints are reusable after unrelated Core test
or checker changes; wider receipt obligations remain at the stable-batch boundary.

| 09:50–09:57 | Scoped preparation and first frozen seven-unit batch | No input mutation during verification. Six units passed: catalogue 26.68s, structure 1.80s, composition 88.72s, Platform config 19.16s, Platform persistence 21.69s, restore controller 1.15s. Core failed at an omitted expected-reason assertion (16.50s). Existing selector intentionally discards child output; used the existing compiled runtime runner to locate the failing assertion without rebuilding. |
| 09:57–10:02 | Review correction and narrow diagnosis | A Core-only retry (17.31s) exposed the second omitted catalogue identity assertion. Directly compiling/running the affected files then caught the extra getter read; fixed implementation rather than relaxing compatibility assertions. Added accepted-text getter proof and all three affected Core files passed. One status-query syntax error affected no source or test. Consolidate affected tests and source corrections before the final five-unit retry; no unchanged controller/structure rerun. |

Final focused batch: core-runtime, platform-config-runtime,
platform-persistence-runtime, diagnostic-catalog-readers,
module-index-structure, persistence-composition, restore-connection-diagnostics.
Platform config is included because it supplies the actual shared checker
callback. Composition owns the actual task fixtures; restore-connection-diagnostics
is the separate local Python/controller compatibility unit, not those fixtures
again. Full impact is planned without executing unrelated suites. All broader
package/container/engine/live obligations remain deferred to the separate
stable-batch/deployment boundary; no Docker/cloud or dependency installation.

### N03 local completion and final proof

Final corrected verification completed by 10:07:43 UTC on 2026-11-04
(49 minutes 16 seconds from the recorded start; outcome-only closeout follows).
All 36 frozen task-file hashes matched after that run. Diagnostic adoption passed
with no findings; existing published code/version definitions remain unchanged.

| Final affected unit | Result | Seconds |
| --- | --- | ---: |
| core-runtime | passed | 20.34 |
| diagnostic-catalog-readers | passed | 26.33 |
| persistence-composition | passed | 87.37 |
| platform-config-runtime | passed | 18.01 |
| platform-persistence-runtime | passed | 21.64 |

The two other selected boundaries passed in the first batch: module-index-structure
(1.80s) and restore-connection-diagnostics (1.15s). They have unchanged relevant
structure/controller/catalogue inputs; they were not repeated just to refresh
broad fingerprints. The final five-unit runner took 173.68s in child commands,
19.27s in runtime identity, 5.65s in planning and 2.25s in fingerprinting. All
findings are empty. Reports and frozen identities are under
/tmp/N03-maintenance-eoSjqP/{final-corrected-focused.json,final-adoption.json,final-corrected-frozen.sha256};
prior failed reports remain alongside them, not replaced with successful claims.

README examples were checked against exact runtime results; all new local links
resolve. The README skill kept explanations and ownership walkthroughs in guides,
not a comment on every declaration. Scoped whitespace checks passed before this
outcomes-only closeout and are repeated afterward without rerunning runtime suites.

Efficiency lesson: the first narrow development set should have included the
existing diagnostic-record and foundation runtime files when changing Core's
canonical reasons/definitions/checker. Missing their expected lists delayed the
getter compatibility test and caused avoidable final retries. Use those existing
counterexamples together; no new suite or governance framework was needed. The
actual duplicate-registration correction and additional getter regression test
are retained. Scoped metadata preparation was repeated when stable inputs changed;
no unrelated suite was executed to compensate for an implementation mistake.

All N03 code, focused proof, documentation and harness changes are local. No SQL,
privileges, schema/table definitions, supported providers, credentials, original
outer task codes, exit dispositions or cleanup behavior were changed. New safe
instruction reports are additive. Container/real-engine/cloud/deployment/package
qualification and unrelated N01B/N02/N04/N05 work remain at their existing deferred
boundaries. No dependency installation, Docker, cloud, deployment, staging,
commit, push, work discard or upstream imported-tool change occurred.

## N02 execution — SQS configuration ownership, 2026-11-04

Authorised by the user's “let's go” following the explicit proposed implementation.
Started 13:24:08 UTC in this chat's recorded October 27 worktree. Baselines:
/tmp/N02-sqs-soWsR8/{before,catalogues-before}.tar. Existing dirty work is retained.

### Scope, ownership and consumers recorded before source edits

- New source-independent strict sender (address/region) and receiver (also wait/
  visibility) configuration under the SQS adapter's src/configuration/.
  contract/types.ts owns shapes and a trusted injected checker interface;
  contract/requirements.ts owns frozen Core-compatible rules and SQS bounds;
  contract/reporting/diagnostics.ts owns two content and two source-read reports,
  failure type and selected catalogue. Adjacent JSON is generated, publicly
  exported and included by the existing package files rule. domain/validation.ts
  checks logical sources with Core, domain/assembly.ts constructs checked option
  shapes without clients, and domain/reporting.ts preserves bounded records and
  optional observer isolation. index.ts is export-only; README explains each file.
  Reporting warrants its small cohesive file because both source and returned
  content failures use it; no empty group/index or generic framework.
- src/queue.ts and worker.ts add named FromConfiguration factories outside the
  index; all required values are checked before existing SDK constructors run.
  New factories receive logical ConfigSource, optional diagnostics and optional
  trusted checking function. Default checker is Core; Platform loader can be
  supplied by composition without adding upward adapter dependencies.
- Existing worker environment factory and direct constructors remain supported.
  They share declared numeric bounds through the public configuration index but
  keep legacy Number coercion, text quirks, read/predicate order, first-error,
  native throws and SDK construction order. No new legacy forwarding file.
  Existing retiring worker/relay callers are not migrated. The old environment
  API is retained for those named consumers; removal requires their retirement
  or separately approved migration. New code uses requirements plus checked loading.
- No Core or Platform implementation change is planned: existing strict Core
  checks, issue/record constructors and Platform loadPlatformConfiguration suffice.
  Core primitives and existing published report selections stay byte-equivalent.
  Adapter rules are not universally promoted to Core. Legacy errors stay intact;
  new aggregate errors have the existing adapter config code plus diagnosticRecord.
- Public root index/package JSON, runtime shim (Core subpaths only if used),
  compiler aliases, adapter boundary/type/runtime tests and local composition
  fixtures are connected consumers. No actual target/deployment mutation.
- Existing catalogue exporter/compiler/shims and smoke-test.py gain selected SQS
  local JSON generation, real package JSON resolution, exact four-definition
  membership, stale/missing/conflicting asset and Python literal-reader proof.
  Generic/narrow deployment reader allowlists do not gain SQS records implicitly;
  explicit validate_record(local SQS catalogue) is the intended Python path.
- Harness config standard records strict-new versus legacy-compatible paths and
  source/assembly/client ownership. Source-matched reviews retain existing debt.
  Plan/activity and this session README record measured results and corrections.

### Predicate/context inventory and compatibility

| Boundary | Observed alternatives / report | Actual consumer / proof |
| --- | --- | --- |
| New sender address/region | missing, wrong-type, blank, surrounding-whitespace | aws-sqs.sender-configuration-invalid v1; aggregate issues, exact record, no values; actual sender factory cannot construct SDK on rejection. |
| New receiver address/region | Same four reasons | aws-sqs.worker-configuration-invalid v1; exact sender/receiver attribution and required settings. |
| New receive wait / visibility | missing, wrong-type, blank, surrounding-whitespace, invalid-integer, out-of-range | Worker definition; 0–20 and 0–43200, no default; text is converted to checked numbers. Core syntax deliberately rejects legacy spellings on this new path only. |
| Source get throws | observed logical item only, unclassified read failure; do not infer absent/denied contents | Separate sender/worker source-read definitions; original identity and read stop preserved, no client; fixed phase/effect and source, source9 selection retained if supported. |
| Trusted checker / assembly | returned checked values and failures must be consumed, no raw reread | Injected-checker counterexample and actual SDK construction-options spy; Platform loading fixture with two physical binding sets, owned requirements and assembly. |
| Delivery | Own exact selected packet plus selected original source evidence, fixed client-initialization/selection context | Existing Core queue observer option type; small private reporter validates records, isolates sync/rejected/unusable observers; no raw cause in output. |
| Legacy APIs | Preserve all four reads, first returned error, text whitespace differences and Number spellings; getter throws/receiver/order | Existing sqs-adapter-runtime plus added pinned baseline cases. Legacy path does not acquire stricter checks or new response fields. |
| Effects / meaning | New invalid config proves no SDK construction, not a provider outage; accepted config proves neither queue existence nor access | Constructor/command spies and exact safe report assertions. No send/receive/retry, visibility, message envelope or cleanup redesign. |

Required context: sender versus worker and checking responsibility are bound by
code/version; logical field/reason or source/phase/effect is in the owned packet;
optional CoreQueueDiagnosticContext fixes client-initialization/selection. A
future target supplies its governed workload/stage reporter selection. Next
investigation is the named binding and declared requirement, not arbitrary value
logging, cloud mutation or replay. No new record claims AWS rejected anything.

### Sequence, gates and proof

1. Pin baseline and consumer/predicate inventory (this section).
2. Implement contracts, strict validation/assembly/reporting and public factories;
   preserve old APIs and use shared bounds without changing their evaluation.
3. Extend the existing adapter runtime suite and a cohesive config runtime/type
   file. Early tests include all existing getter/source/callback and envelope
   fixtures, not only new happy paths. Source-independent and constructor spies
   prove actual checked values, no bypass and sender/receiver requirements.
4. Complete local JSON/public asset/compiler/shim and explicit reader fixtures;
   preserve every baseline catalogue definition. No new selector/check framework.
5. README skill, harness guidance and reviewed hashes; consolidated self-review
   and narrow corrections before metadata preparation/freeze.
6. One stable final focused batch: sqs-queue-runtime, diagnostic-catalog-readers,
   module-index-structure. Add a named unit only if actual shared source changes
   require it. Full impact selection is recorded without executing unrelated
   suites; broader target/packaging/live obligations stay at the agreed later
   stable-batch boundary. No installs, Docker/cloud, deployment or Git mutations.

- [x] Scope and baselines recorded before source edits.
- [x] New strict configuration and actual guarded factories.
- [x] Legacy acceptance, errors, getters and operation behavior preserved.
- [x] Types, runtime/composition, delivery and source failures proved.
- [x] Catalogue generation/assets/explicit readers proved.
- [x] Documentation, harness and consolidated source review closed.
- [x] Preparation, frozen final focused verification and closeout.

| UTC / duration | Activity | Outcome |
| --- | --- | --- |
| 13:24–13:30 | Session/governance, affected API/shim/reader and compatibility inspection | Recorded worktree confirmed; source snapshots taken. Existing factory is legacy-only, new strict path additive; Core/Platform implementation unchanged. Reused existing Core exports and final units. |
| 13:30–13:37 | Connected implementation and focused proof | Added the cohesive configuration module and guarded factories. First compiler output exposed generic diagnostic-union inference and a deliberate test-mutant literal cast; corrected annotations without widening schemas. Runtime/type proof, old SQS tests, package boundaries, module structure and explicit Python reader passed. All 19 baseline catalogue files are byte-identical. |
| 13:37–13:44 | README, connected fixtures and consolidated self-review | Added sender command/checked-value and reporter failure/source9 counterexamples. Actual Platform composition, generated asset freshness/membership/private-subpath tests passed. The first temporary fixture adapter had an indentation error before tests; corrected its in-memory source-root adaptation. Source review caught a catalogue owner-prefix mismatch before final verification; corrected owner and added actual Platform registration/context/reporter proof, which passed (18.50s). No generic/narrow reader allowlist widened. |

### N02 consolidated review and freeze handoff

Self-review covers the 23 task paths, original tar snapshots, actual SDK option/
command spies and unchanged target consumers. The strict factory cannot ignore
failed checks or use original values without failing its construction/command
assertions; sender cannot require worker fields without failing its read trap.
All four source positions retain identity/stop/read order and report only the
observed logical item. Source9 remains delivered even if own delivery throws.
Legacy spellings, four reads/first error, getter behavior and original messages
remain pinned. A bounded mutated export proves the old numeric guards read the
shared constraint rather than independently copied endpoints. No raw cause,
address, physical source key or supplied value enters the new owned reports.

The optional checker and assembly callback accept trusted composition code;
they are not security boundaries allowing user-supplied callbacks to approve
their own input. Core mechanisms stay unchanged. Real Platform registration,
fixed workload context and diagnostic log preservation are proved in the
existing compiled package fixture; this does not migrate a production reporter.
The new module owner is aws-sqs so each declared code satisfies the real
Platform owner-prefix requirement. Existing catalogues and source/readers remain
retained. The existing errors.ts needs no edit: its historical typed facts and
outer errors are compatible and the new aggregate failure belongs with its
new report contract. No new dependency or runtime shim installation is needed.

All required corrections are closed before metadata preparation. Freeze and
run exactly sqs-queue-runtime, diagnostic-catalog-readers and
module-index-structure once. Final registered timings are authoritative;
exploratory compiler timings were not separately instrumented. Wider impact is
recorded without unrelated suite execution. Remaining target/engine/container/
cloud proof stays deferred; final local success must not imply it.

### N02 completion and final proof

Local verification completed by 13:51:12 UTC (27 minutes 4 seconds from the
recorded 13:24:08 start; outcome-only closeout follows). All three final
registered units passed on their first stable-batch invocation:

| Unit | Result | Seconds |
| --- | --- | ---: |
| diagnostic-catalog-readers | passed | 49.20 |
| module-index-structure | passed | 3.21 |
| sqs-queue-runtime | passed | 36.35 |

The final runner recorded 88.76s in child commands, 32.01s in runtime identity,
12.74s in planning, 3.92s in fingerprinting and 2.93s in receipt validation. The
nonexecuting preparation impact plan contained 117 rows and no findings; no
unrelated row was executed. All 23 task-file hashes matched after final proof.
Diagnostic adoption passed with no findings (118 adopted, 258 reviewed partial/
support, 190 retained legacy debt; not a repo-wide completeness claim).
All 19 baseline JSON catalogue files remain byte-identical; only the new
four-definition local SQS asset is added. No narrow/generic deployment reader
allowlist or Core/Platform implementation changed.

Reports: /tmp/N02-sqs-soWsR8/{preparation.log,final-focused.json,final-adoption.json,frozen-inputs.sha256}.
The activity journal records compile corrections, a temporary fixture-adaptation
indentation error before execution and the owner-prefix review correction.
All corrections and the real registration/reporter proof preceded final
verification; no final suite retry was required. The existing runtime/type/
getter/source tests were in the early proof set, improving on N03's late fixture
omissions. README links resolve and examples match the actual result shapes;
source/reader fixtures establish the documented behavior, not prose alone.

This is a supported new loading path plus explicit legacy compatibility, not
production adoption. Existing kanbien-platform target callers retain their
legacy APIs until retirement or separately approved migration. Neither SQS nor
another provider was added to core-server. No SDK request was made: constructor/
command spies and existing local fixtures supplied proof. No dependencies,
Docker, cloud, deployment, Git mutation, discarded work, message/retry/DLQ
policy, credentials or unrelated configuration work were introduced. Wider
packaging/target/CI/live obligations remain at the existing deferred boundary.
