#!/usr/bin/env python3
"""Record a proven qualified predecessor without rewriting acceptance history."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.qualify-persistence-rollback-predecessor.impl
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind a previously qualified immutable image to fresh rollback health/read proof and corrected target contracts without retrospectively accepting it.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.workflow.govern-scope-lifecycle
#     path: .agentic/04.deploy/60-run/workflows/govern-scope-lifecycle.md
#   effects: [writes-files]
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[8]
EVIDENCE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence"
RECEIPTS = EVIDENCE / "proof-receipts"
CONTRACTS = {"configuration_contract": "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml", "permission_contract": "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"}
TARGET, SCOPE = "kanbien-core-platform", "core-server-persistence"

def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path); value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader; spec.loader.exec_module(value); return value
RECEIPT = module(ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py", "persistence_proof_receipts")
SUCCESSION = module(ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py", "release_succession")
class Failure(ValueError): pass
def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value: dict[str, Any] = {"schema": "deploy/persistence-rollback-predecessor-report/v1", "target": TARGET, "scope": SCOPE, "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts: value["facts"] = facts
    print(json.dumps(value, sort_keys=True)); return 0 if verdict == "recorded" else 1
def sha256(raw: bytes) -> str: return "sha256:" + hashlib.sha256(raw).hexdigest()
def package(path: Path) -> dict[str, str]:
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error: raise Failure("persistence-rollback-predecessor-package-receipt-invalid") from error
    required = {"schema", "target", "candidate_id", "program_id", "package_contract_id", "source_revision", "image_digest", "receipt_reference", "verdict"}
    if not isinstance(value, dict) or not required <= set(value) or value.get("schema") != "deploy/package-custody-receipt/v1" or value.get("target") != TARGET or value.get("candidate_id") != "kanbien-core-server-persistence-candidate" or value.get("program_id") != "kanbien-core-server-persistence" or value.get("package_contract_id") != "kanbien-core-server-persistence-image" or value.get("verdict") != "qualified": raise Failure("persistence-rollback-predecessor-package-receipt-invalid")
    source, digest, reference = value.get("source_revision"), value.get("image_digest"), value.get("receipt_reference")
    if not isinstance(source, str) or len(source) != 40 or any(c not in "0123456789abcdef" for c in source) or not isinstance(digest, str) or len(digest) != 71 or not digest.startswith("sha256:") or not isinstance(reference, str) or not reference.startswith("github-actions-run:") or not reference.removeprefix("github-actions-run:").isdigit(): raise Failure("persistence-rollback-predecessor-package-receipt-invalid")
    return {"source_revision": source, "image_digest": digest, "package_custody_reference": reference}
def proof(path: Path, *, operation: str, result: str, digest: str) -> tuple[dict[str, Any], dict[str, str]]:
    try:
        path = path.resolve(); path.relative_to(RECEIPTS.resolve()); raw = path.read_bytes(); value = RECEIPT.validate(json.loads(raw))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error: raise Failure("persistence-rollback-predecessor-proof-invalid") from error
    task, provenance = value["task"], value["provenance"]
    if value["proof_type"] != "verifier" or value["operation"] != operation or task["image_digest"] != digest or task["exit_code"] != 0 or task["terminal_status"] != "STOPPED" or task["result_code"] != result or provenance["controller"] != "verify-candidate" or provenance["collection_method"] != "ecs-terminal-task+task-definition+safe-log" or provenance.get("evidence_class", "live") != "live": raise Failure("persistence-rollback-predecessor-proof-mismatch")
    return value, {"path": path.relative_to(EVIDENCE).as_posix(), "sha256": sha256(raw)}
def contracts() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for key, relative in CONTRACTS.items():
        try: result[key] = {"path": relative, "sha256": sha256((ROOT / relative).read_bytes())}
        except OSError as error: raise Failure("persistence-rollback-predecessor-contract-unreadable") from error
    return result
def atomic(path: Path, value: dict[str, Any]) -> None:
    rendered = yaml.safe_dump(value, sort_keys=False).encode("utf-8"); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != rendered: raise Failure("persistence-rollback-predecessor-record-conflict")
        return
    with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as out:
        temporary = Path(out.name); out.write(rendered); out.flush(); os.fsync(out.fileno())
    os.replace(temporary, path)
def same_binding(existing: object, value: dict[str, Any]) -> bool:
    if not isinstance(existing, dict): return False
    fields = ("schema", "target", "scope", "status", "qualified_predecessor", "rollback", "proof_set")
    return all(existing.get(field) == value.get(field) for field in fields)
def main() -> int:
    parser = argparse.ArgumentParser(add_help=False); parser.add_argument("--receipt", type=Path); parser.add_argument("--health-receipt", type=Path); parser.add_argument("--read-receipt", type=Path); parser.add_argument("--json", action="store_true"); parser.add_argument("--validate-arguments", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or not all((args.receipt, args.health_receipt, args.read_receipt)): return report("blocked", "persistence-rollback-predecessor-arguments-invalid")
    if args.validate_arguments: print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
    try:
        predecessor = package(args.receipt)
        health, health_binding = proof(args.health_receipt, operation="health-ready", result="KANBIEN_CORE_PERSISTENCE_HEALTHY", digest=predecessor["image_digest"])
        read, read_binding = proof(args.read_receipt, operation="read", result="KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED", digest=predecessor["image_digest"])
        if health["task"]["arn"] == read["task"]["arn"]: raise Failure("persistence-rollback-predecessor-proof-mismatch")
        proof_set = {"rollback-b-health": health_binding, "rollback-b-read": read_binding}; contract = contracts()
        identity = {"target": TARGET, "scope": SCOPE, "qualified_predecessor": predecessor, "source_revision": predecessor["source_revision"], "image_digest": predecessor["image_digest"], **contract, "workloads": ["core-server-service", "private-release-verifier-task"], "proof_set_sha256": SUCCESSION.sha256_bytes(SUCCESSION.canonical(proof_set))}
        identifier = "rollback-compatibility-" + hashlib.sha256(SUCCESSION.canonical(identity)).hexdigest()[:24]
        value = {"schema": SUCCESSION.COMPATIBILITY_SCHEMA, "target": TARGET, "scope": SCOPE, "status": "verified", "qualified_predecessor": predecessor, "rollback": {"id": identifier, "configuration_contract": contract["configuration_contract"], "permission_contract": contract["permission_contract"], "workloads": identity["workloads"], "proof_set_sha256": identity["proof_set_sha256"]}, "proof": {"qualified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "receipt_count": len(proof_set)}, "proof_set": proof_set}
        SUCCESSION.compatibility_identity(value, EVIDENCE)
        path = EVIDENCE / SUCCESSION.CANDIDATE_DIRECTORY / f"{identifier}.yml"
        if path.exists():
            try:
                existing = yaml.safe_load(path.read_text(encoding="utf-8")); SUCCESSION.compatibility_identity(existing, EVIDENCE)
            except (OSError, UnicodeError, yaml.YAMLError, ValueError) as error: raise Failure("persistence-rollback-predecessor-record-conflict") from error
            if not same_binding(existing, value): raise Failure("persistence-rollback-predecessor-record-conflict")
        else: atomic(path, value)
        return report("recorded", "persistence-rollback-predecessor-qualified", facts={"candidate_record": str(path.relative_to(ROOT)), "rollback_compatibility_id": identifier})
    except Failure as error: return report("blocked", str(error))
if __name__ == "__main__": raise SystemExit(main())
