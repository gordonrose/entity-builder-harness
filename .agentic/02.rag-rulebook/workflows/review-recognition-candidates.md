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
- Run the recognition-candidate review report before changing candidate
  decisions or curated sources.
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
4. Decide whether the term reveals a corpus gap instead of a vocabulary gap.
5. Choose a decision: keep pending, accept, reject, merge, or defer.
6. If accepting, choose the target curated source, category, canonical ID, and
   confidence weight.
7. Add or update an evaluation fixture proving the term matches safely.
8. Move or update the candidate record with the review decision.
9. Run recognition-candidate validation, recognition-source validation when a
   curated source changed, selector evaluations, and the RAG/rulebook commit
   gate.

## Decision Guide

Keep pending when the term is meaningful but the reviewer is not ready to
choose a terminal decision. Pending records live in `inbox/`.

Accept when the term has a stable meaning, belongs in a specific curated
source, has a canonical ID, has safe confidence, has full required corpus
coverage, and has selector evaluation proof. Accepted records live in
`accepted/`.

Defer when the term may be useful but needs more examples, narrower language,
or deeper corpus coverage. Deferred records live in `deferred/`.

Reject when the term is too broad, unsafe, redundant, misleading, or one-off.
Rejected records live in `rejected/`.

Merge when another candidate already captures the same meaning. Merged records
must point at `review.merged_into_candidate_id`.

<!-- deterministic-check: allow reason="candidate corpus-gap triage remains human-reviewed until a review helper is introduced" -->
When a prompt reveals missing subject matter, update `coverage` and keep the
candidate pending or deferred. Do not accept it merely because the term is
important.

## Rules

- Do not auto-accept candidates from runtime observations.
- Do not add a curated term without a sentence-level example.
- Do not add a curated term without a canonical ID.
- Do not add a curated term without evaluation fixture coverage.
- Do not let broad terms bypass session safety, authorize side effects, or cross corpus boundaries without request-context support.
- Reject or defer terms that are too generic to route safely.

## Accepted Candidate Output

An accepted candidate should result in:

- a curated recognition-source term
- a retrieval selector evaluation assertion
- an updated candidate record in `accepted/`
- reviewer, reviewed timestamp, and reviewer notes
- passing RAG/rulebook commit gates

## Rejected Or Deferred Candidate Output

A rejected or deferred candidate should keep:

- the observed term
- the observed sentence
- the decision
- reviewer notes explaining why it was not accepted
- reviewer and reviewed timestamp

This prevents the same ambiguous term from repeatedly re-entering the inbox
without additional evidence.
