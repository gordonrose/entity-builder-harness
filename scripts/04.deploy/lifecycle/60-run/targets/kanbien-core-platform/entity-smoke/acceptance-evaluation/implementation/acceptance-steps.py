#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.acceptance-steps
#   version: 4
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind first-qualification final read and ordinary successor checks to their actual prerequisite custody through existing task admission controls.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.entity-smoke.task-plan.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/implementation/task-route.py
import importlib.util
from pathlib import Path
from types import SimpleNamespace

SUCCESSOR_STEPS = (("baseline", "database-proof", "permissions"), ("baseline", "verifier", "lifecycle"),
                   ("baseline", "database-proof", "collision"), ("initial-recovery", "administration", "observe-migration-state"),
                   ("acceptance", "verifier", "read"))
REQUALIFICATION_PREFIX = (*SUCCESSOR_STEPS[:-1], ("baseline", "verifier", "read"))


class AcceptanceFailure(Exception):
    def __init__(self, code, *, context=None, evidence_reference=None, diagnostics=None):
        super().__init__(code)
        self.code = code
        self.context = {} if context is None else context
        self.evidence_reference = evidence_reference
        self.diagnostics = {} if diagnostics is None else diagnostics


def require(value, code):
    if not value: raise AcceptanceFailure(code)


def supported(args):
    if getattr(args, "expected_predecessor", None) is not None:
        return (getattr(args, "proof_stage", "baseline"), args.workload, args.operation) in (*SUCCESSOR_STEPS, *REQUALIFICATION_PREFIX, ("rollback", "verifier", "read"))
    return (getattr(args, "proof_stage", "baseline"), args.workload, args.operation) == ("acceptance", "verifier", "read")


def restore_owner():
    spec = importlib.util.spec_from_file_location("entity_smoke_acceptance_restore", (Path(__file__).resolve().parents[2] / "recovery-and-replacement/restore/restore-route.py"))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def acceptance_owner():
    spec = importlib.util.spec_from_file_location("entity_smoke_successor_acceptance", (Path(__file__).resolve().parents[2] / "acceptance-evaluation/implementation/acceptance-route.py"))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def predecessor(context, args):
    owner = acceptance_owner()
    try: return owner.successor_parent(context, args)
    except Exception as failure:
        detail = owner.failure_details(failure)
        raise AcceptanceFailure(detail["condition"], context=detail.get("context")) from None


def prerequisites(route, context, args, provider):
    if context.get("delivery") is not None:
        parent = predecessor(context, args)
        if parent["applicability"].get("mode") != "requalify" or (args.proof_stage, args.workload, args.operation) != ("acceptance", "verifier", "read"):
            return successor_prerequisites(route, context, args, provider)
    require(supported(args) and args.expected_digest is not None, "acceptance-final-read-selection-invalid")
    owner = restore_owner()
    def observation(service, operation, **parameters):
        try: return provider(service, operation, **parameters)
        except route.C.RESOURCE.ResourceMissing: raise owner.C.RESOURCE.ResourceMissing() from None
        except route.C.InfrastructureFailure as failure:
            raise owner.C.InfrastructureFailure(failure.code, failure.evidence_reference) from None
    try:
        options = {"retained_source_evidence": context["retained_source_evidence"]} if context.get("retained_source_evidence") is not None else {}
        value = owner.source(args, observation, source_proof=False, require_terminal_jobs=False, **options)
        require(value["binding"] == context["binding"] and value["artifact"] == context["artifact"]
                and value["parameters"] == context["parameters"] and value["resources"] == context["resources"], "acceptance-current-binding-mismatch")
        completed = owner.completed_cleanup(value, args, observation)
        # Reuse only inside this observation phase; a new submission guard calls
        # this owner again with its own fresh provider observations.
        context["acceptance_source"] = value
        context["acceptance_cleanup"] = completed
    except owner.known() as failure:
        safe = {}
        if isinstance(failure, owner.TASK.BINDING.BindingFailure):
            safe = {"field": failure.field, "item": failure.item, "affected_workload": failure.workload}
        diagnostics = {}
        for evidence in (owner.TASK.RUNNER.EVIDENCE, owner.C.RESOURCE.EVIDENCE, owner.R.EVIDENCE):
            if isinstance(failure, evidence.EvidenceFailure):
                diagnostics = evidence.failure_report(failure); break
        reference = failure.evidence_reference if isinstance(failure, owner.C.InfrastructureFailure) else None
        raise AcceptanceFailure(failure.code, context=safe, evidence_reference=reference, diagnostics=diagnostics) from None
    request = route.STEPS.request(route, context, args)
    store = route.RUNNER.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    reservation = store.read(route.STEPS.key(args, context.get("delivery")), request)
    route.C.RESOURCE.require_other_tasks_terminal(provider, reservation=reservation)
    return {"required_after": completed["required_after"], "packets": {
        "credential-history-sha256": route.C.digest_file(value["cache"] / "credential-history.json"),
        "source-snapshot-sha256": route.C.digest_file(value["cache"] / "snapshot-receipt.json"),
        "restore-cleanup-sha256": route.C.digest_file(value["cache"] / "restore-cleanup-receipt.json"),
        "restore-reader-sha256": route.C.DEPLOY.fingerprint(completed["reader"]["step"]),
    }}


def successor_prerequisites(route, context, args, provider):
    """Fresh release checks use existing task admission, not initial setup replay."""
    selection = (getattr(args, "proof_stage", "baseline"), args.workload, args.operation)
    rollback = selection == ("rollback", "verifier", "read")
    require((selection in (*SUCCESSOR_STEPS, *REQUALIFICATION_PREFIX) or rollback) and args.expected_digest is not None,
            "acceptance-successor-selection-invalid")
    parent = predecessor(context, args)
    steps = REQUALIFICATION_PREFIX if parent["applicability"].get("mode") == "requalify" else SUCCESSOR_STEPS
    require(rollback or selection in steps, "acceptance-successor-selection-invalid")
    deployed = route.C.completed_deployment(provider, context["binding"], context["parameters"], context["delivery"], rollback=rollback)
    required_after = deployed["required_after"]
    packets = {"deployment": deployed["receipt"], "predecessor": parent}
    timestamp = route.RUNNER.EVIDENCE.timestamp
    for stage, workload, operation in (() if rollback else steps[:steps.index(selection)]):
        selected = SimpleNamespace(**{**vars(args), "proof_stage": stage, "workload": workload,
                                     "operation": operation, "phase": "operation"})
        checked = route.BINDING.inspect(provider, workload, context["parameters"], context["resources"], context.get("binding_snapshot"))
        selected_context = {**context, "checked": checked,
            "report": {"plan": {"preflight_label": route.C.delivery_preflight_label(context["delivery"], stage, workload, operation)}}}
        packet = route.STEPS.observe_packet(route, selected_context, selected, provider, historical=True)
        if packet is None: raise route.STEPS.PrerequisiteMissing(workload + "-" + operation)
        require(timestamp(packet["receipt"]["task"]["created_at"]) >= timestamp(required_after),
                "acceptance-successor-task-order-invalid")
        required_after = packet["receipt"]["task"]["stopped_at"]
        packets[workload + "-" + operation] = packet
    request = route.STEPS.request(route, context, args)
    store = route.RUNNER.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    reservation = store.read(route.STEPS.key(args, context["delivery"]), request)
    route.C.RESOURCE.require_other_tasks_terminal(provider, reservation=reservation)
    return {"required_after": required_after, "packets": packets}
