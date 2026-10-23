#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface/script.py" "$@"
