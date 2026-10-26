#!/usr/bin/env python3
"""Focused offline checks for bounded observability-MVP evidence."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.observability-receipts
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise integrity, allowlist and persistence rules for readiness-observability receipts.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.test.persistence-acceptance-route
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal/smoke-test.sh
#   effects: [read-only, writes-files]
import copy
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
SOURCE = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts.py"
spec = importlib.util.spec_from_file_location("observability_receipts", SOURCE)
module = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module)

source = {
    "path": "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts/verifier-health-unready-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.json",
    "sha256": "sha256:" + "a" * 64,
    "task_arn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "a" * 32,
    "task_definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:1",
    "image_digest": "sha256:" + "b" * 64,
    "result_code": "KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY",
}
failure_observation = {
    "alarm_name": module.ALARM, "alarm_state": "ALARM", "alarm_state_updated_at": "2026-10-26T12:00:00Z",
    "metric_name": module.METRIC, "dimensions": module.DIMENSIONS, "metric_value": 0, "metric_observed_at": "2026-10-26T11:59:00Z",
}
failure = module.make(receipt_type="readiness-failure-observed", source_proof=source, observation_value=failure_observation, collected_at="2026-10-26T12:00:01Z")
assert module.validate(failure) == failure
notification = module.make(receipt_type="readiness-alarm-notified", source_proof=source, observation_value={"alarm_name": module.ALARM, "alarm_state": "ALARM", "alarm_state_updated_at": "2026-10-26T12:00:00Z", "subscription_confirmed_at": "2026-10-26T11:50:00Z", "operator_delivery_confirmed_at": "2026-10-26T12:01:00Z"}, collected_at="2026-10-26T12:01:01Z")
assert module.validate(notification) == notification
recovery_source = {**source, "result_code": "KANBIEN_CORE_PERSISTENCE_HEALTHY"}
recovery = module.make(receipt_type="readiness-recovery-observed", source_proof=recovery_source, observation_value={"alarm_name": module.ALARM, "alarm_state": "OK", "alarm_state_updated_at": "2026-10-26T12:03:00Z", "metric_name": module.METRIC, "dimensions": module.DIMENSIONS, "metric_value": 1, "metric_observed_at": "2026-10-26T12:02:00Z"}, collected_at="2026-10-26T12:03:01Z")
assert module.validate(recovery) == recovery
for broken in (lambda v: v.update(receipt_type="unknown"), lambda v: v["observation"].update(dimensions={}), lambda v: v["observation"].update(provider_message="unsafe"), lambda v: v["source_proof"].update(result_code="OTHER")):
    value = copy.deepcopy(failure); broken(value)
    try: module.validate(value)
    except module.ReceiptError: pass
    else: raise AssertionError("invalid observability receipt passed")
with tempfile.TemporaryDirectory() as directory:
    module.RECEIPTS = Path(directory)
    first = module.persist(failure)
    assert module.persist(failure) == first
    changed = copy.deepcopy(failure); changed["provenance"]["collected_at"] = "2026-10-26T12:00:02Z"; changed["integrity"]["payload_sha256"] = module.digest({key: value for key, value in changed.items() if key != "integrity"})
    assert module.persist(changed) != first
print("observability receipt checks passed")
