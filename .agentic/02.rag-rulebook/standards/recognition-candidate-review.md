<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.standard.recognition-candidate-review
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: standard
purpose: Define how unmatched or ambiguous recognition candidates are recorded and reviewed before curated-source changes.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.schema.recognition-candidate
  path: .agentic/02.rag-rulebook/schemas/recognition-candidate.schema.yml
- id: rag-rulebook.workflow.review-recognition-candidates
  path: .agentic/02.rag-rulebook/workflows/review-recognition-candidates.md
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.script.validate-recognition-candidates
  path: scripts/02.rag-rulebook/validate-recognition-candidates/script.sh
-->
# Recognition Candidate Review

## Purpose

Define the maintenance loop for prompt terms that are important but not yet
covered by generated or curated recognition sources.

Recognition happens at runtime. Curated-source maintenance happens only after
review.

## Two-Stage Loop

Runtime recognition may produce candidate observations:

1. A prompt, response, fixture, or report contains an important unmatched term.
2. The candidate records the term, sentence, suggested category, and reason.
3. The candidate waits for review.

Governed review decides whether to:

- accept the candidate into a curated recognition source
- reject it as too broad, wrong, or unnecessary
- merge it into an existing candidate
- defer it until more examples appear

## Candidate Context Rule

Every candidate must include the sentence or sentence-like prompt fragment where
the term appeared.

The sentence is required because isolated terms are often ambiguous. For
example, `server` alone is too broad, while `MCP server` in the sentence `How do
I update my harness so we can deploy it behind an MCP server?` carries service
architecture meaning.

Do not store whole transcripts by default. Store the smallest useful context.

## Corpus Coverage Rule

Some candidates identify real terms before the repo has enough source material
to answer from corpus knowledge.

When that happens, record the candidate as a coverage gap instead of accepting
it into active curated vocabulary.

For example, `MCP server` may be a useful service architecture term, but if the
corpus does not yet explain MCP-server deployment behind the harness, the
candidate should preserve:

- the observed sentence
- the likely target corpus or corpora
- the missing topic
- a `missing-corpus` gap ID
- the source material needed before acceptance

Selector fixtures may use coverage-gap candidates to report gaps, but they must
not use them as evidence that the corpus already contains the answer.

## Durable Candidate Locations

Durable candidate records live under:

- `.agentic/02.rag-rulebook/recognition-candidates/inbox/`
- `.agentic/02.rag-rulebook/recognition-candidates/accepted/`
- `.agentic/02.rag-rulebook/recognition-candidates/rejected/`
- `.agentic/02.rag-rulebook/recognition-candidates/deferred/`

Session-local observations may stay in context packets or chat logs until a
human chooses to promote them into the durable inbox.

## Acceptance Rules

A candidate may become a curated recognition-source term only when it has:

- observed term
- observed sentence
- suggested source ID
- suggested category
- suggested canonical ID
- confidence weight
- corpus coverage evidence when coverage is required
- review decision
- curated-source update
- evaluation fixture coverage

Accepted candidates must not bypass existing commit gates.

## Banned Behavior

Do not:

- add every unknown term automatically
- accept one vague term from one prompt without reviewing context
- allow candidates to override complete session metadata
- store full chat transcripts as candidate context by default
- add a curated term without a canonical ID
- accept a coverage-required term before the corpus has source material for it
- add a curated term without evaluation coverage
- treat planning or explanation language as implementation, commit, deploy, or
  destructive-action permission

## Maintenance Guidance

Prefer small, specific terms with stable meaning.

Reject or defer terms that are generic, one-off, or likely to over-route.

<!-- deterministic-check: allow reason="candidate review category gaps require human review until a candidate validator or review helper is introduced" -->
When repeated candidates point to a missing category, update the schema,
standard, and fixtures before expanding curated vocabulary.
