# Teaching Note: Evidence Before Judgment

## What It Teaches

AI systems cannot exercise useful judgment from vibes alone. If a system is
expected to decide whether a change needs an ADR, route a task, summarize a
decision, or recommend an action, it needs preserved evidence.

The point is not bureaucracy. The point is giving judgment somewhere to stand.

## Source Moment

On June 15, 2026, the harness gained a commit-time ADR check. The first design
exposed a hidden dependency: the existing chat logs were too thin to support
the judgment. The system first needed structured session memory: questions,
issues, decisions, commit summaries, ADR disposition, and metrics.

## Classroom Use

Use this as a short case study after students or participants have seen an AI
tool produce a confident answer.

Ask:

- What evidence would the system need before making this decision?
- Where should that evidence live?
- Which parts can be checked deterministically?
- Which parts still require human judgment?
- What would make the output inspectable later?

## Exercise

Give learners this prompt:

> An AI assistant must decide whether a project change needs an architecture
> decision record. Design the minimum session log that would let it make that
> decision responsibly.

Expected ingredients:

- initial intent
- questions asked and answers received
- issues raised and resolutions
- decisions made and rationale
- files or systems affected
- commit summary
- explicit ADR-needed or ADR-not-needed disposition

## Audience Translation

For non-technical AI audiences, frame this as:

> The next level after AI fluency is knowing what the system knew when it
> sounded confident.

This keeps the lesson positive and opportunity-facing while quietly shifting
the reader from borrowed fluency toward grounded orientation.

## Common Mistake

Do not present logs as administrative overhead. Present them as trust
infrastructure.

## Reusable Line

Confidence is more useful when it comes with a trace.
