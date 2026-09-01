<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.operator-guide
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: guide
purpose: Guide Codex sessions that continue architecture rulebook creation.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.manifest
  path: .agentic/01.harness/manifest.yml
-->

# Architecture Rulebook Operator Guide

## Purpose

Use this guide when continuing architecture rules and rule packs from
`docs/03.product/source-material/guides/markdown`.

This operating pack is instructional only. It is not the runtime harness and it
does not create executable checks or generated architecture artifacts by itself.

## Operating Rules

- Work one artifact at a time.
- Prefer small, reviewable changes.
- Do not invent architecture rules without checking the source guides.
- Do not duplicate full source-guide content inside rules.
- Do not duplicate concern rules inside rule packs; reference rulesets instead.
- Manually check each `source_refs` entry against the named source document and
  section before treating it as accurate.
- Update `state/rulebook-coverage.yml` when an artifact covers, defers, or
  deliberately excludes guide content.
- Validate YAML after editing.
- Print final paths and assumptions.
- Stop after the requested artifact.

## Artifact Meanings

A layer ruleset answers: "What belongs in this repo layer?"

A concern ruleset answers: "What cross-cutting rule applies across layers?"

A rule pack answers: "What rules and steps apply to this task?"

## Decision Model

Structured rulebook YAML belongs in the narrowest owner corpus:

```text
docs/01.harness/rules/
docs/02.rag-rulebook/rules/
docs/03.product/rules/
docs/04.deploy/rules/
docs/06.shared/rules/
```

Product rules and rule packs use owner topic subdirectories such as:

```text
docs/03.product/rules/<topic>/concerns/*.yml
docs/03.product/rules/<topic>/layers/*.yml
docs/03.product/rule-packs/<topic>/*.yml
```

Do not add new rule artifacts to retired prototype corpus locations. If an old
prototype architecture reference is encountered, follow
`standards/document-artifact-placement.md` and the prototype corpus migration
plan before changing it.

## Default Flow

1. Inspect source guides.
2. Inspect `state/rulebook-coverage.yml`.
3. Inspect existing rules and rule packs.
4. Choose one small artifact to create.
5. Use the correct template.
6. Preserve source references.
7. Manually confirm each source reference points to the claimed source content.
8. Update coverage status for the source content touched.
9. Validate YAML.
10. Summarize assumptions.
11. Stop.
