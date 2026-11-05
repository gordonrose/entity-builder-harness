<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l028
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/runtime/ecs-fargate/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L028 — platform/adapters/aws/runtime/ecs-fargate/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/runtime/ecs-fargate/src -->

## What you will understand

Runtime mounts apps into a registry, builds request/job contexts and coordinates startup and shutdown.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

The second app fails during mount after the first registered successfully. Report the actual boundary using available selected catalogs; do not pretend that no registration happened or rerun the first app for diagnostics.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Mounting and lifecycle already existed. A thrown app callback, invalid registration and shutdown failure could become one generic failure without retaining the stage reached.

**After:** Optional observers identify registry/state/context/lifecycle boundaries, retain selected catalogs and preserve source evidence. Existing app order and original errors remain the compatibility boundary.

**Why this was needed:** An agent needs to know whether failure occurred while declaring a route, constructing a context, starting work or shutting down. These imply different affected components.

This directory contains `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/runtime/ecs-fargate/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/adapters/aws/runtime/ecs-fargate/src/index.ts) · **Snapshot:** modified existing file; 28 added / 8 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports application mounting and lifecycle at this layer.

**Before:** Mounting and lifecycle already existed. A thrown app callback, invalid registration and shutdown failure could become one generic failure without retaining the stage reached. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `createAlbTrustedClientAddressResolver`, `finalValidForwardedAddress` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Server owns trust rejection/fallback meanings; ECS translates only the actual configured-mode predicate and final-forwarded-address/fallback selection. Original RangeError text/class, result, header/peer/trim/isIP read order and fallback behavior remain.

**Why:** An agent needs to know whether failure occurred while declaring a route, constructing a context, starting work or shutting down. These imply different affected components.

Changed declaration anchors: `createAlbTrustedClientAddressResolver`, `finalValidForwardedAddress`.

Owning registered proof: `ecs-fargate-runtime`, `platform-server-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=7e737254ee7c1a665f44c3fa96a8c50b44b4a44c83b87260d9420a309481f26a after=6b49a26710f4428c1731707302d4d1738ffa35e032cb19f35e6403bd4e6ebd5e -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What state is known when mount fails after an earlier app has registered routes?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** A reported shutdown deadline is an observation, not proof that work was cancelled or cleanup completed. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/runtime/ecs-fargate/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L027 platform/adapters/aws/runtime/ecs-fargate](027-aws-runtime-ecs-fargate.md) · [L029 platform/adapters/aws/runtime/ecs-fargate/tests](029-runtime-ecs-fargate-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
