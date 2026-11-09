#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-steps
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
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
    require(value in allowed and (allowed[value] is None or (args.workload, args.operation) in allowed[value]), "task-proof-stage-not-supported")
    require(not (value == "credential-recovery" and args.operation == "unready") or args.phase == "operation", "task-unready-preflight-phase-prohibited")
    return value


def key(args):
    suffix = "" if stage(args) == "baseline" else ":" + stage(args)
    return "task-" + hashlib.sha256((args.proof_label + ":" + args.workload + ":" + args.operation + ":" + args.phase + suffix).encode()).hexdigest()[:48]


def path(context, args):
    suffix = "" if stage(args) == "baseline" else "-" + stage(args)
    return context["cache"] / "task-steps" / (args.workload + "-" + args.operation + suffix + "-" + args.phase + ".json")


def request(route, context, args):
    binding, checked = context["binding"], context["checked"]
    probe = args.phase == "preflight"
    operation = ("ready" if args.workload == "verifier" else "preflight") if probe else args.operation
    label = context["report"]["plan"]["preflight_label"] if probe else args.proof_label
    environment = {route.RUNNER.CONTROL.OPERATIONS[args.workload][0]: operation}
    if args.workload in {"verifier", "database-proof", "restore-reader"}: environment["ENTITY_SMOKE_PROOF_LABEL"] = label
    if args.workload == "verifier": environment["ENTITY_SMOKE_EXPECTED_SOURCE"] = binding["source_revision"]
    metadata_only = stage(args) == "initial-recovery" and args.workload == "administration" or stage(args) == "credential-recovery" and (args.workload == "administration" or args.operation in {"unready", "permissions"})
    if not probe and args.expected_digest is not None and not metadata_only:
        environment["ENTITY_SMOKE_EXPECTED_DIGEST"] = args.expected_digest
    deadline = 90 if probe else context["completion_deadlines"][args.workload]
    if stage(args) == "credential-recovery" and operation == "unready": deadline = 90
    return route.RUNNER.CONTROL.validate_request({**binding, "workload": args.workload, "definition": checked["definition"],
           "security_group": checked["security_group"], "subnets": checked["subnets"], "environment": environment,
           "deadline_seconds": deadline, "proof_label": label})


def observe_packet(route, context, args, provider, *, completion_required=True, historical=False):
    """Reobserve by default; explicit retained completion is historical only."""
    C, runner = route.C, route.RUNNER
    require(type(historical) is bool and (not historical or completion_required), "task-historical-completion-required")
    target = path(context, args)
    runner.CONTROL.no_symlinks(target)
    if not target.exists(): return None
    value = C.read_json(target)
    require(isinstance(value, dict) and set(value) == {"schema", "plan_sha256", "binding", "reservation", "receipt"}
            and value["schema"] == "deploy/entity-smoke-task-step/v1" and value["binding"] == context["binding"], "task-step-binding-mismatch")
    require(isinstance(value["plan_sha256"], str) and route.re.fullmatch(r"sha256:[a-f0-9]{64}", value["plan_sha256"]), "task-step-plan-invalid")
    reservation = value["reservation"]
    require(isinstance(reservation, dict) and isinstance(reservation.get("request"), dict), "task-step-reservation-invalid")
    expected = request(route, context, args)
    require(reservation["request"] == expected, "task-step-request-mismatch")
    store = runner.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    require(store.read(key(args), expected) == reservation, "task-step-reservation-not-retained")
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
    if stage(args) == "acceptance": return route.ACCEPTANCE.prerequisites(route, context, args, provider)
    if stage(args) == "initial-recovery": return route.RECOVERY.prerequisites(route, context, args, provider)
    if stage(args) == "credential-recovery": return route.CREDENTIAL.prerequisites(route, context, args, provider)
    index = selected(args)
    if index is None: return route.FEATURE.prerequisites(route, context, args, provider)
    created = route.C.read_json(context["cache"] / "receipts/create.json")
    previous_stop = created["result"]["reservation"]["reserved_at"]
    packets = {}
    for name, workload, operation, logical in STEPS[:index]:
        prior_args = SimpleNamespace(**{**vars(args), "workload": workload, "operation": operation, "phase": "operation", "expected_digest": None})
        # Each prior workload has its own checked physical definition/network.
        prior_context = {**context, "checked": route.BINDING.inspect(provider, workload, context["parameters"], context["resources"], context.get("binding_snapshot"))}
        packet = observe_packet(route, prior_context, prior_args, provider)
        if packet is None: raise PrerequisiteMissing(name)
        receipt = packet["receipt"]
        require(receipt["task"]["definition"] == context["resources"][logical]["physical_id"]
                and route.RUNNER.EVIDENCE.timestamp(receipt["task"]["created_at"]) >= route.RUNNER.EVIDENCE.timestamp(previous_stop), "task-step-order-invalid")
        previous_stop = receipt["task"]["stopped_at"]
        packets[name] = {"reservation": packet["reservation"], "receipt": receipt}
    return {"required_after": previous_stop, "packets": packets}


def retain(route, context, args, reservation, receipt):
    value = {"schema": "deploy/entity-smoke-task-step/v1", "plan_sha256": context["report"]["plan_sha256"],
             "binding": context["binding"], "reservation": reservation, "receipt": receipt}
    target = path(context, args)
    if not route.C.RESOURCE.write_exclusive(target, value):
        previous = route.C.read_json(target)
        # A fresh gate report timestamp/approval does not rewrite historical proof.
        require(isinstance(previous, dict) and {k: v for k, v in previous.items() if k != "plan_sha256"} == {k: v for k, v in value.items() if k != "plan_sha256"}, "task-step-retention-conflict")
    return target


def manifest(route, context, args, provider, prerequisites, packet):
    if stage(args) != "baseline": return None
    if (args.workload, args.operation, args.phase) != ("database-proof", "permissions", "operation"): return None
    value = {**prerequisites["packets"], "permissions": {"reservation": packet["reservation"], "receipt": packet["receipt"]}}
    target = context["cache"] / "task-steps/activation-prerequisites.json"
    if not route.C.RESOURCE.write_exclusive(target, value): require(route.C.read_json(target) == value, "task-activation-manifest-conflict")
    # The existing real activation consumer remains authoritative; do not invent
    # a second interpretation or mark activation itself complete here.
    store = route.C.RESOURCE.ResourceStore(context["cache"] / "attempts")
    route.C.activation_prerequisites(provider, target, context["binding"], context["parameters"], context["cache"], store)
    return target
