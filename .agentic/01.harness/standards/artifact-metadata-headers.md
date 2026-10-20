<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.standards.artifact-metadata-headers
version: 2
status: active
created_on: "2026-06-19"
updated_on: "2026-10-20"
layer: 01.harness
domain: metadata
disciplines:
- agentic
kind: standard
purpose: Define metadata headers for scripts, harness process documents, and harness
  YAML artifacts.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.agentic-artifact-standards
  path: .agentic/01.harness/standards/agentic-artifact-standards.md
- id: chat.checklists.before-commit
  path: .agentic/00.chat/checklists/before-commit.md
-->

# Artifact Metadata Headers

## Purpose

Use metadata headers to make harness artifacts self-describing. A reader should
be able to open a script, harness document, or harness YAML artifact and see who
owns it, why it exists, where it is used, and whether it is portable to upstream
repos.

## Capability Home

This file documents legacy v1 header shapes for compatibility. New authoring
uses the v3 lifecycle contract; v1/v2 remain readable during migration. The
current metadata model, date-maintenance rules, taxonomy, stable ID policy and
index contract live in `.agentic/01.harness/artifact-metadata/standard.md`.

## Scope

These placement rules are separate from discovery. Every leading artifact
header is validated and indexed regardless of path or extension; see the
canonical metadata standard for discovery, template exceptions and coverage
checks. Discovery alone does not require headers on additional files.

This standard applies to new:

- scripts under `scripts/`
- harness/process Markdown documents under `.agentic/`
- harness architecture and process documents under `docs/harness/`
- harness YAML artifacts under `docs/harness/`
- RAG/rulebook corpus documents and YAML artifacts under
  `docs/02.rag-rulebook/`

Existing files should be backfilled in focused batches. The commit gate checks
new files and existing metadata on modifications, including v3 lifecycle rules.
Ordinary modifications to legacy files without headers remain grandfathered.

## Script Header

Scripts must declare metadata near the top of the file, after any shebang:

```bash
# agentic-script:
#   owner: 00.chat
#   purpose: Verify whether a chat branch can be merged into local main.
#   domain: git
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-promote-to-main.md
#   effects: read-only
```

Allowed `owner` values are real harness layers:

- `00.chat`
- `shared`
- `harness`
- `aws`
- `product`
- `education`

Use `domain` for mechanism or topic boundaries such as `git`, `startup`,
`session-log`, `governance`, `metadata`, `reporting`, `refresh`, or
`validation`. Do not encode domains into owner names.

Allowed `portability` values:

- `llm-workbench-required`
- `llm-workbench-validation`
- `llm-workbench-compatibility`
- `source-only`
- `internal`

Allowed `effects` values may be comma-separated:

- `read-only`
- `writes-files`
- `stages-files`
- `commits`
- `branches`
- `worktrees`
- `network`
- `destructive`

Use `destructive` only when a script can delete, overwrite, rewrite history, or
otherwise remove user work. Destructive scripts must support dry-run mode before
mutation.

## Markdown Header

Harness Markdown documents must declare metadata at the top of the file:

```markdown
<!-- agentic-artifact:
owner: 00.chat
kind: workflow
purpose: Govern chat startup and session routing.
domain: startup
portability: llm-workbench-required
used_by:
  - AGENTS.md
-->
```

Common `kind` values:

- `workflow`
- `standard`
- `checklist`
- `adr`
- `readme`
- `skill`
- `gate`
- `doc`

## YAML Header

Harness YAML artifacts must declare metadata at the top of the file using YAML
comments:

```yaml
# agentic-artifact:
#   owner: harness
#   kind: rule-pack
#   purpose: Govern package core module changes.
#   domain: architecture
#   portability: source-only
#   used_by:
#     - docs/03.product/rule-packs/core/add-core-module.yml
```

Common `kind` values:

- `rule-pack`
- `ruleset`
- `fixture`
- `manifest`
- `config`

## Used-By Rules

`used_by` entries should point to committed paths that explain why the artifact
is needed. A path can name a workflow, checklist, standard, script, `AGENTS.md`,
or another process document.

When a file is intentionally public surface, include the public alias or
workflow that exposes it.

When a file is a smoke test or compatibility helper, include the workflow,
standard, or checker that treats that validation as part of the harness.

## Checker

Run:

```bash
bash scripts/01.harness/run-governed-script.sh scripts/01.harness/artifact-metadata/check-headers/script.sh --staged
```

The staged mode validates the Git index, including modifications to v3 lifecycle
metadata. Legacy v1/v2 remain valid; missing headers on ordinary legacy
modifications remain grandfathered. The compatibility `--staged-added` mode is
still available. Current v3 authoring and migration rules live in the capability
standard linked above.
