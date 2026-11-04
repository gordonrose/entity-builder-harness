<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.template.module-readme
version: 1
status: active
created_on: "2026-11-01"
updated_on: "2026-11-04"
layer: 06.shared
domain: documentation
disciplines: [agentic, architecture]
kind: template
purpose: Supply an adaptable shape for source-module README explanations without duplicating writing requirements.
portability: {class: source-only, targets: []}
used_by:
- id: shared.skill.write-readme
  path: .agentic/shared/skills/write-readme.md
-->
# Module README template

Use the [skill](../skills/write-readme.md) and its linked standard. The skeleton
below supplies shape, not another set of requirements. For a single-file addition
to an existing guide, use only the relevant parts and preserve its surrounding
structure. Replace bracketed prompts; do not copy this artifact's metadata into
a source README unless the owning format requires it.

---

# [Module name]

[Concrete need, necessary terms, what this folder does and does not do.]

## What each file does

[Linked direct-file inventory and purpose; distinguish subfolders and generated
files, locally implemented work and forwarded exports.]

## Worked examples

### One input

[Where the example lives; public import and implementation locations; supplied
information, requirement, intermediate steps, result and relevant failure.]

### Several inputs or related steps

[Richer example when useful; explain each step, exact results and omissions.]

## How it fits into the repo

[Small diagram with caller/module boundary, inputs and outputs; identify current
examples versus future reuse. Explain any paths the diagram does not cover.]

## When to use it and what governs its use

[Owning rule/check links, implemented guarantees, limits, and relevant not-yet-
implemented items with backlog links.]

## File walkthrough: [file]

[What is implemented here versus made available from another file.]

### [Public name]

[What it is, why it exists, when/how it is used, input/output or code-checking
role, relevant syntax, failure/limit and an example or link where useful.]

[Repeat for every in-scope public name; link an existing explanation for re-exports.]

## Tests and outstanding work

[Existing proof links, deliberately deferred coverage and actual known gaps.
Do not turn draft tests or current examples into implementation guarantees.]
