#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.inventory-deploy-control.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-10-06"
#   updated_on: "2026-10-28"
#   layer: 04.deploy
#   domain: deployment.governance
#   disciplines:
#   - architecture
#   - sre
#   kind: script
#   purpose: Require covered independent delivery census and exercise its discovery and command-boundary regressions.
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
    ["bash", "scripts/04.deploy/inventory-deploy-control/script.sh", "--check", "--json"],
    check=True,
    capture_output=True,
    encoding="utf-8",
)
report = json.loads(result.stdout)
assert report["schema"] == "deploy/delivery-coverage-report/v1"
assert report["verdict"] == "covered" and not report["findings"], report["findings"]
assert report["source_revision"] and report["input_digest"] and report["inputs"]
assert report["summary"]["entrypoints"] >= 1
assert report["summary"]["routes"] >= 1
assert any(item["path"] == "scripts/04.deploy/inventory-deploy-control/script.py" for item in report["entrypoints"])
assert all("path" in item and "classification" in item for item in report["entrypoints"])
PY

python3 -B scripts/04.deploy/inventory-deploy-control/delivery-smoke-test.py
echo "Deploy control inventory smoke test passed."
