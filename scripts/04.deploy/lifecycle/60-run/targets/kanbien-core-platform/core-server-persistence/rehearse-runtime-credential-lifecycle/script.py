#!/usr/bin/env python3
"""Govern one bounded runtime PostgreSQL credential lifecycle rehearsal."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[8]
STACK = "kanbien-core-platform-core-server-persistence"
RUNTIME_SECRET_OUTPUT = "RuntimeCredentialsSecretArn"

def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(value)
    return value

def report(verdict: str, *codes: str, facts: dict[str, object] | None = None) -> int:
    body: dict[str, object] = {"schema": "deploy/persistence-runtime-credential-lifecycle-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts: body["facts"] = facts
    print(json.dumps(body, sort_keys=True))
    return 0 if verdict == "accepted" else 1

def last_report(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        try: value = json.loads(line)
        except json.JSONDecodeError: continue
        if isinstance(value, dict) and isinstance(value.get("verdict"), str): return value
    return None

def child(path: str, *args: str) -> dict[str, Any] | None:
    completed = subprocess.run(["bash", str(ROOT / path), *args], cwd=ROOT, capture_output=True, text=True)
    body = last_report(completed.stdout)
    return body if completed.returncode == 0 and isinstance(body, dict) else None

def outputs(prepare: Any) -> tuple[dict[str, str] | None, str]:
    ok, data, code = prepare.aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    stacks = data.get("Stacks") if ok and isinstance(data, dict) else None
    if not isinstance(stacks, list) or len(stacks) != 1 or not isinstance(stacks[0], dict): return None, code if not ok else "persistence-credential-lifecycle-stack-outputs-unavailable"
    values = {item.get("OutputKey"): item.get("OutputValue") for item in stacks[0].get("Outputs", []) if isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str)}
    return values, "ok"

def current_secret_version(prepare: Any, secret_arn: str) -> tuple[str | None, str]:
    ok, data, code = prepare.aws("secretsmanager", "describe-secret", "--secret-id", secret_arn)
    versions = data.get("VersionIdsToStages") if ok and isinstance(data, dict) else None
    if not isinstance(versions, dict): return None, code if not ok else "persistence-credential-lifecycle-secret-metadata-unavailable"
    current = [version for version, stages in versions.items() if isinstance(version, str) and isinstance(stages, list) and stages == ["AWSCURRENT"]]
    return (current[0], "ok") if len(current) == 1 else (None, "persistence-credential-lifecycle-current-secret-version-ambiguous")

def advance_secret(prepare: Any, secret_arn: str) -> tuple[str | None, str]:
    ok, generated, code = prepare.aws("secretsmanager", "get-random-password", "--password-length", "32", "--exclude-punctuation")
    password = generated.get("RandomPassword") if ok and isinstance(generated, dict) else None
    if not isinstance(password, str) or not password: return None, code if not ok else "persistence-credential-lifecycle-password-generation-unavailable"
    path: str | None = None
    try:
        descriptor, path = tempfile.mkstemp(prefix="kanbien-runtime-credential-", suffix=".json")
        os.fchmod(descriptor, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle: json.dump({"username": "core_runtime", "password": password}, handle, separators=(",", ":"))
        completed = subprocess.run(["aws", "secretsmanager", "put-secret-value", "--secret-id", secret_arn, "--secret-string", f"file://{path}", "--profile", prepare.PROFILE, "--region", prepare.REGION, "--output", "json"], capture_output=True, text=True)
        if completed.returncode != 0: return None, "persistence-credential-lifecycle-secret-version-write-failed"
        try: response = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError: return None, "persistence-credential-lifecycle-secret-version-write-response-invalid"
        version = response.get("VersionId") if isinstance(response, dict) else None
        return (version, "ok") if isinstance(version, str) and version else (None, "persistence-credential-lifecycle-secret-version-write-response-invalid")
    finally:
        if path is not None:
            try: os.unlink(path)
            except FileNotFoundError: pass

def healthy(verify: str) -> bool:
    return child("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh", "--mode", verify, "--json") is not None

def migrate(operation: str) -> bool:
    return child("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.sh", "--runtime-credential-operation", operation, "--json") is not None

def replace(receipt: Path) -> bool:
    return child("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.sh", "--receipt", str(receipt), "--json") is not None

def rotate_and_replace(prepare: Any, secret_arn: str, receipt: Path) -> tuple[str | None, str]:
    version, code = advance_secret(prepare, secret_arn)
    if version is None: return None, code
    # An unconfirmed migration may have changed the database role.  Do not
    # revert the secret automatically: block and require fresh observation.
    if not migrate("rotate"): return version, "persistence-credential-lifecycle-rotation-migration-not-confirmed"
    if not replace(receipt): return version, "persistence-credential-lifecycle-rotation-replacement-not-confirmed"
    if not healthy("health-ready") or not healthy("read"): return version, "persistence-credential-lifecycle-rotation-meaningful-operation-not-confirmed"
    return version, "ok"

def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path); parser.add_argument("--operation"); parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None or args.operation not in {"rotate", "revoke-and-recover"}: return report("blocked", "persistence-credential-lifecycle-arguments-invalid")
    prepare = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py", "prepare")
    create = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py", "create")
    receipt = prepare.validate_receipt(args.receipt)
    if receipt is None or not create.package_gates(args.receipt) or not prepare.live_budget()[0]: return report("blocked", "persistence-credential-lifecycle-preconditions-not-proven")
    values, code = outputs(prepare); secret_arn = values.get(RUNTIME_SECRET_OUTPUT) if isinstance(values, dict) else None
    if not isinstance(secret_arn, str) or not secret_arn: return report("blocked", code if values is None else "persistence-credential-lifecycle-runtime-secret-unavailable")
    prior_version, code = current_secret_version(prepare, secret_arn)
    if prior_version is None: return report("blocked", code)
    if not healthy("health-ready"): return report("blocked", "persistence-credential-lifecycle-baseline-health-not-proven")
    if args.operation == "rotate":
        version, code = rotate_and_replace(prepare, secret_arn, args.receipt)
        return report("accepted", "persistence-runtime-credential-rotation-proved", facts={"prior_secret_version": prior_version, "replacement_secret_version": version}) if code == "ok" else report("blocked", code, facts={"prior_secret_version": prior_version, "replacement_secret_version": version})
    if not migrate("revoke"): return report("blocked", "persistence-credential-lifecycle-revocation-not-confirmed", facts={"prior_secret_version": prior_version})
    if not replace(args.receipt) or not healthy("health-unready"): return report("blocked", "persistence-credential-lifecycle-revocation-denial-not-confirmed", facts={"prior_secret_version": prior_version})
    version, code = rotate_and_replace(prepare, secret_arn, args.receipt)
    return report("accepted", "persistence-runtime-credential-revocation-and-recovery-proved", facts={"prior_secret_version": prior_version, "recovery_secret_version": version}) if code == "ok" else report("blocked", code, facts={"prior_secret_version": prior_version, "recovery_secret_version": version})

if __name__ == "__main__": raise SystemExit(main())
