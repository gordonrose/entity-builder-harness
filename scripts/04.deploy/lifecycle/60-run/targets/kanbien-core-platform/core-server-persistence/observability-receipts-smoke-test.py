#!/usr/bin/env python3
"""Focused offline checks for bounded observability-MVP evidence."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.observability-receipts
#   version: 2
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise integrity, allowlist and persistence rules for readiness-observability receipts.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.test.persistence-acceptance-route
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal/smoke-test.sh
#   effects: [read-only, writes-files]
import copy
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
SOURCE = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts.py"
spec = importlib.util.spec_from_file_location("observability_receipts", SOURCE)
module = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module)

source = {
    "path": "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts/verifier-health-unready-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.json",
    "sha256": "sha256:" + "a" * 64,
    "task_arn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "a" * 32,
    "task_definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:1",
    "image_digest": "sha256:" + "b" * 64,
    "result_code": "KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY",
}
failure_observation = {
    "alarm_name": module.ALARM, "alarm_state": "ALARM", "alarm_state_updated_at": "2026-10-26T12:00:00Z",
    "metric_name": module.METRIC, "dimensions": module.DIMENSIONS, "metric_value": 0, "metric_observed_at": "2026-10-26T11:59:00Z",
}
failure = module.make(receipt_type="readiness-failure-observed", source_proof=source, observation_value=failure_observation, collected_at="2026-10-26T12:00:01Z")
assert module.validate(failure) == failure
notification = module.make(receipt_type="readiness-alarm-notified", source_proof=source, observation_value={"alarm_name": module.ALARM, "alarm_state": "ALARM", "alarm_state_updated_at": "2026-10-26T12:00:00Z", "subscription_confirmed_at": "2026-10-26T11:50:00Z", "operator_delivery_confirmed_at": "2026-10-26T12:01:00Z"}, collected_at="2026-10-26T12:01:01Z")
assert module.validate(notification) == notification
assert module.same_alarm_episode(failure["observation"], notification["observation"])
assert module.same_alarm_episode(failure["observation"], {**notification["observation"], "alarm_state_updated_at": "2026-10-26T13:00:00+01:00"})
assert not module.same_alarm_episode(failure["observation"], {**notification["observation"], "alarm_state_updated_at": "2026-10-26T12:00:01Z"})
recovery_source = {**source, "result_code": "KANBIEN_CORE_PERSISTENCE_HEALTHY"}
recovery = module.make(receipt_type="readiness-recovery-observed", source_proof=recovery_source, observation_value={"alarm_name": module.ALARM, "alarm_state": "OK", "alarm_state_updated_at": "2026-10-26T12:03:00Z", "metric_name": module.METRIC, "dimensions": module.DIMENSIONS, "metric_value": 1, "metric_observed_at": "2026-10-26T12:02:00Z"}, collected_at="2026-10-26T12:03:01Z")
assert module.validate(recovery) == recovery
for broken in (lambda v: v.update(receipt_type="unknown"), lambda v: v["observation"].update(dimensions={}), lambda v: v["observation"].update(provider_message="unsafe"), lambda v: v["source_proof"].update(result_code="OTHER")):
    value = copy.deepcopy(failure); broken(value)
    try: module.validate(value)
    except module.ReceiptError: pass
    else: raise AssertionError("invalid observability receipt passed")
with tempfile.TemporaryDirectory() as directory:
    module.RECEIPTS = Path(directory)
    first = module.persist(failure)
    assert module.persist(failure) == first
    changed = copy.deepcopy(failure); changed["provenance"]["collected_at"] = "2026-10-26T12:00:02Z"; changed["integrity"]["payload_sha256"] = module.digest({key: value for key, value in changed.items() if key != "integrity"})
    assert module.persist(changed) != first
print("observability receipt checks passed")


def scheduling_fixture(scope="entity-smoke"):
    expected = {"scope": scope, "source_revision": "a" * 40,
        "version_arn": "arn:aws:lambda:eu-west-1:123456789012:function:kc-" + scope + "-schedule-dispatch:2",
        "image_uri": "123456789012.dkr.ecr.eu-west-1.amazonaws.com/scheduling@sha256:" + "b" * 64,
        "log_group": "/aws/lambda/kanbien-core-platform/" + scope + "/scheduling",
        "topic_arn": "arn:aws:sns:eu-west-1:123456789012:kanbien-core-platform-observability-alerts"}
    failure = {"operation_id": "scheduling-proof-10000000000040008000000000000001",
        "request_id": "10000000-0000-4000-8000-000000000002", "invoked_at": "2026-11-26T12:00:00Z", "request_sha256": "c" * 64}
    resource = expected["version_arn"].split(":function:")[1]
    stream = "2026/11/26/" + resource.replace(":2", "[2]") + "[controlled]"
    marker = {"schema": "kanbien/scheduling-proof-invocation/v1", "operation_id": "10000000-0000-4000-8000-000000000001",
        "source_revision": expected["source_revision"], "request_id": failure["request_id"], "function_arn": expected["version_arn"], "checked_at": "2026-11-26T12:00:01Z"}
    fault = [{"level": "info", "message": "Scheduling proof invocation.", "fields": {"scheduling_invocation": marker}},
        {"type": "platform.start", "record": {"requestId": failure["request_id"], "version": "2"}},
        {"type": "platform.report", "record": {"requestId": failure["request_id"], "status": "error", "metrics": {"billedDurationMs": 1000, "memorySizeMB": 512}}}]
    recovered_id = "10000000-0000-4000-8000-000000000003"
    recovery = [{"type": "platform.start", "record": {"requestId": recovered_id, "version": "2"}},
        {"level": "info", "message": "Scheduling runtime observation.", "fields": {"scheduling_runtime": {
            "schema": "kanbien/scheduling-runtime-observation/v1", "purpose": "dispatch", "source_revision": expected["source_revision"],
            "function_arn": expected["version_arn"], "request_id": recovered_id, "observed_at": "2026-11-26T12:02:01Z",
            "kind": "dispatch-completed", "trigger": None, "result": {"delivery": {"inspected": 1, "deliveryCreated": 1, "deliveryAlreadyCreated": 0, "notDue": 0},
                "relayAttempts": 2, "published": 1, "stopReason": "idle"}}}},
        {"type": "platform.report", "record": {"requestId": recovered_id, "status": "success", "metrics": {"billedDurationMs": 1250, "memorySizeMB": 512}}}]
    epoch = int(datetime(2026, 11, 26, 12, 2, tzinfo=timezone.utc).timestamp() * 1000)
    recovery_events = [{"eventId": "recover-" + str(index), "logStreamName": stream, "timestamp": epoch + index * 1000, "message": json.dumps(value)} for index, value in enumerate(recovery)]
    function = {"Code": {"ResolvedImageUri": expected["image_uri"]}, "Configuration": {"FunctionArn": expected["version_arn"], "Version": "2", "State": "Active",
        "MemorySize": 512, "Timeout": 60, "Environment": {"Variables": {"PLATFORM_SOURCE_COMMIT_SHA": expected["source_revision"], "PRIVATE_CANARY": "do-not-retain"}},
        "LoggingConfig": {"LogGroup": expected["log_group"], "LogFormat": "JSON"}}}
    alarm_name = "kanbien-core-platform-" + scope + "-scheduling-dispatch-errors"
    alarm = {"AlarmName": alarm_name, "Namespace": "AWS/Lambda", "MetricName": "Errors", "Dimensions": [
        {"Name": "Resource", "Value": resource}, {"Name": "FunctionName", "Value": resource.rsplit(":", 1)[0]}],
        "Statistic": "Sum", "Period": 60, "EvaluationPeriods": 1, "Threshold": 1,
        "ComparisonOperator": "GreaterThanOrEqualToThreshold", "TreatMissingData": "notBreaching", "ActionsEnabled": True,
        "AlarmActions": [expected["topic_arn"]], "OKActions": [expected["topic_arn"]], "StateValue": "OK", "StateUpdatedTimestamp": "2026-11-26T12:03:00Z"}
    history = [{"AlarmName": alarm_name, "AlarmType": "MetricAlarm", "HistoryItemType": "StateUpdate", "Timestamp": at,
        "HistoryData": json.dumps({"version": "1.0", "oldState": {"stateValue": old}, "newState": {"stateValue": new}, "reason": "PRIVATE_CANARY"})}
        for at, old, new in (("2026-11-26T12:01:00Z", "OK", "ALARM"), ("2026-11-26T12:03:00Z", "ALARM", "OK"))]
    history.append({"AlarmName": alarm_name, "AlarmType": "MetricAlarm", "HistoryItemType": "Action", "Timestamp": "2026-11-26T12:01:01Z",
        "HistoryData": json.dumps({"actionState": "Succeeded", "error": None, "muteWindowEndTimestamp": None,
            "notificationResource": expected["topic_arn"], "publishedMessage": "PRIVATE_CANARY",
            "stateUpdateTimestamp": int(datetime(2026, 11, 26, 12, 1, tzinfo=timezone.utc).timestamp() * 1000)})})
    calls = []
    def provider(service, operation, **arguments):
        calls.append((service, operation, arguments))
        if (service, operation) == ("lambda", "get-function"): return copy.deepcopy(function)
        if (service, operation) == ("logs", "filter-log-events"):
            return {"events": [{"logStreamName": stream, "message": json.dumps(fault[0])}] if "filterPattern" in arguments else copy.deepcopy(recovery_events)}
        if (service, operation) == ("logs", "get-log-events"): return {"events": [{"message": json.dumps(value)} for value in fault]}
        if (service, operation) == ("cloudwatch", "describe-alarms"): return {"MetricAlarms": [copy.deepcopy(alarm)]}
        if (service, operation) == ("cloudwatch", "describe-alarm-history"): return {"AlarmHistoryItems": copy.deepcopy(history)}
        if (service, operation) == ("cloudwatch", "get-metric-statistics"): return {"Datapoints": [{"Timestamp": "2026-11-26T12:00:00Z", "Sum": 1.0}]}
        if (service, operation) == ("sns", "list-subscriptions-by-topic"):
            return {"Subscriptions": [{"Protocol": "email", "SubscriptionArn": expected["topic_arn"] + ":owned", "Endpoint": "PRIVATE_CANARY"}]}
        if (service, operation) == ("sns", "get-subscription-attributes"):
            return {"Attributes": {"TopicArn": expected["topic_arn"], "Protocol": "email", "PendingConfirmation": "false", "Endpoint": "PRIVATE_CANARY"}}
        raise AssertionError("unowned provider operation")
    return expected, failure, provider, calls, history


for scope in ("core-server-persistence", "entity-smoke"):
    expected, failure, provider, calls, history = scheduling_fixture(scope)
    runtime = module.scheduling_runtime()
    selected = module.scheduling_expected(expected)
    recovery_window = runtime.capture_runtime_window(provider, expected=selected, started_at="2026-11-26T12:02:00Z", ended_at="2026-11-26T12:03:00Z")
    packet = module.capture_scheduling_alert(provider, expected=expected, failure=failure, recovery_window=recovery_window,
        started_at="2026-11-26T12:00:00Z", ended_at="2026-11-26T12:05:00Z")
    assert "PRIVATE_CANARY" not in json.dumps(packet)
    assert module.validate_scheduling_alert(packet, expected=expected, failure=failure, require_notification=False)["notification_confirmed"] is False
    try: module.validate_scheduling_alert(packet, expected=expected, failure=failure)
    except module.ReceiptError as error: assert str(error) == "scheduling-alert-human-delivery-confirmation-required"
    else: raise AssertionError("SNS publish alone became human delivery")
    confirmed = module.confirm_scheduling_alert(provider, packet, expected=expected, failure=failure,
        operator_delivery_confirmed_at="2026-11-26T12:01:30Z", recorded_at=datetime.now(timezone.utc).isoformat())
    assert packet["notification"] is None
    call_count = len(calls)
    assert module.validate_scheduling_alert(json.loads(json.dumps(confirmed)), expected=expected, failure=failure)["notification_confirmed"] is True
    assert len(calls) == call_count, "historical replay must not reread expiring provider state"
    def pending(service, operation, **arguments):
        value = provider(service, operation, **arguments)
        if (service, operation) == ("sns", "get-subscription-attributes"): value["Attributes"]["PendingConfirmation"] = "true"
        return value
    try: module.confirm_scheduling_alert(pending, packet, expected=expected, failure=failure,
        operator_delivery_confirmed_at="2026-11-26T12:01:30Z", recorded_at=datetime.now(timezone.utc).isoformat())
    except module.ReceiptError as error: assert str(error) == "scheduling-alert-confirmed-subscription-required"
    else: raise AssertionError("pending actual subscription became confirmed")
    for change in (
        lambda value: value["failure"].update(request_sha256="d" * 64),
        lambda value: value["invocation"]["report"].update(status="success"),
        lambda value: value["alarm"].update(EvaluationPeriods=2),
        lambda value: value["alarm"].update(ActionsEnabled=False),
        lambda value: value["alarm"].update(Threshold=True),
        lambda value: value["alarm"]["Dimensions"][1].update(Value="foreign:2"),
        lambda value: value["history"]["states"].pop(),
        lambda value: value["history"]["states"].append(copy.deepcopy(value["history"]["states"][0])),
        lambda value: value["history"]["actions"][0].update(episode_at="2026-11-26T12:01:01Z"),
        lambda value: value["history"].update(actions=[]),
        lambda value: value["metrics"][0].update(sum=0),
        lambda value: value["metrics"].append(copy.deepcopy(value["metrics"][0])),
        lambda value: value.update(subscriptions=[]),
        lambda value: value["subscriptions"].append(copy.deepcopy(value["subscriptions"][0])),
        lambda value: value["notification"].update(alarm_state_updated_at="2026-11-26T12:01:01Z"),
        lambda value: value["notification"].update(operator_delivery_confirmed_at="2026-11-26T11:59:00Z"),
        lambda value: value["recovery_window"].update(events=[]),
    ):
        broken = copy.deepcopy(confirmed); change(broken)
        try: module.validate_scheduling_alert(broken, expected=expected, failure=failure)
        except (ValueError, runtime.control_owner().Failure, runtime.ADMISSION.AdmissionFailure): pass
        else: raise AssertionError("invalid scheduler alert evidence passed")
    action = json.loads(history[-1]["HistoryData"])
    action["stateUpdateTimestamp"] //= 1000
    history[-1]["HistoryData"] = json.dumps(action)
    try: module.scheduling_history(provider, alarm_name=packet["alarm"]["AlarmName"], topic=expected["topic_arn"], started_at=packet["started_at"], ended_at=packet["ended_at"])
    except module.ReceiptError as error: assert str(error) == "scheduling-alert-history-action-time-invalid"
    else: raise AssertionError("seconds accepted as actual millisecond action evidence")
print("scheduler alert source, historical replay and notification checks passed")
