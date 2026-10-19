#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.core-server-dependency-boundary
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Report the actual local compile boundary of the fixed Kanbien core server program without contacting a target or publishing a package.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.workflow.runnable-program-candidates
#     path: .agentic/04.deploy/workflows/runnable-program-candidates.md

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT
CONTRACT="infra/04.deploy/03.product/entrypoints/runnable-program-index.yml"

if ! bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh --contract "$CONTRACT" --json >/dev/null; then
  python3 scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py --contract "$CONTRACT" --json
  exit 1
fi

if ! bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/build.sh --out-dir "$TEMPORARY_DIRECTORY" >/dev/null 2>&1; then
  printf '%s\n' '{"findings":[{"code":"core-server-program-build-failed"}],"program_id":"kanbien-core-server","schema":"deploy/core-server-dependency-report/v1","scope":"dependency-boundary","verdict":"failed"}'
  exit 1
fi

python3 scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.py \
  --build-output "$TEMPORARY_DIRECTORY" \
  "$@"
