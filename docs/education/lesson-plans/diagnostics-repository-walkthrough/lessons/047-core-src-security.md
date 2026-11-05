<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l047
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/security.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L047 — packages/core/src/security

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/security -->

## What you will understand

Security owns reusable meanings for trust material, TLS, tokens, claims, permissions, headers/CORS and rate-limiter checks. CORS is the browser cross-origin response policy.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **6 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A bundle has two complete certificate blocks and the second cannot be parsed. Report the block number and fixed reason, never certificate bytes. Parsing success is syntax only; hostname, chain, expiration and revocation are separate facts.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations.

**After:** Core owns provider-neutral security definitions; Platform implements shared parsing/observation; adapters bind native evidence; callers retain operation context. Existing token and policy decisions are preserved.

**Why this was needed:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

This directory contains `implementation`, `definition`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/security/classification.ts -->

### classification.ts

[Open current source](../../../../../packages/core/src/security/classification.ts) · **Snapshot:** modified existing file; 4 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `assertKnownValue` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Natural Core config/shared/security/authz modules own closed actual guard meanings and a package-root explicit catalog. Exact primitive grammar, first failure, source/getter reads, same thrown identity, custom map/some semantics and unavailable location/classification are independently tested.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `assertKnownValue`.

Added import edges: `../shared/diagnostics`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=a49e486c3e9ec84ed9f5687752249144e813f963e75f2f57e9e4afa5eb612818 after=22feb385debc944fe3671651eb72171509dc426ddb39cff49b1a186f46a10274 -->

<!-- course-file: packages/core/src/security/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/security/diagnostics.ts) · **Snapshot:** added (absent from baseline); 99 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.security.primitive-invalid`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `securityTrustMaterialFailureReasons`, `SecurityTrustMaterialFailureReason`, `securityPeerIdentityFailureReasons`, `SecurityPeerIdentityFailureReason`, `securityPeerTrustFailureReasons`, `SecurityPeerTrustFailureReason`, `SecurityTrustMaterialFailureDetail`, `securityCertificateBlockFailureReasons`, `SecurityCertificateBlockFailureReason`, `SecurityCertificateBlockFailureDetail`, `SecurityPeerIdentityFailureDetail`, `SecurityPeerTrustFailureDetail` (6 more in source).

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=073dc471ecd4f9cbfc62951cbe8e60ad37dde35db909298d4de3f875701ecd75 -->

<!-- course-file: packages/core/src/security/hashing.ts -->

### hashing.ts

[Open current source](../../../../../packages/core/src/security/hashing.ts) · **Snapshot:** modified existing file; 8 added / 6 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `assertNonEmpty`, `assertToken` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Natural Core config/shared/security/authz modules own closed actual guard meanings and a package-root explicit catalog. Exact primitive grammar, first failure, source/getter reads, same thrown identity, custom map/some semantics and unavailable location/classification are independently tested.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `assertNonEmpty`, `assertToken`.

Added import edges: `../shared/diagnostics`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=faf561ed36309a98c7e486c2b3fb286e1dc891b3860018b67a6888e7ddfcaef0 after=21a4f7c1239b85c7f4ae175ddeeb8c1c37ad9eaf30cfd3a1917ba934ac54ab60 -->

<!-- course-file: packages/core/src/security/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/security/index.ts) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./diagnostics`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=aad5c6f541801a276da0fce124b913e74b6fd993338084a35e5fa9f64499399c after=c38bad9547143cc8202e454b20b09aecabffce1b9c9fb2c640620c914b010352 -->

<!-- course-file: packages/core/src/security/policy.ts -->

### policy.ts

[Open current source](../../../../../packages/core/src/security/policy.ts) · **Snapshot:** modified existing file; 5 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `assertNonEmpty`, `assertToken` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Natural Core config/shared/security/authz modules own closed actual guard meanings and a package-root explicit catalog. Exact primitive grammar, first failure, source/getter reads, same thrown identity, custom map/some semantics and unavailable location/classification are independently tested.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `assertNonEmpty`, `assertToken`.

Added import edges: `../shared/diagnostics`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=8973759374766995c2b94b37c4fa4c4de3d471ea7bce2d4f78303f5ffbee7ca5 after=24d7cecc96c80a21d0145c97e4674709215d15d0fc97dd00a6bb728d82da4493 -->

<!-- course-file: packages/core/src/security/secrets.ts -->

### secrets.ts

[Open current source](../../../../../packages/core/src/security/secrets.ts) · **Snapshot:** modified existing file; 3 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `assertNonEmpty` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Natural Core config/shared/security/authz modules own closed actual guard meanings and a package-root explicit catalog. Exact primitive grammar, first failure, source/getter reads, same thrown identity, custom map/some semantics and unavailable location/classification are independently tested.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `assertNonEmpty`.

Added import edges: `../shared/diagnostics`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=53a1cde1529ff1854c74ad0c40e7fa415d49ad4ad8a5cdfd5c202778ee7eb5f4 after=ffab575c0f21621cfe5174c518530464c1470b577c20174aa201c3b352444706 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why does certificate parsing success not prove that a remote server is trustworthy?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Sessions, cookies, CSRF, broader secret lifecycle and additional tenant controls remain separately planned, not silently implemented. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/security) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 6 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
