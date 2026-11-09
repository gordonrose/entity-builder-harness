#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.resource-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reserve and reconcile exact owned runtime replacement, stopped-state control and snapshot creation without mutation replay.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Internal controls, not an AWS authority or accepted-release ledger.

The public owning route must supply a provider capability only after its
declaration/custody/realization gates and concrete approval pass. Importing this
module calls no provider. A reservation is intent, never proof of completion.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import uuid


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


CONTROL = module("entity_smoke_resource_task_control", Path(__file__).with_name("task-control.py"))
EVIDENCE = module("entity_smoke_resource_task_evidence", Path(__file__).with_name("task-evidence.py"))
ACCOUNT, REGION, CLUSTER = CONTROL.ACCOUNT, CONTROL.REGION, CONTROL.CLUSTER
SERVICE = "kanbien-core-platform-entity-smoke"
SOURCE_DATABASE = "kanbien-core-platform-persistence"
PATTERNS = {
    "source_revision": r"[a-f0-9]{40}", "image_digest": r"sha256:[a-f0-9]{64}",
    "configuration_contract_sha256": r"sha256:[a-f0-9]{64}", "permission_contract_sha256": r"sha256:[a-f0-9]{64}",
    "dependency_incarnation_sha256": r"sha256:[a-f0-9]{64}", "proof_label": r"entity-smoke-[a-f0-9]{24}",
    "record_digest": r"[a-f0-9]{64}",
}


class ResourceFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class ResourceMissing(Exception):
    """Only a governed provider adapter may map an exact service missing code."""


class SubmissionNotStarted(ResourceFailure):
    """Provider-side guard rejected before invoking any remote mutation."""


def require(value, code):
    if not value: raise ResourceFailure(code)


def timestamp(value):
    try: return EVIDENCE.timestamp(value)
    except EVIDENCE.EvidenceFailure: raise ResourceFailure("resource-time-invalid") from None


def validate_binding(binding, *, record_required=True):
    patterns = PATTERNS if record_required else {key: pattern for key, pattern in PATTERNS.items() if key != "record_digest"}
    require(isinstance(binding, dict) and set(binding) == set(patterns), "resource-binding-invalid")
    require(all(isinstance(binding[key], str) and re.fullmatch(pattern, binding[key]) is not None for key, pattern in patterns.items()), "resource-binding-invalid")
    return binding


def write_exclusive(path, value):
    CONTROL.no_symlinks(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(CONTROL.canonical(value) + b"\n"); stream.flush(); os.fsync(stream.fileno())
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
    except FileExistsError: return False
    except (OSError, ValueError, TypeError, UnicodeError): raise ResourceFailure("resource-retention-not-confirmed") from None
    return True


def validate_request(phase, request):
    fields = {
        "server-replacement": {"binding", "definition", "original_task"},
        "credential-replacement": {"binding", "definition", "original_task"},
        "stop-runtime": {"binding", "definition", "desired_count", "original_tasks"},
        "start-runtime": {"binding", "definition", "desired_count", "original_tasks"},
        "create-recovery-point": {"binding", "source_resource_id", "snapshot", "original_commit_observed_at"},
        "restore-change-set": {"binding", "parameters_sha256", "template_sha256"},
        "execute-restore": {"binding", "parameters_sha256", "template_sha256", "change_set_arn", "stack_arn"},
        "delete-restore": {"binding", "stack_arn", "restored_resource_id", "resources_sha256", "reader_task_arn", "reader_receipt_sha256"},
        "deploy-create-change-set": {"binding", "parameters_sha256", "template_sha256"},
        "deploy-activate-change-set": {"binding", "parameters_sha256", "template_sha256"},
        "deploy-execute-create": {"binding", "parameters_sha256", "template_sha256", "change_set_arn", "stack_arn"},
        "deploy-execute-activate": {"binding", "parameters_sha256", "template_sha256", "change_set_arn", "stack_arn"},
    }
    require(isinstance(phase, str) and phase in fields and isinstance(request, dict) and set(request) == fields[phase], "resource-request-invalid")
    deployment = phase.startswith("deploy-")
    validate_binding(request["binding"], record_required=not deployment)
    for key in ("parameters_sha256", "template_sha256", "resources_sha256", "reader_receipt_sha256"):
        if key in request: require(isinstance(request[key], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", request[key]) is not None, "resource-request-invalid")
    task_pattern = r"arn:aws:ecs:" + REGION + ":" + ACCOUNT + ":task/" + CLUSTER + r"/[a-f0-9]{32}"
    if "definition" in request:
        require(isinstance(request["definition"], str) and re.fullmatch(r"arn:aws:ecs:" + REGION + ":" + ACCOUNT + r":task-definition/kanbien-core-platform-entity-smoke-server:[1-9][0-9]*", request["definition"]) is not None, "resource-request-invalid")
    if "original_task" in request:
        require(isinstance(request["original_task"], str) and re.fullmatch(task_pattern, request["original_task"]) is not None, "resource-request-invalid")
    if "original_tasks" in request:
        originals, expected = request["original_tasks"], 1 if phase == "stop-runtime" else 0
        require(isinstance(originals, list) and len(originals) == expected and all(isinstance(item, str) and re.fullmatch(task_pattern, item) is not None for item in originals) and type(request["desired_count"]) is int and request["desired_count"] == (0 if expected else 1), "resource-request-invalid")
    if phase == "create-recovery-point":
        require(isinstance(request["source_resource_id"], str) and re.fullmatch(r"db-[A-Za-z0-9]+", request["source_resource_id"]) is not None and request["snapshot"] == "kanbien-core-platform-" + request["binding"]["proof_label"], "resource-request-invalid")
        timestamp(request["original_commit_observed_at"])
    if "change_set_arn" in request:
        name = ("entity-smoke-" + ("activate" if phase.endswith("activate") else "create") + "-" if deployment else "entity-smoke-restore-") + request["binding"]["proof_label"].removeprefix("entity-smoke-")
        require(isinstance(request["change_set_arn"], str) and re.fullmatch(r"arn:aws:cloudformation:" + REGION + ":" + ACCOUNT + ":changeSet/" + name + r"/[A-Za-z0-9-]+", request["change_set_arn"]) is not None, "resource-request-invalid")
    if "stack_arn" in request:
        stack = "kanbien-core-platform-entity-smoke" if deployment else "kanbien-core-platform-entity-smoke-restore-" + request["binding"]["proof_label"].removeprefix("entity-smoke-")
        require(isinstance(request["stack_arn"], str) and re.fullmatch(r"arn:aws:cloudformation:" + REGION + ":" + ACCOUNT + ":stack/" + stack + r"/[A-Za-z0-9-]+", request["stack_arn"]) is not None, "resource-request-invalid")
    if phase == "delete-restore":
        require(isinstance(request["restored_resource_id"], str) and re.fullmatch(r"db-[A-Za-z0-9]+", request["restored_resource_id"]) is not None and isinstance(request["reader_task_arn"], str) and re.fullmatch(task_pattern, request["reader_task_arn"]) is not None, "resource-request-invalid")


class ResourceStore:
    def __init__(self, root):
        self.root = Path(root)
        CONTROL.no_symlinks(self.root)

    def path_for(self, phase, request):
        validate_request(phase, request)
        # One phase per proof label: a different user-facing key cannot repeat
        # the same replacement/stop/snapshot mutation after a lost response.
        path = self.root / (request["binding"]["proof_label"] + "-" + phase + ".json")
        CONTROL.no_symlinks(path)
        return path

    def read(self, phase, request):
        path = self.path_for(phase, request)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as stream: raw = stream.read(65537)
            require(len(raw) <= 65536, "resource-reservation-unavailable")
            previous = json.loads(raw)
        except FileNotFoundError: return None
        except (OSError, ValueError, TypeError, UnicodeError): raise ResourceFailure("resource-reservation-unavailable") from None
        require(isinstance(previous, dict) and set(previous) == {"schema", "phase", "operation_id", "request", "request_sha256", "reserved_at"} and previous.get("schema") == "deploy/entity-smoke-resource-reservation/v1" and previous.get("phase") == phase and previous.get("request") == request and previous.get("request_sha256") == hashlib.sha256(CONTROL.canonical(request)).hexdigest() and isinstance(previous.get("operation_id"), str) and re.fullmatch(r"es-[a-f0-9]{32}", previous["operation_id"]) is not None, "resource-reservation-mismatch")
        timestamp(previous.get("reserved_at"))
        return previous

    def reserve(self, phase, request):
        path = self.path_for(phase, request)
        value = {"schema": "deploy/entity-smoke-resource-reservation/v1", "phase": phase,
                 "operation_id": "es-" + uuid.uuid4().hex, "request": request,
                 "request_sha256": hashlib.sha256(CONTROL.canonical(request)).hexdigest(),
                 "reserved_at": datetime.now(timezone.utc).isoformat()}
        fresh = write_exclusive(path, value)
        if fresh: return value, True
        previous = self.read(phase, request)
        require(previous is not None, "resource-reservation-unavailable")
        return previous, False


def only(response, field):
    values = response.get(field) if isinstance(response, dict) else None
    require(isinstance(values, list) and len(values) == 1 and isinstance(values[0], dict) and not response.get("failures"), "resource-observation-not-confirmed")
    return values[0]


def service(provider, definition, expected_count):
    require(isinstance(definition, str) and re.fullmatch(r"arn:aws:ecs:" + REGION + ":" + ACCOUNT + r":task-definition/kanbien-core-platform-entity-smoke-server:[1-9][0-9]*", definition) is not None, "resource-server-definition-invalid")
    value = only(provider("ecs", "describe-services", cluster=CLUSTER, services=[SERVICE]), "services")
    require(value.get("serviceName") == SERVICE and value.get("clusterArn") == "arn:aws:ecs:" + REGION + ":" + ACCOUNT + ":cluster/" + CLUSTER and value.get("taskDefinition") == definition and value.get("status") == "ACTIVE" and value.get("desiredCount") == expected_count, "resource-service-identity-not-confirmed")
    return value


def task(provider, arn, definition, digest, *, allow_starting=False):
    require(isinstance(arn, str) and re.fullmatch(r"arn:aws:ecs:" + REGION + ":" + ACCOUNT + ":task/" + CLUSTER + r"/[a-f0-9]{32}", arn) is not None, "resource-server-task-invalid")
    value = only(provider("ecs", "describe-tasks", cluster=CLUSTER, tasks=[arn]), "tasks")
    containers = value.get("containers")
    require(value.get("taskArn") == arn and value.get("taskDefinitionArn") == definition and value.get("group") == "service:" + SERVICE and value.get("launchType") == "FARGATE" and isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict) and containers[0].get("name") == "entity-smoke-server", "resource-server-task-identity-not-confirmed")
    pulled = containers[0].get("imageDigest")
    require(pulled == digest or allow_starting is True and pulled is None and value.get("lastStatus") in {"PROVISIONING", "PENDING", "ACTIVATING"}, "resource-server-task-identity-not-confirmed")
    return value


def running_service_tasks(provider):
    response = provider("ecs", "list-tasks", cluster=CLUSTER, serviceName=SERVICE, desiredStatus="RUNNING")
    values = response.get("taskArns") if isinstance(response, dict) else None
    require(isinstance(values, list) and not response.get("nextToken") and len(set(values)) == len(values) and all(isinstance(value, str) for value in values), "resource-service-task-observation-incomplete")
    return values


def require_other_tasks_terminal(provider, *, reservation=None):
    active = []
    for workload in CONTROL.OPERATIONS:
        family = "kanbien-core-platform-entity-smoke-" + workload
        arns = set()
        for status in ("RUNNING", "STOPPED"):
            response = provider("ecs", "list-tasks", cluster=CLUSTER, family=family, desiredStatus=status)
            values = response.get("taskArns") if isinstance(response, dict) else None
            require(isinstance(values, list) and not response.get("nextToken") and all(isinstance(value, str) for value in values), "resource-owned-completion-task-observation-incomplete")
            arns.update(values)
        for offset in range(0, len(arns), 100):
            batch = sorted(arns)[offset:offset + 100]
            response = provider("ecs", "describe-tasks", cluster=CLUSTER, tasks=batch)
            tasks = response.get("tasks") if isinstance(response, dict) else None
            require(isinstance(tasks, list) and len(tasks) == len(batch) and not response.get("failures") and {item.get("taskArn") for item in tasks} == set(batch), "resource-owned-completion-task-observation-incomplete")
            require(all(isinstance(item.get("taskDefinitionArn"), str) and re.fullmatch(r"arn:aws:ecs:" + REGION + ":" + ACCOUNT + ":task-definition/" + family + r":[1-9][0-9]*", item["taskDefinitionArn"]) is not None for item in tasks), "resource-owned-completion-task-not-terminal")
            for item in tasks:
                if item.get("lastStatus") == "STOPPED": continue
                require(reservation is not None and item.get("lastStatus") in {"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"}, "resource-owned-completion-task-not-terminal")
                try: CONTROL.exact_task(item, reservation)
                except CONTROL.TaskFailure as failure: raise ResourceFailure(failure.code) from None
                active.append(item["taskArn"])
    require(len(active) <= 1, "resource-owned-completion-task-not-terminal")


def replace_runtime(provider, store, binding, definition, original, *, credential_recovery=False):
    validate_binding(binding)
    phase = "credential-replacement" if credential_recovery else "server-replacement"
    # Validate all immutable selectors before even the first read. Existing
    # reservations skip the mutation, never the identity checks.
    require(isinstance(original, str) and re.fullmatch(r"arn:aws:ecs:" + REGION + ":" + ACCOUNT + ":task/" + CLUSTER + r"/[a-f0-9]{32}", original) is not None, "resource-server-task-invalid")
    service(provider, definition, 1)
    before = task(provider, original, definition, binding["image_digest"])
    reservation, fresh = store.reserve(phase, {"binding": binding, "definition": definition, "original_task": original})
    if fresh:
        require(before.get("lastStatus") == "RUNNING" and original in running_service_tasks(provider), "resource-replacement-precondition-not-confirmed")
        try: provider("ecs", "stop-task", cluster=CLUSTER, task=original, reason=reservation["operation_id"])
        except SubmissionNotStarted: raise
        except Exception: raise ResourceFailure("resource-submission-uncertain-reconcile-only") from None
    predecessor = task(provider, original, definition, binding["image_digest"])
    if predecessor.get("lastStatus") != "STOPPED": return {"status": "pending", "reservation": reservation}
    require(predecessor.get("stoppedReason") == reservation["operation_id"], "resource-replacement-cause-not-confirmed")
    old_stop = timestamp(predecessor.get("stoppedAt"))
    require(old_stop >= timestamp(reservation["reserved_at"]) - timedelta(seconds=60), "resource-predecessor-predates-reservation")
    candidates = running_service_tasks(provider)
    if original in candidates or len(candidates) != 1: return {"status": "pending", "reservation": reservation}
    successor = task(provider, candidates[0], definition, binding["image_digest"], allow_starting=True)
    current = service(provider, definition, 1)
    if current.get("runningCount") != 1 or current.get("pendingCount") != 0 or successor.get("lastStatus") != "RUNNING" or successor.get("healthStatus") != "HEALTHY": return {"status": "pending", "reservation": reservation}
    created, started = timestamp(successor.get("createdAt")), timestamp(successor.get("startedAt"))
    require(created >= timestamp(reservation["reserved_at"]), "resource-successor-predates-reservation")
    require(started >= created, "resource-successor-start-precedes-creation")
    return {"status": "completed", "reservation": reservation, "facts": {"original_task": original, "successor_task": candidates[0], "predecessor_stopped_at": old_stop.isoformat(), "successor_started_at": started.isoformat()}}


def control_runtime_count(provider, store, binding, definition, original_tasks, *, start=False):
    validate_binding(binding)
    desired, prior = (1, 0) if start else (0, 1)
    phase = "start-runtime" if start else "stop-runtime"
    require(isinstance(original_tasks, list) and len(original_tasks) == (0 if start else 1) and all(isinstance(arn, str) for arn in original_tasks), "resource-original-task-set-invalid")
    # Exact current source/image is checked independently of service desired
    # count. No unknown task or other scope is stopped as part of this control.
    require_other_tasks_terminal(provider)
    value = only(provider("ecs", "describe-services", cluster=CLUSTER, services=[SERVICE]), "services")
    require(value.get("desiredCount") in {prior, desired}, "resource-service-state-not-confirmed")
    current = service(provider, definition, value["desiredCount"])
    for arn in running_service_tasks(provider): task(provider, arn, definition, binding["image_digest"], allow_starting=start)
    reservation, fresh = store.reserve(phase, {"binding": binding, "definition": definition, "desired_count": desired, "original_tasks": original_tasks})
    if fresh:
        require(current["desiredCount"] == prior and sorted(running_service_tasks(provider)) == sorted(original_tasks), "resource-runtime-control-precondition-not-confirmed")
        try: provider("ecs", "update-service", cluster=CLUSTER, service=SERVICE, desiredCount=desired)
        except SubmissionNotStarted: raise
        except Exception: raise ResourceFailure("resource-submission-uncertain-reconcile-only") from None
    value = only(provider("ecs", "describe-services", cluster=CLUSTER, services=[SERVICE]), "services")
    require(value.get("desiredCount") in {prior, desired}, "resource-service-state-not-confirmed")
    current = service(provider, definition, value["desiredCount"])
    if current["desiredCount"] != desired: return {"status": "pending", "reservation": reservation}
    arns = running_service_tasks(provider)
    if current.get("runningCount") != desired or current.get("pendingCount") != 0 or len(arns) != desired: return {"status": "pending", "reservation": reservation}
    if desired:
        running = task(provider, arns[0], definition, binding["image_digest"], allow_starting=True)
        if running.get("lastStatus") != "RUNNING" or running.get("healthStatus") != "HEALTHY": return {"status": "pending", "reservation": reservation}
    else:
        if any(task(provider, arn, definition, binding["image_digest"]).get("lastStatus") != "STOPPED" for arn in original_tasks): return {"status": "pending", "reservation": reservation}
        require_other_tasks_terminal(provider)
    return {"status": "completed", "reservation": reservation, "facts": {"desired_count": desired, "running_count": desired, "tasks": arns}}


def create_recovery_point(provider, store, binding, resource_id, original_commit_observed_at):
    validate_binding(binding)
    require(isinstance(resource_id, str) and re.fullmatch(r"db-[A-Za-z0-9]+", resource_id) is not None, "resource-source-incarnation-invalid")
    committed = timestamp(original_commit_observed_at)
    source = only(provider("rds", "describe-db-instances", DBInstanceIdentifier=SOURCE_DATABASE), "DBInstances")
    require(source.get("DBInstanceIdentifier") == SOURCE_DATABASE and source.get("DbiResourceId") == resource_id and source.get("DBInstanceStatus") == "available" and source.get("StorageEncrypted") is True and source.get("PubliclyAccessible") is False, "resource-source-incarnation-not-confirmed")
    incarnation = "sha256:" + hashlib.sha256(CONTROL.canonical({"resource_id": resource_id, "database": source.get("DBName"), "schema": "entity_smoke"})).hexdigest()
    require(incarnation == binding["dependency_incarnation_sha256"], "resource-source-incarnation-not-confirmed")
    snapshot = "kanbien-core-platform-" + binding["proof_label"]
    reservation, fresh = store.reserve("create-recovery-point", {"binding": binding, "source_resource_id": resource_id, "snapshot": snapshot, "original_commit_observed_at": original_commit_observed_at})
    require(timestamp(reservation["reserved_at"]) >= committed, "resource-snapshot-reservation-predates-record")
    if fresh:
        # An independently existing object cannot be adopted merely because its
        # name matches. This must be an exact service-code absence observation.
        try: provider("rds", "describe-db-snapshots", DBSnapshotIdentifier=snapshot)
        except ResourceMissing: pass
        except Exception: raise ResourceFailure("resource-snapshot-precondition-unavailable") from None
        else: raise ResourceFailure("resource-snapshot-already-exists")
        tags = [{"Key": "Target", "Value": CLUSTER}, {"Key": "Scope", "Value": "entity-smoke"}, {"Key": "ProofLabel", "Value": binding["proof_label"]}]
        try: provider("rds", "create-db-snapshot", DBInstanceIdentifier=SOURCE_DATABASE, DBSnapshotIdentifier=snapshot, Tags=tags)
        except SubmissionNotStarted: raise
        except Exception: raise ResourceFailure("resource-submission-uncertain-reconcile-only") from None
    try: observed = only(provider("rds", "describe-db-snapshots", DBSnapshotIdentifier=snapshot), "DBSnapshots")
    except ResourceMissing: return {"status": "pending", "reservation": reservation}
    arn = "arn:aws:rds:" + REGION + ":" + ACCOUNT + ":snapshot:" + snapshot
    require(observed.get("DBSnapshotIdentifier") == snapshot and observed.get("DBSnapshotArn") == arn and observed.get("DBInstanceIdentifier") == SOURCE_DATABASE and observed.get("DbiResourceId") == resource_id and observed.get("Encrypted") is True and observed.get("SnapshotType") == "manual", "resource-snapshot-identity-not-confirmed")
    require(timestamp(observed.get("SnapshotCreateTime")) >= committed, "resource-snapshot-predates-record")
    require(timestamp(observed.get("SnapshotCreateTime")) >= timestamp(reservation["reserved_at"]), "resource-snapshot-predates-reservation")
    tags = provider("rds", "list-tags-for-resource", ResourceName=arn).get("TagList")
    require(isinstance(tags, list) and len(tags) <= 50 and all(isinstance(item, dict) and isinstance(item.get("Key"), str) and isinstance(item.get("Value"), str) for item in tags), "resource-snapshot-ownership-not-confirmed")
    tag_map = {item["Key"]: item["Value"] for item in tags}
    require(len(tag_map) == len(tags) and all(tag_map.get(key) == value for key, value in {"Target": CLUSTER, "Scope": "entity-smoke", "ProofLabel": binding["proof_label"]}.items()), "resource-snapshot-ownership-not-confirmed")
    if observed.get("Status") in {"creating", "copying"}: return {"status": "pending", "reservation": reservation}
    require(observed.get("Status") == "available", "resource-snapshot-not-available")
    return {"status": "completed", "reservation": reservation, "facts": {"snapshot_arn": arn, "source_resource_id": resource_id, "snapshot_created_at": timestamp(observed["SnapshotCreateTime"]).isoformat()}}
