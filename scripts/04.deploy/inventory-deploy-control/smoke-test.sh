#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.inventory-deploy-control.smoke-test
#   version: 1
#   status: active
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
assert report["schema"] == "deploy/control-inventory/v1"
assert report["scope"] == "repository source only; no provider reads, writes, or execution"
assert report["summary"]["script_capabilities"] >= 1
assert report["summary"]["infra_files"] >= 1
assert any(item["capability"] == "inventory-deploy-control" for item in report["scripts"])
assert all("path" in item and "role" in item for item in report["infra"])
PY

echo "Deploy control inventory smoke test passed."
