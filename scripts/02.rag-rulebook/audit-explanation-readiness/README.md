<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.audit-explanation-readiness.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the explanation readiness audit for governed Markdown source material and guides.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.audit-explanation-readiness
  path: scripts/02.rag-rulebook/audit-explanation-readiness/script.sh
-->
# Explanation Readiness Audit

`script.sh` reports whether governed Markdown source material and guides are
ready to support human explanation prompts.

The audit is read-only. It builds temporary current rulebook index and chunk
outputs, then compares approved Markdown source roots with generated
`source-explanation` chunks and source-derived execution rule chunks.

## Usage

```bash
bash scripts/02.rag-rulebook/audit-explanation-readiness/script.sh --current
bash scripts/02.rag-rulebook/audit-explanation-readiness/script.sh --current --json
```

## What It Reports

For each source file, the report includes:

- whether the file is indexed and chunked as `source-explanation`
- source-explanation section count, heading paths, source lines, and token
  estimate
- whether any source-derived rule chunk carries `execution-authority`
- weak or missing heading issues such as a single-section outline or generic
  headings
- explanation value
- recommended repair source: source material, guide, or none

The audit distinguishes `gap:not-chunked` from `gap:weak-explanation`. A source
can be chunked but still weak for human teaching if it has only a generic
single-section outline.

## What It Does Not Do

The audit does not rewrite Markdown, generate rules, update projections, or
authorize side effects. It is a learning/readiness report only. Binding
execution coverage still belongs to structured rules, derivation reports,
source projections, corpus gaps, and selector fixtures.
