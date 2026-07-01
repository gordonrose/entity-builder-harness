<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.architecture.adr.0004-require-source-packets-for-public-articles
  version: 1
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: adr
  purpose: Document 0004 Require Source Packets For Public Articles.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# 0004 Require Source Packets For Public Articles

Status: accepted
Date: 2026-06-16

## Context

The education layer produced clearer public article drafts after adding
article editor and writer agents, but the drafts still hit a quality ceiling.
The problem was not mainly sentence polish. The article pipeline was asking a
writer to produce magazine-standard short public writing from commit logs,
ADRs, internal summaries, and prompt guardrails.

Feedback identified that this creates article-shaped explanations rather than
articles with lived material. The strongest diagnosis was that the harness had
become good at describing good writing, but not yet good at forcing the
conditions that produce it: source material, concrete scenes, reader-world
bridges, voice evidence, and real revision.

The intended public output is not a low-standard content-marketing blog post.
It is a compact public article at magazine-style quality: short enough to read
quickly, but sourced, scene-led, specific, and recognizably in the author's
voice.

## Decision

Public short articles now require a source-first pipeline:

1. Mine a source window, not just a single day when the day is thin.
2. Allow `no publishable article this cycle` as a successful outcome.
3. Run an Article Reporter Agent before the Article Editor Agent.
4. Produce an article source packet and scene cards before commissioning.
5. Block drafting when the source packet is insufficient.
6. Use a sourced short-magazine quality bar before approval.
7. Use the author's voice sample bank as the primary sentence-level voice
   reference.
8. Store public article bodies separately from source packets, notes, reviews,
   and revision logs.

The Article Reporter Agent gathers and tests material. The Article Editor Agent
commissions or blocks from the source packet and scene cards. The Article
Writer Agent drafts only from approved source material, approved scene cards,
an approved brief, and an approved opening lab.

Hypothetical examples may clarify an idea after the article has earned trust,
but they must not serve as the opening, main evidence, or primary reader bridge
for a public short article.

## Consequences

The education layer becomes more willing to publish nothing when the source
material is weak. This adds friction, but it protects the public voice from
generic, over-smoothed AI writing.

Article artifacts now need more structure. Future public article folders should
contain the article body, source packet, scene cards, editor brief, opening lab,
writer notes, editor review, and revision log as separate files. Legacy flat
article files may remain until revised through the new pipeline.

The quality bar is sourced to external writing and journalism guidance rather
than invented from taste alone. The rubric can evolve as more credible sources
are reviewed, but article approval must continue to depend on material
sufficiency, scene strength, felt stakes, reader orientation, thesis freshness,
voice match, specificity, and ending quality.
