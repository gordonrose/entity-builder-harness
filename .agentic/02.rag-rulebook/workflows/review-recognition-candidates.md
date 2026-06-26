<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.workflows.review-recognition-candidates
version: 1
status: active
layer: 02.rag-rulebook
domain: governance
disciplines:
- agentic
- architecture
kind: workflow
purpose: Govern review of recognition candidates before curated lookup sources are changed.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.workflows.readme
  path: .agentic/02.rag-rulebook/workflows/README.md
- id: rag-rulebook.standard.recognition-candidate-review
  path: .agentic/02.rag-rulebook/standards/recognition-candidate-review.md
-->
# Review Recognition Candidates Workflow

Use this workflow when reviewing unmatched, ambiguous, or corrected prompt terms
that may become curated recognition-source entries.

## Required Gates

- Follow the current chat-start and write-location gates before editing files.
- Validate recognition sources after any curated-source change.
- Add or update retrieval selector evaluation fixtures for accepted candidates.
- Run the RAG/rulebook commit gate before commit.

## Inputs

- Candidate records under `.agentic/02.rag-rulebook/recognition-candidates/`
- Candidate observations from context packets or chat/session notes
- Existing recognition sources under `.agentic/02.rag-rulebook/recognition-sources/`
- Retrieval selector evaluation fixtures

## Flow

1. Read the candidate term and observed sentence.
2. Decide whether the sentence gives enough context to review the term.
3. Deduplicate against existing candidates and curated source terms.
4. Choose a decision: accept, reject, merge, or defer.
5. If accepting, choose the target curated source, category, canonical ID, and
   confidence weight.
6. Add or update an evaluation fixture proving the term matches safely.
7. Move or update the candidate record with the review decision.
8. Run recognition-source validation and selector evaluations.

## Rules

- Do not auto-accept candidates from runtime observations.
- Do not add a curated term without a sentence-level example.
- Do not add a curated term without a canonical ID.
- Do not add a curated term without evaluation fixture coverage.
- Do not let broad terms override complete session metadata.
- Reject or defer terms that are too generic to route safely.

## Accepted Candidate Output

An accepted candidate should result in:

- a curated recognition-source term
- a retrieval selector evaluation assertion
- an updated candidate record in `accepted/`
- passing RAG/rulebook commit gates

## Rejected Or Deferred Candidate Output

A rejected or deferred candidate should keep:

- the observed term
- the observed sentence
- the decision
- reviewer notes explaining why it was not accepted

This prevents the same ambiguous term from repeatedly re-entering the inbox
without additional evidence.
