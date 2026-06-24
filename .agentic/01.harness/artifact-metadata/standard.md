<!-- agentic-artifact:
owner: harness
kind: standard
purpose: Define the versioned artifact metadata model used for agent navigation, migration planning, and repo indexing.
domain: metadata
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/standards/artifact-metadata-headers.md
  - docs/harness/architecture/adrs/0021-use-versioned-artifact-metadata-for-agent-navigation.md
  - scripts/01.harness/artifact-metadata/check-headers/script.sh
-->

# Artifact Metadata Standard

## Purpose

Use artifact metadata to make harness artifacts self-describing and indexable.
The metadata should let agents and humans locate relevant files by stable
identity, layer, domain, discipline, purpose, portability target, and
relationship without reading every file in full.

## Compatibility

Existing `agentic-artifact` and `agentic-script` v1 headers remain valid during
migration. New or materially changed artifacts should prefer
`agentic-artifact/v2`.

Do not bulk-migrate historical artifacts only to modernize headers. Backfill in
focused batches with validation evidence.

## V2 Header

Markdown artifacts should use this shape at the top of the file:

```markdown
<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.metadata.artifact-headers
version: 1
status: active
layer: 01.harness
domain: metadata
disciplines:
  - agentic
  - architecture
kind: standard
purpose: Define metadata headers for harness artifacts.
portability:
  class: reusable
  targets:
    - llm-workbench
    - entity-builder
used_by:
  - id: harness.check.artifact-metadata-headers
    path: scripts/01.harness/artifact-metadata/check-headers/script.sh
-->
```

YAML artifacts should use the same fields as YAML comments:

```yaml
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.rule.layer.packages-core
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: packages.core
#   disciplines:
#     - architecture
#   kind: ruleset
#   purpose: Define packages/core architecture placement rules for agents.
#   portability:
#     class: source-only
#     targets: []
#   used_by:
#     - id: harness.rulepack.add-core-module
#       path: docs/harness/architecture/rule-packs/add-core-module.yml
```

Script artifacts are also in scope for v2. They should eventually use the same
`agentic-artifact/v2` shape with `kind: script` and an `effects` array:

```bash
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.artifact-metadata.check-headers
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Check artifact metadata headers.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#   effects:
#     - read-only
#   used_by:
#     - id: harness.checklist.before-commit
#       path: .agentic/00.chat/checklists/before-commit.md
```

Existing scripts with `agentic-script` v1 headers remain valid during migration.
New or materially changed scripts should prefer `agentic-artifact/v2` once they
are intentionally migrated.

## Fields

`schema` is required. The current value is `agentic-artifact/v2`.

`id` is required. It is the stable identity of the artifact and must not encode
the current file path. Use lowercase dot-separated segments.

`version` is required. It is an integer that tracks meaningful changes to the
artifact contract or guidance.

`status` is required. Use `draft`, `active`, `deprecated`, or `retired`.

`layer` is required. Use a numbered layer from `taxonomy.yml`.

`domain` is required and extensible. Use dot-separated values for nested areas,
such as `packages.design-system`, `apps.persistence`, or `infra.ci-cd`.

`disciplines` is required for v2. Use one or more controlled values from
`taxonomy.yml`.

`kind` is required and extensible. Use the narrowest artifact type, such as
`workflow`, `standard`, `checklist`, `adr`, `readme`, `rule-pack`, `ruleset`,
`manifest`, `config`, `script`, or `index`.

`effects` is required when `kind: script`. Use one or more controlled script
effects from `taxonomy.yml`.

`purpose` is required. Use one concise sentence that explains why the artifact
exists.

`portability` is required. It contains a `class` and a `targets` array.

`used_by` is required. Prefer ID-first references with a path hint:

```yaml
used_by:
  - id: harness.workflow.change-harness
    path: .agentic/01.harness/workflows/change-harness.md
```

## Identity Rules

Artifact IDs must be stable across path moves and file renames. Change an ID
only when the artifact is replaced by a different concept.

When one artifact splits into multiple durable artifacts, keep the old ID on the
continuing artifact only if the original concept remains intact. Otherwise mark
the old artifact `deprecated` or `retired` and create new IDs for the new
concepts.

## Version Policy

Bump `version` when the artifact changes its contract, behavior, required
inputs, output shape, or durable guidance.

Do not bump `version` for typo fixes, formatting-only changes, path moves, or
non-semantic wording cleanup.

Use generated index fields such as `content_hash`, `indexed_at`, and
`git_commit` for exact content reconciliation. Do not rely on humans to bump
`version` for every byte-level change.

## Portability Policy

Use `portability.class` to describe how the artifact should be treated during
cross-repo extraction:

- `required` means the target repo needs the artifact to function.
- `reusable` means the artifact is intended to be copied or adapted.
- `compatible` means the artifact can be used when the target supports the same
  capability.
- `source-only` means the artifact should remain in this source repo by default.
- `internal` means the artifact is private to local process or state.

Use `portability.targets` for repo or product targets such as `llm-workbench`,
`entity-builder`, or `design-system-builder`. Leave it empty when no target is
known or when the artifact is source-only.

## Used-By Policy

Use `used_by.id` as the durable relationship. Use `used_by.path` as a current
path hint and migration aid.

The checker should eventually validate that referenced IDs resolve in the
artifact index. During migration it may warn instead of fail when a referenced
ID is not yet indexed.

Path-only v1 `used_by` entries remain valid until their artifacts are migrated
to v2.

## Index Policy

The artifact index should be generated from metadata headers, not maintained by
hand. The first index should map stable IDs to current paths and metadata.

The generator should emit JSON to stdout by default. Existing v1 artifacts may
appear as legacy entries with provisional IDs until they are migrated to v2.

Historical path reconciliation can come later from Git history after v2 IDs are
widely adopted.
