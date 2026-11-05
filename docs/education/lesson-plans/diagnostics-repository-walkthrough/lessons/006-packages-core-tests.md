<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l006
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L006 — packages/core/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/tests -->

## What you will understand

Core defines provider-independent facts and their allowed shapes. It must remain usable without a server, AWS account or particular database.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **31 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a raw exception with an object carrying code, definitionVersion, schema and detail. Add an undeclared detail property: parsing must reject that record. A valid shape still does not prove that the claimed event happened; the producer must have observed it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The baseline already had diagnostic classifications and monitoring concepts. Those useful abstractions did not, by themselves, give every capability a closed, versioned record that a reader could validate.

**After:** Definitions declare a stable code, version, classification and permitted detail. Constructors copy and validate records; selectors accept only explicitly selected evidence. Shared helpers bound related evidence to eight records.

**Why this was needed:** A description written by an agent is not a runtime contract. Code-owned definitions let producers and readers agree without interpreting prose or trusting an arbitrary error object.

This directory contains `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/tests/audit-runtime.test.ts -->

### audit-runtime.test.ts

[Open current source](../../../../../packages/core/tests/audit-runtime.test.ts) · **Snapshot:** modified existing file; 125 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for audit records and projection.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Existing Audit type/version/target predicates retain exact first-failure alternatives and original repeated reads. Closed raw records identify actor/target/metadata projection, eager entries-before-nested-copy, record append uncertainty and snapshot callback ordinals.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `diagnosticCoverage`.

New declarations within this existing file: `diagnosticCoverage`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=829f0d536bec0553955e1e25af5f3b0d4c479737671b80928280fb3b7d62181c after=db1dc7c1efe5bb5c2b712b1dd49aa65f51381333427f72a527d735c148600ea3 -->

<!-- course-file: packages/core/tests/audit-types.test.ts -->

### audit-types.test.ts

[Open current source](../../../../../packages/core/tests/audit-types.test.ts) · **Snapshot:** modified existing file; 13 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for audit records and projection.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Existing Audit type/version/target predicates retain exact first-failure alternatives and original repeated reads. Closed raw records identify actor/target/metadata projection, eager entries-before-nested-copy, record append uncertainty and snapshot callback ordinals.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `diagnosticOptions`.

New declarations within this existing file: `diagnosticOptions`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=4274801d6291ad25202274f0668896a686a9a79990a8f86ec50bb35886bdc987 after=7e2bd52bad71a1c83344b339cd7c1d6fe0bd2cdf7080193bdc906414d249069a -->

<!-- course-file: packages/core/tests/authn-runtime.test.ts -->

### authn-runtime.test.ts

[Open current source](../../../../../packages/core/tests/authn-runtime.test.ts) · **Snapshot:** modified existing file; 96 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for identity and tenant construction.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns additive principal and tenant-constructor boundary definitions. Optional observers independently deliver the exact observed projection/copy location and selected source primary plus up to eight related records, preserving raw primitive/frozen throw identity, eager claims enumeration, repeated getters, scope iteration and nullish tenant fallback.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `sameThrow`, `main`.

New declarations within this existing file: `sameThrow`.

Added import edges: `../src/diagnostics/index`.

Owning registered proof: `core-runtime`, `platform-security-runtime`, `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6c99e72a8ecd8b2f9e6bd8e7cbfee293fac97c26be3dc06834571ded23aa81c4 after=174ae8d2ff58b32f16dd350705e72ab59f668c393c6059516d477b5475e8ab7d -->

<!-- course-file: packages/core/tests/authn-types.test.ts -->

### authn-types.test.ts

[Open current source](../../../../../packages/core/tests/authn-types.test.ts) · **Snapshot:** modified existing file; 4 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for identity and tenant construction.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns additive principal and tenant-constructor boundary definitions. Optional observers independently deliver the exact observed projection/copy location and selected source primary plus up to eight related records, preserving raw primitive/frozen throw identity, eager claims enumeration, repeated getters, scope iteration and nullish tenant fallback.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `diagnostics`.

New declarations within this existing file: `diagnostics`.

Owning registered proof: `core-runtime`, `platform-security-runtime`, `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6f73c9253083e1de573f037cb8af3b48ef1bbd0447a52a6e2d612e7f4b847352 after=5d0a57348fb381ba2f49c9fcc22d274c7b4b05d179ea43d19a063318ecaf4dcb -->

<!-- course-file: packages/core/tests/config-runtime.test.ts -->

### config-runtime.test.ts

[Open current source](../../../../../packages/core/tests/config-runtime.test.ts) · **Snapshot:** modified existing file; 57 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for configuration: tell absence from invalidity.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. Indexed issue collection copies and freezes logical references/positions, retains deterministic order and explicitly reports overflow at 32 issues.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `settings`, `relationships`, `equalValues`, `invalidDeclarations`, `maximumSettings`, `maximumRelationships`, `maximumResult`, `integerSettings`, `bounded`, `mutableIssue`, `firstSnapshot`, `issueGetterReads`.

New declarations within this existing file: `settings`, `relationships`, `equalValues`, `invalidDeclarations`, `maximumSettings`, `maximumRelationships`, `maximumResult`, `integerSettings` (4 more in source).

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=5cf6a556da834e314f442f593d54acf8d7a344112496dff8e21192ae0254fae6 after=fbb162e20f81230c2a7270cd9dc3a5a753bc6b64ccddb9cb284568b6faaa1f4d -->

<!-- course-file: packages/core/tests/config-types.test.ts -->

### config-types.test.ts

[Open current source](../../../../../packages/core/tests/config-types.test.ts) · **Snapshot:** modified existing file; 29 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for configuration: tell absence from invalidity.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. Indexed issue collection copies and freezes logical references/positions, retains deterministic order and explicitly reports overflow at 32 issues.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `relationSettings`, `relation`, `relationshipResult`, `legacyResult`, `issueCollector`.

New declarations within this existing file: `relationSettings`, `relation`, `relationshipResult`, `legacyResult`, `issueCollector`.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c9b685ef236c3f46c24d7f5e91a1150c68c7694efcb43027caebbc73fe8bac3f after=e03fab581c838c777a8bd2f53dba6aef8436e8580b4de8fbafe7944c213fb83a -->

<!-- course-file: packages/core/tests/diagnostic-record-runtime.test.ts -->

### diagnostic-record-runtime.test.ts

[Open current source](../../../../../packages/core/tests/diagnostic-record-runtime.test.ts) · **Snapshot:** added (absent from baseline); 179 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for the diagnostic language.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. Indexed issue collection copies and freezes logical references/positions, retains deterministic order and explicitly reports overflow at 32 issues.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `CompanionFactory`, `companionFactories`, `definition`, `result`, `emptyRelated`, `accessed`, `enumValues`, `settings`, `selectedLiteral`, `anotherVersion`, `versionTwo`, `unselected` (25 more in source).

Added import edges: `node:assert/strict`, `../src/diagnostics/index`, `../src/config/index`, `../src/persistence/index`, `../src/audit/index`, `../src/files/index`, `../src/i18n/index`, `../src/localization/index`, `../src/events/index`, `../src/queues/index` (more in source).

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=0b59205fd3e72d3ba9ee8c066954858fd5a75b25087091dd1d7f894a2f65dfc3 -->

<!-- course-file: packages/core/tests/diagnostic-record-types.test.ts -->

### diagnostic-record-types.test.ts

[Open current source](../../../../../packages/core/tests/diagnostic-record-types.test.ts) · **Snapshot:** added (absent from baseline); 43 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for the diagnostic language.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. Indexed issue collection copies and freezes logical references/positions, retains deterministic order and explicitly reports overflow at 32 issues.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `definition`, `evidence`, `primary`, `companions`, `unsafeDetail`, `legacyErrorInput`, `CompanionFactory`, `companionFactories`.

Added import edges: `../src/diagnostics`, `../src/index`.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=28d03fa4e417d21d3a336f19b4cdf8803bf51b15b6f6592b615f5994f383ca84 -->

<!-- course-file: packages/core/tests/events-runtime.test.ts -->

### events-runtime.test.ts

[Open current source](../../../../../packages/core/tests/events-runtime.test.ts) · **Snapshot:** modified existing file; 159 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for events, handlers and publication.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Existing Event type/version predicates retain exact regex/integer/positive alternatives. Closed records distinguish declaration, batch/argument projection, actual event/handler traversal, getter selection, invocation, completion, published append and snapshots.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `diagnosticCoverage`.

New declarations within this existing file: `diagnosticCoverage`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=8092a2d8b91094ec46d784be07d65bf8f380826c46484a8504ded28fc0b01fd7 after=4e7f023044d4cb775b96fbccb7c621757cad1dd2fa9dd4221d97faa3e6da2781 -->

<!-- course-file: packages/core/tests/events-types.test.ts -->

### events-types.test.ts

[Open current source](../../../../../packages/core/tests/events-types.test.ts) · **Snapshot:** modified existing file; 11 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for events, handlers and publication.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Existing Event type/version predicates retain exact regex/integer/positive alternatives. Closed records distinguish declaration, batch/argument projection, actual event/handler traversal, getter selection, invocation, completion, published append and snapshots.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `diagnosticOptions`.

New declarations within this existing file: `diagnosticOptions`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ba17957aefdab3a26c20fbd057bf78f5619043637d4432c6e5087bac726c805b after=fbf26acf6fa8b0df2f2eff3569422db95bccf045514fd045e09a4d5814bcd135 -->

<!-- course-file: packages/core/tests/files-runtime.test.ts -->

### files-runtime.test.ts

[Open current source](../../../../../packages/core/tests/files-runtime.test.ts) · **Snapshot:** modified existing file; 480 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for file capabilities.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Existing Files predicates retain exact order, coercion, closed scan/access membership, checksum forwarding and first rejected storage-segment visit ordinal. Custom aggregate truthiness without a rejecting callback has predicate-rejected with no fabricated position.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `literalFileRecord`, `fileDiagnosticsProof`.

New declarations within this existing file: `literalFileRecord`, `fileDiagnosticsProof`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=795670270a758f7d5b8e3a748df4c148fd0893f855006d2eb0e751d152123a1b after=2711529e5ed90505df0ccc0413d2631129af65593e071783807ed6f633e1b375 -->

<!-- course-file: packages/core/tests/files-types.test.ts -->

### files-types.test.ts

[Open current source](../../../../../packages/core/tests/files-types.test.ts) · **Snapshot:** modified existing file; 50 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for file capabilities.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Existing Files predicates retain exact order, coercion, closed scan/access membership, checksum forwarding and first rejected storage-segment visit ordinal. Custom aggregate truthiness without a rejecting callback has predicate-rejected with no fabricated position.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `fileDiagnosticOptions`, `fileDiagnosticEvidence`.

New declarations within this existing file: `fileDiagnosticOptions`, `fileDiagnosticEvidence`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=01383bc3b6a2c31b8b8a4e031c09f512c42d1b546c3f8deac4a90676cc0281ee after=5d8fafa62a8d7cddd9d70b7dc05307f0e1d3831427e9109bda3f1931d7ecef42 -->

<!-- course-file: packages/core/tests/foundation-diagnostics-runtime.test.ts -->

### foundation-diagnostics-runtime.test.ts

[Open current source](../../../../../packages/core/tests/foundation-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 363 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for the diagnostic language.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns closed queue validation, unknown boundary and informational receive-reduction definitions, with finite optional native reported-condition detail. Runtime factories and independent receiver-preserving own/selected source primary plus eight related records observation remain physically reviewed under core-error-preservation rather than duplicating source ownership.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `record`, `observed`, `thrownRecord`, `configRecord`, `primitive`, `readers`, `preserved`, `related`, `supplied`, `readInvocations`, `upstream`, `text` (43 more in source).

Added import edges: `node:assert/strict`, `../src/index`, `../src/config/index`, `../src/shared/index`, `../src/security/index`, `../src/authz/index`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=23b71bb75ee779cb3a1e06e2afcf087dd4771aeeaff2cea6f54454bc7dfa153e -->

<!-- course-file: packages/core/tests/foundation-diagnostics-types.test.ts -->

### foundation-diagnostics-types.test.ts

[Open current source](../../../../../packages/core/tests/foundation-diagnostics-types.test.ts) · **Snapshot:** added (absent from baseline); 33 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for the diagnostic language.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. Indexed issue collection copies and freezes logical references/positions, retains deterministic order and explicitly reports overflow at 32 issues.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `primitive`, `historical`, `enriched`, `evidence`, `related`, `catalog`, `capabilityDefinitions`.

Added import edges: `../src/index`, `../src/config/index`, `../src/shared/index`, `../src/security/index`, `../src/authz/index`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=f954c00858ddb467267e7aa16dd516801d4c40e2e947cea0d4b979511b99472f -->

<!-- course-file: packages/core/tests/i18n-runtime.test.ts -->

### i18n-runtime.test.ts

[Open current source](../../../../../packages/core/tests/i18n-runtime.test.ts) · **Snapshot:** modified existing file; 308 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for internationalization and localization.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed existing locale/template/catalog/unsafe-or-missing-parameter predicates retain syntax-only acceptance, eager entries before validation, original final missing sentinel and last missing callback ordinal. Selection records distinguish requested/fallback/default source, actual candidate ordinal and captured miss counts before rendering, never successful translation.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `englishLocale`, `frenchLocale`, `validation`, `boundary`, `caught`, `records`, `contexts`, `observations`, `clear`, `lastMissing`, `observedAccessor`, `eagerError` (67 more in source).

New declarations within this existing file: `englishLocale`, `frenchLocale`, `validation`, `boundary`, `caught`, `records`, `contexts`, `observations` (71 more in source).

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c33bd0267f15d34583940e509634ab76c10c5e8dc7f7396e82b25e625b98bfab after=ddcb3da4669fd9507d7d0e64b24e8491c2d77d2f162853dcd5a1684a58465f7c -->

<!-- course-file: packages/core/tests/i18n-types.test.ts -->

### i18n-types.test.ts

[Open current source](../../../../../packages/core/tests/i18n-types.test.ts) · **Snapshot:** modified existing file; 45 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for internationalization and localization.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed existing locale/template/catalog/unsafe-or-missing-parameter predicates retain syntax-only acceptance, eager entries before validation, original final missing sentinel and last missing callback ordinal. Selection records distinguish requested/fallback/default source, actual candidate ordinal and captured miss counts before rendering, never successful translation.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `observedContexts`, `diagnosticOptions`, `observedTranslator`, `oldTranslatorImplementation`, `validationDetail`, `selectionDetail`, `boundaryDetail`.

New declarations within this existing file: `observedContexts`, `diagnosticOptions`, `observedTranslator`, `oldTranslatorImplementation`, `validationDetail`, `selectionDetail`, `boundaryDetail`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f4add4391af72396fac43db505e8ea392ad063d56d5638516b3da29767e3d73c after=777d16b25f873b58aa1d5ed407ee22bf32c40905d31ad8a7069214149daa7860 -->

<!-- course-file: packages/core/tests/localization-runtime.test.ts -->

### localization-runtime.test.ts

[Open current source](../../../../../packages/core/tests/localization-runtime.test.ts) · **Snapshot:** modified existing file; 360 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for internationalization and localization.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed existing currency/region/time-zone/number/fraction predicates retain syntax-only grammar, native calls/coercion, repeated getters, both fraction argument reads before predicates, earlier formatting throws and later nonfinite return precedence. Predicate evidence does not claim the returned error; the parent-sequence branch is proved with a coercible custom value rather than invented IANA validation.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `localeValue`, `currencyValue`, `dateValue`, `localizationRecord`, `localizationDiagnosticProof`.

New declarations within this existing file: `localeValue`, `currencyValue`, `dateValue`, `localizationRecord`, `localizationDiagnosticProof`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ec05d5fdb4a8f3a721371f9ca961f53560c0a10bfbcf48f28714772db0a7a738 after=1108f97ed83e60886f0b48e33f2c886afce4d86e2497e7ffc01b73f5c60eb46f -->

<!-- course-file: packages/core/tests/localization-types.test.ts -->

### localization-types.test.ts

[Open current source](../../../../../packages/core/tests/localization-types.test.ts) · **Snapshot:** modified existing file; 53 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for internationalization and localization.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed existing currency/region/time-zone/number/fraction predicates retain syntax-only grammar, native calls/coercion, repeated getters, both fraction argument reads before predicates, earlier formatting throws and later nonfinite return precedence. Predicate evidence does not claim the returned error; the parent-sequence branch is proved with a coercible custom value rather than invented IANA validation.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `localizationDiagnostics`, `boundLocalizer`, `legacyLocalizer`.

New declarations within this existing file: `localizationDiagnostics`, `boundLocalizer`, `legacyLocalizer`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b75bcd1bf4983ad93361eaa121e7bc6e9a33077ce68dadc3749ebef95b4edd72 after=2c7bd20e07886ac2e8bb678aa093b09f07d24309f53592dc966207eabbb2cd25 -->

<!-- course-file: packages/core/tests/logging-runtime.test.ts -->

### logging-runtime.test.ts

[Open current source](../../../../../packages/core/tests/logging-runtime.test.ts) · **Snapshot:** modified existing file; 103 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for monitoring primitives and logging.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `loggingDiagnostics`.

New declarations within this existing file: `loggingDiagnostics`.

Added import edges: `../src/monitoring/index`, `../src/diagnostics/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=71df9ec476d6ebde02f245578d9b9ec86febccdd4438d04698f698496e39edc4 after=5d235dbe6a46b0d35f68ec0d7a0b7b8ca62209dbfd78c2c1640b83efc6ce8008 -->

<!-- course-file: packages/core/tests/logging-types.test.ts -->

### logging-types.test.ts

[Open current source](../../../../../packages/core/tests/logging-types.test.ts) · **Snapshot:** modified existing file; 12 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for monitoring primitives and logging.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `diagnostics`, `unchangedVoid`, `invalidLocation`.

New declarations within this existing file: `diagnostics`, `unchangedVoid`, `invalidLocation`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=183753d5e4da613f1bdf8a698b7a513fe17760a7112abc7fab3b4af4d2b5192d after=26de5f3c6a091b54dd1193e3b59c1a1fa633ad73288f6fe5ef78e26b5562ca26 -->

<!-- course-file: packages/core/tests/monitoring-metric-diagnostics-runtime.test.ts -->

### monitoring-metric-diagnostics-runtime.test.ts

[Open current source](../../../../../packages/core/tests/monitoring-metric-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 39 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for monitoring primitives and logging.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Existing metric name/unit/label predicates supply closed value-free observations through an optional current-invocation callback. Accepted values, TypeError class/messages, first-failure order and public module imports are retained; callback failure cannot replace validation and a prior error rethrown from input cannot establish current guard evidence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `cases`, `observations`, `observe`, `previous`, `hostile`.

Added import edges: `node:assert/strict`, `../src/monitoring/index`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=3ef495deceac5f140a82e941295dd920be47990d3871d5105e77dcba9b7fab87 -->

<!-- course-file: packages/core/tests/monitoring-runtime.test.ts -->

### monitoring-runtime.test.ts

[Open current source](../../../../../packages/core/tests/monitoring-runtime.test.ts) · **Snapshot:** modified existing file; 202 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for monitoring primitives and logging.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `monitoringDiagnostics`.

New declarations within this existing file: `monitoringDiagnostics`.

Added import edges: `../src/diagnostics/index`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=17f19935a46138fa59046acc238b81060b0635187a5c2f17ab0dea296f43df88 after=c000a471de6b470bbbe912bcc0a42bbdc3866595d327801bfd7a4cc08e798e9a -->

<!-- course-file: packages/core/tests/monitoring-types.test.ts -->

### monitoring-types.test.ts

[Open current source](../../../../../packages/core/tests/monitoring-types.test.ts) · **Snapshot:** modified existing file; 21 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for monitoring primitives and logging.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `observeMetric`, `invalidMetricReason`, `diagnostics`, `invalidMonitoringLocation`.

New declarations within this existing file: `observeMetric`, `invalidMetricReason`, `diagnostics`, `invalidMonitoringLocation`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=e9b2730cb30f6582e20e5246e3939da60b881e26a93290c8447b89449562c1e8 after=4440bdbb85833f67d60dd4aa58020ce06e884b1f4abd9ee668868bd857c5a080 -->

<!-- course-file: packages/core/tests/persistence-runtime.test.ts -->

### persistence-runtime.test.ts

[Open current source](../../../../../packages/core/tests/persistence-runtime.test.ts) · **Snapshot:** modified existing file; 271 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for persistence meaning and coordination.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns exact lifecycle/lineage/outbox/pagination predicates and in-memory getId/clone/token/UoW boundaries. Existing brands, guards, callback receivers/read counts, error classes/causes, first failure and post-map-write behavior are preserved.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `assertValidation`, `boundary`, `caught`, `rejected`, `diagnosticCoverage`.

New declarations within this existing file: `assertValidation`, `boundary`, `caught`, `rejected`, `diagnosticCoverage`.

Added import edges: `../src/diagnostic-catalog`, `../src/authz/index`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=a8f302c9dc7987363e041c42eaba0bd6254cbd813b6928ebec150d516945d651 after=b6f58f413a8438f4a4bc066d2d322f1c67090979bbd1c73b6332ff419306a395 -->

<!-- course-file: packages/core/tests/persistence-types.test.ts -->

### persistence-types.test.ts

[Open current source](../../../../../packages/core/tests/persistence-types.test.ts) · **Snapshot:** modified existing file; 30 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for persistence meaning and coordination.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns exact lifecycle/lineage/outbox/pagination predicates and in-memory getId/clone/token/UoW boundaries. Existing brands, guards, callback receivers/read counts, error classes/causes, first failure and post-map-write behavior are preserved.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `HistoricalPersistenceCode`, `exactPersistenceCodes`, `observePersistence`, `persistenceDiagnosticOptions`, `observedUnitOfWork`, `observedRepository`, `validationDetail`, `boundaryDetail`, `companionDefinition`, `persistenceWithCompanions`, `invalidDiagnosticField`.

New declarations within this existing file: `HistoricalPersistenceCode`, `exactPersistenceCodes`, `observePersistence`, `persistenceDiagnosticOptions`, `observedUnitOfWork`, `observedRepository`, `validationDetail`, `boundaryDetail` (3 more in source).

Added import edges: `../src/diagnostics/index`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=3ccff62e8e2811b9ddbc6373879d56cb18df162d3869126877136bf05f593b35 after=3f900e6ee423f92fe6a29752c1108e489ed53a9e876ab4815f3ce008372ffceb -->

<!-- course-file: packages/core/tests/queues-runtime.test.ts -->

### queues-runtime.test.ts

[Open current source](../../../../../packages/core/tests/queues-runtime.test.ts) · **Snapshot:** modified existing file; 68 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns closed queue validation, unknown boundary and informational receive-reduction definitions, with finite optional native reported-condition detail. Runtime factories and independent receiver-preserving own/selected source primary plus eight related records observation remain physically reviewed under core-error-preservation rather than duplicating source ownership.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=e458bdde53882a77180bf1f6b038557e9c817bd93b4c6fe346826193870f2fd2 after=459933e58f112386349b5cd77be6baf7360d1b543e20e08fd813d8567a56eb47 -->

<!-- course-file: packages/core/tests/queues-types.test.ts -->

### queues-types.test.ts

[Open current source](../../../../../packages/core/tests/queues-types.test.ts) · **Snapshot:** modified existing file; 15 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for worker processing and queue delivery.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns closed queue validation, unknown boundary and informational receive-reduction definitions, with finite optional native reported-condition detail. Runtime factories and independent receiver-preserving own/selected source primary plus eight related records observation remain physically reviewed under core-error-preservation rather than duplicating source ownership.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `diagnosticOptions`, `contextualDiagnosticOptions`, `boundary`.

New declarations within this existing file: `diagnosticOptions`, `contextualDiagnosticOptions`, `boundary`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=24d88bf2ce58bfe4087289d50cfa2a5b2a49e3423de3380a23097994048d09a2 after=59f2a7dd8b3198a11d642e5051f17fafce3cd71c1b3da9b00d0bd8e5184ec924 -->

<!-- course-file: packages/core/tests/security-diagnostics-runtime.test.ts -->

### security-diagnostics-runtime.test.ts

[Open current source](../../../../../packages/core/tests/security-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 35 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for shared security observations.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Immutable provider-neutral content, positional block, peer-identity and peer-trust contracts; no filesystem, cryptographic-runtime or provider operations.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `definition`, `accessed`.

Added import edges: `node:assert/strict`, `../src/diagnostics/index`, `../src/security/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=e6ad0c89e2a7ca313876b15b40087039748d86e48a34283699ff01fd23df8369 -->

<!-- course-file: packages/core/tests/security-diagnostics-types.test.ts -->

### security-diagnostics-types.test.ts

[Open current source](../../../../../packages/core/tests/security-diagnostics-types.test.ts) · **Snapshot:** added (absent from baseline); 19 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for shared security observations.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Immutable provider-neutral content, positional block, peer-identity and peer-trust contracts; no filesystem, cryptographic-runtime or provider operations.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `tokenReason`, `wrongOperation`, `content`, `identity`, `trust`, `invalidContent`, `invalidIdentity`, `invalidEffect`.

Added import edges: `../src/security/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=78795d5b426e2d70f687451ee95b19d31d75b0bd9e504f7744002f6b083f99a3 -->

<!-- course-file: packages/core/tests/tenancy-runtime.test.ts -->

### tenancy-runtime.test.ts

[Open current source](../../../../../packages/core/tests/tenancy-runtime.test.ts) · **Snapshot:** modified existing file; 55 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for identity and tenant construction.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns additive principal and tenant-constructor boundary definitions. Optional observers independently deliver the exact observed projection/copy location and selected source primary plus up to eight related records, preserving raw primitive/frozen throw identity, eager claims enumeration, repeated getters, scope iteration and nullish tenant fallback.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `../src/diagnostics/index`.

Owning registered proof: `core-runtime`, `platform-security-runtime`, `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b0d7dae41ebbfa6e9140824fadd001a4ecf564ba3520842236a494ec44d044ec after=52393f8556185983e768e2cc126d6832588a2ee5e2864ffb183b18e361abd646 -->

<!-- course-file: packages/core/tests/tenancy-types.test.ts -->

### tenancy-types.test.ts

[Open current source](../../../../../packages/core/tests/tenancy-types.test.ts) · **Snapshot:** modified existing file; 4 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for identity and tenant construction.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns additive principal and tenant-constructor boundary definitions. Optional observers independently deliver the exact observed projection/copy location and selected source primary plus up to eight related records, preserving raw primitive/frozen throw identity, eager claims enumeration, repeated getters, scope iteration and nullish tenant fallback.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `diagnostics`.

New declarations within this existing file: `diagnostics`.

Owning registered proof: `core-runtime`, `platform-security-runtime`, `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=fe2951951749b2da5aa2187213ba80e36153e32f4a018cd3c4563ace8e9def5b after=f8c1d59091d2f899e4a39016f79952156a0a3e455a193bfd697d4c356f30dde3 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must a schema-valid record from an arbitrary caller not automatically become trusted evidence about a database call?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Shape validation establishes admissible data, not truth, exhaustiveness or remote delivery. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L001 packages/core](001-packages-core.md) · [L002 packages/core/contracts](002-packages-core-contracts.md) · [L003 packages/core/src](003-packages-core-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 31 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
