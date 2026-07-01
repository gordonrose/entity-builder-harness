<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.lesson-plans.0001-the-next-ai-advantage-is-evidence
  version: 1
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: 'Document Lesson Plan: The Next AI Advantage Is Evidence.'
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Lesson Plan: The Next AI Advantage Is Evidence

## Metadata

- Title: The Next AI Advantage Is Evidence
- Audience: hype-adjacent, non-technical or lightly technical AI-curious
  professionals; adaptable for students or technical teams
- Primary duration: 30 minutes
- Extension duration: 50 minutes
- Format: facilitated lesson, workshop segment, or executive learning session
- Prerequisite knowledge: basic familiarity with AI tools and current AI
  vocabulary; no coding knowledge required
- Source material:
  - `commitLogs/2026/jun/15/2026-06-15-21-27-i-d-like-to-update-my-harness-so-that-whenever-i-commit-some/README.md`
  - `docs/harness/architecture/adrs/0001-record-harness-session-decisions-before-commit.md`
- Profiles used:
  - `.agentic/education/profiles/audience-profile.md`
  - `.agentic/education/profiles/voice-profile.md`
  - `.agentic/education/profiles/structure-profile.md`
- References used:
  - `.agentic/education/references/teaching-principles.md`
  - `.agentic/education/references/writing-style-principles.md`

## Lesson Promise

After 30 minutes, learners will understand why AI-assisted work becomes more
useful when people can come back later and see why a recommendation or decision
happened, not just what output was produced.

The 50-minute version adds practice applying the same pattern to a workplace AI
workflow: what to log, what to automate, and what to leave as human judgment.

## Learning Outcomes

By the end of the 30-minute core, learners can:

- explain the difference between AI fluency and AI orientation
- name the evidence an AI system needs before making a recommendation or
  judgment
- improve a thin record into a useful evidence record

With the 50-minute extension, learners can also:

- apply the evidence-before-judgment pattern to a familiar workflow
- separate deterministic checks, useful logs, and human decisions

## Audience Fit

- Primary reader/learner served: people who follow AI closely and like to feel
  current, but may not yet have a concrete model for how trustworthy AI work is
  structured.
- Secondary learner preserved: thoughtful underconfident learners who suspect
  there is more going on under the surface and want a non-patronizing way in.
- How the lesson makes learners feel upgraded rather than exposed: it frames
  evidence as the next layer of sophistication, not as a correction for being
  wrong.
- Where technical reality is preserved without patronizing: the lesson uses a
  real decision-check failure mode, but translates the repo mechanics into
  plain language before naming them.
- What would make the lesson too beginner, too accusatory, or too fluffy:
  explaining basic AI vocabulary at length, saying "people do not understand
  AI", or using vague claims about the future without the harness incident.

## Source Evidence

- The June 15 session identified that a decision check could not stand alone
  because the work record did not preserve enough activity for the check to
  inspect.
- The harness added structured session-record sections: questions, issues,
  decisions, activity, summaries, final explanation status, and metrics.
- ADR 0001 records the repo-specific architecture decision behind that change.

## Lesson Arc

1. Hook: AI-assisted work can feel fine until someone who was not there asks
   why it says what it says.
2. Source story: A decision check exposed that the record had preserved the
   outer shape of the work but not the substance.
3. Core concept: AI judgment needs an evidence record.
4. Worked example: Thin work record versus useful evidence record.
5. Participant activity: Design the minimum evidence record for an AI decision.
6. Debrief: Sort evidence into logs, deterministic checks, and human judgment.
7. Landing: Confidence is better when it comes with a trace.

## 30-Minute Core Plan

| Time | Segment | Facilitator move | Learner action | Materials |
|---|---|---|---|---|
| 0:00-3:00 | Hook | Start with the human stake: AI-assisted work can look fine until someone who was not there asks why it says what it says. Ask learners where AI-assisted decisions become hard to explain later. | Name a moment where an AI output looked useful but the basis was unclear. | Slide or board with hook question |
| 3:00-8:00 | Source story | Tell the harness story in plain language: the decision check sounded sensible, but the existing record only proved that a work session existed. | Listen for the distinction between output and evidence. | Thin record excerpt |
| 8:00-13:00 | Core concept | Introduce the frame: fluency is producing the right-looking words; orientation is knowing what the system knew and why it acted. | Name one AI decision they would want evidence for. | Concept slide: fluency, judgment, trace |
| 13:00-20:00 | Worked example | Compare the thin record and improved record. Mark which fields make judgment possible. | Identify missing evidence and useful additions. | Worked example table |
| 20:00-27:00 | Participant activity | Ask learners to design a minimum evidence record for an AI assistant deciding whether a change needs review. | Fill in a small evidence table individually or in pairs. | Worksheet |
| 27:00-30:00 | Debrief and landing | Pull out two examples. Land the point: evidence is not admin; it is trust infrastructure. | Share one field they added and why. | Final takeaway slide |

## 50-Minute Extension

| Time | Segment | Facilitator move | Learner action | Materials |
|---|---|---|---|---|
| 30:00-38:00 | Deeper discussion | Ask learners to sort evidence fields into three buckets: log it, automate it, or leave it to human judgment. | Debate where each field belongs. | Bucket table |
| 38:00-45:00 | Application | Ask learners to choose a real AI workflow: sales summary, hiring screen, research brief, support triage, board report. | Draft a minimum evidence record for that workflow. | Blank workflow worksheet |
| 45:00-50:00 | Share and refine | Invite one example and refine it live. Keep the tone practical, not corrective. | Improve the example with one missing evidence field. | Board or shared document |

## Facilitator Script

### Hook

Say:

> AI work often looks good in the first conversation. The summary is clean, the
> recommendation is plausible, and everyone is relieved not to be starting from
> a blank page. The harder moment comes later, when someone has to explain what
> the answer was based on and why the decision made sense at the time.

Show the hook question:

> Where does AI-assisted work become hard to reconstruct later?

Ask learners for quick answers. Listen for: source, context, assumptions,
review, data, objective, tradeoff, who asked, what changed, and why the decision
mattered.

Catch this misconception:

> A confident answer is not the same thing as a well-supported answer.

### Source Story

Say:

> In my harness, I wanted an AI assistant to notice when a change needed a short
> explanation for future-me. That sounds like a responsible thing to ask. But
> the record was too thin. It knew a session started. It did not know enough
> about the questions, decisions, or tradeoffs to judge responsibly.

Show the thin record excerpt.

Ask:

> If this is all the system has, what can it responsibly conclude?

Expected answer: almost nothing beyond "a session happened."

### Core Concept

Say:

> The upgrade was not just adding a better check. The upgrade was giving the
> system somewhere to put the evidence before asking it to judge.

Show:

| Word | What it means here |
|---|---|
| Fluency | The system can produce the right-looking answer. |
| Judgment | The system is asked to decide or recommend. |
| Trace | A human can inspect what the system knew and why it acted. |

### Worked Example

Say:

> Here is the same situation in two forms. One sounds orderly. The other is
> actually useful.

Walk through the table in the worked example section.

Ask:

> Which field first makes the decision possible?

Good answers include: decisions made, issues raised, rationale, affected area,
and final explanation status.

### Activity

Say:

> You are not trying to log everything. You are trying to preserve enough for a
> future person, or future system, to understand the judgment.

Timebox seven minutes. Keep learners focused on minimum viable evidence.

### Debrief

Say:

> The aim is not paperwork. It is making confidence inspectable.

Ask:

> Which one field would you refuse to remove?

Land:

> Confidence is more useful when it comes with a trace.

## Materials

### Thin Example

```text
Session started.
Working copy created.
Change list initialized.
Final note: update decision check.
```

### Improved Example

```text
Initial intent:
Add a check for whether important decisions need a short explanation for
future review.

Question:
How should the system know whether an explanation is needed?

Issue:
The current work record is too thin to support the decision.

Decision:
Record questions, issues, decisions, summaries, and final explanation status
before the work is finished.

Rationale:
The check needs evidence from the session, not transient chat memory.

Summary:
Added a better session record and a check before finishing the work.

Explanation status:
Explanation needed: yes.
Path: docs/harness/architecture/adrs/0001-record-harness-session-decisions-before-commit.md
```

### Worksheet

| Decision the AI must make | Evidence needed | Where should it live? | Automate, log, or human judgment? |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

### Discussion Prompts

- What is the smallest useful evidence record?
- What would be annoying to log but dangerous to lose?
- Which parts can be checked by a script?
- Which parts require human judgment?
- What would make this feel like bureaucracy rather than trust?

### Optional Slide Outline

1. The next AI advantage is evidence.
2. The work looked complete, but the reason was missing.
3. Fluency, judgment, trace.
4. Thin record versus useful evidence record.
5. Activity: design the minimum evidence record.
6. Landing: confidence is better when it comes with a trace.

## Participant Activity

- Prompt: An AI assistant must decide whether a project change needs an
  explanation for future review. Design the minimum evidence record that would
  let it make that decision responsibly.
- Individual, pair, or group format: pairs for 30-minute version; small groups
  for 50-minute version.
- Timebox: 7 minutes in the core lesson; 12 minutes in the extension.
- Expected output: a filled evidence table with 5-7 fields.
- Debrief question: Which field makes the decision responsible rather than just
  confident?

## Worked Example

### Pass 1: Thin But Tidy

```text
Session started.
Working copy created.
Change list initialized.
```

This is orderly, but it does not tell the system what was decided, what went
wrong, or why the decision matters.

### Pass 2: Useful Evidence

```text
Issue:
The original explanation-check plan assumed the session record contained enough
evidence.

Resolution:
Add structured session sections before relying on the decision check.

Decision:
Use structured session records as the evidence base for deciding whether an
explanation is needed.

Rationale:
The decision requires summarized questions, issues, decisions, and intent
rather than a thin startup record.
```

What changed:

- the record now names the failure mode
- the decision is explicit
- the rationale is inspectable
- a future person or system can challenge the judgment

## Debrief Guide

- Expected answers: intent, source material, decision, rationale, affected
  system, risk, human approval, final disposition.
- Strong answers: distinguish between evidence the system can verify and
  judgment a human must own.
- Common wrong turns: logging everything, writing vague summaries, treating the
  AI output itself as evidence, or assuming confidence means context exists.
- How to respond without embarrassing learners: say "that is useful, but what
  would a future reviewer need that is not there yet?"
- Final takeaway: evidence is not the opposite of speed; it is what lets useful
  work survive the moment someone asks why it happened.

## Adaptation Notes

- For non-technical professional audiences: keep the harness story brief and
  translate quickly to familiar workflows such as AI-generated reports,
  recommendations, summaries, or triage.
- For students: spend more time on the thin-versus-useful log comparison.
- For technical practitioners: add a short discussion of deterministic gates,
  commit hooks, and where logs become testable artifacts.
- For executive briefings: focus on governance without bureaucracy: what must
  be visible for AI-assisted work to be trusted?

## Audits

### Specificity Audit

- Which concrete evidence supports the lesson? The June 15 session log and ADR
  0001 show that the decision check required structured session evidence.
- Could this have been written without reading the source logs? Not in this
  form; the thin-log failure mode comes directly from the harness work.
- Is there a real incident, tradeoff, mistake, or surprise? Yes: the system was
  asked to make a responsible judgment before the evidence structure existed.

### Audience Audit

- Does the lesson make learners feel upgraded rather than exposed? Yes. It
  frames evidence as the next layer of AI maturity.
- Is the surface tone positive and opportunity-facing? Yes. The core frame is
  advantage and orientation.
- Is critique present as subtext, contrast, implication, or upgrade path? Yes.
  The lesson critiques shallow fluency without accusing the learner directly.

### Teaching Audit

- What will learners understand afterward? AI-assisted work is more useful when
  people can inspect why a decision happened, not just admire the output.
- Does the 30-minute core stand alone? Yes: hook, story, concept, worked
  example, activity, debrief.
- Does the 50-minute extension deepen rather than distract? Yes: it applies the
  same pattern to learner workflows.
- Is there one main idea at a time? Yes: evidence before judgment.
- Is there a worked example before abstraction? Yes.
- Is there a retrieval, prediction, or practice moment? Yes: the hook question,
  evidence design activity, and debrief.

### AI-Smell Audit

- Are positive claims anchored in concrete evidence? Yes.
- Are significance inflation, vague authority, and promotional phrasing
  removed? Yes.
- Does specificity earn the lift? Yes: the broader AI point grows from the
  session-log failure mode.
