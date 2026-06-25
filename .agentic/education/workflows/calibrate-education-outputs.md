<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.workflows.calibrate-education-outputs
  version: 1
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: workflow
  purpose: Document Calibrate Education Outputs.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Calibrate Education Outputs

## Use When

Use this when the user reviews generated education outputs and wants future
outputs to improve in humor, storytelling, tone of voice, structure, teaching
depth, or audience fit.

## Inputs

- Generated output
- User feedback
- Optional user-final or preferred rewrite
- Optional preferred examples
- Optional disliked examples
- Relevant current profiles

## Process

1. Separate feedback into voice, humor, storytelling, structure, teaching depth,
   and audience fit.
2. When a user-final rewrite exists, compare it against the generated draft.
   Identify what the user restored, removed, simplified, expanded, or
   re-centered.
3. Identify whether each change belongs in a profile, template, prompt, or
   workflow.
4. Prefer profile updates for taste and voice calibration.
5. Prefer template updates for repeated structural changes.
6. Version prompts only when the task contract or model behavior needs to
   change.
7. Preserve concrete examples of liked and disliked lines when useful.
8. For public articles, produce an article calibration report when feedback
   reveals reusable lessons beyond the current draft.

## Outputs

Update the relevant profile or template only after explicit write permission.

Recommended profile targets:

- `../profiles/audience-profile.md`
- `../profiles/voice-profile.md`
- `../profiles/humor-profile.md`
- `../profiles/storytelling-profile.md`
- `../profiles/structure-profile.md`

Recommended template targets:

- `../templates/article-editor-brief.md`
- `../templates/article-opening-lab.md`
- `../templates/article-calibration-report.md`

## Quality Rules

- Do not turn prompts into a diary of corrections.
- Keep stable prompts separate from evolving taste data.
- Preserve the author's natural teaching voice over generic polish.
