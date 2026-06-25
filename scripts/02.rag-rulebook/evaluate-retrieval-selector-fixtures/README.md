<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.evaluate-retrieval-selector-fixtures.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the retrieval selector evaluation fixture runner.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.evaluate-retrieval-selector-fixtures
  path: scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh
- id: rag-rulebook.standard.retrieval-selector-evaluations
  path: .agentic/02.rag-rulebook/standards/retrieval-selector-evaluations.md
-->
# Evaluate Retrieval Selector Fixtures

`script.sh` runs machine-readable retrieval selector evaluation fixtures.

The evaluator generates one current chunk set, runs
`generate-retrieval-selector-fixture/script.sh` for each fixture input, then
checks expected and banned packet behavior.

Run all current fixtures:

```bash
bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --current
```

Run one fixture:

```bash
bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh \
  --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/exact-rag-rulebook-workflow.yml \
  --json
```

## Effects

The command is read-only. It writes only temporary generated chunk and packet
files while evaluating fixtures.
