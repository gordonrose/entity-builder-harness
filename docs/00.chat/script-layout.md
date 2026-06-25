<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script-layout
  version: 1
  status: active
  layer: 00.chat
  domain: scripts
  disciplines:
  - agentic
  kind: doc
  purpose: Explain the current script layout after the chat harness script migration.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: harness.readme
    path: .agentic/01.harness/README.md
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
    path: docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
  - id: harness.architecture.adr.0020-use-scripts-for-layer-command-surfaces
    path: docs/harness/architecture/adrs/0020-use-scripts-for-layer-command-surfaces.md
-->
# Script Layout

This document describes the current script layout. For the migration history,
see ADR 0017. For the numbered layer command-surface direction, see ADR 0020.

## Current Shape

Chat lifecycle scripts live under:

```txt
scripts/00.chat/<domain>/<capability>/
```

Shared harness governance scripts live under:

```txt
scripts/01.harness/
```

Future RAG/rulebook, product, and deployment command surfaces should live under:

```txt
scripts/02.rag-rulebook/<domain>/<capability>/
scripts/03.product/<domain>/<capability>/
scripts/04.deploy/<domain>/<capability>/
```

That split is intentional:

- `scripts/00.chat/` owns chat startup, commands, reporting, session logs,
  recovery, worktrees, main refresh, local merge checks, and upstream bootstrap
  support.
- `scripts/01.harness/` owns cross-layer harness checks such as metadata,
  deterministic process drift, governed command drift, and the governed script
  runner.
- `scripts/02.rag-rulebook/` is reserved for future standalone RAG/rulebook
  automation such as corpus extraction, rulebook index generation, chunk
  generation, graph expansion, and context-packet validation.
- `scripts/03.product/` is reserved for future product-owned automation such as
  entity-builder commands, code generation, migration helpers, product
  validation, and developer CLI capabilities.
- `scripts/04.deploy/` is reserved for future deployment-owned automation
  such as environment checks, release helpers, deployment validation, and
  operational command wrappers.

Use `scripts/` as the canonical executable command surface. The term `tools`
describes automation capabilities, not a separate top-level command namespace.
Future MCP exposure should wrap stable script capabilities through an explicit
registry or manifest instead of importing layer internals directly.

Do not add new chat lifecycle scripts under `scripts/shared/chat/` or
`scripts/shared/git/`. Those were compatibility locations from the earlier
layout and are now retired.

## Capability Folders

Each capability folder should contain the files that help a reader understand,
run, and test that capability:

- `script.sh`, `script.js`, or `lib.sh` for the implementation
- `smoke-test.sh` or another focused validation file when behavior needs proof
- `README.md` explaining the purpose, inputs, effects, and boundaries

Domain folders also have a `README.md` that explains how the capabilities in
that domain fit together.

## Public Surface

Humans should usually use `package.json` `chat:*` scripts. Those package
scripts delegate to canonical `scripts/00.chat/...` paths.

Harness workflows, checklists, standards, and gates should point directly at
canonical `scripts/<numbered-layer>/...` paths for the layer that owns the
behavior.

## Historical Paths

Historical documents may mention retired paths, but should do so as migration
history:

- say what previously lived there
- name the current canonical path or say the behavior was retired
- avoid runnable examples that make the old path look current

Negative tests may create retired paths in throwaway repositories when they are
proving the governed runner rejects old compatibility surfaces.
