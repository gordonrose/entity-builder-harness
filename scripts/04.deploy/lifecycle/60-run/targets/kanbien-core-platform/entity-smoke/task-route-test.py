#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.task-route
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual selected-operation graphs and public planning with controlled prerequisites plus real offline CLI rejection, without qualification or AWS effects.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
from datetime import datetime, timezone
import hashlib
from contextlib import redirect_stdout
import importlib.util
import json
import io
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

if not __debug__: raise SystemExit("ENTITY_SMOKE_TASK_ROUTE_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
M = module("entity_smoke_task_route_fixture", DIRECTORY / "task-route.py")
BF = module("entity_smoke_task_binding_responses", DIRECTORY / "task-binding-test.py")
F = BF.F
REAL_ROOT, CANARY = M.C.ROOT, BF.CANARY


class Provider(F.Provider):
    def __init__(self):
        super().__init__()
        self.effect = "not-started"
        self.resources = [{"LogicalResourceId": name, "ResourceType": row["type"], "PhysicalResourceId": row["physical_id"], "ResourceStatus": "CREATE_COMPLETE"} for name, row in BF.RESOURCES.items()]
        self.bindings = {name: BF.Provider(name) for name in M.BINDING.WORKLOADS}
        self.observed = []
        self.remote, self.results, self.lost_next = {}, {}, False
        self.next_task_number = 101
        self.missing_create_result, self.created_record = False, False
        self.server_states, self.replacement_lost = None, False
        self.history_applied = True
    def __call__(self, service, operation, **parameters):
        self.observed.append((service, operation, parameters))
        if self.server_states is not None:
            if operation == "describe-tasks" and all(arn in self.server_states for arn in parameters["tasks"]):
                return {"tasks": [copy.deepcopy(self.server_states[arn]) for arn in parameters["tasks"]], "failures": []}
            if operation == "list-tasks" and "serviceName" in parameters:
                return {"taskArns": [arn for arn, row in self.server_states.items() if row["lastStatus"] == "RUNNING"]}
            if operation == "stop-task":
                original = self.server_states[parameters["task"]]
                observed_at = datetime.now(timezone.utc).isoformat()
                original.update(lastStatus="STOPPED", stoppedAt=observed_at, stoppedReason=parameters["reason"])
                successor = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "4" * 32
                self.server_states[successor] = {**copy.deepcopy(original), "taskArn": successor, "lastStatus": "RUNNING", "createdAt": observed_at, "startedAt": observed_at}
                self.server_states[successor].pop("stoppedAt"); self.server_states[successor].pop("stoppedReason")
                if self.replacement_lost: raise OSError(CANARY)
                return {}
        if operation == "run-task":
            workload = parameters["taskDefinition"].split("entity-smoke-")[1].split(":")[0]
            environment = {row["name"]: row["value"] for row in parameters["overrides"]["containerOverrides"][0]["environment"]}
            selected = environment[M.RUNNER.CONTROL.OPERATIONS[workload][0]]
            identifier = format(self.next_task_number, "032x")
            self.next_task_number += 1
            arn = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + identifier
            observed_at = datetime.now(timezone.utc).isoformat()
            task = {"taskArn": arn, "taskDefinitionArn": parameters["taskDefinition"], "startedBy": parameters["startedBy"], "overrides": parameters["overrides"],
                    "lastStatus": "STOPPED", "launchType": "FARGATE", "createdAt": observed_at, "startedAt": observed_at, "stoppedAt": observed_at,
                    "containers": [{"name": "entity-smoke-" + workload, "imageDigest": F.BINDING["image_digest"], "exitCode": 0}]}
            if selected == "preflight":
                result = {"verdict": "passed", "code": "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED"}
                if workload == "administration": result["operation"] = "preflight"
            elif workload == "administration":
                result = {"verdict": "passed", "code": "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED", "operation": selected}
                if selected == "observe-migration-state": result["code"] = "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED" if self.history_applied else "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED"
            elif workload == "migration": result = {"verdict": "passed", "code": "ENTITY_SMOKE_MIGRATION_APPLIED"}
            elif workload == "restore-reader":
                assert selected == "restore-read"
                result = {"schema": "deploy/entity-smoke-database-proof/v1", "verdict": "passed", "operation": selected, "code": "ENTITY_SMOKE_RESTORED_RECORD_RETRIEVED",
                          "proof_label_sha256": hashlib.sha256(environment["ENTITY_SMOKE_PROOF_LABEL"].encode()).hexdigest(), "steps": ["identity", "read"], "record_digest": "1" * 64, "checked_at": observed_at}
            elif workload == "database-proof":
                assert selected in {"permissions", "collision"}
                result = {"schema": "deploy/entity-smoke-database-proof/v1", "verdict": "passed", "operation": selected, "code": "ENTITY_SMOKE_EFFECTIVE_PRIVILEGES_PROVEN",
                          "proof_label_sha256": hashlib.sha256(environment["ENTITY_SMOKE_PROOF_LABEL"].encode()).hexdigest(),
                          "steps": ["identity", "delete", "truncate", "create-table", "alter-table", "drop-table", "history-write"], "checked_at": observed_at}
                if selected == "collision": result.update(code="ENTITY_SMOKE_IDENTIFIER_COLLISION_PROVEN", steps=["identity", "read", "collision", "read"], record_digest="1" * 64)
            else:
                assert workload == "verifier"
                codes = {"ready": "ENTITY_SMOKE_HEALTHY", "unready": "ENTITY_SMOKE_LIVE_NOT_READY", "create": "ENTITY_SMOKE_RECORD_CREATED", "observe-create": "ENTITY_SMOKE_RECORD_RECONCILED", "lifecycle": "ENTITY_SMOKE_LIFECYCLE_PROVEN", "read": "ENTITY_SMOKE_RECORD_RETRIEVED"}
                steps = ["release", "liveness", "readiness"]
                if selected == "create": steps += ["create", "read"]; self.created_record = True
                if selected in {"read", "observe-create"}: steps += ["read"]; assert self.created_record
                if selected == "lifecycle": steps += ["create", "read", "update", "list", "archive", "restore-archive", "delete", "restore-deleted", "purge-eligibility"]
                result = {"schema": "deploy/entity-smoke-task-proof/v1", "verdict": "passed", "operation": selected, "code": codes[selected], "source_revision": F.BINDING["source_revision"],
                          "proof_label_sha256": hashlib.sha256(environment["ENTITY_SMOKE_PROOF_LABEL"].encode()).hexdigest(), "steps": steps, "checked_at": observed_at}
                if selected not in {"ready", "unready"}: result["record_digest"] = ("2" if selected == "lifecycle" else "1") * 64
                if selected == "create" and self.missing_create_result: result = None
            self.remote[arn], self.results[identifier] = task, result
            if self.lost_next:
                self.lost_next = False
                raise OSError(CANARY)
            return {"tasks": [copy.deepcopy(task)]}
        if operation == "describe-tasks" and all(arn in self.remote for arn in parameters["tasks"]): return {"tasks": [copy.deepcopy(self.remote[arn]) for arn in parameters["tasks"]], "failures": []}
        if operation == "list-tasks" and "family" in parameters: return {"taskArns": [arn for arn, task in self.remote.items() if parameters["desiredStatus"] == "STOPPED" and task["taskDefinitionArn"].split("/")[1].split(":")[0] == parameters["family"]]}
        if operation == "get-log-events":
            result = self.results[parameters["logStreamName"].split("/")[-1]]
            return {"events": [] if "nextToken" in parameters or result is None else [{"message": json.dumps(result)}], "nextForwardToken": "complete"}
        if operation == "get-caller-identity": return {"Account": M.C.ALIGN.ACCOUNT, "Arn": "arn:aws:sts::337159794548:assumed-role/ApprovedOperator/fixture"}
        if operation == "get-role" and parameters["RoleName"] == "ApprovedOperator": return {"Role": {"RoleName": "ApprovedOperator", "Arn": "arn:aws:iam::337159794548:role/ApprovedOperator"}}
        if operation == "simulate-principal-policy": return {"IsTruncated": False, "EvaluationResults": [{"EvalActionName": parameters["ActionNames"][0], "EvalResourceName": arn, "EvalDecision": "allowed"} for arn in parameters["ResourceArns"]]}
        if operation == "describe-task-definition":
            name = next(name for name, value in self.bindings.items() if value.task["taskDefinitionArn"] == parameters["taskDefinition"])
            return self.bindings[name](service, operation, **parameters)
        if (service, operation) in {("iam", "get-role"), ("iam", "list-role-policies"), ("iam", "list-attached-role-policies"), ("iam", "get-role-policy"), ("ec2", "describe-security-groups")}:
            return self.bindings["administration"](service, operation, **parameters)
        try: return super().__call__(service, operation, **parameters)
        except F.R.ResourceMissing: raise M.C.RESOURCE.ResourceMissing() from None


def fails(call, code):
    try: call()
    except (M.TaskRouteFailure, M.BINDING.BindingFailure, M.C.InfrastructureFailure, M.C.RESOURCE.ResourceFailure, M.C.GATE.ContractFailure,
            M.STEPS.StepFailure, M.FEATURE.FeatureStepFailure, M.RUNNER.CONTROL.TaskFailure, M.RUNNER.RunnerFailure, M.RUNNER.EVIDENCE.EvidenceFailure, M.RUNNER.PREFLIGHT.PreflightFailure) as failure:
        assert failure.code == code, (failure.code, code)
        return failure
    else: raise AssertionError("expected bounded task-plan rejection")


def run():
    original = {name: getattr(M.C, name) for name in ("ROOT", "source_digest", "digest_file", "local_checks")}
    old_read, old_source, old_inspect = M.C.ALIGN.read_receipt, M.C.ALIGN.source_preflight, M.C.ALIGN.inspect
    with tempfile.TemporaryDirectory(prefix="entity-smoke-task-plan-") as temporary:
        root = Path(temporary); M.C.ROOT = root
        actual_digest = M.C.digest_file
        M.C.digest_file = lambda path: actual_digest(path) if path.is_file() else "sha256:" + "c" * 64
        M.C.source_digest = lambda: "sha256:" + "f" * 64
        calls = []
        M.C.local_checks = lambda: calls.append("local-proof-double")
        receipt = {"source_revision": F.BINDING["source_revision"], "image_digest": F.BINDING["image_digest"], "receipt_reference": "github-actions-run:controlled-not-qualification"}
        M.C.ALIGN.read_receipt = lambda path: receipt
        M.C.ALIGN.source_preflight = lambda selected: calls.append("clean-source-custody-double")
        alignment = {"dependency_incarnation_sha256": F.BINDING["dependency_incarnation_sha256"]}
        M.C.ALIGN.inspect = lambda provider, selected, checked: (alignment, copy.deepcopy(F.PARAMETERS), "private-subnet-group")
        binding = {**M.C.binding_for(receipt, alignment), "proof_label": F.BINDING["proof_label"]}
        provider = Provider()
        cache = root / ".cache/entity-smoke-live" / binding["proof_label"]
        store = M.C.RESOURCE.ResourceStore(cache / "attempts")
        reviewed = M.C.DEPLOY.prepare(provider, store, binding, F.PARAMETERS)
        result = M.C.DEPLOY.execute(provider, store, binding, F.PARAMETERS, reviewed["facts"]["change_set_arn"], reviewed["facts"]["stack_arn"])
        assert result["status"] == "completed"
        M.C.RESOURCE.write_exclusive(cache / "receipts/create.json", {"schema": "deploy/entity-smoke-infrastructure-receipt/v1", "binding": binding, "result": result})
        start = len(provider.observed)
        old_prepare, old_binding_source = M.prepare, M.BINDING.DEPLOY.source
        binding_source_reads = []
        def read_binding_source():
            result = old_binding_source()
            binding_source_reads.append(M.C.DEPLOY.fingerprint(result[1]))
            return result
        def one_source_per_preparation(args, selected_provider):
            before = len(binding_source_reads)
            result = old_prepare(args, selected_provider)
            assert len(binding_source_reads) == before + 1, "one fresh binding snapshot per prepared operation, not per prerequisite or process"
            assert M.C.DEPLOY.fingerprint(result["binding_snapshot"]) == binding_source_reads[-1]
            return result
        M.BINDING.DEPLOY.source, M.prepare = read_binding_source, one_source_per_preparation
        provider_class, old_enable_task = M.Provider, M.Provider.enable_task
        def fresh_source_at_guard(self, request, selected_store, key, guard):
            if guard.__module__ != M.__name__:
                return old_enable_task(self, request, selected_store, key, guard)
            def checked_guard():
                before = len(binding_source_reads)
                guard()
                assert len(binding_source_reads) == before + 1, "actual provider guard reads a fresh snapshot, not the preparation snapshot"
            return old_enable_task(self, request, selected_store, key, checked_guard)
        provider_class.enable_task = fresh_source_at_guard
        for workload, operation in (("administration", "bootstrap"), ("migration", "apply"), ("database-proof", "permissions"), ("verifier", "create")):
            args = SimpleNamespace(receipt=root / "controlled.json", proof_label=binding["proof_label"], workload=workload, operation=operation, phase="preflight", expected_digest=None)
            planned = M.plan(args, provider)
            assert planned["verdict"] == "planned" and planned["plan"]["execution_route_available"] is (workload == "administration")
            assert planned["plan"]["operation"] == ("ready" if workload == "verifier" else "preflight")
            assert CANARY not in json.dumps(planned) and F.PARAMETERS["AdministratorSecretArn"] not in json.dumps(planned)
            evidence = json.loads((root / planned["realization_evidence"]).read_text())
            assert evidence["plan_sha256"] == planned["plan_sha256"]
            assert [row["gate"] for row in evidence["facts"]["gate_evidence"]] == list(M.C.GATE.GATE_ORDER[:5])
            assert "arn:" not in json.dumps(evidence)
            graph = M.GRAPH.contract(workload, M.C.GATE)
            units = {unit["id"] for unit in graph["execution_units"]}
            assert units == {"task-controller", M.GRAPH.ROOT_UNITS[workload]} | ({"feature-runtime"} if workload == "verifier" else set())
            M.C.GATE.validate_facts(evidence["facts"], graph, graph["id"], M.C.GATE.ids(graph)[1], "change-set")
            args.phase = "operation"
            business = M.plan(args, provider)
            assert business["plan"]["preflight_label"] == planned["plan"]["preflight_label"] and business["plan_sha256"] != planned["plan_sha256"]
        assert all(operation not in {"run-task", "create-change-set", "execute-change-set"} for _, operation, _ in provider.observed[start:])
        assert calls.count("local-proof-double") == calls.count("clean-source-custody-double")
        saved = cache / "receipts/create.json"
        bytes_before = saved.read_bytes(); moved = saved.with_suffix(".temporarily-moved"); saved.rename(moved)
        fails(lambda: M.plan(args, provider), "infrastructure-input-unavailable")
        moved.rename(saved)
        assert saved.read_bytes() == bytes_before
        # Exercise the real single-use provider/runner/collector/step path. Only
        # transport and source/custody/alignment prerequisites are controlled.
        live = M.Provider(); live._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
        execute_args = SimpleNamespace(receipt=root / "controlled.json", proof_label=binding["proof_label"], workload="administration", operation="bootstrap", phase="operation", expected_digest=None, approved_plan="sha256:" + "0" * 64)
        before = sum(op == "run-task" for _, op, _ in provider.observed)
        fails(lambda: M.execute(execute_args, live), "task-approved-plan-mismatch")
        execute_args.approved_plan = M.plan(execute_args, live)["plan_sha256"]
        fails(lambda: M.execute(execute_args, live), "task-preflight-receipt-required")
        assert sum(op == "run-task" for _, op, _ in provider.observed) == before
        assert not (cache / "task-attempts").exists()
        for number, (_, workload, operation, _) in enumerate(M.STEPS.STEPS):
            execute_args.workload, execute_args.operation = workload, operation
            execute_args.phase = "preflight"
            planned = M.plan(execute_args, live)
            assert planned["plan"]["execution_route_available"] is True
            execute_args.approved_plan = planned["plan_sha256"]
            if number == 0:
                provider.lost_next = True
                fails(lambda: M.execute(execute_args, live), "task-submission-uncertain-reconcile-required")
                assert live.effect == "unknown-reconcile-only"
                live = M.Provider(); live._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
            completed = M.execute(execute_args, live)
            assert completed["verdict"] == "completed"
            gates = json.loads((root / completed["realization_evidence"]).read_text())["facts"]["gate_evidence"]
            assert [row["gate"] for row in gates] == list(M.C.GATE.GATE_ORDER[:7]), "actual preflight completion, not simulation, supplies gate six"
            count = sum(op == "run-task" for _, op, _ in provider.observed)
            live = M.Provider(); live._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
            reused = M.execute(execute_args, live)
            assert reused["reused"] is True and sum(op == "run-task" for _, op, _ in provider.observed) == count
            execute_args.phase = "operation"
            execute_args.approved_plan = M.plan(execute_args, live)["plan_sha256"]
            live = M.Provider(); live._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
            if number == 2:
                provider.lost_next = True
                fails(lambda: M.execute(execute_args, live), "task-submission-uncertain-reconcile-required")
                live = M.Provider(); live._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
            completed = M.execute(execute_args, live)
            assert completed["verdict"] == "completed"
            assert CANARY not in json.dumps(completed)
            if number == 3:
                manifest = json.loads((root / completed["activation_prerequisites"]).read_text())
                assert set(manifest) == {"bootstrap", "migration", "grant-runtime", "permissions"}
                assert all(set(pair) == {"reservation", "receipt"} for pair in manifest.values())
            live = M.Provider(); live._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
        assert sum(op == "run-task" for _, op, _ in provider.observed) == before + 8, "exactly four probes and four operations, including lost-response reconciliation"
        feature_args = SimpleNamespace(**{**vars(execute_args), "workload": "verifier", "operation": "create", "phase": "preflight"})
        unavailable = M.plan(feature_args, live)
        assert unavailable["plan"]["execution_route_available"] is False and unavailable["plan"]["pending_prerequisite"] == "activation"
        feature_args.approved_plan = unavailable["plan_sha256"]
        failure = fails(lambda: M.execute(feature_args, live), "task-prerequisite-required")
        assert failure.item == "activation"
        # Seed activation with actual private controls and the collector-produced
        # manifest already checked above. This is still controlled provider proof.
        active_parameters = {**F.PARAMETERS, "ServerDesiredCount": "1"}
        review = M.C.DEPLOY.prepare(provider, store, binding, active_parameters, activate=True)
        activated = M.C.DEPLOY.execute(provider, store, binding, active_parameters, review["facts"]["change_set_arn"], review["facts"]["stack_arn"], activate=True)
        M.C.RESOURCE.write_exclusive(cache / "receipts/activate.json", {"schema": "deploy/entity-smoke-infrastructure-receipt/v1", "binding": binding, "result": activated})
        def execute_feature(workload, operation, *, digest=None, missing_result=False, stage="baseline"):
            selected = SimpleNamespace(**{**vars(feature_args), "workload": workload, "operation": operation, "expected_digest": digest, "proof_stage": stage})
            for phase in ("preflight", "operation"):
                selected.phase = phase
                capability = M.Provider(); capability._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
                prepared = M.plan(selected, capability)
                assert prepared["plan"]["execution_route_available"] is True
                selected.approved_plan = prepared["plan_sha256"]
                if missing_result and phase == "operation":
                    provider.missing_create_result = True
                    fails(lambda: M.execute(selected, capability), "task-success-observation-not-confirmed")
                    provider.missing_create_result = False
                    count = sum(op == "run-task" for _, op, _ in provider.observed)
                    capability = M.Provider(); capability._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
                    fails(lambda: M.execute(selected, capability), "task-success-observation-not-confirmed")
                    assert sum(op == "run-task" for _, op, _ in provider.observed) == count
                else:
                    completed = M.execute(selected, capability)
                    assert completed["verdict"] == "completed" and CANARY not in json.dumps(completed)
            return selected
        # An absent original reservation must reject before even an observer probe.
        unreserved = SimpleNamespace(**{**vars(feature_args), "operation": "observe-create"})
        fails(lambda: M.plan(unreserved, live), "feature-original-create-reservation-required")
        execute_feature("verifier", "create", missing_result=True)
        assert not (cache / "task-steps/verifier-create-operation.json").exists()
        original_create = next(task for task in provider.remote.values() if {"name": "ENTITY_SMOKE_VERIFICATION_OPERATION", "value": "create"} in task["overrides"]["containerOverrides"][0]["environment"])
        original_create["lastStatus"] = "RUNNING"
        fails(lambda: M.plan(unreserved, live), "feature-original-create-not-terminal")
        original_create["lastStatus"] = "STOPPED"
        original_create["containers"][0]["imageDigest"] = "sha256:" + "0" * 64
        fails(lambda: M.plan(unreserved, live), "feature-original-create-image-not-confirmed")
        original_create["containers"][0]["imageDigest"] = F.BINDING["image_digest"]
        execute_feature("verifier", "observe-create")
        execute_feature("verifier", "lifecycle")
        wrong_digest = SimpleNamespace(**{**vars(feature_args), "workload": "database-proof", "operation": "collision", "expected_digest": "2" * 64})
        fails(lambda: M.plan(wrong_digest, live), "feature-original-record-digest-mismatch")
        execute_feature("database-proof", "collision", digest="1" * 64)
        execute_feature("verifier", "read", digest="1" * 64)
        submitted_creates = [row for _, op, row in provider.observed if op == "run-task" and any(entry == {"name": "ENTITY_SMOKE_VERIFICATION_OPERATION", "value": "create"} for entry in row["overrides"]["containerOverrides"][0]["environment"])]
        assert len(submitted_creates) == 1, "observer, lifecycle and original read never replay the original create"
        staged_read = SimpleNamespace(**{**vars(feature_args), "operation": "read", "phase": "operation", "expected_digest": "1" * 64, "proof_stage": "server-replacement"})
        premature = M.plan(staged_read, live)
        assert premature["plan"]["execution_route_available"] is False and premature["plan"]["pending_prerequisite"] == "server-replacement"
        # The public replacement consumes the real baseline/prefix packets produced
        # above. Only source/custody/alignment/transport are still explicit doubles.
        XR = module("entity_smoke_public_replacement_fixture", DIRECTORY / "replacement-route.py")
        XR.TASK, XR.C = M, M.C
        def replacement_capability():
            value = XR.Provider(); value._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
            return value
        replacement_args = SimpleNamespace(mode="plan", receipt=root / "controlled.json", proof_label=binding["proof_label"], expected_digest="1" * 64, approved_plan=None, wait_seconds=0)
        baseline_path = cache / "task-steps/verifier-read-operation.json"
        baseline_bytes = baseline_path.read_bytes(); baseline_path.unlink()
        try: XR.run(replacement_args, replacement_capability())
        except XR.ReplacementFailure as failure: assert failure.code == "replacement-baseline-read-required"
        else: raise AssertionError("replacement needs the actual baseline read")
        baseline_path.write_bytes(baseline_bytes)
        observed_at = datetime.now(timezone.utc).isoformat()
        provider.server_states = {F.TASK: {"taskArn": F.TASK, "taskDefinitionArn": F.SERVER_DEFINITION, "group": "service:" + M.C.RESOURCE.SERVICE,
            "launchType": "FARGATE", "lastStatus": "RUNNING", "healthStatus": "HEALTHY", "createdAt": observed_at, "startedAt": observed_at,
            "containers": [{"name": "entity-smoke-server", "imageDigest": binding["image_digest"]}]}}
        replacement_plan = XR.run(replacement_args, replacement_capability())
        assert replacement_plan["verdict"] == "planned" and replacement_plan["plan"]["maximum_task_stops"] == 1
        assert "arn:" not in json.dumps(replacement_plan) and CANARY not in json.dumps(replacement_plan)
        replacement_args.mode, replacement_args.approved_plan = "execute", replacement_plan["plan_sha256"]
        provider.replacement_lost = True
        try: XR.run(replacement_args, replacement_capability())
        except M.C.RESOURCE.ResourceFailure as failure: assert failure.code == "resource-submission-uncertain-reconcile-only"
        else: raise AssertionError("lost stop response must not fabricate completion")
        assert sum(op == "stop-task" for _, op, _ in provider.observed) == 1
        completed_replacement = XR.run(replacement_args, replacement_capability())
        assert completed_replacement["verdict"] == "completed" and completed_replacement["post_replacement_record_readback"] is False
        XR.run(replacement_args, replacement_capability())
        assert sum(op == "stop-task" for _, op, _ in provider.observed) == 1, "never select the successor for a second stop"
        replacement_receipt = json.loads((root / completed_replacement["receipt"]).read_text())
        assert replacement_receipt["result"]["facts"]["original_task"] == F.TASK
        assert replacement_receipt["result"]["facts"]["successor_task"] != F.TASK
        baseline_probe = M.plan(SimpleNamespace(**{**vars(staged_read), "proof_stage": "baseline", "phase": "preflight"}), live)
        later_probe = M.plan(SimpleNamespace(**{**vars(staged_read), "phase": "preflight"}), live)
        assert baseline_probe["plan"]["preflight_label"] != later_probe["plan"]["preflight_label"]
        staged_read.approved_plan = M.plan(staged_read, live)["plan_sha256"]
        fails(lambda: M.execute(staged_read, live), "task-preflight-receipt-required")
        execute_feature("verifier", "read", digest="1" * 64, stage="server-replacement")
        staged_packet_path = cache / "task-steps/verifier-read-server-replacement-operation.json"
        staged_bytes = staged_packet_path.read_bytes()
        staged_packet = json.loads(staged_bytes)
        assert staged_packet["receipt"]["task"]["created_at"] >= replacement_receipt["result"]["facts"]["successor_started_at"]
        staged_packet_path.write_bytes(baseline_bytes)
        staged_context = M.prepare(staged_read, live)
        fails(lambda: M.STEPS.observe_packet(M.dependencies(), staged_context, staged_read, live), "task-step-reservation-not-retained")
        staged_packet_path.write_bytes(staged_bytes)
        gate_path = root / replacement_receipt["realization_evidence"]
        gate_bytes = gate_path.read_bytes(); gate_path.write_text('{"native":"' + CANARY + '"}')
        fails(lambda: M.plan(staged_read, live), "feature-replacement-gate-evidence-changed")
        gate_path.write_bytes(gate_bytes)
        assert sum(op == "stop-task" for _, op, _ in provider.observed) == 1
        # Closed provider capability rejects substitutions before any transport, and
        # preserves the actual guard's safe explanation through the public main.
        public_store = M.C.RESOURCE.ResourceStore(cache / "attempts")
        public_request = replacement_receipt["packet"]["request"]
        public_reservation = public_store.read("server-replacement", public_request)
        stopped_payload = {"cluster": M.C.RESOURCE.CLUSTER, "task": F.TASK, "reason": public_reservation["operation_id"]}
        guarded_replacement = replacement_capability()
        guard_failure = M.BINDING.BindingFailure("task-binding-policy-not-confirmed", "server", "roles", "execution-role")
        guarded_replacement.enable_replacement(public_store, public_request, lambda: (_ for _ in ()).throw(guard_failure))
        for changes in ({"cluster": "another-cluster"}, {"task": replacement_receipt["result"]["facts"]["successor_task"]}, {"reason": CANARY}, {"extra": True}):
            fails(lambda: guarded_replacement("ecs", "stop-task", **{**stopped_payload, **changes}), "replacement-submission-does-not-match-plan")
        old_xr_parse, old_xr_factory, old_xr_run = XR.parse, XR.Provider, XR.run
        XR.parse, XR.Provider = lambda: SimpleNamespace(**vars(replacement_args), validate_arguments=False), lambda: guarded_replacement
        XR.run = lambda *arguments: guarded_replacement("ecs", "stop-task", **stopped_payload)
        output = io.StringIO()
        with redirect_stdout(output): status = XR.main()
        reported = json.loads(output.getvalue())
        assert status == 1 and reported["condition"] == "task-binding-policy-not-confirmed" and reported["effect"] == "not-started"
        assert reported["context"]["affected_workload"] == "server" and reported["context"]["item"] == "execution-role" and CANARY not in output.getvalue()
        XR.parse, XR.Provider, XR.run = old_xr_parse, old_xr_factory, old_xr_run
        assert len([row for _, op, row in provider.observed if op == "run-task" and any(entry == {"name": "ENTITY_SMOKE_VERIFICATION_OPERATION", "value": "create"} for entry in row["overrides"]["containerOverrides"][0]["environment"])]) == 1
        # A historical prerequisite must survive real reobservation before a later
        # launch; no successful log prefix or edited local packet can advance it.
        bootstrap = cache / "task-steps/administration-bootstrap-operation.json"
        original_packet = bootstrap.read_bytes(); changed = json.loads(original_packet)
        changed["reservation"]["request"]["source_revision"] = "0" * 40
        bootstrap.write_text(json.dumps(changed))
        execute_args.workload, execute_args.operation = "migration", "apply"
        count = sum(op == "run-task" for _, op, _ in provider.observed)
        fails(lambda: M.plan(execute_args, live), "task-step-request-mismatch")
        assert sum(op == "run-task" for _, op, _ in provider.observed) == count
        bootstrap.write_bytes(original_packet)
        probe_args = SimpleNamespace(**{**vars(execute_args), "workload": "administration", "operation": "bootstrap", "phase": "preflight"})
        prepared = M.prepare(probe_args, live)
        request = M.STEPS.request(M.dependencies(), prepared, probe_args)
        old_yaml = M.C.yaml.safe_load
        M.C.yaml.safe_load = lambda *arguments: (_ for _ in ()).throw(AssertionError("requests must use their prepared checked declaration, not reparse it"))
        assert M.STEPS.request(M.dependencies(), prepared, probe_args) == request
        business_args = SimpleNamespace(**{**vars(probe_args), "phase": "operation"})
        assert M.STEPS.request(M.dependencies(), prepared, business_args)["deadline_seconds"] == 300
        M.C.yaml.safe_load = old_yaml
        guard_store = M.RUNNER.CONTROL.AttemptStore(root / "guard-attempts")
        reserved, _ = guard_store.reserve("guard", request)
        payload = {"cluster": M.C.RESOURCE.CLUSTER, "taskDefinition": request["definition"], "launchType": "FARGATE", "count": 1,
                   "networkConfiguration": {"awsvpcConfiguration": {"subnets": request["subnets"], "securityGroups": [request["security_group"]], "assignPublicIp": "DISABLED"}},
                   "overrides": M.RUNNER.CONTROL.overrides(request), "startedBy": reserved["operation_id"], "clientToken": reserved["operation_id"]}
        attempts = []
        guarded = M.Provider(); guarded._invoke = lambda *call: attempts.append(call)
        def denied(): raise M.BINDING.BindingFailure("task-binding-policy-not-confirmed", "server", "roles", "execution-role")
        guarded.enable_task(request, guard_store, "guard", denied)
        failure = fails(lambda: guarded("ecs", "run-task", **payload), "task-binding-policy-not-confirmed")
        assert failure.field == "roles" and failure.item == "execution-role" and failure.workload == "server" and guarded.effect == "not-started" and attempts == []
        for changed in ({**payload, "count": 2}, {**payload, "count": True}, {**payload, "enableExecuteCommand": True}, {**payload, "clientToken": CANARY}):
            fails(lambda: guarded("ecs", "run-task", **changed), "task-submission-does-not-match-plan")
        assert attempts == [] and guarded.effect == "not-started"
        single_use = M.Provider(); single_use._invoke = lambda *call: attempts.append(call)
        single_use.enable_task(request, guard_store, "guard", lambda: None)
        single_use("ecs", "run-task", **payload)
        fails(lambda: single_use("ecs", "run-task", **payload), "task-provider-operation-prohibited")
        fails(lambda: single_use.enable_task(request, guard_store, "guard", lambda: None), "task-capability-already-used")
        assert len(attempts) == 1 and single_use.effect == "unknown-reconcile-only"
        # The actual public reporter must retain supported guard context and native
        # uncertainty, not mislabel either as an unstarted generic boundary failure.
        old_parse, old_factory, old_execute = M.parse, M.Provider, M.execute
        M.parse = lambda: SimpleNamespace(**{**vars(execute_args), "execute": True, "validate_arguments": False})
        for thrown, effect, expected_code in ((failure, "not-started", "task-binding-policy-not-confirmed"),
                (M.C.ALIGN.AlignmentFailure("alignment-ecr-api-policy-not-confirmed"), "not-started", "alignment-ecr-api-policy-not-confirmed"),
                (M.C.ALIGN.AlignmentFailure("alignment-ecr-registry-policy-not-confirmed"), "not-started", "alignment-ecr-registry-policy-not-confirmed"),
                (M.TaskRouteFailure("task-prerequisite-required", "activation"), "not-started", "task-prerequisite-required"),
                (M.RUNNER.CONTROL.TaskFailure("task-submission-uncertain-reconcile-required"), "unknown-reconcile-only", "task-submission-uncertain-reconcile-required")):
            guarded.effect = effect
            M.Provider = lambda: guarded
            M.execute = lambda *arguments: (_ for _ in ()).throw(thrown)
            output = io.StringIO()
            with redirect_stdout(output): status = M.main()
            rejected = json.loads(output.getvalue())
            assert status == 1 and rejected["condition"] == expected_code and rejected["effect"] == effect
            if expected_code == "task-binding-policy-not-confirmed": assert rejected["context"]["item"] == "execution-role" and rejected["context"]["affected_workload"] == "server"
            if expected_code == "task-prerequisite-required": assert rejected["context"]["item"] == "activation"
            assert CANARY not in output.getvalue() and "Traceback" not in output.getvalue()
        diagnostic = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.preflight-rejected", "definitionVersion": 1,
                      "detail": {"identity": "runtime", "field": "identity", "condition": "mismatch", "effect": "not-started"}}
        bundle = {"diagnostic": diagnostic, "related_diagnostics": []}
        rejected_by_activation = M.C.RESOURCE.EVIDENCE.EvidenceFailure("task-unsuccessful-completion", diagnostic, [], [bundle])
        M.execute = lambda *arguments: (_ for _ in ()).throw(rejected_by_activation)
        output = io.StringIO()
        with redirect_stdout(output): status = M.main()
        rejected = json.loads(output.getvalue())
        assert status == 1 and rejected["condition"] == "task-unsuccessful-completion" and rejected["observations"] == [bundle]
        assert rejected["diagnostic"] == diagnostic and rejected["related_diagnostics"] == []
        assert CANARY not in output.getvalue(), "the existing activation consumer's own evidence class must not lose its supported meaning"
        # Exercise the actual provider -> runner -> evidence -> public reporter
        # path with a task that never starts, including original reconciliation.
        startup_store = M.RUNNER.CONTROL.AttemptStore(root / "public-startup-attempts")
        startup_calls, startup_task = [], {}
        def startup_transport(service, operation, parameters):
            startup_calls.append(operation)
            if operation == "run-task":
                startup_task.update(taskArn="arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "9" * 32,
                                    taskDefinitionArn=request["definition"], startedBy=parameters["startedBy"], overrides=parameters["overrides"],
                                    lastStatus="STOPPED", launchType="FARGATE", stopCode="TaskFailedToStart",
                                    stoppedReason="CannotPullContainerError: 403 Forbidden " + CANARY,
                                    containers=[{"name": "entity-smoke-administration"}])
                return {"tasks": [copy.deepcopy(startup_task)]}
            if operation == "list-tasks": return {"taskArns": [startup_task["taskArn"]] if parameters["desiredStatus"] == "STOPPED" else []}
            if operation == "describe-tasks": return {"tasks": [copy.deepcopy(startup_task)]}
            raise AssertionError("a failed start cannot fetch application logs or submit another operation")
        def startup_factory():
            selected = old_factory(); selected._invoke = startup_transport
            return selected
        def startup_execute(_args, selected):
            if startup_store.read("startup", request) is None:
                selected.enable_task(request, startup_store, "startup", lambda: None)
            else: selected.effect = "original-operation-reconcile-only"
            return M.RUNNER.run_owned_task(selected, startup_store, "startup", request, root / "public-startup-receipts")
        M.parse = lambda: SimpleNamespace(**{**vars(probe_args), "execute": True, "validate_arguments": False})
        M.Provider, M.execute = startup_factory, startup_execute
        for effect in ("unknown-reconcile-only", "original-operation-reconcile-only"):
            output = io.StringIO()
            with redirect_stdout(output): status = M.main()
            rejected = json.loads(output.getvalue())
            assert status == 1 and rejected["condition"] == "task-image-pull-access-denied" and rejected["effect"] == effect
            assert rejected["context"]["workload"] == "administration" and rejected["context"]["operation"] == "bootstrap" and rejected["context"]["phase"] == "preflight"
            assert CANARY not in output.getvalue() and "Traceback" not in output.getvalue()
        assert startup_calls.count("run-task") == 1 and "get-log-events" not in startup_calls
        assert not (root / "public-startup-receipts").exists()
        M.parse, M.Provider, M.execute = old_parse, old_factory, old_execute
        reference = ".cache/test-runs/20261108T000000Z-" + "0" * 32 + "/report.json"
        report = root / reference; report.parent.mkdir(parents=True); report.write_text('{"fixture":true}')
        old_parse, old_factory, old_subprocess = M.parse, M.Provider, M.C.subprocess.run
        M.parse, M.Provider = lambda: SimpleNamespace(**vars(args), validate_arguments=False, execute=False), lambda: provider
        M.C.local_checks = original["local_checks"]
        M.C.subprocess.run = lambda *arguments, **options: SimpleNamespace(returncode=1, stdout=json.dumps({"run_report_path": reference, "checks": [], "findings": []}), stderr=CANARY)
        output = io.StringIO(); provider_calls = len(provider.observed)
        with redirect_stdout(output): status = M.main()
        failure = json.loads(output.getvalue())
        assert status == 1 and failure["condition"] == "infrastructure-local-proof-not-passed" and failure["evidence_reference"] == reference
        assert len(provider.observed) == provider_calls and CANARY not in output.getvalue()
        M.parse, M.Provider, M.C.subprocess.run = old_parse, old_factory, old_subprocess
    M.prepare, M.BINDING.DEPLOY.source = old_prepare, old_binding_source
    provider_class.enable_task = old_enable_task
    for name, value in original.items(): setattr(M.C, name, value)
    M.C.ALIGN.read_receipt, M.C.ALIGN.source_preflight, M.C.ALIGN.inspect = old_read, old_source, old_inspect

    with tempfile.TemporaryDirectory(prefix="entity-smoke-task-plan-cli-") as temporary:
        root = Path(temporary); marker = root / "aws-called"
        fake = root / "aws"; fake.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\nraise SystemExit(99)\n"); fake.chmod(0o700)
        env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"]}
        wrapper = DIRECTORY / "task-plan.sh"
        common = ["--receipt", str(root / "missing.json"), "--proof-label", F.BINDING["proof_label"], "--workload", "administration", "--operation", "bootstrap", "--phase", "preflight"]
        for suffix, verdict in ((["--validate-arguments"], "valid"), ([], "blocked"), (["--mode", "execute", CANARY], "blocked"),
                                (["--execute", "--approved-plan", "sha256:" + "0" * 64], "blocked")):
            result = subprocess.run(["bash", str(wrapper), *common, *suffix], cwd=REAL_ROOT, env=env, capture_output=True, text=True)
            assert json.loads(result.stdout)["verdict"] == verdict and CANARY not in result.stdout + result.stderr and "Traceback" not in result.stderr
        assert not marker.exists()
        replacement_common = ["--receipt", str(root / "missing.json"), "--proof-label", F.BINDING["proof_label"], "--expected-digest", "1" * 64]
        for suffix, verdict in ((["--mode", "plan", "--validate-arguments"], "valid"), (["--mode", "execute"], "blocked"),
                                (["--mode", "plan"], "blocked"), (["--mode", "plan", "--unknown", CANARY], "blocked")):
            result = subprocess.run(["bash", str(DIRECTORY / "replacement.sh"), *replacement_common, *suffix], cwd=REAL_ROOT, env=env, capture_output=True, text=True)
            assert json.loads(result.stdout)["verdict"] == verdict and CANARY not in result.stdout + result.stderr and "Traceback" not in result.stderr and not marker.exists()
        for suffix, condition in (([], "task-approved-plan-required"), (["--approved-plan", "sha256:" + "0" * 64], "target-alignment-receipt-unavailable")):
            result = subprocess.run(["bash", str(DIRECTORY / "task-execute.sh"), *common, *suffix], cwd=REAL_ROOT, env=env, capture_output=True, text=True)
            response = json.loads(result.stdout)
            assert response["verdict"] == "blocked" and CANARY not in result.stdout + result.stderr and not marker.exists()
            if not suffix: assert response["condition"] == condition
    read_boundary = M.Provider()
    read_boundary._invoke = lambda *arguments, **options: (_ for _ in ()).throw(AssertionError("planning must not reach provider I/O for a mutation"))
    fails(lambda: read_boundary("ecs", "run-task", cluster=CANARY), "task-provider-operation-prohibited")
    read_boundary.enable(("cloudformation", "execute-change-set"), lambda operation, parameters: None)
    fails(lambda: read_boundary("cloudformation", "execute-change-set", StackName=M.C.DEPLOY.STACK), "task-provider-operation-prohibited")
    print(json.dumps({"schema": "deploy/entity-smoke-task-plan-fixture/v1", "verdict": "passed", "provider_observation": False,
                      "prerequisites": "controlled-source-custody-local-proof-and-target-responses-not-qualification", "checks": ["actual-selected-graph-and-generic-gates", "all-reachable-callees-retained", "deployed-resource-lineage", "exact-task-role-network-binding", "preflight-and-business-plan-binding", "no-sixth-gate-before-probe", "planning-no-write-capability", "actual-offline-cli", "actual-execute-provider-runner-collector", "lost-launch-no-replay", "four-ordered-prerequisites-and-activation-consumer", "changed-prerequisite-rejected", "exact-reserved-payload", "known-prewrite-versus-unknown-effect-reporter", "named-missing-prerequisite", "activated-feature-prerequisites", "uncertain-create-observed-never-replayed", "terminal-qualified-original-before-observer", "lifecycle-digest-cannot-replace-original", "collision-and-original-read", "selected-primary-diagnostic-preserved", "public-replacement-requires-baseline-read", "lost-stop-reconciles-original-not-successor", "separate-post-replacement-ready-and-read", "baseline-receipt-substitution-rejected", "changed-replacement-gate-rejected", "replacement-exact-payload", "replacement-public-main-preserves-guard-context", "no-original-record-recreation"]}))


if __name__ == "__main__": run()
