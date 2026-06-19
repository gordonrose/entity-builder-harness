#!/usr/bin/env bash

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility source shim for chat session id and commit log path helpers.
#   domain: session-log
#   portability: llm-workbench-compatibility
#   used_by:
#     - scripts/shared/git/prepare-chat-session-before-commit.sh
#     - scripts/00.chat/session-log/record-chat-commit/script.sh
#     - scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh
#   effects: read-only

# shellcheck source=../../00.chat/session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"
