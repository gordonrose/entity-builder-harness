#!/usr/bin/env python3
"""Exercise and retain the bounded PostgreSQL-readiness alert path.

The controller deliberately has three resumable stages. It retains provider
facts at each completed stage, so an ECS stopped-task retention window cannot
turn a completed observation into a reason to repeat an IAM revocation.
"""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-observability-readiness
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Retain the first governed PostgreSQL readiness failure, notification and recovery observations without logging secrets or notification content.
#   portability: { class: internal, targets: [] }
#   argument_validation:
#     flag: --validate-arguments
#     effects: [read-only]
#   used_by:
#   - id: deploy.workflow.kanbien-core-platform-core-server-persistence
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/core-server-persistence/create-and-verify-private-postgresql-candidate.md
#   - id: deploy.command.kanbien-core-platform.rehearse-observability-readiness.wrapper
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/script.sh
#   effects: [network, writes-files]
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[8]
PROFILE, REGION = "kanbien-dev", "eu-west-1"
EVIDENCE_ROOT = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence"
PROOF_ROOT = EVIDENCE_ROOT / "proof-receipts"


class RehearsalFailure(ValueError):
    pass


def load(relative: str, name: str):
    source = ROOT / relative
    specification = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(specification)
    assert specification and specification.loader
    specification.loader.exec_module(module)
    return module


def receipts():
    return load("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts.py", "observability_receipts")


def task_receipts():
    return load("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py", "persistence_proof_receipts")


def succession():
    return load("scripts/04.deploy/lifecycle/60-run/release-succession/script.py", "release_succession")


def iso(value: object, code: str) -> str:
    if not isinstance(value, str):
        raise RehearsalFailure(code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RehearsalFailure(code) from error
    if parsed.tzinfo is None or parsed.astimezone(timezone.utc) > datetime.now(timezone.utc) + timedelta(minutes=1):
        raise RehearsalFailure(code)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def aws(*parts: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["aws", *parts, "--profile", PROFILE, "--region", REGION, "--output", "json"],
            capture_output=True, text=True, timeout=30, check=False,
            env={**os.environ, "AWS_PAGER": ""},
        )
    except subprocess.TimeoutExpired as error:
        raise RehearsalFailure("observability-rehearsal-provider-observation-timeout") from error
    if completed.returncode:
        detail = completed.stderr.lower()
        raise RehearsalFailure("observability-rehearsal-provider-access-denied" if "accessdenied" in detail or "not authorized" in detail else "observability-rehearsal-provider-observation-failed")
    try:
        value = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as error:
        raise RehearsalFailure("observability-rehearsal-provider-response-invalid") from error
    if not isinstance(value, dict):
        raise RehearsalFailure("observability-rehearsal-provider-response-invalid")
    return value


def last_report(text: str) -> dict[str, Any] | None:
    for line in reversed(text.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get("verdict"), str):
            return value
    return None


def lifecycle(receipt: Path, operation: str) -> dict[str, Any]:
    command = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh"
    try:
        completed = subprocess.run(["bash", str(command), "--receipt", str(receipt), "--operation", operation, "--json"], cwd=ROOT, capture_output=True, text=True, timeout=420, check=False)
    except subprocess.TimeoutExpired as error:
        raise RehearsalFailure("observability-rehearsal-lifecycle-outcome-uncertain") from error
    report = last_report(completed.stdout) or last_report(completed.stderr)
    if completed.returncode or not isinstance(report, dict):
        raise RehearsalFailure("observability-rehearsal-lifecycle-not-complete")
    return report


def candidate(receipt: Path) -> str:
    prepare = load("scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py", "persistence_prepare")
    value = prepare.validate_receipt(receipt)
    digest = value.get("image_digest") if isinstance(value, dict) else None
    if not isinstance(digest, str):
        raise RehearsalFailure("observability-rehearsal-candidate-receipt-invalid")
    return digest


def source_proof(path_value: str, result_code: str, image_digest: str) -> dict[str, str]:
    path = Path(path_value).resolve()
    if PROOF_ROOT.resolve() not in path.parents:
        raise RehearsalFailure("observability-rehearsal-source-proof-invalid")
    try:
        raw = path.read_bytes()
        proof = task_receipts().validate(json.loads(raw.decode("utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise RehearsalFailure("observability-rehearsal-source-proof-invalid") from error
    task = proof.get("task") if isinstance(proof, dict) else None
    if not isinstance(task, dict) or proof.get("proof_type") != "verifier" or task.get("result_code") != result_code or task.get("image_digest") != image_digest or proof.get("provenance", {}).get("evidence_class", "live") != "live":
        raise RehearsalFailure("observability-rehearsal-source-proof-invalid")
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError as error:
        raise RehearsalFailure("observability-rehearsal-source-proof-invalid") from error
    return {"path": relative, "sha256": succession().sha256_bytes(raw), "task_arn": task["arn"], "task_definition": task["definition"], "image_digest": task["image_digest"], "result_code": task["result_code"]}


def retained_source(result_code: str, image_digest: str, *, not_before: datetime | None = None) -> dict[str, str] | None:
    """Reuse a freshly retained verifier proof after controller interruption.

    This is intentionally narrow: it will not infer a provider outcome from a
    log, and it will not reuse an old unready result to start a new rehearsal.
    A caller still obtains a current CloudWatch metric and alarm observation.
    """
    matches: list[tuple[datetime, Path]] = []
    try:
        paths = sorted(PROOF_ROOT.glob("*.json"))
    except OSError as error:
        raise RehearsalFailure("observability-rehearsal-source-proof-unavailable") from error
    for path in paths:
        try:
            proof = task_receipts().validate(json.loads(path.read_text(encoding="utf-8")))
            task = proof["task"]
            completed = datetime.fromisoformat(task["stopped_at"].replace("Z", "+00:00")).astimezone(timezone.utc)
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, ValueError):
            continue
        if proof.get("proof_type") == "verifier" and proof.get("provenance", {}).get("evidence_class", "live") == "live" and task.get("result_code") == result_code and task.get("image_digest") == image_digest and (not_before is None or completed >= not_before):
            matches.append((completed, path))
    if not matches:
        return None
    _, selected = max(matches, key=lambda item: item[0])
    return source_proof(str(selected), result_code, image_digest)


def alarm(expected_state: str) -> dict[str, str]:
    module = receipts()
    response = aws("cloudwatch", "describe-alarms", "--alarm-names", module.ALARM)
    alarms = response.get("MetricAlarms")
    item = alarms[0] if isinstance(alarms, list) and len(alarms) == 1 and isinstance(alarms[0], dict) else None
    if item is None or item.get("AlarmName") != module.ALARM or item.get("StateValue") != expected_state:
        raise RehearsalFailure("observability-rehearsal-alarm-state-not-observed")
    return {"alarm_name": module.ALARM, "alarm_state": expected_state, "alarm_state_updated_at": iso(item.get("StateUpdatedTimestamp"), "observability-rehearsal-alarm-timestamp-invalid")}


def metric(expected_value: int) -> dict[str, Any]:
    module = receipts()
    now = datetime.now(timezone.utc)
    query = {"Id": "readiness", "MetricStat": {"Metric": {"Namespace": "Kanbien/CorePlatform", "MetricName": module.METRIC, "Dimensions": [{"Name": key, "Value": value} for key, value in module.DIMENSIONS.items()]}, "Period": 60, "Stat": "Minimum"}, "ReturnData": True}
    response = aws("cloudwatch", "get-metric-data", "--metric-data-queries", json.dumps([query], separators=(",", ":")), "--start-time", (now - timedelta(minutes=10)).isoformat().replace("+00:00", "Z"), "--end-time", now.isoformat().replace("+00:00", "Z"), "--scan-by", "TimestampDescending")
    values = response.get("MetricDataResults")
    result = values[0] if isinstance(values, list) and len(values) == 1 and isinstance(values[0], dict) else None
    entries, timestamps = (result.get("Values"), result.get("Timestamps")) if isinstance(result, dict) else (None, None)
    if not isinstance(entries, list) or not isinstance(timestamps, list) or not entries or not timestamps or len(entries) != len(timestamps) or type(entries[0]) not in {int, float} or entries[0] != expected_value:
        raise RehearsalFailure("observability-rehearsal-metric-not-observed")
    observed = iso(timestamps[0], "observability-rehearsal-metric-timestamp-invalid")
    if datetime.fromisoformat(observed.replace("Z", "+00:00")) < now - timedelta(minutes=10):
        raise RehearsalFailure("observability-rehearsal-metric-stale")
    return {"metric_name": module.METRIC, "dimensions": module.DIMENSIONS, "metric_value": expected_value, "metric_observed_at": observed}


def confirmed_subscription() -> bool:
    topic = "arn:aws:sns:eu-west-1:337159794548:kanbien-core-platform-observability-alerts"
    response = aws("sns", "list-subscriptions-by-topic", "--topic-arn", topic)
    values = response.get("Subscriptions")
    return isinstance(values, list) and any(isinstance(item, dict) and item.get("Protocol") == "email" and isinstance(item.get("SubscriptionArn"), str) and item["SubscriptionArn"].startswith("arn:aws:sns:") for item in values)


def receipt_argument(path_value: str, expected_type: str, image_digest: str) -> dict[str, Any]:
    path = Path(path_value).resolve()
    root = EVIDENCE_ROOT / "observability-receipts"
    if root.resolve() not in path.parents:
        raise RehearsalFailure("observability-rehearsal-receipt-argument-invalid")
    try:
        value = receipts().validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise RehearsalFailure("observability-rehearsal-receipt-argument-invalid") from error
    if value["receipt_type"] != expected_type or value["source_proof"]["image_digest"] != image_digest or value["provenance"]["evidence_class"] != "live":
        raise RehearsalFailure("observability-rehearsal-receipt-argument-invalid")
    return value


def persist(receipt_type: str, source: dict[str, str], observation: dict[str, Any]) -> Path:
    module = receipts()
    value = module.make(receipt_type=receipt_type, source_proof=source, observation_value=observation, collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    return module.persist(value)


def report(verdict: str, *codes: str, facts: dict[str, str] | None = None) -> int:
    body: dict[str, Any] = {"schema": "deploy/persistence-observability-rehearsal-report/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence", "verdict": verdict, "findings": [{"code": code} for code in codes]}
    if facts:
        body["facts"] = facts
    print(json.dumps(body, sort_keys=True))
    return 0 if verdict in {"prepared", "recorded"} else 1


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--operation", choices=("prepare-failure", "record-notification", "recover"))
    parser.add_argument("--failure-receipt")
    parser.add_argument("--notification-receipt")
    parser.add_argument("--subscription-confirmed-at")
    parser.add_argument("--operator-delivery-confirmed-at")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    try:
        args, unknown = parser.parse_known_args()
        if unknown or args.receipt is None or args.operation is None:
            raise RehearsalFailure("observability-rehearsal-arguments-invalid")
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []}))
            return 0
        image_digest = candidate(args.receipt)
        if args.operation == "prepare-failure":
            source = retained_source("KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY", image_digest, not_before=datetime.now(timezone.utc) - timedelta(minutes=15))
            if source is None:
                result = lifecycle(args.receipt, "revoke-await-observability")
                if result.get("verdict") != "prepared":
                    raise RehearsalFailure("observability-rehearsal-failure-preparation-not-complete")
                facts = result.get("facts")
                path_value = facts.get("unready_verifier_receipt") if isinstance(facts, dict) else None
                if not isinstance(path_value, str):
                    raise RehearsalFailure("observability-rehearsal-source-proof-missing")
                source = source_proof(path_value, "KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY", image_digest)
            path = persist("readiness-failure-observed", source, {**alarm("ALARM"), **metric(0)})
            return report("prepared", "observability-rehearsal-readiness-failure-observed", facts={"receipt": path.relative_to(ROOT).as_posix()})
        if args.operation == "record-notification":
            if not isinstance(args.failure_receipt, str):
                raise RehearsalFailure("observability-rehearsal-failure-receipt-required")
            failure = receipt_argument(args.failure_receipt, "readiness-failure-observed", image_digest)
            subscription = iso(args.subscription_confirmed_at, "observability-rehearsal-subscription-confirmation-invalid")
            delivery = iso(args.operator_delivery_confirmed_at, "observability-rehearsal-delivery-confirmation-invalid")
            if not confirmed_subscription():
                raise RehearsalFailure("observability-rehearsal-notification-subscription-pending")
            observed_alarm = alarm("ALARM")
            if datetime.fromisoformat(delivery.replace("Z", "+00:00")) < datetime.fromisoformat(observed_alarm["alarm_state_updated_at"].replace("Z", "+00:00")):
                raise RehearsalFailure("observability-rehearsal-delivery-before-alarm")
            path = persist("readiness-alarm-notified", failure["source_proof"], {**observed_alarm, "subscription_confirmed_at": subscription, "operator_delivery_confirmed_at": delivery})
            return report("recorded", "observability-rehearsal-notification-delivery-recorded", facts={"receipt": path.relative_to(ROOT).as_posix()})
        if not isinstance(args.failure_receipt, str) or not isinstance(args.notification_receipt, str):
            raise RehearsalFailure("observability-rehearsal-prerequisite-receipts-required")
        failure = receipt_argument(args.failure_receipt, "readiness-failure-observed", image_digest)
        notification = receipt_argument(args.notification_receipt, "readiness-alarm-notified", image_digest)
        if failure["source_proof"] != notification["source_proof"]:
            raise RehearsalFailure("observability-rehearsal-notification-source-mismatch")
        delivered_after = datetime.fromisoformat(notification["observation"]["operator_delivery_confirmed_at"].replace("Z", "+00:00")).astimezone(timezone.utc)
        source = retained_source("KANBIEN_CORE_PERSISTENCE_HEALTHY", image_digest, not_before=delivered_after)
        if source is None:
            result = lifecycle(args.receipt, "recover-after-revocation")
            if result.get("verdict") != "accepted":
                raise RehearsalFailure("observability-rehearsal-recovery-not-complete")
            facts = result.get("facts")
            path_value = facts.get("ready_verifier_receipt") if isinstance(facts, dict) else None
            if not isinstance(path_value, str):
                raise RehearsalFailure("observability-rehearsal-recovery-source-proof-missing")
            source = source_proof(path_value, "KANBIEN_CORE_PERSISTENCE_HEALTHY", image_digest)
        path = persist("readiness-recovery-observed", source, {**alarm("OK"), **metric(1)})
        return report("recorded", "observability-rehearsal-readiness-recovery-observed", facts={"receipt": path.relative_to(ROOT).as_posix()})
    except (RehearsalFailure, OSError, ValueError, subprocess.SubprocessError) as error:
        return report("blocked", str(error) if isinstance(error, RehearsalFailure) else "observability-rehearsal-malformed-input")


if __name__ == "__main__":
    raise SystemExit(main())
