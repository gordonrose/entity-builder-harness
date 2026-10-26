#!/usr/bin/env python3
"""Offline regression coverage for the bounded readiness-alert rehearsal."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.rehearse-observability-readiness.impl
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
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
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[8]
BASE = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence"
spec = importlib.util.spec_from_file_location("observability_rehearsal", BASE / "rehearse-observability-readiness/script.py")
controller = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(controller)


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
