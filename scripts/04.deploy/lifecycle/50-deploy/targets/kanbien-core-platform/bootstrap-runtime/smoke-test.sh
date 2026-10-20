#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.target-controls
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove fixed core-platform control commands reject target selection and fail closed without external access.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: aws.plan.kanbien-core-platform.release-rehearsal
#     path: docs/aws/kanbien-core-platform-release-rehearsal-plan.md

ROOT="$(git rev-parse --show-toplevel)"
PREPARE="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/prepare-candidate/script.sh"
DEPLOY="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/script.sh"
VERIFY="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/script.sh"
expect_failure() {
  local code="$1"; shift
  local output
  if output="$("$@" 2>&1)"; then
    echo "ERROR: expected fixed target control to fail closed" >&2
    exit 1
  fi
  [[ "$output" == *"$code"* ]] || { echo "ERROR: expected $code" >&2; exit 1; }
}

expect_selector_rejected() {
  local output
  if output="$("$1" --target kanbien/staging 2>&1)"; then
    echo "ERROR: target selector must be rejected" >&2
    exit 1
  fi
  [[ "$output" == *'ARGUMENTS_INVALID'* || "$output" == *'arguments-invalid'* ]] || { echo "ERROR: expected target selector rejection" >&2; exit 1; }
  [[ "$output" != *'kanbien/staging'* ]] || { echo "ERROR: rejected target value must not be echoed" >&2; exit 1; }
}

expect_failure RUNTIME_ALIGNMENT_RECEIPT_REQUIRED "$PREPARE" --json
expect_failure package-custody-receipt-invalid "$DEPLOY" --receipt /tmp/missing-core-receipt.json --approved-change-set kanbien-core-platform-a-aaaaaaaaaaaa --json
expect_failure package-custody-receipt-invalid "$VERIFY" --receipt /tmp/missing-core-receipt.json --json
expect_selector_rejected "$PREPARE"
expect_selector_rejected "$DEPLOY"
expect_selector_rejected "$VERIFY"

python3 - "$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/bootstrap-runtime.yml" <<'PY'
import re
import sys

template = open(sys.argv[1], encoding="utf-8").read()
match = re.search(r"ImageRepositoryUri:\n    Type: String\n    AllowedPattern: '([^']+)'", template)
assert match, "missing image repository pattern"
assert re.fullmatch(match.group(1), "337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server")
service_registry = re.search(r"ServiceRegistries:\n        - RegistryArn: !Ref ServiceDiscoveryArn\n(?P<body>.*?)      TaskDefinition:", template, re.S)
assert service_registry, "missing service-discovery registry binding"
assert "ContainerName:" not in service_registry.group("body")
assert "ContainerPort:" not in service_registry.group("body")
PY

python3 - "$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/foundation.yml" <<'PY'
import re
import sys

template = open(sys.argv[1], encoding="utf-8").read()
endpoint = re.search(r"LogsEndpoint:.*?\n      Tags:", template, re.S)
assert endpoint, "missing CloudWatch Logs endpoint"
expected = "Resource: !Sub 'arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:${LogGroup}:log-stream:*'"
assert expected in endpoint.group(0), "missing exact CloudWatch Logs endpoint policy resource"
assert "Resource: !Sub '${LogGroup.Arn}:log-stream:*'" not in endpoint.group(0)
PY

python3 - "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/deploy.py" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("deploy_candidate", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.initial_change_set_is_reviewable({"Status": "CREATE_COMPLETE"}, None)
assert module.initial_change_set_is_reviewable({"Status": "CREATE_COMPLETE", "ChangeSetType": "CREATE"}, "REVIEW_IN_PROGRESS")
assert not module.initial_change_set_is_reviewable({"Status": "CREATE_COMPLETE", "ChangeSetType": "UPDATE"}, "REVIEW_IN_PROGRESS")
assert not module.initial_change_set_is_reviewable({"Status": "CREATE_COMPLETE"}, "CREATE_COMPLETE")
assert module.decoded_aws_response("") == {}
assert module.decoded_aws_response('{"accepted": true}') == {"accepted": True}
PY

echo "Fixed core-platform target control tests passed."
