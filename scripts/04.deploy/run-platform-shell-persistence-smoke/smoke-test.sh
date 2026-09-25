#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-persistence-smoke.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Locally validate the bounded persistence smoke policy without contacting AWS or the public target.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-persistence-smoke/script.py").read_text(encoding="utf-8"), "persistence-smoke.py", "exec")'
result="$(bash scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh --validate)"
if [[ "$result" != '{"persistence_smoke":"validated"}' ]]; then
  echo "ERROR: persistence smoke validation did not emit the safe expected result" >&2
  exit 1
fi

fixture="$(mktemp)"
trap 'rm -f "$fixture"' EXIT
python3 - "$fixture" <<'PY'
import json
from pathlib import Path
import sys
import yaml

source = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
target = Path(sys.argv[1])
document = yaml.safe_load(source.read_text(encoding="utf-8"))
write_client = document["auth"]["persistence_write_test_client"]
write_client["status"] = "write-proof-failed-non-committing-iam-remediation-deployed-authorization-proven-fresh-acceptance-pending"
write_client["client_id"] = "persistence-write-client-id"
write_client["secret_arn"] = "arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-persistence-write-client-fixture"
negative_client_id = document["auth"]["negative_test_client"]["client_id"]
document["config"]["non_secret_env"]["PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS"] = json.dumps([negative_client_id, write_client["client_id"]], separators=(",", ":"))
document["config"]["secret_refs"]["cognito_persistence_write_client_secret"] = {
    "name": "kanbien/staging/platform-shell/cognito-persistence-write-client",
    "arn": write_client["secret_arn"],
    "delivery": "bounded-persistence-smoke-only-not-ecs-task-environment",
    "value_format": "opaque-raw-string",
}
target.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
PY

fixture_result="$(bash scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh --validate --target-profile "$fixture")"
if [[ "$fixture_result" != '{"persistence_smoke":"validated"}' ]]; then
  echo "ERROR: deployed persistence smoke policy validation did not emit the safe expected result" >&2
  exit 1
fi

if bash scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh --validate --approve-fresh-after-iam-remediation >/dev/null 2>&1; then
  echo "ERROR: persistence smoke IAM-remediation guard must be unavailable in validation mode" >&2
  exit 1
fi

if bash scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh --execute >/dev/null 2>&1; then
  echo "ERROR: initial persistence smoke execution must not run against the recorded remediation-pending lifecycle" >&2
  exit 1
fi

if bash scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh --execute --approve-fresh-after-iam-remediation --approve-replacement-after-remediation --target-profile "$fixture" >/dev/null 2>&1; then
  echo "ERROR: persistence smoke must reject conflicting fresh-write guards before live AWS access" >&2
  exit 1
fi

echo "Persistence smoke local validation passed."
