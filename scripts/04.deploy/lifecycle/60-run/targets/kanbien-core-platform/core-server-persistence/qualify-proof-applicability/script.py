#!/usr/bin/env python3
"""Read historical restore-verifier-only applicability; new releases use shared policy."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.qualify-persistence-proof-applicability
#   version: 3
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate historical restore-verifier-only applicability without authorizing new proof reuse or generating records.
#   portability: { class: internal, targets: [] }
#   argument_validation: {flag: --validate-arguments, effects: [read-only]}
#   used_by:
#   - id: deploy.command.kanbien-core-platform.collect-core-server-persistence-acceptance
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py
#   effects: [read-only]
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[8]
TARGET, SCOPE = "kanbien-core-platform", "core-server-persistence"
EVIDENCE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence"
PACKAGE_RECEIPTS = EVIDENCE / "package-receipts"
RECORDS = EVIDENCE / "proof-applicability"
PACKAGE_VALIDATOR = ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
SCHEMA = "deploy/persistence-proof-applicability/v1"
REUSABLE = {
    "migration-applied-state", "effective-privilege", "server-replacement", "server-replacement-read",
    "runtime-identity-initial-access", "credential-revocation", "credential-revocation-unready",
    "credential-recovery", "credential-recovery-health", "credential-recovery-read",
    "rollback-final-health", "rollback-final-read",
}
RESTORE_VERIFIER_INPUT = "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts"
IAM_AUTHENTICATION_INPUT = "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-iam-authentication.ts"
# These paths are copied or compiled into the qualified image. A change to any
# of them can alter the executable candidate and therefore cannot inherit an
# earlier proof. Deployment controllers, receipt collectors, test fixtures and
# target declarations remain in the recorded repository delta, but are not
# image input simply because they are in the same source revision.
IMAGE_INPUT_PREFIXES = (
    "packages/",
    "platform/",
    "infra/04.deploy/03.product/entrypoints/",
    "infra/04.deploy/03.product/image/core-server-persistence/",
)
IMAGE_INPUT_FILES = {"package.json", "package-lock.json"}
PACKAGE_FIELDS = {"source_revision", "image_digest", "receipt_reference"}


class ApplicabilityError(ValueError): pass

def canonical(value: object) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
def sha(value: object) -> str: return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()

def safe_relative(path: Path) -> str:
    try: return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as error: raise ApplicabilityError("persistence-proof-applicability-path-invalid") from error


def validate_package_receipt(path: Path) -> None:
    """Use the existing package-custody authority before retaining a receipt."""
    completed = subprocess.run([
        "bash", str(PACKAGE_VALIDATOR), "--receipt", str(path),
        "--expected-target", TARGET,
        "--expected-candidate", "kanbien-core-server-persistence-candidate",
        "--expected-package-contract", "kanbien-core-server-persistence-image",
        "--expected-program", "kanbien-core-server-persistence", "--json",
    ], capture_output=True, text=True, check=False)
    if completed.returncode:
        raise ApplicabilityError("persistence-proof-applicability-package-receipt-invalid")


def receipt(path: Path) -> tuple[dict[str, str], dict[str, Any]]:
    try: raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error: raise ApplicabilityError("persistence-proof-applicability-package-receipt-unreadable") from error
    if not isinstance(raw, dict) or raw.get("schema") != "deploy/package-custody-receipt/v1" or raw.get("target") != TARGET or raw.get("candidate_id") != "kanbien-core-server-persistence-candidate" or raw.get("package_contract_id") != "kanbien-core-server-persistence-image" or raw.get("program_id") != "kanbien-core-server-persistence" or raw.get("verdict") != "qualified": raise ApplicabilityError("persistence-proof-applicability-package-receipt-invalid")
    validate_package_receipt(path)
    identity = {key: raw.get(key) for key in PACKAGE_FIELDS}
    if not isinstance(identity["source_revision"], str) or re.fullmatch(r"[a-f0-9]{40}", identity["source_revision"]) is None or not isinstance(identity["image_digest"], str) or re.fullmatch(r"sha256:[a-f0-9]{64}", identity["image_digest"]) is None or not isinstance(identity["receipt_reference"], str) or not re.fullmatch(r"github-actions-run:[1-9][0-9]*", identity["receipt_reference"]): raise ApplicabilityError("persistence-proof-applicability-package-identity-invalid")
    return identity, raw

def source_paths(predecessor: str, candidate: str) -> list[str]:
    if subprocess.run(["git", "merge-base", "--is-ancestor", predecessor, candidate], cwd=ROOT, capture_output=True, text=True, check=False).returncode: raise ApplicabilityError("persistence-proof-applicability-source-not-successor")
    completed = subprocess.run(["git", "diff", "--name-only", predecessor, candidate], cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode: raise ApplicabilityError("persistence-proof-applicability-source-diff-unavailable")
    paths = [line for line in completed.stdout.splitlines() if line]
    if not paths or len(paths) != len(set(paths)): raise ApplicabilityError("persistence-proof-applicability-source-diff-invalid")
    return sorted(paths)

def image_input_paths(paths: list[str]) -> list[str]:
    return sorted(path for path in paths if path in IMAGE_INPUT_FILES or path.startswith(IMAGE_INPUT_PREFIXES))

def test_only_iam_qualification_delta(predecessor: str, candidate: str) -> bool:
    """Accept one reviewed test-only helper change, never a general IAM change.

    The candidate image contains a local-qualification delay hook solely so the
    packaged restore verifier can prove that token acquisition is outside the
    PostgreSQL connection deadline.  It is guarded by ``NODE_ENV == test`` and
    target configuration rejects both local-token variables.  Match the exact
    reviewed diff rather than treating arbitrary changes to IAM authentication
    as harmless.
    """
    completed = subprocess.run(
        ["git", "diff", "--unified=0", predecessor, candidate, "--", IAM_AUTHENTICATION_INPUT],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        return False
    changed = [
        line
        for line in completed.stdout.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]
    return changed == [
        "-//   version: 1",
        "+//   version: 2",
        '-//   updated_on: "2026-10-25"',
        '+//   updated_on: "2026-10-26"',
        '-  if (env["NODE_ENV"] === "test" && localToken !== undefined) return { username, authenticationToken: async () => localToken };',
        '+  const localDelayText = text(env["PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN_DELAY_MS"]);',
        "+  const localDelay = localDelayText === undefined ? 0 : Number(localDelayText);",
        '+  if (env["NODE_ENV"] === "test" && localToken !== undefined && Number.isInteger(localDelay) && localDelay >= 0 && localDelay <= 10_000) {',
        "+    return {",
        "+      username,",
        "+      authenticationToken: async () => {",
        "+        if (localDelay > 0) await new Promise<void>((resolve) => setTimeout(resolve, localDelay));",
        "+        return localToken;",
        "+      },",
        "+    };",
        "+  }",
    ]


def restore_only_delta(paths: list[str], predecessor: str | None = None, candidate: str | None = None) -> bool:
    # Keep the complete revision delta in the record for review, but establish
    # historical runtime-proof applicability from the actual package input
    # closure. A source revision can legitimately add receipt retention or a
    # controller regression without changing the immutable executable image.
    inputs = image_input_paths(paths)
    if inputs == [RESTORE_VERIFIER_INPUT]:
        return True
    return (
        inputs == [IAM_AUTHENTICATION_INPUT, RESTORE_VERIFIER_INPUT]
        and isinstance(predecessor, str)
        and isinstance(candidate, str)
        and test_only_iam_qualification_delta(predecessor, candidate)
    )

def retained_package(binding: object) -> dict[str, str]:
    if not isinstance(binding, dict) or set(binding) != PACKAGE_FIELDS | {"receipt_path", "receipt_sha256"}: raise ApplicabilityError("persistence-proof-applicability-package-binding-invalid")
    identity = {key: binding.get(key) for key in PACKAGE_FIELDS}
    if any(not isinstance(value, str) for value in identity.values()) or not isinstance(binding.get("receipt_path"), str) or not isinstance(binding.get("receipt_sha256"), str): raise ApplicabilityError("persistence-proof-applicability-package-binding-invalid")
    path = ROOT / binding["receipt_path"]
    if path.resolve().parent != PACKAGE_RECEIPTS.resolve() or not path.is_file() or path.is_symlink(): raise ApplicabilityError("persistence-proof-applicability-retained-package-receipt-missing")
    retained_identity, raw = receipt(path)
    if retained_identity != identity or sha(raw) != binding["receipt_sha256"]: raise ApplicabilityError("persistence-proof-applicability-retained-package-receipt-mismatch")
    return identity

def validate(value: object, expected_candidate: dict[str, str] | None = None) -> dict[str, Any]:
    expected = {"schema", "target", "scope", "change_class", "predecessor", "candidate", "source_delta", "reused_proofs", "integrity"}
    if not isinstance(value, dict) or set(value) != expected or value.get("schema") != SCHEMA or value.get("target") != TARGET or value.get("scope") != SCOPE or value.get("change_class") != "restore-verifier-only": raise ApplicabilityError("persistence-proof-applicability-record-invalid")
    integrity = value.get("integrity"); body = {key: item for key, item in value.items() if key != "integrity"}
    if not isinstance(integrity, dict) or integrity.get("algorithm") != "sha256" or integrity.get("payload_sha256") != sha(body): raise ApplicabilityError("persistence-proof-applicability-integrity-invalid")
    old, new = retained_package(value["predecessor"]), retained_package(value["candidate"])
    if old["source_revision"] == new["source_revision"] or old["image_digest"] == new["image_digest"]: raise ApplicabilityError("persistence-proof-applicability-identity-not-changed")
    if expected_candidate is not None and any(new.get(key) != expected_candidate.get(key) for key in PACKAGE_FIELDS): raise ApplicabilityError("persistence-proof-applicability-candidate-mismatch")
    delta = value.get("source_delta")
    if not isinstance(delta, dict) or set(delta) != {"paths", "sha256"} or not isinstance(delta.get("paths"), list) or not all(isinstance(path, str) for path in delta["paths"]): raise ApplicabilityError("persistence-proof-applicability-source-diff-invalid")
    paths = source_paths(old["source_revision"], new["source_revision"])
    if paths != delta["paths"] or delta.get("sha256") != sha(paths) or not restore_only_delta(paths, old["source_revision"], new["source_revision"]): raise ApplicabilityError("persistence-proof-applicability-change-not-restore-only")
    reused = value.get("reused_proofs")
    if not isinstance(reused, list) or set(reused) != REUSABLE or len(reused) != len(REUSABLE) or reused != sorted(reused): raise ApplicabilityError("persistence-proof-applicability-reused-proof-set-invalid")
    return value

def main() -> int:
    parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    try:
        args, unknown = parser.parse_known_args()
        if unknown or args.record is None:
            raise ApplicabilityError("persistence-proof-applicability-historical-reader-only")
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        validate(json.loads(args.record.read_text()))
        print(json.dumps({"schema": SCHEMA, "target": TARGET, "scope": SCOPE, "verdict": "validated", "findings": []})); return 0
    except (ApplicabilityError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"schema": SCHEMA, "target": TARGET, "scope": SCOPE, "verdict": "blocked", "findings": [{"code": str(error) if isinstance(error, ApplicabilityError) else "persistence-proof-applicability-malformed-input"}]}, sort_keys=True)); return 1

if __name__ == "__main__": raise SystemExit(main())
