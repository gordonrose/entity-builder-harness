<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.prototype-corpus.pointer
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: compatibility-pointer
purpose: Point legacy prototype architecture corpus references to owner-aligned numbered corpus roots after the migration.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
- id: harness.standards.document-artifact-placement
  path: .agentic/01.harness/standards/document-artifact-placement.md
-->
# Prototype Architecture Corpus Pointer

The prototype architecture corpus that used to live under this directory has
been split into owner-aligned corpus and governance homes.

Use these canonical roots instead:

- `docs/00.chat/` for chat lifecycle and portable workbench documentation.
- `docs/01.harness/` for harness ADRs, migration history, and harness-owned
  rulebook content.
- `docs/02.rag-rulebook/` for RAG/rulebook source material, ADRs, and rules
  about the RAG/rulebook service itself.
- `docs/03.product/` for product source material, product ADRs, structured
  product rules, and product rule packs.
- `docs/04.deploy/` for deployment source material, deployment ADRs, and
  deployment/runtime-operation rules.
- `docs/06.shared/` for deliberately cross-layer ADRs and structured rules.
- `.agentic/03.product/plans/implementation/` for product implementation
  plans such as the platform runtime plan.

Do not add new ordinary content under `docs/harness/architecture/**`.

Use `.agentic/01.harness/standards/document-artifact-placement.md` for new
document placement decisions and
`.agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md`
for the migration record.
