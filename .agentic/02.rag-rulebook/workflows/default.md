<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.workflows.default
version: 1
status: active
layer: 02.rag-rulebook
domain: governance
disciplines:
- agentic
- architecture
kind: workflow
purpose: Govern RAG and rulebook layer design, corpus, index, retrieval, and context-packet changes.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.workflows.readme
  path: .agentic/02.rag-rulebook/workflows/README.md
- id: chat.script.classification.classify-task
  path: scripts/00.chat/classification/classify-task/script.sh
-->
# RAG/Rulebook Default Workflow

Use this workflow for changes to reusable RAG/rulebook machinery, including
intent models, corpus generation, YAML rulebook schemas, chunking, graph or
index design, context packets, and standalone RAG service boundaries.

## Required Gates

Follow the current chat-start and write-location gates before editing files.
If the task also changes chat startup, git governance, artifact metadata, or
another layer's workflow, split the work into separate governed phases.

## Rules

- Keep the RAG/rulebook machinery separate from domain corpus content.
- For planning, discovery, and investigation prompts that depend on repo
  rulebook knowledge, use `skills/ab-context-evaluation.md`: query the local
  RAG runtime, verify targeted source files directly, compare the two evidence
  paths, and report RAG misses or improvements.
- Treat numbered corpora such as `corpus.01.harness`,
  `corpus.02.rag-rulebook`, `corpus.03.product`, `corpus.04.deploy`, and
  `corpus.05.education` as modular inputs, not one merged instruction corpus.
- Prefer structured schemas, indexes, and deterministic graph expansion before
  semantic retrieval.
- Do not build a RAG server, MCP server, or executable runtime unless the user
  explicitly asks for that implementation slice.
- Do not move existing prototype rulebook artifacts without the artifact path
  migration workflow.
- If corpus ownership is unclear, stop and ask whether to update the layer
  boundary before continuing.
- If source material is created, changed, removed, or reorganized in a way that
  affects rulebook knowledge, use `review-okf-source-material.md` before
  `derive-rules-from-source.md`. Do not treat downstream rules, chunks, or
  selector evaluations as current until review, derivation, and validation are
  complete.

## Default Flow

1. Identify whether the task is about reusable RAG/rulebook machinery or a
   domain corpus.
2. Name the intended domain corpus when one is involved.
3. Decide whether the output is a schema, workflow, index, chunk model,
   context-packet model, service boundary, or migration note.
4. Keep the change to one small artifact or scaffold unless explicitly asked
   to perform a migration.
5. Check `plans/repo-plan.md` when choosing the next small slice.
6. For planning, discovery, or investigation tasks, run the A/B context
   evaluation skill before treating the answer as complete.
7. If source material drives the change, create or update an OKF
   source-material review record and complete the reviewer loop before
   derivation.
8. After source review acceptance, create or update a derivation report that
   names claims, drift, conflicts, affected artifacts, and validation.
9. Validate YAML or metadata headers when edited.
10. Summarize boundaries, assumptions, and any deferred migration.
