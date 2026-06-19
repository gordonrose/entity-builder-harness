<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain stable public aliases for chat-layer scripts.
domain: command
portability: llm-workbench-required
used_by:
  - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
-->

# Chat Script Aliases

This directory exposes chat-layer script entrypoints.

The implementations live under `scripts/00.chat/`. Keep these public aliases
thin so terminal users and bootstrap installs have stable, memorable command
paths while canonical ownership remains in the `00.chat` layer.
