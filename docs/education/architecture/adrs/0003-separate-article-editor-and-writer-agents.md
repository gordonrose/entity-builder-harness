# 0003 Separate Article Editor And Writer Agents

Status: accepted
Date: 2026-06-16

## Context

The first public article attempts failed because drafting began before the
article had a strong enough commission. The education layer now has an Article
Editor Agent that can approve or block a public article premise.

That still leaves a second problem. A drafting pass can collapse the approved
commission back into generic AI writing if the writer is allowed to renegotiate
the thesis, start from an abstract hook, or teach internal vocabulary before
the reader needs it.

## Decision

Separate article commissioning, opening selection, drafting, and review into
distinct stages:

1. The Article Editor Agent approves or blocks the article brief.
2. The Article Writer Agent produces an opening lab from the approved brief.
3. The Article Editor Agent approves or blocks the opening before full drafting.
4. The Article Writer Agent drafts only from an approved brief and approved
   opening.
5. The Article Editor Agent reviews the draft before it is treated as
   publishable.

The writer agent must not select the topic, invent a new thesis, or polish a
blocked draft. It writes from the selected source scene, preserves the approved
thesis, teaches vocabulary only after reader need is clear, and includes draft
notes for the editor.

The opening lab must test at least three candidates: a human-consequence
opening, a scene-first opening, and a mechanism-first opening included to expose
why system-first writing is weaker unless proven otherwise.

## Consequences

The education layer gains a stricter public-article pipeline:
commission first, opening lab second, draft third, review fourth.

This adds friction, but the friction is intentional. It protects the work from
the exact failure mode identified in feedback: a fluent draft with weak story,
weak stakes, unbuilt context, and generic AI cadence.
