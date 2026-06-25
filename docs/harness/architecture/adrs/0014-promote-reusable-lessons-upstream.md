<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0014-promote-reusable-lessons-upstream
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the 0014 Promote Reusable Lessons Upstream architecture decision.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
-->

# 0014 Promote Reusable Lessons Upstream

Status: accepted
Date: 2026-06-19

## Context

Product repos such as Kanbien are where reusable chat harness gaps often become
visible. The same work can contain product-specific decisions and reusable
agentic process lessons.

Without a governed handoff, reusable harness changes can either stay buried in
a product repo or leak upstream with product-specific assumptions attached.

## Decision

Use an explicit upstream reusable lesson workflow for cross-repo harness
promotion.

The source repo owns the evidence: source branch, source chat worktree, session
log, transcript path when available, and concrete failure or decision context.

The upstream workbench repo owns the reusable implementation. The upstream chat
may inspect the source packet read-only, but it must not edit the source repo or
copy product, deployment, customer, or domain rules into the reusable harness.

## Consequences

Kanbien and similar repos can act as proving grounds for reusable harness
lessons without becoming the canonical source for reusable chat governance.

The upstream workbench can receive source-backed tasks with enough local
evidence to inspect the original context.

Future automation may prepare the handoff packet and open the upstream chat,
but it must preserve read-only source inspection and avoid silent cross-repo
copying.

