# Education Layer

The education layer governs educational resources derived from repo work.

Use this layer for turning commit logs, ADRs, implementation decisions,
debugging trails, and project documentation into teaching material such as:

- short public articles with magazine-style quality gates
- 30-minute talks
- 30-minute lesson plans with 50-minute extension paths
- lecture anecdotes
- classroom exercises
- mini case studies
- teaching assets
- voice, humor, storytelling, and structure calibration
- source-backed education quality principles
- article commissioning and reader-advocate review

Education work should preserve a clear link to the underlying repo evidence.
Mine the material before drafting from it.

Public articles also need reader-world evidence. For non-technical or lightly
technical audiences, gather current examples from public discourse or
author-owned material before drafting so the article can build the setting
before stating the thesis.

## Workflows

- `workflows/mine-daily-learning-material.md` - extract story-worthy learning
  material from a day of repo work.
- `workflows/create-educational-resource.md` - draft a selected educational
  resource from mined material.
- `workflows/calibrate-education-outputs.md` - update profiles from feedback on
  generated outputs.
- `workflows/improve-education-system.md` - incorporate durable source-backed
  principles without copying source expression.

## Supporting Artifacts

- `templates/` defines reusable output shapes.
- `profiles/` stores evolving voice, humor, storytelling, and structure
  calibration.
- `agents/` stores bounded education roles such as article editor review.
- `prompts/` stores versioned task prompts.
- `references/` stores distilled principles from reviewed source material.
- `feedback/` stores dated feedback notes for future calibration.

## Output Locations

- `docs/education/articles/` stores public article drafts.
- `docs/education/lesson-plans/` stores facilitator-ready lesson plans.
- `docs/education/teaching-notes/` stores smaller reusable teaching notes that
  are not yet complete lesson plans.
- `docs/education/title-banks/` stores reusable title calibration material.

Public articles should use one folder per article, with `article.md`,
`source-packet.md`, `reader-world-research-packet.md`, `editor-brief.md`,
`opening-lab.md`, `writer-notes.md`, `editor-review.md`, `revision-log.md`,
optional `calibration-report.md`, and `scene-cards/`. Legacy flat files may
remain until they are next revised through the source-packet pipeline.

## Article Drafting

Public-facing articles use a source-report-commission-write-review loop.

First, use `.agentic/education/agents/article-reporter.md`,
`.agentic/education/templates/article-source-packet.md`, and
`.agentic/education/templates/reader-world-research-packet.md`, and
`.agentic/education/templates/scene-card.md` to test whether there is enough
material to write. `No publishable article this cycle` is a valid outcome.

The reader-world research packet should gather 6 to 10 scene seeds, check
`docs/education/articles/example-ledger.md`, and answer the line 30
cold-reader gate before drafting.

Then use `.agentic/education/agents/article-editor.md` and
`.agentic/education/templates/article-editor-brief.md` to test story, stakes,
topic strength, reader context, source sufficiency, and draft readiness.

Then use `.agentic/education/agents/article-writer.md` and
`.agentic/education/templates/article-opening-lab.md` to produce opening
candidates. Return the opening lab to the Article Editor Agent before drafting.

Then use the Article Writer Agent to turn the approved source packet, scene
reader-world research packet, scene cards, brief, and opening into a fresh
article body. Store writer notes and editor reviews beside the article, not in
the public article body.

After drafting, return the article to the Article Editor Agent for review. The
writer does not mark its own draft publishable.

When user feedback or a user-final rewrite reveals reusable lessons, create an
article calibration report using
`.agentic/education/templates/article-calibration-report.md`. Use it to compare
the generated draft with the preferred version and route durable lessons into
profiles, templates, workflows, or prompts.

Prefer no article over a weak article.

## Open Harness Improvements

When asked what education-harness work remains, surface these backlog items:

- Add an article-mission layer before drafting. The harness should capture what
  the piece is trying to do to the reader: sharpen them, reassure them,
  unsettle them, give them a better lens, make them harder to fool, or help
  them feel more capable without being patronized.
- Add a humor and wit pass after the source, story, and structure are working.
  The pass should find situational wit, dry authorial bite, and pressure
  release already latent in the material, not paste jokes over a weak draft.

See `feedback/2026-06-16-article-mission-and-wit-backlog.md`.

## Education ADRs

Durable education-layer decisions live in
`docs/education/architecture/adrs/`.

Use an education ADR for decisions about audience, pedagogy, public voice,
content strategy, or recurring educational artifact shape. Do not create an ADR
for every taste correction or one-off draft preference; store those in
`profiles/` or `feedback/`.
