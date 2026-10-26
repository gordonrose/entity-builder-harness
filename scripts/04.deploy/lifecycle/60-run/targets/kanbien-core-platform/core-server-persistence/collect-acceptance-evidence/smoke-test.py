#!/usr/bin/env python3
"""Regression coverage for retained-proof receipt acceptance parsing."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.persistence-acceptance-receipts
#   version: 2
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise retained persistence acceptance receipt parsing without AWS calls.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/core-server-persistence/create-and-verify-private-postgresql-candidate.md
#   effects: [read-only, writes-files]
from __future__ import annotations
import copy
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[8]
BASE = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence"
def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path); module = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module); return module
collector = load("collector", BASE / "collect-acceptance-evidence/script.py")
receipts = load("proof_receipts", BASE / "proof-receipts.py")
receipts.EVIDENCE_CLASS = collector.EVIDENCE_CLASS = "simulated"

candidate, rollback = "sha256:" + "a" * 64, "sha256:" + "b" * 64
required = {
 "migration-applied-state": ("administration", "kanbien-core-platform-persistence-administration", candidate, "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED", "persistence-administration"),
 "effective-privilege": ("administration", "kanbien-core-platform-persistence-administration", candidate, "PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN", "persistence-administration"),
 "server-replacement": ("server-replacement", "kanbien-core-platform-core-server-persistence", candidate, "PERSISTENCE_SERVER_REPLACED", None),
 "server-replacement-read": ("verifier", "kanbien-core-platform-persistence-verifier", candidate, "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", "private-release-verifier"),
 "runtime-identity-initial-access": ("administration", "kanbien-core-platform-persistence-administration", candidate, "PERSISTENCE_RUNTIME_IAM_ACCESS_CONFIRMED", "persistence-administration"),
 "credential-revocation": ("administration", "kanbien-core-platform-persistence-administration", candidate, "PERSISTENCE_RUNTIME_IAM_ACCESS_REVOKED", "persistence-administration"),
 "credential-revocation-unready": ("verifier", "kanbien-core-platform-persistence-verifier", candidate, "KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY", "private-release-verifier"),
 "credential-recovery": ("administration", "kanbien-core-platform-persistence-administration", candidate, "PERSISTENCE_RUNTIME_IAM_ACCESS_RESTORED", "persistence-administration"),
 "credential-recovery-health": ("verifier", "kanbien-core-platform-persistence-verifier", candidate, "KANBIEN_CORE_PERSISTENCE_HEALTHY", "private-release-verifier"),
 "credential-recovery-read": ("verifier", "kanbien-core-platform-persistence-verifier", candidate, "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", "private-release-verifier"),
 "rollback-b-health": ("verifier", "kanbien-core-platform-persistence-verifier", rollback, "KANBIEN_CORE_PERSISTENCE_HEALTHY", "private-release-verifier"),
 "rollback-b-read": ("verifier", "kanbien-core-platform-persistence-verifier", rollback, "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", "private-release-verifier"),
 "rollback-final-health": ("verifier", "kanbien-core-platform-persistence-verifier", candidate, "KANBIEN_CORE_PERSISTENCE_HEALTHY", "private-release-verifier"),
 "rollback-final-read": ("verifier", "kanbien-core-platform-persistence-verifier", candidate, "KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", "private-release-verifier"),
 "isolated-restore": ("restore", "kanbien-core-platform-persistence-restoration-verifier", candidate, "KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED", "persistence-restoration-verifier"),
}
operations = {"migration-applied-state":"observe-migration-state","effective-privilege":"prove-effective-privilege","server-replacement":"controlled-replacement","server-replacement-read":"read","runtime-identity-initial-access":"confirm-runtime-iam-access","credential-revocation":"revoke-runtime","credential-revocation-unready":"health-unready","credential-recovery":"restore-runtime","credential-recovery-health":"health-ready","credential-recovery-read":"read","rollback-b-health":"health-ready","rollback-b-read":"read","rollback-final-health":"health-ready","rollback-final-read":"read","isolated-restore":"isolated-restore"}
controllers={"administration":"run-administration","migration":"run-migration","verifier":"verify-candidate","restore":"rehearse-isolated-database-restore","server-replacement":"rehearse-server-replacement"}
deadlines={"persistence-migration":300,"persistence-administration":300,"private-release-verifier":120,"persistence-restoration-verifier":120}
directory = Path(tempfile.mkdtemp(prefix="persistence-proof-receipt-"))
try:
    arguments=[]
    for index,(name,(kind,family,digest,code,workload)) in enumerate(required.items()):
        task={"taskArn":f"arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/{index:032x}","taskDefinitionArn":f"arn:aws:ecs:eu-west-1:337159794548:task-definition/{family}:15","startedAt":f"2026-10-24T15:{index:02d}:00Z","stoppedAt":f"2026-10-24T15:{index:02d}:23Z","lastStatus":"STOPPED","containers":[{"exitCode":0}]}
        if kind in {"administration", "migration"}: context={"completion_deadline_seconds":deadlines[workload],"completion_duration_seconds":23}
        elif kind == "verifier": context={"record_id":"acceptance-record","completion_deadline_seconds":deadlines[workload],"completion_duration_seconds":23}
        elif kind == "restore": context={"snapshot":"kanbien-core-platform-persistence-recovery-20261024-r3","restored_database":"kanbien-core-platform-persistence-restore-20261024-r3","completion_deadline_seconds":deadlines[workload],"completion_duration_seconds":23}
        else:
            task["stoppedReason"]="governed core-server-persistence replacement rehearsal"
            context={"original_stopped_reason":"governed core-server-persistence replacement rehearsal","successor_task_arn":"arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/ffffffffffffffffffffffffffffffff","successor_started_at":f"2026-10-24T15:{index:02d}:24Z","runtime_task_definition":task["taskDefinitionArn"],"recovery_boundary":f"2026-10-24T15:{index:02d}:12Z"}
        item=receipts.make(proof_type=kind,operation=operations[name],task=task,image_digest=digest,result_code=code,context=context,controller=controllers[kind],collected_at=f"2026-10-24T15:{index:02d}:24Z")
        path=directory/f"{name}.json"; path.write_text(json.dumps(item),encoding="utf-8"); arguments.append(f"{name}={path}")
    # Retained receipts remain usable after ECS has aged the stopped tasks out:
    # parsing must not make an ECS query for those historical operations.
    with patch.object(collector, "aws", side_effect=AssertionError("historical ECS lookup")):
        observed = collector.parse_proof_receipts(arguments,required,deadlines,directory)
    assert set(observed) == set(required)
    # A qualified applicability record may carry only the named predecessor
    # proofs across the exact restore-verifier-only image change.  Without it,
    # a historical digest cannot be silently accepted.
    predecessor = "sha256:" + "c" * 64
    migration_path = directory / "migration-applied-state.json"
    original_migration = json.loads(migration_path.read_text())
    historical_migration = copy.deepcopy(original_migration)
    historical_migration["task"]["image_digest"] = predecessor
    historical_migration["integrity"]["payload_sha256"] = receipts.digest({key: value for key, value in historical_migration.items() if key != "integrity"})
    migration_path.write_text(json.dumps(historical_migration), encoding="utf-8")
    try:
        collector.parse_proof_receipts(arguments, required, deadlines, directory)
    except collector.EvidenceFailure as error:
        assert str(error) == "acceptance-evidence-proof-receipt-mismatch"
    else:
        raise AssertionError("historical proof passed without applicability")
    applicability = {"predecessor": {"image_digest": predecessor}, "reused_proofs": ["migration-applied-state"]}
    assert set(collector.parse_proof_receipts(arguments, required, deadlines, directory, applicability=applicability)) == set(required)
    migration_path.write_text(json.dumps(original_migration), encoding="utf-8")
    restore_path = directory / "isolated-restore.json"
    original_restore = json.loads(restore_path.read_text())
    historical_restore = copy.deepcopy(original_restore)
    historical_restore["task"]["image_digest"] = predecessor
    historical_restore["integrity"]["payload_sha256"] = receipts.digest({key: value for key, value in historical_restore.items() if key != "integrity"})
    restore_path.write_text(json.dumps(historical_restore), encoding="utf-8")
    try:
        collector.parse_proof_receipts(arguments, required, deadlines, directory, applicability=applicability)
    except collector.EvidenceFailure as error:
        assert str(error) == "acceptance-evidence-proof-receipt-mismatch"
    else:
        raise AssertionError("historical restore proof passed")
    restore_path.write_text(json.dumps(original_restore), encoding="utf-8")
    retained = collector.EVIDENCE_ROOT / "proof-receipts/migration-apply-6ac40437365f4a72b1d86cc42a664a83.json"
    candidate_path, successor = collector.candidate_record(
        {"source_revision": "f" * 40, "image_digest": candidate, "receipt_reference": "test-receipt"},
        {"migration-apply": {"receipt": str(retained.relative_to(collector.ROOT))}},
        "2026-10-25T10:00:00Z",
    )
    succession = collector.succession_module()
    assert candidate_path.name == successor["release"]["id"] + ".yml"
    assert succession.candidate_identity(successor)[0:2] == (collector.TARGET, collector.SCOPE)
    broken=directory/"migration-applied-state.json"; value=json.loads(broken.read_text()); value["task"]["exit_code"]=None; broken.write_text(json.dumps(value),encoding="utf-8")
    try: collector.parse_proof_receipts(arguments,required,deadlines,directory)
    except collector.EvidenceFailure: pass
    else: raise AssertionError("incomplete retained task proof passed")
    # Historical receipts never replace fresh observation of current safety and
    # cleanup posture.
    try:
        with patch.object(collector, "aws", return_value={"services": [{"status": "ACTIVE", "desiredCount": 1, "runningCount": 0}]}):
            collector.current_service("arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-core-server-persistence:1", {"image_digest": candidate, "source_revision": "f" * 40}, candidate)
    except collector.EvidenceFailure as error:
        assert str(error) == "acceptance-evidence-current-service-unhealthy"
    else:
        raise AssertionError("unhealthy current service was concealed by historical receipts")
    try:
        with patch.object(collector, "aws", return_value={"DBInstances": [{"DBInstanceStatus": "available", "Engine": "postgres", "PubliclyAccessible": False, "StorageEncrypted": True, "DeletionProtection": False}]}):
            collector.database_posture("kanbien-core-platform-persistence-recovery-20261024-r3", {})
    except collector.EvidenceFailure as error:
        assert str(error) == "acceptance-evidence-source-database-posture-invalid"
    else:
        raise AssertionError("incomplete restore-cleanup posture was concealed by historical receipts")
finally:
    shutil.rmtree(directory)
print("retained persistence acceptance receipt checks passed")

# Current-state proof remains fresh even when historical task receipts are reused.
import subprocess, sys
subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("current-observations-test.py"))], check=True)
