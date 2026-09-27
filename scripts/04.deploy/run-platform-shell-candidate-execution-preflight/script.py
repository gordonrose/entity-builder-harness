#!/usr/bin/env python3
"""Prove one immutable staging candidate can start before any service promotion."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-candidate-execution-preflight
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Run one isolated, non-routable candidate task with the live server network and report only a safe verdict.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network
#   used_by:
#   - id: deploy.script.run-platform-shell-candidate-execution-preflight.wrapper
#     path: scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.sh

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
CLUSTER = "arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-staging"
SOURCE_SERVICE = "kanbien-staging-platform-shell"
SAFE_RESULT_SCHEMA = "deploy/platform-shell-candidate-execution-preflight-result/v1"
IMMUTABLE_IMAGE = re.compile(r"^.+@sha256:([0-9a-f]{64})$")


class CandidatePreflightError(Exception):
    """Represent one allowlisted safe result without retaining provider output."""


def parse_arguments() -> argparse.Namespace:
    """Accept no caller-selected target, image, network, task, label, or timing input."""

    parser = argparse.ArgumentParser(description="Validate or run the one Kanbien staging candidate execution preflight.")
    parser.add_argument("--validate", action="store_true", help="Validate committed source only; make no AWS call.")
    parser.add_argument("--execute", action="store_true", help="Run exactly one derived-label candidate task and clean it up.")
    parser.add_argument("--approve-candidate-execution-preflight", action="store_true", help="Acknowledge the one isolated candidate task start and controlled stop.")
    result = parser.parse_args()
    if sum((result.validate, result.execute)) != 1:
        parser.error("choose exactly one validation or execution mode")
    if result.validate and result.approve_candidate_execution_preflight:
        parser.error("the execution approval guard is unavailable in validation mode")
    if result.execute and not result.approve_candidate_execution_preflight:
        parser.error("the fixed candidate execution preflight requires --approve-candidate-execution-preflight")
    return result


def mapping(value: Any, code: str) -> dict[str, Any]:
    """Require one reviewed mapping rather than silently adopting a default."""

    if not isinstance(value, dict):
        raise CandidatePreflightError(code)
    return value


def text(value: Any, code: str) -> str:
    """Require a finite reviewed string."""

    if not isinstance(value, str) or not value:
        raise CandidatePreflightError(code)
    return value


def load_policy() -> dict[str, Any]:
    """Read only the one committed target policy and fail closed on drift."""

    try:
        import yaml
        source = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception as exception:
        raise CandidatePreflightError("candidate-preflight-policy-unavailable") from exception
    root = mapping(source, "candidate-preflight-target-profile-invalid")
    cloud = mapping(root.get("cloud"), "candidate-preflight-cloud-policy-missing")
    deployment = mapping(root.get("deployment"), "candidate-preflight-deployment-policy-missing")
    control = mapping(deployment.get("candidate_execution_preflight"), "candidate-preflight-control-missing")
    if cloud.get("account_id") != ACCOUNT or cloud.get("region") != REGION or text(cloud.get("profile"), "candidate-preflight-profile-missing") != "kanbien-dev":
        raise CandidatePreflightError("candidate-preflight-target-not-reviewed")
    expected = {
        "status": "source-ready-dormant-task-boundary-not-yet-deployed",
        "command": "npm-run-platform-shell-candidate-execution-preflight",
        "execution_guard": "execute-and-approve-candidate-execution-preflight",
        "realization_contract": "infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/candidate-execution-preflight.v1.yml",
        "service_stack": "kanbien-staging-platform-shell-service",
        "source_service": SOURCE_SERVICE,
        "candidate_task_definition_output": "CandidatePreflightTaskDefinitionArn",
        "candidate_task_family": "kanbien-staging-platform-shell-candidate-preflight",
        "application_container": "platform-shell",
        "runtime_network": "exact-active-server-awsvpc-configuration-without-service-listener-or-load-balancer-attachment",
        "candidate_label": "derived-from-immutable-image-digest-and-not-caller-selectable",
        "maximum_start_seconds": 300,
        "maximum_stop_seconds": 120,
        "successful_task_state": "running-and-healthy-before-controlled-stop",
        "final_state": "stopped-with-no-running-task-for-derived-label",
        "output_policy": "safe-verdict-and-allowlisted-failure-category-only-no-provider-response-task-identifier-endpoint-log-message-or-runtime-value",
    }
    if control != expected or not Path(expected["realization_contract"]).is_file():
        raise CandidatePreflightError("candidate-preflight-control-not-reviewed")
    return {
        "profile": cloud["profile"],
        "service_stack": expected["service_stack"],
        "source_service": expected["source_service"],
        "candidate_task_definition_output": expected["candidate_task_definition_output"],
        "candidate_task_family": expected["candidate_task_family"],
        "application_container": expected["application_container"],
        "maximum_start_seconds": expected["maximum_start_seconds"],
        "maximum_stop_seconds": expected["maximum_stop_seconds"],
    }


def aws(arguments: list[str], policy: dict[str, Any], failure_code: str) -> dict[str, Any]:
    """Call exactly one AWS operation while retaining raw provider data only in memory."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    try:
        result = subprocess.run(
            ["aws", *arguments, "--profile", policy["profile"], "--region", REGION, "--output", "json"],
            capture_output=True,
            check=False,
            encoding="utf-8",
            env=environment,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exception:
        raise CandidatePreflightError(failure_code) from exception
    if result.returncode != 0:
        raise CandidatePreflightError(failure_code)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exception:
        raise CandidatePreflightError(failure_code) from exception
    if not isinstance(payload, dict):
        raise CandidatePreflightError(failure_code)
    return payload


def verify_account(policy: dict[str, Any]) -> None:
    """Refuse all execution outside the reviewed staging account."""

    if aws(["sts", "get-caller-identity"], policy, "candidate-account-verification-unavailable").get("Account") != ACCOUNT:
        raise CandidatePreflightError("candidate-account-mismatch")


def candidate_task_definition(policy: dict[str, Any]) -> str:
    """Resolve only the reviewed dormant task-definition output from a stable service stack."""

    payload = aws(["cloudformation", "describe-stacks", "--stack-name", policy["service_stack"]], policy, "candidate-service-stack-inspection-unavailable")
    stacks = payload.get("Stacks")
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict) or stacks[0].get("StackStatus") != "UPDATE_COMPLETE":
        raise CandidatePreflightError("candidate-service-stack-not-stable")
    outputs = {
        item.get("OutputKey"): item.get("OutputValue")
        for item in stacks[0].get("Outputs", [])
        if isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str)
    }
    value = outputs.get(policy["candidate_task_definition_output"])
    if not isinstance(value, str) or not value:
        raise CandidatePreflightError("candidate-task-definition-not-deployed")
    return value


def active_server(policy: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Require one healthy live server and return its exact awsvpc topology in memory."""

    payload = aws(["ecs", "describe-services", "--cluster", CLUSTER, "--services", policy["source_service"]], policy, "candidate-source-service-inspection-unavailable")
    services = payload.get("services")
    if not isinstance(services, list) or len(services) != 1 or not isinstance(services[0], dict):
        raise CandidatePreflightError("candidate-source-service-not-unique")
    service = services[0]
    if service.get("serviceName") != policy["source_service"] or service.get("desiredCount") != 1 or service.get("runningCount") != 1:
        raise CandidatePreflightError("candidate-source-service-not-healthy")
    task_definition = service.get("taskDefinition")
    network = mapping(mapping(service.get("networkConfiguration"), "candidate-source-network-missing").get("awsvpcConfiguration"), "candidate-source-awsvpc-network-missing")
    subnets = network.get("subnets")
    groups = network.get("securityGroups")
    if not isinstance(task_definition, str) or not task_definition or network.get("assignPublicIp") != "ENABLED" or not isinstance(subnets, list) or not subnets or not all(isinstance(item, str) and item for item in subnets) or not isinstance(groups, list) or not groups or not all(isinstance(item, str) and item for item in groups):
        raise CandidatePreflightError("candidate-source-network-not-reviewed")
    return task_definition, {"awsvpcConfiguration": {"assignPublicIp": "ENABLED", "subnets": subnets, "securityGroups": groups}}


def task_definition(reference: str, policy: dict[str, Any], failure_code: str) -> dict[str, Any]:
    """Read one task definition solely for exact in-memory equivalence checks."""

    payload = aws(["ecs", "describe-task-definition", "--task-definition", reference], policy, failure_code)
    return mapping(payload.get("taskDefinition"), failure_code)


def canonical_task_shape(definition: dict[str, Any], application_container: str) -> dict[str, Any]:
    """Retain every execution-relevant task field while removing only image identity."""

    containers = definition.get("containerDefinitions")
    if not isinstance(containers, list):
        raise CandidatePreflightError("candidate-task-definition-invalid")
    canonical_containers: list[dict[str, Any]] = []
    found_application = False
    for item in containers:
        if not isinstance(item, dict):
            raise CandidatePreflightError("candidate-task-definition-invalid")
        normalized = dict(item)
        if normalized.get("name") == application_container:
            image = normalized.get("image")
            if not isinstance(image, str) or not IMMUTABLE_IMAGE.fullmatch(image):
                raise CandidatePreflightError("candidate-image-not-immutable")
            normalized["image"] = "<immutable-candidate-image>"
            found_application = True
        canonical_containers.append(normalized)
    if not found_application:
        raise CandidatePreflightError("candidate-application-container-missing")
    return {
        "cpu": definition.get("cpu"),
        "memory": definition.get("memory"),
        "networkMode": definition.get("networkMode"),
        "requiresCompatibilities": definition.get("requiresCompatibilities"),
        "runtimePlatform": definition.get("runtimePlatform"),
        "executionRoleArn": definition.get("executionRoleArn"),
        "taskRoleArn": definition.get("taskRoleArn"),
        "containerDefinitions": canonical_containers,
    }


def candidate_image(definition: dict[str, Any], application_container: str) -> str:
    """Extract only the exact immutable candidate reference from its reviewed container."""

    containers = definition.get("containerDefinitions")
    if not isinstance(containers, list):
        raise CandidatePreflightError("candidate-task-definition-invalid")
    for item in containers:
        if isinstance(item, dict) and item.get("name") == application_container:
            image = item.get("image")
            if isinstance(image, str) and IMMUTABLE_IMAGE.fullmatch(image):
                return image
    raise CandidatePreflightError("candidate-image-not-immutable")


def verify_candidate_shape(candidate: dict[str, Any], server: dict[str, Any], policy: dict[str, Any]) -> str:
    """Require an exact server mirror except for the immutable candidate image and family."""

    if candidate.get("family") != policy["candidate_task_family"]:
        raise CandidatePreflightError("candidate-task-family-not-reviewed")
    candidate_shape = canonical_task_shape(candidate, policy["application_container"])
    server_shape = canonical_task_shape(server, policy["application_container"])
    if candidate_shape != server_shape:
        raise CandidatePreflightError("candidate-task-shape-drift")
    return candidate_image(candidate, policy["application_container"])


def attempt_label(image: str) -> str:
    """Derive an unselectable, bounded ECS started-by value from one image digest."""

    digest = IMMUTABLE_IMAGE.fullmatch(image)
    if digest is None:
        raise CandidatePreflightError("candidate-image-not-immutable")
    return f"kb-candidate-{hashlib.sha256(digest.group(1).encode('ascii')).hexdigest()[:20]}"


def labelled_tasks(label: str, desired_state: str, policy: dict[str, Any]) -> list[str]:
    """Read task identifiers only in memory to enforce one terminal attempt per digest."""

    payload = aws(["ecs", "list-tasks", "--cluster", CLUSTER, "--started-by", label, "--desired-status", desired_state], policy, "candidate-attempt-inspection-unavailable")
    tasks = payload.get("taskArns")
    if not isinstance(tasks, list) or not all(isinstance(item, str) for item in tasks):
        raise CandidatePreflightError("candidate-attempt-inspection-invalid")
    return tasks


def assert_fresh_attempt(label: str, policy: dict[str, Any]) -> None:
    """Reject a replay of any candidate whose prior attempt has started or stopped."""

    if labelled_tasks(label, "RUNNING", policy) or labelled_tasks(label, "STOPPED", policy):
        raise CandidatePreflightError("candidate-attempt-label-consumed")


def run_candidate(reference: str, label: str, network: dict[str, Any], policy: dict[str, Any]) -> str:
    """Start one Fargate task with the active server network and no service attachment."""

    payload = aws([
        "ecs", "run-task", "--cluster", CLUSTER, "--task-definition", reference, "--launch-type", "FARGATE", "--count", "1",
        "--network-configuration", json.dumps(network, separators=(",", ":")), "--started-by", label,
    ], policy, "candidate-run-task-admission-failure")
    tasks = payload.get("tasks")
    failures = payload.get("failures")
    if not isinstance(tasks, list) or len(tasks) != 1 or failures or not isinstance(tasks[0], dict) or not isinstance(tasks[0].get("taskArn"), str):
        raise CandidatePreflightError("candidate-run-task-admission-failure")
    return tasks[0]["taskArn"]


def terminal_category(task: dict[str, Any]) -> str:
    """Classify a terminal task only into reviewed operational categories."""

    reasons = [str(item.get("reason", "")) for item in task.get("containers", []) if isinstance(item, dict)]
    combined = " ".join(reasons)
    if "CannotPullContainer" in combined:
        return "candidate-image-distribution-failure"
    if "ResourceInitializationError" in combined:
        return "candidate-runtime-initialization-failure"
    if task.get("stopCode") == "TaskFailedToStart":
        return "candidate-task-startup-failure"
    return "candidate-runtime-startup-failure"


def wait_for_healthy(task_arn: str, policy: dict[str, Any]) -> None:
    """Require RUNNING plus ECS HEALTHY before the controller asks the task to stop."""

    deadline = time.monotonic() + policy["maximum_start_seconds"]
    while time.monotonic() < deadline:
        payload = aws(["ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", task_arn], policy, "candidate-task-inspection-unavailable")
        tasks = payload.get("tasks")
        if not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict):
            raise CandidatePreflightError("candidate-task-inspection-invalid")
        task = tasks[0]
        if task.get("lastStatus") == "STOPPED":
            raise CandidatePreflightError(terminal_category(task))
        if task.get("lastStatus") == "RUNNING" and task.get("healthStatus") == "HEALTHY":
            return
        time.sleep(5)
    raise CandidatePreflightError("candidate-health-timeout")


def stop_and_wait(task_arn: str, policy: dict[str, Any]) -> None:
    """Always clean up an accepted task and prove it no longer runs."""

    aws(["ecs", "stop-task", "--cluster", CLUSTER, "--task", task_arn, "--reason", "controlled-candidate-preflight-complete"], policy, "candidate-cleanup-request-failure")
    deadline = time.monotonic() + policy["maximum_stop_seconds"]
    while time.monotonic() < deadline:
        payload = aws(["ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", task_arn], policy, "candidate-cleanup-inspection-failure")
        tasks = payload.get("tasks")
        if not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict):
            raise CandidatePreflightError("candidate-cleanup-inspection-invalid")
        if tasks[0].get("lastStatus") == "STOPPED":
            return
        time.sleep(5)
    raise CandidatePreflightError("candidate-cleanup-timeout")


def safe_result(verdict: str, category: str | None = None) -> str:
    """Produce the only permitted external evidence shape."""

    result: dict[str, str] = {"schema": SAFE_RESULT_SCHEMA, "candidate_execution_preflight": verdict}
    if category is not None:
        result["failure_category"] = category
    return json.dumps(result, sort_keys=True)


def execute(policy: dict[str, Any]) -> int:
    """Perform the bounded start-health-stop proof and never print raw runtime data."""

    accepted_task: str | None = None
    try:
        verify_account(policy)
        candidate_reference = candidate_task_definition(policy)
        server_reference, network = active_server(policy)
        candidate = task_definition(candidate_reference, policy, "candidate-task-definition-inspection-unavailable")
        server = task_definition(server_reference, policy, "candidate-source-task-definition-inspection-unavailable")
        image = verify_candidate_shape(candidate, server, policy)
        label = attempt_label(image)
        assert_fresh_attempt(label, policy)
        accepted_task = run_candidate(candidate_reference, label, network, policy)
        wait_for_healthy(accepted_task, policy)
        stop_and_wait(accepted_task, policy)
        if labelled_tasks(label, "RUNNING", policy):
            raise CandidatePreflightError("candidate-cleanup-incomplete")
        print(safe_result("passed"))
        return 0
    except CandidatePreflightError as exception:
        category = str(exception)
        if accepted_task is not None:
            try:
                stop_and_wait(accepted_task, policy)
            except CandidatePreflightError:
                category = "candidate-cleanup-failure"
        print(safe_result("failed", category))
        return 1


def main() -> int:
    """Dispatch source validation or the one explicit candidate execution."""

    arguments = parse_arguments()
    try:
        policy = load_policy()
        if arguments.validate:
            print(safe_result("validated"))
            return 0
        return execute(policy)
    except CandidatePreflightError as exception:
        print(safe_result("failed", str(exception)))
        return 1


if __name__ == "__main__":
    sys.exit(main())
