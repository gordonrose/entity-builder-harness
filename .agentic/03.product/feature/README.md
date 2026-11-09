<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.feature.readme
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: feature-governance
disciplines: [architecture, agentic, backend]
kind: capability-readme
purpose: Explain the governed path for creating and qualifying real product features.
portability: {class: source-only, targets: []}
used_by:
- id: product.feature.workflow.create
  path: .agentic/03.product/feature/workflows/create-feature.md
-->
# Product feature governance

This capability governs a real product feature from its first bounded design through local proof and the handoff to package and deployment governance. It exists because `apps/platform-smoke` proves the platform shell, but is not the architecture template for a business feature.

For example, a small persistence-backed record feature may have a title, active/archived business visibility, logical deletion, and a bounded index. The feature owns its public contract and use cases; Core owns reusable lifecycle nouns, Platform owns provider-neutral persistence ports, and deployment owns the selected AWS target and release evidence.

## What each file does

- [standard](standards/feature-boundary.md) owns the durable feature boundary: where contracts, transport, domain services, persistence mapping, migrations, errors, diagnostics, and public exports belong.
- [workflow](workflows/create-feature.md) is the ordered procedure for adopting that boundary and discovering whether the requested runtime/deployment proof is actually available.
- [readiness checklist](checklists/feature-readiness.md) makes completion claims reviewable without replacing the workflow.
- [first persistence-feature pilot](plans/implementation/first-persistence-feature-pilot.md) defines the first deliberately small consumer and its exclusions.
- [feature-creation skill](skills/create-feature.md) is the concise reusable procedure. The Codex discovery adapter is `.agents/skills/create-product-feature/SKILL.md`.

## How it fits into the repo

```text
apps/<app>/features/<feature>/ ──public app mount──> products/<product>/
        │                                      │
        ├── contract / transport / domain       └── platform composition root
        └── persistence / migrations                         │
                                                             v
                                             04.deploy target, package, AWS proof
```

The app mount is the only platform-facing feature boundary. A feature does not import AWS adapters, target profiles, cloud SDKs, or deployment manifests.

## Limits

This capability does not grant cloud mutation, define a universal app folder layout, or make a local test into package or AWS evidence. The deployment workflow remains the authority for target alignment, package custody, deploy, and live acceptance.

A durable business resource is governed additionally by [entity governance](../entity/README.md).
