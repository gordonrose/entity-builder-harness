#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.replacement.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind one approved server replacement to actual original-record proof and its original reserved task without replay or an implied post-replacement data read.
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
from types import SimpleNamespace


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


TASK = module("entity_smoke_replacement_task", Path(__file__).with_name("task-route.py"))
C = TASK.C


class ReplacementFailure(Exception):
    def __init__(self, code, item=None):
        super().__init__(code)
        self.code, self.item = code, item


def require(value, code, item=None):
    if not value: raise ReplacementFailure(code, item)


def stage(args):
    value = getattr(args, "proof_stage", "baseline")
    require(value in {"baseline", "credential-recovery"}, "replacement-proof-stage-invalid")
    return value


def prefix(args): return "replacement" if stage(args) == "baseline" else "credential-replacement"


def graph(proof_stage="baseline"):
    return TASK.GRAPH.replacement(C.GATE, C.CONTRACT, proof_stage)


def baseline(args, provider):
    if stage(args) == "credential-recovery": return TASK.CREDENTIAL.replacement_context(TASK, args, provider)
    selected = SimpleNamespace(**{**vars(args), "workload": "verifier", "operation": "read", "phase": "operation"})
    context = TASK.prepare(selected, provider)
    require(context["prerequisites"] is not None, "replacement-baseline-prerequisite-required", context["report"]["plan"].get("pending_prerequisite"))
    packet = TASK.STEPS.observe_packet(TASK.dependencies(), context, selected, provider)
    require(packet is not None, "replacement-baseline-read-required")
    require(packet["receipt"]["result"]["record_digest"] == args.expected_digest, "replacement-original-digest-mismatch")
    require(TASK.RUNNER.EVIDENCE.timestamp(packet["receipt"]["task"]["created_at"]) >= TASK.RUNNER.EVIDENCE.timestamp(context["prerequisites"]["required_after"]), "replacement-baseline-order-invalid")
    C.RESOURCE.require_other_tasks_terminal(provider)
    return context, packet


def actor(provider, task):
    # Use the existing actual operator/role check, but simulate only the exact
    # StopTask resource, never RunTask or a widened set of task families.
    caller = provider("sts", "get-caller-identity")
    arn = caller.get("Arn") if isinstance(caller, dict) else None
    require(caller.get("Account") == C.ALIGN.ACCOUNT and isinstance(arn, str)
            and re.fullmatch(r"arn:aws:sts::" + C.ALIGN.ACCOUNT + r":assumed-role/[A-Za-z0-9+=,.@_-]+/[A-Za-z0-9+=,.@_-]+", arn) is not None, "replacement-operator-not-confirmed")
    name = arn.split("/")[1]
    role = provider("iam", "get-role", RoleName=name).get("Role")
    require(isinstance(role, dict) and role.get("RoleName") == name and isinstance(role.get("Arn"), str)
            and role["Arn"].startswith("arn:aws:iam::" + C.ALIGN.ACCOUNT + ":role/") and role["Arn"].endswith("/" + name), "replacement-operator-not-confirmed")
    result = provider("iam", "simulate-principal-policy", PolicySourceArn=role["Arn"], ActionNames=["ecs:StopTask"], ResourceArns=[task],
                      ContextEntries=[{"ContextKeyName": "ecs:cluster", "ContextKeyValues": ["arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":cluster/" + C.RESOURCE.CLUSTER], "ContextKeyType": "string"}])
    rows = result.get("EvaluationResults") if isinstance(result, dict) else None
    require(isinstance(rows, list) and len(rows) == 1 and result.get("IsTruncated") is False and isinstance(rows[0], dict)
            and rows[0].get("EvalActionName") == "ecs:StopTask" and rows[0].get("EvalResourceName") == task
            and rows[0].get("EvalDecision") == "allowed" and not rows[0].get("MissingContextValues"), "replacement-operator-policy-preflight-not-confirmed")
    return C.DEPLOY.fingerprint({"account": caller["Account"], "role": role["Arn"]})


class Provider(C.Provider):
    def __init__(self):
        super().__init__()
        self.capability, self.consumed, self.provider_condition, self.rejected_failure = None, False, None, None

    def enable_replacement(self, store, request, guard, *, phase="server-replacement"):
        require(self.capability is None, "replacement-capability-already-enabled")
        require(phase in {"server-replacement", "credential-replacement"}, "replacement-phase-not-supported")
        C.RESOURCE.validate_request(phase, request)
        self.capability = store, request, guard, phase

    def __call__(self, service_name, operation, **parameters):
        if (service_name, operation) in TASK.READS: return self._invoke(service_name, operation, parameters)
        try:
            require((service_name, operation) == ("ecs", "stop-task") and self.capability is not None and not self.consumed, "replacement-provider-operation-prohibited")
            store, request, guard, phase = self.capability
            reservation = store.read(phase, request)
            require(reservation is not None, "replacement-effect-reservation-required")
            expected = {"cluster": C.RESOURCE.CLUSTER, "task": request["original_task"], "reason": reservation["operation_id"]}
            require(C.RESOURCE.CONTROL.canonical(parameters) == C.RESOURCE.CONTROL.canonical(expected), "replacement-submission-does-not-match-plan")
            guard()
        except Exception as failure:
            code = failure.code if isinstance(failure, known_failures()) else "replacement-submission-preflight-not-confirmed"
            self.rejected_failure = failure if isinstance(failure, known_failures()) else None
            raise C.RESOURCE.SubmissionNotStarted(code) from None
        self.consumed, self.effect = True, "unknown-reconcile-only"
        try: return self._invoke(service_name, operation, parameters)
        except C.InfrastructureFailure as failure:
            self.provider_condition = failure.code
            raise


def known_failures():
    return (ReplacementFailure, TASK.TaskRouteFailure, TASK.BINDING.BindingFailure, TASK.STEPS.StepFailure, TASK.FEATURE.FeatureStepFailure, TASK.CREDENTIAL.CredentialFailure,
            TASK.RUNNER.CONTROL.TaskFailure, TASK.RUNNER.EVIDENCE.EvidenceFailure, TASK.RUNNER.PREFLIGHT.PreflightFailure,
            C.InfrastructureFailure, C.RESOURCE.ResourceFailure, C.RESOURCE.CONTROL.TaskFailure, C.RESOURCE.EVIDENCE.EvidenceFailure,
            C.ALIGN.AlignmentFailure, C.GATE.ContractFailure) + TASK.RECOVERY.failures()


def packet_path(cache, digest, proof_stage="baseline"):
    require(isinstance(digest, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", digest), "replacement-approved-plan-required")
    directory = "replacement-plans" if proof_stage == "baseline" else "credential-replacement-plans"
    return cache / directory / (digest.removeprefix("sha256:") + ".json")


def prepare(args, provider):
    proof_stage = stage(args)
    phase = "server-replacement" if proof_stage == "baseline" else "credential-replacement"
    context, read = baseline(args, provider)
    cache, binding = context["cache"], {**context["binding"], "record_digest": args.expected_digest}
    store = C.RESOURCE.ResourceStore(cache / "attempts")
    active_path = cache / (prefix(args) + "-plan.json")
    C.RESOURCE.CONTROL.no_symlinks(active_path)
    packet = C.read_json(active_path) if active_path.exists() else C.read_json(packet_path(cache, args.approved_plan, proof_stage)) if args.mode == "execute" else None
    if packet is not None:
        require(isinstance(packet, dict) and set(packet) == {"schema", "plan", "request", "plan_sha256"} and packet["schema"] == "deploy/entity-smoke-replacement-plan-packet/v1"
                and isinstance(packet["plan"], dict) and isinstance(packet["request"], dict) and packet["plan_sha256"] == C.DEPLOY.fingerprint(packet["plan"]), "replacement-original-plan-not-confirmed")
        C.RESOURCE.validate_request(phase, packet["request"])
        original = packet["request"]["original_task"]
    else:
        tasks = C.RESOURCE.running_service_tasks(provider)
        require(len(tasks) == 1, "replacement-original-server-not-confirmed")
        original = context.get("credential_original_task", tasks[0])
    require("credential_original_task" not in context or original == context["credential_original_task"], "replacement-credential-original-task-changed")
    definition = context["callees"]["server"]["definition"]
    request = {"binding": binding, "definition": definition, "original_task": original}
    C.RESOURCE.validate_request(phase, request)
    C.RESOURCE.service(provider, definition, 1)
    before = C.RESOURCE.task(provider, original, definition, binding["image_digest"])
    previous = store.read(phase, request)
    require(previous is not None or before.get("lastStatus") == "RUNNING" and C.RESOURCE.running_service_tasks(provider) == [original], "replacement-original-server-not-confirmed")
    declaration = graph(proof_stage)
    safe = {"schema": "deploy/entity-smoke-replacement-plan/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "binding": binding, "proof_stage": proof_stage,
            "request_sha256": C.DEPLOY.fingerprint(request), "baseline_read_sha256": C.DEPLOY.fingerprint(read), "prerequisites_sha256": C.DEPLOY.fingerprint(context["prerequisites"]),
            "controller_sha256": context["artifact"], "graph_sha256": C.DEPLOY.fingerprint(declaration), "operator_sha256": actor(provider, original),
            "configuration_sha256": C.DEPLOY.fingerprint({"parameters": context["parameters"], "resources": context["resources"], "server": context["callees"]["server"]}),
            "package_custody_reference": context["custody"]["receipt_reference"], "maximum_task_stops": 1, "database_mutation": False,
            "task_launch": False, "automatic_retry": False, "post_replacement_record_readback": False}
    digest = C.DEPLOY.fingerprint(safe)
    expected = {"schema": "deploy/entity-smoke-replacement-plan-packet/v1", "plan": safe, "request": request, "plan_sha256": digest}
    require(packet is None or packet == expected, "replacement-original-plan-binding-changed")
    packet = expected
    path = packet_path(cache, digest, proof_stage)
    if not C.RESOURCE.write_exclusive(path, packet): require(C.read_json(path) == packet, "replacement-plan-retention-conflict")
    require(args.mode != "execute" or args.approved_plan == digest, "replacement-approved-plan-mismatch")
    book = C.GateBook(context["artifact"], cache / (prefix(args) + "-realization"), contract=declaration,
                      artifact_bindings={row["id"]: context["artifact"] for row in declaration["artifacts"]})
    for identifier in book.known: book.component(identifier)
    book.gate("source"); book.gate("artifact"); book.gate("semantic-integration"); book.bind_plan(digest)
    book.gate("live-read"); book.gate("change-set"); evidence = book.validate("change-set", 1, True)
    return {"packet": packet, "context": context, "store": store, "book": book, "evidence": evidence, "active_path": active_path, "original_task_observation": before}


def run(args, provider):
    proof_stage = stage(args)
    phase = "server-replacement" if proof_stage == "baseline" else "credential-replacement"
    prepared = prepare(args, provider)
    packet, context, store, book = (prepared[key] for key in ("packet", "context", "store", "book"))
    if args.mode == "plan": return {"verdict": "planned", "plan": packet["plan"], "plan_sha256": packet["plan_sha256"], "effect": "not-started"}
    if not C.RESOURCE.write_exclusive(prepared["active_path"], packet): require(C.read_json(prepared["active_path"]) == packet, "replacement-active-plan-conflict")
    def guard():
        current = prepare(args, provider)
        require(current["packet"] == packet, "replacement-source-or-prerequisite-changed-before-submission")
        require(current["original_task_observation"].get("lastStatus") == "RUNNING", "replacement-original-no-longer-running-before-submission")
        book.validate("execution-preflight", 1, True)
    book.gate("execution-preflight"); book.validate("execution-preflight", 1, True)
    request = packet["request"]
    previous = store.read(phase, request)
    if previous is None: provider.enable_replacement(store, request, guard, phase=phase)
    else: provider.effect = "original-operation-reconcile-only"
    deadline = time.monotonic() + args.wait_seconds
    while True:
        result = C.RESOURCE.replace_runtime(provider, store, request["binding"], request["definition"], request["original_task"], credential_recovery=proof_stage == "credential-recovery")
        if result["status"] == "completed": break
        if time.monotonic() >= deadline: return {"verdict": "pending", "plan_sha256": packet["plan_sha256"], "effect": "original-replacement-not-terminal"}
        print(json.dumps({"schema": "deploy/entity-smoke-replacement-progress/v1", "state": "waiting-for-original-replacement"}), file=C.os.sys.stderr, flush=True)
        time.sleep(2)
    require(prepare(args, provider)["packet"] == packet, "replacement-source-or-prerequisite-changed-before-completion")
    book.gate("controlled-execution"); evidence = book.validate("controlled-execution", 1, True)
    target = context["cache"] / (prefix(args) + "-receipt.json")
    retained = {"schema": "deploy/entity-smoke-replacement-receipt/v1", "packet": packet, "result": result,
                "realization_evidence": str(evidence.relative_to(C.ROOT)), "realization_evidence_sha256": C.digest_file(evidence)}
    if not C.RESOURCE.write_exclusive(target, retained):
        previous = C.read_json(target)
        require(isinstance(previous, dict) and set(previous) == set(retained) and previous["schema"] == retained["schema"]
                and previous["packet"] == packet and previous["result"] == result, "replacement-receipt-conflict")
        reference = previous["realization_evidence"]
        retained_prefix = str((context["cache"] / (prefix(args) + "-realization")).relative_to(C.ROOT)) + "/controlled-execution-"
        require(isinstance(reference, str) and reference.startswith(retained_prefix) and re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(retained_prefix):])
                and C.digest_file(C.ROOT / reference) == previous["realization_evidence_sha256"], "replacement-retained-gate-not-confirmed")
    provider.effect = "original-server-replacement-observed"
    return {"verdict": "completed", "plan_sha256": packet["plan_sha256"], "receipt": str(target.relative_to(C.ROOT)),
            "post_replacement_record_readback": False, "effect": provider.effect}


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(ReplacementFailure("replacement-arguments-invalid"))
    parser.add_argument("--mode", choices=("plan", "execute"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--proof-label", required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--proof-stage", choices=("baseline", "credential-recovery"), default="baseline")
    parser.add_argument("--approved-plan")
    parser.add_argument("--wait-seconds", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) and re.fullmatch(r"[a-f0-9]{64}", args.expected_digest)
            and 0 <= args.wait_seconds <= 60, "replacement-arguments-invalid")
    require(args.mode == "plan" or isinstance(args.approved_plan, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", args.approved_plan), "replacement-approved-plan-required")
    return args


def main():
    provider, context = Provider(), {}
    try:
        args = parse()
        context = {"mode": args.mode, "proof_label_sha256": hashlib.sha256(args.proof_label.encode()).hexdigest()}
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        result = run(args, provider)
        print(json.dumps({"schema": "deploy/entity-smoke-replacement-report/v1", **result}, sort_keys=True))
        return 0 if result["verdict"] in {"planned", "completed"} else 2
    except Exception as failure:
        source_failure = provider.rejected_failure or failure
        if isinstance(source_failure, ReplacementFailure) and source_failure.item is not None: context["item"] = source_failure.item
        if isinstance(source_failure, TASK.STEPS.PrerequisiteMissing): context["item"] = source_failure.item
        recovery_item = TASK.RECOVERY.failure_item(source_failure)
        if recovery_item is not None: context["item"] = recovery_item
        if provider.provider_condition is not None: context["provider_condition"] = provider.provider_condition
        if isinstance(source_failure, TASK.BINDING.BindingFailure): context.update(affected_workload=source_failure.workload, field=source_failure.field, item=source_failure.item)
        diagnostics = TASK.RUNNER.EVIDENCE.failure_report(source_failure) if isinstance(source_failure, TASK.RUNNER.EVIDENCE.EvidenceFailure) else C.RESOURCE.EVIDENCE.failure_report(source_failure) if isinstance(source_failure, C.RESOURCE.EVIDENCE.EvidenceFailure) else {}
        reference = source_failure.evidence_reference if isinstance(source_failure, C.InfrastructureFailure) else None
        print(json.dumps({"schema": "deploy/entity-smoke-replacement-report/v1", "verdict": "blocked", "condition": failure.code if isinstance(failure, known_failures()) else "replacement-boundary-not-confirmed",
                          "context": context, "effect": provider.effect, **diagnostics,
                          **({"evidence_reference": reference} if reference is not None else {})}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
