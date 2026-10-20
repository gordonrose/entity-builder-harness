#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-server-image-payload-fixture
#   version: 1
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove the core-server package payload checker rejects a deliberately injected forbidden dependency without exposing payload contents.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - writes-files
#   used_by:
#   - id: deploy.command.smoke-test-core-server-image
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/build.sh --out-dir "$TEMPORARY_DIRECTORY/artifacts"
node scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs \
  --compiled-root "$TEMPORARY_DIRECTORY/artifacts"
python3 scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py \
  --compiled-root "$TEMPORARY_DIRECTORY/artifacts" --json | grep -F '"verdict": "passed"' >/dev/null
node scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/runtime-command-test.mjs \
  "$TEMPORARY_DIRECTORY/artifacts"

printf '%s\n' 'require("@kanbien/platform-persistence");' >> "$TEMPORARY_DIRECTORY/artifacts/kanbien-core-server.main.js"
if output="$(python3 scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py --compiled-root "$TEMPORARY_DIRECTORY/artifacts" --json 2>&1)"; then
  printf '%s\n' 'ERROR: expected injected forbidden dependency fixture to fail.' >&2
  exit 1
fi
[[ "$output" == *'"code": "compiled-payload-forbidden-dependency"'* ]]
[[ "$output" != *'platform-persistence'* ]]
printf '%s\n' 'Core-server package payload fixture passed.'
