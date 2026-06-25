<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0001-the-next-ai-advantage-is-evidence.scene-cards.002-thin-session-record
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Scene Card.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Scene Card

## Metadata

- Scene title: Thin Session Record
- Article candidate: The Next AI Advantage Is Evidence
- Source packet: `../source-packet.md`
- Source evidence:
  - `commitLogs/2026/jun/15/2026-06-15-21-27-i-d-like-to-update-my-harness-so-that-whenever-i-commit-some/README.md`
  - `docs/harness/architecture/adrs/0001-record-harness-session-decisions-before-commit.md`
- Status: usable

## Scene

The author wanted the assistant to check whether chat decisions deserved
durable notes before finishing work. The plan failed when the author noticed
the session record did not preserve enough of the conversation to support that
judgment.

## Where And When

During a harness change about commit-time decision records. The exact date is
not important to the reader.

## Who Is Present

The author and the assistant, with the session log as the visible artifact.

## What The Protagonist Wants

The author wants the assistant to catch decisions before they disappear.

## What Is Being Looked At, Changed, Asked, Or Discovered

The author is looking at the session record and asking what the assistant would
actually know when deciding whether an ADR is needed.

## Friction

The record had startup and branch metadata, but not enough questions, issues,
decisions, and reasons.

## Downside If Ignored

The assistant could produce a responsible-sounding decision check from a record
that had already lost the reasons.

## Concrete Details

- object: session log
- phrase: "chat logs were not recording enough activity"
- number: 10-step plan revised after the issue surfaced
- before/after: ADR check alone; structured session evidence first
- human reaction: the sensible rule turns out to depend on missing material

## Exact Source Evidence

Commit log issue: "The original plan assumed ADR checks could stand alone, but
chat logs were not recording enough activity."

ADR 0001: "Without a structured session log, a commit-time ADR check would have
to infer architecture decisions from a thin record or from transient chat
context."

## Cold Reader Test

A cold reader can understand this as a common work problem: asking someone to
make a judgment after the useful context has vanished.

## Thesis Relevance

This is the article's source turn. It shows why AI evidence matters before
judgment.

## Opening Strength

- Strong enough to open: possible, but weaker than the customer scene
- Why: It is real and concrete, but still close to internal repo mechanics.
- What additional material would make it stronger: an exact before/after log
  excerpt or screenshot-like description.
