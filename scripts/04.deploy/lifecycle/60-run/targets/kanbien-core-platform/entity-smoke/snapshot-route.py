#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.snapshot.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Plan or explicitly reserve one original-record-bound source snapshot after completed credential proof without task replay, database deletion or implied restore acceptance.
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

SPEC = importlib.util.spec_from_file_location("entity_smoke_snapshot_task", Path(__file__).with_name("task-route.py"))
TASK = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(TASK)
C = TASK.C
READS = TASK.READS | {("rds", "describe-db-snapshots"), ("rds", "list-tags-for-resource")}


class SnapshotFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(value, code):
    if not value: raise SnapshotFailure(code)


def known():
    return (SnapshotFailure, TASK.HISTORY.HistoryFailure, TASK.TaskRouteFailure, TASK.BINDING.BindingFailure, TASK.STEPS.StepFailure,
            TASK.RUNNER.CONTROL.TaskFailure, TASK.RUNNER.EVIDENCE.EvidenceFailure, TASK.RUNNER.RunnerFailure, TASK.RUNNER.PREFLIGHT.PreflightFailure,
            C.InfrastructureFailure, C.RESOURCE.ResourceFailure, C.RESOURCE.CONTROL.TaskFailure, C.ALIGN.AlignmentFailure, C.GATE.ContractFailure)


def graph():
    def rename(value):
        if isinstance(value, str): return value.replace("infrastructure", "snapshot")
        if isinstance(value, list): return [rename(item) for item in value]
        if isinstance(value, dict): return {key: rename(item) for key, item in value.items()}
        return value
    value = rename(C.yaml.safe_load(C.CONTRACT.read_text()))
    value["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/snapshot-route.py"
    value["identities"][0]["permissions"] = ["inspect-qualified-source-database", "create-one-labelled-source-snapshot"]
    value["state_stores"][0]["semantics"] = ["completed-credential-history-custody", "original-record-id-and-facts-digest", "snapshot-after-proof-completion", "one-reserved-labelled-snapshot"]
    value["recovery_plans"][0].update(entry_condition="original-snapshot-not-terminal", cleanup="no-source-or-snapshot-deletion", rollback="observe-original-snapshot-never-resubmit")
    value["change_shape"]["allowed_operation_classes"] = ["create"]
    value["change_shape"]["forbidden_operation_classes"] = ["update", "delete", "replace", "broaden-permission"]
    value["assumptions"] = [{"id": "snapshot-is-not-restore-proof", "statement": "snapshot-completion-needs-separate-isolated-restored-original-record-read-and-owned-cleanup-before-acceptance", "required_proof": "declared", "actual_proof": "declared"}]
    C.GATE.validate_contract(value)
    return value


def actor(provider, snapshot):
    caller = provider("sts", "get-caller-identity")
    arn = caller.get("Arn") if isinstance(caller, dict) else None
    require(caller.get("Account") == C.ALIGN.ACCOUNT and isinstance(arn, str) and re.fullmatch(r"arn:aws:sts::" + C.ALIGN.ACCOUNT + r":assumed-role/[A-Za-z0-9+=,.@_-]+/[A-Za-z0-9+=,.@_-]+", arn), "snapshot-operator-not-confirmed")
    role_name = arn.split("/")[1]
    role = provider("iam", "get-role", RoleName=role_name).get("Role")
    require(isinstance(role, dict) and role.get("RoleName") == role_name and isinstance(role.get("Arn"), str)
            and role["Arn"].startswith("arn:aws:iam::" + C.ALIGN.ACCOUNT + ":role/") and role["Arn"].endswith("/" + role_name), "snapshot-operator-not-confirmed")
    prefix = "arn:aws:rds:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":"
    resources = [prefix + "db:" + C.RESOURCE.SOURCE_DATABASE, prefix + "snapshot:" + snapshot]
    result = provider("iam", "simulate-principal-policy", PolicySourceArn=role["Arn"], ActionNames=["rds:CreateDBSnapshot"], ResourceArns=resources)
    rows = result.get("EvaluationResults") if isinstance(result, dict) else None
    require(isinstance(rows, list) and len(rows) == len(resources) and result.get("IsTruncated") is False
            and all(isinstance(row, dict) and row.get("EvalActionName") == "rds:CreateDBSnapshot" and row.get("EvalDecision") == "allowed" and not row.get("MissingContextValues") for row in rows)
            and {row.get("EvalResourceName") for row in rows} == set(resources), "snapshot-operator-policy-preflight-not-confirmed")
    return C.DEPLOY.fingerprint({"account": caller["Account"], "role": role["Arn"]})


def context(args, provider, *, source_proof=True, require_terminal_jobs=True, retained_source_evidence=None):
    custody = C.ALIGN.read_receipt(args.receipt.absolute())
    C.ALIGN.source_preflight(custody, **({"retained_source_evidence": retained_source_evidence} if retained_source_evidence is not None else {}))
    if source_proof: C.local_checks()
    artifact = C.source_digest()
    alignment, parameters, subnet_group = C.ALIGN.inspect(provider, custody, C.now())
    binding = {**C.binding_for(custody, alignment), "proof_label": args.proof_label}
    cache = C.ROOT / ".cache/entity-smoke-live" / args.proof_label
    C.filesystem_preflight(cache)
    parameters, resources = TASK.owned_stack(provider, binding, parameters, cache)
    snapshot = TASK.BINDING.DEPLOY.source()[1]
    server = TASK.BINDING.inspect(provider, "server", parameters, resources, snapshot)
    checked = TASK.BINDING.inspect(provider, "database-proof", parameters, resources, snapshot)
    declaration = C.yaml.safe_load((C.CONTRACT.parent / "declaration-contract.yml").read_text())
    deadlines = {row["id"].removeprefix("entity-smoke-"): row["completion"]["deadline_seconds"] for row in declaration["health_recovery"]["workloads"] if "completion" in row}
    value = {"binding": binding, "cache": cache, "parameters": parameters, "resources": resources, "checked": checked, "custody": custody,
             "provider": provider, "artifact": artifact, "binding_snapshot": snapshot, "completion_deadlines": deadlines, "subnet_group": subnet_group,
             "report": {"plan": {}}, "server": server}
    history = TASK.HISTORY.read(TASK.dependencies(), value, args)
    service = C.RESOURCE.service(provider, server["definition"], 1)
    tasks = C.RESOURCE.running_service_tasks(provider)
    require(len(tasks) == 1 and service.get("runningCount") == 1 and service.get("pendingCount") == 0, "snapshot-current-runtime-not-confirmed")
    running = C.RESOURCE.task(provider, tasks[0], server["definition"], binding["image_digest"])
    network = service.get("networkConfiguration")
    awsvpc = network.get("awsvpcConfiguration") if isinstance(network, dict) else None
    require(running.get("lastStatus") == "RUNNING" and running.get("healthStatus") == "HEALTHY" and service.get("launchType") == "FARGATE"
            and isinstance(network, dict) and set(network) == {"awsvpcConfiguration"} and isinstance(awsvpc, dict)
            and set(awsvpc) == {"subnets", "securityGroups", "assignPublicIp"} and awsvpc["assignPublicIp"] == "DISABLED"
            and isinstance(awsvpc["subnets"], list) and len(awsvpc["subnets"]) == len(server["subnets"]) and set(awsvpc["subnets"]) == set(server["subnets"])
            and awsvpc["securityGroups"] == [server["security_group"]], "snapshot-current-runtime-not-confirmed")
    if require_terminal_jobs: C.RESOURCE.require_other_tasks_terminal(provider)
    value["history"] = history
    return value


class Provider(C.Provider):
    def __init__(self):
        super().__init__()
        self.capability, self.consumed, self.rejected_failure, self.provider_condition = None, False, None, None

    def enable_snapshot(self, store, request, guard):
        require(self.capability is None and not self.consumed, "snapshot-capability-already-enabled")
        C.RESOURCE.validate_request("create-recovery-point", request)
        self.capability = store, request, guard

    def __call__(self, service, operation, **parameters):
        if (service, operation) in READS: return self._invoke(service, operation, parameters)
        try:
            require((service, operation) == ("rds", "create-db-snapshot") and self.capability is not None and not self.consumed, "snapshot-provider-operation-prohibited")
            store, request, guard = self.capability
            require(store.read("create-recovery-point", request) is not None, "snapshot-reservation-required")
            expected = {"DBInstanceIdentifier": C.RESOURCE.SOURCE_DATABASE, "DBSnapshotIdentifier": request["snapshot"],
                        "Tags": [{"Key": "Target", "Value": C.RESOURCE.CLUSTER}, {"Key": "Scope", "Value": "entity-smoke"}, {"Key": "ProofLabel", "Value": request["binding"]["proof_label"]}]}
            require(C.RESOURCE.CONTROL.canonical(parameters) == C.RESOURCE.CONTROL.canonical(expected), "snapshot-submission-does-not-match-plan")
            guard()
        except Exception as failure:
            self.rejected_failure = failure if isinstance(failure, known()) else None
            raise C.RESOURCE.SubmissionNotStarted(failure.code if self.rejected_failure is not None else "snapshot-submission-preflight-not-confirmed") from None
        self.capability, self.consumed, self.effect = None, True, "unknown-reconcile-only"
        try: return self._invoke(service, operation, parameters)
        except C.InfrastructureFailure as failure:
            self.provider_condition = failure.code
            raise


def prepare(args, provider, *, source_proof=True):
    value = context(args, provider, source_proof=source_proof)
    binding = {**value["binding"], "record_digest": args.expected_digest}
    snapshot = "kanbien-core-platform-" + args.proof_label
    request = {"binding": binding, "source_resource_id": value["parameters"]["DatabaseResourceId"], "snapshot": snapshot, "original_commit_observed_at": value["history"]["completed_at"]}
    C.RESOURCE.validate_request("create-recovery-point", request)
    store = C.RESOURCE.ResourceStore(value["cache"] / "attempts")
    declaration = graph()
    safe = {"schema": "deploy/entity-smoke-snapshot-plan/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "binding": binding,
            "request_sha256": C.DEPLOY.fingerprint(request), "history_sha256": C.digest_file(value["cache"] / "credential-history.json"), "controller_sha256": value["artifact"],
            "graph_sha256": C.DEPLOY.fingerprint(declaration), "operator_sha256": actor(provider, snapshot),
            "configuration_sha256": C.DEPLOY.fingerprint({"parameters": value["parameters"], "resources": value["resources"], "server": value["server"]}),
            "package_custody_reference": value["custody"]["receipt_reference"], "maximum_snapshot_creates": 1, "task_launch": False, "source_data_mutation": False, "resource_deletion": False, "automatic_retry": False, "isolated_restore_proven": False}
    digest = C.DEPLOY.fingerprint(safe)
    packet = {"schema": "deploy/entity-smoke-snapshot-plan-packet/v1", "plan": safe, "request": request, "plan_sha256": digest}
    path = value["cache"] / "snapshot-plans" / (digest.removeprefix("sha256:") + ".json")
    if not C.RESOURCE.write_exclusive(path, packet): require(C.read_json(path) == packet, "snapshot-plan-retention-conflict")
    active = value["cache"] / "snapshot-plan.json"
    C.RESOURCE.CONTROL.no_symlinks(active)
    require(not active.exists() or C.read_json(active) == packet, "snapshot-original-plan-binding-changed")
    require(args.mode != "execute" or args.approved_plan == digest, "snapshot-approved-plan-mismatch")
    book = C.GateBook(value["artifact"], value["cache"] / "snapshot-realization", contract=declaration, artifact_bindings={row["id"]: value["artifact"] for row in declaration["artifacts"]})
    for identifier in book.known: book.component(identifier)
    book.bind_plan(digest)
    for gate in C.GATE.GATE_ORDER[:5]: book.gate(gate)
    book.validate("change-set", 1)
    return {"context": value, "packet": packet, "store": store, "book": book, "active": active}


def run(args, provider):
    prepared = prepare(args, provider)
    value, packet, store, book = (prepared[key] for key in ("context", "packet", "store", "book"))
    if args.mode == "plan": return {"verdict": "planned", "plan": packet["plan"], "plan_sha256": packet["plan_sha256"], "effect": "not-started"}
    if not C.RESOURCE.write_exclusive(prepared["active"], packet): require(C.read_json(prepared["active"]) == packet, "snapshot-active-plan-conflict")
    def guard():
        require(C.source_digest() == value["artifact"], "snapshot-source-changed-before-submission")
        require(prepare(args, provider, source_proof=False)["packet"] == packet, "snapshot-bindings-changed-before-submission")
        book.validate("execution-preflight", 1)
        require(C.source_digest() == value["artifact"], "snapshot-source-changed-before-submission")
    book.gate("execution-preflight"); book.validate("execution-preflight", 1)
    request = packet["request"]
    if store.read("create-recovery-point", request) is None: provider.enable_snapshot(store, request, guard)
    else: provider.effect = "original-snapshot-reconcile-only"
    deadline = time.monotonic() + args.wait_seconds
    while True:
        result = C.RESOURCE.create_recovery_point(provider, store, request["binding"], request["source_resource_id"], request["original_commit_observed_at"])
        if result["status"] == "completed": break
        if time.monotonic() >= deadline: return {"verdict": "pending", "plan_sha256": packet["plan_sha256"], "effect": "original-snapshot-not-terminal"}
        time.sleep(2)
    require(prepare(args, provider, source_proof=False)["packet"] == packet, "snapshot-bindings-changed-before-completion")
    book.gate("controlled-execution"); evidence = book.validate("controlled-execution", 1)
    retained = {"schema": "deploy/entity-smoke-snapshot-receipt/v1", "packet": packet, "result": result, "realization_evidence": str(evidence.relative_to(C.ROOT)), "realization_evidence_sha256": C.digest_file(evidence), "isolated_restore_proven": False}
    path = value["cache"] / "snapshot-receipt.json"
    if not C.RESOURCE.write_exclusive(path, retained):
        prior = C.read_json(path)
        require(isinstance(prior, dict) and set(prior) == set(retained) and all(prior[key] == retained[key] for key in ("schema", "packet", "result", "isolated_restore_proven")), "snapshot-receipt-conflict")
        reference = prior["realization_evidence"]
        prefix = str((value["cache"] / "snapshot-realization").relative_to(C.ROOT)) + "/controlled-execution-"
        require(isinstance(reference, str) and reference.startswith(prefix) and re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):])
                and C.digest_file(C.ROOT / reference) == prior["realization_evidence_sha256"], "snapshot-retained-gate-not-confirmed")
    provider.effect = "original-snapshot-observed"
    return {"verdict": "completed", "receipt": str(path.relative_to(C.ROOT)), "plan_sha256": packet["plan_sha256"], "isolated_restore_proven": False, "effect": provider.effect}


def completed(context_value, args, provider):
    path = context_value["cache"] / "snapshot-receipt.json"
    C.RESOURCE.CONTROL.no_symlinks(path)
    require(path.is_file(), "snapshot-completion-required")
    value = C.read_json(path)
    require(isinstance(value, dict) and set(value) == {"schema", "packet", "result", "realization_evidence", "realization_evidence_sha256", "isolated_restore_proven"}
            and value["schema"] == "deploy/entity-smoke-snapshot-receipt/v1" and value["isolated_restore_proven"] is False, "snapshot-completion-invalid")
    packet = value["packet"]
    require(isinstance(packet, dict) and set(packet) == {"schema", "plan", "request", "plan_sha256"} and packet["schema"] == "deploy/entity-smoke-snapshot-plan-packet/v1"
            and isinstance(packet["plan"], dict) and packet["plan_sha256"] == C.DEPLOY.fingerprint(packet["plan"]), "snapshot-completed-plan-invalid")
    request, plan = packet["request"], packet["plan"]
    expected = {"binding": {**context_value["binding"], "record_digest": args.expected_digest}, "source_resource_id": context_value["parameters"]["DatabaseResourceId"],
                "snapshot": "kanbien-core-platform-" + args.proof_label, "original_commit_observed_at": context_value["history"]["completed_at"]}
    require(request == expected and plan.get("request_sha256") == C.DEPLOY.fingerprint(request) and plan.get("binding") == expected["binding"]
            and plan.get("controller_sha256") == context_value["artifact"] and plan.get("graph_sha256") == C.DEPLOY.fingerprint(graph())
            and plan.get("history_sha256") == C.digest_file(context_value["cache"] / "credential-history.json")
            and plan.get("configuration_sha256") == C.DEPLOY.fingerprint({"parameters": context_value["parameters"], "resources": context_value["resources"], "server": context_value["server"]}), "snapshot-completed-binding-mismatch")
    for retained in (context_value["cache"] / "snapshot-plan.json", context_value["cache"] / "snapshot-plans" / (packet["plan_sha256"].removeprefix("sha256:") + ".json")):
        require(C.read_json(retained) == packet, "snapshot-original-plan-not-retained")
    store = C.RESOURCE.ResourceStore(context_value["cache"] / "attempts")
    require(store.read("create-recovery-point", request) is not None, "snapshot-original-journal-required")
    actual = C.RESOURCE.create_recovery_point(provider, store, request["binding"], request["source_resource_id"], request["original_commit_observed_at"])
    require(actual.get("status") == "completed" and actual == value["result"], "snapshot-original-completion-not-confirmed")
    reference = value["realization_evidence"]
    prefix = str((context_value["cache"] / "snapshot-realization").relative_to(C.ROOT)) + "/controlled-execution-"
    require(isinstance(reference, str) and reference.startswith(prefix) and re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):])
            and C.digest_file(C.ROOT / reference) == value["realization_evidence_sha256"], "snapshot-retained-gate-not-confirmed")
    gate = C.read_json(C.ROOT / reference)
    require(isinstance(gate, dict) and gate.get("plan_sha256") == packet["plan_sha256"] and isinstance(gate.get("facts"), dict)
            and [row.get("gate") for row in gate["facts"].get("gate_evidence", [])] == list(C.GATE.GATE_ORDER[:7]), "snapshot-completed-gate-invalid")
    return value


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(SnapshotFailure("snapshot-arguments-invalid"))
    parser.add_argument("--mode", choices=("plan", "execute"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--proof-label", required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--approved-plan")
    parser.add_argument("--wait-seconds", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) and re.fullmatch(r"[a-f0-9]{64}", args.expected_digest) and 0 <= args.wait_seconds <= 60, "snapshot-arguments-invalid")
    require(args.mode != "execute" or isinstance(args.approved_plan, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", args.approved_plan), "snapshot-approved-plan-required")
    require(args.mode == "execute" or args.approved_plan is None, "snapshot-arguments-invalid")
    return args


def main():
    provider, context_value = Provider(), {}
    try:
        args = parse()
        context_value = {"mode": args.mode, "proof_label_sha256": hashlib.sha256(args.proof_label.encode()).hexdigest()}
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        result = run(args, provider)
        print(json.dumps({"schema": "deploy/entity-smoke-snapshot-report/v1", **result}, sort_keys=True))
        return 0 if result["verdict"] in {"planned", "completed"} else 2
    except Exception as failure:
        failure = provider.rejected_failure or failure
        condition = failure.code if isinstance(failure, known()) else "snapshot-boundary-not-confirmed"
        if isinstance(failure, TASK.BINDING.BindingFailure): context_value.update(field=failure.field, item=failure.item, affected_workload=failure.workload)
        reference = failure.evidence_reference if isinstance(failure, C.InfrastructureFailure) else None
        print(json.dumps({"schema": "deploy/entity-smoke-snapshot-report/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "verdict": "blocked", "condition": condition, "context": context_value, "effect": provider.effect,
                          **({"provider_condition": provider.provider_condition} if provider.provider_condition is not None else {}), **({"evidence_reference": reference} if reference is not None else {})}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
