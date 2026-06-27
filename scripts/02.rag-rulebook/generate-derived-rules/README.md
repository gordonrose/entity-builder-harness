<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.generate-derived-rules.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: script-readme
purpose: Document the derived rule projection planner for source material to YAML rule outputs.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.generate-derived-rules
  path: scripts/02.rag-rulebook/generate-derived-rules/script.sh
-->
# Generate Derived Rules

Generates a read-only source-to-rule projection plan from the active source
projection manifest.

This command does not semantically rewrite rule YAML yet. It verifies the
current projection state and emits the deterministic data that a future
agentic apply step will need:

- source material paths and current SHA-256 hashes
- expected derived rule paths
- current `source_derivation` status for each rule
- derivation reports and review status
- provenance templates for future generated projections
- actions such as `current`, `create-derived-rule`, or
  `refresh-source-derivation`

## Usage

Emit a JSON projection plan:

```sh
bash scripts/02.rag-rulebook/generate-derived-rules/script.sh --current --json
```

Check that all declared projections are mechanically current:

```sh
bash scripts/02.rag-rulebook/generate-derived-rules/script.sh --current --check
```

Smoke test:

```sh
bash scripts/02.rag-rulebook/generate-derived-rules/smoke-test.sh
```

