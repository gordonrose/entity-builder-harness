#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.accept-release
#   version: 3
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Replace the accepted release only after qualified package custody and exact private runtime verification agree.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform-bootstrap-runtime-release
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/review-and-execute-ecs-runtime-update.md
#   effects: [writes-files]
from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[8]
RECORD = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml"


def fail(code: str) -> int:
    print(json.dumps({"schema":"deploy/accepted-release-report/v1","target":"kanbien-core-platform","verdict":"blocked","findings":[{"code":code}]})); return 1


def receipt(path: Path) -> dict | None:
    command = ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
        # Validate exactly the document retained for recording, even if the caller
        # replaces the original receipt while the validator is running.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json") as snapshot:
            json.dump(candidate, snapshot)
            snapshot.flush()
            run = subprocess.run(["bash", str(command), "--receipt", snapshot.name, "--expected-target", "kanbien-core-platform", "--expected-candidate", "kanbien-core-server-candidate", "--expected-package-contract", "kanbien-core-server-image", "--expected-program", "kanbien-core-server", "--json"], capture_output=True, text=True)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return candidate if run.returncode == 0 and isinstance(candidate, dict) else None


def record_metadata(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0] != "# agentic-artifact:":
        raise ValueError("accepted release metadata missing")
    header = []
    for line in lines[1:]:
        if not line.startswith("#"):
            break
        header.append(line[1:])
    metadata = yaml.safe_load("\n".join(header))
    if not isinstance(metadata, dict) or type(metadata.get("version")) is not int or metadata["version"] < 1:
        raise ValueError("accepted release metadata invalid")
    created_on = metadata.get("created_on")
    if not isinstance(created_on, str):
        raise ValueError("accepted release creation date invalid")
    date.fromisoformat(created_on)
    return metadata


def render(candidate: dict, facts: dict, existing: dict, prior_metadata: dict) -> str:
    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    record = {
        "schema":"deploy/accepted-release/v1", "target":"kanbien-core-platform", "scope":"bootstrap-runtime", "status":"accepted",
        "release": {"source_revision":candidate["source_revision"], "image_digest":candidate["image_digest"], "image_repository":"337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server", "runtime_stack":"kanbien-core-platform-bootstrap-runtime", "service":"kanbien-core-platform-bootstrap-runtime", "runtime_task_definition":facts["runtime_task_definition"], "verifier_task_definition":facts["verifier_task_definition"], "package_custody_reference":candidate["receipt_reference"], "private_verification":{"verdict":"accepted", "code":"runtime-digest-and-private-verifier-accepted", "verified_at":stamp, "evidence_reference":"private-verification-command"}},
        "acceptance": {"accepted_at":stamp, "acceptance_checkpoint_commit":"pending-commit", "deployment_evidence_commit":"pending-commit", "retained_for_restoration":True},
        "cost_condition": existing.get("cost_condition", {}) if isinstance(existing, dict) else {},
    }
    metadata = {
        "schema": "agentic-artifact/v3",
        "id": "infra.04-deploy.03-product.targets.kanbien-core-platform.scope.bootstrap-runtime.accepted-release",
        "version": prior_metadata["version"] + 1,
        "status": "active",
        "created_on": prior_metadata["created_on"],
        "updated_on": stamp[:10],
        "layer": "04.deploy",
        "domain": "deployment.bootstrap-runtime",
        "disciplines": ["security", "sre"],
        "kind": "accepted-release-record",
        "purpose": "Record the immutable package and live proof that form the retained bootstrap-runtime baseline.",
        "portability": {"class": "internal", "targets": []},
        "used_by": [{"id": "deploy.command.core-platform-target-declaration", "path": "scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh"}],
    }
    header = "# agentic-artifact:\n" + "".join("#   " + line + "\n" for line in yaml.safe_dump(metadata, sort_keys=False).splitlines())
    return header + yaml.safe_dump(record, sort_keys=False)


def write_record(text: str) -> None:
    pending = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RECORD.parent, prefix=f".{RECORD.name}.", suffix=".tmp", delete=False) as output:
            pending = Path(output.name)
            os.fchmod(output.fileno(), RECORD.stat().st_mode & 0o777)
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        os.replace(pending, RECORD)
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--verification-report", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown: return fail("accepted-release-arguments-invalid")
    candidate = receipt(args.receipt)
    if candidate is None: return fail("package-custody-receipt-invalid")
    try: verification = json.loads(args.verification_report.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError): return fail("private-verification-report-unreadable")
    if not isinstance(verification, dict) or verification.get("schema") != "deploy/private-runtime-verification-report/v1" or verification.get("target") != "kanbien-core-platform":
        return fail("private-verification-report-invalid")
    facts = verification.get("facts")
    if verification.get("verdict") != "accepted" or not isinstance(facts, dict) or verification.get("findings") != [{"code":"runtime-digest-and-private-verifier-accepted"}]: return fail("private-verification-not-accepted")
    if facts.get("source_revision") != candidate["source_revision"] or facts.get("image_digest") != candidate["image_digest"] or not all(isinstance(facts.get(key), str) and facts[key] for key in ("runtime_task_definition", "verifier_task_definition")):
        return fail("accepted-release-identity-mismatch")
    try:
        existing_text = RECORD.read_text(encoding="utf-8")
        existing = yaml.safe_load(existing_text)
        prior_metadata = record_metadata(existing_text)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError): return fail("accepted-release-record-invalid")
    if not isinstance(existing, dict) or existing.get("schema") != "deploy/accepted-release/v1" or existing.get("target") != "kanbien-core-platform" or existing.get("scope") != "bootstrap-runtime" or existing.get("status") != "accepted":
        return fail("accepted-release-record-invalid")
    rendered = render(candidate, facts, existing, prior_metadata)
    if not args.write:
        print(json.dumps({"schema":"deploy/accepted-release-report/v1","target":"kanbien-core-platform","verdict":"ready-to-record","findings":[]})); return 0
    try: write_record(rendered)
    except OSError: return fail("accepted-release-record-write-failed")
    print(json.dumps({"schema":"deploy/accepted-release-report/v1","target":"kanbien-core-platform","verdict":"recorded","findings":[]})); return 0


if __name__ == "__main__": raise SystemExit(main())
