<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.generate-rulebook-chunks.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: chunking
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the read-only rulebook chunk generator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.scripts.readme
  path: scripts/02.rag-rulebook/README.md
- id: rag-rulebook.script.generate-rulebook-chunks
  path: scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh
-->
# Generate Rulebook Chunks

`script.sh` emits deterministic retrieval chunks from a validated
`rag-rulebook/rulebook-index/v1` JSON document.

It reads chunk candidates from the index and renders chunks from structured
sections such as:

- artifact summaries
- individual rules
- rule-pack agent steps
- rule-pack required checks

The script validates the input index before generating chunks. It does not
modify files, write generated chunk files, call the network, use embeddings, or
split files by arbitrary character windows.

Generate chunks from the current prototype corpus and current
`docs/02.rag-rulebook/rules/` corpus content:

```bash
bash scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh --generate-current --pretty
```

Generate chunks from a saved index:

```bash
bash scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh --index /tmp/rulebook-index.json --pretty
```

Run the smoke test:

```bash
bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh
```
