<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.workflows.mine-daily-learning-material
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: workflow
  purpose: Document Mine Daily Learning Material.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Mine Daily Learning Material

## Use When

Use this when the user wants to analyze commit logs or repo work to find
educational content opportunities. Despite the filename, the mining window may
span multiple days when one day does not contain a publishable public article
candidate.

Typical outputs include blog candidates, talk candidates, teaching assets,
story moments, humor angles, and voice notes.

## Inputs

- Date, commit log path, or rolling source window
- Optional project context
- Optional target audience
- Optional profile files from `.agentic/education/profiles/`
- Optional prior feedback from `.agentic/education/feedback/`

## Process

1. Read the relevant commit logs and supporting repo evidence. If the target is
   a public article and one day is thin, scan the agreed rolling window before
   recommending a weak candidate.
2. Load relevant education profiles before proposing public-facing candidates:
   audience, voice, humor, storytelling, and structure.
3. Summarize what actually happened.
4. Extract raw material before proposing finished content.
5. Identify competing source arcs before choosing topics.
6. For each candidate, cite concrete evidence from the logs.
7. Identify technical, emotional, teaching, and humor potential.
8. Score only candidates with real content potential.
9. Compare candidate theses and reject true-but-weak lessons when a stronger
   source story exists.
10. For public article candidates, identify whether a source packet and scene
   cards could plausibly be made sufficient.
11. Calibrate titles against the audience and voice profiles.
12. Produce topic-strength, audience-fit, subtext, specificity, AI-smell, and machine-smell
   audits before finalizing.
13. If no candidate clears the material bar, recommend `no publishable article
   this cycle` and identify the strongest non-article teaching asset instead.

## Output

Use `../templates/content-mining-report.md`.

The output should include:

- what actually happened
- raw material inventory
- candidate short public articles
- candidate 30-minute talks
- teaching assets
- voice calibration notes
- topic-strength comparison
- best picks
- iteration questions
- audience-fit audit
- title calibration
- zeitgeist alignment
- subtext audit
- AI-smell audit
- specificity audit
- machine-smell audit

## Quality Rules

- Do not merely summarize the logs.
- Do not draft full posts or talks unless the user asks for a one-shot output.
- Prefer concrete incidents over generic lessons.
- Prefer story before abstraction and example before definition.
- Cut any idea that could have been produced without reading the logs.
- Prefer no public article over a weak public article.
- Do not settle for the first coherent thesis. Hunt for the strongest source
  story: the most concrete, surprising, emotionally live, and audience-relevant
  arc in the material.
- Reject weak-but-true abstractions when the logs contain a richer story.
- Humor should come from recognition, understatement, irony, or real technical
  absurdity.
- For hype-adjacent public AI audiences, keep the surface positive and
  opportunity-facing while placing critique in subtext, contrast, or upgrade
  path.
- Keep positivity grounded in concrete evidence. Do not use significance
  inflation, vague authority, or generic broader-trend language to make a thin
  incident sound larger than it is.
- Reject technically accurate titles when they sound generic, accusatory, or
  unlike the author.
- Public article candidates need enough source material for an Article Reporter
  Agent source packet. If the candidate would require an invented bridge, mark
  it insufficient.
