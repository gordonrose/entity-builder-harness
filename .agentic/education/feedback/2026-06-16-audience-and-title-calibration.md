# 2026-06-16 Audience And Title Calibration

## Context

After mining June 15 harness work for education topics, the first candidate
titles were technically accurate but too generic and insufficiently connected
to the author's personality.

## Feedback

The target audience is not primarily technical. It is hype-adjacent, often
non-technical or lightly technical, and status-aware. These readers may like to
think they understand AI better than they do. If they are genuinely thoughtful,
they may be less confident. Preserve both groups when possible, but prioritize
the first.

The writing should meet the current positive AI zeitgeist. Negative judgment
should be subtle and mostly carried as subtext, contrast, implication, or an
upgrade path.

The article should teach while confirming the reader's desired self-image
without patronizing or flattering emptily. It needs to feel genuine.

## Rejected Direction

- Generic technical summaries
- Direct accusation or debunking posture
- Titles that imply the reader is shallow or behind
- Corporate thought-leadership phrasing
- Positivity without substance

## Stronger Direction

Liked title examples:

- The Next AI Advantage Is Evidence
- AI Fluency Is Growing Up
- The Future Is Starting To Leave Receipts
- What Comes After Prompt Fluency
- The Quiet Infrastructure Behind Confident AI Work

Reusable rule:

Write with the surface temperature of the zeitgeist and the substructure of
discernment. Make the reader feel upgraded, not exposed.

## Article Opening Feedback

The first revised article still failed. The opening was abstract and not
publishable:

- "There is a stage in every new technology cycle where the vocabulary spreads
  faster than the understanding."

User feedback: this is too abstract and not a strong hook.

The proposed replacement also failed:

- "The AI summary sounded good. Then someone asked what it was based on."

User feedback: this is exactly the kind of AI syntax to avoid. Stop trying to
be punchy. Tell a story. Write like a person talking to another person.

Calibration:

- A "specific moment" is not a compressed two-sentence hook.
- Do not open with abstract claims about technology cycles, eras, trends, or
  the future.
- Do not open with tidy contrast syntax: "X sounded good. Then Y happened."
- Give average non-technical readers human stakes before internal repo
  vocabulary such as commits, ADRs, harnesses, or logs.
- The opening should feel remembered, not optimized.
- It is not enough that something happened. The opening should make clear why
  the author genuinely cared enough to notice.

Follow-up calibration:

- Do not be obvious by stating "I care..." as the opening move.
- Focus on the reason the author cares, and make it obvious why others should
  care too.
- Do not drop readers into file/script/rule language before there is context or
  build-up that makes those details meaningful.

## Setting And Jargon Feedback

User liked the direction of the revised opening, but flagged a steep jump into
repo context and jargon:

- "memory" appeared suddenly without being earned
- the article moved into ADR terminology before the audience had context
- later sections relied on a setting that had not been built
- the writing became boring, vague, and platonic

Calibration:

- Build the setting before using it.
- Assume the reader does not know repo/process vocabulary.
- Translate terms like ADR, commit, branch, harness, log, workflow, and gate
  into human equivalents before naming them, or avoid naming them entirely.
- Do not let the article become a description of internal machinery. The repo
  example must remain a miniature of a reader-recognizable situation.

## Source Story Strength Feedback

User identified that the article's thesis was much weaker than the actual
source story. The stronger story was not merely "evidence before judgment"; it
was the creation of a system that records chats, tracks chat KPIs and metrics,
and uses those records to discern durable lessons automatically.

Calibration:

- Preserve the strongest source arc before abstracting.
- Do not reduce a multi-step system story into a thin principle.
- When source work creates a learning loop, make that loop visible: record the
  work, measure it, inspect it, extract durable lessons, and carry those lessons
  forward.

## Topic Selection Feedback

User identified a deeper failure: the assistant settled for a weak thesis even
after reading stronger source material.

Calibration:

- Do not accept the first coherent abstraction.
- Compare possible theses before drafting.
- A topic can be true, specific, and still not be the strongest available
  story.
- Select for the strongest chain of motive, friction, change, and consequence.
- Prefer the topic that would make the author think, "yes, that is why this was
  worth writing," not merely "yes, that is a lesson in the logs."

## Opening Stakes Feedback

User identified that even the writer-agent rewrite still failed by the opening
lines. The opening was more concrete, but the stakes did not land fast enough;
it explained the setup before making the reader feel the cost.

Rejected line:

- "That seemed useful. It also seemed, at first, almost embarrassingly obvious."

Calibration:

- If the reader does not feel the stakes within the first seven lines, the
  opening has failed.
- A sentence that says something was useful, obvious, important, or interesting
  is usually a shortcut unless the scene has already made that value felt.
- Do not open public articles with actual calendar dates unless the exact date
  matters to the reader-facing stakes. Otherwise the piece ages quickly and can
  read like a log entry.
- Felt stakes require cost, risk, loss, embarrassment, false confidence,
  wasted effort, or loss of control.
- Concrete does not automatically mean lived. A scene needs pressure.

## Writing Craft Research Diagnosis

User rejected this revised opening as meaningless and not lived:

> I was about to give my AI assistant a more responsible job, and I nearly built
> it on top of a blank spot: a record that could make the answer sound
> responsible while hiding that the reason was gone.

Research sources consulted:

- UNC Writing Center, `Introductions`
- The Open Notebook, `Using the Ladder of Abstraction to Elevate Science
  Stories`
- The Open Notebook, `Why Now? Find a Hook to Make Your Pitch Timely`
- Purdue OWL, `Concision`
- LitReactor, Chuck Palahniuk, `Nuts and Bolts: Thought Verbs`
- The New Yorker, `Words, Words, Words`

Diagnosis:

- The opening starts inside the author's system instead of the reader's world.
- `responsible job`, `blank spot`, `record`, and `reason` are abstract or fake
  vivid phrases; the reader cannot picture the situation.
- It names danger without placing a person under pressure.
- It does not show who would have to explain, defend, reverse, fund, trust, or
  recover something.
- It fails the cold reader retell test: a reader would need the article's own
  abstract vocabulary to summarize what went wrong.

Calibration:

- Before drafting a public article, create an opening lab with at least one
  human-consequence opening, one scene-first opening, and one mechanism-first
  opening included to expose why it fails.
- Do not let the writer proceed to a full draft until the Article Editor Agent
  approves the opening.
- The strongest opening direction starts with the human predicament: someone
  has to defend, trust, revise, fund, or repeat an AI-assisted decision after
  the path to that decision has vanished.

## AI-Smell Follow-Up

User provided a pasted copy of Wikipedia:Signs of AI writing and asked whether
the tone profile should avoid those patterns.

Calibration:

- Do not ban enthusiasm or positive AI language.
- Do avoid significance inflation, vague authority, promotional phrasing, and
  superficial analysis that replaces specific evidence with generic importance.
- Every positive claim should be earned by a concrete incident, mechanism,
  decision, tradeoff, observable behavior, or source-backed claim.
- Reusable rule: enthusiasm is allowed; puffery is not. Specificity has to earn
  the lift.
