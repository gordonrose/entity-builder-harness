<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l008
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/config.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L008 — platform/config

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/config -->

## What you will understand

Configuration code turns supplied settings into values the workload can use. A setting is a logical requirement; its environment-variable name belongs to the caller that binds it.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Start with the original combined host/database/schema/reference/port guard. If port is absent and host is present, the useful observation is the port requirement being missing—not a guessed connection failure. If reading the source throws before a value is obtained, wrong-type would be an unsupported claim.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing readers rejected missing or malformed values, but several callers collapsed alternatives into undefined or one broad configuration error.

**After:** Reusable readers retain safe setting references, exact observed reasons, source-read failures, indexed issues and explicitly declared relationships. Target bindings supply exact source names privately, without placing submitted values in diagnostic detail.

**Why this was needed:** An agent needs to know which requirement failed and whether to fix a declaration, provide a setting, or investigate an unreadable source. One broad rejection cannot support that decision.

This directory contains `documentation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/config/README.md -->

### README.md

[Open current source](../../../../../platform/config/README.md) · **Snapshot:** added (absent from baseline); 25 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** This dedicated document was absent at the baseline.

**After:** Explains the diagnostic responsibilities and compatibility limits for configuration: tell absence from invalidity; read the sections `Platform configuration`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform configuration`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=absent after=7772c06afa96f2c8d60abf849838d970e33878ca95b3ba21fc01d7804ebfdee5 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which fact distinguishes a missing setting from a getter that threw before the setting could be read?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Do not expose hostnames, usernames, passwords, source contents or rejected values. The issue collector has a bound; overflow must not be called complete. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/config) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L009 platform/config/contracts](009-platform-config-contracts.md) · [L010 platform/config/src](010-platform-config-src.md) · [L011 platform/config/tests](011-platform-config-tests.md) · [L023 platform/contracts](023-platform-contracts.md) · [L030 platform/runtime](030-platform-runtime.md) · [L034 platform/testing](034-platform-testing.md) · [L037 platform/server](037-platform-server.md) · [L043 platform/health](043-platform-health.md) · [L053 platform/security](053-platform-security.md) · [L058 platform/persistence](058-platform-persistence.md) · [L070 platform/workers](070-platform-workers.md) · [L077 platform/observability](077-platform-observability.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
