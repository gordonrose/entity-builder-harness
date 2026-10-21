#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.accept-release
#   version: 1
#   status: draft
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
#     path: .agentic/aws/workflows/kanbien-core-platform-bootstrap-runtime-release.md
#   effects: [writes-files]
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[8]
RECORD = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml"


def fail(code: str) -> int:
    print(json.dumps({"schema":"deploy/accepted-release-report/v1","target":"kanbien-core-platform","verdict":"blocked","findings":[{"code":code}]})); return 1


def receipt(path: Path) -> dict | None:
    command = ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
    run = subprocess.run(["bash", str(command), "--receipt", str(path), "--expected-target", "kanbien-core-platform", "--expected-candidate", "kanbien-core-server-candidate", "--expected-package-contract", "kanbien-core-server-image", "--expected-program", "kanbien-core-server", "--json"], capture_output=True, text=True)
    return json.loads(run.stdout) if run.returncode == 0 else None


def render(candidate: dict, facts: dict, existing: dict) -> str:
    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    record = {
        "schema":"deploy/accepted-release/v1", "target":"kanbien-core-platform", "scope":"bootstrap-runtime", "status":"accepted",
        "release": {"source_revision":candidate["source_revision"], "image_digest":candidate["image_digest"], "image_repository":"337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server", "runtime_stack":"kanbien-core-platform-bootstrap-runtime", "service":"kanbien-core-platform-bootstrap-runtime", "runtime_task_definition":facts["runtime_task_definition"], "verifier_task_definition":facts["verifier_task_definition"], "package_custody_reference":candidate["receipt_reference"], "private_verification":{"verdict":"accepted", "code":"runtime-digest-and-private-verifier-accepted", "verified_at":stamp, "evidence_reference":"private-verification-command"}},
        "acceptance": {"accepted_at":stamp, "acceptance_checkpoint_commit":"pending-commit", "deployment_evidence_commit":"pending-commit", "retained_for_restoration":True},
        "cost_condition": existing.get("cost_condition", {}) if isinstance(existing, dict) else {},
    }
    header = "# agentic-artifact:\n#   schema: agentic-artifact/v3\n#   id: infra.04-deploy.03-product.targets.kanbien-core-platform.scope.bootstrap-runtime.accepted-release\n#   version: 1\n#   status: active\n#   layer: 04.deploy\n#   domain: deployment.bootstrap-runtime\n#   kind: accepted-release-record\n#   purpose: Record the immutable package and live proof that form the retained bootstrap-runtime baseline.\n"
    return header + yaml.safe_dump(record, sort_keys=False)


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
    except (OSError, json.JSONDecodeError): return fail("private-verification-report-unreadable")
    facts = verification.get("facts") if isinstance(verification, dict) else None
    if verification.get("verdict") != "accepted" or not isinstance(facts, dict) or verification.get("findings") != [{"code":"runtime-digest-and-private-verifier-accepted"}]: return fail("private-verification-not-accepted")
    if facts.get("source_revision") != candidate["source_revision"] or facts.get("image_digest") != candidate["image_digest"] or not all(isinstance(facts.get(key), str) and facts[key] for key in ("runtime_task_definition", "verifier_task_definition")):
        return fail("accepted-release-identity-mismatch")
    try: existing = yaml.safe_load(RECORD.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError): existing = {}
    if not args.write:
        print(json.dumps({"schema":"deploy/accepted-release-report/v1","target":"kanbien-core-platform","verdict":"ready-to-record","findings":[]})); return 0
    RECORD.write_text(render(candidate, facts, existing if isinstance(existing, dict) else {}), encoding="utf-8")
    print(json.dumps({"schema":"deploy/accepted-release-report/v1","target":"kanbien-core-platform","verdict":"recorded","findings":[]})); return 0


if __name__ == "__main__": raise SystemExit(main())
