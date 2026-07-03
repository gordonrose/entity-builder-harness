<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.upstream.validate-llm-workbench-portability.readme
  version: 1
  status: active
  layer: 00.chat
  domain: validation
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the acceptance suite for provider-neutral llm-workbench installs.
  portability:
    class: reusable
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.upstream.validate-llm-workbench-portability
    path: scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh
-->
# Validate llm-workbench Portability

`script.sh` is the user-acceptance suite for the public `llm-workbench`
install contract. It validates that the source export can produce a public
workbench which installs into blank and existing repositories without binding
chat startup to one model provider, operating system, or code-assistant surface.

The suite intentionally tests the generated public workbench instead of only the
source harness. That keeps the acceptance target aligned with what external
users will clone and install.

It also runs `scripts/00.chat/upstream/check-llm-workbench-contract/script.sh`
against the source repo and generated public repo for fast static contract
checks.

Coverage includes:

- assistant surfaces: Codex-style `AGENTS.md`, Claude, Copilot, Cursor, and a
  generic CLI/Mistral handoff document
- operating-system portability signals for Linux, macOS, Windows, and WSL
- existing repositories with existing `package.json` and assistant instruction
  files
- blank repositories that need an install-time initial commit before first chat
- no durable chat classification in startup metadata
- provider-neutral transcript metrics with no Codex-only commit blocker
- provider-neutral default cost metrics with explicit pricing overrides
- source and public static contract checks
