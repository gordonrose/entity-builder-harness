<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.templates.article-editor-brief
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: template
  purpose: Document Article Editor Brief.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Article Editor Brief

## Metadata

- Candidate title:
- Source packet:
- Reader-world research packet:
- Scene cards:
- Source material:
- Audience:
- Profiles used:
- Writing references or research consulted:
- Draft readiness: approved / blocked / insufficient material

## Material Sufficiency

Summarize the Article Reporter source packet.

Include:

- core incident
- exact moment
- visible artifact
- artifact availability
- real reader-world bridge
- reader-world scene seeds and recognition patterns
- only-I-could-write-this details
- missing material
- source packet decision

## Article Premise

State the proposed article in one plain paragraph.

## Central Story

Describe what actually happened in sequence.

Include:

- protagonist or point of view
- what they wanted
- what changed
- what became difficult
- what was discovered

## Source Scene Inventory

List concrete scenes found in the source material before selecting an opening.
Use the scene cards as the source of truth.

For each scene include:

- what happened
- who wanted something
- visible friction
- real downside if ignored
- concrete details a cold reader can picture
- what changed afterward
- whether the scene is usable, needs more reporting, or should be rejected

Block if no scene has a human actor under pressure.

## Artifact Availability

For every named public artifact, record:

- artifact:
- direct link:
- if unavailable, pulled, archived, paywalled, or known only through secondary
  reporting, what source establishes that:
- how the article will say this to the reader:

Block if the piece relies on a public artifact but gives the reader no honest
route to inspect it or understand why it cannot be inspected directly.

## Reader Tension

Describe what the target reader already feels, fears, wants, or performs but
may not have named yet.

## Reader Prerequisite Ladder

List the steps of understanding the reader needs before the article can use
its central analogy, technical model, or harness mechanism.

Include:

- what the reader already wants
- what hidden cost or pressure follows from that desire
- what normal-world model helps explain the pressure
- what part of the model transfers to the source story
- what part does not transfer and must be created, governed, or explained
- what sentence or section will bridge the gap

Block if the article depends on a technical analogy but the ladder skips the
missing middle step.

## Analogy Transfer Test

For each major analogy, answer:

- analogy:
- what transfers cleanly:
- what does not transfer:
- what the source story or harness had to create:
- where the analogy could mislead the reader:
- what must be stated plainly before drafting:

For example, a human developer analogy does not transfer cleanly to AI chats
unless the article explains that chats are not naturally separate accountable
individuals. The harness must manufacture that separateness upstream through
branch, worktree, session log, write guard, or another boundary.

## Reader-World Research Summary

Summarize the reader-world research packet.

Include:

- source types checked
- 6 to 10 scene seeds gathered
- strongest reader recognition patterns
- 2 to 3 examples that can set the table before the thesis
- examples rejected because they are generic, overused, weakly sourced, or too
  close to a prior article

Block if the article needs audience recognition but has no research packet.

## Real Stakes

Name the downside if the problem is ignored.

Stakes must be more than an observation. Identify a palpable risk, cost, loss,
embarrassment, bad decision, wasted effort, loss of control, loss of memory, or
false confidence.

For AI-output articles, also identify the accountability bottleneck:

- what is being generated quickly:
- what remains slow for humans:
- what becomes expensive if inspectability is too low:
- who owns the result when the assistant is wrong:

## Why Now

Explain why this belongs to the current AI moment.

## Competing Theses

| Thesis | Source arc preserved | What it leaves out | Strength | Verdict |
|---|---|---|---|---|
|  |  |  |  |  |

## Selected Thesis

Name the selected thesis and why it is stronger than the alternatives.

## Rejected Weaker Theses

List true-but-weak lessons that should not drive the article.

## Opening Scene Candidates

For each candidate include:

- scene
- who is present
- what is happening
- what pressure is visible
- where the stakes appear within the first seven lines
- why a cold reader can follow
- why it might fail
- sample opening movement, not a polished draft

## Setting-The-Table Plan

Explain how the article will help a reader recognize the problem before it
states the thesis.

Include:

- the opening scene
- 2 to 3 supporting reader-world situations
- the concrete object under pressure in each situation
- the point at which the article may move from recognition into thesis
- what must not be rushed
- what technical or process model must be taught before the harness mechanism
  appears
- what missing transfer step must be stated directly

## Opening Lab Requirement

Before full article drafting, create an opening lab using
`article-opening-lab.md` and return it to the Article Editor Agent. The full
draft is blocked until an opening passes the human-consequence, felt-stakes,
and cold-reader retell tests.

## Nut Graf

Explain what the article is really about, why the reader should care, and what
is at stake.

The nut graf should arrive after the opening scene has created reader tension.
It should make the article's angle, timeliness, and stakes clear without
flattening the story into a slogan.

## Terms To Teach

List any technical or repo-specific terms the article may need.

For each term include:

- plain-language need before the term appears
- when to introduce it
- whether to name it, translate it, or avoid it

## Cold Reader Bounce Risks

List reasons a reader might stop reading.

Include:

- unbuilt setting
- unexplained jargon
- weak stakes
- abstract nouns without antecedent scene
- insufficient human pressure
- thesis that sounds true but not urgent
- named artifact with no link and no availability explanation
- analogy that assumes the reader already understands the missing middle step
- polished prose that compresses a needed teaching step

## Line 30 Cold-Reader Gate

By roughly line 30, answer:

- what world is the reader in?
- what kind of person does this happen to?
- what object, document, message, meeting, or decision is under pressure?
- why does AI make the situation tempting?
- what can go wrong?
- why should the reader personally care?

If any answer is weak, block or revise the setting-the-table plan.

## Example Ledger Check

Record the check against `docs/education/articles/example-ledger.md`.

Include:

- major anecdotes already used
- examples barred from reuse
- examples approved for this article
- whether selected examples should be retired after publication

## Research Notes

Summarize writing-craft guidance or source research used before advising.

## Quality Rubric

Use `../references/short-magazine-article-quality-bar.md`.

| Category | Score | Evidence | Required change |
|---|---:|---|---|
| Source material density |  |  |  |
| Artifact availability |  |  |  |
| Opening scene |  |  |  |
| Felt stakes |  |  |  |
| Reader orientation |  |  |  |
| Thesis freshness and angle |  |  |  |
| Structure and tension chain |  |  |  |
| Voice match |  |  |  |
| Sentence craft and specificity |  |  |  |
| Ending |  |  |  |

## Editorial Decision

State one:

- Approved to draft
- Blocked pending stronger story
- Blocked pending clearer stakes
- Blocked pending insufficient material/reporting
- Blocked pending better source evidence
- Blocked pending reader-context work
- No publishable article this cycle

Give the reason.
