<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.architecture.adr.0037-use-lifecycle-first-deployment-authority-paths
version: 1
status: active
created_on: "2026-10-21"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.governance
disciplines:
- architecture
- agentic
- sre
kind: adr
purpose: Make deployment authority paths state when they are used, what they do, and which target or scope they affect.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.plan.migration.ordered-deployment-harness-and-target-layout
  path: .agentic/04.deploy/plans/migration/ordered-deployment-harness-and-target-layout.md
- id: deploy.standards.deployment-artifact-placement-and-naming
  path: .agentic/04.deploy/standards/deployment-artifact-placement-and-naming.md
-->
# ADR 0037: Use Lifecycle-First Deployment Authority Paths

## Status

Accepted. This ADR records the durable decision required for the remaining
generic-harness moves in the ordered deployment-layout migration. The first
generic target-alignment move was completed before this decision was recorded;
it made no public compatibility promise and had no cloud effect. This ADR is
the corrective authority for that completed move and every later move.

## Context

The deployment repository contained valid facts and controls, but its folders
mostly started with an artefact type such as `workflows`, `standards`, or
`schemas`. That made it difficult to see when an instruction applied. Target
declarations similarly mixed the target profile, shared foundation, scope
facts, provider realization, and package custody at one level.

The result was a repository that could be technically correct while still
being hard to scan. An agent or maintainer could discover an instruction only
after knowing its internal artefact category, rather than from the delivery
stage and action at hand.

## Decision

Deployment paths use this readable order:

```text
folder = when or where it is used
file name = what it does
target and scope = what it affects
```

For target declarations, `infra/04.deploy/03.product/targets/<target>/` is
ordered as target, foundation, scopes, provider realization, and package
custody. A scope owns its declaration, workload binding, alignment contract,
and release evidence.

For generic deployment authority, `.agentic/04.deploy/` is lifecycle-first.
Reusable workflow, standard, schema, template, and guide files live beneath
the phase where they are primarily used and have action-oriented names. There
is one generic authoritative copy; it is never copied per target.

For provider-specific target procedures, the provider authority remains
separate and the path includes the lifecycle phase, target, and scope. If one
procedure spans deploy and run, it remains one routed workflow only when its
sections explicitly identify both phases. It must not be copied into both
locations.

Scripts remain lifecycle-first, then target and scope where binding is needed.
Plans explain and sequence migration work; they do not become a second source
of operational procedure. README files explain a tree but do not add mandatory
rules.

All future placement and naming follows the deployment-artifact placement and
naming standard. A path migration updates active consumers, runs the migration
checker and affected tests, refreshes generated recognition sources, and is
committed as a recoverable batch. Historical logs and plans remain historical
evidence rather than being rewritten merely to modernize paths.

## Consequences

New deployment files are easier to discover from the work being done, while
the executable workflow still controls sequence and authority. The repository
has a single canonical location for each active declaration or instruction.

Moves have an explicit cost: every active consumer and generated index must be
updated and validated. A later phase may not be created empty simply to make
the tree look uniform; a real owned artefact and consumer are required.

This decision changes repository organization only. It does not select a cloud
provider, grant deployment permission, alter AWS, dispatch GitHub Actions, or
change an accepted release.
