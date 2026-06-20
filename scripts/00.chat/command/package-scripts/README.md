<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain validation for package.json chat command scripts.
domain: command
portability: llm-workbench-validation
used_by:
  - scripts/00.chat/command/package-scripts/smoke-test.sh
  - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
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

