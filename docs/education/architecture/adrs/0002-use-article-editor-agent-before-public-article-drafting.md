# 0002 Use Article Editor Agent Before Public Article Drafting

Status: accepted
Date: 2026-06-16

## Context

The education layer produced early article drafts that were technically related
to the source work but weak as public writing. Repeated feedback showed several
failure modes:

- settling for a true but weak thesis
- opening with abstract or punchy AI syntax instead of story
- stating authorial care directly instead of making the reader feel the stakes
- relying on repo setting and jargon before building reader context
- reducing a rich source arc into a thin lesson

These are not merely prose-polish problems. They are commissioning and
editorial judgment problems that happen before drafting.

## Decision

Create an education-layer Article Editor Agent and require it before drafting or
substantially revising public-facing articles.

The agent acts as a narrative commissioning editor and reader advocate. It does
not draft articles. It produces an article editor brief that tests story,
stakes, reader relevance, topic strength, opening path, vocabulary teaching,
and cold-reader risks.

The brief must include a source scene inventory before it selects an opening or
approves drafting. The scene inventory forces the editor to identify what
actually happened, who wanted something, what friction made the moment matter,
what downside was present, and what concrete details a cold reader could
picture.

The agent may block drafting when the article is true but weak, when stakes are
not palpable, when the setting has not been built, or when the source story has
been reduced to a generic lesson.

Before advising, the agent must review local writing references or current
writing-craft research when the local references are insufficient. It must not
improvise definitions of hook, stakes, story, or magazine style from vibes.

## Consequences

Article drafting becomes a two-step process: commission first, draft second.

The education layer gains a bounded role for rejecting weak premises before the
writer turns them into polished but unpublishable prose. This adds overhead,
but the overhead is intentional because article quality has been failing at the
story-selection and reader-stakes stage rather than at the sentence-polish
stage.
