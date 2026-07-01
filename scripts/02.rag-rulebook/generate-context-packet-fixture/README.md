<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.generate-context-packet-fixture.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: context-packets
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the read-only context-packet fixture generator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.scripts.readme
  path: scripts/02.rag-rulebook/README.md
- id: rag-rulebook.script.generate-context-packet-fixture
  path: scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh
-->
# Generate Context Packet Fixture

`script.sh` emits a small deterministic `rag-rulebook/context-packet/v1`
fixture from a generated or saved `rag-rulebook/chunk-set/v1` JSON document.

It is a fixture builder, not a semantic retrieval engine. It selects a small
ranked chunk subset from request terms, preserves chunk and citation references,
adds checks, forbidden actions, stop conditions, budgets, confidence, and
provenance, then validates the packet before printing it.

Generate a fixture from the current prototype corpus:

```bash
bash scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh \
  --generate-current \
  --pretty
```

Generate a fixture from a saved chunk set:

```bash
bash scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh \
  --chunks /tmp/rulebook-chunks.json \
  --request-text "Add a product app route with governed checks." \
  --pretty
```

Run the smoke test:

```bash
bash scripts/02.rag-rulebook/generate-context-packet-fixture/smoke-test.sh
```
