#!/usr/bin/env python3
"""Verify safe live boundary facts for the Kanbien staging PostgreSQL reference."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-postgresql-live-boundary
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: persistence.operations
#   kind: script
#   purpose: Fail closed unless the private PostgreSQL reference keeps its reviewed boundary.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any


PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
SCHEMA = "deploy/postgresql-relational-live-boundary-result/v1"
DATABASE = "kanbien-staging-platform-relational"


class BoundaryError(Exception):
    """Safe failure: provider data must never become command output."""


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the safe staging PostgreSQL boundary.")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--target-profile", default=PROFILE)
    parser.add_argument("--aws-cli", default="aws")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    result = parser.parse_args()
    if not 1 <= result.timeout_seconds <= 30:
        parser.error("--timeout-seconds must be between 1 and 30")
    return result


def fail(code: str) -> None:
    raise BoundaryError(code)


def mapping(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(code)
    return value


def string(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value:
        fail(code)
    return value


def load_policy(path: Path) -> dict[str, str]:
    try:
        import yaml
        source = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as error:
        raise BoundaryError("target-profile-unreadable") from error
    cloud = mapping(mapping(source, "target-profile-invalid").get("cloud"), "cloud-policy-missing")
    deployment = mapping(source.get("deployment"), "deployment-policy-missing")
    foundation = mapping(deployment.get("cloudformation"), "foundation-policy-missing")
    persistence = mapping(source.get("persistence"), "persistence-policy-missing")
    reference = mapping(persistence.get("relational_reference"), "relational-policy-missing")
    connection = mapping(reference.get("connection_security"), "connection-policy-missing")
    if connection.get("public_accessibility") != "prohibited":
        fail("public-access-policy-not-reviewed")
    if connection.get("database_egress") != "explicit-loopback-only-127-0-0-1-32-no-external-ipv4-ipv6-prefix-list-or-security-group-destination":
        fail("database-egress-policy-not-reviewed")
    policy = {
        "account": string(cloud.get("account_id"), "account-id-missing"),
        "region": string(cloud.get("region"), "region-missing"),
        "profile": string(cloud.get("profile"), "aws-profile-missing"),
        "foundation": string(foundation.get("foundation_stack"), "foundation-stack-missing"),
    }
    if policy["account"] != "337159794548" or policy["region"] != "eu-west-1":
        fail("target-account-or-region-not-reviewed")
    return policy


def aws(args: argparse.Namespace, policy: dict[str, str], command: list[str], code: str) -> Any:
    try:
        result = subprocess.run(
            [args.aws_cli, *command, "--profile", policy["profile"], "--region", policy["region"], "--output", "json"],
            check=True, capture_output=True, text=True, timeout=args.timeout_seconds,
        )
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        raise BoundaryError(code) from error


def require(condition: bool, code: str) -> None:
    if not condition:
        fail(code)


def resource_id(args: argparse.Namespace, policy: dict[str, str], logical: str) -> str:
    result = aws(args, policy, ["cloudformation", "describe-stack-resource", "--stack-name", policy["foundation"], "--logical-resource-id", logical, "--query", "StackResourceDetail.PhysicalResourceId"], "foundation-resource-lookup")
    return string(result, "foundation-resource-lookup")


def verify_database(args: argparse.Namespace, policy: dict[str, str]) -> str:
    result = aws(args, policy, [
        "rds", "describe-db-instances", "--db-instance-identifier", DATABASE,
        "--query", "DBInstances[0].{status:DBInstanceStatus,public:PubliclyAccessible,encrypted:StorageEncrypted,multi:MultiAZ,backup:BackupRetentionPeriod,deletion:DeletionProtection,engine:Engine,version:EngineVersion,class:DBInstanceClass,storage:AllocatedStorage,max:MaxAllocatedStorage,type:StorageType,parameter:DBParameterGroups[0].DBParameterGroupName,parameterStatus:DBParameterGroups[0].ParameterApplyStatus}",
    ], "relational-database-unavailable")
    expected = {"status": "available", "public": False, "encrypted": True, "multi": False, "backup": 7, "deletion": True, "engine": "postgres", "version": "17.11", "class": "db.t4g.micro", "storage": 20, "max": 30, "type": "gp3", "parameterStatus": "in-sync"}
    require(isinstance(result, dict) and all(result.get(key) == value for key, value in expected.items()), "relational-database-boundary")
    return string(result.get("parameter"), "relational-parameter-group")


def verify_network(args: argparse.Namespace, policy: dict[str, str]) -> None:
    database_group = resource_id(args, policy, "RelationalDatabaseSecurityGroup")
    workload_groups = {resource_id(args, policy, name) for name in ("ServiceSecurityGroup", "WorkerSecurityGroup", "RelaySecurityGroup")}
    group = aws(args, policy, ["ec2", "describe-security-groups", "--group-ids", database_group, "--query", "SecurityGroups[0].{ingress:IpPermissions,egress:IpPermissionsEgress}"], "relational-security-group-unavailable")
    require(isinstance(group, dict), "relational-security-group")
    ingress, egress = group.get("ingress"), group.get("egress")
    require(isinstance(ingress, list) and len(ingress) == 1, "relational-database-ingress")
    rule = ingress[0]
    sources = {pair.get("GroupId") for pair in rule.get("UserIdGroupPairs", []) if isinstance(pair, dict)} if isinstance(rule, dict) else set()
    require(isinstance(rule, dict) and rule.get("IpProtocol") == "tcp" and rule.get("FromPort") == 5432 and rule.get("ToPort") == 5432 and sources == workload_groups and not rule.get("IpRanges") and not rule.get("Ipv6Ranges") and not rule.get("PrefixListIds"), "relational-database-ingress")
    require(isinstance(egress, list) and len(egress) == 1, "relational-database-egress")
    outbound = egress[0]
    ranges = outbound.get("IpRanges", []) if isinstance(outbound, dict) else []
    require(isinstance(outbound, dict) and outbound.get("IpProtocol") == "-1" and isinstance(ranges, list) and len(ranges) == 1 and ranges[0].get("CidrIp") == "127.0.0.1/32" and not outbound.get("Ipv6Ranges") and not outbound.get("PrefixListIds") and not outbound.get("UserIdGroupPairs"), "relational-database-egress")
    for workload in workload_groups:
        outbound_rules = aws(args, policy, ["ec2", "describe-security-groups", "--group-ids", workload, "--query", "SecurityGroups[0].IpPermissionsEgress"], "relational-workload-egress-unavailable")
        found = any(isinstance(item, dict) and item.get("IpProtocol") == "tcp" and item.get("FromPort") == 5432 and item.get("ToPort") == 5432 and {pair.get("GroupId") for pair in item.get("UserIdGroupPairs", []) if isinstance(pair, dict)} == {database_group} and not item.get("IpRanges") and not item.get("Ipv6Ranges") and not item.get("PrefixListIds") for item in outbound_rules if isinstance(outbound_rules, list))
        require(found, "relational-workload-egress")


def verify_operations(args: argparse.Namespace, policy: dict[str, str]) -> None:
    alarms = aws(args, policy, ["cloudwatch", "describe-alarms", "--alarm-name-prefix", "kanbien-staging-platform-relational-", "--query", "MetricAlarms[].{metric:MetricName,threshold:Threshold,operator:ComparisonOperator,period:Period,evaluations:EvaluationPeriods,datapoints:DatapointsToAlarm,missing:TreatMissingData}"], "relational-alarms-unavailable")
    expected = {("CPUUtilization", 80, "GreaterThanOrEqualToThreshold", 300, 3, 3, "breaching"), ("FreeStorageSpace", 3221225472, "LessThanOrEqualToThreshold", 300, 3, 3, "breaching"), ("DatabaseConnections", 60, "GreaterThanOrEqualToThreshold", 300, 3, 3, "breaching")}
    actual = {(item.get("metric"), item.get("threshold"), item.get("operator"), item.get("period"), item.get("evaluations"), item.get("datapoints"), item.get("missing")) for item in alarms if isinstance(item, dict)} if isinstance(alarms, list) else set()
    require(actual == expected and len(alarms) == 3, "relational-alarms")
    subscription = aws(args, policy, ["rds", "describe-event-subscriptions", "--subscription-name", "kanbien-staging-platform-relational-events", "--query", "EventSubscriptionsList[0].{status:Status,enabled:Enabled,sourceType:SourceType,sourceCount:length(SourceIdsList),categoryCount:length(EventCategoriesList)}"], "relational-events-unavailable")
    require(subscription == {"status": "active", "enabled": True, "sourceType": "db-instance", "sourceCount": 1, "categoryCount": 6}, "relational-events")


def main() -> int:
    args, checks = arguments(), []
    try:
        policy = load_policy(Path(args.target_profile))
        checks.append({"id": "source-policy", "verdict": "passed"})
        if not args.validate:
            account = aws(args, policy, ["sts", "get-caller-identity", "--query", "Account"], "aws-account-unavailable")
            require(account == policy["account"], "aws-account-mismatch")
            checks.append({"id": "aws-account", "verdict": "passed"})
            status = aws(args, policy, ["cloudformation", "describe-stacks", "--stack-name", policy["foundation"], "--query", "Stacks[0].StackStatus"], "foundation-stack-unavailable")
            require(status == "UPDATE_COMPLETE", "foundation-stack-not-ready")
            checks.append({"id": "foundation-stack", "verdict": "passed"})
            parameter_group = verify_database(args, policy)
            checks.append({"id": "relational-database", "verdict": "passed"})
            tls = aws(args, policy, ["rds", "describe-db-parameters", "--db-parameter-group-name", parameter_group, "--query", "Parameters[?ParameterName==`rds.force_ssl`].ParameterValue | [0]"], "relational-tls-unavailable")
            require(tls == "1", "relational-tls-not-enforced")
            checks.append({"id": "relational-tls", "verdict": "passed"})
            verify_network(args, policy)
            checks.append({"id": "relational-network", "verdict": "passed"})
            verify_operations(args, policy)
            checks.append({"id": "relational-operations", "verdict": "passed"})
        print(json.dumps({"schema": SCHEMA, "target": "kanbien/staging", "verdict": "passed", "checks": checks}, sort_keys=True))
        return 0
    except BoundaryError as error:
        checks.append({"id": str(error), "verdict": "failed"})
        print(json.dumps({"schema": SCHEMA, "target": "kanbien/staging", "verdict": "failed", "checks": checks}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
