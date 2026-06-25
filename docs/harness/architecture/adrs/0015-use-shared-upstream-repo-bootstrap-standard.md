<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0015-use-shared-upstream-repo-bootstrap-standard
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the 0015 Use Shared Upstream Repo Bootstrap Standard architecture
  decision.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
-->

# 0015 Use Shared Upstream Repo Bootstrap Standard

Status: accepted
Date: 2026-06-19

## Context

The harness may produce multiple reusable upstream repos over time, including
chat workbench, frontend, CRUD factory, and AWS CI/CD repos.

Each repo type needs layer-specific bootstrap details, but all of them share
the same risk: copying source-repo-specific material into a public or reusable
upstream repo.

## Decision

Create a shared upstream repo bootstrap standard for cross-layer ownership,
inspection, approval, exclusion, and stop-condition rules.

Layer-specific workflows must consult the shared standard and define their own
portable file sets. The chat layer owns the first workflow for bootstrapping a
chat workbench repo such as `llm-workbench`.

Empty upstream repos must establish an initial branch, starter public files, and
an initial commit before normal chat startup can be exercised there. Source repo
`commitLogs/` are not copied; the upstream repo creates its own session logs
after startup is available.

For open-source upstream repos, bootstrap should create a minimal usable product
surface, not only an internal harness file baseline. The first `llm-workbench`
bootstrap includes public docs, examples, install/uninstall scripts, and an
install smoke test so the final user experience is tested from the beginning.

## Consequences

Future reusable repos can share the same bootstrap safety model without routing
every bootstrap through the chat layer.

Layer workflows can stay concrete about their portable files while relying on
one shared standard for source/upstream boundaries.

The first `llm-workbench` bootstrap remains governed, but no files are copied
into the upstream repo until the bootstrap workflow is used with explicit write
approval.

The first upstream commit becomes a prerequisite for testing chat startup in an
empty reusable repo.

Bootstrapping more product surface up front increases initial scope, but avoids
validating a harness-only shape that external engineers would never use
directly.
