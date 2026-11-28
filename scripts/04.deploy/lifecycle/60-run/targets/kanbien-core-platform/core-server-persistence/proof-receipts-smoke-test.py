#!/usr/bin/env python3
"""Focused regression coverage for durable persistence proof receipts."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.persistence-proof-receipts
#   version: 3
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-11-28"
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
import io
import json
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace
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
def authenticated_maintenance_checks():
    """Exercise the real source-owned publisher and archive reader, offline."""
    package = "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/"
    custody = module.owner("maintenance_test_custody", package + "validate.py")
    publisher = module.owner("maintenance_test_publisher", "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/publication.py").PUBLISHER.binding
    revision, program = "a" * 40, "kanbien-core-server-persistence"
    receipt = {"schema": custody.SCHEMA, "target": module.TARGET, "environment_class": "staging", "provider_region_alias": "aws-eu-west-1",
        "candidate_id": program + "-candidate", "package_contract_id": program + "-image", "program_id": program,
        "source_revision": revision, "image_digest": "sha256:" + "b" * 64, "release_identity": "proof",
        "checked_at": "2026-11-27T05:09:00Z", "checks": {key: "passed" for key in custody.BASE_CHECKS | {"ecr_scan"}},
        "verdict": "qualified", "receipt_reference": "github-actions-run:1"}
    inputs = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        "infra/04.deploy/03.product/image/core-server-persistence/image-contract.yml",
        "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml")}
    configurations = []
    for adapter, source, selector in publisher.configuration:
        projection = module.owner("maintenance_test_configuration", adapter).package_projection(ROOT / source, selector)
        configurations.append({"adapter": adapter, "source": source, "selector": selector,
            "adapter_sha256": hashlib.sha256((ROOT / adapter).read_bytes()).hexdigest(),
            "projection_sha256": hashlib.sha256(module.canonical(projection)).hexdigest()})
    documents = {"package-custody-receipt.json": receipt, "qualified-image.json": {
        "schema": "deploy/local-image-qualification/v1", "image_id": "sha256:" + "c" * 64,
        "inputs": inputs, "configuration_inputs": configurations}}
    prefix = "repos/" + publisher.source_repository + "/actions/"
    run = {"id": 1, "run_attempt": 1, "repository": {"id": 2, "full_name": publisher.source_repository},
        "head_repository": {"id": 2, "full_name": publisher.source_repository}, "head_branch": "main", "head_sha": revision,
        "path": ".github/workflows/" + publisher.workflow, "event": "workflow_dispatch", "status": "completed", "conclusion": "success",
        "run_started_at": "2026-11-27T05:00:00Z", "updated_at": "2026-11-27T05:10:00Z"}

    def archive_provider(changed_documents=None, changed_run=None, artifact_mutation=None):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for name, value in (documents if changed_documents is None else changed_documents).items():
                archive.writestr(name, json.dumps(value))
        raw = stream.getvalue()
        artifact = {"id": 3, "name": "kanbien-core-platform-persistence-package-custody-1", "size_in_bytes": len(raw),
            "expired": False, "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "created_at": "2026-11-27T05:09:00Z", "updated_at": "2026-11-27T05:09:00Z",
            "workflow_run": {"id": 1, "repository_id": 2, "head_repository_id": 2, "head_branch": "main", "head_sha": revision}}
        if artifact_mutation: artifact_mutation(artifact)
        replies = {prefix + "runs/1": run if changed_run is None else changed_run,
            prefix + "runs/1/artifacts?per_page=100": {"total_count": 1, "artifacts": [artifact]}}
        calls = []
        def get(path):
            calls.append(path)
            return raw if path == prefix + "artifacts/3/zip" else json.dumps(replies[path]).encode()
        get.calls = calls
        return get

    def git(argv, **_options):
        assert argv[:3] == ["git", "-C", str(ROOT)]
        return SimpleNamespace(stdout=revision if argv[-1] == "HEAD" else "")

    with tempfile.TemporaryDirectory() as directory:
        selected = Path(directory) / "receipt.json"
        selected.write_text(json.dumps(receipt))
        def reject(get, *, source=git):
            with patch.object(module.subprocess, "run", side_effect=source):
                try: module.qualified_maintenance(selected, get=get)
                except module.ReceiptError as error:
                    assert str(error) == "persistence-scheduling-maintenance-custody-invalid"
                    assert "PRIVATE_AUTH_CANARY" not in str(error)
                else: raise AssertionError("untrusted maintenance custody accepted")
        get = archive_provider()
        with patch.object(module.subprocess, "run", side_effect=git):
            assert module.qualified_maintenance(selected, get=get) == receipt
        assert get.calls == [prefix + "runs/1", prefix + "runs/1/artifacts?per_page=100", prefix + "artifacts/3/zip"]
        for key, value in (("head_branch", "PRIVATE_AUTH_CANARY"), ("head_sha", "d" * 40), ("conclusion", "failure"),
                ("path", ".github/workflows/foreign.yml"), ("run_attempt", 2)):
            reject(archive_provider(changed_run={**run, key: value}))
        for mutate in (lambda value: value.update(expired=True), lambda value: value.update(digest="sha256:" + "0" * 64),
                lambda value: value.update(name="foreign-private-artifact")):
            reject(archive_provider(artifact_mutation=mutate))
        for mutate in (
            lambda value: value["package-custody-receipt.json"].update(image_digest="sha256:" + "e" * 64),
            lambda value: value["qualified-image.json"].update(configuration_inputs=[]),
            lambda value: value["qualified-image.json"].update(inputs={next(iter(inputs)): "0" * 64}),
            lambda value: value["qualified-image.json"].update(inputs={"../PRIVATE_AUTH_CANARY": "0" * 64}),
            lambda value: value["qualified-image.json"].update(image_id="invalid"),
        ):
            changed = copy.deepcopy(documents); mutate(changed)
            reject(archive_provider(changed_documents=changed))
        get = archive_provider()
        reject(get, source=lambda *_args, **_kwargs: SimpleNamespace(stdout="d" * 40))
        assert not get.calls, "wrong checkout must fail before provider reads"
        get = archive_provider()
        reject(get, source=lambda argv, **kwargs: SimpleNamespace(stdout=" M platform/PRIVATE_AUTH_CANARY.ts\0") if "status" in argv else git(argv, **kwargs))
        assert not get.calls, "dirty executable inputs must fail before provider reads"
        generated = next((ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts").glob("administration-*.json")).relative_to(ROOT).as_posix()
        def generated_receipt(argv, **kwargs):
            return SimpleNamespace(stdout="?? " + generated + "\0") if "status" in argv else git(argv, **kwargs)
        get = archive_provider()
        with patch.object(module.subprocess, "run", side_effect=generated_receipt):
            assert module.qualified_maintenance(selected, get=get) == receipt
        assert len(get.calls) == 3, "new native receipts do not waive actual package authentication"
        get = archive_provider()
        reject(get, source=lambda argv, **kwargs: SimpleNamespace(stdout="?? PRIVATE_AUTH_CANARY") if "status" in argv else git(argv, **kwargs))
        assert not get.calls, "unavailable or malformed source observation cannot authenticate maintenance"
        selected.write_text(json.dumps({**receipt, "program_id": "kanbien-entity-smoke"}))
        get = archive_provider(); reject(get)
        assert not get.calls, "foreign package must fail before provider reads"


authenticated_maintenance_checks()
print("durable persistence proof receipt and authenticated maintenance checks passed")
