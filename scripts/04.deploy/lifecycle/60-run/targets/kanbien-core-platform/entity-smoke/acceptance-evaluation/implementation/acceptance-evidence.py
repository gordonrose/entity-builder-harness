#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.acceptance-evidence
#   version: 3
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Preserve checked task, admission and historical gate evidence for the isolated feature without turning captured proof into current health or release promotion.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from datetime import timedelta
import hashlib
import importlib.util
from pathlib import Path
import re
from types import SimpleNamespace


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


T = module("entity_smoke_acceptance_evidence_task", (Path(__file__).resolve().parents[2] / "task-execution/implementation/task-route.py"))
C = T.C
POLICY = module("entity_smoke_shared_proof_policy", C.ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/proof-policy.py")
SCHEMA = "deploy/entity-smoke-retained-task-proof/v1"
# Explicit selections, not all operations that might later be added to a runner.
TASKS = {
    "bootstrap": ("baseline", "administration", ("bootstrap",)),
    "migration": ("baseline", "migration", ("apply",)),
    "grant-runtime": ("baseline", "administration", ("grant-runtime",)),
    "baseline-permissions": ("baseline", "database-proof", ("permissions",)),
    "original-record": ("baseline", "verifier", ("create", "observe-create")),
    "lifecycle": ("baseline", "verifier", ("lifecycle",)),
    "collision": ("baseline", "database-proof", ("collision",)),
    "baseline-read": ("baseline", "verifier", ("read",)),
    "replacement-read": ("server-replacement", "verifier", ("read",)),
    "initial-read": ("initial-recovery", "verifier", ("read",)),
    "migration-state": ("initial-recovery", "administration", ("observe-migration-state",)),
    "permission-state": ("credential-recovery", "administration", ("observe-permissions",)),
    "credential-revoke": ("credential-recovery", "administration", ("revoke-runtime",)),
    "credential-unready": ("credential-recovery", "verifier", ("unready",)),
    "credential-restore": ("credential-recovery", "administration", ("restore-runtime",)),
    "credential-read": ("credential-recovery", "verifier", ("read",)),
    "credential-permissions": ("credential-recovery", "database-proof", ("permissions",)),
    "restore-read": ("isolated-restore", "restore-reader", ("restore-read",)),
    "final-read": ("acceptance", "verifier", ("read",)),
}


EvidenceFailure = POLICY.PolicyFailure

def require(value, code, item=None):
    if not value: raise EvidenceFailure(code, item)


def digest(value):
    return "sha256:" + hashlib.sha256(T.RUNNER.CONTROL.canonical(value)).hexdigest()


def document_digest(value):
    return "sha256:" + hashlib.sha256(T.RUNNER.CONTROL.canonical(value) + b"\n").hexdigest()


# Compatibility names retain the v1 feature packet; comparison has one owner.
recovery_input_paths = POLICY.recovery_input_paths
recovery_input_tree = POLICY.recovery_input_tree


def recovery_applicability(previous, candidate, paths, *, root=None):
    result = POLICY.recovery_applicability(previous, candidate, paths,
        root=C.ROOT if root is None else root, additional_bindings=("proof_label", "record_digest"))
    return {**result, "schema": "deploy/entity-smoke-recovery-applicability/v1"}


def preflight_label(binding, stage, workload, operation, *, delivery=None, namespace_delivery=None):
    namespace = delivery or namespace_delivery
    if namespace is not None:
        return C.delivery_preflight_label(namespace, stage, workload, operation)
    suffix = "" if stage == "baseline" else ":" + stage
    original = "entity-smoke-" + hashlib.sha256((binding["proof_label"] + ":" + workload + ":" + operation + ":preflight" + suffix).encode()).hexdigest()[:24]
    # Historical selection only, not launch authority: the public task route
    # requires the original failure and actual repair receipt before recovery.
    if (binding["proof_label"], workload, operation, stage) == (T.IMAGE_REPAIR.LABEL, "administration", "bootstrap", "baseline"):
        return "entity-smoke-" + hashlib.sha256((original + ":" + T.IMAGE_REPAIR.FAILURE_ID + ":image-delivery-recovery-1").encode()).hexdigest()[:24]
    return C.TRANSITION.replacement_label(None, SimpleNamespace(proof_label=binding["proof_label"], workload=workload, operation=operation, proof_stage=stage), original)


def validate_gate(graph, gate, plan_sha256, artifacts, counts, *, item, family="task"):
    """Reuse the original completion owner; additionally close archived fields."""
    C.GATE.validate_contract(graph)
    require(isinstance(gate, dict) and isinstance(gate.get("facts"), dict)
            and set(gate["facts"]) == {"schema", "contract_id", "gate_evidence", "component_evidence", "artifact_bindings"},
            "acceptance-" + family + "-gate-fields-invalid", item)
    for key, fields in (("gate_evidence", {"gate", "check_id", "timestamp", "verdict", "input_sha256"}),
                        ("component_evidence", {"component_id", "component_kind", "check_id", "timestamp", "verdict", "input_sha256"}),
                        ("artifact_bindings", {"component_id", "immutable_reference", "check_id", "timestamp", "verdict"})):
        rows = gate["facts"].get(key)
        require(isinstance(rows, list) and all(isinstance(row, dict) and set(row) == fields for row in rows),
                "acceptance-" + family + "-gate-fields-invalid", item)
    T.COMPLETION.validate_gate(T.dependencies(), graph, gate, plan_sha256, artifacts)
    summary = gate["change_summary"]
    require(isinstance(summary, dict) and set(summary) == {"schema", "contract_id", "check_id", "timestamp", "input_sha256", "operation_counts"}
            and summary["schema"] == C.GATE.CHANGE_SCHEMA and summary["contract_id"] == graph["id"]
            and summary["check_id"] in graph["gates"][4]["evidence"]
            and summary["input_sha256"] == C.GATE.evidence_bindings(graph, gate["facts"])["gates"]["change-set"]
            and isinstance(summary["operation_counts"], dict) and set(summary["operation_counts"]) == set(counts)
            and all(type(value) is int for value in summary["operation_counts"].values())
            and summary["operation_counts"] == counts, "acceptance-" + family + "-change-summary-invalid", item)
    C.GATE.safe_timestamp(summary["timestamp"], "acceptance-" + family + "-change-summary-time-invalid")
    return gate


def recovered_observation_label(value, request, base):
    """Validate archived negative custody without consulting current AWS state."""
    recovery = value["observation_recovery"]
    require(value["name"] == "restore-read" and isinstance(recovery, dict)
        and set(recovery) == {"plan", "failure"}, "acceptance-observation-recovery-invalid")
    plan, failure = recovery["plan"], recovery["failure"]
    require(isinstance(plan, dict) and C.DEPLOY.fingerprint(plan) == value["packet"]["plan_sha256"]
        and plan.get("binding") == value["packet"]["binding"]
        and plan.get("request_sha256") == C.DEPLOY.fingerprint(request)
        and plan.get("controller_sha256") == value["controller_sha256"]
        and isinstance(failure, dict) and set(failure) == {"schema", "reservation", "parent_sha256", "terminal", "report"}
        and failure["schema"] == "deploy/terminal-observation-recovery/v1"
        and plan.get("parent_deployment_sha256") == failure["parent_sha256"]
        and plan.get("failed_observation_sha256") == document_digest(failure), "acceptance-observation-recovery-invalid")
    original = failure["reservation"]
    expected = {**request, "proof_label": base, "deadline_seconds": 90,
        "environment": {"ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "preflight", "ENTITY_SMOKE_PROOF_LABEL": base}}
    T.RUNNER.PREFLIGHT.validate_launch(expected)
    require(isinstance(original, dict) and set(original) == {"schema", "operation_id", "request", "request_sha256", "reserved_at"}
        and original.get("schema") == "deploy/entity-smoke-task-reservation/v1"
        and isinstance(original.get("operation_id"), str) and re.fullmatch(r"es-[a-f0-9]{32}", original["operation_id"])
        and original.get("request") == expected and original.get("request_sha256") == hashlib.sha256(T.RUNNER.CONTROL.canonical(expected)).hexdigest(),
        "acceptance-observation-recovery-invalid")
    terminal = failure["terminal"]
    identity = {key: expected[key] for key in ("source_revision", "image_digest", "workload")}
    identity.update(operation_id=original.get("operation_id"), request_sha256=original["request_sha256"],
        operation="preflight", proof_label_sha256=hashlib.sha256(base.encode()).hexdigest())
    try: selected = "entity-smoke-" + POLICY.failed_observation_id(base, terminal, identity, dependent_reserved=False)
    except POLICY.PolicyFailure as error: raise EvidenceFailure(error.code) from None
    report = failure["report"]
    require(terminal.get("task_definition") == expected["definition"]
        and isinstance(terminal.get("task_arn"), str) and re.fullmatch(r"arn:aws:ecs:" + T.RUNNER.CONTROL.REGION + ":" + T.RUNNER.CONTROL.ACCOUNT + ":task/" + T.RUNNER.CONTROL.CLUSTER + r"/[a-f0-9]{32}", terminal["task_arn"])
        and isinstance(report, dict) and report == T.RUNNER.EVIDENCE.failure_report(T.RUNNER.EVIDENCE.TerminalTaskFailure(
        terminal, report.get("diagnostic"), report.get("related_diagnostics"), report.get("observations")))
        and T.RUNNER.EVIDENCE.timestamp(terminal["stopped_at"]) >= T.RUNNER.EVIDENCE.timestamp(original["reserved_at"])
        and T.RUNNER.EVIDENCE.timestamp(value["packet"]["reservation"]["reserved_at"]) >= T.RUNNER.EVIDENCE.timestamp(terminal["stopped_at"])
        and plan.get("preflight_label") == selected, "acceptance-observation-recovery-invalid")
    return selected


def validate_task(value, collection_binding, *, expected_binding=None, delivery=None, namespace_delivery=None):
    """Pure historical validation; no provider access or today's source hash."""
    fields = {"schema", "name", "stage", "phase", "requested_operation", "controller_sha256", "collection_binding", "graph", "packet", "completion", "gate", "admission"}
    if isinstance(value, dict) and "observation_recovery" in value: fields.add("observation_recovery")
    if delivery is not None:
        C.RESOURCE.validate_delivery(delivery)
        fields.add("delivery")
        require(isinstance(value, dict) and value.get("delivery") == delivery,
                "acceptance-task-delivery-mismatch")
    require(isinstance(value, dict) and set(value) == fields and value["schema"] == SCHEMA, "acceptance-task-envelope-invalid")
    name = value["name"]
    require(isinstance(name, str) and name in TASKS, "acceptance-task-selection-invalid")
    if namespace_delivery is not None:
        C.RESOURCE.validate_delivery(namespace_delivery)
        require(name == "restore-read" and delivery is None
            and namespace_delivery["proof_label"] == collection_binding["proof_label"]
            and all(namespace_delivery["candidate"][key] == collection_binding[key] for key in ("source_revision", "image_digest")), "acceptance-task-delivery-mismatch")
    stage, workload, allowed_operations = TASKS[name]
    operation, phase = value["requested_operation"], value["phase"]
    require(value["stage"] == stage and isinstance(operation, str) and operation in allowed_operations and isinstance(phase, str) and phase in {"preflight", "operation"}
            and not (name == "credential-unready" and phase != "operation"), "acceptance-task-selection-invalid", name)
    C.RESOURCE.validate_binding(collection_binding)
    require(value["collection_binding"] == collection_binding and isinstance(value["controller_sha256"], str)
            and re.fullmatch(r"sha256:[a-f0-9]{64}", value["controller_sha256"]), "acceptance-task-source-invalid", name)
    packet = value["packet"]
    packet_fields = {"schema", "plan_sha256", "binding", "reservation", "receipt"} | ({"delivery", "plan", "prerequisites"} if delivery is not None else set())
    require(isinstance(packet, dict) and set(packet) == packet_fields
            and packet["schema"] in ({"deploy/entity-smoke-task-step/v2", "deploy/entity-smoke-task-step/v3"} if delivery is not None else {"deploy/entity-smoke-task-step/v1"}), "acceptance-task-packet-invalid", name)
    parent = {key: item for key, item in collection_binding.items() if key != "record_digest"}
    legacy = delivery is None and C.TRANSITION.historical(packet, value["completion"])
    source_transition = legacy and any(packet["binding"].get(key) != parent[key] for key in ("source_revision", "image_digest"))
    if source_transition:
        C.TRANSITION.compatible(C, packet["binding"], parent)
        expected_binding = packet["binding"]
    expected_binding = parent if expected_binding is None else expected_binding
    C.RESOURCE.validate_binding(expected_binding, record_required=False)
    require(packet["binding"] == expected_binding, "acceptance-task-binding-mismatch", name)
    if delivery is not None:
        selection = SimpleNamespace(workload=workload, operation=operation, phase=phase, proof_stage=stage)
        T.STEPS.validate_delivery_step(T.dependencies(), packet, expected_binding, delivery, selection)
    # The clone reader alone has a distinct incarnation and permission contract.
    require(source_transition or all(expected_binding[key] == parent[key] for key in parent if name != "restore-read" or key not in {"permission_contract_sha256", "dependency_incarnation_sha256"})
            and (name == "restore-read" or expected_binding == parent), "acceptance-task-parent-mismatch", name)
    reservation, receipt = packet["reservation"], packet["receipt"]
    checked = T.RUNNER.EVIDENCE.validate_retained(receipt, reservation)
    require(checked == receipt, "acceptance-task-receipt-mismatch", name)
    request = reservation["request"]
    require(request["workload"] == workload and all(request[key] == expected_binding[key] for key in parent if key != "proof_label"), "acceptance-task-request-binding-mismatch", name)
    actual_operation = ("ready" if workload == "verifier" else "preflight") if phase == "preflight" else operation
    label = preflight_label(parent, stage, workload, operation, delivery=delivery, namespace_delivery=namespace_delivery) if phase == "preflight" else (
        C.delivery_operation_label(delivery, workload, operation) if delivery is not None else parent["proof_label"])
    if delivery is not None and phase == "preflight": label = packet["plan"]["preflight_label"]
    recovered_label = None
    if "observation_recovery" in value:
        base = (C.delivery_preflight_label(namespace_delivery, stage, workload, operation) if namespace_delivery is not None
            else "entity-smoke-" + hashlib.sha256((parent["proof_label"] + ":restore-reader:restore-read:preflight:isolated-restore").encode()).hexdigest()[:24])
        recovered_label = recovered_observation_label(value, request, base)
        if phase == "preflight": label = recovered_label
    require(request["environment"][T.RUNNER.CONTROL.OPERATIONS[workload][0]] == actual_operation
            and request["proof_label"] == label, "acceptance-task-request-selection-mismatch", name)
    if workload in {"verifier", "database-proof", "restore-reader"}:
        require(request["environment"].get("ENTITY_SMOKE_PROOF_LABEL") == label, "acceptance-task-label-mismatch", name)
    original = name in {"original-record", "collision", "baseline-read", "replacement-read", "initial-read", "credential-read", "restore-read", "final-read"}
    if phase == "operation" and original:
        require(receipt["result"].get("record_digest") == collection_binding["record_digest"], "acceptance-original-record-mismatch", name)
    if phase == "operation" and name == "migration-state":
        require(receipt["result"].get("code") == "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED", "acceptance-migration-state-not-applied", name)
    graph, gate, completion = value["graph"], value["gate"], value["completion"]
    C.GATE.validate_contract(graph)
    require(graph.get("id") == T.GRAPH.contract(workload, C.GATE, negative=name == "credential-unready")["id"], "acceptance-task-graph-selection-mismatch", name)
    require(isinstance(completion, dict) and set(completion) == {"schema", "step_sha256", "plan_sha256", "realization_evidence", "realization_evidence_sha256"}
            and completion["schema"] == "deploy/entity-smoke-task-completion/v1" and completion["plan_sha256"] == packet["plan_sha256"]
            and completion["step_sha256"] == document_digest(packet) and completion["realization_evidence_sha256"] == document_digest(gate), "acceptance-task-completion-mismatch", name)
    namespace_owner = delivery or namespace_delivery
    namespace = "" if namespace_owner is None else "/releases/" + namespace_owner["delivery_id"]
    require(isinstance(completion["realization_evidence"], str) and re.fullmatch(
        r"\.cache/entity-smoke-live/" + re.escape(parent["proof_label"]) + namespace + r"/task-realization/controlled-execution-[a-f0-9]{32}\.json",
        completion["realization_evidence"]), "acceptance-task-gate-reference-invalid", name)
    expected = {row["id"]: value["controller_sha256"] if row["id"] == T.GRAPH.CONTROLLER_SOURCE else expected_binding["image_digest"] for row in graph["artifacts"]}
    validate_gate(graph, gate, packet["plan_sha256"], expected,
                  {"create": 1, "update": 0, "delete": 0, "replace": 0, "broaden-permission": 0}, item=name)
    admission = value["admission"]
    if phase == "preflight": require(admission is None, "acceptance-preflight-admission-unexpected", name)
    elif name == "credential-unready": T.RUNNER.UNREADY.validate_admission(admission, reservation)
    else:
        T.RUNNER.PREFLIGHT.validate_admission(admission, reservation)
        selected_label = packet["plan"]["preflight_label"] if delivery is not None else preflight_label(parent, stage, workload, operation, namespace_delivery=namespace_delivery)
        require(admission["preflight"]["label"] == (recovered_label or selected_label), "acceptance-preflight-stage-mismatch", name)
    return value


def fresh_final(value, cleanup_at, current_time):
    require(value.get("name") == "final-read" and value.get("phase") == "operation", "acceptance-final-read-required")
    receipt = value["packet"]["receipt"]
    timestamp = T.RUNNER.EVIDENCE.timestamp
    created, stopped, collected, current = (timestamp(receipt["task"]["created_at"]), timestamp(receipt["task"]["stopped_at"]), timestamp(receipt["collected_at"]), timestamp(current_time))
    require(created >= timestamp(cleanup_at) and stopped >= created and collected >= stopped, "acceptance-final-read-predates-cleanup")
    require(-timedelta(seconds=60) <= current - collected <= timedelta(seconds=900), "acceptance-final-read-not-fresh")
    return receipt


def capture_task(route, context, args, provider, name, collection_binding, *, historical=True):
    require(name in TASKS and (args.proof_stage, args.workload) == TASKS[name][:2]
            and args.operation in TASKS[name][2], "acceptance-task-selection-invalid", name)
    packet = route.STEPS.observe_packet(route.dependencies(), context, args, provider, historical=historical)
    require(packet is not None, "acceptance-task-completion-required", name)
    step = route.STEPS.path(context, args)
    completion = route.C.read_json(route.COMPLETION.path(step))
    gate = route.C.read_json(route.C.ROOT / completion["realization_evidence"])
    admission = None
    if args.phase == "operation":
        selected = route.RUNNER.UNREADY.path_for(context["cache"] / "task-receipts", packet["reservation"]) if name == "credential-unready" else route.RUNNER.PREFLIGHT.admission_path(context["cache"] / "task-receipts", packet["reservation"])
        admission = route.C.read_json(selected)
    value = {"schema": SCHEMA, "name": name, "stage": args.proof_stage, "phase": args.phase, "requested_operation": args.operation,
             "controller_sha256": route.COMPLETION.controller_for(route.dependencies(), packet, completion, context["artifact"]), "collection_binding": collection_binding,
             "graph": route.GRAPH.retained(route.C, route.GRAPH.contract(args.workload, route.C.GATE, negative=name == "credential-unready"), gate=gate),
             "packet": packet, "completion": completion, "gate": gate, "admission": admission}
    delivery = context.get("delivery")
    if delivery is not None: value["delivery"] = delivery
    if context.get("failed_observation"):
        plan = route.C.read_json(context["cache"] / "restore-reader-plans" / (packet["plan_sha256"].removeprefix("sha256:") + ".json"))
        value["observation_recovery"] = {"plan": plan, "failure": context["failed_observation"]}
    return validate_task(value, collection_binding, expected_binding=context["binding"], delivery=delivery,
        namespace_delivery=context.get("recovery_delivery"))


def immutable_json(path, value):
    """Content-addressed owned evidence only; no overwrite or promotion."""
    C.RESOURCE.CONTROL.no_symlinks(path)
    if not C.RESOURCE.write_exclusive(path, value):
        expected = T.RUNNER.CONTROL.canonical(value) + b"\n"
        try:
            with path.open("rb") as stream: previous = stream.read(len(expected) + 1)
        except OSError: raise EvidenceFailure("acceptance-retained-proof-unavailable") from None
        require(previous == expected, "acceptance-retained-proof-conflict")
    return {"path": path, "sha256": document_digest(value)}
