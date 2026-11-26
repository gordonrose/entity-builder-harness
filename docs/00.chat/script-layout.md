<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.script-layout
  version: 2
  status: active
  created_on: "2026-06-20"
  updated_on: "2026-11-26"
  layer: 00.chat
  domain: scripts
  disciplines:
  - agentic
  kind: doc
  purpose: Explain implemented script owners, retained legacy areas and bounded capability placement.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.docs.readme
    path: docs/00.chat/README.md
-->
# Script Layout

This document maps the current repository layout, not a proposal to create more
folders. The existing owner, callers and command guide determine where work
belongs. Exported workbench copies contain only their declared portable subset;
an omitted repository-specific owner is not a requirement to create it.

## Current Shape

| Current home | Responsibility |
| --- | --- |
| `scripts/00.chat/<domain>/<capability>/` | Chat startup, session logs, worktrees, refresh, commit/promotion and portable workbench support. |
| `scripts/01.harness/` | Metadata, process/command checks and the governed script runner. |
| `scripts/repo/<capability>/` | Existing repository machinery such as check selection, commit gates, workspace compilation, module structure and diagnostic coverage. |
| `scripts/04.deploy/` | Active build, package, deployment, runtime and recovery owners, plus shared controls and separately retained legacy families. |
| `scripts/02.rag-rulebook/` | Dormant retrieval and rulebook machinery, retained for explicit maintenance, not automatic core-platform or ordinary commit work. |
| `scripts/helpers/` | Helper catalogue, audit evidence and migration planning; not a destination for every reusable function. |

`scripts/03.product/` remains a proposed product-automation namespace, not an
implemented owner in this checkout. Product application code remains with its
actual application/package owners; a file need not live under `scripts/`
merely because a check imports it.

Active deployment work uses the implemented `lifecycle/00-target-alignment/`,
`20-build/`, `40-package/`, `50-deploy/` and `60-run/` homes. The current target
is `kanbien-core-platform`. Staging-specific commands live separately under
`scripts/04.deploy/legacy/kanbien-staging/`; RAG deployment readiness lives under
`scripts/04.deploy/legacy/rag-rulebook/`. Retained does not mean deleted or
automatically disabled: existing staging schedules keep their own authority.
See `scripts/04.deploy/README.md` for concrete command boundaries.

Helpers stay with the capability that actually owns them. For example,
`scripts/repo/check-selection/check-inputs.mjs` derives check inputs while
`scripts/repo/workspace-build/` owns compilation. A shared directory requires
real shared consumers, not just a generic function name.

Use `scripts/` as the canonical executable command surface. The term `tools`
describes automation capabilities, not a separate top-level command namespace.
Future MCP exposure should wrap stable script capabilities through an explicit
registry or manifest instead of importing layer internals directly.

Do not add new chat lifecycle scripts under `scripts/shared/chat/` or
`scripts/shared/git/`. Those were compatibility locations from the earlier
layout and are now retired.

## Capability Folders

Keep each capability's operation, helpers, tests, fixtures and wrappers
recognisable. Existing entry-point names include `script.sh`, `script.py` and
focused `*-test` files; a file name alone does not determine its role or effects.
Use subfolders when distinct responsibilities warrant them, not to fill an
empty template or fragment one cohesive function.

The existing capability guide should explain purpose, inputs, effects and
boundaries. Extend its current implementation and proof before inventing a new
wrapper. New files need metadata; new source above 50 code lines, excluding
metadata, needs prior approval. The existing script-admission standard owns
the need, owner, consumer, risk and cost decision. Approved moves update the
files and real callers together, without an unnecessary compatibility copy.

## Public Surface

Humans should usually use `package.json` `chat:*` scripts. Those package
scripts delegate to canonical `scripts/00.chat/...` paths.

Harness workflows and command guides name the implemented owner, including
`scripts/repo/` where appropriate. Approval-sensitive instructions use the
governed runner as required by the permissions standard; selection does not
grant execution authority.

The existing selector uses `scripts/repo/check-selection/checks.yml` to choose
required proof from affected inputs and the commit/integration boundary. Helpers are not all
standalone checks, and the folder map is not a request to run every test.
Broad hygiene remains explicitly requested or deferred unless its declared
candidate risk requires selection. A retained check is not a nightly schedule;
no new scheduler is introduced by this layout.

## Historical Paths

Historical documents may mention retired paths, but should do so as migration
history:

- say what previously lived there
- name the current canonical path or say the behavior was retired
- avoid runnable examples that make the old path look current

Negative tests may create retired paths in throwaway repositories when they are
proving the governed runner rejects old compatibility surfaces.
