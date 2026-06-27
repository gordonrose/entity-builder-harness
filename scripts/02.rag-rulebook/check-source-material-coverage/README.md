<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.check-source-material-coverage.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the source-material coverage checker for governed RAG/rulebook corpora.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.check-source-material-coverage
  path: scripts/02.rag-rulebook/check-source-material-coverage/script.sh
-->
# Source Material Coverage Checker

`script.sh` verifies that governed source material is not orphaned.

The checker is read-only. It scans current source material under:

- `docs/02.rag-rulebook/source-material/`
- `docs/04.deploy/source-material/`

For every non-README Markdown source file, the checker requires at least one
governed outcome:

- structured rule YAML that references the source material
- a source-to-rule derivation report that names the source material
- a corpus gap record that names the source material as coverage evidence

When structured rule YAML is claimed, the checker also verifies that the rule
path is present in the generated rulebook index and generated chunk set. That
keeps source coverage tied to retrievable rulebook material instead of stopping
at a file-path reference.

## Usage

```bash
bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current
bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current --json
```

## What It Does Not Do

The checker does not judge whether the derived rules are semantically complete.
Semantic conflict and drift review belongs in the source-to-rule derivation
report.

The checker also does not generate YAML rules, update corpus gaps, rewrite
derivation reports, or package a runtime. It only proves that source material
has a governed coverage path and that claimed rules reached the index/chunk
pipeline.
