#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.failure-stop.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-11"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Plan and execute only first-release owned-workload stop under fresh custody, exact approval and normal control-plane gates without SQL or replay.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import time


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
C = module("entity_smoke_failure_common", DIRECTORY / "script.py")
B = module("entity_smoke_failure_binding", DIRECTORY / "failure-binding.py")
F = module("entity_smoke_failure_control", DIRECTORY / "failure-control.py")
RESTORE = module("entity_smoke_failure_restore", DIRECTORY / "restore-control.py")
SUCCESSION = module("entity_smoke_failure_succession", C.ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py")
READS = C.READS | {("ecs", "describe-task-definition"), ("ecs", "list-services")}


class RecoveryFailure(Exception):
    def __init__(self, code, item=None):
        super().__init__(code)
        self.code, self.item = code, item


def require(value, code, item=None):
    if not value: raise RecoveryFailure(code, item)


def policy(common=None):
    owner = C if common is None else common
    declaration = owner.ROOT / owner.ALIGN.SCOPE
    selected = SUCCESSION.recovery_policy(declaration.parent.parent / "30-release-evidence", declaration)
    require(selected.get("target") == C.RESOURCE.CLUSTER and selected.get("scope") == "entity-smoke"
            and selected.get("policy") == "stop-own-scope-workloads-preserve-data" and selected.get("accepted_release_id") == "none", "failure-initial-policy-not-applicable")
    return selected


@contextmanager
def custody_lock(common=None):
    owner = C if common is None else common
    root = (owner.ROOT / owner.ALIGN.SCOPE).parent.parent / "30-release-evidence"
    target = root / ".release-succession.lock"
    C.RESOURCE.CONTROL.no_symlinks(target)
    require(root.is_dir(), "failure-custody-directory-unavailable")
    descriptor = os.open(target, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try: fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise RecoveryFailure("failure-custody-busy") from None
        policy(owner)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def artifact_basis(common=None):
    owner = C if common is None else common
    paths = [Path(SUCCESSION.__file__), owner.ROOT / owner.ALIGN.SCOPE,
             (owner.ROOT / owner.ALIGN.SCOPE).parent.parent.parent / "scope-index.yml",
             owner.ROOT / "scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.py"]
    return {"controller": owner.source_digest(), "custody_sources": {str(path.relative_to(owner.ROOT)): owner.digest_file(path) for path in paths}}


def artifact(common=None):
    owner = C if common is None else common
    return owner.DEPLOY.fingerprint(artifact_basis(owner))


def graph():
    source = C.yaml.safe_load(C.CONTRACT.read_text())
    def rename(value):
        if isinstance(value, str): return value.replace("infrastructure", "failure-stop")
        if isinstance(value, list): return [rename(item) for item in value]
        if isinstance(value, dict): return {key: rename(item) for key, item in value.items()}
        return value
    result = rename(source)
    result["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/failure-route.py"
    result["artifacts"][0]["assertions"] = ["committed-source-and-qualified-candidate", "actual-failure-control-and-custody-fixtures"]
    result["identities"][0]["permissions"] = ["inspect-selected-target", "set-only-own-service-count-zero", "stop-only-exact-owned-tasks"]
    result["state_stores"][0]["semantics"] = ["exact-tagged-stack-and-creation-lineage", "terminal-target-writer", "bounded-owned-task-set", "other-service-configurations-preserved"]
    result["recovery_plans"][0].update(entry_condition="first-release-policy-selected-under-custody-lock", cleanup="no-resource-or-data-deletion", rollback="stop-only-own-workloads-no-task-launch-or-database-reversal")
    result["change_shape"]["allowed_operation_classes"] = ["update"]
    result["change_shape"]["forbidden_operation_classes"] = ["create", "delete", "replace", "broaden-permission"]
    result["assumptions"] = [{"id": "stop-is-not-data-readback", "statement": "control-plane-stop-does-not-claim-healthy-application-or-independent-data-and-history-readback", "required_proof": "declared", "actual_proof": "declared"}]
    C.GATE.validate_contract(result)
    return result


def operator(provider, selected):
    caller = provider("sts", "get-caller-identity")
    arn = caller.get("Arn") if isinstance(caller, dict) else None
    require(caller.get("Account") == C.ALIGN.ACCOUNT and isinstance(arn, str)
            and re.fullmatch(r"arn:aws:sts::" + C.ALIGN.ACCOUNT + r":assumed-role/[A-Za-z0-9+=,.@_-]+/[A-Za-z0-9+=,.@_-]+", arn) is not None, "failure-operator-not-confirmed")
    name = arn.split("/")[1]
    role = provider("iam", "get-role", RoleName=name).get("Role")
    require(isinstance(role, dict) and role.get("RoleName") == name and isinstance(role.get("Arn"), str)
            and role["Arn"].startswith("arn:aws:iam::" + C.ALIGN.ACCOUNT + ":role/") and role["Arn"].endswith("/" + name), "failure-operator-not-confirmed")
    operations = [("ecs:StopTask", sorted(selected["task_stops"]))]
    if selected["service"] is not None: operations.append(("ecs:UpdateService", [selected["service"]["arn"]]))
    for action, resources in operations:
        if not resources: continue
        require(C.operator_resources_allowed(provider, role["Arn"], action, resources, context=[
            {"ContextKeyName": "ecs:cluster", "ContextKeyValues": ["arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":cluster/" + C.RESOURCE.CLUSTER], "ContextKeyType": "string"}]),
            "failure-operator-policy-preflight-not-confirmed", "service" if action == "ecs:UpdateService" else "tasks")
    return C.DEPLOY.fingerprint({"account": caller["Account"], "role": role["Arn"]})


class Provider(C.Provider):
    def __init__(self):
        super().__init__()
        self.stop_capability, self.consumed = None, set()

    def enable_stop(self, root, store, guard):
        require(self.stop_capability is None, "failure-capability-already-enabled")
        self.stop_capability = root, store, guard

    def __call__(self, service_name, operation, **parameters):
        if (service_name, operation) in READS: return self._invoke(service_name, operation, parameters)
        try:
            require(service_name == "ecs" and operation in {"update-service", "stop-task"} and self.stop_capability is not None, "failure-provider-operation-prohibited")
            root, store, guard = self.stop_capability
            selected = root["request"]["packet"]["intent"]
            if operation == "update-service":
                require(selected["service"] is not None, "failure-service-not-planned")
                key = "service"
                payload = {"cluster": C.RESOURCE.CLUSTER, "service": selected["service"]["arn"], "desiredCount": 0}
            else:
                target = parameters.get("task")
                require(isinstance(target, str) and target in selected["task_stops"], "failure-task-not-planned")
                key = F.task_key(target)
                payload = {"cluster": C.RESOURCE.CLUSTER, "task": target}
            request = {"root_sha256": C.DEPLOY.fingerprint(root), "operation": operation, "payload": payload}
            reserved = store.read(key, request)
            require(reserved is not None and key not in self.consumed, "failure-effect-reservation-required", key)
            expected = {**payload, **({"reason": reserved["operation_id"]} if operation == "stop-task" else {})}
            require(C.RESOURCE.CONTROL.canonical(parameters) == C.RESOURCE.CONTROL.canonical(expected), "failure-submission-does-not-match-plan", key)
            context = guard()
            self.consumed.add(key)
            if operation == "update-service" and (context["service"] is None or context["service"]["desired_count"] == 0): return {}
            if operation == "stop-task" and parameters["task"] not in context["active_tasks"]: return {}
        except Exception as failure:
            known = (RecoveryFailure, F.StopFailure, B.FailureBindingError, C.InfrastructureFailure, C.RESOURCE.ResourceFailure,
                     C.ALIGN.AlignmentFailure, C.GATE.ContractFailure, RESTORE.RESOURCE.ResourceFailure, SUCCESSION.SuccessionFailure)
            raise F.SubmissionNotStarted(failure.code if isinstance(failure, known) else "failure-submission-preflight-not-confirmed",
                                         failure.item if isinstance(failure, (RecoveryFailure, F.StopFailure, B.FailureBindingError)) else None) from None
        self.effect = "unknown-reconcile-only"
        return self._invoke(service_name, operation, parameters)


def packet_path(cache, digest):
    require(isinstance(digest, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", digest) is not None, "failure-approved-plan-required")
    return cache / "failure-plans" / (digest.removeprefix("sha256:") + ".json")


def validate_packet(value):
    require(isinstance(value, dict) and set(value) == {"schema", "plan", "intent", "plan_sha256"} and value["schema"] == "deploy/entity-smoke-failure-plan-packet/v1"
            and isinstance(value["plan"], dict) and isinstance(value["intent"], dict) and value["plan_sha256"] == C.DEPLOY.fingerprint(value["plan"])
            and value["plan"].get("intent_sha256") == C.DEPLOY.fingerprint(value["intent"]), "failure-original-plan-not-confirmed")
    return value


def prepare(args, provider):
    receipt = C.ALIGN.read_receipt(args.receipt.absolute())
    C.ALIGN.source_preflight(receipt); C.local_checks()
    selected_policy = policy()
    source, declaration = artifact(), graph()
    cache = C.ROOT / ".cache/entity-smoke-live" / args.proof_label
    C.filesystem_preflight(cache)
    store = F.StopStore(C, cache / "failure-attempts")
    root = store.read("root")
    if root is not None:
        require(set(root["request"]) == {"packet"}, "failure-original-root-not-confirmed")
        packet = validate_packet(root["request"]["packet"])
    elif args.mode == "execute": packet = validate_packet(C.read_json(packet_path(cache, args.approved_plan)))
    else: packet = None
    context = B.inspect(C, RESTORE, provider, receipt, args.proof_label, cache)
    selected = F.intent(C, context) if packet is None else packet["intent"]
    F.validate_intent(C, selected, B.MAX_TASKS)
    F.verify_current(C, selected, context)
    actor = operator(provider, selected)
    safe = {"schema": "deploy/entity-smoke-failure-plan/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "account": C.ALIGN.ACCOUNT, "region": C.ALIGN.REGION,
            "purpose": "first-release-stop-preserve-control", "binding": context["binding"], "intent_sha256": C.DEPLOY.fingerprint(selected),
            "controller_sha256": source, "graph_sha256": C.DEPLOY.fingerprint(declaration), "policy_sha256": C.DEPLOY.fingerprint(selected_policy), "operator_sha256": actor,
            "package_custody_reference": receipt["receipt_reference"], "maximum_service_updates": int(selected["service"] is not None), "maximum_task_stops": len(selected["task_stops"]),
            "application_health_prerequisite": False, "database_mutation": False, "permission_mutation": False, "task_launch": False, "resource_deletion": False,
            "independent_data_readback": False, "migration_history_readback": False, "automatic_retry": False}
    digest = C.DEPLOY.fingerprint(safe)
    if packet is not None: require(packet["plan"] == safe and packet["plan_sha256"] == digest, "failure-original-plan-binding-changed")
    else:
        packet = {"schema": "deploy/entity-smoke-failure-plan-packet/v1", "plan": safe, "intent": selected, "plan_sha256": digest}
        path = packet_path(cache, digest)
        if not C.RESOURCE.write_exclusive(path, packet): require(C.read_json(path) == packet, "failure-plan-retention-conflict")
    require(args.mode != "execute" or args.approved_plan == digest, "failure-approved-plan-mismatch")
    bindings = {item["id"]: source for item in declaration["artifacts"]}
    book = C.GateBook(source, cache / "failure-realization", contract=declaration, artifact_bindings=bindings)
    book.gate("source"); book.gate("artifact"); book.gate("semantic-integration")
    for name in book.known: book.component(name)
    book.bind_plan(digest); book.gate("live-read"); book.gate("change-set")
    count = safe["maximum_service_updates"] + safe["maximum_task_stops"]
    evidence = book.validate("change-set", count, True)
    return {"packet": packet, "context": context, "cache": cache, "store": store, "root": root, "book": book, "count": count,
            "receipt": receipt, "source": source, "policy": selected_policy, "evidence": evidence}


def run(args, provider):
    prepared = prepare(args, provider)
    packet, store, book = prepared["packet"], prepared["store"], prepared["book"]
    if args.mode == "plan": return {"verdict": "planned", "plan": packet["plan"], "plan_sha256": packet["plan_sha256"], "effect": "not-started",
                                    "realization_evidence": str(prepared["evidence"].relative_to(C.ROOT))}
    with custody_lock():
        def observe(): return B.inspect(C, RESTORE, provider, prepared["receipt"], args.proof_label, prepared["cache"])
        def guard():
            require(artifact() == prepared["source"] and C.DEPLOY.fingerprint(graph()) == packet["plan"]["graph_sha256"] and policy() == prepared["policy"], "failure-source-or-custody-changed-before-submission")
            C.ALIGN.source_preflight(prepared["receipt"])
            current = observe()
            F.verify_current(C, packet["intent"], current)
            require(operator(provider, packet["intent"]) == packet["plan"]["operator_sha256"], "failure-operator-changed-before-submission")
            require(artifact() == prepared["source"] and policy() == prepared["policy"], "failure-source-or-custody-changed-before-submission")
            book.validate("execution-preflight", prepared["count"], True)
            return current
        current = observe(); F.verify_current(C, packet["intent"], current)
        require(policy() == prepared["policy"] and artifact() == prepared["source"], "failure-source-or-custody-changed-before-submission")
        book.gate("execution-preflight"); book.validate("execution-preflight", prepared["count"], True)
        root, fresh = store.reserve("root", {"packet": packet})
        if not fresh: provider.effect = "original-operation-reconcile-only"
        retained_path = prepared["cache"] / "failure-receipts/stopped.json"
        C.RESOURCE.CONTROL.no_symlinks(retained_path)
        if retained_path.exists():
            F.validate_receipt(C, C.read_json(retained_path), root, prepared["cache"])
            return {"verdict": "completed", "historical": True, "current_scope_stopped": not current["active_tasks"] and (current["service"] is None or all(current["service"][key] == 0 for key in ("desired_count", "running_count", "pending_count"))),
                    "receipt": str(retained_path.relative_to(C.ROOT)), "plan_sha256": packet["plan_sha256"], "effect": "historical-operation-observed-no-new-stop"}
        provider.enable_stop(root, store, guard)
        deadline = time.monotonic() + args.wait_seconds
        while True:
            result = F.progress(C, store, root, current, provider, observe)
            if result["status"] == "completed": break
            if time.monotonic() >= deadline: return {"verdict": "pending", "plan_sha256": packet["plan_sha256"], "effect": "original-stop-not-terminal"}
            print(json.dumps({"schema": "deploy/entity-smoke-failure-progress/v1", "state": "waiting-for-original-stop"}), file=os.sys.stderr, flush=True)
            time.sleep(2); current = observe()
        book.gate("controlled-execution"); evidence = book.validate("controlled-execution", prepared["count"], True)
        retained = {"schema": "deploy/entity-smoke-failure-stop-receipt/v1", "plan_sha256": packet["plan_sha256"], "root": root,
                    "realization_evidence": str(evidence.relative_to(C.ROOT)), "realization_evidence_sha256": C.digest_file(evidence), "facts": result["facts"]}
        F.validate_receipt(C, retained, root, prepared["cache"])
        if not C.RESOURCE.write_exclusive(retained_path, retained): require(C.read_json(retained_path) == retained, "failure-receipt-conflict")
        provider.effect = "owned-workloads-stopped-observed"
        return {"verdict": "completed", "historical": False, "plan_sha256": packet["plan_sha256"], "receipt": str(retained_path.relative_to(C.ROOT)),
                "realization_evidence": str(evidence.relative_to(C.ROOT)), "independent_data_readback": False, "migration_history_readback": False, "effect": provider.effect}


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(RecoveryFailure("failure-arguments-invalid"))
    parser.add_argument("--mode", choices=("plan", "execute"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--proof-label", required=True)
    parser.add_argument("--approved-plan")
    parser.add_argument("--wait-seconds", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) is not None and 0 <= args.wait_seconds <= 60, "failure-arguments-invalid")
    require(args.mode == "plan" or isinstance(args.approved_plan, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", args.approved_plan) is not None, "failure-approved-plan-required")
    return args


def main():
    provider, context = Provider(), {}
    try:
        args = parse()
        context = {"mode": args.mode, "proof_label_sha256": hashlib.sha256(args.proof_label.encode()).hexdigest()}
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        result = run(args, provider)
        print(json.dumps({"schema": "deploy/entity-smoke-failure-report/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", **result}, sort_keys=True))
        return 0 if result["verdict"] in {"planned", "completed"} else 2
    except Exception as failure:
        known = (RecoveryFailure, F.StopFailure, B.FailureBindingError, C.InfrastructureFailure, C.RESOURCE.ResourceFailure, C.RESOURCE.CONTROL.TaskFailure,
                 C.ALIGN.AlignmentFailure, C.GATE.ContractFailure, RESTORE.RESOURCE.ResourceFailure, SUCCESSION.SuccessionFailure)
        if isinstance(failure, (RecoveryFailure, F.StopFailure, B.FailureBindingError)) and failure.item is not None: context["item"] = failure.item
        if isinstance(failure, F.StopFailure) and failure.provider_condition is not None: context["provider_condition"] = failure.provider_condition
        print(json.dumps({"schema": "deploy/entity-smoke-failure-report/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "verdict": "blocked", "condition": failure.code if isinstance(failure, known) else "failure-boundary-not-confirmed",
                          "effect": provider.effect, "context": context}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
