<!-- agentic-artifact:
owner: harness
kind: guide
purpose: Guide Codex sessions that continue architecture rulebook creation.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/manifest.yml
-->

# Architecture Rulebook Operator Guide

## Purpose

Use this guide when continuing architecture rules and rule packs from
`docs/harness/architecture/guides/markdown`.

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
- Validate YAML after editing.
- Print final paths and assumptions.
- Stop after the requested artifact.

## Artifact Meanings

A layer ruleset answers: "What belongs in this repo layer?"

A concern ruleset answers: "What cross-cutting rule applies across layers?"

A rule pack answers: "What rules and steps apply to this task?"

## Decision Model

Layer rules belong in:

```text
docs/harness/architecture/rules/layers/*.yml
```

Concern rules belong in:

```text
docs/harness/architecture/rules/concerns/*.yml
```

Rule packs belong in:

```text
docs/harness/architecture/rule-packs/*.yml
```

## Default Flow

1. Inspect source guides.
2. Inspect existing rules and rule packs.
3. Choose one small artifact to create.
4. Use the correct template.
5. Preserve source references.
6. Manually confirm each source reference points to the claimed source content.
7. Validate YAML.
8. Summarize assumptions.
9. Stop.
