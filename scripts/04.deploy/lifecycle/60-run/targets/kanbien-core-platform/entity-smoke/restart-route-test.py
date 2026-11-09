#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.initial-restart
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual stop custody, prior collected read and gated single-restart consumers with shared controlled provider protocols, not AWS proof.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
from contextlib import contextmanager, redirect_stdout
import copy
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import importlib.util
import json
import io
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

if not __debug__: raise SystemExit("ENTITY_SMOKE_RESTART_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
R = module("entity_smoke_restart_fixture", DIRECTORY / "restart-route.py")
FD = module("entity_smoke_restart_stop_producer", DIRECTORY / "failure-route-test.py")
TD = module("entity_smoke_restart_task_producer", DIRECTORY / "task-route-test.py")
R.C = R.TASK.C = FD.M.C
R.STATE.STOP = FD.M
R.TASK.RECOVERY.STATE = R.STATE
CANARY = FD.CANARY
RECOVERED = FD.PREFIX + "task/kanbien-core-platform/" + "4" * 32


class Transport(FD.Transport):
    def __init__(self):
        super().__init__()
        self.jobs = TD.Provider(); self.jobs.created_record = True
        self.starting, self.lost_start = False, False
        self.hold_next = False
        self.network_override = None

    def service(self):
        expected = {"awsvpcConfiguration": {"assignPublicIp": "DISABLED", "subnets": FD.F.PARAMETERS["PrivateSubnetIds"].split(","), "securityGroups": [FD.BF.RESOURCES["ServerSecurityGroup"]["physical_id"]]}}
        return {**super().service(), "launchType": "FARGATE", "networkConfiguration": expected if self.network_override is None else copy.deepcopy(self.network_override)}

    def __call__(self, service_name, operation, **parameters):
        if operation == "run-task":
            try:
                response = self.jobs(service_name, operation, **parameters)
                if self.hold_next:
                    for task in response["tasks"]:
                        task["lastStatus"] = self.jobs.remote[task["taskArn"]]["lastStatus"] = "RUNNING"
                    self.hold_next = False
                return response
            finally:
                for arn, row in self.jobs.remote.items():
                    copied = copy.deepcopy(row)
                    copied["group"] = "family:" + copied["taskDefinitionArn"].split("/")[1].split(":")[0]
                    self.task_rows[arn] = copied
        if operation == "get-log-events": return self.jobs(service_name, operation, **parameters)
        if operation in {"get-role", "list-role-policies", "list-attached-role-policies", "get-role-policy", "describe-security-groups"} and parameters.get("RoleName") != "ApprovedOperator":
            return self.bindings["administration"](service_name, operation, **parameters)
        if operation == "update-service" and parameters.get("desiredCount") == 1:
            self.observed.append((service_name, operation, copy.deepcopy(parameters)))
            assert parameters == {"cluster": R.C.RESOURCE.CLUSTER, "service": R.C.RESOURCE.SERVICE, "desiredCount": 1}
            self.before_write(operation, parameters)
            self.desired, self.server_running = 1, not self.starting
            now = datetime.now(timezone.utc).isoformat()
            self.task_rows[RECOVERED] = {"taskArn": RECOVERED, "taskDefinitionArn": FD.BF.RESOURCES["ServerTaskDefinition"]["physical_id"], "group": "service:" + R.C.RESOURCE.SERVICE,
                                       "launchType": "FARGATE", "lastStatus": "PENDING" if self.starting else "RUNNING", "healthStatus": "HEALTHY", "createdAt": now, "startedAt": now,
                                       "containers": [{"name": "entity-smoke-server", **({} if self.starting else {"imageDigest": FD.F.BINDING["image_digest"]})}]}
            if self.lost_start: raise OSError(CANARY)
            return {}
        return super().__call__(service_name, operation, **parameters)


@contextmanager
def scenario(*, network_override=None, transport_factory=Transport):
    with FD.scenario(transport_factory=transport_factory) as case:
        case.transport.stack["StackStatus"] = "UPDATE_COMPLETE"
        case.transport.network_override = network_override
        case.transport.stopped(FD.MIGRATION)
        case.transport.task_rows[FD.SERVER]["healthStatus"] = "HEALTHY"
        case.transport.task_rows[FD.SERVER]["containers"][0]["imageDigest"] = case.binding["image_digest"]
        R.C.RESOURCE.write_exclusive(case.cache / "receipts/create.json", {"schema": "deploy/entity-smoke-infrastructure-receipt/v1", "binding": case.binding, "result": case.creation})
        # Seed a controlled preexisting labelled record through the real runner,
        # collector, admission and step stores, before reserving the real stop.
        # This is a local task protocol, not an actual database/history claim.
        args = SimpleNamespace(**{**vars(case.args), "workload": "verifier", "operation": "read", "proof_stage": "server-replacement", "phase": "preflight", "expected_digest": "1" * 64})
        parameters, resources = R.TASK.owned_stack(case.transport, case.binding, FD.F.PARAMETERS, case.cache)
        snapshot = R.TASK.BINDING.DEPLOY.source()[1]
        checked = R.TASK.BINDING.inspect(case.transport, "verifier", parameters, resources, snapshot)
        label = "entity-smoke-" + hashlib.sha256((args.proof_label + ":verifier:read:preflight:server-replacement").encode()).hexdigest()[:24]
        declaration = R.C.yaml.safe_load((R.C.CONTRACT.parent / "declaration-contract.yml").read_text())
        deadlines = {row["id"].removeprefix("entity-smoke-"): row["completion"]["deadline_seconds"] for row in declaration["health_recovery"]["workloads"] if "completion" in row}
        context = {"binding": case.binding, "cache": case.cache, "parameters": parameters, "resources": resources, "checked": checked,
                   "completion_deadlines": deadlines, "report": {"plan": {"preflight_label": label}, "plan_sha256": "sha256:" + "1" * 64}}
        runner, steps = R.TASK.RUNNER, R.TASK.STEPS
        store = runner.CONTROL.AttemptStore(case.cache / "task-attempts")
        for phase in ("preflight", "operation"):
            args.phase = phase
            request = steps.request(R.TASK.dependencies(), context, args)
            options = {} if phase == "preflight" else {"preflight": probe, "required_after": case.creation["reservation"]["reserved_at"]}
            result = runner.run_owned_task(case.transport, store, steps.key(args), request, case.cache / "task-receipts", **options)
            reservation = store.read(steps.key(args), request)
            step = steps.retain(R.TASK.dependencies(), context, args, reservation, result["receipt"])
            graph = R.TASK.GRAPH.contract(args.workload, R.C.GATE)
            book = R.C.GateBook(R.C.source_digest(), case.cache / "task-realization", contract=graph,
                                artifact_bindings={row["id"]: R.C.source_digest() if row["id"] == R.TASK.GRAPH.CONTROLLER_SOURCE else case.binding["image_digest"] for row in graph["artifacts"]})
            for identifier in book.known: book.component(identifier)
            book.bind_plan(context["report"]["plan_sha256"])
            for gate in R.C.GATE.GATE_ORDER[:7]: book.gate(gate)
            evidence = book.validate("controlled-execution", 1)
            R.TASK.COMPLETION.retain(R.TASK.dependencies(), context, args, step, evidence)
            if phase == "preflight": probe = {"reservation": reservation, "receipt": result["receipt"], "label": label}
        plan = FD.M.run(case.args, case.capability())
        case.args.mode, case.args.approved_plan = "execute", plan["plan_sha256"]
        stopped = FD.M.run(case.args, case.capability())
        assert stopped["verdict"] == "completed"
        case.restart_args = SimpleNamespace(**{**vars(case.args), "mode": "plan", "approved_plan": None, "expected_digest": "1" * 64})
        def capability():
            provider = R.Provider()
            provider._invoke = lambda service, operation, parameters: case.transport(service, operation, **parameters)
            return provider
        case.restart_capability = capability
        old_inspect = R.C.ALIGN.inspect
        R.C.ALIGN.inspect = lambda provider, custody, checked: ({"dependency_incarnation_sha256": case.binding["dependency_incarnation_sha256"]}, copy.deepcopy(FD.F.PARAMETERS), "controlled-private-subnet-group")
        try: yield case
        finally: R.C.ALIGN.inspect = old_inspect


def fails(call, code):
    try: call()
    except R.known() + R.TASK.RECOVERY.failures() as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
        return failure
    else: raise AssertionError("expected bounded restart rejection")


def plan(case):
    planned = R.run(case.restart_args, case.restart_capability())
    assert planned["verdict"] == "planned" and planned["plan"]["maximum_service_updates"] == 1
    assert planned["plan"]["independent_data_readback"] is False and planned["plan"]["migration_history_readback"] is False
    assert CANARY not in json.dumps(planned)
    case.restart_args.mode, case.restart_args.approved_plan = "execute", planned["plan_sha256"]
    return planned


def execute_task(case, workload, operation, phase):
    selected = SimpleNamespace(**{**vars(case.restart_args), "workload": workload, "operation": operation, "phase": phase, "proof_stage": "initial-recovery", "execute": False})
    def provider():
        value = R.TASK.Provider()
        value._invoke = lambda service, action, parameters: case.transport(service, action, **parameters)
        return value
    planned = R.TASK.plan(selected, provider())
    assert planned["plan"]["execution_route_available"] is True
    selected.approved_plan = planned["plan_sha256"]
    return R.TASK.execute(selected, provider()), selected


def run():
    with scenario() as case:
        planned = plan(case); before = copy.deepcopy(case.transport.other)
        def reserved_and_locked(operation, parameters):
            path = case.cache / "attempts" / (case.args.proof_label + "-start-runtime.json")
            assert path.is_file() and path.stat().st_mode & 0o777 == 0o600
            descriptor = os.open(case.evidence / ".release-succession.lock", os.O_RDWR)
            try:
                try: fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError: pass
                else: raise AssertionError("actual succession lock must guard restart I/O")
            finally: os.close(descriptor)
        case.transport.before_write = reserved_and_locked
        result = R.run(case.restart_args, case.restart_capability())
        assert result["verdict"] == "completed" and result["independent_data_readback"] is False
        assert case.transport.other == before
        assert R.run(case.restart_args, case.restart_capability())["historical"] is True
        assert sum(op == "update-service" and args["desiredCount"] == 1 for _, op, args in case.transport.observed) == 1
        task_args = SimpleNamespace(**{**vars(case.restart_args), "workload": "administration", "operation": "observe-migration-state", "phase": "preflight", "proof_stage": "initial-recovery", "execute": False})
        premature = R.TASK.plan(task_args, case.restart_capability())
        assert premature["plan"]["pending_prerequisite"] == "initial-recovery-original-read" and premature["plan"]["execution_route_available"] is False
        execute_task(case, "verifier", "read", "preflight")
        observed, read_args = execute_task(case, "verifier", "read", "operation")
        read = R.C.read_json(case.root / observed["receipt"])
        assert read["receipt"]["result"]["record_digest"] == "1" * 64
        assert R.TASK.RUNNER.EVIDENCE.timestamp(read["receipt"]["task"]["created_at"]) >= R.TASK.RUNNER.EVIDENCE.timestamp(R.C.read_json(case.cache / "initial-restart-receipt.json")["server"]["started_at"])
        execute_task(case, "administration", "observe-migration-state", "preflight")
        history_result, history_args = execute_task(case, "administration", "observe-migration-state", "operation")
        history = R.C.read_json(case.root / history_result["receipt"])
        assert history["receipt"]["result"]["code"] == "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED"
        assert history["reservation"]["request"]["environment"] == {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "observe-migration-state"}
        assert R.TASK.RUNNER.EVIDENCE.timestamp(history["receipt"]["task"]["created_at"]) >= R.TASK.RUNNER.EVIDENCE.timestamp(read["receipt"]["task"]["stopped_at"])
        assert len(case.transport.jobs.remote) == 6, "two historical and four separately admitted recovery jobs only"
        for path in case.cache.rglob("*.json"): assert CANARY not in path.read_text()

    for missing, code in (("failure-receipts/stopped.json", "recovery-stop-receipt-required"),
                          ("task-steps/verifier-read-server-replacement-operation.json", "recovery-pre-stop-original-read-required")):
        with scenario() as case:
            source = case.cache / missing; source.rename(source.with_suffix(".temporarily-moved"))
            fails(lambda: R.run(case.restart_args, case.restart_capability()), code)
            assert not any(op == "update-service" and args["desiredCount"] == 1 for _, op, args in case.transport.observed)

    with scenario() as case:
        plan(case); case.restart_args.approved_plan = "sha256:" + "0" * 64
        fails(lambda: R.run(case.restart_args, case.restart_capability()), "restart-approved-plan-mismatch")
        assert not any(op == "update-service" and args["desiredCount"] == 1 for _, op, args in case.transport.observed)

    with scenario() as case:
        plan(case); case.transport.other[0]["desiredCount"] = 2
        fails(lambda: R.run(case.restart_args, case.restart_capability()), "failure-other-service-configuration-changed")
        assert not any(op == "update-service" and args["desiredCount"] == 1 for _, op, args in case.transport.observed)

    with scenario() as case:
        case.transport.task_rows[FD.MIGRATION]["lastStatus"] = "RUNNING"
        fails(lambda: R.run(case.restart_args, case.restart_capability()), "restart-active-owned-job-not-permitted")

    with scenario() as case:
        plan(case); case.transport.lost_start = True
        fails(lambda: R.run(case.restart_args, case.restart_capability()), "resource-submission-uncertain-reconcile-only")
        assert R.run(case.restart_args, case.restart_capability())["verdict"] == "completed"
        assert sum(op == "update-service" and args["desiredCount"] == 1 for _, op, args in case.transport.observed) == 1

    with scenario(network_override={"awsvpcConfiguration": {"assignPublicIp": "ENABLED", "subnets": FD.F.PARAMETERS["PrivateSubnetIds"].split(","), "securityGroups": [FD.BF.RESOURCES["ServerSecurityGroup"]["physical_id"]]}}) as case:
        fails(lambda: R.run(case.restart_args, case.restart_capability()), "recovery-runtime-network-not-confirmed")
        assert not any(op == "update-service" and args["desiredCount"] == 1 for _, op, args in case.transport.observed), "unchanged but unqualified original service networking must still reject"

    with scenario() as case:
        plan(case); case.transport.starting = True
        for _ in range(2): assert R.run(case.restart_args, case.restart_capability())["verdict"] == "pending"
        case.transport.task_rows[RECOVERED]["containers"][0]["imageDigest"] = "sha256:" + "0" * 64
        fails(lambda: R.run(case.restart_args, case.restart_capability()), "resource-server-task-identity-not-confirmed")
        case.transport.task_rows[RECOVERED]["containers"][0]["imageDigest"] = case.binding["image_digest"]
        case.transport.task_rows[RECOVERED]["lastStatus"] = "RUNNING"; case.transport.server_running = True
        assert R.run(case.restart_args, case.restart_capability())["verdict"] == "completed"
        assert sum(op == "update-service" and args["desiredCount"] == 1 for _, op, args in case.transport.observed) == 1

    with scenario() as case:
        path = case.cache / "task-steps/verifier-read-server-replacement-operation.json"
        value = R.C.read_json(path); reservation = value["reservation"]
        task = case.transport.task_rows[value["receipt"]["task"]["arn"]]
        root = R.C.read_json(case.cache / "failure-attempts/root.json")
        late = (R.C.RESOURCE.timestamp(root["reserved_at"]) + timedelta(seconds=10)).isoformat()
        task.update(createdAt=late, startedAt=late, stoppedAt=late)
        result = case.transport.jobs.results[task["taskArn"].split("/")[-1]]; result["checked_at"] = late
        receipt = R.TASK.RUNNER.EVIDENCE.collect(task, reservation, {"events": [{"message": json.dumps(result)}]}, late)
        value["receipt"] = receipt; path.write_text(json.dumps(value))
        # Keep this synthetic counterexample's byte linkage consistent so the
        # original late-read predicate, not the independent tamper guard, is
        # what rejects it. No real retained evidence is modified by this test.
        completion = R.TASK.COMPLETION.path(path)
        linked = R.C.read_json(completion); linked["step_sha256"] = R.C.digest_file(path)
        completion.write_text(json.dumps(linked))
        retained = R.TASK.RUNNER.receipt_path(case.cache / "task-receipts", reservation["request"], reservation)
        retained.write_text(json.dumps(receipt))
        fails(lambda: R.run(case.restart_args, case.restart_capability()), "recovery-original-read-not-before-stop")

    with scenario() as case:
        prepared = R.prepare(case.restart_args, case.restart_capability())
        store, request = prepared["store"], prepared["packet"]["request"]
        store.reserve("start-runtime", request)
        provider = case.restart_capability(); calls = []
        provider._invoke = lambda *args: calls.append(args)
        denial = R.TASK.BINDING.BindingFailure("task-binding-policy-not-confirmed", "server", "roles", "execution-role")
        def denied(): raise denial
        provider.enable_restart(store, request, denied)
        payload = {"cluster": R.C.RESOURCE.CLUSTER, "service": R.C.RESOURCE.SERVICE, "desiredCount": 1}
        for changed in ({"desiredCount": True}, {"desiredCount": 2}, {"service": "another-service"}, {"forceNewDeployment": True}):
            fails(lambda: provider("ecs", "update-service", **{**payload, **changed}), "restart-submission-does-not-match-plan")
        fails(lambda: provider("ecs", "update-service", **payload), "task-binding-policy-not-confirmed")
        assert provider.rejected_failure is denial and calls == [] and provider.effect == "not-started"

    with scenario() as case:
        plan(case); R.run(case.restart_args, case.restart_capability())
        execute_task(case, "verifier", "read", "preflight"); execute_task(case, "verifier", "read", "operation")
        execute_task(case, "administration", "observe-migration-state", "preflight")
        case.transport.jobs.history_applied = False
        fails(lambda: execute_task(case, "administration", "observe-migration-state", "operation"), "recovery-migration-history-not-applied")
        assert not (case.cache / "task-steps/administration-observe-migration-state-initial-recovery-operation.json").exists()
        before = len(case.transport.jobs.remote)
        fails(lambda: execute_task(case, "administration", "observe-migration-state", "operation"), "recovery-migration-history-not-applied")
        assert len(case.transport.jobs.remote) == before, "unsuitable terminal history result cannot authorize another observation launch"
        selected = SimpleNamespace(**{**vars(case.restart_args), "workload": "administration", "operation": "observe-migration-state", "phase": "operation", "proof_stage": "initial-recovery", "execute": True, "validate_arguments": False})
        def task_provider():
            value = R.TASK.Provider(); value._invoke = lambda service, action, parameters: case.transport(service, action, **parameters)
            return value
        selected.approved_plan = R.TASK.plan(selected, task_provider())["plan_sha256"]
        old_parse, old_factory = R.TASK.parse, R.TASK.Provider
        R.TASK.parse, R.TASK.Provider = lambda: selected, task_provider
        output = io.StringIO()
        # The factory must use the original class while the actual main reporter runs.
        def main_provider():
            value = old_factory(); value._invoke = lambda service, action, parameters: case.transport(service, action, **parameters)
            return value
        R.TASK.Provider = main_provider
        try:
            with redirect_stdout(output): status = R.TASK.main()
        finally: R.TASK.parse, R.TASK.Provider = old_parse, old_factory
        rejected = json.loads(output.getvalue())
        assert status == 1 and rejected["condition"] == "recovery-migration-history-not-applied" and rejected["effect"] == "terminal-task-observed-proof-not-confirmed"
        assert rejected["context"]["proof_stage"] == "initial-recovery" and CANARY not in output.getvalue() and len(case.transport.jobs.remote) == before

    with scenario() as case:
        plan(case); R.run(case.restart_args, case.restart_capability())
        retained = R.C.read_json(case.cache / "initial-restart-receipt.json")
        gate = case.root / retained["realization_evidence"]; original_gate = gate.read_bytes(); gate.write_text('{}')
        args = SimpleNamespace(**{**vars(case.restart_args), "workload": "verifier", "operation": "read", "phase": "operation", "proof_stage": "initial-recovery"})
        fails(lambda: R.TASK.plan(args, case.restart_capability()), "recovery-restart-gate-changed")
        gate.write_bytes(original_gate)
        journal = case.cache / "attempts" / (case.args.proof_label + "-start-runtime.json")
        moved = journal.with_suffix(".temporarily-moved"); journal.rename(moved)
        fails(lambda: R.TASK.plan(args, case.restart_capability()), "recovery-step-restart-journal-required")
        moved.rename(journal)
        old = R.C.read_json(case.cache / "task-steps/verifier-read-server-replacement-operation.json")
        runner, steps = R.TASK.RUNNER, R.TASK.STEPS
        store = runner.CONTROL.AttemptStore(case.cache / "task-attempts")
        staged_path = store.path_for(steps.key(args), old["reservation"]["request"])
        assert R.C.RESOURCE.write_exclusive(staged_path, old["reservation"])
        old_step_path = steps.path({"cache": case.cache}, args)
        assert R.C.RESOURCE.write_exclusive(old_step_path, old)
        prepared = R.TASK.plan(args, case.restart_capability()); args.approved_plan = prepared["plan_sha256"]
        count = len(case.transport.jobs.remote)
        provider = R.TASK.Provider(); provider._invoke = lambda service, action, parameters: case.transport(service, action, **parameters)
        fails(lambda: R.TASK.execute(args, provider), "task-state-observation-not-fresh")
        assert len(case.transport.jobs.remote) == count, "copied old stage/journal cannot become a post-restart observation"

    with scenario() as case:
        precise = datetime(2026, 11, 8, 12, 0, 0, 123456, timezone.utc)
        class Clock:
            @staticmethod
            def now(zone): assert zone is timezone.utc; return precise
        old_clock, old_now = FD.M.F.datetime, R.C.now
        FD.M.F.datetime, R.C.now = Clock, lambda: precise.strftime("%Y-%m-%dT%H:%M:%SZ")
        try: reservation, _ = FD.M.F.StopStore(R.C, case.cache / "precision-witness").reserve("root", {"fixture": "precision-witness"})
        finally: FD.M.F.datetime, R.C.now = old_clock, old_now
        assert R.C.RESOURCE.timestamp(reservation["reserved_at"]) == precise, "stop producer must retain actual fractions, not the common rounded clock"

    with scenario() as case:
        plan(case); R.run(case.restart_args, case.restart_capability())
        execute_task(case, "verifier", "read", "preflight")
        case.transport.hold_next = True
        old_run = R.TASK.RUNNER.run_owned_task
        ticks = [0]
        def monotonic(): ticks[0] += 1000; return ticks[0]
        def bounded(*args, **options): return old_run(*args, **{**options, "monotonic": monotonic, "sleep": lambda _: None})
        R.TASK.RUNNER.run_owned_task = bounded
        try: fails(lambda: execute_task(case, "verifier", "read", "operation"), "task-deadline-remote-operation-not-terminal")
        finally: R.TASK.RUNNER.run_owned_task = old_run
        active = [arn for arn, task in case.transport.task_rows.items() if task.get("lastStatus") == "RUNNING" and task.get("group", "").startswith("family:")]
        assert len(active) == 1
        count = len(case.transport.jobs.remote)
        args = SimpleNamespace(**{**vars(case.restart_args), "workload": "verifier", "operation": "read", "phase": "operation", "proof_stage": "initial-recovery"})
        assert R.TASK.plan(args, case.restart_capability())["plan"]["execution_route_available"] is True, "the exact running reserved job must remain observable, not become unplanned work"
        for arn in active:
            case.transport.task_rows[arn]["lastStatus"] = case.transport.jobs.remote[arn]["lastStatus"] = "STOPPED"
        observed, _ = execute_task(case, "verifier", "read", "operation")
        assert observed["reused"] is False and len(case.transport.jobs.remote) == count, "actual reserved job reconciles without a second launch"

    with scenario() as case:
        plan(case)
        original_current = FD.M.SUCCESSION.current
        def acceptance_during_guard():
            target = case.evidence / ".release-succession.lock"
            if not target.exists(): return
            descriptor = os.open(target, os.O_RDWR)
            try:
                try: fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError: FD.M.SUCCESSION.current = lambda root: {"target": R.C.RESOURCE.CLUSTER, "scope": "entity-smoke", "release_id": "a" * 64}
                else: fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally: os.close(descriptor)
        case.transport.during_simulation = acceptance_during_guard
        try: fails(lambda: R.run(case.restart_args, case.restart_capability()), "failure-initial-policy-not-applicable")
        finally: FD.M.SUCCESSION.current = original_current
        assert not any(op == "update-service" and args["desiredCount"] == 1 for _, op, args in case.transport.observed)

    denied = R.Provider()
    denied._invoke = lambda *args: (_ for _ in ()).throw(AssertionError("prohibited effect reached transport"))
    denied.enable(("cloudformation", "execute-change-set"), lambda *args: None)
    fails(lambda: denied("cloudformation", "execute-change-set", StackName=R.C.DEPLOY.STACK), "restart-provider-operation-prohibited")
    fails(lambda: denied("ecs", "run-task", cluster=R.C.RESOURCE.CLUSTER), "restart-provider-operation-prohibited")

    with scenario() as case:
        case.transport.task_rows[FD.SERVER]["taskDefinitionArn"] = case.transport.task_rows[FD.SERVER]["taskDefinitionArn"].rsplit(":", 1)[0] + ":2"
        provider = case.restart_capability()
        old_parse, old_factory = R.parse, R.Provider
        R.parse, R.Provider = lambda: case.restart_args, lambda: provider
        output = io.StringIO()
        try:
            with redirect_stdout(output): status = R.main()
        finally: R.parse, R.Provider = old_parse, old_factory
        rejected = json.loads(output.getvalue())
        assert status == 1 and rejected["condition"] == "failure-original-task-identity-changed" and rejected["context"]["item"] == "server"
        assert rejected["effect"] == "not-started" and CANARY not in output.getvalue()
        assert not any(op == "update-service" and args["desiredCount"] == 1 for _, op, args in case.transport.observed)

    with scenario() as case:
        plan(case); R.run(case.restart_args, case.restart_capability())
        selected = SimpleNamespace(**{**vars(case.restart_args), "workload": "verifier", "operation": "read", "phase": "preflight", "proof_stage": "initial-recovery", "execute": True, "validate_arguments": False})
        def provider():
            value = R.TASK.Provider(); value._invoke = lambda service, operation, parameters: case.transport(service, operation, **parameters)
            return value
        selected.approved_plan = R.TASK.plan(selected, provider())["plan_sha256"]
        old_parse, old_factory, old_enable = R.TASK.parse, R.TASK.Provider, R.TASK.Provider.enable_task
        def changed_original_at_guard(self, request, store, key, guard):
            def changed():
                case.transport.task_rows[FD.SERVER]["taskDefinitionArn"] = case.transport.task_rows[FD.SERVER]["taskDefinitionArn"].rsplit(":", 1)[0] + ":2"
                guard()
            return old_enable(self, request, store, key, changed)
        old_factory.enable_task = changed_original_at_guard
        def main_provider():
            value = old_factory(); value._invoke = lambda service, operation, parameters: case.transport(service, operation, **parameters)
            return value
        R.TASK.parse, R.TASK.Provider = lambda: selected, main_provider
        output = io.StringIO(); before = len(case.transport.jobs.remote)
        try:
            with redirect_stdout(output): status = R.TASK.main()
        finally:
            R.TASK.parse, R.TASK.Provider = old_parse, old_factory
            old_factory.enable_task = old_enable
        rejected = json.loads(output.getvalue())
        assert status == 1 and rejected["condition"] == "failure-original-task-identity-changed"
        assert rejected["context"]["field"] == "prerequisite" and rejected["context"]["item"] == "server" and rejected["effect"] == "not-started"
        assert CANARY not in output.getvalue() and len(case.transport.jobs.remote) == before

    with tempfile.TemporaryDirectory(prefix="entity-smoke-restart-cli-") as temporary:
        root = Path(temporary); marker = root / "aws-called"
        sentinel = root / "aws"; sentinel.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\nraise SystemExit(99)\n"); sentinel.chmod(0o700)
        env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"]}
        common = ["--receipt", str(root / "missing.json"), "--proof-label", FD.F.BINDING["proof_label"], "--expected-digest", "1" * 64]
        for suffix, verdict in ((["--mode", "plan", "--validate-arguments"], "valid"), (["--mode", "execute"], "blocked"),
                                (["--mode", "plan"], "blocked"), (["--mode", "plan", "--unknown", CANARY], "blocked")):
            result = subprocess.run(["bash", str(DIRECTORY / "restart.sh"), *common, *suffix], cwd=FD.REAL_ROOT, env=env, capture_output=True, text=True)
            assert json.loads(result.stdout)["verdict"] == verdict and CANARY not in result.stdout + result.stderr and "Traceback" not in result.stderr
            assert not marker.exists()
        task = ["--receipt", str(root / "missing.json"), "--proof-label", FD.F.BINDING["proof_label"], "--proof-stage", "initial-recovery", "--workload", "administration", "--operation", "observe-migration-state", "--validate-arguments"]
        for suffix, expected in (([], "blocked"), (["--expected-digest", "1" * 64], "valid")):
            result = subprocess.run(["bash", str(DIRECTORY / "task-plan.sh"), *task, *suffix], cwd=FD.REAL_ROOT, env=env, capture_output=True, text=True)
            assert json.loads(result.stdout)["verdict"] == expected and not marker.exists()

    print(json.dumps({"schema": "deploy/entity-smoke-initial-restart-fixture/v1", "verdict": "passed", "provider_observation": False,
                      "prerequisites": "shared-controlled-source-custody-existing-record-task-and-provider-protocol-not-qualification", "cases": ["real-pre-stop-collected-read", "actual-policy-and-custody-lock", "reserved-count-one-only", "qualified-new-runtime", "unchanged-other-services", "historical-no-second-start", "separate-ready-and-original-read", "history-after-read-only", "applied-history-not-replay-permission", "administrator-digest-not-an-override", "missing-prerequisites-no-start", "wrong-approval-no-start", "changed-baseline-no-start", "unplanned-job-no-start", "lost-start-no-replay", "pending-unpulled-not-complete", "wrong-pending-image-rejected", "fractional-before-stop-order", "genuinely-late-read-rejected", "exact-payload-before-io", "known-prewrite-identity", "history-real-main-condition", "changed-gate-and-missing-journal", "old-stage-copied-journal", "precise-clock-producer", "fresh-custody-at-io", "no-inherited-capabilities", "actual-offline-cli", "unqualified-original-network", "running-owned-job-reconciles"]}))


if __name__ == "__main__": run()
