<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.validate-recognition-sources.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the recognition-source validator command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.validate-recognition-sources
  path: scripts/02.rag-rulebook/validate-recognition-sources/script.sh
- id: rag-rulebook.script.commit-gates
  path: scripts/02.rag-rulebook/commit-gates/script.sh
-->
# Validate Recognition Sources

`script.sh` validates `rag-rulebook/recognition-source/v1` YAML files.

Recognition sources are lookup vocabularies used before retrieval. This command
checks that those vocabularies are governed, current enough to trust, and tied
back to source evidence.

## Usage

Validate the committed recognition-source directory:

```bash
bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current
```

Validate a specific file or directory:

```bash
bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --source <path>
```

Add `--json` for machine-readable output.

## Checks

- required top-level fields from the recognition-source schema
- valid source IDs, statuses, generation modes, source kinds, and owner layers
- non-empty used-by dimensions, validation rules, refresh policy, and terms
- generated sources declare source artifacts and a generation command
- generated source artifacts and term evidence paths exist
- curated sources declare review triggers
- duplicate source IDs, terms, and aliases are rejected
- term match types and confidence weights are valid

## Commit Gate Behavior

The RAG/rulebook commit gate calls this validator only when
`.agentic/02.rag-rulebook/recognition-sources` exists. That lets the repo add
the validator before the first generated source, then makes validation
mandatory as soon as recognition sources are committed.

## Effects

This command is read-only. It does not generate sources, update files, stage
changes, or create commits.
