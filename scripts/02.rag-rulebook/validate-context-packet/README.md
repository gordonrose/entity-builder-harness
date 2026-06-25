<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.validate-context-packet.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: context-packets
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the read-only context-packet validator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.scripts.readme
  path: scripts/02.rag-rulebook/README.md
- id: rag-rulebook.script.validate-context-packet
  path: scripts/02.rag-rulebook/validate-context-packet/script.sh
-->
# Validate Context Packet

`script.sh` validates a `rag-rulebook/context-packet/v1` JSON packet against a
`rag-rulebook/chunk-set/v1` JSON file.

It checks:

- required top-level packet fields
- duplicate packet IDs, citation IDs, selected chunk IDs, and check IDs
- selected chunk IDs against the chunk set
- selected chunk corpus, artifact, source, rule, content, and citation fields
- packet citations against chunk-set citations
- checks, forbidden actions, and stop conditions against packet citations
- matched corpora, rule packs, and rulesets against selected evidence
- confidence values and budget consistency
- blocking gaps and routing status consistency
- provenance references to the chunk set

It does not modify files or build a packet.

Validate a packet:

```bash
bash scripts/02.rag-rulebook/validate-context-packet/script.sh \
  --packet /tmp/context-packet.json \
  --chunks /tmp/rulebook-chunks.json
```

Emit a machine-readable report:

```bash
bash scripts/02.rag-rulebook/validate-context-packet/script.sh \
  --packet /tmp/context-packet.json \
  --chunks /tmp/rulebook-chunks.json \
  --json
```

Run the smoke test:

```bash
bash scripts/02.rag-rulebook/validate-context-packet/smoke-test.sh
```
