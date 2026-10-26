#!/usr/bin/env python3
"""Promote verified release evidence without overwriting accepted history."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.release-succession.implementation
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Atomically advance a target-scope current accepted-release reference only after preserving immutable release history and validating a qualified successor.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [writes-files]
#   used_by:
#   - id: deploy.command.release-succession
#     path: scripts/04.deploy/lifecycle/60-run/release-succession/script.sh
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

CURRENT_SCHEMA = "deploy/release-current-ref/v1"
HISTORY_SCHEMA = "deploy/accepted-release-history/v1"
CANDIDATE_SCHEMA = "deploy/release-candidate/v1"
COMPATIBILITY_SCHEMA = "deploy/release-rollback-compatibility/v1"
LEGACY_SCHEMA = "deploy/persistence-accepted-release/v1"
CURRENT = "current-accepted-release.yml"
HISTORY_DIRECTORY = "accepted-releases"
CANDIDATE_DIRECTORY = "release-candidates"
COMPATIBILITY_DIRECTORY = "rollback-compatibility"
REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
EVIDENCE_CLASS = "live"


class SuccessionFailure(ValueError):
    pass


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise SuccessionFailure("release-succession-string-invalid")
    return value


def iso_time(value: object) -> str:
    result = text(value)
    try:
        parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))
    except ValueError as error:
        raise SuccessionFailure("release-succession-timestamp-invalid") from error
    if parsed.tzinfo is None:
        raise SuccessionFailure("release-succession-timestamp-invalid")
    return result


def sha(value: object) -> str:
    result = text(value)
    if not result.startswith("sha256:") or len(result) != 71 or any(character not in "0123456789abcdef" for character in result[7:]):
        raise SuccessionFailure("release-succession-sha256-invalid")
    return result


def document(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = yaml.safe_load(raw.decode("utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise SuccessionFailure("release-succession-record-unreadable") from error
    if not isinstance(value, dict):
        raise SuccessionFailure("release-succession-record-invalid")
    return value, raw


def child(root: Path, name: str) -> Path:
    result = (root / name).resolve()
    if result.parent != root.resolve():
        raise SuccessionFailure("release-succession-path-invalid")
    return result


def under(root: Path, path: Path, directory: str) -> Path:
    root = root.resolve()
    result = path.resolve()
    base = (root / directory).resolve()
    if base not in result.parents:
        raise SuccessionFailure("release-succession-path-invalid")
    return result


def repository_file(path: str) -> Path:
    relative = Path(path)
    if relative.is_absolute():
        raise SuccessionFailure("release-succession-candidate-contract-invalid")
    result = (REPOSITORY_ROOT / relative).resolve()
    if REPOSITORY_ROOT.resolve() not in result.parents:
        raise SuccessionFailure("release-succession-candidate-contract-invalid")
    return result


def release_id(identity: dict[str, Any]) -> str:
    return "release-" + hashlib.sha256(canonical(identity)).hexdigest()[:24]


def proof_set(record: dict[str, Any], root: Path | None = None) -> dict[str, dict[str, str]]:
    value = record.get("proof_set")
    if not isinstance(value, dict) or not value:
        raise SuccessionFailure("release-succession-candidate-proof-set-invalid")
    result: dict[str, dict[str, str]] = {}
    for name, item in value.items():
        if not isinstance(name, str) or not name or not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise SuccessionFailure("release-succession-candidate-proof-set-invalid")
        path = Path(text(item.get("path")))
        if path.is_absolute():
            raise SuccessionFailure("release-succession-candidate-proof-set-invalid")
        result[name] = {"path": str(path), "sha256": sha(item.get("sha256"))}
        if root is not None:
            receipt = under(root, root / path, "proof-receipts")
            try:
                raw = receipt.read_bytes()
            except OSError as error:
                raise SuccessionFailure("release-succession-proof-receipt-unreadable") from error
            if sha256_bytes(raw) != result[name]["sha256"]:
                raise SuccessionFailure("release-succession-proof-receipt-mismatch")
    return result


def candidate_identity(record: dict[str, Any], root: Path | None = None, *, current_contracts: bool = True) -> tuple[str, str, str, dict[str, Any]]:
    if record.get("evidence_class", "live") != EVIDENCE_CLASS:
        raise SuccessionFailure("release-succession-evidence-class-invalid")
    if record.get("schema") != CANDIDATE_SCHEMA or record.get("status") != "verified":
        raise SuccessionFailure("release-succession-candidate-schema-invalid")
    target, scope = text(record.get("target")), text(record.get("scope"))
    release = record.get("release")
    if not isinstance(release, dict) or set(release) != {"id", "source_revision", "image_digest", "configuration_contract", "permission_contract", "proof_set_sha256"}:
        raise SuccessionFailure("release-succession-candidate-release-invalid")
    contracts: dict[str, dict[str, str]] = {}
    for key in ("configuration_contract", "permission_contract"):
        contract = release.get(key)
        if not isinstance(contract, dict) or set(contract) != {"path", "sha256"}:
            raise SuccessionFailure("release-succession-candidate-contract-invalid")
        contracts[key] = {"path": text(contract.get("path")), "sha256": sha(contract.get("sha256"))}
    if root is not None and current_contracts:
        for contract in contracts.values():
            path = repository_file(contract["path"])
            try:
                raw = path.read_bytes()
            except OSError as error:
                raise SuccessionFailure("release-succession-candidate-contract-unreadable") from error
            if sha256_bytes(raw) != contract["sha256"]:
                raise SuccessionFailure("release-succession-candidate-contract-mismatch")
    identity = {
        "target": target,
        "scope": scope,
        "source_revision": text(release.get("source_revision")),
        "image_digest": sha(release.get("image_digest")),
        "configuration_contract": contracts["configuration_contract"],
        "permission_contract": contracts["permission_contract"],
        "proof_set_sha256": sha(release.get("proof_set_sha256")),
    }
    if text(release.get("id")) != release_id(identity):
        raise SuccessionFailure("release-succession-candidate-identity-invalid")
    proof = record.get("proof")
    if not isinstance(proof, dict) or set(proof) != {"accepted_at", "receipt_count"} or type(proof.get("receipt_count")) is not int or proof["receipt_count"] < 1:
        raise SuccessionFailure("release-succession-candidate-proof-invalid")
    iso_time(proof.get("accepted_at"))
    proofs = proof_set(record, root)
    if proof["receipt_count"] != len(proofs):
        raise SuccessionFailure("release-succession-candidate-proof-count-mismatch")
    if identity["proof_set_sha256"] != sha256_bytes(canonical(proofs)):
        raise SuccessionFailure("release-succession-candidate-proof-set-mismatch")
    return target, scope, identity["image_digest"], identity


def legacy_identity(record: dict[str, Any], raw: bytes) -> tuple[str, str, str, dict[str, Any]]:
    if record.get("evidence_class", "live") != EVIDENCE_CLASS:
        raise SuccessionFailure("release-succession-evidence-class-invalid")
    if record.get("schema") != LEGACY_SCHEMA or record.get("status") != ("rehearsed" if EVIDENCE_CLASS == "simulated" else "accepted"):
        raise SuccessionFailure("release-succession-legacy-schema-invalid")
    target, scope = text(record.get("target")), text(record.get("scope"))
    release = record.get("release")
    if not isinstance(release, dict):
        raise SuccessionFailure("release-succession-legacy-release-invalid")
    identity = {
        "target": target,
        "scope": scope,
        "source_revision": text(release.get("source_revision")),
        "image_digest": sha(release.get("image_digest")),
        "legacy_record_sha256": sha256_bytes(raw),
    }
    return target, scope, identity["image_digest"], identity


def retained_rollback_identity(root: Path) -> dict[str, Any]:
    """Read, but never amend, the earlier release retained by a legacy record."""
    record, raw = document(root / "accepted-release.yml")
    target, scope, _, _ = legacy_identity(record, raw)
    acceptance = record.get("acceptance")
    rollback = acceptance.get("rollback_release") if isinstance(acceptance, dict) else None
    if not isinstance(rollback, dict):
        raise SuccessionFailure("release-succession-retained-rollback-unavailable")
    identity = {
        "target": target, "scope": scope,
        "source_revision": text(rollback.get("source_revision")),
        "image_digest": sha(rollback.get("image_digest")),
        "legacy_record_sha256": sha256_bytes(raw),
    }
    identity["release_id"] = "retained-rollback-" + hashlib.sha256(canonical(identity)).hexdigest()[:24]
    return identity


def compatibility_identity(record: dict[str, Any], root: Path | None = None) -> tuple[str, str, str, dict[str, Any]]:
    """Validate a fresh, additive compatibility proof for a rollback release.

    This record does not promote or amend any previous acceptance.  It names
    either a historical accepted image or an earlier qualified image that a
    controlled rollback may select only after the corrected configuration and
    permission surfaces have been proved.
    """
    if record.get("evidence_class", "live") != EVIDENCE_CLASS:
        raise SuccessionFailure("release-succession-evidence-class-invalid")
    if record.get("schema") != COMPATIBILITY_SCHEMA or record.get("status") != "verified":
        raise SuccessionFailure("release-succession-compatibility-schema-invalid")
    target, scope = text(record.get("target")), text(record.get("scope"))
    historical = record.get("historical_release")
    qualified = record.get("qualified_predecessor")
    rollback = record.get("rollback")
    proof = record.get("proof")
    if (historical is None) == (qualified is None):
        raise SuccessionFailure("release-succession-compatibility-predecessor-invalid")
    if historical is not None and (not isinstance(historical, dict) or set(historical) != {"release_id", "source_revision", "image_digest"}):
        raise SuccessionFailure("release-succession-compatibility-historical-release-invalid")
    if qualified is not None and (not isinstance(qualified, dict) or set(qualified) != {"source_revision", "image_digest", "package_custody_reference"}):
        raise SuccessionFailure("release-succession-compatibility-qualified-predecessor-invalid")
    if not isinstance(rollback, dict) or set(rollback) != {"id", "configuration_contract", "permission_contract", "workloads", "proof_set_sha256"}:
        raise SuccessionFailure("release-succession-compatibility-rollback-invalid")
    if not isinstance(proof, dict) or set(proof) != {"qualified_at", "receipt_count"} or type(proof.get("receipt_count")) is not int or proof["receipt_count"] < 1:
        raise SuccessionFailure("release-succession-compatibility-proof-invalid")
    iso_time(proof.get("qualified_at"))
    contracts: dict[str, dict[str, str]] = {}
    for key in ("configuration_contract", "permission_contract"):
        contract = rollback.get(key)
        if not isinstance(contract, dict) or set(contract) != {"path", "sha256"}:
            raise SuccessionFailure("release-succession-compatibility-contract-invalid")
        contracts[key] = {"path": text(contract.get("path")), "sha256": sha(contract.get("sha256"))}
    workloads = rollback.get("workloads")
    if not isinstance(workloads, list) or not workloads or any(not isinstance(value, str) or not value for value in workloads) or len(set(workloads)) != len(workloads):
        raise SuccessionFailure("release-succession-compatibility-workloads-invalid")
    proofs = proof_set(record, root)
    if proof["receipt_count"] != len(proofs):
        raise SuccessionFailure("release-succession-compatibility-proof-count-mismatch")
    if root is not None:
        for contract in contracts.values():
            path = repository_file(contract["path"])
            try: raw = path.read_bytes()
            except OSError as error: raise SuccessionFailure("release-succession-compatibility-contract-unreadable") from error
            if sha256_bytes(raw) != contract["sha256"]:
                raise SuccessionFailure("release-succession-compatibility-contract-mismatch")
    if historical is not None:
        # Preserve the existing legacy compatibility identity exactly.  That
        # keeps previously generated, immutable compatibility records valid.
        identity_predecessor = {"historical_release_id": text(historical.get("release_id"))}
        source_revision = text(historical.get("source_revision"))
        image_digest = sha(historical.get("image_digest"))
    else:
        reference = text(qualified.get("package_custody_reference"))
        if not reference.startswith("github-actions-run:") or not reference.removeprefix("github-actions-run:").isdigit():
            raise SuccessionFailure("release-succession-compatibility-qualified-custody-invalid")
        source_revision = text(qualified.get("source_revision"))
        image_digest = sha(qualified.get("image_digest"))
        identity_predecessor = {
            "qualified_predecessor": {
                "source_revision": source_revision,
                "image_digest": image_digest,
                "package_custody_reference": reference,
            }
        }
    identity = {
        "target": target, "scope": scope,
        **identity_predecessor,
        "source_revision": source_revision,
        "image_digest": image_digest,
        "configuration_contract": contracts["configuration_contract"],
        "permission_contract": contracts["permission_contract"],
        "workloads": sorted(workloads),
        "proof_set_sha256": sha(rollback.get("proof_set_sha256")),
    }
    if text(rollback.get("id")) != "rollback-compatibility-" + hashlib.sha256(canonical(identity)).hexdigest()[:24]:
        raise SuccessionFailure("release-succession-compatibility-identity-invalid")
    if identity["proof_set_sha256"] != sha256_bytes(canonical(proofs)):
        raise SuccessionFailure("release-succession-compatibility-proof-set-mismatch")
    return target, scope, identity["image_digest"], identity


def compatibility_record(root: Path, identifier: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if not re.fullmatch(r"rollback-compatibility-[0-9a-f]{24}", identifier):
        raise SuccessionFailure("release-succession-compatibility-reference-invalid")
    path = root / COMPATIBILITY_DIRECTORY / f"{identifier}.yml"
    record, raw = document(path)
    target, scope, _, identity = compatibility_identity(record, root)
    if identifier != record.get("rollback", {}).get("id"):
        raise SuccessionFailure("release-succession-compatibility-reference-mismatch")
    return record, {"target": target, "scope": scope, "identity": identity, "sha256": sha256_bytes(raw)}


def record_compatibility(root: Path, source: Path) -> tuple[str, str]:
    source = under(root, source, CANDIDATE_DIRECTORY)
    record, raw = document(source)
    target, scope, _, identity = compatibility_identity(record, root)
    qualified = identity.get("qualified_predecessor")
    if qualified is not None:
        # Qualification is established by the target-owned proof set.  The
        # generic controller verifies its immutable receipt hashes and the
        # corrected contract hashes above, but deliberately does not invent a
        # second acceptance history for this release.
        matches = True
    else:
        historical_id = identity["historical_release_id"]
        try:
            history, _ = history_record_for_id(root, historical_id)
            release = history.get("release")
            matches = isinstance(release, dict) and release.get("source_revision") == identity["source_revision"] and release.get("image_digest") == identity["image_digest"]
        except SuccessionFailure:
            retained = retained_rollback_identity(root)
            matches = historical_id == retained["release_id"] and retained["source_revision"] == identity["source_revision"] and retained["image_digest"] == identity["image_digest"]
    if not matches:
        raise SuccessionFailure("release-succession-compatibility-historical-release-mismatch")
    identifier = "rollback-compatibility-" + hashlib.sha256(canonical(identity)).hexdigest()[:24]
    if source.name != f"{identifier}.yml":
        raise SuccessionFailure("release-succession-compatibility-reference-mismatch")
    archived = root / COMPATIBILITY_DIRECTORY / f"{identifier}.yml"
    immutable_write(archived, raw)
    return identifier, sha256_bytes(raw)


def history_record_for_id(root: Path, identifier: str) -> tuple[dict[str, Any], bytes]:
    if not re.fullmatch(r"release-[0-9a-f]{24}", identifier):
        raise SuccessionFailure("release-succession-history-reference-invalid")
    value, raw = document(root / HISTORY_DIRECTORY / f"{identifier}.yml")
    history_identity(root, {"path": str(Path(HISTORY_DIRECTORY) / f"{identifier}.yml"), "sha256": sha256_bytes(raw)})
    return value, raw


def rendered(value: dict[str, Any]) -> bytes:
    return yaml.safe_dump(value, sort_keys=False).encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as output:
        temporary = Path(output.name)
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def immutable_write(path: Path, payload: bytes) -> None:
    """Publish a complete file once, including across concurrent producers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes() != payload:
                raise SuccessionFailure("release-succession-history-conflict")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def history_identity(root: Path, reference: dict[str, Any]) -> tuple[str, str, str, str | None]:
    """Validate an immutable record and the exact evidence it preserves."""
    path = under(root, root / reference["path"], HISTORY_DIRECTORY)
    record, raw = document(path)
    if sha256_bytes(raw) != reference["sha256"]:
        raise SuccessionFailure("release-succession-current-history-mismatch")
    required = {"schema", "target", "scope", "status", "release", "predecessor", "evidence"}
    if record.get("schema") != HISTORY_SCHEMA or set(record) != required or record.get("status") != "accepted":
        raise SuccessionFailure("release-succession-history-invalid")
    target, scope = text(record.get("target")), text(record.get("scope"))
    predecessor = record.get("predecessor")
    if predecessor is not None:
        text(predecessor)
    evidence = record.get("evidence")
    release = record.get("release")
    if not isinstance(evidence, dict) or set(evidence) != {"path", "sha256", "kind"} or not isinstance(release, dict):
        raise SuccessionFailure("release-succession-history-invalid")
    source_path = Path(text(evidence.get("path")))
    if source_path.is_absolute():
        raise SuccessionFailure("release-succession-history-invalid")
    source = under(root, root / source_path, ".")
    _, source_raw = document(source)
    if sha256_bytes(source_raw) != sha(evidence.get("sha256")):
        raise SuccessionFailure("release-succession-evidence-mismatch")
    kind = evidence.get("kind")
    if kind == "legacy-accepted-record":
        source_record, _ = document(source)
        _, _, _, identity = legacy_identity(source_record, source_raw)
        expected_contracts: dict[str, Any] = {"status": "legacy-not-recorded"}
        expected_proofs: str = "legacy-not-recorded"
    elif kind == "verified-release-candidate":
        under(root, source, CANDIDATE_DIRECTORY)
        source_record, _ = document(source)
        # Historical custody verifies retained bytes, not today's contracts.
        # A new promotion/rollback separately checks current contract identity.
        _, _, _, identity = candidate_identity(source_record, root, current_contracts=False)
        expected_contracts = {"configuration": identity["configuration_contract"], "permissions": identity["permission_contract"]}
        expected_proofs = identity["proof_set_sha256"]
    else:
        raise SuccessionFailure("release-succession-history-invalid")
    expected = {
        "id": release_id(identity),
        "source_revision": identity["source_revision"],
        "image_digest": identity["image_digest"],
        "contract_revisions": expected_contracts,
        "proof_set_sha256": expected_proofs,
    }
    if release != expected or target != identity["target"] or scope != identity["scope"]:
        raise SuccessionFailure("release-succession-history-identity-invalid")
    return target, scope, expected["id"], predecessor


def current(root: Path) -> dict[str, Any] | None:
    path = child(root, CURRENT)
    if not path.exists():
        return None
    value, _ = document(path)
    if value.get("schema") != CURRENT_SCHEMA or value.get("status") != "active":
        raise SuccessionFailure("release-succession-current-invalid")
    if set(value) != {"schema", "target", "scope", "status", "release_id", "record", "predecessor", "promoted_at"}:
        raise SuccessionFailure("release-succession-current-invalid")
    text(value.get("target")); text(value.get("scope")); text(value.get("release_id")); text(value.get("promoted_at"))
    record = value.get("record")
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        raise SuccessionFailure("release-succession-current-invalid")
    path_value, digest = text(record.get("path")), sha(record.get("sha256"))
    history = under(root, root / path_value, HISTORY_DIRECTORY)
    if not history.exists():
        raise SuccessionFailure("release-succession-current-history-mismatch")
    predecessor = value.get("predecessor")
    if predecessor is not None and not isinstance(predecessor, str):
        raise SuccessionFailure("release-succession-current-invalid")
    history_target, history_scope, history_release, history_predecessor = history_identity(root, {"path": path_value, "sha256": digest})
    if (history_target, history_scope, history_release, history_predecessor) != (value["target"], value["scope"], value["release_id"], predecessor):
        raise SuccessionFailure("release-succession-current-history-mismatch")
    seen = {value["release_id"]}
    while predecessor is not None:
        if predecessor in seen:
            raise SuccessionFailure("release-succession-history-cycle")
        seen.add(predecessor)
        historical, _ = history_record_for_id(root, predecessor)
        if historical.get("target") != value["target"] or historical.get("scope") != value["scope"] or historical.get("release", {}).get("id") != predecessor:
            raise SuccessionFailure("release-succession-history-identity-invalid")
        predecessor = historical.get("predecessor")
    return value


def history_record(*, target: str, scope: str, identity: dict[str, Any], source_path: Path, source_digest: str, predecessor: str | None, legacy: bool) -> dict[str, Any]:
    release = {
        "id": release_id(identity),
        "source_revision": identity["source_revision"],
        "image_digest": identity["image_digest"],
        "contract_revisions": ({"status": "legacy-not-recorded"} if legacy else {"configuration": identity["configuration_contract"], "permissions": identity["permission_contract"]}),
        "proof_set_sha256": ("legacy-not-recorded" if legacy else identity["proof_set_sha256"]),
    }
    return {
        "schema": HISTORY_SCHEMA,
        "target": target,
        "scope": scope,
        "status": "accepted",
        "release": release,
        "predecessor": predecessor,
        "evidence": {"path": str(source_path), "sha256": source_digest, "kind": "legacy-accepted-record" if legacy else "verified-release-candidate"},
    }


def promote(root: Path, *, target: str, scope: str, identity: dict[str, Any], source_path: Path, source_digest: str, expected_predecessor: str, legacy: bool) -> tuple[str, str]:
    if expected_predecessor == "":
        raise SuccessionFailure("release-succession-expected-predecessor-required")
    identifier = release_id(identity)
    state = current(root)
    if state is not None and state["release_id"] == identifier:
        expected = None if expected_predecessor == "none" else expected_predecessor
        if state["target"] != target or state["scope"] != scope or state["predecessor"] != expected:
            raise SuccessionFailure("release-succession-current-identity-conflict")
        return "already-current", identifier
    if state is None:
        if expected_predecessor != "none":
            raise SuccessionFailure("release-succession-predecessor-missing")
        predecessor: str | None = None
    else:
        if state["target"] != target or state["scope"] != scope:
            raise SuccessionFailure("release-succession-current-identity-conflict")
        if state["release_id"] != expected_predecessor:
            raise SuccessionFailure("release-succession-predecessor-mismatch")
        predecessor = expected_predecessor
    history = root / HISTORY_DIRECTORY / f"{identifier}.yml"
    record = history_record(target=target, scope=scope, identity=identity, source_path=source_path.relative_to(root), source_digest=source_digest, predecessor=predecessor, legacy=legacy)
    immutable_write(history, rendered(record))
    reference = {
        "schema": CURRENT_SCHEMA,
        "target": target,
        "scope": scope,
        "status": "active",
        "release_id": identifier,
        "record": {"path": str(history.relative_to(root)), "sha256": sha256_bytes(history.read_bytes())},
        "predecessor": predecessor,
        "promoted_at": timestamp(),
    }
    atomic_write(child(root, CURRENT), rendered(reference))
    return "initialized" if legacy else "promoted", identifier


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value: dict[str, Any] = {"schema": "deploy/release-succession-report/v1", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict in {"initialized", "promoted", "already-current", "recorded", "valid"} else 1


def main() -> int:
    global REPOSITORY_ROOT, EVIDENCE_CLASS
    parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)
    parser.add_argument("--operation", choices=("initialize-legacy", "promote", "record-compatibility", "validate-current"))
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--legacy-record", type=Path)
    parser.add_argument("--candidate-record", type=Path)
    parser.add_argument("--expected-predecessor")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    parser.add_argument("--rehearsal-root", type=Path)
    try:
        args, unknown = parser.parse_known_args()
    except argparse.ArgumentError:
        return report("blocked", "release-succession-arguments-invalid")
    if unknown or args.operation is None or args.evidence_root is None or (args.operation in {"initialize-legacy", "promote"} and not isinstance(args.expected_predecessor, str)):
        return report("blocked", "release-succession-arguments-invalid")
    if args.operation == "initialize-legacy" and (args.legacy_record is None or args.candidate_record is not None) or args.operation in {"promote", "record-compatibility"} and (args.candidate_record is None or args.legacy_record is not None) or args.operation == "validate-current" and (args.legacy_record is not None or args.candidate_record is not None or args.expected_predecessor is not None):
        return report("blocked", "release-succession-arguments-invalid")
    if args.validate_arguments:
        print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
    root = args.evidence_root.resolve()
    try:
        if args.rehearsal_root is not None:
            rehearsal = args.rehearsal_root.resolve()
            if not rehearsal.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not root.is_relative_to(rehearsal) or rehearsal.is_relative_to(REPOSITORY_ROOT.resolve()):
                raise SuccessionFailure("release-succession-rehearsal-root-invalid")
            REPOSITORY_ROOT, EVIDENCE_CLASS = rehearsal, "simulated"
        if args.operation == "validate-current":
            if args.legacy_record is not None or args.candidate_record is not None or args.expected_predecessor is not None:
                raise SuccessionFailure("release-succession-arguments-invalid")
            state = current(root)
            if state is None:
                raise SuccessionFailure("release-succession-current-missing")
            return report("valid", "release-succession-current-reference-valid", facts={"target": state["target"], "scope": state["scope"], "release_id": state["release_id"]})
        root.mkdir(parents=True, exist_ok=True)
        lock = root / ".release-succession.lock"
        with lock.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            if args.operation == "record-compatibility":
                if args.candidate_record is None or args.legacy_record is not None or args.expected_predecessor is not None:
                    raise SuccessionFailure("release-succession-arguments-invalid")
                identifier, digest = record_compatibility(root, args.candidate_record)
                return report("recorded", "release-succession-rollback-compatibility-recorded", facts={"rollback_compatibility_id": identifier, "sha256": digest})
            if args.operation == "initialize-legacy":
                if args.legacy_record is None or args.candidate_record is not None:
                    raise SuccessionFailure("release-succession-arguments-invalid")
                source = under(root, args.legacy_record, ".")
                record, raw = document(source)
                target, scope, _, identity = legacy_identity(record, raw)
                verdict, identifier = promote(root, target=target, scope=scope, identity=identity, source_path=source, source_digest=sha256_bytes(raw), expected_predecessor=args.expected_predecessor, legacy=True)
            else:
                if args.candidate_record is None or args.legacy_record is not None:
                    raise SuccessionFailure("release-succession-arguments-invalid")
                source = under(root, args.candidate_record, CANDIDATE_DIRECTORY)
                record, raw = document(source)
                target, scope, _, identity = candidate_identity(record, root)
                verdict, identifier = promote(root, target=target, scope=scope, identity=identity, source_path=source, source_digest=sha256_bytes(raw), expected_predecessor=args.expected_predecessor, legacy=False)
            return report(verdict, "release-succession-current-reference-advanced", facts={"target": target, "scope": scope, "release_id": identifier})
    except (SuccessionFailure, OSError) as error:
        return report("blocked", str(error) if isinstance(error, SuccessionFailure) else "release-succession-storage-unavailable")


if __name__ == "__main__":
    raise SystemExit(main())

