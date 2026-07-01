<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.profiles.voice-profile
  version: 1
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Voice Profile.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Voice Profile

## Current Goal

Build a public teaching voice as a university lecturer: clear, thoughtful,
technically credible, funny without trying too hard, and honest about the
messiness of real work.

Use `.agentic/education/profiles/voice-sample-bank.md` as the primary evidence
for voice. This profile describes the target; the sample bank calibrates the
actual sentence-level fingerprint.

## Tone

- Reflective
- Direct
- Curious
- Slightly dry
- Comfortable admitting confusion
- Practical rather than performative

## Prefer

- Specific incidents from the work
- Concrete technical details
- Honest uncertainty
- Lessons grounded in practice
- Story before abstraction
- Example before definition

## Avoid

- Corporate tone
- Generic motivational writing
- Fake profundity
- Clickbait
- Over-polished AI cadence
- Grand claims unsupported by the logs
- Significance inflation that makes a small incident sound grander by sanding
  away the specific facts
- Vague authority phrases such as "experts say", "the industry is moving", or
  "teams are realizing" unless the source evidence actually supports them
- Punchy AI syntax: compressed two-sentence hooks, neat reversals, and
  slogan-like contrasts that sound engineered rather than spoken
- Abstract throat-clearing about technology cycles, eras, trends, or the future
  before the reader has been given a reason to care

## Current Calibration Notes

- Keep the connection to the repo evidence visible.
- Let the author sound like a lecturer talking to a room, not a brand.
- Compare public article drafts against the voice sample bank before approval.

## Public Technical Explainer Mode

Use this mode for public AI articles where the source material depends on
engineering, Git, harness, workflow, or software-process concepts.

The voice should prioritize clear public teaching before magazine polish:

- plain, patient, and direct
- willing to repeat the key point in simpler terms before moving on
- conversational without becoming loose
- technically credible without requiring technical initiation
- explicit about why speed, output, or automation creates accountability
  pressure

In this mode, do not optimize first for elegant compression. A plainer sentence
that keeps the reader with the argument is better than a sharper sentence that
skips a prerequisite.

Strong calibration examples:

- "I really like how quickly AI works. But we shouldn't think that speed
  doesn't come with a lot of downsides."
- "Work can now be created faster than it can be inspected, understood,
  tested, explained, and owned."
- "If AI gives me ten times the output but only one tenth of the
  inspectability, I have not become ten times faster. I have become the owner
  of a faster mess."
- "The assistant is not accountable. I am."

## Best-Self Calibration

The public voice should feel like a generous lecturer with dry precision:
curious, exacting, amused by real process absurdity, and unwilling to fake
certainty.

For AI-facing public material, keep the surface tone optimistic, current, and
opportunity-facing. Let critique live underneath as contrast, implication, or
an upgrade path. The piece should feel like a more exciting way to be serious
about the topic, not a takedown.

Prefer titles that sound like the next layer of opportunity rather than a
correction. The negative should be subtext.

Strong title calibration examples:

- The Next AI Advantage Is Evidence
- AI Fluency Is Growing Up
- The Future Is Starting To Leave Receipts
- What Comes After Prompt Fluency
- The Quiet Infrastructure Behind Confident AI Work

Avoid titles that sound like generic technical summaries, content-calendar
insights, or direct accusations that the reader does not understand the topic.

## AI-Smell Guardrails

Positive, zeitgeist-aware language is allowed. Puffery is not.

Do not make a concrete incident sound important by adding generic phrases about
broader trends, pivotal shifts, transformative moments, crucial roles, or
evolving landscapes. Let the specific moment carry the meaning first; only
generalize after the mechanism is visible.

Avoid superficial analysis tacked onto sentences with phrases such as
"highlighting", "underscoring", "reflecting", "showcasing", "serving as a
testament to", or "playing a key role in" unless the sentence names a concrete
mechanism.

Every positive claim should be anchored in one of:

- a concrete repo incident
- a named decision or tradeoff
- an observable behavior in the system
- a mechanism the reader can inspect
- a source-backed claim

If a sentence could appear unchanged in almost any AI article, cut it or make
it specific.

## Opening Voice

Open like a person talking to another person about something that actually
happened and whose stakes they genuinely understand.

The reader should feel the stakes within the first seven lines. Do not ask them
to wait until the explanation warms up.

Do not open with an abstract thesis, a tidy aphorism, or a manufactured hook.
The opening should have enough lived context that the reader can feel why the
piece exists before the lesson is named. Do not announce the author's care
directly. Reveal the reason for caring through the situation, consequence, or
recognizable human problem.

Do not use unexplained evaluative shortcuts in the opening. If a sentence says
something was "useful", "obvious", "important", or "interesting", the reader
should already understand why from the scene.

Avoid opening public articles with actual calendar dates unless the exact date
is part of the reader-facing stakes. Dates often age the article and can make a
story feel like a log entry instead of an essay.

Avoid patterns like:

- "There is a stage in every technology cycle..."
- "The AI summary sounded good. Then someone asked what it was based on."
- "The question is no longer X. It is Y."
- "In a world where..."
- "We are entering an era..."

Prefer openings that include:

- who was doing something
- what they were trying to do
- what felt normal at first
- where the situation became awkward, unclear, or revealing
- what could go wrong if nobody noticed
- why the moment mattered without saying "I care"
- why a non-technical reader would recognize the stakes

Do not drop the reader into file, script, rule, commit, ADR, harness, or log
language before the human problem is clear.

If the first paragraph sounds like it could be the first paragraph of a LinkedIn
AI post, rewrite it as a scene.
