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

The generated sources are:

```text
.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml
.agentic/02.rag-rulebook/recognition-sources/generated/routing.yml
```

`artifacts.yml` is derived from the artifact metadata index. The generator does
not parse metadata headers itself; it delegates to the existing artifact
metadata indexer.

`routing.yml` is derived from governed routing, layer, workflow, corpus, and
mode sources.

## Usage

Regenerate all committed sources:

```bash
bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --write-all
```

Regenerate one committed source:

```bash
bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --source routing \
  --output .agentic/02.rag-rulebook/recognition-sources/generated/routing.yml
```

Print generated YAML without writing:

```bash
bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --source artifacts --print
```

Check committed sources are current:

```bash
bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check
```

## Maintenance Rule

The RAG/rulebook commit gate runs `--check` when generated recognition sources
exist. If artifact metadata, routing policy, layer taxonomy, workflow files, or
retrieval policy change and generated sources are stale, the commit gate fails
before the task commit.

## Effects

`--print` and `--check` are read-only. `--output` and `--write-all` write
generated YAML files.
