<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.generate-source-to-rule-draft-packet.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: script-readme
purpose: Document the source-to-rule draft packet generator for semantic YAML proposal work.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.generate-source-to-rule-draft-packet
  path: scripts/02.rag-rulebook/generate-source-to-rule-draft-packet/script.sh
-->
# Generate Source-To-Rule Draft Packet

Builds a read-only draft packet for an agent or reviewer that needs to propose
semantic source-to-rule changes.

The packet is downstream from the source-to-rule work order. The work order
names the projection and required actions. The draft packet adds bounded file
content for the approved source material, current structured YAML projections,
derivation reports, corpus gaps, and selector evaluations.

This command does not write source material, YAML rules, derivation reports,
chunks, evaluations, generated provenance, or runtime outputs.

## Usage

Emit draft packets for all active projections:

```sh
bash scripts/02.rag-rulebook/generate-source-to-rule-draft-packet/script.sh --current --json
```

Emit one projection packet:

```sh
bash scripts/02.rag-rulebook/generate-source-to-rule-draft-packet/script.sh \
  --current \
  --projection-id projection.04.deploy.02-rag-rulebook.mcp-server-deployment \
  --json
```

Use a smaller per-file content budget:

```sh
bash scripts/02.rag-rulebook/generate-source-to-rule-draft-packet/script.sh \
  --current \
  --max-file-chars 12000 \
  --json
```

Smoke test:

```sh
bash scripts/02.rag-rulebook/generate-source-to-rule-draft-packet/smoke-test.sh
```

## Boundary

Use the packet as input to semantic proposal work. Durable acceptance still
requires derivation report review, source projection checks, provenance
refresh, generated index and chunk proof, selector evaluations, runtime
freshness, and any deploy-readiness checks named by the projection.
