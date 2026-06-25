<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0018-govern-artifact-path-migrations
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the decision to govern artifact path moves with reusable planning
  and validation.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
- id: harness.standards.artifact-path-migrations
  path: .agentic/01.harness/standards/artifact-path-migrations.md
- id: chat.doc.public-chat-workbench-adrs
  path: docs/00.chat/public-chat-workbench-adrs.md
-->

# 0018 Govern Artifact Path Migrations

Status: accepted
Date: 2026-06-20

## Context

The harness now has several path-based contracts:

- startup and routing files name workflow paths
- classifier fixtures emit workflow paths
- scripts read harness data and allowlist governed helper paths
- bootstrap templates copy selected paths into public workbench repos
- commit logs preserve historical workflow metadata

A directory rename can therefore break compatibility even when the file content
does not change. The proposed `.agentic/01.harness` to `.agentic/01.harness`
rename exposed the same concern for the matching script namespace: if the
process owner path changes, the `scripts/` owner path needs to be planned too.

Before this decision, agents could search manually, but there was no reusable
workflow, standard, or validation helper that separated active references from
historical session evidence.

## Decision

Add a governed artifact path migration capability:

- `.agentic/01.harness/workflows/migrate-artifact-paths.md`
- `.agentic/01.harness/standards/artifact-path-migrations.md`
- `scripts/01.harness/plan-artifact-path-migration.sh`
- `scripts/01.harness/check-artifact-path-migration.sh`
- `scripts/01.harness/smoke-test-artifact-path-migration.sh`

Path migrations must start with a reference plan for the old and proposed new
paths. The plan classifies references into active buckets and session history.
The checker fails when active old-path references remain unless an explicit
compatibility surface is approved.

For harness layer or owner namespace renames, the workflow requires planning
both the `.agentic/` namespace and the matching `scripts/` namespace.

## Consequences

Path moves become slower at the start but safer overall. Agents have a standard
way to answer whether a rename is a simple move, a compatibility migration, or
a stop condition.

Historical commit logs do not need to be rewritten only to modernize paths.
They remain audit history unless they are being treated as current runnable
instructions.

The `.agentic/01.harness` to `.agentic/01.harness` rename is not blocked forever,
but it is now clearly a compatibility migration. It needs either active
reference updates plus a temporary compatibility alias, or an explicit decision
to keep the old path as a durable pointer.

The matching script path later received a separate namespace decision. ADR 0020
keeps numbered `scripts/<layer>/...` namespaces as the durable executable
command surface and reserves future product and deployment command surfaces
under that convention. Any future `scripts/01.harness/...` move would update
that script-layout decision rather than happen incidentally.
