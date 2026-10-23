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
    result = subprocess.run(["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json"], capture_output=True, text=True)
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
    services = data.get("services") if ok and isinstance(data, dict) else None
    if not isinstance(services, list) or not services:
        return True, "ok"
    service = services[0]
    if not isinstance(service, dict):
        return False, "persistence-failed-candidate-service-state-unknown"
    active = any(service.get(field) not in (0, None) for field in ("desiredCount", "runningCount", "pendingCount"))
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


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--approved-failed-stack")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.approved_failed_stack != STACK:
        return report("blocked", "persistence-failed-candidate-retirement-arguments-invalid")
    for check in (failed_candidate_database, no_active_service, protected_target_database):
        valid, code = check()
        if not valid:
            return report("blocked", code)
    ok, _, code = aws("rds", "modify-db-instance", "--db-instance-identifier", DATABASE, "--no-deletion-protection", "--apply-immediately")
    if not ok:
        return report("blocked", code)
    waited = subprocess.run(["aws", "rds", "wait", "db-instance-available", "--db-instance-identifier", DATABASE, "--profile", PROFILE, "--region", REGION], capture_output=True, text=True)
    if waited.returncode:
        return report("blocked", "persistence-failed-candidate-database-protection-change-unconfirmed")
    valid, code = protected_target_database_after_unlock()
    if not valid:
        return report("blocked", code)
    ok, _, code = aws("cloudformation", "delete-stack", "--stack-name", STACK)
    if not ok:
        return report("blocked", code)
    deleted = subprocess.run(["aws", "cloudformation", "wait", "stack-delete-complete", "--stack-name", STACK, "--profile", PROFILE, "--region", REGION], capture_output=True, text=True)
    if deleted.returncode:
        return report("blocked", "persistence-failed-candidate-stack-delete-unconfirmed")
    return report("retired", "persistence-failed-candidate-retired-with-final-snapshot-retained", facts={"stack": STACK, "database": DATABASE})


def protected_target_database_after_unlock() -> tuple[bool, str]:
    ok, data, code = aws("rds", "describe-db-instances", "--db-instance-identifier", DATABASE)
    instances = data.get("DBInstances") if ok and isinstance(data, dict) else None
    if not isinstance(instances, list) or len(instances) != 1 or not isinstance(instances[0], dict):
        return False, code if not ok else "persistence-failed-candidate-database-unavailable"
    instance = instances[0]
    if instance.get("DeletionProtection") is not False or instance.get("PubliclyAccessible") is not False:
        return False, "persistence-failed-candidate-database-unlock-unconfirmed"
    return True, "ok"


if __name__ == "__main__":
    raise SystemExit(main())
