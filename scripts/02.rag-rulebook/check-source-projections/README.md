<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.check-source-projections.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: validation
disciplines:
- agentic
- architecture
kind: script-readme
purpose: Document the source projection checker that verifies source material to derived rulebook mappings.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.check-source-projections
  path: scripts/02.rag-rulebook/check-source-projections/script.sh
-->
# Check Source Projections

Validates the active source projection manifest:

`.agentic/02.rag-rulebook/source-projections/v1.yml`

The checker is read-only. It verifies that governed source material is declared
in the manifest, derived YAML outputs exist, derived YAML outputs carry current
source hashes, derivation reports exist and mention the source, and expected
selector or corpus-gap proof paths exist.

## Usage

```sh
bash scripts/02.rag-rulebook/check-source-projections/script.sh --current
```

Machine-readable report:

```sh
bash scripts/02.rag-rulebook/check-source-projections/script.sh --current --json
```

Smoke test:

```sh
bash scripts/02.rag-rulebook/check-source-projections/smoke-test.sh
```

