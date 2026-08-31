<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0008-add-education-layer
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the 0008 Add Education Layer architecture decision.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
-->

# 0008 Add Education Layer

Status: accepted
Date: 2026-06-16

## Context

The repo already records detailed chat sessions, decisions, ADRs, and commit
log summaries. Those records are useful not only for engineering traceability
but also for teaching: they contain mistakes, tradeoffs, debugging trails,
moments of confusion, design decisions, and explanations that can become
educational resources.

Before this decision, the harness had `shared`, `harness`, and `product`
layers. Educational content generation did not fit cleanly into any of them.
It is not product behavior, not shared git/chat process, and not harness
maintenance unless the education system itself is being changed.

The user also wants the outputs to improve over time in storytelling, humor,
tone of voice, structure, and teaching quality. That requires a feedback and
calibration loop, not one large prompt that is edited after every run.

## Decision

Add `.agentic/education/` as a first-class layer for educational resources
derived from repo work.

The education layer owns:

- mining commit logs and repo artifacts for teaching material
- generating candidate 3-minute blog posts and 30-minute talks
- drafting selected blog posts, talk scripts, lecture anecdotes, and classroom
  assets
- maintaining voice, humor, storytelling, and structure profiles
- collecting feedback on generated outputs
- incorporating source-backed teaching, writing, storytelling, humor, and talk
  design principles

The first workflows separate mining from drafting. Mining extracts evidence,
story material, teaching potential, humor angles, and risks before any finished
resource is written. Drafting uses selected candidates plus profiles and
feedback.

Profiles evolve separately from prompts. Taste changes usually update profiles;
repeated structural changes update templates; prompts are versioned only when
the task contract or model behavior needs to change.

External source material is used as a source of distilled principles, not as
copyable expression or stylistic imitation.

## Consequences

Future education requests can route directly to `.agentic/education/` instead
of being treated as product or generic harness work.

The layer adds more harness surface area, but keeps always-loaded instructions
small by placing detailed guidance in load-on-demand workflows, prompts,
profiles, templates, and references.

The quality loop becomes cumulative. Feedback about humor, voice, tone,
storytelling, and structure can improve future outputs without turning stable
prompts into a noisy record of one-off corrections.

The layer also creates a clear boundary: changing the education system itself
is still a harness change, while using the system to produce educational
resources is education work.
