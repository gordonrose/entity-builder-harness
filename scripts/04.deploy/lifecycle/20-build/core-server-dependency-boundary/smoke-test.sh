#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.core-server-dependency-boundary
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove the core server dependency report accepts its reviewed graph and rejects a forbidden compiled dependency fixture.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - writes-files
#   used_by:
#   - id: deploy.command.core-server-dependency-boundary
#     path: scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
SCRIPT="scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.py"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/smoke-test.sh
bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/build.sh --out-dir "$TEMPORARY_DIRECTORY"
node scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/runtime-test.mjs "$TEMPORARY_DIRECTORY"

report="$(python3 "$SCRIPT" --build-output "$TEMPORARY_DIRECTORY" --json)"
[[ "$report" == *'"verdict": "passed"'* ]]
[[ "$report" == *'"platform-server"'* ]]
[[ "$report" != *'"platform-persistence"'* ]]

printf '%s\n' 'require("@kanbien/platform-persistence");' >> "$TEMPORARY_DIRECTORY/infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.js"
if output="$(python3 "$SCRIPT" --build-output "$TEMPORARY_DIRECTORY" --json 2>&1)"; then
  printf '%s\n' 'ERROR: expected forbidden dependency fixture to fail.' >&2
  exit 1
fi
[[ "$output" == *'"code": "build-output-forbidden-dependency"'* ]]
[[ "$output" != *'platform-persistence'* ]]

echo "Core server dependency-boundary local tests passed."
