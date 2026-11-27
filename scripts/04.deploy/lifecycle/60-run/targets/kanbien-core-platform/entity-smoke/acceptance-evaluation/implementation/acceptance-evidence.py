#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.acceptance-evidence
#   version: 4
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-27"
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
SCHEDULING = module("entity_smoke_shared_scheduling_profile", C.ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof.py")
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
METADATA_TASKS = {
    "scheduling-prefix": ("scheduling-preparation", "administration", ("observe-scheduling-prefix",)),
    "scheduling-migration": ("scheduling-migration", "migration", ("apply",)),
    "scheduling-state": ("scheduling-preparation", "administration", ("observe-scheduling-state",)),
    "scheduling-grant": ("scheduling-preparation", "administration", ("grant-scheduling-access",)),
    "scheduling-permissions": ("scheduling-preparation", "administration", ("prove-scheduling-access",)),
}
SYNTHETIC_TASKS = {operation: ("scheduling-proof", "administration" if operation == "observe-scheduling-proof" else "verifier", (operation,))
    for operation in ("scheduling-create", "scheduling-observe-create", "scheduling-delete", "scheduling-restore", "observe-scheduling-proof")}
PROFILE_NEUTRAL_TASKS = frozenset({"bootstrap", "migration", "grant-runtime", "restore-read", *METADATA_TASKS})


EvidenceFailure = POLICY.PolicyFailure

def require(value, code, item=None):
    if not value: raise EvidenceFailure(code, item)


def profile(value=None):
    try: return SCHEDULING.profile(value)
    except SCHEDULING.ProofFailure: raise EvidenceFailure("acceptance-qualification-profile-invalid") from None


def tasks(value=None, *, metadata=False, synthetic=False):
    selected = SCHEDULING.database_proof(profile(value))
    return {**TASKS, "migration-state": (selected["stage"], "administration", (selected["operation"],)), **(METADATA_TASKS if metadata else {}), **(SYNTHETIC_TASKS if synthetic else {})}


def task_profile(name, value=None):
    return None if name in PROFILE_NEUTRAL_TASKS else profile(value)


def database_result(result, value=None, *, manifest_sha256=None):
    selected = SCHEDULING.database_proof(profile(value))
    require(result.get("code") == selected["result_code"], "acceptance-migration-state-not-applied", "migration-state")
    if value is not None:
        try: return SCHEDULING.complete_database_state(result.get("database_state"), manifest_sha256=manifest_sha256)
        except SCHEDULING.ProofFailure as failure: raise EvidenceFailure(failure.code, "migration-state") from None


def scheduling_database_readiness(receipt_path, proof_label, provider, *, required_after, source_revision, image_digest, expected_predecessor=None):
    """Reobserve native completed metadata tasks for the initial empty gate.

    Preparation authenticates package/source, current stack, database identity,
    roles and task configuration. Its local gates do not launch any task. The
    caller must supply its retained control boundary as required_after.
    """
    phase = "selection"
    try:
        arguments = ["--receipt", str(receipt_path), "--proof-label", proof_label, "--workload", "administration",
            "--operation", "prove-scheduling-access", "--proof-stage", "scheduling-preparation"]
        if expected_predecessor is not None: arguments += ["--expected-predecessor", expected_predecessor]
        args = T.parse(arguments)
        phase = "current-binding"
        context = T.prepare(args, provider)
        binding = {key: context["binding"][key] for key in ("source_revision", "image_digest", "dependency_incarnation_sha256")}
        require((binding["source_revision"], binding["image_digest"]) == (source_revision, image_digest), "scheduling-readiness-identity-mismatch")
        timestamp, checked_at = T.RUNNER.EVIDENCE.timestamp, C.now()
        observations = {}
        for name, operation in (("state", "observe-scheduling-state"), ("grant", "grant-scheduling-access"), ("prove", "prove-scheduling-access")):
            phase = name
            selected = SimpleNamespace(**{**vars(args), "operation": operation, "phase": "operation"})
            packet = T.STEPS.observe_packet(T.dependencies(), context, selected, provider)
            require(packet is not None, "scheduling-readiness-original-task-required")
            receipt = packet["receipt"]
            task, result = receipt["task"], receipt["result"]
            require(result["code"] == T.RUNNER.EVIDENCE.SCHEDULING_STATE.RESULTS[operation]
                and result["operation"] == operation and result["verdict"] == "passed"
                and task["definition"] == context["checked"]["definition"], "scheduling-readiness-result-mismatch")
            original = T.STEPS.path(context, selected)
            observations[name] = {"receipt_sha256": "sha256:" + hashlib.sha256(original.read_bytes()).hexdigest(),
                "task_arn": task["arn"], "started_at": task["started_at"], "stopped_at": task["stopped_at"], "database_state": result["database_state"]}
        phase = "comparison"
        return T.RUNNER.EVIDENCE.SCHEDULING_STATE.initial_readiness(binding, observations,
            target="kanbien-core-platform", scope="entity-smoke", required_after=required_after, checked_at=checked_at,
            timestamp=timestamp, observation_expired=POLICY.observation_expired)
    except Exception as error:
        if isinstance(error, ValueError) and str(error) == "scheduling-database-readiness-unrelated-work":
            raise EvidenceFailure("scheduling-readiness-unrelated-work") from None
        raise EvidenceFailure("scheduling-readiness-not-confirmed", phase) from None


def observe_scheduling_state_receipt(receipt_path, proof_label, provider, *, required_after, source_revision, image_digest, expected_predecessor=None, scheduling_control_phase=None):
    """Current native inventory observation, without a zero-work assumption.

    Controls and the explanation of every pending synthetic row belong to the
    caller's retained phase. This reader neither submits a task nor grants access.
    """
    phase = "selection"
    try:
        arguments = ["--receipt", str(receipt_path), "--proof-label", proof_label, "--workload", "administration",
            "--operation", "observe-scheduling-state", "--proof-stage", "scheduling-preparation"]
        if expected_predecessor is not None: arguments += ["--expected-predecessor", expected_predecessor]
        if scheduling_control_phase is not None: arguments += ["--scheduling-control-phase", scheduling_control_phase]
        args = T.parse(arguments)
        phase = "current-binding"
        context = T.prepare(args, provider)
        binding = {key: context["binding"][key] for key in ("source_revision", "image_digest", "dependency_incarnation_sha256")}
        require((binding["source_revision"], binding["image_digest"]) == (source_revision, image_digest), "scheduling-state-identity-mismatch")
        phase = "original-task"
        selected = SimpleNamespace(**{**vars(args), "phase": "operation"})
        packet = T.STEPS.observe_packet(T.dependencies(), context, selected, provider, historical=False)
        require(packet is not None, "scheduling-state-original-task-required")
        task, result = packet["receipt"]["task"], packet["receipt"]["result"]
        require(result["code"] == T.RUNNER.EVIDENCE.SCHEDULING_STATE.RESULTS[args.operation]
            and result["operation"] == args.operation and result["verdict"] == "passed"
            and task["definition"] == context["checked"]["definition"], "scheduling-state-result-mismatch")
        state = SCHEDULING.complete_database_state(result["database_state"])
        checked_at, timestamp = C.now(), T.RUNNER.EVIDENCE.timestamp
        times = [timestamp(value) for value in (required_after, task["started_at"], task["stopped_at"], checked_at)]
        require(all(value is not None for value in times) and times == sorted(times)
            and not POLICY.observation_expired(task["stopped_at"], checked_at, timestamp), "scheduling-state-not-fresh")
        original = T.STEPS.path(context, selected)
        return {"schema": "kanbien/scheduling-database-observation/v1", "target": "kanbien-core-platform", "scope": "entity-smoke",
            "binding": binding, "database_state": state, "task": {key: task[key] for key in ("arn", "definition", "started_at", "stopped_at")},
            "receipt_sha256": "sha256:" + hashlib.sha256(original.read_bytes()).hexdigest(), "required_after": required_after,
            "checked_at": checked_at, "packet": packet}
    except Exception:
        raise EvidenceFailure("scheduling-state-not-confirmed", phase) from None


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


def preflight_label(binding, stage, workload, operation, *, delivery=None, namespace_delivery=None, qualification_profile=None, scheduling_case=None, scheduling_snapshot=None, scheduling_control_phase=None):
    selected = SimpleNamespace(proof_stage=stage, workload=workload, operation=operation, phase="preflight", qualification_profile=qualification_profile,
        migration_profile="scheduling" if stage == "scheduling-migration" else "baseline", scheduling_case=scheduling_case, scheduling_snapshot=scheduling_snapshot,
        scheduling_control_phase=scheduling_control_phase)
    identity_stage = T.STEPS.identity_stage(selected)
    namespace = delivery or namespace_delivery
    if namespace is not None:
        return C.delivery_preflight_label(namespace, identity_stage, workload, operation)
    suffix = "" if identity_stage == "baseline" else ":" + identity_stage
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


def validate_task(value, collection_binding, *, expected_binding=None, delivery=None, namespace_delivery=None, qualification_profile=None, metadata=False, synthetic=False):
    """Pure historical validation; no provider access or today's source hash."""
    fields = {"schema", "name", "stage", "phase", "requested_operation", "controller_sha256", "collection_binding", "graph", "packet", "completion", "gate", "admission"}
    qualification_profile = profile(qualification_profile)
    if qualification_profile is not None: fields.add("qualification_profile")
    if isinstance(value, dict) and "observation_recovery" in value: fields.add("observation_recovery")
    if synthetic:
        fields.update({"scheduling_case", "scheduling_snapshot"})
        require(delivery is not None and qualification_profile is None, "acceptance-scheduling-selection-invalid")
    if isinstance(value, dict) and "scheduling_control_phase" in value:
        fields.add("scheduling_control_phase")
        require(metadata and value.get("name") == "scheduling-state" and delivery is not None
            and value["scheduling_control_phase"] in T.STEPS.SCHEDULING_STATE_PHASES, "acceptance-task-control-phase-invalid")
    if delivery is not None:
        C.RESOURCE.validate_delivery(delivery)
        fields.add("delivery")
        require(isinstance(value, dict) and value.get("delivery") == delivery,
                "acceptance-task-delivery-mismatch")
    require(isinstance(value, dict) and set(value) == fields and value["schema"] == SCHEMA, "acceptance-task-envelope-invalid")
    require(value.get("qualification_profile") == qualification_profile, "acceptance-task-profile-mismatch")
    name = value["name"]
    selected_tasks = tasks(qualification_profile, metadata=metadata, synthetic=synthetic)
    require(isinstance(name, str) and name in selected_tasks, "acceptance-task-selection-invalid")
    if namespace_delivery is not None:
        C.RESOURCE.validate_delivery(namespace_delivery)
        require(name == "restore-read" and delivery is None
            and namespace_delivery["proof_label"] == collection_binding["proof_label"]
            and all(namespace_delivery["candidate"][key] == collection_binding[key] for key in ("source_revision", "image_digest")), "acceptance-task-delivery-mismatch")
    stage, workload, allowed_operations = selected_tasks[name]
    operation, phase = value["requested_operation"], value["phase"]
    require(value["stage"] == stage and isinstance(operation, str) and operation in allowed_operations and isinstance(phase, str) and phase in {"preflight", "operation"}
            and not (name == "credential-unready" and phase != "operation"), "acceptance-task-selection-invalid", name)
    C.RESOURCE.validate_binding(collection_binding, record_required=not (metadata and name == "scheduling-state"
        and value.get("scheduling_control_phase") is not None and "record_digest" not in collection_binding))
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
        selection = SimpleNamespace(workload=workload, operation=operation, phase=phase, proof_stage=stage, qualification_profile=qualification_profile,
            migration_profile="scheduling" if name == "scheduling-migration" else "baseline",
            scheduling_case=value.get("scheduling_case"), scheduling_snapshot=value.get("scheduling_snapshot"),
            scheduling_control_phase=value.get("scheduling_control_phase"))
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
    label = preflight_label(parent, stage, workload, operation, delivery=delivery, namespace_delivery=namespace_delivery, qualification_profile=qualification_profile,
        scheduling_case=value.get("scheduling_case"), scheduling_snapshot=value.get("scheduling_snapshot"),
        scheduling_control_phase=value.get("scheduling_control_phase")) if phase == "preflight" else (
        C.delivery_operation_label(delivery, workload, operation) if delivery is not None else parent["proof_label"])
    if synthetic and phase == "operation": label = T.STEPS.scheduling_label(delivery, value["scheduling_case"])
    if delivery is not None and phase == "preflight": label = packet["plan"]["preflight_label"]
    recovered_label = None
    if "observation_recovery" in value:
        base = (C.delivery_preflight_label(namespace_delivery, stage, workload, operation) if namespace_delivery is not None
            else "entity-smoke-" + hashlib.sha256((parent["proof_label"] + ":restore-reader:restore-read:preflight:isolated-restore").encode()).hexdigest()[:24])
        recovered_label = recovered_observation_label(value, request, base)
        if phase == "preflight": label = recovered_label
    require(request["environment"][T.RUNNER.CONTROL.OPERATIONS[workload][0]] == actual_operation
            and request["proof_label"] == label, "acceptance-task-request-selection-mismatch", name)
    if name == "migration":
        require("PERSISTENCE_MIGRATION_PROFILE" not in request["environment"], "acceptance-migration-profile-mismatch", name)
    if name == "scheduling-migration":
        require(request["environment"].get("PERSISTENCE_MIGRATION_PROFILE") == ("scheduling" if phase == "operation" else None), "acceptance-migration-profile-mismatch", name)
    if workload in {"verifier", "database-proof", "restore-reader"}:
        require(request["environment"].get("ENTITY_SMOKE_PROOF_LABEL") == label, "acceptance-task-label-mismatch", name)
    original = name in {"original-record", "collision", "baseline-read", "replacement-read", "initial-read", "credential-read", "restore-read", "final-read"}
    if phase == "operation" and original:
        require(receipt["result"].get("record_digest") == collection_binding["record_digest"], "acceptance-original-record-mismatch", name)
    if phase == "operation" and name == "migration-state":
        database_result(receipt["result"], qualification_profile,
            manifest_sha256=packet.get("plan", {}).get("scheduling_manifest_sha256") if qualification_profile else None)
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
        selected_label = packet["plan"]["preflight_label"] if delivery is not None else preflight_label(parent, stage, workload, operation, namespace_delivery=namespace_delivery, qualification_profile=qualification_profile)
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
    selected_profile = task_profile(name, getattr(args, "qualification_profile", None))
    synthetic = name in SYNTHETIC_TASKS
    selected_tasks = tasks(selected_profile, metadata=name in METADATA_TASKS, synthetic=synthetic)
    require(name in selected_tasks and (args.proof_stage, args.workload) == selected_tasks[name][:2]
            and args.operation in selected_tasks[name][2], "acceptance-task-selection-invalid", name)
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
    if selected_profile is not None: value["qualification_profile"] = selected_profile
    if delivery is not None: value["delivery"] = delivery
    if synthetic: value.update(scheduling_case=args.scheduling_case, scheduling_snapshot=args.scheduling_snapshot)
    if getattr(args, "scheduling_control_phase", None) is not None:
        value["scheduling_control_phase"] = args.scheduling_control_phase
    if context.get("failed_observation"):
        plan = route.C.read_json(context["cache"] / "restore-reader-plans" / (packet["plan_sha256"].removeprefix("sha256:") + ".json"))
        value["observation_recovery"] = {"plan": plan, "failure": context["failed_observation"]}
    return validate_task(value, collection_binding, expected_binding=context["binding"], delivery=delivery,
        namespace_delivery=context.get("recovery_delivery"), qualification_profile=selected_profile, metadata=name in METADATA_TASKS, synthetic=synthetic)


def _validate_scheduling_proof_packet(value, *, expected_binding, required_after):
    """Validate native archives and their original row/generation links offline."""
    require(isinstance(value, dict) and set(value) == {"task", "original", "deletion", "preparation", "original_terminal"}, "acceptance-scheduling-packet-invalid")
    require(isinstance(value["task"], dict) and set(value["task"]) == {"preflight", "operation"}, "acceptance-scheduling-packet-invalid")
    selected = value["task"]["operation"]
    binding, delivery = selected["collection_binding"], selected["delivery"]
    require(set(expected_binding) == {"source_revision", "image_digest", "dependency_incarnation_sha256"}
        and all(binding.get(key) == item for key, item in expected_binding.items()), "acceptance-scheduling-binding-mismatch")
    case, snapshot, operation = selected["scheduling_case"], selected["scheduling_snapshot"], selected["requested_operation"]
    timestamp, available = T.RUNNER.EVIDENCE.timestamp, set()
    pairs = []
    def pair(candidate, name, *, synthetic):
        require(isinstance(candidate, dict) and set(candidate) == {"preflight", "operation"}, "acceptance-scheduling-packet-invalid")
        for phase, item in candidate.items():
            require(item.get("name") == name and item.get("phase") == phase, "acceptance-scheduling-selection-invalid")
            if synthetic:
                require(item.get("scheduling_case") == case and item.get("scheduling_snapshot") == (snapshot if name == "observe-scheduling-proof" else None), "acceptance-scheduling-selection-invalid")
            validate_task(item, binding, delivery=delivery, metadata=not synthetic, synthetic=synthetic)
            available.add(C.DEPLOY.fingerprint(item["packet"]))
        before, admission = candidate["preflight"]["packet"], candidate["operation"]["admission"]["preflight"]
        require(admission["reservation"] == before["reservation"] and admission["receipt"] == before["receipt"], "acceptance-original-preflight-mismatch", name)
        pairs.append(candidate)
        return candidate["operation"]["packet"]["receipt"]
    current = pair(value["task"], operation, synthetic=True)
    require(timestamp(current["task"]["created_at"]) >= timestamp(required_after), "acceptance-scheduling-proof-order-invalid")
    preparation = value["preparation"]
    require(isinstance(preparation, dict) and set(preparation) == {"scheduling-state", "scheduling-grant", "scheduling-permissions"}, "acceptance-scheduling-preparation-invalid")
    prior, manifest = None, None
    for name in ("scheduling-state", "scheduling-grant", "scheduling-permissions"):
        receipt = pair(preparation[name], name, synthetic=False)
        state = SCHEDULING.complete_database_state(receipt["result"]["database_state"], manifest_sha256=manifest)
        manifest = state["manifest_sha256"]
        require(prior is None or timestamp(receipt["task"]["created_at"]) >= timestamp(prior), "acceptance-scheduling-proof-order-invalid")
        prior = receipt["task"]["stopped_at"]
    require(timestamp(current["task"]["created_at"]) >= timestamp(prior), "acceptance-scheduling-proof-order-invalid")
    needs_original = operation in {"scheduling-delete", "scheduling-restore", "observe-scheduling-proof"}
    require((value["original"] is not None) == needs_original, "acceptance-scheduling-original-required")
    original = deletion = None
    if needs_original:
        name = value["original"]["operation"]["name"]
        require(name in {"scheduling-create", "scheduling-observe-create"}, "acceptance-scheduling-original-required")
        original = pair(value["original"], name, synthetic=True)
        require(original["result"]["record_digest"] == binding["record_digest"] and timestamp(original["task"]["stopped_at"]) <= timestamp(current["task"]["created_at"]), "acceptance-scheduling-original-mismatch")
    needs_deletion = operation == "observe-scheduling-proof" and case != "scope-isolation"
    require((value["deletion"] is not None) == needs_deletion, "acceptance-scheduling-deletion-required")
    if needs_deletion:
        deletion = pair(value["deletion"], "scheduling-restore" if case == "cancellation" else "scheduling-delete", synthetic=True)
        require(all(deletion["result"][key] == original["result"][key] for key in ("record_id", "record_digest"))
            and timestamp(original["task"]["stopped_at"]) <= timestamp(deletion["task"]["created_at"])
            and timestamp(deletion["task"]["stopped_at"]) <= timestamp(current["task"]["created_at"]), "acceptance-scheduling-generation-mismatch")
    terminal_required = operation == "scheduling-observe-create" or needs_original and value["original"]["operation"]["name"] == "scheduling-observe-create"
    require((value["original_terminal"] is not None) == terminal_required, "acceptance-scheduling-original-terminal-required")
    if terminal_required:
        terminal = value["original_terminal"]
        require(isinstance(terminal, dict) and set(terminal) == {"reservation", "task_arn", "stopped_at"}, "acceptance-scheduling-original-terminal-invalid")
        reservation = terminal["reservation"]
        request = T.RUNNER.CONTROL.validate_request(reservation["request"])
        require(reservation["schema"] == "deploy/entity-smoke-task-reservation/v1" and reservation["request_sha256"] == hashlib.sha256(T.RUNNER.CONTROL.canonical(request)).hexdigest()
            and request["environment"].get("ENTITY_SMOKE_VERIFICATION_OPERATION") == "scheduling-create"
            and request["proof_label"] == T.STEPS.scheduling_label(delivery, case)
            and all(request[key] == binding[key] for key in expected_binding)
            and re.fullmatch(r"arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/[a-f0-9]{32}", terminal["task_arn"])
            and timestamp(reservation["reserved_at"]) <= timestamp(terminal["stopped_at"]) <= timestamp((original or current)["task"]["created_at"]), "acceptance-scheduling-original-terminal-invalid")
    for candidate in pairs:
        for item in candidate.values():
            native = item["packet"]
            POLICY.validate_prerequisite_references(native["prerequisites"], available)
            if item["name"] not in SYNTHETIC_TASKS: continue
            name = item["name"]
            expected = None
            if name in {"scheduling-delete", "scheduling-restore", "observe-scheduling-proof"}:
                expected = {key: original["result"][key] for key in ("record_id", "record_digest")}
                reference = native["prerequisites"]["packets"].get("scheduling-original-record")
                require(reference == {"schema": "deploy/proof-prerequisite-reference/v1", "packet_sha256": C.DEPLOY.fingerprint(value["original"]["operation"]["packet"])}, "acceptance-scheduling-original-mismatch")
                if name == "observe-scheduling-proof" and needs_deletion:
                    expected["due_at"] = deletion["result"]["due_at"]
                    require(native["prerequisites"]["packets"].get("scheduling-original-deletion") == {"schema": "deploy/proof-prerequisite-reference/v1", "packet_sha256": C.DEPLOY.fingerprint(value["deletion"]["operation"]["packet"])}, "acceptance-scheduling-generation-mismatch")
            require(native["plan"]["scheduling_selection_sha256"] == (None if expected is None else C.DEPLOY.fingerprint(expected)), "acceptance-scheduling-selection-mismatch")
            if name == "scheduling-observe-create": require(native["prerequisites"]["packets"].get("original-create-terminal") == value["original_terminal"], "acceptance-scheduling-original-terminal-invalid")
    result, task = current["result"], current["task"]
    return {"operation": operation, "case": case, "snapshot": snapshot, "result": result, "binding": expected_binding,
        "task": {key: task[key] for key in ("arn", "definition", "created_at", "started_at", "stopped_at")},
        "receipt_sha256": C.DEPLOY.fingerprint(selected["packet"]), "packet": selected["packet"], "archive": value}


def validate_scheduling_proof_packet(value, *, expected_binding, required_after):
    try: return _validate_scheduling_proof_packet(value, expected_binding=expected_binding, required_after=required_after)
    except EvidenceFailure: raise
    except Exception: raise EvidenceFailure("acceptance-scheduling-packet-invalid") from None


def capture_scheduling_proof(route, context, args, provider, *, required_after, source_revision, image_digest):
    """Capture the original native phases, not a summary labelled successful."""
    require(route.STEPS.stage(args) == "scheduling-proof" and args.phase == "operation", "acceptance-scheduling-selection-invalid")
    packet = route.STEPS.observe_packet(route.dependencies(), context, args, provider, historical=True)
    require(packet is not None, "acceptance-scheduling-proof-required")
    result = packet["receipt"]["result"]
    digest_value = result.get("record_digest", context.get("scheduling_selection", {}).get("record_digest"))
    binding = {**context["binding"], "record_digest": digest_value}
    expected = {key: binding[key] for key in ("source_revision", "image_digest", "dependency_incarnation_sha256")}
    require((source_revision, image_digest) == (expected["source_revision"], expected["image_digest"]), "acceptance-scheduling-binding-mismatch")
    def capture(name, *, original_packet=None):
        stage, workload, operations = (SYNTHETIC_TASKS if name in SYNTHETIC_TASKS else METADATA_TASKS)[name]
        selected = SimpleNamespace(**{**vars(args), "proof_stage": stage, "workload": workload, "operation": operations[0],
            "scheduling_case": args.scheduling_case if name in SYNTHETIC_TASKS else None,
            "scheduling_snapshot": args.scheduling_snapshot if name == "observe-scheduling-proof" else None, "qualification_profile": None})
        if original_packet is not None: selected.operation = original_packet["receipt"]["result"]["operation"]
        current = {**context, "checked": route.BINDING.inspect(provider, workload, context["parameters"], context["resources"], context.get("binding_snapshot"))}
        return {phase: capture_task(route, current, SimpleNamespace(**{**vars(selected), "phase": phase}), provider, name, binding, historical=phase == "preflight")
            for phase in ("preflight", "operation")}
    prerequisites = context["prerequisites"]["packets"]
    original = prerequisites.get("scheduling-original-record")
    deletion = prerequisites.get("scheduling-original-deletion")
    value = {"task": capture(args.operation),
        "original": None if original is None else capture(original["receipt"]["result"]["operation"], original_packet=original),
        "deletion": None if deletion is None else capture(deletion["receipt"]["result"]["operation"], original_packet=deletion),
        "preparation": {name: capture(name) for name in ("scheduling-state", "scheduling-grant", "scheduling-permissions")},
        "original_terminal": prerequisites.get("original-create-terminal")}
    return validate_scheduling_proof_packet(value, expected_binding=expected, required_after=required_after)


def reobserve_scheduling_proof_packet(value, *, qualified_path, expected_binding, required_after):
    """Reconstruct only the original closed selection and reread native custody."""
    try:
        checked = validate_scheduling_proof_packet(value, expected_binding=expected_binding, required_after=required_after)
        qualified = Path(qualified_path)
        require(not qualified.is_absolute() and bool(qualified.parts) and all(part not in {".", ".."} for part in qualified.parts),
            "acceptance-scheduling-qualified-path-invalid")
        selected = value["task"]["operation"]
        arguments = ["--receipt", str(C.ROOT / qualified), "--proof-label", selected["collection_binding"]["proof_label"],
            "--expected-predecessor", selected["delivery"]["expected_predecessor"], "--proof-stage", "scheduling-proof",
            "--workload", SYNTHETIC_TASKS[checked["operation"]][1], "--operation", checked["operation"], "--scheduling-case", checked["case"]]
        if checked["snapshot"] is not None: arguments += ["--scheduling-snapshot", checked["snapshot"]]
        args, provider = T.parse(arguments), T.Provider()
        context = T.prepare(args, provider)
        observed = capture_scheduling_proof(T, context, args, provider, required_after=required_after,
            source_revision=expected_binding["source_revision"], image_digest=expected_binding["image_digest"])
        require(observed == checked, "acceptance-scheduling-original-packet-mismatch")
        return observed
    except Exception:
        raise EvidenceFailure("acceptance-scheduling-proof-not-confirmed") from None


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
