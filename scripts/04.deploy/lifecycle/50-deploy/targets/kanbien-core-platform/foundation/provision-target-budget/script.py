#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.provision-target-budget
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.foundation-cost-control
#   disciplines: [security, sre]
#   kind: script
#   purpose: Create, review, execute, and verify the one bounded Foundation update that provisions the declared target-filtered monthly budget.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform.provision-target-budget
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/10-foundation/provision-target-budget.md
#   effects: [aws-mutation]
"""Fixed, one-purpose target-budget provisioning control."""
from __future__ import annotations

import argparse
import datetime as dt
from decimal import Decimal, InvalidOperation
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[8]
PROFILE, STACK_REGION, BUDGET_REGION = "kanbien-dev", "eu-west-1", "us-east-1"
ACCOUNT_ID, TARGET, STACK = "337159794548", "kanbien-core-platform", "kanbien-core-platform-foundation"
BUDGET_NAME, EXPECTED_FILTER = "kanbien-core-platform-monthly", "user:Target$kanbien-core-platform"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/foundation.yml"
TAG_EVIDENCE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/evidence/target-cost-allocation-tag.yml"
TAG_VALIDATOR = ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.sh"

def report(verdict: str, *, findings: list[str] | None = None, **fields: Any) -> int:
    print(json.dumps({"schema": "deploy/foundation-budget-provisioning-report/v1", "target": TARGET, "stack": STACK, "budget_name": BUDGET_NAME, "verdict": verdict, "findings": [{"code": code} for code in findings or []], **fields}, sort_keys=True))
    return 0 if verdict in {"created-awaiting-review", "reviewed", "executed-and-verified", "verified"} else 1

def aws(service: str, *arguments: str, budget: bool = False, expect_json: bool = True) -> tuple[bool, Any, str]:
    completed = subprocess.run(["aws", service, *arguments, "--profile", PROFILE, "--region", BUDGET_REGION if budget else STACK_REGION, "--output", "json"], capture_output=True, text=True, check=False)
    if completed.returncode:
        lowered = completed.stderr.lower()
        if "accessdenied" in lowered or "not authorized" in lowered: return False, None, "aws-access-denied"
        if "does not exist" in lowered or "notfound" in lowered: return False, None, "aws-resource-missing"
        if "already exists" in lowered: return False, None, "aws-resource-already-exists"
        return False, None, "aws-command-failed"
    if not expect_json and not completed.stdout.strip(): return True, {}, "ok"
    try: return True, json.loads(completed.stdout), "ok"
    except json.JSONDecodeError: return False, None, "aws-response-invalid"

def stack_parameters(cost_alert_email: str) -> tuple[list[dict[str, Any]], str | None]:
    ok, payload, code = aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    if not ok: return [], code
    stacks = payload.get("Stacks", []) if isinstance(payload, dict) else []
    if len(stacks) != 1 or stacks[0].get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"}: return [], "foundation-stack-not-stable"
    current = stacks[0].get("Parameters", [])
    if not isinstance(current, list): return [], "foundation-stack-parameters-invalid"
    values = {item.get("ParameterKey"): item.get("ParameterValue") for item in current if isinstance(item, dict)}
    if values.get("EnableTargetBudget") != "false": return [], "target-budget-not-in-provisioning-state"
    parameters: list[dict[str, Any]] = []
    for key in sorted(key for key in values if isinstance(key, str)):
        if key == "EnableTargetBudget": parameters.append({"ParameterKey": key, "ParameterValue": "true"})
        elif key == "CostAlertEmail": parameters.append({"ParameterKey": key, "ParameterValue": cost_alert_email})
        else: parameters.append({"ParameterKey": key, "UsePreviousValue": True})
    return parameters, None

def cost_alert_email() -> str | None:
    value = os.environ.get("KANBIEN_CORE_PLATFORM_COST_ALERT_EMAIL", "")
    if "@" not in value or "\n" in value or "\r" in value or len(value.strip()) < 3:
        return None
    return value.strip()

def require_active_tag() -> str | None:
    check = subprocess.run(["bash", str(TAG_VALIDATOR), "--evidence", str(TAG_EVIDENCE), "--required-status", "verified", "--json"], capture_output=True, text=True, check=False)
    return None if check.returncode == 0 else "target-cost-allocation-tag-not-verified"

def describe_change_set(name: str) -> tuple[dict[str, Any] | None, str | None]:
    ok, payload, code = aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
    return (payload, None) if ok and isinstance(payload, dict) else (None, code)

def review(name: str) -> tuple[dict[str, Any] | None, str | None]:
    change_set, code = describe_change_set(name)
    if change_set is None: return None, code
    if change_set.get("Status") != "CREATE_COMPLETE" or change_set.get("ExecutionStatus") != "AVAILABLE": return None, "foundation-budget-change-set-not-reviewable"
    changes = change_set.get("Changes")
    if not isinstance(changes, list) or len(changes) != 1: return None, "foundation-budget-change-set-scope-invalid"
    resource = changes[0].get("ResourceChange") if isinstance(changes[0], dict) else None
    if not isinstance(resource, dict) or (resource.get("Action"), resource.get("LogicalResourceId"), resource.get("ResourceType")) != ("Add", "Budget", "AWS::Budgets::Budget"):
        return None, "foundation-budget-change-set-scope-invalid"
    parameters = change_set.get("Parameters")
    values = {item.get("ParameterKey"): item.get("ParameterValue") for item in parameters if isinstance(item, dict)} if isinstance(parameters, list) else {}
    if values.get("EnableTargetBudget") != "true": return None, "foundation-budget-parameter-invalid"
    return change_set, None

def verify() -> tuple[dict[str, Any] | None, str | None]:
    ok, payload, code = aws("budgets", "describe-budget", "--account-id", ACCOUNT_ID, "--budget-name", BUDGET_NAME, budget=True)
    if not ok: return None, code
    budget = payload.get("Budget") if isinstance(payload, dict) else None
    if not isinstance(budget, dict): return None, "budget-response-invalid"
    limit, filters = budget.get("BudgetLimit"), budget.get("CostFilters")
    try: amount_matches = isinstance(limit, dict) and Decimal(str(limit.get("Amount"))) == Decimal("100")
    except (InvalidOperation, ValueError): amount_matches = False
    if not (budget.get("BudgetName") == BUDGET_NAME and budget.get("BudgetType") == "COST" and budget.get("TimeUnit") == "MONTHLY" and amount_matches and isinstance(limit, dict) and limit.get("Unit") == "USD" and isinstance(filters, dict) and filters.get("TagKeyValue") == [EXPECTED_FILTER]):
        return None, "target-budget-provider-configuration-mismatch"
    return {"budget_type": "COST", "time_unit": "MONTHLY", "amount": "100", "unit": "USD", "target_filter": EXPECTED_FILTER, "checked_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")}, None

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("create", "review", "execute", "verify"), required=True); parser.add_argument("--change-set"); parser.add_argument("--json", action="store_true"); args = parser.parse_args()
    if args.mode in {"review", "execute"} and not args.change_set: return report("blocked", findings=["foundation-budget-change-set-required"])
    if args.mode == "verify" and args.change_set: return report("blocked", findings=["foundation-budget-arguments-invalid"])
    if args.mode == "create":
        email = cost_alert_email()
        if email is None: return report("blocked", findings=["cost-alert-email-required"])
        code = require_active_tag()
        if code: return report("blocked", findings=[code])
        parameters, code = stack_parameters(email)
        if code: return report("blocked", findings=[code])
        name = f"kanbien-core-platform-budget-{dt.datetime.now(dt.UTC).strftime('%Y%m%d%H%M%S')}"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as handle:
            json.dump(parameters, handle); handle.flush()
            ok, _, code = aws("cloudformation", "create-change-set", "--stack-name", STACK, "--change-set-name", name, "--change-set-type", "UPDATE", "--template-body", f"file://{TEMPLATE}", "--parameters", f"file://{handle.name}", "--capabilities", "CAPABILITY_NAMED_IAM")
        if not ok: return report("blocked", findings=[code])
        for _ in range(24):
            proposed, code = describe_change_set(name)
            if proposed and proposed.get("Status") in {"CREATE_COMPLETE", "FAILED"}: break
            time.sleep(5)
        else: return report("blocked", findings=["foundation-budget-change-set-creation-unresolved"], change_set=name)
        _, code = review(name)
        if code: return report("blocked", findings=[code], change_set=name)
        return report("created-awaiting-review", change_set=name, changes=[{"action": "Add", "resource": "Budget", "type": "AWS::Budgets::Budget"}])
    if args.mode == "review":
        _, code = review(args.change_set)
        return report("reviewed", change_set=args.change_set, changes=[{"action": "Add", "resource": "Budget", "type": "AWS::Budgets::Budget"}]) if not code else report("blocked", findings=[code], change_set=args.change_set)
    if args.mode == "execute":
        _, code = review(args.change_set)
        if code: return report("blocked", findings=[code], change_set=args.change_set)
        ok, _, code = aws("cloudformation", "execute-change-set", "--stack-name", STACK, "--change-set-name", args.change_set, expect_json=False)
        if not ok: return report("blocked", findings=[code], change_set=args.change_set)
        for _ in range(48):
            ok, payload, code = aws("cloudformation", "describe-stacks", "--stack-name", STACK); stacks = payload.get("Stacks", []) if ok and isinstance(payload, dict) else []; status = stacks[0].get("StackStatus") if len(stacks) == 1 else None
            if status == "UPDATE_COMPLETE":
                observation, code = verify()
                return report("executed-and-verified", change_set=args.change_set, provider_observation=observation) if not code else report("blocked", findings=[code], change_set=args.change_set)
            if isinstance(status, str) and (status.endswith("FAILED") or status in {"UPDATE_ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_FAILED"}): return report("blocked", findings=["foundation-budget-stack-update-failed"], change_set=args.change_set, stack_status=status)
            time.sleep(5)
        return report("blocked", findings=["foundation-budget-stack-update-unresolved"], change_set=args.change_set)
    observation, code = verify()
    return report("verified", provider_observation=observation) if not code else report("blocked", findings=[code])

if __name__ == "__main__": raise SystemExit(main())
