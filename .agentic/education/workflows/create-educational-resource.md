# Create Educational Resource

## Use When

Use this after a mining pass or when the user selects a specific educational
resource to draft.

Supported resources include:

- short public articles with magazine-style quality gates
- 30-minute talk scripts
- slide outlines
- 30-minute lesson plans with 50-minute extension paths
- lecture anecdotes
- classroom exercises
- mini case studies
- debugging exercises
- discussion prompts

## Inputs

- Selected candidate or source material
- Relevant extracted material
- Voice, humor, storytelling, and structure profiles
- Prior feedback when available
- Target audience and format

## Process

1. Confirm the selected output type and audience.
2. Gather the specific evidence from logs or repo artifacts.
3. Load only the relevant profiles and reference principles.
4. For public-facing articles, run the Article Reporter Agent before the
   editor. Produce a reader-world research packet, article source packet, and
   scene cards. Stop if the reporter marks the material insufficient.
5. For public-facing articles, run the Article Editor Agent before drafting.
   Produce an article editor brief from the reader-world research packet,
   source packet, and scene cards. Do not draft if the brief blocks the
   candidate.
6. For approved public-facing articles, run the Article Writer Agent from the
   approved reader-world research packet, source packet, scene cards, and
   brief to produce an article opening lab.
7. Return the opening lab to the Article Editor Agent. Do not draft the full
   article until the opening is approved.
8. Draft the article body only from the approved reader-world research packet,
   source packet, scene cards, opening, and brief. Store writer notes
   separately.
9. Run separate revision passes: structural edit, source gap pass, voice pass,
   line edit, and cold-reader review.
10. Return article drafts to the Article Editor Agent for review before
   treating them as publishable.
11. For non-article resources, draft from the concrete incident outward.
12. Keep the author's voice central; do not imitate external sources.
13. For lesson plans, design the 30-minute core first, then add the 50-minute
   extension.
14. Run the audits before final output.

## Output

Use `../templates/educational-resource.md`.

For public-facing articles, use:

- `../templates/reader-world-research-packet.md`
- `../templates/article-source-packet.md`
- `../templates/scene-card.md`
- `../templates/article-editor-brief.md`
- `../templates/article-opening-lab.md`
- `../templates/article-revision-log.md`

Then use `../agents/article-writer.md` for the draft body only.

For lesson plans, use `../templates/lesson-plan.md`.

Include:

- title
- audience
- source evidence
- draft or script
- structure notes
- humor notes
- teaching notes
- revision notes
- specificity audit
- voice audit
- teaching audit

Lesson plans must include:

- a complete 30-minute core that stands alone
- a 50-minute extension that deepens practice, discussion, or application
- one source story
- one worked example
- one participant activity
- facilitator script notes
- debrief guidance
- audience, specificity, teaching, and AI-smell audits

## Quality Rules

- Write in first person when drafting authorial material.
- Do not draft public-facing articles until the Article Reporter Agent has
  marked the reader-world research packet and source packet sufficient.
- Do not draft public-facing articles until the Article Editor Agent has
  approved the article brief.
- Do not draft public-facing articles until the Article Editor Agent has
  approved an article opening lab.
- Do not treat a writer-agent draft as publishable until it has returned to the
  Article Editor Agent for review.
- Do not use a hypothetical example as the opening, main evidence, or primary
  reader bridge for public-facing articles.
- Do not reuse a major anecdote or example from a prior article as the
  opening, main evidence, or primary reader bridge.
- Do not let a public article state the thesis before the reader has enough
  fresh, recognizable examples to understand the setting.
- Do not store writer notes inside the public article body.
- Prefer no public article over a weak public article.
- Use spoken language for talks.
- Use concrete details from the logs.
- Avoid corporate tone, fake profundity, and generic AI phrasing.
- A 30-minute talk needs one central spine, not many loosely related ideas.
- A lesson plan needs one teachable transformation, not a collection of related
  notes.
- The 50-minute extension must deepen the same lesson rather than introduce a
  second lesson.
