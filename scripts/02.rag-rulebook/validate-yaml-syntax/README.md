<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.validate-yaml-syntax.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: validation
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the RAG/rulebook YAML syntax validator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.validate-yaml-syntax
  path: scripts/02.rag-rulebook/validate-yaml-syntax/script.sh
- id: rag-rulebook.script.validate-yaml-syntax.smoke-test
  path: scripts/02.rag-rulebook/validate-yaml-syntax/smoke-test.sh
-->
# Validate YAML Syntax

`script.sh` parses governed RAG/rulebook and deploy YAML files with PyYAML.

It is intentionally broad enough to catch schema, corpus-gap, recognition,
fixture, and deploy-rule syntax errors before narrower validators run.

## Usage

Validate the default governed YAML roots:

```bash
bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh
```

Validate explicit paths:

```bash
bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh \
  --paths .agentic/02.rag-rulebook docs/04.deploy .agentic/aws
```

Emit JSON:

```bash
bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh --json
```

## Effects

Read-only. This command parses files only.
