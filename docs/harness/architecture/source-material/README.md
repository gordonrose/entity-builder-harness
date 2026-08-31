<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.source-material.pointer
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: compatibility-pointer
purpose: Point older prototype source-material references to the product source-material corpus.
portability:
  class: source-only
  targets: []
used_by:
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# Prototype Source Material Moved

Product source material now lives under `docs/03.product/source-material/`.

Moved files:

- `docs/03.product/source-material/core/packages-core-contract-surface-v1.md`
- `docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md`
- `docs/03.product/source-material/platform/platform-infra-capability-layering-v1.md`

This compatibility pointer exists while the prototype architecture corpus is
split into numbered owner-aligned homes.
