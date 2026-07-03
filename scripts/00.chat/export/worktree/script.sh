#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.export.worktree
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: export
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Export a full chat worktree as a portable review bundle.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.command.download-repo
#     path: scripts/00.chat/command/download-repo/script.sh
#   effects:
#   - writes-files

exec node scripts/00.chat/export/create-worktree-bundle/script.js --mode worktree "$@"

