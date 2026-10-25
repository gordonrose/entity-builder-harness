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
    if observability.get("declaration_schema") != "deploy/readiness-observability-mvp/v1" or observability.get("status") != "local-contract-validated-live-proof-required" or observability.get("owner") != "observability-owner":
        raise Failure("observability-declaration-invalid")
    envelope = mapping(observability.get("event_envelope"), "observability-event-envelope-invalid")
    if envelope.get("owner") != "platform-contracts" or envelope.get("type") != "dependency.readiness-observed" or envelope.get("code_owner") != "platform-observability" or envelope.get("raw_error_fields") != "prohibited" or envelope.get("closed_fields") != ["event_type", "target", "scope", "workload", "dependency", "readiness", "observed_at", "diagnostic_code"]:
        raise Failure("observability-event-envelope-invalid")
    observation = mapping(observability.get("readiness_observation"), "observability-readiness-observation-invalid")
    if observation.get("workload") != "core-server" or observation.get("dependency") != "postgresql" or observation.get("producer") != "core-server-process-independent-of-request-traffic" or observation.get("cadence_seconds") != 30 or observation.get("timeout_seconds") != 5 or observation.get("stale_after_seconds") != 180:
        raise Failure("observability-readiness-observation-invalid")
    codes = observation.get("not_ready_codes")
    if not isinstance(codes, list) or set(codes) != {"persistence.transport-unavailable", "persistence.credential-rejected", "persistence.trust-validation-failed", "persistence.schema-incompatible"}:
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
    if collector.get("runtime_dependency") != "task-local-otel-collector" or collector.get("adapter") != "@kanbien/platform-adapter-aws-observability-cloudwatch" or collector.get("endpoint") != "http://127.0.0.1:4318/v1/metrics" or collector.get("configuration_delivery") != "target-owned-ssm-parameter-non-secret":
        raise Failure("observability-collector-invalid")
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
    template = (root / "30-provider-realization/aws/cloudformation/core-server-persistence.yml").read_text(encoding="utf-8")
    required_template_text = [
        "ObservabilityCollectorImage:", "ObservabilityAlarmTopicArn:", "MonitoringEndpoint:", "ObservabilityCollectorConfiguration:", "ServerTaskRole:", "TaskRoleArn: !GetAtt ServerTaskRole.Arn", "Name: observability-collector", "PLATFORM_OBSERVABILITY_READINESS_CADENCE_MS", "Value: '30000'", "PLATFORM_OBSERVABILITY_READINESS_TIMEOUT_MS", "Value: '5000'", "PLATFORM_OBSERVABILITY_READINESS_STALE_AFTER_MS", "Value: '180000'", "CoreServerPostgreSqlReadinessAlarm:", "TreatMissingData: breaching", "PersistenceDatabaseFreeStorageAlarm:", "TreatMissingData: notBreaching",
    ]
    if any(item not in template for item in required_template_text):
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

