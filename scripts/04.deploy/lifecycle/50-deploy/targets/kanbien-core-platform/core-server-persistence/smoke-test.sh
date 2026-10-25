#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.core-server-persistence-target-controls
#   version: 2
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the persistence creation, failed-candidate retirement, and run controls reject selectors, unqualified receipts, unsuitable change sets, and unsafe verifier use without contacting AWS.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/core-server-persistence/create-and-verify-private-postgresql-candidate.md
#   effects: [read-only]
ROOT="$(git rev-parse --show-toplevel)"
PREPARE="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.sh"
CREATE="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.sh"
DEPLOY="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate/script.sh"
RETIRE="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.sh"
MIGRATE="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.sh"
VERIFY="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh"
REPLACE="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.sh"
ROUTE_UPDATE="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-private-verifier-route-update/script.sh"
TRANSITION="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.sh"
expect_failure() { local code="$1"; shift; local output; if output="$("$@" 2>&1)"; then echo 'ERROR: expected failure' >&2; exit 1; fi; [[ "$output" == *"$code"* ]] || { echo "ERROR: expected $code: $output" >&2; exit 1; }; }
expect_failure persistence-candidate-preparation-arguments-invalid "$PREPARE" --target staging --json
expect_failure package-custody-receipt-invalid "$CREATE" --receipt /tmp/missing-persistence-receipt.json --json
expect_failure package-custody-receipt-invalid "$DEPLOY" --receipt /tmp/missing-persistence-receipt.json --approved-change-set unexpected --json
expect_failure persistence-failed-candidate-retirement-arguments-invalid "$RETIRE" --approved-failed-stack staging --json
expect_failure persistence-failed-candidate-retirement-arguments-invalid "$RETIRE" --json
expect_failure persistence-migration-arguments-invalid "$MIGRATE" --target staging --json
expect_failure private-persistence-verification-arguments-invalid "$VERIFY" --target staging --json
expect_failure private-persistence-verification-arguments-invalid "$VERIFY" --mode arbitrary --json
expect_failure persistence-replacement-arguments-invalid "$REPLACE" --json
expect_failure persistence-private-route-update-arguments-invalid "$ROUTE_UPDATE" --json
expect_failure persistence-release-transition-arguments-invalid "$TRANSITION" --json
python3 - "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate/script.py" <<'PY'
import importlib.util, subprocess, sys
from unittest.mock import patch
spec = importlib.util.spec_from_file_location("candidate_deploy", sys.argv[1])
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
valid = {"ChangeSetName":"arn:aws:cloudformation:eu-west-1:337159794548:changeSet/kanbien-core-platform-persistence-create-aaaaaaaaaaaa/x","Status":"CREATE_COMPLETE","ChangeSetType":"CREATE","Parameters":[{"ParameterKey":"ImageDigest","ParameterValue":"sha256:" + "a" * 64},{"ParameterKey":"RestoreVerifierImageDigest","ParameterValue":"sha256:" + "a" * 64},{"ParameterKey":"SourceRevision","ParameterValue":"a" * 40}],"Changes":[{"ResourceChange":{"ResourceType":"AWS::RDS::DBInstance"}}]}
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
with patch.object(prepare.subprocess, "run", side_effect=subprocess.TimeoutExpired(["aws"], 30)):
    assert prepare.aws("cloudformation", "describe-stacks") == (False, None, "aws-command-timeout")
PY
python3 - "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-private-verifier-route-update/script.py" <<'PY'
import importlib.util, sys
from unittest.mock import patch
spec = importlib.util.spec_from_file_location("route_update", sys.argv[1]); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
name = "kanbien-core-platform-persistence-route-update-" + "a" * 12
change = {"ChangeSetName": name, "Status":"CREATE_COMPLETE", "ChangeSetType":"UPDATE", "Parameters":[{"ParameterKey":"ImageDigest","ParameterValue":"sha256:" + "a" * 64},{"ParameterKey":"RestoreVerifierImageDigest","ParameterValue":"sha256:" + "a" * 64},{"ParameterKey":"SourceRevision","ParameterValue":"a" * 40}], "Changes":[{"ResourceChange":{"Action":"Add","ResourceType":"AWS::EC2::SecurityGroupEgress","LogicalResourceId":"VerifierEgressToServer"}}]}
assert module.route_update_reviewable(change, "CREATE_COMPLETE", name, "sha256:" + "a" * 64, "a" * 40)
assert not module.route_update_reviewable({**change, "Changes":[{"ResourceChange":{"Action":"Modify","ResourceType":"AWS::EC2::SecurityGroupEgress","LogicalResourceId":"VerifierEgressToServer"}}]}, "CREATE_COMPLETE", name, "sha256:" + "a" * 64, "a" * 40)
class Prepare:
    def __init__(self): self.calls = 0
    def aws(self, *parts):
        self.calls += 1
        return True, ({**change, "Changes": []} if self.calls == 1 else change), "ok"
prepare = Prepare()
with patch.object(module.time, "sleep"):
    observed, code = module.reviewed_change_set(prepare, name, "CREATE_COMPLETE", "sha256:" + "a" * 64, "a" * 40)
assert observed == change and code == "ok" and prepare.calls == 2
PY
python3 - "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("replacement", sys.argv[1]); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
healthy = {"status":"ACTIVE", "desiredCount":1, "runningCount":1, "taskDefinition":"arn:task-definition/current", "deployments":[{"status":"PRIMARY", "rolloutState":"COMPLETED"}]}
assert module.healthy_service(healthy)
assert not module.healthy_service({**healthy, "runningCount": 0})
assert not module.healthy_service({**healthy, "deployments": [{"status":"PRIMARY", "rolloutState":"IN_PROGRESS"}]})
PY
python3 - "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.py" <<'PY'
import importlib.util, sys
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("candidate_retirement", sys.argv[1])
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

assert module.STACK == "kanbien-core-platform-core-server-persistence"
assert module.DATABASE == "kanbien-core-platform-persistence"

with patch.object(module, "aws", return_value=(True, {"Stacks": [{"StackStatus": "CREATE_COMPLETE"}]}, "ok")):
    assert module.failed_candidate_database() == (False, "persistence-failed-candidate-stack-not-retirable")

with patch.object(module, "aws", return_value=(True, {"services": [{"serviceName":module.SERVICE,"serviceArn":f"arn:aws:ecs:{module.REGION}:337159794548:service/{module.CLUSTER}/{module.SERVICE}","desiredCount": 1, "runningCount": 0, "pendingCount": 0}]}, "ok")):
    assert module.no_active_service() == (False, "persistence-failed-candidate-service-still-active")

database = {"DBInstances": [{"DBInstanceIdentifier": module.DATABASE, "PubliclyAccessible": False, "DeletionProtection": True, "DBInstanceArn": "arn:aws:rds:eu-west-1:337159794548:db:kanbien-core-platform-persistence"}]}
with patch.object(module, "aws", side_effect=[(True, database, "ok"), (True, {"TagList": [{"Key": "Target", "Value": "staging"}]}, "ok")]):
    assert module.protected_target_database() == (False, "persistence-failed-candidate-database-target-mismatch")

unlocked = {"DBInstances": [{"DBInstanceIdentifier": module.DATABASE, "DBInstanceArn": "synthetic", "DBInstanceStatus": "available", "PubliclyAccessible": False, "DeletionProtection": False}]}
with patch.object(module, "aws", side_effect=[(True, unlocked, "ok"), (True, {"TagList": [{"Key": "Target", "Value": "kanbien-core-platform"}]}, "ok")]):
    assert module.protected_target_database_after_unlock() == (True, "ok")
PY
python3 - "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.py" <<'PY'
import importlib.util, sys

spec = importlib.util.spec_from_file_location("migration", sys.argv[1])
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
arn = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "a" * 32
definition = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-migration:2"
task = {"taskArn": arn, "taskDefinitionArn": definition, "lastStatus": "STOPPED"}
assert module.current_reconciliation_task(task, arn, definition) == "ok"
assert module.current_reconciliation_task({**task, "lastStatus": "RUNNING"}, arn, definition) == "persistence-migration-reconciliation-task-not-terminal"
assert module.current_reconciliation_task({**task, "taskDefinitionArn": definition + "-other"}, arn, definition) == "persistence-migration-reconciliation-task-not-current"
assert module.current_reconciliation_task(task, "arn:aws:ecs:eu-west-1:337159794548:task/another-cluster/" + "a" * 32, definition) == "persistence-migration-reconciliation-task-identity-invalid"
PY
python3 - "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.py" <<'PY'
import importlib.util, sys

spec = importlib.util.spec_from_file_location("verifier", sys.argv[1])
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
arn = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "b" * 32
definition = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:2"
task = {"taskArn": arn, "taskDefinitionArn": definition, "lastStatus": "STOPPED"}
assert module.current_reconciliation_task(task, arn, definition) == "ok"
assert module.current_reconciliation_task({**task, "lastStatus": "RUNNING"}, arn, definition) == "private-persistence-verifier-reconciliation-task-not-terminal"
assert module.current_reconciliation_task({**task, "taskDefinitionArn": definition + "-other"}, arn, definition) == "private-persistence-verifier-reconciliation-task-not-current"
assert module.current_reconciliation_task(task, "arn:aws:ecs:eu-west-1:337159794548:task/another-cluster/" + "b" * 32, definition) == "private-persistence-verifier-reconciliation-task-identity-invalid"
PY
python3 - "$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml" <<'PY'
import sys
template = open(sys.argv[1], encoding="utf-8").read()
assert "PubliclyAccessible: false" in template
assert "DeletionProtection: true" in template
assert "BackupRetentionPeriod: 7" in template
assert "PERSISTENCE_POSTGRES_CA_PATH=/app/assets/rds-eu-west-1-bundle.crt" not in template
assert "PERSISTENCE_POSTGRES_CA_PATH" not in template, "the image owns this non-secret runtime default"
verifier = template[template.index("VerifierExecutionRole:"):template.index("RestorationVerifierExecutionRole:")]
assert "secretsmanager:GetSecretValue" not in verifier
assert "DatabaseIngressFromVerifier" not in template
for group in ("ServerSecurityGroup", "MigrationSecurityGroup"):
    expected = f"GroupId: !Ref {group}, IpProtocol: tcp, FromPort: 443, ToPort: 443, DestinationPrefixListId: !Ref S3ArtifactPrefixListId"
    assert expected in template, f"{group} must permit private ECR artifact-layer retrieval"
assert "GroupId: !Ref VerifierSecurityGroupId, IpProtocol: tcp, FromPort: 3000, ToPort: 3000, DestinationSecurityGroupId: !Ref ServerSecurityGroup" in template, "the private verifier must have explicit egress to the candidate server"
PY
python3 -B "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/controller-regression.py"
echo 'Core-server-persistence fixed target controls passed.'
