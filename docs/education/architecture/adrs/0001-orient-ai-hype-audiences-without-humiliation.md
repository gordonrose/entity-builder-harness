<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.architecture.adr.0001-orient-ai-hype-audiences-without-humiliation
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: adr
  purpose: Document 0001 Orient AI Hype Audiences Without Humiliation.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# 0001 Orient AI Hype Audiences Without Humiliation

Status: accepted
Date: 2026-06-16

## Context

The education layer turns repo work into public teaching material. Early topic
mining produced technically accurate titles and candidates, but they sounded too
generic and too unlike the intended authorial voice.

The intended audience is not primarily technical practitioners. The primary
reader is hype-adjacent: someone who follows AI trends, enjoys sounding current,
and may perform confidence beyond their actual understanding. Some readers in
the same audience may be genuinely thoughtful and underconfident, but the
education layer should optimize first for people whose self-image is tied to
being ahead of the curve.

Direct critique of shallow fluency would miss the moment. The current AI
zeitgeist rewards positivity, momentum, opportunity language, and confidence.
Educational material should participate in that surface mood while quietly
helping readers move toward grounded understanding.

## Decision

Education outputs about AI should orient hype-adjacent readers without
humiliating them.

The surface tone should be optimistic, current, and opportunity-facing.
Critique should usually appear as subtext, contrast, implication, or an upgrade
path rather than accusation. The writing should let readers keep their desired
self-image while offering a more sophisticated version of it: not borrowed
fluency, but orientation grounded in evidence.

The education layer should therefore prefer topics, titles, and article shapes
that:

- make the reader feel upgraded rather than exposed
- teach through concrete incidents before abstraction
- preserve enough technical reality to create orientation
- avoid patronizing beginner framing
- avoid takedown posture, debunking energy, or anti-hype scolding
- follow the positive zeitgeist around the topic while carrying discernment
  underneath

When this decision conflicts with serving highly technical readers, prioritize
the hype-adjacent non-technical or lightly technical audience.

## Consequences

Education profiles and templates need explicit audience, title, and subtext
checks. Generic technical titles should be rejected even when they summarize the
material accurately. Stronger titles should feel like the next layer of
opportunity while leaving the harder lesson underneath.

Content should not flatter the reader falsely or dilute the work into hype. The
standard is genuine orientation: the reader should leave feeling sharper, safer,
and more able to name what is happening.
