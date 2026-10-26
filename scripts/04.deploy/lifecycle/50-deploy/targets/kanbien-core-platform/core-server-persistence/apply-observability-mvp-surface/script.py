#!/usr/bin/env python3
"""Apply one reviewed, private collector observability update for persistence.

The controller deliberately owns the small transition from no collector to the
declared dedicated collector.  It never retries an ambiguous provider mutation:
``--reconcile`` only observes the deterministic change-set name.
"""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.apply-core-server-persistence-observability-mvp.impl
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Review and reconcile only the receipt-bound dedicated private collector activation change set.
#   portability: { class: internal, targets: [] }
#   effects: [aws-mutation]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.apply-core-server-persistence-observability-mvp.wrapper
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-observability-mvp-surface/script.sh
from __future__ import annotations

import argparse
import hashlib
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
CLOUDFORMATION_INLINE_TEMPLATE_LIMIT_BYTES = 51_200

# The server and collector are intentionally separate task identities. These
# lists are both an allowlist for the change-set and a review aid: enabling the
# collector deliberately replaces every task definition that packages the new
# qualified program image, and grants the server only its collector-delivery
# configuration. It cannot smuggle in database, secret, broad-IAM, or unrelated
# topology changes.
ADDED = {
    "ObservabilityCollectorSecurityGroup": "AWS::EC2::SecurityGroup",
    "ServerObservabilityCollectorEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorDnsUdpEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorDnsTcpEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorEndpointEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorArtifactObjectStoreEgress": "AWS::EC2::SecurityGroupEgress",
    "ObservabilityCollectorIngressFromServer": "AWS::EC2::SecurityGroupIngress",
    "EndpointIngressFromObservabilityCollector": "AWS::EC2::SecurityGroupIngress",
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
    "CoreServerPersistenceAdministrationTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceMigrationTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceRestorationVerifierTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceVerifierTaskDefinition": "AWS::ECS::TaskDefinition",
    "CoreServerPersistenceService": "AWS::ECS::Service",
    "ServerTaskRole": "AWS::IAM::Role",
}
REPAIR_ADDED: dict[str, str] = {}
REPAIR_MODIFIED = {
    "ObservabilityCollectorTaskDefinition": "AWS::ECS::TaskDefinition",
    "ObservabilityCollectorService": "AWS::ECS::Service",
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


def collector_image_available(prepare, value: dict) -> bool:
    """Prove the collector's runnable index exists without inventing ECR scan proof.

    The collector's custody workflow scans its exact saved archive with the
    pinned portable scanner and records ``vulnerability_scan`` in its receipt.
    ECR basic scans are part of the Node server's different custody route, so
    requiring one here would misrepresent the collector's accepted proof.
    """
    digest, _ = prepare.candidate_runnable_manifest(value)
    return isinstance(digest, str)


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


def review(
    change: object, name: str, server: dict, collector: dict, alert_email: str,
    collector_image: str, *, expected_added: dict[str, str] = ADDED,
    expected_modified: dict[str, str] = MODIFIED,
) -> bool:
    if not isinstance(change, dict) or change.get("Status") != "CREATE_COMPLETE" or change.get("ChangeSetType") not in {None, "UPDATE"} or not name_matches(change.get("ChangeSetName"), name):
        return False
    values = {item.get("ParameterKey"): item.get("ParameterValue") for item in change.get("Parameters", []) if isinstance(item, dict)}
    # A NoEcho parameter is intentionally redacted by CloudFormation. Its
    # input is instead bound into this operation's deterministic name.
    if values.get("ImageDigest") != server["image_digest"] or values.get("SupportImageDigest") != server["image_digest"] or values.get("RestoreVerifierImageDigest") != server["image_digest"] or values.get("SourceRevision") != server["source_revision"] or values.get("EnableObservability") != "true" or values.get("ObservabilityCollectorImage") != collector_image or values.get("ObservabilityAlertEmail") != "****":
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
        if action == "Add" and expected_added.get(logical) == kind:
            added.add(logical)
        elif action == "Modify" and expected_modified.get(logical) == kind:
            modified.add(logical)
        else:
            return False
    return added == set(expected_added) and modified == set(expected_modified)


def template_fingerprint() -> str:
    """Bind a reviewed operation identity to its exact provider realization.

    A rejected change set is durable diagnostic evidence, not a reusable
    deployment object. Including the template fingerprint means a corrected
    realization for the same qualified images receives a separate review while
    preserving the rejected operation for investigation.
    """
    return hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()[:12]


def inline_template_body_is_supported(path: Path = TEMPLATE) -> bool:
    """Fail before AWS rejects an oversized ``--template-body`` payload."""
    try:
        size = path.stat().st_size
    except OSError:
        return False
    return 0 < size <= CLOUDFORMATION_INLINE_TEMPLATE_LIMIT_BYTES


def change_name(server: dict, collector: dict, alert_email: str) -> str:
    recipient = hashlib.sha256(alert_email.encode("utf-8")).hexdigest()[:12]
    return f"kanbien-core-platform-observability-{server['image_digest'][7:19]}-{collector['image_digest'][7:19]}-{template_fingerprint()}-{recipient}"


def reconcile(prepare, name: str, expected: dict[str, str], server: dict, collector: dict, alert_email: str, *, expected_added: dict[str, str] = ADDED, expected_modified: dict[str, str] = MODIFIED) -> int:
    observable_expected = {key: value for key, value in expected.items() if key != "ObservabilityAlertEmail"}
    verdict, code = prepare.observe_update(name, observable_expected, lambda value: review(value, name, server, collector, alert_email, expected["ObservabilityCollectorImage"], expected_added=expected_added, expected_modified=expected_modified))
    return report("updated-awaiting-observability-proof" if verdict == "complete" else verdict, code, facts={"change_set": name, "server_image_digest": server["image_digest"], "collector_image_digest": collector["image_digest"]})


def wait_for_review(prepare, name: str, server: dict, collector: dict, alert_email: str, collector_image: str, *, expected_added: dict[str, str] = ADDED, expected_modified: dict[str, str] = MODIFIED) -> tuple[dict | None, str]:
    for attempt in range(6):
        ok, change, code = prepare.aws("cloudformation", "describe-change-set", "--stack-name", STACK, "--change-set-name", name)
        if not ok:
            return None, code
        if isinstance(change, dict) and change.get("Status") == "FAILED":
            return None, "persistence-observability-mvp-change-set-failed"
        if review(change, name, server, collector, alert_email, collector_image, expected_added=expected_added, expected_modified=expected_modified):
            return change, "ok"
        if attempt < 5:
            time.sleep(2)
    return None, "persistence-observability-mvp-change-set-not-reviewable"


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--server-receipt", type=Path)
    parser.add_argument("--collector-receipt", type=Path)
    parser.add_argument("--alert-email")
    parser.add_argument("--repair-readiness-metric-delivery", action="store_true")
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
    if not inline_template_body_is_supported():
        return report("blocked", "persistence-observability-mvp-template-body-too-large")
    name = change_name(server, collector, args.alert_email)
    import subprocess
    collector_gate = subprocess.run(["bash", str(COLLECTOR_GATE), "--json"], capture_output=True, text=True)
    if collector_gate.returncode or not create.package_gates(args.server_receipt) or not prepare.declaration_covered() or not prepare.live_budget()[0] or not prepare.candidate_image(server)[0] or not collector_image_available(prepare, collector):
        return report("blocked", "persistence-observability-mvp-preconditions-not-proven")
    foundation, code = prepare.foundation_outputs()
    if foundation is None:
        return report("blocked", code)
    expected = {"ImageDigest": server["image_digest"], "SupportImageDigest": server["image_digest"], "RestoreVerifierImageDigest": server["image_digest"], "SourceRevision": server["source_revision"], "EnableObservability": "true", "ObservabilityCollectorImage": f"{foundation['RepositoryUri']}@{collector['image_digest']}", "ObservabilityAlertEmail": args.alert_email}
    infrastructure, code = prepare.infrastructure_parameters(foundation)
    if infrastructure is None:
        return report("blocked", code)
    ok, stack, code = prepare.aws("cloudformation", "describe-stacks", "--stack-name", STACK)
    current = parameters(stack) if ok else None
    if current is None or stack.get("Stacks", [{}])[0].get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        return report("blocked", code if not ok else "persistence-observability-mvp-stack-not-healthy")
    expected_added, expected_modified = (REPAIR_ADDED, REPAIR_MODIFIED) if args.repair_readiness_metric_delivery else (ADDED, MODIFIED)
    if args.reconcile:
        return reconcile(prepare, name, expected, server, collector, args.alert_email, expected_added=expected_added, expected_modified=expected_modified)
    observable_expected = {key: value for key, value in expected.items() if key != "ObservabilityAlertEmail"}
    if args.repair_readiness_metric_delivery:
        if current.get("EnableObservability") != "true" or any(current.get(key) != value for key, value in observable_expected.items()):
            return report("blocked", "persistence-observability-mvp-repair-baseline-mismatch")
    elif current.get("EnableObservability") != "false":
        return report("blocked", "persistence-observability-mvp-not-at-unactivated-baseline")
    service_names = [SERVER_SERVICE, COLLECTOR_SERVICE] if args.repair_readiness_metric_delivery else [SERVER_SERVICE]
    ok, observed, code = prepare.aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", *service_names)
    services = observed.get("services") if ok and isinstance(observed, dict) else None
    if not isinstance(services, list) or len(services) != len(service_names) or not all(healthy(item) for item in services):
        return report("blocked", "persistence-observability-mvp-services-not-healthy")
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
    change, code = wait_for_review(prepare, name, server, collector, args.alert_email, expected["ObservabilityCollectorImage"], expected_added=expected_added, expected_modified=expected_modified)
    if change is None:
        return reconcile(prepare, name, expected, server, collector, args.alert_email, expected_added=expected_added, expected_modified=expected_modified)
    if change.get("ExecutionStatus") != "AVAILABLE":
        return reconcile(prepare, name, expected, server, collector, args.alert_email, expected_added=expected_added, expected_modified=expected_modified)
    actual = {item.get("ParameterKey"): item.get("ParameterValue") for item in change.get("Parameters", []) if isinstance(item, dict)}
    if not prepare.update_parameters_match(actual, observable_expected, current):
        return report("blocked", "persistence-observability-mvp-parameters-mismatch")
    ok, _, code = prepare.aws("cloudformation", "execute-change-set", "--stack-name", STACK, "--change-set-name", name)
    if not ok:
        return report("uncertain", code, facts={"change_set": name})
    return reconcile(prepare, name, expected, server, collector, args.alert_email, expected_added=expected_added, expected_modified=expected_modified)


if __name__ == "__main__":
    raise SystemExit(main())
