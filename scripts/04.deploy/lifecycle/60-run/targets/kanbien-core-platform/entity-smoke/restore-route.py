#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.restore.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind isolated clone review, execution and successful-reader cleanup to actual snapshot custody, exact owned resource intents and normal gates without source mutation or replay.
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
import time
from types import SimpleNamespace


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
S = module("entity_smoke_restore_snapshot", DIRECTORY / "snapshot-route.py")
TASK, C = S.TASK, S.C
RESTORE = module("entity_smoke_restore_owned_controls", DIRECTORY / "restore-control.py")
R = RESTORE.RESOURCE
BINDING = module("entity_smoke_restore_reader_binding", DIRECTORY / "restore-binding.py")


class RestoreFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(value, code):
    if not value: raise RestoreFailure(code)


def known(): return (RestoreFailure, R.ResourceFailure, R.CONTROL.TaskFailure, R.EVIDENCE.EvidenceFailure) + S.known() + TASK.RECOVERY.failures()


def adapted(provider):
    # The existing separately loaded helper owns its missing-resource sentinel;
    # translate the canonical CLI adapter's exact missing result, not text.
    def call(service, operation, **parameters):
        try: return provider(service, operation, **parameters)
        except C.RESOURCE.ResourceMissing: raise R.ResourceMissing() from None
    return call


def parameters(value, snapshot):
    p, binding = value["parameters"], {**value["binding"], "record_digest": value["history"]["binding"]["record_digest"]}
    result = {key: p[key] for key in ("VpcId", "VpcCidr", "EndpointSecurityGroupId", "S3ArtifactPrefixListId", "LogGroupName", "ImageRepositoryUri", "ImageRepositoryArn", "ImageDigest", "SourceRevision")}
    result.update(DatabaseSubnetGroupName=value["subnet_group"], RestoredDatabaseName=p["DatabaseName"], RestoredDatabaseIdentifier=RESTORE.names(binding)[2],
                  SourceSnapshotArn=snapshot["result"]["facts"]["snapshot_arn"], ProofLabel=binding["proof_label"])
    RESTORE.parameters_for(binding, result)
    return result


def source(args, provider, *, source_proof=True, require_terminal_jobs=True):
    value = S.context(args, provider, source_proof=source_proof, require_terminal_jobs=require_terminal_jobs)
    snapshot = S.completed(value, args, provider)
    scope = {"resources": value["resources"]}
    _, other = TASK.RECOVERY.STATE.STOP.B.services(C, provider, scope, {"server": value["server"]["definition"]})
    old = value["history"]["prerequisites"]["packets"]["initial-stop"]["root"]["request"]["packet"]["intent"]["other_services"]
    require(other == old, "restore-other-service-configuration-changed")
    return {**value, "snapshot": snapshot, "restore_parameters": parameters(value, snapshot), "restore_binding": {**value["binding"], "record_digest": args.expected_digest}}


def gate_reference(value, cache, name, plan_hash):
    reference = value.get("realization_evidence")
    prefix = str((cache / (name + "-realization")).relative_to(C.ROOT)) + "/controlled-execution-"
    require(isinstance(reference, str) and reference.startswith(prefix) and re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):])
            and C.digest_file(C.ROOT / reference) == value.get("realization_evidence_sha256"), "restore-retained-gate-changed")
    gate = C.read_json(C.ROOT / reference)
    require(isinstance(gate, dict) and gate.get("plan_sha256") == plan_hash and isinstance(gate.get("facts"), dict)
            and [row.get("gate") for row in gate["facts"].get("gate_evidence", [])] == list(C.GATE.GATE_ORDER[:7]), "restore-retained-gate-invalid")


def deployment(value, args, provider, *, observe=True):
    path = value["cache"] / "restore-deploy-receipt.json"
    C.RESOURCE.CONTROL.no_symlinks(path)
    require(path.is_file(), "restore-deployment-completion-required")
    receipt = C.read_json(path)
    require(isinstance(receipt, dict) and set(receipt) == {"schema", "packet", "result", "observed_at", "realization_evidence", "realization_evidence_sha256", "restored_data_readback"}
            and receipt["schema"] == "deploy/entity-smoke-restore-deploy-receipt/v1" and receipt["restored_data_readback"] is False, "restore-deployment-receipt-invalid")
    packet = receipt["packet"]
    require(isinstance(packet, dict) and set(packet) == {"schema", "plan", "request", "plan_sha256"} and packet["schema"] == "deploy/entity-smoke-restore-plan-packet/v1"
            and isinstance(packet["plan"], dict) and packet["plan_sha256"] == C.DEPLOY.fingerprint(packet["plan"]), "restore-deployment-plan-invalid")
    request = RESTORE.request(value["restore_binding"], value["restore_parameters"])
    require(packet["request"] == request and packet["plan"].get("phase") == "deploy" and packet["plan"].get("binding") == value["restore_binding"]
            and packet["plan"].get("request_sha256") == C.DEPLOY.fingerprint(request) and packet["plan"].get("controller_sha256") == value["artifact"]
            and packet["plan"].get("snapshot_sha256") == C.digest_file(value["cache"] / "snapshot-receipt.json"), "restore-deployment-binding-mismatch")
    for path in (value["cache"] / "restore-deploy-plan.json", value["cache"] / "restore-deploy-plans" / (packet["plan_sha256"].removeprefix("sha256:") + ".json")):
        require(C.read_json(path) == packet, "restore-deployment-plan-not-retained")
    result = receipt["result"]
    require(isinstance(result, dict) and set(result) == {"status", "reservation", "facts"} and result.get("status") == "completed"
            and isinstance(result.get("reservation"), dict) and isinstance(result.get("facts"), dict), "restore-deployment-result-invalid")
    facts = result["facts"]
    require(set(facts) == {"stack_arn", "database_identifier", "restored_resource_id", "resources", "resources_sha256"} and isinstance(facts["resources"], dict)
            and set(facts["resources"]) == set(RESTORE.RESOURCE_TYPES) and all(isinstance(row, dict) and set(row) == {"type", "physical_id"}
                and row["type"] == RESTORE.RESOURCE_TYPES[name] and isinstance(row["physical_id"], str) and row["physical_id"] for name, row in facts["resources"].items())
            and facts["resources_sha256"] == C.DEPLOY.fingerprint(facts["resources"]) and facts["database_identifier"] == RESTORE.names(value["restore_binding"])[2]
            and facts["resources"]["RestoredDatabase"]["physical_id"] == facts["database_identifier"] and isinstance(facts["restored_resource_id"], str)
            and re.fullmatch(r"db-[A-Za-z0-9]+", facts["restored_resource_id"]), "restore-deployment-resources-invalid")
    store = R.ResourceStore(value["cache"] / "attempts")
    execution = result["reservation"]
    require(isinstance(execution.get("request"), dict) and all(execution["request"].get(key) == item for key, item in request.items())
            and execution["request"].get("stack_arn") == facts["stack_arn"] and store.read("execute-restore", execution["request"]) == execution
            and store.read("restore-change-set", request) is not None, "restore-deployment-journal-required")
    require(C.RESOURCE.timestamp(receipt["observed_at"]) >= C.RESOURCE.timestamp(execution["reserved_at"])
            and C.RESOURCE.timestamp(execution["reserved_at"]) >= C.RESOURCE.timestamp(value["snapshot"]["result"]["facts"]["snapshot_created_at"]), "restore-deployment-order-invalid")
    gate_reference(receipt, value["cache"], "restore-deploy", packet["plan_sha256"])
    if observe:
        current = RESTORE.observe_restore(adapted(provider), store, value["restore_binding"], value["restore_parameters"], execution["request"]["change_set_arn"], execution["request"]["stack_arn"])
        require(current == result, "restore-deployment-observation-changed")
    return receipt


def reader_context(value, deployed):
    facts = deployed["result"]["facts"]
    p, parent = value["restore_parameters"], value["restore_binding"]
    child = {**{key: item for key, item in parent.items() if key != "record_digest"}, "permission_contract_sha256": C.digest_file(RESTORE.SOURCE),
             "dependency_incarnation_sha256": C.DEPLOY.fingerprint({"resource_id": facts["restored_resource_id"], "database": p["RestoredDatabaseName"], "schema": "entity_smoke"})}
    checked = {"definition": facts["resources"]["RestoreReaderTaskDefinition"]["physical_id"], "security_group": facts["resources"]["RestoreReaderSecurityGroup"]["physical_id"], "subnets": value["parameters"]["PrivateSubnetIds"].split(",")}
    probe_label = "entity-smoke-" + hashlib.sha256((parent["proof_label"] + ":restore-reader:restore-read:preflight:isolated-restore").encode()).hexdigest()[:24]
    return {**value, "binding": child, "checked": checked, "report": {"plan": {"preflight_label": probe_label}}, "required_after": deployed["observed_at"], "deployed": deployed}


def reader(value, args, provider):
    deployed = deployment(value, args, provider, observe=False)
    child = reader_context(value, deployed)
    selected = SimpleNamespace(**{**vars(args), "proof_stage": "isolated-restore", "workload": "restore-reader", "operation": "restore-read", "phase": "operation"})
    for phase in ("preflight", "operation"):
        prior = SimpleNamespace(**{**vars(selected), "phase": phase})
        step = TASK.STEPS.observe_packet(TASK.dependencies(), child, prior, provider, historical=True)
        require(step is not None, "restore-reader-completion-required")
        require(TASK.RUNNER.EVIDENCE.timestamp(step["receipt"]["task"]["created_at"]) >= TASK.RUNNER.EVIDENCE.timestamp(deployed["observed_at"]), "restore-reader-predates-clone-completion")
    require(step["receipt"]["result"].get("record_digest") == args.expected_digest, "restore-reader-original-digest-mismatch")
    plan_path = value["cache"] / "restore-reader-plans" / (step["plan_sha256"].removeprefix("sha256:") + ".json")
    plan = C.read_json(plan_path)
    require(isinstance(plan, dict) and C.DEPLOY.fingerprint(plan) == step["plan_sha256"] and plan.get("phase") == "operation" and plan.get("binding") == child["binding"]
            and plan.get("parent_deployment_sha256") == C.digest_file(value["cache"] / "restore-deploy-receipt.json")
            and plan.get("request_sha256") == C.DEPLOY.fingerprint(step["reservation"]["request"]) and plan.get("controller_sha256") == value["artifact"]
            and plan.get("graph_sha256") == C.DEPLOY.fingerprint(TASK.GRAPH.contract("restore-reader", C.GATE)), "restore-reader-original-plan-mismatch")
    return {"context": child, "step": step, "deployed": deployed}


def graph(phase):
    def rename(value):
        if isinstance(value, str): return value.replace("infrastructure", "restore-" + phase)
        if isinstance(value, list): return [rename(item) for item in value]
        if isinstance(value, dict): return {key: rename(item) for key, item in value.items()}
        return value
    value = rename(C.yaml.safe_load(C.CONTRACT.read_text()))
    value["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/restore-route.py"
    value["identities"][0]["permissions"] = ["inspect-source-snapshot-and-owned-clone", "review-and-execute-only-own-clone-create" if phase == "deploy" else "delete-only-proven-disposable-clone"]
    value["state_stores"][0]["semantics"] = ["completed-original-record-snapshot", "exact-isolated-clone-template-and-lineage", "single-reserved-provider-effect", "separate-reader-and-cleanup-proof"]
    value["change_shape"]["allowed_operation_classes"] = ["create" if phase == "deploy" else "delete"]
    value["change_shape"]["forbidden_operation_classes"] = ["update", "replace", "broaden-permission", "delete" if phase == "deploy" else "create"]
    if phase == "cleanup":
        value["change_shape"]["disposable_restore_cleanup"] = {
            "original_readback_required": True, "positive_ownership_required": True,
            "explicit_execution_approval_required": True, "preserve_source_and_shared_resources": True}
    value["assumptions"] = [{"id": "clone-is-not-acceptance", "statement": "creation-requires-separate-original-record-read-and-owned-cleanup-before-acceptance", "required_proof": "declared", "actual_proof": "declared"}]
    C.GATE.validate_contract(value)
    return value


def actor(provider, binding, phase):
    caller = provider("sts", "get-caller-identity")
    arn = caller.get("Arn") if isinstance(caller, dict) else None
    require(caller.get("Account") == C.ALIGN.ACCOUNT and isinstance(arn, str) and re.fullmatch(r"arn:aws:sts::" + C.ALIGN.ACCOUNT + r":assumed-role/[A-Za-z0-9+=,.@_-]+/[A-Za-z0-9+=,.@_-]+", arn), "restore-operator-not-confirmed")
    name = arn.split("/")[1]
    role = provider("iam", "get-role", RoleName=name).get("Role")
    require(isinstance(role, dict) and role.get("RoleName") == name and isinstance(role.get("Arn"), str) and role["Arn"].startswith("arn:aws:iam::" + C.ALIGN.ACCOUNT + ":role/") and role["Arn"].endswith("/" + name), "restore-operator-not-confirmed")
    resource = "arn:aws:cloudformation:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":stack/" + RESTORE.names(binding)[0] + "/*"
    actions = ["cloudformation:CreateChangeSet", "cloudformation:ExecuteChangeSet"] if phase == "deploy" else ["cloudformation:DeleteStack"]
    for action in actions:
        value = provider("iam", "simulate-principal-policy", PolicySourceArn=role["Arn"], ActionNames=[action], ResourceArns=[resource])
        rows = value.get("EvaluationResults") if isinstance(value, dict) else None
        require(isinstance(rows, list) and len(rows) == 1 and value.get("IsTruncated") is False and isinstance(rows[0], dict)
                and rows[0].get("EvalActionName") == action and rows[0].get("EvalResourceName") == resource and rows[0].get("EvalDecision") == "allowed" and not rows[0].get("MissingContextValues"), "restore-operator-policy-preflight-not-confirmed")
    return C.DEPLOY.fingerprint({"account": caller["Account"], "role": role["Arn"]})


class Provider(C.Provider):
    def __init__(self):
        super().__init__()
        self.capability, self.consumed, self.rejected_failure, self.provider_condition = None, False, None, None

    def enable_restore(self, phase, store, request, payload, guard):
        require(self.capability is None and not self.consumed, "restore-capability-already-enabled")
        R.validate_request(phase, request)
        self.capability = phase, store, request, payload, guard

    def __call__(self, service, operation, **parameters):
        if (service, operation) in S.READS: return self._invoke(service, operation, parameters)
        try:
            require(self.capability is not None and not self.consumed, "restore-provider-operation-prohibited")
            phase, store, request, payload, guard = self.capability
            selected = {"restore-change-set": "create-change-set", "execute-restore": "execute-change-set", "delete-restore": "delete-stack"}[phase]
            require((service, operation) == ("cloudformation", selected) and store.read(phase, request) is not None, "restore-effect-reservation-required")
            require(R.CONTROL.canonical(parameters) == R.CONTROL.canonical(payload()), "restore-submission-does-not-match-plan")
            guard()
        except Exception as failure:
            self.rejected_failure = failure if isinstance(failure, known()) else None
            raise R.SubmissionNotStarted(failure.code if self.rejected_failure is not None else "restore-submission-preflight-not-confirmed") from None
        self.capability, self.consumed, self.effect = None, True, "unknown-reconcile-only"
        try: return self._invoke(service, operation, parameters)
        except C.InfrastructureFailure as failure:
            self.provider_condition = failure.code
            raise


def cleanup_request(value, captured):
    facts, step = captured["deployed"]["result"]["facts"], captured["step"]
    return {"binding": value["restore_binding"], "stack_arn": facts["stack_arn"], "restored_resource_id": facts["restored_resource_id"], "resources_sha256": facts["resources_sha256"],
            "reader_task_arn": step["receipt"]["task"]["arn"], "reader_receipt_sha256": RESTORE.digest(step["receipt"])}


def completed_cleanup(value, args, provider):
    """Read retained gated cleanup and actual absence, with no deletion path."""
    path = value["cache"] / "restore-cleanup-receipt.json"
    R.CONTROL.no_symlinks(path)
    require(path.is_file(), "restore-cleanup-completion-required")
    receipt = C.read_json(path)
    require(isinstance(receipt, dict) and set(receipt) == {"schema", "packet", "result", "observed_at", "realization_evidence", "realization_evidence_sha256", "restored_data_readback"}
            and receipt["schema"] == "deploy/entity-smoke-restore-cleanup-receipt/v1" and receipt["restored_data_readback"] is False, "restore-cleanup-receipt-invalid")
    captured = reader(value, args, provider)
    expected = cleanup_request(value, captured)
    packet = receipt["packet"]
    require(isinstance(packet, dict) and set(packet) == {"schema", "plan", "request", "plan_sha256"}
            and packet["schema"] == "deploy/entity-smoke-restore-plan-packet/v1" and isinstance(packet["plan"], dict)
            and packet["plan_sha256"] == C.DEPLOY.fingerprint(packet["plan"]), "restore-cleanup-plan-invalid")
    plan = packet["plan"]
    require(packet["request"] == expected and plan.get("phase") == "cleanup" and plan.get("binding") == value["restore_binding"]
            and plan.get("target") == C.RESOURCE.CLUSTER and plan.get("scope") == "entity-smoke"
            and plan.get("request_sha256") == C.DEPLOY.fingerprint(expected) and plan.get("controller_sha256") == value["artifact"]
            and plan.get("snapshot_sha256") == C.digest_file(value["cache"] / "snapshot-receipt.json")
            and plan.get("history_sha256") == C.digest_file(value["cache"] / "credential-history.json")
            and plan.get("configuration_sha256") == C.DEPLOY.fingerprint(value["restore_parameters"])
            and plan.get("template_sha256") == C.digest_file(RESTORE.SOURCE)
            and plan.get("reader_sha256") == C.DEPLOY.fingerprint(captured["step"])
            and plan.get("package_custody_reference") == value["custody"]["receipt_reference"]
            and type(plan.get("resource_count")) is int and plan["resource_count"] == len(RESTORE.RESOURCE_TYPES)
            and all(plan.get(key) is False for key in ("task_launch", "source_mutation", "automatic_retry", "scope_acceptance")), "restore-cleanup-binding-mismatch")
    # Validate the exact bounded cleanup graph, not a generic deletion waiver.
    require(plan.get("graph_sha256") == C.DEPLOY.fingerprint(graph("cleanup")), "restore-cleanup-graph-mismatch")
    for retained in (value["cache"] / "restore-cleanup-plan.json", value["cache"] / "restore-cleanup-plans" / (packet["plan_sha256"].removeprefix("sha256:") + ".json")):
        R.CONTROL.no_symlinks(retained)
        require(C.read_json(retained) == packet, "restore-cleanup-plan-not-retained")
    store = R.ResourceStore(value["cache"] / "attempts")
    reservation = store.read("delete-restore", expected)
    require(reservation is not None, "restore-cleanup-journal-required")
    result = receipt["result"]
    require(isinstance(result, dict) and result.get("status") == "completed" and result.get("reservation") == reservation,
            "restore-cleanup-terminal-result-required")
    require(C.RESOURCE.timestamp(reservation["reserved_at"]) >= C.RESOURCE.timestamp(captured["step"]["receipt"]["collected_at"])
            and C.RESOURCE.timestamp(receipt["observed_at"]) >= C.RESOURCE.timestamp(reservation["reserved_at"]), "restore-cleanup-order-invalid")
    gate_reference(receipt, value["cache"], "restore-cleanup", packet["plan_sha256"])
    # Unlike cleanup_restore, observe_cleanup has no reserve/submission call.
    current = RESTORE.observe_cleanup(adapted(provider), store, value["restore_binding"], value["restore_parameters"], captured["deployed"]["result"]["facts"],
                                      captured["step"]["reservation"], captured["step"]["receipt"])
    require(current == result and current.get("facts", {}).get("absence_observed") is True
            and current["facts"].get("source_mutation") is False, "restore-cleanup-current-absence-not-confirmed")
    return {"receipt": receipt, "reader": captured, "required_after": receipt["observed_at"]}


def prepare(args, provider, *, source_proof=True):
    value = source(args, provider, source_proof=source_proof)
    store = R.ResourceStore(value["cache"] / "attempts")
    captured = reader(value, args, provider) if args.phase == "cleanup" else None
    request = cleanup_request(value, captured) if captured is not None else RESTORE.request(value["restore_binding"], value["restore_parameters"])
    if captured is not None and store.read("delete-restore", request) is None:
        deployed = deployment(value, args, provider)
        BINDING.inspect(C, TASK.BINDING, RESTORE, provider, value["restore_binding"], value["restore_parameters"], deployed["result"]["facts"], value["parameters"]["PrivateSubnetIds"].split(","))
    declaration = graph(args.phase)
    safe = {"schema": "deploy/entity-smoke-restore-plan/v1", "phase": args.phase, "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "binding": value["restore_binding"],
            "request_sha256": C.DEPLOY.fingerprint(request), "controller_sha256": value["artifact"], "graph_sha256": C.DEPLOY.fingerprint(declaration), "operator_sha256": actor(provider, value["restore_binding"], args.phase),
            "snapshot_sha256": C.digest_file(value["cache"] / "snapshot-receipt.json"), "history_sha256": C.digest_file(value["cache"] / "credential-history.json"),
            "configuration_sha256": C.DEPLOY.fingerprint(value["restore_parameters"]), "template_sha256": C.digest_file(RESTORE.SOURCE), "package_custody_reference": value["custody"]["receipt_reference"],
            "reader_sha256": None if captured is None else C.DEPLOY.fingerprint(captured["step"]), "resource_count": len(RESTORE.RESOURCE_TYPES), "task_launch": False, "source_mutation": False, "automatic_retry": False, "scope_acceptance": False}
    digest = C.DEPLOY.fingerprint(safe)
    packet = {"schema": "deploy/entity-smoke-restore-plan-packet/v1", "plan": safe, "request": request, "plan_sha256": digest}
    prefix = "restore-" + args.phase
    active, retained = value["cache"] / (prefix + "-plan.json"), value["cache"] / (prefix + "-plans") / (digest.removeprefix("sha256:") + ".json")
    if not R.write_exclusive(retained, packet): require(C.read_json(retained) == packet, "restore-plan-retention-conflict")
    R.CONTROL.no_symlinks(active)
    require(not active.exists() or C.read_json(active) == packet, "restore-original-plan-binding-changed")
    require(args.mode == "plan" or args.approved_plan == digest, "restore-approved-plan-mismatch")
    book = C.GateBook(value["artifact"], value["cache"] / (prefix + "-realization"), contract=declaration, artifact_bindings={row["id"]: value["artifact"] for row in declaration["artifacts"]})
    for identifier in book.known: book.component(identifier)
    book.bind_plan(digest)
    for gate in C.GATE.GATE_ORDER[:5]: book.gate(gate)
    operation = "create" if args.phase == "deploy" else "delete"
    book.validate("change-set", len(RESTORE.RESOURCE_TYPES), operation_class=operation)
    return {"context": value, "store": store, "packet": packet, "active": active, "book": book, "captured": captured, "operation": operation}


def payload(prepared, phase):
    value, store, packet = (prepared[key] for key in ("context", "store", "packet"))
    binding, parameters_value = value["restore_binding"], value["restore_parameters"]
    stack, change, _ = RESTORE.names(binding)
    if phase == "restore-change-set":
        reservation = store.read(phase, packet["request"])
        return {"StackName": stack, "ChangeSetName": change, "ChangeSetType": "CREATE", "TemplateBody": RESTORE.source()[0],
                "Parameters": [{"ParameterKey": key, "ParameterValue": item} for key, item in sorted(parameters_value.items())], "Capabilities": ["CAPABILITY_IAM"], "OnStackFailure": "DO_NOTHING",
                "Description": reservation["operation_id"], "ClientToken": reservation["operation_id"], "Tags": [{"Key": key, "Value": item} for key, item in RESTORE.tags(binding).items()]}
    request = prepared["effect_request"]
    reservation = store.read(phase, request)
    if phase == "execute-restore": return {"StackName": request["stack_arn"], "ChangeSetName": request["change_set_arn"], "ClientRequestToken": reservation["operation_id"]}
    return {"StackName": request["stack_arn"], "ClientRequestToken": reservation["operation_id"]}


def run(args, provider):
    prepared = prepare(args, provider)
    value, store, packet, book = (prepared[key] for key in ("context", "store", "packet", "book"))
    if args.mode == "plan": return {"verdict": "planned", "plan": packet["plan"], "plan_sha256": packet["plan_sha256"], "effect": "not-started"}
    if not R.write_exclusive(prepared["active"], packet): require(C.read_json(prepared["active"]) == packet, "restore-active-plan-conflict")
    count, operation = len(RESTORE.RESOURCE_TYPES), prepared["operation"]
    def guard():
        require(C.source_digest() == value["artifact"] and prepare(args, provider, source_proof=False)["packet"] == packet, "restore-bindings-changed-before-submission")
        book.validate("execution-preflight", count, operation_class=operation)
        require(C.source_digest() == value["artifact"], "restore-source-changed-before-submission")
    book.gate("execution-preflight"); book.validate("execution-preflight", count, operation_class=operation)
    phase = "delete-restore" if args.phase == "cleanup" else "restore-change-set" if args.mode == "review" else "execute-restore"
    if phase == "execute-restore":
        review = C.read_json(value["cache"] / "restore-review-receipt.json")
        require(isinstance(review, dict) and review.get("packet") == packet and isinstance(review.get("result"), dict)
                and review["result"].get("status") == "reviewed", "restore-reviewed-change-required")
        gate_reference(review, value["cache"], "restore-deploy", packet["plan_sha256"])
        facts = review["result"]["facts"]
        prepared["effect_request"] = {**packet["request"], "change_set_arn": facts["change_set_arn"], "stack_arn": facts["stack_arn"]}
    else: prepared["effect_request"] = packet["request"]
    effect_request = prepared["effect_request"]
    if store.read(phase, effect_request) is None: provider.enable_restore(phase, store, effect_request, lambda: payload(prepared, phase), guard)
    else: provider.effect = "original-restore-operation-reconcile-only"
    deadline = time.monotonic() + args.wait_seconds
    while True:
        if phase == "restore-change-set": result = RESTORE.prepare_restore(adapted(provider), store, value["restore_binding"], value["restore_parameters"])
        elif phase == "execute-restore": result = RESTORE.execute_restore(adapted(provider), store, value["restore_binding"], value["restore_parameters"], effect_request["change_set_arn"], effect_request["stack_arn"])
        else:
            captured = prepared["captured"]
            result = RESTORE.cleanup_restore(adapted(provider), store, value["restore_binding"], value["restore_parameters"], captured["deployed"]["result"]["facts"], captured["step"]["reservation"], captured["step"]["receipt"], historical_reader=True)
        if result["status"] in {"completed", "reviewed"}: break
        if time.monotonic() >= deadline: return {"verdict": "pending", "plan_sha256": packet["plan_sha256"], "effect": "original-restore-operation-not-terminal"}
        time.sleep(2)
    require(prepare(args, provider, source_proof=False)["packet"] == packet, "restore-bindings-changed-before-completion")
    book.gate("controlled-execution"); evidence = book.validate("controlled-execution", count, operation_class=operation)
    target = value["cache"] / ("restore-review-receipt.json" if phase == "restore-change-set" else "restore-" + args.phase + "-receipt.json")
    retained = {"schema": "deploy/entity-smoke-restore-" + ("review" if phase == "restore-change-set" else args.phase) + "-receipt/v1", "packet": packet, "result": result,
                "observed_at": datetime.now(timezone.utc).isoformat(), "realization_evidence": str(evidence.relative_to(C.ROOT)), "realization_evidence_sha256": C.digest_file(evidence), "restored_data_readback": False}
    if not R.write_exclusive(target, retained):
        prior = C.read_json(target)
        require(isinstance(prior, dict) and set(prior) == set(retained) and all(prior[key] == retained[key] for key in ("schema", "packet", "result", "restored_data_readback")), "restore-receipt-retention-conflict")
        gate_reference(prior, value["cache"], "restore-" + args.phase, packet["plan_sha256"])
    provider.effect = "original-restore-operation-observed"
    return {"verdict": "completed", "plan_sha256": packet["plan_sha256"], "receipt": str(target.relative_to(C.ROOT)), "restored_data_readback": False, "effect": provider.effect}


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(RestoreFailure("restore-arguments-invalid"))
    parser.add_argument("--mode", choices=("plan", "review", "execute"), required=True)
    parser.add_argument("--phase", choices=("deploy", "cleanup"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--proof-label", required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--approved-plan")
    parser.add_argument("--wait-seconds", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) and re.fullmatch(r"[a-f0-9]{64}", args.expected_digest) and 0 <= args.wait_seconds <= 60
            and not (args.phase == "cleanup" and args.mode == "review"), "restore-arguments-invalid")
    require(args.mode == "plan" and args.approved_plan is None or args.mode != "plan" and isinstance(args.approved_plan, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", args.approved_plan), "restore-approved-plan-required")
    return args


def main():
    provider, safe = Provider(), {}
    try:
        args = parse()
        safe = {"mode": args.mode, "phase": args.phase, "proof_label_sha256": hashlib.sha256(args.proof_label.encode()).hexdigest()}
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        result = run(args, provider)
        print(json.dumps({"schema": "deploy/entity-smoke-restore-report/v1", **result}, sort_keys=True)); return 2 if result["verdict"] == "pending" else 0
    except Exception as failure:
        failure = provider.rejected_failure or failure
        condition = failure.code if isinstance(failure, known()) else "restore-boundary-not-confirmed"
        if isinstance(failure, TASK.BINDING.BindingFailure): safe.update(field=failure.field, item=failure.item, affected_workload=failure.workload)
        item = TASK.RECOVERY.failure_item(failure)
        if item is not None: safe["item"] = item
        evidence = failure.evidence_reference if isinstance(failure, C.InfrastructureFailure) else None
        print(json.dumps({"schema": "deploy/entity-smoke-restore-report/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "verdict": "blocked", "condition": condition, "context": safe, "effect": provider.effect,
                          **({"provider_condition": provider.provider_condition} if provider.provider_condition is not None else {}), **({"evidence_reference": evidence} if evidence is not None else {})}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
