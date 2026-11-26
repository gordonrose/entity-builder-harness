#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.failure-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reserve each exact first-release stop effect once and retain actual stopped-state evidence without SQL or mutation replay.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import hashlib
from datetime import datetime, timezone
import re
import uuid


class StopFailure(Exception):
    def __init__(self, code, item=None, provider_condition=None):
        super().__init__(code)
        self.code, self.item, self.provider_condition = code, item, provider_condition


class SubmissionNotStarted(StopFailure):
    """Only a provider guard which has not invoked AWS may raise this."""


def require(value, code, item=None):
    if not value: raise StopFailure(code, item)


def intent(C, context):
    own = context["service"]
    restored = context["restored"]
    actors = {arn: {key: row[key] for key in ("definition", "workload")} for arn, row in context["active_tasks"].items()}
    stops = {arn: row for arn, row in actors.items() if row["workload"] != "server" or own is None}
    return {"binding": context["binding"], "stack_arn": context["stack_arn"], "creation_sha256": context["creation_sha256"],
            "resources_sha256": C.DEPLOY.fingerprint(context["resources"]), "definitions": context["definitions"],
            "restored_stack_arn": None if restored is None else restored["stack_arn"], "restored_creation_sha256": None if restored is None else restored["creation_sha256"],
            "service": None if own is None else {key: own[key] for key in ("arn", "stable_configuration_sha256")},
            "initial_tasks": actors, "task_stops": stops, "other_services": context["other_services"], "database_before": context["database"]}


def validate_intent(C, selected, task_bound):
    fields = {"binding", "stack_arn", "creation_sha256", "resources_sha256", "definitions", "restored_stack_arn", "restored_creation_sha256", "service", "initial_tasks", "task_stops", "other_services", "database_before"}
    require(isinstance(selected, dict) and set(selected) == fields, "failure-original-intent-invalid")
    C.RESOURCE.validate_binding(selected["binding"], record_required=False)
    workloads = set(C.RESOURCE.CONTROL.OPERATIONS) | {"server"}
    refs = selected["definitions"]
    require(isinstance(refs, dict) and set(refs) == workloads, "failure-original-definition-set-invalid")
    prefix = "arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT
    for workload, arn in refs.items():
        require(arn is None or isinstance(arn, str) and re.fullmatch(re.escape(prefix) + ":task-definition/kanbien-core-platform-entity-smoke-" + workload + r":[1-9][0-9]*", arn) is not None, "failure-original-definition-set-invalid")
    for key in ("creation_sha256", "resources_sha256"):
        require(isinstance(selected[key], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", selected[key]) is not None, "failure-original-intent-invalid")
    own = selected["service"]
    require(own is None or isinstance(own, dict) and set(own) == {"arn", "stable_configuration_sha256"}
            and own["arn"] == prefix + ":service/" + C.RESOURCE.CLUSTER + "/" + C.RESOURCE.SERVICE
            and isinstance(own["stable_configuration_sha256"], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", own["stable_configuration_sha256"]), "failure-original-service-invalid")
    actors = selected["initial_tasks"]
    require(isinstance(actors, dict) and len(actors) <= task_bound and isinstance(selected["task_stops"], dict), "failure-original-task-set-invalid")
    for arn, actor in actors.items():
        require(isinstance(arn, str) and re.fullmatch(re.escape(prefix) + ":task/" + C.RESOURCE.CLUSTER + r"/[a-f0-9]{32}", arn) is not None
                and isinstance(actor, dict) and set(actor) == {"definition", "workload"} and isinstance(actor["workload"], str) and actor["workload"] in workloads
                and refs[actor["workload"]] is not None and actor["definition"] == refs[actor["workload"]], "failure-original-task-set-invalid")
    expected_stops = {arn: actor for arn, actor in actors.items() if actor["workload"] != "server" or own is None}
    require(selected["task_stops"] == expected_stops and isinstance(selected["other_services"], dict), "failure-original-task-set-invalid")
    observed = selected["database_before"]
    require(isinstance(observed, dict) and observed.get("state") in {"missing", "not-observed", "same-incarnation", "different-incarnation"}
            and not set(observed) - {"state", "condition", "identity_sha256", "configuration_sha256", "data_readback"}, "failure-original-database-observation-invalid")


def verify_scope_bindings(C, selected, context):
    require(context["binding"] == selected["binding"] and context["stack_arn"] == selected["stack_arn"]
            and context["creation_sha256"] == selected["creation_sha256"] and C.DEPLOY.fingerprint(context["resources"]) == selected["resources_sha256"]
            and context["definitions"] == selected["definitions"], "failure-original-scope-binding-changed")
    restored = context["restored"]
    require((None if restored is None else restored["stack_arn"]) == selected["restored_stack_arn"]
            and (None if restored is None else restored["creation_sha256"]) == selected["restored_creation_sha256"], "failure-original-restored-scope-changed")
    require(context["other_services"] == selected["other_services"], "failure-other-service-configuration-changed")
    own = context["service"]
    if own is not None:
        require(selected["service"] is not None and all(own[key] == value for key, value in selected["service"].items()), "failure-own-service-configuration-changed")


def verify_current(C, selected, context):
    verify_scope_bindings(C, selected, context)
    for arn, row in context["active_tasks"].items():
        expected = selected["initial_tasks"].get(arn)
        if row["workload"] == "server" and selected["service"] is not None: continue
        require(expected is not None and all(row[key] == value for key, value in expected.items()), "failure-unplanned-owned-task", row["workload"])


class StopStore:
    """Private local intent/effect records, never accepted release custody."""
    def __init__(self, C, directory):
        self.C, self.directory = C, directory
        C.RESOURCE.CONTROL.no_symlinks(directory)

    def path(self, key):
        require(key in {"root", "service"} or re.fullmatch(r"task-[a-f0-9]{32}", key) is not None, "failure-storage-key-invalid")
        target = self.directory / (key + ".json")
        self.C.RESOURCE.CONTROL.no_symlinks(target)
        return target

    def read(self, key, request=None):
        target = self.path(key)
        if not target.exists(): return None
        value = self.C.read_json(target)
        require(isinstance(value, dict) and set(value) == {"schema", "key", "operation_id", "request", "request_sha256", "reserved_at"}
                and value["schema"] == "deploy/entity-smoke-failure-reservation/v1" and value["key"] == key and isinstance(value["request"], dict)
                and value["request_sha256"] == self.C.DEPLOY.fingerprint(value["request"]) and isinstance(value["operation_id"], str)
                and re.fullmatch(r"es-[a-f0-9]{32}", value["operation_id"]) is not None, "failure-reservation-not-confirmed", key)
        self.C.RESOURCE.timestamp(value["reserved_at"])
        require(request is None or self.C.RESOURCE.CONTROL.canonical(value["request"]) == self.C.RESOURCE.CONTROL.canonical(request), "failure-original-request-changed", key)
        return value

    def reserve(self, key, request):
        value = {"schema": "deploy/entity-smoke-failure-reservation/v1", "key": key, "operation_id": "es-" + uuid.uuid4().hex,
                 "request": request, "request_sha256": self.C.DEPLOY.fingerprint(request), "reserved_at": datetime.now(timezone.utc).isoformat()}
        if self.C.RESOURCE.write_exclusive(self.path(key), value): return value, True
        previous = self.read(key, request)
        require(previous is not None, "failure-reservation-not-confirmed", key)
        return previous, False


def task_key(arn):
    return "task-" + hashlib.sha256(arn.encode()).hexdigest()[:32]


def once(C, store, root, key, operation, payload, provider):
    request = {"root_sha256": C.DEPLOY.fingerprint(root), "operation": operation, "payload": payload}
    reservation, fresh = store.reserve(key, request)
    if fresh:
        selected = {**payload, **({"reason": reservation["operation_id"]} if operation == "stop-task" else {})}
        try: provider("ecs", operation, **selected)
        except SubmissionNotStarted: raise
        except Exception as failure:
            raise StopFailure("failure-submission-uncertain-reconcile-only", key, failure.code if isinstance(failure, C.InfrastructureFailure) else None) from None
    return reservation


def terminal_tasks(C, provider, selected):
    arns = sorted(selected["initial_tasks"])
    if not arns: return {}
    response = provider("ecs", "describe-tasks", cluster=C.RESOURCE.CLUSTER, tasks=arns)
    rows = response.get("tasks") if isinstance(response, dict) else None
    require(isinstance(rows, list) and len(rows) == len(arns) and not response.get("failures") and all(isinstance(row, dict) for row in rows)
            and {row.get("taskArn") for row in rows} == set(arns), "failure-original-task-observation-incomplete")
    result = {}
    for row in rows:
        expected = selected["initial_tasks"][row["taskArn"]]
        workload = expected["workload"]
        group = "service:" + C.RESOURCE.SERVICE if workload == "server" else "family:kanbien-core-platform-entity-smoke-" + workload
        require(row.get("taskDefinitionArn") == expected["definition"] and row.get("group") == group and row.get("launchType") == "FARGATE", "failure-original-task-identity-changed", workload)
        if row.get("lastStatus") != "STOPPED": return None
        try: stopped_at = C.RESOURCE.timestamp(row.get("stoppedAt")).isoformat()
        except C.RESOURCE.ResourceFailure as failure: raise StopFailure(failure.code, workload) from None
        result[row["taskArn"]] = {**expected, "state": "STOPPED", "stopped_at": stopped_at}
    return result


def validate_receipt(C, value, root, cache):
    fields = {"schema", "plan_sha256", "root", "realization_evidence", "realization_evidence_sha256", "facts"}
    packet = root["request"]["packet"]
    require(isinstance(value, dict) and set(value) == fields and value["schema"] == "deploy/entity-smoke-failure-stop-receipt/v1"
            and value["root"] == root and value["plan_sha256"] == packet["plan_sha256"], "failure-retained-receipt-not-confirmed")
    facts = value["facts"]
    expected = {"owned_service_desired_count", "owned_service_running_count", "owned_service_pending_count", "terminal_tasks", "other_service_configurations_sha256", "source_database_before", "source_database_after", "database_mutation", "independent_data_readback", "migration_history_readback", "observed_at"}
    require(isinstance(facts, dict) and set(facts) == expected and all(type(facts[key]) is int and facts[key] == 0 for key in ("owned_service_desired_count", "owned_service_running_count", "owned_service_pending_count"))
            and all(facts[key] is False for key in ("database_mutation", "independent_data_readback", "migration_history_readback")), "failure-retained-stopped-facts-invalid")
    selected = packet["intent"]
    require(facts["other_service_configurations_sha256"] == C.DEPLOY.fingerprint(selected["other_services"])
            and facts["source_database_before"] == selected["database_before"] and isinstance(facts["source_database_after"], dict)
            and facts["source_database_after"].get("state") in {"missing", "not-observed", "same-incarnation", "different-incarnation"}
            and not set(facts["source_database_after"]) - {"state", "condition", "identity_sha256", "configuration_sha256", "data_readback"}, "failure-retained-preservation-boundary-invalid")
    observed = C.RESOURCE.timestamp(facts["observed_at"])
    require(observed >= C.RESOURCE.timestamp(root["reserved_at"]), "failure-retained-observation-time-invalid")
    terminal = facts["terminal_tasks"]
    require(isinstance(terminal, dict) and set(terminal) == set(selected["initial_tasks"]), "failure-retained-task-set-invalid")
    for arn, actor in selected["initial_tasks"].items():
        row = terminal[arn]
        require(isinstance(row, dict) and set(row) == {"definition", "workload", "state", "stopped_at"} and all(row.get(key) == item for key, item in actor.items())
                and row["state"] == "STOPPED" and observed.timestamp() >= C.RESOURCE.timestamp(row["stopped_at"]).timestamp() - 60, "failure-retained-task-facts-invalid")
    reference = value["realization_evidence"]
    prefix = str((cache / "failure-realization").relative_to(C.ROOT)) + "/controlled-execution-"
    require(isinstance(reference, str) and reference.startswith(prefix) and re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):]) is not None, "failure-retained-gate-reference-invalid")
    path = C.ROOT / reference
    require(C.digest_file(path) == value["realization_evidence_sha256"], "failure-retained-gate-evidence-changed")
    retained_gate = C.read_json(path)
    require(isinstance(retained_gate, dict) and retained_gate.get("plan_sha256") == packet["plan_sha256"] and isinstance(retained_gate.get("facts"), dict), "failure-retained-gate-evidence-invalid")
    # The producer validated these exact bytes with the generic compiler when
    # the operation completed. This checks historical custody, not fresh gates.
    require([row.get("gate") for row in retained_gate["facts"].get("gate_evidence", [])] == list(C.GATE.GATE_ORDER[:7]), "failure-retained-gate-evidence-invalid")
    return value


def progress(C, store, root, context, provider, observe):
    """One pass; the owning bounded route decides when to observe again.

    The provider capability must already hold custody/source/plan guards. A
    service drains its own tasks at count zero even if unhealthy. No SQL, task
    launch, database reversal, permission repair or baseline write is possible.
    """
    selected = root["request"]["packet"]["intent"]
    verify_current(C, selected, context)
    own = context["service"]
    if own is not None and own["desired_count"] != 0:
        once(C, store, root, "service", "update-service", {"cluster": C.RESOURCE.CLUSTER, "service": selected["service"]["arn"], "desiredCount": 0}, provider)
        context = observe()
        verify_current(C, selected, context)
        if context["service"] is not None and context["service"]["desired_count"] != 0:
            return {"status": "pending", "context": context}
    for arn, expected in sorted(selected["task_stops"].items()):
        current = context["active_tasks"].get(arn)
        if current is None: continue
        require(all(current[key] == value for key, value in expected.items()), "failure-original-task-identity-changed", expected["workload"])
        once(C, store, root, task_key(arn), "stop-task", {"cluster": C.RESOURCE.CLUSTER, "task": arn}, provider)
        context = observe()
        verify_current(C, selected, context)
        if arn in context["active_tasks"]: return {"status": "pending", "context": context}
    own = context["service"]
    if own is not None and (own["desired_count"] != 0 or own["running_count"] != 0 or own["pending_count"] != 0): return {"status": "pending", "context": context}
    if context["active_tasks"]: return {"status": "pending", "context": context}
    terminal = terminal_tasks(C, provider, selected)
    if terminal is None: return {"status": "pending", "context": context}
    return {"status": "completed", "facts": {"owned_service_desired_count": 0, "owned_service_running_count": 0, "owned_service_pending_count": 0,
            "terminal_tasks": terminal, "other_service_configurations_sha256": C.DEPLOY.fingerprint(context["other_services"]),
            "source_database_before": selected["database_before"], "source_database_after": context["database"],
            "database_mutation": False, "independent_data_readback": False, "migration_history_readback": False, "observed_at": datetime.now(timezone.utc).isoformat()}}
