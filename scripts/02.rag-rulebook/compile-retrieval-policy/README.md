<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.compile-retrieval-policy.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the compiled retrieval policy command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.scripts.readme
  path: scripts/02.rag-rulebook/README.md
- id: rag-rulebook.script.compile-retrieval-policy
  path: scripts/02.rag-rulebook/compile-retrieval-policy/script.sh
-->
# Compile Retrieval Policy

`script.sh` compiles governed selector inputs into one
`rag-rulebook/compiled-retrieval-policy/v1` JSON artifact.

It consumes:

- the active retrieval policy pack
- imported policy dimensions
- generated and curated recognition sources
- corpus ownership and rule graph metadata from a rulebook index

It is the boundary between human-governed YAML and runtime selector behavior.
Production runtime code should load this compiled artifact instead of carrying
hidden intent precedence, evidence bundle, corpus-routing, or confidence
constants.

Compile from the current repo:

```bash
bash scripts/02.rag-rulebook/compile-retrieval-policy/script.sh \
  --current \
  --pretty
```

Compile against an existing index and write the artifact:

```bash
bash scripts/02.rag-rulebook/compile-retrieval-policy/script.sh \
  --current \
  --index .cache/02.rag-rulebook/rulebook-index.json \
  --output .cache/02.rag-rulebook/compiled-retrieval-policy.json \
  --pretty
```

Run the smoke test:

```bash
bash scripts/02.rag-rulebook/compile-retrieval-policy/smoke-test.sh
```

## Effects

Without `--output`, the command is read-only and writes JSON to stdout. With
`--output`, it writes only the requested compiled-policy JSON file.
