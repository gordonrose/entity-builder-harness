#!/usr/bin/env bash
set -euo pipefail

# This fixed target wrapper intentionally accepts no target, database, task,
# credential, queue, restore identifier, or timing override from a caller.
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 "$ROOT/scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py" "$@"
