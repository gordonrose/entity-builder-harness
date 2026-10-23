#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.core-server-persistence-target-controls
#   version: 1
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the persistence creation and run controls reject selectors, unqualified receipts, unsuitable change sets, and unsafe verifier use without contacting AWS.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/core-server-persistence/create-and-verify-private-postgresql-candidate.md
#   effects: [read-only]
ROOT="$(git rev-parse --show-toplevel)"
PREPARE="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.sh"
CREATE="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.sh"
DEPLOY="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate/script.sh"
MIGRATE="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.sh"
VERIFY="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh"
expect_failure() { local code="$1"; shift; local output; if output="$("$@" 2>&1)"; then echo 'ERROR: expected failure' >&2; exit 1; fi; [[ "$output" == *"$code"* ]] || { echo "ERROR: expected $code: $output" >&2; exit 1; }; }
expect_failure persistence-candidate-preparation-arguments-invalid "$PREPARE" --target staging --json
expect_failure package-custody-receipt-invalid "$CREATE" --receipt /tmp/missing-persistence-receipt.json --json
expect_failure package-custody-receipt-invalid "$DEPLOY" --receipt /tmp/missing-persistence-receipt.json --approved-change-set unexpected --json
expect_failure persistence-migration-arguments-invalid "$MIGRATE" --target staging --json
expect_failure private-persistence-verification-arguments-invalid "$VERIFY" --target staging --json
expect_failure private-persistence-verification-arguments-invalid "$VERIFY" --mode arbitrary --json
python3 - "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate/script.py" <<'PY'
import importlib.util, sys
from unittest.mock import patch
spec = importlib.util.spec_from_file_location("candidate_deploy", sys.argv[1])
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
valid = {"ChangeSetName":"arn:aws:cloudformation:eu-west-1:337159794548:changeSet/kanbien-core-platform-persistence-create-aaaaaaaaaaaa/x","Status":"CREATE_COMPLETE","ChangeSetType":"CREATE","Parameters":[{"ParameterKey":"ImageDigest","ParameterValue":"sha256:" + "a" * 64},{"ParameterKey":"SourceRevision","ParameterValue":"a" * 40}],"Changes":[{"ResourceChange":{"ResourceType":"AWS::RDS::DBInstance"}}]}
assert module.reviewable(valid, "REVIEW_IN_PROGRESS", "kanbien-core-platform-persistence-create-aaaaaaaaaaaa", "sha256:" + "a" * 64, "a" * 40)
assert not module.reviewable({**valid, "Changes":[{"ResourceChange":{"ResourceType":"AWS::S3::Bucket"}}]}, "REVIEW_IN_PROGRESS", "kanbien-core-platform-persistence-create-aaaaaaaaaaaa", "sha256:" + "a" * 64, "a" * 40)
assert not module.reviewable(valid, "CREATE_COMPLETE", "kanbien-core-platform-persistence-create-aaaaaaaaaaaa", "sha256:" + "a" * 64, "a" * 40)
assert not module.reviewable({**valid, "Parameters": []}, "REVIEW_IN_PROGRESS", "kanbien-core-platform-persistence-create-aaaaaaaaaaaa", "sha256:" + "a" * 64, "a" * 40)
prepare = module.controls()
class Result:
    returncode = 0
    stdout = ""
    stderr = ""
with patch.object(prepare.subprocess, "run", return_value=Result()):
    assert prepare.aws("cloudformation", "execute-change-set") == (True, {}, "ok")
PY
python3 - "$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml" <<'PY'
import sys
template = open(sys.argv[1], encoding="utf-8").read()
assert "PubliclyAccessible: false" in template
assert "DeletionProtection: true" in template
assert "BackupRetentionPeriod: 7" in template
assert "PERSISTENCE_POSTGRES_CA_PATH=/app/assets/rds-eu-west-1-bundle.crt" not in template
assert "PERSISTENCE_POSTGRES_CA_PATH" not in template, "the image owns this non-secret runtime default"
verifier = template[template.index("VerifierExecutionRole:"):template.index("Outputs:")]
assert "secretsmanager:GetSecretValue" not in verifier
assert "DatabaseIngressFromVerifier" not in template
PY
echo 'Core-server-persistence fixed target controls passed.'
