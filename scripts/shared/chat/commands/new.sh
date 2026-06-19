#!/usr/bin/env bash
set -euo pipefail

exec bash scripts/shared/chat/request-initialization/start-chat-session.sh "$@"
