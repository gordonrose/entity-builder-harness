# 0005 Require Reader-World Research For Public Articles

Status: accepted
Date: 2026-06-16

## Context

The public article pipeline became stronger after adding source packets,
scene cards, editor briefs, opening labs, and separate writer/editor agents.
The first new draft was closer to the author's voice, but feedback showed a
remaining failure mode: the article could open from a real anecdote and still
lose the reader soon afterward.

The problem was setting. The draft moved from one strong author-owned story
into the thesis before giving the reader enough recognizable examples to
understand the world being described. A non-technical or lightly technical
reader needs concrete situations before the article asks them to follow a
harness story, especially when the subject is AI work, confidence, records,
or decision quality.

The user also identified a reuse risk. Strong anecdotes should not be recycled
from article to article. Reuse makes the work feel thin and teaches the
harness to lean on familiar material instead of reporting the current piece.

## Decision

Public short articles now require a reader-world research packet before
drafting unless the Article Editor Agent records a specific exception.

The reader-world research packet must:

1. Review public or author-owned sources where the intended audience's world is
   visible, such as Reddit, Substack, X/Twitter, LinkedIn, founder/operator
   blogs, product forums, customer support stories, newsletters, essays, or
   transcripts.
2. Convert sources into 6 to 10 scene seeds rather than copying phrasing.
3. Identify recognition patterns, concrete objects, human pressure, and
   possible downside.
4. Propose 2 to 3 setting-the-table examples for the article.
5. Check `docs/education/articles/example-ledger.md`.
6. Answer the line 30 cold-reader gate: world, person, object under pressure,
   AI temptation, downside, and personal relevance.

The Article Reporter Agent owns this packet. The Article Editor Agent must
block public article drafting when the packet is missing or too thin. The
Article Writer Agent must use the approved packet to help the reader recognize
the problem before stating the thesis.

Major anecdotes from prior articles must not be reused as the opening, main
evidence, or primary reader bridge.

## Consequences

The article pipeline becomes slower and more research-heavy. That is
intentional. The cost is acceptable because the alternative is a polished draft
that sounds plausible while asking the reader to make too many leaps.

The source packet still protects the author's real story. The reader-world
research packet protects the reader's context. Both are required for strong
public articles.

This decision also makes `no publishable article this cycle` easier to choose.
If the repo story is real but the reader-world setting cannot be built without
inventing examples, the article should pause until more source material exists.
