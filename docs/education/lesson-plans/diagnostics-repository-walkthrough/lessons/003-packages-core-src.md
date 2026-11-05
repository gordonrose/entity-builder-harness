<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l003
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L003 — packages/core/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src -->

## What you will understand

Core defines provider-independent facts and their allowed shapes. It must remain usable without a server, AWS account or particular database.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

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

<!-- course-file: packages/core/src/diagnostic-catalog.ts -->

### diagnostic-catalog.ts

[Open current source](../../../../../packages/core/src/diagnostic-catalog.ts) · **Snapshot:** added (absent from baseline); 28 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Explicitly combines Core capability definitions.

**Before:** This aggregate file was absent; Core capabilities already existed.

**After:** Exports a deliberate list assembled from capability-owned arrays, without importing Platform or discovering modules dynamically.

**Why:** Runtime meaning should be reviewable and dependency direction predictable.

Changed declaration anchors: `coreDiagnosticCatalog`.

Added import edges: `./config/diagnostics`, `./shared/diagnostics`, `./security/diagnostics`, `./authz/diagnostics`, `./authn/diagnostics`, `./tenancy/diagnostics`, `./persistence/diagnostics`, `./queues/diagnostics`, `./monitoring/boundary-diagnostics`, `./logging/diagnostics` (more in source).

Connected review context (`platform-config-diagnostics`; this review may span several files): Schema rejection reports its position independently from explicitly selected Core/app primary and eight companions. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-config-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`, `platform-workers-runtime`, `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=221afd9c1c67370cec57f4b95ba7710667f8d80b1faa701ad21bc03f2e3d9040 -->

<!-- course-file: packages/core/src/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/index.ts) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./diagnostic-catalog`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./diagnostic-catalog`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6a426dcac4325daccd046a329c554e7b2e2b09f39418a130b09eb5d9af9ed60b after=b8475d296f5f00b812a0fc6bf53396c71af3ae815fea9d3266a23ecb7bf6c852 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must a schema-valid record from an arbitrary caller not automatically become trusted evidence about a database call?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Shape validation establishes admissible data, not truth, exhaustiveness or remote delivery. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L001 packages/core](001-packages-core.md) · [L002 packages/core/contracts](002-packages-core-contracts.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L006 packages/core/tests](006-packages-core-tests.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
