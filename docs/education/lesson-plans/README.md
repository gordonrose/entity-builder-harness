<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.lesson-plans.readme
  version: 2
  status: active
  created_on: "2026-06-16"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Education Lesson Plans.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Education Lesson Plans

Lesson plans are facilitator-ready teaching resources derived from repo work.

Use this directory for lessons with a timed teaching arc, worked examples,
participant activities, and debrief guidance. The default shape is a complete
30-minute core with a 50-minute extension path.

Use `docs/education/teaching-notes/` for smaller reusable notes that are not
yet complete lesson plans.

## Repository courses

- [Diagnostics repository walkthrough](diagnostics-repository-walkthrough/README.md):
  a source-backed course covering every changed folder and file in the diagnostic
  adoption project, with before/after explanations and a guided starting lesson.
