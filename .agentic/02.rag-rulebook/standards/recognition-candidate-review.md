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

## Candidate Lifecycle

Runtime recognition may produce candidate observations:

1. A prompt, response, fixture, or report contains an important unmatched term.
2. The candidate records the term, sentence, suggested category, and reason.
3. The candidate waits for review.

Governed review decides whether to:

- accept the candidate into a curated recognition source
- reject it as too broad, wrong, or unnecessary
- merge it into an existing candidate
- defer it until more examples or corpus coverage appear
- keep it pending while it records a corpus gap

The lifecycle is intentionally slower than prompt recognition. Prompt-time
recognition may notice a term, but only review may change curated vocabulary.

## Outcome Rules

Use `needs-review` when the candidate is still being understood. The file must
live in `recognition-candidates/inbox/`.

Use `accepted` only when the term has a stable meaning, full required coverage,
a curated-source update, and selector evaluation proof. The file must live in
`recognition-candidates/accepted/`.

Use `deferred` when the term may be useful but needs more examples, narrower
scope, or deeper corpus coverage before acceptance. The file must live in
`recognition-candidates/deferred/`.

Use `rejected` when the term is too broad, misleading, one-off, unsafe, or
already handled by generated sources. The file must live in
`recognition-candidates/rejected/`.

Use `merged` when the candidate is a duplicate of another durable candidate.
The file must identify `review.merged_into_candidate_id`. Merged files should
live in `recognition-candidates/merged/` when that directory is introduced.

Use corpus-gap metadata when the term is real but the corpus is not yet strong
enough. A corpus gap is not the same thing as acceptance. It keeps the
candidate pending or deferred until source material, structured rulebook
content, indexed chunks, and selector evaluation proof exist.

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
- staged coverage status for source material, structured rulebook content,
  indexed chunks, and selector evaluation proof

Selector fixtures may use coverage-gap candidates to report gaps, but they must
not use them as evidence that the corpus already contains the answer.

Coverage has three useful states:

- `missing` means no required stage has evidence yet.
- `partial` means some required stages have evidence, but retrieval is not
  fully ready.
- `covered` means every required stage has evidence and the term can be
  accepted if the review outcome also supports it.

The required coverage stages are:

- `source_material` - human-readable source material exists.
- `structured_rulebook` - the source has been converted into governed rulebook
  structure.
- `indexed_chunks` - the governed material can be retrieved as chunks.
- `selector_evaluation` - a fixture proves expected and banned retrieval
  behavior.

## Durable Candidate Locations

Durable candidate records live under:

- `.agentic/02.rag-rulebook/recognition-candidates/inbox/`
- `.agentic/02.rag-rulebook/recognition-candidates/accepted/`
- `.agentic/02.rag-rulebook/recognition-candidates/rejected/`
- `.agentic/02.rag-rulebook/recognition-candidates/deferred/`
- `.agentic/02.rag-rulebook/recognition-candidates/merged/`

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
- full staged corpus coverage when coverage is required
- review decision
- curated-source update
- evaluation fixture coverage
- reviewer identity, reviewed timestamp, and reviewer notes

Accepted candidates must not bypass existing commit gates.

## Review Action Rules

Good review actions:

- run the read-only recognition-candidate review report before choosing a
  terminal decision
- preserve the exact observed sentence
- compare the term with generated sources and existing curated sources
- choose the narrowest stable canonical ID
- keep confidence weights below generated metadata when the term is broad
- defer or reject generic words that could over-route
- record corpus gaps when a term is meaningful but not yet retrievable
- add or update selector fixtures before acceptance

Wrong or banned review actions:

- promoting an inbox candidate by only changing `status`
- accepting a candidate without moving it to the accepted lifecycle location
- accepting a coverage-required term before `coverage.status: covered`
- accepting a term because it appeared once in an ambiguous sentence
- using a candidate to bypass chat/session safety or authorize side effects
- treating a corpus gap as proof that the corpus already answers the request

## Banned Behavior

Do not:

- add every unknown term automatically
- accept one vague term from one prompt without reviewing context
- allow candidates to bypass session safety or authorize side effects
- store full chat transcripts as candidate context by default
- add a curated term without a canonical ID
- accept a coverage-required term before every required coverage stage has
  evidence
- add a curated term without evaluation coverage
- treat planning or explanation language as implementation, commit, deploy, or
  destructive-action permission

## Maintenance Guidance

Prefer small, specific terms with stable meaning.

Reject or defer terms that are generic, one-off, or likely to over-route.

<!-- deterministic-check: allow reason="candidate review category gaps require human review until a candidate validator or review helper is introduced" -->
When repeated candidates point to a missing category, update the schema,
standard, and fixtures before expanding curated vocabulary.
