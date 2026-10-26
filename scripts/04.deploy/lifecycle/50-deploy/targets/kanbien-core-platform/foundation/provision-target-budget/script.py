#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.provision-target-budget
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-26"
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
import hashlib
import importlib.util
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

_AWS_RESPONSE=None

def aws(service: str, *arguments: str, budget: bool = False, expect_json: bool = True) -> tuple[bool, Any, str]:
    global _AWS_RESPONSE
    if _AWS_RESPONSE is None:
        spec=importlib.util.spec_from_file_location("aws_response",ROOT/"scripts/04.deploy/shared/provider-adapters/aws/response.py")
        _AWS_RESPONSE=importlib.util.module_from_spec(spec);spec.loader.exec_module(_AWS_RESPONSE)
    if not _AWS_RESPONSE.inventory_covered(ROOT):return False,None,"delivery-inventory-not-covered"
    try:
        completed = subprocess.run(["aws", service, *arguments, "--profile", PROFILE, "--region", BUDGET_REGION if budget else STACK_REGION, "--output", "json", "--cli-connect-timeout", "5", "--cli-read-timeout", "20"], capture_output=True, text=True, check=False,timeout=30)
    except subprocess.TimeoutExpired:return False,None,"aws-command-timeout"
    if completed.returncode:return False,None,_AWS_RESPONSE.classify_error(service,arguments[0],completed.stderr)
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

def reconcile(name: str) -> int:
    """Observe one retained operation identity; never create, execute or delete."""
    change,code=describe_change_set(name)
    if change is None:return report("uncertain",findings=[code or "foundation-budget-operation-unobserved"],change_set=name)
    actual=change.get("ChangeSetName")
    if actual!=name and not (isinstance(actual,str) and actual.startswith("arn:aws:cloudformation:") and actual.split(":changeSet/",1)[-1].split("/",1)[0]==name):return report("uncertain",findings=["foundation-budget-operation-identity-unproven"],change_set=name)
    status=change.get("Status")
    if status in {"CREATE_PENDING","CREATE_IN_PROGRESS"}:return report("pending",findings=["foundation-budget-review-pending"],change_set=name)
    if status in {"FAILED","DELETE_FAILED","DELETE_COMPLETE"}:return report("failed",findings=["foundation-budget-review-failed"],change_set=name)
    execution=change.get("ExecutionStatus")
    if execution in {"AVAILABLE","EXECUTE_IN_PROGRESS"}:return report("pending",findings=["foundation-budget-execution-pending"],change_set=name)
    if execution!="EXECUTE_COMPLETE":return report("uncertain",findings=["foundation-budget-execution-unknown"],change_set=name)
    ok,payload,code=aws("cloudformation","describe-stacks","--stack-name",STACK)
    stacks=payload.get("Stacks") if ok and isinstance(payload,dict) else None
    if not isinstance(stacks,list) or len(stacks)!=1 or not isinstance(stacks[0],dict):return report("uncertain",findings=[code if not ok else "foundation-budget-stack-unobservable"],change_set=name)
    status=stacks[0].get("StackStatus")
    if status in {"UPDATE_IN_PROGRESS","UPDATE_COMPLETE_CLEANUP_IN_PROGRESS","UPDATE_ROLLBACK_IN_PROGRESS","UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"}:return report("pending",findings=["foundation-budget-stack-pending"],change_set=name)
    if status in {"UPDATE_FAILED","UPDATE_ROLLBACK_FAILED","UPDATE_ROLLBACK_COMPLETE"}:return report("failed",findings=["foundation-budget-stack-update-failed"],change_set=name)
    if status!="UPDATE_COMPLETE":return report("uncertain",findings=["foundation-budget-stack-state-unknown"],change_set=name)
    observation,code=verify()
    return report("executed-and-verified",change_set=name,provider_observation=observation) if code is None else report("uncertain",findings=[code],change_set=name)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("create", "review", "execute", "verify", "reconcile"), required=True); parser.add_argument("--change-set"); parser.add_argument("--json", action="store_true"); args = parser.parse_args()
    if args.mode in {"review", "execute", "reconcile"} and not args.change_set: return report("blocked", findings=["foundation-budget-change-set-required"])
    if args.mode == "verify" and args.change_set: return report("blocked", findings=["foundation-budget-arguments-invalid"])
    if args.mode == "reconcile":return reconcile(args.change_set)
    if args.mode == "create":
        email = cost_alert_email()
        if email is None: return report("blocked", findings=["cost-alert-email-required"])
        code = require_active_tag()
        if code: return report("blocked", findings=[code])
        parameters, code = stack_parameters(email)
        if code: return report("blocked", findings=[code])
        identity=hashlib.sha256(TEMPLATE.read_bytes()+json.dumps(parameters,sort_keys=True,separators=(",",":")).encode()).hexdigest()[:16]
        name=f"kanbien-core-platform-budget-{identity}"
        existing,observed_code=describe_change_set(name)
        if existing is not None:return reconcile(name)
        if observed_code!="aws-resource-missing":return report("uncertain",findings=[observed_code or "foundation-budget-operation-unobservable"],change_set=name)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as handle:
            json.dump(parameters, handle); handle.flush()
            ok, _, code = aws("cloudformation", "create-change-set", "--stack-name", STACK, "--change-set-name", name, "--change-set-type", "UPDATE", "--client-token", name, "--template-body", f"file://{TEMPLATE}", "--parameters", f"file://{handle.name}", "--capabilities", "CAPABILITY_NAMED_IAM")
        if not ok:return report("uncertain",findings=[code],change_set=name)
        return report("pending",findings=["foundation-budget-review-submitted"],change_set=name)
    if args.mode == "review":
        _, code = review(args.change_set)
        return report("reviewed", change_set=args.change_set, changes=[{"action": "Add", "resource": "Budget", "type": "AWS::Budgets::Budget"}]) if not code else report("blocked", findings=[code], change_set=args.change_set)
    if args.mode == "execute":
        proposed,code=describe_change_set(args.change_set)
        if proposed is None or proposed.get("ExecutionStatus")!="AVAILABLE":return reconcile(args.change_set)
        _,code=review(args.change_set)
        if code:return report("blocked",findings=[code],change_set=args.change_set)
        code=require_active_tag()
        if code:return report("blocked",findings=[code],change_set=args.change_set)
        ok,_,code=aws("cloudformation","execute-change-set","--stack-name",STACK,"--change-set-name",args.change_set,expect_json=False)
        if not ok:return report("uncertain",findings=[code],change_set=args.change_set)
        return reconcile(args.change_set)
    observation, code = verify()
    return report("verified", provider_observation=observation) if not code else report("blocked", findings=[code])

if __name__ == "__main__": raise SystemExit(main())
