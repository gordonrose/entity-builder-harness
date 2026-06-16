# Education Layer

The education layer governs educational resources derived from repo work.

Use this layer for turning commit logs, ADRs, implementation decisions,
debugging trails, and project documentation into teaching material such as:

- 3-minute blog posts
- 30-minute talks
- 30-minute lesson plans with 50-minute extension paths
- lecture anecdotes
- classroom exercises
- mini case studies
- teaching assets
- voice, humor, storytelling, and structure calibration
- source-backed education quality principles

Education work should preserve a clear link to the underlying repo evidence.
Mine the material before drafting from it.

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
- `prompts/` stores versioned task prompts.
- `references/` stores distilled principles from reviewed source material.
- `feedback/` stores dated feedback notes for future calibration.

## Output Locations

- `docs/education/articles/` stores public article drafts.
- `docs/education/lesson-plans/` stores facilitator-ready lesson plans.
- `docs/education/teaching-notes/` stores smaller reusable teaching notes that
  are not yet complete lesson plans.
- `docs/education/title-banks/` stores reusable title calibration material.

## Education ADRs

Durable education-layer decisions live in
`docs/education/architecture/adrs/`.

Use an education ADR for decisions about audience, pedagogy, public voice,
content strategy, or recurring educational artifact shape. Do not create an ADR
for every taste correction or one-off draft preference; store those in
`profiles/` or `feedback/`.
