<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.generate-rulebook-index.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: indexing
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the read-only prototype rulebook index generator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.scripts.readme
  path: scripts/02.rag-rulebook/README.md
- id: rag-rulebook.script.generate-rulebook-index
  path: scripts/02.rag-rulebook/generate-rulebook-index/script.sh
-->
# Generate Rulebook Index

`script.sh` emits a read-only JSON index for the current prototype rulebook.

It reads:

- `docs/harness/architecture/`
- `docs/02.rag-rulebook/rules/`
- `.agentic/02.rag-rulebook/plans/prototype-corpus-migration-map.yml`

It emits:

- corpus packages
- indexed artifacts
- extracted rules
- extracted rule packs
- chunk candidates
- graph edges
- source references
- path mappings
- unresolved references
- diagnostics
- provenance

The output uses the `rag-rulebook/rulebook-index/v1` contract defined in
`.agentic/02.rag-rulebook/schemas/rulebook-index.schema.yml`.

The script does not move files, write generated indexes, call the network, use
embeddings, or build a server.

Use:

```bash
bash scripts/02.rag-rulebook/generate-rulebook-index/script.sh --pretty
```

Run the smoke test:

```bash
bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh
```
