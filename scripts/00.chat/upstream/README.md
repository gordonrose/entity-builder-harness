<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.upstream.readme
  version: 1
  status: active
  layer: 00.chat
  domain: upstream
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain scripts that support promotion of reusable chat-harness lessons upstream.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-upstream-reusable-lesson
    path: .agentic/00.chat/workflows/chat-upstream-reusable-lesson.md
  - id: chat.script.upstream.bootstrap-llm-workbench-repo.readme
    path: scripts/00.chat/upstream/bootstrap-llm-workbench-repo/README.md
  - id: chat.script.upstream.ensure-llm-workbench-repo.readme
    path: scripts/00.chat/upstream/ensure-llm-workbench-repo/README.md
-->
# Upstream Scripts

Upstream scripts support moving reusable chat-harness lessons into a separate
workbench repository such as `llm-workbench`.

They do not decide what should be open sourced. They provide deterministic
checks around local upstream repo availability so the promotion workflow can
stay explicit.

## Capabilities

- `bootstrap-llm-workbench-repo/` plans how the public workbench shell and
  canonical chat harness files would be materialized into a target upstream
  repo. Its current implementation is dry-run only.
- `ensure-llm-workbench-repo/` checks the source-side canonical local clone of
  `gordonrose/llm-workbench`.
