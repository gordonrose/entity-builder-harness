<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.validate-rulebook-index.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: indexing
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the read-only rulebook index validator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.scripts.readme
  path: scripts/02.rag-rulebook/README.md
- id: rag-rulebook.script.validate-rulebook-index
  path: scripts/02.rag-rulebook/validate-rulebook-index/script.sh
-->
# Validate Rulebook Index

`script.sh` validates a `rag-rulebook/rulebook-index/v1` JSON document.

It checks:

- required top-level fields
- duplicate corpus, artifact, rule, rule-pack, chunk, and source IDs
- diagnostic counts against actual index contents
- artifact, rule, rule-pack, chunk, source, path-mapping, and provenance refs
- graph edges and relationship targets
- required and related ruleset resolution
- unresolved reference and `diagnostics.ok` consistency
- current source paths that should exist in the repository

It does not modify files.

Validate the current generated index:

```bash
bash scripts/02.rag-rulebook/validate-rulebook-index/script.sh --generate-current
```

Validate a saved index:

```bash
bash scripts/02.rag-rulebook/validate-rulebook-index/script.sh --index /tmp/rulebook-index.json
```

Emit a machine-readable report:

```bash
bash scripts/02.rag-rulebook/validate-rulebook-index/script.sh --generate-current --json
```

Run the smoke test:

```bash
bash scripts/02.rag-rulebook/validate-rulebook-index/smoke-test.sh
```
