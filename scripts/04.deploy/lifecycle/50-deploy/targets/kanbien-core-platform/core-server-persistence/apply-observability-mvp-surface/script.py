#!/usr/bin/env python3
"""Apply one reviewed, private collector observability update for persistence.

The controller deliberately owns the small transition from no collector to the
declared dedicated collector.  It never retries an ambiguous provider mutation:
``--reconcile`` only observes the deterministic change-set name.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
STACK = "kanbien-core-platform-core-server-persistence"
CLUSTER = "kanbien-core-platform"
SERVER_SERVICE = "kanbien-core-platform-core-server-persistence"
COLLECTOR_SERVICE = "kanbien-core-platform-observability-collector"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
COLLECTOR_GATE = ROOT / "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/script.sh"

# The server and collector are intentionally separate task identities.  This
# list is both an allowlist for the change-set and a review aid: an activation
# cannot smuggle in database, secret, broad-IAM, or unrelated topology changes.
ADDED = {
    "ObservabilityCollectorSecurityGroup": "AWS::EC2::SecurityGroup",
    "ServerObservabilityCollectorEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorDnsUdpEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorDnsTcpEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorEndpointEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorArtifactObjectStoreEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorIngressFromServer": "AWS::EC2::SecurityGroupIngress",
    "EndpointIngressFromObservabilityCollector": "AWS::EC2::SecurityGroupIngress",
    "ObservabilityCollectorConfiguration": "AWS::SSM::Parameter",
    "ObservabilityCollectorServiceDiscovery": "AWS::ServiceDiscovery::Service",
    "ObservabilityCollectorExecutionRole": "AWS::IAM::Role",
    "ObservabilityCollectorTaskRole": "AWS::IAM::Role",
    "ObservabilityAlarmTopic": "AWS::SNS::Topic",
    "ObservabilityAlertSubscription": "AWS::SNS::Subscription",
    "CoreServerPostgreSqlReadinessAlarm": "AWS::CloudWatch::Alarm",
    "PersistenceDatabaseFreeStorageAlarm": "AWS::CloudWatch::Alarm",
    "ObservabilityCollectorTaskDefinition": "AWS::ECS::TaskDefinition",
    "ObservabilityCollectorService": "AWS::ECS::Service",
}
MODIFIED = {
    "CoreServerPersistenceTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceService": "AWS::ECS::Service",
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    value: dict[str, object] = {
        "schema": "deploy/persistence-observability-mvp-surface-report/v1",
        "target": "kanbien-core-platform",
        "scope": "core-server-persistence",
        "verdict": verdict,
        "findings": [{"code": code} for code in dict.fromkeys(codes)],
    }
    if facts:
        value["facts"] = facts
    print(json.dumps(value, sort_keys=True))
    return 0 if verdict == "updated-awaiting-observability-proof" else 1


def receipt(path: Path, *, candidate: str, contract: str, program: str) -> dict | None:
    import subprocess
    check = ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
    result = subprocess.run([
        "bash", str(check), "--receipt", str(path), "--expected-target", "kanbien-core-platform",
        "--expected-candidate", candidate, "--expected-package-contract", contract,
        "--expected-program", program, "--json",
    ], capture_output=True, text=True)
    if result.returncode:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def healthy(service: object) -> bool:
    return isinstance(service, dict) and service.get("desiredCount") == 1 and service.get("runningCount") == 1 and service.get("status") == "ACTIVE"


def parameters(stack: object) -> dict[str, str] | None:
    try:
        items = stack["Stacks"]
        values = items[0]["Parameters"]
    except (KeyError, IndexError, TypeError):
        return None
    if not isinstance(items, list) or len(items) != 1 or not isinstance(values, list):
        return None
    found: dict[str, str] = {}
    for item in values:
        if not isinstance(item, dict) or not isinstance(item.get("ParameterKey"), str) or not isinstance(item.get("ParameterValue"), str):
            return None
        found[item["ParameterKey"]] = item["ParameterValue"]
    return found


def name_matches(value: object, name: str) -> bool:
    return value == name or (isinstance(value, str) and value.startswith("arn:aws:cloudformation:") and value.split(":changeSet/", 1)[-1].split("/", 1)[0] == name)


def review(change: object, name: str, server: dict, collector: dict, alert_email: str) -> bool:
    if not isinstance(change, dict) or change.get("Status") != "CREATE_COMPLETE" or change.get("ChangeSetType") not in {None, "UPDATE"} or not name_matches(change.get("ChangeSetName"), name):
        return False
    values = {item.get("ParameterKey"): item.get("ParameterValue") for item in change.get("Parameters", []) if isinstance(item, dict)}
    if values.get("ImageDigest") != server["image_digest"] or values.get("SupportImageDigest") != server["image_digest"] or values.get("RestoreVerifierImageDigest") != server["image_digest"] or values.get("SourceRevision") != server["source_revision"] or values.get("EnableObservability") != "true" or values.get("ObservabilityCollectorImage") != collector["image_digest"] or values.get("ObservabilityAlertEmail") != alert_email:
        return False
    added, modified = set(), set()
    changes = change.get("Changes")
    if not isinstance(changes, list):
        return False
    for item in changes:
        value = item.get("ResourceChange") if isinstance(item, dict) else None
        if not isinstance(value, dict):
            return False
        logical, kind, action = value.get("LogicalResourceId"), value.get("ResourceType"), value.get("Action")
        if action == "Add" and ADDED.get(logical) == kind:
            added.add(logical)
        elif action == "Modify" and MODIFIED.get(logical) == kind:
            modified.add(logical)
        else:
            return False
    return added == set(ADDED) and modified == set(MODIFIED)


def change_name(server: dict, collector: dict) -> str:
    return f"kanbien-core-platform-observability-{server['image_digest'][7:19]}-{collector['image_digest'][7:19]}"


def reconcile(prepare, name: str, expected: dict[str, str], server: dict, collector: dict, alert_email: str) -> int:
    verdict, code = prepare.observe_update(name, expected, lambda value: review(value, name, server, collector, alert_email))
    return report("updated-awaiting-observability-proof" if verdict == "complete" else verdict, code, facts={"change_set": name, "server_image_digest": server["image_digest"], "collector_image_digest": collector["image_digest"]})


def wait_for_review(prepare, name: str, server: dict, collector: dict, alert_email: str) -> tuple[dict | None, str]:
    for attempt in range(6):
        ok, change, code = prepare.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
        if not ok:
            return None, code
        if isinstance(change, dict) and change.get("Status") == "FAILED":
            return None, "persistence-observability-mvp-change-set-failed"
        if review(change, name, server, collector, alert_email):
            return change, "ok"
        if attempt < 5:
            time.sleep(2)
    return None, "persistence-observability-mvp-change-set-not-reviewable"


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--server-receipt", type=Path)
    parser.add_argument("--collector-receipt", type=Path)
    parser.add_argument("--alert-email")
    parser.add_argument("--reconcile", action="store_true")
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    if unknown or args.server_receipt is None or args.collector_receipt is None or not isinstance(args.alert_email, str) or not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}", args.alert_email):
        return report("blocked", "persistence-observability-mvp-arguments-invalid")
    prepare = load(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py", "prepare")
    create = load(ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py", "create")
    server = receipt(args.server_receipt, candidate="kanbien-core-server-persistence-candidate", contract="kanbien-core-server-persistence-image", program="kanbien-core-server-persistence")
    collector = receipt(args.collector_receipt, candidate="observability-collector", contract="core-server-persistence-observability-collector-image", program="kanbien-observability-collector")
    if server is None or collector is None or server.get("source_revision") != collector.get("source_revision"):
        return report("blocked", "persistence-observability-mvp-package-receipts-invalid")
    name = change_name(server, collector)
    expected = {"ImageDigest": server["image_digest"], "SupportImageDigest": server["image_digest"], "RestoreVerifierImageDigest": server["image_digest"], "SourceRevision": server["source_revision"], "EnableObservability": "true", "ObservabilityCollectorImage": collector["image_digest"], "ObservabilityAlertEmail": args.alert_email}
    if args.reconcile:
        return reconcile(prepare, name, expected, server, collector, args.alert_email)
    import subprocess
    collector_gate = subprocess.run(["bash", str(COLLECTOR_GATE), "--json"], capture_output=True, text=True)
    if collector_gate.returncode or not create.package_gates(args.server_receipt) or not prepare.declaration_covered() or not prepare.live_budget()[0] or not prepare.candidate_image(server)[0] or not prepare.candidate_image(collector)[0]:
        return report("blocked", "persistence-observability-mvp-preconditions-not-proven")
    foundation, code = prepare.foundation_outputs()
    if foundation is None:
        return report("blocked", code)
    infrastructure, code = prepare.infrastructure_parameters(foundation)
    if infrastructure is None:
        return report("blocked", code)
    ok, stack, code = prepare.aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    current = parameters(stack) if ok else None
    if current is None or stack.get("Stacks", [{}])[0].get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        return report("blocked", code if not ok else "persistence-observability-mvp-stack-not-healthy")
    if current.get("EnableObservability") != "false":
        return report("blocked", "persistence-observability-mvp-not-at-unactivated-baseline")
    ok, observed, code = prepare.aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", SERVER_SERVICE)
    services = observed.get("services") if ok and isinstance(observed, dict) else None
    if not isinstance(services, list) or len(services) != 1 or not healthy(services[0]):
        return report("blocked", "persistence-observability-mvp-server-not-healthy")
    values = {**infrastructure, "ImageRepositoryArn": f"arn:aws:ecr:{prepare.REGION}:{prepare.ACCOUNT}:repository/kanbien-core-platform/core-server", "ImageRepositoryUri": foundation["RepositoryUri"], **expected}
    ok, _, code = prepare.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok:
        if code != "aws-resource-missing":
            return report("blocked", code)
        parameter_values = [{"ParameterKey": key, "ParameterValue": value} for key, value in values.items()]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as file:
            json.dump(parameter_values, file)
            file.flush()
            ok, _, code = prepare.aws("cloudformation", "create-change-set", "--stack-name", STACK, "--change-set-name", name, "--change-set-type", "UPDATE", "--template-body", f"file://{TEMPLATE}", "--parameters", f"file://{file.name}", "--capabilities", "CAPABILITY_NAMED_IAM")
        if not ok:
            return report("uncertain", code, facts={"change_set": name})
    change, code = wait_for_review(prepare, name, server, collector, args.alert_email)
    if change is None:
        return reconcile(prepare, name, expected, server, collector, args.alert_email)
    if change.get("ExecutionStatus") != "AVAILABLE":
        return reconcile(prepare, name, expected, server, collector, args.alert_email)
    actual = {item.get("ParameterKey"): item.get("ParameterValue") for item in change.get("Parameters", []) if isinstance(item, dict)}
    if not prepare.update_parameters_match(actual, expected, current):
        return report("blocked", "persistence-observability-mvp-parameters-mismatch")
    ok, _, code = prepare.aws("cloudformation", "execute-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok:
        return report("uncertain", code, facts={"change_set": name})
    return reconcile(prepare, name, expected, server, collector, args.alert_email)


if __name__ == "__main__":
    raise SystemExit(main())
