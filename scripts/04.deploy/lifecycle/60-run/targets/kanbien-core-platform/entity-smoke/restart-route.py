#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.initial-restart.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Plan and execute one explicitly approved first-release feature restart after actual owned stop proof without SQL, replay or invented preservation evidence.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


TASK = module("entity_smoke_restart_task", Path(__file__).with_name("task-route.py"))
STATE = module("entity_smoke_restart_state", Path(__file__).with_name("recovery-state.py"))
C = TASK.C


class RestartFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(allowed, code):
    if not allowed: raise RestartFailure(code)


def known():
    return (RestartFailure, STATE.RecoveryStateFailure, STATE.STOP.RecoveryFailure, STATE.STOP.F.StopFailure, STATE.STOP.B.FailureBindingError,
            STATE.STOP.SUCCESSION.SuccessionFailure, STATE.STOP.RESTORE.RESOURCE.ResourceFailure, C.InfrastructureFailure, C.ALIGN.AlignmentFailure, C.RESOURCE.ResourceFailure, C.GATE.ContractFailure,
            TASK.TaskRouteFailure, TASK.BINDING.BindingFailure, TASK.STEPS.StepFailure, TASK.RUNNER.RunnerFailure,
            TASK.RUNNER.CONTROL.TaskFailure, TASK.RUNNER.EVIDENCE.EvidenceFailure, TASK.RUNNER.PREFLIGHT.PreflightFailure)


def graph():
    def rename(value):
        if isinstance(value, str): return value.replace("infrastructure", "initial-restart")
        if isinstance(value, list): return [rename(item) for item in value]
        if isinstance(value, dict): return {key: rename(item) for key, item in value.items()}
        return value
    value = rename(C.yaml.safe_load(C.CONTRACT.read_text()))
    value["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/restart-route.py"
    value["identities"][0]["permissions"] = ["inspect-selected-target", "set-only-own-service-count-one"]
    value["state_stores"][0]["semantics"] = ["initial-policy-under-custody-lock", "original-stop-and-pre-stop-record-read", "one-reserved-own-service-restart"]
    value["recovery_plans"][0].update(entry_condition="initial-stop-and-data-read-bound", cleanup="no-data-or-resource-deletion", rollback="observe-original-start-never-resubmit")
    value["change_shape"]["allowed_operation_classes"] = ["update"]
    value["change_shape"]["forbidden_operation_classes"] = ["create", "delete", "replace", "broaden-permission"]
    value["assumptions"] = [{"id": "restart-is-not-preservation-readback", "statement": "healthy-runtime-restart-requires-separate-original-record-and-applied-migration-history-observation", "required_proof": "declared", "actual_proof": "declared"}]
    C.GATE.validate_contract(value)
    return value


def packet_path(cache, digest):
    require(isinstance(digest, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", digest), "restart-approved-plan-required")
    return cache / "initial-restart-plans" / (digest.removeprefix("sha256:") + ".json")


def prepare(args, provider):
    custody = C.ALIGN.read_receipt(args.receipt.absolute())
    C.ALIGN.source_preflight(custody); C.local_checks()
    state = STATE.context(TASK, args, provider, custody)
    cache, scope = state["cache"], state["scope"]
    require(not any(row["workload"] != "server" for row in scope["active_tasks"].values()), "restart-active-owned-job-not-permitted")
    request = {"binding": {**scope["binding"], "record_digest": args.expected_digest}, "definition": state["server"]["definition"], "desired_count": 1, "original_tasks": []}
    store = C.RESOURCE.ResourceStore(cache / "attempts")
    previous = store.read("start-runtime", request)
    if previous is None:
        require(not scope["active_tasks"] and all(scope["service"][key] == 0 for key in ("desired_count", "running_count", "pending_count")), "restart-scope-not-stopped")
    actor = STATE.STOP.operator(provider, {"service": {"arn": scope["service"]["arn"]}, "task_stops": []})
    source, declaration = STATE.STOP.artifact(C), graph()
    safe = {"schema": "deploy/entity-smoke-initial-restart-plan/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "binding": request["binding"],
            "request_sha256": C.DEPLOY.fingerprint(request), "stop_sha256": C.DEPLOY.fingerprint(state["stop"]), "original_read_sha256": C.DEPLOY.fingerprint(state["read"]),
            "controller_sha256": source, "graph_sha256": C.DEPLOY.fingerprint(declaration), "policy_sha256": C.DEPLOY.fingerprint(state["policy"]), "operator_sha256": actor,
            "configuration_sha256": C.DEPLOY.fingerprint({"parameters": scope["parameters"], "resources": scope["resources"], "server": state["server"]}),
            "package_custody_reference": custody["receipt_reference"], "maximum_service_updates": 1, "desired_count": 1,
            "task_launch": False, "database_mutation": False, "permission_mutation": False, "resource_deletion": False, "automatic_retry": False,
            "independent_data_readback": False, "migration_history_readback": False}
    digest = C.DEPLOY.fingerprint(safe)
    packet = {"schema": "deploy/entity-smoke-initial-restart-plan-packet/v1", "plan": safe, "request": request, "plan_sha256": digest}
    active = cache / "initial-restart-plan.json"
    C.RESOURCE.CONTROL.no_symlinks(active)
    if active.exists(): require(C.read_json(active) == packet, "restart-original-plan-binding-changed")
    path = packet_path(cache, digest)
    if not C.RESOURCE.write_exclusive(path, packet): require(C.read_json(path) == packet, "restart-plan-retention-conflict")
    require(args.mode != "execute" or args.approved_plan == digest, "restart-approved-plan-mismatch")
    book = C.GateBook(source, cache / "initial-restart-realization", contract=declaration, artifact_bindings={row["id"]: source for row in declaration["artifacts"]})
    for name in book.known: book.component(name)
    book.gate("source"); book.gate("artifact"); book.gate("semantic-integration"); book.bind_plan(digest)
    book.gate("live-read"); book.gate("change-set"); evidence = book.validate("change-set", 1, True)
    return {"packet": packet, "state": state, "store": store, "book": book, "active": active, "evidence": evidence}


class Provider(C.Provider):
    def __init__(self):
        super().__init__()
        self.capability, self.consumed, self.rejected_failure, self.provider_condition = None, False, None, None

    def enable_restart(self, store, request, guard):
        require(self.capability is None, "restart-capability-already-enabled")
        C.RESOURCE.validate_request("start-runtime", request)
        self.capability = store, request, guard

    def __call__(self, service_name, operation, **parameters):
        if (service_name, operation) in TASK.READS | STATE.STOP.READS: return self._invoke(service_name, operation, parameters)
        try:
            require((service_name, operation) == ("ecs", "update-service") and self.capability is not None and not self.consumed, "restart-provider-operation-prohibited")
            store, request, guard = self.capability
            require(store.read("start-runtime", request) is not None, "restart-effect-reservation-required")
            expected = {"cluster": C.RESOURCE.CLUSTER, "service": C.RESOURCE.SERVICE, "desiredCount": 1}
            require(C.RESOURCE.CONTROL.canonical(parameters) == C.RESOURCE.CONTROL.canonical(expected), "restart-submission-does-not-match-plan")
            guard()
        except Exception as failure:
            self.rejected_failure = failure if isinstance(failure, known()) else None
            raise C.RESOURCE.SubmissionNotStarted(failure.code if isinstance(failure, known()) else "restart-submission-preflight-not-confirmed") from None
        self.consumed, self.effect = True, "unknown-reconcile-only"
        try: return self._invoke(service_name, operation, parameters)
        except C.InfrastructureFailure as failure:
            self.provider_condition = failure.code
            raise


def run(args, provider):
    prepared = prepare(args, provider)
    packet, state, store, book = (prepared[key] for key in ("packet", "state", "store", "book"))
    if args.mode == "plan": return {"verdict": "planned", "plan": packet["plan"], "plan_sha256": packet["plan_sha256"], "effect": "not-started"}
    with STATE.STOP.custody_lock(C):
        require(STATE.STOP.policy(C) == state["policy"], "restart-custody-changed")
        if not C.RESOURCE.write_exclusive(prepared["active"], packet): require(C.read_json(prepared["active"]) == packet, "restart-active-plan-conflict")
        target = state["cache"] / "initial-restart-receipt.json"
        C.RESOURCE.CONTROL.no_symlinks(target)
        request = packet["request"]
        previous = store.read("start-runtime", request)
        if target.exists():
            require(previous is not None, "restart-original-reservation-required")
            STATE.validate_restart(C, C.read_json(target), packet, previous, state["cache"])
            return {"verdict": "completed", "historical": True, "receipt": str(target.relative_to(C.ROOT)), "effect": "historical-operation-observed-no-new-start"}
        def guard():
            current = prepare(args, provider)
            require(current["packet"] == packet, "restart-source-or-prerequisite-changed-before-submission")
            scope = current["state"]["scope"]
            require(not scope["active_tasks"] and all(scope["service"][key] == 0 for key in ("desired_count", "running_count", "pending_count")), "restart-scope-not-stopped-before-submission")
            require(STATE.STOP.policy(C) == state["policy"], "restart-custody-changed")
            book.validate("execution-preflight", 1, True)
        book.gate("execution-preflight"); book.validate("execution-preflight", 1, True)
        if previous is None: provider.enable_restart(store, request, guard)
        else: provider.effect = "original-operation-reconcile-only"
        deadline = time.monotonic() + args.wait_seconds
        while True:
            result = C.RESOURCE.control_runtime_count(provider, store, request["binding"], request["definition"], [], start=True)
            if result["status"] == "completed": break
            if time.monotonic() >= deadline: return {"verdict": "pending", "effect": "original-start-not-terminal", "plan_sha256": packet["plan_sha256"]}
            time.sleep(2)
        require(prepare(args, provider)["packet"] == packet, "restart-source-or-prerequisite-changed-before-completion")
        running = C.RESOURCE.task(provider, result["facts"]["tasks"][0], request["definition"], request["binding"]["image_digest"])
        service = C.RESOURCE.service(provider, request["definition"], 1)
        require(running.get("lastStatus") == "RUNNING" and running.get("healthStatus") == "HEALTHY" and service.get("runningCount") == 1
                and service.get("pendingCount") == 0 and C.RESOURCE.running_service_tasks(provider) == [running["taskArn"]], "restart-qualified-runtime-not-confirmed")
        server = {"task": running["taskArn"], "created_at": running.get("createdAt"), "started_at": running.get("startedAt")}
        require(C.RESOURCE.timestamp(server["started_at"]) >= C.RESOURCE.timestamp(server["created_at"]) >= C.RESOURCE.timestamp(result["reservation"]["reserved_at"]), "restart-server-time-invalid")
        book.gate("controlled-execution"); evidence = book.validate("controlled-execution", 1, True)
        receipt = {"schema": "deploy/entity-smoke-initial-restart-receipt/v1", "packet": packet, "result": result, "server": server,
                   "realization_evidence": str(evidence.relative_to(C.ROOT)), "realization_evidence_sha256": C.digest_file(evidence),
                   "independent_data_readback": False, "migration_history_readback": False}
        STATE.validate_restart(C, receipt, packet, result["reservation"], state["cache"])
        if not C.RESOURCE.write_exclusive(target, receipt): require(C.read_json(target) == receipt, "restart-receipt-conflict")
        provider.effect = "initial-runtime-restart-observed"
        return {"verdict": "completed", "historical": False, "receipt": str(target.relative_to(C.ROOT)), "independent_data_readback": False, "migration_history_readback": False, "effect": provider.effect}


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(RestartFailure("restart-arguments-invalid"))
    parser.add_argument("--mode", choices=("plan", "execute"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--proof-label", required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--approved-plan")
    parser.add_argument("--wait-seconds", type=int, default=30)
    parser.add_argument("--validate-arguments", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(arguments)
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) and re.fullmatch(r"[a-f0-9]{64}", args.expected_digest) and 0 <= args.wait_seconds <= 60, "restart-arguments-invalid")
    require(args.mode == "plan" or isinstance(args.approved_plan, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", args.approved_plan), "restart-approved-plan-required")
    return args


def main():
    provider, context = Provider(), {}
    try:
        args = parse()
        context = {"mode": args.mode, "proof_label_sha256": hashlib.sha256(args.proof_label.encode()).hexdigest()}
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        result = run(args, provider)
        print(json.dumps({"schema": "deploy/entity-smoke-initial-restart-report/v1", **result}, sort_keys=True))
        return 0 if result["verdict"] in {"planned", "completed"} else 2
    except Exception as failure:
        source = provider.rejected_failure or failure
        if isinstance(source, TASK.BINDING.BindingFailure): context.update(field=source.field, item=source.item, affected_workload=source.workload)
        if isinstance(source, (STATE.STOP.RecoveryFailure, STATE.STOP.F.StopFailure, STATE.STOP.B.FailureBindingError)) and source.item is not None:
            context["item"] = source.item
        if isinstance(source, TASK.STEPS.PrerequisiteMissing): context["item"] = source.item
        if provider.provider_condition is not None: context["provider_condition"] = provider.provider_condition
        diagnostics = TASK.RUNNER.EVIDENCE.failure_report(source) if isinstance(source, TASK.RUNNER.EVIDENCE.EvidenceFailure) else {}
        reference = source.evidence_reference if isinstance(source, C.InfrastructureFailure) else None
        print(json.dumps({"schema": "deploy/entity-smoke-initial-restart-report/v1", "verdict": "blocked", "condition": source.code if isinstance(source, known()) else "restart-boundary-not-confirmed",
                          "effect": provider.effect, "context": context, **diagnostics,
                          **({"evidence_reference": reference} if reference is not None else {})}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
