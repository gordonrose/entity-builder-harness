<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.references.article-writing-craft
  version: 1
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Article Writing Craft.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Article Writing Craft

Use this as an operational reference for public article drafting. These are not
style ornaments; they are gates that protect the reader from vague, synthetic,
or system-first writing.

## Sources Reviewed

- UNC Writing Center, `Introductions`:
  https://writingcenter.unc.edu/tips-and-tools/introductions/
- The Open Notebook, `Using the Ladder of Abstraction to Elevate Science
  Stories`:
  https://www.theopennotebook.com/2023/05/30/using-the-ladder-of-abstraction-to-elevate-science-stories/
- The Open Notebook, `Why Now? Find a Hook to Make Your Pitch Timely`:
  https://www.theopennotebook.com/2026/02/24/why-now-find-a-hook-to-make-your-pitch-timely/
- Purdue OWL, `Concision`:
  https://owl.purdue.edu/owl/general_writing/academic_writing/conciseness/index.html
- LitReactor, Chuck Palahniuk, `Nuts and Bolts: Thought Verbs`:
  https://litreactor.com/essays/chuck-palahniuk/nuts-and-bolts-%E2%80%9Cthought%E2%80%9D-verbs
- The New Yorker, `Words, Words, Words`:
  https://www.newyorker.com/books/page-turner/words-words-words

## Durable Lessons

### Bridge From The Reader's World

The opening has to carry the reader from their ordinary life into the article's
world. A technically true source scene is not enough if it begins inside an
internal system the reader has not been helped to care about.

Operational test:

- Can a cold reader name the human situation without repo or system vocabulary?
- Can they say why this might happen to them, their team, or someone they
  recognize?
- Has the writer gathered examples from places where the intended reader
  actually talks, such as Reddit, Substack, X/Twitter, LinkedIn, founder blogs,
  operator forums, or customer support stories?
- Are those examples being used as scene seeds, not copied language or generic
  proof that "people are talking about this"?

### No Thesis Before Recognition

Do not ask the reader to accept the thesis before they can recognize the
problem.

A strong article may open with one author-owned story, but the writer still
has to set the table. For a non-technical or lightly technical reader, one
internal anecdote rarely creates enough context. The article usually needs 2
to 3 concrete reader-world situations before or near the nut graf: a deck, a
Slack message, a board update, a customer email, a meeting summary, a roadmap,
or another object under pressure.

Operational test:

- Before the thesis appears, what examples let the reader think "I know this
  world"?
- Are those examples fresh for this article, or are they being recycled from a
  prior piece?
- If the reader stopped by roughly line 30, could they explain why the article
  matters without using the writer's abstract vocabulary?

### Stay Low On The Ladder First

Start with concrete, imageable detail before climbing toward concepts. Words
such as `evidence`, `record`, `system`, `process`, `responsibility`,
`reasoning`, and `memory` are not forbidden, but they must be earned by
something the reader can picture.

Operational test:

- What is the first concrete object, action, person, place, or social moment?
- Is the opening made mostly of nouns the reader can see or nouns the writer is
  asking the reader to believe?

### Make Stakes Felt, Not Mentioned

Stakes are not the word `risk`. Stakes are a felt consequence: a decision that
may be wrong, a recommendation someone has to defend, money or time wasted, a
loss of control, public embarrassment, false confidence, or a lesson that cannot
compound.

Operational test:

- By line seven, what can go wrong?
- Who pays the cost?
- What would be harder to explain, defend, recover, or fix?

### Use Specific Words That Do Work

Concise writing is not merely short writing. It uses words that carry more
meaning. Weak phrases often have a polished surface but little load-bearing
value.

Red flags:

- "responsible job"
- "blank spot"
- "the system"
- "the process"
- "the reason was gone"
- "this matters"
- "that was useful"
- "that seemed obvious"

Operational test:

- Which words could be replaced by a camera, a calendar invite, a document, a
  question in a meeting, a deleted paragraph, a missing note, or a person
  trying to explain themselves?

### Unpack Thought And Value Labels

Do not tell the reader something was useful, obvious, important, interesting,
confusing, responsible, or risky until the scene has made that value felt.
Unpack the evidence instead.

Operational test:

- If the value label is removed, does the scene still make the value obvious?
- Can the reader infer the pressure from actions, missing evidence, or social
  consequence?

### Prefer Ordinary Human Life Over Conceptual Drama

Public articles should not open with system mechanics dressed up as drama. A
reader needs a person under pressure, not an abstract machine with a problem.

Operational test:

- Is someone going to have to explain, defend, decide, spend, trust, reverse,
  admit, or recover something?
- If not, the opening is probably still mechanism-first.

### Cut Fake Vividness

A metaphor can sound vivid while hiding vagueness. Phrases like `blank spot`,
`memory theater`, `learning loop`, and `receipts` only work after the piece has
shown what is actually missing, fake, repeated, or provable.

Operational test:

- Does the metaphor create a picture, or does it merely decorate an abstraction?
- Could the reader retell the problem without using the metaphor?

## Cold Reader Retell Test

After the first seven lines, a cold reader should be able to tell a friend:

- who is in trouble
- what they were trying to do
- what went missing or wrong
- what could happen because of it

If they need the article's abstract vocabulary to retell it, the opening has
failed.

## Line 30 Gate

After roughly the first 30 lines, a cold reader should also be able to say:

- what world the article is in
- what kind of person this happens to
- what object, document, message, meeting, or decision is under pressure
- why AI makes the situation tempting
- what can go wrong
- why they should personally care

If the article moves into thesis, jargon, or internal machinery before those
answers are clear, it is setting the table too quickly.

## Failure Pattern: Fake Stakes

Fake stakes happen when prose says danger exists but does not make the reader
feel a person, decision, cost, embarrassment, wasted effort, false confidence,
or loss of control.

Rejected example:

> I was about to give my AI assistant a more responsible job, and I nearly built
> it on top of a blank spot: a record that could make the answer sound
> responsible while hiding that the reason was gone.

Why it fails:

- `responsible job` is not concrete.
- `blank spot` is fake vividness.
- `answer sound responsible` names a vibe, not a situation.
- `the reason was gone` is closer, but still does not show what happened, who
  would rely on it, or what the cost would be.
- The reader cannot retell the problem without borrowing the article's abstract
  terms.

Better direction:

Start from the human predicament: someone has to defend, trust, revise, fund,
or repeat an AI-assisted decision after the path to that decision has vanished.
