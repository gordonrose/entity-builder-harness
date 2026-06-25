<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0001-the-next-ai-advantage-is-evidence.source-packet
  version: 1
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Article Source Packet.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Article Source Packet

## Metadata

- Working title: The Answer Has To Stand Up
- Source window: June 15 harness sessions plus reader-world research gathered
  on 2026-06-16
- Source logs or artifacts:
  - `reader-world-research-packet.md`
  - `commitLogs/2026/jun/15/2026-06-15-21-27-i-d-like-to-update-my-harness-so-that-whenever-i-commit-some/README.md`
  - `commitLogs/2026/jun/15/2026-06-15-23-18-i-d-like-to-update-the-harness-so-that-the-chat-duration-is-/README.md`
  - `docs/harness/architecture/adrs/0001-record-harness-session-decisions-before-commit.md`
  - `docs/harness/architecture/adrs/0004-group-chat-logs-and-summarize-session-metrics.md`
- Reader-world research packet: `reader-world-research-packet.md`
- Requested audience: hype-adjacent, non-technical or lightly technical AI
  readers
- Reporter: Codex
- Status: sufficient

## Core Incident

The author wanted the harness to check, before a piece of work was finished,
whether any decisions from the chat deserved to be saved as durable decision
notes.

The attempt exposed a missing layer. The session record showed that work had
started, a branch existed, and a session note existed. It did not reliably
preserve enough of the questions, issues, decisions, rejected options, and
rationale to support a judgment about whether a durable note was needed.

The work changed from "ask the assistant to judge decisions" to "make the work
leave enough evidence for judgment." A later harness pass grouped sessions by
date and added readable duration and token summaries so chats could become an
inspectable body of work.

## Human Protagonist

- Who wanted something? The author, working with an AI assistant.
- What did they want? To make AI-assisted work preserve decisions that would
  matter later.
- What pressure were they under? A responsible-looking assistant judgment from
  a thin record would create false confidence.
- What would failure cost? Future work would look documented while still
  forcing the author to reconstruct why a decision happened.

## Exact Moment

The revealing moment was the plan revision captured in the first June 15 log:

- Issue: "The original plan assumed ADR checks could stand alone, but chat logs
  were not recording enough activity."
- Resolution: "Revised the plan so structured session finalization provides
  evidence for the ADR disposition."

The author expected a decision-recording rule. The real problem was the record
underneath the rule.

## Visible Artifacts

- A polished public AI report whose citations and case studies did not hold
  up, now referenced through reporting because the original no longer appears
  publicly available from KPMG.
- A customer-service chatbot answer that became a disputed company promise.
- AI meeting recaps and generated summaries that need review, correction, and
  context.
- A legal filing with fake cases.
- A session log that mostly proved the session existed.
- Structured log sections for questions, issues, decisions, commit summaries,
  ADR disposition, duration, and token estimates.

## Artifact Availability

- KPMG report: no direct public KPMG link found during research. The
  Financial Times reports that KPMG pulled the report from some websites while
  it investigates. The article should say the report itself no longer appears
  publicly available from KPMG and link the Financial Times and TechRadar
  coverage instead.
- GPTZero analysis: use through TechRadar's summary unless a primary GPTZero
  artifact is found before publication.
- Internal harness artifacts: direct local paths are available in this packet.

## Reader-World Bridge

The reader-world research packet supplies the bridge. The article opens with a
public report about AI whose evidence failed under inspection, then gives
supporting examples from customer-service chatbots, meeting recaps, and legal
filings.

These examples let the reader recognize the broader pattern before the harness
appears: AI can give weak work the posture of strong work. It can make a claim
look cited, a customer answer look official, a meeting look settled, and a
decision look finished before the evidence underneath is strong enough.

## Stakes

The downside is false confidence that travels.

If ignored, AI work becomes easier to polish and harder to defend. A customer
acts on a chatbot answer. A team acts on a recap. A report gets cited. A
future author trusts a decision note. The cost appears later, when someone
must explain what the answer was standing on.

## Counterpoint Or Objection

"Isn't this just bureaucracy?"

The article answers that evidence is not saving everything. It is preserving
the minimum trail needed to explain what changed, why it changed, and what
should happen next.

## Surprise Or Turn

The stronger lesson is not "AI needs receipts" or "documentation matters." The
turn is that AI polish creates a new burden: if the work is going to travel,
it needs a trail strong enough to travel with it.

## Only-I-Could-Write-This Details

- The harness plan revision explicitly changed the work from ADR checking to
  structured session evidence.
- The first session record mostly proved that a session existed, not what had
  been decided inside it.
- The later metrics work recorded durations as `dd:hh:mm:ss` and estimated
  token use.
- The author frames this as a trust problem: evidence buys freedom from
  reconstructing your own reasoning later.

## Missing Material

- A before/after excerpt of the thin session log would strengthen the second
  act.
- Source links should be checked again before publication.

## Scene Cards

- `scene-cards/001-kpmg-report-citations.md`
- `scene-cards/002-thin-session-record.md`
- `scene-cards/003-chats-become-a-body-of-work.md`
- `scene-cards/004-air-canada-chatbot-answer.md`
- `scene-cards/005-meeting-recap-action-items.md`

## Example Ledger Check

Checked: `docs/education/articles/example-ledger.md`.

The prior customer-worth-20%-of-revenue anecdote is retired as a major example
for this article. The rewrite uses fresh reader-world examples.

## Quality Gate

- Is there enough material for a short magazine-standard article? Yes.
- Would the piece need an invented opening or generic bridge to work? No.
- Does the material support a fresh thesis? Yes.
- Is the strongest story from this window better than publishing nothing? Yes.
- Has the reader-world research packet produced enough examples to set the
  table before the thesis? Yes.
- Are named public artifacts linked or explicitly marked as pulled,
  unavailable, archived, paywalled, or known only through secondary reporting?
  Yes. The KPMG report is marked unavailable from KPMG and routed through
  secondary reporting.
- Can a cold reader understand the world, object under pressure, AI temptation,
  downside, and personal relevance by roughly line 30? Yes.

Decision: sufficient.
