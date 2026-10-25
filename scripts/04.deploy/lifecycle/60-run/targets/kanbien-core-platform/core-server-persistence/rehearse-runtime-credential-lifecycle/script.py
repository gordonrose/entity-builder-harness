#!/usr/bin/env python3
"""Govern one bounded runtime IAM-access revocation and recovery rehearsal.

The directory keeps its historical name so accepted route references remain
resolvable.  It no longer rotates, reads, writes, or transports a long-lived
database credential.  Runtime access is restored by the RDS IAM role and a
new task.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[8]
CHILD_CHECKPOINT: dict[str, Any] | None = None

def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(value)
    return value

def report(verdict: str, *codes: str, facts: dict[str, object] | None = None) -> int:
    if verdict == "blocked" and CHILD_CHECKPOINT is not None and CHILD_CHECKPOINT.get("verdict") in {"pending", "failed", "uncertain"}:
        verdict = CHILD_CHECKPOINT["verdict"]
        facts = {**(facts or {}), "child_checkpoint": CHILD_CHECKPOINT}
    body: dict[str, object] = {"schema": "deploy/persistence-runtime-identity-lifecycle-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts: body["facts"] = facts
    print(json.dumps(body, sort_keys=True))
    return 0 if verdict in {"accepted", "prepared"} else 1

def last_report(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        try: value = json.loads(line)
        except json.JSONDecodeError: continue
        if isinstance(value, dict) and isinstance(value.get("verdict"), str): return value
    return None

def child(path: str, *args: str) -> dict[str, Any] | None:
    global CHILD_CHECKPOINT
    CHILD_CHECKPOINT = None
    try:
        completed = subprocess.run(["bash", str(ROOT / path), *args], cwd=ROOT, capture_output=True, text=True, timeout=180)
        body = last_report(completed.stdout)
        fallback = last_report(completed.stderr)
        succeeded = completed.returncode == 0
    except subprocess.TimeoutExpired as error:
        # Preserve only a parsed safe controller receipt, never raw child output.
        stdout = error.stdout.decode("utf-8", errors="replace") if isinstance(error.stdout, bytes) else error.stdout or ""
        stderr = error.stderr.decode("utf-8", errors="replace") if isinstance(error.stderr, bytes) else error.stderr or ""
        body, fallback, succeeded = last_report(stdout), last_report(stderr), False
    observed = body or fallback
    if not succeeded:
        observed = observed if isinstance(observed, dict) else {}
        raw = observed.get("facts") if isinstance(observed.get("facts"), dict) else {}
        safe = {key: value for key, value in raw.items() if key in {"operation", "administration_task", "verifier_task", "original_task", "recovery_boundary"} and isinstance(value, str)}
        CHILD_CHECKPOINT = {"command": path, "verdict": observed.get("verdict") if observed.get("verdict") in {"pending", "failed", "uncertain"} else "uncertain", "facts": safe}
    return body if succeeded and isinstance(body, dict) else None

def healthy(verify: str) -> bool:
    return child("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh", "--mode", verify, "--json") is not None

def administer(operation: str) -> bool:
    """Use the separately governed administrator task for credential state."""
    return child("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh", "--operation", operation, "--json") is not None

def replace(receipt: Path) -> bool:
    return child("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.sh", "--receipt", str(receipt), "--json") is not None

def recover(receipt: Path) -> str:
    """Restore only the bounded IAM identity after proven denied readiness."""
    if not administer("restore-runtime"):
        return "persistence-runtime-identity-recovery-not-confirmed"
    if not replace(receipt):
        return "persistence-runtime-identity-recovery-replacement-not-confirmed"
    if not healthy("health-ready") or not healthy("read"):
        return "persistence-runtime-identity-recovery-meaningful-operation-not-confirmed"
    return "ok"

def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path); parser.add_argument("--operation", choices=("revoke-and-recover", "recover-after-revocation")); parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None or args.operation is None: return report("blocked", "persistence-runtime-identity-lifecycle-arguments-invalid")
    if args.validate_arguments: print(json.dumps({"schema":"deploy/command-arguments-report/v1","verdict":"valid","findings":[]})); return 0
    prepare = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py", "prepare")
    create = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py", "create")
    receipt = prepare.validate_receipt(args.receipt)
    if receipt is None or not create.package_gates(args.receipt) or not prepare.live_budget()[0]: return report("blocked", "persistence-runtime-identity-lifecycle-preconditions-not-proven")
    if args.operation == "recover-after-revocation":
        if not healthy("health-unready"):
            return report("blocked", "persistence-runtime-identity-revocation-denial-not-proven")
        code = recover(args.receipt)
        return report("accepted", "persistence-runtime-identity-recovery-proved") if code == "ok" else report("blocked", code)
    if not healthy("health-ready"):
        return report("blocked", "persistence-runtime-identity-baseline-health-not-proven")
    if not administer("revoke-runtime"):
        return report("blocked", "persistence-runtime-identity-revocation-not-confirmed")
    if not replace(args.receipt) or not healthy("health-unready"):
        return report("blocked", "persistence-runtime-identity-revocation-denial-not-proven")
    code = recover(args.receipt)
    return report("accepted", "persistence-runtime-identity-revocation-and-recovery-proved") if code == "ok" else report("blocked", code)

if __name__ == "__main__": raise SystemExit(main())
