#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-server-image-payload-fixture
#   version: 2
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-10-31"
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

python3 -B scripts/04.deploy/lifecycle/40-package/build-core-server-image/runtime-preparation-diagnostic-test.py
bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/build.sh --out-dir "$TEMPORARY_DIRECTORY/artifacts"
node scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs \
  --compiled-root "$TEMPORARY_DIRECTORY/artifacts"
python3 scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py \
  --compiled-root "$TEMPORARY_DIRECTORY/artifacts" --json | grep -F '"verdict": "passed"' >/dev/null
node scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/runtime-command-test.mjs \
  "$TEMPORARY_DIRECTORY/artifacts"

python3 - "$ROOT" "$TEMPORARY_DIRECTORY/artifacts" <<'PY'
import json, subprocess, sys
from pathlib import Path
root, compiled = map(Path, sys.argv[1:])
manifest = compiled / 'node_modules/@kanbien/core/package.json'
original = manifest.read_bytes()
try:
    broken = json.loads(original)
    del broken['exports']['./security']
    manifest.write_text(json.dumps(broken))
    checked = subprocess.run(['python3', str(root / 'scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py'), '--compiled-root', str(compiled), '--json'], capture_output=True, text=True)
    assert checked.returncode == 1, 'missing transitive security export must fail before image construction'
    assert json.loads(checked.stdout)['diagnostics'] == [{'code': 'compiled-payload-core-export-unavailable'}]
finally:
    manifest.write_bytes(original)
print('Core-server transitive core-security export regression passed.')
PY

printf '%s\n' 'require("@kanbien/platform-persistence");' >> "$TEMPORARY_DIRECTORY/artifacts/kanbien-core-server.main.js"
if output="$(python3 scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py --compiled-root "$TEMPORARY_DIRECTORY/artifacts" --json 2>&1)"; then
  printf '%s\n' 'ERROR: expected injected forbidden dependency fixture to fail.' >&2
  exit 1
fi
[[ "$output" == *'"code": "compiled-payload-forbidden-dependency"'* ]]
[[ "$output" != *'platform-persistence'* ]]
printf '%s\n' 'Core-server package payload fixture passed.'
