#!/usr/bin/env python3
"""Regression coverage for immutable release succession."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.release-succession.regression
#   version: 4
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-11-09"
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
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

if not __debug__:
    raise SystemExit("Release succession fixtures require enabled assertions.")

SCRIPT = Path(__file__).with_name("script.py")
spec = importlib.util.spec_from_file_location("release_succession", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def run(*arguments: str) -> int:
    result = subprocess.run(["bash", str(SCRIPT.with_name("script.sh")), *arguments, "--rehearsal-root", str(module.REPOSITORY_ROOT), "--json"], cwd=SCRIPT.parents[5], text=True, capture_output=True)
    try: value = json.loads(result.stdout)
    except ValueError: raise AssertionError((result.returncode, result.stdout, result.stderr)) from None
    expected_schema = "deploy/command-arguments-report/v1" if "--validate-arguments" in arguments and result.returncode == 0 else "deploy/release-succession-report/v1"
    assert value.get("schema") == expected_schema, value
    print(json.dumps(value, sort_keys=True))
    return result.returncode


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def candidate(root: Path, *, source: str, image: str, configuration: str, permissions: str, proof: str, accepted: str = "2026-10-25T10:00:00Z") -> Path:
    receipt = root / "proof-receipts" / f"{source[:8]}.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({"receipt": source}), encoding="utf-8")
    proof_set = {"complete-proof": {"path": str(receipt.relative_to(root)), "sha256": module.sha256_bytes(receipt.read_bytes())}}
    config_path = module.REPOSITORY_ROOT / "contracts/configuration.yml"
    permission_path = module.REPOSITORY_ROOT / "contracts/permissions.yml"
    write(config_path, {"configuration": configuration})
    write(permission_path, {"permissions": permissions})
    contract = {"path": "contracts/configuration.yml", "sha256": module.sha256_bytes(config_path.read_bytes())}
    permission = {"path": "contracts/permissions.yml", "sha256": module.sha256_bytes(permission_path.read_bytes())}
    identity = {
        "target": "example-target",
        "scope": "example-scope",
        "source_revision": source,
        "image_digest": image,
        "configuration_contract": contract,
        "permission_contract": permission,
        "proof_set_sha256": module.sha256_bytes(module.canonical(proof_set)),
    }
    value = {
        "schema": module.CANDIDATE_SCHEMA,
        "evidence_class": "simulated",
        "target": identity["target"],
        "scope": identity["scope"],
        "status": "verified",
        "release": {"id": module.release_id(identity), **{key: identity[key] for key in ("source_revision", "image_digest", "configuration_contract", "permission_contract", "proof_set_sha256")}},
        "proof": {"accepted_at": accepted, "receipt_count": len(proof_set)},
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
    contract_path = module.REPOSITORY_ROOT / "contracts/configuration.yml"
    contract = {"path": "contracts/configuration.yml", "sha256": module.sha256_bytes(contract_path.read_bytes())}
    identity = {
        "target": retained["target"], "scope": retained["scope"],
        "historical_release_id": retained["release_id"], "source_revision": retained["source_revision"], "image_digest": retained["image_digest"],
        "configuration_contract": contract, "permission_contract": contract,
        "workloads": ["core-server-service", "persistence-restoration-verifier-task", "private-release-verifier-task"],
        "proof_set_sha256": module.sha256_bytes(module.canonical(proof_set)),
    }
    identifier = "rollback-compatibility-" + __import__("hashlib").sha256(module.canonical(identity)).hexdigest()[:24]
    value = {
        "schema": module.COMPATIBILITY_SCHEMA, "evidence_class": "simulated", "target": identity["target"], "scope": identity["scope"], "status": "verified",
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
    contract_path = module.REPOSITORY_ROOT / "contracts/configuration.yml"
    contract = {"path": "contracts/configuration.yml", "sha256": module.sha256_bytes(contract_path.read_bytes())}
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
        "schema": module.COMPATIBILITY_SCHEMA, "evidence_class": "simulated", "target": identity["target"], "scope": identity["scope"], "status": "verified",
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
    module.REPOSITORY_ROOT = Path(temporary)
    module.EVIDENCE_CLASS = "simulated"
    write(module.REPOSITORY_ROOT / "contracts/configuration.yml", {"configuration": "initial"})
    root = Path(temporary) / "30-release-evidence"
    legacy = root / "accepted-release.yml"
    legacy_value = {
        "schema": module.LEGACY_SCHEMA,
        "target": "example-target",
        "scope": "example-scope",
        "status": "rehearsed",
        "evidence_class": "simulated",
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
    # Later contract revisions do not rewrite archival truth.  The ordinary
    # selector rejects the stale binding, while an archive reader can still
    # validate its immutable receipt and identity before skipping it.
    current_contract_path = module.REPOSITORY_ROOT / "contracts/configuration.yml"
    current_contract_path.write_text("configuration: later\n", encoding="utf-8")
    try:
        module.compatibility_record(root, identifier)
        raise AssertionError("stale compatibility binding selected")
    except module.SuccessionFailure as error:
        assert str(error) == "release-succession-compatibility-contract-mismatch"
    assert module.compatibility_record(root, identifier, current_contracts=False)[1]["identity"]["image_digest"] == retained["image_digest"]
    current_contract_path.write_text("configuration: initial\n", encoding="utf-8")
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
    # Candidate validation is independently available to the acceptance route;
    # it cannot advance the current reference or accept a malformed candidate.
    current_before_validation = (root / module.CURRENT).read_bytes()
    assert run("--operation", "validate-candidate", "--evidence-root", str(root), "--candidate-record", str(first_candidate), "--validate-arguments") == 0
    failure("--operation", "validate-candidate", "--evidence-root", str(root), "--validate-arguments")
    failure("--operation", "validate-candidate", "--evidence-root", str(root), "--candidate-record", str(first_candidate), "--legacy-record", str(legacy), "--validate-arguments")
    failure("--operation", "validate-candidate", "--evidence-root", str(root), "--candidate-record", str(first_candidate), "--expected-predecessor", "none", "--validate-arguments")
    assert run("--operation", "validate-candidate", "--evidence-root", str(root), "--candidate-record", str(first_candidate)) == 0
    assert (root / module.CURRENT).read_bytes() == current_before_validation
    invalid_candidate = yaml.safe_load(first_candidate.read_text(encoding="utf-8"))
    invalid_candidate["proof_set"]["complete-proof"]["sha256"] = "sha256:" + "0" * 64
    write(root / module.CANDIDATE_DIRECTORY / "invalid-candidate.yml", invalid_candidate)
    failure("--operation", "validate-candidate", "--evidence-root", str(root), "--candidate-record", str(root / module.CANDIDATE_DIRECTORY / "invalid-candidate.yml"))
    wrong_count = yaml.safe_load(first_candidate.read_text(encoding="utf-8"))
    wrong_count["proof"]["receipt_count"] = 2
    write(root / module.CANDIDATE_DIRECTORY / "wrong-proof-count.yml", wrong_count)
    failure("--operation", "validate-candidate", "--evidence-root", str(root), "--candidate-record", str(root / module.CANDIDATE_DIRECTORY / "wrong-proof-count.yml"))
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

    # Changed current configuration invalidates a new promotion, never retained
    # historical custody. Proof bytes remain mandatory after contract changes.
    contract_path = module.REPOSITORY_ROOT / "contracts/configuration.yml"
    contract_path.write_text("configuration: changed-after-acceptance\n")
    assert run("--operation", "validate-current", "--evidence-root", str(root)) == 0
    failure("--operation", "promote", "--evidence-root", str(root), "--candidate-record", str(resumed), "--expected-predecessor", second_id)
    receipt_path = root / yaml.safe_load(resumed.read_text())["proof_set"]["complete-proof"]["path"]
    receipt_bytes = receipt_path.read_bytes(); receipt_path.write_text("changed historical proof")
    failure("--operation", "validate-current", "--evidence-root", str(root))
    receipt_path.write_bytes(receipt_bytes)
    assert run("--operation", "validate-current", "--evidence-root", str(root)) == 0

    # Production CLI cannot accept explicit simulated evidence.
    production = subprocess.run(["bash", str(SCRIPT.with_name("script.sh")), "--operation", "validate-current", "--evidence-root", str(root), "--json"], cwd=SCRIPT.parents[5], text=True, capture_output=True)
    assert production.returncode == 1 and "release-succession-evidence-class-invalid" in production.stdout

    # A fabricated archive, altered candidate, missing terminal proof, or bad ref is detectable offline.
    archive.write_text("schema: fabricated\n", encoding="utf-8")
    failure("--operation", "validate-current", "--evidence-root", str(root))
    archive.write_bytes(module.rendered(history))
    current = yaml.safe_load((root / module.CURRENT).read_text(encoding="utf-8"))
    current["record"]["sha256"] = "sha256:" + "0" * 64
    write(root / module.CURRENT, current)
    failure("--operation", "validate-current", "--evidence-root", str(root))

with tempfile.TemporaryDirectory(prefix="initial-recovery-policy-") as temporary:
    module.REPOSITORY_ROOT = Path(temporary)
    module.EVIDENCE_CLASS = "simulated"
    scopes = Path(temporary) / "example-target/20-scopes"
    scope_root = scopes / "example-scope"
    root = scope_root / "30-release-evidence"
    root.mkdir(parents=True)
    contract_path = scope_root / "00-declaration/declaration-contract.yml"
    policy = {
        "applicability": "no-current-or-historical-accepted-release",
        "strategy": "stop-own-scope-workloads-preserve-data",
        "provider_mutation": "explicit-approved-bounded-control-only",
        "automatic_replay": "prohibited", "database_reversal": "prohibited",
        "verification": "owned-workloads-stopped-and-data-preserved",
        "proof_requirement": "required-before-first-scope-acceptance",
        "subsequent_releases": "prior-compatible-accepted-image-required",
    }
    declaration = {"schema": "deploy/target-scope-contract/v1", "target": "example-target", "scope": "example-scope",
        "health_recovery": {"declaration_schema": "deploy/health-failure-and-recovery-declaration/v2", "initial_release_recovery": policy}}
    entry = {"id": "example-scope", "lifecycle": "candidate", "declaration": "example-scope/00-declaration/declaration-contract.yml",
        "workload_binding": "example-scope/10-workload-binding/workload-binding.yml", "workload_ownership": ["feature-service"]}
    inventory = {"schema": "deploy/scope-lifecycle-inventory/v1", "target": "example-target", "scopes": [entry]}
    write(contract_path, declaration); write(scopes / "scope-index.yml", inventory)

    def select(expected: str | None = None, *, extra: tuple[str, ...] = (), evidence: Path = root) -> dict:
        def snapshot() -> dict:
            return {str(path.relative_to(Path(temporary))): ("symlink" if path.is_symlink() else "directory" if path.is_dir() else path.read_bytes()) for path in Path(temporary).rglob("*")}
        before = snapshot()
        result = subprocess.run(["bash", str(SCRIPT.with_name("script.sh")), "--operation", "select-recovery", "--evidence-root", str(evidence),
            "--scope-contract", str(contract_path), "--rehearsal-root", temporary, "--json", *extra], cwd=SCRIPT.parents[5], capture_output=True, text=True)
        value = json.loads(result.stdout)
        assert "PRIVATE-POLICY-CANARY" not in result.stdout + result.stderr
        after = snapshot()
        assert before == after, "recovery selection must not create a lock, directory, receipt or accepted reference"
        if expected is None:
            assert result.returncode == 0 and value["verdict"] == "valid", value
        else:
            assert result.returncode == 1 and value["findings"] == [{"code": expected}], value
        return value

    assert select()["facts"]["policy"] == "stop-own-scope-workloads-preserve-data"
    assert select()["facts"]["accepted_release_id"] == "none"
    assert select(extra=("--validate-arguments",))["schema"] == "deploy/command-arguments-report/v1"
    failure("--operation", "select-recovery", "--evidence-root", str(root), "--validate-arguments")
    for field in policy:
        invalid = copy.deepcopy(declaration)
        invalid["health_recovery"]["initial_release_recovery"][field] = "PRIVATE-POLICY-CANARY"
        write(contract_path, invalid); select("initial-release-recovery-invalid")
    write(contract_path, {**declaration, "health_recovery": {"declaration_schema": "deploy/health-failure-and-recovery-declaration/v2"}})
    select("initial-release-recovery-not-declared")
    write(contract_path, declaration)
    for amendment in [{"lifecycle": "active"}, {"predecessor": "old-scope"}, {"successor": "next-scope"}, {"declaration": "other/00-declaration/declaration-contract.yml"}]:
        write(scopes / "scope-index.yml", {**inventory, "scopes": [{**entry, **amendment}]})
        select("initial-release-recovery-lifecycle-invalid")
    write(scopes / "scope-index.yml", {**inventory, "scopes": [entry, {"id": "baseline", "workload_ownership": ["feature-service"]}]})
    select("initial-release-recovery-lifecycle-invalid")
    write(scopes / "scope-index.yml", inventory)
    root.rmdir()
    select("release-recovery-evidence-unavailable", evidence=root)
    assert not root.exists(), "a failed observation cannot create the missing evidence store"
    root.mkdir()
    select("release-recovery-evidence-root-invalid", evidence=Path(temporary))
    select("release-succession-arguments-invalid", extra=("--expected-predecessor", "none"))
    legacy_path = root / "accepted-release.yml"
    write(legacy_path, {"unimported": "PRIVATE-POLICY-CANARY"})
    select("release-recovery-accepted-history-without-current")
    legacy_path.unlink()
    history = root / module.HISTORY_DIRECTORY
    write(history / "orphan.yml", {"unobserved": "PRIVATE-POLICY-CANARY"})
    select("release-recovery-accepted-history-without-current")
    (history / "orphan.yml").unlink(); history.rmdir()
    (root / module.CURRENT).symlink_to(root / "missing.yml")
    select("release-recovery-context-unsafe")
    (root / module.CURRENT).unlink()
    (root / module.CURRENT).mkdir()
    select("release-succession-record-unreadable")
    (root / module.CURRENT).rmdir()
    write(root / module.CURRENT, {"schema": "PRIVATE-POLICY-CANARY"})
    select("release-succession-current-invalid")
    (root / module.CURRENT).unlink()
    # Actual simulated promotion makes the same declaration select the normal
    # rollback policy. It is not possible to keep opting into first-release mode.
    first_candidate = candidate(root, source="6" * 40, image="sha256:" + "6" * 64, configuration="initial", permissions="initial", proof="fixture")
    (root / module.CURRENT).symlink_to(root / "missing.yml")
    failure("--operation", "promote", "--evidence-root", str(root), "--candidate-record", str(first_candidate), "--expected-predecessor", "none")
    assert not (root / "missing.yml").exists()
    (root / module.CURRENT).unlink()
    # An interrupted *same* first promotion can finish its already-written
    # immutable archive. This is different from resetting some other history.
    record, raw = module.document(first_candidate)
    target, scope, _, identity = module.candidate_identity(record, root)
    pending_archive = root / module.HISTORY_DIRECTORY / f"{module.release_id(identity)}.yml"
    write(pending_archive, module.history_record(target=target, scope=scope, identity=identity, source_path=first_candidate.relative_to(root), source_digest=module.sha256_bytes(raw), predecessor=None, legacy=False))
    select("release-recovery-accepted-history-without-current")
    assert run("--operation", "promote", "--evidence-root", str(root), "--candidate-record", str(first_candidate), "--expected-predecessor", "none") == 0
    selected = select()["facts"]
    assert selected["policy"] == "restore-prior-accepted-immutable-release" and selected["accepted_release_id"] == module.current(root)["release_id"]
    assert selected["compatibility"] == "not-assessed", "history validation is not rollback compatibility proof"
    # A missing current ref with retained accepted history must be reconciled,
    # never reinterpreted as an initial scope.
    (root / module.CURRENT).unlink()
    select("release-recovery-accepted-history-without-current")
    before = {path.name: path.read_bytes() for path in history.iterdir()}
    reset = candidate(root, source="7" * 40, image="sha256:" + "7" * 64, configuration="next", permissions="next", proof="fixture")
    failure("--operation", "promote", "--evidence-root", str(root), "--candidate-record", str(reset), "--expected-predecessor", "none")
    assert before == {path.name: path.read_bytes() for path in history.iterdir()} and not (root / module.CURRENT).exists()

# Rehearsal trees must be disjoint from an implementation checkout even when
# that checkout itself lives below the temporary directory.
with tempfile.TemporaryDirectory(prefix="succession-implementation-") as directory:
    ancestor = Path(directory)
    implementation = ancestor / "repository"
    copied = implementation / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py"
    copied.parent.mkdir(parents=True)
    copied.write_bytes(SCRIPT.read_bytes())
    evidence = implementation / "30-release-evidence"
    legacy = evidence / "accepted-release.yml"
    write(legacy, {"schema": module.LEGACY_SCHEMA, "target": "example-target", "scope": "example-scope", "status": "rehearsed", "evidence_class": "simulated", "release": {"source_revision": "a" * 40, "image_digest": "sha256:" + "a" * 64}, "acceptance": {"rollback_release": {"source_revision": "0" * 40, "image_digest": "sha256:" + "0" * 64}}})
    original = legacy.read_bytes()
    for rehearsal in [ancestor, implementation, evidence]:
        result = subprocess.run([sys.executable, "-B", str(copied), "--operation", "initialize-legacy", "--evidence-root", str(evidence), "--legacy-record", str(legacy), "--expected-predecessor", "none", "--rehearsal-root", str(rehearsal), "--json"], capture_output=True, text=True, timeout=10)
        report = json.loads(result.stdout)
        assert result.returncode == 1 and report["findings"] == [{"code": "release-succession-rehearsal-root-invalid"}], report
        assert legacy.read_bytes() == original
        assert sorted(path.name for path in evidence.iterdir()) == ["accepted-release.yml"]

# The ephemeral own lock must not dirty source custody; ignoring the entire
# evidence directory would instead hide the records that custody must retain.
with tempfile.TemporaryDirectory(prefix="succession-ignore-") as directory:
    repository = Path(directory)
    original_ignore = (SCRIPT.parents[5] / ".gitignore").read_text()
    scope = "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/30-release-evidence/"
    lock = scope + ".release-succession.lock"
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null")
    def git(*arguments):
        return subprocess.run(["git", "-c", "core.excludesFile=/dev/null", "-C", str(repository), *arguments],
                              env=environment, capture_output=True, text=True, timeout=10)
    assert git("init", "--quiet").returncode == 0
    ignore = repository / ".gitignore"
    ignore.write_text(original_ignore)
    assert git("check-ignore", "--no-index", "--", lock).returncode == 0
    visible = [scope + item for item in ("current-accepted-release.yml", "accepted-release.yml", "release-candidates/release-example.yml",
        "accepted-releases/release-example.yml", "proof-receipts/entity-smoke-example.json", ".release-succession.lock.extra")]
    visible += [lock.replace("/entity-smoke/", "/" + name + "/") for name in ("bootstrap-runtime", "core-server-persistence", "entity-smoke-other")]
    for path in visible:
        observed = git("check-ignore", "--no-index", "--", path)
        assert observed.returncode == 1 and observed.stdout == "", "release evidence or unrelated locks must stay visible"
    # Removing just the owned entry reproduces the dirty-lock outcome; the
    # positive assertion above would reject that plausible broken declaration.
    lines = original_ignore.splitlines()
    assert lines.count(lock) == 1
    ignore.write_text("\n".join(line for line in lines if line != lock) + "\n")
    assert git("check-ignore", "--no-index", "--", lock).returncode == 1
    catalog = yaml.safe_load((SCRIPT.parents[5] / "scripts/repo/check-selection/checks.yml").read_text())
    unit = catalog["checks"]["release-succession-regression"]
    assert {".gitignore", "scripts/repo/check-selection/checks.yml"} <= set(unit["inputs"]) and "git" in unit["runtime"]["tools"], "actual consumed ignore rule, catalog and Git runtime must invalidate trusted proof"
    assert any(".gitignore" in rule["inputs"] and "release-succession-regression" in rule["checks"]
               for rule in catalog["repository_inputs"]), "input fingerprint binding alone cannot supply impact selection coverage"

print("Release succession regressions passed.")

