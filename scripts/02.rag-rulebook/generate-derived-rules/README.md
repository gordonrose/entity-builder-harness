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

Generates a source-to-rule projection plan from the active source projection
manifest.

By default this command is read-only. It does not semantically rewrite rule
YAML. It verifies the current projection state and emits deterministic data:

- source material paths and current SHA-256 hashes
- expected derived rule paths
- current `source_derivation` status for each rule
- derivation reports and review status
- provenance templates for future generated projections
- actions such as `current`, `create-derived-rule`, or
  `refresh-source-derivation`

The first write mode is intentionally narrow. `--apply-provenance` rewrites
only existing top-level `source_derivation` blocks for declared rule paths.
It does not create rule files and does not change rule content.

## Usage

Emit a JSON projection plan:

```sh
bash scripts/02.rag-rulebook/generate-derived-rules/script.sh --current --json
```

Check that all declared projections are mechanically current:

```sh
bash scripts/02.rag-rulebook/generate-derived-rules/script.sh --current --check
```

Refresh only existing provenance blocks:

```sh
bash scripts/02.rag-rulebook/generate-derived-rules/script.sh --current --apply-provenance
```

Smoke test:

```sh
bash scripts/02.rag-rulebook/generate-derived-rules/smoke-test.sh
```
