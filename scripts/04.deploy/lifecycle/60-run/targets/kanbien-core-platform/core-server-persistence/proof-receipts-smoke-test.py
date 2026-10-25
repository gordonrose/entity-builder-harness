#!/usr/bin/env python3
"""Focused regression coverage for durable persistence proof receipts."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.persistence-proof-receipts
#   version: 2
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise retained persistence proof receipt integrity and conflict rejection without provider calls.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/core-server-persistence/create-and-verify-private-postgresql-candidate.md
#   effects: [read-only, writes-files]
from __future__ import annotations
import copy
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
PATH = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py"
spec = importlib.util.spec_from_file_location("proof_receipts", PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

task = {
    "taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "a" * 32,
    "taskDefinitionArn": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:15",
    "startedAt": "2026-10-24T15:00:00Z", "stoppedAt": "2026-10-24T15:00:23Z", "lastStatus": "STOPPED",
    "containers": [{"exitCode": 0}],
}
valid = module.make(proof_type="verifier", operation="read", task=task, image_digest="sha256:" + "b" * 64, result_code="KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", context={"record_id": "core-persistence-acceptance-v1", "completion_deadline_seconds": 120, "completion_duration_seconds": 23}, controller="verify-candidate", collected_at="2026-10-24T15:00:24Z")
assert module.validate(valid) == valid
administration_task = {**task, "taskDefinitionArn": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:15"}
administration = module.make(proof_type="administration", operation="prove-effective-privilege", task=administration_task, image_digest="sha256:" + "d" * 64, result_code="PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN", context={"completion_deadline_seconds": 300, "completion_duration_seconds": 23}, controller="run-administration", collected_at="2026-10-24T15:00:24Z")
assert module.validate(administration) == administration
for mutate in (
    lambda value: value["task"].update({"exit_code": None}),
    lambda value: value.update({"target": "other-target"}),
    lambda value: value["task"].update({"image_digest": "sha256:" + "c" * 64}),
    lambda value: value["context"].update({"provider_message": "not allowlisted"}),
):
    changed = copy.deepcopy(valid); mutate(changed)
    try:
        module.validate(changed)
    except module.ReceiptError:
        pass
    else:
        raise AssertionError("tampered/incomplete receipt unexpectedly passed")
with tempfile.TemporaryDirectory() as directory:
    module.RECEIPTS = Path(directory)
    stored = module.persist(valid)
    assert stored.exists() and module.persist(valid) == stored
    original_bytes = stored.read_bytes()
    repeated = copy.deepcopy(valid)
    repeated['provenance']['collected_at'] = '2026-10-25T15:00:24Z'
    repeated['integrity']['payload_sha256'] = module.digest({key: value for key, value in repeated.items() if key != 'integrity'})
    assert module.persist(repeated) == stored and stored.read_bytes() == original_bytes
    conflict = copy.deepcopy(valid); conflict["context"]["record_id"] = "other"; conflict["integrity"]["payload_sha256"] = module.digest({key: value for key, value in conflict.items() if key != "integrity"})
    try:
        module.persist(conflict)
    except module.ReceiptError as error:
        assert str(error) == "persistence-proof-receipt-conflict"
    else:
        raise AssertionError("conflicting receipt unexpectedly passed")
print("durable persistence proof receipt checks passed")
