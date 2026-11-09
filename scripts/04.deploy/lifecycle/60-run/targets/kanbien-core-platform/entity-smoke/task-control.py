#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reserve one immutable ECS task attempt and reconcile uncertainty without resubmitting a mutation.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [writes-files, network]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Internal primitive, not AWS authority or a release ledger.

The caller must establish declaration coverage, custody, fresh alignment,
reviewed change shape and explicit execution approval before supplying the
provider capability. Importing this library performs no I/O.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

ACCOUNT, REGION, CLUSTER = "337159794548", "eu-west-1", "kanbien-core-platform"
OPERATIONS = {
    "administration": ("ENTITY_SMOKE_ADMINISTRATION_OPERATION", {"preflight", "bootstrap", "grant-runtime", "observe-permissions", "observe-migration-state", "revoke-runtime", "restore-runtime"}),
    "migration": ("ENTITY_SMOKE_MIGRATION_OPERATION", {"preflight", "apply"}),
    "verifier": ("ENTITY_SMOKE_VERIFICATION_OPERATION", {"create", "read", "observe-create", "cleanup", "lifecycle", "ready", "unready"}),
    "database-proof": ("ENTITY_SMOKE_DATABASE_PROOF_OPERATION", {"preflight", "permissions", "collision"}),
    "restore-reader": ("ENTITY_SMOKE_DATABASE_PROOF_OPERATION", {"preflight", "restore-read"}),
}


class TaskFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class SubmissionNotStarted(TaskFailure):
    """An owning provider guard rejected before any remote submission."""
    def __init__(self, code, field=None, item=None, workload=None):
        super().__init__(code)
        self.field, self.item, self.workload = field, item, workload


def reject(code):
    raise TaskFailure(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def validate_request(value):
    fields = {"workload", "definition", "image_digest", "source_revision", "configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256", "security_group", "subnets", "environment", "deadline_seconds", "proof_label"}
    if not isinstance(value, dict) or set(value) != fields:
        reject("task-request-invalid")
    workload = value["workload"]
    if not isinstance(workload, str) or workload not in OPERATIONS:
        reject("task-request-invalid")
    family = "kanbien-core-platform-entity-smoke-" + workload
    patterns = {
        "definition": rf"arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/{family}:[1-9][0-9]*",
        "image_digest": r"sha256:[a-f0-9]{64}", "source_revision": r"[a-f0-9]{40}",
        "configuration_contract_sha256": r"sha256:[a-f0-9]{64}", "permission_contract_sha256": r"sha256:[a-f0-9]{64}",
        "dependency_incarnation_sha256": r"sha256:[a-f0-9]{64}",
        "security_group": r"sg-(?:[a-f0-9]{8}|[a-f0-9]{17})", "proof_label": r"entity-smoke-[a-f0-9]{24}",
    }
    for key, pattern in patterns.items():
        if not isinstance(value[key], str) or re.fullmatch(pattern, value[key]) is None:
            reject("task-request-invalid")
    if type(value["deadline_seconds"]) is not int or not 1 <= value["deadline_seconds"] <= 900:
        reject("task-request-invalid")
    subnets = value["subnets"]
    if not isinstance(subnets, list) or not 1 <= len(subnets) <= 3 or any(not isinstance(item, str) or re.fullmatch(r"subnet-(?:[a-f0-9]{8}|[a-f0-9]{17})", item) is None for item in subnets) or len(set(subnets)) != len(subnets):
        reject("task-request-invalid")
    environment = value["environment"]
    if not isinstance(environment, dict) or not environment or any(not isinstance(key, str) or not isinstance(content, str) for key, content in environment.items()):
        reject("task-request-invalid")
    # Only proof selectors are overridable, never commands, roles, credentials,
    # network or database settings supplied by the immutable task definition.
    selector, allowed_operations = OPERATIONS[workload]
    allowed = {selector, "ENTITY_SMOKE_PROOF_LABEL", "ENTITY_SMOKE_EXPECTED_DIGEST", "ENTITY_SMOKE_EXPECTED_SOURCE"}
    if set(environment) - allowed or environment.get(selector) not in allowed_operations:
        reject("task-request-invalid")
    if environment[selector] == "preflight":
        expected = {selector} | ({"ENTITY_SMOKE_PROOF_LABEL"} if workload in {"database-proof", "restore-reader"} else set())
        if set(environment) != expected or value["deadline_seconds"] > 90: reject("task-preflight-request-invalid")
    if workload in {"verifier", "database-proof", "restore-reader"} and environment.get("ENTITY_SMOKE_PROOF_LABEL") != value["proof_label"]:
        reject("task-request-invalid")
    if "ENTITY_SMOKE_EXPECTED_SOURCE" in environment and environment["ENTITY_SMOKE_EXPECTED_SOURCE"] != value["source_revision"]:
        reject("task-request-invalid")
    digest = environment.get("ENTITY_SMOKE_EXPECTED_DIGEST")
    if (digest is not None and re.fullmatch(r"[a-f0-9]{64}", digest) is None) or (environment[selector] in {"read", "restore-read", "cleanup", "collision"} and digest is None):
        reject("task-request-invalid")
    return value


def no_symlinks(path):
    if not path.is_absolute() or ".." in path.parts or any(part.is_symlink() for part in [path, *path.parents]):
        reject("attempt-path-invalid")


class AttemptStore:
    def __init__(self, root):
        self.root = Path(root)
        no_symlinks(self.root)

    def path_for(self, key, request):
        validate_request(request)
        selector = OPERATIONS[request["workload"]][0]
        if request["environment"][selector] == "preflight" or request["workload"] == "verifier" and request["environment"][selector] == "ready":
            key = request["proof_label"] + "-" + request["workload"] + "-preflight"
        if request["workload"] == "verifier" and request["environment"][selector] == "unready":
            key = request["proof_label"] + "-verifier-unready"
        if request["workload"] == "verifier" and request["environment"][selector] in {"create", "lifecycle", "cleanup"}:
            # An alternate caller key cannot create a second submission for
            # the same synthetic record label, even across host interruptions.
            key = request["proof_label"] + "-" + request["environment"][selector]
        if not isinstance(key, str) or re.fullmatch(r"[a-z][a-z0-9-]{0,79}", key) is None:
            reject("attempt-key-invalid")
        path = self.root / (key + ".json")
        no_symlinks(path)
        return path

    def read(self, key, request):
        path = self.path_for(key, request)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as stream: raw = stream.read(65537)
            if len(raw) > 65536: reject("attempt-reservation-unavailable")
            existing = json.loads(raw)
            if not isinstance(existing, dict) or set(existing) != {"schema", "operation_id", "request", "request_sha256", "reserved_at"} or existing.get("schema") != "deploy/entity-smoke-task-reservation/v1" or existing.get("request") != request or existing.get("request_sha256") != hashlib.sha256(canonical(request)).hexdigest() or not isinstance(existing.get("operation_id"), str) or re.fullmatch(r"es-[a-f0-9]{32}", existing["operation_id"]) is None:
                reject("attempt-reservation-mismatch")
            reserved_at = datetime.fromisoformat(existing["reserved_at"])
            if reserved_at.tzinfo is None: reject("attempt-reservation-mismatch")
            return existing
        except FileNotFoundError: return None
        except TaskFailure: raise
        except (OSError, ValueError, TypeError, UnicodeError, RecursionError): reject("attempt-reservation-unavailable")

    def reserve(self, key, request):
        path = self.path_for(key, request)
        try:
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            value = {"schema": "deploy/entity-smoke-task-reservation/v1", "operation_id": "es-" + uuid.uuid4().hex,
                     "request": request, "request_sha256": hashlib.sha256(canonical(request)).hexdigest(),
                     "reserved_at": datetime.now(timezone.utc).isoformat()}
            try:
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            except FileExistsError:
                existing = self.read(key, request)
                if existing is None: reject("attempt-reservation-unavailable")
                return existing, False
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(canonical(value) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            descriptor = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try: os.fsync(descriptor)
            finally: os.close(descriptor)
            return value, True
        except TaskFailure:
            raise
        except (OSError, ValueError, TypeError, UnicodeError):
            reject("attempt-reservation-unavailable")


def overrides(request):
    return {"containerOverrides": [{"name": "entity-smoke-" + request["workload"], "environment": [{"name": key, "value": value} for key, value in sorted(request["environment"].items())]}]}


def exact_task(task, reservation):
    request = reservation["request"]
    prefix = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/"
    if not isinstance(task, dict) or not isinstance(task.get("taskArn"), str) or re.fullmatch(re.escape(prefix) + r"[a-f0-9]{32}", task["taskArn"]) is None:
        reject("task-observation-invalid")
    if task.get("taskDefinitionArn") != request["definition"] or task.get("startedBy") != reservation["operation_id"]:
        reject("task-observation-identity-mismatch")
    actual = task.get("overrides")
    if not isinstance(actual, dict) or set(actual) - {"containerOverrides", "inferenceAcceleratorOverrides"} or actual.get("inferenceAcceleratorOverrides", []) != []:
        reject("task-observation-overrides-mismatch")
    containers = actual.get("containerOverrides")
    expected = overrides(request)["containerOverrides"]
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict) or set(containers[0]) != {"name", "environment"} or containers[0].get("name") != expected[0]["name"]:
        reject("task-observation-overrides-mismatch")
    environment = containers[0].get("environment")
    if not isinstance(environment, list) or len(environment) != len(request["environment"]) or any(not isinstance(item, dict) or set(item) != {"name", "value"} or not isinstance(item["name"], str) or not isinstance(item["value"], str) for item in environment) or {item["name"]: item["value"] for item in environment} != request["environment"]:
        reject("task-observation-overrides-mismatch")
    return task


def invoke_once(provider, store, key, request, *, before_submit=None):
    """provider(service, operation, **parameters) is an already gated capability.

    An existing reservation ALWAYS reconciles, even if a lost response yields
    an empty list. No provider mutation is retried by this helper.
    """
    reservation, fresh = store.reserve(key, request)
    if fresh:
        if before_submit is not None: before_submit(reservation)
        network = {"awsvpcConfiguration": {"subnets": request["subnets"], "securityGroups": [request["security_group"]], "assignPublicIp": "DISABLED"}}
        try:
            result = provider("ecs", "run-task", cluster=CLUSTER, taskDefinition=request["definition"], launchType="FARGATE", count=1,
                              networkConfiguration=network, overrides=overrides(request), startedBy=reservation["operation_id"], clientToken=reservation["operation_id"])
        except SubmissionNotStarted: raise
        except Exception:
            reject("task-submission-uncertain-reconcile-required")
        tasks = result.get("tasks") if isinstance(result, dict) else None
        if not isinstance(tasks, list) or len(tasks) != 1 or result.get("failures"):
            reject("task-submission-uncertain-reconcile-required")
        return reservation, exact_task(tasks[0], reservation)
    return reconcile_reserved(provider, reservation)


def reconcile_reserved(provider, reservation):
    """Observe a checked existing reservation; this function cannot RunTask.

    The owning caller reads it through AttemptStore, including the request/hash
    and reservation identity checks. Unknown absence never authorizes replay.
    """
    request = validate_request(reservation["request"])
    family = request["definition"].rsplit("/", 1)[1].split(":", 1)[0]
    arns = []
    for status in ("RUNNING", "STOPPED"):
        try: result = provider("ecs", "list-tasks", cluster=CLUSTER, family=family, desiredStatus=status)
        except Exception: reject("task-reconciliation-unavailable")
        batch = result.get("taskArns") if isinstance(result, dict) else None
        if not isinstance(batch, list) or result.get("nextToken") or any(not isinstance(arn, str) for arn in batch):
            reject("task-reconciliation-unavailable")
        arns.extend(batch)
    arns = sorted(set(arns))
    matching = []
    for offset in range(0, len(arns), 100):
        batch = arns[offset:offset + 100]
        try: result = provider("ecs", "describe-tasks", cluster=CLUSTER, tasks=batch)
        except Exception: reject("task-reconciliation-unavailable")
        tasks = result.get("tasks") if isinstance(result, dict) else None
        if not isinstance(tasks, list) or len(tasks) != len(batch) or result.get("failures") or any(not isinstance(task, dict) or not isinstance(task.get("taskArn"), str) for task in tasks) or {task["taskArn"] for task in tasks} != set(batch):
            reject("task-reconciliation-unavailable")
        matching.extend(task for task in tasks if task.get("startedBy") == reservation["operation_id"])
    if len(matching) != 1:
        reject("task-reconciliation-unresolved-no-replay")
    return reservation, exact_task(matching[0], reservation)
