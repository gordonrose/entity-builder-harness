#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.accept-release
#   version: 4
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-25"
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
import importlib.util
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[8]
IMPLEMENTATION_ROOT = ROOT
EVIDENCE_CLASS = "live"  # Isolated imported test harnesses label their output simulated.
OBSERVATION_MAX_AGE = timedelta(minutes=10)
TASK_ARN = re.compile(r"arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/[a-f0-9]{32}")
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


def render(candidate: dict, facts: dict, existing: dict, prior_metadata: dict, rehearsal_references: dict | None = None) -> str:
    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    record = {
        "schema":"deploy/accepted-release/v1", "target":"kanbien-core-platform", "scope":"bootstrap-runtime", "status":"accepted" if EVIDENCE_CLASS == "live" else "rehearsed",
        "evidence_class": EVIDENCE_CLASS,
        "release": {"source_revision":candidate["source_revision"], "image_digest":candidate["image_digest"], "image_repository":"337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server", "runtime_stack":"kanbien-core-platform-bootstrap-runtime", "service":"kanbien-core-platform-bootstrap-runtime", "runtime_task_definition":facts["runtime_task_definition"], "verifier_task_definition":facts["verifier_task_definition"], "package_custody_reference":candidate["receipt_reference"], "private_verification":{"verdict":"accepted", "code":"runtime-digest-and-private-verifier-accepted", "verified_at":facts["observed_at"], "runtime_task_arn":facts["runtime_task_arn"], "verifier_task_arn":facts["verifier_task_arn"], "evidence_reference":"private-verification-command"}},
        "acceptance": {"accepted_at":stamp, "acceptance_checkpoint_commit":"pending-commit", "deployment_evidence_commit":"pending-commit", "retained_for_restoration":True},
        "cost_condition": existing.get("cost_condition", {}) if isinstance(existing, dict) else {},
    }
    record["acceptance"].update(rehearsal_references or {})
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


def load_implementation(relative: str):
    source = IMPLEMENTATION_ROOT / relative
    spec = importlib.util.spec_from_file_location("bootstrap_acceptance_dependency", source)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def retained_rehearsals(candidate: dict, existing: dict, rehearsal: Path | None, restoration: Path | None) -> dict:
    old_release = existing.get("release", {})
    same_identity = isinstance(old_release, dict) and all(old_release.get(key) == candidate.get(key) for key in ("source_revision", "image_digest"))
    prior = existing.get("acceptance", {})
    result = {}
    for field, supplied in (("last_rehearsal", rehearsal), ("last_restoration_rehearsal", restoration)):
        value = supplied if supplied is not None else prior.get(field) if same_identity and isinstance(prior, dict) else None
        if value is None: raise ValueError("accepted-release-matching-rehearsal-required")
        selected = Path(value)
        if not selected.is_absolute(): selected = RECORD.parent / selected
        try: relative = selected.resolve().relative_to(RECORD.parent.resolve())
        except ValueError: raise ValueError("accepted-release-rehearsal-path-invalid") from None
        if not selected.is_file() or any(part.is_symlink() for part in (selected, *selected.parents)):
            raise ValueError("accepted-release-rehearsal-path-invalid")
        evidence = yaml.safe_load(selected.read_text(encoding="utf-8"))
        if not isinstance(evidence, dict) or evidence.get("evidence_class", "live") != EVIDENCE_CLASS:
            raise ValueError("accepted-release-rehearsal-evidence-class-invalid")
        result[field] = relative.as_posix()
    return result


def validate_rendered(text: str) -> None:
    validator = load_implementation("scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py")
    validator.check_accepted_release(ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform", record_path=RECORD, record_override=yaml.safe_load(text), evidence_class=EVIDENCE_CLASS)


def observation_valid(facts: dict) -> bool:
    value = facts.get("observed_at")
    if not isinstance(value, str): return False
    try:
        observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if observed.tzinfo is None: return False
        observed = observed.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError): return False
    now = datetime.now(timezone.utc)
    if not now - OBSERVATION_MAX_AGE <= observed <= now: return False
    if any(not isinstance(facts.get(key), str) or TASK_ARN.fullmatch(facts[key]) is None for key in ("runtime_task_arn", "verifier_task_arn")): return False
    return facts["runtime_task_arn"] != facts["verifier_task_arn"]


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--verification-report", type=Path)
    parser.add_argument("--rehearsal", type=Path)
    parser.add_argument("--restoration-rehearsal", type=Path)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    try:
        args, unknown = parser.parse_known_args()
        direct = (args.receipt, args.verification_report, args.rehearsal, args.restoration_rehearsal)
        if unknown or (args.inputs is not None and any(value is not None for value in direct)) or (args.inputs is None and (args.receipt is None or args.verification_report is None)):
            return fail("accepted-release-arguments-invalid")
        if args.validate_arguments:
            print(json.dumps({"schema":"deploy/command-arguments-report/v1","verdict":"valid","findings":[]})); return 0
        if EVIDENCE_CLASS != "live" and (EVIDENCE_CLASS != "simulated" or not ROOT.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()) or not RECORD.resolve().is_relative_to(ROOT.resolve())):
            return fail("accepted-release-simulation-root-invalid")
        if args.inputs is not None:
            route = load_implementation("scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py")
            contract = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml"
            values = route.input_values(args.inputs, route.load_route(contract, ROOT)[0], root=ROOT)
            args.receipt, args.verification_report = Path(values["candidate_receipt"]), Path(values["verification_report"])
            args.rehearsal, args.restoration_rehearsal = Path(values["rehearsal"]), Path(values["restoration_rehearsal"])
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, argparse.ArgumentError): return fail("accepted-release-arguments-invalid")
    candidate = receipt(args.receipt)
    if candidate is None: return fail("package-custody-receipt-invalid")
    try: verification = json.loads(args.verification_report.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError): return fail("private-verification-report-unreadable")
    if not isinstance(verification, dict) or verification.get("schema") != "deploy/private-runtime-verification-report/v1" or verification.get("target") != "kanbien-core-platform" or verification.get("evidence_class", "live") != EVIDENCE_CLASS:
        return fail("private-verification-report-invalid")
    facts = verification.get("facts")
    if verification.get("verdict") != "accepted" or not isinstance(facts, dict) or verification.get("findings") != [{"code":"runtime-digest-and-private-verifier-accepted"}]: return fail("private-verification-not-accepted")
    if facts.get("source_revision") != candidate["source_revision"] or facts.get("image_digest") != candidate["image_digest"] or not all(isinstance(facts.get(key), str) and facts[key] for key in ("runtime_task_definition", "verifier_task_definition")):
        return fail("accepted-release-identity-mismatch")
    if not observation_valid(facts): return fail("private-verification-observation-stale-or-invalid")
    try:
        existing_text = RECORD.read_text(encoding="utf-8")
        existing = yaml.safe_load(existing_text)
        prior_metadata = record_metadata(existing_text)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError): return fail("accepted-release-record-invalid")
    if not isinstance(existing, dict) or existing.get("schema") != "deploy/accepted-release/v1" or existing.get("target") != "kanbien-core-platform" or existing.get("scope") != "bootstrap-runtime" or existing.get("status") not in ("accepted", "rehearsed") or (EVIDENCE_CLASS == "live" and existing.get("evidence_class", "live") != "live"):
        return fail("accepted-release-record-invalid")
    try:
        rehearsals = retained_rehearsals(candidate, existing, args.rehearsal, args.restoration_rehearsal)
        rendered = render(candidate, facts, existing, prior_metadata, rehearsals)
        validate_rendered(rendered)
    except Exception as error:
        codes = getattr(error, "codes", ())
        return fail(codes[0] if codes else str(error) if isinstance(error, ValueError) and str(error).startswith("accepted-release-") else "accepted-release-rendered-record-invalid")
    if not args.write:
        print(json.dumps({"schema":"deploy/accepted-release-report/v1","target":"kanbien-core-platform","verdict":"ready-to-record","evidence_class":EVIDENCE_CLASS,"findings":[]})); return 0
    try:
        if RECORD.read_text(encoding="utf-8") != existing_text: return fail("accepted-release-record-changed-during-validation")
        write_record(rendered)
    except OSError: return fail("accepted-release-record-write-failed")
    print(json.dumps({"schema":"deploy/accepted-release-report/v1","target":"kanbien-core-platform","verdict":"recorded" if EVIDENCE_CLASS == "live" else "rehearsed","evidence_class":EVIDENCE_CLASS,"findings":[]})); return 0


if __name__ == "__main__": raise SystemExit(main())
