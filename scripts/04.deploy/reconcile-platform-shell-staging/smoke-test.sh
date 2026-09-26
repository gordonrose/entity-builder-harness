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
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/reconcile-platform-shell-staging/script.py").read_text(encoding="utf-8"), "reconcile-platform-shell-staging.py", "exec")'
python3 - <<'PY'
import importlib.util
from pathlib import Path

source = Path("scripts/04.deploy/reconcile-platform-shell-staging/script.py")
specification = importlib.util.spec_from_file_location("reconciliation", source)
module = importlib.util.module_from_spec(specification)
assert specification.loader is not None
specification.loader.exec_module(module)

try:
    module.run_check(
        "artifact-bucket-controls",
        lambda: (_ for _ in ()).throw(module.ReconciliationError("aws-verification-unavailable")),
    )
except module.ReconciliationError as exception:
    assert str(exception) == "artifact-bucket-controls-verification-unavailable"
else:
    raise AssertionError("unavailable provider result was not attributed to its owning control")
PY
result="$(bash scripts/04.deploy/reconcile-platform-shell-staging/script.sh --validate --json)"
if [[ "$result" != *'"verdict": "passed"'* || "$result" != *'"id": "source-policy"'* ]]; then
  echo "ERROR: reconciliation source validation did not emit the expected safe result" >&2
  exit 1
fi
echo "Platform-shell deployment reconciliation local check passed."
