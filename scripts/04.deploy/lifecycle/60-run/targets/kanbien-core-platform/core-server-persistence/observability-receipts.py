#!/usr/bin/env python3
"""Validate bounded readiness and scheduler alert evidence.

The legacy readiness path retains its three immutable receipts. The separate
scheduler contract returns a source-bound packet to existing acceptance custody;
neither path is an alert journal, mail archive or general execution history.
"""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.kanbien-core-platform.observability-receipts
#   version: 2
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate bounded non-secret readiness and scheduler alert evidence through their separate closed contracts.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.collect-core-server-persistence-acceptance
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py
#   effects: [network, writes-files]
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from functools import lru_cache
import importlib.util
from pathlib import Path
from typing import Any

TARGET = "kanbien-core-platform"
SCOPE = "core-server-persistence"
ROOT = Path(__file__).resolve().parents[7]
EVIDENCE_ROOT = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence"
RECEIPTS = EVIDENCE_ROOT / "observability-receipts"
SCHEMA = "deploy/persistence-observability-receipt/v1"
TYPES = {"readiness-failure-observed", "readiness-alarm-notified", "readiness-recovery-observed"}
ALARM = "kanbien-core-platform-core-server-postgresql-readiness-not-ready-or-silent"
METRIC = "kanbien.core_server.postgresql_readiness"
DIMENSIONS = {
    "target": TARGET,
    "scope": SCOPE,
    "workload": "core-server",
    "dependency": "postgresql",
}
TASK_ARN = re.compile(r"^arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/[0-9a-f]{32}$")
TASK_DEFINITION = re.compile(r"^arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:[1-9][0-9]*$")
SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class ReceiptError(ValueError):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def string(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReceiptError(code)
    return value


def timestamp(value: object, code: str) -> str:
    result = string(value, code)
    if "T" not in result or not (result.endswith("Z") or "+" in result):
        raise ReceiptError(code)
    return result


def source(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256", "task_arn", "task_definition", "image_digest", "result_code"}:
        raise ReceiptError("observability-receipt-source-invalid")
    path = string(value.get("path"), "observability-receipt-source-invalid")
    if Path(path).is_absolute() or not path.startswith("infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts/"):
        raise ReceiptError("observability-receipt-source-invalid")
    if SHA.fullmatch(string(value.get("sha256"), "observability-receipt-source-invalid")) is None or TASK_ARN.fullmatch(string(value.get("task_arn"), "observability-receipt-source-invalid")) is None or TASK_DEFINITION.fullmatch(string(value.get("task_definition"), "observability-receipt-source-invalid")) is None or SHA.fullmatch(string(value.get("image_digest"), "observability-receipt-source-invalid")) is None:
        raise ReceiptError("observability-receipt-source-invalid")
    if value.get("result_code") not in {"KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY", "KANBIEN_CORE_PERSISTENCE_HEALTHY"}:
        raise ReceiptError("observability-receipt-source-invalid")
    return value


def observation(receipt_type: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReceiptError("observability-receipt-observation-invalid")
    if receipt_type == "readiness-alarm-notified":
        required = {"alarm_name", "alarm_state", "alarm_state_updated_at", "subscription_confirmed_at", "operator_delivery_confirmed_at"}
        if set(value) != required or value.get("alarm_name") != ALARM or value.get("alarm_state") != "ALARM":
            raise ReceiptError("observability-receipt-notification-invalid")
        for field in required - {"alarm_name", "alarm_state"}:
            timestamp(value.get(field), "observability-receipt-notification-invalid")
        return value
    required = {"alarm_name", "alarm_state", "alarm_state_updated_at", "metric_name", "dimensions", "metric_value", "metric_observed_at"}
    state = "ALARM" if receipt_type == "readiness-failure-observed" else "OK"
    expected_value = 0 if receipt_type == "readiness-failure-observed" else 1
    if set(value) != required or value.get("alarm_name") != ALARM or value.get("alarm_state") != state or value.get("metric_name") != METRIC or value.get("dimensions") != DIMENSIONS or type(value.get("metric_value")) is not int or value.get("metric_value") != expected_value:
        raise ReceiptError("observability-receipt-observation-invalid")
    timestamp(value.get("alarm_state_updated_at"), "observability-receipt-observation-invalid")
    timestamp(value.get("metric_observed_at"), "observability-receipt-observation-invalid")
    return value


def same_alarm_episode(failure: dict[str, Any], notification: dict[str, Any]) -> bool:
    """Compare instants, not timestamp spelling or an operator attestation."""
    try:
        first = datetime.fromisoformat(failure["alarm_state_updated_at"].replace("Z", "+00:00"))
        second = datetime.fromisoformat(notification["alarm_state_updated_at"].replace("Z", "+00:00"))
        if first.tzinfo is None or second.tzinfo is None:
            raise ValueError()
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise ReceiptError("observability-receipt-alarm-episode-invalid") from error
    return first == second


def validate(receipt: object) -> dict[str, Any]:
    if not isinstance(receipt, dict) or set(receipt) != {"schema", "target", "scope", "receipt_type", "source_proof", "observation", "provenance", "integrity"}:
        raise ReceiptError("observability-receipt-invalid")
    if receipt.get("schema") != SCHEMA or receipt.get("target") != TARGET or receipt.get("scope") != SCOPE or receipt.get("receipt_type") not in TYPES:
        raise ReceiptError("observability-receipt-identity-invalid")
    source(receipt.get("source_proof"))
    observation(receipt["receipt_type"], receipt.get("observation"))
    provenance = receipt.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != {"controller", "collection_method", "collected_at", "evidence_class"} or provenance.get("controller") != "rehearse-observability-readiness" or provenance.get("collection_method") != "cloudwatch-alarm+metric+confirmed-subscription" or provenance.get("evidence_class") not in {"live", "simulated"}:
        raise ReceiptError("observability-receipt-provenance-invalid")
    timestamp(provenance.get("collected_at"), "observability-receipt-provenance-invalid")
    integrity = receipt.get("integrity")
    if not isinstance(integrity, dict) or set(integrity) != {"algorithm", "payload_sha256"} or integrity.get("algorithm") != "sha256" or SHA.fullmatch(str(integrity.get("payload_sha256"))) is None:
        raise ReceiptError("observability-receipt-integrity-invalid")
    if integrity["payload_sha256"] != digest({key: value for key, value in receipt.items() if key != "integrity"}):
        raise ReceiptError("observability-receipt-integrity-mismatch")
    return receipt


def make(*, receipt_type: str, source_proof: dict[str, str], observation_value: dict[str, Any], collected_at: str, evidence_class: str = "live") -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "target": TARGET,
        "scope": SCOPE,
        "receipt_type": receipt_type,
        "source_proof": source_proof,
        "observation": observation_value,
        "provenance": {
            "controller": "rehearse-observability-readiness",
            "collection_method": "cloudwatch-alarm+metric+confirmed-subscription",
            "collected_at": collected_at,
            "evidence_class": evidence_class,
        },
    }
    body["integrity"] = {"algorithm": "sha256", "payload_sha256": digest(body)}
    return validate(body)


def persist(receipt: dict[str, Any]) -> Path:
    value = validate(receipt)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    suffix = value["integrity"]["payload_sha256"][7:19]
    destination = RECEIPTS / f"{value['receipt_type']}-{suffix}.json"
    rendered = json.dumps(value, sort_keys=True, indent=2) + "\n"
    if destination.exists():
        try:
            existing = validate(json.loads(destination.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, ReceiptError) as error:
            raise ReceiptError("observability-receipt-existing-invalid") from error
        if existing != value:
            raise ReceiptError("observability-receipt-conflict")
        return destination
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RECEIPTS, prefix=f".{destination.name}.", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, destination)
    return destination


@lru_cache(maxsize=1)
def scheduling_runtime():
    """Reuse actual runtime/original-Invoke readers, never a second log parser."""
    path = ROOT / "scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/proof.py"
    specification = importlib.util.spec_from_file_location("observability_scheduling_runtime", path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def scheduling_require(condition, code):
    if not condition:
        raise ReceiptError("scheduling-alert-" + code)


def scheduling_time(value):
    if isinstance(value, datetime):
        scheduling_require(value.tzinfo is not None, "time-invalid")
        value = value.astimezone(timezone.utc).isoformat()
    scheduling_require(isinstance(value, str), "time-invalid")
    try: parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: raise ReceiptError("scheduling-alert-time-invalid") from None
    scheduling_require(parsed.tzinfo is not None, "time-invalid")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def scheduling_expected(expected):
    scheduling_require(isinstance(expected, dict) and set(expected) == {"scope", "source_revision", "version_arn", "image_uri", "log_group", "topic_arn"}
        and expected["scope"] in {"core-server-persistence", "entity-smoke"}, "selection-invalid")
    topic = re.fullmatch(r"arn:aws:sns:eu-west-1:([0-9]{12}):kanbien-core-platform-observability-alerts", str(expected["topic_arn"]))
    scheduling_require(topic is not None and re.fullmatch(r"[a-f0-9]{40}", str(expected["source_revision"]))
        and re.fullmatch(r"arn:aws:lambda:eu-west-1:" + topic.group(1) + r":function:kc-" + expected["scope"] + r"-schedule-dispatch:[1-9][0-9]*", str(expected["version_arn"]))
        and re.fullmatch(topic.group(1) + r"\.dkr\.ecr\.eu-west-1\.amazonaws\.com/[a-z0-9][a-z0-9/_-]{0,255}@sha256:[a-f0-9]{64}", str(expected["image_uri"]))
        and expected["log_group"] == "/aws/lambda/kanbien-core-platform/" + expected["scope"] + "/scheduling", "selection-invalid")
    return {"purpose": "dispatch", **{key: expected[key] for key in ("source_revision", "version_arn", "image_uri", "log_group")}}


def scheduling_subscriptions(provider, topic):
    runtime = scheduling_runtime()
    rows = runtime.ADMISSION.collection(provider, "sns", "list-subscriptions-by-topic", "Subscriptions", TopicArn=topic)
    scheduling_require(len(rows) <= 20 and all(isinstance(row, dict) for row in rows), "subscription-inventory-invalid")
    confirmed = []
    for row in rows:
        if row.get("Protocol") != "email" or not isinstance(row.get("SubscriptionArn"), str) or not row["SubscriptionArn"].startswith(topic + ":"): continue
        value = provider("sns", "get-subscription-attributes", SubscriptionArn=row["SubscriptionArn"]).get("Attributes", {})
        if isinstance(value, dict) and value.get("TopicArn") == topic and value.get("Protocol") == "email" and value.get("PendingConfirmation") == "false":
            confirmed.append({"protocol": "email", "subscription_sha256": hashlib.sha256(row["SubscriptionArn"].encode()).hexdigest()})
    scheduling_require(0 < len(confirmed) <= 20 and len({row["subscription_sha256"] for row in confirmed}) == len(confirmed), "confirmed-subscription-required")
    return sorted(confirmed, key=lambda row: row["subscription_sha256"])


def scheduling_history(provider, *, alarm_name, topic, started_at, ended_at):
    """Retain bounded machine facts only, excluding reasons and message content."""
    runtime = scheduling_runtime()
    rows = runtime.ADMISSION.collection(provider, "cloudwatch", "describe-alarm-history", "AlarmHistoryItems",
        AlarmName=alarm_name, StartDate=started_at, EndDate=ended_at, ScanBy="TimestampAscending", MaxRecords=100)
    scheduling_require(len(rows) <= 100, "history-too-large")
    states, actions = [], []
    for row in rows:
        scheduling_require(isinstance(row, dict), "history-invalid")
        scheduling_require(row.get("AlarmName") == alarm_name and row.get("AlarmType", "MetricAlarm") == "MetricAlarm", "history-alarm-mismatch")
        kind = row.get("HistoryItemType")
        if kind not in {"StateUpdate", "Action"}: continue
        try: data = json.loads(row.get("HistoryData", ""))
        except (ValueError, TypeError): raise ReceiptError("scheduling-alert-history-invalid") from None
        scheduling_require(isinstance(data, dict), "history-invalid")
        stamp = scheduling_time(row.get("Timestamp"))
        if kind == "StateUpdate":
            scheduling_require(data.get("version") == "1.0" and isinstance(data.get("oldState"), dict)
                and isinstance(data.get("newState"), dict), "history-version-unrecognized")
            old, new = data.get("oldState", {}).get("stateValue"), data.get("newState", {}).get("stateValue")
            scheduling_require(old in {"OK", "ALARM", "INSUFFICIENT_DATA"} and new in {"OK", "ALARM", "INSUFFICIENT_DATA"}, "history-state-unrecognized")
            states.append({"at": stamp, "old": old, "new": new})
        else:
            scheduling_require(data.get("actionState") == "Succeeded" and data.get("notificationResource") == topic, "notification-action-unconfirmed")
            epoch = data.get("stateUpdateTimestamp")
            scheduling_require(type(epoch) is int and 946684800000 <= epoch < 4102444800000, "history-action-time-invalid")
            episode = datetime.fromtimestamp(epoch / 1000, timezone.utc)
            actions.append({"at": stamp, "episode_at": scheduling_time(episode), "topic_arn": topic, "status": "Succeeded"})
    return {"states": states, "actions": actions}


def capture_scheduling_alert(provider, *, expected, failure, recovery_window, started_at, ended_at):
    """Observe only. The caller first authenticates the original M6 fault effect."""
    runtime, selected = scheduling_runtime(), scheduling_expected(expected)
    control = runtime.control_owner()
    start, end = map(runtime.ADMISSION.utc, (started_at, ended_at))
    scheduling_require(0 < (end - start).total_seconds() <= 3600 and end <= datetime.now(timezone.utc), "window-invalid")
    scheduling_require(isinstance(failure, dict) and set(failure) == {"operation_id", "request_id", "invoked_at", "request_sha256"}, "original-failure-invalid")
    invocation = control.capture_failed_invocation(provider, {"expected": {"runtime": selected}},
        {"operation_id": failure["operation_id"], "reserved_at": failure["invoked_at"]})
    function = runtime.runtime_function(provider("lambda", "get-function", FunctionName=expected["version_arn"]), selected)
    alarm_name = "kanbien-core-platform-" + expected["scope"] + "-scheduling-dispatch-errors"
    rows = provider("cloudwatch", "describe-alarms", AlarmNames=[alarm_name]).get("MetricAlarms", [])
    scheduling_require(isinstance(rows, list) and len(rows) == 1, "alarm-unavailable")
    alarm = rows[0]
    fields = ("AlarmName", "Namespace", "MetricName", "Dimensions", "Statistic", "Period", "EvaluationPeriods", "Threshold",
        "ComparisonOperator", "TreatMissingData", "AlarmActions", "OKActions", "StateValue")
    selected_alarm = {key: alarm.get(key) for key in fields}
    selected_alarm["ActionsEnabled"] = alarm.get("ActionsEnabled")
    dimensions = alarm.get("Dimensions")
    scheduling_require(isinstance(dimensions, list) and all(isinstance(row, dict) and set(row) == {"Name", "Value"}
        and isinstance(row["Name"], str) and isinstance(row["Value"], str) for row in dimensions), "alarm-policy-mismatch")
    selected_alarm["Dimensions"] = sorted(dimensions, key=lambda row: row["Name"])
    selected_alarm["StateUpdatedTimestamp"] = scheduling_time(alarm.get("StateUpdatedTimestamp"))
    function_name = expected["version_arn"].split(":function:")[1].rsplit(":", 1)[0]
    dimensions = [{"Name": "FunctionName", "Value": function_name}, {"Name": "Resource", "Value": expected["version_arn"].split(":function:")[1]}]
    result = provider("cloudwatch", "get-metric-statistics", Namespace="AWS/Lambda", MetricName="Errors", Dimensions=dimensions,
        StartTime=started_at, EndTime=ended_at, Period=60, Statistics=["Sum"], Unit="Count")
    points = result.get("Datapoints", [])
    scheduling_require(isinstance(points, list) and 1 <= len(points) <= 60, "error-signal-missing")
    metrics = [{"at": scheduling_time(row.get("Timestamp")), "sum": row.get("Sum")} for row in points]
    packet = {"schema": "deploy/scheduling-alert-observation/v1", "expected": expected, "failure": failure,
        "invocation": invocation, "function": function, "recovery_window": recovery_window,
        "started_at": started_at, "ended_at": ended_at, "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "alarm": selected_alarm, "metrics": metrics,
        "history": scheduling_history(provider, alarm_name=alarm_name, topic=expected["topic_arn"], started_at=started_at, ended_at=ended_at),
        "subscriptions": scheduling_subscriptions(provider, expected["topic_arn"]), "notification": None}
    validate_scheduling_alert(packet, expected=expected, failure=failure, require_notification=False)
    return packet


def validate_scheduling_alert(packet, *, expected, failure, require_notification=True):
    """Pure historical replay; selected original effect/material custody is external."""
    try:
        return _validate_scheduling_alert(packet, expected=expected, failure=failure, require_notification=require_notification)
    except ReceiptError:
        raise
    except (KeyError, TypeError, AttributeError, ValueError, OverflowError, RecursionError):
        raise ReceiptError("scheduling-alert-packet-invalid") from None


def _validate_scheduling_alert(packet, *, expected, failure, require_notification):
    runtime, selected = scheduling_runtime(), scheduling_expected(expected)
    scheduling_require(isinstance(packet, dict) and set(packet) == {"schema", "expected", "failure", "invocation", "function", "recovery_window",
        "started_at", "ended_at", "collected_at", "alarm", "metrics", "history", "subscriptions", "notification"}
        and packet["schema"] == "deploy/scheduling-alert-observation/v1" and packet["expected"] == expected and packet["failure"] == failure, "packet-mismatch")
    scheduling_require(isinstance(failure, dict) and set(failure) == {"operation_id", "request_id", "invoked_at", "request_sha256"}
        and isinstance(failure["request_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", failure["request_sha256"])
        and isinstance(failure["operation_id"], str) and re.fullmatch(r"scheduling-proof-[a-f0-9]{32}", failure["operation_id"]), "original-failure-invalid")
    start, end, collected = map(runtime.ADMISSION.utc, (packet["started_at"], packet["ended_at"], packet["collected_at"]))
    invoked = runtime.ADMISSION.utc(scheduling_time(failure["invoked_at"]))
    scheduling_require(0 < (end - start).total_seconds() <= 3600 and start <= invoked < end <= collected, "window-invalid")
    scheduling_require(runtime.runtime_function(packet["function"], selected) == packet["function"], "function-mismatch")
    value = packet["invocation"]
    scheduling_require(isinstance(value, dict) and set(value) == {"log_stream", "marker", "start", "report"}, "invocation-invalid")
    logs = [{"level": "info", "message": "Scheduling proof invocation.", "fields": {"scheduling_invocation": value["marker"]}},
        {"type": "platform.start", "record": value["start"]}, {"type": "platform.report", "record": value["report"]}]
    checked = runtime.control_owner().failed_invocation_evidence(logs, {"expected": {"runtime": selected}},
        {"operation_id": failure["operation_id"], "reserved_at": failure["invoked_at"]}, value["log_stream"])
    scheduling_require(checked == value and value["marker"]["request_id"] == failure["request_id"], "invocation-mismatch")
    recovered = runtime.validate_runtime_window(packet["recovery_window"], expected=selected)
    recoveries = [runtime.ADMISSION.utc(row["observation"]["observed_at"]) for row in recovered
        if row["observation"]["result"]["published"] > 0 and row["observation"]["request_id"] != failure["request_id"]]
    scheduling_require(recoveries and invoked < min(recoveries) < end, "recovered-delivery-missing")
    name = "kanbien-core-platform-" + expected["scope"] + "-scheduling-dispatch-errors"
    resource = expected["version_arn"].split(":function:")[1]
    alarm = packet["alarm"]
    expected_alarm = {"AlarmName": name, "Namespace": "AWS/Lambda", "MetricName": "Errors",
        "Dimensions": [{"Name": "FunctionName", "Value": resource.rsplit(":", 1)[0]}, {"Name": "Resource", "Value": resource}],
        "Statistic": "Sum", "Period": 60, "EvaluationPeriods": 1, "Threshold": 1,
        "ComparisonOperator": "GreaterThanOrEqualToThreshold", "TreatMissingData": "notBreaching",
        "AlarmActions": [expected["topic_arn"]], "OKActions": [expected["topic_arn"]], "StateValue": "OK", "ActionsEnabled": True}
    scheduling_require(isinstance(alarm, dict) and set(alarm) == set(expected_alarm) | {"StateUpdatedTimestamp"}
        and all(alarm[key] == value for key, value in expected_alarm.items())
        and type(alarm["Period"]) is int and type(alarm["EvaluationPeriods"]) is int
        and type(alarm["Threshold"]) in {int, float} and alarm["ActionsEnabled"] is True, "alarm-policy-mismatch")
    history = packet["history"]
    scheduling_require(isinstance(history, dict) and set(history) == {"states", "actions"}
        and isinstance(history["states"], list) and isinstance(history["actions"], list)
        and len(history["states"]) <= 100 and len(history["actions"]) <= 100, "history-invalid")
    for row in history["states"]:
        scheduling_require(isinstance(row, dict) and set(row) == {"at", "old", "new"}
            and row["old"] in {"OK", "ALARM", "INSUFFICIENT_DATA"} and row["new"] in {"OK", "ALARM", "INSUFFICIENT_DATA"}
            and start <= runtime.ADMISSION.utc(row["at"]) < end, "history-invalid")
    alarms = [row for row in history["states"] if row["new"] == "ALARM" and row["old"] != "ALARM" and runtime.ADMISSION.utc(row["at"]) >= invoked]
    scheduling_require(len(alarms) == 1, "alarm-episode-ambiguous")
    episode = alarms[0]["at"]
    recoveries_in_history = [row for row in history["states"] if row["old"] == "ALARM" and row["new"] == "OK"
        and runtime.ADMISSION.utc(row["at"]) > runtime.ADMISSION.utc(episode)]
    scheduling_require(len(recoveries_in_history) == 1 and same_alarm_episode({"alarm_state_updated_at": recoveries_in_history[0]["at"]},
        {"alarm_state_updated_at": alarm["StateUpdatedTimestamp"]}), "alarm-recovery-missing")
    actions = []
    for row in history["actions"]:
        scheduling_require(isinstance(row, dict) and set(row) == {"at", "episode_at", "topic_arn", "status"}
            and row["topic_arn"] == expected["topic_arn"] and row["status"] == "Succeeded"
            and start <= runtime.ADMISSION.utc(row["episode_at"]) <= runtime.ADMISSION.utc(row["at"]) < end, "notification-action-unconfirmed")
        if same_alarm_episode({"alarm_state_updated_at": episode}, {"alarm_state_updated_at": row["episode_at"]}): actions.append(row)
    scheduling_require(actions, "notification-action-missing")
    metrics = packet["metrics"]
    scheduling_require(isinstance(metrics, list) and 1 <= len(metrics) <= 60, "error-signal-missing")
    bins = {}
    for row in metrics:
        scheduling_require(isinstance(row, dict) and set(row) == {"at", "sum"} and type(row["sum"]) in {int, float}
            and 0 <= row["sum"] <= 100 and int(row["sum"]) == row["sum"], "error-signal-invalid")
        stamp = runtime.ADMISSION.utc(row["at"])
        scheduling_require(stamp not in bins and start <= stamp < end and stamp.second == stamp.microsecond == 0, "error-signal-invalid")
        bins[stamp] = row["sum"]
    scheduling_require(any(total > 0 and invoked.replace(second=0, microsecond=0) <= stamp <= runtime.ADMISSION.utc(episode)
        for stamp, total in bins.items()), "original-error-signal-missing")
    subscriptions = packet["subscriptions"]
    scheduling_require(isinstance(subscriptions, list) and 0 < len(subscriptions) <= 20
        and all(isinstance(row, dict) and set(row) == {"protocol", "subscription_sha256"} and row["protocol"] == "email"
            and isinstance(row["subscription_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", row["subscription_sha256"]) for row in subscriptions)
        and len({row["subscription_sha256"] for row in subscriptions}) == len(subscriptions), "confirmed-subscription-required")
    notification = packet["notification"]
    if notification is None:
        scheduling_require(not require_notification, "human-delivery-confirmation-required")
    else:
        scheduling_require(isinstance(notification, dict) and set(notification) == {"alarm_state_updated_at", "operator_delivery_confirmed_at", "recorded_at"}
            and same_alarm_episode({"alarm_state_updated_at": episode}, notification)
            and runtime.ADMISSION.utc(episode) <= runtime.ADMISSION.utc(notification["operator_delivery_confirmed_at"])
                <= runtime.ADMISSION.utc(notification["recorded_at"])
            and collected <= runtime.ADMISSION.utc(notification["recorded_at"]), "human-delivery-confirmation-invalid")
    return {"scope": expected["scope"], "source_revision": expected["source_revision"], "function_arn": expected["version_arn"],
        "request_id": failure["request_id"], "alarm_state_updated_at": episode, "notification_confirmed": notification is not None,
        "recovered_at": recoveries_in_history[0]["at"], "packet_sha256": digest(packet)}


def confirm_scheduling_alert(provider, packet, *, expected, failure, operator_delivery_confirmed_at, recorded_at):
    """Only the owned operator-confirmation route calls this; never infer delivery."""
    checked = validate_scheduling_alert(packet, expected=expected, failure=failure, require_notification=False)
    scheduling_require(packet["notification"] is None, "notification-already-recorded")
    scheduling_require(scheduling_subscriptions(provider, expected["topic_arn"]) == packet["subscriptions"], "subscription-changed")
    value = {**packet, "notification": {"alarm_state_updated_at": checked["alarm_state_updated_at"],
        "operator_delivery_confirmed_at": scheduling_time(operator_delivery_confirmed_at), "recorded_at": scheduling_time(recorded_at)}}
    validate_scheduling_alert(value, expected=expected, failure=failure)
    return value
