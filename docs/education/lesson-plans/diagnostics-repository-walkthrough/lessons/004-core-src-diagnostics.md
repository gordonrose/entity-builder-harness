<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l004
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/diagnostics.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L004 — packages/core/src/diagnostics

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/diagnostics -->

## What you will understand

Core defines provider-independent facts and their allowed shapes. It must remain usable without a server, AWS account or particular database.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **4 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a raw exception with an object carrying code, definitionVersion, schema and detail. Add an undeclared detail property: parsing must reject that record. A valid shape still does not prove that the claimed event happened; the producer must have observed it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The baseline already had diagnostic classifications and monitoring concepts. Those useful abstractions did not, by themselves, give every capability a closed, versioned record that a reader could validate.

**After:** Definitions declare a stable code, version, classification and permitted detail. Constructors copy and validate records; selectors accept only explicitly selected evidence. Shared helpers bound related evidence to eight records.

**Why this was needed:** A description written by an agent is not a runtime contract. Code-owned definitions let producers and readers agree without interpreting prose or trusting an arbitrary error object.

This directory contains `implementation`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/diagnostics/definition.ts -->

### definition.ts

[Open current source](../../../../../packages/core/src/diagnostics/definition.ts) · **Snapshot:** added (absent from baseline); 47 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Defines and validates a diagnostic meaning.

**Before:** This file was absent; existing descriptor classifications lived in the diagnostic module.

**After:** defineDiagnostic validates the code/version/classification/detail declaration, snapshots it and freezes it. validDiagnosticDefinition rejects malformed declarations.

**Why:** Definitions must not mutate later with caller state or silently accept undeclared shapes.

Changed declaration anchors: `DiagnosticClassification`, `DiagnosticDefinition`, `validDiagnosticDefinition`, `defineDiagnostic`, `freezeDefinition`.

Added import edges: `./index`, `./schema`.

Connected review context (`core-diagnostic-contracts`; this review may span several files): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=c6844ffe6edf159d7c93aaefb407d15c0f6b0ce7aeae71f1319f6fa57488ea6b -->

<!-- course-file: packages/core/src/diagnostics/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/diagnostics/index.ts) · **Snapshot:** modified existing file; 7 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Keeps the existing diagnostic descriptor API and exports the new record API.

**Before:** The barrel already exposed classifications/descriptors.

**After:** Adds exports from definition, record and schema. It does not implement the configuration issue collector described by the wider foundation review.

**Why:** Consumers need a stable public import; implementation remains in its owning files.

Added import edges: `./definition`, `./record`, `./schema`.

Connected review context (`core-diagnostic-contracts`; this review may span several files): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ffc294face8a97304df0707b8cf59eaacfc646a75758d701cc823663d6b81c8c after=cb5e30e2f379287f84abba61d0987e0d65a7cf1c036e5ef252a14fb48dbd14db -->

<!-- course-file: packages/core/src/diagnostics/record.ts -->

### record.ts

[Open current source](../../../../../packages/core/src/diagnostics/record.ts) · **Snapshot:** added (absent from baseline); 111 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Constructs, parses and selects safe diagnostic records.

**Before:** No dedicated versioned record/selection module existed at this path.

**After:** Creates frozen code/version/detail records, caps serialized length, validates exact envelopes and selects own-data primary/related records from explicitly provided definitions. Related evidence is bounded at eight.

**Why:** A caller-controlled getter, prototype field or cause chain must not execute or become trusted merely because a wrapper inspects an exception.

Changed declaration anchors: `DiagnosticRecord`, `DiagnosticRecordError`, `diagnosticRelatedRecordLimit`, `selectDiagnosticEvidence`, `ownDataValue`, `selectedRecord`, `selectedRelatedRecords`, `parseRelatedDiagnosticRecords`, `invalid`, `createDiagnosticRecord`, `parseDiagnosticRecord`.

Added import edges: `../shared/index`, `./definition`, `./schema`.

Connected review context (`core-diagnostic-contracts`; this review may span several files): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`, `platform-contracts-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=87092521a24bd063cf780b36e91c5cf3b684ca1079325b3959a082d1aa91d954 -->

<!-- course-file: packages/core/src/diagnostics/schema.ts -->

### schema.ts

[Open current source](../../../../../packages/core/src/diagnostics/schema.ts) · **Snapshot:** added (absent from baseline); 106 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Defines the restricted diagnostic detail grammar.

**Before:** This dedicated schema implementation was absent.

**After:** Validates supported detail schemas and copies only admissible detail, rejecting unsupported or unsafe structures.

**Why:** A TypeScript type disappears at runtime; untrusted input still needs actual validation.

Changed declaration anchors: `DiagnosticDetailSchema`, `DiagnosticDetail`, `forbiddenKeys`, `diagnosticObject`, `diagnosticArray`, `exactKeys`, `validDiagnosticSchema`, `copyDiagnosticDetail`.

Connected review context (`core-diagnostic-contracts`; this review may span several files): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=2894b65e61fab00220d80d64688b63f880dcbe844f09528ae439cf46d328dead -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must a schema-valid record from an arbitrary caller not automatically become trusted evidence about a database call?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Shape validation establishes admissible data, not truth, exhaustiveness or remote delivery. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/diagnostics) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 4 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
