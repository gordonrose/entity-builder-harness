#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-server-dependency-boundary
#   version: 1
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

# B10 isolated diagnostic fixture (no compiler, provider or repository mutation).
python3 -B - "$ROOT" <<'B10_PY'
import importlib.util, json, sys, tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('b10_boundary',Path(sys.argv[1])/'scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.py'); module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory); module.ROOT=root; package=root/'packages/core/package.json'; package.parent.mkdir(parents=True)
    package.write_text('[]')
    try: module.discover_manifest_dependencies({'@kanbien/core'})
    except module.BoundaryFailure as error: assert error.codes==('package-manifest-invalid',)
    else: raise AssertionError('nonmapping manifest accepted')
    lock=root/'package-lock.json'; lock.write_text('[]')
    try: module.ensure_lockfile_records(set())
    except module.BoundaryFailure as error: assert error.codes==('lockfile-invalid',)
    else: raise AssertionError('nonmapping lockfile accepted')
    package.write_bytes(b'\xff')
    try: module.discover_manifest_dependencies({'@kanbien/core'})
    except module.BoundaryFailure as error: assert error.codes==('package-manifest-unreadable',)
    else: raise AssertionError('invalid UTF8 accepted')
B10_PY
echo "Core server dependency-boundary local tests passed."
