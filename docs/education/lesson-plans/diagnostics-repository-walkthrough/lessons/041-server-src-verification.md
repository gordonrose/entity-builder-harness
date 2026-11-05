<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l041
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/server/src/verification.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L041 — platform/server/src/verification

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/server/src/verification -->

## What you will understand

The server resolves configuration, starts a listener, admits transport requests, creates context, authenticates/authorizes, invokes handlers and writes responses.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Send a body that fails the existing decode boundary, then contrast a valid body whose handler throws. Keep the established public response, but give the internal agent distinct evidence for each observed stage.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The HTTP path already existed. Several fallback choices, rejected inputs and thrown transport/request boundaries were observable only as broad failures.

**After:** Closed records identify listener/port/health choices, transport predicates, decode/context/handler boundaries, writer/drain/close failures and process stages. Selected upstream evidence travels internally without entering response metadata.

**Why this was needed:** A fallback port is not a listener failure; a handler exception is not invalid JSON; a response-write failure does not prove that the handler never ran.

This directory contains `documentation`, `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/server/src/verification/README.md -->

### README.md

[Open current source](../../../../../platform/server/src/verification/README.md) · **Snapshot:** modified existing file; 6 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for http transport and request handling; read the sections `Server Verification Source Map`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Server Verification Source Map`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=916fd0594a4671a22888b19f4d012d74bf64d060d288a1cf0cd6939196005ef5 after=edaaf624f2a776ef7e25443317342f793966ea787b1282eaa8636a7def03f771 -->

<!-- course-file: platform/server/src/verification/release.ts -->

### release.ts

[Open current source](../../../../../platform/server/src/verification/release.ts) · **Snapshot:** modified existing file; 6 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports http transport and request handling at this layer.

**Before:** The HTTP path already existed. Several fallback choices, rejected inputs and thrown transport/request boundaries were observable only as broad failures. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `resolvePlatformReleaseIdentity` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): One shared resolver explains host/port and health exposure choices with closed bounded records; preserves original API, Number conversion, programmatic overrides including port zero, defaults and HTTP behavior. Exact reasons, independent choices and safe delivery are tested.

**Why:** A fallback port is not a listener failure; a handler exception is not invalid JSON; a response-write failure does not prove that the handler never ran.

Changed declaration anchors: `resolvePlatformReleaseIdentity`.

Added import edges: `@kanbien/core/diagnostics`, `../diagnostics`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`, `core-dependency-boundary`, `persistence-composition`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=81e1506e540477fd37461b794a3e1217fb8f55b7e49493007271f5ed302ab82d after=24d589b5fbe07f1448900e64722da55682b3c9da6b0fcaad219178a7bbb93fc6 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: If response writing fails after a handler committed a change, why must diagnostic handling not replay the handler?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new HTTP routes, authentication policy or public error-detail expansion is implied. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/server/src/verification) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L039 platform/server/src](039-platform-server-src.md) · [L040 platform/server/src/configuration](040-server-src-configuration.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
