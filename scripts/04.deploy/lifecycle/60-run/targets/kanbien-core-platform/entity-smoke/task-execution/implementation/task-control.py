#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-control
#   version: 4
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-27"
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
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re

_RESPONSE_SPEC = importlib.util.spec_from_file_location("entity_smoke_aws_response", Path(__file__).resolve().parents[7] / "shared/provider-adapters/aws/response.py")
_RESPONSE = importlib.util.module_from_spec(_RESPONSE_SPEC)
_RESPONSE_SPEC.loader.exec_module(_RESPONSE)
TASKS_SPEC = importlib.util.spec_from_file_location("entity_smoke_aws_tasks", Path(__file__).resolve().parents[7] / "shared/provider-adapters/aws/tasks.py")
TASKS = importlib.util.module_from_spec(TASKS_SPEC)
TASKS_SPEC.loader.exec_module(TASKS)
RESERVATIONS_SPEC = importlib.util.spec_from_file_location("entity_smoke_reservations", Path(__file__).resolve().parents[7] / "shared/provider-adapters/aws/resource_reservation.py")
RESERVATIONS = importlib.util.module_from_spec(RESERVATIONS_SPEC)
RESERVATIONS_SPEC.loader.exec_module(RESERVATIONS)

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


def runtime(request):
    """Checked syntax only; source inspection owns origin, never launch authority."""
    if not isinstance(request, dict): reject("runtime-binding-invalid")
    if "runtime" not in request:
        workload = request.get("workload")
        if not isinstance(workload, str): reject("runtime-binding-invalid")
        return {"cluster": CLUSTER, "cluster_arn": f"arn:aws:ecs:{REGION}:{ACCOUNT}:cluster/{CLUSTER}",
                "family": "kanbien-core-platform-entity-smoke-" + workload, "container_name": "entity-smoke-" + workload,
                "log_group": "/aws/ecs/kanbien-core-platform", "log_stream_prefix": "entity-smoke-" + workload}
    try: selected = TASKS.runtime_binding(request["runtime"], account=ACCOUNT, region=REGION)
    except TASKS.TaskFailure: reject("runtime-binding-invalid")
    return {**selected, "cluster": selected["cluster_arn"]}


def validate_request(value):
    fields = {"workload", "definition", "image_digest", "source_revision", "configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256", "security_group", "subnets", "environment", "deadline_seconds", "proof_label"}
    if not isinstance(value, dict) or set(value) not in (fields, fields | {"runtime"}):
        reject("task-request-invalid")
    workload = value["workload"]
    if not isinstance(workload, str) or workload not in OPERATIONS:
        reject("task-request-invalid")
    family = runtime(value)["family"]
    patterns = {
        "definition": rf"arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/{re.escape(family)}:[1-9][0-9]*",
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


class _AttemptReservationFailure(TaskFailure):
    def __init__(self, code):
        # Shared storage reasons never widen this caller's historical vocabulary.
        super().__init__({"path-invalid": "attempt-path-invalid",
                          "reservation-mismatch": "attempt-reservation-mismatch"}.get(code, "attempt-reservation-unavailable"))


class AttemptStore(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/entity-smoke-task-reservation/v1"
    operation_prefix = "es-"
    failure = _AttemptReservationFailure

    def __init__(self, root, *, storage=None):
        try:
            if storage is None:
                no_symlinks(Path(root))
            super().__init__(root, storage=storage)
        except TaskFailure: raise
        except RESERVATIONS.ReservationFailure as failure: raise self.failure(failure.code) from None
        except Exception: reject("attempt-reservation-unavailable")

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
        if self._storage is not None:
            return key + ".json"
        path = self.root / (key + ".json")
        no_symlinks(path)
        return path

    def make_record(self, key, request):
        value = super().make_record(key, request)
        del value["phase"]
        return value

    def validate_time(self, value):
        try:
            reserved_at = datetime.fromisoformat(value)
        except (ValueError, TypeError, OverflowError):
            reject("attempt-reservation-unavailable")
        if reserved_at.tzinfo is None:
            reject("attempt-reservation-mismatch")

    @classmethod
    def validate_record(cls, key, request, previous, *, validate_time):
        if not (isinstance(previous, dict) and set(previous) == {"schema", "operation_id", "request", "request_sha256", "reserved_at"}
                and previous.get("schema") == cls.schema and previous.get("request") == request
                and previous.get("request_sha256") == hashlib.sha256(canonical(request)).hexdigest()
                and isinstance(previous.get("operation_id"), str) and re.fullmatch(r"es-[a-f0-9]{32}", previous["operation_id"])):
            reject("attempt-reservation-mismatch")
        validate_time(previous["reserved_at"])
        return previous

    def read(self, key, request):
        try:
            return super().read(key, request)
        except TaskFailure: raise
        except RESERVATIONS.ReservationFailure as failure: raise self.failure(failure.code) from None
        except Exception: reject("attempt-reservation-unavailable")

    def reserve(self, key, request):
        try:
            return super().reserve(key, request)
        except TaskFailure: raise
        except RESERVATIONS.ReservationFailure as failure: raise self.failure(failure.code) from None
        except Exception: reject("attempt-reservation-unavailable")


def overrides(request):
    return {"containerOverrides": [{"name": runtime(request)["container_name"], "environment": [{"name": key, "value": value} for key, value in sorted(request["environment"].items())]}]}


def exact_task(task, reservation):
    request = reservation["request"]
    selected = runtime(request)
    prefix = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/" + selected["cluster_arn"].rsplit("/", 1)[1] + "/"
    if not isinstance(task, dict) or not isinstance(task.get("taskArn"), str) or re.fullmatch(re.escape(prefix) + r"[a-f0-9]{32}", task["taskArn"]) is None:
        reject("task-observation-invalid")
    if task.get("taskDefinitionArn") != request["definition"] or task.get("startedBy") != reservation["operation_id"]:
        reject("task-observation-identity-mismatch")
    if not _RESPONSE.task_overrides_match(task, selected["container_name"], request["environment"]):
        reject("task-observation-overrides-mismatch")
    return task


def invoke_once(provider, store, key, request, *, before_submit=None):
    """Durably reserve before shared submission; existing attempts only reconcile."""
    reservation, fresh = store.reserve(key, request)
    if not fresh: return reconcile_reserved(provider, reservation)
    network = {"awsvpcConfiguration": {"subnets": request["subnets"], "securityGroups": [request["security_group"]], "assignPublicIp": "DISABLED"}}
    try:
        task = TASKS.submit_task(provider, cluster=runtime(request)["cluster"], definition=request["definition"], operation_id=reservation["operation_id"],
            network=network, overrides=overrides(request), validate_task=lambda task: exact_task(task, reservation),
            before_submit=(lambda: before_submit(reservation)) if before_submit is not None else None, passthrough=(SubmissionNotStarted,))
        return reservation, task
    except TASKS.TaskFailure: reject("task-submission-uncertain-reconcile-required")


def reconcile_reserved(provider, reservation):
    """Observe the checked existing reservation without another submission."""
    request = validate_request(reservation["request"])
    try:
        task = TASKS.reconcile_task(provider, cluster=runtime(request)["cluster"], definition=request["definition"], operation_id=reservation["operation_id"],
            validate_task=lambda task: exact_task(task, reservation), sort_arns=True)
        return reservation, task
    except TASKS.TaskFailure as failure:
        reject("task-reconciliation-unresolved-no-replay" if failure.code == "reconciliation-unresolved" else "task-reconciliation-unavailable")
