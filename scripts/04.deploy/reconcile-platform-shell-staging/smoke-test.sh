#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.reconcile-platform-shell-staging.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Verify local fail-closed reconciliation source validation without contacting AWS.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: package.script.platform-shell-deployment-reconciliation-check
#     path: package.json
#   effects:
#   - read-only

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if rg -q 'ThreadPoolExecutor|concurrent\.futures' scripts/04.deploy/reconcile-platform-shell-staging/script.py; then
  echo "ERROR: reconciliation AWS calls must remain serial." >&2
  exit 1
fi
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/reconcile-platform-shell-staging/script.py").read_text(encoding="utf-8"), "reconcile-platform-shell-staging.py", "exec")'
python3 - <<'PY'
import runpy
import subprocess
from types import SimpleNamespace
from pathlib import Path

module = runpy.run_path(Path("scripts/04.deploy/reconcile-platform-shell-staging/script.py"))

try:
    module["run_check"](
        "artifact-bucket-controls",
        lambda: (_ for _ in ()).throw(module["ReconciliationError"]("aws-verification-unavailable")),
    )
except module["ReconciliationError"] as exception:
    assert str(exception) == "artifact-bucket-controls-verification-unavailable"
else:
    raise AssertionError("unavailable provider result was not attributed to its owning control")

attempts = 0
original_run = module["subprocess"].run
original_sleep = module["time"].sleep

def transient_then_success(*_arguments, **_keywords):
    global attempts
    attempts += 1
    if attempts < 3:
        raise subprocess.CalledProcessError(1, "aws")
    return SimpleNamespace(stdout='"retry-success"')

module["subprocess"].run = transient_then_success
module["time"].sleep = lambda _seconds: None
try:
    result = module["run_aws"](
        SimpleNamespace(aws_cli="aws", aws_credential_source="environment", timeout_seconds=1),
        {"region": "eu-west-1"},
        ["sts", "get-caller-identity"],
    )
finally:
    module["subprocess"].run = original_run
    module["time"].sleep = original_sleep
assert result == "retry-success"
assert attempts == 3

attempts = 0

def always_fail(*_arguments, **_keywords):
    global attempts
    attempts += 1
    raise subprocess.CalledProcessError(1, "aws")

module["subprocess"].run = always_fail
module["time"].sleep = lambda _seconds: None
try:
    module["run_aws"](
        SimpleNamespace(aws_cli="aws", aws_credential_source="environment", timeout_seconds=1),
        {"region": "eu-west-1"},
        ["cloudformation", "detect-stack-drift"],
        "artifact-stack-drift-detection-unavailable",
    )
except module["ReconciliationError"] as exception:
    assert str(exception) == "artifact-stack-drift-detection-unavailable"
else:
    raise AssertionError("provider unavailability did not preserve the supplied safe failure code")
finally:
    module["subprocess"].run = original_run
    module["time"].sleep = original_sleep
assert attempts == 3
PY
result="$(bash scripts/04.deploy/reconcile-platform-shell-staging/script.sh --validate --json)"
if [[ "$result" != *'"verdict": "passed"'* || "$result" != *'"id": "source-policy"'* ]]; then
  echo "ERROR: reconciliation source validation did not emit the expected safe result" >&2
  exit 1
fi
echo "Platform-shell deployment reconciliation local check passed."
