<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l049
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/auth/cognito/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L049 — platform/adapters/aws/auth/cognito/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/auth/cognito/tests -->

## What you will understand

Security owns reusable meanings for trust material, TLS, tokens, claims, permissions, headers/CORS and rate-limiter checks. CORS is the browser cross-origin response policy.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

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

<!-- course-file: platform/adapters/aws/auth/cognito/tests/cognito-adapter-runtime.test.ts -->

### cognito-adapter-runtime.test.ts

[Open current source](../../../../../platform/adapters/aws/auth/cognito/tests/cognito-adapter-runtime.test.ts) · **Snapshot:** modified existing file; 42 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for shared security observations.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Preserve provider-neutral authentication observations; distinguish absent/empty settings, JSON/container/entry failures, exact missing or wrong-type mapping attributes and permission item index without exposing configured values.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Owning registered proof: `diagnostic-catalog-readers`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`, `deployment-operation-diagnostics-regression`, `shell-package-source`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b87b563bedb80c2d685b232dd3fcdc0dbc03e49800726ffe1ef0ae4f7f1fc50e after=c310a82f1174562488dec46ff770fc006f63f0dd1d68cfa756acc1f0a4c6e6dd -->

<!-- course-file: platform/adapters/aws/auth/cognito/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/adapters/aws/auth/cognito/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=fa3aa27f00e01ab46f963a8175d81e52ac1a8f3a0c83e5c5ffd6a477bdfc5a80 after=c3f7ace1d56521bdca6579fd1ba7d7d5a8932ae25c6e398092f1808c68ca3f0e -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why does certificate parsing success not prove that a remote server is trustworthy?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Sessions, cookies, CSRF, broader secret lifecycle and additional tenant controls remain separately planned, not silently implemented. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/auth/cognito/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L048 platform/adapters/aws/auth/cognito/src](048-auth-cognito-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
