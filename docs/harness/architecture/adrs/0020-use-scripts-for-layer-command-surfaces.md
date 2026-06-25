<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0020-use-scripts-for-layer-command-surfaces
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the decision to use numbered scripts namespaces as the durable executable
  command surface for agentic layers.
portability:
  class: source-only
  targets: []
used_by:
- id: chat.doc.script-layout
  path: docs/00.chat/script-layout.md
- id: harness.workflows.build-capability-workflow
  path: .agentic/01.harness/workflows/build-capability-workflow.md
-->

# 0020 Use Scripts For Layer Command Surfaces

Status: accepted
Date: 2026-06-23

## Context

The harness already uses `scripts/00.chat/` and `scripts/01.harness/` as
canonical executable surfaces for chat lifecycle and harness governance
capabilities. Those scripts are invoked by workflows, checklists, package
scripts, governed-script allowlists, bootstrap planners, and future command
wrappers.

At the same time, architecture source guides described repo automation,
generators, migration helpers, lint rules, release tooling, and developer CLI
code as living under `tools/`. That language was harvested into an active
`tools` layer ruleset, creating two plausible trajectories:

- continue growing executable capabilities under numbered `scripts/` layer
  namespaces
- introduce a top-level `tools/` layer for automation and generators

The intended long-term shape is for each agentic layer to expose deterministic
commands that can later be wrapped by an MCP server. A separate top-level
`tools/` path would split the command surface from the layer ownership model and
make future MCP exposure less direct.

## Decision

Use `scripts/` as the durable executable command surface for agentic layers.

The target shape is:

```txt
scripts/
  00.chat/
  01.harness/
  02.product/
  03.deployment/
```

Each layer-owned command capability should live under:

```txt
scripts/<numbered-layer>/<domain>/<capability>/
```

The term "tools" describes a class of automation capabilities, not a canonical
top-level repo path for this harness. Existing architecture rules that refer to
`tools/**` should be remediated in a later, governed rulebook slice so they map
automation, generation, migration, lint, release, and developer CLI behavior to
the appropriate numbered `scripts/` layer.

Future MCP exposure should wrap stable script capabilities through an explicit
registry or manifest rather than importing product, deployment, or harness
internals directly.

## Consequences

The harness has one command-surface convention: numbered layer namespaces under
`scripts/`.

The current `scripts/00.chat/` and `scripts/01.harness/` paths remain canonical.
Product and deployment command surfaces should be added as future governed
capability work, not as compatibility aliases.

The existing `tools` architecture ruleset remains temporarily divergent until a
follow-up rulebook remediation decides whether to rename it, convert it to a
concern ruleset, or rewrite it around `scripts/**` command-surface ownership.

Because this decision changes direction rather than moving committed files, it
does not perform an artifact path migration. Any future move, rename, or
retirement of committed paths must still follow the governed artifact path
migration workflow.
