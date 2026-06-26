<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.build-local-runtime.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: runtime
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the local deterministic RAG/rulebook runtime build command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.build-local-runtime
  path: scripts/02.rag-rulebook/build-local-runtime/script.sh
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# Build Local Runtime

`script.sh` builds a local deterministic RAG/rulebook runtime cache from
governed repo sources.

This is the local-first bootstrap step before deploy-corpus expansion or hosted
RAG service work.

## Usage

Build the default local runtime cache:

```bash
bash scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
```

Build into a custom directory:

```bash
bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir /tmp/rag-rulebook-runtime \
  --pretty
```

## Outputs

The default output directory is ignored by git:

```text
.cache/02.rag-rulebook/
  rulebook-index.json
  rulebook-chunks.json
  manifest.json
  validation-report.json
```

## What It Checks

The command checks:

- retrieval policy pack validity
- recognition-source validity
- recognition-candidate validity
- generated recognition-source freshness
- rulebook index validity

Then it writes the generated index, chunk set, manifest, and validation report.

## Effects

This command writes only to the selected local runtime directory. It does not
call the network, generate embeddings, start a server, deploy anything, or
modify curated sources.
