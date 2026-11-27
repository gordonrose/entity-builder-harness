#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-steps
#   version: 3
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind the initial database preparation sequence to actual immutable task receipts and produce its existing activation manifest.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Own-scope preparation steps, not a generic scheduler or AWS authority.

The owning route supplies its checked context and already gated provider.
Recovery/record operations remain unavailable until their predecessors are wired.
"""
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

_spec = importlib.util.spec_from_file_location("entity_smoke_step_recovery_selection", (Path(__file__).resolve().parents[2] / "recovery-and-replacement/source-transition/source-transition.py"))
TRANSITION = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(TRANSITION)
_policy = importlib.util.spec_from_file_location("entity_smoke_step_proof_policy", Path(__file__).resolve().parents[5] / "release-succession/proof-policy.py")
POLICY = importlib.util.module_from_spec(_policy); _policy.loader.exec_module(POLICY)
_scheduling = importlib.util.spec_from_file_location("entity_smoke_step_scheduling_proof", Path(__file__).resolve().parents[5] / "release-succession/scheduling-proof.py")
SCHEDULING = importlib.util.module_from_spec(_scheduling); _scheduling.loader.exec_module(SCHEDULING)

STEPS = (
    ("bootstrap", "administration", "bootstrap", "AdministrationTaskDefinition"),
    ("migration", "migration", "apply", "MigrationTaskDefinition"),
    ("grant-runtime", "administration", "grant-runtime", "AdministrationTaskDefinition"),
    ("permissions", "database-proof", "permissions", "DatabaseProofTaskDefinition"),
)
SCHEDULING_OPERATIONS = frozenset({"observe-scheduling-prefix", "observe-scheduling-state", "grant-scheduling-access", "prove-scheduling-access"})
SYNTHETIC_OPERATIONS = frozenset({"scheduling-create", "scheduling-observe-create", "scheduling-delete", "scheduling-restore", "observe-scheduling-proof"})
SCHEDULING_STATE_PHASES = ("scope-create-disabled", "missed-tick-disable", "fault-disable", "fault-on", "fault-off", "proof-disable")
_SCHEDULING_CONTROL = None


class StepFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class PrerequisiteMissing(StepFailure):
    def __init__(self, item):
        super().__init__("task-prerequisite-required")
        self.item = item


def require(value, code):
    if not value: raise StepFailure(code)


def selected(args):
    return next((index for index, (_, workload, operation, _) in enumerate(STEPS) if (args.workload, args.operation) == (workload, operation)), None)


def scheduling_preparation(args):
    return getattr(args, "proof_stage", "baseline") == "scheduling-preparation" and args.workload == "administration" and args.operation in SCHEDULING_OPERATIONS


def scheduling_control():
    """The existing provider owner keeps its own fixed read vocabulary/store."""
    global _SCHEDULING_CONTROL
    if _SCHEDULING_CONTROL is None:
        spec = importlib.util.spec_from_file_location("entity_smoke_state_scheduling_control",
            Path(__file__).resolve().parents[6] / "50-deploy/capabilities/scheduling-control/script.py")
        _SCHEDULING_CONTROL = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_SCHEDULING_CONTROL)
    return _SCHEDULING_CONTROL


def validate_scheduling_control_phase(route, packet, binding, phase):
    """Historical phase binding only; fresh submission also reads its provider."""
    try:
        require(phase in SCHEDULING_STATE_PHASES, "task-scheduling-control-phase-invalid")
        owner, intent = scheduling_control(), packet["intent"]
        owner.validate_phase_evidence(packet, target="kanbien-core-platform", scope="entity-smoke",
            source_revision=binding["source_revision"], predecessor_sha256=intent["predecessor_sha256"])
        require(intent["phase"] == phase, "task-scheduling-control-phase-mismatch")
        parameters = intent["parameters"]
        incarnation = route.C.DEPLOY.fingerprint({"resource_id": parameters["DatabaseResourceId"],
            "database": parameters["DatabaseName"], "schema": "entity_smoke"})
        require(incarnation == binding["dependency_incarnation_sha256"], "task-scheduling-control-database-mismatch")
        return packet["terminal"]["Timestamp"].replace("+00:00", "Z")
    except StepFailure:
        raise
    except Exception:
        raise StepFailure("task-scheduling-control-phase-not-confirmed") from None


def scheduling_migration(args):
    return getattr(args, "proof_stage", "baseline") == "scheduling-migration" and args.workload == "migration" and args.operation == "apply" and getattr(args, "migration_profile", "baseline") == "scheduling"


def qualification_profile(args):
    try: return SCHEDULING.profile(getattr(args, "qualification_profile", None))
    except SCHEDULING.ProofFailure: raise StepFailure("task-qualification-profile-invalid") from None


def validate_qualification_result(args, receipt, manifest_sha256):
    if stage(args) == "scheduling-qualification" and args.phase == "operation":
        try:
            require(isinstance(manifest_sha256, str) and len(manifest_sha256) == 64, "task-scheduling-manifest-mismatch")
            SCHEDULING.complete_database_state(receipt.get("result", {}).get("database_state"), manifest_sha256=manifest_sha256)
        except SCHEDULING.ProofFailure:
            raise StepFailure("task-scheduling-manifest-mismatch") from None


def stage(args):
    value = getattr(args, "proof_stage", "baseline")
    allowed = {"baseline": None, "server-replacement": {("verifier", "read")}, "initial-recovery": {("verifier", "read"), ("administration", "observe-migration-state")}}
    allowed["credential-recovery"] = {("administration", value) for value in ("observe-permissions", "revoke-runtime", "restore-runtime")} | {("verifier", "unready"), ("verifier", "read"), ("database-proof", "permissions")}
    allowed["isolated-restore"] = {("restore-reader", "restore-read")}
    allowed["acceptance"] = {("verifier", "read")}
    allowed["rollback"] = {("verifier", "read")}
    allowed["activation"] = {("database-proof", "permissions")}
    allowed["scheduling-preparation"] = {("administration", operation) for operation in SCHEDULING_OPERATIONS}
    allowed["scheduling-migration"] = {("migration", "apply")}
    allowed["scheduling-qualification"] = {("administration", "observe-scheduling-state")}
    allowed["scheduling-proof"] = {("verifier", operation) for operation in SYNTHETIC_OPERATIONS if operation != "observe-scheduling-proof"} | {("administration", "observe-scheduling-proof")}
    require(value in allowed and (allowed[value] is None or (args.workload, args.operation) in allowed[value]), "task-proof-stage-not-supported")
    require(args.operation not in SCHEDULING_OPERATIONS or value in {"scheduling-preparation", "scheduling-qualification"}, "task-proof-stage-not-supported")
    require((args.operation in SYNTHETIC_OPERATIONS) == (value == "scheduling-proof"), "task-proof-stage-not-supported")
    case, snapshot = getattr(args, "scheduling_case", None), getattr(args, "scheduling_snapshot", None)
    require((case in SCHEDULING.CASES if value == "scheduling-proof" else case is None), "task-scheduling-case-invalid")
    require((snapshot in SCHEDULING.SNAPSHOTS if args.operation == "observe-scheduling-proof" else snapshot is None), "task-scheduling-snapshot-invalid")
    require(args.operation != "scheduling-restore" or case == "cancellation", "task-scheduling-case-invalid")
    require(args.operation != "scheduling-delete" or case != "cancellation", "task-scheduling-case-invalid")
    require(case != "scope-isolation" or args.operation in {"scheduling-create", "scheduling-observe-create", "observe-scheduling-proof"}, "task-scheduling-case-invalid")
    require((getattr(args, "migration_profile", "baseline") == "scheduling") == (value == "scheduling-migration"), "task-migration-profile-invalid")
    control_phase = getattr(args, "scheduling_control_phase", None)
    require(control_phase is None or (control_phase in SCHEDULING_STATE_PHASES
        and value == "scheduling-preparation" and args.workload == "administration" and args.operation == "observe-scheduling-state"),
        "task-scheduling-control-phase-invalid")
    profile = qualification_profile(args)
    require(value != "scheduling-qualification" or profile is not None, "task-qualification-profile-required")
    require(profile is None or value not in {"scheduling-preparation", "scheduling-migration", "isolated-restore", "scheduling-proof"}, "task-qualification-profile-not-supported")
    require(profile is None or (args.workload, args.operation) not in {(workload, operation) for _, workload, operation, _ in STEPS[:3]}, "task-qualification-profile-not-supported")
    require(profile is None or (args.workload, args.operation) != ("administration", "observe-migration-state"), "task-qualification-database-selection-mismatch")
    require(not (value == "credential-recovery" and args.operation == "unready") or args.phase == "operation", "task-unready-preflight-phase-prohibited")
    return value


def identity_stage(args):
    """Keep legacy labels byte-identical; selected proof has separate custody."""
    value = stage(args) + ("-scheduling-qualification" if qualification_profile(args) else "")
    if stage(args) == "scheduling-proof": value += "-" + args.scheduling_case + ("-" + args.scheduling_snapshot if args.operation == "observe-scheduling-proof" else "")
    if getattr(args, "scheduling_control_phase", None) is not None: value += "-" + args.scheduling_control_phase
    return value


def scheduling_label(delivery, case):
    require(case in SCHEDULING.CASES, "task-scheduling-case-invalid")
    return "entity-smoke-" + hashlib.sha256((delivery["delivery_id"] + ":scheduling:" + case).encode()).hexdigest()[:24]


def activation_generation(args):
    value = getattr(args, "activation_generation", None)
    require(isinstance(value, str) and value.startswith("sha256:") and len(value) == 71
            and all(character in "0123456789abcdef" for character in value[7:]), "task-activation-controller-required")
    return value[7:]


def key(args, delivery=None):
    suffix = "" if identity_stage(args) == "baseline" else ":" + identity_stage(args)
    if delivery is None:
        if TRANSITION.acceptance_refresh(args): suffix += ":collector-recovery-1"
        if TRANSITION.acceptance_renewal(args) and args.phase == "preflight": suffix += ":readback-recovery-1"
    if stage(args) == "activation": suffix += ":" + activation_generation(args)
    if delivery is not None: suffix += ":delivery:" + delivery["delivery_id"]
    if renewed(args): suffix += ":preflight-renewal-1"
    return "task-" + hashlib.sha256((args.proof_label + ":" + args.workload + ":" + args.operation + ":" + args.phase + suffix).encode()).hexdigest()[:48]


def path(context, args):
    suffix = "" if identity_stage(args) == "baseline" else "-" + identity_stage(args)
    if not context.get("delivery"): suffix += TRANSITION.preflight_step_suffix(args)
    if args.phase == "preflight" and context.get("failed_observation_sha256"):
        suffix += "-terminal-observation-recovery-1"
    if renewed(args): suffix += "-preflight-renewal-1"
    if stage(args) == "activation":
        generation = activation_generation(args)
        require(context["artifact"] == "sha256:" + generation, "task-activation-controller-mismatch")
        suffix += "-" + generation
    return context["cache"] / "task-steps" / (args.workload + "-" + args.operation + suffix + "-" + args.phase + ".json")


def renewed(args):
    return args.phase == "preflight" and getattr(args, "preflight_renewal_selection", None) == (stage(args), args.workload, args.operation)


def renewal_label(original):
    return "entity-smoke-" + POLICY.observation_renewal_id(original)


def select_preflight(route, context, args, provider):
    """One unused expired success may be renewed; an operation is never replayed.

    The original packet, completion and gate remain immutable. The replacement
    keeps a distinct label, reservation and packet; its plan carries original
    custody for independent collection. No failed/unknown probe is renewable.
    """
    if not context.get("delivery") or route.CREDENTIAL.negative(args): return
    C, runner = route.C, route.RUNNER
    base = C.delivery_preflight_label(context["delivery"], identity_stage(args), args.workload, args.operation)
    plan = context["report"]["plan"]
    plan["preflight_label"] = base
    plan.pop("preflight_renewal", None)
    if "schema" in plan: plan["schema"] = "deploy/entity-smoke-task-plan/v2"
    args.preflight_renewal_selection = None
    probe = SimpleNamespace(**{**vars(args), "phase": "preflight"})
    operation = SimpleNamespace(**{**vars(args), "phase": "operation"})
    original_path = path(context, probe)
    if not route.COMPLETION.path(original_path).is_file(): return
    original = observe_packet(route, context, probe, provider, historical=True, select=False)
    completion = route.COMPLETION.read(route, context, probe, original_path)
    operation_request = request(route, context, operation)
    store = runner.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    reserved = store.read(key(operation, context["delivery"]), operation_request)
    selected = None
    if reserved is not None:
        runner.PREFLIGHT.read_admission(context["cache"] / "task-receipts", reserved)
        admission = C.read_json(runner.PREFLIGHT.admission_path(context["cache"] / "task-receipts", reserved))
        selected = admission["preflight"]["label"]
        require(selected in {base, renewal_label(base)}, "task-step-delivery-label-mismatch")
        if selected == base: return
    elif not POLICY.observation_expired(original["receipt"]["task"]["stopped_at"], C.now(), runner.EVIDENCE.timestamp):
        return
    args.preflight_renewal_selection = (stage(args), args.workload, args.operation)
    plan["preflight_label"] = renewal_label(base)
    if "schema" in plan: plan["schema"] = "deploy/entity-smoke-task-plan/v3"
    plan["preflight_renewal"] = {"packet": original, "completion": completion,
        "gate": C.read_json(C.ROOT / completion["realization_evidence"])}
    renewed_probe = SimpleNamespace(**{**vars(args), "phase": "preflight"})
    if reserved is None and route.COMPLETION.path(path(context, renewed_probe)).is_file():
        latest = observe_packet(route, context, renewed_probe, provider, historical=True, select=False)
        require(not POLICY.observation_expired(latest["receipt"]["task"]["stopped_at"], C.now(), runner.EVIDENCE.timestamp),
            "preflight-renewal-exhausted")


def validate_renewal(route, plan, binding, delivery, args):
    """Closed historical proof, not present-tense permission to launch."""
    base = route.C.delivery_preflight_label(delivery, identity_stage(args), args.workload, args.operation)
    previous = plan.get("preflight_renewal")
    if previous is None:
        require(plan["preflight_label"] == base, "task-step-delivery-label-mismatch")
        return
    require(isinstance(previous, dict) and set(previous) == {"packet", "completion", "gate"}, "preflight-renewal-custody-invalid")
    packet, completion, gate = (previous[name] for name in ("packet", "completion", "gate"))
    require(isinstance(packet, dict) and isinstance(packet.get("plan"), dict)
        and "preflight_renewal" not in packet["plan"], "preflight-renewal-custody-invalid")
    probe = SimpleNamespace(**{**vars(args), "phase": "preflight"})
    validate_delivery_step(route, packet, binding, delivery, probe)
    require(all(plan[key] == packet["plan"][key] for key in ("task_definition_sha256", "configuration_sha256", "roles_sha256", "network_sha256", "prerequisites_sha256", "expected_record_digest", "package_custody_reference")),
        "preflight-renewal-binding-changed")
    route.RUNNER.PREFLIGHT.validate_launch(packet["reservation"]["request"])
    route.RUNNER.EVIDENCE.validate_retained(packet["receipt"], packet["reservation"])
    document = lambda value: "sha256:" + hashlib.sha256(route.RUNNER.CONTROL.canonical(value) + b"\n").hexdigest()
    require(isinstance(completion, dict) and set(completion) == {"schema", "step_sha256", "plan_sha256", "realization_evidence", "realization_evidence_sha256"}
        and completion["schema"] == "deploy/entity-smoke-task-completion/v1"
        and completion["step_sha256"] == document(packet) and completion["plan_sha256"] == packet["plan_sha256"]
        and completion["realization_evidence_sha256"] == document(gate), "preflight-renewal-custody-invalid")
    graph = route.GRAPH.contract(args.workload, route.C.GATE)
    graph = route.GRAPH.retained(route.C, graph, gate=gate)
    artifacts = {item["id"]: packet["plan"]["controller_sha256"] if item["id"] == route.GRAPH.CONTROLLER_SOURCE else binding["image_digest"] for item in graph["artifacts"]}
    route.COMPLETION.validate_gate(route, graph, gate, packet["plan_sha256"], artifacts)
    require(plan["preflight_label"] == renewal_label(base), "task-step-delivery-label-mismatch")


def request(route, context, args):
    binding, checked = context["binding"], context["checked"]
    probe = args.phase == "preflight"
    operation = ("ready" if args.workload == "verifier" else "preflight") if probe else args.operation
    label = context["report"]["plan"]["preflight_label"] if probe else args.proof_label
    if not probe and context.get("delivery"):
        label = route.C.delivery_operation_label(context["delivery"], args.workload, args.operation)
    if not probe and stage(args) == "scheduling-proof":
        require(context.get("delivery") is not None, "task-scheduling-successor-required")
        label = scheduling_label(context["delivery"], args.scheduling_case)
    environment = {route.RUNNER.CONTROL.OPERATIONS[args.workload][0]: operation}
    profile = getattr(args, "migration_profile", "baseline")
    require(profile in {"baseline", "scheduling"}, "task-migration-profile-invalid")
    if profile == "scheduling":
        require(scheduling_migration(args), "task-migration-profile-invalid")
        if not probe: environment["PERSISTENCE_MIGRATION_PROFILE"] = "scheduling"
    if args.workload in {"verifier", "database-proof", "restore-reader"}: environment["ENTITY_SMOKE_PROOF_LABEL"] = label
    if args.workload == "verifier": environment["ENTITY_SMOKE_EXPECTED_SOURCE"] = binding["source_revision"]
    metadata_only = stage(args) in {"initial-recovery", "scheduling-qualification", "scheduling-proof"} and args.workload == "administration" or stage(args) == "credential-recovery" and (args.workload == "administration" or args.operation in {"unready", "permissions"})
    if context.get("delivery") and (args.workload, args.operation) in {("database-proof", "permissions"), ("verifier", "lifecycle")}:
        metadata_only = True
    if not probe and args.expected_digest is not None and not metadata_only:
        environment["ENTITY_SMOKE_EXPECTED_DIGEST"] = args.expected_digest
    if not probe and stage(args) == "scheduling-proof":
        selected = context.get("scheduling_selection")
        if args.operation in {"scheduling-delete", "scheduling-restore", "observe-scheduling-proof"}:
            require(isinstance(selected, dict), "task-scheduling-original-selection-required")
            if args.workload == "verifier":
                environment.update(ENTITY_SMOKE_EXPECTED_ID=selected["record_id"], ENTITY_SMOKE_EXPECTED_DIGEST=selected["record_digest"])
            else:
                environment["PERSISTENCE_SCHEDULING_PROOF_ENTITY_ID"] = selected["record_id"]
                if "due_at" in selected: environment["PERSISTENCE_SCHEDULING_PROOF_DUE_AT"] = selected["due_at"]
    deadline = 90 if probe else context["completion_deadlines"][args.workload]
    if stage(args) == "credential-recovery" and operation == "unready": deadline = 90
    return route.RUNNER.CONTROL.validate_request({**binding, "workload": args.workload, "definition": checked["definition"],
           "security_group": checked["security_group"], "subnets": checked["subnets"], "environment": environment,
           "deadline_seconds": deadline, "proof_label": label})


def prerequisite_custody(C, value):
    """Retain prerequisite identity once; do not recursively copy prior steps."""
    return POLICY.prerequisite_references(value, {"deploy/entity-smoke-task-step/v2", "deploy/entity-smoke-task-step/v3"}, C.DEPLOY.fingerprint)


def validate_delivery_step(route, value, binding, delivery, args):
    """Captured delivery custody only; callers validate actual task evidence."""
    C = route.C
    C.RESOURCE.validate_delivery(delivery)
    require(isinstance(value, dict) and set(value) == {"schema", "plan_sha256", "binding", "reservation", "receipt", "delivery", "plan", "prerequisites"}
            and value["schema"] in {"deploy/entity-smoke-task-step/v2", "deploy/entity-smoke-task-step/v3"} and value["binding"] == binding
            and isinstance(value["reservation"], dict) and isinstance(value["reservation"].get("request"), dict), "task-step-binding-mismatch")
    plan, expected = value["plan"], value["reservation"]["request"]
    fields = {"schema", "target", "scope", "account", "region", "workload", "phase", "operation", "prepared_operation", "proof_stage", "preflight_label", "database_effect",
              "expected_record_digest", "binding", "controller_sha256", "graph_sha256", "parameters_sha256", "template_sha256", "preflight_rule_sha256", "operator_sha256",
              "task_definition_sha256", "configuration_sha256", "roles_sha256", "network_sha256", "callee_bindings_sha256", "package_custody_reference", "task_count",
              "automatic_retry", "delivery", "prerequisites_sha256", "pending_prerequisite", "execution_route_available", "request_sha256"}
    profile = qualification_profile(args)
    if profile is not None: fields.add("qualification_profile")
    if stage(args) == "scheduling-qualification":
        fields.add("scheduling_manifest_sha256")
        require(isinstance(plan.get("scheduling_manifest_sha256"), str)
            and route.re.fullmatch(r"[a-f0-9]{64}", plan["scheduling_manifest_sha256"]) is not None, "task-scheduling-manifest-mismatch")
    if stage(args) == "scheduling-proof":
        fields.update({"scheduling_case", "scheduling_snapshot", "scheduling_selection_sha256"})
        require(plan.get("scheduling_case") == args.scheduling_case and plan.get("scheduling_snapshot") == args.scheduling_snapshot,
                "task-scheduling-selection-mismatch")
    if getattr(args, "scheduling_control_phase", None) is not None:
        fields.add("scheduling_control_phase")
        require(plan.get("scheduling_control_phase") == args.scheduling_control_phase, "task-scheduling-control-phase-mismatch")
    require(value["delivery"] == delivery and isinstance(plan, dict)
            and ((set(plan) == fields and plan["schema"] == "deploy/entity-smoke-task-plan/v2")
                 or (set(plan) == fields | {"preflight_renewal"} and plan["schema"] == "deploy/entity-smoke-task-plan/v3"))
            and plan["delivery"] == delivery and C.DEPLOY.fingerprint(plan) == value["plan_sha256"]
            and plan["binding"] == binding and plan["request_sha256"] == C.DEPLOY.fingerprint(expected)
            and isinstance(value["prerequisites"], dict) and plan["prerequisites_sha256"] == C.DEPLOY.fingerprint(value["prerequisites"])
            and plan["proof_stage"] == stage(args) and plan["workload"] == args.workload and plan["phase"] == args.phase
            and plan.get("qualification_profile") == profile
            and plan["prepared_operation"] == args.operation and plan["pending_prerequisite"] is None and plan["execution_route_available"] is True
            and plan["package_custody_reference"] == delivery["candidate"]["receipt_reference"], "task-step-delivery-plan-mismatch")
    validate_renewal(route, plan, binding, delivery, args)
    if getattr(args, "scheduling_control_phase", None) is not None:
        phase_packet = value["prerequisites"].get("packets", {}).get("scheduling-control-phase")
        boundary = validate_scheduling_control_phase(route, phase_packet, binding, args.scheduling_control_phase)
        timestamp = route.RUNNER.EVIDENCE.timestamp
        require(timestamp(value["prerequisites"]["required_after"]) >= timestamp(boundary)
            and timestamp(value["reservation"]["reserved_at"]) >= timestamp(boundary), "task-step-order-invalid")
    if "preflight_renewal" in plan:
        original = plan["preflight_renewal"]["packet"]
        require(POLICY.observation_expired(original["receipt"]["task"]["stopped_at"], value["receipt"]["task"]["created_at"], route.RUNNER.EVIDENCE.timestamp), "preflight-renewal-before-expiry")
    return value


def observe_packet(route, context, args, provider, *, completion_required=True, historical=False, select=True):
    """Reobserve by default; explicit retained completion is historical only."""
    C, runner = route.C, route.RUNNER
    require(type(historical) is bool and (not historical or completion_required), "task-historical-completion-required")
    if select and context.get("delivery"):
        context = {**context, "report": {"plan": dict(context["report"]["plan"])}}
        select_preflight(route, context, args, provider)
    target = path(context, args)
    runner.CONTROL.no_symlinks(target)
    if not target.exists(): return None
    value = C.read_json(target)
    if not context.get("delivery") and completion_required and route.COMPLETION.path(target).is_file():
        legacy = C.TRANSITION.legacy_context(route, context, args, value, C.read_json(route.COMPLETION.path(target)))
        if legacy is not None: context, historical = legacy, True
    delivery = context.get("delivery")
    fields = {"schema", "plan_sha256", "binding", "reservation", "receipt"} | ({"delivery", "plan", "prerequisites"} if delivery else set())
    require(isinstance(value, dict) and set(value) == fields
            and value["schema"] in ({"deploy/entity-smoke-task-step/v2", "deploy/entity-smoke-task-step/v3"} if delivery else {"deploy/entity-smoke-task-step/v1"}) and value["binding"] == context["binding"], "task-step-binding-mismatch")
    require(isinstance(value["plan_sha256"], str) and route.re.fullmatch(r"sha256:[a-f0-9]{64}", value["plan_sha256"]), "task-step-plan-invalid")
    reservation = value["reservation"]
    require(isinstance(reservation, dict) and isinstance(reservation.get("request"), dict), "task-step-reservation-invalid")
    expected = request(route, context, args)
    require(reservation["request"] == expected, "task-step-request-mismatch")
    if delivery:
        validate_delivery_step(route, value, context["binding"], delivery, args)
    store = runner.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    require(store.read(key(args, delivery), expected) == reservation, "task-step-reservation-not-retained")
    receipt = runner.EVIDENCE.validate_retained(value["receipt"], reservation)
    expected_manifest = context["report"]["plan"].get("scheduling_manifest_sha256")
    retained_manifest = value.get("plan", {}).get("scheduling_manifest_sha256")
    if expected_manifest is not None:
        require(retained_manifest == expected_manifest, "task-scheduling-manifest-mismatch")
    validate_qualification_result(args, receipt, retained_manifest)
    retained = runner.read_receipt(runner.receipt_path(context["cache"] / "task-receipts", expected, reservation), reservation)
    require(retained == receipt, "task-step-receipt-not-retained")
    if expected["workload"] == "verifier" and expected["environment"].get("ENTITY_SMOKE_VERIFICATION_OPERATION") == "unready":
        try: runner.UNREADY.read_admission(context["cache"] / "task-receipts", reservation)
        except runner.UNREADY.UnreadyFailure as failure: raise StepFailure(failure.code) from None
    elif args.phase != "preflight": runner.PREFLIGHT.read_admission(context["cache"] / "task-receipts", reservation)
    if not historical:
        task = C.RESOURCE.only(provider("ecs", "describe-tasks", cluster=C.RESOURCE.CLUSTER, tasks=[receipt["task"]["arn"]]), "tasks")
        logs = runner.EVIDENCE.read_logs(provider, expected, receipt["task"]["arn"])
        require(runner.EVIDENCE.collect(task, reservation, logs, receipt["collected_at"]) == receipt, "task-step-observation-mismatch")
    if completion_required: route.COMPLETION.read(route, context, args, target)
    return value


def prerequisites(route, context, args, provider):
    """Return the exact prefix or absence; malformed evidence is never absence."""
    from types import SimpleNamespace
    if scheduling_preparation(args): return scheduling_prerequisites(route, context, args, provider)
    if scheduling_migration(args): return scheduling_migration_prerequisites(route, context, args, provider)
    if stage(args) == "scheduling-proof": return synthetic_prerequisites(route, context, args, provider)
    if stage(args) == "scheduling-qualification":
        context["scheduling_lineage"] = scheduling_migration_lineage(route, context, args, provider)
        return route.ACCEPTANCE.prerequisites(route, context, args, provider)
    if context.get("delivery") and stage(args) != "credential-recovery": return route.ACCEPTANCE.prerequisites(route, context, args, provider)
    if stage(args) == "acceptance": return route.ACCEPTANCE.prerequisites(route, context, args, provider)
    if stage(args) == "initial-recovery": return route.RECOVERY.prerequisites(route, context, args, provider)
    if stage(args) == "credential-recovery": return route.CREDENTIAL.prerequisites(route, context, args, provider)
    index = selected(args)
    if index is None: return route.FEATURE.prerequisites(route, context, args, provider)
    created = route.C.read_json(context["cache"] / "receipts/create.json")
    previous_stop = created["result"]["reservation"]["reserved_at"]
    packets = {}
    refreshing = stage(args) == "activation"
    if refreshing: require(context["parameters"]["ServerDesiredCount"] == "0", "task-activation-refresh-requires-stopped-service")
    for name, workload, operation, logical in STEPS[:index]:
        prior_args = SimpleNamespace(**{**vars(args), "workload": workload, "operation": operation, "phase": "operation", "expected_digest": None, "proof_stage": "baseline" if refreshing else stage(args), "qualification_profile": None})
        # Each prior workload has its own checked physical definition/network.
        prior_context = {**context, "checked": route.BINDING.inspect(provider, workload, context["parameters"], context["resources"], context.get("binding_snapshot"))}
        packet = observe_packet(route, prior_context, prior_args, provider, historical=True)
        if packet is None: raise PrerequisiteMissing(name)
        receipt = packet["receipt"]
        original = route.C.TRANSITION.original_receipt(route.C, context, packet, route.C.read_json(route.COMPLETION.path(path(context, prior_args))))
        require((original or receipt["task"]["definition"] == context["resources"][logical]["physical_id"])
                and route.RUNNER.EVIDENCE.timestamp(receipt["task"]["created_at"]) >= route.RUNNER.EVIDENCE.timestamp(previous_stop), "task-step-order-invalid")
        previous_stop = receipt["task"]["stopped_at"]
        packets[name] = {"reservation": packet["reservation"], "receipt": receipt}
    result = {"required_after": previous_stop, "packets": packets}
    if refreshing:
        original_args = SimpleNamespace(**{**vars(args), "proof_stage": "baseline", "phase": "operation", "expected_digest": None})
        original = observe_packet(route, context, original_args, provider, historical=True)
        if original is None: raise PrerequisiteMissing("baseline-permissions")
        require(route.RUNNER.EVIDENCE.timestamp(original["receipt"]["task"]["created_at"]) >= route.RUNNER.EVIDENCE.timestamp(previous_stop), "task-step-order-invalid")
        result.update(required_after=original["receipt"]["task"]["stopped_at"], original_permissions_sha256=route.C.DEPLOY.fingerprint(original))
    return result


def synthetic_prerequisites(route, context, args, provider):
    """One stable synthetic row per declared case, original packets before mutation."""
    require(context.get("delivery") is not None, "task-scheduling-successor-required")
    timestamp = route.RUNNER.EVIDENCE.timestamp
    def arguments(workload, operation, **extra):
        return SimpleNamespace(**{**vars(args), "workload": workload, "operation": operation, "phase": "operation",
            "expected_digest": None, "scheduling_snapshot": None, **extra})
    def current(workload):
        return {**context, "provider": provider, "checked": route.BINDING.inspect(provider, workload, context["parameters"], context["resources"], context.get("binding_snapshot"))}
    prepare = arguments("administration", "prove-scheduling-access", proof_stage="scheduling-preparation", scheduling_case=None)
    admin = current("administration")
    base = scheduling_prerequisites(route, admin, prepare, provider)
    proven = observe_packet(route, admin, prepare, provider, historical=True)
    if proven is None: raise PrerequisiteMissing("prove-scheduling-access")
    require(timestamp(proven["receipt"]["task"]["created_at"]) >= timestamp(base["required_after"]), "task-step-order-invalid")
    base["required_after"] = proven["receipt"]["task"]["stopped_at"]
    base["packets"]["prove-scheduling-access"] = proven
    if args.operation == "scheduling-create": return base
    created_args = arguments("verifier", "scheduling-create")
    verifier = current("verifier")
    if args.operation == "scheduling-observe-create":
        terminal = route.FEATURE.original_terminal(route, verifier, args, selected=created_args)
        require(timestamp(terminal["stopped_at"]) >= timestamp(base["required_after"]), "task-step-order-invalid")
        base["packets"]["original-create-terminal"] = terminal
        base["required_after"] = terminal["stopped_at"]
        return base
    original = observe_packet(route, verifier, created_args, provider, historical=True)
    if original is None:
        reconciled_args = arguments("verifier", "scheduling-observe-create")
        original = observe_packet(route, verifier, reconciled_args, provider, historical=True)
        if original is None: raise PrerequisiteMissing("scheduling-original-record")
        base["packets"]["original-create-terminal"] = route.FEATURE.original_terminal(route, verifier, args, selected=created_args)
    result = original["receipt"]["result"]
    require(timestamp(original["receipt"]["task"]["created_at"]) >= timestamp(base["required_after"]), "task-step-order-invalid")
    context["scheduling_selection"] = {"record_id": result["record_id"], "record_digest": result["record_digest"]}
    base["packets"]["scheduling-original-record"] = original
    base["required_after"] = original["receipt"]["task"]["stopped_at"]
    if args.operation in {"scheduling-delete", "scheduling-restore"} or args.scheduling_case == "scope-isolation": return base
    deletion_args = arguments("verifier", "scheduling-restore" if args.scheduling_case == "cancellation" else "scheduling-delete")
    verifier["scheduling_selection"] = context["scheduling_selection"]
    deletion = observe_packet(route, verifier, deletion_args, provider, historical=True)
    if deletion is None: raise PrerequisiteMissing("scheduling-original-deletion")
    deleted = deletion["receipt"]["result"]
    require((deleted["record_id"], deleted["record_digest"]) == (result["record_id"], result["record_digest"])
            and timestamp(deletion["receipt"]["task"]["created_at"]) >= timestamp(base["required_after"]), "task-scheduling-original-selection-required")
    context["scheduling_selection"] = {**context["scheduling_selection"], "due_at": deleted["due_at"]}
    base["packets"]["scheduling-original-deletion"] = deletion
    base["required_after"] = deletion["receipt"]["task"]["stopped_at"]
    return base


def scheduling_migration_lineage(route, context, args, provider):
    """Independently retain exact prefix and successful explicit-profile apply.

    Acceptance uses this link before its later full-state observation. A
    complete prefix requires no manufactured apply task or success receipt.
    """
    selected = SimpleNamespace(**{**vars(args), "proof_stage": "scheduling-migration", "workload": "migration",
        "operation": "apply", "phase": "operation", "migration_profile": "scheduling", "qualification_profile": None, "expected_digest": None})
    current = {**context, "checked": route.BINDING.inspect(provider, "migration", context["parameters"], context["resources"], context.get("binding_snapshot"))}
    result = scheduling_migration_prerequisites(route, current, selected, provider, historical=True)
    prefix = result["packets"]["observe-scheduling-prefix"]["receipt"]["result"]["migration_prefix"]
    if prefix["state"] == "partial":
        migration = observe_packet(route, current, selected, provider, historical=True)
        if migration is None: raise PrerequisiteMissing("scheduling-migration")
        timestamp = route.RUNNER.EVIDENCE.timestamp
        require(timestamp(migration["receipt"]["task"]["created_at"]) >= timestamp(result["required_after"]), "task-step-order-invalid")
        result["required_after"] = migration["receipt"]["task"]["stopped_at"]
        result["packets"]["scheduling-migration"] = migration
    return {**result, "manifest_sha256": prefix["manifest_sha256"]}


def scheduling_prerequisites(route, context, args, provider):
    """Metadata preparation precedes scheduler activation and application proof."""
    C, timestamp = route.C, route.RUNNER.EVIDENCE.timestamp
    if context.get("delivery"):
        # delivery_context already validates the accepted predecessor identity;
        # completed_deployment independently binds the installed maintenance image.
        deployed = C.completed_deployment(provider, context["binding"], context["parameters"], context["delivery"])
        required_after = deployed["required_after"]
        packets = {"maintenance-deployment": deployed["receipt"], "bootstrap-lineage": context["delivery"]["predecessor"]}
    else:
        bootstrap_args = SimpleNamespace(**{**vars(args), "proof_stage": "baseline", "workload": "administration",
                                            "operation": "bootstrap", "phase": "operation", "expected_digest": None, "migration_profile": "baseline"})
        bootstrap_context = {**context, "checked": route.BINDING.inspect(provider, "administration", context["parameters"], context["resources"], context.get("binding_snapshot"))}
        bootstrap = observe_packet(route, bootstrap_context, bootstrap_args, provider, historical=True)
        if bootstrap is None: raise PrerequisiteMissing("bootstrap")
        required_after = bootstrap["receipt"]["task"]["stopped_at"]
        packets = {"bootstrap": bootstrap}
    if getattr(args, "scheduling_control_phase", None) is not None:
        require(context.get("delivery") is not None, "task-scheduling-successor-required")
        require_other_scheduling_state_terminal(route, context, args, provider)
        try:
            phase_packet = scheduling_control().read_disabled_phase("kanbien-core-platform", "entity-smoke", args.scheduling_control_phase)
        except Exception:
            raise StepFailure("task-scheduling-control-phase-not-confirmed") from None
        boundary = validate_scheduling_control_phase(route, phase_packet, context["binding"], args.scheduling_control_phase)
        require(timestamp(boundary) >= timestamp(required_after), "task-step-order-invalid")
        required_after, packets["scheduling-control-phase"] = boundary, phase_packet
    preceding = {"grant-scheduling-access": ("observe-scheduling-state",),
                 "prove-scheduling-access": ("observe-scheduling-state", "grant-scheduling-access")}.get(args.operation, ())
    expected_state = None
    for operation in preceding:
        prior_args = SimpleNamespace(**{**vars(args), "operation": operation, "phase": "operation"})
        prior = observe_packet(route, context, prior_args, provider, historical=True)
        if prior is None: raise PrerequisiteMissing(operation)
        state = prior["receipt"]["result"].get("database_state")
        require(isinstance(state, dict) and state.get("migration_count") == 7,
                "task-scheduling-complete-state-required")
        if expected_state is not None:
            require(state["manifest_sha256"] == expected_state["manifest_sha256"], "task-scheduling-manifest-mismatch")
        expected_state = state
        require(timestamp(prior["receipt"]["task"]["created_at"]) >= timestamp(required_after), "task-step-order-invalid")
        required_after = prior["receipt"]["task"]["stopped_at"]
        packets[operation] = prior
    request_value = request(route, context, args)
    store = route.RUNNER.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    reservation = store.read(key(args, context.get("delivery")), request_value)
    # Fresh state is needed to admit a new mutating grant; an existing exact
    # reservation reconciles its original admission instead of replaying it.
    if args.operation == "grant-scheduling-access" and reservation is None and args.phase == "operation":
        require(not POLICY.observation_expired(required_after, C.now(), timestamp), "task-scheduling-state-not-fresh")
    C.RESOURCE.require_other_tasks_terminal(provider, reservation=reservation)
    return {"required_after": required_after, "packets": packets}


def require_other_scheduling_state_terminal(route, context, args, provider):
    """A new finite phase never bypasses another unresolved native state task."""
    store = route.RUNNER.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    for phase in (None, *SCHEDULING_STATE_PHASES):
        if phase == args.scheduling_control_phase: continue
        selected = SimpleNamespace(**{**vars(args), "scheduling_control_phase": phase, "preflight_renewal_selection": None})
        current = {**context, "report": {"plan": dict(context["report"]["plan"])}}
        select_preflight(route, current, selected, provider)
        for task_phase in ("preflight", "operation"):
            candidate = SimpleNamespace(**{**vars(selected), "phase": task_phase})
            expected = request(route, current, candidate)
            if store.read(key(candidate, context["delivery"]), expected) is None: continue
            require(route.COMPLETION.path(path(current, candidate)).is_file(), "task-scheduling-original-state-unresolved")
            require(observe_packet(route, current, candidate, provider, historical=True) is not None,
                "task-scheduling-original-state-unresolved")


def scheduling_migration_prerequisites(route, context, args, provider, *, historical=False):
    """Use the actual retained prefix, current maintenance and DB incarnation.

    The existing qualified binding contains source/image and dependency identity.
    No application record or baseline application acceptance is a prerequisite.
    A terminal failed apply has no retry route here: its original reservation
    continues to reconcile until a separately governed successor observation.
    """
    result = scheduling_prerequisites(route, context, args, provider)
    prior_args = SimpleNamespace(**{**vars(args), "proof_stage": "scheduling-preparation", "workload": "administration",
        "operation": "observe-scheduling-prefix", "phase": "operation", "migration_profile": "baseline", "expected_digest": None})
    prior_context = {**context, "checked": route.BINDING.inspect(provider, "administration", context["parameters"], context["resources"], context.get("binding_snapshot"))}
    prior = observe_packet(route, prior_context, prior_args, provider, historical=True)
    if prior is None: raise PrerequisiteMissing("observe-scheduling-prefix")
    prefix = route.RUNNER.EVIDENCE.SCHEDULING_STATE.validate_prefix(prior["receipt"]["result"].get("migration_prefix"),
        minimum_applied_migrations=1, manifest_migration_count=7)
    timestamp = route.RUNNER.EVIDENCE.timestamp
    require(timestamp(prior["receipt"]["task"]["created_at"]) >= timestamp(result["required_after"]), "task-step-order-invalid")
    request_value = request(route, context, args)
    reserved = route.RUNNER.CONTROL.AttemptStore(context["cache"] / "task-attempts").read(key(args, context.get("delivery")), request_value)
    if reserved is None and not historical:
        require(not POLICY.observation_expired(prior["receipt"]["task"]["stopped_at"], route.C.now(), timestamp), "task-scheduling-prefix-not-fresh")
    # Retaining the packet in the existing prerequisite digest binds the exact
    # prefix result. Its state is not an assertion that a migration was run.
    result["packets"]["observe-scheduling-prefix"] = prior
    result["required_after"] = prior["receipt"]["task"]["stopped_at"]
    return result


def retain(route, context, args, reservation, receipt):
    value = {"schema": "deploy/entity-smoke-task-step/v1", "plan_sha256": context["report"]["plan_sha256"],
             "binding": context["binding"], "reservation": reservation, "receipt": receipt}
    if context.get("delivery"):
        value.update(schema="deploy/entity-smoke-task-step/v3", delivery=context["delivery"], plan=context["report"]["plan"],
            prerequisites=prerequisite_custody(route.C, context["prerequisites"]))
    target = path(context, args)
    if not route.C.RESOURCE.write_exclusive(target, value):
        previous = route.C.read_json(target)
        # A fresh gate report timestamp/approval does not rewrite historical proof.
        require(isinstance(previous, dict) and {k: v for k, v in previous.items() if k != "plan_sha256"} == {k: v for k, v in value.items() if k != "plan_sha256"}, "task-step-retention-conflict")
    return target


def manifest(route, context, args, provider, prerequisites, packet):
    if context.get("delivery"): return None
    if stage(args) not in {"baseline", "activation"}: return None
    if (args.workload, args.operation, args.phase) != ("database-proof", "permissions", "operation"): return None
    value = {**prerequisites["packets"], "permissions": {"reservation": packet["reservation"], "receipt": packet["receipt"]}}
    target = context["cache"] / "task-steps" / ("activation-refresh-" + activation_generation(args) + "-prerequisites.json" if stage(args) == "activation" else "activation-prerequisites.json")
    if not route.C.RESOURCE.write_exclusive(target, value): require(route.C.read_json(target) == value, "task-activation-manifest-conflict")
    # The existing real activation consumer remains authoritative; do not invent
    # a second interpretation or mark activation itself complete here.
    store = route.C.RESOURCE.ResourceStore(context["cache"] / "attempts")
    route.C.activation_prerequisites(provider, target, context["binding"], context["parameters"], context["cache"], store)
    return target
