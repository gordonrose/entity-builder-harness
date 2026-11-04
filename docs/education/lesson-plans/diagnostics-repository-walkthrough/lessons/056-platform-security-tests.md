<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l056
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/security/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L056 — platform/security/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/security/tests -->

## What you will understand

Security owns reusable meanings for trust material, TLS, tokens, claims, permissions, headers/CORS and rate-limiter checks. CORS is the browser cross-origin response policy.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **8 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A bundle has two complete certificate blocks and the second cannot be parsed. Report the block number and fixed reason, never certificate bytes. Parsing success is syntax only; hostname, chain, expiration and revocation are separate facts.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** These security mechanisms existed in several places. Certificate and TLS problems could be described using persistence-specific or coarse errors, while other paths lacked consistent safe observations.

**After:** Core owns provider-neutral security definitions; Platform implements shared parsing/observation; adapters bind native evidence; callers retain operation context. Existing token and policy decisions are preserved.

**Why this was needed:** TLS is used by more than databases. Reusing Security meaning avoids one certificate vocabulary in Persistence and a different one in each future integration.

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/security/tests/configuration-predicate-diagnostics-runtime.test.ts -->

### configuration-predicate-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/security/tests/configuration-predicate-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 90 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for shared security observations.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed reason-specific certificate, peer, header, token, signing-key, authorization, policy and limiter definitions; required safe locations, copied validated extraction, invocation-local private evidence retention, phase-safe public types and immutable prior definitions. Additive shared-security configuration-predicate records identify exact limiter fields and observed numeric/empty alternatives without widening historical identities.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `primary`, `companion`, `fields`, `invalids`, `coercionReads`, `noCoercion`, `definition`, `valid`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `../src/index`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=9e3e614c7f1dc6dcc54c0580a454c7ba4583cadb1999b7877fcae5a03ddf3f42 -->

<!-- course-file: platform/security/tests/platform-security-runtime.test.ts -->

### platform-security-runtime.test.ts

[Open current source](../../../../../platform/security/tests/platform-security-runtime.test.ts) · **Snapshot:** modified existing file; 68 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for shared security observations.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `@kanbien/core/diagnostics`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=9dec2b26a0d588e80395feb78de788031bcc0485ff8f84f19a02f5cf9cc935a5 after=656fa494b6779ae3cfa06afa5ec4b890cd52881158edb39b9802eba29a942f2c -->

<!-- course-file: platform/security/tests/platform-security-types.test.ts -->

### platform-security-types.test.ts

[Open current source](../../../../../platform/security/tests/platform-security-types.test.ts) · **Snapshot:** modified existing file; 8 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for shared security observations.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `principalDiagnostics`.

New declarations within this existing file: `principalDiagnostics`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=54e6f96116b0a5b5cb1ba6512d91351cf4a36e64c234a73e30264c08649265b1 after=347f362a4f07ae4f8ba8a50377565e700e9b21cd63132519d22755bed435a7e8 -->

<!-- course-file: platform/security/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/security/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 2 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=ba1885c92f5150fb1a539a9f0059ce484ba02868be29c65eb5958cbf049c5214 after=b9d6ee7ae819b761008cfe65fdcf5512eec41f147fe000050af42963c4d2bcc9 -->

<!-- course-file: platform/security/tests/security-certificates-runtime.test.ts -->

### security-certificates-runtime.test.ts

[Open current source](../../../../../platform/security/tests/security-certificates-runtime.test.ts) · **Snapshot:** added (absent from baseline); 85 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for shared security observations.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Parse complete certificate blocks with exact one-based malformed-block records, plus explicit strict marker validation; preserve production complete-block acceptance and comments without retaining content/native errors or claiming CA role, lifetime or peer trust.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `bundle`, `blocks`, `malformed`, `valid`, `begin`, `end`, `blockRecord`.

Added import edges: `node:assert/strict`, `node:fs`, `@kanbien/core/diagnostics`, `@kanbien/core/security`, `../src/index`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=4ee807f9a2008205c9abfa7a9065f9fbaddbb3c774a8d356ab5b6a76b6e665bb -->

<!-- course-file: platform/security/tests/security-certificates-types.test.ts -->

### security-certificates-types.test.ts

[Open current source](../../../../../platform/security/tests/security-certificates-types.test.ts) · **Snapshot:** added (absent from baseline); 15 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for shared security observations.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Parse complete certificate blocks with exact one-based malformed-block records, plus explicit strict marker validation; preserve production complete-block acceptance and comments without retaining content/native errors or claiming CA role, lifetime or peer trust.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `contentRecord`, `result`.

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/core/security`, `../src/index`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=198ce55865cfb6572f0914e867593ff647dc9b3cac7e35eef9c7c8e90230879e -->

<!-- course-file: platform/security/tests/security-operation-diagnostics-runtime.test.ts -->

### security-operation-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/security/tests/security-operation-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 237 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for shared security observations.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed reason-specific certificate, peer, header, token, signing-key, authorization, policy and limiter definitions; required safe locations, copied validated extraction, invocation-local private evidence retention, phase-safe public types and immutable prior definitions. Additive shared-security configuration-predicate records identify exact limiter fields and observed numeric/empty alternatives without widening historical identities.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `publicJwk`, `clock`, `baseClaims`, `segment`, `token`, `verifier`, `reason`, `invalid`, `main`, `rateLimitClockObservations`.

Added import edges: `node:assert/strict`, `node:crypto`, `@kanbien/core/authz`, `@kanbien/core/shared`, `@kanbien/core/security`, `@kanbien/core/diagnostics`, `../src/index`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=56402af826f0a14beafd549f17104018637ec06d4dd35348166b107b3a6a6467 -->

<!-- course-file: platform/security/tests/security-operation-diagnostics-types.test.ts -->

### security-operation-diagnostics-types.test.ts

[Open current source](../../../../../platform/security/tests/security-operation-diagnostics-types.test.ts) · **Snapshot:** added (absent from baseline); 23 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for shared security observations.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Closed reason-specific certificate, peer, header, token, signing-key, authorization, policy and limiter definitions; required safe locations, copied validated extraction, invocation-local private evidence retention, phase-safe public types and immutable prior definitions. Additive shared-security configuration-predicate records identify exact limiter fields and observed numeric/empty alternatives without widening historical identities.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `compileOnly`.

Added import edges: `../src/index`.

Owning registered proof: `platform-security-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=8d167037ab824f2e0078c98ea05cd0a8ad5d949e5ef9789dafc4abc2046783e8 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why does certificate parsing success not prove that a remote server is trustworthy?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Sessions, cookies, CSRF, broader secret lifecycle and additional tenant controls remain separately planned, not silently implemented. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/security/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L053 platform/security](053-platform-security.md) · [L054 platform/security/contracts](054-platform-security-contracts.md) · [L055 platform/security/src](055-platform-security-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 8 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
