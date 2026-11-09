#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.collect-acceptance.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Collect current full first-release proof into immutable scope-local candidate evidence without launching tasks, deleting resources or promoting a release.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
D = module("entity_smoke_acceptance_restore_owner", DIRECTORY / "restore-route.py")
A = module("entity_smoke_acceptance_retention", DIRECTORY / "acceptance-evidence.py")
CONTROL = module("entity_smoke_acceptance_control_custody", DIRECTORY / "acceptance-controls.py")
RESTART = module("entity_smoke_acceptance_restart_graph", DIRECTORY / "restart-route.py")
T, C = D.TASK, D.C
S = module("entity_smoke_acceptance_succession", C.ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py")
TARGET, SCOPE = "kanbien-core-platform", "entity-smoke"
EVIDENCE_ROOT = C.CONTRACT.parent.parent / "30-release-evidence"
SCHEMA = "deploy/entity-smoke-collected-acceptance/v1"
PROOF_CONTRACT = {"proof_type": "entity-smoke-complete-acceptance", "operation": "collect", "result_code": "ENTITY_SMOKE_COMPLETE_PROOF_COLLECTED"}
MAX_PACKET_BYTES = 4 * 1024 * 1024
CONTROLS = {"server-replacement", "initial-stop", "initial-restart", "credential-replacement", "snapshot", "restore-deployment", "restore-cleanup"}


class CollectionFailure(Exception):
    def __init__(self, code, item=None):
        super().__init__(code)
        self.code, self.item = code, item


def require(value, code, item=None):
    if not value: raise CollectionFailure(code, item)


def read_packet(path):
    C.RESOURCE.CONTROL.no_symlinks(path)
    try:
        with path.open("rb") as stream: raw = stream.read(MAX_PACKET_BYTES + 1)
        require(len(raw) <= MAX_PACKET_BYTES, "acceptance-collected-proof-too-large")
        value = json.loads(raw)
    except (OSError, ValueError, UnicodeError, RecursionError): raise CollectionFailure("acceptance-collected-proof-unavailable") from None
    return validate_packet(value)


class Provider(C.Provider):
    """The collector has no mutation capability, even if a caller asks for it."""
    def __call__(self, service, operation, **parameters):
        require((service, operation) in D.S.READS, "acceptance-provider-operation-prohibited")
        return self._invoke(service, operation, parameters)


def selected_args(args, stage, workload, operation, phase="operation"):
    digest = None if stage == "baseline" and operation in {"bootstrap", "apply", "grant-runtime", "permissions", "create", "observe-create", "lifecycle"} else args.expected_digest
    return SimpleNamespace(**{**vars(args), "proof_stage": stage, "workload": workload, "operation": operation, "phase": phase, "expected_digest": digest})


def task_context(value, args, provider, checked):
    if args.workload not in checked:
        checked[args.workload] = T.BINDING.inspect(provider, args.workload, value["parameters"], value["resources"], value["binding_snapshot"])
    context = {**value, "checked": checked[args.workload]}
    context["report"] = {"plan": {"preflight_label": A.preflight_label(value["binding"], args.proof_stage, args.workload, args.operation)}}
    return context


def task_proofs(value, cleanup, args, provider):
    root_binding = {**value["binding"], "record_digest": args.expected_digest}
    checked, result = {}, {}
    for name, (stage, workload, operations) in A.TASKS.items():
        operation = operations[0]
        selected = selected_args(args, stage, workload, operation)
        if name == "original-record" and not T.STEPS.path(value, selected).is_file():
            selected = selected_args(args, stage, workload, "observe-create")
        context = cleanup["reader"]["context"] if name == "restore-read" else task_context(value, selected, provider, checked)
        pair = {}
        for phase in (("operation",) if name == "credential-unready" else ("preflight", "operation")):
            current = SimpleNamespace(**{**vars(selected), "phase": phase})
            path = T.STEPS.path(context, current)
            if stage not in {"isolated-restore", "acceptance"}:
                relative = str(path.relative_to(value["cache"]))
                require(value["history"]["references"].get(relative) == C.digest_file(path), "acceptance-history-task-not-bound", name)
            pair[phase] = A.capture_task(T, context, current, provider, name, root_binding, historical=stage != "acceptance")
        result[name] = pair
    return result


def control_graph(name):
    require(isinstance(name, str) and name in CONTROLS, "acceptance-control-selection-invalid")
    if name == "initial-stop": return T.RECOVERY.STATE.STOP.graph()
    if name == "initial-restart": return RESTART.graph()
    if name.endswith("replacement"): return T.GRAPH.replacement(C.GATE, C.CONTRACT, "baseline" if name == "server-replacement" else "credential-recovery")
    if name == "snapshot": return D.S.graph()
    return D.graph("deploy" if name == "restore-deployment" else "cleanup")


def control_proof(name, receipt, binding, cache, artifact):
    """Project checked control facts, never retain a raw provider response."""
    if name == "initial-stop":
        facts = receipt["facts"]
        detail = {key: facts[key] for key in ("owned_service_desired_count", "owned_service_running_count", "owned_service_pending_count", "terminal_tasks", "other_service_configurations_sha256", "database_mutation", "observed_at")}
        detail.update(source_database_before_sha256=A.digest(facts["source_database_before"]), source_database_after_sha256=A.digest(facts["source_database_after"]))
        operation_id, plan = receipt["root"]["operation_id"], receipt["plan_sha256"]
    else:
        result = receipt["result"]
        require(result.get("status") == "completed", "acceptance-control-not-completed", name)
        detail = dict(result["facts"])
        if name == "initial-restart": detail["server"] = receipt["server"]
        if name == "restore-deployment":
            # Full raw resources are not needed in this public-safe projection;
            # their original checked hash and sole reader definition are retained.
            resources = detail.pop("resources")
            detail["reader_definition"] = resources["RestoreReaderTaskDefinition"]["physical_id"]
        if name in {"restore-deployment", "restore-cleanup"}: detail["observed_at"] = receipt["observed_at"]
        operation_id, plan = result["reservation"]["operation_id"], receipt["packet"]["plan_sha256"]
    controller = T.RECOVERY.STATE.STOP.artifact(C) if name in {"initial-stop", "initial-restart"} else artifact
    custody = CONTROL.capture(T, A, name, receipt, control_graph(name), binding, cache, controller)
    return {"schema": "deploy/entity-smoke-retained-control-proof/v1", "name": name, "plan_sha256": plan,
            "operation_id": operation_id, "source_receipt_sha256": A.digest(receipt), "source_receipt_document_sha256": A.document_digest(receipt),
            "realization_evidence_sha256": receipt["realization_evidence_sha256"], "facts": detail, "custody": custody}


def validate_control_facts(name, value):
    require(isinstance(name, str) and name in CONTROLS and isinstance(value, dict) and set(value) == {"schema", "name", "plan_sha256", "operation_id", "source_receipt_sha256", "source_receipt_document_sha256", "realization_evidence_sha256", "facts"}
            and value["schema"] == "deploy/entity-smoke-retained-control-proof/v1" and value["name"] == name and name in CONTROLS,
            "acceptance-control-envelope-invalid", name)
    require(isinstance(value["operation_id"], str) and re.fullmatch(r"es-[a-f0-9]{32}", value["operation_id"]), "acceptance-control-operation-invalid", name)
    for field in ("plan_sha256", "source_receipt_sha256", "source_receipt_document_sha256", "realization_evidence_sha256"):
        require(isinstance(value[field], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", value[field]), "acceptance-control-hash-invalid", name)
    fields = {
        "initial-stop": {"owned_service_desired_count", "owned_service_running_count", "owned_service_pending_count", "terminal_tasks", "other_service_configurations_sha256", "database_mutation", "observed_at", "source_database_before_sha256", "source_database_after_sha256"},
        "initial-restart": {"desired_count", "running_count", "tasks", "server"},
        "server-replacement": {"original_task", "successor_task", "predecessor_stopped_at", "successor_started_at"},
        "credential-replacement": {"original_task", "successor_task", "predecessor_stopped_at", "successor_started_at"},
        "snapshot": {"snapshot_arn", "source_resource_id", "snapshot_created_at"},
        "restore-deployment": {"stack_arn", "database_identifier", "restored_resource_id", "resources_sha256", "reader_definition", "observed_at"},
        "restore-cleanup": {"stack_arn", "database_identifier", "resources_sha256", "absence_observed", "source_mutation", "observed_at"},
    }
    facts = value["facts"]
    require(isinstance(facts, dict) and set(facts) == fields[name], "acceptance-control-facts-invalid", name)
    # The operation-specific source reader establishes truth. This independent
    # historical check closes nested shapes as well as the envelope; it cannot
    # turn projected facts or hashes alone into complete original gate custody.
    task_pattern = r"arn:aws:ecs:" + C.RESOURCE.REGION + ":" + C.RESOURCE.ACCOUNT + ":task/" + C.RESOURCE.CLUSTER + r"/[a-f0-9]{32}"
    definition_prefix = r"arn:aws:ecs:" + C.RESOURCE.REGION + ":" + C.RESOURCE.ACCOUNT + ":task-definition/kanbien-core-platform-entity-smoke-"
    def matches(item, pattern): return isinstance(item, str) and re.fullmatch(pattern, item) is not None
    def instant(item): return T.RUNNER.EVIDENCE.timestamp(item)
    hash_fields = {"other_service_configurations_sha256", "source_database_before_sha256", "source_database_after_sha256", "resources_sha256"}
    require(all(matches(facts[key], r"sha256:[a-f0-9]{64}") for key in hash_fields & set(facts)), "acceptance-control-hash-invalid", name)
    for key in ("observed_at", "snapshot_created_at", "predecessor_stopped_at", "successor_started_at"):
        if key in facts: instant(facts[key])
    if name == "initial-stop":
        require(all(type(facts[key]) is int and facts[key] == 0 for key in ("owned_service_desired_count", "owned_service_running_count", "owned_service_pending_count"))
                and facts["database_mutation"] is False and isinstance(facts["terminal_tasks"], dict) and len(facts["terminal_tasks"]) <= 100,
                "acceptance-initial-stop-invalid", name)
        for arn, actor in facts["terminal_tasks"].items():
            require(matches(arn, task_pattern) and isinstance(actor, dict) and set(actor) == {"definition", "workload", "state", "stopped_at"}
                    and isinstance(actor["workload"], str) and actor["workload"] in {"server", "migration", "administration", "verifier", "database-proof"}
                    and matches(actor["definition"], definition_prefix + re.escape(actor["workload"]) + r":[1-9][0-9]*")
                    and actor["state"] == "STOPPED", "acceptance-initial-stop-actor-invalid", name)
            require((instant(actor["stopped_at"]) - instant(facts["observed_at"])).total_seconds() <= 60, "acceptance-initial-stop-time-invalid", name)
    if name == "initial-restart":
        require(type(facts["desired_count"]) is int and facts["desired_count"] == 1 and type(facts["running_count"]) is int and facts["running_count"] == 1
                and isinstance(facts["server"], dict) and set(facts["server"]) == {"task", "created_at", "started_at"}
                and facts["tasks"] == [facts["server"]["task"]], "acceptance-initial-restart-invalid", name)
        server = facts["server"]
        require(matches(server["task"], task_pattern) and instant(server["started_at"]) >= instant(server["created_at"]), "acceptance-initial-restart-invalid", name)
    if name in {"server-replacement", "credential-replacement"}:
        require(matches(facts["original_task"], task_pattern) and matches(facts["successor_task"], task_pattern), "acceptance-replacement-task-invalid", name)
        require(facts["original_task"] != facts["successor_task"], "acceptance-replacement-not-distinct", name)
    if name == "snapshot":
        require(matches(facts["snapshot_arn"], r"arn:aws:rds:" + C.RESOURCE.REGION + ":" + C.RESOURCE.ACCOUNT + r":snapshot:kanbien-core-platform-entity-smoke-[a-f0-9]{24}")
                and matches(facts["source_resource_id"], r"db-[A-Za-z0-9]{1,64}"), "acceptance-snapshot-identity-invalid", name)
    if name in {"restore-deployment", "restore-cleanup"}:
        suffix = r"[a-f0-9]{24}"
        require(matches(facts["stack_arn"], r"arn:aws:cloudformation:" + C.RESOURCE.REGION + ":" + C.RESOURCE.ACCOUNT + r":stack/kanbien-core-platform-entity-smoke-restore-" + suffix + r"/[A-Za-z0-9-]{1,128}")
                and matches(facts["database_identifier"], r"kanbien-core-platform-entity-smoke-restore-[a-f0-9]{16}"), "acceptance-restore-identity-invalid", name)
    if name == "restore-deployment":
        require(matches(facts["restored_resource_id"], r"db-[A-Za-z0-9]{1,64}")
                and matches(facts["reader_definition"], definition_prefix + r"restore-reader:[1-9][0-9]*"), "acceptance-restored-reader-invalid", name)
    if name == "restore-cleanup":
        require(facts["absence_observed"] is True and facts["source_mutation"] is False, "acceptance-cleanup-not-proven", name)
    return value


def validate_control(name, value, binding):
    require(isinstance(value, dict) and "custody" in value, "acceptance-control-custody-required", name)
    validate_control_facts(name, {key: item for key, item in value.items() if key != "custody"})
    CONTROL.validate(A, value["custody"], binding, name=name, plan_sha256=value["plan_sha256"],
                     gate_sha256=value["realization_evidence_sha256"], operation_id=value["operation_id"])
    return value


def gather(args, provider):
    value = D.source(args, provider)
    policy = S.recovery_policy(EVIDENCE_ROOT, C.CONTRACT.parent / "declaration-contract.yml")
    require(policy["policy"] == "stop-own-scope-workloads-preserve-data" and policy["accepted_release_id"] == "none", "acceptance-subsequent-release-proof-required")
    cleanup = D.completed_cleanup(value, args, provider)
    tasks = task_proofs(value, cleanup, args, provider)
    final = tasks["final-read"]["operation"]
    A.fresh_final(final, cleanup["required_after"], C.now())
    history = value["history"]["prerequisites"]["packets"]
    source_controls = {"initial-stop": history["initial-stop"], "initial-restart": history["initial-restart"],
        "credential-replacement": history["credential-replacement"],
        "server-replacement": C.read_json(value["cache"] / "replacement-receipt.json"), "snapshot": value["snapshot"],
        "restore-deployment": cleanup["reader"]["deployed"], "restore-cleanup": cleanup["receipt"]}
    controls = {name: control_proof(name, receipt, {**value["binding"], "record_digest": args.expected_digest}, value["cache"], value["artifact"])
                for name, receipt in source_controls.items()}
    server = value["server"]
    service = C.RESOURCE.service(provider, server["definition"], 1)
    arns = C.RESOURCE.running_service_tasks(provider)
    require(len(arns) == 1 and service.get("runningCount") == 1 and service.get("pendingCount") == 0, "acceptance-current-runtime-not-confirmed")
    running = C.RESOURCE.task(provider, arns[0], server["definition"], value["binding"]["image_digest"])
    require(running.get("lastStatus") == "RUNNING" and running.get("healthStatus") == "HEALTHY", "acceptance-current-runtime-not-confirmed")
    custody = value["custody"]
    packet = {"schema": SCHEMA, "target": TARGET, "scope": SCOPE, "evidence_class": "live",
              "binding": {**value["binding"], "record_digest": args.expected_digest}, "controller_sha256": value["artifact"],
              "controller_basis": T.RECOVERY.STATE.STOP.artifact_basis(C),
              "package": {key: custody[key] for key in ("source_revision", "image_digest", "receipt_reference", "program_id", "package_contract_id")},
              "tasks": tasks, "controls": controls, "restored_binding": cleanup["reader"]["context"]["binding"],
              "runtime": {"task": running["taskArn"], "definition": server["definition"], "created_at": running["createdAt"], "started_at": running["startedAt"],
                          "source_resource_id": value["parameters"]["DatabaseResourceId"], "database_name": value["parameters"]["DatabaseName"], "observed_at": C.now()}}
    validate_packet(packet)
    # Final local/current binding rechecks cannot launch or stop anything.
    require(C.source_digest() == value["artifact"], "acceptance-source-changed-before-retention")
    C.ALIGN.source_preflight(custody)
    return packet, value["cache"]


def validate_packet(value, *, evidence_class="live"):
    require(isinstance(value, dict) and set(value) == {"schema", "target", "scope", "evidence_class", "binding", "controller_sha256", "controller_basis", "package", "tasks", "controls", "restored_binding", "runtime"}
            and value["schema"] == SCHEMA and value["target"] == TARGET and value["scope"] == SCOPE and value["evidence_class"] == evidence_class,
            "acceptance-collection-envelope-invalid")
    binding = C.RESOURCE.validate_binding(value["binding"])
    require(isinstance(value["controller_sha256"], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", value["controller_sha256"]), "acceptance-controller-source-invalid")
    package = value["package"]
    require(isinstance(package, dict) and set(package) == {"source_revision", "image_digest", "receipt_reference", "program_id", "package_contract_id"}
            and package["source_revision"] == binding["source_revision"] and package["image_digest"] == binding["image_digest"]
            and package["program_id"] == "kanbien-entity-smoke" and package["package_contract_id"] == "kanbien-entity-smoke-image"
            and isinstance(package["receipt_reference"], str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,512}", package["receipt_reference"]), "acceptance-package-binding-invalid")
    tasks, controls = value["tasks"], value["controls"]
    require(isinstance(tasks, dict) and set(tasks) == set(A.TASKS) and isinstance(controls, dict) and set(controls) == CONTROLS, "acceptance-proof-set-incomplete")
    operations = set()
    for name, pair in tasks.items():
        phases = {"operation"} if name == "credential-unready" else {"preflight", "operation"}
        require(isinstance(pair, dict) and set(pair) == phases, "acceptance-task-phases-incomplete", name)
        for phase, task in pair.items():
            require(isinstance(task, dict) and task.get("name") == name and task.get("phase") == phase and task.get("controller_sha256") == value["controller_sha256"], "acceptance-task-attribution-mismatch", name)
            A.validate_task(task, binding, expected_binding=value["restored_binding"] if name == "restore-read" else None)
            operation_id = task["packet"]["reservation"]["operation_id"]
            require(operation_id not in operations, "acceptance-task-reused-across-proofs", name)
            operations.add(operation_id)
            if phase == "operation" and name != "credential-unready":
                before = pair["preflight"]["packet"]
                admission = task["admission"]["preflight"]
                require(admission["reservation"] == before["reservation"] and admission["receipt"] == before["receipt"], "acceptance-original-preflight-mismatch", name)
    for name, proof in controls.items(): validate_control(name, proof, binding)
    runtime = value["runtime"]
    require(isinstance(runtime, dict) and set(runtime) == {"task", "definition", "created_at", "started_at", "source_resource_id", "database_name", "observed_at"}, "acceptance-runtime-facts-invalid")
    require(isinstance(runtime["database_name"], str) and re.fullmatch(r"[a-z][a-z0-9_]{0,62}", runtime["database_name"])
            and isinstance(runtime["source_resource_id"], str) and re.fullmatch(r"db-[A-Za-z0-9]+", runtime["source_resource_id"])
            and A.digest({"resource_id": runtime["source_resource_id"], "database": runtime["database_name"], "schema": "entity_smoke"}) == binding["dependency_incarnation_sha256"], "acceptance-source-incarnation-mismatch")
    snapshot = controls["snapshot"]["facts"]
    deployed, cleaned = controls["restore-deployment"]["facts"], controls["restore-cleanup"]["facts"]
    require(snapshot["source_resource_id"] == runtime["source_resource_id"] and deployed["restored_resource_id"] != runtime["source_resource_id"]
            and deployed["database_identifier"] == D.RESTORE.names(binding)[2]
            and all(cleaned[key] == deployed[key] for key in ("database_identifier", "stack_arn", "resources_sha256")), "acceptance-isolated-restore-mismatch")
    require(snapshot["snapshot_arn"] == "arn:aws:rds:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":snapshot:kanbien-core-platform-" + binding["proof_label"], "acceptance-source-snapshot-mismatch")
    child = value["restored_binding"]
    require(child["dependency_incarnation_sha256"] == A.digest({"resource_id": deployed["restored_resource_id"], "database": runtime["database_name"], "schema": "entity_smoke"})
            and tasks["restore-read"]["operation"]["packet"]["receipt"]["task"]["definition"] == deployed["reader_definition"], "acceptance-restored-reader-mismatch")
    timestamp = T.RUNNER.EVIDENCE.timestamp
    final = tasks["final-read"]["operation"]
    A.fresh_final(final, cleaned["observed_at"], runtime["observed_at"])
    require(runtime["task"] == controls["credential-replacement"]["facts"]["successor_task"]
            and timestamp(runtime["started_at"]) >= timestamp(runtime["created_at"])
            and timestamp(runtime["observed_at"]) >= timestamp(final["packet"]["receipt"]["collected_at"]), "acceptance-current-server-mismatch")
    CONTROL.validate_connections(A, value)
    return value


def retain(packet, cache, *, root=EVIDENCE_ROOT):
    validate_packet(packet)
    require(root == EVIDENCE_ROOT, "acceptance-evidence-root-invalid")
    require(len(T.RUNNER.CONTROL.canonical(packet)) + 1 <= MAX_PACKET_BYTES, "acceptance-collected-proof-too-large")
    C.RESOURCE.CONTROL.no_symlinks(root)
    artifact = A.immutable_json(root / "proof-receipts" / ("entity-smoke-" + A.digest(packet)[7:] + ".json"), packet)
    proofs = {"entity-smoke-complete-proof": {"path": str(artifact["path"].relative_to(root)), "sha256": artifact["sha256"]}}
    contracts = {"configuration_contract": {"path": str((C.CONTRACT.parent / "declaration-contract.yml").relative_to(C.ROOT)), "sha256": packet["binding"]["configuration_contract_sha256"]},
                 "permission_contract": {"path": str(C.DEPLOY.SOURCE.relative_to(C.ROOT)), "sha256": packet["binding"]["permission_contract_sha256"]}}
    identity = {"target": TARGET, "scope": SCOPE, "source_revision": packet["binding"]["source_revision"], "image_digest": packet["binding"]["image_digest"],
                **contracts, "proof_set_sha256": S.sha256_bytes(S.canonical(proofs))}
    candidate = {"schema": S.CANDIDATE_SCHEMA, "target": TARGET, "scope": SCOPE, "status": "verified", "evidence_class": "live",
                 "release": {"id": S.release_id(identity), **{key: item for key, item in identity.items() if key not in {"target", "scope"}}},
                 "proof": {"accepted_at": packet["runtime"]["observed_at"], "receipt_count": 1}, "proof_set": proofs}
    S.candidate_identity(candidate, root)
    target = root / S.CANDIDATE_DIRECTORY / (candidate["release"]["id"] + ".yml")
    C.RESOURCE.CONTROL.no_symlinks(target)
    S.immutable_write(target, S.rendered(candidate))
    marker = {"schema": "deploy/entity-smoke-acceptance-collection/v1", "binding": packet["binding"], "controller_sha256": packet["controller_sha256"],
              "candidate_record": str(target.relative_to(C.ROOT)), "candidate_sha256": C.digest_file(target), "proof_sha256": artifact["sha256"], "scope_acceptance": False, "current_readiness": False}
    A.immutable_json(cache / "acceptance-collection.json", marker)
    return marker


def collect(args, provider):
    cache = C.ROOT / ".cache/entity-smoke-live" / args.proof_label
    observation = cache / "acceptance-observation.json"
    C.RESOURCE.CONTROL.no_symlinks(observation)
    if observation.exists():
        packet = read_packet(observation)
        custody = C.ALIGN.read_receipt(args.receipt.absolute())
        C.ALIGN.source_preflight(custody)
        require(packet["controller_sha256"] == C.source_digest()
                and packet["binding"]["source_revision"] == custody["source_revision"] and packet["binding"]["image_digest"] == custody["image_digest"]
                and packet["binding"]["proof_label"] == args.proof_label and packet["binding"]["record_digest"] == args.expected_digest,
                "acceptance-original-collection-binding-mismatch")
        # Original captured observation only: no fresh provider claims or jobs.
        return retain(packet, cache), "retained"
    packet, selected_cache = gather(args, provider)
    require(selected_cache == cache, "acceptance-proof-cache-mismatch")
    A.fresh_final(packet["tasks"]["final-read"]["operation"], packet["controls"]["restore-cleanup"]["facts"]["observed_at"], C.now())
    require(len(T.RUNNER.CONTROL.canonical(packet)) + 1 <= MAX_PACKET_BYTES, "acceptance-collected-proof-too-large")
    # Reserve the immutable observation before any durable copy. A lost response
    # resumes these same bytes, never restamps old tasks or creates another proof.
    A.immutable_json(observation, packet)
    return retain(packet, cache), "collected"


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(CollectionFailure("acceptance-arguments-invalid"))
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--proof-label")
    parser.add_argument("--expected-digest")
    parser.add_argument("--write-candidate", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    if args.inputs is None:
        require(args.receipt is not None and isinstance(args.proof_label, str) and isinstance(args.expected_digest, str)
                and re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) and re.fullmatch(r"[a-f0-9]{64}", args.expected_digest), "acceptance-arguments-invalid")
    else: require(all(value is None for value in (args.receipt, args.proof_label, args.expected_digest)), "acceptance-arguments-invalid")
    require(args.write_candidate, "acceptance-candidate-write-approval-required")
    return args


def resolve_inputs(args):
    if args.inputs is None: return args
    owner = module("entity_smoke_acceptance_manifest", C.ROOT / "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py")
    route = owner.document(C.CONTRACT.parent / "acceptance-route-contract.yml")
    try: values = owner.input_values(args.inputs, route, root=C.ROOT)
    except ValueError as failure:
        code = str(failure)
        raise CollectionFailure(code if re.fullmatch(r"acceptance-inputs-[a-z0-9-]+", code) else "acceptance-inputs-not-confirmed") from None
    require(set(values) == {"candidate_receipt", "proof_label", "expected_digest"}, "acceptance-inputs-set-invalid")
    return parse(["--receipt", values["candidate_receipt"], "--proof-label", values["proof_label"], "--expected-digest", values["expected_digest"], "--write-candidate"])


def failure_details(failure, context=None):
    context = dict(context or {})
    known = (CollectionFailure, CONTROL.ControlFailure, A.EvidenceFailure, A.T.STEPS.StepFailure, A.C.GATE.ContractFailure,
             A.T.RUNNER.CONTROL.TaskFailure, A.C.RESOURCE.CONTROL.TaskFailure, C.RESOURCE.CONTROL.TaskFailure,
             A.T.RUNNER.EVIDENCE.EvidenceFailure, A.T.RUNNER.PREFLIGHT.PreflightFailure, A.T.RUNNER.UNREADY.UnreadyFailure,
             A.C.RESOURCE.ResourceFailure, A.C.RESOURCE.EVIDENCE.EvidenceFailure, A.T.BINDING.BindingFailure, A.C.InfrastructureFailure,
             C.RESOURCE.EVIDENCE.EvidenceFailure, T.RUNNER.UNREADY.UnreadyFailure, S.SuccessionFailure) + D.known()
    condition = str(failure) if isinstance(failure, S.SuccessionFailure) and re.fullmatch(r"release-succession-[a-z0-9-]{1,100}", str(failure)) else failure.code if isinstance(failure, known) and not isinstance(failure, S.SuccessionFailure) else "acceptance-boundary-not-confirmed"
    if isinstance(failure, (CollectionFailure, CONTROL.ControlFailure, A.EvidenceFailure)) and failure.item is not None: context["item"] = failure.item
    if isinstance(failure, CONTROL.ControlFailure) and failure.field is not None: context["field"] = failure.field
    if isinstance(failure, (T.BINDING.BindingFailure, A.T.BINDING.BindingFailure)):
        context.update(field=failure.field, item=failure.item, affected_workload=failure.workload)
    recovery_item = T.RECOVERY.failure_item(failure)
    if recovery_item is not None: context["item"] = recovery_item
    diagnostics = {}
    for owner in (T.RUNNER.EVIDENCE, C.RESOURCE.EVIDENCE, D.R.EVIDENCE, A.T.RUNNER.EVIDENCE, A.C.RESOURCE.EVIDENCE):
        if isinstance(failure, owner.EvidenceFailure):
            diagnostics = owner.failure_report(failure); break
    reference = failure.evidence_reference if isinstance(failure, (C.InfrastructureFailure, A.C.InfrastructureFailure)) else None
    return {"condition": condition, "context": context, **diagnostics, **({"evidence_reference": reference} if reference is not None else {})}


def main():
    provider, context = Provider(), {"stage": "acceptance-collection"}
    try:
        args = parse()
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": [], "proof_contract": PROOF_CONTRACT})); return 0
        args = resolve_inputs(args)
        context["proof_label_sha256"] = hashlib.sha256(args.proof_label.encode()).hexdigest()
        retained, verdict = collect(args, provider)
        print(json.dumps({"schema": "deploy/entity-smoke-acceptance-report/v1", "verdict": verdict, "code": PROOF_CONTRACT["result_code"] if verdict == "collected" else "ENTITY_SMOKE_COMPLETE_PROOF_RETAINED", "candidate_record": retained["candidate_record"], "scope_acceptance": False, "current_readiness": False})); return 0
    except Exception as failure:
        print(json.dumps({"schema": "deploy/entity-smoke-acceptance-report/v1", "target": TARGET, "scope": SCOPE, "verdict": "blocked",
                          **failure_details(failure, context), "effect": "no-provider-mutation-no-scope-promotion"}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
