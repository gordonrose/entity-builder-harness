<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.notes
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Record learner questions and progress without silently skipping files.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# Our learning notes

[Course start](README.md)

No lessons have been taught or signed off merely by creating this course. Begin with lesson zero and wait for your direction before moving on.

## Next meeting

- Start: Sunday, 1 November 2026; exact time to be chosen by you.
- First topic: why the combined configuration guard lost useful information.
- Pace: one step at a time, explain jargon when needed, stop for questions.
- Evidence rule: inspect the actual guard/call and assertion before making a precise claim.

## Questions and explanations

| Lesson / file | Your question | Explanation we agreed | Source / uncertainty | Revisit? |
| --- | --- | --- | --- | --- |

Add rows during the walkthrough. If an annotation disagrees with the current source, record the exact symbol and source identity; do not quietly mark it understood.

## Progress

The [file checklist](file-index.md) is authoritative for individual file coverage. The [folder index](folder-index.md) is a convenient overview. Mark a folder covered only after every listed file and its explain-back question are covered.

## Course corrections, not implementation authority

This learning exercise does not reopen the diagnostics goal, authorize deployment or start deferred security/telemetry/LLM work. Record implementation questions here; we can decide separately whether they warrant a bounded task.

## Preparation record — 31 October 2026

The course was built from the frozen Git/source inventory and existing owner reviews, with authored ownership explanations and a worked core-server example. Source readback refined the distinction between a single file's behavior and a review spanning several connected files; in particular, a migration file must not be described as owning the HTTP readiness route.

The first documentation validation found trailing whitespace in four generated paragraphs across three lessons; those were corrected in the course only. The passing validation accounted for all **584 paths exactly once in their 187 correct folder lessons**, resolved **4,667 local links**, and passed the existing metadata validator for **196 documents** (195 new course files plus the existing education index). Every original diagnostic-project source hash and the original path inventory remained unchanged.

Readback included the foundation, telemetry, target and operational-declaration lessons. Coverage/link/metadata checks are mechanical; they do not certify that every prose explanation is infallible. During teaching, use the linked source and record any discrepancy. No runtime, container or deployment suite was rerun for this documentation-only task.
