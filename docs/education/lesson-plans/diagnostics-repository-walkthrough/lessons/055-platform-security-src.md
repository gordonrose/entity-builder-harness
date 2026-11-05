<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l055
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/security/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L055 — platform/security/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/security/src -->

## What you will understand

Security owns reusable meanings for trust material, TLS, tokens, claims, permissions, headers/CORS and rate-limiter checks. CORS is the browser cross-origin response policy.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **10 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A bundle has two complete certificate blocks and the second cannot be parsed. Report the block number and fixed reason, never certificate bytes. Parsing success is syntax only; hostname, chain, expiration and revocation are separate facts.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations.

**After:** Core owns provider-neutral security definitions; Platform implements shared parsing/observation; adapters bind native evidence; callers retain operation context. Existing token and policy decisions are preserved.

**Why this was needed:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

This directory contains `documentation`, `implementation`, `definition`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/security/src/README.md -->

### README.md

[Open current source](../../../../../platform/security/src/README.md) · **Snapshot:** modified existing file; 38 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for shared security observations; read the sections `Platform Security Source Map`, `Detailed guide to the files`, `errors.ts — one safe language for security failures`, `authorization.ts — generic permission mechanics, not business policy`, `jwt.ts — proving that a token is trustworthy`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Security Source Map`; `Detailed guide to the files`; `errors.ts — one safe language for security failures`; `authorization.ts — generic permission mechanics, not business policy`; `jwt.ts — proving that a token is trustworthy`; `authentication.ts — turning verified identity facts into a principal`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=e81f5a802c813bf78cdd87f6cdcb3702e961a9f5685725b1b1fc5060c049614b after=98416d23b416e4006ac0cc54a87f9e881d815e3e2edad08f42a2394a422ccfac -->

<!-- course-file: platform/security/src/authentication.ts -->

### authentication.ts

[Open current source](../../../../../platform/security/src/authentication.ts) · **Snapshot:** modified existing file; 89 added / 25 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformAuthenticationResult`, `PlatformPrincipalMissingAttribute`, `PlatformPrincipalDiagnosticContext`, `PlatformPrincipalDiagnosticOptions`, `principalNativeThen`, `isolatePrincipalObservation`, `principalFromPlatformAuthenticationResult` (3 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Exact observed header/token/signing-key/mapping/policy/limiter predicates, bounded locations and omission counts; preserve acceptance, cache, throw-vs-denial, time and HTTP boundaries, no raw identity/provider values; safe unknown observations and invocation-specific TLS evidence. In-memory limiter direct guards preserve historical primary, RangeError and defaults while adding exact predicate companions with no clock/store work or new policy.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `PlatformAuthenticationResult`, `PlatformPrincipalMissingAttribute`, `PlatformPrincipalDiagnosticContext`, `PlatformPrincipalDiagnosticOptions`, `principalNativeThen`, `isolatePrincipalObservation`, `principalFromPlatformAuthenticationResult`, `createJwtBearerAuthenticationHook`, `bearerTokenFromHeaders`, `observeBearerTokenFromHeaders`.

New declarations within this existing file: `PlatformPrincipalMissingAttribute`, `PlatformPrincipalDiagnosticContext`, `PlatformPrincipalDiagnosticOptions`, `principalNativeThen`, `isolatePrincipalObservation`, `observeBearerTokenFromHeaders`.

Added import edges: `@kanbien/core/diagnostics`, `./diagnostics`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f9d3a942202ce74ada2f5fac11460b594a0211216440a6038bc2a95145bedbb1 after=f2ae1c6a9978ff308c6c66bdaa882ddcd2ad34da299a5b62a6d9cc4971af6837 -->

<!-- course-file: platform/security/src/authorization.ts -->

### authorization.ts

[Open current source](../../../../../platform/security/src/authorization.ts) · **Snapshot:** modified existing file; 28 added / 5 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `authorizePlatformPermissions`, `permissionsFromClaims`, `observePermissionsFromClaims`, `validateAuthzMappingPermissions` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Exact observed header/token/signing-key/mapping/policy/limiter predicates, bounded locations and omission counts; preserve acceptance, cache, throw-vs-denial, time and HTTP boundaries, no raw identity/provider values; safe unknown observations and invocation-specific TLS evidence. In-memory limiter direct guards preserve historical primary, RangeError and defaults while adding exact predicate companions with no clock/store work or new policy.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `authorizePlatformPermissions`, `permissionsFromClaims`, `observePermissionsFromClaims`, `validateAuthzMappingPermissions`.

New declarations within this existing file: `observePermissionsFromClaims`.

Added import edges: `@kanbien/core/diagnostics`, `./diagnostics`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=da7000f2c6383b568d1e0b869b8815c2f0d0ff9c502330be619b1765ff1568ab after=4af20c124b67bdd6e068247bcbd213f5afe6ee215c87f35f3b0fb6400f7f394c -->

<!-- course-file: platform/security/src/certificates.ts -->

### certificates.ts

[Open current source](../../../../../platform/security/src/certificates.ts) · **Snapshot:** added (absent from baseline); 73 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Parses complete PEM certificate blocks without doing I/O.

**Before:** There was no shared Platform certificate-content observer at this path.

**After:** Uses Node X509Certificate for each complete block, returns certificate count or fixed indexed reasons, and keeps strict marker validation opt-in.

**Why:** Syntax meaning belongs to shared Security; preserving the compatible complete-block policy avoids a silent acceptance-policy change.

Changed declaration anchors: `CertificateAuthorityContentObservation`, `CertificateAuthorityContentError`, `validateCertificateAuthorityContent`.

Added import edges: `node:crypto`, `@kanbien/core/diagnostics`, `@kanbien/core/security`, `@kanbien/core/shared`, `./diagnostics`.

Connected review context (`platform-certificate-content-observation`; this review may span several files): Parse complete certificate blocks with exact one-based malformed-block records, plus explicit strict marker validation; preserve production complete-block acceptance and comments without retaining content/native errors or claiming CA role, lifetime or peer trust. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=e43a02071dea3b24701c114cc3991308cdc973e4b832c96e3a2e99ca07846d27 -->

<!-- course-file: platform/security/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../platform/security/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 266 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `security.trust-material-invalid`, `security.peer-identity-verification-failed`, `security.peer-trust-verification-failed`, `security.certificate-block-invalid`, `security.configuration-predicate-invalid`, `security.rate-limit-clock-failed`, `security.authentication.principal-boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `securityConfigurationReferences`, `securityOwnedHeaderReferences`, `SecurityObservationOptions`, `operationDefinitions`, `RequiredSecurityOptions`, `SecurityRecordArguments`, `securityOperationDiagnosticRecord`, `securityOperationDiagnosticRecord`, `observedFailures`, `observedCompanions`, `observeSecurityFailure`, `securityFailureDiagnosticRecord` (20 more in source).

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/core/security`.

Owning registered proof: `postgresql-connection-diagnostics`, `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`, `persistence-composition`, `platform-shell-payload`, `platform-security-runtime`, `security-cognito-diagnostics`, `shell-package-source`, `security-shared-rate-limit-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=77f0648756fd3eea7176a1ecc5f0f20efd0705372844b2cf2ede51737e4f083d -->

<!-- course-file: platform/security/src/errors.ts -->

### errors.ts

[Open current source](../../../../../platform/security/src/errors.ts) · **Snapshot:** modified existing file; 3 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformSecurityError` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Closed reason-specific certificate, peer, header, token, signing-key, authorization, policy and limiter definitions; required safe locations, copied validated extraction, invocation-local private evidence retention, phase-safe public types and immutable prior definitions. Additive shared-security configuration-predicate records identify exact limiter fields and observed numeric/empty alternatives without widening historical identities.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `PlatformSecurityError`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=be6488e1e8d19772d68757333f22fbc320224169dedb63716236ce23b49f5e2a after=930618f945fd906a56248dcc6d43a3fd7ac170294aafeb4690832511ca66431a -->

<!-- course-file: platform/security/src/headers.ts -->

### headers.ts

[Open current source](../../../../../platform/security/src/headers.ts) · **Snapshot:** modified existing file; 14 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `corsPolicyForRequestOrigin`, `observeCorsPolicyForRequestOrigin` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Exact observed header/token/signing-key/mapping/policy/limiter predicates, bounded locations and omission counts; preserve acceptance, cache, throw-vs-denial, time and HTTP boundaries, no raw identity/provider values; safe unknown observations and invocation-specific TLS evidence. In-memory limiter direct guards preserve historical primary, RangeError and defaults while adding exact predicate companions with no clock/store work or new policy.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `corsPolicyForRequestOrigin`, `observeCorsPolicyForRequestOrigin`.

New declarations within this existing file: `observeCorsPolicyForRequestOrigin`.

Added import edges: `@kanbien/core/diagnostics`, `./diagnostics`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=37eeba3e342c58e567b7983cd9159015deadad3fe19593213fa8a996d7c7ef81 after=64fc1a492e49562db929a49393bf5495c7d24b2e3e16e722eb04017cd4d83035 -->

<!-- course-file: platform/security/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/security/src/index.ts) · **Snapshot:** modified existing file; 19 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./certificates`, `./diagnostics`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./certificates`, `./diagnostics`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=7ef7d79fffb83937abdcb84b78fb8f1273515f82a8e060009cc4ad4e3228976c after=0cd02a8a59197c6ede601ad88390744955cbbf5b1d65538ec712e6111b013e9e -->

<!-- course-file: platform/security/src/jwt.ts -->

### jwt.ts

[Open current source](../../../../../platform/security/src/jwt.ts) · **Snapshot:** modified existing file; 71 added / 34 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformVerifiedJwt`, `createJwksJwtVerifier`, `validateJwtClaims`, `decodeJwt`, `decodeJsonSegment`, `invalidToken`, `defaultJwksFetcher` (1 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Exact observed header/token/signing-key/mapping/policy/limiter predicates, bounded locations and omission counts; preserve acceptance, cache, throw-vs-denial, time and HTTP boundaries, no raw identity/provider values; safe unknown observations and invocation-specific TLS evidence. In-memory limiter direct guards preserve historical primary, RangeError and defaults while adding exact predicate companions with no clock/store work or new policy.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `PlatformVerifiedJwt`, `createJwksJwtVerifier`, `validateJwtClaims`, `decodeJwt`, `decodeJsonSegment`, `invalidToken`, `defaultJwksFetcher`, `stringFailure`.

New declarations within this existing file: `stringFailure`.

Added import edges: `./diagnostics`, `@kanbien/core/security`, `@kanbien/core/diagnostics`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=77d2b85e5cb7c9c51ebc29163e3c477ab52623c467a026dac312a0e6da81cab4 after=6753e05211f75aff51ea66fab22c7969450d255bcb89501d265692ec08182e37 -->

<!-- course-file: platform/security/src/rate-limiting.ts -->

### rate-limiting.ts

[Open current source](../../../../../platform/security/src/rate-limiting.ts) · **Snapshot:** modified existing file; 33 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared security observations at this layer.

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformRateLimitDecision`, `createInMemoryPlatformRateLimiter`, `assertPositiveInteger`, `observePlatformRateLimitCheck` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Exact observed header/token/signing-key/mapping/policy/limiter predicates, bounded locations and omission counts; preserve acceptance, cache, throw-vs-denial, time and HTTP boundaries, no raw identity/provider values; safe unknown observations and invocation-specific TLS evidence. In-memory limiter direct guards preserve historical primary, RangeError and defaults while adding exact predicate companions with no clock/store work or new policy.

**Why:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

Changed declaration anchors: `PlatformRateLimitDecision`, `createInMemoryPlatformRateLimiter`, `assertPositiveInteger`, `observePlatformRateLimitCheck`.

New declarations within this existing file: `observePlatformRateLimitCheck`.

Added import edges: `@kanbien/core/diagnostics`, `./diagnostics`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=73f2caabae0289727d857a2f3375e6303863930a176a1868d840eb6a12b9e1bb after=3c8e49899cdb6207ac0cb38e10ab873987b17bb385b2960a4028a9cae67bccf7 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why does certificate parsing success not prove that a remote server is trustworthy?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Sessions, cookies, CSRF, broader secret lifecycle and additional tenant controls remain separately planned, not silently implemented. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/security/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L053 platform/security](053-platform-security.md) · [L054 platform/security/contracts](054-platform-security-contracts.md) · [L056 platform/security/tests](056-platform-security-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 10 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
