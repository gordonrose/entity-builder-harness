<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.profiles.structure-profile
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Structure Profile.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Structure Profile

## Short Public Articles

Default shape for a short public article:

1. Source scene with felt stakes
2. Reader-world bridge
3. Nut graf that names the angle
4. Source story and complication
5. Practical meaning
6. Return, image, or changed understanding

The structure is blocked if it needs an invented hypothetical to make the
reader care. Source packet and scene cards come before drafting.

## Public Technical Explainers

Use this shape when a public article teaches a technical or harness concept to
AI-curious readers who may not know the underlying software process.

Default shape:

1. Reader desire
2. Hidden cost or accountability pressure
3. Public examples that make the cost recognizable
4. Author-owned concrete version of the same problem
5. Plain-language model or analogy
6. What does not transfer from that model
7. Harness mechanism that creates the missing condition
8. Practical payoff

This shape should still use source evidence, but it may open from the reader's
desire before the source scene when that helps orientation. Block the draft if
the technical analogy has no prerequisite ladder or if the article jumps from
the analogy to the harness without explaining what does not transfer.

## Talks

Default shape for a 30-minute talk:

- 0:00-3:00 opening
- 3:00-8:00 setup/context
- 8:00-15:00 main concept 1
- 15:00-22:00 main concept 2
- 22:00-27:00 synthesis/application
- 27:00-30:00 landing/Q&A bridge

## Teaching Assets

Prefer classroom-ready forms:

- 30-minute lesson plans with 50-minute extension paths
- worked examples
- debugging exercises
- spot-the-mistake prompts
- discussion questions
- whiteboard diagrams
- mini case studies

## Lesson Plans

Default lesson plans use a complete 30-minute core with an optional 50-minute
extension.

The 30-minute core must stand alone:

- 0:00-3:00 hook
- 3:00-8:00 source story
- 8:00-13:00 core concept
- 13:00-20:00 worked example
- 20:00-27:00 participant activity
- 27:00-30:00 debrief and landing

The 50-minute extension adds 20 minutes:

- 30:00-38:00 deeper discussion
- 38:00-45:00 application to learner context
- 45:00-50:00 share, refine, and land

The extension should deepen practice, discussion, or application. It should not
introduce a different lesson.

A strong lesson plan includes:

- one teachable transformation
- one concrete source story
- one worked example before abstraction
- one participant activity
- facilitator notes
- expected answers and common wrong turns
- a landing that makes learners feel more oriented, not exposed

## Current Calibration Notes

- Mine before drafting.
- Draft only selected candidates unless the user asks for a one-shot run.
