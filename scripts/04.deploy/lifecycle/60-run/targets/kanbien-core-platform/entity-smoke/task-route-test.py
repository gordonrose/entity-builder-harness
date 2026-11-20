#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.task-route
#   version: 5
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-20"
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
from datetime import datetime, timedelta, timezone
import hashlib
from contextlib import redirect_stdout
import importlib.util
import json
import io
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

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
        self.fail_operation = None
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
                    "containers": [{"name": "entity-smoke-" + workload, "imageDigest": self.bindings[workload].task["containerDefinitions"][0]["image"].split("@")[-1], "exitCode": 0}]}
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
                result = {"schema": "deploy/entity-smoke-task-proof/v1", "verdict": "passed", "operation": selected, "code": codes[selected], "source_revision": environment["ENTITY_SMOKE_EXPECTED_SOURCE"],
                          "proof_label_sha256": hashlib.sha256(environment["ENTITY_SMOKE_PROOF_LABEL"].encode()).hexdigest(), "steps": steps, "checked_at": observed_at}
                if selected not in {"ready", "unready"}: result["record_digest"] = ("2" if selected == "lifecycle" else "1") * 64
                if selected == "create" and self.missing_create_result: result = None
            if selected == self.fail_operation: task["containers"][0]["exitCode"] = 1
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
        if operation == "simulate-principal-policy": return {"IsTruncated": False, "EvaluationResults": [{"EvalActionName": action, "EvalResourceName": arn, "EvalDecision": "allowed"} for action in parameters["ActionNames"] for arn in parameters["ResourceArns"]]}
        if operation == "validate-template": return {"Parameters": [{"ParameterKey": name} for name in M.C.DEPLOY.PARAMETERS], "Capabilities": ["CAPABILITY_IAM"]}
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


def operator_protocols():
    definition = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-migration:1"
    roles = ["arn:aws:iam::337159794548:role/ControlledExecution", "arn:aws:iam::337159794548:role/ControlledTask"]
    calls = []
    altered = {"mutate": None, "resource": roles[-1]}
    def provider(service, operation, **parameters):
        if operation == "get-caller-identity": return {"Account": M.C.ALIGN.ACCOUNT, "Arn": "arn:aws:sts::337159794548:assumed-role/ApprovedOperator/fixture"}
        if operation == "get-role": return {"Role": {"RoleName": "ApprovedOperator", "Arn": "arn:aws:iam::337159794548:role/ApprovedOperator"}}
        assert (service, operation) == ("iam", "simulate-principal-policy")
        assert len(parameters["ResourceArns"]) == 1, "do not assume one top-level IAM result per resource in a batch"
        resource, action = parameters["ResourceArns"][0], parameters["ActionNames"][0]
        calls.append((action, resource))
        result = {"IsTruncated": False, "EvaluationResults": [{"EvalActionName": action, "EvalResourceName": resource, "EvalDecision": "allowed",
                   "ResourceSpecificResults": [{"EvalResourceName": resource, "EvalResourceDecision": "allowed"}]}]}
        if resource == altered["resource"] and altered["mutate"] is not None: altered["mutate"](result)
        return result
    M.operator(provider, definition, roles)
    assert calls == [("ecs:RunTask", definition), *(('iam:PassRole', role) for role in roles)]
    for mutate in (lambda v: v["EvaluationResults"][0].update(EvalDecision="implicitDeny"),
                   lambda v: v["EvaluationResults"][0].update(MissingContextValues=["controlled-context"]),
                   lambda v: v["EvaluationResults"][0].update(EvalResourceName=roles[0]),
                   lambda v: v["EvaluationResults"][0].update(EvalActionName="iam:GetRole"),
                   lambda v: v.update(IsTruncated=True), lambda v: v.update(EvaluationResults=[])):
        calls.clear(); altered["mutate"] = mutate
        fails(lambda: M.operator(provider, definition, roles), "task-operator-policy-preflight-not-confirmed")
        assert calls[-1] == ("iam:PassRole", roles[-1])
    altered["mutate"] = None; calls.clear()
    M.operator(provider, definition, roles[:1])
    assert len(calls) == 2
    for resources in ([], [roles[0], roles[0]], [None]):
        assert M.C.operator_resources_allowed(provider, roles[0], "iam:PassRole", resources) is False
    snapshot = module("operator_snapshot_fixture", DIRECTORY / "snapshot-route.py")
    failure = module("operator_failure_fixture", DIRECTORY / "failure-route.py")
    snapshot_name = "kanbien-core-platform-entity-smoke-" + "a" * 24
    calls.clear(); snapshot.actor(provider, snapshot_name)
    prefix = "arn:aws:rds:eu-west-1:337159794548:"
    assert calls == [("rds:CreateDBSnapshot", prefix + "db:" + M.C.RESOURCE.SOURCE_DATABASE), ("rds:CreateDBSnapshot", prefix + "snapshot:" + snapshot_name)]
    denied_snapshot = calls[-1][1]
    tasks = ["arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + character * 32 for character in ("1", "2")]
    service = "arn:aws:ecs:eu-west-1:337159794548:service/kanbien-core-platform/kanbien-core-platform-entity-smoke"
    selected = {"task_stops": {task: {} for task in tasks}, "service": {"arn": service}}
    calls.clear(); failure.operator(provider, selected)
    assert calls == [("ecs:StopTask", task) for task in tasks] + [("ecs:UpdateService", service)]
    for invoke, resource, code in ((lambda: snapshot.actor(provider, snapshot_name), denied_snapshot, "snapshot-operator-policy-preflight-not-confirmed"),
                                   (lambda: failure.operator(provider, selected), tasks[-1], "failure-operator-policy-preflight-not-confirmed")):
        altered.update(resource=resource, mutate=lambda value: value["EvaluationResults"][0].update(EvalDecision="implicitDeny"))
        calls.clear()
        try: invoke()
        except Exception as error: assert getattr(error, "code", None) == code
        else: raise AssertionError("later-resource denial ignored")
        assert calls[-1][1] == resource


def run():
    operator_protocols()
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
        preparation_reads = []
        def read_binding_source():
            result = old_binding_source()
            binding_source_reads.append(M.C.DEPLOY.fingerprint(result[1]))
            return result
        def one_source_per_preparation(args, selected_provider):
            before = len(binding_source_reads)
            before_reads = len(provider.observed)
            result = old_prepare(args, selected_provider)
            configuration = [(service, operation, json.dumps(parameters, sort_keys=True)) for service, operation, parameters in provider.observed[before_reads:]
                             if (service, operation) in {("ecs", "describe-task-definition"), ("ec2", "describe-security-groups"),
                                *(('iam', name) for name in ('get-role', 'list-role-policies', 'list-attached-role-policies', 'get-role-policy'))}]
            assert len(configuration) == len(set(configuration)), "identical configuration reads share only this preparation scope"
            assert len(binding_source_reads) == before + 1, "one fresh binding snapshot per prepared operation, not per prerequisite or process"
            assert M.C.DEPLOY.fingerprint(result["binding_snapshot"]) == binding_source_reads[-1]
            preparation_reads.append(len(binding_source_reads))
            return result
        M.BINDING.DEPLOY.source, M.prepare = read_binding_source, one_source_per_preparation
        provider_class, old_enable_task = M.Provider, M.Provider.enable_task
        def fresh_source_at_guard(self, request, selected_store, key, guard):
            if guard.__module__ != M.__name__:
                return old_enable_task(self, request, selected_store, key, guard)
            assert len(binding_source_reads) == preparation_reads[-1] + 1, "fresh binding recheck precedes reservation"
            def checked_guard():
                before = len(binding_source_reads)
                guard()
                assert len(binding_source_reads) == before, "submission guard has no fallible provider read after reservation"
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
        with patch.object(M.C.TRANSITION, "RETIRED_PROOF_LABEL", binding["proof_label"]):
            fails(lambda: M.execute(execute_args, live), "incident-proof-new-attempt-retired")
        assert not (cache / "task-attempts").exists()
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
                original_inspect = M.C.ALIGN.inspect
                reads = []
                def fail_second_read(*arguments):
                    reads.append(True)
                    if len(reads) == 2: raise M.C.InfrastructureFailure("aws-command-failed", provider_operation=("ecs", "describe-task-definition"))
                    return original_inspect(*arguments)
                M.C.ALIGN.inspect = fail_second_read
                try: fails(lambda: M.execute(execute_args, live), "aws-command-failed")
                finally: M.C.ALIGN.inspect = original_inspect
                assert not (cache / "task-attempts").exists() and live.effect == "not-started"
                provider.lost_next = True
                fails(lambda: M.execute(execute_args, live), "task-submission-uncertain-reconcile-required")
                assert live.effect == "unknown-reconcile-only"
                live = M.Provider(); live._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
                # Observe a controlled failed outcome through the real execute,
                # runner, evidence and public reporter. Repeating the observation
                # must reconcile the original lost submission, not launch again.
                observed_task = next(iter(provider.remote.values()))
                observed_task["containers"][0]["exitCode"] = 1
                submitted = sum(op == "run-task" for _, op, _ in provider.observed)
                try:
                    for _ in range(2):
                        output = io.StringIO()
                        with patch.object(M, "parse", return_value=SimpleNamespace(**{**vars(execute_args), "execute": True, "validate_arguments": False})), patch.object(M, "Provider", return_value=live), redirect_stdout(output):
                            status = M.main()
                        failure_report = json.loads(output.getvalue())
                        assert status == 1 and failure_report["verdict"] == "failed"
                        terminal = failure_report["terminal_failure"]
                        assert terminal["task_arn"] == observed_task["taskArn"] and terminal["operation_id"] == observed_task["startedBy"]
                        assert terminal["workload"] == "administration" and terminal["operation"] == "preflight" and terminal["exit_code"] == 1
                        assert terminal["failure_basis"] == "nonzero-exit" and CANARY not in output.getvalue()
                    assert sum(op == "run-task" for _, op, _ in provider.observed) == submitted
                finally:
                    # Return the fixture to its success branch, not a real retry.
                    observed_task["containers"][0]["exitCode"] = 0
            if number == 0:
                # A closed incident can observe the original lost submission,
                # but cannot reserve another task under the retired identity.
                submitted = sum(op == "run-task" for _, op, _ in provider.observed)
                with patch.object(M.C.TRANSITION, "RETIRED_PROOF_LABEL", binding["proof_label"]):
                    completed = M.execute(execute_args, live)
                assert sum(op == "run-task" for _, op, _ in provider.observed) == submitted
            else:
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
        # Activation accepts exact completed grant custody even after ECS has
        # aged out that task; fresh permissions remain an actual observation.
        grant_path = cache / "task-steps/administration-grant-runtime-operation.json"
        grant_packet = M.C.read_json(grant_path)
        grant_completion = M.C.read_json(M.COMPLETION.path(grant_path))
        old_pins = M.C.TRANSITION.CONTROLLER_REPAIR_PINS
        M.C.TRANSITION.CONTROLLER_REPAIR_PINS = {**old_pins, M.C.TRANSITION.document(grant_packet): (M.C.TRANSITION.document(grant_completion), "f" * 64)}
        def expired_grant(service, operation, **parameters):
            assert not (operation == "describe-tasks" and grant_packet["receipt"]["task"]["arn"] in parameters.get("tasks", [])), "historical grant must not query expired ECS state"
            return provider(service, operation, **parameters)
        try:
            M.C.activation_prerequisites(expired_grant, cache / "task-steps/activation-prerequisites.json", binding, F.PARAMETERS, cache, store)
            gate_path = root / grant_completion["realization_evidence"]
            gate_bytes = gate_path.read_bytes(); gate_path.write_bytes(b'{}\n')
            try: fails(lambda: M.C.activation_prerequisites(expired_grant, cache / "task-steps/activation-prerequisites.json", binding, F.PARAMETERS, cache, store), "infrastructure-original-preparation-changed")
            finally: gate_path.write_bytes(gate_bytes)
        finally: M.C.TRANSITION.CONTROLLER_REPAIR_PINS = old_pins

        refresh_args = SimpleNamespace(**{**vars(execute_args), "proof_stage": "activation"})
        original_manifest = (cache / "task-steps/activation-prerequisites.json").read_bytes()
        original_permissions = (cache / "task-steps/database-proof-permissions-operation.json").read_bytes()
        for phase in ("preflight", "operation"):
            refresh_args.phase = phase
            refresh_args.activation_generation = "caller-cannot-select-generation"
            live = M.Provider(); live._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
            refresh_args.approved_plan = M.plan(refresh_args, live)["plan_sha256"]
            assert refresh_args.activation_generation == "sha256:" + "f" * 64
            refreshed = M.execute(refresh_args, live)
            assert refreshed["verdict"] == "completed"
        assert refreshed["activation_prerequisites"].endswith("activation-refresh-" + "f" * 64 + "-prerequisites.json")
        next_controller = SimpleNamespace(**{**vars(refresh_args), "activation_generation": "sha256:" + "a" * 64})
        assert M.STEPS.key(next_controller) != M.STEPS.key(refresh_args)
        assert M.STEPS.path({"cache": cache, "artifact": next_controller.activation_generation}, next_controller) != M.STEPS.path({"cache": cache, "artifact": refresh_args.activation_generation}, refresh_args)
        fails(lambda: M.STEPS.path({"cache": cache, "artifact": refresh_args.activation_generation}, next_controller), "task-activation-controller-mismatch")
        assert (cache / "task-steps/activation-prerequisites.json").read_bytes() == original_manifest
        assert (cache / "task-steps/database-proof-permissions-operation.json").read_bytes() == original_permissions
        assert sum(op == "run-task" for _, op, _ in provider.observed) == before + 10
        fails(lambda: M.STEPS.stage(SimpleNamespace(proof_stage="activation", workload="administration", operation="grant-runtime")), "task-proof-stage-not-supported")
        missing_original = cache / "task-steps/database-proof-permissions-operation.json"
        missing_original.rename(missing_original.with_suffix(".saved"))
        try: assert M.plan(refresh_args, live)["plan"]["pending_prerequisite"] == "baseline-permissions"
        finally: missing_original.with_suffix(".saved").rename(missing_original)
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
        fails(lambda: M.plan(refresh_args, live), "task-activation-refresh-requires-stopped-service")
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
        # A completed predecessor is history, not a requirement that ECS keep
        # its stopped task forever. Its exact completion gate remains mandatory.
        lifecycle_path = cache / "task-steps/verifier-lifecycle-operation.json"
        lifecycle_packet = M.C.read_json(lifecycle_path)
        lifecycle_arn = lifecycle_packet["receipt"]["task"]["arn"]
        expired = provider.remote.pop(lifecycle_arn)
        historical_args = SimpleNamespace(**{**vars(feature_args), "workload": "database-proof", "operation": "collision", "expected_digest": "1" * 64})
        try:
            assert M.plan(historical_args, live)["plan"]["execution_route_available"]
            completion = M.C.read_json(M.COMPLETION.path(lifecycle_path))
            gate = root / completion["realization_evidence"]
            gate_bytes = gate.read_bytes(); gate.write_bytes(b'{}\n')
            try: fails(lambda: M.plan(historical_args, live), "task-step-completion-gate-changed")
            finally: gate.write_bytes(gate_bytes)
        finally: provider.remote[lifecycle_arn] = expired
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
        # ECS may expire the stopped predecessor. Completed custody and the
        # current healthy successor must suffice without another stop.
        provider.server_states.pop(F.TASK)
        completion_path = M.C.CONTROL_COMPLETION.companion(cache / "replacement-receipt.json")
        completion_bytes = completion_path.read_bytes()
        completion_path.write_bytes(b'{}\n')
        fails(lambda: M.plan(staged_read, live), "control-completion-changed")
        completion_path.write_bytes(completion_bytes)
        completion_path.rename(completion_path.with_suffix(".saved"))
        try: fails(lambda: M.plan(staged_read, live), "control-completion-required")
        finally: completion_path.with_suffix(".saved").rename(completion_path)
        successor = provider.server_states[replacement_receipt["result"]["facts"]["successor_task"]]
        successor["healthStatus"] = "UNHEALTHY"
        fails(lambda: M.plan(staged_read, live), "deployment-service-not-steady")
        successor["healthStatus"] = "HEALTHY"
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
        fails(lambda: M.plan(staged_read, live), "control-completion-gate-changed")
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
        assert rejected["verdict"] == "blocked" and "terminal_failure" not in rejected
        for evidence_owner in (M.C.RESOURCE.EVIDENCE, M.RUNNER.EVIDENCE):
            prerequisite = evidence_owner.TerminalTaskFailure(terminal, diagnostic, [], [bundle])
            with patch.object(M, "execute", side_effect=prerequisite), redirect_stdout(output := io.StringIO()):
                status = M.main()
            rejected = json.loads(output.getvalue())
            assert status == 1 and rejected["verdict"] == "blocked" and "terminal_failure" not in rejected, "terminal prerequisite evidence is not the current task's outcome"
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


def successor_task_protocols(*, requalify=False, failed_recovery=None):
    """Actual controller/task/collector chain; source/applicability are doubles."""
    evidence = module("successor_task_actual_evidence", DIRECTORY / "acceptance-evidence.py")
    with tempfile.TemporaryDirectory(prefix="entity-smoke-successor-tasks-") as temporary:
        root = Path(temporary)
        receipt = {**F.delivery_fixture()["candidate"], "program_id": "kanbien-entity-smoke", "package_contract_id": "kanbien-entity-smoke-image"}
        prior = F.delivery_fixture()["predecessor"]
        current = {"target": M.C.RESOURCE.CLUSTER, "scope": "entity-smoke", "release_id": prior["release_id"]}
        history = {"release": {"id": prior["release_id"], **{key: prior[key] for key in ("source_revision", "image_digest", "proof_set_sha256")}}}
        actual_digest = M.C.digest_file
        with patch.object(M.C, "ROOT", root), patch.object(M.C, "source_digest", lambda: "sha256:" + "f" * 64), \
             patch.object(M.C, "digest_file", lambda path: actual_digest(path) if path.is_file() else "sha256:" + "c" * 64), \
             patch.object(M.C, "local_checks", lambda: None), patch.object(M.C.ALIGN, "source_preflight", lambda *args, **kwargs: None), \
             patch.object(M.C.ALIGN, "read_receipt", lambda path: receipt), \
             patch.object(M.C.ALIGN, "inspect", lambda *args: ({"dependency_incarnation_sha256": F.BINDING["dependency_incarnation_sha256"]}, copy.deepcopy(F.PARAMETERS), "fixture")), \
             patch.object(M.C.SUCCESSION, "current", lambda path: current), patch.object(M.C.SUCCESSION, "history_record_for_id", lambda *args: (history, b"controlled")), \
             patch.object(M.C, "successor_admission", lambda *args: None), \
             patch.object(M.C, "rollback_selection", lambda args, delivery, binding: ({**binding, **{key: prior[key] for key in ("source_revision", "image_digest")}}, {
                 "compatibility_id": "rollback-compatibility-" + "8" * 24, "compatibility_sha256": "sha256:" + "8" * 64, "receipt_reference": "github-actions-run:99"})):
            provider = Provider(); F.accepted_provider(provider, F.delivery_fixture()); provider.created_record = True
            def live(owner=M):
                value = owner.Provider(); value._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
                return value
            deploy_args = SimpleNamespace(mode="plan", phase="update", receipt=root / "candidate.json", proof_label=F.BINDING["proof_label"], expected_predecessor=prior["release_id"], approved_plan=None, wait_seconds=0, prerequisites=None)
            planned = M.C.run(deploy_args, live(M.C))
            deploy_args.approved_plan, deploy_args.mode = planned["plan_sha256"], "review"
            assert M.C.run(deploy_args, live(M.C))["verdict"] == "reviewed"
            deploy_args.mode = "execute"
            assert M.C.run(deploy_args, live(M.C))["verdict"] == "completed"
            delivery, binding = planned["plan"]["delivery"], planned["plan"]["binding"]
            cache = M.C.delivery_cache(binding["proof_label"], delivery)
            deployment = M.C.read_json(cache / "receipts/update.json")
            if requalify:
                original = M.C.RESOURCE.running_service_tasks(provider)[0]
                row = provider("ecs", "describe-tasks", tasks=[original])["tasks"][0]
                row.update(createdAt=deployment["result"]["facts"]["completed_at"], startedAt=deployment["result"]["facts"]["completed_at"])
                provider.server_states = {original: row}
            coordinator = module("task_delivery_coordinator", DIRECTORY.parents[2] / "release-succession/ordinary-update.py")
            adapter = module("task_delivery_adapter", DIRECTORY / "ordinary-update.py")
            consumer = object.__new__(adapter.Consumer)
            consumer.K = SimpleNamespace(C=M.C, T=M, A=evidence, SUCCESSOR_TASKS=("baseline-permissions", "lifecycle", "collision", "migration-state", "final-read"))
            consumer.require, consumer.halt = coordinator.require, coordinator.Halt
            consumer.rollback = root / "prior.json"
            consumer.context = SimpleNamespace(package=receipt, expected=prior["release_id"], route={"target": M.C.RESOURCE.CLUSTER, "scope": "entity-smoke"},
                values={"proof_label": binding["proof_label"], "expected_digest": "1" * 64, "rollback_compatibility_id": "rollback-compatibility-" + "8" * 24}, check_authority=lambda: None)
            consumer.release_context = lambda: (binding, delivery, cache)
            original_provider = M.C.Provider
            def retained_provider():
                value = original_provider(); value._invoke = lambda service, operation, parameters: provider(service, operation, **parameters)
                return value
            with patch.object(M.C, "Provider", retained_provider):
                before = list(provider.observed)
                consumer.deploy()
                assert not any(op in {"create-change-set", "execute-change-set", "run-task"} for _, op, _ in provider.observed[len(before):])
            assert consumer.approved_plan(planned, phase="update") == planned["plan_sha256"]
            for key, bad in (("resource_additions", 1), ("database_data_or_schema_changes", True), ("phase", "create"),
                             ("package_custody_reference", "github-actions-run:1"), ("account", "000000000000")):
                changed = copy.deepcopy(planned); changed["plan"][key] = bad
                changed["plan_sha256"] = M.C.DEPLOY.fingerprint(changed["plan"])
                try: consumer.approved_plan(changed, phase="update")
                except coordinator.Halt as error: assert error.condition == "delivery-plan-outside-approval"
                else: raise AssertionError("generated broader plan obtained approval")
            # Only typed predecessor/applicability is controlled. Actual ordering,
            # deployed receipt, task observations and retained archive validation run.
            predecessor = {"release_id": prior["release_id"], "candidate_record": "release-candidates/" + prior["release_id"] + ".yml",
                "candidate_sha256": "sha256:" + "9" * 64, "applicability": {"mode": "requalify" if requalify else "reuse"}}
            if requalify:
                predecessor["applicability"].update(schema="deploy/recovery-requirements/v1",
                    predecessor_source=prior["source_revision"], candidate_source=receipt["source_revision"], input_paths=["platform"],
                    predecessor_inputs_sha256="sha256:" + "8" * 64, candidate_inputs_sha256="sha256:" + "9" * 64,
                    changed_bindings=["recovery_inputs"])
            predecessor_owner = SimpleNamespace(successor_parent=lambda *args: predecessor)
            with patch.object(M.ACCEPTANCE, "acceptance_owner", lambda: predecessor_owner), patch.object(M.C.TRANSITION, "RETIRED_PROOF_LABEL", binding["proof_label"]):
                previous_stop = deployment["result"]["facts"]["completed_at"]
                for stage, workload, operation in (M.ACCEPTANCE.REQUALIFICATION_PREFIX if requalify else M.ACCEPTANCE.SUCCESSOR_STEPS):
                    args = SimpleNamespace(receipt=root / "candidate.json", proof_label=binding["proof_label"], expected_predecessor=prior["release_id"],
                                           workload=workload, operation=operation, proof_stage=stage, phase="preflight", expected_digest="1" * 64)
                    for phase in ("preflight", "operation"):
                        args.phase = phase
                        context = M.prepare(args, live())
                        assert context["delivery"] == delivery and context["report"]["plan"]["execution_route_available"]
                        args.approved_plan = context["report"]["plan_sha256"]
                        assert consumer.approved_plan(context["report"], selection=(stage, workload, operation, phase)) == args.approved_plan
                        if not requalify and operation == "permissions" and phase == "preflight":
                            provider.lost_next = True
                            fails(lambda: M.execute(args, live()), "task-submission-uncertain-reconcile-required")
                            failed = list(provider.remote.values())[-1]
                            failed["containers"][0]["exitCode"] = 1
                            observer = live()
                            with patch.object(M, "Provider", return_value=observer):
                                terminal = consumer.terminal_failure("baseline-permissions.preflight")
                                assert terminal["task_arn"] == failed["taskArn"]
                                error = coordinator.Halt("delivery-child-not-successful", verdict="failed", evidence={"schema": "deploy/entity-smoke-task-report/v1", "terminal_failure": terminal})
                                assert consumer.confirm_failure("baseline-permissions.preflight", error)
                                assert not consumer.confirm_failure("collect", error)
                                error.evidence["terminal_failure"] = {**terminal, "operation_id": "es-" + "0" * 32}
                                assert not consumer.confirm_failure("baseline-permissions.preflight", error)
                            assert sum(op == "run-task" for _, op, _ in provider.observed) == 1
                            failed["containers"][0]["exitCode"] = 0  # Controlled fixture alternate, never a live retry.
                        completed = M.execute(args, live())
                        assert completed["verdict"] == "completed"
                        step = M.C.read_json(root / completed["receipt"])
                        assert step["schema"] == "deploy/entity-smoke-task-step/v3" and step["prerequisites"]["packets"]["deployment"] == deployment
                        assert M.RUNNER.EVIDENCE.timestamp(step["prerequisites"]["required_after"]) >= M.RUNNER.EVIDENCE.timestamp(previous_stop)
                        M.STEPS.validate_delivery_step(M.dependencies(), step, binding, delivery, args)
                        proof_name = {"permissions": "baseline-permissions", "lifecycle": "lifecycle", "collision": "collision", "observe-migration-state": "migration-state", "read": "baseline-read" if requalify else "final-read"}[operation]
                        archive = evidence.capture_task(M, context, args, live(), proof_name, {**binding, "record_digest": "1" * 64})
                        assert archive["packet"] == step and archive["delivery"] == delivery
                        if requalify and failed_recovery is None and operation == "permissions" and phase == "preflight":
                            renewal_protocols(provider, args, context, evidence, consumer)
                        request = step["reservation"]["request"]
                        label = M.C.delivery_preflight_label(delivery, stage, workload, operation) if phase == "preflight" else M.C.delivery_operation_label(delivery, workload, operation)
                        assert request["proof_label"] == label
                        if workload in {"verifier", "database-proof"}:
                            assert request["environment"]["ENTITY_SMOKE_PROOF_LABEL"] == label
                        assert M.STEPS.key(args, delivery) != M.STEPS.key(args)
                        if operation == "lifecycle" and phase == "operation": assert label == delivery["smoke_label"] != binding["proof_label"]
                        if phase == "operation" and operation in {"permissions", "lifecycle"}: assert "ENTITY_SMOKE_EXPECTED_DIGEST" not in request["environment"]
                        for mutate in (
                            lambda packet: packet["delivery"].update(delivery_id="0" * 64),
                            lambda packet: packet["plan"].update(request_sha256="sha256:" + "0" * 64),
                            lambda packet: packet["prerequisites"].update(required_after="2000-01-01T00:00:00Z"),
                            lambda packet: packet["plan"].update(preflight_label=binding["proof_label"]),
                        ):
                            changed = copy.deepcopy(step); mutate(changed)
                            changed["plan_sha256"] = M.C.DEPLOY.fingerprint(changed["plan"])
                            try: M.STEPS.validate_delivery_step(M.dependencies(), changed, binding, delivery, args)
                            except M.STEPS.StepFailure: pass
                            else: raise AssertionError("successor delivery/plan/prerequisite mutation accepted")
                        observed = sum(op == "run-task" for _, op, _ in provider.observed)
                        assert M.execute(args, live())["reused"] is True
                        assert sum(op == "run-task" for _, op, _ in provider.observed) == observed
                    previous_stop = step["receipt"]["task"]["stopped_at"]
                if requalify:
                    successor_recovery_protocols(provider, live, args, binding, delivery, cache, evidence, failed_recovery=failed_recovery)
                    return
                # Actual prerequisite owner rejects absent and stale predecessors.
                with patch.object(M.STEPS, "observe_packet", lambda *args, **kwargs: None):
                    try: M.ACCEPTANCE.successor_prerequisites(M.dependencies(), context, args, live())
                    except M.STEPS.PrerequisiteMissing: pass
                    else: raise AssertionError("missing successor prerequisite admitted")
                stale = copy.deepcopy(step)
                stale["receipt"]["task"]["created_at"] = "2000-01-01T00:00:00Z"
                with patch.object(M.STEPS, "observe_packet", lambda *args, **kwargs: stale):
                    try: M.ACCEPTANCE.successor_prerequisites(M.dependencies(), context, args, live())
                    except M.ACCEPTANCE.AcceptanceFailure as failure: assert failure.code == "acceptance-successor-task-order-invalid"
                    else: raise AssertionError("stale successor prerequisite admitted")
                # Restore through the actual infrastructure owner, then prove a
                # distinct read bound to its completion and predecessor image.
                deploy_args.phase, deploy_args.mode = "rollback", "plan"
                rollback_plan = M.C.run(deploy_args, live(M.C))
                deploy_args.approved_plan, deploy_args.mode = rollback_plan["plan_sha256"], "apply"
                assert M.C.run(deploy_args, live(M.C))["verdict"] == "completed"
                restored = M.C.read_json(cache / "receipts/rollback.json")
                restored_parameters = {**F.PARAMETERS, "ServerDesiredCount": "1", "ImageDigest": prior["image_digest"], "SourceRevision": prior["source_revision"]}
                for workload, fixture in provider.bindings.items():
                    if workload == "restore-reader": continue
                    fixture.task = {**fixture.task, **M.BINDING.expected_task(workload, restored_parameters, restored["result"]["facts"]["resources"]),
                                    "taskDefinitionArn": fixture.task["taskDefinitionArn"], "status": "ACTIVE"}
                args = SimpleNamespace(receipt=root / "candidate.json", proof_label=binding["proof_label"], expected_predecessor=prior["release_id"],
                    workload="verifier", operation="read", proof_stage="rollback", phase="preflight", expected_digest="1" * 64,
                    rollback_receipt=root / "prior.json", rollback_compatibility_id="rollback-compatibility-" + "8" * 24)
                for phase in ("preflight", "operation"):
                    args.phase = phase
                    context = M.prepare(args, live())
                    assert context["binding"]["source_revision"] == prior["source_revision"]
                    assert context["custody"] == receipt and context["delivery"] == delivery
                    assert context["prerequisites"]["packets"]["deployment"] == restored
                    assert set(context["prerequisites"]["packets"]) == {"deployment", "predecessor"}, "failed candidate prefix must not gate restoration read"
                    args.approved_plan = context["report"]["plan_sha256"]
                    completed = M.execute(args, live())
                    step = M.C.read_json(root / completed["receipt"])
                    assert step["receipt"]["image_digest"] == prior["image_digest"]
                    assert step["reservation"]["request"]["environment"]["ENTITY_SMOKE_EXPECTED_SOURCE"] == prior["source_revision"]
                    before = sum(op == "run-task" for _, op, _ in provider.observed)
                    assert M.execute(args, live())["reused"] is True
                    assert sum(op == "run-task" for _, op, _ in provider.observed) == before
            assert sum(op == "run-task" for _, op, _ in provider.observed) == 2 * len(M.ACCEPTANCE.SUCCESSOR_STEPS) + 2
            assert not (root / ".cache/entity-smoke-live" / binding["proof_label"] / "task-steps").exists()
            for path in cache.rglob("*.json"):
                assert CANARY not in path.read_text() and F.PARAMETERS["AdministratorSecretArn"] not in path.read_text()


def renewal_protocols(provider, args, context, evidence, consumer):
    """Advance controlled time, not retained timestamps; run the real owners."""
    real_datetime = datetime
    offset = timedelta(seconds=901)
    class Later(real_datetime):
        @classmethod
        def now(cls, tz=None): return real_datetime.now(tz) + offset
    timestamp = M.RUNNER.EVIDENCE.timestamp
    policy = M.STEPS.POLICY
    assert not policy.observation_expired("2026-11-20T00:00:00Z", "2026-11-20T00:15:00Z", timestamp)
    assert policy.observation_expired("2026-11-20T00:00:00Z", "2026-11-20T00:15:00.001Z", timestamp)
    original_root = M.C.ROOT
    with tempfile.TemporaryDirectory(prefix="entity-smoke-renewal-") as temporary:
        root = Path(temporary)
        shutil.copytree(original_root / ".cache", root / ".cache")
        remote = copy.deepcopy(provider)
        def live():
            value = M.Provider(); value._invoke = lambda service, operation, parameters: remote(service, operation, **parameters)
            return value
        current = SimpleNamespace(**vars(args))
        with patch.object(M.C, "ROOT", root), patch.dict(globals(), datetime=Later), \
             patch.object(M.C, "datetime", Later), patch.object(M, "datetime", Later), \
             patch.object(M.RUNNER, "datetime", Later), patch.object(M.RUNNER.CONTROL, "datetime", Later), \
             patch.object(M.C.GATE, "datetime", Later):
            before = sum(op == "run-task" for _, op, _ in remote.observed)
            initial = M.prepare(current, live())
            old = initial["report"]["plan"]["preflight_renewal"]["packet"]
            original_bytes = M.RUNNER.CONTROL.canonical(old)
            assert initial["report"]["plan"]["preflight_label"] != old["plan"]["preflight_label"]
            current.approved_plan = initial["report"]["plan_sha256"]
            assert consumer.approved_plan(initial["report"], selection=(current.proof_stage, current.workload, current.operation, current.phase)) == current.approved_plan
            actual_read = M.RUNNER.CONTROL.AttemptStore.read
            digest_reads = {"count": 0}
            def changing_source_read():
                digest_reads["count"] += 1
                return context["artifact"]
            def competing_reservation(store, key, request):
                if digest_reads["count"] > 1 and request["environment"].get(M.RUNNER.CONTROL.OPERATIONS[current.workload][0]) == current.operation:
                    return {"fixture": "concurrent-dependent-reservation"}
                return actual_read(store, key, request)
            with patch.object(M.C, "source_digest", changing_source_read), patch.object(M.RUNNER.CONTROL.AttemptStore, "read", competing_reservation):
                fails(lambda: M.execute(current, live()), "preflight-renewal-operation-already-reserved")
            assert sum(op == "run-task" for _, op, _ in remote.observed) == before
            completed = M.execute(current, live())
            assert completed["verdict"] == "completed" and not completed["reused"]
            fresh = M.C.read_json(root / completed["receipt"])
            assert fresh["reservation"]["operation_id"] != old["reservation"]["operation_id"]
            assert M.RUNNER.CONTROL.canonical(fresh["plan"]["preflight_renewal"]["packet"]) == original_bytes
            archive = evidence.capture_task(M, initial, current, live(), "baseline-permissions", {**context["binding"], "record_digest": "1" * 64})
            assert archive["packet"] == fresh
            changed = copy.deepcopy(fresh)
            changed["plan"]["preflight_renewal"]["packet"]["receipt"]["task"]["stopped_at"] = "2026-01-01T00:00:00Z"
            changed["plan_sha256"] = M.C.DEPLOY.fingerprint(changed["plan"])
            try: M.STEPS.validate_delivery_step(M.dependencies(), changed, context["binding"], context["delivery"], current)
            except (M.STEPS.StepFailure, M.RUNNER.EVIDENCE.EvidenceFailure, M.RUNNER.PREFLIGHT.EVIDENCE.EvidenceFailure): pass
            else: raise AssertionError("altered original renewal custody accepted")
            offset += timedelta(seconds=901)
            fails(lambda: M.prepare(current, live()), "preflight-renewal-exhausted")
            offset -= timedelta(seconds=901)
            current.phase = "operation"
            operation_context = M.prepare(current, live())
            current.approved_plan = operation_context["report"]["plan_sha256"]
            assert M.execute(current, live())["verdict"] == "completed"
            operation_proof = evidence.capture_task(M, operation_context, current, live(), "baseline-permissions", {**context["binding"], "record_digest": "1" * 64})
            assert operation_proof["admission"]["preflight"]["reservation"] == fresh["reservation"]
            # AWS may forget old completed tasks. Historical custody still
            # reconciles; no read of those tasks and no extra launch is allowed.
            remote.remote.clear()
            remote.results.clear()
            for phase in ("preflight", "operation"):
                current.phase = phase
                current.approved_plan = M.plan(current, live())["plan_sha256"]
                result = M.execute(current, live())
                assert result["reused"] and result["effect"] == "historical-task-completion-validated"
            assert sum(op == "run-task" for _, op, _ in remote.observed) == before + 2
    print("ENTITY_SMOKE_EXPIRED_PREFLIGHT_RENEWAL_AND_HISTORY_PASSED")


def successor_recovery_protocols(provider, live, args, binding, delivery, cache, evidence, *, failed_recovery=None):
    """Actual task/replacement/history owners after update, not initial setup."""
    replacement = module("successor_credential_replacement", DIRECTORY / "replacement-route.py")
    replacement.TASK, replacement.C = M, M.C
    selected = lambda workload, operation, phase: SimpleNamespace(**{**vars(args), "proof_stage": "credential-recovery",
        "workload": workload, "operation": operation, "phase": phase})
    observed = sum(op == "run-task" for _, op, _ in provider.observed)
    with patch.object(M.RECOVERY.STATE.STOP.B, "services", return_value=({}, {})), \
         patch.object(M.RECOVERY, "restart", side_effect=AssertionError("accepted successor used initial restart")):
        for name, workload, operation in M.CREDENTIAL.STEPS:
            if name == "read":
                current = SimpleNamespace(**{**vars(args), "mode": "plan", "proof_stage": "credential-recovery", "approved_plan": None, "wait_seconds": 0})
                planned = replacement.run(current, live(replacement))
                current.mode, current.approved_plan = "execute", planned["plan_sha256"]
                provider.replacement_lost = True
                try: replacement.run(current, live(replacement))
                except M.C.RESOURCE.ResourceFailure as error: assert error.code == "resource-submission-uncertain-reconcile-only"
                else: raise AssertionError("lost replacement was reported complete")
                provider.replacement_lost = False
                assert replacement.run(current, live(replacement))["verdict"] == "completed"
                assert sum(op == "stop-task" for _, op, _ in provider.observed) == 1
            for phase in (("operation",) if name == "unready" else ("preflight", "operation")):
                current = selected(workload, operation, phase)
                context = M.prepare(current, live())
                assert context["prerequisites"] is not None
                current.approved_plan = context["report"]["plan_sha256"]
                if phase == "operation" and operation == failed_recovery:
                    provider.fail_operation = operation
                    try: M.execute(current, live())
                    except M.CurrentTaskFailure as failure:
                        assert failure.evidence.terminal["operation"] == operation and failure.evidence.terminal["exit_code"] == 1
                    else: raise AssertionError("expected controlled terminal failure")
                    before = sum(op == "run-task" for _, op, _ in provider.observed)
                    for restore_phase in ("preflight", "operation"):
                        restore_args = selected("administration", "restore-runtime", restore_phase)
                        restore_context = M.prepare(restore_args, live())
                        assert "credential-" + name + "-terminal-failure" in restore_context["prerequisites"]["packets"]
                        restore_args.approved_plan = restore_context["report"]["plan_sha256"]
                        assert M.execute(restore_args, live())["verdict"] == "completed"
                        assert M.execute(restore_args, live())["reused"] is True
                    assert sum(op == "run-task" for _, op, _ in provider.observed) == before + 2
                    assert not (cache / "credential-history.json").exists()
                    print("ENTITY_SMOKE_SUCCESSOR_FAILED_" + name.upper() + "_ACCESS_RESTORATION_PASSED")
                    return
                completed = M.execute(current, live())
                assert completed["verdict"] == "completed"
                proof_name = {"permission-state": "permission-state", "revoke": "credential-revoke", "unready": "credential-unready",
                    "restore": "credential-restore", "read": "credential-read", "permissions": "credential-permissions"}[name]
                archive = evidence.capture_task(M, context, current, live(), proof_name, {**binding, "record_digest": args.expected_digest})
                assert archive["delivery"] == delivery
                before = sum(op == "run-task" for _, op, _ in provider.observed)
                assert M.execute(current, live())["reused"] is True
                assert sum(op == "run-task" for _, op, _ in provider.observed) == before
        history = M.HISTORY.read(M.dependencies(), {**context, "provider": live()}, current)
        assert history["prerequisites"]["packets"]["deployment"] == M.C.read_json(cache / "receipts/update.json")
        assert "initial-stop" not in history["prerequisites"]["packets"] and not (cache / "receipts/create.json").exists()
        assert sum(op == "run-task" for _, op, _ in provider.observed) == observed + 11
        assert history["current_readiness"] is False and history["scope_acceptance"] is False
        before = sum(op == "run-task" for _, op, _ in provider.observed)
        for phase in ("preflight", "operation"):
            restore_args = selected("administration", "restore-runtime", phase)
            restore_args.approved_plan = M.plan(restore_args, live())["plan_sha256"]
            assert M.execute(restore_args, live())["reused"] is True
        assert sum(op == "run-task" for _, op, _ in provider.observed) == before
        successor_restore_protocols(provider, args, binding, delivery, cache)
    print("ENTITY_SMOKE_SUCCESSOR_CREDENTIAL_REQUALIFICATION_PROTOCOLS_PASSED")


def successor_restore_protocols(tasks, args, binding, delivery, cache):
    """Reuse the existing clone fixture with actual successor task/history custody."""
    snapshot = module("successor_snapshot_owner", DIRECTORY / "snapshot-route.py")
    snapshot.TASK, snapshot.C = M, M.C
    clone_fixture = module("successor_restore_fixture", DIRECTORY / "restore-route-test.py")
    class Transport:
        snapshot = None
        jobs, task_rows, other = tasks, tasks.remote, {}
        bindings = tasks.bindings
        def __call__(self, service, operation, **parameters):
            if operation == "describe-db-instances":
                return {"DBInstances": [{"DBInstanceIdentifier": M.C.RESOURCE.SOURCE_DATABASE,
                    "DbiResourceId": F.PARAMETERS["DatabaseResourceId"], "DBName": F.PARAMETERS["DatabaseName"],
                    "DBInstanceStatus": "available", "StorageEncrypted": True, "PubliclyAccessible": False}]}
            if operation == "describe-db-snapshots":
                assert parameters["DBSnapshotIdentifier"] == "kanbien-core-platform-" + delivery["smoke_label"]
                if self.snapshot is None: raise M.C.RESOURCE.ResourceMissing()
                return {"DBSnapshots": [copy.deepcopy(self.snapshot)]}
            if operation == "create-db-snapshot":
                tasks.observed.append((service, operation, parameters))
                assert self.snapshot is None and parameters["DBInstanceIdentifier"] == M.C.RESOURCE.SOURCE_DATABASE
                name = parameters["DBSnapshotIdentifier"]
                self.snapshot = {"DBSnapshotIdentifier": name, "DBSnapshotArn": "arn:aws:rds:eu-west-1:337159794548:snapshot:" + name,
                    "DBInstanceIdentifier": M.C.RESOURCE.SOURCE_DATABASE, "DbiResourceId": F.PARAMETERS["DatabaseResourceId"],
                    "Encrypted": True, "SnapshotType": "manual", "SnapshotCreateTime": datetime.now(timezone.utc).isoformat(), "Status": "available"}
                self.tags = parameters["Tags"]
                return {}
            if operation == "list-tags-for-resource" and self.snapshot and parameters["ResourceName"] == self.snapshot["DBSnapshotArn"]:
                return {"TagList": copy.deepcopy(self.tags)}
            result = tasks(service, operation, **parameters)
            if operation == "describe-services":
                for row in result["services"]:
                    row.update(launchType="FARGATE", networkConfiguration={"awsvpcConfiguration": {
                        "assignPublicIp": "DISABLED", "subnets": F.PARAMETERS["PrivateSubnetIds"].split(","),
                        "securityGroups": [BF.RESOURCES["ServerSecurityGroup"]["physical_id"]]}})
            return result
    transport = Transport()
    def capability():
        value = snapshot.Provider()
        value._invoke = lambda service, operation, parameters: transport(service, operation, **parameters)
        return value
    selected = SimpleNamespace(**{**vars(args), "mode": "plan", "approved_plan": None, "wait_seconds": 0})
    plan = snapshot.run(selected, capability())
    selected.mode, selected.approved_plan = "execute", plan["plan_sha256"]
    assert snapshot.run(selected, capability())["verdict"] == "completed"
    assert snapshot.run(selected, capability())["verdict"] == "completed"
    assert sum(op == "create-db-snapshot" for _, op, _ in tasks.observed) == 1
    case = SimpleNamespace(transport=transport, root=M.C.ROOT, cache=cache, binding=binding,
        predecessor=M.ACCEPTANCE.acceptance_owner().successor_parent(None, args))
    clone_fixture.run(case, selected, snapshot, M, CANARY)


def transport_read_protocols():
    """Actual task provider transport, controlled CLI responses; never AWS."""
    original_run, original_parse, original_plan = M.C.subprocess.run, M.parse, M.plan
    try:
        reads = {("ecs", "describe-task-definition"), ("ecs", "list-services"), ("ec2", "describe-security-groups"),
                 ("iam", "list-role-policies"), ("iam", "list-attached-role-policies"), ("iam", "get-role-policy"),
                 ("rds", "describe-db-snapshots"), ("rds", "list-tags-for-resource")}
        assert reads <= M.READS == M.C.READS
        for service, operation in sorted(reads):
            endpoint = "https://iam.amazonaws.com/" if service == "iam" else "https://" + service + ".eu-west-1.amazonaws.com/"
            for scenario, count in (("recover", 2), ("exhaust", 3), ("process-timeout", 3), ("denied", 1), ("foreign", 1)):
                attempts = []
                def transport(arguments, **options):
                    attempts.append(arguments)
                    assert options["env"]["AWS_MAX_ATTEMPTS"] == "1"
                    if scenario == "recover" and len(attempts) == 2: return SimpleNamespace(returncode=0, stdout='{"observed":true}', stderr="")
                    if scenario == "process-timeout": raise subprocess.TimeoutExpired(arguments, 30, stderr=CANARY)
                    error = 'aws: [ERROR]: Connect timeout on endpoint URL: "' + ("https://foreign.invalid/" if scenario == "foreign" else endpoint) + '"'
                    if scenario == "denied": error = "An error occurred (AccessDenied) when calling the Read operation: " + CANARY
                    return SimpleNamespace(returncode=255, stdout="", stderr=error)
                M.C.subprocess.run = transport
                provider = M.Provider()
                if scenario == "recover": assert provider(service, operation)["observed"] is True
                else:
                    try: provider(service, operation)
                    except M.C.InfrastructureFailure as failure:
                        assert failure.provider_operation == (service, operation)
                        assert failure.code == ("aws-access-denied" if scenario == "denied" else "infrastructure-provider-observation-unavailable" if scenario == "process-timeout" else "aws-command-failed")
                    else: raise AssertionError("expected read failure")
                assert len(attempts) == count and provider.effect == "not-started"
        # Transport never retries RunTask, even for the same endpoint timeout.
        for process_timeout in (False, True):
            attempts = []
            def mutation_transport(arguments, **options):
                attempts.append(arguments)
                if process_timeout: raise subprocess.TimeoutExpired(arguments, 30)
                return SimpleNamespace(returncode=255, stdout="", stderr='aws: [ERROR]: Connect timeout on endpoint URL: "https://ecs.eu-west-1.amazonaws.com/"')
            M.C.subprocess.run = mutation_transport
            try: M.Provider()._invoke("ecs", "run-task", {})
            except M.C.InfrastructureFailure: pass
            else: raise AssertionError("expected mutation transport failure")
            assert len(attempts) == 1
        M.parse = lambda: SimpleNamespace(workload="database-proof", operation="permissions", phase="preflight", proof_stage="baseline", proof_label="entity-smoke-" + "a" * 24, validate_arguments=False, execute=False)
        def denied_plan(*args): raise M.C.InfrastructureFailure("aws-command-failed", provider_operation=("ecs", "describe-task-definition"))
        M.plan = denied_plan
        output = io.StringIO()
        with redirect_stdout(output): result = M.main()
        reported = json.loads(output.getvalue())
        assert result == 1 and reported["context"]["provider_operation"] == "ecs/describe-task-definition" and reported["effect"] == "not-started" and CANARY not in output.getvalue()
    finally:
        M.C.subprocess.run, M.parse, M.plan = original_run, original_parse, original_plan
    print("ENTITY_SMOKE_TASK_READ_TRANSPORT_PROTOCOLS_PASSED")


if __name__ == "__main__":
    successor_task_protocols()
    successor_task_protocols(requalify=True)
    successor_task_protocols(requalify=True, failed_recovery="revoke-runtime")
    successor_task_protocols(requalify=True, failed_recovery="unready")
    transport_read_protocols()
    run()
