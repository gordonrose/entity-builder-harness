#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.rehearse-accepted-workload-replacement
#   version: 1
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the controlled accepted-workload replacement command rejects selector substitution and preserves safe task identity handling.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh
ROOT="$(git rev-parse --show-toplevel)"
COMMAND="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.sh"
if output="$("$COMMAND" --target kanbien/staging 2>&1)"; then
  echo "ERROR: fixed replacement rehearsal accepted a target selector" >&2; exit 1
fi
[[ "$output" == *"workload-recovery-arguments-invalid"* ]] || { echo "ERROR: missing fixed-target rejection" >&2; exit 1; }
[[ "$output" != *"kanbien/staging"* ]] || { echo "ERROR: unsafe selector echo" >&2; exit 1; }
python3 - "$COMMAND" <<'PY'
import importlib.util, sys
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("rehearsal", Path(sys.argv[1]).with_name("script.py"))
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
assert module.task_suffix({"taskArn":"arn:aws:ecs:region:account:task/cluster/0123456789abcdef"}) == "456789abcdef"
class Failed:
    returncode = 1
    stdout = ""
    stderr = ""
with patch.object(module.subprocess, "run", return_value=Failed()):
    assert module.preflight({}, Path("/tmp/accepted-receipt.json")) == (None, "cost-condition-not-approved")
PY
