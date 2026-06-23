<!-- agentic-artifact:
owner: 00.chat
kind: readme
purpose: Index chat workbench documentation that supports the portable chat harness and public bootstrap.
domain: documentation
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
  - scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh
-->

# Chat Workbench Docs

This folder contains documentation owned by the chat layer.

These files explain the portable chat workbench shape, not the source product
repo as a whole. Keep docs here when they are about chat lifecycle scripts,
public `llm-workbench` bootstrap boundaries, or the set of chat-related ADRs
exported to the public workbench.

## Files

- `script-layout.md` explains the numbered `scripts/` layer command-surface
  convention, including the current `scripts/00.chat/` and
  `scripts/01.harness/` split.
- `chat-workbench-public-repo-readiness.md` defines what is copied,
  transformed, created, and excluded when bootstrapping `llm-workbench`.
- `public-chat-workbench-adrs.md` is the manifest of centralized harness ADRs
  copied into the public workbench.

## ADRs

Harness ADRs remain centralized under `docs/harness/architecture/adrs/`.

Use `public-chat-workbench-adrs.md` to select chat-relevant ADRs for public
export instead of moving ADR files into this folder.
