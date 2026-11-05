<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l039
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/server/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L039 — platform/server/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/server/src -->

## What you will understand

The server resolves configuration, starts a listener, admits transport requests, creates context, authenticates/authorizes, invokes handlers and writes responses.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **5 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Send a body that fails the existing decode boundary, then contrast a valid body whose handler throws. Keep the established public response, but give the internal agent distinct evidence for each observed stage.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The HTTP path already existed. Several fallback choices, rejected inputs and thrown transport/request boundaries were observable only as broad failures.

**After:** Closed records identify listener/port/health choices, transport predicates, decode/context/handler boundaries, writer/drain/close failures and process stages. Selected upstream evidence travels internally without entering response metadata.

**Why this was needed:** A fallback port is not a listener failure; a handler exception is not invalid JSON; a response-write failure does not prove that the handler never ran.

This directory contains `documentation`, `definition`, `barrel-or-implementation`, `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/server/src/README.md -->

### README.md

[Open current source](../../../../../platform/server/src/README.md) · **Snapshot:** modified existing file; 28 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for http transport and request handling; read the sections `Platform Server Source Map`, `index.ts — policy pipeline and route adaptation`, `transport.ts — converting hostile network input into a bounded request`, `main.ts — generic lifecycle host, not product composition`, `configuration/ and verification/ — process facts without target selection`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Server Source Map`; `index.ts — policy pipeline and route adaptation`; `transport.ts — converting hostile network input into a bounded request`; `main.ts — generic lifecycle host, not product composition`; `configuration/ and verification/ — process facts without target selection`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=2c322297a61ba4c020a5e40a014275fe0dbcc2731d452fabb4e0c95755c91091 after=739e6d415f3773d16a1d53ed3a6ea22ba834f4c08c25e0839eb4973e23642e35 -->

<!-- course-file: platform/server/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../platform/server/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 265 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `platform-server.operation-failed`, `platform-server.listener-configuration-selected`, `platform-server.port-configuration-fallback`, `platform-server.health-exposure-selected`, `platform-server.health-exposure-fallback`, `platform-server.transport-configuration-invalid`, `platform-server.transport-configuration-inconsistent`, `platform-server.transport-request-rejected`, `platform-server.transport-boundary-failed`, `platform-server.transport-state-observed`, `platform-server.client-address-trust-invalid`, `platform-server.client-address-fallback-selected`, `platform-server.configuration-omitted`, `platform-server.process-boundary-failed`, `platform-server.request-predicate-rejected`, `platform-server.request-boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `serverDiagnosticErrorCodes`, `serverObservedPhases`, `platformServerDiagnostic`, `selectionClassification`, `fallbackClassification`, `configurationPhase`, `selectedEffect`, `serverListenerConfigurationDiagnostic`, `serverPortFallbackReasons`, `serverPortConfigurationFallbackDiagnostic`, `healthSelectionProperties`, `serverHealthExposureSelectionDiagnostic` (34 more in source).

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`, `shell-package-source`, `platform-shell-payload`, `core-dependency-boundary`, `persistence-composition`, `ecs-fargate-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=53174bc250c7fcc7c4c497d3785a8ababd24e23f18d1fe7fa17dca7eb83e4786 -->

<!-- course-file: platform/server/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/server/src/index.ts) · **Snapshot:** modified existing file; 460 added / 77 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports http transport and request handling at this layer.

**Before:** The HTTP path already existed. Several fallback choices, rejected inputs and thrown transport/request boundaries were observable only as broad failures. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformServerError`, `PlatformServerOptions`, `PlatformServerRequestHandlingInput`, `serverBuiltinDiagnosticCatalogs`, `createPlatformServerShell`, `handlePlatformServerRequest`, `admitPlatformServerTransportRequest` (22 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** A fallback port is not a listener failure; a handler exception is not invalid JSON; a response-write failure does not prove that the handler never ran.

Changed declaration anchors: `PlatformServerError`, `PlatformServerOptions`, `PlatformServerRequestHandlingInput`, `serverBuiltinDiagnosticCatalogs`, `createPlatformServerShell`, `handlePlatformServerRequest`, `admitPlatformServerTransportRequest`, `handlePlatformServerTransportFailure`, `serverProfileForRoute`, `recordServerProfileObservation`, `endServerProfileTrace`, `serverNomenclature` (17 more in source).

New declarations within this existing file: `serverBuiltinDiagnosticCatalogs`, `diagnosticsFor`, `serverObservationDiagnostics`, `reportServerObservationFailure`, `serverObservationProjection`, `serverObservationElapsed`, `selectedServerEvidence`, `ServerDiagnosticRequest` (4 more in source).

Added import edges: `@kanbien/core`, `./diagnostics`, `@kanbien/core/diagnostics`, `@kanbien/core/validation`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=01851429fc6764ff5d543dbd9ecc6abf726a451442f1dbd305156a3518f0f026 after=3e97d703e3ba13039a063c71322b903a06c549f965279754e816592a3c6f12b7 -->

<!-- course-file: platform/server/src/main.ts -->

### main.ts

[Open current source](../../../../../platform/server/src/main.ts) · **Snapshot:** modified existing file; 56 added / 12 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports http transport and request handling at this layer.

**Before:** The HTTP path already existed. Several fallback choices, rejected inputs and thrown transport/request boundaries were observable only as broad failures. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformServerProcessOptions`, `startPlatformServerProcess`, `installShutdownHandlers` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** A fallback port is not a listener failure; a handler exception is not invalid JSON; a response-write failure does not prove that the handler never ran.

Changed declaration anchors: `PlatformServerProcessOptions`, `startPlatformServerProcess`, `installShutdownHandlers`.

Added import edges: `@kanbien/core`, `@kanbien/platform-runtime`, `@kanbien/core/diagnostics`, `@kanbien/platform-observability`, `./diagnostics`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=31ab47c49aafb1fe8ee87251009b36d770086174427e32e04e8a738e3f52ac4d after=0f0dac955368889c04442b24a71c3a51823cdda71686d7069dfd8dca3ac11053 -->

<!-- course-file: platform/server/src/transport.ts -->

### transport.ts

[Open current source](../../../../../platform/server/src/transport.ts) · **Snapshot:** modified existing file; 168 added / 51 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements Node HTTP admission, request metadata/body reading, response writing and close.

**Before:** These transport operations existed with coarser rejected/failure observations.

**After:** Adds observed configuration/request/boundary records and preserves supported client-address choices, request order and original failure behavior.

**Why:** Decode, trust selection, listener, writer and cleanup failures need distinct next checks; they must not trigger handler replay.

Changed declaration anchors: `PlatformClientAddressResolverInput`, `PlatformServerTransportFailure`, `PlatformServerTransportDiagnosticRequest`, `resolvePlatformServerTransportOptions`, `listenNodePlatformServer`, `requestMetadata`, `resolvedClientAddress`, `readNodeRequestBody`, `transportFailure`, `writeNodeResponse`, `closeServer`.

New declarations within this existing file: `PlatformServerTransportDiagnosticRequest`.

Added import edges: `@kanbien/core/diagnostics`, `./diagnostics`.

Declarations removed or relocated: `isJsonContentType`. Read the current exports/consumer tests before assuming the public API was removed.

Connected review context (`platform-server-diagnostics`; this review may span several files): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=7a143e8f9b20f6cedb19d6873a6ecbee1c7cb4480475b91c2427b6ec9bf00eb9 after=7956c666bb7d4f021f0e97288ac31ba511f060cc0ef58b2ee7f8cabd50558078 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: If response writing fails after a handler committed a change, why must diagnostic handling not replay the handler?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new HTTP routes, authentication policy or public error-detail expansion is implied. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/server/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L037 platform/server](037-platform-server.md) · [L038 platform/server/contracts](038-platform-server-contracts.md) · [L040 platform/server/src/configuration](040-server-src-configuration.md) · [L041 platform/server/src/verification](041-server-src-verification.md) · [L042 platform/server/tests](042-platform-server-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 5 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
