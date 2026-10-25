#!/usr/bin/env python3
"""Apply only the reviewed verifier-to-current-server route correction."""
from __future__ import annotations
import argparse, importlib.util, json, subprocess, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
STACK = "kanbien-core-platform-core-server-persistence"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"

def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path); value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader; spec.loader.exec_module(value); return value

def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value = {"schema":"deploy/persistence-private-route-update-report/v1","target":"kanbien-core-platform","scope":"core-server-persistence","verdict":verdict,"findings":[{"code":code} for code in codes]}
    if facts: value["facts"] = facts
    print(json.dumps(value, sort_keys=True)); return 0 if verdict == "updated" else 1

def route_update_reviewable(change: object, stack_status: object, name: str, digest: str, revision: str) -> bool:
    if not isinstance(change, dict) or stack_status not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}: return False
    if not (change.get("ChangeSetName") == name or (isinstance(change.get("ChangeSetName"), str) and change["ChangeSetName"].startswith("arn:aws:cloudformation:") and change["ChangeSetName"].split(":changeSet/", 1)[-1].split("/", 1)[0] == name)) or change.get("Status") != "CREATE_COMPLETE" or change.get("ChangeSetType") not in {None, "UPDATE"}: return False
    parameters = {item.get("ParameterKey"): item.get("ParameterValue") for item in change.get("Parameters", []) if isinstance(item, dict)}
    if parameters.get("ImageDigest") != digest or parameters.get("SupportImageDigest") != digest or parameters.get("RestoreVerifierImageDigest") != digest or parameters.get("SourceRevision") != revision: return False
    changes = [item.get("ResourceChange", {}) for item in change.get("Changes", []) if isinstance(item, dict)]
    return len(changes) == 1 and changes[0].get("Action") == "Add" and changes[0].get("ResourceType") == "AWS::EC2::SecurityGroupEgress" and changes[0].get("LogicalResourceId") == "VerifierEgressToServer"

def reviewed_change_set(prepare: object, name: str, stack_status: str, digest: str, revision: str) -> tuple[dict | None, str]:
    """Await the named, already-created change set becoming fully reviewable.

    CloudFormation can briefly report CREATE_COMPLETE before the `Changes`
    collection is visible. The fixed name makes this reconciliation idempotent:
    it can only ever inspect and, later, execute the one bounded correction.
    """
    last_code = "persistence-private-route-update-not-reviewable"
    for attempt in range(6):
        ok, change, code = prepare.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
        if not ok:
            return None, code
        if route_update_reviewable(change, stack_status, name, digest, revision):
            return change, "ok"
        last_code = "persistence-private-route-update-not-reviewable"
        if attempt < 5:
            time.sleep(2)
    return None, last_code

def reconcile(prepare, name, digest, revision):
    verdict, code = prepare.observe_update(name, {"ImageDigest": digest, "SupportImageDigest": digest, "RestoreVerifierImageDigest": digest, "SourceRevision": revision}, lambda change: route_update_reviewable(change, "UPDATE_COMPLETE", name, digest, revision))
    return report("updated" if verdict == "complete" else verdict, code, facts={"change_set": name, "candidate_image_digest": digest})

def main() -> int:
    parser = argparse.ArgumentParser(add_help=False); parser.add_argument("--receipt", type=Path); parser.add_argument("--json", action="store_true"); parser.add_argument("--reconcile", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.receipt is None: return report("blocked", "persistence-private-route-update-arguments-invalid")
    prepare = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py", "prepare")
    create = module(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py", "create")
    receipt = prepare.validate_receipt(args.receipt)
    if receipt is None: return report("blocked", "package-custody-receipt-invalid")
    digest, revision = receipt["image_digest"], receipt["source_revision"]
    name = f"kanbien-core-platform-persistence-route-update-{digest[7:19]}"
    if args.reconcile: return reconcile(prepare, name, digest, revision)
    if not create.package_gates(args.receipt): return report("blocked", "persistence-declaration-or-package-gate-not-proven")
    foundation, code = prepare.foundation_outputs()
    if foundation is None: return report("blocked", code)
    infrastructure, code = prepare.infrastructure_parameters(foundation)
    if infrastructure is None or not prepare.candidate_image(receipt)[0] or not prepare.live_budget()[0]: return report("blocked", "persistence-private-route-update-preconditions-not-proven")
    ok, stack, code = prepare.aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    status = stack.get("Stacks", [{}])[0].get("StackStatus") if ok and isinstance(stack, dict) else None
    if not ok or status not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}: return report("blocked", code if not ok else "persistence-private-route-update-stack-not-healthy")
    ok, service, code = prepare.aws("ecs", "describe-services", "--cluster", prepare.CLUSTER if hasattr(prepare, "CLUSTER") else "kanbien-core-platform", "--services", "kanbien-core-platform-core-server-persistence")
    services = service.get("services", []) if ok and isinstance(service, dict) else []
    if len(services) != 1 or not isinstance(services[0], dict) or services[0].get("desiredCount") != 1 or services[0].get("runningCount") != 1: return report("blocked", "persistence-private-route-update-service-not-healthy")
    digest, revision = receipt["image_digest"], receipt["source_revision"]
    name = f"kanbien-core-platform-persistence-route-update-{digest[7:19]}"
    parameters = [{"ParameterKey": key, "ParameterValue": value} for key, value in prepare.candidate_parameters(foundation, infrastructure, receipt).items()]
    ok, _, code = prepare.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok:
        if code != "aws-resource-missing": return report("blocked", code)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as file:
            json.dump(parameters, file); file.flush()
            ok, _, code = prepare.aws("cloudformation", "create-change-set", "--stack-name", STACK, "--change-set-name", name, "--change-set-type", "UPDATE", "--template-body", f"file://{TEMPLATE}", "--parameters", f"file://{file.name}", "--capabilities", "CAPABILITY_NAMED_IAM")
        if not ok: return report("uncertain", code, facts={"change_set": name})
    change, code = reviewed_change_set(prepare, name, status, digest, revision)
    if change is None: return reconcile(prepare, name, digest, revision)
    if change.get("ExecutionStatus") != "AVAILABLE": return reconcile(prepare, name, digest, revision)
    expected = prepare.candidate_parameters(foundation, infrastructure, receipt)
    actual = {item.get("ParameterKey"): item.get("ParameterValue") for item in change.get("Parameters", []) if isinstance(item, dict)}
    if actual != expected: return report("blocked", "persistence-update-live-parameters-mismatch")
    ok, _, code = prepare.aws("cloudformation", "execute-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok: return report("uncertain", code, facts={"change_set": name})
    return reconcile(prepare, name, digest, revision)

if __name__ == "__main__": raise SystemExit(main())
