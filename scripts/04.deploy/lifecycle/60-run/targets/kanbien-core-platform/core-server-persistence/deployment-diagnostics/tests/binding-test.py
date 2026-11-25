#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.core-server-persistence-diagnostics-binding
#   version: 1
#   status: draft
#   created_on: "2026-11-23"
#   updated_on: "2026-11-23"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.diagnostics
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove that Core Server Persistence task evidence remains bounded and is the sole caller-owned extension of the shared deployment report.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.test.deployment-operation-diagnostics.wrapper
#     path: scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.sh
#   effects: [read-only, writes-files]
"""Focused proofs for the Core Server Persistence diagnostics binding."""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[9]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


binding = load(Path(__file__).resolve().parents[1] / "binding.py", "persistence_diagnostics_binding")
shared = binding.shared()
RUN = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/"


def generic_report(**overrides):
    report = shared.build_report(
        target="test-target", scope="test-scope", operation_id="test-operation",
        stage="deploy", original_code="test-operation-failed", exit_status=9,
        outcome="failed", classification="provider-property-rejection",
        evidence_reference="github-actions-artifact:test-diagnostic",
        next_decision="inspect-retained-evidence",
        observed_at="2026-10-25T10:00:00Z",
    )
    report.update(overrides)
    return report


def event(value):
    return {"message": json.dumps(value)}


def source(ordinal):
    return {"schema": "core/diagnostic-record/v1", "code": "core.persistence.in-memory-boundary-failed", "definitionVersion": 1, "detail": {"operation": "initialize", "phase": "get-id", "reason": "boundary-threw", "effect": "write-not-reached", "ordinal": ordinal}}


sources = [source(index) for index in range(9)]
own = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.operations.verification-boundary-failed", "definitionVersion": 1, "detail": {"task": "verification", "operation": "verification", "phase": "fetch", "condition": "rejected", "effect": "unknown"}}
failure = {"schema": "deploy/persistence-task-failure/v1", "task": "verification", "verdict": "rejected", "code": "KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE", "diagnostic": sources[0], "related_diagnostics": sources[1:], "observations": [own]}

checked = binding.validate_persistence_task_failure(failure, "verification")
assert checked == failure and checked is not failure and checked["diagnostic"] is not failure["diagnostic"]
shared.validate(generic_report(task_failure=failure), extension_validators=binding.report_extension_validators())
try:
    shared.validate(generic_report(task_failure=failure))
except shared.DiagnosticFailure:
    pass
else:
    raise AssertionError("generic reports accepted a target extension without its binding")

for mutate in [
    lambda value: value.update(extra="PRIVATE_TASK_CANARY"),
    lambda value: value.update(code="BOOTSTRAP_PRIVATE_TASK_CANARY"),
    lambda value: value.update(task="administration"),
    lambda value: value.update(observations=[own] * 9),
    lambda value: value.update(related_diagnostics=sources),
    lambda value: value.update(diagnostic=own),
    lambda value: value["diagnostic"]["detail"].update(private="PRIVATE_TASK_CANARY"),
    lambda value: value.update(source_bundles=[{"diagnostic": source(10)}] * 9),
    lambda value: value.update(source_bundles=[{"diagnostic": sources[0], "related_diagnostics": sources[1:]}]),
    lambda value: value.update(overflow={"observations": 0, "source_bundles": 0}),
    lambda value: value.update(overflow={"observations": True, "source_bundles": 1}),
    lambda value: value.update(overflow={"observations": -1, "source_bundles": 0}),
    lambda value: value.update(overflow={"observations": 1, "source_bundles": 0, "private": "PRIVATE_TASK_CANARY"}),
]:
    malformed = copy.deepcopy(failure)
    mutate(malformed)
    try:
        binding.validate_persistence_task_failure(malformed, "verification")
    except binding.DiagnosticFailure as error:
        assert error.codes == ("persistence-task-failure-invalid",)
    else:
        raise AssertionError("malformed or unselected private task evidence was admitted")

try:
    binding.validate_verifier_result(failure)
except binding.DiagnosticFailure:
    pass
else:
    raise AssertionError("private task envelope widened the historical verifier reader")

different_companions = {"diagnostic": sources[0], "related_diagnostics": [*sources[1:8], source(9)]}
extended = {**failure, "source_bundles": [different_companions], "overflow": {"observations": 2, "source_bundles": 1}}
assert binding.validate_persistence_task_failure(extended, "verification") == extended
selected, observation = binding.collect_persistence_task_failure({"events": [{"message": "PRIVATE_TASK_CANARY"}, event(failure), event({"private": "PRIVATE_TASK_CANARY"}), event({**failure, "diagnostic": source(10), "related_diagnostics": sources[1:]})]}, "verification")
assert observation == "malformed" and selected["diagnostic"] == sources[0] and selected["related_diagnostics"] == sources[1:]
assert selected["source_bundles"] == [{"diagnostic": source(10), "related_diagnostics": sources[1:]}] and selected["observations"] == [own, own]
full = {**failure, "observations": [own] * 8, "source_bundles": [{"diagnostic": source(index), "related_diagnostics": sources[1:]} for index in range(10, 18)]}
later = {**failure, "diagnostic": source(20), "observations": [own, own], "overflow": {"observations": 3, "source_bundles": 4}}
merged, state = binding.collect_persistence_task_failure({"events": [event(full), event(later)]}, "verification")
assert state == "complete" and merged["diagnostic"] == sources[0] and merged["related_diagnostics"] == sources[1:]
assert merged["observations"] == [own] * 8 and merged["source_bundles"] == full["source_bundles"] and merged["overflow"] == {"observations": 5, "source_bundles": 5}
maximum = shared.runtime_contract().persistence_task_failure_contract()["maxOverflowCount"]
first = {**failure, "overflow": {"observations": maximum, "source_bundles": 0}}
merged, state = binding.collect_persistence_task_failure({"events": [event(first), event({**failure, "overflow": {"observations": 1, "source_bundles": 0}})]}, "verification")
assert state == "incomplete" and merged == first

task_arn = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "a" * 32
command = RUN + "verify-candidate/script.sh"
controller_report = {"schema": "deploy/private-persistence-verification-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": "failed", "findings": [{"code": "PRIVATE_TASK_CANARY"}], "facts": {"operation_id": "kp-" + "b" * 32, "verifier_task": task_arn, "task_failure": failure}}
checkpoint = binding.validate_persistence_controller_checkpoint(controller_report, command)
assert checkpoint["facts"] == controller_report["facts"]
for key, value in [("operation_id", "kp-PRIVATE_TASK_CANARY"), ("verifier_task", task_arn.replace("337159794548", "000000000000")), ("proof_receipt", "../PRIVATE_TASK_CANARY.json"), ("completed_at", "2026-10-31T00:00:00"), ("evidence_reuse", "PRIVATE_TASK_CANARY")]:
    changed = copy.deepcopy(controller_report)
    changed["facts"][key] = value
    checked = binding.validate_persistence_controller_checkpoint(changed, command)
    assert key not in checked["facts"] and checked["facts"]["task_failure"] == failure
changed = copy.deepcopy(controller_report)
changed["facts"]["task_failure"]["diagnostic"]["detail"]["private"] = "PRIVATE_TASK_CANARY"
assert binding.validate_persistence_controller_checkpoint(changed, command)["facts"] == {"operation_id": "kp-" + "b" * 32, "verifier_task": task_arn}
assert binding.validate_persistence_controller_checkpoint({**controller_report, "schema": "other"}, command) is None
assert binding.validate_persistence_controller_checkpoint(controller_report, RUN + "run-administration/script.sh") is None

identity = load(ROOT / (RUN + "rehearse-runtime-credential-lifecycle/script.py"), "credential_lifecycle")
pending = {**controller_report, "verdict": "pending", "facts": {"operation_id": "kp-" + "b" * 32, "verifier_task": task_arn}}
completed = subprocess.CompletedProcess([], 17, json.dumps(controller_report), "PRIVATE_CHILD_CANARY\n" + json.dumps(pending))
with patch.object(identity.subprocess, "run", return_value=completed) as child:
    assert identity.child(command, "--mode", "create", "--json") is None
    assert child.call_count == 1
assert identity.CHILD_CHECKPOINT["facts"]["task_failure"] == failure
capture = io.StringIO()
with redirect_stdout(capture):
    assert identity.report("blocked", "outer-original-code") == 1
body = json.loads(capture.getvalue())
assert body["verdict"] == "failed" and "PRIVATE_CHILD_CANARY" not in capture.getvalue()

outer = load(ROOT / (RUN + "rehearse-observability-readiness/script.py"), "observability_readiness")
expired = subprocess.TimeoutExpired(["bash"], 420, output=json.dumps(body).encode(), stderr=b"PRIVATE_CHILD_CANARY")
with patch.object(outer.subprocess, "run", side_effect=expired) as child:
    try:
        outer.lifecycle(Path("unused-receipt"), "revoke-await-observability")
    except outer.RehearsalFailure as error:
        assert str(error) == "observability-rehearsal-lifecycle-outcome-uncertain"
    else:
        raise AssertionError("outer timeout was accepted")
    assert child.call_count == 1
capture = io.StringIO()
with redirect_stdout(capture):
    assert outer.report("blocked", "observability-rehearsal-lifecycle-outcome-uncertain") == 1
body = json.loads(capture.getvalue())
assert body["facts"]["child_checkpoint"]["facts"]["child_checkpoint"]["facts"]["task_failure"] == failure
assert "PRIVATE_CHILD_CANARY" not in capture.getvalue()

administration = load(ROOT / (RUN + "run-administration/script.py"), "administration")
admin_own = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.operations.administration-boundary-failed", "definitionVersion": 1, "detail": {"task": "administration", "operation": "administration", "phase": "task-body", "condition": "threw", "effect": "unknown"}}
admin_failure = {**failure, "task": "administration", "code": "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", "observations": [admin_own]}
configuration = {"schema": "core/diagnostic-record/v1", "code": "kanbien-core-server.configuration-invalid", "definitionVersion": 1, "detail": {"issues": [{"setting": "database.host", "reason": "missing"}]}}
legacy_codes = ["PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID", "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED", "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", "PERSISTENCE_ADMINISTRATION_ACCESS_DENIED", "PERSISTENCE_ADMINISTRATION_CREDENTIAL_REJECTED"]
legacy = []
for safe_code in legacy_codes:
    record = configuration if safe_code == legacy_codes[0] else sources[0]
    legacy.append({"verdict": "rejected", "code": safe_code, "diagnostic": record, **({"related_diagnostics": sources[1:]} if record is sources[0] else {})})
for rejected in [admin_failure, *legacy]:
    capture = io.StringIO()
    with patch.object(administration.MIGRATION, "duration", return_value=1), patch.object(administration.MIGRATION, "task_exit", return_value=False), patch.object(administration.MIGRATION, "aws", return_value=(True, {"events": [event(rejected)]}, "ok")) as provider, redirect_stdout(capture):
        assert administration.accept({"taskArn": task_arn}, 30, "prove-effective-privilege") == 1
    assert provider.call_args.args == ("logs", "get-log-events", "--log-group-name", administration.LOG_GROUP, "--log-stream-name", "persistence-administration/persistence-administration/" + "a" * 32, "--start-from-head")
    body = json.loads(capture.getvalue())
    assert body["verdict"] == "blocked" and body["findings"] == [{"code": "persistence-administration-unsuccessful-completion"}]
    assert body["facts"]["administration_task"] == "a" * 32 and body["facts"]["safe_result_code"] == rejected["code"]
    if rejected is admin_failure:
        assert body["facts"]["task_failure"] == admin_failure
    else:
        assert body["facts"]["diagnostic"] == rejected["diagnostic"]
        if "related_diagnostics" in rejected:
            assert body["facts"]["related_diagnostics"] == sources[1:]

capture = io.StringIO()
with patch.object(administration.MIGRATION, "duration", return_value=1), patch.object(administration.MIGRATION, "task_exit", return_value=False), patch.object(administration.MIGRATION, "aws", return_value=(True, {"events": [event(admin_failure)]}, "ok")) as provider, redirect_stdout(capture):
    assert administration.accept({"taskArn": task_arn.replace("337159794548", "000000000000")}, 30, "prove-effective-privilege") == 1
assert provider.call_count == 1
assert json.loads(capture.getvalue())["facts"] == {"task_log_observation": "unavailable"}

replacement = load(ROOT / (RUN + "rehearse-server-replacement/script.py"), "server_replacement")
for original_arn in [task_arn, task_arn.replace("337159794548", "000000000000")]:
    capture, errors, calls = io.StringIO(), io.StringIO(), []
    owner = replacement.operations()
    def interrupted_stop(*parts):
        calls.append(parts)
        checkpoint = json.loads(errors.getvalue())
        assert checkpoint["schema"] == "deploy/persistence-server-replacement-report/v1"
        assert checkpoint["target"] == "kanbien-core-platform" and checkpoint["scope"] == "core-server-persistence"
        assert checkpoint["verdict"] == "pending" and "recovery_boundary" in checkpoint["facts"]
        assert checkpoint["facts"]["original_task"] == task_arn
        assert binding.validate_persistence_controller_checkpoint(checkpoint, RUN + "rehearse-server-replacement/script.sh")["facts"] == checkpoint["facts"]
        return False, None, "aws-command-timeout"
    receipt = {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64}
    definition = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-core-server-persistence:1"
    prepare = SimpleNamespace(validate_receipt=lambda _: receipt, live_budget=lambda: (True, "ok"), aws=interrupted_stop)
    create = SimpleNamespace(package_gates=lambda _: True)
    with tempfile.TemporaryDirectory(prefix="replacement-checkpoint-fixture-") as directory:
        store = owner.Store(Path(directory))
        with patch.object(replacement, "operations", return_value=owner), patch.object(owner, "store", return_value=store), patch.object(replacement, "module", side_effect=[prepare, create]), patch.object(replacement, "current_task", return_value=({"taskArn": original_arn}, "ok", definition)), patch.object(replacement, "receipt_matches_task", return_value=(True, "ok")), patch.object(sys, "argv", ["replacement", "--receipt", "unused.json"]), redirect_stdout(capture), patch.object(sys, "stderr", errors):
            assert replacement.main() == 1
        observed = json.loads(capture.getvalue())
        if original_arn == task_arn:
            assert calls == [("ecs", "stop-task", "--cluster", replacement.CLUSTER, "--task", original_arn, "--reason", "governed core-server-persistence replacement rehearsal")]
            assert observed["verdict"] == "uncertain" and observed["findings"] == [{"code": "aws-command-timeout"}]
            assert binding.validate_persistence_controller_checkpoint(observed, RUN + "rehearse-server-replacement/script.sh")["facts"] == observed["facts"]
            assert store.selected(receipt)["request"]["original_task"] == task_arn
        else:
            assert not calls and not errors.getvalue()
            assert observed["verdict"] == "blocked" and observed["findings"] == [{"code": "persistence-replacement-request-invalid"}]

execution = {"phase": "pool_connect", "elapsed_ms": 12, "code_status": "recognized", "classification": "authentication_rejected"}
for value in [{"verdict": "rejected", "code": "SAFE_REJECTED"}, {"schema": "deploy/persistence-restore-verifier-result/v2", "verdict": "rejected", "code": "SAFE_REJECTED", "execution": execution}]:
    binding.validate_verifier_result(value)
for value in [{"verdict": "accepted", "code": "SAFE_RESULT", "provider_message": "synthetic-canary"}, {"schema": "deploy/persistence-restore-verifier-result/v2", "verdict": "accepted", "code": "SAFE_RESULT", "execution": execution}]:
    try:
        binding.validate_verifier_result(value)
    except binding.DiagnosticFailure:
        pass
    else:
        raise AssertionError("unsafe result envelope accepted")

print("Core Server Persistence diagnostics binding tests passed.")
