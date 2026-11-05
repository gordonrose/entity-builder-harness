<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l057
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/persistence.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L057 — packages/core/src/persistence

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/persistence -->

## What you will understand

Persistence covers records, transactions, outbox messages, processing claims and lineage. An outbox holds work alongside a business change so it can be delivered later.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **9 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A write throws and a reconciliation read follows under existing policy. Report each observed step separately. A failed reconciliation cannot establish that the write did not happen, and diagnostic reporting must not introduce another write.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions.

**After:** Core owns primitive/storage-independent meanings; Platform owns orchestration meanings. Adapters add actual provider evidence. Local rejection, boundary failure, conditional conflict, stored shape and reconciliation remain distinct.

**Why this was needed:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

This directory contains `documentation`, `definition`, `implementation`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/persistence/README.md -->

### README.md

[Open current source](../../../../../packages/core/src/persistence/README.md) · **Snapshot:** modified existing file; 26 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for persistence meaning and coordination; read the sections `Core Persistence Source Map`, `What belongs elsewhere`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Core Persistence Source Map`; `What belongs elsewhere`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=4f72d4c74c39c998eaf92b3da74f9eca48ee527e1ce2ab3a2224fb09376ee0b9 after=f47b1c8befcbc6278e5def5989601ac36bdc1808686547b5d162b0ff659a0c67 -->

<!-- course-file: packages/core/src/persistence/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/persistence/diagnostics.ts) · **Snapshot:** added (absent from baseline); 49 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.persistence.validation-rejected`, `core.persistence.in-memory-boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `corePersistenceValidationDiagnostic`, `corePersistenceInMemoryBoundaryDiagnostic`, `corePersistenceDiagnosticDefinitions`, `CorePersistenceValidationDetail`, `CorePersistenceInMemoryBoundaryDetail`, `CorePersistenceDiagnosticObserver`, `InMemoryPersistenceDiagnosticOptions`, `corePersistenceValidationRecord`, `corePersistenceInMemoryBoundaryRecord`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `platform-smoke-runtime`, `diagnostic-catalog-readers`, `persistence-composition`, `platform-shell-payload`, `shell-package-source`, `core-runtime`, `postgresql-connection-diagnostics`, `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=eb4601f927835f8dd6110d5490283ee7a5503d85235076835c3bbefc029090ce -->

<!-- course-file: packages/core/src/persistence/errors.ts -->

### errors.ts

[Open current source](../../../../../packages/core/src/persistence/errors.ts) · **Snapshot:** modified existing file; 17 added / 18 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `persistenceErrorCodes`, `PersistenceErrorCode`, `PersistenceErrorInput`, `persistenceError` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Preserve supplied diagnosticRecord through existing error factories and add the optional validation projection; CoreError declares bounded related observations, with affected persistence factories validating them against explicitly supplied definitions. Shared date/JSON guards now retain value-free positional evidence; overridden map semantics and unavailable callback locations are tested without replacing existing errors.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `persistenceErrorCodes`, `PersistenceErrorCode`, `PersistenceErrorInput`, `persistenceError`.

New declarations within this existing file: `persistenceErrorCodes`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=9f632da9e0f3239fdf908885e7776a35204444272788a3c2c1cbcbb4285918d2 after=4eddea3edc2d1afb9155342cf3f95d7c815c9725651b3e941bb78ca53b4432b7 -->

<!-- course-file: packages/core/src/persistence/in-memory.ts -->

### in-memory.ts

[Open current source](../../../../../packages/core/src/persistence/in-memory.ts) · **Snapshot:** modified existing file; 94 added / 10 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `InMemoryRepositoryOptions`, `inMemoryRepository`, `inMemoryUnitOfWork`, `selectedDefinitions`, `intrinsicPromiseThen`, `observe`, `boundaryEvidence` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core owns exact lifecycle/lineage/outbox/pagination predicates and in-memory getId/clone/token/UoW boundaries. Existing brands, guards, callback receivers/read counts, error classes/causes, first failure and post-map-write behavior are preserved.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `InMemoryRepositoryOptions`, `inMemoryRepository`, `inMemoryUnitOfWork`, `selectedDefinitions`, `intrinsicPromiseThen`, `observe`, `boundaryEvidence`.

New declarations within this existing file: `selectedDefinitions`, `intrinsicPromiseThen`, `observe`, `boundaryEvidence`.

Added import edges: `../diagnostic-catalog`, `../diagnostics/index`, `./diagnostics`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c9bb0ce9552aa66dbf76d579121409aa4658ed1bf564bac70fecd2943b17283a after=22303ff5115cd1e2791dfae1cf9e0eac798e66588e29f0df3f3223fc0b32e12e -->

<!-- course-file: packages/core/src/persistence/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/persistence/index.ts) · **Snapshot:** modified existing file; 6 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./diagnostics`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./diagnostics`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d80c0a18dac3d65384e7176e7f4cb9d330727dec733a3f260c5899ac9c1e5ede after=d32939ed17476a6d419f07bc873b156d1438e49905868635f89f1dbc25fd702b -->

<!-- course-file: packages/core/src/persistence/lifecycle.ts -->

### lifecycle.ts

[Open current source](../../../../../packages/core/src/persistence/lifecycle.ts) · **Snapshot:** modified existing file; 18 added / 8 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `recordLifecyclePolicy`, `recordRetentionPolicyReference`, `logicallyDeleteRecord`, `restoreLogicallyDeletedRecord`, `invalidLifecycle` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core owns exact lifecycle/lineage/outbox/pagination predicates and in-memory getId/clone/token/UoW boundaries. Existing brands, guards, callback receivers/read counts, error classes/causes, first failure and post-map-write behavior are preserved.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `recordLifecyclePolicy`, `recordRetentionPolicyReference`, `logicallyDeleteRecord`, `restoreLogicallyDeletedRecord`, `invalidLifecycle`.

Added import edges: `./diagnostics`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=5919f73f1139151ec865f75823060a06ea8fb43a29b4be902af00e88222fc268 after=14ff1e5b70a7f128c243b1563802b5bbf724b8caa79a18c40327dcc8ab4637fd -->

<!-- course-file: packages/core/src/persistence/lineage.ts -->

### lineage.ts

[Open current source](../../../../../packages/core/src/persistence/lineage.ts) · **Snapshot:** modified existing file; 24 added / 10 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `recordKind`, `recordId`, `recordRevision`, `recordChangeFieldName`, `recordChangeActor`, `recordChange`, `invalidLineageError` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core owns exact lifecycle/lineage/outbox/pagination predicates and in-memory getId/clone/token/UoW boundaries. Existing brands, guards, callback receivers/read counts, error classes/causes, first failure and post-map-write behavior are preserved.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `recordKind`, `recordId`, `recordRevision`, `recordChangeFieldName`, `recordChangeActor`, `recordChange`, `invalidLineageError`.

Added import edges: `./diagnostics`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=60e8192b4dbbb4ab06e07b6532b9e3f2603445f3231c5a8faf02f9823de45b81 after=6c10356e36a2a7f2b1eed35081adf31cad40149ade9823d6e3b310778d737b4d -->

<!-- course-file: packages/core/src/persistence/outbox.ts -->

### outbox.ts

[Open current source](../../../../../packages/core/src/persistence/outbox.ts) · **Snapshot:** modified existing file; 6 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `outboxMessageType`, `outboxMessageVersion`, `outboxDeliveryPolicy` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core owns exact lifecycle/lineage/outbox/pagination predicates and in-memory getId/clone/token/UoW boundaries. Existing brands, guards, callback receivers/read counts, error classes/causes, first failure and post-map-write behavior are preserved.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `outboxMessageType`, `outboxMessageVersion`, `outboxDeliveryPolicy`.

Added import edges: `./diagnostics`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c50f99d639f6541e26c715b7de06423c1218be215d836f74b9b2901610f5aa98 after=67beed2467ac92e7df90a7d864db85ffa4f218ca15069fec7a41301cb7ec1d58 -->

<!-- course-file: packages/core/src/persistence/pagination.ts -->

### pagination.ts

[Open current source](../../../../../packages/core/src/persistence/pagination.ts) · **Snapshot:** modified existing file; 15 added / 6 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `pageTotal`, `pageTotals`, `pageRequest`, `invalidPageTotalError` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core owns exact lifecycle/lineage/outbox/pagination predicates and in-memory getId/clone/token/UoW boundaries. Existing brands, guards, callback receivers/read counts, error classes/causes, first failure and post-map-write behavior are preserved.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `pageTotal`, `pageTotals`, `pageRequest`, `invalidPageTotalError`.

Added import edges: `./diagnostics`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=aba5fc086b24e9e32b553a21ef8be72473cb09331246b3d5890532046d507b05 after=68e2ddd266272e3cda05bed323e810d27169463ce1a3537dc8299b1dc98c5bbf -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which evidence would establish write-not-reached, and which merely establishes that the invocation did not return?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new transaction, SQL, privilege, retry or delivery guarantee is authorized by adding diagnostics. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/persistence) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 9 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
