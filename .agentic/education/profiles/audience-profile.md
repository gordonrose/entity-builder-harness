<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.profiles.audience-profile
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Audience Profile.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Audience Profile

## Primary Audience

Write first for hype-adjacent, non-technical or lightly technical AI readers.
They follow the conversation, enjoy sounding current, and may perform more
confidence than their understanding can support.

They are often status-aware and allergic to being made to feel behind. They do
not want beginner treatment, even when they need orientation. They respond to
frames that feel like the next layer of sophistication.

## Secondary Audience

Also preserve room for genuinely thoughtful readers who are underconfident
despite being capable. They should feel relieved by the clarity, not pushed out
by status games.

## Emotional Contract

The reader should feel upgraded, not exposed.

The writing should say, in effect:

- you are right that this matters
- the interesting part is underneath the surface language
- here is a more grounded way to understand what is happening

Do not humiliate the reader for having borrowed fluency. Offer them a better
form of confidence: orientation backed by evidence.

## Teaching Posture

Use concrete repo incidents as small windows into larger AI truths. Start with
a real moment, then translate it into a useful frame for the reader.

Prefer:

- orientation without humiliation
- positive surface, discerning subtext
- opportunity language with real substance underneath
- concrete systems behavior over abstract AI commentary
- status-upgrading frames that are also true

Avoid:

- "you do not understand AI" energy
- beginner framing that makes the reader feel small
- debunking posture
- anti-hype scolding
- empty positivity
- flattering the reader without teaching them anything
- unexplained technical or repo-specific vocabulary before the reader has a
  reason to care
- examples that depend on an internal setting the reader has not been helped to
  imagine

## Context Rule

Assume the primary reader does not know repo, software, or architecture-process
language. They may know AI buzzwords, but not the mechanics underneath.

Before using terms like commit, branch, ADR, harness, log, workflow, or gate,
translate the human situation first. If the human situation cannot be explained
plainly, do not use the term yet.

The reader should never feel that the piece has suddenly walked into a room
where everyone else already knows the furniture.

## Competent Non-Technical Reader Rule

Treat the reader as intelligent and AI-curious, not as technically initiated.
They can follow a careful explanation, but they may not know how engineering
work normally converges through local work, branches, shared baselines, review,
checks, and merge.

When a public article depends on a technical analogy, build a prerequisite
ladder first:

- what the reader already wants
- what hidden cost or pressure follows from that desire
- what normal-world model helps explain it
- what part of the model transfers to the AI setting
- what part does not transfer and must be created by the harness

Prefer slight over-explanation to a missing middle step. A sentence that is
less elegant but keeps the reader oriented is better than a sharper sentence
that requires insider context.

## Reader Outcome

A successful piece leaves the reader feeling sharper, safer, and more able to
name what is happening. It should let them keep their desired self-image while
quietly improving the substance underneath it.
