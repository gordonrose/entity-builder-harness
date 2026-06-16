# Mine Daily Learning Material

## Use When

Use this when the user wants to analyze commit logs or repo work to find
educational content opportunities.

Typical outputs include blog candidates, talk candidates, teaching assets,
story moments, humor angles, and voice notes.

## Inputs

- Date or commit log path
- Optional project context
- Optional target audience
- Optional profile files from `.agentic/education/profiles/`
- Optional prior feedback from `.agentic/education/feedback/`

## Process

1. Read the relevant commit logs and supporting repo evidence.
2. Summarize what actually happened.
3. Extract raw material before proposing finished content.
4. For each candidate, cite concrete evidence from the logs.
5. Identify technical, emotional, teaching, and humor potential.
6. Score only candidates with real content potential.
7. Produce a specificity audit before finalizing.

## Output

Use `../templates/content-mining-report.md`.

The output should include:

- what actually happened
- raw material inventory
- candidate 3-minute blog posts
- candidate 30-minute talks
- teaching assets
- voice calibration notes
- best picks
- iteration questions
- specificity audit
- machine-smell audit

## Quality Rules

- Do not merely summarize the logs.
- Do not draft full posts or talks unless the user asks for a one-shot output.
- Prefer concrete incidents over generic lessons.
- Prefer story before abstraction and example before definition.
- Cut any idea that could have been produced without reading the logs.
- Humor should come from recognition, understatement, irony, or real technical
  absurdity.
