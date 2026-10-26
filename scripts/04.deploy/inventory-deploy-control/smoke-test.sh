#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.inventory-deploy-control.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-10-06"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.governance
#   disciplines:
#   - architecture
#   - sre
#   kind: script
#   purpose: Validate the deploy-control inventory's stable report shape.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   - writes-files
#   used_by:
#   - id: deploy.script.inventory-deploy-control
#     path: scripts/04.deploy/inventory-deploy-control/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 - <<'PY'
from __future__ import annotations

import json
import subprocess

result = subprocess.run(
    ["bash", "scripts/04.deploy/inventory-deploy-control/script.sh", "--json"],
    check=True,
    capture_output=True,
    encoding="utf-8",
)
report = json.loads(result.stdout)
assert report["schema"] == "deploy/delivery-coverage-report/v1"
assert report["source_revision"] and report["input_digest"] and report["inputs"]
assert report["summary"]["entrypoints"] >= 1
assert report["summary"]["routes"] >= 1
assert any(item["path"] == "scripts/04.deploy/inventory-deploy-control/script.py" for item in report["entrypoints"])
assert all("path" in item and "classification" in item for item in report["entrypoints"])
PY

python3 -B scripts/04.deploy/inventory-deploy-control/delivery-smoke-test.py
echo "Deploy control inventory smoke test passed."
