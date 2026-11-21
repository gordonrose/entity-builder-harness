#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.resource-control
#   version: 3
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-19"
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
from datetime import timedelta
import hashlib
import importlib.util
from pathlib import Path
import re


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


CONTROL = module("entity_smoke_resource_task_control", Path(__file__).with_name("task-control.py"))
EVIDENCE = module("entity_smoke_resource_task_evidence", Path(__file__).with_name("task-evidence.py"))
RESERVATIONS = module("aws_resource_reservations", Path(__file__).resolve().parents[5] / "shared/provider-adapters/aws/resource_reservation.py")
SNAPSHOTS = module("aws_snapshot_execution", Path(__file__).resolve().parents[5] / "shared/provider-adapters/aws/snapshots.py")
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
    if record_required and isinstance(binding, dict) and "recovery_id" in binding:
        patterns = {**patterns, "recovery_id": r"[a-f0-9]{64}"}
    require(isinstance(binding, dict) and set(binding) == set(patterns), "resource-binding-invalid")
    require(all(isinstance(binding[key], str) and re.fullmatch(pattern, binding[key]) is not None for key, pattern in patterns.items()), "resource-binding-invalid")
    return binding


def recovery_binding(binding, delivery=None):
    validate_binding(binding)
    if delivery is None: return binding
    validate_delivery(delivery)
    require(all(binding[key] == delivery["candidate"][key] for key in ("source_revision", "image_digest"))
        and all(binding[key] == delivery["contracts"][key] for key in delivery["contracts"])
        and all(binding[key] == delivery[key] for key in ("proof_label", "dependency_incarnation_sha256")), "resource-delivery-binding-mismatch")
    return {**binding, "recovery_id": delivery["delivery_id"]}


def recovery_namespace(C, context):
    """A successor's own journal, not an exception for the retired first journal.

    Call only after the live source owner validated its accepted predecessor,
    completed update, package, snapshot and restore lineage. A record label is
    deliberately stable across releases and cannot identify an operation journal.
    """
    delivery = validate_delivery(context.get("delivery") or context.get("recovery_delivery"))
    binding = context["restore_binding"]
    require(recovery_binding(binding, delivery) == binding
        and context["cache"] == C.delivery_cache(binding["proof_label"], delivery)
        and context["custody"]["receipt_reference"] == delivery["candidate"]["receipt_reference"], "resource-delivery-binding-mismatch")
    return delivery


def resource_label(binding):
    validate_binding(binding)
    return "entity-smoke-" + binding["recovery_id"][:24] if "recovery_id" in binding else binding["proof_label"]


def write_exclusive(path, value):
    CONTROL.no_symlinks(path)
    try: return RESERVATIONS.write_exclusive(path, value)
    except RESERVATIONS.ReservationFailure as failure: raise ResourceFailure("resource-" + failure.code) from None


def validate_delivery(value):
    """Closed delivery identity, not a claim of acceptance or provider success."""
    fields = {"schema", "delivery_id", "expected_predecessor", "predecessor", "candidate", "contracts", "dependency_incarnation_sha256", "proof_label", "smoke_label"}
    require(isinstance(value, dict) and set(value) == fields and value["schema"] == "deploy/entity-smoke-delivery-context/v1", "resource-delivery-invalid")
    predecessor, candidate, contracts = value["predecessor"], value["candidate"], value["contracts"]
    require(isinstance(predecessor, dict) and set(predecessor) == {"release_id", "source_revision", "image_digest", "proof_set_sha256"}
            and isinstance(candidate, dict) and set(candidate) == {"source_revision", "image_digest", "receipt_reference"}
            and isinstance(contracts, dict) and set(contracts) == {"configuration_contract_sha256", "permission_contract_sha256"}, "resource-delivery-invalid")
    def matches(item, pattern): return isinstance(item, str) and re.fullmatch(pattern, item) is not None
    require(matches(value["expected_predecessor"], r"release-[a-f0-9]{24}") and predecessor["release_id"] == value["expected_predecessor"]
            and matches(value["proof_label"], PATTERNS["proof_label"])
            and matches(value["dependency_incarnation_sha256"], PATTERNS["dependency_incarnation_sha256"])
            and all(matches(contracts[key], PATTERNS[key]) for key in contracts)
            and all(matches(item["source_revision"], PATTERNS["source_revision"]) and matches(item["image_digest"], PATTERNS["image_digest"]) for item in (predecessor, candidate))
            and matches(predecessor["proof_set_sha256"], r"sha256:[a-f0-9]{64}")
            and matches(candidate["receipt_reference"], r"github-actions-run:[0-9]+"), "resource-delivery-invalid")
    identity = {key: item for key, item in value.items() if key not in {"schema", "delivery_id", "smoke_label"}}
    digest = hashlib.sha256(CONTROL.canonical(identity)).hexdigest()
    require(value["delivery_id"] == digest and value["smoke_label"] == "entity-smoke-" + digest[:24], "resource-delivery-identity-mismatch")
    return value


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
    for action in ("update", "rollback"):
        fields["deploy-" + action + "-change-set"] = {"binding", "parameters_sha256", "template_sha256", "delivery", "previous_parameters_sha256"}
        fields["deploy-execute-" + action] = fields["deploy-" + action + "-change-set"] | {"change_set_arn", "stack_arn"}
    require(isinstance(phase, str) and phase in fields and isinstance(request, dict) and set(request) == fields[phase], "resource-request-invalid")
    deployment = phase.startswith("deploy-")
    validate_binding(request["binding"], record_required=not deployment)
    for key in ("parameters_sha256", "previous_parameters_sha256", "template_sha256", "resources_sha256", "reader_receipt_sha256"):
        if key in request: require(isinstance(request[key], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", request[key]) is not None, "resource-request-invalid")
    if "delivery" in request:
        delivery = validate_delivery(request["delivery"])
        binding = request["binding"]
        require(binding["proof_label"] == delivery["proof_label"] and binding["dependency_incarnation_sha256"] == delivery["dependency_incarnation_sha256"]
                and all(binding[key] == value for key, value in delivery["contracts"].items()), "resource-delivery-binding-mismatch")
        selected = delivery["predecessor"] if "rollback" in phase else delivery["candidate"]
        require(all(binding[key] == selected[key] for key in ("source_revision", "image_digest")), "resource-delivery-binding-mismatch")
    task_pattern = r"arn:aws:ecs:" + REGION + ":" + ACCOUNT + ":task/" + CLUSTER + r"/[a-f0-9]{32}"
    if "definition" in request:
        require(isinstance(request["definition"], str) and re.fullmatch(r"arn:aws:ecs:" + REGION + ":" + ACCOUNT + r":task-definition/kanbien-core-platform-entity-smoke-server:[1-9][0-9]*", request["definition"]) is not None, "resource-request-invalid")
    if "original_task" in request:
        require(isinstance(request["original_task"], str) and re.fullmatch(task_pattern, request["original_task"]) is not None, "resource-request-invalid")
    if "original_tasks" in request:
        originals, expected = request["original_tasks"], 1 if phase == "stop-runtime" else 0
        require(isinstance(originals, list) and len(originals) == expected and all(isinstance(item, str) and re.fullmatch(task_pattern, item) is not None for item in originals) and type(request["desired_count"]) is int and request["desired_count"] == (0 if expected else 1), "resource-request-invalid")
    if phase == "create-recovery-point":
        require(isinstance(request["source_resource_id"], str) and re.fullmatch(r"db-[A-Za-z0-9]+", request["source_resource_id"]) is not None and request["snapshot"] == "kanbien-core-platform-" + resource_label(request["binding"]), "resource-request-invalid")
        timestamp(request["original_commit_observed_at"])
    if "change_set_arn" in request:
        name = ("entity-smoke-" + ("activate" if phase.endswith("activate") else "create") + "-" if deployment else "entity-smoke-restore-") + request["binding"]["proof_label"].removeprefix("entity-smoke-")
        if "delivery" in request:
            name = "entity-smoke-" + ("rollback" if "rollback" in phase else "update") + "-" + request["delivery"]["delivery_id"][:24]
        elif not deployment:
            name = "entity-smoke-restore-" + resource_label(request["binding"]).removeprefix("entity-smoke-")
        require(isinstance(request["change_set_arn"], str) and re.fullmatch(r"arn:aws:cloudformation:" + REGION + ":" + ACCOUNT + ":changeSet/" + name + r"/[A-Za-z0-9-]+", request["change_set_arn"]) is not None, "resource-request-invalid")
    if "stack_arn" in request:
        stack = "kanbien-core-platform-entity-smoke" if deployment else "kanbien-core-platform-entity-smoke-restore-" + request["binding"]["proof_label"].removeprefix("entity-smoke-")
        if not deployment: stack = "kanbien-core-platform-entity-smoke-restore-" + resource_label(request["binding"]).removeprefix("entity-smoke-")
        require(isinstance(request["stack_arn"], str) and re.fullmatch(r"arn:aws:cloudformation:" + REGION + ":" + ACCOUNT + ":stack/" + stack + r"/[A-Za-z0-9-]+", request["stack_arn"]) is not None, "resource-request-invalid")
    if phase == "delete-restore":
        require(isinstance(request["restored_resource_id"], str) and re.fullmatch(r"db-[A-Za-z0-9]+", request["restored_resource_id"]) is not None and isinstance(request["reader_task_arn"], str) and re.fullmatch(task_pattern, request["reader_task_arn"]) is not None, "resource-request-invalid")


class ResourceStore(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/entity-smoke-resource-reservation/v1"
    operation_prefix = "es-"
    failure = staticmethod(lambda code: ResourceFailure("resource-" + code))
    validate_time = staticmethod(timestamp)

    def __init__(self, root):
        CONTROL.no_symlinks(Path(root))
        super().__init__(root)

    def path_for(self, phase, request):
        validate_request(phase, request)
        # One phase per proof label: a different user-facing key cannot repeat
        # the same replacement/stop/snapshot mutation after a lost response.
        path = self.root / (request["binding"]["proof_label"] + "-" + phase + ".json")
        CONTROL.no_symlinks(path)
        return path

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
    request = {"binding": binding, "definition": definition, "original_task": original}
    def precondition(_reservation):
        require(before.get("lastStatus") == "RUNNING" and original in running_service_tasks(provider), "resource-replacement-precondition-not-confirmed")
    def observe(reservation):
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
    try:
        return CONTROL.TASKS.replace_task(provider, store, phase=phase, request=request,
            cluster=CLUSTER, original=original, reason=lambda reservation: reservation["operation_id"],
            precondition=precondition, observe=observe, passthrough=(SubmissionNotStarted,))
    except CONTROL.TASKS.TaskFailure:
        raise ResourceFailure("resource-submission-uncertain-reconcile-only") from None


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
    snapshot = "kanbien-core-platform-" + resource_label(binding)
    request = {"binding": binding, "source_resource_id": resource_id, "snapshot": snapshot, "original_commit_observed_at": original_commit_observed_at}
    def validate_reservation(reservation):
        require(timestamp(reservation["reserved_at"]) >= committed, "resource-snapshot-reservation-predates-record")
    def precondition(reservation):
        # An independently existing object cannot be adopted merely because its
        # name matches. This must be an exact service-code absence observation.
        try: provider("rds", "describe-db-snapshots", DBSnapshotIdentifier=snapshot)
        except ResourceMissing: pass
        except Exception: raise ResourceFailure("resource-snapshot-precondition-unavailable") from None
        else: raise ResourceFailure("resource-snapshot-already-exists")
    def observe(reservation, fresh):
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
    tags = [{"Key": "Target", "Value": CLUSTER}, {"Key": "Scope", "Value": "entity-smoke"}, {"Key": "ProofLabel", "Value": binding["proof_label"]}]
    try:
        return SNAPSHOTS.create(provider, store, phase="create-recovery-point", request=request,
            arguments=lambda reservation: {"DBInstanceIdentifier": SOURCE_DATABASE, "DBSnapshotIdentifier": snapshot, "Tags": tags},
            precondition=precondition, validate_reservation=validate_reservation, observe=observe,
            passthrough=(SubmissionNotStarted,))
    except SNAPSHOTS.SnapshotFailure:
        raise ResourceFailure("resource-submission-uncertain-reconcile-only") from None
