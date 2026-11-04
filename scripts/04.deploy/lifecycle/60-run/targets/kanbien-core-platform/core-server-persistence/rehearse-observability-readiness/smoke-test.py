#!/usr/bin/env python3
"""Offline regression coverage for the bounded readiness-alert rehearsal."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.rehearse-observability-readiness.impl
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise bounded observability-rehearsal decisions with synthetic provider observations.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.test.kanbien-core-platform.rehearse-observability-readiness
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/smoke-test.sh
#   effects: [read-only, writes-files]
from __future__ import annotations

import contextlib
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[8]
BASE = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence"
spec = importlib.util.spec_from_file_location("observability_rehearsal", BASE / "rehearse-observability-readiness/script.py")
controller = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(controller)

# Exact command/status/empty-response compatibility at the real AWS wrapper;
# canonical access denial differs from arbitrary prose containing those words.
parts = ("cloudwatch", "describe-alarms", "--alarm-names", "owned-alarm")
expected = ["aws", *parts, "--profile", controller.PROFILE, "--region", controller.REGION, "--output", "json"]
for fault, code in [(OSError("PRIVATE_OBSERVABILITY_NATIVE_CANARY"), "observability-rehearsal-provider-command-unavailable"),
                    (UnicodeDecodeError("utf8", b"\xff", 0, 1, "PRIVATE_OBSERVABILITY_NATIVE_CANARY"), "observability-rehearsal-provider-response-invalid"),
                    (subprocess.TimeoutExpired(["PRIVATE_OBSERVABILITY_NATIVE_CANARY"], 30), "observability-rehearsal-provider-observation-timeout")]:
    output, errors = io.StringIO(), io.StringIO()
    with patch.object(controller.subprocess, "run", side_effect=fault) as provider, contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        try: controller.aws(*parts)
        except controller.RehearsalFailure as error:
            assert str(error) == code and error.__cause__ is fault
        else: raise AssertionError("native provider observation passed")
    assert provider.call_count == 1 and provider.call_args.args == (expected,)
    assert provider.call_args.kwargs == {"capture_output": True, "text": True, "timeout": 30, "check": False, "env": {**os.environ, "AWS_PAGER": ""}}
    assert output.getvalue() + errors.getvalue() == ""
for status, stdout, stderr, value, code in [
    (0, "", "", {}, None), (0, '{"MetricAlarms":[]}', "", {"MetricAlarms": []}, None),
    (0, "{PRIVATE_OBSERVABILITY_NATIVE_CANARY", "", None, "observability-rehearsal-provider-response-invalid"),
    (0, "[]", "", None, "observability-rehearsal-provider-response-invalid"),
    (0, " ", "", None, "observability-rehearsal-provider-response-invalid"),
    (254, "", "An error occurred (AccessDeniedException) when calling the DescribeAlarms operation: PRIVATE_OBSERVABILITY_NATIVE_CANARY", None, "observability-rehearsal-provider-access-denied"),
    (254, "", "PRIVATE_OBSERVABILITY_NATIVE_CANARY accessdenied not authorized", None, "observability-rehearsal-provider-observation-failed"),
    (254, "", "An error occurred (ResourceNotFoundException) when calling the DescribeAlarms operation: PRIVATE_OBSERVABILITY_NATIVE_CANARY", None, "observability-rehearsal-provider-observation-failed"),
]:
    output, errors = io.StringIO(), io.StringIO()
    with patch.object(controller.subprocess, "run", return_value=subprocess.CompletedProcess([], status, stdout, stderr)) as provider, contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        try: observed = controller.aws(*parts)
        except controller.RehearsalFailure as error:
            assert code is not None and str(error) == code
        else: assert code is None and observed == value
    assert provider.call_count == 1 and provider.call_args.args == (expected,)
    assert provider.call_args.kwargs == {"capture_output": True, "text": True, "timeout": 30, "check": False, "env": {**os.environ, "AWS_PAGER": ""}}
    assert output.getvalue() + errors.getvalue() == ""


def invoke(arguments: list[str]):
    output = io.StringIO()
    with patch.object(sys, "argv", ["observability-rehearsal", *arguments]), contextlib.redirect_stdout(output):
        status = controller.main()
    return status, json.loads(output.getvalue())


past = (datetime.now(timezone.utc) - timedelta(minutes=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
assert controller.iso(past, "bad") == past
try:
    controller.iso([], "bad")
except controller.RehearsalFailure as error:
    assert str(error) == "bad"
else:
    raise AssertionError("malformed timestamp passed")

# A fresh retained proof lets a resumed controller observe the same fault
# without calling the revocation lifecycle again.
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    proofs = root / "proof-receipts"; proofs.mkdir()
    task_module = controller.task_receipts()
    task_module.EVIDENCE_CLASS = "live"
    now = datetime.now(timezone.utc).replace(microsecond=0)
    digest = "sha256:" + "a" * 64
    task = {
        "taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "b" * 32,
        "taskDefinitionArn": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:1",
        "lastStatus": "STOPPED",
        "startedAt": (now - timedelta(seconds=30)).isoformat().replace("+00:00", "Z"),
        "stoppedAt": (now - timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
        "containers": [{"exitCode": 0}],
    }
    proof = task_module.make(
        proof_type="verifier", operation="health-unready", task=task,
        image_digest=digest, result_code="KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY",
        context={"record_id": "observability-smoke", "completion_deadline_seconds": 120, "completion_duration_seconds": 29},
        controller="verify-candidate", collected_at=now.isoformat().replace("+00:00", "Z"),
    )
    selected = proofs / "verifier-health-unready.json"; selected.write_text(json.dumps(proof))
    class Succession:
        @staticmethod
        def sha256_bytes(value: bytes) -> str:
            return "sha256:" + hashlib.sha256(value).hexdigest()
    with patch.object(controller, "PROOF_ROOT", proofs), patch.object(controller, "ROOT", root), patch.object(controller, "task_receipts", lambda: task_module), patch.object(controller, "succession", lambda: Succession):
        source = controller.retained_source("KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY", digest, not_before=now - timedelta(minutes=2))
    assert source is not None and source["result_code"] == "KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY"
    assert controller.retained_source("KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY", digest, not_before=now + timedelta(minutes=1)) is None

# Notification collection requires a confirmed subscription; a pending topic
# cannot be converted into a delivery receipt by a supplied timestamp.
fake_failure = {"source_proof": {"image_digest": "sha256:" + "c" * 64}}
with patch.object(controller, "candidate", return_value="sha256:" + "c" * 64), \
     patch.object(controller, "receipt_argument", return_value=fake_failure), \
     patch.object(controller, "confirmed_subscription", return_value=False):
    subscribed = (datetime.now(timezone.utc) - timedelta(minutes=2)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    delivered = (datetime.now(timezone.utc) - timedelta(minutes=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    code, report = invoke(["--receipt", "/tmp/candidate.json", "--operation", "record-notification", "--failure-receipt", "/tmp/failure.json", "--subscription-confirmed-at", subscribed, "--operator-delivery-confirmed-at", delivered])
assert code == 1 and report["findings"] == [{"code": "observability-rehearsal-notification-subscription-pending"}]

# An operator attestation concerns this exact ALARM episode, not merely an
# ALARM with the same name. Equivalent timezone representations are one instant.
episode = "2026-10-24T14:00:00Z"
fake_failure["observation"] = {"alarm_state_updated_at": episode}
arguments = ["--receipt", "/tmp/candidate.json", "--operation", "record-notification", "--failure-receipt", "/tmp/failure.json", "--subscription-confirmed-at", subscribed, "--operator-delivery-confirmed-at", delivered]
for state_updated, accepted in [("2026-10-24T15:00:00+01:00", True), ("2026-10-24T14:00:01Z", False)]:
    observation = {"alarm_name": controller.receipts().ALARM, "alarm_state": "ALARM", "alarm_state_updated_at": state_updated}
    with patch.object(controller, "candidate", return_value="sha256:" + "c" * 64), \
         patch.object(controller, "receipt_argument", return_value=fake_failure), \
         patch.object(controller, "confirmed_subscription", return_value=True), \
         patch.object(controller, "alarm", return_value=observation) as alarm_read, \
         patch.object(controller, "persist", return_value=ROOT / "recorded.json") as persist:
        code, report = invoke(arguments)
    assert alarm_read.call_args.args == ("ALARM",)
    assert persist.call_count == int(accepted)
    assert code == (0 if accepted else 1)
    if accepted:
        assert persist.call_args.args[2]["alarm_state_updated_at"] == state_updated
    else:
        assert report["findings"] == [{"code": "observability-rehearsal-alarm-episode-mismatch"}]

# Recovery must reject a different, individually valid episode before invoking
# the recovery lifecycle or observing a new task.
notification = {**fake_failure, "observation": {"alarm_state_updated_at": "2026-10-24T14:00:01Z"}}
with patch.object(controller, "candidate", return_value="sha256:" + "c" * 64), \
     patch.object(controller, "receipt_argument", side_effect=[fake_failure, notification]), \
     patch.object(controller, "lifecycle") as lifecycle, \
     patch.object(controller, "retained_source") as retained:
    code, report = invoke(["--receipt", "/tmp/candidate.json", "--operation", "recover", "--failure-receipt", "/tmp/failure.json", "--notification-receipt", "/tmp/notification.json"])
assert code == 1 and report["findings"] == [{"code": "observability-rehearsal-alarm-episode-mismatch"}]
lifecycle.assert_not_called(); retained.assert_not_called()

# The provider metric must be exact, recent and dimensioned; controller code
# must not treat an alarm state alone as evidence of readiness.
module = controller.receipts()
timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
with patch.object(controller, "aws", return_value={"MetricDataResults": [{"Values": [0], "Timestamps": [timestamp]}]}):
    observed = controller.metric(0)
assert observed["dimensions"] == module.DIMENSIONS and observed["metric_value"] == 0
with patch.object(controller, "aws", return_value={"MetricDataResults": [{"Values": [1], "Timestamps": [timestamp]}]}):
    try:
        controller.metric(0)
    except controller.RehearsalFailure as error:
        assert str(error) == "observability-rehearsal-metric-not-observed"
    else:
        raise AssertionError("wrong readiness metric passed")

print("observability readiness rehearsal checks passed")
