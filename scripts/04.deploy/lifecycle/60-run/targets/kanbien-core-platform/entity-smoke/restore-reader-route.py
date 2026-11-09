#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.restore-reader.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind one separately probed restricted restored-record reader to the actual owned clone, original digest and durable task completion without source writes or replay.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace

SPEC = importlib.util.spec_from_file_location("entity_smoke_restore_reader_parent", Path(__file__).with_name("restore-route.py"))
D = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(D)
TASK, C = D.TASK, D.C


class ReaderFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(value, code):
    if not value: raise ReaderFailure(code)


def known(): return (ReaderFailure,) + D.known()


class Provider(C.Provider):
    def __init__(self):
        super().__init__()
        self.delegate = None

    def enable_task(self, request, store, key, guard):
        require(self.delegate is None, "restore-reader-capability-already-enabled")
        self.delegate = TASK.Provider()
        self.delegate._invoke = lambda service, operation, parameters: self._invoke(service, operation, parameters)
        def checked_guard():
            try: guard()
            except Exception as failure:
                # Preserve new parent/reader-owned finite reasons through the
                # existing task provider's typed before-I/O boundary.
                if isinstance(failure, (ReaderFailure, D.RestoreFailure, D.R.ResourceFailure, D.S.SnapshotFailure, TASK.HISTORY.HistoryFailure)):
                    raise TASK.TaskRouteFailure(failure.code) from None
                raise
        self.delegate.enable_task(request, store, key, checked_guard)

    def __call__(self, service, operation, **parameters):
        if (service, operation) in D.S.READS: return self._invoke(service, operation, parameters)
        require((service, operation) == ("ecs", "run-task") and self.delegate is not None, "restore-reader-provider-operation-prohibited")
        try: return self.delegate(service, operation, **parameters)
        finally: self.effect = self.delegate.effect


def prepare(args, provider, *, source_proof=True):
    value = D.source(args, provider, source_proof=source_proof, require_terminal_jobs=False)
    deployed = D.deployment(value, args, provider)
    child = D.reader_context(value, deployed)
    inspected = D.BINDING.inspect(C, TASK.BINDING, D.RESTORE, provider, value["restore_binding"], value["restore_parameters"], deployed["result"]["facts"], child["checked"]["subnets"])
    require(inspected["binding"] == child["binding"] and all(inspected["checked"][key] == child["checked"][key] for key in child["checked"]), "restore-reader-child-binding-mismatch")
    child["checked"] = inspected["checked"]
    expected = TASK.BINDING.expected_task("restore-reader", inspected["inputs"], deployed["result"]["facts"]["resources"], inspected["view"], prefix="RestoreReader")
    operator = TASK.operator(provider, child["checked"]["definition"], [expected["executionRoleArn"], expected["taskRoleArn"]])
    request = TASK.STEPS.request(TASK.dependencies(), child, args)
    store = TASK.RUNNER.CONTROL.AttemptStore(child["cache"] / "task-attempts")
    previous = store.read(TASK.STEPS.key(args), request)
    C.RESOURCE.require_other_tasks_terminal(provider, reservation=previous)
    declaration = TASK.GRAPH.contract("restore-reader", C.GATE)
    safe = {"schema": "deploy/entity-smoke-restore-reader-plan/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "workload": "restore-reader", "operation": "restore-read", "phase": args.phase,
            "proof_stage": "isolated-restore", "binding": child["binding"], "expected_record_digest": args.expected_digest, "preflight_label": child["report"]["plan"]["preflight_label"],
            "controller_sha256": child["artifact"], "graph_sha256": C.DEPLOY.fingerprint(declaration), "operator_sha256": operator, "request_sha256": C.DEPLOY.fingerprint(request),
            "task_binding_sha256": C.DEPLOY.fingerprint(child["checked"]), "parent_deployment_sha256": C.digest_file(child["cache"] / "restore-deploy-receipt.json"),
            "history_sha256": C.digest_file(child["cache"] / "credential-history.json"), "snapshot_sha256": C.digest_file(child["cache"] / "snapshot-receipt.json"),
            "package_custody_reference": child["custody"]["receipt_reference"], "task_count": 1, "source_mutation": False, "scope_acceptance": False, "automatic_retry": False}
    digest = C.DEPLOY.fingerprint(safe)
    path = child["cache"] / "restore-reader-plans" / (digest.removeprefix("sha256:") + ".json")
    if not C.RESOURCE.write_exclusive(path, safe): require(C.read_json(path) == safe, "restore-reader-plan-retention-conflict")
    book = C.GateBook(child["artifact"], child["cache"] / "task-realization", contract=declaration,
                      artifact_bindings={row["id"]: child["artifact"] if row["id"] == TASK.GRAPH.CONTROLLER_SOURCE else child["binding"]["image_digest"] for row in declaration["artifacts"]})
    for identifier in book.known: book.component(identifier)
    book.bind_plan(digest)
    for gate in C.GATE.GATE_ORDER[:5]: book.gate(gate)
    evidence = book.validate("change-set", 1)
    child.update(report={"plan": safe, "plan_sha256": digest}, book=book, store=store, request=request)
    return child, {"verdict": "planned", "plan": safe, "plan_sha256": digest, "realization_evidence": str(evidence.relative_to(C.ROOT)), "effect": "not-started"}


def run(args, provider):
    value, report = prepare(args, provider)
    if args.mode == "plan": return report
    require(args.approved_plan == report["plan_sha256"], "restore-reader-approved-plan-mismatch")
    deps, runner, steps, book = TASK.dependencies(), TASK.RUNNER, TASK.STEPS, value["book"]
    request, store, key = value["request"], value["store"], steps.key(args)
    previous = store.read(key, request)
    step_path = steps.path(value, args)
    completion_path = TASK.COMPLETION.path(step_path)
    runner.CONTROL.no_symlinks(completion_path)
    if completion_path.exists():
        packet = steps.observe_packet(deps, value, args, provider, historical=True)
        require(packet is not None and packet["plan_sha256"] == report["plan_sha256"], "restore-reader-original-plan-required")
        captured = TASK.COMPLETION.read(deps, value, args, step_path)
        provider.effect = "historical-restore-reader-completion-only"
        return {"verdict": "completed", "plan_sha256": packet["plan_sha256"], "receipt": str(step_path.relative_to(C.ROOT)), "realization_evidence": captured["realization_evidence"], "historical": True, "effect": provider.effect}
    preflight = None
    if args.phase == "operation":
        if previous is None:
            prior_args = SimpleNamespace(**{**vars(args), "phase": "preflight"})
            prior = steps.observe_packet(deps, value, prior_args, provider, historical=True)
            require(prior is not None, "restore-reader-preflight-required")
            preflight = {"reservation": prior["reservation"], "receipt": prior["receipt"], "label": report["plan"]["preflight_label"]}
            runner.PREFLIGHT.require_receipt(request, prior["reservation"], prior["receipt"], expected_preflight_label=preflight["label"], current_time=datetime.now(timezone.utc).isoformat(), required_after=value["required_after"])
        else: runner.PREFLIGHT.read_admission(value["cache"] / "task-receipts", previous)
        book.gate("execution-preflight"); book.validate("execution-preflight", 1)
    else: runner.PREFLIGHT.validate_launch(request)
    def guard():
        require(C.source_digest() == value["artifact"] and prepare(args, provider, source_proof=False)[1]["plan_sha256"] == report["plan_sha256"], "restore-reader-bindings-changed-before-submission")
        book.validate("change-set" if args.phase == "preflight" else "execution-preflight", 1)
        require(C.source_digest() == value["artifact"], "restore-reader-source-changed-before-submission")
    if previous is None: provider.enable_task(request, store, key, guard)
    else: provider.effect = "original-restore-reader-reconcile-only"
    completed = runner.run_owned_task(provider, store, key, request, value["cache"] / "task-receipts", required_after=value["required_after"], preflight=preflight)
    reservation = store.read(key, request)
    step_path = steps.retain(deps, value, args, reservation, completed["receipt"])
    steps.observe_packet(deps, value, args, provider, completion_required=False)
    if args.phase == "preflight": book.gate("execution-preflight")
    book.gate("controlled-execution"); evidence = book.validate("controlled-execution", 1)
    TASK.COMPLETION.retain(deps, value, args, step_path, evidence)
    provider.effect = "original-restore-reader-completion-observed"
    return {"verdict": "completed", "plan_sha256": report["plan_sha256"], "receipt": str(step_path.relative_to(C.ROOT)), "realization_evidence": str(evidence.relative_to(C.ROOT)), "historical": False, "effect": provider.effect}


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(ReaderFailure("restore-reader-arguments-invalid"))
    parser.add_argument("--mode", choices=("plan", "execute"), required=True)
    parser.add_argument("--phase", choices=("preflight", "operation"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--proof-label", required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--approved-plan")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) and re.fullmatch(r"[a-f0-9]{64}", args.expected_digest), "restore-reader-arguments-invalid")
    require(args.mode == "plan" and args.approved_plan is None or args.mode == "execute" and isinstance(args.approved_plan, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", args.approved_plan), "restore-reader-approved-plan-required")
    args.workload, args.operation, args.proof_stage = "restore-reader", "restore-read", "isolated-restore"
    return args


def main():
    provider, safe = Provider(), {}
    try:
        args = parse()
        safe = {"mode": args.mode, "phase": args.phase, "workload": "restore-reader", "proof_label_sha256": hashlib.sha256(args.proof_label.encode()).hexdigest()}
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        print(json.dumps({"schema": "deploy/entity-smoke-restore-reader-report/v1", **run(args, provider)}, sort_keys=True)); return 0
    except Exception as failure:
        condition = failure.code if isinstance(failure, known()) else "restore-reader-boundary-not-confirmed"
        if isinstance(failure, TASK.BINDING.BindingFailure): safe.update(field=failure.field, item=failure.item, affected_workload=failure.workload)
        if isinstance(failure, TASK.RUNNER.CONTROL.SubmissionNotStarted) and failure.field is not None:
            safe.update(field=failure.field, item=failure.item)
            if failure.workload is not None: safe["affected_workload"] = failure.workload
        item = TASK.RECOVERY.failure_item(failure)
        if item is not None: safe["item"] = item
        diagnostics = TASK.RUNNER.EVIDENCE.failure_report(failure) if isinstance(failure, TASK.RUNNER.EVIDENCE.EvidenceFailure) else {}
        evidence = failure.evidence_reference if isinstance(failure, C.InfrastructureFailure) else None
        print(json.dumps({"schema": "deploy/entity-smoke-restore-reader-report/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "verdict": "blocked", "condition": condition, "context": safe, "effect": provider.effect,
                          **diagnostics, **({"evidence_reference": evidence} if evidence is not None else {})}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
