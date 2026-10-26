#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.provision-target-budget
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.foundation-cost-control
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the target-budget bootstrap route fails closed before AWS when alert configuration is absent and preserves CloudFormation's typed parameter semantics.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.provision-target-budget
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.py
#   effects: [read-only]
ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.py"

if output="$(env -u KANBIEN_CORE_PLATFORM_COST_ALERT_EMAIL python3 "$SCRIPT" --mode create --json 2>&1)"; then
  echo "ERROR: expected absent cost-alert configuration to block before AWS" >&2
  exit 1
fi
[[ "$output" == *'"code": "cost-alert-email-required"'* ]]

python3 - "$SCRIPT" <<'PY'
import ast
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
ast.parse(source)
assert '"UsePreviousValue": True' in source
assert 'expect_json: bool = True' in source
assert 'not expect_json and not completed.stdout.strip()' in source
PY

echo "Target-budget provisioning smoke test passed."

python3 -B "$ROOT/scripts/04.deploy/shared/provider-adapters/aws/recovery-test.py" RecoveryCli.test_budget_lost_response_resumes_exact_operation
