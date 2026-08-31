<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0032-use-owner-aligned-adr-roots
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the decision to split prototype centralized ADR storage into owner-aligned ADR roots.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.document-artifact-placement
  path: .agentic/01.harness/standards/document-artifact-placement.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
- id: chat.script.session-log.prepare-chat-session-before-commit
  path: scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
-->
# ADR 0032: Use Owner-Aligned ADR Roots

## Status

Accepted.

## Context

ADR 0019 deliberately kept ADRs centralized under
`docs/harness/architecture/adrs/` because the repo did not yet have
owner-aligned ADR tooling. That was a safe intermediate state, but the
prototype corpus has since grown into a mixed decision history for chat,
harness, RAG/rulebook, product, deploy, education, and shared process work.

The document artifact placement standard now routes new document artifacts to
the narrowest owner layer. Slice 1 of the prototype corpus migration also
initialized numbered `docs/01.harness/`, `docs/03.product/`, and
`docs/06.shared/` corpus roots. Keeping new ADRs in the prototype path would
extend the layout drift the migration is trying to unwind.

The commit readiness gate still accepted only `docs/<track>/architecture/adrs`
paths when `ADR needed: yes`, so a new owner-aligned ADR root would be blocked
unless the gate changed with the decision.

## Decision

Use owner-aligned ADR roots for new and migrated corpus-history ADRs:

```text
docs/<numbered-owner-layer>/adrs/
```

Examples:

```text
docs/01.harness/adrs/
docs/02.rag-rulebook/adrs/
docs/03.product/adrs/
docs/04.deploy/adrs/
docs/06.shared/adrs/
```

The prototype `docs/harness/architecture/adrs/` root is now a legacy migration
source. Do not add ordinary new ADRs there. Leave compatibility pointers at
old paths while active references, public export manifests, or historical
session logs still need them.

Existing specialized roots such as `docs/aws/architecture/adrs/` and
`docs/education/architecture/adrs/` remain valid until their owning migration
or namespace decision moves them. The commit readiness gate must accept both
the owner-aligned ADR roots and these legacy governed ADR roots during the
transition.

When moving an ADR, preserve the stable artifact ID unless the decision is
split. Update the `layer` metadata to the decision owner and refresh generated
recognition sources.

## Consequences

New durable layout decisions can live in the layer that owns them instead of
adding more files to the prototype harness architecture corpus.

ADRs can be migrated in slices by owner. Product contract ADRs can move to the
product corpus before chat, RAG/rulebook, deploy, education, or shared ADRs are
ready to move.

The commit readiness gate and its smoke test must recognize the new numbered
ADR roots, while keeping legacy roots valid until their compatibility period
ends.

Public chat-workbench export remains manifest-driven. Moving a chat-relevant
ADR later must update `docs/00.chat/public-chat-workbench-adrs.md` rather than
assuming the old centralized ADR directory.
