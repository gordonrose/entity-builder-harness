#!/usr/bin/env python3
"""Focused regression coverage for durable persistence proof receipts."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.persistence-proof-receipts
#   version: 3
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-11-27"
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
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

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
assert "stopped_reason" not in valid["task"]
private_task = {**task, "stoppedReason": "PRIVATE_RECEIPT_CANARY"}
private = module.make(proof_type="verifier", operation="read", task=private_task, image_digest="sha256:" + "b" * 64, result_code="KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", context=valid["context"], controller="verify-candidate", collected_at="2026-10-24T15:00:24Z")
assert "PRIVATE_RECEIPT_CANARY" not in json.dumps(private) and "stopped_reason" not in private["task"]
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
with tempfile.TemporaryDirectory() as directory:
    module.RECEIPTS = Path(directory)
    historical = copy.deepcopy(valid)
    historical["task"]["stopped_reason"] = "PRIVATE_HISTORICAL_REASON"
    historical["integrity"]["payload_sha256"] = module.digest({key: value for key, value in historical.items() if key != "integrity"})
    assert module.validate(historical) is historical
    stored = module.persist(historical)
    before = stored.read_bytes()
    assert module.persist(valid) == stored and stored.read_bytes() == before
    broken = copy.deepcopy(historical); broken["task"]["stopped_reason"] = "changed-without-rehash"
    stored.write_text(json.dumps(broken))
    try: module.persist(valid)
    except module.ReceiptError as error: assert str(error) == "persistence-proof-receipt-existing-invalid"
    else: raise AssertionError("semantic reuse bypassed historical integrity")
replacement_task = {**task, "stoppedReason": "governed core-server-persistence replacement rehearsal"}
replacement_context = {"original_stopped_reason": replacement_task["stoppedReason"], "successor_task_arn": module.TASK_ARN_PREFIX + "c" * 32, "successor_started_at": "2026-10-24T15:00:24Z", "runtime_task_definition": task["taskDefinitionArn"], "recovery_boundary": "2026-10-24T15:00:12Z"}
replacement = module.make(proof_type="server-replacement", operation="controlled-replacement", task=replacement_task, image_digest="sha256:" + "b" * 64, result_code="PERSISTENCE_SERVER_REPLACED", context=replacement_context, controller="rehearse-server-replacement", collected_at="2026-10-24T15:00:25Z")
assert replacement["task"]["stopped_reason"] == "governed core-server-persistence replacement rehearsal"
try: module.make(proof_type="server-replacement", operation="controlled-replacement", task=private_task, image_digest="sha256:" + "b" * 64, result_code="PERSISTENCE_SERVER_REPLACED", context=replacement_context, controller="rehearse-server-replacement", collected_at="2026-10-24T15:00:25Z")
except module.ReceiptError as error: assert str(error) == "persistence-proof-receipt-terminal-invalid"
else: raise AssertionError("unowned replacement reason retained")
try: module.make(proof_type="server-replacement", operation="controlled-replacement", task=replacement_task, image_digest="sha256:" + "b" * 64, result_code="PERSISTENCE_SERVER_REPLACED", context={**replacement_context, "original_stopped_reason": "PRIVATE_RECEIPT_CANARY"}, controller="rehearse-server-replacement", collected_at="2026-10-24T15:00:25Z")
except module.ReceiptError as error: assert str(error) == "persistence-proof-receipt-context-invalid"
else: raise AssertionError("unowned replacement context reason retained")
CANARY = "RECEIPT_STORAGE_CREDENTIAL_CANARY"
PREFIX = "arn:aws:ecs:eu-west-1:337159794548:task/s-" + "a" * 19 + "/"


def rejected(code, action):
    try: action()
    except module.ReceiptError as error:
        assert str(error) == "persistence-proof-receipt-" + code, str(error)
        assert CANARY not in str(error)
        return error
    raise AssertionError("expected receipt rejection: " + code)


def rehashed(value):
    value = copy.deepcopy(value)
    value["integrity"]["payload_sha256"] = module.digest({key: item for key, item in value.items() if key != "integrity"})
    return value


class Storage:
    def __init__(self):
        self.values, self.reads, self.writes = {}, [], []
        self.fail = None

    def read_receipt(self, label):
        self.reads.append(label)
        if self.fail == "read": raise OSError(CANARY)
        return self.values.get(label)

    def retain_receipt(self, label, proposed):
        self.writes.append((label, proposed))
        if self.fail == "write-before": raise OSError(CANARY)
        raw = self.values.setdefault(label, proposed)
        if self.fail == "write-after": raise OSError(CANARY)
        return raw


temporary_task = {**task, "taskArn": PREFIX + "a" * 32,
                  "taskDefinitionArn": "arn:aws:ecs:eu-west-1:337159794548:task-definition/s-" + "a"*19 + "-persistence-verifier:15"}
temporary = module.make(proof_type="verifier", operation="read", task=temporary_task,
    image_digest="sha256:" + "b"*64, result_code="KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED",
    context=valid["context"], controller="verify-candidate", collected_at="2026-10-24T15:00:24Z", task_arn_prefix=PREFIX)
assert module.validate(temporary, task_arn_prefix=PREFIX) is temporary
rejected("task-arn-invalid", lambda: module.validate(temporary))
rejected("task-arn-invalid", lambda: module.validate(valid, task_arn_prefix=PREFIX))
for prefix in (None, 1, PREFIX.replace("337159794548", "000000000000"), PREFIX.replace("eu-west-1", "eu-west-2"),
               PREFIX.replace("s-" + "a"*19, "*"), PREFIX + "extra/", PREFIX.replace("s-" + "a"*19, "..")):
    rejected("task-prefix-invalid", lambda: module.validate(temporary, task_arn_prefix=prefix))
foreign = rehashed({**temporary, "task": {**temporary["task"], "arn": PREFIX.replace("a"*19, "b"*19) + "a"*32}})
rejected("task-arn-invalid", lambda: module.validate(foreign, task_arn_prefix=PREFIX))
temporary_replacement = module.make(proof_type="server-replacement", operation="controlled-replacement",
    task={**temporary_task, "stoppedReason": replacement_task["stoppedReason"]}, image_digest="sha256:" + "b"*64,
    result_code="PERSISTENCE_SERVER_REPLACED", context={**replacement_context, "successor_task_arn": PREFIX + "c"*32},
    controller="rehearse-server-replacement", collected_at="2026-10-24T15:00:25Z", task_arn_prefix=PREFIX)
assert module.validate(temporary_replacement, task_arn_prefix=PREFIX) is temporary_replacement
for successor in (module.TASK_ARN_PREFIX + "c"*32, PREFIX.replace("a"*19, "b"*19) + "c"*32,
                  PREFIX.replace("337159794548", "000000000000") + "c"*32, PREFIX.replace("eu-west-1", "eu-west-2") + "c"*32):
    wrong = rehashed({**temporary_replacement, "context": {**temporary_replacement["context"], "successor_task_arn": successor}})
    rejected("context-invalid", lambda: module.validate(wrong, task_arn_prefix=PREFIX))
# This increment selects the prefix; it does not tighten historical suffix rules.
historical_suffix = rehashed({**replacement, "context": {**replacement["context"], "successor_task_arn": module.TASK_ARN_PREFIX + "historical-suffix"}})
assert module.validate(historical_suffix) is historical_suffix

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    module.RECEIPTS = root / "production-evidence"
    storage = Storage()
    kwargs = {"root": root, "storage": storage, "task_arn_prefix": PREFIX}
    with patch.object(module, "persist", side_effect=AssertionError("retained route must not write locally")):
        reference = module.retain(temporary, **kwargs)
        label = "verifier-read-" + "a"*32 + ".json"
        raw = (json.dumps(temporary, sort_keys=True, indent=2) + "\n").encode("utf-8")
        assert reference == {"path": label, "sha256": hashlib.sha256(raw).hexdigest()}
        assert reference["sha256"] != hashlib.sha256(module.canonical(temporary)).hexdigest()
        assert storage.writes == [(label, raw)]
        assert module.read(reference, **kwargs) == temporary
        assert not module.RECEIPTS.exists()
        repeated = rehashed({**temporary, "provenance": {**temporary["provenance"], "collected_at": "2026-10-25T15:00:24Z"}})
        assert module.retain(repeated, **kwargs) == reference
        assert storage.values[label] == raw and storage.writes[-1][1] != raw
        conflict = rehashed({**temporary, "context": {**temporary["context"], "record_id": "different"}})
        rejected("conflict", lambda: module.retain(conflict, **kwargs))
        assert storage.values[label] == raw
        historical = rehashed({**temporary, "task": {**temporary["task"], "stopped_reason": CANARY}})
        storage.values[label] = (json.dumps(historical, sort_keys=True, indent=2) + "\n").encode()
        retained = module.retain(temporary, **kwargs)
        assert retained["sha256"] == hashlib.sha256(storage.values[label]).hexdigest()
        assert module.read(retained, **kwargs) == historical
        storage.values[label] = raw
        rejected("reference-mismatch", lambda: module.read({**reference, "sha256": "f"*64}, **kwargs))
        for wrong in ({}, {**reference, "extra": True}, {**reference, "path": "../" + label},
                      {**reference, "path": "/" + label}, {**reference, "path": "nested/" + label},
                      {**reference, "path": "unknown-read-" + "a"*32 + ".json"}, {**reference, "sha256": True}):
            reads_before = len(storage.reads)
            rejected("reference-invalid", lambda: module.read(wrong, **kwargs))
            assert len(storage.reads) == reads_before
        other_label = "verifier-create-" + "a"*32 + ".json"
        storage.values[other_label] = raw
        rejected("reference-mismatch", lambda: module.read({**reference, "path": other_label}, **kwargs))
        wrong_task = rehashed({**temporary, "task": {**temporary["task"], "arn": PREFIX + "b"*32}})
        storage.values[label] = (json.dumps(wrong_task) + "\n").encode()
        rejected("conflict", lambda: module.retain(temporary, **kwargs))
        for malformed in (None, True, {}, raw.decode(), bytearray(raw), b"", b"{", b"\xff", b"["*100000 + b"]"*100000, b"x"*(module.MAX_RECEIPT_BYTES+1)):
            storage.values[label] = malformed
            writes_before, reads_before = len(storage.writes), len(storage.reads)
            rejected("storage-invalid", lambda: module.retain(temporary, **kwargs))
            changed_reference = {**reference, "sha256": hashlib.sha256(malformed).hexdigest()} if type(malformed) is bytes else reference
            rejected("storage-invalid", lambda: module.read(changed_reference, **kwargs))
            assert len(storage.writes) == writes_before + 1 and len(storage.reads) == reads_before + 1
        storage.values[label] = raw
        for outcome in ("write-before", "write-after"):
            lost = Storage(); lost.fail = outcome
            error = rejected("retention-not-confirmed", lambda: module.retain(temporary, root=root, storage=lost, task_arn_prefix=PREFIX))
            assert error.__suppress_context__
            assert len(lost.writes) == 1
            lost.fail = None
            confirmed = module.retain(temporary, root=root, storage=lost, task_arn_prefix=PREFIX)
            assert confirmed == reference
        storage.fail = "read"
        error = rejected("storage-unavailable", lambda: module.read(reference, **kwargs))
        assert error.__suppress_context__
        storage.fail = None
        oversized = rehashed({**temporary, "context": {**temporary["context"], "record_id": "a"*module.MAX_RECEIPT_BYTES}})
        writes_before = len(storage.writes)
        rejected("storage-invalid", lambda: module.retain(oversized, **kwargs))
        assert len(storage.writes) == writes_before
        for malformed_storage in (object(), type("ReadOnly", (), {"read_receipt": lambda *_: raw})()):
            rejected("storage-invalid", lambda: module.retain(temporary, root=root, storage=malformed_storage, task_arn_prefix=PREFIX))
        assert not module.RECEIPTS.exists()
    # The new local reference route preserves the existing Path writer and bytes.
    local = module.retain(valid, root=root)
    local_path = root / local["path"]
    assert local_path == module.persist(valid)
    assert local_path.read_bytes() == (json.dumps(valid, sort_keys=True, indent=2) + "\n").encode()
    assert local["sha256"] == hashlib.sha256(local_path.read_bytes()).hexdigest()
    assert module.read(local, root=root) == valid
    assert module.retain(valid, root=root) == local
    rejected("task-arn-invalid", lambda: module.retain(temporary, root=root, task_arn_prefix=PREFIX))
    assert list(module.RECEIPTS.iterdir()) == [local_path]

print("durable persistence proof receipt checks passed (local parity and retained storage)")
