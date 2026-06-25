<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0001-the-next-ai-advantage-is-evidence-opening-lab
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Article Opening Lab.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Article Opening Lab

## Metadata

- Article: `docs/education/articles/0001-the-next-ai-advantage-is-evidence.md`
- Editor brief:
  `docs/education/articles/0001-the-next-ai-advantage-is-evidence.editor-brief.md`
- Source scene: The attempted decision-recording rule failed because the
  session record was too thin to support the judgment.
- Audience: hype-adjacent, non-technical or lightly technical AI readers
- Profiles used:
  - `.agentic/education/profiles/audience-profile.md`
  - `.agentic/education/profiles/voice-profile.md`
  - `.agentic/education/profiles/storytelling-profile.md`
- Craft references used:
  - `.agentic/education/references/article-writing-craft.md`
  - `.agentic/education/references/writing-style-principles.md`
  - `.agentic/education/references/storytelling-principles.md`
- Opening status: legacy-approved for prior rewrite; blocked under current
  source-packet pipeline

## Current Pipeline Note

This opening lab was approved before the education layer required source
packets, scene cards, and non-hypothetical primary bridges. Under the current
pipeline, the article is blocked pending a source packet and approved scene
cards.

## Human Predicament

A person has used AI to help produce or change a piece of work. The work looks
clean enough to trust, but the path to the recommendation has disappeared. The
person may later have to explain, defend, reverse, or repeat the decision
without knowing which question, objection, or tradeoff caused the final answer.

The bad outcome is not "missing documentation" in the abstract. The bad outcome
is false confidence: a tidy answer that appears defensible because the messy
reasoning has vanished from view.

## Opening Candidates

### Candidate 1: Human Consequence

- Draft opening:

  Imagine a team using AI to clean up a one-page recommendation: launch the
  customer pilot next month, or wait.

  In the first version, the warning is plain. Support is thin. The customer is
  high profile. A bad rollout would be expensive to unwind. After a few rounds
  of prompting, the note reads better. The warning has become a sentence near
  the bottom. The recommendation sounds calmer. By the time it reaches the
  meeting, everyone can see what it says.

  No one can quite say why it now says that.

- First concrete noun/action: team using AI to clean up a one-page
  recommendation
- Who is under pressure: the person who has to present or defend the
  recommendation in the meeting
- Felt stake by line seven: a customer pilot could be launched or delayed from
  a polished note whose changed reasoning nobody can explain
- Cold reader retell: AI helped improve a recommendation's surface, but the
  team lost the path back to why the recommendation changed
- Abstract words used before they are earned: none serious; `recommendation`
  is grounded in the customer-pilot choice
- Verdict: approved for the prior article rewrite; under the current
  source-packet pipeline this opening is insufficient because it uses a
  hypothetical as the primary reader bridge

### Candidate 2: Scene First

- Draft opening:

  A strategy note changes between one version and the next. The recommendation
  gets firmer. A risk that looked awkward becomes a footnote. The final version
  reads better, which is why nobody notices the more important problem until
  the meeting: nobody can say what changed the argument.

- First concrete noun/action: strategy note changes
- Who is under pressure: the team in the meeting
- Felt stake by line seven: the team cannot explain why the recommendation
  changed
- Cold reader retell: the AI-assisted document improved on the surface while
  losing the reason for the change
- Abstract words used before they are earned: none serious
- Verdict: strong, but it is illustrative rather than from the actual source
  scene

### Candidate 3: Mechanism First

This candidate exists to show the tempting but weaker system-first version.

- Draft opening:

  I was about to give my AI assistant a more responsible job, and I nearly
  built it on top of a blank spot: a record that could make the answer sound
  responsible while hiding that the reason was gone.

- First concrete noun/action: none strong; `assistant` is concrete-ish but not
  active in a human situation
- Who is under pressure: unclear
- Felt stake by line seven: named, but not felt
- Cold reader retell: difficult without abstract terms such as `record`,
  `responsible`, and `reason`
- Abstract words used before they are earned: `responsible`, `blank spot`,
  `record`, `reason`
- Why it fails or why it unexpectedly works: it names the thesis but does not
  dramatize the predicament; the metaphor sounds vivid while hiding the missing
  human situation
- Verdict: reject

## Comparison

- Candidate 1 makes the reader feel the cost fastest because it starts with the
  social consequence: a clean answer that cannot be explained.
- Candidate 2 is more scene-like and may be useful as the bridge after the
  opening.
- Candidate 3 is the current failure mode: mechanism-first, abstract, and
  dependent on fake vividness.

The current article draft proceeds from Candidate 1, then brings in the actual
source story once the reader understands the human predicament. Under the
current source-packet pipeline, this must be replaced or reworked from approved
source material before the article can be treated as publishable.

## Banned Or Delayed Language

- evidence
- system
- process
- record
- memory
- responsible
- important
- useful
- obvious
- interesting
- blank spot
- learning loop

## Editor Decision

Blocked under current source-packet pipeline.

The revised opening begins with the defensibility problem, but it does so
through a hypothetical customer-pilot recommendation. The article now needs a
source packet, scene cards, and a non-hypothetical opening or primary reader
bridge before it can be treated as publishable.
