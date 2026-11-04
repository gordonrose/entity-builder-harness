<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.standard.config-runtime-settings
version: 7
status: active
created_on: "2026-11-01"
updated_on: "2026-11-04"
layer: 03.product
domain: configuration
disciplines: [architecture, sre, agentic]
kind: standard
purpose: Govern typed configuration, startup checks, secret references, environment differences and ownership.
portability: {class: source-only, targets: []}
used_by:
- id: product.workflow.platform-runtime-implementation
  path: .agentic/03.product/workflows/platform-runtime-implementation.md
-->
# Configuration and runtime settings

## Worker retry and persistence leases

For new and changed worker/relay paths, Platform workers owns retry instructions
in `platform/workers/src/configuration`; Platform persistence owns the common
lease-duration requirement in `platform/persistence/src/leasing`. Targets select
values, not competing definitions. Reuse Core numeric/queue primitives where
their semantics match. Keep public indexes export-only and group contract and
domain files by validation/reporting responsibility.

Consume checked values: capture supplied retry/lease properties once and use
the accepted result, without later rereading mutable options. Do not invoke a
delay calculator speculatively at construction. Check each actual answer before
retry submission, preserving existing settlement order and raw calculator/source
throws. Only omitted values receive declared defaults; do not coerce text or
null to numeric instructions. Lease bounds, retry bounds and permitted delay
fractions are runtime-owned requirements, not rules invented by target wiring.

Tests must prove actual caller rejection before dependent work, use of accepted
values, defaults, callback timing, privacy, reporter-fault containment and
preserved surrounding behavior. Register new diagnostic definitions and public
local catalogues through existing generation/reader fixtures. Do not widen
historical definitions to accommodate new meanings. Record scheduling or live
coordination gaps separately: valid instructions do not prove those behaviors.

## Token verifier construction

New and refactored token-verifier construction uses Platform security's checked
`createJwksJwtVerifier` path and its `jwt-configuration` contracts. Provider
adapters translate their configuration into that interface; targets choose actual
identities and sources. Do not duplicate JWT requirements in Core or entrypoints.
Runtime source owns permitted values, defaults and diagnostic definitions.

Check verifier instructions before returning a usable verifier, not after the
first token arrives. Distinguish invalid instructions from an invalid token and
from a later clock/key-fetch failure. The built-in fetcher and a supplied trusted
fetcher need not share network source-format rules. Structural dependency checks
must not call those dependencies speculatively or claim future success. Preserve
supported caller return/error forms and approved source-throw semantics; translate
only recognised owned configuration failures, never arbitrary exceptions by text.
Actual caller tests must establish checked-value use, failure before dependent
work, safe diagnostic preservation and valid token behaviour. Schema validity,
imports and fresh review hashes alone do not establish those guarantees.

## Scope and authority

Cross-cutting rules for typed configuration access, startup validation, required keys, environment names, secret references, environment parity, feature flag access patterns, regional config, change audit, and ownership splits across core, apps, platform, and infra.

Applies to `apps/**`, `packages/core/**`, `platform/**`, `infra/**`.

This standard is the authoritative replacement for the legacy configuration
ruleset. Requirement identifiers and normative wording below are preserved.
Named APIs in the inherited wording are examples, not claims that those exact
exports exist today; runtime packages own their actual supported interfaces.
The responsibilities below govern new and changed work; the original location
migration alone did not establish runtime compliance.

## Requirements

### config-runtime-settings.maintenance-instruction-ownership

For new or changed migration, restore or other maintenance instructions:

- The module owning the task owns supported operations, defaults, conditional
  requirements, reference-proof formats and safe diagnostic definitions.
  Provider-neutral persistence maintenance belongs to Platform persistence,
  not an app or target entrypoint. Provider-specific requirements remain with
  the adapter; environment/source-name bindings remain with target composition.
- Use Core config's shared `choice` rule for finite allowed text choices.
  Add new shared reasons through `configReasonNames`; explicitly select reasons
  in each diagnostic definition rather than widening historical versions.
- Entrypoints compose the declared requirements and consume returned checked
  instructions. They must not re-declare accepted job words or proof patterns,
  or fall back to unchecked supplied values after successful validation.
- Separate supplied-content failures from source-read failures and declaration
  mistakes. Preserve established defaults, optional-input interpretation, reads,
  failure precedence, execution and cleanup unless a behavior change is approved.
- Tests must cover applicable field/reason pairs, conditional non-requirements,
  combined independent failures, exact value-safe records, actual caller rejection
  before work and actual consumption of checked values. Generated local/combined
  catalogue and selected-reader proof must include newly introduced identities.
- Register each owning catalogue once. A combined reader export may contain
  upstream definitions; do not register that aggregate beside its constituents.

Existing catalogue, module-structure and focused runtime checks enforce their
respective structural and behavior assertions. Review must still establish task
ownership and diagnostic truth; these rules do not claim automated discovery
of every future maintenance requirement.

### config-runtime-settings.config-is-typed-and-validated

Configuration is typed and validated at startup. Severity: error.

Missing configuration and configuration drift are common deployment failures. Runtime config should be typed, validated early, and accessed through stable contracts.

Must:

- Use typed configuration access such as ConfigProvider, EnvironmentName, requireConfig, getString, getOptionalString, getNumber, and getBoolean where reused.
- Validate required config keys at startup before serving requests or consuming jobs.
- Fail fast for missing or invalid required config.
- Retain each safely knowable logical setting and exact failure reason using code-owned diagnostic definitions; aggregate independent failures without retaining values, and keep source-key bindings in target composition.
- Keep config schemas or validation close to the runtime or app surface that owns the setting.

Must not:

- Do not scatter raw process.env access through app business logic.
- Do not let missing required config fail only on first production request.
- Do not hide environment-specific behavior in hardcoded conditionals instead of governed config.

Agent guidance: If a value changes by environment, ask where it is typed, validated, and failed fast.

### config-runtime-settings.secrets-are-references-not-code

Secrets are references, not code. Severity: error.

Config may reference secrets, but actual secrets should be fetched through controlled runtime mechanisms and provisioned infrastructure.

Must:

- Represent secret references or required secret keys without storing secret values in code.
- Fetch secrets through platform-owned secret manager integrations or approved runtime mechanisms.
- Account for secret rotation, access controls, redaction, and change audit where secrets are involved.

Must not:

- Do not check secrets into source code, config defaults, test fixtures, generated artifacts, or docs.
- Do not log secret values while validating config.
- Do not put cloud secret manager implementation code in packages/core.

Agent guidance: A config contract can name the need for a secret. The secret value belongs in controlled runtime and infrastructure paths.

### config-runtime-settings.feature-flags-are-governed-config

Feature flags are governed config. Severity: error.

Feature flags are runtime settings with product meaning, operational risk, fallback behavior, and lifecycle. They should not become unowned string checks scattered through the codebase.

Must:

- Use a stable feature flag reader or config-backed flag abstraction where flags are reused.
- Define flag owner, name, fallback behavior, expected lifetime, and cleanup path for non-permanent flags.
- Keep product behavior tied to app-owned flag meaning while platform owns provider integration and evaluation mechanics.
- Support regional or tenant-aware flag context only when the ownership model is explicit.

Must not:

- Do not scatter ungoverned string flag checks across unrelated modules.
- Do not let feature flags replace authorization, tenancy, or rollout governance.
- Do not build a complex flag platform before the product needs it.

Agent guidance: A flag is a temporary fork in behavior unless intentionally permanent. Ask who owns closing it.

### config-runtime-settings.environments-are-parity-checked

Environments are parity-checked. Severity: error.

Development, test, staging, and production settings should be explicit enough to avoid surprise drift while still allowing environment-specific differences.

Must:

- Use named environment concepts such as development, test, staging, and production where runtime behavior depends on environment.
- Document environment-specific differences such as auth issuer, log level, queue names, region, CORS origins, rate-limit store, and feature flag provider.
- Validate regional config and tenant-specific config where those values affect runtime behavior.
- Audit changes to sensitive or production-impacting config where appropriate.

Must not:

- Do not assume local defaults are safe in staging or production.
- Do not create hidden environment hacks with no validation or documentation.
- Do not mix config values with business rules that belong in apps.

Agent guidance: Environment drift is quiet until deploy time. Keep the differences named, validated, and reviewable.

### config-runtime-settings.layer-ownership-is-explicit

Configuration ownership is explicit. Severity: error.

Core defines provider-neutral config contracts. Platform loads values from environment variables, files, or secret managers. Apps own namespaced app config meaning. Infra provisions secrets and environment resources.

Must:

- Put ConfigProvider, EnvironmentName, requireConfig, config errors, and secret reference concepts in packages/core when reused and framework-independent.
- Put global config loading, startup validation runtime, config provider bindings, secret-manager integrations, feature flag provider integration, and regional config resolution in platform.
- Put feature-specific business constants, app config schemas, product flag meaning, and app-owned required keys in apps or product packages.
- Put actual secrets, secret manager resources, environment variables, parameter store paths, IAM, and deployment-time config resources in infra or deployment configuration.

Must not:

- Do not put actual secrets, cloud secret manager implementations, feature-specific business constants, or hardcoded environment hacks in packages/core.
- Do not put product-specific config meaning in platform shared runtime code.
- Do not put config validation only in docs with no executable startup check.

Agent guidance: Separate the config contract, config source, product meaning, and provisioned secret/resource.

## Configuration checking responsibilities

Apply when adding or changing configuration loading, checking or its consumers.
Account for affected inputs and callers in the existing task inventory, not a
second registry.

### Checking ownership and reuse

- Name the boundary receiving unchecked information and the operation needing
  its checked result. Reuse applicable Core helpers directly or through an
  existing named checked-loading function. No token Core import is required in
  that function's caller or code that receives checked configuration.
- Record the shared checker considered, its use or the exact reason for a local
  check. Compare types, spellings, whitespace, defaults, optional/conditional
  behaviour and first-error/collection policy. Equal numbers or reason names
  do not establish interchangeable checks. Apply shared constraint ownership.
- Keep certificate/TLS, provider and business validation with their owners.
  Generic config helpers do not replace specialised checks. Core uses actual
  owning relative imports, not imports back through its own public package.

### Used inputs and checked results

For every supplied input actually used, identify logical name, source owner,
rule, required/optional status, permitted default and conditions making it
required. Ignored extras need no invented validation result, but must not later
be used as checked information. A default is an explicit policy choice, not
permission to convert arbitrary invalid information into success.

On success use returned checked values, not the original source or an unchecked
fallback. Handle failure before the dependent connection/start/job operation
and preserve exact safe reports. An import, discarded call or type assertion
is not evidence of checking. Preserve issue order, collection/first-error
behaviour and thrown-source identity. A failed read establishes neither missing
content nor access denied. Do not invent continuation or teaching-only response
fields such as notChecked.

### Context and actual caller proof

Apply the [safe diagnostic context obligations](../../shared/standards/require-safe-diagnostic-record.md#context-and-consumer-obligations).
Identify who supplies the operation, logical item/source, failure step, condition,
known effect, uncertainty and permitted next investigation. Reuse existing
records, required typed/runtime construction or a governed code-owned lookup.
Core establishes reusable facts; Platform owns context/delivery; adapters
interpret provider evidence; entrypoints supply actual bindings. Bind fixed
operation/item/stage choices where appropriate; valid syntax alone is not
correct attribution. Do not add all context fields to every Core record.

Test actual callers, not only helpers: no checker call, ignored failure, original
unchecked values, omitted used requirements and unchecked extras must be caught
by their owning assertions. Cover direct/helper paths, optional/default and
conditional cases, specialised checks, single/multiple failures and source
throws where supported. Reject missing/wrong required context and prove actual
reporting preservation. Reporter failure must not change the workload result,
disclose supplied values or replay dependent work. Use bounded fixtures, not
a new universal validation framework.

### Narrow automatic access boundary and limitations

The existing module-structure check inspects TS/TSX under package, Platform, app
and product src trees, including future files. Recognised direct Node environment
access is prohibited there except Platform config loaders and the existing
server/worker process entrypoints. Infra/target entrypoints remain binding
owners. The [command guide](../../../scripts/repo/module-structure/README.md#configuration-source-access)
specifies syntax, paths and exclusions. New loader exceptions require an owning
policy/check change and positive/negative proof, not renaming a feature file.

This boundary does not prove every validation result is consumed. Arbitrary
aliases, dynamic property names, indirect data flow, other sources and unscanned
languages require source review and behaviour proof. Shell/Python/tooling use
their governed loaders/checks and explicit failure handling, not TypeScript
imports. Diagnostic adoption checks review freshness and proof references;
neither check proves universal completeness. Use focused affected-path proof;
broader integration checks stay at the governed stable batch boundary.

## Related requirements

These other documents remain at legacy locations; this task does not migrate
them or create a new rules document type. Follow their current owners where
applicable.

- [packages-core.yml](../../../docs/03.product/rules/core/layers/packages-core.yml)
- [platform.yml](../../../docs/03.product/rules/platform/layers/platform.yml)
- [identity-access-security.yml](../../../docs/03.product/rules/platform/concerns/identity-access-security.yml)
- [tenancy.yml](../../../docs/03.product/rules/platform/concerns/tenancy.yml)
- [dependency-direction.yml](../../../docs/06.shared/rules/concerns/dependency-direction.yml)

For shared configuration constraint ownership, use the
[public module structure standard](public-module-structure.md#reusable-configuration-constraint-ownership).
For diagnostic accuracy, privacy and proof, use the
[diagnostic review workflow](../../shared/workflows/verify-diagnostic-coverage.md).

## Historical provenance

The former document had metadata ID
`harness.architecture.rules.concerns.config-runtime-settings` and body ID
`concern.config-runtime-settings`. Its requirement IDs remain unchanged.

The retained source references below record the original derivation; this move
does not claim a fresh source-guide review.

- kanbien-core-architecture-guide.md: `config/ deep dive`, `Part 9: Building Kanbien v1`, `config`, `Enterprise Future`.

## Completion expectations

- The authoritative document exists at `.agentic/03.product/standards/config-runtime-settings.md` with kind `standard`.
- It requires typed config access and startup validation.
- It prevents scattered process.env access and late missing-config failures.
- It keeps secrets out of code and requires controlled secret references.
- It treats feature flags as governed runtime settings.
- It requires environment parity checks, regional config awareness, and change audit where relevant.
- It defines ownership splits across core contracts, platform runtime loading, app config meaning, and infra resources.
- It includes manually verified source_refs back to the core architecture guide.

The migration and its compatibility limits are recorded in the
[migration plan](../plans/migration/configuration-requirements-standard.md).
Document presence, metadata and selected checks are not evidence that every
runtime consumer already implements every requirement.

## Dependency requirements, implementation selection and composition

When introducing a checked-loading path beside supported legacy constructors
or environment factories, make the distinction explicit. New composition uses
the source-independent requirements and returned checked configuration, with
all required inputs checked before client construction. Existing entrypoints
do not acquire stricter parsing, changed getter/throw order or different errors
merely because a shared checker is available. Record the retained consumers and
retirement condition, share applicable constraints without copying their bounds,
and test both paths. Keep compatibility bindings isolated from new requirements;
do not create another forwarding file or make the legacy path the default for
new work. A stricter new API is not evidence its existing callers were migrated.

Prove sender/receiver or other operation-specific requirements independently;
unused settings must not become mandatory. Source exceptions must retain their
identity and identify only observed read facts, not invented missing-content or
access-denied causes. Accepted loading proves configuration checks, not provider
existence, credentials, network access or successful delivery.

For new dependencies and relevant refactoring, account for these distinct owners
in the existing task inventory:

- The consuming Platform or feature module declares required operations and
  their meaning, including consistency/atomicity guarantees and business policy.
- A service-specific implementation translates those operations into requests
  and stored representations. Its required database structures follow that
  implementation; a generic client must not own every feature's storage rules.
- The implementation declares source-independent configuration requirements and
  checked-configuration assembly. Reuse Core requirements/constraints where
  their meaning agrees; do not reconstruct these rules in a target.
- Platform config coordinates supplied readers, explicit bindings, Core checks
  and checked assembly. It does not choose a provider or construct clients.
- Target configuration selects an approved implementation for the capability/
  module and concrete sources/policy. Dedicated target composition connects
  that selection to code-owned requirements and constructors.
- Infrastructure creates compatible resources. Build processes compile/package
  implementation source and wiring; generated output is not its authoritative
  source. Runtime arguments are not necessarily available at build time.

Make selection timing explicit. Startup selection is fixed for the process;
changing it requires restart/redeployment. Build-time selection and live
switching are different designs, not implicit requirements of configuration.
Use finite supported identifiers and explicit code-owned imports. Reject an
unsupported explicit selection before reading its settings or constructing
clients; never load caller-supplied module paths or silently fall back after
failure. An explicitly permitted omitted-selection default must preserve the
governed existing behaviour, not mask invalid input.

Require only the selected implementation's inputs. Consumers must receive the
selected constructor's returned component and checked values. Prove selection,
default compatibility, rejection before effects, checked-result consumption,
safe diagnostic context and no fallback using actual caller fixtures.

An alternative is selectable only after proving the same operation contract
and guarantees, not because it has a similar name or configuration shape.
Retain shared behavioural contract tests for each supported alternative, plus
service-specific tests. Configuration selection neither migrates stored data
nor establishes parity. Distinguish unsupported selection, invalid selected
configuration, source-read failure and later operation failure in approved
diagnostics; never echo supplied selection strings or other private values.
