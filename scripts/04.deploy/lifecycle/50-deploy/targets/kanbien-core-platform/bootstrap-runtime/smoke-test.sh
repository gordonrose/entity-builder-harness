#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.target-controls
#   version: 4
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove fixed core-platform controls fail closed, recognise AWS lifecycle responses, and safely record accepted releases using isolated files without external access.
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
RELEASE_CONTRACT="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/release-contract/script.sh"
RESTORE="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/restore-accepted-release/script.sh"
ACCEPT="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/accept-release/script.sh"
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
expect_failure package-custody-receipt-invalid "$DEPLOY" --receipt /tmp/missing-core-receipt.json --operation update --approved-change-set kanbien-core-platform-update-aaaaaaaaaaaa --json
expect_failure package-custody-receipt-invalid "$VERIFY" --receipt /tmp/missing-core-receipt.json --json
expect_failure package-custody-receipt-invalid "$ACCEPT" --receipt /tmp/missing-core-receipt.json --verification-report /tmp/missing-verification-report.json --json
expect_failure RESTORE_CHANGE_SET_NOT_APPROVED "$RESTORE" --approved-change-set kanbien-core-platform-restore-aaaaaaaaaaaa --json
expect_selector_rejected "$PREPARE"
expect_selector_rejected "$DEPLOY"
expect_selector_rejected "$VERIFY"
"$RELEASE_CONTRACT" --json | grep -q '"verdict": "passed"'
bash "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/release-contract/smoke-test.sh"

accepted_receipt="$(mktemp)"; accepted_verification="$(mktemp)"; trap 'rm -f "$accepted_receipt" "$accepted_verification"' EXIT
python3 - "$accepted_receipt" "$accepted_verification" <<'PY'
import json, sys
digest="sha256:" + "a" * 64
revision="1" * 40
json.dump({"schema":"deploy/package-custody-receipt/v1","target":"kanbien-core-platform","environment_class":"private-bootstrap","provider_region_alias":"aws-eu-west-1","candidate_id":"kanbien-core-server-candidate","package_contract_id":"kanbien-core-server-image","program_id":"kanbien-core-server","source_revision":revision,"image_digest":digest,"release_identity":"source-"+revision,"checked_at":"2026-10-20T21:15:49Z","checks":{"runnable_program_contract":"passed","dependency_boundary":"passed","delivery_access_static":"passed","delivery_access_live":"passed","local_image_smoke":"passed","ecr_scan":"passed","sbom":"passed","provenance_attestation":"passed"},"verdict":"qualified","receipt_reference":"github-actions-run:39464882266"}, open(sys.argv[1], "w"))
json.dump({"schema":"deploy/private-runtime-verification-report/v1","target":"kanbien-core-platform","verdict":"accepted","findings":[{"code":"runtime-digest-and-private-verifier-accepted"}],"facts":{"source_revision":revision,"image_digest":digest,"runtime_task_definition":"runtime:2","verifier_task_definition":"verifier:2"}}, open(sys.argv[2], "w"))
PY
"$ACCEPT" --receipt "$accepted_receipt" --verification-report "$accepted_verification" --json | grep -q '"verdict": "ready-to-record"'

python3 - "$ROOT" "$accepted_receipt" "$accepted_verification" <<'PY'
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import yaml

sys.dont_write_bytecode = True
root = Path(sys.argv[1])
receipt_path, verification_path = map(Path, sys.argv[2:])
spec = importlib.util.spec_from_file_location("accept_release", root / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/accept-release/script.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
real_record = module.RECORD
baseline = real_record.read_bytes()
candidate = json.loads(receipt_path.read_text())
accepted = json.loads(verification_path.read_text())


def invoke(write=True):
    argv = ["accept-release", "--receipt", str(receipt_path), "--verification-report", str(verification_path), "--json"]
    if write:
        argv.append("--write")
    output = io.StringIO()
    with patch.object(sys, "argv", argv), contextlib.redirect_stdout(output):
        status = module.main()
    return status, json.loads(output.getvalue())


def blocked(code):
    before = module.RECORD.read_bytes()
    status, report = invoke()
    assert status == 1 and report["verdict"] == "blocked", report
    assert report["findings"] == [{"code": code}], report
    assert module.RECORD.read_bytes() == before, "failed acceptance changed the retained baseline"


with tempfile.TemporaryDirectory() as directory:
    # Exercise the real command and custody validator against a private record copy.
    module.RECORD = Path(directory) / "accepted-release.yml"
    module.RECORD.write_bytes(baseline)
    module.RECORD.chmod(0o640)
    status, report = invoke(write=False)
    assert status == 0 and report["verdict"] == "ready-to-record", report
    assert module.RECORD.read_bytes() == baseline
    status, report = invoke()
    assert status == 0 and report["verdict"] == "recorded", report
    generated = module.RECORD.read_text()
    record = yaml.safe_load(generated)
    release = record["release"]
    assert release["package_custody_reference"] == candidate["receipt_reference"]
    for key in ("source_revision", "image_digest", "runtime_task_definition", "verifier_task_definition"):
        assert release[key] == accepted["facts"][key], key
    assert record["cost_condition"] == yaml.safe_load(baseline)["cost_condition"]
    before_metadata = module.record_metadata(baseline.decode())
    after_metadata = module.record_metadata(generated)
    assert after_metadata["version"] == before_metadata["version"] + 1
    assert after_metadata["created_on"] == before_metadata["created_on"]
    assert after_metadata["updated_on"] == record["acceptance"]["accepted_at"][:10]
    assert module.RECORD.stat().st_mode & 0o777 == 0o640
    metadata_check = subprocess.run(
        ["bash", str(root / "scripts/01.harness/check-artifact-metadata-headers.sh"), "--proposed"],
        input=json.dumps({str(real_record.relative_to(root)): generated}), text=True, capture_output=True, cwd=root,
    )
    assert metadata_check.returncode == 0, metadata_check.stdout + metadata_check.stderr

    for invalid in (None, [], "accepted", 0, False, {}, {**accepted, "schema": "other/v1"}, {**accepted, "target": "other"}):
        verification_path.write_text(json.dumps(invalid))
        blocked("private-verification-report-invalid")
    verification_path.write_text("{")
    blocked("private-verification-report-unreadable")
    verification_path.write_text(json.dumps({**accepted, "facts": []}))
    blocked("private-verification-not-accepted")
    verification_path.write_text(json.dumps({**accepted, "facts": {**accepted["facts"], "image_digest": "sha256:" + "b" * 64}}))
    blocked("accepted-release-identity-mismatch")
    verification_path.write_text(json.dumps(accepted))
    receipt_path.write_text(json.dumps({**candidate, "receipt_reference": "invalid"}))
    blocked("package-custody-receipt-invalid")
    receipt_path.write_text(json.dumps(candidate))

    real_run = subprocess.run

    def replace_original_after_validation(command, **kwargs):
        assert command[command.index("--receipt") + 1] != str(receipt_path)
        result = real_run(command, **kwargs)
        receipt_path.write_text(json.dumps({**candidate, "receipt_reference": "invalid"}))
        return result

    with patch.object(module.subprocess, "run", side_effect=replace_original_after_validation):
        assert module.receipt(receipt_path) == candidate, "recording must retain the exact validated receipt"
    receipt_path.write_text(json.dumps(candidate))

    for operation in ("fsync", "replace"):
        with patch.object(module.os, operation, side_effect=OSError("simulated write failure")):
            blocked("accepted-release-record-write-failed")
        assert not list(Path(directory).glob(".accepted-release.yml.*.tmp")), "failed write left a temporary record"
    module.RECORD.write_text("schema: invalid\n")
    blocked("accepted-release-record-invalid")

assert real_record.read_bytes() == baseline, "isolated acceptance tests touched the real baseline"
PY

python3 - "$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml" <<'PY'
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
assert "User:" not in template, "the task definition must preserve the image's declared non-root runtime identity"
assert "- CMD\n              - /nodejs/bin/node\n              - -e" in template, "the ECS health check must execute the distroless image's Node binary without a shell"
assert "CMD-SHELL" not in template, "the ECS health check must not require a shell that the distroless image does not contain"
assert "- 'node -e" not in template, "the ECS health check must not rely on PATH in the distroless image"
verifier_command = re.search(r"Name: private-release-verifier\n.*?Command:\n(?P<body>.*?)          Environment:", template, re.S)
assert verifier_command, "missing private verifier command"
assert "- -e" in verifier_command.group("body"), "the private verifier must pass its inline program to the image entrypoint"
assert "- node" not in verifier_command.group("body"), "the private verifier must not duplicate the distroless Node entrypoint"
PY

python3 - "$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/foundation.yml" <<'PY'
import re
import sys

template = open(sys.argv[1], encoding="utf-8").read()
endpoint = re.search(r"LogsEndpoint:.*?\n      Tags:", template, re.S)
assert endpoint, "missing CloudWatch Logs endpoint"
expected = "Resource: !Sub 'arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:${LogGroup}:log-stream:*'"
assert expected in endpoint.group(0), "missing exact CloudWatch Logs endpoint policy resource"
assert "Resource: !Sub '${LogGroup.Arn}:log-stream:*'" not in endpoint.group(0)
assert template.count(expected) == 2, "endpoint and execution-role policies must use the exact log-stream ARN"
assert "Resource: !Sub '${LogGroup.Arn}:log-stream:*'" not in template
assert "S3ArtifactPrefixListId:" in template, "private image-layer retrieval must require an object-store prefix list"
for group in ("ServiceSecurityGroup", "VerifierSecurityGroup"):
    expected_egress = f"GroupId: !Ref {group}, IpProtocol: tcp, FromPort: 443, ToPort: 443, DestinationPrefixListId: !Ref S3ArtifactPrefixListId"
    assert expected_egress in template, f"{group} must permit private image-layer retrieval only through the managed object-store prefix list"
assert "CidrIp: 0.0.0.0/0" not in template, "foundation must not widen private workload egress to the internet"
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
assert module.update_change_set_is_reviewable({"Status": "CREATE_COMPLETE", "ChangeSetType": "UPDATE"}, "UPDATE_COMPLETE")
assert module.update_change_set_is_reviewable({"Status": "CREATE_COMPLETE", "ChangeSetType": "UPDATE"}, "CREATE_COMPLETE")
assert module.update_change_set_is_reviewable({"Status": "CREATE_COMPLETE"}, "UPDATE_COMPLETE")
assert not module.update_change_set_is_reviewable({"Status": "CREATE_COMPLETE", "ChangeSetType": "CREATE"}, "UPDATE_COMPLETE")
assert not module.update_change_set_is_reviewable({"Status": "CREATE_COMPLETE"}, "REVIEW_IN_PROGRESS")
assert not module.update_change_set_is_reviewable({"Status": "CREATE_COMPLETE", "ChangeSetType": "UPDATE"}, "UPDATE_IN_PROGRESS")
assert module.decoded_aws_response("") == {}
assert module.decoded_aws_response('{"accepted": true}') == {"accepted": True}
PY

python3 - "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/verify.py" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("verify_candidate", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

verifier = "arn:aws:ecs:eu-west-1:111122223333:task-definition/verifier:3"
tasks = [
    {"taskDefinitionArn": verifier, "stoppedAt": "2026-10-21T08:59:59Z", "taskArn": "arn:task/old"},
    {"taskDefinitionArn": verifier, "stoppedAt": "2026-10-21T09:01:00Z", "taskArn": "arn:task/new"},
]
assert module.completed_verifier_after(tasks, verifier, "2026-10-21T09:00:00Z")["taskArn"] == "arn:task/new"
assert module.completed_verifier_after(tasks, verifier, "2026-10-21T09:02:00Z") is None
assert module.task_exited_successfully({"containers": [{"exitCode": 0}]})
assert not module.task_exited_successfully({"containers": [{"exitCode": 1}]})
PY

echo "Fixed core-platform target control tests passed."
