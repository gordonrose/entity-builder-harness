#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.credential-route
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual credential stage, bounded negative admission and reserved replacement consumers with controlled shared task/provider protocols, not AWS or database proof.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
from contextlib import contextmanager, redirect_stdout
import copy
from datetime import datetime, timezone
import importlib.util
import json
import io
from pathlib import Path
from types import SimpleNamespace

if not __debug__: raise SystemExit("ENTITY_SMOKE_CREDENTIAL_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
I = module("entity_smoke_credential_initial_fixture", DIRECTORY / "restart-route-test.py")
R, FD = I.R, I.FD
T = R.TASK
RP = module("entity_smoke_credential_replacement_fixture", DIRECTORY / "replacement-route.py")
RP.TASK, RP.C = T, R.C
S = module("entity_smoke_snapshot_fixture", DIRECTORY / "snapshot-route.py")
S.TASK, S.C = T, R.C
CANARY = I.CANARY
SUCCESSOR = FD.PREFIX + "task/kanbien-core-platform/" + "5" * 32


class Transport(I.Transport):
    def __init__(self):
        super().__init__()
        self.access, self.wrong_negative, self.lost_replacement = True, False, False
        self.snapshot, self.lost_snapshot, self.deny_snapshot = None, False, False
        self.database_ready = False

    def __call__(self, service_name, operation, **parameters):
        if operation == "describe-db-instances" and self.database_ready:
            response = super().__call__(service_name, operation, **parameters)
            response["DBInstances"][0]["DBInstanceStatus"] = "available"
            return response
        if operation == "describe-db-snapshots":
            assert parameters == {"DBSnapshotIdentifier": "kanbien-core-platform-" + FD.F.BINDING["proof_label"]}
            if self.snapshot is None: raise R.C.RESOURCE.ResourceMissing()
            return {"DBSnapshots": [copy.deepcopy(self.snapshot)]}
        if operation == "create-db-snapshot":
            self.observed.append((service_name, operation, copy.deepcopy(parameters)))
            assert parameters["DBInstanceIdentifier"] == R.C.RESOURCE.SOURCE_DATABASE and self.snapshot is None
            name = parameters["DBSnapshotIdentifier"]
            self.snapshot = {"DBSnapshotIdentifier": name, "DBSnapshotArn": "arn:aws:rds:eu-west-1:337159794548:snapshot:" + name,
                             "DBInstanceIdentifier": R.C.RESOURCE.SOURCE_DATABASE, "DbiResourceId": FD.F.PARAMETERS["DatabaseResourceId"],
                             "Encrypted": True, "SnapshotType": "manual", "SnapshotCreateTime": datetime.now(timezone.utc).isoformat(), "Status": "available"}
            self.snapshot_tags = copy.deepcopy(parameters["Tags"])
            if self.lost_snapshot: raise OSError(CANARY)
            return {}
        if operation == "list-tags-for-resource" and self.snapshot is not None and parameters.get("ResourceName") == self.snapshot["DBSnapshotArn"]:
            return {"TagList": copy.deepcopy(self.snapshot_tags)}
        if operation == "simulate-principal-policy" and self.deny_snapshot and parameters["ActionNames"] == ["rds:CreateDBSnapshot"]:
            return {"IsTruncated": False, "EvaluationResults": [{"EvalActionName": "rds:CreateDBSnapshot", "EvalResourceName": arn, "EvalDecision": "implicitDeny"} for arn in parameters["ResourceArns"]]}
        if operation == "run-task":
            env = {row["name"]: row["value"] for row in parameters["overrides"]["containerOverrides"][0]["environment"]}
            selected = env.get("ENTITY_SMOKE_ADMINISTRATION_OPERATION", env.get("ENTITY_SMOKE_VERIFICATION_OPERATION"))
            try: return super().__call__(service_name, operation, **parameters)
            finally:
                if selected == "revoke-runtime": self.access = False
                if selected == "restore-runtime": self.access = True
                if selected == "unready" and (self.access or self.wrong_negative):
                    for arn, task in self.jobs.remote.items():
                        if task["startedBy"] == parameters["startedBy"]:
                            self.jobs.results[arn.split("/")[-1]]["code"] = "ENTITY_SMOKE_HEALTHY"
        if operation == "stop-task" and parameters.get("task") == I.RECOVERED:
            self.observed.append((service_name, operation, copy.deepcopy(parameters)))
            assert parameters["cluster"] == R.C.RESOURCE.CLUSTER and parameters["reason"].startswith("es-") and self.access is True
            now = datetime.now(timezone.utc).isoformat()
            original = self.task_rows[I.RECOVERED]
            original.update(lastStatus="STOPPED", stoppedAt=now, stoppedReason=parameters["reason"])
            self.task_rows[SUCCESSOR] = {**copy.deepcopy(original), "taskArn": SUCCESSOR, "lastStatus": "RUNNING", "createdAt": now, "startedAt": now}
            self.task_rows[SUCCESSOR].pop("stoppedAt"); self.task_rows[SUCCESSOR].pop("stoppedReason")
            if self.lost_replacement: raise OSError(CANARY)
            return {}
        return super().__call__(service_name, operation, **parameters)


def task_provider(case):
    value = T.Provider(); value._invoke = lambda service, operation, parameters: case.transport(service, operation, **parameters)
    return value


def selected(case, workload, operation, phase="operation"):
    return SimpleNamespace(**{**vars(case.restart_args), "workload": workload, "operation": operation, "phase": phase, "proof_stage": "credential-recovery", "execute": False})


def task(case, workload, operation, phase="operation"):
    args = selected(case, workload, operation, phase)
    planned = T.plan(args, task_provider(case))
    assert planned["plan"]["execution_route_available"] is True
    args.approved_plan = planned["plan_sha256"]
    return T.execute(args, task_provider(case)), args, planned


def pair(case, workload, operation):
    task(case, workload, operation, "preflight")
    return task(case, workload, operation)


@contextmanager
def scenario():
    with I.scenario(transport_factory=Transport) as case:
        I.plan(case); R.run(case.restart_args, case.restart_capability())
        I.execute_task(case, "verifier", "read", "preflight"); I.execute_task(case, "verifier", "read", "operation")
        I.execute_task(case, "administration", "observe-migration-state", "preflight"); I.execute_task(case, "administration", "observe-migration-state", "operation")
        def replacement_provider():
            value = RP.Provider(); value._invoke = lambda service, operation, parameters: case.transport(service, operation, **parameters)
            return value
        case.replacement_provider = replacement_provider
        case.replacement_args = SimpleNamespace(**{**vars(case.restart_args), "mode": "plan", "approved_plan": None, "proof_stage": "credential-recovery"})
        yield case


def fails(call, code, kind=None):
    kinds = RP.known_failures() + S.known() + (T.RUNNER.RunnerFailure, T.RUNNER.EVIDENCE.EvidenceFailure, T.RUNNER.PREFLIGHT.PreflightFailure) if kind is None else (kind,)
    try: call()
    except kinds as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
        return failure
    else: raise AssertionError("expected credential recovery rejection")


with scenario() as case:
    original_baselines = copy.deepcopy(case.transport.other)
    marker = case.cache / "task-steps/activation-prerequisites.json"
    marker.write_text('{"fixture":"original-activation-must-not-be-rebuilt"}')
    original_manifest = marker.read_bytes()
    pending = T.plan(selected(case, "administration", "revoke-runtime"), task_provider(case))
    assert pending["plan"]["execution_route_available"] is False
    task(case, "administration", "observe-permissions", "preflight")
    permission_args = selected(case, "administration", "observe-permissions")
    permission_args.approved_plan = T.plan(permission_args, task_provider(case))["plan_sha256"]
    original_validate = R.C.GateBook.validate
    def interrupt_completion(self, through, *args, **kwargs):
        if through == "controlled-execution": raise R.C.GATE.ContractFailure("fixture-completion-interruption")
        return original_validate(self, through, *args, **kwargs)
    R.C.GateBook.validate = interrupt_completion
    try: fails(lambda: T.execute(permission_args, task_provider(case)), "fixture-completion-interruption")
    finally: R.C.GateBook.validate = original_validate
    permission_step = T.STEPS.path({"cache": case.cache}, permission_args)
    assert permission_step.is_file() and not T.COMPLETION.path(permission_step).exists()
    before_reconcile = len(case.transport.jobs.remote)
    fails(lambda: T.plan(selected(case, "administration", "revoke-runtime"), task_provider(case)), "task-step-completion-required")
    T.execute(permission_args, task_provider(case))
    assert len(case.transport.jobs.remote) == before_reconcile, "the gap must complete the original reserved task, not relaunch it"
    completion_path = T.COMPLETION.path(permission_step)
    completion_raw = completion_path.read_bytes()
    completion = json.loads(completion_raw)
    evidence_path = case.root / completion["realization_evidence"]
    evidence_raw = evidence_path.read_bytes()
    evidence_path.write_bytes(evidence_raw + b"\n")
    try: fails(lambda: T.plan(selected(case, "administration", "revoke-runtime"), task_provider(case)), "task-step-completion-gate-changed")
    finally: evidence_path.write_bytes(evidence_raw)
    for mutate, code in ((lambda value: value["facts"].update(contract_id="wrong-operation"), "task-step-completion-contract-mismatch"),
                         (lambda value: value["facts"]["artifact_bindings"][0].update(immutable_reference="sha256:" + "0" * 64), "task-step-completion-artifacts-mismatch")):
        altered = json.loads(evidence_raw); mutate(altered); evidence_path.write_text(json.dumps(altered))
        completion_path.write_text(json.dumps({**completion, "realization_evidence_sha256": R.C.digest_file(evidence_path)}))
        try: fails(lambda: T.plan(selected(case, "administration", "revoke-runtime"), task_provider(case)), code)
        finally: evidence_path.write_bytes(evidence_raw); completion_path.write_bytes(completion_raw)
    assert len(case.transport.jobs.remote) == before_reconcile
    pair(case, "administration", "revoke-runtime")
    assert case.transport.access is False
    fails(lambda: T.plan(selected(case, "verifier", "unready", "preflight"), task_provider(case)), "task-unready-preflight-phase-prohibited")
    missing = T.plan(selected(case, "administration", "restore-runtime"), task_provider(case))
    assert missing["plan"]["pending_prerequisite"] == "credential-recovery-unready" and missing["plan"]["execution_route_available"] is False
    negative_args = selected(case, "verifier", "unready")
    revoke_path = case.cache / "task-steps/administration-revoke-runtime-credential-recovery-operation.json"
    revoke_raw = revoke_path.read_bytes()
    moved = revoke_path.with_suffix(".temporarily-moved")
    revoke_path.rename(moved)
    try:
        missing = T.plan(negative_args, task_provider(case))
        assert missing["plan"]["pending_prerequisite"] == "credential-recovery-revoke-runtime" and missing["plan"]["execution_route_available"] is False
    finally: moved.rename(revoke_path)
    copied = json.loads(revoke_raw); copied["reservation"]["request"]["proof_label"] = "entity-smoke-" + "0" * 24
    revoke_path.write_text(json.dumps(copied))
    try: fails(lambda: T.plan(negative_args, task_provider(case)), "task-step-request-mismatch")
    finally: revoke_path.write_bytes(revoke_raw)
    negative_plan = T.plan(negative_args, task_provider(case))
    declaration = T.GRAPH.contract("verifier", R.C.GATE, negative=True)
    normal = T.GRAPH.contract("verifier", R.C.GATE)
    assert R.C.GATE.ids(declaration)[1] == R.C.GATE.ids(normal)[1], "negative graph must retain every reachable component"
    first = R.C.read_json(case.root / negative_plan["realization_evidence"])
    assert first["facts"]["contract_id"] == "entity-smoke-credential-unready-observation" and len(first["facts"]["gate_evidence"]) == 5
    negative_args.approved_plan = negative_plan["plan_sha256"]
    before_negative = len(case.transport.jobs.remote)
    case.transport.jobs.lost_next = True
    fails(lambda: T.execute(negative_args, task_provider(case)), "task-submission-uncertain-reconcile-required")
    assert len(case.transport.jobs.remote) == before_negative + 1
    result = T.execute(negative_args, task_provider(case))
    assert len(case.transport.jobs.remote) == before_negative + 1, "lost negative response must reconcile without another launch"
    receipt = R.C.read_json(case.root / result["receipt"])
    assert receipt["receipt"]["result"]["code"] == "ENTITY_SMOKE_LIVE_NOT_READY" and receipt["reservation"]["request"]["deadline_seconds"] == 90
    assert set(receipt["reservation"]["request"]["environment"]) == {"ENTITY_SMOKE_VERIFICATION_OPERATION", "ENTITY_SMOKE_EXPECTED_SOURCE", "ENTITY_SMOKE_PROOF_LABEL"}
    completed = R.C.read_json(case.root / result["realization_evidence"])
    assert completed["facts"]["contract_id"] == declaration["id"] and len(completed["facts"]["gate_evidence"]) == 7
    negative_id = receipt["receipt"]["task"]["arn"].split("/")[-1]
    original_result = copy.deepcopy(case.transport.jobs.results[negative_id])
    case.transport.jobs.results[negative_id]["code"] = "ENTITY_SMOKE_HEALTHY"
    try:
        # Exercise the real public reporter too: retained success cannot hide
        # contradictory task/log observations or permit another submission.
        old_parse, old_provider = T.parse, T.Provider
        reported_provider = task_provider(case)
        T.parse, T.Provider = lambda: SimpleNamespace(**{**vars(negative_args), "execute": True, "validate_arguments": False}), lambda: reported_provider
        output = io.StringIO()
        try:
            with redirect_stdout(output): status = T.main()
        finally: T.parse, T.Provider = old_parse, old_provider
        report = json.loads(output.getvalue())
        assert status == 1 and report["condition"] == "task-http-result-not-confirmed" and report["verdict"] == "blocked"
        assert report["context"]["proof_stage"] == "credential-recovery" and CANARY not in output.getvalue()
        assert len(case.transport.jobs.remote) == before_negative + 1
    finally: case.transport.jobs.results[negative_id] = original_result
    fails(lambda: T.RUNNER.PREFLIGHT.validate_launch(receipt["reservation"]["request"]), "preflight-operation-not-read-only")
    pair(case, "administration", "restore-runtime")
    assert case.transport.access is True
    planned = RP.run(case.replacement_args, case.replacement_provider())
    case.replacement_args.mode, case.replacement_args.approved_plan = "execute", planned["plan_sha256"]
    case.transport.lost_replacement = True
    fails(lambda: RP.run(case.replacement_args, case.replacement_provider()), "resource-submission-uncertain-reconcile-only")
    replaced = RP.run(case.replacement_args, case.replacement_provider())
    assert replaced["verdict"] == "completed"
    copied_read = selected(case, "verifier", "read")
    fails(lambda: task(case, "verifier", "read"), "task-preflight-receipt-required")
    assert not T.STEPS.path({"cache": case.cache}, copied_read).exists(), "pre-restoration readiness is not fresh recovered readiness"
    replacement_path = case.cache / "credential-replacement-receipt.json"
    replacement_raw = replacement_path.read_bytes()
    moved = replacement_path.with_suffix(".temporarily-moved"); replacement_path.rename(moved)
    try:
        (case.cache / "replacement-receipt.json").write_bytes(replacement_raw)
        pending = T.plan(copied_read, task_provider(case))
        assert pending["plan"]["pending_prerequisite"] == "credential-replacement" and pending["plan"]["execution_route_available"] is False
    finally: moved.rename(replacement_path)
    journal = case.cache / "attempts" / (case.args.proof_label + "-credential-replacement.json")
    moved_journal = journal.with_suffix(".temporarily-moved"); journal.rename(moved_journal)
    try: fails(lambda: T.plan(copied_read, task_provider(case)), "credential-replacement-journal-required")
    finally: moved_journal.rename(journal)
    assert sum(action == "stop-task" and args.get("task") == I.RECOVERED for _, action, args in case.transport.observed) == 1
    pair(case, "verifier", "read")
    pair(case, "database-proof", "permissions")
    history_path = case.cache / "credential-history.json"
    history_raw = history_path.read_bytes(); history = json.loads(history_raw)
    assert history["current_readiness"] is False and history["scope_acceptance"] is False and history_path.stat().st_mode & 0o777 == 0o600
    assert len(history["references"]) <= 256
    def snapshot_provider():
        value = S.Provider(); value._invoke = lambda service, operation, parameters: case.transport(service, operation, **parameters)
        return value
    snapshot_args = SimpleNamespace(**{**vars(case.replacement_args), "mode": "plan", "approved_plan": None})
    for edited, code in (({**history, "references": {**history["references"], "../provider-canary.json": "sha256:" + "0" * 64}}, "history-reference-invalid"),
                         ({**history, "references": {key: value for key, value in history["references"].items() if key != history["final_step"]}}, "history-final-step-not-bound"),
                         ({**history, "references": {key: value for key, value in history["references"].items() if not key.startswith("task-receipts/admissions/")}}, "history-required-dependencies-omitted")):
        history_path.write_text(json.dumps(edited))
        try: fails(lambda: S.run(snapshot_args, snapshot_provider()), code)
        finally: history_path.write_bytes(history_raw)
        assert not any(operation == "create-db-snapshot" for _, operation, _ in case.transport.observed)
    referenced = case.cache / history["final_step"]; raw = referenced.read_bytes(); referenced.write_bytes(raw + b"\n")
    try: fails(lambda: S.run(snapshot_args, snapshot_provider()), "history-dependency-changed")
    finally: referenced.write_bytes(raw)
    before_snapshot_jobs = sum(operation == "run-task" for _, operation, _ in case.transport.jobs.observed)
    # Expire the controlled old stopped tasks/logs entirely. Snapshot admission
    # must use the captured history, not mistake missing provider evidence for
    # success or submit any of those jobs again. Current server still exists.
    for arn, row in list(case.transport.task_rows.items()):
        if row["lastStatus"] == "STOPPED": case.transport.task_rows.pop(arn)
    case.transport.jobs.remote.clear(); case.transport.jobs.results.clear()
    case.transport.deny_snapshot = True
    try: fails(lambda: S.run(snapshot_args, snapshot_provider()), "snapshot-operator-policy-preflight-not-confirmed")
    finally: case.transport.deny_snapshot = False
    planned_snapshot = S.run(snapshot_args, snapshot_provider())
    assert planned_snapshot["plan"]["maximum_snapshot_creates"] == 1 and planned_snapshot["plan"]["isolated_restore_proven"] is False
    old_parse, old_provider = S.parse, S.Provider
    main_provider = snapshot_provider()
    S.parse, S.Provider = lambda: snapshot_args, lambda: main_provider
    moved_history = history_path.with_suffix(".temporarily-moved"); history_path.rename(moved_history)
    output = io.StringIO()
    try:
        with redirect_stdout(output): status = S.main()
    finally: moved_history.rename(history_path); S.parse, S.Provider = old_parse, old_provider
    failure_report = json.loads(output.getvalue())
    assert status == 1 and failure_report["condition"] == "history-completion-required" and failure_report["effect"] == "not-started"
    assert CANARY not in output.getvalue()
    snapshot_args.mode, snapshot_args.approved_plan = "execute", planned_snapshot["plan_sha256"]
    # The shared emergency-stop producer intentionally reports a rebooting DB.
    # It may be stopped safely, but is not an eligible snapshot source. Preserve
    # that rejection, then explicitly simulate its later recovered availability.
    fails(lambda: S.run(snapshot_args, snapshot_provider()), "resource-source-incarnation-not-confirmed")
    assert not any(operation == "create-db-snapshot" for _, operation, _ in case.transport.observed)
    case.transport.database_ready = True
    prepared_snapshot = S.prepare(snapshot_args, snapshot_provider())
    guarded_store = R.C.RESOURCE.ResourceStore(case.cache / "snapshot-guard-attempts")
    guarded_request = prepared_snapshot["packet"]["request"]
    guarded_provider = snapshot_provider()
    def refuse_before_io(): raise S.SnapshotFailure("snapshot-source-changed-before-submission")
    guarded_provider.enable_snapshot(guarded_store, guarded_request, refuse_before_io)
    guarded_call = lambda: R.C.RESOURCE.create_recovery_point(guarded_provider, guarded_store, guarded_request["binding"], guarded_request["source_resource_id"], guarded_request["original_commit_observed_at"])
    fails(guarded_call, "snapshot-source-changed-before-submission")
    assert guarded_provider.effect == "not-started" and guarded_provider.rejected_failure.code == "snapshot-source-changed-before-submission"
    assert guarded_call()["status"] == "pending", "a consumed pre-I/O reservation is still reconciliation-only, never an automatic fresh submission"
    assert not any(operation == "create-db-snapshot" for _, operation, _ in case.transport.observed)
    case.transport.lost_snapshot = True
    fails(lambda: S.run(snapshot_args, snapshot_provider()), "resource-submission-uncertain-reconcile-only")
    observed_snapshot = S.run(snapshot_args, snapshot_provider())
    assert observed_snapshot["verdict"] == "completed" and observed_snapshot["isolated_restore_proven"] is False
    assert S.run(snapshot_args, snapshot_provider())["verdict"] == "completed"
    assert sum(operation == "create-db-snapshot" for _, operation, _ in case.transport.observed) == 1
    assert sum(operation == "run-task" for _, operation, _ in case.transport.jobs.observed) == before_snapshot_jobs
    assert history_path.read_bytes() == history_raw
    restore_fixture = module("entity_smoke_credential_connected_restore", DIRECTORY / "restore-route-test.py")
    restore_fixture.run(case, snapshot_args, S, T, CANARY)
    assert marker.read_bytes() == original_manifest and case.transport.other == original_baselines
    assert sum(action == "stop-task" and args.get("task") == I.RECOVERED for _, action, args in case.transport.observed) == 1
    for path in case.cache.rglob("*.json"): assert CANARY not in path.read_text()

print(json.dumps({"schema": "deploy/entity-smoke-credential-route-fixture/v1", "verdict": "passed", "provider_observation": False,
                  "prerequisites": "shared-controlled-source-custody-alignment-task-and-transport-not-qualification",
                  "cases": ["actual-sequenced-task-route", "completion-gap-blocks-next-step", "interrupted-completion-reconciles-without-launch", "changed-gate-bytes-contract-and-artifact-rejected", "premature-restore-closed", "missing-and-copied-revoke-rejected", "all-reachable-negative-components", "first-five-before-unready", "no-negative-preflight", "one-bounded-unready", "lost-negative-no-replay", "real-negative-collector-result", "wrong-negative-at-public-reporter", "negative-not-business-admission", "separate-restore", "actual-credential-replacement", "lost-replacement-no-second-stop", "baseline-receipt-cannot-substitute", "missing-replacement-journal-no-effects", "fresh-positive-read-and-permissions", "activation-not-rebuilt", "baseline-preserved", "bounded-immutable-history", "history-not-current-readiness", "history-path-omission-and-byte-rejection", "old-task-expiry-no-replay", "snapshot-operator-denial", "snapshot-pre-io-reason-no-replay", "rebooting-source-rejection", "lost-snapshot-one-create", "history-failure-at-public-reporter"]}))
