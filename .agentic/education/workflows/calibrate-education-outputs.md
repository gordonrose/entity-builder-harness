# Calibrate Education Outputs

## Use When

Use this when the user reviews generated education outputs and wants future
outputs to improve in humor, storytelling, tone of voice, structure, teaching
depth, or audience fit.

## Inputs

- Generated output
- User feedback
- Optional preferred examples
- Optional disliked examples
- Relevant current profiles

## Process

1. Separate feedback into voice, humor, storytelling, structure, teaching depth,
   and audience fit.
2. Identify whether each change belongs in a profile, template, prompt, or
   workflow.
3. Prefer profile updates for taste and voice calibration.
4. Prefer template updates for repeated structural changes.
5. Version prompts only when the task contract or model behavior needs to
   change.
6. Preserve concrete examples of liked and disliked lines when useful.

## Outputs

Update the relevant profile or template only after explicit write permission.

Recommended profile targets:

- `../profiles/voice-profile.md`
- `../profiles/humor-profile.md`
- `../profiles/storytelling-profile.md`
- `../profiles/structure-profile.md`

## Quality Rules

- Do not turn prompts into a diary of corrections.
- Keep stable prompts separate from evolving taste data.
- Preserve the author's natural teaching voice over generic polish.
