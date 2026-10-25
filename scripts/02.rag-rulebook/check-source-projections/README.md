<!-- agentic-artifact:
schema: agentic-artifact/v3
id: rag-rulebook.script.check-source-projections.readme
version: 1
status: active
created_on: "2026-06-27"
updated_on: "2026-10-25"
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

Retired projection sets must be backed by accepted retirement records for their
retired source, rule, derivation report, corpus-gap, and selector-evaluation
paths. Active projection sets must not name artifacts that have accepted
retirement records.

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

For a focused change, select its exact active projection ID:

```sh
bash scripts/02.rag-rulebook/check-source-projections/script.sh --current \
  --projection-set projection.02.rag-rulebook.hosted-context-provider-contract --json
bash scripts/02.rag-rulebook/check-source-projections/scoped-smoke-test.sh
```

Scoped mode still checks the complete manifest shape, unique declarations,
retirement alignment and source/rule inventory. It validates source hashes and
report bindings for the selected active set. Unknown, duplicate and inactive
selections fail. The report identifies its scope and does not claim that other
sets have current content. Without the option, the existing global checks are
unchanged. Record unrelated global failures separately; do not repair other
owners' source hashes as part of a focused change.
