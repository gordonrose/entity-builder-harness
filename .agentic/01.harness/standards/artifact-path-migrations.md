<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.standards.artifact-path-migrations
version: 1
status: active
layer: 01.harness
domain: migration
disciplines:
- agentic
- architecture
kind: standard
purpose: Define safety rules for moving, renaming, retiring, or removing repository
  artifact paths.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
- id: harness.script.plan-artifact-path-migration
  path: scripts/01.harness/plan-artifact-path-migration.sh
- id: harness.script.check-artifact-path-migration
  path: scripts/01.harness/check-artifact-path-migration.sh
-->

# Artifact Path Migrations

## Purpose

Use this standard when a task moves, renames, retires, or removes committed
files or directories.

Path migrations are compatibility work. A path can be a process contract even
when the file contents are simple, because workflows, classifiers, scripts,
templates, bootstrap exports, and session metadata may name that path.

## Requirements

- Plan before editing. Produce a reference inventory for the old path and, when
  relevant, the proposed new path.
- Separate active references from historical references.
- Keep old paths working when current sessions, public templates, bootstrap
  exports, or compatibility contracts still require them.
- Retire old paths only after active references point at the canonical path or a
  documented compatibility surface exists.
- Include the matching `scripts/` owner path in the plan when renaming a harness
  layer or owner namespace.
- Do not rewrite historical session logs only to modernize old paths.
- Do not remove files with recorded work, compatibility value, or bootstrap
  value unless the governing workflow and ADR cover the removal.
- Record ADR impact when the migration changes a durable namespace, public
  bootstrap surface, compatibility promise, or layer layout.

## Reference Buckets

Classify old-path references into these buckets:

| Bucket | Meaning |
|---|---|
| `routing` | Always-loaded routers, routing policy, and classifiers |
| `workflow` | `.agentic/` workflows, standards, checklists, skills, and process docs |
| `script` | Runtime scripts, governed runner allowlists, tests, and smoke fixtures |
| `bootstrap` | Public templates, bootstrap planners, export manifests, and readiness docs |
| `architecture` | ADRs and architecture docs |
| `session-history` | `commitLogs/` and other audit history |
| `other` | Any remaining reference |

Active references are every bucket except `session-history`. Historical
references may stay if they are clearly audit history and do not look like
current runnable instructions.

## Compatibility Choices

Choose one of these outcomes for the old path:

- `alias`: keep the old path as a symlink or thin pointer to the canonical path.
- `wrapper`: keep an executable compatibility file that delegates to the new
  canonical implementation.
- `pointer`: keep a human-readable document that names the new canonical path.
- `retired`: remove the old path after active references and compatibility
  obligations are gone.

Prefer `alias` or `wrapper` when tools read the path directly. Prefer
`pointer` when humans may follow older docs but no executable compatibility is
needed.

## Stop Conditions

Stop before editing when:

- the old path has active references and no compatibility choice is selected
- the new path collides with an existing path
- the migration would change branch, session, commit-log, or bootstrap behavior
  without a workflow or ADR owner
- the plan cannot tell active references from historical references
- the task needs to delete, overwrite, or rewrite work without explicit approval
