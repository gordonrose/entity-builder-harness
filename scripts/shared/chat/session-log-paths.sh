#!/usr/bin/env bash

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility source shim for chat session id and commit log path helpers.
#   domain: session-log
#   portability: llm-workbench-compatibility
#   used_by:
#     - scripts/shared/git/prepare-chat-session-before-commit.sh
#     - scripts/shared/git/record-chat-commit.sh
#   effects: read-only

# shellcheck source=../../00.chat/session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"
