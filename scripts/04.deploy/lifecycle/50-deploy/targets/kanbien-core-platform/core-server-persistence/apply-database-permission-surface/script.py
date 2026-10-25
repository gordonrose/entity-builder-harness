#!/usr/bin/env python3
"""Apply only the reviewed PostgreSQL privilege-separation provider surface."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.apply-core-server-persistence-database-permission-surface.impl
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject every CloudFormation change except the reviewed database privilege-separation additions and expected task, role, and endpoint updates.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.apply-core-server-persistence-database-permission-surface
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-database-permission-surface/script.sh
#   effects: [aws-mutation]
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
STACK = "kanbien-core-platform-core-server-persistence"
CLUSTER = "kanbien-core-platform"
SERVICE = "kanbien-core-platform-core-server-persistence"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
COLLECTOR_ECR_URI = "337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server"
ALERT_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ADDED = {
    "AdministrationSecurityGroup": "AWS::EC2::SecurityGroup",
    "AdministrationDnsUdpEgress": "AWS::EC2::SecurityGroupEgress",
    "AdministrationDnsTcpEgress": "AWS::EC2::SecurityGroupEgress",
    "AdministrationEndpointEgress": "AWS::EC2::SecurityGroupEgress",
    "AdministrationArtifactObjectStoreEgress": "AWS::EC2::SecurityGroupEgress",
    "AdministrationDatabaseEgress": "AWS::EC2::SecurityGroupEgress",
    "DatabaseIngressFromAdministration": "AWS::EC2::SecurityGroupIngress",
    "EndpointIngressFromAdministration": "AWS::EC2::SecurityGroupIngress",
    "OrdinaryMigrationCredentialsSecret": "AWS::SecretsManager::Secret",
    "AdministrationExecutionRole": "AWS::IAM::Role",
    "CoreServerPersistenceAdministrationTaskDefinition": "AWS::ECS::TaskDefinition",
    "ObservabilityCollectorConfiguration": "AWS::SSM::Parameter",
    "ObservabilityAlarmTopic": "AWS::SNS::Topic",
    "ObservabilityAlertSubscription": "AWS::SNS::Subscription",
    "CoreServerPostgreSqlReadinessAlarm": "AWS::CloudWatch::Alarm",
    "PersistenceDatabaseFreeStorageAlarm": "AWS::CloudWatch::Alarm",
}
MODIFIED = {
    "ServerExecutionRole": "AWS::IAM::Role",
    "ServerTaskRole": "AWS::IAM::Role",
    "SecretsManagerEndpoint": "AWS::EC2::VPCEndpoint",
    "MigrationExecutionRole": "AWS::IAM::Role",
    "CoreServerPersistenceMigrationTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceVerifierTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceRestorationVerifierTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceService": "AWS::ECS::Service",
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value: dict[str, object] = {
        "schema": "deploy/persistence-database-permission-surface-report/v1",
        "target": "kanbien-core-platform",
        "scope": "core-server-persistence",
        "stack": STACK,
        "verdict": verdict,
        "findings": [{"code": code} for code in codes],
    }
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "updated-awaiting-administration" else 1


def stack_parameters(stack: object) -> dict[str, str] | None:
    if not isinstance(stack, dict):
        return None
    stacks = stack.get("Stacks")
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
        return None
    parameters = stacks[0].get("Parameters")
    if not isinstance(parameters, list):
        return None
    result: dict[str, str] = {}
    for parameter in parameters:
        if not isinstance(parameter, dict):
            return None
        key, value = parameter.get("ParameterKey"), parameter.get("ParameterValue")
        if not isinstance(key, str) or not isinstance(value, str):
            return None
        result[key] = value
    return result


def collector_receipt(path: Path) -> dict[str, str] | None:
    command = [
        "bash", str(ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"),
        "--receipt", str(path), "--expected-target", "kanbien-core-platform",
        "--expected-candidate", "observability-collector",
        "--expected-package-contract", "core-server-persistence-observability-collector-image",
        "--expected-program", "kanbien-observability-collector", "--json",
    ]
    checked = subprocess.run(command, capture_output=True, text=True)
    if checked.returncode:
        return None
    try:
        value = json.loads(checked.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) and isinstance(value.get("image_digest"), str) else None


def reviewable(change: object, stack_status: object, name: str, digest: str, revision: str, collector_image: str) -> bool:
    if not isinstance(change, dict) or stack_status not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        return False
    if name not in str(change.get("ChangeSetName", "")) or change.get("Status") != "CREATE_COMPLETE" or change.get("ChangeSetType") not in {None, "UPDATE"}:
        return False
    parameters = {
        item.get("ParameterKey"): item.get("ParameterValue")
        for item in change.get("Parameters", [])
        if isinstance(item, dict)
    }
    if parameters.get("ImageDigest") != digest or parameters.get("SupportImageDigest") != digest or parameters.get("RestoreVerifierImageDigest") != digest or parameters.get("SourceRevision") != revision or parameters.get("ObservabilityCollectorImage") != collector_image:
        return False
    # CloudFormation redacts NoEcho values in review responses.  The controller
    # therefore proves that the approved parameter was supplied without
    # copying its recipient value into a report or retained evidence.
    if "ObservabilityAlertEmail" not in parameters:
        return False
    added: set[str] = set()
    modified: set[str] = set()
    changes = change.get("Changes")
    if not isinstance(changes, list):
        return False
    for item in changes:
        resource = item.get("ResourceChange") if isinstance(item, dict) else None
        if not isinstance(resource, dict):
            return False
        logical_id, resource_type, action = resource.get("LogicalResourceId"), resource.get("ResourceType"), resource.get("Action")
        if action == "Add" and logical_id in ADDED and ADDED[logical_id] == resource_type:
            added.add(logical_id)
        elif action == "Modify" and logical_id in MODIFIED and MODIFIED[logical_id] == resource_type:
            modified.add(logical_id)
        else:
            return False
    return added == set(ADDED) and modified == set(MODIFIED)


def wait_for_review(prepare: object, name: str, status: str, digest: str, revision: str, collector_image: str) -> tuple[dict | None, str]:
    for attempt in range(6):
        ok, change, code = prepare.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
        if not ok:
            return None, code
        if reviewable(change, status, name, digest, revision, collector_image):
            return change, "ok"
        if attempt < 5:
            time.sleep(2)
    return None, "persistence-database-permission-surface-change-set-not-reviewable"


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--collector-receipt", type=Path)
    parser.add_argument("--alert-email")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None or args.collector_receipt is None or not isinstance(args.alert_email, str) or not ALERT_EMAIL.fullmatch(args.alert_email):
        return report("blocked", "persistence-database-permission-surface-arguments-invalid")
    prepare = load(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py", "prepare")
    create = load(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py", "create")
    receipt = prepare.validate_receipt(args.receipt)
    collector = collector_receipt(args.collector_receipt)
    if receipt is None or not create.package_gates(args.receipt) or not prepare.live_budget()[0]:
        return report("blocked", "persistence-database-permission-surface-preconditions-not-proven")
    if collector is None:
        return report("blocked", "persistence-database-permission-surface-collector-custody-not-proven")
    if not prepare.candidate_image(receipt)[0]:
        return report("blocked", "persistence-database-permission-surface-candidate-image-unavailable")
    ok, stack, code = prepare.aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    parameters = stack_parameters(stack) if ok else None
    status = stack.get("Stacks", [{}])[0].get("StackStatus") if ok and isinstance(stack, dict) else None
    if parameters is None or status not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        return report("blocked", code if not ok else "persistence-database-permission-surface-stack-not-healthy")
    if parameters.get("ImageDigest") == receipt["image_digest"]:
        return report("blocked", "persistence-database-permission-surface-image-not-new")
    ok, service, code = prepare.aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", SERVICE)
    services = service.get("services", []) if ok and isinstance(service, dict) else []
    if len(services) != 1 or not isinstance(services[0], dict) or services[0].get("desiredCount") != 1 or services[0].get("runningCount") != 1:
        return report("blocked", "persistence-database-permission-surface-service-not-healthy")
    name = f"kanbien-core-platform-persistence-permissions-{receipt['image_digest'][7:19]}"
    collector_image = f"{COLLECTOR_ECR_URI}@{collector['image_digest']}"
    ok, _, code = prepare.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok:
        if code != "aws-resource-missing":
            return report("blocked", code)
        parameter_values = [{"ParameterKey": key, "UsePreviousValue": True} for key in parameters]
        for key, value in (("ImageDigest", receipt["image_digest"]), ("SupportImageDigest", receipt["image_digest"]), ("RestoreVerifierImageDigest", receipt["image_digest"]), ("SourceRevision", receipt["source_revision"]), ("ObservabilityCollectorImage", collector_image), ("ObservabilityAlertEmail", args.alert_email)):
            parameter_values = [item for item in parameter_values if item["ParameterKey"] != key]
            parameter_values.append({"ParameterKey": key, "ParameterValue": value})
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as parameter_file:
            json.dump(parameter_values, parameter_file)
            parameter_file.flush()
            ok, _, code = prepare.aws(
                "cloudformation", "create-change-set", "--stack-name", STACK, "--change-set-name", name,
                "--change-set-type", "UPDATE", "--template-body", f"file://{TEMPLATE}",
                "--parameters", f"file://{parameter_file.name}", "--capabilities", "CAPABILITY_NAMED_IAM",
            )
        if not ok:
            return report("blocked", code)
    change, code = wait_for_review(prepare, name, status, receipt["image_digest"], receipt["source_revision"], collector_image)
    if change is None:
        return report("blocked", code)
    ok, _, code = prepare.aws("cloudformation", "execute-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok:
        return report("blocked", code)
    waited = subprocess.run(
        ["aws", "cloudformation", "wait", "stack-update-complete", "--stack-name", STACK, "--profile", prepare.PROFILE, "--region", prepare.REGION],
        capture_output=True,
        text=True,
    )
    if waited.returncode:
        return report("blocked", "persistence-database-permission-surface-update-not-complete")
    return report(
        "updated-awaiting-administration",
        "persistence-database-permission-surface-update-executed",
        facts={"change_set": name, "candidate_image_digest": receipt["image_digest"], "candidate_source_revision": receipt["source_revision"], "collector_image_digest": collector["image_digest"]},
    )


if __name__ == "__main__":
    raise SystemExit(main())

