<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.generate-recognition-sources.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the recognition-source generator command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.generate-recognition-sources
  path: scripts/02.rag-rulebook/generate-recognition-sources/script.sh
- id: rag-rulebook.recognition-source.generated.artifacts
  path: .agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml
-->
# Generate Recognition Sources

`script.sh` generates committed recognition-source YAML from governed metadata.

The first generated source is:

```text
.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml
```

It is derived from the artifact metadata index. The generator does not parse
metadata headers itself; it delegates to the existing artifact metadata indexer.

## Usage

Regenerate the committed source:

```bash
bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --output .agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml
```

Print generated YAML without writing:

```bash
bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --print
```

Check the committed source is current:

```bash
bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check
```

## Maintenance Rule

The RAG/rulebook commit gate runs `--check` when generated recognition sources
exist. If artifact metadata changes and the generated source is stale, the
commit gate fails before the task commit.

## Effects

`--print` and `--check` are read-only. `--output` writes the generated YAML file.
