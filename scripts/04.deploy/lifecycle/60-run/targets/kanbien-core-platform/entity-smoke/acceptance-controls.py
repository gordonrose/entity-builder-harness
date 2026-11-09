#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.acceptance-control-custody
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Retain original safe control plans and seven-gate custody without provider mutation, current-health claims or a parallel gate engine.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.entity-smoke.collect-acceptance.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-route.py
import re


SCHEMA = "deploy/entity-smoke-retained-control-custody/v1"
SELECTIONS = {
    "initial-stop": ("failure-stop", "failure", "failure-route.py", "root", "update"),
    "initial-restart": ("initial-restart", "initial-restart", "restart-route.py", "start-runtime", "update"),
    "server-replacement": ("replacement", "replacement", "replacement-route.py", "server-replacement", "update"),
    "credential-replacement": ("credential-replacement", "credential-replacement", "replacement-route.py", "credential-replacement", "update"),
    "snapshot": ("snapshot", "snapshot", "snapshot-route.py", "create-recovery-point", "create"),
    "restore-deployment": ("restore-deploy", "restore-deploy", "restore-route.py", "execute-restore", "create"),
    "restore-cleanup": ("restore-cleanup", "restore-cleanup", "restore-route.py", "delete-restore", "delete"),
}
COMMON = {"schema", "target", "scope", "binding", "controller_sha256", "graph_sha256", "operator_sha256", "package_custody_reference"}
PLAN_EXTRA = {
    "initial-stop": {"account", "region", "purpose", "intent_sha256", "policy_sha256", "maximum_service_updates", "maximum_task_stops", "application_health_prerequisite", "database_mutation", "permission_mutation", "task_launch", "resource_deletion", "independent_data_readback", "migration_history_readback", "automatic_retry"},
    "initial-restart": {"request_sha256", "stop_sha256", "original_read_sha256", "policy_sha256", "configuration_sha256", "maximum_service_updates", "desired_count", "task_launch", "database_mutation", "permission_mutation", "resource_deletion", "automatic_retry", "independent_data_readback", "migration_history_readback"},
    "server-replacement": {"proof_stage", "request_sha256", "baseline_read_sha256", "prerequisites_sha256", "configuration_sha256", "maximum_task_stops", "database_mutation", "task_launch", "automatic_retry", "post_replacement_record_readback"},
    "credential-replacement": {"proof_stage", "request_sha256", "baseline_read_sha256", "prerequisites_sha256", "configuration_sha256", "maximum_task_stops", "database_mutation", "task_launch", "automatic_retry", "post_replacement_record_readback"},
    "snapshot": {"request_sha256", "history_sha256", "configuration_sha256", "maximum_snapshot_creates", "task_launch", "source_data_mutation", "resource_deletion", "automatic_retry", "isolated_restore_proven"},
    "restore-deployment": {"phase", "request_sha256", "snapshot_sha256", "history_sha256", "configuration_sha256", "template_sha256", "reader_sha256", "resource_count", "task_launch", "source_mutation", "automatic_retry", "scope_acceptance"},
    "restore-cleanup": {"phase", "request_sha256", "snapshot_sha256", "history_sha256", "configuration_sha256", "template_sha256", "reader_sha256", "resource_count", "task_launch", "source_mutation", "automatic_retry", "scope_acceptance"},
}
FALSE_FLAGS = {"application_health_prerequisite", "database_mutation", "permission_mutation", "task_launch", "resource_deletion", "independent_data_readback", "migration_history_readback", "automatic_retry", "post_replacement_record_readback", "source_data_mutation", "isolated_restore_proven", "source_mutation", "scope_acceptance"}


class ControlFailure(Exception):
    def __init__(self, code, item=None, field=None):
        super().__init__(code)
        self.code, self.item, self.field = code, item, field


def require(value, code, item=None, *, field=None):
    if not value: raise ControlFailure(code, item, field)


def hash_value(value):
    return isinstance(value, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", value) is not None


def validate_plan(A, name, plan, binding):
    require(isinstance(name, str) and name in SELECTIONS, "acceptance-control-selection-invalid")
    require(isinstance(plan, dict) and set(plan) == COMMON | PLAN_EXTRA[name], "acceptance-control-plan-fields-invalid", name)
    A.C.RESOURCE.validate_binding(binding)
    selected_binding = {key: item for key, item in binding.items() if key != "record_digest"} if name == "initial-stop" else binding
    schema = "failure" if name == "initial-stop" else "initial-restart" if name == "initial-restart" else "replacement" if name.endswith("replacement") else "snapshot" if name == "snapshot" else "restore"
    require(plan["schema"] == "deploy/entity-smoke-" + schema + "-plan/v1" and plan["target"] == "kanbien-core-platform"
            and plan["scope"] == "entity-smoke" and plan["binding"] == selected_binding, "acceptance-control-plan-binding-mismatch", name)
    nullable_reader = name == "restore-deployment"
    require(all(hash_value(item) for key, item in plan.items() if key.endswith("_sha256") and not (key == "reader_sha256" and nullable_reader)), "acceptance-control-plan-hash-invalid", name)
    require(all(plan[key] is False for key in FALSE_FLAGS & set(plan)), "acceptance-control-plan-effect-invalid", name)
    reference = plan["package_custody_reference"]
    require(isinstance(reference, str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,512}", reference), "acceptance-control-package-reference-invalid", name)
    if name == "initial-stop":
        require(plan["account"] == A.C.ALIGN.ACCOUNT and plan["region"] == A.C.ALIGN.REGION and plan["purpose"] == "first-release-stop-preserve-control"
                and type(plan["maximum_service_updates"]) is int and plan["maximum_service_updates"] in {0, 1}
                and type(plan["maximum_task_stops"]) is int and 0 <= plan["maximum_task_stops"] <= 32, "acceptance-control-plan-limit-invalid", name)
    elif name == "initial-restart":
        require(type(plan["maximum_service_updates"]) is int and plan["maximum_service_updates"] == 1
                and type(plan["desired_count"]) is int and plan["desired_count"] == 1, "acceptance-control-plan-limit-invalid", name)
    elif name.endswith("replacement"):
        require(plan["proof_stage"] == ("baseline" if name == "server-replacement" else "credential-recovery")
                and type(plan["maximum_task_stops"]) is int and plan["maximum_task_stops"] == 1, "acceptance-control-plan-limit-invalid", name)
    elif name == "snapshot":
        require(type(plan["maximum_snapshot_creates"]) is int and plan["maximum_snapshot_creates"] == 1, "acceptance-control-plan-limit-invalid", name)
    else:
        require(plan["phase"] == ("deploy" if name == "restore-deployment" else "cleanup")
                and type(plan["resource_count"]) is int and plan["resource_count"] == 8
                and (not nullable_reader or plan["reader_sha256"] is None), "acceptance-control-plan-limit-invalid", name)
    return plan


def validate(A, value, binding, *, name, plan_sha256, gate_sha256, operation_id):
    require(isinstance(value, dict) and set(value) == {"schema", "plan", "graph", "gate", "reservation"}
            and value["schema"] == SCHEMA, "acceptance-control-custody-required", name)
    plan = validate_plan(A, name, value["plan"], binding)
    require(A.digest(plan) == plan_sha256 and A.document_digest(value["gate"]) == gate_sha256, "acceptance-control-custody-hash-mismatch", name)
    graph_id, _, entrypoint, phase, operation = SELECTIONS[name]
    graph = value["graph"]
    A.C.GATE.validate_contract(graph)
    require(graph.get("id") == "entity-smoke-" + graph_id + "-control" and A.digest(graph) == plan["graph_sha256"]
            and isinstance(graph.get("artifacts"), list) and len(graph["artifacts"]) == 1 and graph["artifacts"][0].get("id") == graph_id + "-controller-source"
            and graph["artifacts"][0].get("entrypoint") == "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/" + entrypoint,
            "acceptance-control-graph-binding-mismatch", name)
    counts = {key: 0 for key in ("create", "update", "delete", "replace", "broaden-permission")}
    counts[operation] = plan["maximum_service_updates"] + plan["maximum_task_stops"] if name == "initial-stop" else plan["resource_count"] if name.startswith("restore-") else 1
    require(graph["change_shape"]["allowed_operation_classes"] == [operation]
            and set(graph["change_shape"]["forbidden_operation_classes"]) == set(counts) - {operation}, "acceptance-control-operation-class-mismatch", name)
    A.validate_gate(graph, value["gate"], plan_sha256, {graph_id + "-controller-source": plan["controller_sha256"]}, counts, item=name, family="control")
    reservation = value["reservation"]
    require(isinstance(reservation, dict) and set(reservation) == {"phase", "operation_id", "request_sha256", "reserved_at"}
            and reservation["phase"] == phase and reservation["operation_id"] == operation_id
            and isinstance(operation_id, str) and re.fullmatch(r"es-[a-f0-9]{32}", operation_id)
            and hash_value(reservation["request_sha256"]), "acceptance-control-reservation-mismatch", name)
    reserved = A.T.RUNNER.EVIDENCE.timestamp(reservation["reserved_at"])
    completed = A.T.RUNNER.EVIDENCE.timestamp(value["gate"]["facts"]["gate_evidence"][-1]["timestamp"])
    require((reserved - completed).total_seconds() <= 60, "acceptance-control-gate-predates-reservation", name)
    return value


def capture(route, A, name, receipt, graph, binding, cache, controller):
    require(isinstance(name, str) and name in SELECTIONS, "acceptance-control-selection-invalid")
    if name == "initial-stop":
        reservation = receipt["root"]
        packet = reservation["request"]["packet"]
    else:
        reservation, packet = receipt["result"]["reservation"], receipt["packet"]
    plan = packet["plan"]
    require(plan.get("controller_sha256") == controller, "acceptance-control-current-source-mismatch", name)
    reference = receipt.get("realization_evidence")
    prefix = str((cache / (SELECTIONS[name][1] + "-realization")).relative_to(route.C.ROOT)) + "/controlled-execution-"
    require(isinstance(reference, str) and reference.startswith(prefix) and re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):]), "acceptance-control-gate-reference-invalid", name)
    path = route.C.ROOT / reference
    route.C.RESOURCE.CONTROL.no_symlinks(path)
    require(route.C.digest_file(path) == receipt["realization_evidence_sha256"], "acceptance-control-original-gate-changed", name)
    request_digest = reservation["request_sha256"]
    if isinstance(request_digest, str) and re.fullmatch(r"[a-f0-9]{64}", request_digest): request_digest = "sha256:" + request_digest
    value = {"schema": SCHEMA, "plan": plan, "graph": graph, "gate": route.C.read_json(path), "reservation": {
        "phase": reservation["key"] if name == "initial-stop" else reservation["phase"], "operation_id": reservation["operation_id"],
        "request_sha256": request_digest, "reserved_at": reservation["reserved_at"]}}
    return validate(A, value, binding, name=name, plan_sha256=receipt["plan_sha256"] if name == "initial-stop" else packet["plan_sha256"],
                    gate_sha256=receipt["realization_evidence_sha256"], operation_id=reservation["operation_id"])


def validate_connections(A, value):
    """Connect already owner-validated receipts; no provider or current file IO."""
    tasks, controls, runtime = value["tasks"], value["controls"], value["runtime"]
    timestamp = A.T.RUNNER.EVIDENCE.timestamp
    binding, basis = value["binding"], value["controller_basis"]
    declaration = str((A.C.CONTRACT.parent / "declaration-contract.yml").relative_to(A.C.ROOT))
    sources = {declaration, str((A.C.CONTRACT.parent.parent.parent / "scope-index.yml").relative_to(A.C.ROOT)),
        "scripts/04.deploy/lifecycle/60-run/release-succession/script.py", "scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.py"}
    require(isinstance(basis, dict) and set(basis) == {"controller", "custody_sources"} and basis["controller"] == value["controller_sha256"]
            and isinstance(basis["custody_sources"], dict) and set(basis["custody_sources"]) == sources
            and all(hash_value(item) for item in basis["custody_sources"].values())
            and basis["custody_sources"][declaration] == binding["configuration_contract_sha256"], "acceptance-controller-basis-invalid")
    def plan(name): return controls[name]["custody"]["plan"]
    def facts(name): return controls[name]["facts"]
    def reserved(name): return controls[name]["custody"]["reservation"]["reserved_at"]
    def packet(name, phase="operation"): return tasks[name][phase]["packet"]
    def receipt(name, phase="operation"): return packet(name, phase)["receipt"]
    def stopped(name): return receipt(name)["task"]["stopped_at"]
    def later(first, second, item):
        require(timestamp(first) >= timestamp(second), "acceptance-proof-order-invalid", item)
    def task_after(name, floor=None):
        if floor is not None:
            later(receipt(name)["task"]["created_at"], floor, name)
        if "preflight" in tasks[name]:
            later(receipt(name)["task"]["created_at"], receipt(name, "preflight")["task"]["stopped_at"], name)
            if floor is not None:
                later(receipt(name, "preflight")["task"]["created_at"], floor, name)
                later(tasks[name]["operation"]["admission"]["required_after"], floor, name)
    attempts, jobs, actors = set(), set(), {}
    for name, pair in tasks.items():
        workload = A.TASKS[name][1]
        for task in pair.values():
            selected = task["packet"]
            attempt, arn = selected["reservation"]["operation_id"], selected["receipt"]["task"]["arn"]
            require(attempt not in attempts and arn not in jobs, "acceptance-proof-attempt-reused", name)
            attempts.add(attempt); jobs.add(arn)
            request = selected["reservation"]["request"]
            actor = (request["definition"], request["security_group"], tuple(sorted(request["subnets"])))
            if workload in actors:
                for field, before, after in zip(("definition", "security_group", "subnets"), actors[workload], actor):
                    require(before == after, "acceptance-workload-binding-drift", name, field=field)
            actors[workload] = actor
    for name, control in controls.items():
        require(control["operation_id"] not in attempts, "acceptance-proof-attempt-reused", name)
        attempts.add(control["operation_id"])
        expected = A.digest(basis) if name in {"initial-stop", "initial-restart"} else value["controller_sha256"]
        require(plan(name)["controller_sha256"] == expected and plan(name)["package_custody_reference"] == value["package"]["receipt_reference"], "acceptance-control-source-attribution-mismatch", name)
    prefix = ("bootstrap", "migration", "grant-runtime", "baseline-permissions", "original-record", "lifecycle", "collision", "baseline-read")
    previous = None
    for name in prefix:
        task_after(name, previous); previous = stopped(name)
    require(plan("server-replacement")["baseline_read_sha256"] == A.digest(packet("baseline-read")), "acceptance-control-predecessor-mismatch", "server-replacement")
    later(reserved("server-replacement"), previous, "server-replacement")
    task_after("replacement-read", max(reserved("server-replacement"), facts("server-replacement")["successor_started_at"], key=timestamp))
    later(reserved("initial-stop"), stopped("replacement-read"), "initial-stop")
    later(facts("initial-stop")["observed_at"], reserved("initial-stop"), "initial-stop")
    require(plan("initial-restart")["stop_sha256"] == controls["initial-stop"]["source_receipt_sha256"]
            and plan("initial-restart")["original_read_sha256"] == A.digest(packet("replacement-read")), "acceptance-control-predecessor-mismatch", "initial-restart")
    later(reserved("initial-restart"), facts("initial-stop")["observed_at"], "initial-restart")
    server = facts("initial-restart")["server"]
    later(server["created_at"], reserved("initial-restart"), "initial-restart")
    task_after("initial-read", server["started_at"])
    task_after("migration-state", stopped("initial-read"))
    task_after("permission-state", stopped("migration-state"))
    task_after("credential-revoke", stopped("permission-state"))
    negative = tasks["credential-unready"]["operation"]
    revoke = packet("credential-revoke")
    require(negative["admission"]["revocation"] == {"reservation": revoke["reservation"], "receipt": revoke["receipt"], "label": binding["proof_label"]}, "acceptance-original-revocation-mismatch", "credential-unready")
    task_after("credential-unready", stopped("credential-revoke"))
    task_after("credential-restore", stopped("credential-unready"))
    require(plan("credential-replacement")["baseline_read_sha256"] == A.digest(packet("initial-read"))
            and facts("credential-replacement")["original_task"] == server["task"], "acceptance-control-predecessor-mismatch", "credential-replacement")
    later(reserved("credential-replacement"), stopped("credential-restore"), "credential-replacement")
    task_after("credential-read", facts("credential-replacement")["successor_started_at"])
    task_after("credential-permissions", stopped("credential-read"))
    later(reserved("snapshot"), receipt("credential-permissions")["collected_at"], "snapshot")
    later(facts("snapshot")["snapshot_created_at"], reserved("snapshot"), "snapshot")
    later(reserved("restore-deployment"), facts("snapshot")["snapshot_created_at"], "restore-deployment")
    later(facts("restore-deployment")["observed_at"], reserved("restore-deployment"), "restore-deployment")
    task_after("restore-read", facts("restore-deployment")["observed_at"])
    later(reserved("restore-cleanup"), receipt("restore-read")["collected_at"], "restore-cleanup")
    later(facts("restore-cleanup")["observed_at"], reserved("restore-cleanup"), "restore-cleanup")
    task_after("final-read", facts("restore-cleanup")["observed_at"])
    child = value["restored_binding"]
    for name in ("restore-deployment", "restore-cleanup"):
        require(plan(name)["snapshot_sha256"] == controls["snapshot"]["source_receipt_document_sha256"]
                and plan(name)["history_sha256"] == plan("snapshot")["history_sha256"]
                and plan(name)["template_sha256"] == child["permission_contract_sha256"], "acceptance-restore-custody-mismatch", name)
    require(plan("restore-cleanup")["reader_sha256"] == A.digest(packet("restore-read")), "acceptance-restore-reader-predecessor-mismatch", "restore-cleanup")
    definition = r"arn:aws:ecs:" + A.C.RESOURCE.REGION + ":" + A.C.RESOURCE.ACCOUNT + r":task-definition/kanbien-core-platform-entity-smoke-server:[1-9][0-9]*"
    task = r"arn:aws:ecs:" + A.C.RESOURCE.REGION + ":" + A.C.RESOURCE.ACCOUNT + r":task/" + A.C.RESOURCE.CLUSTER + r"/[a-f0-9]{32}"
    for field, pattern in (("definition", definition), ("task", task)):
        require(isinstance(runtime[field], str) and re.fullmatch(pattern, runtime[field]), "acceptance-current-server-binding-invalid", "runtime", field=field)
    require(timestamp(runtime["started_at"]) == timestamp(facts("credential-replacement")["successor_started_at"]), "acceptance-current-server-time-mismatch", "runtime", field="started_at")
    require(timestamp(runtime["created_at"]) >= timestamp(reserved("credential-replacement")), "acceptance-current-server-time-mismatch", "runtime", field="created_at")
    for actor in facts("initial-stop")["terminal_tasks"].values():
        if actor["workload"] == "server": require(actor["definition"] == runtime["definition"], "acceptance-stopped-server-definition-mismatch", "initial-stop")
    return value
