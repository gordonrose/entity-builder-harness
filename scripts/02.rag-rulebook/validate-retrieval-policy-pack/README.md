<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.validate-retrieval-policy-pack.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the read-only retrieval policy-pack validator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.scripts.readme
  path: scripts/02.rag-rulebook/README.md
- id: rag-rulebook.script.validate-retrieval-policy-pack
  path: scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh
-->
# Validate Retrieval Policy Pack

`script.sh` validates a `rag-rulebook/retrieval-policy-pack/v1` YAML policy
pack against the current retrieval policy-pack schema and repo references.

It checks:

- required top-level policy-pack fields
- policy-pack schema, status, version, and applies-to compatibility
- required retrieval dimension manifest entries
- imported dimension file existence and schema compatibility
- dimension required inputs, expected actions, banned actions, output
  obligations, gaps/stops, ranking effects, and validation examples
- prompt-dimension recognition sources, extraction rules, term categories, and
  classification outputs
- precedence rank ordering and required precedence concepts
- threshold ranges and v1 semantic-recall safety
- referenced workflows, validators, and smoke fixtures
- evolution rules for compatible changes and review-required changes

Validate the current seed policy:

```bash
bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh --current
```

Validate another policy pack:

```bash
bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh \
  --policy /tmp/retrieval-policy-pack.yml
```

Emit a machine-readable report:

```bash
bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh \
  --current \
  --json
```

Run the smoke test:

```bash
bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/smoke-test.sh
```
