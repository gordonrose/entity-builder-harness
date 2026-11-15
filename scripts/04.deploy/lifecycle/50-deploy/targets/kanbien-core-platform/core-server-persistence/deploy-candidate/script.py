#!/usr/bin/env python3
"""Execute only the exact reviewed persistence CREATE change set."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
STACK = "kanbien-core-platform-core-server-persistence"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
ALLOWED_TYPES = {
    "AWS::EC2::SecurityGroup", "AWS::EC2::SecurityGroupIngress", "AWS::EC2::SecurityGroupEgress", "AWS::EC2::VPCEndpoint",
    "AWS::RDS::DBSubnetGroup", "AWS::RDS::DBInstance", "AWS::SecretsManager::Secret", "AWS::ServiceDiscovery::Service",
    "AWS::IAM::Role", "AWS::ECS::TaskDefinition", "AWS::ECS::Service",
}


def controls():
    path = ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"
    spec = importlib.util.spec_from_file_location("persistence_prepare", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def operations():
    path = Path(__file__).resolve().parents[1] / "change-set-operations.py"
    spec = importlib.util.spec_from_file_location("persistence_change_set_operations", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value = {"schema": "deploy/persistence-deployment-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "stack": STACK, "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "deployed-awaiting-migration" else 1


def change_name_matches(value: object, expected: str) -> bool:
    return value == expected or (isinstance(value, str) and value.startswith("arn:aws:cloudformation:") and value.split(":changeSet/", 1)[-1].split("/", 1)[0] == expected)


def reviewable(change: object, stack_status: object, expected: str, digest: str, revision: str) -> bool:
    if not isinstance(change, dict) or stack_status not in {None, "REVIEW_IN_PROGRESS"}:
        return False
    if not change_name_matches(change.get("ChangeSetName"), expected) or change.get("Status") != "CREATE_COMPLETE":
        return False
    if change.get("ChangeSetType") not in {None, "CREATE"}:
        return False
    parameters = {item.get("ParameterKey"): item.get("ParameterValue") for item in change.get("Parameters", []) if isinstance(item, dict)}
    if parameters.get("ImageDigest") != digest or parameters.get("SupportImageDigest") != digest or parameters.get("RestoreVerifierImageDigest") != digest or parameters.get("SourceRevision") != revision:
        return False
    types = {item.get("ResourceChange", {}).get("ResourceType") for item in change.get("Changes", []) if isinstance(item, dict)}
    return bool(types) and types <= ALLOWED_TYPES


def parameters_match(change: dict, expected: dict[str, str]) -> bool:
    items = change.get("Parameters")
    return isinstance(items, list) and len(items) == len(expected) and all(isinstance(item, dict) for item in items) and {item.get("ParameterKey"): item.get("ParameterValue") for item in items} == expected


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--approved-change-set")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--reconcile", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None or not isinstance(args.approved_change_set, str):
        return report("blocked", "persistence-deployment-arguments-invalid")
    module = controls()
    receipt = module.validate_receipt(args.receipt)
    if receipt is None:
        return report("blocked", "package-custody-receipt-invalid")
    expected = f"kanbien-core-platform-persistence-create-{receipt['image_digest'][7:19]}"
    if args.approved_change_set != expected:
        return report("blocked", "approved-change-set-does-not-match-qualified-digest")
    if args.reconcile:
        return reconcile(module, expected, receipt)
    if not module.declaration_covered():
        return report("blocked", "persistence-declaration-coverage-gap")
    # Re-inspect the live prerequisites immediately before the only stack mutation.
    outputs, code = module.foundation_outputs()
    if outputs is None:
        return report("blocked", code)
    infrastructure, code = module.infrastructure_parameters(outputs)
    if infrastructure is None:
        return report("blocked", "persistence-private-startup-connectivity-not-proven")
    if not module.candidate_image(receipt)[0] or not module.live_budget()[0]:
        return report("blocked", "persistence-candidate-preconditions-not-proven")
    owner = operations()
    parameters = module.candidate_parameters(outputs, infrastructure, receipt)
    def precondition(reservation):
        ok, change, code = module.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", expected)
        if not ok: raise owner.OperationFailure("blocked", code)
        ok, stack, code = module.aws("cloudformation", "describe-stacks", "--stack-name", STACK)
        try: stack_status = stack.get("Stacks", [{}])[0].get("StackStatus") if ok and isinstance(stack, dict) else None
        except (AttributeError, TypeError, KeyError, IndexError): raise owner.OperationFailure("uncertain", "persistence-stack-observation-uncertain") from None
        if not ok and code != "aws-resource-missing": raise owner.OperationFailure("blocked", code)
        try: reviewed = reviewable(change, stack_status, expected, receipt["image_digest"], receipt["source_revision"])
        except (AttributeError, TypeError): raise owner.OperationFailure("uncertain", "persistence-change-set-observation-invalid") from None
        if not reviewed: raise owner.OperationFailure("blocked", "persistence-change-set-not-reviewable")
        try: matching = parameters_match(change, parameters)
        except TypeError: raise owner.OperationFailure("uncertain", "persistence-parameter-observation-invalid") from None
        if not matching: raise owner.OperationFailure("blocked", "persistence-change-set-live-parameters-mismatch")
        if change.get("ExecutionStatus") != "AVAILABLE": raise owner.Reported(reconcile(module, expected, receipt, reservation=reservation))
    def submit(service, operation, **arguments):
        ok, _, code = module.aws(service, operation, "--stack-name", STACK, "--change-set-name", expected, "--client-request-token", arguments["ClientRequestToken"])
        if not ok: raise owner.Reported(report("uncertain", code, facts={"change_set": expected}))
    try:
        return owner.CHANGE_SETS.execute(submit, owner.store(ROOT), phase="execute", request=owner.intent(expected, receipt, parameters, TEMPLATE),
            arguments={}, precondition=precondition, observe=lambda reservation: reconcile(module, expected, receipt, reservation=reservation), passthrough=(owner.Reported,))
    except owner.Reported as result: return result.status
    except owner.OperationFailure as failure: return report(failure.verdict, failure.code)
    except owner.CHANGE_SETS.ChangeSetFailure:
        return report("uncertain", "persistence-change-set-submission-uncertain", facts={"change_set": expected})


def reconcile(module, expected: str, receipt: dict, *, reservation=None) -> int:
    """Observe the approved operation; this path contains no provider mutation."""
    facts = {"change_set": expected, "candidate_image_digest": receipt["image_digest"], "candidate_source_revision": receipt["source_revision"]}
    ok, change, code = module.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", expected)
    if not ok or not isinstance(change, dict):
        return report("uncertain", code if not ok else "persistence-change-set-observation-invalid", facts=facts)
    try: reviewed = reviewable(change, "REVIEW_IN_PROGRESS", expected, receipt["image_digest"], receipt["source_revision"])
    except (AttributeError, TypeError): return report("uncertain", "persistence-change-set-observation-invalid", facts=facts)
    if not reviewed:
        return report("blocked", "persistence-change-set-reconciliation-identity-invalid", facts=facts)
    ok, observed, code = module.aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks = observed.get("Stacks") if ok and isinstance(observed, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
        return report("uncertain", "persistence-stack-observation-uncertain", facts=facts)
    stack = stacks[0]
    status = stack.get("StackStatus")
    try: pending = status in {"REVIEW_IN_PROGRESS", "CREATE_IN_PROGRESS", "ROLLBACK_IN_PROGRESS"}
    except TypeError: return report("uncertain", "persistence-stack-status-unobservable", facts=facts)
    if pending:
        return report("pending", "persistence-stack-operation-pending", facts=facts)
    if status in {"CREATE_FAILED", "ROLLBACK_FAILED", "ROLLBACK_COMPLETE", "DELETE_COMPLETE"}:
        return report("failed", "persistence-stack-creation-failed", facts=facts)
    try: params = {item.get("ParameterKey"): item.get("ParameterValue") for item in stack.get("Parameters", []) if isinstance(item, dict)}
    except (AttributeError, TypeError): return report("uncertain", "persistence-stack-parameters-unobservable", facts=facts)
    if status != "CREATE_COMPLETE" or change.get("ExecutionStatus") != "EXECUTE_COMPLETE" or any(params.get(key) != value for key, value in (("ImageDigest", receipt["image_digest"]), ("SupportImageDigest", receipt["image_digest"]), ("RestoreVerifierImageDigest", receipt["image_digest"]), ("SourceRevision", receipt["source_revision"]))):
        return report("uncertain", "persistence-stack-completion-identity-unproven", facts=facts)
    if reservation is not None:
        stack_id = stack.get("StackId")
        if not isinstance(stack_id, str) or not stack_id.startswith("arn:aws:cloudformation:eu-west-1:337159794548:stack/" + STACK + "/"):
            return report("uncertain", "persistence-stack-reservation-identity-unproven", facts=facts)
        ok, events, code = module.aws("cloudformation", "describe-stack-events", "--stack-name", stack_id)
        rows = events.get("StackEvents") if ok and isinstance(events, dict) else None
        if not isinstance(rows, list) or not any(isinstance(row, dict) and row.get("PhysicalResourceId") == stack_id and row.get("ClientRequestToken") == reservation["operation_id"] for row in rows):
            return report("uncertain", "persistence-stack-execution-lineage-unproven", facts=facts)
    return report("deployed-awaiting-migration", "persistence-create-change-set-executed", facts=facts)


if __name__ == "__main__":
    raise SystemExit(main())
