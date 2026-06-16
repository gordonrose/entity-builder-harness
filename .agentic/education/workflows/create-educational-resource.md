# Create Educational Resource

## Use When

Use this after a mining pass or when the user selects a specific educational
resource to draft.

Supported resources include:

- 3-minute blog posts
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
4. Draft from the concrete incident outward.
5. Keep the author's voice central; do not imitate external sources.
6. For lesson plans, design the 30-minute core first, then add the 50-minute
   extension.
7. Run the audits before final output.

## Output

Use `../templates/educational-resource.md`.

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
- Use spoken language for talks.
- Use concrete details from the logs.
- Avoid corporate tone, fake profundity, and generic AI phrasing.
- A 30-minute talk needs one central spine, not many loosely related ideas.
- A lesson plan needs one teachable transformation, not a collection of related
  notes.
- The 50-minute extension must deepen the same lesson rather than introduce a
  second lesson.
