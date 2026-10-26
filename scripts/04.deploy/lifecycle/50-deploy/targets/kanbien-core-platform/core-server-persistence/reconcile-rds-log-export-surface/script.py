#!/usr/bin/env python3
"""Reconcile the one declared RDS log-export drift needed by restore diagnosis.

This controller deliberately does not use CloudFormation to make an otherwise
empty update look meaningful.  It may enable only the missing
``iam-db-auth-error`` export on the named, private PostgreSQL database.  It
never disables exports, changes engine settings, alters credentials, or
touches the application service.  An interrupted mutation is reconciled from
the live RDS state before another command can be issued.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
DATABASE = "kanbien-core-platform-persistence"
REQUIRED_EXPORTS = frozenset({"postgresql", "iam-db-auth-error"})
TRANSITIONAL_STATUSES = frozenset({"modifying", "configuring-log-exports", "rebooting"})


def report(verdict: str, *codes: str, facts: dict[str, object] | None = None) -> int:
    value: dict[str, object] = {
        "schema": "deploy/persistence-rds-log-export-reconciliation/v1",
        "target": "kanbien-core-platform",
        "scope": "core-server-persistence",
        "verdict": verdict,
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
    }
    if facts is not None:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "reconciled" else 1


def aws(*parts: str) -> tuple[bool, object | None, str]:
    try:
        result = subprocess.run(
            ["aws", *parts, "--profile", "kanbien-dev", "--region", "eu-west-1", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, None, "aws-command-timeout"
    except OSError:
        return False, None, "aws-command-unavailable"
    if result.returncode != 0:
        # Keep raw provider stderr out of repository evidence and terminal
        # output. Only the bounded disposition crosses this controller.
        return False, None, "aws-command-failed"
    try:
        return True, json.loads(result.stdout), "ok"
    except json.JSONDecodeError:
        return False, None, "aws-command-invalid-json"


def template_declares_required_exports(path: Path = TEMPLATE) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "EnableCloudwatchLogsExports: [postgresql, iam-db-auth-error]" in text


def database_state(value: object) -> tuple[dict[str, object] | None, str]:
    if not isinstance(value, dict):
        return None, "persistence-rds-log-export-observation-invalid"
    instances = value.get("DBInstances")
    if not isinstance(instances, list) or len(instances) != 1 or not isinstance(instances[0], dict):
        return None, "persistence-rds-log-export-observation-invalid"
    database = instances[0]
    exports = database.get("EnabledCloudwatchLogsExports")
    if not isinstance(exports, list) or not all(isinstance(item, str) for item in exports):
        return None, "persistence-rds-log-export-observation-invalid"
    if database.get("DBInstanceIdentifier") != DATABASE:
        return None, "persistence-rds-log-export-target-mismatch"
    if database.get("Engine") != "postgres" or database.get("PubliclyAccessible") is not False or database.get("IAMDatabaseAuthenticationEnabled") is not True:
        return None, "persistence-rds-log-export-boundary-invalid"
    status = database.get("DBInstanceStatus")
    if not isinstance(status, str):
        return None, "persistence-rds-log-export-observation-invalid"
    return {"status": status, "exports": sorted(set(exports))}, "ok"


def observe() -> tuple[dict[str, object] | None, str]:
    ok, value, code = aws("rds", "describe-db-instances", "--db-instance-identifier", DATABASE)
    if not ok:
        return None, code
    return database_state(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--reconcile", action="store_true")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        return report("blocked", "persistence-rds-log-export-arguments-invalid")
    if not template_declares_required_exports():
        return report("blocked", "persistence-rds-log-export-template-not-declared")
    state, code = observe()
    if state is None:
        return report("uncertain", code)
    status = state["status"]
    exports = frozenset(state["exports"])
    facts = {"database": DATABASE, "status": status, "enabled_exports": sorted(exports)}
    if REQUIRED_EXPORTS.issubset(exports):
        return report("reconciled", "persistence-rds-log-exports-observed", facts=facts)
    if status in TRANSITIONAL_STATUSES:
        return report("pending", "persistence-rds-log-export-update-still-provisioning", facts=facts)
    if status != "available":
        return report("blocked", "persistence-rds-log-export-database-not-available", facts=facts)
    # This route repairs exactly the observed drift. Missing PostgreSQL logging
    # is a broader target correction, not permission to reinterpret this
    # controller as a general RDS configuration tool.
    if "postgresql" not in exports or "iam-db-auth-error" in exports:
        return report("blocked", "persistence-rds-log-export-drift-not-owned", facts=facts)
    if args.reconcile:
        return report("pending", "persistence-rds-log-export-update-not-observed", facts=facts)
    ok, _, mutation_code = aws(
        "rds", "modify-db-instance",
        "--db-instance-identifier", DATABASE,
        "--cloudwatch-logs-export-configuration", json.dumps({"EnableLogTypes": ["iam-db-auth-error"]}, separators=(",", ":")),
        "--apply-immediately",
    )
    if not ok:
        return report("uncertain", mutation_code, facts=facts)
    return report("pending", "persistence-rds-log-export-update-submitted", facts=facts)


if __name__ == "__main__":
    raise SystemExit(main())
