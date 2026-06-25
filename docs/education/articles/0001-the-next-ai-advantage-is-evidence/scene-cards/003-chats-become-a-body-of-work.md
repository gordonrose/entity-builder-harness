<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0001-the-next-ai-advantage-is-evidence.scene-cards.003-chats-become-a-body-of-work
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

- Scene title: Chats Become A Body Of Work
- Article candidate: The Next AI Advantage Is Evidence
- Source packet: `../source-packet.md`
- Source evidence:
  - `commitLogs/2026/jun/15/2026-06-15-23-18-i-d-like-to-update-the-harness-so-that-the-chat-duration-is-/README.md`
  - `docs/harness/architecture/adrs/0004-group-chat-logs-and-summarize-session-metrics.md`
- Status: usable

## Scene

After structured records existed, the author changed the harness again so chat
logs were grouped by date and summarized with duration and token statistics.
The chats stopped being isolated windows and started to become a body of work
that could be reviewed.

## Where And When

During the later harness work on grouped commit logs and session metrics.

## Who Is Present

The author reviewing accumulated AI work through commit logs and summary
metrics.

## What The Protagonist Wants

The author wants to see whether repeated AI sessions are producing patterns,
not just isolated outputs.

## What Is Being Looked At, Changed, Asked, Or Discovered

Grouped log folders, readable chat durations, token estimates, and aggregate
statistics.

## Friction

Individual chats can feel productive while remaining impossible to compare.
Without grouping and metrics, the work stays anecdotal.

## Downside If Ignored

The author cannot see which sessions take longer, consume more AI interaction,
or produce decisions and lessons worth carrying forward.

## Concrete Details

- object: `commitLogs/<yyyy>/<mmm>/<dd>/`
- phrase: `dd:hh:mm:ss`
- number: max, min, average, median, quartiles, outlier count
- before/after: isolated chats; grouped sessions with aggregate stats
- human reaction: the work becomes inspectable instead of merely remembered

## Exact Source Evidence

ADR 0004 originally maintained `commitLogs/README.md` with aggregate chat
duration and token consumption statistics; ADR 0013 later moved that summary
to on-demand generation.

Commit log summary: grouped logs by year/month/day, added deterministic
duration and token statistics, formatted durations as seconds plus
`dd:hh:mm:ss`.

## Cold Reader Test

A cold reader can understand this as moving from "I had some useful AI chats"
to "I can see what kinds of AI work actually happened."

## Thesis Relevance

This scene expands the article from decision evidence to compound learning.

## Opening Strength

- Strong enough to open: no
- Why: It is a strong middle act but too process-heavy before the reader cares.
- What additional material would make it stronger: a concrete pattern that the
  metrics revealed.
