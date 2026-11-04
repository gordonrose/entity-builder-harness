<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l007
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-02"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/config.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L007 — packages/core/src/config

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/config -->

Current-source links follow the config contract/domain reorganisation. Snapshot
paths and counts below remain historical. The collector is now in
[domain/issue-collection.ts](../../../../../packages/core/src/config/domain/reporting/issue-collection.ts),
and JSON parsing in [domain/json-object.ts](../../../../../packages/core/src/config/domain/validation/json-object.ts).

## What you will understand

Configuration code turns supplied settings into values the workload can use. A setting is a logical requirement; its environment-variable name belongs to the caller that binds it.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **5 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Start with the original combined host/database/schema/reference/port guard. If port is absent and host is present, the useful observation is the port requirement being missing—not a guessed connection failure. If reading the source throws before a value is obtained, wrong-type would be an unsupported claim.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing readers rejected missing or malformed values, but several callers collapsed alternatives into undefined or one broad configuration error.

**After:** Reusable readers retain safe setting references, exact observed reasons, source-read failures, indexed issues and explicitly declared relationships. Target bindings supply exact source names privately, without placing submitted values in diagnostic detail.

**Why this was needed:** An agent needs to know which requirement failed and whether to fix a declaration, provide a setting, or investigate an unreadable source. One broad rejection cannot support that decision.

This directory contains `definition`, `barrel-or-implementation`, `implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/config/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/config/contract/reporting/diagnostics.ts) · **Snapshot:** added (absent from baseline); 47 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.config.primitive-invalid`, `core.config.source-threw`, `core.config.declaration-invalid`, `core.config.relationship-declaration-invalid`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `classification`, `coreConfigPrimitiveDiagnostic`, `CoreConfigReader`, `coreConfigSourceDiagnostic`, `coreConfigDeclarationDiagnostic`, `coreConfigRelationshipDeclarationDiagnostic`, `coreConfigDiagnosticDefinitions`, `coreConfigPrimitiveRecord`, `coreConfigSourceRecord`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`, `platform-smoke-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b92302c9f586ebe09cf74e07e2092e2f4faca41d617a092287b302c6b6d8c20c -->

<!-- course-file: packages/core/src/config/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/config/index.ts) · **Snapshot:** modified existing file; 49 added / 16 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports configuration: tell absence from invalidity at this layer.

**Before:** Existing readers rejected missing or malformed values, but several callers collapsed alternatives into undefined or one broad configuration error. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `ConfigError`, `configError`, `environmentName`, `secretReference`, `requiredConfigValue`, `readRequiredConfigValue`, `optionalConfigValue` (7 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. Indexed issue collection copies and freezes logical references/positions, retains deterministic order and explicitly reports overflow at 32 issues.

**Why:** An agent needs to know which requirement failed and whether to fix a declaration, provide a setting, or investigate an unreadable source. One broad rejection cannot support that decision.

Changed declaration anchors: `ConfigError`, `configError`, `environmentName`, `secretReference`, `requiredConfigValue`, `readRequiredConfigValue`, `optionalConfigValue`, `readConfigSource`, `stringConfigValue`, `numberConfigValue`, `booleanConfigValue`, `missingConfigError` (2 more in source).

New declarations within this existing file: `readRequiredConfigValue`, `readConfigSource`.

Added import edges: `../diagnostics/index`, `../shared/diagnostics`, `./diagnostics`, `./issues`, `./schema`, `./source-observation`.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=134c5d34d3d9fb7db25e529c7314469f309dacc6d06d0850cf9bde616a6d5d45 after=fbe2e20fe76ba564cb23321e10b18d7cdd34fd5776c44348fa94962b353b4d43 -->

<!-- course-file: packages/core/src/config/issues.ts -->

### issues.ts

[Open current source](../../../../../packages/core/src/config/contract/reporting/setting-issues.ts) · **Snapshot:** added (absent from baseline); 56 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Represents bounded configuration issues.

**Before:** There was no shared indexed issue collector in this file.

**After:** Collects logical setting/check/relationship issues in order, copies/freezes references and records overflow at its 32-issue bound.

**Why:** An agent can see multiple independent problems without exposing values or assuming a truncated collection is exhaustive.

Changed declaration anchors: `configIssueReasons`, `configValueIssueReasons`, `ConfigIssueReason`, `ConfigSettingIssue`, `ConfigCheckIssue`, `ConfigCheckFailure`, `createConfigIssueCollector`, `ConfigRelationshipIssue`.

Connected review context (`core-diagnostic-contracts`; this review may span several files): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=3ff221fa7ab537a6feda494552749328cced7e33b4932c72d502d395cf416d2c -->

<!-- course-file: packages/core/src/config/schema.ts -->

### schema.ts

[Open current source](../../../../../packages/core/src/config/domain/validation/settings.ts) · **Snapshot:** added (absent from baseline); 163 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Validates declared settings and relationships.

**Before:** Callers composed primitive readers and custom checks without this shared declared-settings implementation.

**After:** Adds reusable setting rules, bounded positions, declaration checking and opt-in relationships, including comparisons only after both parsed participants are valid.

**Why:** A malformed rule and a bad supplied setting have different owners; neither should be hidden by a combined undefined result.

Changed declaration anchors: `nativeDeclarationSome`, `applyDeclarationSome`, `declarationSome`, `declarationPosition`, `parseConfigJsonObject`, `ConfigSettingRule`, `ConfigSettingDefinition`, `ConfigSettingsFailure`, `ConfigSettingRelationship`, `ConfigSettingsRelationshipFailure`, `validateConfigSettings`, `validateConfigSettings` (3 more in source).

Added import edges: `../shared/index`, `./index`, `./issues`, `../diagnostics/index`, `../shared/diagnostics`, `./diagnostics`.

Connected review context (`core-diagnostic-contracts`; this review may span several files): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=7dfbd1ca81bc99a28fc693937ec64168a2af1e426d145f7d0755a204dac3459b -->

<!-- course-file: packages/core/src/config/source-observation.ts -->

### source-observation.ts

[Open current source](../../../../../packages/core/src/config/contract/reporting/sourcing-issues.ts) · **Snapshot:** added (absent from baseline); 22 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Names failures of reading a configuration source.

**Before:** This source-read vocabulary was absent at this path.

**After:** Separates a source invocation failure from a successfully read value that fails validation.

**Why:** Unavailable evidence must not be diagnosed as a missing or wrong-type value.

Changed declaration anchors: `configSourceReadFailureReasons`, `ConfigSourceReadFailureReason`.

Connected review context (`core-diagnostic-contracts`; this review may span several files): Closed diagnostic construction, bounded dense related-record validation and reusable value-free configuration/source-read observations, including opt-in must-differ comparisons of independently valid parsed settings; existing two-argument results, primitive readers and retained definition reason sets remain compatible. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=88cffdd9ed056da2b6ba198b9a1116d2c7a0ca9b8ded49c52fb6b4018ad93790 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which fact distinguishes a missing setting from a getter that threw before the setting could be read?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Do not expose hostnames, usernames, passwords, source contents or rejected values. The issue collector has a bound; overflow must not be called complete. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/config) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 5 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
