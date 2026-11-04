<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l038
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/server/contracts.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L038 — platform/server/contracts

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/server/contracts -->

## What you will understand

The server resolves configuration, starts a listener, admits transport requests, creates context, authenticates/authorizes, invokes handlers and writes responses.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Send a body that fails the existing decode boundary, then contrast a valid body whose handler throws. Keep the established public response, but give the internal agent distinct evidence for each observed stage.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The HTTP path already existed. Several fallback choices, rejected inputs and thrown transport/request boundaries were observable only as broad failures.

**After:** Closed records identify listener/port/health choices, transport predicates, decode/context/handler boundaries, writer/drain/close failures and process stages. Selected upstream evidence travels internally without entering response metadata.

**Why this was needed:** A fallback port is not a listener failure; a handler exception is not invalid JSON; a response-write failure does not prove that the handler never ran.

This directory contains `catalog` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/server/contracts/diagnostics.v1.json -->

### diagnostics.v1.json

[Open current source](../../../../../platform/server/contracts/diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 852 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected http transport and request handling contract for non-TypeScript readers, including 16 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `platform-server.operation-failed` v1, `platform-server.listener-configuration-selected` v1, `platform-server.port-configuration-fallback` v1, `platform-server.health-exposure-selected` v1, `platform-server.health-exposure-fallback` v1; 11 more definitions are in the export.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=3daad86145aa766c4f62818a62ecf9b76300da69bc1ba8c120ef883c7adac9b8 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: If response writing fails after a handler committed a change, why must diagnostic handling not replay the handler?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new HTTP routes, authentication policy or public error-detail expansion is implied. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/server/contracts) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L037 platform/server](037-platform-server.md) · [L039 platform/server/src](039-platform-server-src.md) · [L042 platform/server/tests](042-platform-server-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
