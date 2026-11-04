<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l009
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/config/contracts.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L009 — platform/config/contracts

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/config/contracts -->

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

This directory contains `catalog` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/config/contracts/diagnostics.v1.json -->

### diagnostics.v1.json

[Open current source](../../../../../platform/config/contracts/diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 111 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected configuration: tell absence from invalidity contract for non-TypeScript readers, including 3 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `platform-config.schema-rejected` v1, `platform-config.schema-rejected` v2, `platform-config.schema-boundary-threw` v1.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=a5e67c5f7eefb524e119242b023e09463628131d0eb7cb818213c868c68e866f -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which fact distinguishes a missing setting from a getter that threw before the setting could be read?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Do not expose hostnames, usernames, passwords, source contents or rejected values. The issue collector has a bound; overflow must not be called complete. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/config/contracts) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L008 platform/config](008-platform-config.md) · [L010 platform/config/src](010-platform-config-src.md) · [L011 platform/config/tests](011-platform-config-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
