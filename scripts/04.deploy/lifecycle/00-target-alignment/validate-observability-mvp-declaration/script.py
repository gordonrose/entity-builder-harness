#!/usr/bin/env python3
"""Fail closed on the first core-server-persistence observability MVP contract."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-core-server-persistence-observability-mvp
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Check the closed readiness-observation event, bounded metric catalogue, collector dependency, and two alarm policies before a target mutation.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.core-platform-target-declaration
#     path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh
#   - id: deploy.command.kanbien-core-platform.collect-persistence-acceptance-evidence
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.sh
#   effects: [read-only]
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

TARGET, SCOPE = "kanbien-core-platform", "core-server-persistence"
ROOT = Path(__file__).resolve().parents[5]


class Failure(Exception):
    def __init__(self, code: str) -> None:
        self.code = code


def document(path: Path, code: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise Failure(code) from error
    if not isinstance(value, dict):
        raise Failure(code)
    return value


def mapping(value: object, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Failure(code)
    return value


def named(items: object, code: str) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        raise Failure(code)
    result = {item.get("id"): item for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)}
    if len(result) != len(items):
        raise Failure(code)
    return result


def contains_recipient(value: object) -> bool:
    if isinstance(value, dict):
        return any(key in {"recipient", "email", "endpoint", "address"} or contains_recipient(item) for key, item in value.items())
    if isinstance(value, list):
        return any(contains_recipient(item) for item in value)
    return False


def check(root: Path) -> None:
    declaration = document(root / "20-scopes" / SCOPE / "00-declaration" / "declaration-contract.yml", "observability-scope-contract-unreadable")
    observability = mapping(declaration.get("observability_mvp"), "observability-declaration-missing")
    if observability.get("declaration_schema") != "deploy/readiness-observability-mvp/v1" or observability.get("status") != "dedicated-collector-composed-live-proof-pending" or observability.get("owner") != "observability-owner":
        raise Failure("observability-declaration-invalid")
    envelope = mapping(observability.get("event_envelope"), "observability-event-envelope-invalid")
    if envelope.get("owner") != "platform-contracts" or envelope.get("type") != "dependency.readiness-observed" or envelope.get("code_owner") != "platform-observability" or envelope.get("raw_error_fields") != "prohibited" or envelope.get("closed_fields") != ["event_type", "target", "scope", "workload", "dependency", "readiness", "observed_at", "diagnostic_code"]:
        raise Failure("observability-event-envelope-invalid")
    observation = mapping(observability.get("readiness_observation"), "observability-readiness-observation-invalid")
    if observation.get("workload") != "core-server" or observation.get("dependency") != "postgresql" or observation.get("producer") != "core-server-process-independent-of-request-traffic" or observation.get("cadence_seconds") != 30 or observation.get("timeout_seconds") != 5 or observation.get("stale_after_seconds") != 180:
        raise Failure("observability-readiness-observation-invalid")
    codes = observation.get("not_ready_codes")
    if not isinstance(codes, list) or set(codes) != {"persistence.transport-unavailable", "persistence.credential-rejected", "persistence.trust-validation-failed", "persistence.schema-incompatible", "persistence.unclassified-failure"}:
        raise Failure("observability-readiness-code-policy-invalid")
    catalogue = mapping(observability.get("metric_catalogue"), "observability-metric-catalogue-invalid")
    application = named(catalogue.get("application"), "observability-metric-catalogue-invalid")
    native = named(catalogue.get("rds_native"), "observability-metric-catalogue-invalid")
    app = application.get("core-server-postgresql-readiness")
    if app is None or app.get("source") != "application-observer" or app.get("source_metric") != "platform.dependency.readiness" or app.get("kind") != "gauge" or app.get("dimensions") != ["target", "scope", "workload", "dependency", "readiness"] or app.get("cardinality_limit") != 16:
        raise Failure("observability-application-metric-invalid")
    expected_rds = {"postgresql-free-storage": "FreeStorageSpace", "postgresql-database-connections": "DatabaseConnections", "postgresql-cpu-utilization": "CPUUtilization"}
    if set(native) != set(expected_rds) or any(item.get("source") != "rds-native" or item.get("namespace") != "AWS/RDS" or item.get("metric") != expected_rds[item_id] for item_id, item in native.items()):
        raise Failure("observability-rds-metric-catalogue-invalid")
    collector = mapping(observability.get("collector"), "observability-collector-invalid")
    if collector.get("runtime_dependency") != "dedicated-private-otel-collector-service" or collector.get("adapter") != "@kanbien/platform-adapter-aws-observability-cloudwatch" or collector.get("endpoint") != "http://observability-collector.kanbien-core-platform.internal:4318/v1/metrics" or collector.get("configuration_delivery") != "target-owned-ssm-parameter-non-secret" or collector.get("activation_control") != "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-observability-mvp-surface/script.sh" or collector.get("deployment_status") != "governed-private-service-update-pending-live-proof" or collector.get("prohibited_topology") != "task-local-sidecar-sharing-server-task-role" or collector.get("identity_boundary") != "separate-collector-task-role-no-rds-connect" or collector.get("network_boundary") != "server-to-collector-otlp-4318-only-collector-to-private-aws-endpoints-443-only":
        raise Failure("observability-collector-invalid")
    if not (ROOT / collector["activation_control"]).is_file():
        raise Failure("observability-collector-activation-control-unavailable")
    alarms = mapping(observability.get("alarms"), "observability-alarm-policy-invalid")
    if contains_recipient(alarms):
        raise Failure("observability-notification-recipient-prohibited")
    alarm_definitions = named(alarms.get("definitions"), "observability-alarm-policy-invalid")
    readiness_alarm = alarm_definitions.get("core-server-postgresql-readiness-not-ready-or-silent")
    storage_alarm = alarm_definitions.get("postgresql-free-storage-low")
    if len(alarm_definitions) != 2 or readiness_alarm is None or storage_alarm is None or readiness_alarm.get("source") != "application" or readiness_alarm.get("treat_missing_data") != "breaching" or storage_alarm.get("source") != "rds-native" or storage_alarm.get("treat_missing_data") != "not-breaching":
        raise Failure("observability-alarm-policy-invalid")
    acceptance = mapping(observability.get("acceptance"), "observability-acceptance-invalid")
    if acceptance.get("collector") != "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.sh" or acceptance.get("receipt_location") != "30-release-evidence/observability-receipts" or acceptance.get("required_receipts") != ["readiness-failure-observed", "readiness-alarm-notified", "readiness-recovery-observed"] or acceptance.get("status") != "required-before-observability-mvp-acceptance":
        raise Failure("observability-acceptance-invalid")
    foundation = document(root / "10-foundation" / "observability.yml", "observability-foundation-unreadable")
    if foundation.get("schema") != "deploy/observability-foundation/v1" or foundation.get("target") != TARGET or foundation.get("status") != "local-contract-validated-live-proof-required" or contains_recipient(foundation):
        raise Failure("observability-foundation-invalid")
    collector_contract = document(
        root.parent.parent / "image" / "core-server-persistence-observability-collector" / "image-contract.yml",
        "observability-collector-package-contract-unreadable",
    )
    collector_source = mapping(collector_contract.get("source"), "observability-collector-package-contract-invalid")
    collector_upstream = mapping(collector_source.get("upstream_release"), "observability-collector-package-contract-invalid")
    collector_builder = mapping(collector_source.get("builder_image"), "observability-collector-package-contract-invalid")
    collector_files = mapping(collector_source.get("source_files"), "observability-collector-package-contract-invalid")
    if (
        collector_contract.get("schema") != "deploy/collector-image-contract/v1"
        or collector_contract.get("target") != TARGET
        or collector_contract.get("scope") != SCOPE
        or collector_contract.get("candidate_id") != "observability-collector"
        or collector_contract.get("package_contract_id") != "core-server-persistence-observability-collector-image"
        or collector_contract.get("program_id") != "kanbien-observability-collector"
        or collector_source.get("kind") != "minimal-custom-collector-build"
        or collector_upstream != {"repository": "open-telemetry/opentelemetry-collector-releases", "version": "v0.163.0", "contrib_manifest_sha256": "0bd72a020e0b8414c85df56fd5dcc1ebd05f160a8bbe03f8fb2c53a1248218e8"}
        or collector_builder != {"reference": "docker.io/library/golang@sha256:27f2d3b83cfc5803c8078f8e730af0f7c431bf067afaec8f60a36fb763187cba", "go_version": "1.26.10"}
        or collector_files != {"dockerfile": "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/Dockerfile", "component_manifest": "infra/04.deploy/03.product/image/core-server-persistence-observability-collector/builder-config.yaml"}
        or collector_source.get("selected_components") != ["otlp-http-receiver", "memory-limiter", "batch", "aws-emf-exporter", "health-check"]
        or collector_source.get("identity_proof") != "reviewed-upstream-release-manifest-and-pinned-builder-image"
        or mapping(collector_contract.get("destination"), "observability-collector-package-contract-invalid").get("selection") != "private-ecr-immutable-digest"
        or mapping(collector_contract.get("destination"), "observability-collector-package-contract-invalid").get("precondition") != "exact-qualified-archive-must-pass-unprivileged-scan-before-private-publication"
        or mapping(collector_contract.get("runtime"), "observability-collector-package-contract-invalid").get("exporter") != "aws-emf-cloudwatch-logs"
        or mapping(collector_contract.get("runtime"), "observability-collector-package-contract-invalid").get("receiver") != "otlp-http-private-service-4318"
    ):
        raise Failure("observability-collector-package-contract-invalid")
    template = (root / "30-provider-realization/aws/cloudformation/core-server-persistence.yml").read_text(encoding="utf-8")
    # Observability is an independently activated target concern.  Its
    # implementation must remain complete and conditionally composed, but a
    # database-permission transition must not claim notification delivery or
    # couple its recovery to collector activation.
    required_template_text = [
        "EnableObservability: { Type: String, Default: 'false', AllowedValues: ['false', 'true'] }", "ObservabilityEnabled: !Equals [!Ref EnableObservability, 'true']",
        "ObservabilityCollectorImage:", "ObservabilityAlertEmail:", "ObservabilityCollectorConfiguration:", "Condition: ObservabilityEnabled", "awsemf:", "dimension_rollup_option: NoDimensionRollup", "ObservabilityAlarmTopic:", "ObservabilityAlertSubscription:", "ObservabilityCollectorSecurityGroup:", "ObservabilityCollectorIngressFromServer:", "ServerObservabilityCollectorEgress:", "ObservabilityCollectorExecutionRole:", "ObservabilityCollectorTaskRole:", "ObservabilityCollectorTaskDefinition:", "ObservabilityCollectorService:", "TaskRoleArn: !GetAtt ObservabilityCollectorTaskRole.Arn", "ServiceRegistries: [{ RegistryArn: !GetAtt ObservabilityCollectorServiceDiscovery.Arn }]", "http://observability-collector.kanbien-core-platform.internal:4318/v1/metrics", "PLATFORM_OBSERVABILITY_DELIVERY_BOUNDARY, Value: private-collector-service", "PLATFORM_OBSERVABILITY_READINESS_CADENCE_MS", "Value: '30000'", "PLATFORM_OBSERVABILITY_READINESS_TIMEOUT_MS", "Value: '5000'", "PLATFORM_OBSERVABILITY_READINESS_STALE_AFTER_MS", "Value: '180000'", "CoreServerPostgreSqlReadinessAlarm:", "TreatMissingData: breaching", "PersistenceDatabaseFreeStorageAlarm:", "TreatMissingData: notBreaching",
    ]
    server_role = template.split("ServerTaskRole:", 1)[1].split("ObservabilityCollectorExecutionRole:", 1)[0] if "ServerTaskRole:" in template and "ObservabilityCollectorExecutionRole:" in template else ""
    collector_role = template.split("ObservabilityCollectorTaskRole:", 1)[1].split("MigrationExecutionRole:", 1)[0] if "ObservabilityCollectorTaskRole:" in template and "MigrationExecutionRole:" in template else ""
    if not collector_role or any(item not in template for item in required_template_text) or "rds-db:connect" in collector_role or "deliver-reviewed-readiness-metrics" in server_role or "DependsOn: !If [ObservabilityEnabled" in template:
        raise Failure("observability-provider-realization-invalid")


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--target-root", type=Path, default=ROOT / "infra/04.deploy/03.product/targets" / TARGET)
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args()
    try:
        if unknown:
            raise Failure("arguments-invalid")
        check(args.target_root)
        report = {"schema": "deploy/observability-mvp-declaration-report/v1", "target": TARGET, "scope": SCOPE, "verdict": "valid", "findings": []}
        print(json.dumps(report, sort_keys=True))
        return 0
    except Failure as error:
        report = {"schema": "deploy/observability-mvp-declaration-report/v1", "target": TARGET, "scope": SCOPE, "verdict": "invalid", "findings": [{"code": error.code}]}
        print(json.dumps(report, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

