#!/usr/bin/env python3
"""Run the one fixed, redacted Kanbien staging relational reference proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any


PROFILE_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
ACCOUNT = "337159794548"
REGION = "eu-west-1"
SERVER_SERVICE = "kanbien-staging-platform-shell"
WORKER_SERVICE = "kanbien-staging-platform-shell-worker"
CANDIDATE_TASK_FAMILY = "kanbien-staging-platform-shell-candidate-preflight"
IMMUTABLE_IMAGE = re.compile(r"^.+@sha256:([0-9a-f]{64})$")


class RelationalSmokeError(Exception):
    """Represent a safe outcome without exposing AWS data or task output."""


def arguments() -> argparse.Namespace:
    """Accept only an offline check or the one approved fixed-stage sequence."""

    parser = argparse.ArgumentParser(description="Validate or run one Kanbien staging relational smoke proof.")
    parser.add_argument("--validate", action="store_true", help="Validate the committed policy without AWS calls.")
    parser.add_argument("--execute", action="store_true", help="Run the fixed bootstrap-to-restore proof.")
    parser.add_argument("--execute-bootstrap-recovery", action="store_true", help="Run only the fixed recovery bootstrap stage.")
    parser.add_argument("--execute-recovery-continuation", action="store_true", help="Continue only after the fixed recovery bootstrap succeeded.")
    parser.add_argument("--diagnose-bootstrap-recovery", action="store_true", help="Classify only the consumed fixed bootstrap recovery failure.")
    parser.add_argument("--reconcile-current-state", action="store_true", help="Read only the fixed relational aggregate state without starting a task.")
    parser.add_argument("--approve-relational-stage6", action="store_true", help="Acknowledge the one bounded relational proof and recovery cleanup.")
    parser.add_argument("--approve-relational-bootstrap-recovery", action="store_true", help="Acknowledge only the fixed bootstrap recovery stage.")
    parser.add_argument("--approve-relational-recovery-continuation", action="store_true", help="Acknowledge only the one bounded post-bootstrap continuation.")
    parser.add_argument("--approve-relational-bootstrap-recovery-diagnostic", action="store_true", help="Acknowledge only the fixed bootstrap failure classification read.")
    result = parser.parse_args()
    selected = sum((result.validate, result.execute, result.execute_bootstrap_recovery, result.execute_recovery_continuation, result.diagnose_bootstrap_recovery, result.reconcile_current_state))
    if selected != 1:
        parser.error("choose exactly one fixed validation, execution, recovery, or diagnostic mode")
    if (result.validate or result.reconcile_current_state) and (result.approve_relational_stage6 or result.approve_relational_bootstrap_recovery or result.approve_relational_recovery_continuation or result.approve_relational_bootstrap_recovery_diagnostic):
        parser.error("an execution approval guard is unavailable in validation mode")
    if result.execute and (not result.approve_relational_stage6 or result.approve_relational_bootstrap_recovery or result.approve_relational_recovery_continuation or result.approve_relational_bootstrap_recovery_diagnostic):
        parser.error("the fixed relational proof requires --approve-relational-stage6")
    if result.execute_bootstrap_recovery and (not result.approve_relational_bootstrap_recovery or result.approve_relational_stage6 or result.approve_relational_recovery_continuation or result.approve_relational_bootstrap_recovery_diagnostic):
        parser.error("the fixed bootstrap recovery requires --approve-relational-bootstrap-recovery")
    if result.execute_recovery_continuation and (not result.approve_relational_recovery_continuation or result.approve_relational_stage6 or result.approve_relational_bootstrap_recovery or result.approve_relational_bootstrap_recovery_diagnostic):
        parser.error("the fixed recovery continuation requires --approve-relational-recovery-continuation")
    if result.diagnose_bootstrap_recovery and (not result.approve_relational_bootstrap_recovery_diagnostic or result.approve_relational_stage6 or result.approve_relational_bootstrap_recovery or result.approve_relational_recovery_continuation):
        parser.error("the fixed bootstrap recovery diagnostic requires --approve-relational-bootstrap-recovery-diagnostic")
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


def load_policy(mode: str) -> dict[str, Any]:
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
    expected_lifecycle = (
        "stage-5-live-boundary-proven-stage-6-bootstrap-recovery-4-source-ready",
        "candidate-preflight-dormant-definition-deployed-current-image-attempt-terminal-new-immutable-candidate-required",
    )
    if (reference.get("status"), stage.get("status")) != expected_lifecycle:
        raise RelationalSmokeError("the relational lifecycle does not permit the Stage 6 proof")
    control = mapping(stage.get("control"), "stage_6_relational_smoke_composition.control")
    task_families = mapping(control.get("task_families"), "control.task_families")
    task_containers = mapping(control.get("task_containers"), "control.task_containers")
    started_by = mapping(control.get("started_by"), "control.started_by")
    bootstrap_diagnostic = mapping(control.get("bootstrap_recovery_diagnostic"), "control.bootstrap_recovery_diagnostic")
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
        "bootstrap": "kanbien-postgresql-stage6-bootstrap-20260928-recovery-4",
        "migration": "kanbien-postgresql-stage6-migration-20260928-recovery-4",
        "relay": "kanbien-postgresql-stage6-relay-20260928-recovery-4",
        "worker": "kanbien-postgresql-stage6-worker-20260928-recovery-4",
        "restore_verification": "kanbien-postgresql-stage6-restore-verify-20260928-recovery-4",
    }
    required = {
        "command": "npm-run-platform-shell-postgresql-relational-smoke",
        "execution_guard": "execute-and-approve-relational-stage6",
        "bootstrap_recovery_execution_guard": "execute-bootstrap-recovery-and-approve-relational-bootstrap-recovery",
        "recovery_continuation_execution_guard": "execute-recovery-continuation-and-approve-relational-recovery-continuation",
        "bootstrap_recovery_diagnostic_guard": "diagnose-bootstrap-recovery-and-approve-relational-bootstrap-recovery-diagnostic",
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
    expected_diagnostic = {
        "metadata_fallback": "allowlisted-task-stop-code-and-bootstrap-container-reason-classification-only-after-direct-and-derived-log-stream-unavailable",
        "derived_log_stream_prefix": "relational-bootstrap/relational-bootstrap/",
        "output_policy": "safe-failure-category-only-no-stop-code-reason-task-identifier-log-text-or-provider-payload",
        "categories": [
            "bootstrap-task-log-stream-unavailable",
            "bootstrap-task-log-events-unavailable",
            "bootstrap-task-log-stream-empty",
            "bootstrap-runtime-module-unavailable",
            "bootstrap-certificate-authority-unavailable",
            "bootstrap-database-authentication-failure",
            "bootstrap-database-authorization-failure",
            "bootstrap-database-connectivity-failure",
            "bootstrap-database-tls-failure",
            "bootstrap-input-validation-failure",
            "bootstrap-password-quotation-failure",
            "bootstrap-role-provisioning-failure",
            "bootstrap-database-grant-failure",
            "bootstrap-schema-provisioning-failure",
            "bootstrap-schema-grant-failure",
            "bootstrap-workload-failure-unclassified",
            "bootstrap-workload-failure-log-marker-unavailable",
            "bootstrap-image-retrieval-failure",
            "bootstrap-secret-injection-failure",
            "bootstrap-log-driver-initialization-failure",
            "bootstrap-resource-initialization-failure",
            "bootstrap-task-startup-failure",
            "bootstrap-essential-container-exited-without-log-stream",
            "bootstrap-task-terminal-metadata-unclassified",
        ],
    }
    if bootstrap_diagnostic != expected_diagnostic:
        raise RelationalSmokeError("the relational bootstrap diagnostic control differs from the reviewed fixed shape")
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
        "bootstrap_diagnostic_categories": set(expected_diagnostic["categories"]),
        "bootstrap_diagnostic_log_stream_prefix": expected_diagnostic["derived_log_stream_prefix"],
    }


def aws(arguments: list[str], policy: dict[str, Any], allowed_not_found_code: str | None = None) -> dict[str, Any] | None:
    """Call AWS while keeping raw provider responses solely in process memory."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    result = subprocess.run(["aws", *arguments, "--profile", policy["profile"], "--region", REGION, "--output", "json"], capture_output=True, encoding="utf-8", check=False, env=environment)
    if result.returncode != 0:
        if allowed_not_found_code is not None and allowed_not_found_code in result.stderr:
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
    required = ("RelationalSmokeQueueUrl", "RelationalSmokeDeadLetterQueueUrl", "RelayLogGroupName")
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


def candidate_preflight_label(image: str, path: Path = DEFAULT_CANDIDATE_LEDGER_PATH) -> str:
    """Require the successful durable candidate receipt for the active image."""

    match = IMMUTABLE_IMAGE.fullmatch(image)
    if match is None:
        raise RelationalSmokeError("the active service image is not an immutable candidate digest")
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exception:
        raise RelationalSmokeError("the active service candidate receipt is unavailable") from exception
    if ledger.get("schema") != "postgresql-candidate-attempt-ledger/v1" or not isinstance(ledger.get("attempts"), list):
        raise RelationalSmokeError("the active service candidate receipt is invalid")
    image_hash = hashlib.sha256(match.group(1).encode("ascii")).hexdigest()[:16]
    successful = [
        receipt.get("label")
        for receipt in ledger["attempts"]
        if isinstance(receipt, dict)
        and receipt.get("image_hash") == image_hash
        and receipt.get("state") == "succeeded"
        and isinstance(receipt.get("label"), str)
        and re.fullmatch(r"kb-candidate-[a-f0-9]{16}-a[1-4]", receipt["label"])
    ]
    if len(successful) != 1:
        raise RelationalSmokeError("the active image lacks one durable successful candidate receipt")
    return successful[0]


def candidate_execution_preflight_succeeded(policy: dict[str, Any]) -> None:
    """Require the exact active image to have one healthy, stopped private candidate task."""

    service = aws(["ecs", "describe-services", "--cluster", policy["cluster"], "--services", SERVER_SERVICE], policy)
    services = service.get("services")
    current = services[0] if isinstance(services, list) and len(services) == 1 and isinstance(services[0], dict) else None
    task_reference = current.get("taskDefinition") if isinstance(current, dict) else None
    if not isinstance(task_reference, str) or not task_reference:
        raise RelationalSmokeError("the active service candidate preflight source is unavailable")
    definition = aws(["ecs", "describe-task-definition", "--task-definition", task_reference], policy).get("taskDefinition")
    containers = definition.get("containerDefinitions") if isinstance(definition, dict) else None
    application = next((item for item in containers if isinstance(item, dict) and item.get("name") == "platform-shell"), None) if isinstance(containers, list) else None
    image = application.get("image") if isinstance(application, dict) else None
    if not isinstance(image, str):
        raise RelationalSmokeError("the active service candidate preflight image is unavailable")
    label = candidate_preflight_label(image)
    running = aws(["ecs", "list-tasks", "--cluster", policy["cluster"], "--started-by", label, "--desired-status", "RUNNING"], policy).get("taskArns")
    stopped = aws(["ecs", "list-tasks", "--cluster", policy["cluster"], "--started-by", label, "--desired-status", "STOPPED"], policy).get("taskArns")
    if not isinstance(running, list) or running or not isinstance(stopped, list) or len(stopped) != 1 or not isinstance(stopped[0], str):
        raise RelationalSmokeError("the active image lacks one terminal candidate execution preflight")
    observed = aws(["ecs", "describe-tasks", "--cluster", policy["cluster"], "--tasks", stopped[0]], policy).get("tasks")
    task = observed[0] if isinstance(observed, list) and len(observed) == 1 and isinstance(observed[0], dict) else None
    candidate_reference = task.get("taskDefinitionArn") if isinstance(task, dict) else None
    if not isinstance(task, dict) or task.get("lastStatus") != "STOPPED" or task.get("healthStatus") != "HEALTHY" or not isinstance(candidate_reference, str):
        raise RelationalSmokeError("the active image candidate execution preflight did not become healthy and stop")
    candidate_definition = aws(["ecs", "describe-task-definition", "--task-definition", candidate_reference], policy).get("taskDefinition")
    if not isinstance(candidate_definition, dict) or candidate_definition.get("family") != CANDIDATE_TASK_FAMILY:
        raise RelationalSmokeError("the active image candidate preflight did not use the reviewed dormant task family")


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

    for desired_status in ("RUNNING", "STOPPED"):
        response = aws(["ecs", "list-tasks", "--cluster", policy["cluster"], "--started-by", policy["labels"][stage], "--desired-status", desired_status], policy)
        tasks = response.get("taskArns")
        if not isinstance(tasks, list) or tasks:
            raise RelationalSmokeError("a fixed relational proof stage has already been consumed")


def prior_label_succeeded(stage: str, policy: dict[str, Any]) -> None:
    """Require one consumed, successful terminal stage before a continuation."""

    listed = aws(["ecs", "list-tasks", "--cluster", policy["cluster"], "--started-by", policy["labels"][stage], "--desired-status", "STOPPED"], policy)
    tasks = listed.get("taskArns")
    if not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], str):
        raise RelationalSmokeError("the fixed relational continuation predecessor is not one consumed terminal stage")
    described = aws(["ecs", "describe-tasks", "--cluster", policy["cluster"], "--tasks", tasks[0]], policy)
    current = described.get("tasks")
    task = current[0] if isinstance(current, list) and len(current) == 1 and isinstance(current[0], dict) else None
    containers = task.get("containers") if isinstance(task, dict) else None
    container = next((item for item in containers if isinstance(item, dict) and item.get("name") == policy["containers"][stage]), None) if isinstance(containers, list) else None
    if not isinstance(container, dict) or container.get("exitCode") != 0:
        raise RelationalSmokeError("the fixed relational continuation predecessor did not succeed")


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

    return aws(["rds", "describe-db-instances", "--db-instance-identifier", policy["restore_database"]], policy, allowed_not_found_code="DBInstanceNotFound") is None


def reconcile_current_state(policy: dict[str, Any]) -> dict[str, Any]:
    """Read the fixed aggregate prerequisites without receiving data or starting work."""

    verify_account(policy)
    update_complete(policy["foundation_stack"], policy)
    update_complete(policy["service_stack"], policy)
    outputs = stack_outputs(policy)
    server = service_counts(SERVER_SERVICE, policy)
    worker = service_counts(WORKER_SERVICE, policy)
    source_queue = queue_total(outputs["RelationalSmokeQueueUrl"], policy)
    dead_letter_queue = queue_total(outputs["RelationalSmokeDeadLetterQueueUrl"], policy)
    source_database(policy)
    return {
        "source_database": "available-reviewed-posture",
        "restore_target": "absent" if restore_absent(policy) else "present",
        "server": {"desired": server[0], "running": server[1]},
        "worker": {"desired": worker[0], "running": worker[1]},
        "source_queue_total": source_queue,
        "dead_letter_queue_total": dead_letter_queue,
    }


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
    candidate_execution_preflight_succeeded(policy)
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


def execute_bootstrap_recovery(policy: dict[str, Any]) -> None:
    """Run only the fixed replacement bootstrap before any later recovery stage."""

    verify_account(policy)
    update_complete(policy["service_stack"], policy)
    candidate_execution_preflight_succeeded(policy)
    outputs = stack_outputs(policy)
    network = worker_network(policy)
    if service_counts(SERVER_SERVICE, policy) != (1, 1) or service_counts(WORKER_SERVICE, policy) != (0, 0) or queue_total(outputs["RelationalSmokeQueueUrl"], policy) != 0 or queue_total(outputs["RelationalSmokeDeadLetterQueueUrl"], policy) != 0:
        raise RelationalSmokeError("the bootstrap recovery preconditions are not the reviewed dormant aggregate state")
    source_database(policy)
    run_and_wait("bootstrap", network, policy)
    if service_counts(SERVER_SERVICE, policy) != (1, 1) or service_counts(WORKER_SERVICE, policy) != (0, 0) or queue_total(outputs["RelationalSmokeQueueUrl"], policy) != 0 or queue_total(outputs["RelationalSmokeDeadLetterQueueUrl"], policy) != 0:
        raise RelationalSmokeError("the bootstrap recovery did not preserve the reviewed terminal aggregate state")


def execute_recovery_continuation(policy: dict[str, Any]) -> None:
    """Continue a successful bootstrap once, without replaying its consumed label."""

    verify_account(policy)
    update_complete(policy["service_stack"], policy)
    candidate_execution_preflight_succeeded(policy)
    outputs = stack_outputs(policy)
    network = worker_network(policy)
    if service_counts(SERVER_SERVICE, policy) != (1, 1) or service_counts(WORKER_SERVICE, policy) != (0, 0) or queue_total(outputs["RelationalSmokeQueueUrl"], policy) != 0 or queue_total(outputs["RelationalSmokeDeadLetterQueueUrl"], policy) != 0:
        raise RelationalSmokeError("the recovery continuation preconditions are not the reviewed dormant aggregate state")
    source_database(policy)
    prior_label_succeeded("bootstrap", policy)
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
        raise RelationalSmokeError("the recovery continuation did not preserve the reviewed terminal aggregate state")


def bootstrap_metadata_category(task: dict[str, Any], container: dict[str, Any], policy: dict[str, Any]) -> str:
    """Reduce terminal metadata to one reviewed category without emitting raw values."""

    stop_code = task.get("stopCode")
    reason = container.get("reason")
    details = " ".join(value for value in (stop_code, reason) if isinstance(value, str)).lower()
    if "cannotpullcontainererror" in details:
        category = "bootstrap-image-retrieval-failure"
    elif "resourceinitializationerror" in details and "secret" in details:
        category = "bootstrap-secret-injection-failure"
    elif "resourceinitializationerror" in details and "log" in details:
        category = "bootstrap-log-driver-initialization-failure"
    elif "resourceinitializationerror" in details:
        category = "bootstrap-resource-initialization-failure"
    elif stop_code == "TaskFailedToStart":
        category = "bootstrap-task-startup-failure"
    elif stop_code == "EssentialContainerExited":
        category = "bootstrap-essential-container-exited-without-log-stream"
    else:
        category = "bootstrap-task-terminal-metadata-unclassified"
    if category not in policy["bootstrap_diagnostic_categories"]:
        raise RelationalSmokeError("the terminal metadata classifier selected an unapproved category")
    return category


def derived_bootstrap_log_stream(task: dict[str, Any], policy: dict[str, Any]) -> str | None:
    """Construct only the standard awslogs name for this fixed bootstrap task."""

    task_arn = task.get("taskArn")
    if not isinstance(task_arn, str):
        return None
    task_id = task_arn.rsplit("/", 1)[-1]
    if not task_id or any(character not in "0123456789abcdef-" for character in task_id.lower()):
        return None
    return policy["bootstrap_diagnostic_log_stream_prefix"] + task_id


def failed_bootstrap_receipt_label(policy: dict[str, Any]) -> str:
    """Select only the durable terminal bootstrap receipt being diagnosed."""

    ledger = load_ledger(policy)
    receipt = ledger["stages"].get("bootstrap")
    label = receipt.get("label") if isinstance(receipt, dict) else None
    if (
        not isinstance(receipt, dict)
        or receipt.get("state") != "failed"
        or not isinstance(label, str)
        or not re.fullmatch(r"kb-pg6-bootstrap-r5-a[1-4]", label)
    ):
        raise RelationalSmokeError("the bootstrap diagnostic has no durable terminal failed receipt")
    return label


def diagnose_bootstrap_recovery(policy: dict[str, Any]) -> str:
    """Classify one durable failed bootstrap without emitting task or log details."""

    verify_account(policy)
    update_complete(policy["service_stack"], policy)
    outputs = stack_outputs(policy)
    label = failed_bootstrap_receipt_label(policy)
    listed = aws(["ecs", "list-tasks", "--cluster", policy["cluster"], "--started-by", label, "--desired-status", "STOPPED"], policy)
    task_arns = listed.get("taskArns")
    if not isinstance(task_arns, list) or len(task_arns) != 1 or not isinstance(task_arns[0], str):
        raise RelationalSmokeError("the fixed bootstrap diagnostic cannot identify one consumed terminal task")
    described = aws(["ecs", "describe-tasks", "--cluster", policy["cluster"], "--tasks", task_arns[0]], policy)
    tasks = described.get("tasks")
    task = tasks[0] if isinstance(tasks, list) and len(tasks) == 1 and isinstance(tasks[0], dict) else None
    containers = task.get("containers") if isinstance(task, dict) else None
    container = next((item for item in containers if isinstance(item, dict) and item.get("name") == policy["containers"]["bootstrap"]), None) if isinstance(containers, list) else None
    if not isinstance(container, dict) or container.get("exitCode") != 1:
        raise RelationalSmokeError("the fixed bootstrap diagnostic terminal metadata differs from the reviewed recovery-1 failure")
    stream = container.get("logStreamName")
    if not isinstance(stream, str) or not stream:
        stream = derived_bootstrap_log_stream(task, policy)
        if stream is None:
            return bootstrap_metadata_category(task, container, policy)
    logged = aws(["logs", "get-log-events", "--log-group-name", outputs["RelayLogGroupName"], "--log-stream-name", stream, "--start-from-head", "--limit", "20"], policy, allowed_not_found_code="ResourceNotFoundException")
    if logged is None:
        return bootstrap_metadata_category(task, container, policy)
    events = logged.get("events")
    if not isinstance(events, list):
        return "bootstrap-task-log-events-unavailable"
    if not events:
        return "bootstrap-task-log-stream-empty"
    for event in events:
        message = event.get("message") if isinstance(event, dict) else None
        if not isinstance(message, str):
            continue
        if "ERR_MODULE_NOT_FOUND" in message or "Cannot find module" in message:
            return "bootstrap-runtime-module-unavailable"
        if "RELATIONAL_TASK_CERTIFICATE_AUTHORITY_UNAVAILABLE" in message:
            return "bootstrap-certificate-authority-unavailable"
        if "password authentication failed" in message:
            return "bootstrap-database-authentication-failure"
        if "no pg_hba.conf entry" in message or "permission denied" in message:
            return "bootstrap-database-authorization-failure"
        if "ETIMEDOUT" in message or "ECONNREFUSED" in message:
            return "bootstrap-database-connectivity-failure"
        if "self-signed certificate" in message or "certificate verify failed" in message:
            return "bootstrap-database-tls-failure"
        try:
            safe_event = json.loads(message)
        except json.JSONDecodeError:
            continue
        fields = safe_event.get("fields") if isinstance(safe_event, dict) else None
        failure_category = fields.get("failure_category") if isinstance(fields, dict) else None
        if isinstance(safe_event, dict) and safe_event.get("level") == "error" and safe_event.get("message") == "kanbien-platform.relational-smoke.bootstrap_completed" and fields == {"outcome": "failed", "failure_category": failure_category} and isinstance(failure_category, str) and failure_category in policy["bootstrap_diagnostic_categories"]:
            return failure_category
        if safe_event == {"level": "error", "message": "kanbien-platform.relational-smoke.bootstrap_completed", "fields": {"outcome": "failed"}}:
            return "bootstrap-workload-failure-unclassified"
    return "bootstrap-workload-failure-log-marker-unavailable"


def main() -> int:
    """Emit one safe final verdict and no provider response details."""

    parsed = arguments()
    try:
        mode = "diagnostic" if (parsed.diagnose_bootstrap_recovery or parsed.reconcile_current_state) else "validate" if parsed.validate else "execution"
        policy = load_policy(mode)
        if parsed.validate:
            print('{"postgresql_relational_smoke":"validated"}')
            return 0
        if parsed.execute_bootstrap_recovery:
            execute_bootstrap_recovery(policy)
            print('{"postgresql_relational_bootstrap_recovery":"passed"}')
            return 0
        if parsed.execute_recovery_continuation:
            execute_recovery_continuation(policy)
            print('{"postgresql_relational_recovery_continuation":"passed"}')
            return 0
        if parsed.diagnose_bootstrap_recovery:
            category = diagnose_bootstrap_recovery(policy)
            print(json.dumps({"postgresql_relational_bootstrap_recovery_diagnostic": category}, sort_keys=True))
            return 0
        if parsed.reconcile_current_state:
            print(json.dumps({"postgresql_relational_current_state": reconcile_current_state(policy)}, sort_keys=True))
            return 0
        execute(policy)
        print('{"postgresql_relational_smoke":"passed"}')
        return 0
    except RelationalSmokeError:
        if parsed.execute_bootstrap_recovery:
            print('{"postgresql_relational_bootstrap_recovery":"failed"}')
        elif parsed.execute_recovery_continuation:
            print('{"postgresql_relational_recovery_continuation":"failed"}')
        elif parsed.diagnose_bootstrap_recovery:
            print('{"postgresql_relational_bootstrap_recovery_diagnostic":"diagnostic-unavailable"}')
        else:
            print('{"postgresql_relational_smoke":"failed"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
