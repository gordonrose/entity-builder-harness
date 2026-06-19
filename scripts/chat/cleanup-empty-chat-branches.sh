#!/usr/bin/env bash
set -euo pipefail

exec bash scripts/shared/git/cleanup-empty-chat-branches.sh "$@"

