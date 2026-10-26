#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.run-platform-shell-persistence-admission-probe.smoke-test
#   version: 2
#   status: active
#   created_on: "2026-09-25"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Verify that the write-admission probe stays fixed, no-body, and non-mutating without contacting AWS or the public target.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   - writes-files
#   used_by:
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.py").read_text(encoding="utf-8"), "persistence-admission-probe.py", "exec")'
result="$(bash scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.sh --validate)"
if [[ "$result" != '{"persistence_admission_probe":"validated"}' ]]; then
  echo "ERROR: persistence admission-probe validation did not emit the safe expected result" >&2
  exit 1
fi


if bash scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.sh --validate --execute >/dev/null 2>&1; then
  echo "ERROR: the admission probe must accept exactly one operating mode" >&2
  exit 1
fi

if grep -Eq -- 'smoke/work-items"|X-Request-Id|data=.*admission|request_acceptance|atomicWriter|repository' scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.py; then
  echo "ERROR: the admission probe must not contain a write route, request identity, request body, or persistence seam" >&2
  exit 1
fi

# Exercise the real Python CLI against disposable policy inputs. The tripwire
# denies AWS and HTTP even if a lifecycle guard regresses; source-state changes
# must never cause this local smoke to access the real target.
python3 - <<'PYTEST'
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

program = Path("scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.py").resolve()
profile_path = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
source_profile = yaml.safe_load(profile_path.read_text())
checks = 0
with tempfile.TemporaryDirectory(prefix="admission-probe-cli-") as directory:
    root = Path(directory)
    fixture = root / profile_path
    fixture.parent.mkdir(parents=True)
    tripwire = root / "external-access-attempted"
    (root / "sitecustomize.py").write_text("""import os, pathlib, subprocess, urllib.request
_original_run = subprocess.run
def _deny(*args, **kwargs):
    pathlib.Path(os.environ['ADMISSION_TEST_TRIPWIRE']).write_text('attempted')
    raise AssertionError('local admission validation attempted external access')
def _run(argv, *args, **kwargs):
    if isinstance(argv, (list, tuple)) and argv and pathlib.Path(str(argv[0])).name == 'aws':
        return _deny()
    return _original_run(argv, *args, **kwargs)
subprocess.run = _run
urllib.request.urlopen = _deny
""")
    environment = {**os.environ, "PYTHONPATH": str(root), "ADMISSION_TEST_TRIPWIRE": str(tripwire), "PYTHONDONTWRITEBYTECODE": "1"}

    def run(profile, args, *, code=0, error=None):
        global checks
        fixture.write_text(yaml.safe_dump(profile, sort_keys=False))
        result = subprocess.run([sys.executable, "-B", str(program), *args], cwd=root, env=environment, capture_output=True, text=True, timeout=10)
        assert result.returncode == code, (args, result.returncode, result.stdout, result.stderr)
        if error:
            assert error in result.stderr, result.stderr
        else:
            assert json.loads(result.stdout) == {"persistence_admission_probe": "validated"}, result.stdout
        assert not tripwire.exists(), "local fixture attempted AWS or HTTP"
        checks += 1

    run(source_profile, ["--validate"])
    for field, replacement in (
        ("entrypoint", None),
        ("entrypoint", "scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh"),
        ("route", "POST /smoke/work-items"),
        ("request_body", "allowed"),
        ("persistence_side_effects", "allowed"),
        ("output_policy", "include-response-body"),
        ("unexpected", "ignored"),
    ):
        profile = copy.deepcopy(source_profile)
        probe = profile["auth"]["persistence_write_test_client"]["admission_probe"]
        if replacement is None:
            del probe[field]
        else:
            probe[field] = replacement
        run(profile, ["--validate"], code=1, error="must retain its fixed non-mutating policy")

    states = (
        ("write-proof-failed-non-committing-admission-probe-source-ready-deployment-pending", "source-ready-deployment-pending", "reviewed-service-deployment-and-health-before-one-execution", False),
        ("write-proof-failed-non-committing-admission-probe-deployed-pending-execution", "deployed-pending-one-execution", "one-execution-only-then-record-safe-result-before-any-fresh-persistence-write", True),
        ("write-proof-failed-non-committing-admission-probe-passed-fresh-acceptance-pending", "executed-passed-fresh-acceptance-pending", "one-fresh-acceptance-with-new-fixed-identity-before-relay-or-worker-action", False),
        ("write-proof-failed-non-committing-iam-remediation-source-ready-deployment-pending", "executed-passed-iam-remediation-pending", "deploy-and-prove-least-privilege-iam-remediation-before-one-new-fixed-identity-acceptance", False),
        ("write-proof-failed-non-committing-iam-remediation-deployed-authorization-proven-fresh-acceptance-pending", "executed-passed-iam-remediation-pending", "one-fresh-acceptance-with-new-fixed-identity-before-relay-or-worker-action", False),
        ("deployed-and-write-proven", "executed-passed-iam-remediation-pending", "one-fresh-acceptance-with-new-fixed-identity-before-relay-or-worker-action", False),
    )
    for status, probe_status, next_guard, executable in states:
        profile = copy.deepcopy(source_profile)
        client = profile["auth"]["persistence_write_test_client"]
        client["status"] = status
        client["admission_probe"].update(status=probe_status, next_guard=next_guard)
        run(profile, ["--validate"])
        if not executable:
            run(profile, ["--execute"], code=1, error="may run only after the reviewed service deployment is healthy")
    run(source_profile, ["--validate", "--execute"], code=2, error="choose exactly one")
print(f"Persistence admission-probe CLI regressions passed ({checks} cases; no AWS or HTTP).")
PYTEST

echo "Persistence admission-probe local validation passed."
