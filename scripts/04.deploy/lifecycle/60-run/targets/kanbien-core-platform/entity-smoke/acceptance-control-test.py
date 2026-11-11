#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.acceptance-controls
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-11"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise closed final-stage parsing, read-only cleanup prerequisites and safe real task-main reporting with controlled source/cleanup protocols, not AWS acceptance.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from contextlib import redirect_stdout
import copy
from datetime import datetime, timedelta
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

if not __debug__: raise SystemExit("ENTITY_SMOKE_ACCEPTANCE_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
T = module("entity_smoke_acceptance_fixture_task", DIRECTORY / "task-route.py")
M = T.ACCEPTANCE
D = module("entity_smoke_acceptance_fixture_restore", DIRECTORY / "restore-route.py")
K = module("entity_smoke_acceptance_fixture_collection", DIRECTORY / "acceptance-route.py")


def fails(call, owner, code):
    try: call()
    except owner as failure:
        assert failure.code == code, (failure.code, code)
    else: raise AssertionError("Expected acceptance control rejection")


def collection_protocols():
    """Controlled projections only; never a positive live candidate or release."""
    label = "entity-smoke-" + "a" * 24
    stamp = "2026-11-09T02:30:00Z"
    task_prefix = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/"
    definition_prefix = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-"
    task, successor = task_prefix + "1" * 32, task_prefix + "2" * 32
    hash_value = "sha256:" + "d" * 64
    stack = "arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-core-platform-entity-smoke-restore-" + "a" * 24 + "/controlled-stack"
    identifier = "kanbien-core-platform-entity-smoke-restore-" + "a" * 16
    facts = {
        "initial-stop": {"owned_service_desired_count": 0, "owned_service_running_count": 0, "owned_service_pending_count": 0,
            "terminal_tasks": {task: {"definition": definition_prefix + "server:1", "workload": "server", "state": "STOPPED", "stopped_at": stamp}},
            "other_service_configurations_sha256": hash_value, "source_database_before_sha256": hash_value,
            "source_database_after_sha256": hash_value, "database_mutation": False, "observed_at": stamp},
        "initial-restart": {"desired_count": 1, "running_count": 1, "tasks": [successor],
            "server": {"task": successor, "created_at": stamp, "started_at": stamp}},
        "snapshot": {"snapshot_arn": "arn:aws:rds:eu-west-1:337159794548:snapshot:kanbien-core-platform-" + label,
            "source_resource_id": "db-CONTROLLEDSOURCE", "snapshot_created_at": stamp},
        "restore-deployment": {"stack_arn": stack, "database_identifier": identifier, "restored_resource_id": "db-CONTROLLEDCLONE",
            "resources_sha256": hash_value, "reader_definition": definition_prefix + "restore-reader:1", "observed_at": stamp},
        "restore-cleanup": {"stack_arn": stack, "database_identifier": identifier, "resources_sha256": hash_value,
            "absence_observed": True, "source_mutation": False, "observed_at": stamp},
    }
    for name in ("server-replacement", "credential-replacement"):
        facts[name] = {"original_task": task, "successor_task": successor, "predecessor_stopped_at": stamp, "successor_started_at": stamp}
    def envelope(name):
        return {"schema": "deploy/entity-smoke-retained-control-proof/v1", "name": name, "plan_sha256": hash_value,
            "operation_id": "es-" + "b" * 32, "source_receipt_sha256": hash_value, "source_receipt_document_sha256": hash_value, "realization_evidence_sha256": hash_value,
            "facts": copy.deepcopy(facts[name])}
    for name in sorted(K.CONTROLS):
        value = envelope(name)
        assert K.validate_control_facts(name, value) is value
        fails(lambda: K.validate_control(name, value, {}), K.CollectionFailure, "acceptance-control-custody-required")
        for field in value["facts"]:
            malformed = copy.deepcopy(value); malformed["facts"][field] = {"native": "private-control-canary"}
            try: K.validate_control_facts(name, malformed)
            except (K.CollectionFailure, K.T.RUNNER.EVIDENCE.EvidenceFailure) as failure:
                assert "private-control-canary" not in str(failure)
            else: raise AssertionError((name, field, "unchecked control field"))
        value["facts"]["native"] = "private-control-canary"
        fails(lambda: K.validate_control_facts(name, value), K.CollectionFailure, "acceptance-control-facts-invalid")
    stopped = envelope("initial-stop")
    stopped["facts"]["terminal_tasks"][task]["native"] = "private-control-canary"
    fails(lambda: K.validate_control_facts("initial-stop", stopped), K.CollectionFailure, "acceptance-initial-stop-actor-invalid")
    stopped = envelope("initial-stop"); stopped["facts"]["owned_service_running_count"] = False
    fails(lambda: K.validate_control_facts("initial-stop", stopped), K.CollectionFailure, "acceptance-initial-stop-invalid")
    for name in ("server-replacement", "credential-replacement"):
        value = envelope(name); value["facts"]["successor_task"] = task
        fails(lambda: K.validate_control_facts(name, value), K.CollectionFailure, "acceptance-replacement-not-distinct")
    fails(lambda: K.validate_control_facts([], {}), K.CollectionFailure, "acceptance-control-envelope-invalid")
    final = {"name": "final-read", "phase": "operation", "packet": {"receipt": {
        "task": {"created_at": stamp, "stopped_at": stamp}, "collected_at": stamp}}}
    origin = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    for seconds in (-60, 0, 900): K.A.fresh_final(final, stamp, (origin + timedelta(seconds=seconds)).isoformat())
    for seconds in (-61, 901):
        fails(lambda: K.A.fresh_final(final, stamp, (origin + timedelta(seconds=seconds)).isoformat()), K.A.EvidenceFailure, "acceptance-final-read-not-fresh")
    fails(lambda: K.A.fresh_final(final, (origin + timedelta(seconds=1)).isoformat(), stamp), K.A.EvidenceFailure, "acceptance-final-read-predates-cleanup")
    base = ["--receipt", "/tmp/acceptance-controlled-receipt.json", "--proof-label", label, "--expected-digest", "c" * 64, "--write-candidate"]
    assert K.parse(base).write_candidate
    fails(lambda: K.parse(base[:-1]), K.CollectionFailure, "acceptance-candidate-write-approval-required")
    fails(lambda: K.parse([*base, "--execute"]), K.CollectionFailure, "acceptance-arguments-invalid")
    provider = K.Provider(); invoked = []
    provider._invoke = lambda service, operation, parameters: invoked.append((service, operation)) or {}
    assert provider("ecs", "describe-tasks", tasks=[]) == {}
    for service, operation in (("ecs", "run-task"), ("ecs", "stop-task"), ("cloudformation", "delete-stack"), ("rds", "delete-db-instance"), ("secretsmanager", "get-secret-value")):
        fails(lambda: provider(service, operation), K.CollectionFailure, "acceptance-provider-operation-prohibited")
    assert invoked == [("ecs", "describe-tasks")]
    with tempfile.TemporaryDirectory(prefix="entity-smoke-collection-protocol-") as temporary:
        target = Path(temporary) / "retained.json"
        value = {"schema": "controlled-local-retention-not-live-proof", "value": 1}
        first = K.A.immutable_json(target, value); before = target.stat().st_mtime_ns
        assert K.A.immutable_json(target, value) == first and target.stat().st_mtime_ns == before
        fails(lambda: K.A.immutable_json(target, {**value, "value": 2}), K.A.EvidenceFailure, "acceptance-retained-proof-conflict")
        assert json.loads(target.read_bytes()) == value
        missing = Path(temporary) / "missing.json"
        fails(lambda: K.read_packet(missing), K.CollectionFailure, "acceptance-collected-proof-unavailable")
        linked = Path(temporary) / "linked.json"; linked.symlink_to(target)
        fails(lambda: K.A.immutable_json(linked, value), K.A.C.RESOURCE.CONTROL.TaskFailure, "attempt-path-invalid")
    original_collect, original_provider, original_argv = K.collect, K.Provider, sys.argv
    calls = []
    selected = {"failure": None}
    def blocked_collection(args, provider):
        calls.append(args.proof_label); raise selected["failure"]
    diagnostic = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.proof-failed", "definitionVersion": 1,
        "detail": {"operation": "read", "step": "read", "condition": "request-failed", "effect": "unknown"}}
    related = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.boundary-failed", "definitionVersion": 1,
        "detail": {"operation": "close", "effect": "not-assessed"}}
    try:
        K.collect = blocked_collection
        K.Provider = lambda: SimpleNamespace()
        sys.argv = ["acceptance-route.py", *base]
        selected["failure"] = K.T.BINDING.BindingFailure("task-binding-network-not-confirmed", "verifier", "network", "security-group")
        output = io.StringIO()
        with redirect_stdout(output): assert K.main() == 1
        report = json.loads(output.getvalue())
        assert report["condition"] == "task-binding-network-not-confirmed" and report["context"]["field"] == "network" and report["context"]["item"] == "security-group"
        for owner in (K.T.RUNNER.EVIDENCE, K.A.T.RUNNER.EVIDENCE, K.C.RESOURCE.EVIDENCE, K.D.R.EVIDENCE):
            selected["failure"] = owner.EvidenceFailure("task-unsuccessful-completion", diagnostic, [related])
            output = io.StringIO()
            with redirect_stdout(output): assert K.main() == 1
            report = json.loads(output.getvalue())
            assert report["condition"] == "task-unsuccessful-completion" and report["diagnostic"] == diagnostic and report["related_diagnostics"] == [related]
        selected["failure"] = K.CONTROL.ControlFailure("acceptance-control-original-gate-changed", "snapshot")
        output = io.StringIO()
        with redirect_stdout(output): assert K.main() == 1
        report = json.loads(output.getvalue())
        assert report["condition"] == "acceptance-control-original-gate-changed" and report["context"]["item"] == "snapshot"
        selected["failure"] = RuntimeError("private-provider-acceptance-canary")
        output = io.StringIO()
        with redirect_stdout(output): assert K.main() == 1
        assert json.loads(output.getvalue())["condition"] == "acceptance-boundary-not-confirmed" and "private-provider" not in output.getvalue()
        before = len(calls); sys.argv.append("--validate-arguments")
        output = io.StringIO()
        with redirect_stdout(output): assert K.main() == 0
        assert json.loads(output.getvalue())["verdict"] == "valid" and len(calls) == before
        assert all(item == label for item in calls), "failed collection is never replayed"
    finally: K.collect, K.Provider, sys.argv = original_collect, original_provider, original_argv


def archive_protocols(*, bootstrap=False, proof_label=None):
    """Actual local task collector and gate producer, controlled input only."""
    A, T = K.A, K.A.T
    C = T.C
    binding = {"source_revision": "b" * 40, "image_digest": "sha256:" + "c" * 64,
        "configuration_contract_sha256": "sha256:" + "d" * 64, "permission_contract_sha256": "sha256:" + "e" * 64,
        "dependency_incarnation_sha256": "sha256:" + "f" * 64, "proof_label": "entity-smoke-" + "a" * 24, "record_digest": "1" * 64}
    if proof_label is not None: binding["proof_label"] = proof_label
    stage, workload, operation, name = ("baseline", "administration", "bootstrap", "bootstrap") if bootstrap else ("acceptance", "verifier", "read", "final-read")
    label = A.preflight_label(binding, stage, workload, operation)
    request = {**{key: item for key, item in binding.items() if key not in {"proof_label", "record_digest"}},
        "workload": workload, "definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-" + workload + ":1",
        "proof_label": label, "security_group": "sg-" + "a" * 17, "subnets": ["subnet-" + "b" * 17], "deadline_seconds": 90,
        "environment": {"ENTITY_SMOKE_VERIFICATION_OPERATION": "ready", "ENTITY_SMOKE_PROOF_LABEL": label, "ENTITY_SMOKE_EXPECTED_SOURCE": binding["source_revision"]}}
    if bootstrap: request["environment"] = {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "preflight"}
    reservation = {"schema": "deploy/entity-smoke-task-reservation/v1", "operation_id": "es-" + "2" * 32,
        "request": request, "request_sha256": hashlib.sha256(T.RUNNER.CONTROL.canonical(request)).hexdigest(), "reserved_at": "2026-11-09T02:30:00Z"}
    stamp = "2026-11-09T02:30:01Z"
    task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "3" * 32,
        "taskDefinitionArn": request["definition"], "startedBy": reservation["operation_id"], "overrides": T.RUNNER.CONTROL.overrides(request),
        "lastStatus": "STOPPED", "launchType": "FARGATE", "createdAt": stamp, "startedAt": stamp, "stoppedAt": stamp,
        "containers": [{"name": "entity-smoke-" + workload, "imageDigest": binding["image_digest"], "exitCode": 0}]}
    result = {"schema": "deploy/entity-smoke-task-proof/v1", "verdict": "passed", "operation": "ready", "code": "ENTITY_SMOKE_HEALTHY",
        "source_revision": binding["source_revision"], "proof_label_sha256": hashlib.sha256(label.encode()).hexdigest(),
        "steps": ["release", "liveness", "readiness"], "checked_at": stamp}
    if bootstrap: result = {"verdict": "passed", "code": "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED", "operation": "preflight"}
    receipt = T.RUNNER.EVIDENCE.collect(task, reservation, {"events": [{"message": json.dumps(result)}]}, stamp)
    graph = T.GRAPH.contract(workload, C.GATE)
    artifact, plan = "sha256:" + "4" * 64, "sha256:" + "5" * 64
    expected = {row["id"]: artifact if row["id"] == T.GRAPH.CONTROLLER_SOURCE else binding["image_digest"] for row in graph["artifacts"]}
    packet = {"schema": "deploy/entity-smoke-task-step/v1", "plan_sha256": plan,
        "binding": {key: item for key, item in binding.items() if key != "record_digest"}, "reservation": reservation, "receipt": receipt}
    with tempfile.TemporaryDirectory(prefix="entity-smoke-task-archive-") as temporary:
        root = Path(temporary)
        book = C.GateBook(artifact, root, contract=graph, artifact_bindings=expected)
        for component in book.known: book.component(component)
        book.bind_plan(plan)
        for gate in C.GATE.GATE_ORDER[:7]: book.gate(gate)
        produced = book.validate("controlled-execution", 1)
        gate = C.read_json(produced)
        completion = {"schema": "deploy/entity-smoke-task-completion/v1", "step_sha256": A.document_digest(packet), "plan_sha256": plan,
            "realization_evidence": ".cache/entity-smoke-live/" + binding["proof_label"] + "/task-realization/" + produced.name,
            "realization_evidence_sha256": A.document_digest(gate)}
        value = {"schema": A.SCHEMA, "name": name, "stage": stage, "phase": "preflight", "requested_operation": operation,
            "controller_sha256": artifact, "collection_binding": binding, "graph": graph, "packet": packet, "completion": completion, "gate": gate, "admission": None}
        assert A.validate_task(value, binding) is value
        if bootstrap and proof_label == T.IMAGE_REPAIR.LABEL:
            original = "entity-smoke-" + hashlib.sha256((proof_label + ":administration:bootstrap:preflight").encode()).hexdigest()[:24]
            assert label != original
            # A perfectly formed successful receipt with the old identity must
            # still reject; collection must select the approved recovery task.
            invalid = copy.deepcopy(value)
            old_reservation = invalid["packet"]["reservation"]
            old_reservation["request"]["proof_label"] = original
            old_reservation["request_sha256"] = hashlib.sha256(T.RUNNER.CONTROL.canonical(old_reservation["request"])).hexdigest()
            old_task = copy.deepcopy(task)
            old_task["overrides"] = T.RUNNER.CONTROL.overrides(old_reservation["request"])
            invalid["packet"]["receipt"] = T.RUNNER.EVIDENCE.collect(old_task, old_reservation, {"events": [{"message": json.dumps(result)}]}, stamp)
            invalid["completion"]["step_sha256"] = A.document_digest(invalid["packet"])
            fails(lambda: A.validate_task(invalid, binding), A.EvidenceFailure, "acceptance-task-request-selection-mismatch")
        old_source = C.source_digest
        try:
            C.source_digest = lambda: (_ for _ in ()).throw(AssertionError("historical read must not inspect today's source"))
            assert A.validate_task(value, binding) is value
        finally: C.source_digest = old_source
        for field in ("phase", "requested_operation"):
            malformed = copy.deepcopy(value); malformed[field] = []
            fails(lambda: A.validate_task(malformed, binding), A.EvidenceFailure, "acceptance-task-selection-invalid")
        malformed = copy.deepcopy(value); malformed["completion"]["step_sha256"] = "sha256:" + "0" * 64
        fails(lambda: A.validate_task(malformed, binding), A.EvidenceFailure, "acceptance-task-completion-mismatch")
        # Tamper custody then recompute the outer hash: semantic gate membership,
        # not just a content hash, must still reject incomplete evidence.
        malformed = copy.deepcopy(value); malformed["gate"]["facts"]["gate_evidence"].pop()
        malformed["completion"]["realization_evidence_sha256"] = A.document_digest(malformed["gate"])
        fails(lambda: A.validate_task(malformed, binding), T.STEPS.StepFailure, "task-step-completion-gates-incomplete")
        malformed = copy.deepcopy(value); malformed["packet"]["receipt"]["native"] = "private-archive-canary"
        fails(lambda: A.validate_task(malformed, binding), T.RUNNER.EVIDENCE.EvidenceFailure, "task-retained-receipt-mismatch")


def control_custody_protocols():
    """Real local gates/storage; controlled plans, never AWS control receipts."""
    A, M, C = K.A, K.CONTROL, K.C
    binding = {"source_revision": "b" * 40, "image_digest": "sha256:" + "c" * 64,
        "configuration_contract_sha256": "sha256:" + "d" * 64, "permission_contract_sha256": "sha256:" + "e" * 64,
        "dependency_incarnation_sha256": "sha256:" + "f" * 64, "proof_label": "entity-smoke-" + "a" * 24, "record_digest": "1" * 64}
    hash_value, artifact = "sha256:" + "2" * 64, "sha256:" + "3" * 64
    common = {"target": "kanbien-core-platform", "scope": "entity-smoke", "binding": binding,
        "controller_sha256": artifact, "operator_sha256": hash_value, "package_custody_reference": "controlled-local-not-qualified"}
    false_flags = {"task_launch": False, "database_mutation": False, "automatic_retry": False}
    plans = {
        "initial-stop": {**common, "schema": "deploy/entity-smoke-failure-plan/v1", "binding": {k: v for k, v in binding.items() if k != "record_digest"},
            "account": "337159794548", "region": "eu-west-1", "purpose": "first-release-stop-preserve-control", "intent_sha256": hash_value, "policy_sha256": hash_value,
            "maximum_service_updates": 1, "maximum_task_stops": 0, "application_health_prerequisite": False, **false_flags,
            "permission_mutation": False, "resource_deletion": False, "independent_data_readback": False, "migration_history_readback": False},
        "initial-restart": {**common, "schema": "deploy/entity-smoke-initial-restart-plan/v1", "request_sha256": hash_value, "stop_sha256": hash_value,
            "original_read_sha256": hash_value, "policy_sha256": hash_value, "configuration_sha256": hash_value, "maximum_service_updates": 1, "desired_count": 1,
            **false_flags, "permission_mutation": False, "resource_deletion": False, "independent_data_readback": False, "migration_history_readback": False},
        "snapshot": {**common, "schema": "deploy/entity-smoke-snapshot-plan/v1", "request_sha256": hash_value, "history_sha256": hash_value,
            "configuration_sha256": hash_value, "maximum_snapshot_creates": 1, "task_launch": False, "source_data_mutation": False,
            "resource_deletion": False, "automatic_retry": False, "isolated_restore_proven": False},
        "restore-deployment": {**common, "schema": "deploy/entity-smoke-restore-plan/v1", "phase": "deploy", "request_sha256": hash_value,
            "snapshot_sha256": hash_value, "history_sha256": hash_value, "configuration_sha256": hash_value, "template_sha256": hash_value,
            "reader_sha256": None, "resource_count": 8, "task_launch": False, "source_mutation": False, "automatic_retry": False, "scope_acceptance": False},
    }
    plans["restore-cleanup"] = {**plans["restore-deployment"], "phase": "cleanup", "reader_sha256": hash_value}
    for name, stage in (("server-replacement", "baseline"), ("credential-replacement", "credential-recovery")):
        plans[name] = {**common, "schema": "deploy/entity-smoke-replacement-plan/v1", "proof_stage": stage, "request_sha256": hash_value,
            "baseline_read_sha256": hash_value, "prerequisites_sha256": hash_value, "configuration_sha256": hash_value,
            "maximum_task_stops": 1, **false_flags, "post_replacement_record_readback": False}
    original_root = C.ROOT
    with tempfile.TemporaryDirectory(prefix="entity-smoke-control-custody-") as temporary:
        root = Path(temporary); C.ROOT = root
        cache = root / ".cache/entity-smoke-live" / binding["proof_label"]
        try:
            for index, (name, original_plan) in enumerate(plans.items()):
                graph = K.control_graph(name)
                plan = {**original_plan, "graph_sha256": A.digest(graph)}
                # Existing failure/restart source composition is deliberately
                # distinct from the ordinary controller artifact in this fixture.
                if name in {"initial-stop", "initial-restart"}: plan["controller_sha256"] = "sha256:" + "4" * 64
                phase = {"initial-stop": "root", "initial-restart": "start-runtime", "server-replacement": "server-replacement",
                    "credential-replacement": "credential-replacement", "snapshot": "create-recovery-point", "restore-deployment": "execute-restore", "restore-cleanup": "delete-restore"}[name]
                reservation = {"operation_id": "es-" + format(index + 1, "032x"), "request_sha256": hash_value, "reserved_at": C.now(), "phase": phase}
                count = 8 if name.startswith("restore-") else 1
                operation = "delete" if name == "restore-cleanup" else "create" if name in {"snapshot", "restore-deployment"} else "update"
                book = C.GateBook(plan["controller_sha256"], cache / (M.SELECTIONS[name][1] + "-realization"), contract=graph,
                    artifact_bindings={graph["artifacts"][0]["id"]: plan["controller_sha256"]})
                for component in book.known: book.component(component)
                book.bind_plan(A.digest(plan))
                for gate in C.GATE.GATE_ORDER[:7]: book.gate(gate)
                path = book.validate("controlled-execution", count, operation_class=operation)
                value = {"schema": M.SCHEMA, "plan": plan, "graph": graph, "gate": C.read_json(path), "reservation": reservation}
                def checked(candidate):
                    return M.validate(A, candidate, binding, name=name, plan_sha256=A.digest(candidate["plan"]),
                        gate_sha256=A.document_digest(candidate["gate"]), operation_id=reservation["operation_id"])
                assert checked(value) is value
                packet = {"plan": plan, "plan_sha256": A.digest(plan)}
                submitted = {**reservation, "request_sha256": hash_value[7:]}
                receipt = {"packet": packet, "result": {"reservation": submitted},
                    "realization_evidence": str(path.relative_to(root)), "realization_evidence_sha256": C.digest_file(path)}
                if name == "initial-stop":
                    receipt.update(plan_sha256=packet["plan_sha256"], root={**reservation, "key": "root", "request": {"packet": packet}})
                captured = M.capture(SimpleNamespace(C=C), A, name, receipt, graph, binding, cache, plan["controller_sha256"])
                assert captured == value
                malformed = copy.deepcopy(value); malformed["plan"]["native"] = "private-control-plan-canary"
                fails(lambda: checked(malformed), M.ControlFailure, "acceptance-control-plan-fields-invalid")
                malformed = copy.deepcopy(value); malformed["plan"]["task_launch"] = True
                fails(lambda: checked(malformed), M.ControlFailure, "acceptance-control-plan-effect-invalid")
                malformed = copy.deepcopy(value); malformed["plan"]["binding"]["source_revision"] = "0" * 40
                fails(lambda: checked(malformed), M.ControlFailure, "acceptance-control-plan-binding-mismatch")
                malformed = copy.deepcopy(value); malformed["gate"]["change_summary"]["operation_counts"][operation] = count + 1
                fails(lambda: checked(malformed), A.EvidenceFailure, "acceptance-control-change-summary-invalid")
                malformed = copy.deepcopy(value); malformed["gate"]["change_summary"]["operation_counts"][operation] = True
                fails(lambda: checked(malformed), A.EvidenceFailure, "acceptance-control-change-summary-invalid")
                malformed = copy.deepcopy(value); malformed["graph"]["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-route.py"
                malformed["plan"]["graph_sha256"] = A.digest(malformed["graph"])
                fails(lambda: checked(malformed), M.ControlFailure, "acceptance-control-graph-binding-mismatch")
                malformed = copy.deepcopy(value); malformed["gate"]["facts"]["gate_evidence"].pop()
                fails(lambda: checked(malformed), A.T.STEPS.StepFailure, "task-step-completion-gates-incomplete")
                malformed = copy.deepcopy(value); malformed["reservation"]["operation_id"] = "es-" + "0" * 32
                fails(lambda: checked(malformed), M.ControlFailure, "acceptance-control-reservation-mismatch")
                malformed = copy.deepcopy(value)
                completed_at = datetime.fromisoformat(value["gate"]["facts"]["gate_evidence"][-1]["timestamp"].replace("Z", "+00:00"))
                malformed["reservation"]["reserved_at"] = (completed_at + timedelta(seconds=61)).isoformat()
                fails(lambda: checked(malformed), M.ControlFailure, "acceptance-control-gate-predates-reservation")
                old_gate = copy.deepcopy(receipt); old_gate["realization_evidence_sha256"] = "sha256:" + "0" * 64
                fails(lambda: M.capture(SimpleNamespace(C=C), A, name, old_gate, graph, binding, cache, plan["controller_sha256"]), M.ControlFailure, "acceptance-control-original-gate-changed")
                fails(lambda: M.capture(SimpleNamespace(C=C), A, name, receipt, graph, binding, cache, "sha256:" + "0" * 64), M.ControlFailure, "acceptance-control-current-source-mismatch")
                outside = copy.deepcopy(receipt); outside["realization_evidence"] = ".cache/other/controlled-execution-" + "0" * 32 + ".json"
                fails(lambda: M.capture(SimpleNamespace(C=C), A, name, outside, graph, binding, cache, plan["controller_sha256"]), M.ControlFailure, "acceptance-control-gate-reference-invalid")
                before = path.read_bytes()
                # Same original bytes, no filesystem/provider effect on reread.
                assert checked(value) is value and path.read_bytes() == before
                old_source, old_archive_source = C.source_digest, A.C.source_digest
                try:
                    C.source_digest = lambda: (_ for _ in ()).throw(AssertionError("Historical control must not inspect today's source"))
                    A.C.source_digest = C.source_digest
                    assert checked(value) is value
                finally: C.source_digest, A.C.source_digest = old_source, old_archive_source
                if name == "snapshot":
                    outer = {"schema": "deploy/entity-smoke-retained-control-proof/v1", "name": name, "plan_sha256": A.digest(plan),
                        "operation_id": reservation["operation_id"], "source_receipt_sha256": hash_value, "source_receipt_document_sha256": hash_value, "realization_evidence_sha256": A.document_digest(value["gate"]),
                        "facts": {"snapshot_arn": "arn:aws:rds:eu-west-1:337159794548:snapshot:kanbien-core-platform-" + binding["proof_label"],
                                  "source_resource_id": "db-CONTROLLEDSOURCE", "snapshot_created_at": C.now()}, "custody": value}
                    assert K.validate_control(name, outer, binding) is outer
            assert set(plans) == set(K.CONTROLS), "all seven original control archive paths are exercised"
        finally: C.ROOT = original_root


def run():
    collection_protocols()
    archive_protocols()
    archive_protocols(bootstrap=True)
    archive_protocols(bootstrap=True, proof_label=K.T.IMAGE_REPAIR.LABEL)
    control_custody_protocols()
    base = ["--receipt", "/tmp/acceptance-controlled-receipt.json", "--proof-label", "entity-smoke-" + "a" * 24,
            "--workload", "verifier", "--operation", "read", "--proof-stage", "acceptance", "--expected-digest", "b" * 64]
    args = T.parse(base)
    assert M.supported(args) and T.STEPS.stage(args) == "acceptance"
    assert T.STEPS.key(args) not in {T.STEPS.key(SimpleNamespace(**{**vars(args), "proof_stage": stage}))
                                   for stage in ("baseline", "server-replacement", "initial-recovery", "credential-recovery")}
    fails(lambda: T.parse(base[:-2]), T.TaskRouteFailure, "task-original-record-digest-required")
    for operation in ("ready", "unready", "create", "cleanup", "lifecycle"):
        invalid = list(base); invalid[invalid.index("--operation") + 1] = operation
        fails(lambda: T.parse(invalid), T.STEPS.StepFailure, "task-proof-stage-not-supported")
    fails(lambda: T.parse([*base, "--execute"]), T.TaskRouteFailure, "task-approved-plan-required")
    provider = T.Provider()
    invoked = []
    provider._invoke = lambda service, operation, parameters: invoked.append((service, operation)) or {}
    for operation in ("describe-db-snapshots", "list-tags-for-resource"):
        assert provider("rds", operation) == {}
    assert invoked == [("rds", "describe-db-snapshots"), ("rds", "list-tags-for-resource")]
    for service, operation in (("cloudformation", "delete-stack"), ("rds", "create-db-snapshot"), ("rds", "delete-db-instance"), ("secretsmanager", "get-secret-value")):
        fails(lambda: provider(service, operation), T.TaskRouteFailure, "task-provider-operation-prohibited")
    assert len(invoked) == 2, "new snapshot observation grants no mutation or secret-value read"
    # Approved declaration is not a general deletion or execution capability.
    cleanup_graph = D.graph("cleanup")
    assert cleanup_graph["change_shape"]["allowed_operation_classes"] == ["delete"]
    unbounded = copy.deepcopy(cleanup_graph)
    unbounded["change_shape"].pop("disposable_restore_cleanup")
    fails(lambda: D.C.GATE.validate_contract(unbounded), D.C.GATE.ContractFailure, "change-shape-invalid")
    with tempfile.TemporaryDirectory(prefix="entity-smoke-acceptance-controls-") as temporary:
        cache = Path(temporary)
        provider_calls = []
        def no_provider(*values, **named):
            provider_calls.append((values, named)); raise AssertionError("No provider call is permitted")
        fails(lambda: D.completed_cleanup({"cache": cache}, args, no_provider), D.RestoreFailure, "restore-cleanup-completion-required")
        assert provider_calls == [] and list(cache.iterdir()) == []

        context = {"cache": cache, "binding": {"fixture": "checked-binding"}, "artifact": "sha256:" + "c" * 64,
                   "parameters": {"fixture": "checked-parameters"}, "resources": {"fixture": "checked-resources"}}
        selected = copy.deepcopy(context)
        completed = {"required_after": "2026-11-09T02:30:00Z", "reader": {"step": {"fixture": "retained-original-read"}}}
        source_calls, cleanup_calls, terminal_calls, reservation_reads = [], [], [], []
        class SourceFailure(Exception):
            def __init__(self, code): self.code = code
        fault = {"value": None}
        def source(values, provider, **flags):
            source_calls.append((values.proof_stage, flags))
            if fault["value"] is not None: raise fault["value"]
            return copy.deepcopy(selected)
        def cleanup(value, values, provider):
            cleanup_calls.append(values.expected_digest)
            return copy.deepcopy(completed)
        owner = SimpleNamespace(C=D.C, TASK=D.TASK, R=D.R, source=source, completed_cleanup=cleanup,
                                known=lambda: (SourceFailure, D.C.InfrastructureFailure, D.TASK.BINDING.BindingFailure, D.TASK.RUNNER.EVIDENCE.EvidenceFailure))
        class ReadStore:
            def read(self, key, request): reservation_reads.append((key, request)); return None
        route = SimpleNamespace(
            C=SimpleNamespace(RESOURCE=SimpleNamespace(ResourceMissing=T.C.RESOURCE.ResourceMissing,
                require_other_tasks_terminal=lambda provider, **kw: terminal_calls.append(kw)),
                InfrastructureFailure=T.C.InfrastructureFailure, digest_file=lambda path: "sha256:" + "d" * 64,
                DEPLOY=SimpleNamespace(fingerprint=lambda value: "sha256:" + "e" * 64)),
            STEPS=SimpleNamespace(request=lambda route, context, args: {"fixture": "exact-final-request"}, key=T.STEPS.key),
            RUNNER=SimpleNamespace(CONTROL=SimpleNamespace(AttemptStore=lambda path: ReadStore())),
        )
        original_owner = M.restore_owner
        try:
            M.restore_owner = lambda: owner
            proof = M.prerequisites(route, context, args, no_provider)
            assert proof["required_after"] == completed["required_after"]
            assert set(proof["packets"]) == {"credential-history-sha256", "source-snapshot-sha256", "restore-cleanup-sha256", "restore-reader-sha256"}
            assert source_calls == [("acceptance", {"source_proof": False, "require_terminal_jobs": False})]
            assert cleanup_calls == [args.expected_digest] and terminal_calls == [{"reservation": None}]
            assert reservation_reads == [(T.STEPS.key(args), {"fixture": "exact-final-request"})]
            assert provider_calls == [], "controlled prerequisites cannot reach AWS"
            for key in ("binding", "artifact", "parameters", "resources"):
                before_cleanup = len(cleanup_calls)
                previous = selected[key]; selected[key] = {"wrong": True}
                fails(lambda: M.prerequisites(route, context, args, no_provider), M.AcceptanceFailure, "acceptance-current-binding-mismatch")
                assert len(cleanup_calls) == before_cleanup
                selected[key] = previous
            for code in ("restore-cleanup-completion-required", "restore-cleanup-order-invalid", "restore-cleanup-current-absence-not-confirmed"):
                fault["value"] = SourceFailure(code)
                fails(lambda: M.prerequisites(route, context, args, no_provider), M.AcceptanceFailure, code)
            fault["value"] = D.TASK.BINDING.BindingFailure("task-binding-network-not-confirmed", "verifier", "network", "security-group")
            try: M.prerequisites(route, context, args, no_provider)
            except M.AcceptanceFailure as failure:
                assert failure.context == {"field": "network", "item": "security-group", "affected_workload": "verifier"}
            else: raise AssertionError("Expected preserved binding context")
            # Exercise the actual task-main exception projection, not just a
            # manufactured output record. Its source/cleanup producers are doubles.
            original_plan, original_provider, original_argv = T.plan, T.Provider, sys.argv
            class OfflineProvider:
                effect = "not-started"
                def __call__(self, *values, **named): raise AssertionError("Unexpected AWS access")
            try:
                T.Provider = OfflineProvider
                T.plan = lambda values, provider: M.prerequisites(route, context, values, provider)
                sys.argv = ["task-route.py", *base]
                output = io.StringIO()
                with redirect_stdout(output): status = T.main()
                report = json.loads(output.getvalue())
                assert status == 1 and report["condition"] == "task-binding-network-not-confirmed"
                assert report["context"]["proof_stage"] == "acceptance"
                assert report["context"]["field"] == "network" and report["context"]["item"] == "security-group"
                assert report["effect"] == "not-started"
                fault["value"] = RuntimeError("synthetic-private-acceptance-provider-canary")
                output = io.StringIO()
                with redirect_stdout(output): status = T.main()
                assert status == 1 and json.loads(output.getvalue())["condition"] == "task-boundary-not-confirmed"
                assert "synthetic-private" not in output.getvalue()
            finally:
                T.plan, T.Provider, sys.argv = original_plan, original_provider, original_argv
        finally: M.restore_owner = original_owner
        # Check the actual registered wrapper's membership and failure exits.
        command_directory = cache / "commands"
        command_directory.mkdir()
        stub = command_directory / "python3"
        stub.write_text("#!" + sys.executable + "\n" + '''import json, os, sys
with open(os.environ["ENTITY_SMOKE_FIXTURE_TRACE"], "a", encoding="utf-8") as trace:
    trace.write(json.dumps(sys.argv[1:]) + "\\n")
index = "first" if sys.argv[-1].endswith("/restore-control-test.py") else "second" if sys.argv[-1].endswith("/acceptance-control-test.py") else "third"
sys.exit(37 if os.environ["ENTITY_SMOKE_FIXTURE_FAIL"] == index else 0)
''')
        stub.chmod(0o700)
        expected = [["-B", "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/" + name]
                    for name in ("restore-control-test.py", "acceptance-control-test.py", "acceptance-route-test.py")]
        for mode, status, children in (("none", 0, expected), ("first", 37, expected[:1]), ("second", 37, expected[:2]), ("third", 37, expected)):
            trace = cache / (mode + ".jsonl")
            checked = subprocess.run(["bash", str(DIRECTORY / "acceptance-control-test.sh")], cwd=T.C.ROOT,
                env={**os.environ, "PATH": str(command_directory) + os.pathsep + os.environ.get("PATH", ""),
                     "ENTITY_SMOKE_FIXTURE_TRACE": str(trace), "ENTITY_SMOKE_FIXTURE_FAIL": mode},
                capture_output=True, text=True, timeout=20)
            assert checked.returncode == status
            assert [json.loads(line) for line in trace.read_text().splitlines()] == children
    print(json.dumps({"schema": "deploy/entity-smoke-acceptance-control-fixture/v1", "verdict": "passed", "provider_observation": False,
                      "cases": ["closed-control-projections-all-seven", "malformed-control-fields-and-nested-actors", "strict-counts-and-distinct-replacements", "final-freshness-boundaries-and-cleanup-order", "explicit-candidate-write-and-closed-parser", "collector-has-no-mutation-capability", "immutable-byte-retention-and-conflict", "collector-reasons-companions-canary-and-no-replay", "offline-arguments-no-collection", "actual-local-task-and-gate-producer-archive", "historical-archive-no-current-source-read", "archive-selection-hash-gate-and-native-tampering", "closed-final-read-stage", "stage-specific-attempt-key", "digest-required", "concrete-launch-approval-required", "closed-read-only-snapshot-capability", "bounded-cleanup-only-default-delete-denied",
                                "missing-cleanup-before-io", "controlled-complete-prerequisites", "four-binding-mismatches", "finite-cleanup-reasons", "binding-context-at-real-main", "unknown-provider-canary-excluded", "wrapper-exact-membership-and-all-three-child-failures",
                                "seven-original-control-plan-and-gate-archives", "fact-only-projection-not-full-proof", "closed-control-plan-fields-effects-and-bindings", "control-gate-semantic-and-bool-count-tampering", "selected-control-source-and-reservation-binding", "original-gate-byte-hash-at-capture", "historical-control-no-current-source-read", "control-custody-condition-at-real-main"]}))


if __name__ == "__main__": run()
