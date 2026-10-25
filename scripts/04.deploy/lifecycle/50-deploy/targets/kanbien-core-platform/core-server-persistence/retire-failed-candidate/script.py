#!/usr/bin/env python3
"""Retire only a failed, never-accepted persistence candidate with a protected RDS instance."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROFILE, REGION, CLUSTER = "kanbien-dev", "eu-west-1", "kanbien-core-platform"
STACK = "kanbien-core-platform-core-server-persistence"
DATABASE = "kanbien-core-platform-persistence"
SERVICE = "kanbien-core-platform-core-server-persistence"


def aws(*parts: str):
    try:
        result = subprocess.run(["aws", *parts, "--cli-connect-timeout", "5", "--cli-read-timeout", "20", "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False, None, "aws-command-timeout"
    if result.returncode:
        lowered = result.stderr.lower()
        if "does not exist" in lowered or "not found" in lowered:
            return False, None, "aws-resource-missing"
        if "accessdenied" in lowered or "not authorized" in lowered:
            return False, None, "aws-access-denied"
        return False, None, "aws-command-failed"
    try:
        return True, {} if not result.stdout.strip() else json.loads(result.stdout), "ok"
    except json.JSONDecodeError:
        return False, None, "aws-response-invalid"


def report(verdict: str, *codes: str, facts: dict[str, object] | None = None) -> int:
    value: dict[str, object] = {"schema": "deploy/persistence-failed-candidate-retirement-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "retired" else 1


def failed_candidate_database() -> tuple[bool, str]:
    ok, stack, code = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks = stack.get("Stacks") if ok and isinstance(stack, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict) or stacks[0].get("StackStatus") != "ROLLBACK_FAILED":
        return False, code if not ok else "persistence-failed-candidate-stack-not-retirable"
    ok, resources, code = aws("cloudformation", "describe-stack-resources", "--stack-name", STACK)
    items = resources.get("StackResources") if ok and isinstance(resources, dict) else None
    database = next((item for item in items or [] if isinstance(item, dict) and item.get("LogicalResourceId") == "PersistenceDatabase"), None)
    if not isinstance(database, dict) or database.get("ResourceStatus") != "DELETE_FAILED" or database.get("PhysicalResourceId") != DATABASE:
        return False, code if not ok else "persistence-failed-candidate-database-not-isolated"
    return True, "ok"


def no_active_service() -> tuple[bool, str]:
    ok, data, code = aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", SERVICE)
    if not ok and code == "aws-resource-missing":
        return True, "ok"
    if not ok:
        return False, code
    services = data.get("services") if isinstance(data, dict) else None
    if not isinstance(services, list):
        return False, "persistence-failed-candidate-service-state-unknown"
    if not services:
        failures = data.get("failures", [])
        return (True, "ok") if isinstance(failures, list) and bool(failures) and all(isinstance(item, dict) and item.get("reason") == "MISSING" for item in failures) else (False, "persistence-failed-candidate-service-state-unknown")
    if len(services) != 1:
        return False, "persistence-failed-candidate-service-state-unknown"
    service = services[0]
    expected_arn = f"arn:aws:ecs:{REGION}:337159794548:service/{CLUSTER}/{SERVICE}"
    if not isinstance(service, dict) or service.get("serviceName") != SERVICE or service.get("serviceArn") != expected_arn:
        return False, "persistence-failed-candidate-service-state-unknown"
    counts = [service.get(field) for field in ("desiredCount", "runningCount", "pendingCount")]
    if any(type(value) is not int or value < 0 for value in counts):
        return False, "persistence-failed-candidate-service-state-unknown"
    active = any(value != 0 for value in counts)
    return (False, "persistence-failed-candidate-service-still-active") if active else (True, "ok")


def protected_target_database() -> tuple[bool, str]:
    ok, data, code = aws("rds", "describe-db-instances", "--db-instance-identifier", DATABASE)
    instances = data.get("DBInstances") if ok and isinstance(data, dict) else None
    if not isinstance(instances, list) or len(instances) != 1 or not isinstance(instances[0], dict):
        return False, code if not ok else "persistence-failed-candidate-database-unavailable"
    instance = instances[0]
    if instance.get("DBInstanceIdentifier") != DATABASE or instance.get("PubliclyAccessible") is not False or instance.get("DeletionProtection") is not True:
        return False, "persistence-failed-candidate-database-safety-state-invalid"
    arn = instance.get("DBInstanceArn")
    if not isinstance(arn, str):
        return False, "persistence-failed-candidate-database-identity-invalid"
    ok, tags, code = aws("rds", "list-tags-for-resource", "--resource-name", arn)
    values = tags.get("TagList") if ok and isinstance(tags, dict) else None
    if not any(isinstance(tag, dict) and tag.get("Key") == "Target" and tag.get("Value") == "kanbien-core-platform" for tag in values or []):
        return False, code if not ok else "persistence-failed-candidate-database-target-mismatch"
    return True, "ok"


def observed_retirement(stack_id: str, continue_delete: bool = False) -> int:
    facts = {"retirement_stack_id": stack_id}
    prefix = f"arn:aws:cloudformation:{REGION}:337159794548:stack/{STACK}/"
    if not stack_id.startswith(prefix) or not stack_id[len(prefix):]:
        return report("blocked", "persistence-retirement-stack-identity-invalid")
    ok, data, code = aws("cloudformation", "describe-stacks", "--stack-name", stack_id)
    stacks = data.get("Stacks") if ok and isinstance(data, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
        return report("uncertain", "persistence-retirement-stack-observation-uncertain", facts=facts)
    stack = stacks[0]
    if stack.get("StackId") != stack_id or stack.get("StackName") != STACK:
        return report("blocked", "persistence-retirement-stack-identity-invalid", facts=facts)
    status = stack.get("StackStatus")
    if status == "DELETE_COMPLETE":
        return report("pending", "persistence-failed-candidate-deletion-confirmed-recovery-proof-required", facts={**facts, "stack_deletion": "confirmed", "final_snapshot_proof": "separately-required"})
    if status == "DELETE_IN_PROGRESS":
        return report("pending", "persistence-failed-candidate-deletion-pending", facts=facts)
    if status == "DELETE_FAILED":
        return report("failed", "persistence-failed-candidate-deletion-failed", facts=facts)
    if status != "ROLLBACK_FAILED":
        return report("blocked", "persistence-failed-candidate-stack-not-retirable", facts=facts)
    if not continue_delete:
        return report("pending", "persistence-retirement-unlock-reconciliation-required", facts=facts)
    # Continuation requires the same retained stack identity and repeats every
    # ownership/quiescence check before advancing beyond the prior mutation.
    for check in (failed_candidate_database, no_active_service, protected_target_database_after_unlock):
        valid, code = check()
        if not valid:
            return report("uncertain" if code.startswith("aws-") else "blocked", code, facts=facts)
    ok, _, code = aws("cloudformation", "delete-stack", "--stack-name", stack_id)
    return report("pending" if ok else "uncertain", "persistence-failed-candidate-deletion-submitted" if ok else code, facts=facts)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--approved-failed-stack")
    parser.add_argument("--reconcile-stack-id")
    parser.add_argument("--continue-stack-id")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.approved_failed_stack != STACK or (args.reconcile_stack_id and args.continue_stack_id):
        return report("blocked", "persistence-failed-candidate-retirement-arguments-invalid")
    if args.reconcile_stack_id or args.continue_stack_id:
        return observed_retirement(args.reconcile_stack_id or args.continue_stack_id, bool(args.continue_stack_id))
    for check in (failed_candidate_database, no_active_service, protected_target_database):
        valid, code = check()
        if not valid:
            return report("uncertain" if code.startswith("aws-") else "blocked", code)
    ok, data, code = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks = data.get("Stacks") if ok and isinstance(data, dict) else None
    stack_id = stacks[0].get("StackId") if isinstance(stacks, list) and len(stacks) == 1 and isinstance(stacks[0], dict) else None
    prefix = f"arn:aws:cloudformation:{REGION}:337159794548:stack/{STACK}/"
    if not isinstance(stack_id, str) or not stack_id.startswith(prefix):
        return report("uncertain", "persistence-retirement-stack-identity-unavailable")
    facts = {"retirement_stack_id": stack_id}
    print(json.dumps({"verdict": "pending", "facts": facts}), file=sys.stderr, flush=True)
    ok, _, code = aws("rds", "modify-db-instance", "--db-instance-identifier", DATABASE, "--no-deletion-protection", "--apply-immediately")
    return report("pending" if ok else "uncertain", "persistence-retirement-unlock-submitted" if ok else code, facts=facts)


def protected_target_database_after_unlock() -> tuple[bool, str]:
    ok, data, code = aws("rds", "describe-db-instances", "--db-instance-identifier", DATABASE)
    instances = data.get("DBInstances") if ok and isinstance(data, dict) else None
    if not isinstance(instances, list) or len(instances) != 1 or not isinstance(instances[0], dict):
        return False, code if not ok else "persistence-failed-candidate-database-unavailable"
    instance = instances[0]
    if instance.get("DBInstanceIdentifier") != DATABASE or instance.get("DeletionProtection") is not False or instance.get("PubliclyAccessible") is not False or instance.get("DBInstanceStatus") != "available":
        return False, "persistence-failed-candidate-database-unlock-unconfirmed"
    arn = instance.get("DBInstanceArn")
    if not isinstance(arn, str):
        return False, "persistence-failed-candidate-database-identity-invalid"
    ok, tags, code = aws("rds", "list-tags-for-resource", "--resource-name", arn)
    values = tags.get("TagList") if ok and isinstance(tags, dict) else None
    if not any(isinstance(tag, dict) and tag.get("Key") == "Target" and tag.get("Value") == "kanbien-core-platform" for tag in values or []):
        return False, code if not ok else "persistence-failed-candidate-database-target-mismatch"
    return True, "ok"


if __name__ == "__main__":
    raise SystemExit(main())
