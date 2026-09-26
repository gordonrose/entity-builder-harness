#!/usr/bin/env python3
"""Run the one fixed, redacted Kanbien staging relational reference proof."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


PROFILE_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
ACCOUNT = "337159794548"
REGION = "eu-west-1"
SERVER_SERVICE = "kanbien-staging-platform-shell"
WORKER_SERVICE = "kanbien-staging-platform-shell-worker"


class RelationalSmokeError(Exception):
    """Represent a safe outcome without exposing AWS data or task output."""


def arguments() -> argparse.Namespace:
    """Accept only an offline check or the one approved fixed-stage sequence."""

    parser = argparse.ArgumentParser(description="Validate or run one Kanbien staging relational smoke proof.")
    parser.add_argument("--validate", action="store_true", help="Validate the committed policy without AWS calls.")
    parser.add_argument("--execute", action="store_true", help="Run the fixed bootstrap-to-restore proof.")
    parser.add_argument("--approve-relational-stage6", action="store_true", help="Acknowledge the one bounded relational proof and recovery cleanup.")
    result = parser.parse_args()
    if result.validate == result.execute:
        parser.error("choose exactly one of --validate or --execute")
    if result.validate and result.approve_relational_stage6:
        parser.error("the Stage 6 approval guard is valid only with --execute")
    if result.execute and not result.approve_relational_stage6:
        parser.error("the fixed relational proof requires --approve-relational-stage6")
    return result


def mapping(value: Any, label: str) -> dict[str, Any]:
    """Reject an absent policy section rather than choosing an operation default."""

    if not isinstance(value, dict):
        raise RelationalSmokeError(f"missing committed policy section: {label}")
    return value


def text(value: Any, label: str) -> str:
    """Require a finite, non-empty policy string."""

    if not isinstance(value, str) or not value:
        raise RelationalSmokeError(f"invalid committed policy value: {label}")
    return value


def load_policy() -> dict[str, Any]:
    """Read the non-selectable committed staging target and resolve its exact control."""

    try:
        import yaml
        source = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception as exception:
        raise RelationalSmokeError("the committed relational target policy is unavailable") from exception
    root = mapping(source, "target-profile")
    cloud = mapping(root.get("cloud"), "cloud")
    if cloud.get("account_id") != ACCOUNT or cloud.get("region") != REGION:
        raise RelationalSmokeError("the relational proof target is not the reviewed staging account and region")
    reference = mapping(mapping(root.get("persistence"), "persistence").get("relational_reference"), "relational_reference")
    stage = mapping(reference.get("stage_6_relational_smoke_composition"), "stage_6_relational_smoke_composition")
    if reference.get("status") != "stage-5-live-boundary-proven-stage-6-relational-smoke-composition-source-ready" or stage.get("status") != "source-defined-change-set-pending":
        raise RelationalSmokeError("the relational lifecycle does not permit the Stage 6 proof")
    control = mapping(stage.get("control"), "stage_6_relational_smoke_composition.control")
    task_families = mapping(control.get("task_families"), "control.task_families")
    task_containers = mapping(control.get("task_containers"), "control.task_containers")
    started_by = mapping(control.get("started_by"), "control.started_by")
    expected_families = {
        "bootstrap": "kanbien-staging-platform-relational-bootstrap",
        "migration": "kanbien-staging-platform-relational-migration",
        "relay": "kanbien-staging-platform-relational-relay",
        "worker": "kanbien-staging-platform-relational-worker",
        "restore_verification": "kanbien-staging-platform-relational-restore-verify",
    }
    expected_containers = {
        "bootstrap": "relational-bootstrap",
        "migration": "relational-migration",
        "relay": "relational-relay",
        "worker": "relational-worker",
        "restore_verification": "relational-restore-verify",
    }
    expected_labels = {
        "bootstrap": "kanbien-postgresql-stage6-bootstrap-20260926",
        "migration": "kanbien-postgresql-stage6-migration-20260926",
        "relay": "kanbien-postgresql-stage6-relay-20260926",
        "worker": "kanbien-postgresql-stage6-worker-20260926",
        "restore_verification": "kanbien-postgresql-stage6-restore-verify-20260926",
    }
    required = {
        "command": "npm-run-platform-shell-postgresql-relational-smoke",
        "execution_guard": "execute-and-approve-relational-stage6",
        "cluster": "arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-staging",
        "foundation_stack": "kanbien-staging-platform-shell-foundation",
        "service_stack": "kanbien-staging-platform-shell-service",
        "source_database_identifier": "kanbien-staging-platform-relational",
        "restore_database_identifier": "kanbien-staging-platform-relational-restore-proof-20260926",
        "source_network": "existing-dormant-worker-service-awsvpc-configuration-only",
        "restore_cleanup": "delete-disposable-recovery-instance-without-final-snapshot-only-after-restore-verification",
        "output_policy": "safe-stage-status-and-aggregate-counts-only-no-identifiers-endpoints-records-secrets-headers-bodies-messages-or-provider-payloads",
    }
    if any(control.get(key) != value for key, value in required.items()) or task_families != expected_families or task_containers != expected_containers or started_by != expected_labels:
        raise RelationalSmokeError("the relational proof control differs from the reviewed fixed shape")
    if control.get("task_wait_seconds") != 900 or control.get("restore_wait_seconds") != 1800 or control.get("required_queue_counts") != {"before": 0, "after_relay": 1, "terminal": 0}:
        raise RelationalSmokeError("the relational proof duration or queue bounds differ from the reviewed values")
    return {
        "profile": text(cloud.get("profile"), "cloud.profile"),
        "cluster": required["cluster"],
        "foundation_stack": required["foundation_stack"],
        "service_stack": required["service_stack"],
        "source_database": required["source_database_identifier"],
        "restore_database": required["restore_database_identifier"],
        "families": expected_families,
        "containers": expected_containers,
        "labels": expected_labels,
        "task_wait_seconds": 900,
        "restore_wait_seconds": 1800,
    }


def aws(arguments: list[str], policy: dict[str, Any], allow_not_found: bool = False) -> dict[str, Any] | None:
    """Call AWS while keeping raw provider responses solely in process memory."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    result = subprocess.run(["aws", *arguments, "--profile", policy["profile"], "--region", REGION, "--output", "json"], capture_output=True, encoding="utf-8", check=False, env=environment)
    if result.returncode != 0:
        if allow_not_found and "DBInstanceNotFound" in result.stderr:
            return None
        raise RelationalSmokeError("a fixed approved relational-stage AWS operation did not complete")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exception:
        raise RelationalSmokeError("a relational-stage AWS operation returned an unexpected result") from exception
    if not isinstance(payload, dict):
        raise RelationalSmokeError("a relational-stage AWS operation returned an invalid result")
    return payload


def verify_account(policy: dict[str, Any]) -> None:
    """Refuse all task and recovery work outside the one reviewed account."""

    if aws(["sts", "get-caller-identity"], policy).get("Account") != ACCOUNT:
        raise RelationalSmokeError("the configured identity is outside the reviewed staging account")


def stack_outputs(policy: dict[str, Any]) -> dict[str, str]:
    """Read Foundation outputs in memory and require only the fixed proof interface."""

    response = aws(["cloudformation", "describe-stacks", "--stack-name", policy["foundation_stack"]], policy)
    stacks = response.get("Stacks")
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict) or stacks[0].get("StackStatus") != "UPDATE_COMPLETE":
        raise RelationalSmokeError("the relational Foundation stack is not update-complete")
    values = {item.get("OutputKey"): item.get("OutputValue") for item in stacks[0].get("Outputs", []) if isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str)}
    required = ("RelationalSmokeQueueUrl", "RelationalSmokeDeadLetterQueueUrl")
    if any(not isinstance(values.get(name), str) or not values[name] for name in required):
        raise RelationalSmokeError("the relational Foundation output interface is incomplete")
    return {name: values[name] for name in required}


def update_complete(stack: str, policy: dict[str, Any]) -> None:
    """Require the service composition stack to be stable before it supplies tasks."""

    response = aws(["cloudformation", "describe-stacks", "--stack-name", stack], policy)
    stacks = response.get("Stacks")
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict) or stacks[0].get("StackStatus") != "UPDATE_COMPLETE":
        raise RelationalSmokeError("the relational service stack is not update-complete")


def queue_total(url: str, policy: dict[str, Any]) -> int:
    """Read only aggregate visible and in-flight counts; never receive a message."""

    response = aws(["sqs", "get-queue-attributes", "--queue-url", url, "--attribute-names", "ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible"], policy)
    attributes = response.get("Attributes")
    if not isinstance(attributes, dict):
        raise RelationalSmokeError("the isolated relational queue returned no aggregate counts")
    try:
        return int(attributes.get("ApproximateNumberOfMessages", "-1")) + int(attributes.get("ApproximateNumberOfMessagesNotVisible", "-1"))
    except (TypeError, ValueError) as exception:
        raise RelationalSmokeError("the isolated relational queue returned invalid aggregate counts") from exception


def service_counts(name: str, policy: dict[str, Any]) -> tuple[int, int]:
    """Require the public server and dormant worker to retain their safe counts."""

    response = aws(["ecs", "describe-services", "--cluster", policy["cluster"], "--services", name], policy)
    services = response.get("services")
    if not isinstance(services, list) or len(services) != 1 or not isinstance(services[0], dict):
        raise RelationalSmokeError("a reviewed service could not be inspected uniquely")
    try:
        return int(services[0].get("desiredCount")), int(services[0].get("runningCount"))
    except (TypeError, ValueError) as exception:
        raise RelationalSmokeError("a reviewed service returned invalid aggregate counts") from exception


def worker_network(policy: dict[str, Any]) -> str:
    """Reuse exactly the dormant worker's reviewed awsvpc topology for one-shot tasks."""

    response = aws(["ecs", "describe-services", "--cluster", policy["cluster"], "--services", WORKER_SERVICE], policy)
    services = response.get("services")
    if not isinstance(services, list) or len(services) != 1 or not isinstance(services[0], dict):
        raise RelationalSmokeError("the dormant worker service is not available for network derivation")
    awsvpc = services[0].get("networkConfiguration", {}).get("awsvpcConfiguration") if isinstance(services[0].get("networkConfiguration"), dict) else None
    if not isinstance(awsvpc, dict) or awsvpc.get("assignPublicIp") != "ENABLED":
        raise RelationalSmokeError("the dormant worker does not retain the reviewed awsvpc configuration")
    subnets, groups = awsvpc.get("subnets"), awsvpc.get("securityGroups")
    if not isinstance(subnets, list) or len(subnets) < 2 or not isinstance(groups, list) or len(groups) != 1 or any(not isinstance(item, str) or not item for item in [*subnets, *groups]):
        raise RelationalSmokeError("the dormant worker network shape differs from the reviewed boundary")
    return "awsvpcConfiguration={subnets=[" + ",".join(subnets) + "],securityGroups=[" + ",".join(groups) + "],assignPublicIp=ENABLED}"


def assert_task_definition(stage: str, policy: dict[str, Any]) -> None:
    """Ensure a stage can use only its exact target-defined task family/container."""

    response = aws(["ecs", "describe-task-definition", "--task-definition", policy["families"][stage]], policy)
    definition = response.get("taskDefinition")
    containers = definition.get("containerDefinitions") if isinstance(definition, dict) else None
    if not isinstance(definition, dict) or definition.get("family") != policy["families"][stage] or not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or containers[0].get("name") != policy["containers"][stage] or containers[0].get("portMappings"):
        raise RelationalSmokeError("a relational stage task definition differs from the reviewed isolated shape")


def no_prior_label(stage: str, policy: dict[str, Any]) -> None:
    """Make each fixed stage single-use, including after a task failure."""

    response = aws(["ecs", "list-tasks", "--cluster", policy["cluster"], "--started-by", policy["labels"][stage]], policy)
    tasks = response.get("taskArns")
    if not isinstance(tasks, list) or tasks:
        raise RelationalSmokeError("a fixed relational proof stage has already been consumed")


def run_and_wait(stage: str, network: str, policy: dict[str, Any], environment: list[dict[str, str]] | None = None) -> None:
    """Start one labelled Fargate task, wait for it privately, and require exit zero."""

    assert_task_definition(stage, policy)
    no_prior_label(stage, policy)
    command = ["ecs", "run-task", "--cluster", policy["cluster"], "--task-definition", policy["families"][stage], "--launch-type", "FARGATE", "--count", "1", "--started-by", policy["labels"][stage], "--network-configuration", network]
    if environment is not None:
        command.extend(["--overrides", json.dumps({"containerOverrides": [{"name": policy["containers"][stage], "environment": environment}]}, separators=(",", ":"))])
    response = aws(command, policy)
    tasks, failures = response.get("tasks"), response.get("failures")
    if failures not in (None, []) or not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict) or not isinstance(tasks[0].get("taskArn"), str):
        raise RelationalSmokeError("a fixed relational stage task did not start uniquely")
    task_arn = tasks[0]["taskArn"]
    deadline = time.monotonic() + policy["task_wait_seconds"]
    while time.monotonic() < deadline:
        observed = aws(["ecs", "describe-tasks", "--cluster", policy["cluster"], "--tasks", task_arn], policy)
        current = observed.get("tasks")
        if isinstance(current, list) and len(current) == 1 and isinstance(current[0], dict) and current[0].get("lastStatus") == "STOPPED":
            containers = current[0].get("containers")
            container = next((item for item in containers if isinstance(item, dict) and item.get("name") == policy["containers"][stage]), None) if isinstance(containers, list) else None
            if isinstance(container, dict) and container.get("exitCode") == 0:
                return
            raise RelationalSmokeError("a fixed relational stage task did not complete successfully")
        time.sleep(10)
    raise RelationalSmokeError("a fixed relational stage task exceeded its reviewed wait limit")


def source_database(policy: dict[str, Any]) -> dict[str, Any]:
    """Read private source recovery attributes without retaining or printing endpoint data."""

    response = aws(["rds", "describe-db-instances", "--db-instance-identifier", policy["source_database"]], policy)
    instances = response.get("DBInstances")
    if not isinstance(instances, list) or len(instances) != 1 or not isinstance(instances[0], dict):
        raise RelationalSmokeError("the relational source database is not available uniquely")
    instance = instances[0]
    subnet_group = instance.get("DBSubnetGroup", {}).get("DBSubnetGroupName") if isinstance(instance.get("DBSubnetGroup"), dict) else None
    groups = instance.get("VpcSecurityGroups")
    parameter_groups = instance.get("DBParameterGroups")
    if instance.get("DBInstanceStatus") != "available" or instance.get("PubliclyAccessible") is not False or instance.get("StorageEncrypted") is not True or not isinstance(subnet_group, str) or not isinstance(groups, list) or len(groups) != 1 or not isinstance(groups[0], dict) or not isinstance(groups[0].get("VpcSecurityGroupId"), str) or not isinstance(parameter_groups, list) or len(parameter_groups) != 1 or not isinstance(parameter_groups[0], dict) or not isinstance(parameter_groups[0].get("DBParameterGroupName"), str):
        raise RelationalSmokeError("the relational source database recovery boundary differs from the reviewed posture")
    return {"subnet_group": subnet_group, "security_group": groups[0]["VpcSecurityGroupId"], "parameter_group": parameter_groups[0]["DBParameterGroupName"]}


def restore_absent(policy: dict[str, Any]) -> bool:
    """Require the fixed disposable recovery identifier to be unused before restore."""

    return aws(["rds", "describe-db-instances", "--db-instance-identifier", policy["restore_database"]], policy, allow_not_found=True) is None


def restore_and_verify(network: str, policy: dict[str, Any]) -> None:
    """Restore one private disposable instance, prove the fixed state, then remove it."""

    if not restore_absent(policy):
        raise RelationalSmokeError("the fixed disposable recovery target is not absent")
    source = source_database(policy)
    created = False
    try:
        response = aws([
            "rds", "restore-db-instance-to-point-in-time",
            "--source-db-instance-identifier", policy["source_database"],
            "--target-db-instance-identifier", policy["restore_database"],
            "--use-latest-restorable-time",
            "--db-instance-class", "db.t4g.micro",
            "--db-subnet-group-name", source["subnet_group"],
            "--vpc-security-group-ids", source["security_group"],
            "--db-parameter-group-name", source["parameter_group"],
            "--no-publicly-accessible", "--no-multi-az", "--storage-type", "gp3", "--no-deletion-protection",
        ], policy)
        # A successful restore call owns cleanup even if a later response-shape
        # assertion fails. This prevents a disposable recovery from lingering.
        created = True
        if not isinstance(response.get("DBInstance"), dict):
            raise RelationalSmokeError("the disposable recovery database was not created uniquely")
        deadline = time.monotonic() + policy["restore_wait_seconds"]
        host: str | None = None
        while time.monotonic() < deadline:
            response = aws(["rds", "describe-db-instances", "--db-instance-identifier", policy["restore_database"]], policy)
            instances = response.get("DBInstances")
            instance = instances[0] if isinstance(instances, list) and len(instances) == 1 and isinstance(instances[0], dict) else None
            endpoint = instance.get("Endpoint", {}).get("Address") if isinstance(instance, dict) and isinstance(instance.get("Endpoint"), dict) else None
            if isinstance(instance, dict) and instance.get("DBInstanceStatus") == "available" and instance.get("PubliclyAccessible") is False and instance.get("StorageEncrypted") is True and isinstance(endpoint, str):
                host = endpoint
                break
            time.sleep(20)
        if host is None:
            raise RelationalSmokeError("the disposable recovery database did not become available within its reviewed wait limit")
        run_and_wait("restore_verification", network, policy, [{"name": "RELATIONAL_RESTORE_HOST", "value": host}])
    finally:
        if created:
            aws(["rds", "delete-db-instance", "--db-instance-identifier", policy["restore_database"], "--skip-final-snapshot"], policy)
            deadline = time.monotonic() + policy["restore_wait_seconds"]
            while time.monotonic() < deadline:
                if restore_absent(policy):
                    break
                time.sleep(20)
            else:
                raise RelationalSmokeError("the disposable recovery database did not finish cleanup within its reviewed wait limit")


def execute(policy: dict[str, Any]) -> None:
    """Run every stage only after its immediately preceding safe condition passes."""

    verify_account(policy)
    update_complete(policy["service_stack"], policy)
    outputs = stack_outputs(policy)
    network = worker_network(policy)
    if service_counts(SERVER_SERVICE, policy) != (1, 1) or service_counts(WORKER_SERVICE, policy) != (0, 0) or queue_total(outputs["RelationalSmokeQueueUrl"], policy) != 0 or queue_total(outputs["RelationalSmokeDeadLetterQueueUrl"], policy) != 0:
        raise RelationalSmokeError("the relational proof preconditions are not the reviewed dormant aggregate state")
    source_database(policy)
    run_and_wait("bootstrap", network, policy)
    run_and_wait("migration", network, policy)
    run_and_wait("relay", network, policy)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline and queue_total(outputs["RelationalSmokeQueueUrl"], policy) != 1:
        time.sleep(5)
    if queue_total(outputs["RelationalSmokeQueueUrl"], policy) != 1:
        raise RelationalSmokeError("the fixed relational relay did not produce exactly one aggregate delivery")
    run_and_wait("worker", network, policy)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline and queue_total(outputs["RelationalSmokeQueueUrl"], policy) != 0:
        time.sleep(5)
    if queue_total(outputs["RelationalSmokeQueueUrl"], policy) != 0 or queue_total(outputs["RelationalSmokeDeadLetterQueueUrl"], policy) != 0:
        raise RelationalSmokeError("the isolated relational queues did not return to their empty terminal state")
    restore_and_verify(network, policy)
    if service_counts(SERVER_SERVICE, policy) != (1, 1) or service_counts(WORKER_SERVICE, policy) != (0, 0) or queue_total(outputs["RelationalSmokeQueueUrl"], policy) != 0 or queue_total(outputs["RelationalSmokeDeadLetterQueueUrl"], policy) != 0:
        raise RelationalSmokeError("the relational proof did not preserve the reviewed terminal aggregate state")


def main() -> int:
    """Emit one safe final verdict and no provider response details."""

    parsed = arguments()
    try:
        policy = load_policy()
        if parsed.validate:
            print('{"postgresql_relational_smoke":"validated"}')
            return 0
        execute(policy)
        print('{"postgresql_relational_smoke":"passed"}')
        return 0
    except RelationalSmokeError:
        print('{"postgresql_relational_smoke":"failed"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
