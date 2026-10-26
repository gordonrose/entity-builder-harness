#!/usr/bin/env python3
"""Apply only the reviewed PostgreSQL privilege-separation provider surface."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.apply-core-server-persistence-database-permission-surface.impl
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
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
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
STACK = "kanbien-core-platform-core-server-persistence"
CLUSTER = "kanbien-core-platform"
SERVICE = "kanbien-core-platform-core-server-persistence"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
ADDED = {
    # The pre-IAM target already owns the bounded administration network
    # surface.  This transition adds identity roles only; permitting the old
    # network additions here would make an unrelated topology change look like
    # an IAM migration.
    "ServerTaskRole": "AWS::IAM::Role",
    "MigrationTaskRole": "AWS::IAM::Role",
    "AdministrationTaskRole": "AWS::IAM::Role",
    "RestorationVerifierTaskRole": "AWS::IAM::Role",
}
MODIFIED = {
    # RDS IAM database authentication is enabled on the existing retained
    # instance; it is not a database replacement or restoration.
    "PersistenceDatabase": "AWS::RDS::DBInstance",
    "RuntimeCredentialsSecret": "AWS::SecretsManager::Secret",
    "OrdinaryMigrationCredentialsSecret": "AWS::SecretsManager::Secret",
    "SecretsManagerEndpoint": "AWS::EC2::VPCEndpoint",
    "ServerExecutionRole": "AWS::IAM::Role",
    "MigrationExecutionRole": "AWS::IAM::Role",
    "AdministrationExecutionRole": "AWS::IAM::Role",
    "RestorationVerifierExecutionRole": "AWS::IAM::Role",
    "CoreServerPersistenceMigrationTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceAdministrationTaskDefinition": "AWS::ECS::TaskDefinition",
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
        if key in result:return None
        result[key] = value
    return result


def reviewable(change: object, stack_status: object, name: str, digest: str, revision: str) -> bool:
    if not isinstance(change, dict) or stack_status not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        return False
    actual=change.get("ChangeSetName")
    exact=actual==name or (isinstance(actual,str) and actual.startswith("arn:aws:cloudformation:") and actual.split(":changeSet/",1)[-1].split("/",1)[0]==name)
    if not exact or change.get("Status") != "CREATE_COMPLETE" or change.get("ChangeSetType") not in {None, "UPDATE"}:
        return False
    parameters = {
        item.get("ParameterKey"): item.get("ParameterValue")
        for item in change.get("Parameters", [])
        if isinstance(item, dict)
    }
    if parameters.get("ImageDigest") != digest or parameters.get("SupportImageDigest") != digest or parameters.get("RestoreVerifierImageDigest") != digest or parameters.get("SourceRevision") != revision or parameters.get("EnableObservability") != "false":
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


def wait_for_review(prepare: object, name: str, status: str, digest: str, revision: str) -> tuple[dict | None, str]:
    for attempt in range(6):
        ok, change, code = prepare.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
        if not ok:
            return None, code
        if isinstance(change, dict) and change.get("Status") == "FAILED":
            # The provider may retain a failed, unexecuted change set.  Its
            # status is safe to expose as a fixed diagnostic category, but the
            # provider's raw reason can contain user-supplied parameter values
            # and is intentionally not copied into durable reports.
            return None, "persistence-database-permission-surface-change-set-failed"
        if reviewable(change, status, name, digest, revision):
            return change, "ok"
        if attempt < 5:
            time.sleep(2)
    return None, "persistence-database-permission-surface-change-set-not-reviewable"


def desired_parameters(receipt):
    return {"ImageDigest":receipt["image_digest"],"SupportImageDigest":receipt["image_digest"],"RestoreVerifierImageDigest":receipt["image_digest"],"SourceRevision":receipt["source_revision"],"EnableObservability":"false"}


def reconcile(prepare,name,receipt):
    verdict,code=prepare.observe_update(name,desired_parameters(receipt),lambda change:reviewable(change,"UPDATE_COMPLETE",name,receipt["image_digest"],receipt["source_revision"]))
    return report("updated-awaiting-administration" if verdict=="complete" else verdict,code,facts={"change_set":name,"candidate_image_digest":receipt["image_digest"],"candidate_source_revision":receipt["source_revision"]})


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--rollback-receipt",type=Path)
    parser.add_argument("--rollback-compatibility-id")
    parser.add_argument("--reconcile",action="store_true")
    # Accepted temporarily for workflow compatibility.  The independent
    # observability update validates and uses them; the privilege boundary
    # deliberately does not bind a collector or a notification recipient.
    parser.add_argument("--collector-receipt", type=Path)
    parser.add_argument("--alert-email")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None:
        return report("blocked", "persistence-database-permission-surface-arguments-invalid")
    if not args.reconcile and (args.rollback_receipt is None or args.rollback_compatibility_id is None):return report("blocked","persistence-permission-change-rollback-compatibility-required")
    prepare = load(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py", "prepare")
    create = load(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py", "create")
    receipt = prepare.validate_receipt(args.receipt)
    if receipt is None:return report("blocked","package-custody-receipt-invalid")
    name=f"kanbien-core-platform-persistence-permissions-{receipt['image_digest'][7:19]}"
    if args.reconcile:return reconcile(prepare,name,receipt)
    rollback=prepare.validate_receipt(args.rollback_receipt)
    if rollback is None or not prepare.rollback_compatibility(rollback,args.rollback_compatibility_id):return report("blocked","persistence-permission-change-rollback-compatibility-not-proven")
    if not create.package_gates(args.receipt) or not prepare.live_budget()[0]:
        return report("blocked", "persistence-database-permission-surface-preconditions-not-proven")
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
    ok, existing, code = prepare.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
    if ok and isinstance(existing,dict) and (existing.get("Status")=="FAILED" or existing.get("ExecutionStatus")!="AVAILABLE"):
        return reconcile(prepare,name,receipt)
    if not ok:
        if code != "aws-resource-missing":
            return report("blocked", code)
        parameter_values = [{"ParameterKey": key, "UsePreviousValue": True} for key in parameters]
        for key, value in (("ImageDigest", receipt["image_digest"]), ("SupportImageDigest", receipt["image_digest"]), ("RestoreVerifierImageDigest", receipt["image_digest"]), ("SourceRevision", receipt["source_revision"]), ("EnableObservability", "false")):
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
            return report("uncertain", code, facts={"change_set":name})
    change, code = wait_for_review(prepare, name, status, receipt["image_digest"], receipt["source_revision"])
    if change is None:return reconcile(prepare,name,receipt)
    if change.get("ExecutionStatus")!="AVAILABLE":return reconcile(prepare,name,receipt)
    actual={item.get("ParameterKey"):item.get("ParameterValue") for item in change.get("Parameters",[]) if isinstance(item,dict)}
    if not prepare.update_parameters_match(actual,desired_parameters(receipt),parameters):return report("blocked","persistence-update-live-parameters-mismatch")
    ok, _, code = prepare.aws("cloudformation", "execute-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok:return report("uncertain",code,facts={"change_set":name})
    return reconcile(prepare,name,receipt)



if __name__ == "__main__":
    raise SystemExit(main())

