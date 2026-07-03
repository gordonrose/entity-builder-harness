<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.docs.readme
  version: 1
  status: active
  layer: 00.chat
  domain: documentation
  disciplines:
  - agentic
  kind: readme
  purpose: Index chat workbench documentation that supports the portable chat harness
    and public bootstrap.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.bootstrap-chat-workbench-repo
    path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
  - id: chat.script.upstream.bootstrap-llm-workbench-repo
    path: scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh
-->
# Chat Workbench Docs

This folder contains documentation owned by the chat layer.

These files explain the portable chat workbench shape, not the source product
repo as a whole. Keep docs here when they are about chat lifecycle scripts,
public `llm-workbench` bootstrap boundaries, or current public-beta
portability behavior.

## Files

- `script-layout.md` explains the numbered `scripts/` layer command-surface
  convention, including the current `scripts/00.chat/` and
  `scripts/01.harness/` split.
- `llm-workbench-acceptance-matrix.md` maps the public-beta contract to the
  artifacts and checks that enforce it.
- `bootstrap/llm-workbench-template/` contains starter public repo shell files
  for the first `llm-workbench` bootstrap.

## Maintainer History

Maintainer decision history remains in the source repo and is not exported.
Public workbench exports should be understandable from current public docs such
as `docs/install.md`, `docs/workflows.md`, `docs/concepts.md`, and
`docs/adapting-to-your-repo.md`.
