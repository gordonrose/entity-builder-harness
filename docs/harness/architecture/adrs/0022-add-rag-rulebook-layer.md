<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0022-add-rag-rulebook-layer
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the decision to add RAG/Rulebook as a standalone agentic layer before product and deployment layers.
portability:
  class: source-only
  targets: []
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: harness.taxonomy.artifact-metadata
  path: .agentic/01.harness/artifact-metadata/taxonomy.yml
- id: chat.doc.script-layout
  path: docs/00.chat/script-layout.md
-->

# 0022 Add RAG/Rulebook Layer

Status: accepted
Date: 2026-06-25

## Context

The harness has started to encode architecture guidance as structured YAML
rulebooks, rulesets, and rule packs. That work is useful, but the reusable
machinery is broader than harness maintenance:

- RAG can support harness development.
- RAG can support product and app development.
- RAG can support design-system development.
- RAG can support deployment and runtime operations.

Keeping all rulebooks under `docs/harness/architecture/` blurs domain corpus
ownership. It makes product, design-system, deployment, and harness guidance
look like one harness-owned instruction corpus even though those domains should
remain modular.

At the same time, `00.chat` and git governance belong to the LLM Workbench
surface. Chat startup, worktrees, session logs, and branch coordination should
not own reusable RAG/rulebook machinery.

## Decision

Add RAG/Rulebook as a first-class agentic layer:

```txt
02.rag-rulebook
```

The RAG/Rulebook layer owns reusable corpus generation, rulebook schemas,
chunking, indexes, graph relationships, intent models, context packets, and
standalone RAG service boundaries.

Renumber the later metadata layers around that insertion:

```txt
00.chat
01.harness
02.rag-rulebook
03.product
04.deploy
05.education
06.shared
```

The new layer is a scaffold and governance boundary. This decision does not
build a RAG server, MCP server, vector index, or external service.

## Consequences

The harness can route future RAG/rulebook work separately from harness
maintenance.

The artifact metadata taxonomy can distinguish reusable RAG/rulebook machinery
from product, deploy, education, and shared process artifacts.

Existing prototype rulebook artifacts under `docs/harness/architecture/` remain
in place until a separate governed corpus migration assigns final homes to
harness, product/apps, design-system, deploy, and education corpora.

Future command surfaces should reserve:

```txt
scripts/02.rag-rulebook/
scripts/03.product/
scripts/04.deploy/
```

Path moves for existing artifacts are intentionally deferred. Any future move,
rename, or retirement of committed files must follow the governed artifact path
migration workflow.
