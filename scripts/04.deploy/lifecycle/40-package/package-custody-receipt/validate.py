#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.package-custody-receipt-validation
#   version: 4
#   status: draft
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Fail closed when a package-custody receipt is missing, mismatched, or unsafe.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   created_on: "2026-10-20"
#   updated_on: "2026-11-22"
#   used_by:
#   - id: deploy.command.package-custody-receipt
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path

SCHEMA = "deploy/package-custody-receipt/v1"
EXTENDED_SCHEMA = "deploy/package-custody-receipt/v2"
FIELDS = {"schema", "target", "environment_class", "provider_region_alias", "candidate_id", "package_contract_id", "program_id", "source_revision", "image_digest", "release_identity", "checked_at", "checks", "verdict", "receipt_reference"}
BASE_CHECKS = {"runnable_program_contract", "dependency_boundary", "delivery_access_static", "delivery_access_live", "local_image_smoke", "sbom", "provenance_attestation"}
SCAN_CHECKS = {"ecr_scan", "vulnerability_scan"}
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{1,95}$")
REGION = re.compile(r"^[a-z][a-z0-9-]{1,31}-[a-z]+-[a-z0-9-]{1,31}$")
SHA = re.compile(r"^[0-9a-f]{40,64}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
RELEASE = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
REFERENCE = re.compile(r"^github-actions-run:[0-9]+$")
UNSAFE = re.compile(r"(?:https?://|@|[?&](?:token|secret|password|credential)=|authorization:|bearer\\s)", re.I)

class Failure(Exception):
    def __init__(self, *codes): self.codes = tuple(dict.fromkeys(codes))

def fail_if(value, pattern, code):
    if not isinstance(value, str) or not pattern.fullmatch(value) or UNSAFE.search(value): raise Failure(code)
    return value

def args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.error = lambda _message: parser.exit(2, report("failed", ("arguments-invalid",)) + "\n")
    parser.add_argument("--receipt", required=True); parser.add_argument("--expected-target", required=True)
    parser.add_argument("--expected-candidate", required=True); parser.add_argument("--expected-package-contract", required=True)
    parser.add_argument("--expected-program", required=True); parser.add_argument("--json", action="store_true")
    value, unknown = parser.parse_known_args()
    if unknown: raise Failure("arguments-invalid")
    for expected in (value.expected_target, value.expected_candidate, value.expected_package_contract, value.expected_program): fail_if(expected, IDENTIFIER, "expected-identifier-invalid")
    return value

def validate(receipt, expected):
    if not isinstance(receipt, dict) or receipt.get("schema") not in {SCHEMA, EXTENDED_SCHEMA}: raise Failure("receipt-schema-invalid")
    extended = receipt["schema"] == EXTENDED_SCHEMA
    if set(receipt) != (FIELDS | ({"local_qualification"} if extended else set())): raise Failure("receipt-fields-invalid")
    for key, want in (("target", expected.expected_target), ("candidate_id", expected.expected_candidate), ("package_contract_id", expected.expected_package_contract), ("program_id", expected.expected_program)):
        if fail_if(receipt.get(key), IDENTIFIER, f"{key}-invalid") != want: raise Failure(f"{key}-mismatch")
    fail_if(receipt.get("environment_class"), IDENTIFIER, "environment-class-invalid")
    fail_if(receipt.get("provider_region_alias"), REGION, "provider-region-alias-invalid")
    fail_if(receipt.get("source_revision"), SHA, "source-revision-invalid")
    fail_if(receipt.get("image_digest"), DIGEST, "image-digest-invalid")
    fail_if(receipt.get("release_identity"), RELEASE, "release-identity-invalid")
    fail_if(receipt.get("receipt_reference"), REFERENCE, "receipt-reference-invalid")
    try: parsed = datetime.fromisoformat(str(receipt.get("checked_at", "")).replace("Z", "+00:00"))
    except ValueError: raise Failure("checked-at-invalid") from None
    if parsed.tzinfo is None: raise Failure("checked-at-invalid")
    if receipt.get("verdict") != "qualified": raise Failure("receipt-not-qualified")
    checks = receipt.get("checks")
    if not isinstance(checks, dict) or not BASE_CHECKS.issubset(checks) or len(SCAN_CHECKS.intersection(checks)) != 1 or set(checks) != BASE_CHECKS.union(SCAN_CHECKS.intersection(checks)) or any(v != "passed" for v in checks.values()): raise Failure("receipt-checks-invalid")
    if extended:
        qualification = receipt.get("local_qualification")
        if not isinstance(qualification, dict) or set(qualification) != {"schema", "target", "scope", "source_revision", "checks"} or qualification.get("schema") != "deploy/local-qualification/v1" or qualification.get("target") != receipt["target"] or qualification.get("source_revision") != receipt["source_revision"]:
            raise Failure("receipt-local-qualification-invalid")
        fail_if(qualification.get("target"), IDENTIFIER, "receipt-local-qualification-invalid")
        fail_if(qualification.get("scope"), IDENTIFIER, "receipt-local-qualification-invalid")
        rows = qualification.get("checks")
        if not isinstance(rows, dict) or not rows: raise Failure("receipt-local-qualification-invalid")
        for identity, row in rows.items():
            fail_if(identity, IDENTIFIER, "receipt-local-qualification-invalid")
            if not isinstance(row, dict) or set(row) != {"input_digest", "evidence_key"}:
                raise Failure("receipt-local-qualification-invalid")
            fail_if(row.get("input_digest"), re.compile(r"^[a-f0-9]{64}$"), "receipt-local-qualification-invalid")
            fail_if(row.get("evidence_key"), re.compile(r"^[a-f0-9]{64}$"), "receipt-local-qualification-invalid")

def report(verdict, codes=(), receipt=None):
    result = {"schema": "deploy/package-custody-receipt-validation/v1", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if verdict == "passed": result.update({key: receipt[key] for key in ("target", "source_revision", "image_digest")})
    return json.dumps(result, sort_keys=True)

def main():
    try:
        expected = args()
        try: receipt = json.loads(Path(expected.receipt).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError): raise Failure("receipt-unreadable") from None
        validate(receipt, expected); print(report("passed", receipt=receipt))
    except Failure as error:
        print(report("failed", error.codes)); sys.exit(1)

if __name__ == "__main__": main()
