#!/usr/bin/env python3
"""Run one fixed, aggregate-only Kanbien staging outbox-delivery proof."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


PROFILE_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
EXPECTED_ACCOUNT_ID = "337159794548"
EXPECTED_REGION = "eu-west-1"
EXPECTED_CLUSTER = "arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-staging"
EXPECTED_FOUNDATION_STACK = "kanbien-staging-platform-shell-foundation"
EXPECTED_RELAY_FAMILY = "kanbien-staging-platform-shell-relay"
EXPECTED_WORKER_FAMILY = "kanbien-staging-platform-shell-worker"
EXPECTED_WORKER_SERVICE = "kanbien-staging-platform-shell-worker"
EXPECTED_SERVER_SERVICE = "kanbien-staging-platform-shell"
EXPECTED_TABLE_COUNT_BEFORE = 3
EXPECTED_TABLE_COUNT_AFTER = 4
EXPECTED_DUE_BEFORE = 1
EXPECTED_DUE_AFTER = 0
EXPECTED_ALARM_COUNT = 5
RECOVERY_SOURCE_READY = "relay-claim-diagnostic-source-ready-deployment-pending"
RECOVERY_DEPLOYED_READY = "relay-claim-diagnostic-deployed-recovery-pending"
RECOVERY_RELAY_STARTED_BY = "kanbien-outbox-recovery-v2"
RECOVERY_WORKER_STARTED_BY = "kanbien-outbox-worker-recovery-v2"


class DeliveryProofError(Exception):
    """Represent a safe-to-report failure without exposing provider responses."""


def parse_arguments() -> argparse.Namespace:
    """Expose finite resumable proof stages with no caller-selected target or payload."""

    parser = argparse.ArgumentParser(description="Validate or run one fixed resumable Kanbien staging persistence delivery-proof stage.")
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no AWS calls.")
    parser.add_argument("--start-relay", action="store_true", help="Start the one recovery relay task and return immediately.")
    parser.add_argument("--assess-relay", action="store_true", help="Read only the one recovery relay outcome and queue transition.")
    parser.add_argument("--start-worker", action="store_true", help="Start the one self-terminating worker task only after a successful relay assessment.")
    parser.add_argument("--assess-worker", action="store_true", help="Read only the durable worker task outcome and settlement after it exits.")
    parser.add_argument("--verify-terminal", action="store_true", help="Read only the final dormant aggregate state after the one-shot worker exits.")
    parser.add_argument(
        "--approve-outbox-delivery-recovery",
        action="store_true",
        help="Acknowledge the one configuration-remediated relay task and one self-terminating worker task.",
    )
    arguments = parser.parse_args()
    modes = [arguments.validate, arguments.start_relay, arguments.assess_relay, arguments.start_worker, arguments.assess_worker, arguments.verify_terminal]
    if sum(modes) != 1:
        parser.error("choose exactly one proof mode")
    mutating = arguments.start_relay or arguments.start_worker
    if arguments.approve_outbox_delivery_recovery and not mutating:
        parser.error("--approve-outbox-delivery-recovery is valid only for a mutating proof stage")
    if mutating and not arguments.approve_outbox_delivery_recovery:
        parser.error("a mutating proof stage requires --approve-outbox-delivery-recovery")
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
    if worker.get("task_family") != EXPECTED_WORKER_FAMILY:
        raise DeliveryProofError("the delivery proof worker family is not the reviewed task family")
    if smoke.get("status") not in {
        "foundation-and-service-deployed-acceptance-proven-relay-claim-diagnostic-source-ready-deployment-pending",
        "foundation-and-service-deployed-acceptance-proven-relay-claim-diagnostic-deployed-recovery-pending",
    }:
        raise DeliveryProofError("the target lifecycle does not permit the configuration-remediated delivery proof")
    delivery_status = delivery.get("status")
    if delivery_status not in {RECOVERY_SOURCE_READY, RECOVERY_DEPLOYED_READY}:
        raise DeliveryProofError("the delivery proof is not in its governed recovery state")
    if delivery.get("command") != "npm run platform:shell:persistence-delivery-proof" or delivery.get("execution_guard") != "--phase-and-approve-outbox-delivery-recovery":
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
    if action.get("relay_task_count") != 1 or action.get("worker_task_count") != 1:
        raise DeliveryProofError("the delivery proof action is not a one-relay one-worker operation")
    maximum_wait_seconds = integer(action.get("maximum_wait_seconds"), "delivery_proof.bounded_action.maximum_wait_seconds")
    settlement_wait_seconds = integer(action.get("worker_metric_settlement_wait_seconds"), "delivery_proof.bounded_action.worker_metric_settlement_wait_seconds")
    if maximum_wait_seconds != 360 or settlement_wait_seconds != 75:
        raise DeliveryProofError("the delivery proof bounds are not the reviewed fixed values")
    if delivery.get("resumable_stages") != {
        "start_relay": "start-one-labelled-relay-and-return-without-client-side-waiting",
        "assess_relay": "require-one-labelled-successful-relay-and-one-source-delivery-before-worker-activation",
        "start_worker": "start-one-labelled-self-terminating-worker-task-after-successful-relay-assessment",
        "assess_worker": "require-one-labelled-successful-worker-task-one-durable-processing-completion-and-empty-queues",
        "verify_terminal": "require-worker-service-zero-empty-queues-no-due-outbox-and-four-safe-aggregate-records",
    }:
        raise DeliveryProofError("the delivery proof resumable stages are not the reviewed fixed sequence")
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
    if delivery.get("first_relay_attempt") != {
        "executed_on_utc": "2026-09-25",
        "result": "failed-before-outbox-claim-or-queue-send",
        "relay_application_exit_code": 1,
        "stable_error_code": "KANBIEN_PLATFORM_TARGET_RELAY_CONFIG_INVALID",
        "error_field": "not-retained-until-metadata-remediation-is-deployed",
        "post_attempt_state": "three-transaction-records-one-due-outbox-source-and-dead-letter-queues-empty-server-one-worker-zero-five-alarms-ok",
        "evidence_hygiene": "safe-status-exit-code-error-category-and-aggregate-counts-only-no-task-identifiers-records-messages-queue-urls-or-provider-payloads",
    }:
        raise DeliveryProofError("the delivery proof must retain its safe failed relay-attempt evidence")
    if delivery.get("relay_configuration_remediation") != {
        "status": "executed-and-post-deployment-verified",
        "source_change": "derive-a-hashed-lease-owner-from-the-link-local-fargate-task-metadata-endpoint-with-hostname-fallback-only-outside-fargate",
        "deployment_guard": "publish-immutable-image-review-service-change-set-and-health-check-before-one-recovery-relay-run",
        "recovery_limit": "one-relay-task-and-one-self-terminating-worker-task-only-after-remediated-task-definition-is-live",
    }:
        raise DeliveryProofError("the delivery proof must retain its reviewed relay configuration remediation policy")
    if delivery.get("relay_claim_attempt") != {
        "executed_on_utc": "2026-09-25",
        "result": "failed-before-outbox-claim-or-queue-send",
        "relay_application_exit_code": 1,
        "stable_error_code": "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
        "persistence_transition": "platform.persistence.outbox.claim_failed",
        "post_attempt_state": "three-transaction-records-one-due-outbox-source-and-dead-letter-queues-empty-server-one-worker-zero-five-alarms-ok",
        "evidence_hygiene": "safe-status-exit-code-error-category-transition-and-aggregate-counts-only-no-task-identifiers-records-messages-queue-urls-or-provider-payloads",
    }:
        raise DeliveryProofError("the delivery proof must retain its safe failed outbox-claim evidence")
    if delivery.get("relay_claim_diagnostic_remediation") != {
        "status": "source-ready-deployment-pending" if delivery_status == RECOVERY_SOURCE_READY else "deployed-recovery-pending",
        "source_change": "classify-dynamodb-outbox-operation-failures-into-one-allowlisted-provider-category-for-relay-startup-diagnostics",
        "deployment_guard": "publish-immutable-image-review-service-change-set-and-health-check-before-one-new-labelled-recovery-relay-run",
        "relay_started_by": RECOVERY_RELAY_STARTED_BY,
        "worker_started_by": RECOVERY_WORKER_STARTED_BY,
        "recovery_limit": "one-new-relay-task-and-one-new-self-terminating-worker-task-only-after-diagnostic-task-definition-is-live",
    }:
        raise DeliveryProofError("the delivery proof must retain its reviewed outbox-claim diagnostic remediation policy")

    return {
        "account_id": EXPECTED_ACCOUNT_ID,
        "region": EXPECTED_REGION,
        "aws_profile": string(cloud.get("profile"), "cloud.profile"),
        "cluster": EXPECTED_CLUSTER,
        "foundation_stack": EXPECTED_FOUNDATION_STACK,
        "server_service": EXPECTED_SERVER_SERVICE,
        "worker_service": EXPECTED_WORKER_SERVICE,
        "relay_family": EXPECTED_RELAY_FAMILY,
        "worker_family": EXPECTED_WORKER_FAMILY,
        "maximum_wait_seconds": maximum_wait_seconds,
        "settlement_wait_seconds": settlement_wait_seconds,
        "delivery_status": delivery_status,
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


def one_shot_worker_configuration(policy: dict[str, Any]) -> tuple[str, str]:
    """Derive the existing dormant worker's exact task and network configuration without caller input."""

    response = run_aws(["ecs", "describe-services", "--cluster", policy["cluster"], "--services", policy["worker_service"]], policy)
    services = response.get("services")
    if not isinstance(services, list) or len(services) != 1 or not isinstance(services[0], dict):
        raise DeliveryProofError("the reviewed worker service was not found uniquely for its one-shot task")
    service = services[0]
    task_definition = service.get("taskDefinition")
    network_configuration = service.get("networkConfiguration")
    if not isinstance(task_definition, str) or not task_definition or not isinstance(network_configuration, dict):
        raise DeliveryProofError("the reviewed worker service does not expose one task and network configuration")
    awsvpc = network_configuration.get("awsvpcConfiguration")
    if not isinstance(awsvpc, dict):
        raise DeliveryProofError("the reviewed worker service does not use the required awsvpc network configuration")
    subnets = awsvpc.get("subnets")
    security_groups = awsvpc.get("securityGroups")
    if not isinstance(subnets, list) or len(subnets) < 2 or any(not isinstance(value, str) or not value for value in subnets):
        raise DeliveryProofError("the reviewed worker service does not retain two declared task subnets")
    if not isinstance(security_groups, list) or len(security_groups) != 1 or any(not isinstance(value, str) or not value for value in security_groups):
        raise DeliveryProofError("the reviewed worker service does not retain one declared worker security group")
    if awsvpc.get("assignPublicIp") != "ENABLED":
        raise DeliveryProofError("the reviewed worker service does not retain its declared public task address assignment")
    network = "awsvpcConfiguration={subnets=[" + ",".join(subnets) + "],securityGroups=[" + ",".join(security_groups) + "],assignPublicIp=ENABLED}"
    return task_definition, network


def start_one_worker(policy: dict[str, Any]) -> None:
    """Start one labelled worker task that exits after the only permitted successful delivery."""

    task_definition, network = one_shot_worker_configuration(policy)
    overrides = json.dumps({
        "containerOverrides": [{
            "name": "platform-shell-worker",
            "environment": [{"name": "PLATFORM_WORKER_EXIT_AFTER_SUCCESSFUL_DELIVERIES", "value": "1"}],
        }],
    }, separators=(",", ":"))
    response = run_aws([
        "ecs", "run-task", "--cluster", policy["cluster"], "--task-definition", task_definition,
        "--launch-type", "FARGATE", "--count", "1", "--started-by", RECOVERY_WORKER_STARTED_BY,
        "--overrides", overrides, "--network-configuration", network,
    ], policy)
    failures = response.get("failures")
    tasks = response.get("tasks")
    if failures not in ([], None) or not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict):
        raise DeliveryProofError("the one reviewed self-terminating worker task did not start uniquely")
    task_arn = tasks[0].get("taskArn")
    if not isinstance(task_arn, str) or not task_arn:
        raise DeliveryProofError("the one reviewed self-terminating worker task returned no task identity")


def start_one_relay(outputs: dict[str, str], policy: dict[str, Any]) -> None:
    """Start precisely one target-defined Fargate relay task and return before it can outlive this command channel."""

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
        "--started-by", RECOVERY_RELAY_STARTED_BY,
        "--network-configuration", network,
    ], policy)
    failures = response.get("failures")
    tasks = response.get("tasks")
    if failures not in ([], None) or not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict):
        raise DeliveryProofError("the one reviewed relay task did not start uniquely")
    task_arn = tasks[0].get("taskArn")
    if not isinstance(task_arn, str) or not task_arn:
        raise DeliveryProofError("the one reviewed relay task returned no task identity")


def labelled_tasks(started_by: str, expected_family: str, policy: dict[str, Any]) -> list[dict[str, Any]]:
    """Read active and stopped tasks through valid ECS filters, then match the proof label in memory."""

    active = run_aws([
        "ecs", "list-tasks", "--cluster", policy["cluster"], "--started-by", started_by,
    ], policy)
    stopped = run_aws([
        "ecs", "list-tasks", "--cluster", policy["cluster"], "--family", expected_family, "--desired-status", "STOPPED",
    ], policy)
    active_task_arns = active.get("taskArns")
    stopped_task_arns = stopped.get("taskArns")
    if (
        not isinstance(active_task_arns, list)
        or not isinstance(stopped_task_arns, list)
        or any(not isinstance(task, str) or not task for task in [*active_task_arns, *stopped_task_arns])
    ):
        raise DeliveryProofError("the labelled recovery task inspection did not return valid task lists")
    task_arns = list(dict.fromkeys([*active_task_arns, *stopped_task_arns]))
    if not task_arns:
        return []
    response = run_aws(["ecs", "describe-tasks", "--cluster", policy["cluster"], "--tasks", *task_arns], policy)
    described = response.get("tasks")
    if not isinstance(described, list) or len(described) != len(task_arns) or any(not isinstance(task, dict) for task in described):
        raise DeliveryProofError("the labelled recovery task description was incomplete")
    labelled = [task for task in described if task.get("startedBy") == started_by]
    if any(task.get("group") != f"family:{expected_family}" for task in labelled):
        raise DeliveryProofError("a labelled recovery task does not belong to the reviewed task family")
    return labelled


def completed_recovery_relay_exit_code(policy: dict[str, Any]) -> int:
    """Read only the one labelled recovery relay after it has stopped; never emit its identifier."""

    described = labelled_tasks(RECOVERY_RELAY_STARTED_BY, policy["relay_family"], policy)
    if len(described) != 1 or described[0].get("lastStatus") != "STOPPED":
        raise DeliveryProofError("the one labelled recovery relay task is not uniquely stopped")
    containers = described[0].get("containers")
    application = next((container for container in containers if isinstance(container, dict) and container.get("name") == "platform-shell-relay"), None) if isinstance(containers, list) else None
    if not isinstance(application, dict) or not isinstance(application.get("exitCode"), int):
        raise DeliveryProofError("the one reviewed relay task did not complete successfully")
    return application["exitCode"]


def completed_recovery_worker_exit_code(policy: dict[str, Any]) -> int:
    """Read only the one labelled self-terminating worker task after it has stopped."""

    described = labelled_tasks(RECOVERY_WORKER_STARTED_BY, policy["worker_family"], policy)
    if len(described) != 1 or described[0].get("lastStatus") != "STOPPED":
        raise DeliveryProofError("the one reviewed worker task did not reach stopped state")
    containers = described[0].get("containers")
    application = next((container for container in containers if isinstance(container, dict) and container.get("name") == "platform-shell-worker"), None) if isinstance(containers, list) else None
    if not isinstance(application, dict) or not isinstance(application.get("exitCode"), int):
        raise DeliveryProofError("the one reviewed worker task did not report one application exit outcome")
    return application["exitCode"]


def labelled_worker_task_count(desired_status: str, policy: dict[str, Any]) -> int:
    """Count only the fixed recovery worker label so a second task cannot be started by this proof."""

    return sum(1 for task in labelled_tasks(RECOVERY_WORKER_STARTED_BY, policy["worker_family"], policy) if task.get("lastStatus") == desired_status)


def recovery_worker_not_started(policy: dict[str, Any]) -> bool:
    """Permit the one worker task only when no same-labelled recovery task exists."""

    return labelled_worker_task_count("RUNNING", policy) == 0 and labelled_worker_task_count("STOPPED", policy) == 0


def recovery_relay_not_started(policy: dict[str, Any]) -> bool:
    """Permit one relay task only when its fixed recovery label has never been used."""

    return len(labelled_tasks(RECOVERY_RELAY_STARTED_BY, policy["relay_family"], policy)) == 0


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


def relay_delivery_ready(outputs: dict[str, str], policy: dict[str, Any]) -> bool:
    """Require the one relay transition before the proof can activate any worker capacity."""

    source_visible, source_in_flight = queue_counts(outputs["WorkerQueueUrl"], policy)
    dlq_visible, dlq_in_flight = queue_counts(outputs["WorkerDeadLetterQueueUrl"], policy)
    worker_desired, worker_running = service_state(policy["worker_service"], policy)
    server_desired, server_running = service_state(policy["server_service"], policy)
    return (
        completed_recovery_relay_exit_code(policy) == 0
        and table_count(outputs["PlatformPersistenceTableName"], policy) == EXPECTED_TABLE_COUNT_BEFORE
        and due_outbox_count(outputs["PlatformPersistenceTableName"], outputs["PlatformPersistenceOutboxDueIndexName"], policy) == EXPECTED_DUE_AFTER
        and source_visible == 1 and source_in_flight == 0
        and dlq_visible == 0 and dlq_in_flight == 0
        and worker_desired == 0 and worker_running == 0
        and server_desired == 1 and server_running == 1
        and running_relay_count(policy) == 0
        and alarm_health(policy)
    )


def worker_settlement_ready(outputs: dict[str, str], policy: dict[str, Any]) -> bool:
    """Require the one successful self-terminating worker and durable settlement before terminal verification."""

    source_visible, source_in_flight = queue_counts(outputs["WorkerQueueUrl"], policy)
    dlq_visible, dlq_in_flight = queue_counts(outputs["WorkerDeadLetterQueueUrl"], policy)
    worker_desired, worker_running = service_state(policy["worker_service"], policy)
    server_desired, server_running = service_state(policy["server_service"], policy)
    return (
        completed_recovery_worker_exit_code(policy) == 0
        and table_count(outputs["PlatformPersistenceTableName"], policy) == EXPECTED_TABLE_COUNT_AFTER
        and due_outbox_count(outputs["PlatformPersistenceTableName"], outputs["PlatformPersistenceOutboxDueIndexName"], policy) == EXPECTED_DUE_AFTER
        and source_visible == 0 and source_in_flight == 0
        and dlq_visible == 0 and dlq_in_flight == 0
        and worker_desired == 0 and worker_running == 0
        and server_desired == 1 and server_running == 1
        and running_relay_count(policy) == 0
        and alarm_health(policy)
    )


def terminal_state_holds(outputs: dict[str, str], policy: dict[str, Any]) -> bool:
    """Require the dormant safe state that completes this one recovery proof."""

    source_visible, source_in_flight = queue_counts(outputs["WorkerQueueUrl"], policy)
    dlq_visible, dlq_in_flight = queue_counts(outputs["WorkerDeadLetterQueueUrl"], policy)
    worker_desired, worker_running = service_state(policy["worker_service"], policy)
    server_desired, server_running = service_state(policy["server_service"], policy)
    return (
        completed_recovery_worker_exit_code(policy) == 0
        and table_count(outputs["PlatformPersistenceTableName"], policy) == EXPECTED_TABLE_COUNT_AFTER
        and due_outbox_count(outputs["PlatformPersistenceTableName"], outputs["PlatformPersistenceOutboxDueIndexName"], policy) == EXPECTED_DUE_AFTER
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


def require_deployed_recovery(policy: dict[str, Any]) -> dict[str, str]:
    """Fail closed until the immutable remediation image is deployed and health-checked."""

    if policy["delivery_status"] != RECOVERY_DEPLOYED_READY:
        raise DeliveryProofError("the relay configuration remediation has not been deployed and health-checked")
    verify_account(policy)
    return foundation_outputs(policy)


def run_stage(arguments: argparse.Namespace, policy: dict[str, Any]) -> int:
    """Execute one short, resumable proof stage so a client timeout cannot conceal an in-flight state change."""

    outputs = require_deployed_recovery(policy)
    if arguments.start_relay:
        if not preconditions_hold(outputs, policy):
            raise DeliveryProofError("the fixed delivery-proof aggregate preconditions do not hold")
        if not recovery_relay_not_started(policy):
            raise DeliveryProofError("the one labelled recovery relay task has already started or completed")
        start_one_relay(outputs, policy)
        emit("relay-started")
        return 0
    if arguments.assess_relay:
        if not relay_delivery_ready(outputs, policy):
            raise DeliveryProofError("the labelled recovery relay has not reached its exact successful delivery state")
        emit("relay-succeeded", relay_exit_code=0)
        return 0
    if arguments.start_worker:
        if not relay_delivery_ready(outputs, policy):
            raise DeliveryProofError("the worker cannot start before the labelled recovery relay reaches its exact successful delivery state")
        if not recovery_worker_not_started(policy):
            raise DeliveryProofError("the one labelled recovery worker task has already started or completed")
        start_one_worker(policy)
        emit("worker-started")
        return 0
    if arguments.assess_worker:
        if not worker_settlement_ready(outputs, policy):
            raise DeliveryProofError("the self-terminating worker has not reached its exact durable settlement state")
        emit("worker-settled", persistence_table_records=EXPECTED_TABLE_COUNT_AFTER)
        return 0
    if arguments.verify_terminal:
        if not terminal_state_holds(outputs, policy):
            raise DeliveryProofError("the recovery proof terminal aggregate state does not hold")
        emit("passed", relay_exit_code=0, persistence_table_records=EXPECTED_TABLE_COUNT_AFTER)
        return 0
    raise DeliveryProofError("the selected proof stage is not implemented")


def main() -> int:
    """Validate the finite policy or execute its one explicit live action."""

    arguments = parse_arguments()
    policy = resolve_policy(load_profile())
    if arguments.validate:
        emit("validated", maximum_wait_seconds=policy["maximum_wait_seconds"], worker_metric_settlement_wait_seconds=policy["settlement_wait_seconds"])
        return 0
    return run_stage(arguments, policy)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DeliveryProofError as exception:
        print(f"persistence-delivery-proof: {exception}", file=sys.stderr)
        raise SystemExit(1)
