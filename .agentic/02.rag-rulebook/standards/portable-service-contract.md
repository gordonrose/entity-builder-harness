<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.standard.portable-service-contract
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: standard
purpose: Define the portable service boundary for reusable RAG and rulebook machinery.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
- id: rag-rulebook.standard.retrieval-selector-policy-system
  path: .agentic/02.rag-rulebook/standards/retrieval-selector-policy-system.md
-->
# Portable Rulebook/RAG Service Contract

## Purpose

Define the reusable service boundary for turning domain source material into
small, accurate, governed context packets.

The service should be portable across numbered corpora and subcorpora. It
should not be coupled to one repo's current folder layout.

In artifact metadata, the targets identify known seed consumers of this
portable pattern. They are not the final service name and they are not a closed
consumer list. The standalone service/repo target should be named later when
the extraction boundary is explicit.

The service should support numbered corpus IDs such as `corpus.01.harness`,
`corpus.02.rag-rulebook`, `corpus.03.product`, `corpus.04.deploy`,
`corpus.05.education`, and `corpus.06.shared`, plus approved subcorpora.

## Owns

The portable RAG/rulebook service owns:

- corpus package discovery
- source-to-rulebook generation contracts
- YAML rulebook schema expectations
- chunk generation rules
- deterministic index generation
- graph edge generation
- intent normalization contracts
- context-packet assembly
- context-packet validation
- retrieval and reranking policy
- retrieval selector policy packs
- citation and source-reference requirements

## Does Not Own

The service does not own:

- chat startup, chat sessions, worktrees, or git governance
- domain-specific product, design-system, deployment, or harness decisions
- cloud runtime execution
- source Markdown authorship
- migration of committed repo paths
- final agent action after a context packet is returned

Those responsibilities remain with the consuming workbench, domain corpus, or
governed workflow.

## Inputs

The service should accept structured inputs when available:

- user request
- normalized intent candidate
- layer, mode, and workflow metadata
- changed or proposed paths
- open files or focused artifacts
- corpus package manifests
- existing artifact metadata indexes

Natural language is useful evidence, but deterministic inputs should take
precedence when present.

## Outputs

The primary output is a context packet with:

- intent
- routing metadata
- matched corpus packages
- matched rule packs
- matched layer and concern rulesets
- selected chunks
- required checks
- forbidden actions
- stop conditions
- source references and citations
- confidence and gaps

The v1 field contract for this packet is defined in
`.agentic/02.rag-rulebook/schemas/context-packet.schema.yml`.

The service may also emit indexes, graph files, chunk manifests, diagnostics,
and validation reports.

## Retrieval Order

Prefer this order:

1. deterministic intent and task-type matches
2. path and artifact metadata matches
3. required ruleset expansion
4. applies-to and related-ruleset graph expansion
5. keyword or lexical recall
6. semantic/vector recall
7. reranking and token-budget trimming

Semantic recall is a supplement, not the authority.

Retrieval selector behavior should be governed by versioned policy packs as
defined in
`.agentic/02.rag-rulebook/standards/retrieval-selector-policy-system.md`.

## Stop Conditions

Return a gap instead of improvising when:

- no corpus package matches the task
- intent confidence is too low for deterministic routing
- path ownership is ambiguous
- required rulesets or source references are missing
- selected chunks exceed the context budget and cannot be safely trimmed
- a domain corpus claims ownership of another domain's rules
- a corpus package claims ownership of another numbered corpus without an
  explicit relationship

The consuming workflow decides whether to ask a clarifying question, update
governance, or stop.

## Minimum First Implementation

The first implementation should be read-only:

- parse one existing corpus
- emit a deterministic rulebook index
- emit chunk records from structured YAML fields
- validate references and duplicate IDs
- avoid server runtime, embeddings, network calls, and corpus moves
