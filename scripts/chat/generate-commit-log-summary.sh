#!/usr/bin/env bash
set -euo pipefail

exec bash scripts/shared/chat/generate-commit-log-summary.sh "$@"

