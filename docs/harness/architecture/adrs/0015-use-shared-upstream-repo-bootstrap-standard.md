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

## Consequences

Future reusable repos can share the same bootstrap safety model without routing
every bootstrap through the chat layer.

Layer workflows can stay concrete about their portable files while relying on
one shared standard for source/upstream boundaries.

The first `llm-workbench` bootstrap remains governed, but no files are copied
into the upstream repo until the bootstrap workflow is used with explicit write
approval.

