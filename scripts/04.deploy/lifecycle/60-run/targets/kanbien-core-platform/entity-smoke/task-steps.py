#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-steps
#   version: 2
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-15"
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

_spec = importlib.util.spec_from_file_location("entity_smoke_step_recovery_selection", Path(__file__).with_name("source-transition.py"))
TRANSITION = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(TRANSITION)

STEPS = (
    ("bootstrap", "administration", "bootstrap", "AdministrationTaskDefinition"),
    ("migration", "migration", "apply", "MigrationTaskDefinition"),
    ("grant-runtime", "administration", "grant-runtime", "AdministrationTaskDefinition"),
    ("permissions", "database-proof", "permissions", "DatabaseProofTaskDefinition"),
)


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


def stage(args):
    value = getattr(args, "proof_stage", "baseline")
    allowed = {"baseline": None, "server-replacement": {("verifier", "read")}, "initial-recovery": {("verifier", "read"), ("administration", "observe-migration-state")}}
    allowed["credential-recovery"] = {("administration", value) for value in ("observe-permissions", "revoke-runtime", "restore-runtime")} | {("verifier", "unready"), ("verifier", "read"), ("database-proof", "permissions")}
    allowed["isolated-restore"] = {("restore-reader", "restore-read")}
    allowed["acceptance"] = {("verifier", "read")}
    allowed["activation"] = {("database-proof", "permissions")}
    require(value in allowed and (allowed[value] is None or (args.workload, args.operation) in allowed[value]), "task-proof-stage-not-supported")
    require(not (value == "credential-recovery" and args.operation == "unready") or args.phase == "operation", "task-unready-preflight-phase-prohibited")
    return value


def activation_generation(args):
    value = getattr(args, "activation_generation", None)
    require(isinstance(value, str) and value.startswith("sha256:") and len(value) == 71
            and all(character in "0123456789abcdef" for character in value[7:]), "task-activation-controller-required")
    return value[7:]


def key(args, delivery=None):
    suffix = "" if stage(args) == "baseline" else ":" + stage(args)
    if delivery is None:
        if TRANSITION.acceptance_refresh(args): suffix += ":collector-recovery-1"
        if TRANSITION.acceptance_renewal(args) and args.phase == "preflight": suffix += ":readback-recovery-1"
    if stage(args) == "activation": suffix += ":" + activation_generation(args)
    if delivery is not None: suffix += ":delivery:" + delivery["delivery_id"]
    return "task-" + hashlib.sha256((args.proof_label + ":" + args.workload + ":" + args.operation + ":" + args.phase + suffix).encode()).hexdigest()[:48]


def path(context, args):
    suffix = "" if stage(args) == "baseline" else "-" + stage(args)
    if not context.get("delivery"): suffix += TRANSITION.preflight_step_suffix(args)
    if stage(args) == "activation":
        generation = activation_generation(args)
        require(context["artifact"] == "sha256:" + generation, "task-activation-controller-mismatch")
        suffix += "-" + generation
    return context["cache"] / "task-steps" / (args.workload + "-" + args.operation + suffix + "-" + args.phase + ".json")


def request(route, context, args):
    binding, checked = context["binding"], context["checked"]
    probe = args.phase == "preflight"
    operation = ("ready" if args.workload == "verifier" else "preflight") if probe else args.operation
    label = context["report"]["plan"]["preflight_label"] if probe else args.proof_label
    if not probe and context.get("delivery"):
        label = route.C.delivery_operation_label(context["delivery"], args.workload, args.operation)
    environment = {route.RUNNER.CONTROL.OPERATIONS[args.workload][0]: operation}
    if args.workload in {"verifier", "database-proof", "restore-reader"}: environment["ENTITY_SMOKE_PROOF_LABEL"] = label
    if args.workload == "verifier": environment["ENTITY_SMOKE_EXPECTED_SOURCE"] = binding["source_revision"]
    metadata_only = stage(args) == "initial-recovery" and args.workload == "administration" or stage(args) == "credential-recovery" and (args.workload == "administration" or args.operation in {"unready", "permissions"})
    if context.get("delivery") and (args.workload, args.operation) in {("database-proof", "permissions"), ("verifier", "lifecycle")}:
        metadata_only = True
    if not probe and args.expected_digest is not None and not metadata_only:
        environment["ENTITY_SMOKE_EXPECTED_DIGEST"] = args.expected_digest
    deadline = 90 if probe else context["completion_deadlines"][args.workload]
    if stage(args) == "credential-recovery" and operation == "unready": deadline = 90
    return route.RUNNER.CONTROL.validate_request({**binding, "workload": args.workload, "definition": checked["definition"],
           "security_group": checked["security_group"], "subnets": checked["subnets"], "environment": environment,
           "deadline_seconds": deadline, "proof_label": label})


def validate_delivery_step(route, value, binding, delivery, args):
    """Captured delivery custody only; callers validate actual task evidence."""
    C = route.C
    C.RESOURCE.validate_delivery(delivery)
    require(isinstance(value, dict) and set(value) == {"schema", "plan_sha256", "binding", "reservation", "receipt", "delivery", "plan", "prerequisites"}
            and value["schema"] == "deploy/entity-smoke-task-step/v2" and value["binding"] == binding
            and isinstance(value["reservation"], dict) and isinstance(value["reservation"].get("request"), dict), "task-step-binding-mismatch")
    plan, expected = value["plan"], value["reservation"]["request"]
    fields = {"schema", "target", "scope", "account", "region", "workload", "phase", "operation", "prepared_operation", "proof_stage", "preflight_label", "database_effect",
              "expected_record_digest", "binding", "controller_sha256", "graph_sha256", "parameters_sha256", "template_sha256", "preflight_rule_sha256", "operator_sha256",
              "task_definition_sha256", "configuration_sha256", "roles_sha256", "network_sha256", "callee_bindings_sha256", "package_custody_reference", "task_count",
              "automatic_retry", "delivery", "prerequisites_sha256", "pending_prerequisite", "execution_route_available", "request_sha256"}
    require(value["delivery"] == delivery and isinstance(plan, dict) and set(plan) == fields and plan["schema"] == "deploy/entity-smoke-task-plan/v2"
            and plan["delivery"] == delivery and C.DEPLOY.fingerprint(plan) == value["plan_sha256"]
            and plan["binding"] == binding and plan["request_sha256"] == C.DEPLOY.fingerprint(expected)
            and isinstance(value["prerequisites"], dict) and plan["prerequisites_sha256"] == C.DEPLOY.fingerprint(value["prerequisites"])
            and plan["proof_stage"] == stage(args) and plan["workload"] == args.workload and plan["phase"] == args.phase
            and plan["prepared_operation"] == args.operation and plan["pending_prerequisite"] is None and plan["execution_route_available"] is True
            and plan["package_custody_reference"] == delivery["candidate"]["receipt_reference"], "task-step-delivery-plan-mismatch")
    require(plan["preflight_label"] == C.delivery_preflight_label(delivery, stage(args), args.workload, args.operation), "task-step-delivery-label-mismatch")
    return value


def observe_packet(route, context, args, provider, *, completion_required=True, historical=False):
    """Reobserve by default; explicit retained completion is historical only."""
    C, runner = route.C, route.RUNNER
    require(type(historical) is bool and (not historical or completion_required), "task-historical-completion-required")
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
            and value["schema"] == "deploy/entity-smoke-task-step/" + ("v2" if delivery else "v1") and value["binding"] == context["binding"], "task-step-binding-mismatch")
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
    if context.get("delivery"): return route.ACCEPTANCE.prerequisites(route, context, args, provider)
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
        prior_args = SimpleNamespace(**{**vars(args), "workload": workload, "operation": operation, "phase": "operation", "expected_digest": None, "proof_stage": "baseline" if refreshing else stage(args)})
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


def retain(route, context, args, reservation, receipt):
    value = {"schema": "deploy/entity-smoke-task-step/v1", "plan_sha256": context["report"]["plan_sha256"],
             "binding": context["binding"], "reservation": reservation, "receipt": receipt}
    if context.get("delivery"):
        value.update(schema="deploy/entity-smoke-task-step/v2", delivery=context["delivery"], plan=context["report"]["plan"], prerequisites=context["prerequisites"])
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
