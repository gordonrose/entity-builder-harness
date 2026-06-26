<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.generate-retrieval-selector-fixture.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the read-only retrieval selector fixture generator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.scripts.readme
  path: scripts/02.rag-rulebook/README.md
- id: rag-rulebook.script.generate-retrieval-selector-fixture
  path: scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh
-->
# Generate Retrieval Selector Fixture

`script.sh` emits a validated `rag-rulebook/context-packet/v1` packet from the
first deterministic retrieval selector fixture.

It consumes:

- the active retrieval policy pack
- validated recognition sources
- validated recognition candidates, used only for coverage-gap reporting
- request text
- session-like layer, mode, and workflow metadata
- focused path signals
- generated or saved rulebook chunks

It is not the production RAG server and does not perform semantic recall. Its
purpose is to prove that selector ingredients can be combined into a small,
validated context packet before a full runtime exists.

Missing-coverage candidates may produce `missing-corpus` gaps. They do not
select corpora, add chunks, or act as evidence that the corpus already covers a
term.

Generate a fixture from the current prototype chunks:

```bash
bash scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh \
  --generate-current \
  --request-text "Build the first deterministic RAG rulebook retrieval selector fixture." \
  --pretty
```

Generate a fixture from a saved chunk set:

```bash
bash scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh \
  --chunks /tmp/rulebook-chunks.json \
  --session-layer 02.rag-rulebook \
  --session-mode implementation \
  --focused-path .agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml \
  --pretty
```

Run the smoke test:

```bash
bash scripts/02.rag-rulebook/generate-retrieval-selector-fixture/smoke-test.sh
```

## Effects

The command is read-only. It writes only temporary files for validation.
