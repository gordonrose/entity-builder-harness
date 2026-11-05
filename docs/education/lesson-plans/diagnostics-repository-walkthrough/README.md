<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.readme
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the complete folder and file scope of the diagnostic adoption project.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.lesson-plans.readme
    path: docs/education/lesson-plans/README.md
-->

# What changed in the repo: a diagnostics course

Prepared on 31 October 2026 for our walkthrough starting **Sunday, 1 November**. This course is for you as the repo owner: you should be able to explain what the code does, why these changes belong where they do, and what an agent can safely conclude when something fails. No prior familiarity with the diagnostics implementation is assumed.

The course covers **584 changed file paths in 187 directly containing folders**: **408 existing files modified and 176 files added**, compared with Git baseline `d94da2b9401d3abcf86618b5d497e9b93903490a` in the recorded October 27 worktree. There are no deleted paths in this snapshot. Every folder has a lesson and every file has a before/after/why entry. Tests, setup, exports, tooling, packaging, policies and history are included—not only the TypeScript runtime.

This is a new education resource, not a restart of the completed implementation goal. Runtime and deployment code are not changed by preparing it. The existing deployment and LLM follow-up deferrals still apply.

## Begin here tomorrow

Say: **“Start the diagnostics course, lesson zero. One step at a time; wait for me before moving on.”**

We will open [Lesson zero: follow one failure](00-follow-one-failure.md) first. It starts with your original combined configuration guard, not a taxonomy or a tour of hundreds of filenames. You will see how a precise, value-safe observation makes its way from a real check to a reader.

We will then use the route below, opening the corresponding folder lessons as we reach them. The route is a sequence, not a promise to finish 187 deep lessons in one day. You decide the pace; unanswered questions stay visible.

| Order | Question we answer | Where we look |
| --- | --- | --- |
| 1 | What was wrong with returning undefined, and what can we safely report instead? | [Worked vertical example](00-follow-one-failure.md) |
| 2 | Who defines a diagnostic, and why does the harness not own its runtime meaning? | [L004: packages/core/src/diagnostics](lessons/004-core-src-diagnostics.md) and [L007: packages/core/src/config](lessons/007-core-src-config.md) |
| 3 | Who supplies the real target settings and PostgreSQL evidence? | [L089: infra/04.deploy/03.product/entrypoints](lessons/089-04-deploy-03-product-entrypoints.md) and [L064: platform/adapters/aws/persistence/postgresql/src](lessons/064-persistence-postgresql-src.md) |
| 4 | How does a record reach an agent without breaking work or leaking data? | [L079: platform/observability/src](lessons/079-platform-observability-src.md) and [L153: scripts/04.deploy/shared](lessons/153-scripts-04-deploy-shared.md) |
| 5 | Why do certificates belong to Security, and why are health responses limited? | [L055: platform/security/src](lessons/055-platform-security-src.md) and [L045: platform/health/src](lessons/045-platform-health-src.md) |
| 6 | What did the HTTP, lifecycle and worker changes actually add? | [L039: platform/server/src](lessons/039-platform-server-src.md), [L032: platform/runtime/src](lessons/032-platform-runtime-src.md) and [L072: platform/workers/src](lessons/072-platform-workers-src.md) |
| 7 | How did we check the compiled/image boundary and preserve verification quality? | [L093: infra/04.deploy/03.product/image/core-server-persistence](lessons/093-03-product-image-core-server-persistence.md), [L170: scripts/repo/check-selection](lessons/170-scripts-repo-check-selection.md) and [L167: scripts/repo/diagnostic-coverage](lessons/167-scripts-repo-diagnostic-coverage.md) |
| 8 | What else changed, folder by folder, and what remains deferred? | [Complete curriculum](folder-index.md) and [Evidence and limits](sources-and-limits.md) |

An initial two-hour meeting can cover the worked example and the ownership model with breaks. Do not mark untouched folder lessons complete to fit that timebox. The complete reference remains available for the slower file-by-file walkthrough you asked for.

## How to use the full course

- [Folder curriculum](folder-index.md): all 187 lessons, grouped by responsibility rather than by the order files happened to be edited.
- [Every-file checklist](file-index.md): all 584 original changed paths, each linked to its folder lesson and current source. Check a file only after we discuss it.
- [Teaching guide](facilitator-guide.md): lesson pacing, source comparison, exercises, answer criteria and how to record a disagreement.
- [Glossary](glossary.md): terms translated into plain language.
- [Sources and proof limits](sources-and-limits.md): baseline, exact scope, local proof and what has not been proved or implemented.
- [Learning notes](learning-notes.md): our questions, answers and progress.

## The architecture in one view

| Layer | Owns | Must not pretend to own |
| --- | --- | --- |
| Core capability | Reusable meaning, allowed detail and primitive facts | Environment variable names, AWS behavior, concrete server wiring |
| Platform capability/contracts | Orchestration, shared interfaces, selection and safe delivery | App business meaning or fabricated native evidence |
| Adapter | The actual database/provider call and supported machine evidence | Cross-cutting security meaning or guessed causes from prose |
| App/target composition | Feature meaning, concrete settings, selected catalogs and reporter wiring | A second generic diagnostic vocabulary |
| Operational reader | Checked task/receipt observations and next permitted action | Success from incomplete evidence, or authority to replay mutations |
| Harness and checks | Ownership, workflow, drift detection, compatibility and proof | Runtime truth solely because a review label or instruction says so |

The central rule is simple: **report what the code actually observed, at the owner that understands it, using allowed facts only; preserve uncertainty and the original outcome.**

## What the course does not claim

We already had observability, metrics, security mechanisms and persistence before this project. Adding a diagnostic module is not evidence those features were absent or rebuilt. “Locally complete under the amended scope” is not “every possible future diagnostic exists.” Live deployment checks and recorded LLM-tooling follow-up are still separate work. The lessons keep those limits explicit.
