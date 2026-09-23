#!/usr/bin/env python3
"""Validate or run the finite, side-effect-free Kanbien staging worker proof."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
import uuid


DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"


class WorkerSmokeError(Exception):
    """Represent a safe-to-report policy, precondition, or bounded-operation failure."""


def parse_arguments() -> argparse.Namespace:
    """Require an explicit double opt-in before this command can mutate the staging target."""

    parser = argparse.ArgumentParser(description="Validate or run the guarded Kanbien staging worker-consumer proof.")
    parser.add_argument("--validate", action="store_true", help="Validate the source policy only; do not contact AWS.")
    parser.add_argument("--execute", action="store_true", help="Run the reviewed bounded worker proof after current approval.")
    parser.add_argument("--approve-live-worker-smoke", action="store_true", help="Acknowledge that --execute sends one harmless queue message and briefly starts one worker task.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE, help="Path to the Kanbien staging target profile.")
    parser.add_argument("--aws-cli", default="aws", help="AWS CLI executable for fixed target operations.")
    parser.add_argument("--aws-credential-source", choices=("target-profile", "environment"), default="target-profile", help="Use the declared AWS profile or explicitly configured environment credentials.")
    parser.add_argument("--timeout-seconds", type=int, default=360, help="Bound worker convergence and cleanup waits to 60-600 seconds.")
    arguments = parser.parse_args()
    if arguments.validate == arguments.execute:
        parser.error("choose exactly one of --validate or --execute")
    if arguments.validate and arguments.approve_live_worker_smoke:
        parser.error("--approve-live-worker-smoke is valid only with --execute")
    if arguments.execute and not arguments.approve_live_worker_smoke:
        parser.error("--execute requires --approve-live-worker-smoke")
    if not 60 <= arguments.timeout_seconds <= 600:
        parser.error("--timeout-seconds must be between 60 and 600")
    return arguments


def load_profile(path: Path) -> dict[str, Any]:
    """Load the reviewed target profile without a permissive fallback parser."""

    try:
        import yaml
    except ImportError as exception:
        raise WorkerSmokeError("PyYAML is required for worker-smoke policy validation") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            profile = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise WorkerSmokeError("the target profile could not be read") from exception
    if not isinstance(profile, dict):
        raise WorkerSmokeError("the target profile must be a YAML mapping")
    return profile


def mapping(value: Any, path: str) -> dict[str, Any]:
    """Require a reviewed mapping rather than silently accepting a missing policy."""

    if not isinstance(value, dict):
        raise WorkerSmokeError(f"the target profile must declare {path}")
    return value


def required_string(value: Any, path: str) -> str:
    """Require one non-empty, source-governed string before an AWS call."""

    if not isinstance(value, str) or not value:
        raise WorkerSmokeError(f"the target profile must declare {path}")
    return value


def required_integer(value: Any, path: str) -> int:
    """Require a whole source-governed integer before a bounded comparison."""

    if not isinstance(value, int):
        raise WorkerSmokeError(f"the target profile must declare integer {path}")
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract the one reviewed queue, worker, and harmless message policy."""

    runtime = mapping(profile.get("runtime"), "runtime")
    worker = mapping(runtime.get("worker"), "runtime.worker")
    cloud = mapping(profile.get("cloud"), "cloud")
    aws = mapping(profile.get("aws"), "aws")
    operations = mapping(profile.get("operations"), "operations")
    closure = mapping(operations.get("readiness_closure"), "operations.readiness_closure")
    proof = mapping(closure.get("worker_consumer"), "operations.readiness_closure.worker_consumer")
    preconditions = mapping(proof.get("preconditions"), "operations.readiness_closure.worker_consumer.preconditions")
    action = mapping(proof.get("bounded_action"), "operations.readiness_closure.worker_consumer.bounded_action")
    success = mapping(proof.get("success"), "operations.readiness_closure.worker_consumer.success")
    queue = mapping(worker.get("queue"), "runtime.worker.queue")

    expected = {
        "status": "source-defined-deployment-pending",
        "command": "npm run platform:shell:worker-smoke",
        "execution_guard": "--execute-and-approve-live-worker-smoke",
        "proof": "one-side-effect-free-direct-sqs-platform-smoke-rebuild-message-through-the-dormant-worker-service",
        "safe_result": "status-counts-duration-and-task-revision-only-no-message-body-id-receipt-queue-url-or-provider-payload",
        "limitation": "direct-consumer-proof-only-not-a-producer-transaction-outbox-or-durable-business-idempotency-proof",
    }
    for key, expected_value in expected.items():
        if proof.get(key) != expected_value:
            raise WorkerSmokeError("the target profile worker proof policy no longer matches the reviewed bounded shape")
    if preconditions != {
        "worker_desired_count": 0,
        "worker_running_count": 0,
        "source_queue_visible_messages": 0,
        "dead_letter_queue_visible_messages": 0,
    }:
        raise WorkerSmokeError("the target profile worker proof preconditions are no longer zero-state only")
    if action.get("worker_desired_count") != 1 or action.get("message_type") != "platform-smoke.rebuild" or action.get("payload") != '{"rebuild":true}' or action.get("maximum_wait_seconds") != 360 or action.get("metric_export_settlement_wait_seconds") != 75:
        raise WorkerSmokeError("the target profile worker proof action is no longer the reviewed harmless one-message shape")
    if success != {
        "worker_started": True,
        "source_queue_visible_messages": 0,
        "dead_letter_queue_visible_messages": 0,
        "cleanup_worker_desired_count": 0,
    }:
        raise WorkerSmokeError("the target profile worker proof success conditions are no longer the reviewed cleanup shape")

    return {
        "account_id": required_string(cloud.get("account_id"), "cloud.account_id"),
        "aws_profile": required_string(cloud.get("profile"), "cloud.profile"),
        "region": required_string(cloud.get("region"), "cloud.region"),
        "cluster": required_string(aws.get("cluster"), "aws.cluster"),
        "worker_service": required_string(worker.get("service"), "runtime.worker.service"),
        "source_queue_name": required_string(queue.get("source_queue"), "runtime.worker.queue.source_queue"),
        "dead_letter_queue_name": required_string(queue.get("dead_letter_queue"), "runtime.worker.queue.dead_letter_queue"),
        "maximum_wait_seconds": required_integer(action.get("maximum_wait_seconds"), "operations.readiness_closure.worker_consumer.bounded_action.maximum_wait_seconds"),
        "metric_export_settlement_wait_seconds": required_integer(action.get("metric_export_settlement_wait_seconds"), "operations.readiness_closure.worker_consumer.bounded_action.metric_export_settlement_wait_seconds"),
    }


def aws_arguments(policy: dict[str, Any], credential_source: str) -> list[str]:
    """Use only the selected profile or explicitly supplied environment credentials."""

    arguments = ["--region", policy["region"]]
    if credential_source == "target-profile":
        arguments.extend(["--profile", policy["aws_profile"]])
    return arguments


def run_aws(arguments: list[str], policy: dict[str, Any], aws_cli: str, credential_source: str) -> dict[str, Any]:
    """Call one fixed AWS API and keep every raw response only in process memory."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    if credential_source == "environment":
        environment.pop("AWS_PROFILE", None)
    result = subprocess.run([aws_cli, *arguments, *aws_arguments(policy, credential_source), "--output", "json"], check=False, capture_output=True, encoding="utf-8", env=environment)
    if result.returncode != 0:
        raise WorkerSmokeError("an approved AWS worker-proof operation did not complete")
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exception:
        raise WorkerSmokeError("an AWS worker-proof operation returned an unexpected response") from exception
    if not isinstance(response, dict):
        raise WorkerSmokeError("an AWS worker-proof operation must return an object")
    return response


def verify_account(policy: dict[str, Any], aws_cli: str, credential_source: str) -> None:
    """Fail closed before a mutable operation if credentials point to another account."""

    response = run_aws(["sts", "get-caller-identity"], policy, aws_cli, credential_source)
    if response.get("Account") != policy["account_id"]:
        raise WorkerSmokeError("the selected AWS identity is not the target account")


def queue_url(queue_name: str, policy: dict[str, Any], aws_cli: str, credential_source: str) -> str:
    """Resolve only the two reviewed queue names without printing either URL."""

    response = run_aws(["sqs", "get-queue-url", "--queue-name", queue_name], policy, aws_cli, credential_source)
    return required_string(response.get("QueueUrl"), "AWS queue URL response")


def queue_counts(url: str, policy: dict[str, Any], aws_cli: str, credential_source: str) -> dict[str, int]:
    """Read approximate queue counts used only as conservative smoke preconditions."""

    response = run_aws(["sqs", "get-queue-attributes", "--queue-url", url, "--attribute-names", "ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible"], policy, aws_cli, credential_source)
    attributes = response.get("Attributes")
    if not isinstance(attributes, dict):
        raise WorkerSmokeError("the approved queue count inspection returned no attributes")
    try:
        return {
            "visible": int(attributes.get("ApproximateNumberOfMessages", "-1")),
            "not_visible": int(attributes.get("ApproximateNumberOfMessagesNotVisible", "-1")),
        }
    except (TypeError, ValueError) as exception:
        raise WorkerSmokeError("the approved queue count inspection returned invalid counts") from exception


def service_state(policy: dict[str, Any], aws_cli: str, credential_source: str) -> dict[str, Any]:
    """Read desired/running worker state and retain only the safe task revision label."""

    response = run_aws(["ecs", "describe-services", "--cluster", policy["cluster"], "--services", policy["worker_service"]], policy, aws_cli, credential_source)
    services = response.get("services")
    if not isinstance(services, list) or len(services) != 1 or not isinstance(services[0], dict):
        raise WorkerSmokeError("the reviewed worker service was not found uniquely")
    service = services[0]
    task_definition = service.get("taskDefinition")
    if not isinstance(task_definition, str) or ":" not in task_definition:
        raise WorkerSmokeError("the worker service did not report a task definition")
    try:
        return {
            "desired": int(service.get("desiredCount")),
            "running": int(service.get("runningCount")),
            "task_revision": task_definition.rsplit(":", 1)[1],
        }
    except (TypeError, ValueError) as exception:
        raise WorkerSmokeError("the worker service returned invalid safe count values") from exception


def set_desired_count(value: int, policy: dict[str, Any], aws_cli: str, credential_source: str) -> None:
    """Set only the reviewed dormant worker service to zero or one task."""

    run_aws(["ecs", "update-service", "--cluster", policy["cluster"], "--service", policy["worker_service"], "--desired-count", str(value)], policy, aws_cli, credential_source)


def enqueue_smoke_message(url: str, policy: dict[str, Any], aws_cli: str, credential_source: str) -> None:
    """Send one fixed harmless envelope and never print its generated identity or payload."""

    message = {
        "type": "platform-smoke.rebuild",
        "version": 1,
        "enqueuedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "idempotencyKey": f"platform-smoke-worker-{uuid.uuid4()}",
        "payload": {"rebuild": True},
    }
    run_aws(["sqs", "send-message", "--queue-url", url, "--message-body", json.dumps(message, separators=(",", ":"))], policy, aws_cli, credential_source)


def wait_until(predicate: Any, timeout_seconds: int) -> bool:
    """Poll at a slow fixed cadence so the rehearsal remains bounded and inexpensive."""

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(10)
    return bool(predicate())


def wait_for_worker_metric_export(wait_seconds: int, policy: dict[str, Any], aws_cli: str, credential_source: str) -> None:
    """Keep the live worker up through one reviewed exporter interval, then fail closed if it stopped before cleanup."""

    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        time.sleep(min(10, max(0, deadline - time.monotonic())))
    if service_state(policy, aws_cli, credential_source)["running"] < 1:
        raise WorkerSmokeError("the worker stopped before its reviewed metric-export settlement wait completed")


def emit(result: str, **fields: int | str) -> None:
    """Emit only bounded aggregate evidence; never raw AWS, queue, task, or message details."""

    print(json.dumps({"worker_smoke": result, **fields}, separators=(",", ":"), sort_keys=True))


def execute(policy: dict[str, Any], aws_cli: str, credential_source: str, timeout_seconds: int) -> int:
    """Run the one-message proof and always return the worker service to its dormant state."""

    started = time.monotonic()
    source_url = ""
    dlq_url = ""
    worker_enabled = False
    cleanup_failed = False
    task_revision = "unknown"
    result = "inconclusive"
    failure_message = ""
    try:
        verify_account(policy, aws_cli, credential_source)
        source_url = queue_url(policy["source_queue_name"], policy, aws_cli, credential_source)
        dlq_url = queue_url(policy["dead_letter_queue_name"], policy, aws_cli, credential_source)
        before_worker = service_state(policy, aws_cli, credential_source)
        task_revision = before_worker["task_revision"]
        before_source = queue_counts(source_url, policy, aws_cli, credential_source)
        before_dlq = queue_counts(dlq_url, policy, aws_cli, credential_source)
        if before_worker["desired"] != 0 or before_worker["running"] != 0 or before_source["visible"] != 0 or before_source["not_visible"] != 0 or before_dlq["visible"] != 0 or before_dlq["not_visible"] != 0:
            raise WorkerSmokeError("worker or queue preconditions are not empty and dormant")

        enqueue_smoke_message(source_url, policy, aws_cli, credential_source)
        set_desired_count(1, policy, aws_cli, credential_source)
        worker_enabled = True

        def settled() -> bool:
            state = service_state(policy, aws_cli, credential_source)
            source = queue_counts(source_url, policy, aws_cli, credential_source)
            dlq = queue_counts(dlq_url, policy, aws_cli, credential_source)
            return state["running"] >= 1 and source["visible"] == 0 and source["not_visible"] == 0 and dlq["visible"] == 0 and dlq["not_visible"] == 0

        if not wait_until(settled, min(timeout_seconds, policy["maximum_wait_seconds"])):
            raise WorkerSmokeError("the bounded worker proof did not converge")
        wait_for_worker_metric_export(policy["metric_export_settlement_wait_seconds"], policy, aws_cli, credential_source)
        result = "passed"
    except WorkerSmokeError as exception:
        failure_message = str(exception)
    finally:
        if worker_enabled:
            try:
                set_desired_count(0, policy, aws_cli, credential_source)
                if not wait_until(lambda: service_state(policy, aws_cli, credential_source)["desired"] == 0 and service_state(policy, aws_cli, credential_source)["running"] == 0, timeout_seconds):
                    cleanup_failed = True
            except WorkerSmokeError:
                cleanup_failed = True
        if cleanup_failed:
            print("worker-smoke: worker cleanup did not reach the required dormant state", file=sys.stderr)

    duration_ms = round((time.monotonic() - started) * 1000)
    if cleanup_failed:
        emit("cleanup-failed", duration_ms=duration_ms, task_revision=task_revision)
        return 1
    if result == "passed":
        emit("passed", duration_ms=duration_ms, task_revision=task_revision)
        return 0
    emit("inconclusive", duration_ms=duration_ms, task_revision=task_revision)
    print(f"worker-smoke: {failure_message}", file=sys.stderr)
    return 1


def main() -> int:
    """Validate source or run the explicitly guarded live worker proof."""

    arguments = parse_arguments()
    policy = resolve_policy(load_profile(Path(arguments.target_profile)))
    if arguments.validate:
        emit("validated", maximum_wait_seconds=policy["maximum_wait_seconds"], metric_export_settlement_wait_seconds=policy["metric_export_settlement_wait_seconds"])
        return 0
    return execute(policy, arguments.aws_cli, arguments.aws_credential_source, arguments.timeout_seconds)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkerSmokeError as exception:
        print(f"worker-smoke: {exception}", file=sys.stderr)
        raise SystemExit(1)
