#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.package-custody-receipt-validation
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Fail closed when a package-custody receipt is missing, mismatched, or unsafe.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path

SCHEMA = "deploy/package-custody-receipt/v1"
FIELDS = {"schema", "target", "environment_class", "provider_region_alias", "candidate_id", "package_contract_id", "program_id", "source_revision", "image_digest", "release_identity", "checked_at", "checks", "verdict", "receipt_reference"}
CHECKS = {"runnable_program_contract", "dependency_boundary", "local_image_smoke", "ecr_scan", "sbom", "provenance_attestation"}
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
    parser.add_argument("--receipt", required=True); parser.add_argument("--expected-target", required=True)
    parser.add_argument("--expected-candidate", required=True); parser.add_argument("--expected-package-contract", required=True)
    parser.add_argument("--expected-program", required=True); parser.add_argument("--json", action="store_true")
    value, unknown = parser.parse_known_args()
    if unknown: raise Failure("arguments-invalid")
    for expected in (value.expected_target, value.expected_candidate, value.expected_package_contract, value.expected_program): fail_if(expected, IDENTIFIER, "expected-identifier-invalid")
    return value

def validate(receipt, expected):
    if not isinstance(receipt, dict) or set(receipt) != FIELDS: raise Failure("receipt-fields-invalid")
    if receipt.get("schema") != SCHEMA: raise Failure("receipt-schema-invalid")
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
    if not isinstance(receipt.get("checks"), dict) or set(receipt["checks"]) != CHECKS or any(v != "passed" for v in receipt["checks"].values()): raise Failure("receipt-checks-invalid")

def report(verdict, codes=(), receipt=None):
    result = {"schema": "deploy/package-custody-receipt-validation/v1", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if verdict == "passed": result.update({key: receipt[key] for key in ("target", "source_revision", "image_digest")})
    return json.dumps(result, sort_keys=True)

try:
    expected = args()
    try: receipt = json.loads(Path(expected.receipt).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): raise Failure("receipt-unreadable") from None
    validate(receipt, expected); print(report("passed", receipt=receipt))
except Failure as error:
    print(report("failed", error.codes)); sys.exit(1)
