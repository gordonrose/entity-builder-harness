<!-- agentic-artifact:
owner: harness
kind: standard
purpose: Define metadata headers for scripts and harness process documents.
domain: metadata
portability: llm-workbench-required
used_by:
  - .agentic/harness/standards/agentic-artifact-standards.md
  - .agentic/00.chat/checklists/before-commit.md
-->

# Artifact Metadata Headers

## Purpose

Use metadata headers to make harness artifacts self-describing. A reader should
be able to open a script or harness document and see who owns it, why it exists,
where it is used, and whether it is portable to upstream repos.

## Scope

This standard applies to new:

- scripts under `scripts/`
- harness/process Markdown documents under `.agentic/`
- harness architecture and process documents under `docs/harness/`

Existing files should be backfilled in focused batches. Until backfill is
complete, the commit gate enforces metadata for newly added files.

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
bash scripts/shared/harness/run-governed-script.sh scripts/shared/harness/check-artifact-metadata-headers.sh --staged-added
```

The staged-added mode is required before commits so newly created scripts and
harness docs cannot enter the repo without metadata.
