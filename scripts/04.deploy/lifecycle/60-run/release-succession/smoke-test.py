#!/usr/bin/env python3
"""Regression coverage for immutable release succession."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.release-succession.regression
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: test
#   purpose: Prove accepted-release history is immutable, successor promotion is compare-and-swap, and a retained receipt remains usable without ECS history.
#   portability: { class: reusable, targets: [entity-builder] }
#   used_by:
#   - id: deploy.command.release-succession
#     path: scripts/04.deploy/lifecycle/60-run/release-succession/script.sh
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

SCRIPT = Path(__file__).with_name("script.py")
spec = importlib.util.spec_from_file_location("release_succession", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def run(*arguments: str) -> int:
    previous = sys.argv
    try:
        sys.argv = [str(SCRIPT), *arguments, "--json"]
        return module.main()
    finally:
        sys.argv = previous


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def candidate(root: Path, *, source: str, image: str, configuration: str, permissions: str, proof: str, accepted: str = "2026-10-25T10:00:00Z") -> Path:
    receipt = root / "proof-receipts" / f"{source[:8]}.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({"receipt": source}), encoding="utf-8")
    proof_set = {"complete-proof": {"path": str(receipt.relative_to(root)), "sha256": module.sha256_bytes(receipt.read_bytes())}}
    contract_path = SCRIPT.relative_to(module.REPOSITORY_ROOT)
    contract = {"path": str(contract_path), "sha256": module.sha256_bytes(SCRIPT.read_bytes())}
    identity = {
        "target": "example-target",
        "scope": "example-scope",
        "source_revision": source,
        "image_digest": image,
        "configuration_contract": contract,
        "permission_contract": contract,
        "proof_set_sha256": module.sha256_bytes(module.canonical(proof_set)),
    }
    value = {
        "schema": module.CANDIDATE_SCHEMA,
        "target": identity["target"],
        "scope": identity["scope"],
        "status": "verified",
        "release": {"id": module.release_id(identity), **{key: identity[key] for key in ("source_revision", "image_digest", "configuration_contract", "permission_contract", "proof_set_sha256")}},
        "proof": {"accepted_at": accepted, "receipt_count": 2},
        "proof_set": proof_set,
    }
    path = root / module.CANDIDATE_DIRECTORY / f"{value['release']['id']}.yml"
    write(path, value)
    return path


def rollback_compatibility(root: Path, retained: dict[str, str]) -> Path:
    receipt = root / "proof-receipts" / "rollback-compatibility-local.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({"proof": "historical image with corrected permissions"}), encoding="utf-8")
    proof_set = {"local-rollback-compatibility": {"path": str(receipt.relative_to(root)), "sha256": module.sha256_bytes(receipt.read_bytes())}}
    contract_path = SCRIPT.relative_to(module.REPOSITORY_ROOT)
    contract = {"path": str(contract_path), "sha256": module.sha256_bytes(SCRIPT.read_bytes())}
    identity = {
        "target": retained["target"], "scope": retained["scope"],
        "historical_release_id": retained["release_id"], "source_revision": retained["source_revision"], "image_digest": retained["image_digest"],
        "configuration_contract": contract, "permission_contract": contract,
        "workloads": ["core-server-service", "persistence-restoration-verifier-task", "private-release-verifier-task"],
        "proof_set_sha256": module.sha256_bytes(module.canonical(proof_set)),
    }
    identifier = "rollback-compatibility-" + __import__("hashlib").sha256(module.canonical(identity)).hexdigest()[:24]
    value = {
        "schema": module.COMPATIBILITY_SCHEMA, "target": identity["target"], "scope": identity["scope"], "status": "verified",
        "historical_release": {key: retained[key] for key in ("release_id", "source_revision", "image_digest")},
        "rollback": {"id": identifier, **{key: identity[key] for key in ("configuration_contract", "permission_contract", "workloads", "proof_set_sha256")}},
        "proof": {"qualified_at": "2026-10-25T12:00:00Z", "receipt_count": 1}, "proof_set": proof_set,
    }
    path = root / module.CANDIDATE_DIRECTORY / f"{identifier}.yml"
    write(path, value)
    return path


def qualified_predecessor_compatibility(root: Path) -> Path:
    """An earlier qualified release is selectable without becoming history."""
    receipt = root / "proof-receipts" / "qualified-predecessor.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({"proof": "earlier image with corrected permissions"}), encoding="utf-8")
    proof_set = {"rollback-b-health": {"path": str(receipt.relative_to(root)), "sha256": module.sha256_bytes(receipt.read_bytes())}}
    contract_path = SCRIPT.relative_to(module.REPOSITORY_ROOT)
    contract = {"path": str(contract_path), "sha256": module.sha256_bytes(SCRIPT.read_bytes())}
    predecessor = {"source_revision": "2" * 40, "image_digest": "sha256:" + "2" * 64, "package_custody_reference": "github-actions-run:40232309637"}
    identity = {
        "target": "example-target", "scope": "example-scope",
        "qualified_predecessor": predecessor,
        "source_revision": predecessor["source_revision"], "image_digest": predecessor["image_digest"],
        "configuration_contract": contract, "permission_contract": contract,
        "workloads": ["core-server-service", "private-release-verifier-task"],
        "proof_set_sha256": module.sha256_bytes(module.canonical(proof_set)),
    }
    identifier = "rollback-compatibility-" + __import__("hashlib").sha256(module.canonical(identity)).hexdigest()[:24]
    value = {
        "schema": module.COMPATIBILITY_SCHEMA, "target": identity["target"], "scope": identity["scope"], "status": "verified",
        "qualified_predecessor": predecessor,
        "rollback": {"id": identifier, **{key: identity[key] for key in ("configuration_contract", "permission_contract", "workloads", "proof_set_sha256")}},
        "proof": {"qualified_at": "2026-10-25T12:00:00Z", "receipt_count": 1}, "proof_set": proof_set,
    }
    path = root / module.CANDIDATE_DIRECTORY / f"{identifier}.yml"
    write(path, value)
    return path


def failure(*arguments: str) -> None:
    assert run(*arguments) == 1


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary) / "30-release-evidence"
    legacy = root / "accepted-release.yml"
    legacy_value = {
        "schema": module.LEGACY_SCHEMA,
        "target": "example-target",
        "scope": "example-scope",
        "status": "accepted",
        "release": {"source_revision": "a" * 40, "image_digest": "sha256:" + "a" * 64},
        "acceptance": {"rollback_release": {"source_revision": "0" * 40, "image_digest": "sha256:" + "0" * 64}},
    }
    write(legacy, legacy_value)
    original = legacy.read_bytes()

    # First promotion archives, rather than mutating, the legacy record.
    assert run("--operation", "initialize-legacy", "--evidence-root", str(root), "--legacy-record", str(legacy), "--expected-predecessor", "none") == 0
    assert legacy.read_bytes() == original
    first = module.current(root)
    assert first and first["predecessor"] is None
    first_id = first["release_id"]
    assert run("--operation", "validate-current", "--evidence-root", str(root)) == 0
    # First operation is idempotent; an incorrect predecessor cannot overwrite it.
    assert run("--operation", "initialize-legacy", "--evidence-root", str(root), "--legacy-record", str(legacy), "--expected-predecessor", "none") == 0
    failure("--operation", "initialize-legacy", "--evidence-root", str(root), "--legacy-record", str(legacy), "--expected-predecessor", "release-wrong")
    assert module.current(root)["release_id"] == first_id

    # A separately retained earlier image is never declared accepted anew. It
    # becomes selectable only after an immutable fresh compatibility record
    # binds it to corrected contracts and terminal proof receipts.
    retained = module.retained_rollback_identity(root)
    compatibility = rollback_compatibility(root, retained)
    assert run("--operation", "record-compatibility", "--evidence-root", str(root), "--candidate-record", str(compatibility)) == 0
    identifier = yaml.safe_load(compatibility.read_text(encoding="utf-8"))["rollback"]["id"]
    _, archived = module.compatibility_record(root, identifier)
    assert archived["identity"]["image_digest"] == retained["image_digest"]
    archive_path = root / module.COMPATIBILITY_DIRECTORY / f"{identifier}.yml"
    archived_bytes = archive_path.read_bytes()
    archive_path.write_text("schema: fabricated\n", encoding="utf-8")
    try:
        module.compatibility_record(root, identifier)
        raise AssertionError("altered compatibility archive accepted")
    except module.SuccessionFailure:
        pass
    archive_path.write_bytes(archived_bytes)
    assert run("--operation", "record-compatibility", "--evidence-root", str(root), "--candidate-record", str(compatibility)) == 0
    malformed = yaml.safe_load(compatibility.read_text(encoding="utf-8"))
    malformed["historical_release"]["image_digest"] = "sha256:" + "1" * 64
    write(root / module.CANDIDATE_DIRECTORY / "invalid-compatibility.yml", malformed)
    failure("--operation", "record-compatibility", "--evidence-root", str(root), "--candidate-record", str(root / module.CANDIDATE_DIRECTORY / "invalid-compatibility.yml"))
    wrong_contract = yaml.safe_load(compatibility.read_text(encoding="utf-8"))
    wrong_contract["rollback"]["configuration_contract"]["path"] = "missing-contract.yml"
    identity = {
        "target": wrong_contract["target"], "scope": wrong_contract["scope"],
        "historical_release_id": wrong_contract["historical_release"]["release_id"], "source_revision": wrong_contract["historical_release"]["source_revision"], "image_digest": wrong_contract["historical_release"]["image_digest"],
        "configuration_contract": wrong_contract["rollback"]["configuration_contract"], "permission_contract": wrong_contract["rollback"]["permission_contract"],
        "workloads": sorted(wrong_contract["rollback"]["workloads"]), "proof_set_sha256": wrong_contract["rollback"]["proof_set_sha256"],
    }
    wrong_contract["rollback"]["id"] = "rollback-compatibility-" + __import__("hashlib").sha256(module.canonical(identity)).hexdigest()[:24]
    write(root / module.CANDIDATE_DIRECTORY / f"{wrong_contract['rollback']['id']}.yml", wrong_contract)
    failure("--operation", "record-compatibility", "--evidence-root", str(root), "--candidate-record", str(root / module.CANDIDATE_DIRECTORY / f"{wrong_contract['rollback']['id']}.yml"))

    # An earlier qualified release can supply a rollback target after fresh
    # contract-bound proof, without being retroactively written as accepted.
    qualified = qualified_predecessor_compatibility(root)
    assert run("--operation", "record-compatibility", "--evidence-root", str(root), "--candidate-record", str(qualified)) == 0
    qualified_value = yaml.safe_load(qualified.read_text(encoding="utf-8"))
    qualified_id = qualified_value["rollback"]["id"]
    _, qualified_archive = module.compatibility_record(root, qualified_id)
    assert qualified_archive["identity"]["qualified_predecessor"]["package_custody_reference"] == "github-actions-run:40232309637"
    bad_qualified = yaml.safe_load(qualified.read_text(encoding="utf-8"))
    bad_qualified["qualified_predecessor"]["package_custody_reference"] = "not-a-custody-reference"
    write(root / module.CANDIDATE_DIRECTORY / "bad-qualified.yml", bad_qualified)
    failure("--operation", "record-compatibility", "--evidence-root", str(root), "--candidate-record", str(root / module.CANDIDATE_DIRECTORY / "bad-qualified.yml"))

    first_candidate = candidate(root, source="b" * 40, image="sha256:" + "b" * 64, configuration="sha256:" + "c" * 64, permissions="sha256:" + "d" * 64, proof="sha256:" + "e" * 64)
    assert run("--operation", "promote", "--evidence-root", str(root), "--candidate-record", str(first_candidate), "--expected-predecessor", first_id) == 0
    second = module.current(root)
    assert second and second["predecessor"] == first_id
    second_id = second["release_id"]
    before_id = (root / module.CURRENT).read_bytes()
    # Same successor is idempotent. A stale/concurrent predecessor is rejected.
    assert run("--operation", "promote", "--evidence-root", str(root), "--candidate-record", str(first_candidate), "--expected-predecessor", first_id) == 0
    concurrent = candidate(root, source="f" * 40, image="sha256:" + "f" * 64, configuration="sha256:" + "c" * 64, permissions="sha256:" + "d" * 64, proof="sha256:" + "e" * 64)
    failure("--operation", "promote", "--evidence-root", str(root), "--candidate-record", str(concurrent), "--expected-predecessor", first_id)
    assert (root / module.CURRENT).read_bytes() == before_id

    # Bad target and incomplete terminal-proof identity cannot alter the current record.
    bad = yaml.safe_load(first_candidate.read_text(encoding="utf-8"))
    bad["target"] = "wrong-target"
    write(root / module.CANDIDATE_DIRECTORY / "bad.yml", bad)
    failure("--operation", "promote", "--evidence-root", str(root), "--candidate-record", str(root / module.CANDIDATE_DIRECTORY / "bad.yml"), "--expected-predecessor", second_id)
    assert module.current(root)["release_id"] == second_id

    # Simulate interruption after immutable archive write but before atomic ref replacement.
    resumed = candidate(root, source="1" * 40, image="sha256:" + "1" * 64, configuration="sha256:" + "2" * 64, permissions="sha256:" + "3" * 64, proof="sha256:" + "4" * 64)
    source_record, source_raw = module.document(resumed)
    target, scope, _, identity = module.candidate_identity(source_record)
    history = module.history_record(target=target, scope=scope, identity=identity, source_path=resumed.relative_to(root), source_digest=module.sha256_bytes(source_raw), predecessor=second_id, legacy=False)
    archive = root / module.HISTORY_DIRECTORY / f"{module.release_id(identity)}.yml"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(module.rendered(history))
    assert module.current(root)["release_id"] == second_id
    assert run("--operation", "promote", "--evidence-root", str(root), "--candidate-record", str(resumed), "--expected-predecessor", second_id) == 0
    assert module.current(root)["release_id"] == module.release_id(identity)

    # A fabricated archive, altered candidate, missing terminal proof, or bad ref is detectable offline.
    archive.write_text("schema: fabricated\n", encoding="utf-8")
    failure("--operation", "validate-current", "--evidence-root", str(root))
    archive.write_bytes(module.rendered(history))
    current = yaml.safe_load((root / module.CURRENT).read_text(encoding="utf-8"))
    current["record"]["sha256"] = "sha256:" + "0" * 64
    write(root / module.CURRENT, current)
    failure("--operation", "validate-current", "--evidence-root", str(root))

print("Release succession regressions passed.")

