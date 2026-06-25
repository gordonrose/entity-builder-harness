<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.command.package-scripts.readme
  version: 1
  status: active
  layer: 00.chat
  domain: command
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain validation for package.json chat command scripts.
  portability:
    class: reusable
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.command.package-scripts.smoke-test
    path: scripts/00.chat/command/package-scripts/smoke-test.sh
  - id: chat.workflows.bootstrap-chat-workbench-repo
    path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
-->
# Package Scripts

This capability validates the public `package.json` `chat:*` command surface in
a throwaway repository.

The smoke test proves that package scripts can find their canonical
`scripts/00.chat/...` implementations after bootstrap. That matters for a
standalone workbench repo because outside engineers should not need to know the
internal folder layout before trying the harness.

This is validation tooling only; it is not a runtime command used during normal
chat work.

