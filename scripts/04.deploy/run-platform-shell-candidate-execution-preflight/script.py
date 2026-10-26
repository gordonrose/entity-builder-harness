#!/usr/bin/env python3
"""Prove one immutable staging candidate can start before any service promotion."""

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.run-platform-shell-candidate-execution-preflight
#   version: 2
#   status: active
#   created_on: "2026-09-27"
#   updated_on: "2026-10-26"
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
from contextlib import contextmanager
import fcntl
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any


PROFILE_PATH = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
ACCOUNT = "337159794548"
REGION = "eu-west-1"
CLUSTER = "arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-staging"
SOURCE_SERVICE = "kanbien-staging-platform-shell"
SAFE_RESULT_SCHEMA = "deploy/platform-shell-candidate-execution-preflight-result/v1"
IMMUTABLE_IMAGE = re.compile(r"^.+@sha256:([0-9a-f]{64})$")
ACTIVE_CANDIDATE: tuple[str, dict[str, Any]] | None = None


class CandidatePreflightError(Exception):
    """Represent one allowlisted safe result without retaining provider output."""


def durable_ledger_path(filename: str) -> Path:
    """Keep restart receipts in the repository common directory, never a /tmp worktree."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            check=True,
            cwd=Path.cwd(),
            text=True,
            timeout=5,
        )
        common = Path(result.stdout.strip())
    except (OSError, subprocess.SubprocessError) as exception:
        raise CandidatePreflightError("candidate-durable-ledger-location-unavailable") from exception
    if not common.is_absolute() or common.name != ".git":
        raise CandidatePreflightError("candidate-durable-ledger-location-unavailable")
    return common / "postgresql-stage6-receipts" / filename


DEFAULT_CANDIDATE_LEDGER_PATH = durable_ledger_path("candidate-attempts.json")


def parse_arguments() -> argparse.Namespace:
    """Accept no caller-selected target, image, network, task, label, or timing input."""

    parser = argparse.ArgumentParser(description="Validate or run the one Kanbien staging candidate execution preflight.")
    parser.add_argument("--validate", action="store_true", help="Validate committed source only; make no AWS call.")
    parser.add_argument("--execute", action="store_true", help="Run exactly one derived-label candidate task and clean it up.")
    parser.add_argument("--reconcile", action="store_true", help="Observe unresolved retained attempts without submitting or stopping tasks.")
    parser.add_argument("--cleanup", action="store_true", help="Stop only an unresolved retained task with its original definition and label.")
    parser.add_argument("--approve-candidate-execution-preflight", action="store_true", help="Acknowledge the one isolated candidate task start and controlled stop.")
    parser.add_argument("--realization-facts",type=Path)
    parser.add_argument("--realization-change-summary",type=Path)
    result = parser.parse_args()
    if sum((result.validate, result.execute,result.reconcile,result.cleanup)) != 1:
        parser.error("choose exactly one validation, execution, reconciliation or cleanup mode")
    if (result.validate or result.reconcile) and result.approve_candidate_execution_preflight:
        parser.error("the execution approval guard is unavailable in validation mode")
    if (result.execute or result.cleanup) and not result.approve_candidate_execution_preflight:
        parser.error("the fixed candidate execution preflight requires --approve-candidate-execution-preflight")
    if result.execute and (result.realization_facts is None or result.realization_change_summary is None):parser.error("candidate execution requires normalized realization facts and change summary")
    if not result.execute and (result.realization_facts is not None or result.realization_change_summary is not None):parser.error("execution evidence is unavailable in validation mode")
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
        "status": "dormant-task-boundary-deployed-finite-same-image-attempts-require-durable-reconciliation",
        "command": "npm-run-platform-shell-candidate-execution-preflight",
        "entrypoint":"scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.sh",
        "execution_guard": "execute-and-approve-candidate-execution-preflight",
        "realization_contract": "infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/candidate-execution-preflight.v1.yml",
        "service_stack": "kanbien-staging-platform-shell-service",
        "source_service": SOURCE_SERVICE,
        "candidate_task_definition_output": "CandidatePreflightTaskDefinitionArn",
        "candidate_task_family": "kanbien-staging-platform-shell-candidate-preflight",
        "application_container": "platform-shell",
        "runtime_network": "exact-active-server-awsvpc-configuration-without-service-listener-or-load-balancer-attachment",
        "candidate_label": "derived-from-immutable-image-digest-and-finite-durable-attempt-number-not-caller-selectable",
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


def realization_preflight(facts_path=None, summary_path=None):
    """Consume the authoritative compiler, including input/freshness bindings."""
    root=Path(__file__).resolve().parents[3]
    spec=importlib.util.spec_from_file_location("realization",root/"scripts/04.deploy/operational-realization-gate/script.py")
    compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
    try:
        contract=compiler.load_yaml(root/"infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/candidate-execution-preflight.v1.yml","contract-unreadable")
        identifier=compiler.validate_contract(contract)
        if facts_path is None:return None
        facts=compiler.load_yaml(facts_path,"normalized-facts-unreadable")
        _,known=compiler.ids(contract)
        compiler.validate_facts(facts,contract,identifier,known,"execution-preflight")
        compiler.validate_change_summary(compiler.load_yaml(summary_path,"normalized-change-summary-unreadable"),contract,identifier,facts)
        bindings=[item for item in facts.get("artifact_bindings",[]) if item.get("component_id")=="candidate-runtime-artifact"]
        if len(bindings)!=1:raise CandidatePreflightError("candidate-realization-artifact-binding-invalid")
        return bindings[0]["immutable_reference"]
    except compiler.ContractFailure as error:
        raise CandidatePreflightError("candidate-realization-"+error.code) from error


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


def candidate_admission_category(raw_reason: str) -> str:
    """Reduce a RunTask rejection to one reviewed category without retaining it."""

    reason = raw_reason.lower()
    if any(token in reason for token in ("accessdenied", "access denied", "not authorized", "iam:passrole", "pass role")):
        return "candidate-run-task-authorization-failure"
    if any(token in reason for token in ("security group", "securitygroup", "subnet", "assignpublicip", "network configuration", "eni")):
        return "candidate-run-task-network-configuration-failure"
    if any(token in reason for token in ("resource:cpu", "resource:memory", "capacity", "placement", "attribute")):
        return "candidate-run-task-capacity-or-placement-failure"
    if any(token in reason for token in ("task definition", "taskdefinition", "launch type", "fargate", "platform version", "runtimeplatform")):
        return "candidate-run-task-definition-or-launch-contract-failure"
    return "candidate-run-task-provider-rejection-unclassified"


def run_task_payload(arguments: list[str], policy: dict[str, Any]) -> dict[str, Any]:
    """Call ECS RunTask and classify only its in-memory rejection cause."""

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
        raise CandidatePreflightError("candidate-run-task-request-unavailable") from exception
    if result.returncode != 0:
        raise CandidatePreflightError(candidate_admission_category(result.stderr))
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exception:
        raise CandidatePreflightError("candidate-run-task-invalid-response") from exception
    if not isinstance(payload, dict):
        raise CandidatePreflightError("candidate-run-task-invalid-response")
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


def attempt_label(image: str, attempt: int = 1) -> str:
    """Bind a finite attempt identity to an immutable image without requiring a new image."""

    digest = IMMUTABLE_IMAGE.fullmatch(image)
    if digest is None or not 1 <= attempt <= 4:
        raise CandidatePreflightError("candidate-image-not-immutable")
    return f"kb-candidate-{hashlib.sha256(digest.group(1).encode('ascii')).hexdigest()[:16]}-a{attempt}"


def load_candidate_ledger(path: Path = DEFAULT_CANDIDATE_LEDGER_PATH) -> dict[str, Any]:
    """Reload safe candidate receipts so a process restart cannot reset attempts."""

    if not path.exists():
        return {"schema": "postgresql-candidate-attempt-ledger/v1", "attempts": []}
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exception:
        raise CandidatePreflightError("candidate-attempt-ledger-unreadable") from exception
    if ledger.get("schema") != "postgresql-candidate-attempt-ledger/v1" or not isinstance(ledger.get("attempts"), list):
        raise CandidatePreflightError("candidate-attempt-ledger-invalid")
    allowed={"reserved","submitted","uncertain","rejected","succeeded","failed","stopped-reconciled"}
    entries=ledger["attempts"]
    if any(not isinstance(item,dict) or item.get("state") not in allowed or not isinstance(item.get("label"),str) or re.fullmatch(r"kb-candidate-[a-f0-9]{16}-a[1-4]",item["label"]) is None or not isinstance(item.get("image_hash"),str) for item in entries) or len({item["label"] for item in entries})!=len(entries):raise CandidatePreflightError("candidate-attempt-ledger-invalid")
    return ledger


def save_candidate_ledger(ledger: dict[str, Any], path: Path = DEFAULT_CANDIDATE_LEDGER_PATH) -> None:
    """Atomically retain safe attempt receipts without task identifiers."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".postgresql-candidate-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(ledger, output, sort_keys=True, separators=(",", ":"))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_name, path)
    except OSError as exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise CandidatePreflightError("candidate-attempt-ledger-write-failed") from exception


@contextmanager
def candidate_ledger_lock(path: Path):
    """Serialize this owner's safe receipt transactions across local processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path.with_suffix(path.suffix + ".lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    except OSError as error:
        raise CandidatePreflightError("candidate-attempt-ledger-lock-unavailable") from error
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise CandidatePreflightError("candidate-attempt-ledger-busy") from error
        yield
    finally:
        os.close(descriptor)


def reserve_candidate_attempt(image: str, path: Path = DEFAULT_CANDIDATE_LEDGER_PATH, task_definition: str | None = None) -> str:
    """Reserve at most four same-image candidate attempts across restarts."""

    digest = IMMUTABLE_IMAGE.fullmatch(image)
    if digest is None:
        raise CandidatePreflightError("candidate-image-not-immutable")
    with candidate_ledger_lock(path):
        ledger = load_candidate_ledger(path)
        image_hash = hashlib.sha256(digest.group(1).encode("ascii")).hexdigest()[:16]
        attempts = [item for item in ledger["attempts"] if isinstance(item, dict) and item.get("image_hash") == image_hash]
        if any(item["state"] not in {"succeeded","failed","stopped-reconciled"} for item in ledger["attempts"]):raise CandidatePreflightError("candidate-prior-attempt-reconciliation-required")
        if len(attempts) >= 4:
            raise CandidatePreflightError("candidate-attempt-limit-exhausted")
        label = attempt_label(image, len(attempts) + 1)
        ledger["attempts"].append({"image_hash": image_hash, "label": label, "state": "reserved", "reserved_at": time.time(), "task_definition":task_definition})
        save_candidate_ledger(ledger, path)
        return label


def record_candidate_state(label: str, state: str, path: Path = DEFAULT_CANDIDATE_LEDGER_PATH) -> None:
    """Record a safe terminal or uncertain result before another same-image attempt."""

    with candidate_ledger_lock(path):
        ledger = load_candidate_ledger(path)
        receipt = next((item for item in ledger["attempts"] if isinstance(item, dict) and item.get("label") == label), None)
        if not isinstance(receipt, dict):
            raise CandidatePreflightError("candidate-attempt-receipt-missing")
        receipt["state"] = state
        receipt["updated_at"] = time.time()
        save_candidate_ledger(ledger, path)


def labelled_tasks(label: str, desired_state: str, policy: dict[str, Any]) -> list[str]:
    """Enumerate a bounded family, then match startedBy; AWS forbids mixed filters."""
    payload=aws(["ecs","list-tasks","--cluster",CLUSTER,"--family",policy.get("candidate_task_family","kanbien-staging-platform-shell-candidate-preflight"),"--desired-status",desired_state],policy,"candidate-attempt-inspection-unavailable")
    arns=payload.get("taskArns")
    if not isinstance(arns,list) or payload.get("nextToken") or not all(isinstance(item,str) for item in arns):raise CandidatePreflightError("candidate-attempt-inspection-invalid")
    found=[]
    for offset in range(0,len(arns),100):
        batch=arns[offset:offset+100]
        response=aws(["ecs","describe-tasks","--cluster",CLUSTER,"--tasks",*batch],policy,"candidate-attempt-inspection-unavailable")
        tasks=response.get("tasks")
        if not isinstance(tasks,list) or response.get("failures") or len(tasks)!=len(batch) or any(not isinstance(item,dict) for item in tasks) or {item.get("taskArn") for item in tasks}!=set(batch):raise CandidatePreflightError("candidate-attempt-inspection-invalid")
        found.extend(item["taskArn"] for item in tasks if item.get("startedBy")==label)
    return found


def reconcile_attempts(policy: dict[str,Any], *, cleanup: bool=False) -> int:
    """Never replace an unresolved submission; absence remains uncertain."""
    ledger=load_candidate_ledger()
    unresolved=[item for item in ledger["attempts"] if item["state"] not in {"succeeded","failed","stopped-reconciled"}]
    if not unresolved:
        print(safe_result("reconciled","candidate-no-unresolved-attempts"));return 0
    for item in unresolved:
        definition=item.get("task_definition")
        if not isinstance(definition,str) or not definition:raise CandidatePreflightError("candidate-prior-definition-unavailable")
        arns=list(dict.fromkeys(labelled_tasks(item["label"],"RUNNING",policy)+labelled_tasks(item["label"],"STOPPED",policy)))
        if len(arns)!=1:raise CandidatePreflightError("candidate-prior-submission-uncertain")
        payload=aws(["ecs","describe-tasks","--cluster",CLUSTER,"--tasks",arns[0]],policy,"candidate-attempt-inspection-unavailable")
        tasks=payload.get("tasks")
        if not isinstance(tasks,list) or len(tasks)!=1 or payload.get("failures") or not isinstance(tasks[0],dict):raise CandidatePreflightError("candidate-attempt-inspection-invalid")
        task=tasks[0]
        if task.get("taskArn")!=arns[0] or task.get("startedBy")!=item["label"] or task.get("taskDefinitionArn")!=definition:raise CandidatePreflightError("candidate-prior-task-identity-mismatch")
        status=task.get("lastStatus")
        if status in {"PROVISIONING","PENDING","ACTIVATING","RUNNING","DEACTIVATING","STOPPING","DEPROVISIONING"}:
            if not cleanup:
                print(safe_result("pending","candidate-prior-task-still-running"));return 1
            stop_and_wait(arns[0],policy)
        elif status!="STOPPED":raise CandidatePreflightError("candidate-prior-task-state-uncertain")
        record_candidate_state(item["label"],"stopped-reconciled")
    print(safe_result("cleaned-up" if cleanup else "reconciled","candidate-prior-attempts-stopped-not-qualified"));return 0


def assert_fresh_attempt(label: str, policy: dict[str, Any]) -> None:
    """Reject a replay of any candidate whose prior attempt has started or stopped."""

    if labelled_tasks(label, "RUNNING", policy) or labelled_tasks(label, "STOPPED", policy):
        raise CandidatePreflightError("candidate-attempt-label-consumed")


def run_candidate(reference: str, label: str, network: dict[str, Any], policy: dict[str, Any]) -> str:
    """Start one Fargate task with the active server network and no service attachment."""

    payload = run_task_payload([
        "ecs", "run-task", "--cluster", CLUSTER, "--task-definition", reference, "--launch-type", "FARGATE", "--count", "1",
        "--network-configuration", json.dumps(network, separators=(",", ":")), "--started-by", label, "--client-token", label,
    ], policy)
    tasks = payload.get("tasks")
    failures = payload.get("failures")
    if not isinstance(tasks, list) or len(tasks) != 1 or failures or not isinstance(tasks[0], dict) or not isinstance(tasks[0].get("taskArn"), str):
        reasons = " ".join(
            str(item.get("reason", ""))
            for item in failures
            if isinstance(item, dict)
        ) if isinstance(failures, list) else ""
        raise CandidatePreflightError(candidate_admission_category(reasons))
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


def cleanup_active_candidate() -> None:
    """Best-effort cleanup for an accepted task when the controller is interrupted."""

    global ACTIVE_CANDIDATE
    active = ACTIVE_CANDIDATE
    ACTIVE_CANDIDATE = None
    if active is None:
        return
    task_arn, policy = active
    stop_and_wait(task_arn, policy)


def interrupted(_signal_number: int, _frame: Any) -> None:
    """Stop an accepted task before surfacing a controlled interruption result."""

    try:
        cleanup_active_candidate()
    except CandidatePreflightError as exception:
        raise CandidatePreflightError("candidate-cleanup-failure") from exception
    raise CandidatePreflightError("candidate-execution-interrupted")


def safe_result(verdict: str, category: str | None = None, secondary: str | None = None) -> str:
    """Produce the only permitted external evidence shape."""

    result: dict[str, str] = {"schema": SAFE_RESULT_SCHEMA, "candidate_execution_preflight": verdict}
    if category is not None:
        result["failure_category"] = category
    if secondary is not None:result["secondary_failure_category"]=secondary
    return json.dumps(result, sort_keys=True)


def execute(policy: dict[str, Any]) -> int:
    """Perform the bounded start-health-stop proof and never print raw runtime data."""

    global ACTIVE_CANDIDATE
    accepted_task: str | None = None
    reserved=False
    try:
        if any(item["state"] not in {"succeeded","failed","stopped-reconciled"} for item in load_candidate_ledger()["attempts"]):raise CandidatePreflightError("candidate-prior-attempt-reconciliation-required")
        verify_account(policy)
        candidate_reference = candidate_task_definition(policy)
        server_reference, network = active_server(policy)
        candidate = task_definition(candidate_reference, policy, "candidate-task-definition-inspection-unavailable")
        server = task_definition(server_reference, policy, "candidate-source-task-definition-inspection-unavailable")
        image = verify_candidate_shape(candidate, server, policy)
        if image.rsplit("@",1)[-1]!=policy.get("qualified_artifact_digest"):raise CandidatePreflightError("candidate-realization-artifact-mismatch")
        current_attempts = [
            item for item in load_candidate_ledger()["attempts"]
            if isinstance(item, dict) and item.get("image_hash") == hashlib.sha256(IMMUTABLE_IMAGE.fullmatch(image).group(1).encode("ascii")).hexdigest()[:16]
        ]
        label = attempt_label(image, len(current_attempts) + 1)
        assert_fresh_attempt(label, policy)
        label = reserve_candidate_attempt(image,task_definition=candidate_reference)
        reserved=True
        accepted_task = run_candidate(candidate_reference, label, network, policy)
        record_candidate_state(label,"submitted")
        ACTIVE_CANDIDATE = (accepted_task, policy)
        wait_for_healthy(accepted_task, policy)
        stop_and_wait(accepted_task, policy)
        ACTIVE_CANDIDATE = None
        if labelled_tasks(label, "RUNNING", policy):
            raise CandidatePreflightError("candidate-cleanup-incomplete")
        record_candidate_state(label, "succeeded")
        print(safe_result("passed"))
        return 0
    except CandidatePreflightError as exception:
        category = str(exception)
        secondary = None
        if accepted_task is None and reserved:
            try:
                record_candidate_state(label, "uncertain")
            except CandidatePreflightError:
                secondary = "candidate-attempt-receipt-failure"
        if accepted_task is not None:
            try:
                cleanup_active_candidate()
                record_candidate_state(label, "failed")
            except CandidatePreflightError:
                secondary = "candidate-cleanup-failure"
        print(safe_result("uncertain" if (reserved and accepted_task is None) or secondary is not None or category=="candidate-prior-attempt-reconciliation-required" else "failed", category, secondary))
        return 1
    finally:
        ACTIVE_CANDIDATE = None


def main() -> int:
    """Dispatch source validation or the one explicit candidate execution."""

    arguments = parse_arguments()
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    try:
        policy = load_policy()
        policy["qualified_artifact_digest"]=realization_preflight(arguments.realization_facts,arguments.realization_change_summary)
        if arguments.validate:
            print(safe_result("validated"))
            return 0
        root=Path(__file__).resolve().parents[3]
        spec=importlib.util.spec_from_file_location("aws_response",root/"scripts/04.deploy/shared/provider-adapters/aws/response.py")
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        if not adapter.inventory_covered(root):raise CandidatePreflightError("delivery-inventory-not-covered")
        if arguments.reconcile or arguments.cleanup:
            verify_account(policy)
            return reconcile_attempts(policy,cleanup=arguments.cleanup)
        return execute(policy)
    except CandidatePreflightError as exception:
        print(safe_result("uncertain" if arguments.reconcile or arguments.cleanup else "failed", str(exception)))
        return 1


if __name__ == "__main__":
    sys.exit(main())
