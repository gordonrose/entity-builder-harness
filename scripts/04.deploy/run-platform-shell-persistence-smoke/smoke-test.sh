#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.run-platform-shell-persistence-smoke.smoke-test
#   version: 2
#   status: active
#   created_on: "2026-09-24"
#   updated_on: "2026-10-26"
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
#   - writes-files
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

fixture_dir="$(mktemp -d "${TMPDIR:-/tmp}/persistence-smoke-local.XXXXXX")"
fixture="$fixture_dir/target-profile.yml"
trap 'rm -rf "$fixture_dir"' EXIT
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
# Fail closed even if a production lifecycle guard regresses. The fixtures must
# not reach AWS, retrieve credentials, or issue an HTTP acceptance request.
(target.parent / "aws-denied").write_text('#!/bin/sh\nprintf aws > "$PERSISTENCE_SMOKE_TEST_TRIPWIRE"\nexit 97\n', encoding="utf-8")
(target.parent / "aws-denied").chmod(0o700)
(target.parent / "sitecustomize.py").write_text("""import os
from pathlib import Path
from urllib import request
def deny_http(*args, **kwargs):
    Path(os.environ['PERSISTENCE_SMOKE_TEST_TRIPWIRE']).write_text('http')
    raise AssertionError('local persistence smoke attempted HTTP')
request.urlopen = deny_http
""", encoding="utf-8")
PY

export PYTHONPATH="$fixture_dir${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export PERSISTENCE_SMOKE_TEST_TRIPWIRE="$fixture_dir/external-access-attempted"
fake_aws="$fixture_dir/aws-denied"

fixture_result="$(bash scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh --validate --target-profile "$fixture")"
if [[ "$fixture_result" != '{"persistence_smoke":"validated"}' ]]; then
  echo "ERROR: deployed persistence smoke policy validation did not emit the safe expected result" >&2
  exit 1
fi

if bash scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh --validate --approve-fresh-after-iam-remediation --target-profile "$fixture" --aws-cli "$fake_aws" >"$fixture_dir/validate.stdout" 2>"$fixture_dir/validate.stderr"; then
  echo "ERROR: persistence smoke IAM-remediation guard must be unavailable in validation mode" >&2
  exit 1
fi
grep -Fq -- '--approve-fresh-after-iam-remediation is valid only with --execute' "$fixture_dir/validate.stderr"

if bash scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh --execute --target-profile "$fixture" --aws-cli "$fake_aws" >"$fixture_dir/execute.stdout" 2>"$fixture_dir/execute.stderr"; then
  echo "ERROR: initial persistence smoke execution must not run against the controlled remediation-pending lifecycle" >&2
  exit 1
fi
grep -Fq -- 'the initial persistence acceptance proof may run only after its reviewed service deployment' "$fixture_dir/execute.stderr"

if bash scripts/04.deploy/run-platform-shell-persistence-smoke/script.sh --execute --approve-fresh-after-iam-remediation --approve-replacement-after-remediation --target-profile "$fixture" --aws-cli "$fake_aws" >"$fixture_dir/conflicting.stdout" 2>"$fixture_dir/conflicting.stderr"; then
  echo "ERROR: persistence smoke must reject conflicting fresh-write guards before live AWS access" >&2
  exit 1
fi
grep -Fq -- 'choose at most one governed fresh-write approval guard' "$fixture_dir/conflicting.stderr"

if [ -e "$PERSISTENCE_SMOKE_TEST_TRIPWIRE" ]; then
  echo "ERROR: local persistence smoke attempted AWS or HTTP access" >&2
  exit 1
fi

echo "Persistence smoke local validation passed (fixture lifecycle guards; no AWS or HTTP)."
