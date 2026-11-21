#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.recovery-history
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-21"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Retain completed credential proof and its bounded immutable file closure before long restore work without claiming current readiness.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from pathlib import PurePosixPath
from types import SimpleNamespace

DIRECTORIES = ("attempts", "receipts", "failure-attempts", "failure-receipts", "task-attempts", "task-receipts", "task-steps", "initial-restart-plans", "credential-replacement-plans", "replacement-plans")
TOP = ("initial-restart-plan.json", "initial-restart-receipt.json", "credential-replacement-plan.json", "credential-replacement-receipt.json", "replacement-plan.json", "replacement-receipt.json")
GATE_DIRECTORIES = ("task-realization", "failure-realization", "initial-restart-realization", "replacement-realization", "credential-replacement-realization")
SCHEMA = "deploy/entity-smoke-credential-history/v1"
MAX_DEPENDENCIES = 512
TOP += ("source-transition/receipt.json",)
TOP += ("initial-restart-receipt.completion.json", "credential-replacement-receipt.completion.json", "replacement-receipt.completion.json")


class HistoryFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(allowed, code):
    if not allowed: raise HistoryFailure(code)


def supported(args):
    return (getattr(args, "proof_stage", "baseline"), args.workload, args.operation, args.phase) == ("credential-recovery", "database-proof", "permissions", "operation")


def local(route, cache, name):
    require(isinstance(name, str) and len(name) <= 256 and "\\" not in name, "history-reference-invalid")
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and str(relative) == name and all(part not in {".", ".."} for part in relative.parts)
            and relative.suffix == ".json" and (name in TOP or len(relative.parts) == 2 and relative.parts[0] in DIRECTORIES + GATE_DIRECTORIES
            or len(relative.parts) == 3 and relative.parts[:2] == ("task-receipts", "admissions")
            or len(relative.parts) == 4 and relative.parts[:3] == ("task-receipts", "unready", "admissions")), "history-reference-invalid")
    path = cache / name
    route.RUNNER.CONTROL.no_symlinks(path)
    require(path.is_file() and path.stat().st_size <= 1048576, "history-dependency-unavailable")
    return path


def closure(route, cache):
    candidates = set()
    for directory in DIRECTORIES:
        root = cache / directory
        route.RUNNER.CONTROL.no_symlinks(root)
        if root.exists():
            for path in root.rglob("*.json"):
                candidates.add(str(path.relative_to(cache)))
                require(len(candidates) <= MAX_DEPENDENCIES, "history-dependency-bound-exceeded")
    candidates.update(name for name in TOP if (cache / name).exists())
    for name in list(candidates):
        value = route.C.read_json(local(route, cache, name))
        if isinstance(value, dict) and "realization_evidence" in value:
            reference = value["realization_evidence"]
            prefix = str(cache.relative_to(route.C.ROOT)) + "/"
            require(isinstance(reference, str) and reference.startswith(prefix), "history-gate-reference-invalid")
            candidates.add(reference[len(prefix):])
    require(1 <= len(candidates) <= MAX_DEPENDENCIES, "history-dependency-bound-exceeded")
    return {name: route.C.digest_file(local(route, cache, name)) for name in sorted(candidates)}


def retain(route, context, args):
    if not supported(args): return None
    packet = route.STEPS.observe_packet(route, context, args, context["provider"], historical=True)
    require(packet is not None, "history-final-permission-required")
    value = {"schema": SCHEMA, "binding": {**context["binding"], "record_digest": args.expected_digest}, "controller_sha256": context["artifact"],
             "plan": context["report"]["plan"], "plan_sha256": context["report"]["plan_sha256"], "prerequisites": context["prerequisites"],
             "final_step": str(route.STEPS.path(context, args).relative_to(context["cache"])), "completed_at": packet["receipt"]["collected_at"],
             "references": closure(route, context["cache"]), "current_readiness": False, "scope_acceptance": False}
    target = context["cache"] / "credential-history.json"
    validate(route, context, args, value)
    route.C.RESOURCE.write_exclusive(target, value)
    read(route, context, args)
    return target


def reconcile(route, context, args):
    """Finish local history retention after a genuinely completed final task."""
    if not supported(args): return None
    C = route.C
    step = route.STEPS.path(context, args)
    companion = route.COMPLETION.path(step)
    route.RUNNER.CONTROL.no_symlinks(step)
    route.RUNNER.CONTROL.no_symlinks(companion)
    if not step.is_file() or not companion.is_file(): return None
    packet = route.STEPS.observe_packet(route, context, args, context["provider"], historical=True)
    controller = route.COMPLETION.controller_for(route, packet, C.read_json(companion), context["artifact"])
    plan = {**context["report"]["plan"], "controller_sha256": controller}
    require(C.DEPLOY.fingerprint(plan) == packet["plan_sha256"], "history-original-plan-not-confirmed")
    original = {**context, "artifact": controller,
                "report": {"plan": plan, "plan_sha256": packet["plan_sha256"]}}
    context["provider"].effect = "original-task-completion-observed"
    return retain(route, original, args)


def read(route, context, args):
    C = route.C
    target = context["cache"] / "credential-history.json"
    route.RUNNER.CONTROL.no_symlinks(target)
    require(target.is_file(), "history-completion-required")
    value = C.read_json(target)
    return validate(route, context, args, value)


def validate(route, context, args, value):
    C = route.C
    require(isinstance(value, dict) and set(value) == {"schema", "binding", "controller_sha256", "plan", "plan_sha256", "prerequisites", "final_step", "completed_at", "references", "current_readiness", "scope_acceptance"}
            and value["schema"] == SCHEMA and value["current_readiness"] is False and value["scope_acceptance"] is False, "history-packet-invalid")
    selected = SimpleNamespace(**{**vars(args), "proof_stage": "credential-recovery", "workload": "database-proof", "operation": "permissions", "phase": "operation"})
    step = route.STEPS.path(context, selected)
    controller = route.COMPLETION.controller_for(route, C.read_json(step), C.read_json(route.COMPLETION.path(step)), context["artifact"])
    require(value["binding"] == {**context["binding"], "record_digest": args.expected_digest} and value["controller_sha256"] == controller, "history-source-or-binding-mismatch")
    plan, references, prerequisites = value["plan"], value["references"], value["prerequisites"]
    require(isinstance(plan, dict) and value["plan_sha256"] == C.DEPLOY.fingerprint(plan) and plan.get("binding") == context["binding"]
            and plan.get("controller_sha256") == value["controller_sha256"] and plan.get("proof_stage") == "credential-recovery"
            and (plan.get("workload"), plan.get("operation"), plan.get("phase")) == ("database-proof", "permissions", "operation")
            and plan.get("expected_record_digest") == args.expected_digest and isinstance(prerequisites, dict)
            and plan.get("prerequisites_sha256") == C.DEPLOY.fingerprint(route.STEPS.prerequisite_custody(C, prerequisites) if context.get("delivery") else prerequisites), "history-final-plan-mismatch")
    require(isinstance(references, dict) and 1 <= len(references) <= MAX_DEPENDENCIES, "history-reference-set-invalid")
    for name, digest in references.items():
        require(isinstance(digest, str) and route.re.fullmatch(r"sha256:[a-f0-9]{64}", digest) and C.digest_file(local(route, context["cache"], name)) == digest, "history-dependency-changed")
    require(value["final_step"] == str(step.relative_to(context["cache"])) and value["final_step"] in references, "history-final-step-not-bound")
    packets = prerequisites.get("packets")
    delivery = context.get("delivery")
    baseline = {"deployment", "predecessor", "recovery-baseline-read", "recovery-applied-history", "recovery-runtime"} if delivery else {"initial-stop", "initial-restart", "initial-recovery-original-read", "initial-recovery-applied-history"}
    require(isinstance(packets, dict) and baseline | {"credential-permission-state", "credential-revoke", "credential-unready", "credential-restore", "credential-replacement", "credential-read"} <= set(packets), "history-prerequisite-set-incomplete")
    required = {"credential-replacement-receipt.json", "credential-replacement-plan.json"}
    if delivery:
        require(plan.get("delivery") == delivery, "history-source-or-binding-mismatch")
        C.validate_deployment_receipt(packets["deployment"], context["binding"], delivery)
        require(C.read_json(context["cache"] / "receipts/update.json") == packets["deployment"], "history-source-or-binding-mismatch")
        required.add("receipts/update.json")
        prior_steps = (("verifier", "read", "baseline"), ("administration", "observe-migration-state", "initial-recovery"))
    else:
        required.update({"initial-restart-receipt.json", "initial-restart-plan.json", "failure-attempts/root.json", "failure-receipts/stopped.json", "receipts/create.json"})
        prior_steps = (("verifier", "read", "server-replacement"), ("verifier", "read", "initial-recovery"), ("administration", "observe-migration-state", "initial-recovery"))
    for phase in (("credential-replacement",) if delivery else ("start-runtime", "credential-replacement")):
        required.add("attempts/" + args.proof_label + "-" + phase + ".json")
    for workload, operation, stage in (*prior_steps,
                                      *((workload, operation, "credential-recovery") for _, workload, operation in route.CREDENTIAL.STEPS)):
        for phase in (("operation",) if operation == "unready" else ("preflight", "operation")):
            prior = SimpleNamespace(**{**vars(selected), "workload": workload, "operation": operation, "proof_stage": stage, "phase": phase})
            prior_step = route.STEPS.path(context, prior)
            required.update(str(path.relative_to(context["cache"])) for path in (prior_step, route.COMPLETION.path(prior_step)))
            packet = C.read_json(local(route, context["cache"], str(prior_step.relative_to(context["cache"]))))
            if delivery:
                route.STEPS.validate_delivery_step(route, packet, context["binding"], delivery, prior)
            else:
                require(isinstance(packet, dict) and set(packet) == {"schema", "plan_sha256", "binding", "reservation", "receipt"}
                        and packet["schema"] == "deploy/entity-smoke-task-step/v1" and packet["binding"] == context["binding"], "history-step-packet-invalid")
            reservation = packet["reservation"]
            receipt = route.RUNNER.EVIDENCE.validate_retained(packet["receipt"], reservation)
            store = route.RUNNER.CONTROL.AttemptStore(context["cache"] / "task-attempts")
            require(store.read(route.STEPS.key(prior, delivery), reservation["request"]) == reservation
                    and route.RUNNER.read_receipt(route.RUNNER.receipt_path(context["cache"] / "task-receipts", reservation["request"], reservation), reservation) == receipt, "history-step-custody-mismatch")
            route.COMPLETION.read(route, context, prior, prior_step)
            required.update(str(path.relative_to(context["cache"])) for path in (store.path_for(route.STEPS.key(prior, delivery), reservation["request"]), route.RUNNER.receipt_path(context["cache"] / "task-receipts", reservation["request"], reservation)))
            if phase == "operation":
                path = route.RUNNER.UNREADY.path_for(context["cache"] / "task-receipts", reservation) if operation == "unready" else route.RUNNER.PREFLIGHT.admission_path(context["cache"] / "task-receipts", reservation)
                required.add(str(path.relative_to(context["cache"])))
                try:
                    if operation == "unready": route.RUNNER.UNREADY.read_admission(context["cache"] / "task-receipts", reservation, prerequisites.get("revocation"))
                    else: route.RUNNER.PREFLIGHT.read_admission(context["cache"] / "task-receipts", reservation)
                except (route.RUNNER.UNREADY.UnreadyFailure, route.RUNNER.PREFLIGHT.PreflightFailure) as failure: raise HistoryFailure(failure.code) from None
    require(required <= set(references), "history-required-dependencies-omitted")
    for name in references:
        if name.endswith(".json"):
            completed = C.read_json(local(route, context["cache"], name))
            if not isinstance(completed, dict) or "realization_evidence" not in completed: continue
            prefix = str(context["cache"].relative_to(C.ROOT)) + "/"
            ref = completed.get("realization_evidence") if isinstance(completed, dict) else None
            require(isinstance(ref, str) and ref.startswith(prefix) and ref[len(prefix):] in references
                    and references[ref[len(prefix):]] == completed.get("realization_evidence_sha256"), "history-completion-gate-omitted")
    packet = route.STEPS.observe_packet(route, context, selected, context["provider"], historical=True)
    require(packet is not None and packet["plan_sha256"] == value["plan_sha256"] and plan.get("request_sha256") == C.DEPLOY.fingerprint(packet["reservation"]["request"])
            and value["completed_at"] == packet["receipt"]["collected_at"], "history-final-completion-mismatch")
    C.RESOURCE.timestamp(value["completed_at"])
    return value
