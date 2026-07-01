<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.generate-source-to-rule-work-order.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: script-readme
purpose: Document the source-to-rule work-order generator for governed corpus-to-YAML derivation.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.generate-source-to-rule-work-order
  path: scripts/02.rag-rulebook/generate-source-to-rule-work-order/script.sh
-->
# Generate Source-To-Rule Work Order

Builds a read-only work order for converting approved source material into
structured YAML rulebook projections.

This command is the bridge between deterministic scripts and semantic
agent/human derivation. It does not write YAML rules, derivation reports, chunks,
or evaluations. Instead, it gathers the context needed to do that work safely:

- active projection manifest entries
- source material paths, SHA-256 hashes, and heading outlines
- expected derived rule paths and current provenance state
- derivation report status and review state
- corpus gaps and selector evaluations named by the projection
- required checks that must pass before the projection is retrieval-ready
- a narrow ordered action list for the next semantic derivation step

## Usage

Emit the current work order:

```sh
bash scripts/02.rag-rulebook/generate-source-to-rule-work-order/script.sh --current --json
```

Limit output to one projection:

```sh
bash scripts/02.rag-rulebook/generate-source-to-rule-work-order/script.sh \
  --current \
  --projection-id projection.04.deploy.02-rag-rulebook.mcp-server-deployment \
  --json
```

Smoke test:

```sh
bash scripts/02.rag-rulebook/generate-source-to-rule-work-order/smoke-test.sh
```

## Boundary

Use this command before asking an agent to update source-derived YAML. The
agent should use the work order, source material, and derivation workflow to
propose semantic changes, then leave durable acceptance to derivation reports,
provenance checks, runtime freshness checks, chunk generation, and selector
evaluations.
