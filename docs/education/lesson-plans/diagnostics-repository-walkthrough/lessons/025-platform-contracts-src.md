<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l025
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/contracts/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L025 — platform/contracts/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/contracts/src -->

## What you will understand

Contracts define how apps declare routes, jobs, permissions, configuration, observability profiles and diagnostic catalogs without importing runtime implementations.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **15 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Register a route that references an undeclared observability profile. Observe the registration failure before listening. A structurally valid catalog with a conflicting definition must not silently replace the selected meaning.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail.

**After:** Catalog/reporter/context interfaces, registration observations and finite error-class declarations are explicit. Runtime and test consumers share those meanings, rather than inventing parallel declarations.

**Why this was needed:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

This directory contains `documentation`, `implementation`, `definition`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/contracts/src/README.md -->

### README.md

[Open current source](../../../../../platform/contracts/src/README.md) · **Snapshot:** modified existing file; 49 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for platform registration contracts; read the sections `Platform Contracts Source Map`, `Detailed guide to the files`, `errors.ts — a shared language for invalid declarations`, `identifiers.ts — checked names with a distinct TypeScript identity`, `flags.ts — a provider-neutral question about a feature`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Contracts Source Map`; `Detailed guide to the files`; `errors.ts — a shared language for invalid declarations`; `identifiers.ts — checked names with a distinct TypeScript identity`; `flags.ts — a provider-neutral question about a feature`; `contexts.ts — the safe bundle of runtime facts an app receives`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=a121ca021b296c97012ffddeeaf6a5755fe9b855b279ff53407a7e57e9e6a0d8 after=3cf76c650f334b53e6a71629120139a1ee69a3947ede224ec925dd2fa64e2b8f -->

<!-- course-file: platform/contracts/src/app.ts -->

### app.ts

[Open current source](../../../../../platform/contracts/src/app.ts) · **Snapshot:** modified existing file; 3 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports platform registration contracts at this layer.

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformAppRegistry`, `PlatformMountDeps` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

Changed declaration anchors: `PlatformAppRegistry`, `PlatformMountDeps`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b6e7f52f34a608a941d9e1e34e9a5fd1586bd610c573c4c78041bc1c2048eb5b after=4c8017ed88abb0944c4849c9b3779a127e0b0394418825d225e675be71770f3a -->

<!-- course-file: platform/contracts/src/contexts.ts -->

### contexts.ts

[Open current source](../../../../../platform/contracts/src/contexts.ts) · **Snapshot:** modified existing file; 6 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports platform registration contracts at this layer.

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformRequestContext` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): The optional request-only typed diagnostic callback keeps existing request, runtime and job contexts compatible. Server supplies delivery only under matched-route operational-log permission; this contract adds no provider dependency, sink, response field or framework-wide global observer.

**Why:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

Changed declaration anchors: `PlatformRequestContext`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-contracts-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=20118697c84c712209882d2dd68ed5d1bfef7b00cef8121acb7beb8fee1dec81 after=4ebc474f4c5ee64d480e289b2fa18e926a77e6e0b63b8bd53ad568f664d4a2f0 -->

<!-- course-file: platform/contracts/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../platform/contracts/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 60 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines the selected capability records and helpers. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `PlatformDiagnosticCatalog`, `PlatformDiagnosticContext`, `PlatformDiagnosticReporter`, `validatePlatformDiagnosticCatalog`, `invalid`.

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/core/shared`, `./registration-diagnostics`, `./errors`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=3886a190984c2ce2de79eb7a4fda10ab75b141e68cbf9e7c3a12c3461fc58435 -->

<!-- course-file: platform/contracts/src/errors.ts -->

### errors.ts

[Open current source](../../../../../platform/contracts/src/errors.ts) · **Snapshot:** modified existing file; 18 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports platform registration contracts at this layer.

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformRegistrationKind`, `PlatformContractErrorCode`, `PlatformContractError`, `duplicatePlatformRegistration`, `reservedPlatformPath`, `unknownPlatformPermission`, `unknownPlatformObservabilityProfile` (3 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

Changed declaration anchors: `PlatformRegistrationKind`, `PlatformContractErrorCode`, `PlatformContractError`, `duplicatePlatformRegistration`, `reservedPlatformPath`, `unknownPlatformPermission`, `unknownPlatformObservabilityProfile`, `platformRegistrationNamespaceMismatch`, `invalidContractName`, `platformContractError`.

Added import edges: `@kanbien/core/diagnostics`, `./registration-diagnostics`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=086a88aad718c5ef1c293d1b31836e59cc72ef9be357a57638a6631d9d823878 after=7d342e94136f46012de8a997bc6259a43b8a4006cd28503a3053616c37cf4eca -->

<!-- course-file: platform/contracts/src/flags.ts -->

### flags.ts

[Open current source](../../../../../platform/contracts/src/flags.ts) · **Snapshot:** modified existing file; 9 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports platform registration contracts at this layer.

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `fixedFeatureFlagReader` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Readiness-event rejection identifies the exact first observed logical predicate and actual traversal ordinal without supplied fields/values. Separate unknown boundary observations distinguish structure, enumeration, traversal selection/invocation, field/result projection and time parsing.

**Why:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

Changed declaration anchors: `fixedFeatureFlagReader`.

Added import edges: `./operational-observations`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `platform-shell-payload`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=4fa18629c4a7c77a0ff14d4de5eae72f8609cce001561fe82a85c3dd37a51ef8 after=fe7928c6871c532d09327298c1f72b72bfbe94e3da833137042438821b8e9d0e -->

<!-- course-file: platform/contracts/src/identifiers.ts -->

### identifiers.ts

[Open current source](../../../../../platform/contracts/src/identifiers.ts) · **Snapshot:** modified existing file; 4 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports platform registration contracts at this layer.

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `isPlatformContractName` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

Changed declaration anchors: `isPlatformContractName`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=8f3e2c7544428dc829e6346c507368f3b701eafaef25e3a6211ce2dd30031dff after=0d51614481842ac14e575b583ae7cf8cd374debad84c1594daee5912bf1ebe35 -->

<!-- course-file: platform/contracts/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/contracts/src/index.ts) · **Snapshot:** modified existing file; 12 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./diagnostics`, `./registration-diagnostics`, `./operational-observations`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./diagnostics`, `./registration-diagnostics`, `./operational-observations`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=71c1b6a16d6c4706e4774031bb5f71276a128b6c29ce1e1ccb57386401923cc5 after=1c220d4ca429bfab9abf44e98b3e1d4c3ee0bfe326d98b475227967ddbad198e -->

<!-- course-file: platform/contracts/src/observability-profiles.ts -->

### observability-profiles.ts

[Open current source](../../../../../platform/contracts/src/observability-profiles.ts) · **Snapshot:** modified existing file; 66 added / 56 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports platform registration contracts at this layer.

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformCapabilityObservabilityProfile`, `validatePlatformCapabilityObservabilityProfile`, `isPlatformObservabilityRequirement`, `platformProfileLogFields`, `platformProfileMetricLabels`, `platformProfileTraceFields`, `validateNfrObjectives` (4 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

Changed declaration anchors: `PlatformCapabilityObservabilityProfile`, `validatePlatformCapabilityObservabilityProfile`, `isPlatformObservabilityRequirement`, `platformProfileLogFields`, `platformProfileMetricLabels`, `platformProfileTraceFields`, `validateNfrObjectives`, `validateFieldNames`, `isNonEmptyUniqueArray`, `selectProfileFields`, `rejected`.

New declarations within this existing file: `rejected`.

Added import edges: `./registration-diagnostics`.

Declarations removed or relocated: `profileFailure`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b2980aff41740d7aefe71ba041ebcfee45f5e80dc93a8672e002b5daf720cd8b after=ff42d03ec65da3ef62c0020d3cc97967ab54458fe80221d2cedb94ec300c468f -->

<!-- course-file: platform/contracts/src/observability.ts -->

### observability.ts

[Open current source](../../../../../platform/contracts/src/observability.ts) · **Snapshot:** modified existing file; 72 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Defines allowed error-class declarations and classification.

**Before:** Existing observability contracts did not require this finite declared-class treatment.

**After:** Built-in classes and selected app/profile declarations form explicit allowed values; undeclared classifications fall back to unknown.

**Why:** App-owned extension remains possible, but arbitrary runtime strings do not automatically become safe shared labels.

Changed declaration anchors: `platformNativeErrorClasses`, `PlatformErrorClassificationOptions`, `PlatformErrorClassesIssue`, `PlatformErrorClassesSnapshot`, `inspectPlatformErrorClassDeclaration`, `platformErrorClassesIssue`, `readErrorClasses`, `platformErrorClassDeclarations`, `platformErrorClassification`, `platformOptionalErrorClassification`.

New declarations within this existing file: `platformNativeErrorClasses`, `PlatformErrorClassificationOptions`, `PlatformErrorClassesIssue`, `PlatformErrorClassesSnapshot`, `inspectPlatformErrorClassDeclaration`, `platformErrorClassesIssue`, `readErrorClasses`, `platformErrorClassDeclarations` (2 more in source).

Connected review context (`platform-contract-registration`; this review may span several files): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=7f458afc59f9390fdadfa9c23f79910f2ce5c6c04ca740d48043ef2d353179f4 after=0bf81646c6764b6c48cefb8780fdd02eddce6c2e274060b6bf0eb22d1ba33a98 -->

<!-- course-file: platform/contracts/src/operational-events.ts -->

### operational-events.ts

[Open current source](../../../../../platform/contracts/src/operational-events.ts) · **Snapshot:** modified existing file; 72 added / 27 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports platform registration contracts at this layer.

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformOperationalEventError`, `platformReadinessObservationEvent`, `EventIssue`, `ObserveIssue`, `isReadinessState`, `isReadinessDiagnosticCode`, `validIsoTime` (5 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Readiness-event rejection identifies the exact first observed logical predicate and actual traversal ordinal without supplied fields/values. Separate unknown boundary observations distinguish structure, enumeration, traversal selection/invocation, field/result projection and time parsing.

**Why:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

Changed declaration anchors: `PlatformOperationalEventError`, `platformReadinessObservationEvent`, `EventIssue`, `ObserveIssue`, `isReadinessState`, `isReadinessDiagnosticCode`, `validIsoTime`, `boundedName`, `isRecord`, `hasExactKeys`, `keyTraversalSelection`, `invalid`.

New declarations within this existing file: `EventIssue`, `ObserveIssue`, `keyTraversalSelection`.

Added import edges: `@kanbien/core/diagnostics`, `./registration-diagnostics`, `./operational-observations`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `platform-shell-payload`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=9d31e69d2350ab578471aa54c0fb3da707aec255a222ba91ec501741ddd2e228 after=8c067ad28cb03a80c1a2c07ac3dcac978529f51c8393f172d93694bfb71964e0 -->

<!-- course-file: platform/contracts/src/operational-observations.ts -->

### operational-observations.ts

[Open current source](../../../../../platform/contracts/src/operational-observations.ts) · **Snapshot:** added (absent from baseline); 61 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Readiness-event rejection identifies the exact first observed logical predicate and actual traversal ordinal without supplied fields/values. Separate unknown boundary observations distinguish structure, enumeration, traversal selection/invocation, field/result projection and time parsing. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `PlatformOperationalDiagnosticContext`, `PlatformOperationalDiagnosticOptions`, `nativeThen`, `isolate`, `observePlatformOperationalDiagnostic`, `PlatformOperationalObservation`.

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `./registration-diagnostics`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `platform-shell-payload`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=56e732966a106523cef67150bc26e37f74eb6f0a9af9cb82e6b432c02ae91715 -->

<!-- course-file: platform/contracts/src/registration-diagnostics.ts -->

### registration-diagnostics.ts

[Open current source](../../../../../platform/contracts/src/registration-diagnostics.ts) · **Snapshot:** added (absent from baseline); 87 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `platform-contracts.registration-rejected`, `platform-contracts.operational-event-rejected`, `platform-contracts.operational-boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `platformContractDiagnosticFields`, `platformContractDiagnosticConditions`, `PlatformContractDiagnosticField`, `PlatformContractDiagnosticCondition`, `PlatformContractObservation`, `PlatformContractObserver`, `platformContractRegistrationDiagnosticDefinition`, `platformContractClassificationDiagnosticDefinition`, `platformContractClassificationDiagnosticRecord`, `platformOperationalEventDiagnosticDefinition`, `platformOperationalBoundaryDiagnosticDefinition`, `PlatformOperationalEventDiagnosticDetail` (6 more in source).

Added import edges: `@kanbien/core/diagnostics`, `./errors`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `platform-shell-payload`, `persistence-composition`, `diagnostic-catalog-readers`, `platform-runtime-runtime`, `platform-testing-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `shell-package-source`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=2f10b6d7cbe252e446e33c59370ece9857ce2ac3cf3a96fd58b3abedb69e7005 -->

<!-- course-file: platform/contracts/src/routes.ts -->

### routes.ts

[Open current source](../../../../../platform/contracts/src/routes.ts) · **Snapshot:** modified existing file; 2 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports platform registration contracts at this layer.

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformResponseObservability` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

Changed declaration anchors: `PlatformResponseObservability`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6561429872ba49a9fc0d09dd697942e5900968436b5fe0f6dc8a55745d873864 after=bc3971d3de060b4b194e0f91f1d2b8c909263d038bd606aae34dda8dffa38fb6 -->

<!-- course-file: platform/contracts/src/validation.ts -->

### validation.ts

[Open current source](../../../../../platform/contracts/src/validation.ts) · **Snapshot:** modified existing file; 97 added / 69 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports platform registration contracts at this layer.

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `validatePlatformPermissionDeclaration`, `validatePlatformRouteRegistration`, `validatePlatformJobRegistration`, `isPermission`, `isRoutePath`, `rejected`, `isRouteAuthRequirement` (3 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

Changed declaration anchors: `validatePlatformPermissionDeclaration`, `validatePlatformRouteRegistration`, `validatePlatformJobRegistration`, `isPermission`, `isRoutePath`, `rejected`, `isRouteAuthRequirement`, `isPlatformResourceAuthorization`, `isValidator`, `isHandler`.

New declarations within this existing file: `rejected`.

Added import edges: `./registration-diagnostics`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=120b8e60829150ac4ab304995b725ac66a85321dee3f60a310f4b05f8a35cc51 after=7f7bee889d06126eaf4343d4f002e5fefa94c9a76086ebee0b9efc74c01ef0ac -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why should a Contracts interface not import the concrete HTTP server or AWS adapter?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Registration consistency checks cannot certify architectural judgment or all future failure modes on their own. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/contracts/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L023 platform/contracts](023-platform-contracts.md) · [L024 platform/contracts/contracts](024-platform-contracts-contracts.md) · [L026 platform/contracts/tests](026-platform-contracts-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 15 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
