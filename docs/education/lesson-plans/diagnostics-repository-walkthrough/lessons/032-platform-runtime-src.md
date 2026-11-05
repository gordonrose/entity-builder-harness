<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l032
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/runtime/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L032 — platform/runtime/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/runtime/src -->

## What you will understand

Runtime mounts apps into a registry, builds request/job contexts and coordinates startup and shutdown.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **7 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

The second app fails during mount after the first registered successfully. Report the actual boundary using available selected catalogs; do not pretend that no registration happened or rerun the first app for diagnostics.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Mounting and lifecycle already existed. A thrown app callback, invalid registration and shutdown failure could become one generic failure without retaining the stage reached.

**After:** Optional observers identify registry/state/context/lifecycle boundaries, retain selected catalogs and preserve source evidence. Existing app order and original errors remain the compatibility boundary.

**Why this was needed:** An agent needs to know whether failure occurred while declaring a route, constructing a context, starting work or shutting down. These imply different affected components.

This directory contains `documentation`, `implementation`, `definition`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/runtime/src/README.md -->

### README.md

[Open current source](../../../../../platform/runtime/src/README.md) · **Snapshot:** modified existing file; 18 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for application mounting and lifecycle; read the sections `Platform Runtime Source Map`, `Detailed guide to the files`, `errors.ts — a safe language for runtime failures`, `registry.ts — assembling one process’s app catalogue`, `contexts.ts — a consistent bundle of runtime facts`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Runtime Source Map`; `Detailed guide to the files`; `errors.ts — a safe language for runtime failures`; `registry.ts — assembling one process’s app catalogue`; `contexts.ts — a consistent bundle of runtime facts`; `lifecycle.ts — starting and stopping in a controlled order`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=9b526a323545c4c9dd65bd2ad243c6620240b1b259140d68d46549585ba2933f after=0433503b65c46d64a757bf8183da6c89549d827a2f5a8a435ba5181918c091fa -->

<!-- course-file: platform/runtime/src/contexts.ts -->

### contexts.ts

[Open current source](../../../../../platform/runtime/src/contexts.ts) · **Snapshot:** modified existing file; 35 added / 5 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports application mounting and lifecycle at this layer.

**Before:** Mounting and lifecycle already existed. A thrown app callback, invalid registration and shutdown failure could become one generic failure without retaining the stage reached. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformRuntimeContextDepsInput`, `createPlatformRuntimeContextDeps`, `contextDeps`, `createPlatformRuntimeRequestContext`, `createPlatformRuntimeJobContext` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Code-owned Runtime state and boundary records observe original construction, phase-local iteration/selection/invocation/completion/event/projection and request/job-context boundaries without supplied IDs or error text. Raw throws, legacy Results/state, reverse cleanup, native getter/receiver/order and first-failure behavior remain.

**Why:** An agent needs to know whether failure occurred while declaring a route, constructing a context, starting work or shutting down. These imply different affected components.

Changed declaration anchors: `PlatformRuntimeContextDepsInput`, `createPlatformRuntimeContextDeps`, `contextDeps`, `createPlatformRuntimeRequestContext`, `createPlatformRuntimeJobContext`.

New declarations within this existing file: `contextDeps`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-runtime-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=449d30964ec3f7c5564ce6bafa209cb4cf55295187d4748881b54b2a70641c93 after=fa23cc35fcf8b37400003ee558b553786e8c22f36b6e289a4434c3a0fc5142b4 -->

<!-- course-file: platform/runtime/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../platform/runtime/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 84 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `platform-runtime.state-rejected`, `platform-runtime.boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `PlatformRuntimeDiagnosticObserver`, `PlatformRuntimeDiagnosticOptions`, `platformRuntimeStateDiagnostic`, `platformRuntimeBoundaryDiagnostic`, `platformRuntimeDiagnosticCatalog`, `RuntimeBoundaryDetail`, `RuntimeStateDetail`, `RuntimeEvidence`, `intrinsicPromiseThen`, `contextFor`, `observe`, `selected` (2 more in source).

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/platform-contracts`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`, `platform-workers-runtime`, `shell-package-source`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=e4aad0d378828264c8b1486a7f94899a5e5a7e87c5bfdc92d7af7e6a64a55e6a -->

<!-- course-file: platform/runtime/src/errors.ts -->

### errors.ts

[Open current source](../../../../../platform/runtime/src/errors.ts) · **Snapshot:** modified existing file; 7 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports application mounting and lifecycle at this layer.

**Before:** Mounting and lifecycle already existed. A thrown app callback, invalid registration and shutdown failure could become one generic failure without retaining the stage reached. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformRuntimeError`, `platformRuntimeMountFailure`, `platformRuntimeFailure` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Code-owned Runtime state and boundary records observe original construction, phase-local iteration/selection/invocation/completion/event/projection and request/job-context boundaries without supplied IDs or error text. Raw throws, legacy Results/state, reverse cleanup, native getter/receiver/order and first-failure behavior remain.

**Why:** An agent needs to know whether failure occurred while declaring a route, constructing a context, starting work or shutting down. These imply different affected components.

Changed declaration anchors: `PlatformRuntimeError`, `platformRuntimeMountFailure`, `platformRuntimeFailure`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-runtime-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b1860ff2fd29fa550433b0ecec8ca977c3e8daab8bc1708e9abc33154bbb911f after=b59207cf8b1305c92a0d73f1b8d39dfe373107c853358971f470fc550d4813ad -->

<!-- course-file: platform/runtime/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/runtime/src/index.ts) · **Snapshot:** modified existing file; 6 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./diagnostics`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-runtime-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=4240f00d1db656996f57ca25992cd20fe40d4b7a0a89b981f642d9580a28ca31 after=864ae5fbde2059fceb1b8153dfa9f8c54a56933aa3d17425fcf689868fd2fa04 -->

<!-- course-file: platform/runtime/src/lifecycle.ts -->

### lifecycle.ts

[Open current source](../../../../../platform/runtime/src/lifecycle.ts) · **Snapshot:** modified existing file; 151 added / 146 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports application mounting and lifecycle at this layer.

**Before:** Mounting and lifecycle already existed. A thrown app callback, invalid registration and shutdown failure could become one generic failure without retaining the stage reached. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformRuntimeLifecycleEvent`, `PlatformRuntimeTelemetry`, `PlatformRuntimeLifecycleInput`, `Tracking`, `createPlatformRuntimeLifecycle` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Code-owned Runtime state and boundary records observe original construction, phase-local iteration/selection/invocation/completion/event/projection and request/job-context boundaries without supplied IDs or error text. Raw throws, legacy Results/state, reverse cleanup, native getter/receiver/order and first-failure behavior remain.

**Why:** An agent needs to know whether failure occurred while declaring a route, constructing a context, starting work or shutting down. These imply different affected components.

Changed declaration anchors: `PlatformRuntimeLifecycleEvent`, `PlatformRuntimeTelemetry`, `PlatformRuntimeLifecycleInput`, `Tracking`, `createPlatformRuntimeLifecycle`.

New declarations within this existing file: `Tracking`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-runtime-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=dbc41e516537ff3df7ff45856c03c2f561ce4780555d9549b86c0eacf45b359d after=a23dee92a56d61fae89a806a3ea3c3a7db8df03516ca76f0b9cdd792229d2c33 -->

<!-- course-file: platform/runtime/src/registry.ts -->

### registry.ts

[Open current source](../../../../../platform/runtime/src/registry.ts) · **Snapshot:** modified existing file; 108 added / 56 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports application mounting and lifecycle at this layer.

**Before:** Mounting and lifecycle already existed. A thrown app callback, invalid registration and shutdown failure could become one generic failure without retaining the stage reached. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformRuntimeRegistry`, `PlatformRuntimeMountInput`, `PlatformRuntimeMountResult`, `createPlatformRuntimeRegistry`, `mountPlatformRuntimeApps` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** An agent needs to know whether failure occurred while declaring a route, constructing a context, starting work or shutting down. These imply different affected components.

Changed declaration anchors: `PlatformRuntimeRegistry`, `PlatformRuntimeMountInput`, `PlatformRuntimeMountResult`, `createPlatformRuntimeRegistry`, `mountPlatformRuntimeApps`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=0f2efc78f465a7042e8b410073a45d64e678518fff53047ba23fead28be0afdf after=d4ac8c2b156b00e509740d3e2c0a4460bb90cd9a0268ee1741d8ef618fa7d372 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What state is known when mount fails after an earlier app has registered routes?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** A reported shutdown deadline is an observation, not proof that work was cancelled or cleanup completed. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/runtime/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L030 platform/runtime](030-platform-runtime.md) · [L031 platform/runtime/contracts](031-platform-runtime-contracts.md) · [L033 platform/runtime/tests](033-platform-runtime-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 7 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
