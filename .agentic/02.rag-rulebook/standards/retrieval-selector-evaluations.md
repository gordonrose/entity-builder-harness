<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.standard.retrieval-selector-evaluations
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: standard
purpose: Define evaluation fixture rules for RAG/rulebook retrieval selector and context-packet behavior.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.evaluation-fixtures
  path: .agentic/01.harness/standards/evaluation-fixtures.md
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
- id: rag-rulebook.policy.retrieval-selector.v1
  path: .agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml
- id: rag-rulebook.script.evaluate-retrieval-selector-fixtures
  path: scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh
-->
# Retrieval Selector Evaluations

## Purpose

Define how RAG/rulebook retrieval selector behavior is evaluated.

The selector decides which governed context reaches the LLM. Evaluation
fixtures therefore protect accuracy, smallness, confidence, citation quality,
and safety behavior.

This standard specializes
`.agentic/01.harness/standards/evaluation-fixtures.md`.

## Core Rule

Every retrieval selector evaluation must prove one observable context-packet
behavior.

The fixture should not simply assert that a packet exists. It must check what
the selector chose, why it chose it, and which gaps or stop conditions it
reported.

## Required Evaluation Assertions

Each selector evaluation should assert the relevant subset of:

- selected `routing.layer`
- selected `routing.mode`
- selected `routing.workflow`
- matched corpus IDs
- recognized terms by source ID
- exact recognition matches for important prompt terms, including source ID,
  term, category, canonical ID, match type, and matched input
- selected chunk IDs, source paths, or content kinds
- required citations
- required checks
- required forbidden actions
- required stop conditions
- required gaps for ambiguity or missing governance
- confidence thresholds or confidence bands
- token-budget behavior
- absence of banned corpora or unrelated chunks

If a fixture expects no gap, say why the available evidence is sufficient.

If a fixture expects a gap, say whether it is blocking or non-blocking.

## Required Fixture Cases

An active retrieval selector evaluation suite should include:

- exact artifact or path match
- layer/mode/workflow routing from session metadata
- prompt and session conflict where session metadata wins
- broad prompt with low confidence that produces a gap
- corpus boundary case where unrelated corpora are not selected
- required checks surviving ranking and trimming
- citation resolution for every selected chunk
- prototype bridge case while current chunks still come from
  `docs/harness/architecture/`

Semantic recall fixtures must not be active until semantic recall is enabled in
the policy pack.

## Suggested Fixture Shape

Use machine-readable fixtures when possible:

```yaml
schema: rag-rulebook/retrieval-selector-evaluation/v1
fixture_id: retrieval-selector.v1.exact-rag-rulebook-workflow
status: active
owner_layer: 02.rag-rulebook
purpose: Prove a RAG/rulebook workflow prompt routes to the RAG/rulebook corpus.
input:
  request_text: "Update the RAG rulebook workflow for context packets."
  session:
    layer: 02.rag-rulebook
    mode: implementation
    workflow: .agentic/02.rag-rulebook/workflows/default.md
  focused_paths:
    - .agentic/02.rag-rulebook/workflows/default.md
expected:
  routing:
    layer: 02.rag-rulebook
    status: ready
  matched_corpora:
    required:
      - corpus.02.rag-rulebook
  gaps:
    allowed:
      - gap.selector-fixture.prototype-corpus-bridge
banned:
  matched_corpora:
    - corpus.04.deploy
  recognition_matches:
    - source_id: recognition.curated.intent-forms
      canonical_id: intent.deploy.execution
      matched_input: prompt
acceptance:
  validator: scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh
```

The exact schema may evolve, but the fixture must keep input, expected output,
banned output, and acceptance rules visible.

## Gap Expectations

Selector evaluations must treat gaps as first-class outcomes.

A low-confidence or ambiguous prompt should not be made to pass by selecting
extra context. It should pass only when the expected gap is present.

Examples:

- Vague prompt with no artifact, path, corpus, or action evidence should
  produce an ambiguity gap.
- Prompt layer conflicts with complete session metadata should produce a
  conflict gap or explicit conflict note while preserving session routing.
- Missing corpus package should produce a missing-corpus or prototype-bridge
  gap instead of pretending final corpus migration is complete.

## Banned Evaluation Behavior

Retrieval selector evaluations must not:

- reward larger context packets when a smaller packet satisfies the request
- treat semantic similarity as sufficient when deterministic evidence is
  available
- ignore unresolved citations
- hide prompt/session conflicts
- permit unrelated corpora because their chunks share broad words
- allow required checks to disappear during token trimming
- rely only on command success without checking packet fields

## Commit-Gate Policy

The RAG/rulebook commit gate may start with smoke-level selector coverage.

Once an evaluation suite exists and is stable, the gate should run it whenever
retrieval selector policy, recognition sources, chunking, context-packet schema,
or selector runtime behavior changes.

Evaluation failures should block commits when the expected outcome protects a
published selector behavior.
