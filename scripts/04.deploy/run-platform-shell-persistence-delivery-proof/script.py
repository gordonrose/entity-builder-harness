#!/usr/bin/env python3
"""Run one fixed, aggregate-only Kanbien staging outbox-delivery proof."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable


PROFILE_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
EXPECTED_ACCOUNT_ID = "337159794548"
EXPECTED_REGION = "eu-west-1"
EXPECTED_CLUSTER = "arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-staging"
EXPECTED_FOUNDATION_STACK = "kanbien-staging-platform-shell-foundation"
EXPECTED_RELAY_FAMILY = "kanbien-staging-platform-shell-relay"
EXPECTED_WORKER_SERVICE = "kanbien-staging-platform-shell-worker"
EXPECTED_SERVER_SERVICE = "kanbien-staging-platform-shell"
EXPECTED_TABLE_COUNT_BEFORE = 3
EXPECTED_TABLE_COUNT_AFTER = 4
EXPECTED_DUE_BEFORE = 1
EXPECTED_DUE_AFTER = 0
EXPECTED_ALARM_COUNT = 5


class DeliveryProofError(Exception):
    """Represent a safe-to-report failure without exposing provider responses."""


def parse_arguments() -> argparse.Namespace:
    """Expose only validation or the one explicitly approved live operation."""

    parser = argparse.ArgumentParser(description="Validate or run the fixed Kanbien staging persistence delivery proof.")
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no AWS calls.")
    parser.add_argument("--execute", action="store_true", help="Run the one bounded relay and worker proof.")
    parser.add_argument(
        "--approve-outbox-delivery-proof",
        action="store_true",
        help="Acknowledge the one relay task and temporary worker scale-up to one.",
    )
    arguments = parser.parse_args()
    if arguments.validate == arguments.execute:
        parser.error("choose exactly one of --validate or --execute")
    if arguments.validate and arguments.approve_outbox_delivery_proof:
        parser.error("--approve-outbox-delivery-proof is valid only with --execute")
    if arguments.execute and not arguments.approve_outbox_delivery_proof:
        parser.error("--execute requires --approve-outbox-delivery-proof")
    return arguments


def load_profile() -> dict[str, Any]:
    """Load only the committed target policy; callers cannot choose a target."""

    try:
        import yaml
    except ImportError as exception:
        raise DeliveryProofError("PyYAML is required for delivery-proof validation") from exception
    try:
        with PROFILE_PATH.open(encoding="utf-8") as handle:
            profile = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise DeliveryProofError("the committed staging target profile could not be read") from exception
    if not isinstance(profile, dict):
        raise DeliveryProofError("the committed staging target profile must be a mapping")
    return profile


def mapping(value: Any, path: str) -> dict[str, Any]:
    """Require a declared map rather than silently defaulting an operation policy."""

    if not isinstance(value, dict):
        raise DeliveryProofError(f"the target profile must declare {path}")
    return value


def string(value: Any, path: str) -> str:
    """Require one non-empty policy string before it is used by an AWS operation."""

    if not isinstance(value, str) or not value:
        raise DeliveryProofError(f"the target profile must declare {path}")
    return value


def integer(value: Any, path: str) -> int:
    """Require one integer policy value before it bounds a live operation."""

    if not isinstance(value, int):
        raise DeliveryProofError(f"the target profile must declare integer {path}")
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, Any]:
    """Accept only the already-reviewed one-entry delivery lifecycle state."""

    cloud = mapping(profile.get("cloud"), "cloud")
    aws = mapping(profile.get("aws"), "aws")
    deployment_config = mapping(profile.get("deployment"), "deployment")
    cloudformation = mapping(deployment_config.get("cloudformation"), "deployment.cloudformation")
    runtime = mapping(profile.get("runtime"), "runtime")
    deployment = mapping(runtime.get("deployment_project"), "runtime.deployment_project")
    worker = mapping(runtime.get("worker"), "runtime.worker")
    persistence = mapping(profile.get("persistence"), "persistence")
    smoke = mapping(persistence.get("smoke_transactional_outbox"), "persistence.smoke_transactional_outbox")
    delivery = mapping(smoke.get("delivery_proof"), "persistence.smoke_transactional_outbox.delivery_proof")
    preconditions = mapping(delivery.get("preconditions"), "persistence.smoke_transactional_outbox.delivery_proof.preconditions")
    action = mapping(delivery.get("bounded_action"), "persistence.smoke_transactional_outbox.delivery_proof.bounded_action")
    success = mapping(delivery.get("success"), "persistence.smoke_transactional_outbox.delivery_proof.success")

    if cloud.get("account_id") != EXPECTED_ACCOUNT_ID or cloud.get("region") != EXPECTED_REGION:
        raise DeliveryProofError("the delivery proof target account or region is not the reviewed staging target")
    if aws.get("cluster") != EXPECTED_CLUSTER:
        raise DeliveryProofError("the delivery proof cluster is not the reviewed staging cluster")
    if cloudformation.get("foundation_stack") != EXPECTED_FOUNDATION_STACK:
        raise DeliveryProofError("the delivery proof foundation stack is not the reviewed stack")
    if deployment.get("server_service") != EXPECTED_SERVER_SERVICE or deployment.get("worker_service") != EXPECTED_WORKER_SERVICE:
        raise DeliveryProofError("the delivery proof service names are not the reviewed services")
    if deployment.get("relay_task_family") != EXPECTED_RELAY_FAMILY:
        raise DeliveryProofError("the delivery proof relay family is not the reviewed task family")
    if smoke.get("status") != "foundation-and-service-deployed-acceptance-proven-delivery-proof-source-ready":
        raise DeliveryProofError("the target lifecycle does not permit the delivery proof")
    if delivery.get("status") != "source-ready-one-execution-pending":
        raise DeliveryProofError("the delivery proof is not in its one-execution-pending state")
    if delivery.get("command") != "npm run platform:shell:persistence-delivery-proof" or delivery.get("execution_guard") != "--execute-and-approve-outbox-delivery-proof":
        raise DeliveryProofError("the delivery proof command or guard is not the reviewed fixed shape")
    if delivery.get("task_family") != EXPECTED_RELAY_FAMILY:
        raise DeliveryProofError("the delivery proof task family differs from target runtime policy")
    if preconditions != {
        "persistence_table_records": EXPECTED_TABLE_COUNT_BEFORE,
        "due_outbox_entries": EXPECTED_DUE_BEFORE,
        "source_queue_visible_messages": 0,
        "dead_letter_queue_visible_messages": 0,
        "relay_running_tasks": 0,
        "worker_desired_count": 0,
        "worker_running_count": 0,
    }:
        raise DeliveryProofError("the delivery proof preconditions are not the reviewed dormant aggregate state")
    if action.get("relay_task_count") != 1 or action.get("worker_desired_count") != 1:
        raise DeliveryProofError("the delivery proof action is not a one-relay one-worker operation")
    maximum_wait_seconds = integer(action.get("maximum_wait_seconds"), "delivery_proof.bounded_action.maximum_wait_seconds")
    settlement_wait_seconds = integer(action.get("worker_metric_settlement_wait_seconds"), "delivery_proof.bounded_action.worker_metric_settlement_wait_seconds")
    if maximum_wait_seconds != 360 or settlement_wait_seconds != 75:
        raise DeliveryProofError("the delivery proof bounds are not the reviewed fixed values")
    if success != {
        "relay_exit_code": 0,
        "persistence_table_records": EXPECTED_TABLE_COUNT_AFTER,
        "due_outbox_entries": EXPECTED_DUE_AFTER,
        "source_queue_visible_messages": 0,
        "dead_letter_queue_visible_messages": 0,
        "worker_desired_count": 0,
        "worker_running_count": 0,
    }:
        raise DeliveryProofError("the delivery proof success state is not the reviewed terminal aggregate state")
    if delivery.get("output_policy") != "status-duration-and-aggregate-counts-only-no-task-identifiers-records-messages-queue-urls-or-provider-payloads":
        raise DeliveryProofError("the delivery proof output policy is not the reviewed redaction boundary")

    return {
        "account_id": EXPECTED_ACCOUNT_ID,
        "region": EXPECTED_REGION,
        "aws_profile": string(cloud.get("profile"), "cloud.profile"),
        "cluster": EXPECTED_CLUSTER,
        "foundation_stack": EXPECTED_FOUNDATION_STACK,
        "server_service": EXPECTED_SERVER_SERVICE,
        "worker_service": EXPECTED_WORKER_SERVICE,
        "relay_family": EXPECTED_RELAY_FAMILY,
        "maximum_wait_seconds": maximum_wait_seconds,
        "settlement_wait_seconds": settlement_wait_seconds,
    }


def run_aws(arguments: list[str], policy: dict[str, Any]) -> dict[str, Any]:
    """Run one fixed target operation while retaining raw provider data only in memory."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    result = subprocess.run(
        ["aws", *arguments, "--profile", policy["aws_profile"], "--region", policy["region"], "--output", "json"],
        check=False,
        capture_output=True,
        encoding="utf-8",
        env=environment,
    )
    if result.returncode != 0:
        raise DeliveryProofError("an approved staging delivery-proof AWS operation did not complete")
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exception:
        raise DeliveryProofError("an approved staging delivery-proof AWS operation returned an unexpected response") from exception
    if not isinstance(response, dict):
        raise DeliveryProofError("an approved staging delivery-proof AWS operation must return an object")
    return response


def verify_account(policy: dict[str, Any]) -> None:
    """Fail closed before mutable work when credentials resolve outside the target account."""

    if run_aws(["sts", "get-caller-identity"], policy).get("Account") != policy["account_id"]:
        raise DeliveryProofError("the selected AWS identity is not the reviewed staging account")


def foundation_outputs(policy: dict[str, Any]) -> dict[str, str]:
    """Read only stable Foundation output values; do not print URLs or network identifiers."""

    response = run_aws(["cloudformation", "describe-stacks", "--stack-name", policy["foundation_stack"]], policy)
    stacks = response.get("Stacks")
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict):
        raise DeliveryProofError("the reviewed Foundation stack was not found uniquely")
    if stacks[0].get("StackStatus") != "UPDATE_COMPLETE":
        raise DeliveryProofError("the reviewed Foundation stack is not update-complete")
    outputs = stacks[0].get("Outputs")
    if not isinstance(outputs, list):
        raise DeliveryProofError("the reviewed Foundation stack did not return outputs")
    values: dict[str, str] = {}
    for output in outputs:
        if isinstance(output, dict) and isinstance(output.get("OutputKey"), str) and isinstance(output.get("OutputValue"), str):
            values[output["OutputKey"]] = output["OutputValue"]
    required = ("PlatformPersistenceTableName", "PlatformPersistenceOutboxDueIndexName", "WorkerQueueUrl", "WorkerDeadLetterQueueUrl", "PublicSubnetIdsCsv", "RelaySecurityGroupId")
    if any(not values.get(key) for key in required):
        raise DeliveryProofError("the reviewed Foundation outputs are incomplete for the bounded delivery proof")
    return values


def table_count(table_name: str, policy: dict[str, Any]) -> int:
    """Read only DynamoDB's aggregate count, never table items."""

    response = run_aws(["dynamodb", "scan", "--table-name", table_name, "--select", "COUNT"], policy)
    try:
        return int(response.get("Count"))
    except (TypeError, ValueError) as exception:
        raise DeliveryProofError("the persistence table count was not an integer") from exception


def due_outbox_count(table_name: str, index_name: str, policy: dict[str, Any]) -> int:
    """Read only the due-index count for the fixed deliverable outbox partition."""

    response = run_aws([
        "dynamodb", "query",
        "--table-name", table_name,
        "--index-name", index_name,
        "--select", "COUNT",
        "--key-condition-expression", "#dueKey = :dueKey",
        "--expression-attribute-names", '{"#dueKey":"DueKey"}',
        "--expression-attribute-values", '{":dueKey":{"S":"OUTBOX#DELIVERABLE"}}',
    ], policy)
    try:
        return int(response.get("Count"))
    except (TypeError, ValueError) as exception:
        raise DeliveryProofError("the due-outbox aggregate count was not an integer") from exception


def queue_counts(queue_url: str, policy: dict[str, Any]) -> tuple[int, int]:
    """Read only visible and in-flight queue counts for one reviewed queue output."""

    response = run_aws([
        "sqs", "get-queue-attributes",
        "--queue-url", queue_url,
        "--attribute-names", "ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible",
    ], policy)
    attributes = response.get("Attributes")
    if not isinstance(attributes, dict):
        raise DeliveryProofError("the reviewed queue count inspection returned no attributes")
    try:
        return int(attributes.get("ApproximateNumberOfMessages", "-1")), int(attributes.get("ApproximateNumberOfMessagesNotVisible", "-1"))
    except (TypeError, ValueError) as exception:
        raise DeliveryProofError("the reviewed queue count inspection returned invalid counts") from exception


def service_state(service_name: str, policy: dict[str, Any]) -> tuple[int, int]:
    """Read desired and running counts for one reviewed ECS service."""

    response = run_aws(["ecs", "describe-services", "--cluster", policy["cluster"], "--services", service_name], policy)
    services = response.get("services")
    if not isinstance(services, list) or len(services) != 1 or not isinstance(services[0], dict):
        raise DeliveryProofError("a reviewed ECS service was not found uniquely")
    try:
        return int(services[0].get("desiredCount")), int(services[0].get("runningCount"))
    except (TypeError, ValueError) as exception:
        raise DeliveryProofError("a reviewed ECS service returned invalid aggregate counts") from exception


def running_relay_count(policy: dict[str, Any]) -> int:
    """Read only the aggregate number of active tasks in the fixed relay family."""

    response = run_aws([
        "ecs", "list-tasks", "--cluster", policy["cluster"], "--family", policy["relay_family"], "--desired-status", "RUNNING",
    ], policy)
    task_arns = response.get("taskArns")
    if not isinstance(task_arns, list) or any(not isinstance(task, str) for task in task_arns):
        raise DeliveryProofError("the relay task inspection did not return an aggregate task list")
    return len(task_arns)


def alarm_health(policy: dict[str, Any]) -> bool:
    """Require the existing five platform-shell alarms to remain in their healthy state."""

    response = run_aws(["cloudwatch", "describe-alarms", "--alarm-name-prefix", "kanbien-staging-platform-shell"], policy)
    alarms = response.get("MetricAlarms")
    if not isinstance(alarms, list) or len(alarms) != EXPECTED_ALARM_COUNT or any(not isinstance(alarm, dict) for alarm in alarms):
        return False
    return all(alarm.get("StateValue") == "OK" for alarm in alarms)


def update_worker_count(value: int, policy: dict[str, Any]) -> None:
    """Scale only the declared dormant worker service, and only to zero or one."""

    if value not in (0, 1):
        raise DeliveryProofError("the delivery proof permits worker desired count zero or one only")
    run_aws([
        "ecs", "update-service", "--cluster", policy["cluster"], "--service", policy["worker_service"], "--desired-count", str(value),
    ], policy)


def run_one_relay(outputs: dict[str, str], policy: dict[str, Any]) -> int:
    """Start precisely one target-defined Fargate relay task and retain its ARN only in memory."""

    subnets = [item for item in outputs["PublicSubnetIdsCsv"].split(",") if item]
    if len(subnets) < 2:
        raise DeliveryProofError("the reviewed relay network requires two declared public subnets")
    network = "awsvpcConfiguration={subnets=[" + ",".join(subnets) + "],securityGroups=[" + outputs["RelaySecurityGroupId"] + "],assignPublicIp=ENABLED}"
    response = run_aws([
        "ecs", "run-task",
        "--cluster", policy["cluster"],
        "--task-definition", policy["relay_family"],
        "--launch-type", "FARGATE",
        "--count", "1",
        "--network-configuration", network,
    ], policy)
    failures = response.get("failures")
    tasks = response.get("tasks")
    if failures not in ([], None) or not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict):
        raise DeliveryProofError("the one reviewed relay task did not start uniquely")
    task_arn = tasks[0].get("taskArn")
    if not isinstance(task_arn, str) or not task_arn:
        raise DeliveryProofError("the one reviewed relay task returned no task identity")
    wait = subprocess.run(
        ["aws", "ecs", "wait", "tasks-stopped", "--cluster", policy["cluster"], "--tasks", task_arn, "--profile", policy["aws_profile"], "--region", policy["region"]],
        check=False,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "AWS_PAGER": "", "AWS_CLI_AUTO_PROMPT": "off"},
    )
    if wait.returncode != 0:
        raise DeliveryProofError("the one reviewed relay task did not stop within its bounded wait")
    response = run_aws(["ecs", "describe-tasks", "--cluster", policy["cluster"], "--tasks", task_arn], policy)
    described = response.get("tasks")
    if not isinstance(described, list) or len(described) != 1 or not isinstance(described[0], dict) or described[0].get("lastStatus") != "STOPPED":
        raise DeliveryProofError("the one reviewed relay task did not reach stopped state")
    containers = described[0].get("containers")
    if not isinstance(containers, list) or not containers or any(not isinstance(container, dict) or container.get("exitCode") != 0 for container in containers):
        raise DeliveryProofError("the one reviewed relay task did not complete successfully")
    return 0


def wait_until(predicate: Callable[[], bool], timeout_seconds: int) -> bool:
    """Poll at a fixed slow cadence to keep the rehearsal bounded and inexpensive."""

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(10)
    return predicate()


def preconditions_hold(outputs: dict[str, str], policy: dict[str, Any]) -> bool:
    """Require exactly the previously recorded atomic-acceptance aggregate state."""

    source_visible, source_in_flight = queue_counts(outputs["WorkerQueueUrl"], policy)
    dlq_visible, dlq_in_flight = queue_counts(outputs["WorkerDeadLetterQueueUrl"], policy)
    worker_desired, worker_running = service_state(policy["worker_service"], policy)
    server_desired, server_running = service_state(policy["server_service"], policy)
    return (
        table_count(outputs["PlatformPersistenceTableName"], policy) == EXPECTED_TABLE_COUNT_BEFORE
        and due_outbox_count(outputs["PlatformPersistenceTableName"], outputs["PlatformPersistenceOutboxDueIndexName"], policy) == EXPECTED_DUE_BEFORE
        and source_visible == 0 and source_in_flight == 0
        and dlq_visible == 0 and dlq_in_flight == 0
        and worker_desired == 0 and worker_running == 0
        and server_desired == 1 and server_running == 1
        and running_relay_count(policy) == 0
        and alarm_health(policy)
    )


def emit(result: str, **fields: int | str) -> None:
    """Emit only safe status, duration, exit code, and aggregate count facts."""

    print(json.dumps({"persistence_delivery_proof": result, **fields}, separators=(",", ":"), sort_keys=True))


def execute(policy: dict[str, Any]) -> int:
    """Relay the one committed obligation, process it once, and always return worker to zero."""

    started = time.monotonic()
    worker_enabled = False
    cleanup_failed = False
    relay_exit_code = -1
    result = "inconclusive"
    failure = ""
    try:
        verify_account(policy)
        outputs = foundation_outputs(policy)
        if not preconditions_hold(outputs, policy):
            raise DeliveryProofError("the fixed delivery-proof aggregate preconditions do not hold")
        relay_exit_code = run_one_relay(outputs, policy)
        if not wait_until(
            lambda: due_outbox_count(outputs["PlatformPersistenceTableName"], outputs["PlatformPersistenceOutboxDueIndexName"], policy) == EXPECTED_DUE_AFTER
            and queue_counts(outputs["WorkerQueueUrl"], policy) == (1, 0)
            and queue_counts(outputs["WorkerDeadLetterQueueUrl"], policy) == (0, 0),
            policy["maximum_wait_seconds"],
        ):
            raise DeliveryProofError("the relay did not create exactly one expected source-queue delivery")
        update_worker_count(1, policy)
        worker_enabled = True
        if not wait_until(
            lambda: service_state(policy["worker_service"], policy)[1] >= 1
            and table_count(outputs["PlatformPersistenceTableName"], policy) == EXPECTED_TABLE_COUNT_AFTER
            and due_outbox_count(outputs["PlatformPersistenceTableName"], outputs["PlatformPersistenceOutboxDueIndexName"], policy) == EXPECTED_DUE_AFTER
            and queue_counts(outputs["WorkerQueueUrl"], policy) == (0, 0)
            and queue_counts(outputs["WorkerDeadLetterQueueUrl"], policy) == (0, 0),
            policy["maximum_wait_seconds"],
        ):
            raise DeliveryProofError("the bounded worker did not reach the expected durable completion state")
        time.sleep(policy["settlement_wait_seconds"])
        if service_state(policy["worker_service"], policy)[1] < 1:
            raise DeliveryProofError("the worker did not remain available for the reviewed metric-settlement interval")
        result = "passed"
    except DeliveryProofError as exception:
        failure = str(exception)
    finally:
        if worker_enabled:
            try:
                update_worker_count(0, policy)
                if not wait_until(lambda: service_state(policy["worker_service"], policy) == (0, 0), policy["maximum_wait_seconds"]):
                    cleanup_failed = True
            except DeliveryProofError:
                cleanup_failed = True
    duration_ms = round((time.monotonic() - started) * 1000)
    if cleanup_failed:
        emit("cleanup-failed", duration_ms=duration_ms, relay_exit_code=relay_exit_code)
        return 1
    if result == "passed":
        emit("passed", duration_ms=duration_ms, relay_exit_code=relay_exit_code, persistence_table_records=EXPECTED_TABLE_COUNT_AFTER)
        return 0
    emit("inconclusive", duration_ms=duration_ms, relay_exit_code=relay_exit_code)
    print(f"persistence-delivery-proof: {failure}", file=sys.stderr)
    return 1


def main() -> int:
    """Validate the finite policy or execute its one explicit live action."""

    arguments = parse_arguments()
    policy = resolve_policy(load_profile())
    if arguments.validate:
        emit("validated", maximum_wait_seconds=policy["maximum_wait_seconds"], worker_metric_settlement_wait_seconds=policy["settlement_wait_seconds"])
        return 0
    return execute(policy)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DeliveryProofError as exception:
        print(f"persistence-delivery-proof: {exception}", file=sys.stderr)
        raise SystemExit(1)
