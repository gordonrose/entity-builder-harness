#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.scheduling-runtime-proof
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.scheduling
#   disciplines: [security, sre]
#   kind: script
#   purpose: Compose scheduler runtime evidence and explicit paid operating-cost projections without granting provider effects.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, network, writes-files]
#   used_by:
#   - id: deploy.capability.scheduling-control
#     path: scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py
"""Cost arithmetic is not provenance. The controller authenticates its inputs.

Rates: official Ireland AWS price lists checked 2026-11-27, recorded in the
reusable-aws-scheduling plan. No free tier, commitment discount or old account
budget is credited. Extra database/notification/transfer costs must be priced
by their observed owner; absent evidence is not zero cost.
"""
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re

_spec = importlib.util.spec_from_file_location("runtime_proof_admission", Path(__file__).with_name("admission.py"))
ADMISSION = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ADMISSION)


class ProofFailure(ValueError):
    def __init__(self, code):
        self.code = "scheduling-runtime-proof-" + code
        super().__init__(self.code)


def require(condition, code):
    if not condition:
        raise ProofFailure(code)


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, RecursionError):
        raise ProofFailure("input-invalid") from None


def amount(value):
    require(isinstance(value, (str, int, float)) and not isinstance(value, bool), "cost-value-invalid")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ProofFailure("cost-value-invalid") from None
    require(result.is_finite() and result >= 0, "cost-value-invalid")
    return result


def dollars(value):
    return str(value.quantize(Decimal("0.000001"), rounding=ROUND_CEILING))


def runtime_records(events, *, expected, started_at, ended_at, retain_events=False):
    """Reduce actual scoped CloudWatch events, never caller-written success flags.

    Transport and immutable function/image checks belong to runtime_window.
    This pure reducer is separately exercised with controlled AWS responses.
    Retain only safe projections and digests, not provider exception messages.
    """
    start, end = ADMISSION.utc(started_at), ADMISSION.utc(ended_at)
    require(0 < (end - start).total_seconds() <= 900, "runtime-window-invalid")
    require(isinstance(events, list) and 0 < len(events) <= 2000, "runtime-events-invalid")
    require(isinstance(expected, dict) and set(expected) == {"purpose", "source_revision", "version_arn", "image_uri", "log_group"}
        and expected["purpose"] in {"dispatch", "worker"}, "runtime-binding-invalid")
    require(isinstance(expected["source_revision"], str) and re.fullmatch(r"[a-f0-9]{40}", expected["source_revision"])
        and isinstance(expected["version_arn"], str) and re.fullmatch(r"arn:aws:lambda:[a-z0-9-]+:[0-9]{12}:function:[A-Za-z0-9_-]+:[1-9][0-9]*", expected["version_arn"]), "runtime-binding-invalid")
    starts, reports, results, seen = {}, {}, [], set()
    for event in events:
        require(isinstance(event, dict) and isinstance(event.get("message"), str)
            and len(event["message"]) <= 262144 and isinstance(event.get("eventId"), str)
            and isinstance(event.get("logStreamName"), str) and type(event.get("timestamp")) is int, "runtime-event-invalid")
        require(event["eventId"] not in seen, "runtime-event-duplicated")
        seen.add(event["eventId"])
        require(start.timestamp() * 1000 <= event["timestamp"] <= end.timestamp() * 1000, "runtime-event-outside-window")
        try: record = json.loads(event["message"])
        except (ValueError, RecursionError): continue
        if not isinstance(record, dict): continue
        if record.get("type") in {"platform.start", "platform.report"}:
            body = record.get("record")
            if isinstance(body, dict) and isinstance(body.get("requestId"), str):
                target = starts if record["type"] == "platform.start" else reports
                target.setdefault(body["requestId"], []).append((body, event))
            continue
        selected = record
        if set(record) & {"timestamp", "requestId"} and "message" in record:
            selected = record["message"]
            if isinstance(selected, str):
                try: selected = json.loads(selected)
                except (ValueError, RecursionError): continue
        if not isinstance(selected, dict) or selected.get("level") != "info" or selected.get("message") != "Scheduling runtime observation.": continue
        fields = selected.get("fields")
        require(isinstance(fields, dict) and set(fields) == {"scheduling_runtime"}, "runtime-observation-invalid")
        body = fields["scheduling_runtime"]
        require(isinstance(body, dict), "runtime-observation-invalid")
        # The two functions share one declared log group. The exact other
        # immutable function is not evidence for this selected component.
        if body.get("function_arn") != expected["version_arn"]: continue
        require(body.get("schema") == "kanbien/scheduling-runtime-observation/v1"
            and body.get("source_revision") == expected["source_revision"]
            and body.get("purpose") == expected["purpose"], "runtime-source-mismatch")
        request = body.get("request_id")
        require(isinstance(request, str) and re.fullmatch(r"[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}", request), "runtime-request-invalid")
        require("requestId" not in record or record["requestId"] == request, "runtime-request-mismatch")
        observed = ADMISSION.utc(body.get("observed_at"))
        require(start <= observed <= end and abs(observed.timestamp() * 1000 - event["timestamp"]) <= 30000, "runtime-observation-time-invalid")
        common = {"schema", "source_revision", "request_id", "function_arn", "purpose", "observed_at", "kind"}
        if expected["purpose"] == "dispatch":
            require(set(body) == common | {"result", "trigger"} and body["kind"] == "dispatch-completed", "runtime-dispatch-invalid")
            trigger = body["trigger"]
            if trigger is not None:
                require(isinstance(trigger, dict) and set(trigger) == {"schedule_arn", "scheduled_at", "execution_sha256", "attempt"}
                    and isinstance(trigger["schedule_arn"], str) and re.fullmatch(r"arn:aws:scheduler:[a-z0-9-]+:[0-9]{12}:schedule/[A-Za-z0-9_.-]{1,64}/[A-Za-z0-9_.-]{1,64}", trigger["schedule_arn"])
                    and isinstance(trigger["execution_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", trigger["execution_sha256"])
                    and type(trigger["attempt"]) is int and 1 <= trigger["attempt"] <= 99
                    and 0 <= (observed - ADMISSION.utc(trigger["scheduled_at"])).total_seconds() <= 180, "runtime-trigger-invalid")
            result = body["result"]
            require(isinstance(result, dict) and set(result) == {"delivery", "relayAttempts", "published", "stopReason"}
                and all(type(result[key]) is int and 0 <= result[key] <= 20 for key in ("relayAttempts", "published"))
                and result["published"] <= result["relayAttempts"]
                and result["stopReason"] in {"idle", "contended", "requested-stop", "attempt-limit"}, "runtime-dispatch-invalid")
            delivery = result["delivery"]
            if delivery is not None:
                required = {"inspected", "deliveryCreated", "deliveryAlreadyCreated", "notDue"}
                require(isinstance(delivery, dict) and required <= set(delivery) <= required | {"blocked", "stopped"}
                    and all(type(delivery[key]) is int and 0 <= delivery[key] <= 20 for key in set(delivery) - {"stopped"})
                    and ("stopped" not in delivery or delivery["stopped"] is True)
                    and delivery["inspected"] == sum(delivery.get(key, 0) for key in ("deliveryCreated", "deliveryAlreadyCreated", "notDue", "blocked")), "runtime-delivery-invalid")
        else:
            require(set(body) == common | {"outbox_sha256", "attempt", "idempotency"} and body["kind"] == "delivery-completed"
                and isinstance(body["outbox_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", body["outbox_sha256"])
                and type(body["attempt"]) is int and 1 <= body["attempt"] <= 3
                and body["idempotency"] in {"durable-processed", "durable-skipped"}, "runtime-worker-invalid")
        results.append((body, event))
    require(results and len({row[0]["request_id"] for row in results}) == len(results), "runtime-results-not-unique")
    output = []
    for body, event in results:
        request = body["request_id"]
        require(len(starts.get(request, [])) == len(reports.get(request, [])) == 1, "runtime-system-report-missing")
        initial, start_event = starts[request][0]
        report, report_event = reports[request][0]
        ADMISSION.function_log_stream(event["logStreamName"], expected["version_arn"])
        require(initial.get("version") == expected["version_arn"].rsplit(":", 1)[1]
            and start_event["logStreamName"] == event["logStreamName"] == report_event["logStreamName"]
            and start_event["timestamp"] <= event["timestamp"] <= report_event["timestamp"], "runtime-system-identity-mismatch")
        require(report.get("status", "success") == "success", "runtime-invocation-failed")
        metrics = report.get("metrics", {})
        require(type(metrics.get("billedDurationMs")) in {int, float}
            and 0 < metrics["billedDurationMs"] <= 120000 and metrics.get("memorySizeMB") == 512, "runtime-billing-invalid")
        original = [start_event, event, report_event]
        output.append({"observation": body, "billed_duration_ms": metrics["billedDurationMs"], "memory_mb": 512,
            "evidence_sha256": hashlib.sha256(canonical(original)).hexdigest(),
            **({"original_events": original} if retain_events else {})})
    return output


def runtime_window(provider, *, expected, started_at, ended_at):
    """Owned read route: actual immutable version plus actual CloudWatch events."""
    packet = capture_runtime_window(provider, expected=expected, started_at=started_at, ended_at=ended_at)
    return validate_runtime_window(packet, expected=expected)


def runtime_function(value, expected):
    """Project only the selected immutable function identity, never credentials."""
    require(isinstance(value, dict), "runtime-function-mismatch")
    configuration = value.get("Configuration", {})
    require(isinstance(configuration, dict), "runtime-function-mismatch")
    require(configuration.get("FunctionArn") == expected["version_arn"]
        and configuration.get("Version") == expected["version_arn"].rsplit(":", 1)[1]
        and configuration.get("State") == "Active" and configuration.get("MemorySize") == 512 and configuration.get("Timeout") == 60
        and configuration.get("Environment", {}).get("Variables", {}).get("PLATFORM_SOURCE_COMMIT_SHA") == expected["source_revision"]
        and configuration.get("LoggingConfig", {}).get("LogGroup") == expected["log_group"]
        and configuration.get("LoggingConfig", {}).get("LogFormat") == "JSON"
        and value.get("Code", {}).get("ResolvedImageUri") == expected["image_uri"], "runtime-function-mismatch")
    return {"Code": {"ResolvedImageUri": expected["image_uri"]}, "Configuration": {
        **{key: configuration[key] for key in ("FunctionArn", "Version", "State", "MemorySize", "Timeout")},
        "Environment": {"Variables": {"PLATFORM_SOURCE_COMMIT_SHA": expected["source_revision"]}},
        "LoggingConfig": {"LogGroup": expected["log_group"], "LogFormat": "JSON"}}}


def capture_runtime_window(provider, *, expected, started_at, ended_at):
    """Retain the original selected events for the existing acceptance archive.

    Only complete successful observations and their START/REPORT records enter
    this packet. Unrelated application/error logs and environment values do not.
    A historical reader can repeat the same reduction without today's AWS logs.
    """
    start, end = ADMISSION.utc(started_at), ADMISSION.utc(ended_at)
    require(0 < (end - start).total_seconds() <= 900 and end <= datetime.now(timezone.utc), "runtime-window-invalid")
    value = provider("lambda", "get-function", FunctionName=expected["version_arn"])
    function = runtime_function(value, expected)
    events = ADMISSION.collection(provider, "logs", "filter-log-events", "events", logGroupName=expected["log_group"],
        startTime=int(start.timestamp() * 1000), endTime=int(end.timestamp() * 1000))
    selected = runtime_records(events, expected=expected, started_at=started_at, ended_at=ended_at, retain_events=True)
    original = sorted([event for row in selected for event in row["original_events"]], key=lambda row: (row["timestamp"], row["eventId"]))
    packet = {"schema": "deploy/scheduling-runtime-window/v1", "expected": expected,
        "started_at": started_at, "ended_at": ended_at, "function": function, "events": original}
    validate_runtime_window(packet, expected=expected)
    return packet


def validate_runtime_window(packet, *, expected):
    """Pure native historical reader; not permission to invoke or trust a file."""
    require(isinstance(packet, dict) and set(packet) == {"schema", "expected", "started_at", "ended_at", "function", "events"}
        and packet["schema"] == "deploy/scheduling-runtime-window/v1" and packet["expected"] == expected,
        "runtime-packet-invalid")
    require(runtime_function(packet["function"], expected) == packet["function"], "runtime-packet-function-invalid")
    require(len(canonical(packet)) <= 512 * 1024, "runtime-packet-too-large")
    records = runtime_records(packet["events"], expected=expected, started_at=packet["started_at"],
        ended_at=packet["ended_at"], retain_events=True)
    require({event["eventId"] for record in records for event in record["original_events"]}
        == {event["eventId"] for event in packet["events"]}, "runtime-packet-unrelated-events")
    return [{key: value for key, value in record.items() if key != "original_events"} for record in records]


def trigger_query(expected, started_at, ended_at):
    require(isinstance(expected, dict) and set(expected) == {"schedule_arn", "function_arn", "role_arn", "dead_letter_queue_arn", "input"}, "trigger-binding-invalid")
    arn = expected["schedule_arn"]
    require(isinstance(arn, str) and re.fullmatch(r"arn:aws:scheduler:[a-z0-9-]+:[0-9]{12}:schedule/[A-Za-z0-9_.-]{1,64}/due-pass", arn), "trigger-binding-invalid")
    start, end = ADMISSION.utc(started_at), ADMISSION.utc(ended_at)
    require(0 < (end - start).total_seconds() <= 900, "trigger-window-invalid")
    group = arn.split("/")[1]
    beginning = start.replace(second=0, microsecond=0)
    ending = end.replace(second=0, microsecond=0) + timedelta(minutes=1)
    return {"Namespace": "AWS/Scheduler", "MetricName": "InvocationAttemptCount", "Dimensions": [{"Name": "ScheduleGroup", "Value": group}],
        "StartTime": beginning.isoformat().replace("+00:00", "Z"), "EndTime": ending.isoformat().replace("+00:00", "Z"),
        "Period": 60, "Statistics": ["Sum"], "Unit": "Count"}


def capture_automatic_trigger(provider, *, expected, started_at, ended_at, dispatches):
    """Actual Scheduler configuration and service metrics, not event text alone."""
    query = trigger_query(expected, started_at, ended_at)
    require(ADMISSION.utc(ended_at) <= datetime.now(timezone.utc), "trigger-window-invalid")
    group = query["Dimensions"][0]["Value"]
    schedule = provider("scheduler", "get-schedule", Name="due-pass", GroupName=group)
    fields = ("Arn", "GroupName", "Name", "State", "ScheduleExpression", "ScheduleExpressionTimezone", "FlexibleTimeWindow", "Target")
    schedules = ADMISSION.collection(provider, "scheduler", "list-schedules", "Schedules", GroupName=group)
    require(len(schedules) == 1 and schedules[0].get("Arn") == expected["schedule_arn"], "trigger-group-not-exclusive")
    metrics = provider("cloudwatch", "get-metric-statistics", **query)
    packet = {"schema": "deploy/scheduling-automatic-trigger/v1", "expected": expected,
        "started_at": started_at, "ended_at": ended_at, "schedule": {key: schedule.get(key) for key in fields},
        "group_schedule_arns": [row["Arn"] for row in schedules], "metric_query": query,
        "metric_response": {key: metrics.get(key) for key in ("Label", "Datapoints")}}
    validate_automatic_trigger(packet, expected=expected, dispatches=dispatches)
    return packet


def validate_automatic_trigger(packet, *, expected, dispatches):
    require(isinstance(packet, dict) and set(packet) == {"schema", "expected", "started_at", "ended_at", "schedule", "group_schedule_arns", "metric_query", "metric_response"}
        and packet["schema"] == "deploy/scheduling-automatic-trigger/v1" and packet["expected"] == expected, "trigger-packet-invalid")
    query = trigger_query(expected, packet["started_at"], packet["ended_at"])
    group = query["Dimensions"][0]["Value"]
    require(packet["metric_query"] == query and packet["group_schedule_arns"] == [expected["schedule_arn"]], "trigger-query-mismatch")
    require(packet["schedule"] == {"Arn": expected["schedule_arn"], "GroupName": group, "Name": "due-pass", "State": "ENABLED",
        "ScheduleExpression": "rate(1 minute)", "ScheduleExpressionTimezone": "UTC", "FlexibleTimeWindow": {"Mode": "OFF"},
        "Target": {"Arn": expected["function_arn"], "RoleArn": expected["role_arn"], "Input": expected["input"],
            "RetryPolicy": {"MaximumEventAgeInSeconds": 60, "MaximumRetryAttempts": 0},
            "DeadLetterConfig": {"Arn": expected["dead_letter_queue_arn"]}}}, "trigger-configuration-mismatch")
    response = packet["metric_response"]
    require(isinstance(response, dict) and set(response) == {"Label", "Datapoints"} and response["Label"] == "InvocationAttemptCount"
        and isinstance(response["Datapoints"], list) and 1 <= len(response["Datapoints"]) <= 17, "trigger-metrics-missing")
    bins = {}
    for point in response["Datapoints"]:
        require(isinstance(point, dict) and set(point) == {"Timestamp", "Sum", "Unit"} and point["Unit"] == "Count"
            and type(point["Sum"]) in {int, float} and 0 <= point["Sum"] <= 1000 and int(point["Sum"]) == point["Sum"], "trigger-metric-invalid")
        raw = point["Timestamp"]
        stamp = ADMISSION.utc(raw.removesuffix("+00:00") + "Z" if isinstance(raw, str) and raw.endswith("+00:00") else raw)
        require(stamp not in bins and stamp.second == stamp.microsecond == 0
            and ADMISSION.utc(query["StartTime"]) <= stamp < ADMISSION.utc(query["EndTime"]), "trigger-metric-time-invalid")
        bins[stamp] = point["Sum"]
    require(isinstance(dispatches, list) and dispatches, "trigger-runtime-missing")
    executions = set()
    for row in dispatches:
        observation = row["observation"]
        trigger = observation.get("trigger")
        if trigger is None: continue
        require(observation["function_arn"] == expected["function_arn"] and trigger["schedule_arn"] == expected["schedule_arn"]
            and trigger["attempt"] == 1 and trigger["execution_sha256"] not in executions, "trigger-runtime-mismatch")
        scheduled, observed = ADMISSION.utc(trigger["scheduled_at"]), ADMISSION.utc(observation["observed_at"])
        require(ADMISSION.utc(packet["started_at"]) <= scheduled <= observed <= ADMISSION.utc(packet["ended_at"])
            and (observed - scheduled).total_seconds() <= 180, "trigger-runtime-time-invalid")
        require(any(count > 0 and scheduled.replace(second=0, microsecond=0) <= stamp <= observed.replace(second=0, microsecond=0)
            for stamp, count in bins.items()), "trigger-invocation-not-observed")
        executions.add(trigger["execution_sha256"])
    require(executions and len(executions) <= sum(bins.values()) <= 1000, "trigger-invocation-not-observed")
    return {"schedule_arn": expected["schedule_arn"], "executions": len(executions), "invocation_attempts": sum(bins.values()),
        "evidence_sha256": hashlib.sha256(canonical(packet)).hexdigest()}


@lru_cache(maxsize=1)
def proof_semantics():
    path = Path(__file__).resolve().parents[6] / "scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof.py"
    spec = importlib.util.spec_from_file_location("runtime_proof_semantics", path)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    return owner


@lru_cache(maxsize=1)
def control_owner():
    spec = importlib.util.spec_from_file_location("retained_scheduling_control", Path(__file__).with_name("script.py"))
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    return owner


def release_context(phases, *, expected, historical=False):
    """Derive proof identities from the complete original control chain.

    Live collection must additionally reobserve the original provider evidence.
    Pure validation alone is never an admission to submit a provider operation.
    """
    control = control_owner()
    binding = control.load_binding(expected["target"], expected["scope"])
    selected = set(control.CONTROL_PHASES) - {"accepted-enable"}
    require(isinstance(phases, dict) and set(phases) == selected, "control-sequence-incomplete")
    checked = {}
    for phase, (previous, _) in control.CONTROL_PHASES.items():
        if phase not in selected: continue
        checked[phase] = control.validate_phase_evidence(phases[phase], target=expected["target"],
            scope="shared" if phase == "network-create" else expected["scope"], source_revision=expected["source_revision"],
            predecessor_sha256=None if previous is None else checked[previous]["intent_sha256"])
        checked[phase]["intent_created_at"] = phases[phase]["intent"]["created_at"]
        require(checked[phase]["phase"] == phase and checked[phase]["stack"] == binding["network_stack" if phase == "network-create" else "stack"], "control-sequence-mismatch")
        if previous is not None:
            require(ADMISSION.utc(phases[phase]["intent"]["created_at"]) >= ADMISSION.utc(checked[previous]["completed_at"]), "control-sequence-time-invalid")
    created = phases["scope-create-disabled"]["intent"]
    parameters, template = created["parameters"], created["template"]
    resources = checked["scope-create-disabled"]["state"]["resources"]
    require(parameters.get("Scope") == expected["scope"] and parameters.get("SourceRevision") == expected["source_revision"], "release-parameters-mismatch")
    if not historical:
        require(control.rendered_template(binding, "scope", parameters) == template
            and control.rendered_template(binding, "network", phases["network-create"]["intent"]["parameters"])
                == phases["network-create"]["intent"]["template"], "release-source-template-mismatch")
    for phase in selected - {"network-create", "scope-create-disabled"}:
        require(checked[phase]["state"] == checked["scope-create-disabled"]["state"]
            and phases[phase]["intent"]["template"] == template, "release-incarnation-changed")
    account, region = binding["provider"]["account_id"], binding["provider"]["region"]
    require(isinstance(expected.get("components"), dict) and set(expected["components"]) == {"dispatch", "worker"}, "release-components-invalid")
    runtime = {}
    for purpose in ("dispatch", "worker"):
        title = purpose.title()
        versions = [row["PhysicalResourceId"] for logical, row in resources.items()
            if logical.startswith(title + "Version") and row["ResourceType"] == "AWS::Lambda::Version"]
        prefix = f"arn:aws:lambda:{region}:{account}:function:kc-{expected['scope']}-schedule-{purpose}:"
        require(len(versions) == 1 and versions[0].startswith(prefix) and re.fullmatch(r"[1-9][0-9]*", versions[0][len(prefix):]), "release-function-invalid")
        component = expected["components"][purpose]
        require(component["source_revision"] == expected["source_revision"] and component["program_id"] == binding["programs"][purpose]
            and parameters[title + "ImageUri"] == f"{account}.dkr.ecr.{region}.amazonaws.com/{binding['repository']}@{component['image_digest']}", "release-image-mismatch")
        runtime[purpose] = {"purpose": purpose, "source_revision": expected["source_revision"], "version_arn": versions[0],
            "image_uri": parameters[title + "ImageUri"], "log_group": resources["RuntimeLogs"]["PhysicalResourceId"]}
    contract = template["Mappings"]["Scopes"][expected["scope"]]
    require(set(contract) >= {"Schema", "Dispatcher", "Worker"}, "release-scope-contract-invalid")
    def queue_arn(logical):
        url, prefix = resources[logical]["PhysicalResourceId"], f"https://sqs.{region}.amazonaws.com/{account}/"
        require(url.startswith(prefix) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", url[len(prefix):]), "release-queue-invalid")
        return f"arn:aws:sqs:{region}:{account}:" + url[len(prefix):]
    role = resources["TickRole"]["PhysicalResourceId"]
    require(re.fullmatch(r"[A-Za-z0-9_+=,.@-]{1,64}", role) is not None, "release-tick-role-invalid")
    trigger = {"schedule_arn": f"arn:aws:scheduler:{region}:{account}:schedule/{expected['target']}-{expected['scope']}/due-pass",
        "function_arn": runtime["dispatch"]["version_arn"], "role_arn": f"arn:aws:iam::{account}:role/{role}",
        "dead_letter_queue_arn": queue_arn("DeadLetterQueue"), "input": template["Resources"]["FixedTick"]["Properties"]["Target"]["Input"]}
    native_binding = {"source_revision": expected["source_revision"], "image_digest": expected["primary_image_digest"],
        "dependency_incarnation_sha256": proof_semantics().digest({"resource_id": parameters["DatabaseResourceId"], "database": parameters["DatabaseName"], "schema": contract["Schema"]})}
    return {"binding": binding, "phases": checked, "runtime": runtime, "trigger": trigger, "native_binding": native_binding,
        "database": {"name": parameters["DatabaseName"], "schema": contract["Schema"]},
        "users": {"dispatch": contract["Dispatcher"], "worker": contract["Worker"]}, "queue_arn": queue_arn("JobQueue"),
        "endpoint_id": checked["network-create"]["state"]["resources"]["SchedulingSqsEndpoint"]["PhysicalResourceId"]}


@lru_cache(maxsize=2)
def native_owner(scope):
    paths = {"core-server-persistence": "core-server-persistence/run-administration/script.py",
        "entity-smoke": "entity-smoke/acceptance-evaluation/implementation/acceptance-evidence.py"}
    require(scope in paths, "native-scope-invalid")
    return control_owner().module("scheduling_native_" + scope.replace("-", "_"),
        "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/" + paths[scope])


def native_packet(packet, *, context, qualified_path, required_after, historical, preparation=False):
    scope = context["binding"]["scope"]
    require(not preparation or scope == "core-server-persistence", "native-preparation-selection-invalid")
    owner = native_owner(scope)
    family = "preparation" if preparation else "proof"
    reader = getattr(owner, ("validate" if historical else "reobserve") + "_scheduling_" + family + "_packet")
    arguments = {"expected_binding": context["native_binding"], "required_after": required_after}
    if not historical: arguments["qualified_path"] = qualified_path
    return reader(packet, **arguments)


def archive_materials(materials):
    """Expand only selected originals, with shared and aggregate bounds."""
    owner = proof_semantics()
    require(isinstance(materials, dict) and 1 <= len(materials) <= owner.ARCHIVE_PART_LIMIT
        and len(canonical(materials)) <= owner.LIMIT, "material-set-invalid")
    consumed, originals = set(), {}
    expanded = 0
    def original(reference, kind):
        nonlocal expanded
        require(isinstance(reference, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", reference)
            and reference in materials, "material-reference-invalid")
        value = materials[reference]
        require(isinstance(value, dict) and set(value) == {"kind", "packet"} and value["kind"] == kind
            and owner.digest(value) == reference, "material-reference-mismatch")
        if reference in originals: return originals[reference]
        require(len(originals) < owner.ARCHIVE_ROOT_LIMIT, "material-root-limit")
        if kind in owner.ARCHIVE_KINDS:
            packet, used = owner.unpack_archive(reference, materials, kind=kind)
            consumed.update(used)
        else:
            require(kind in {"dispatch", "worker", "automatic", "preflight", "effect"}, "material-kind-unsupported")
            packet = value["packet"]
            consumed.add(reference)
        expanded += len(canonical(packet))
        require(expanded <= owner.ARCHIVE_EXPANSION_LIMIT, "material-expansion-limit")
        originals[reference] = packet
        return packet
    return original, consumed


def case_materials(materials, *, context, qualified_path, historical=False, archives=None):
    """One bounded internal packet table, not another evidence store.

    Each case consumes a typed content reference. The final collector rejects
    unused material, preventing an unrelated packet from padding a proof set.
    """
    original, consumed = archive_materials(materials) if archives is None else archives
    checked = {}
    def read(reference, kind):
        packet = original(reference, kind)
        if reference in checked: return checked[reference]
        if kind in {"native", "preparation"}:
            result = native_packet(packet, context=context, qualified_path=qualified_path,
                required_after=context["phases"]["network-create"]["intent_created_at" if kind == "preparation" else "completed_at"], historical=historical,
                preparation=kind == "preparation")
        elif kind in {"dispatch", "worker"}:
            result = validate_runtime_window(packet, expected=context["runtime"][kind])
            if not historical:
                observed = capture_runtime_window(control_owner().Provider(context["binding"]), expected=context["runtime"][kind],
                    started_at=packet["started_at"], ended_at=packet["ended_at"])
                require(observed == packet, "runtime-original-not-confirmed")
        elif kind == "automatic":
            # Validation needs the selected dispatch window and happens at the
            # case join below. Source binding is never taken from this packet.
            result = packet
        elif kind == "preflight":
            control = control_owner()
            request = packet.get("reservation", {}).get("request", {}) if isinstance(packet, dict) else {}
            expected, slot = request.get("expected"), request.get("slot")
            require(isinstance(expected, dict) and expected.get("purpose") in context["runtime"], "connection-selection-invalid")
            purpose = expected["purpose"]
            runtime = context["runtime"][purpose]
            require(expected.get("function_arn") == runtime["version_arn"]
                and expected.get("source_revision") == runtime["source_revision"] and expected.get("image_uri") == runtime["image_uri"]
                and expected.get("database") == {**context["database"], "username": context["users"][purpose]}
                and expected.get("endpoint_id") == context["endpoint_id"], "connection-identity-mismatch")
            queue = expected.get("queue")
            require(queue is None if purpose == "dispatch" else isinstance(queue, dict)
                and queue.get("arn") == context["queue_arn"] and queue.get("address_count") == 2,
                "connection-queue-mismatch")
            result = control.validate_preflight_evidence(packet, scope=context["binding"]["scope"], slot=slot, expected=expected)
            if not historical:
                provider = control.Provider(context["binding"])
                parameters = context["phase_packets"]["scope-create-disabled"]["intent"]["parameters"]
                require(control.preflight_expected(provider, context["binding"], parameters, purpose) == expected,
                    "connection-current-identity-mismatch")
                require(control.capture_preflight(provider, context["preflight_store"], context["binding"], slot, purpose) == packet,
                    "connection-original-not-confirmed")
        else:
            raise ProofFailure("material-kind-unsupported")
        checked[reference] = result
        return result
    return read, consumed


def owned_work_selection(value, *, context, qualified_path, database_observation, historical=False):
    """Bind every pending row to original synthetic creation before enabling.

    The controller supplies its actual disabled-phase whole-database read.
    This helper does not accept a caller's count as observation authority.
    """
    require(isinstance(value, dict) and set(value) == {"schema", "materials", "snapshots"}
        and value["schema"] == "deploy/scheduling-owned-work-selection/v1"
        and isinstance(value["snapshots"], list) and 0 <= len(value["snapshots"]) <= 8, "owned-selection-invalid")
    observed, binding = database_observation, context["binding"]
    require(isinstance(observed, dict) and observed.get("schema") == "kanbien/scheduling-database-observation/v1"
        and observed.get("target") == binding["target"] and observed.get("scope") == binding["scope"]
        and observed.get("binding") == context["native_binding"], "owned-observation-mismatch")
    task = observed.get("task")
    require(isinstance(task, dict) and set(task) == {"arn", "definition", "started_at", "stopped_at"}, "owned-observation-task-invalid")
    started, stopped = (ADMISSION.utc(task[key].replace("+00:00", "Z")) for key in ("started_at", "stopped_at"))
    checked_at = ADMISSION.utc(observed["checked_at"])
    require(ADMISSION.utc(observed["required_after"]) <= started <= stopped <= checked_at
        and (checked_at - stopped).total_seconds() <= 900, "owned-observation-stale")
    if not historical:
        require(0 <= (datetime.now(timezone.utc) - stopped).total_seconds() <= 900, "owned-observation-stale")
    if not value["snapshots"]:
        require(value["materials"] == {}, "material-unused")
        # An authenticated zero inventory contains no actionable row whose
        # ownership needs another task. This is not an asserted zero shortcut.
        return owned_work_inventory(scope=binding["scope"], database_state=observed["database_state"], snapshots=[])
    required_after = context.get("required_after")
    if required_after is None: required_after = context["phases"]["network-create"]["completed_at"]
    original, consumed = archive_materials(value["materials"])
    snapshots, seen = [], set()
    for selection in value["snapshots"]:
        require(isinstance(selection, dict) and set(selection) == {"snapshot", "seed"}
            and isinstance(selection["snapshot"], str) and selection["snapshot"] not in seen, "owned-selection-duplicated")
        seen.add(selection["snapshot"])
        packet = native_packet(original(selection["snapshot"], "native"), context=context, qualified_path=qualified_path,
            required_after=required_after, historical=historical)
        require(packet["operation"] == "observe-scheduling-proof", "owned-snapshot-operation-invalid")
        snapshot = packet["result"]["scheduling_observation"]
        require(ADMISSION.utc(packet["task"]["stopped_at"].replace("+00:00", "Z")) <= started
            and (started - ADMISSION.utc(snapshot["observed_at"])).total_seconds() <= 900, "owned-snapshot-order-invalid")
        if binding["scope"] == "core-server-persistence":
            seed = native_packet(original(selection["seed"], "native"), context=context, qualified_path=qualified_path,
                required_after=required_after, historical=historical)
            require(seed["operation"] == "seed-scheduling-proof" and snapshot["schedule"] is not None
                and seed["result"]["scheduling_seed"]["schedule_id"] == snapshot["schedule"]["id"]
                and seed["result"]["scheduling_seed"]["due_at"] == snapshot["schedule"]["due_at"]
                and ADMISSION.utc(seed["task"]["stopped_at"].replace("+00:00", "Z")) <= ADMISSION.utc(snapshot["observed_at"]),
                "native-seed-mismatch")
        else:
            require(selection["seed"] is None, "native-seed-unexpected")
        snapshots.append(snapshot)
    require(consumed == set(value["materials"]), "material-unused")
    return owned_work_inventory(scope=binding["scope"], database_state=observed["database_state"], snapshots=snapshots)


def connection_proof(value, *, context, read, observed_at):
    """Reuse unchanged connection evidence; renew only when it is too old.

    Every supplied successor keeps its original reservation. The controller
    reconciles all previously reserved slots before permitting a later one.
    """
    require(isinstance(value, dict) and set(value) == {"dispatch", "worker"}, "connections-incomplete")
    slots = control_owner().PreflightStore.slots
    start = ADMISSION.utc(context["phases"]["scope-create-disabled"]["completed_at"])
    enabled = ADMISSION.utc(context["phases"]["proof-enable"]["completed_at"])
    disabled = ADMISSION.utc(context["phases"]["proof-disable"]["completed_at"])
    observed = ADMISSION.utc(observed_at)
    for purpose, references in value.items():
        require(isinstance(references, list) and 1 <= len(references) <= len(slots), "connection-selection-invalid")
        rows = [read(reference, "preflight") for reference in references]
        positions = [slots.index(row["slot"]) for row in rows]
        require(positions[0] == 0 and positions == sorted(set(positions))
            and all(row["purpose"] == purpose for row in rows), "connection-sequence-invalid")
        times = [ADMISSION.utc(row["response"]["checked_at"]) for row in rows]
        require(start <= times[0] and times == sorted(set(times)) and times[-1] <= observed,
            "connection-time-invalid")
        require(any(0 <= (enabled - checked).total_seconds() <= 900 for checked in times)
            and 0 <= (observed - times[-1]).total_seconds() <= 900, "connection-stale")
        require(all(row["expected"] == rows[0]["expected"] for row in rows), "connection-binding-changed")
        for row, checked in zip(rows, times):
            require(checked >= disabled if row["slot"] == "acceptance" else checked <= enabled,
                "connection-outside-owned-phase")
    return value


def scope_proof(value, *, context, read, before_purge, completed_at):
    """Join native permission proof and the Entity controls that must survive.

    The native readers validate the real maintenance tasks and their immutable
    image/role/database binding. This function does not query another schema or
    treat a schema name supplied in JSON as an isolation test.
    """
    scope = context["binding"]["scope"]
    require(isinstance(value, dict) and set(value) == {"preparation", "controls"}, "scope-proof-invalid")
    if scope == "core-server-persistence":
        operations = ("observe-scheduling-state", "grant-scheduling-access", "prove-scheduling-access")
        require(value["controls"] is None and isinstance(value["preparation"], dict)
            and set(value["preparation"]) == set(operations), "scope-preparation-incomplete")
        prior, manifest = None, None
        for operation in operations:
            packet = read(value["preparation"][operation], "preparation")
            require(packet["operation"] == operation, "scope-preparation-operation-mismatch")
            state = proof_semantics().complete_database_state(packet["result"]["database_state"], manifest_sha256=manifest)
            manifest = state["manifest_sha256"]
            require(state["work_inventory"] == {"waiting_schedules": 0, "pending_outbox": 0, "active_processing": 0},
                "scope-preparation-unrelated-work")
            started, stopped = (ADMISSION.utc(packet["task"][key].replace("+00:00", "Z")) for key in ("started_at", "stopped_at"))
            require(started <= stopped and (prior is None or prior <= started)
                and stopped <= ADMISSION.utc(context["phases"]["scope-create-disabled"]["completed_at"]),
                "scope-preparation-order-invalid")
            prior = stopped
        return {"manifest_sha256": manifest, "controls": []}
    require(scope == "entity-smoke" and value["preparation"] is None
        and isinstance(value["controls"], dict) and set(value["controls"]) == {"untouched", "future"}, "scope-controls-incomplete")
    controls, selections, manifest = [], set(), None
    for name, case in (("untouched", "scope-isolation"), ("future", "cost-and-idle")):
        pair = value["controls"][name]
        require(isinstance(pair, dict) and set(pair) == {"before", "after"}, "scope-control-invalid")
        packets = [read(pair[when], "native") for when in ("before", "after")]
        require(all(packet["operation"] == "observe-scheduling-proof" and packet["case"] == case for packet in packets),
            "scope-control-selection-mismatch")
        before, after = (packet["result"]["scheduling_observation"] for packet in packets)
        selected = canonical(before["selection"])
        require(selected not in selections, "scope-control-duplicated")
        selections.add(selected)
        for packet in packets:
            # The native archive already authenticates the original state,
            # grant and positive/negative permission tasks in their real order.
            for preparation in packet["archive"]["preparation"].values():
                state = preparation["operation"]["packet"]["receipt"]["result"]["database_state"]
                checked = proof_semantics().complete_database_state(state, manifest_sha256=manifest)
                manifest = checked["manifest_sha256"]
        controls.append(preserved_entity(before=before, after=after, before_purge=before_purge,
            after_completion=completed_at, untouched=name == "untouched"))
    return {"manifest_sha256": manifest, "controls": controls}


def case_effect(packet, *, case, delivery, context, original, historical):
    """Authenticate one original queue send or failure invocation, never send."""
    control = control_owner()
    duplicate = case == "duplicate-delivery"
    require(duplicate or case == "failure-recovery", "effect-case-invalid")
    phase = "proof-enable" if duplicate else "fault-on"
    resources = context["phases"]["scope-create-disabled"]["state"]["resources"]
    arguments = {"phase_packet": context["phase_packets"][phase],
        "native_packet": original(delivery["after" if duplicate else "before"], "native"),
        "seed_packet": None if delivery["seed"] is None else original(delivery["seed"], "native"),
        "expected": {"runtime": context["runtime"]["worker" if duplicate else "dispatch"],
            "queue_url": resources["JobQueue"]["PhysicalResourceId"], "queue_arn": context["queue_arn"],
            "native_binding": context["native_binding"], "required_after": context["phases"]["network-create"]["completed_at"]}}
    checked = control.validate_proof_effect(packet, binding=context["binding"], **arguments)
    if not historical:
        observed = control.reobserve_proof_effect(context["provider"], context["effect_store"], context["binding"], packet,
            qualified_path=context["qualified_path"], **arguments)
        require(observed == checked, "effect-original-not-confirmed")
    if duplicate: require(checked["acknowledgement"] == "retained", "duplicate-send-unconfirmed")
    return checked


def runtime_cases(observations, *, context, read, original, historical=False):
    """The finite acceptance cases share native, runtime and control owners."""
    require(isinstance(observations, dict) and set(observations) == proof_semantics().CASES, "cases-incomplete")
    minute = delivery_case(observations["minute-delivery"], case="minute-delivery", context=context, read=read, historical=historical)
    duplicate = observations["duplicate-delivery"]
    require(isinstance(duplicate, dict) and set(duplicate) == {"delivery", "repeated", "worker", "effect"}, "duplicate-case-invalid")
    # Re-send the already demonstrated original, not another synthetic job.
    # Exact references keep all native, automatic and runtime evidence bound.
    require(duplicate["delivery"] == observations["minute-delivery"], "duplicate-original-not-minute")
    first = minute
    repeated = read(duplicate["repeated"], "native")
    scope = context["binding"]["scope"]
    require(repeated["operation"] == "observe-scheduling-proof"
        and (scope == "core-server-persistence" or repeated["case"] == "minute-delivery"), "duplicate-selection-mismatch")
    duplicate_result = duplicate_delivery(scope=scope, original=first["after"],
        repeated=repeated["result"]["scheduling_observation"], workers=read(duplicate["worker"], "worker"))
    effect = case_effect(original(duplicate["effect"], "effect"), case="duplicate-delivery", delivery=duplicate["delivery"],
        context=context, original=original, historical=historical)
    require(ADMISSION.utc(first["after"]["observed_at"]) <= ADMISSION.utc(effect["reserved_at"].replace("+00:00", "Z"))
        <= ADMISSION.utc(repeated["result"]["scheduling_observation"]["observed_at"]), "duplicate-effect-time-invalid")
    skipped = [row["observation"] for row in read(duplicate["worker"], "worker")
        if row["observation"]["request_id"] == duplicate_result["worker_request_id"]]
    require(len(skipped) == 1 and ADMISSION.utc(skipped[0]["observed_at"])
        >= ADMISSION.utc(effect["reserved_at"].replace("+00:00", "Z")), "duplicate-skip-predates-send")
    missed = delivery_case(observations["missed-tick-recovery"], case="missed-tick-recovery", context=context, read=read, historical=historical)
    failure = observations["failure-recovery"]
    require(isinstance(failure, dict) and set(failure) == {"delivery", "effect"}, "failure-case-invalid")
    recovered = delivery_case(failure["delivery"], case="failure-recovery", context=context, read=read, historical=historical)
    failed = case_effect(original(failure["effect"], "effect"), case="failure-recovery", delivery=failure["delivery"],
        context=context, original=original, historical=historical)
    interrupted = read(failure["delivery"]["interrupted"], "native")["result"]["scheduling_observation"]
    require(ADMISSION.utc(recovered["before"]["schedule"]["due_at"]) <= ADMISSION.utc(failed["invoked_at"])
        <= ADMISSION.utc(interrupted["observed_at"]) <= ADMISSION.utc(context["phases"]["fault-off"]["completed_at"]),
        "failure-effect-time-invalid")
    deliveries = {"minute-delivery": minute, "duplicate-delivery": first, "missed-tick-recovery": missed, "failure-recovery": recovered}
    if scope == "entity-smoke":
        deliveries["cancellation"] = delivery_case(observations["cancellation"], case="cancellation", context=context, read=read,
            historical=historical, restored=True)
    else:
        require(observations["cancellation"] == {"applicable": False, "reason": "baseline-job-has-no-entity-lifecycle"},
            "baseline-cancellation-selection-invalid")
    selected = [canonical(value["before"]["selection"]) for name, value in deliveries.items()
        if name != "duplicate-delivery"]
    isolation = scope_proof(observations["scope-isolation"], context=context, read=read,
        before_purge=minute["after"]["outbox"]["created_at"], completed_at=minute["result"]["completed_at"])
    selected += [canonical(value["selection"]) for value in isolation["controls"]]
    require(len(selected) == len(set(selected)), "case-original-reused")
    return {"deliveries": deliveries, "duplicate": duplicate_result, "failure": failed, "scope": isolation}


def delivery_case(value, *, case, context, read, historical=False, restored=False):
    scope = context["binding"]["scope"]
    interrupted = case in {"missed-tick-recovery", "failure-recovery"}
    fields = {"seed", "before", "after", "dispatch", "worker", "automatic"} | ({"interrupted"} if interrupted else set())
    require(isinstance(value, dict) and set(value) == fields, "delivery-case-invalid")
    def snapshot(reference):
        selected = read(reference, "native")
        require(selected["operation"] == "observe-scheduling-proof"
            and (scope == "core-server-persistence" or selected["case"] == case), "native-case-mismatch")
        return selected["result"]["scheduling_observation"]
    before, after = snapshot(value["before"]), snapshot(value["after"])
    if scope == "core-server-persistence":
        seed = read(value["seed"], "native")
        require(seed["operation"] == "seed-scheduling-proof" and before["schedule"] is not None
            and seed["result"]["scheduling_seed"]["schedule_id"] == before["schedule"]["id"]
            and seed["result"]["scheduling_seed"]["due_at"] == before["schedule"]["due_at"]
            and ADMISSION.utc(seed["task"]["stopped_at"].replace("+00:00", "Z")) <= ADMISSION.utc(before["observed_at"]), "native-seed-mismatch")
    else: require(value["seed"] is None, "native-seed-unexpected")
    dispatches, workers = read(value["dispatch"], "dispatch"), read(value["worker"], "worker")
    automatic = read(value["automatic"], "automatic")
    validate_automatic_trigger(automatic, expected=context["trigger"], dispatches=dispatches)
    if not historical:
        # The trigger may now be disabled. Its original enabled phase is bound
        # below; current metrics reauthenticate service-origin attempts without
        # pretending today's control state is the historical state.
        response = control_owner().Provider(context["binding"])("cloudwatch", "get-metric-statistics", **automatic["metric_query"])
        def metric_projection(value):
            require(isinstance(value, dict) and set(value) == {"Label", "Datapoints"}
                and isinstance(value["Datapoints"], list), "trigger-original-metric-invalid")
            return {"Label": value["Label"], "Datapoints": sorted(value["Datapoints"], key=lambda row: row["Timestamp"])}
        require(metric_projection(response) == metric_projection(automatic["metric_response"]), "trigger-original-metric-not-confirmed")
    enabled, disabled = {"missed-tick-recovery": ("missed-tick-recovery-enable", "fault-disable"),
        "failure-recovery": ("failure-recovery-enable", "proof-disable")}.get(case, ("proof-enable", "missed-tick-disable"))
    start = ADMISSION.utc(context["phases"][enabled]["completed_at"])
    end = ADMISSION.utc(context["phases"][disabled]["completed_at"])
    require(start <= ADMISSION.utc(automatic["started_at"]) < ADMISSION.utc(automatic["ended_at"]) <= end,
        "automatic-window-outside-enabled-phase")
    arguments = {"scope": scope, "before": before, "after": after, "dispatches": dispatches, "workers": workers}
    if interrupted:
        observed = snapshot(value["interrupted"])
        result = interrupted_delivery(**arguments, interrupted=observed,
            disabled_at=context["phases"]["missed-tick-disable" if case == "missed-tick-recovery" else "fault-disable"]["completed_at"],
            restored_at=context["phases"][enabled]["completed_at"], kind="missed-tick" if case == "missed-tick-recovery" else "send-failure")
        require(ADMISSION.utc(after["processing"]["completion"]["completed_at"]) >= ADMISSION.utc(observed["observed_at"]),
            "recovery-completion-predates-interruption")
    else: result = completed_delivery(**arguments, restored=restored)
    return {"result": result, "before": before, "after": after, "dispatches": dispatches, "workers": workers}


def owned_work_inventory(*, scope, database_state, snapshots):
    """Compare authenticated exact-ID snapshots to the complete scope counts.

    Native task readers and the disabled-controls gate must authenticate and
    order these inputs before this pure comparison. A count alone cannot
    authorize arbitrary existing work; every actionable row needs its original
    synthetic creation custody and exact selection in the calling controller.
    """
    owner = proof_semantics()
    state = owner.complete_database_state(database_state)
    require(isinstance(snapshots, list) and 0 <= len(snapshots) <= 8, "owned-work-incomplete")
    counts = {"waiting_schedules": 0, "pending_outbox": 0, "active_processing": 0}
    selections, schedules, outboxes = set(), set(), set()
    for snapshot in snapshots:
        owner.proof_snapshot(snapshot, scope=scope)
        selection = canonical(snapshot["selection"])
        require(selection not in selections, "owned-work-selection-duplicated")
        selections.add(selection)
        schedule, outbox, processing = (snapshot[key] for key in ("schedule", "outbox", "processing"))
        if schedule is not None:
            require(schedule["id"] not in schedules and schedule["state"] in {"waiting", "delivery-created"}, "owned-schedule-invalid")
            schedules.add(schedule["id"])
            counts["waiting_schedules"] += schedule["state"] == "waiting"
        if outbox is not None:
            require(outbox["id"] not in outboxes, "owned-outbox-duplicated")
            outboxes.add(outbox["id"])
            counts["pending_outbox"] += outbox["state"] in {"pending", "leased"}
        if processing is not None:
            counts["active_processing"] += processing["state"] in {"claimed", "retry-eligible"}
    require(counts == state["work_inventory"], "unrelated-work-present")
    return {"schema": "deploy/scheduling-owned-work/v1", "scope": scope,
        "manifest_sha256": state["manifest_sha256"], "work_inventory": counts,
        "selections_sha256": hashlib.sha256(canonical(snapshots)).hexdigest()}


def completed_delivery(*, scope, before, after, dispatches, workers, recovered_at=None, restored=False):
    """Judge the durable chain from native snapshots and original runtime logs.

    This is the semantic half of acceptance, not provenance. The public reader
    must obtain these values from their fixed native capture/validation owners.
    No successful HTTP request or absent row by itself establishes execution.
    """
    owner = proof_semantics()
    owner.proof_snapshot(before, scope=scope)
    owner.proof_snapshot(after, scope=scope, selection=before["selection"])
    prior, schedule = before["schedule"], after["schedule"]
    require(prior is not None and schedule is not None and prior["state"] == "waiting"
        and before["outbox"] is None and before["processing"] is None, "delivery-before-invalid")
    require(schedule["state"] == "delivery-created" and all(schedule.get(key) == value for key, value in prior.items() if key != "state"), "delivery-schedule-changed")
    due, beginning, observed = (ADMISSION.utc(value) for value in (prior["due_at"], before["observed_at"], after["observed_at"]))
    require(beginning < observed, "delivery-snapshot-order-invalid")
    if recovered_at is None:
        require(beginning < due, "delivery-before-not-before-due")
        deadline = due.timestamp() + 300
    else:
        restored_at = ADMISSION.utc(recovered_at)
        require(due <= restored_at <= observed and beginning <= restored_at, "recovery-boundary-invalid")
        deadline = restored_at.timestamp() + 600
    outbox, processing = after["outbox"], after["processing"]
    require(outbox is not None and outbox["state"] == "published" and processing is not None
        and processing["state"] == "completed" and processing["completion"]["outcome"] == "succeeded", "delivery-not-completed")
    created, published, completed = (ADMISSION.utc(value) for value in
        (outbox["created_at"], outbox["published_at"], processing["completion"]["completed_at"]))
    # A fast worker can complete before the relay records its publication. Do
    # not invent the stronger ordering 'published record before completion'.
    require(due <= created <= published <= observed and created <= completed <= observed
        and completed.timestamp() <= deadline, "delivery-time-budget-exceeded")
    if scope == "core-server-persistence":
        require(not restored and before["application"] == {"kind": "acceptance", "present": False}
            and after["application"]["present"] is True, "baseline-effect-not-confirmed")
    else:
        require(before["application"]["present"] is True, "entity-before-missing")
        if restored:
            require(before["application"]["lifecycle_state"] == "active"
                and after["application"] == before["application"], "restored-control-not-preserved")
        else:
            application = before["application"]
            require(application["visibility"] == "archived" and application["lifecycle_state"] == "deleted"
                and due == max(ADMISSION.utc(application["deleted_at"]) + timedelta(minutes=5),
                    ADMISSION.utc(application["restore_eligible_until"])) + timedelta(milliseconds=1)
                and after["application"] == {"kind": "entity", "present": False}, "entity-retention-effect-not-confirmed")
    require(isinstance(dispatches, list) and isinstance(workers, list), "delivery-runtime-missing")
    outbox_digest = hashlib.sha256(outbox["id"].encode()).hexdigest()
    delivered = [row["observation"] for row in workers if row["observation"].get("outbox_sha256") == outbox_digest
        and row["observation"].get("idempotency") == "durable-processed"]
    require(len(delivered) == 1 and delivered[0]["attempt"] == processing["attempt"]
        and abs((ADMISSION.utc(delivered[0]["observed_at"]) - completed).total_seconds()) <= 60,
        "delivery-worker-not-confirmed")
    automatic = [row["observation"] for row in dispatches if row["observation"].get("trigger") is not None
        and row["observation"]["result"]["published"] > 0
        and due <= ADMISSION.utc(row["observation"]["observed_at"]) <= completed + timedelta(seconds=60)]
    require(automatic, "automatic-delivery-not-confirmed")
    return {"schedule_id": schedule["id"], "outbox_sha256": outbox_digest,
        "due_at": prior["due_at"], "completed_at": processing["completion"]["completed_at"],
        "worker_request_id": delivered[0]["request_id"],
        "dispatch_request_ids": sorted({row["request_id"] for row in automatic})}


def interrupted_delivery(*, scope, before, interrupted, after, dispatches, workers,
                         disabled_at, restored_at, kind):
    """Require the actual durable interruption, not merely toggled controls.

    The caller authenticates control operations and, for a send failure, its
    original Lambda invocation. This reducer cannot grant either effect.
    """
    require(kind in {"missed-tick", "send-failure"}, "interruption-kind-invalid")
    owner = proof_semantics()
    owner.proof_snapshot(before, scope=scope)
    owner.proof_snapshot(interrupted, scope=scope, selection=before["selection"])
    schedule = before["schedule"]
    require(schedule is not None and schedule["state"] == "waiting", "interruption-before-invalid")
    due = ADMISSION.utc(schedule["due_at"])
    disabled, restored, observed = map(ADMISSION.utc, (disabled_at, restored_at, interrupted["observed_at"]))
    require(disabled <= due < observed <= restored and ADMISSION.utc(before["observed_at"]) <= observed,
        "interruption-boundary-invalid")
    require(interrupted["processing"] is None and interrupted["application"] == before["application"],
        "interruption-effect-already-completed")
    if kind == "missed-tick":
        require((observed - due).total_seconds() >= 60
            and interrupted["schedule"] == schedule and interrupted["outbox"] is None,
            "missed-tick-not-observed")
    else:
        require(interrupted["schedule"] is not None and interrupted["schedule"]["state"] == "delivery-created"
            and all(interrupted["schedule"].get(key) == value for key, value in schedule.items() if key != "state")
            and interrupted["outbox"] is not None and interrupted["outbox"]["state"] == "pending"
            and interrupted["outbox"]["attempt"] > 0 and due <= ADMISSION.utc(interrupted["outbox"]["created_at"]) <= observed,
            "failed-send-not-retained")
        require(after["outbox"] is not None and after["outbox"]["id"] == interrupted["outbox"]["id"]
            and after["outbox"]["attempt"] > interrupted["outbox"]["attempt"], "failed-send-not-retried")
    return completed_delivery(scope=scope, before=before, after=after, dispatches=dispatches, workers=workers,
        recovered_at=restored_at)


def duplicate_delivery(*, scope, original, repeated, workers):
    owner = proof_semantics()
    owner.proof_snapshot(original, scope=scope)
    owner.proof_snapshot(repeated, scope=scope, selection=original["selection"])
    require(original["processing"] is not None and original["processing"]["state"] == "completed"
        and original["processing"]["completion"]["outcome"] == "succeeded"
        and all(original[key] == repeated[key] for key in ("schedule", "outbox", "processing", "application"))
        and ADMISSION.utc(original["observed_at"]) < ADMISSION.utc(repeated["observed_at"]), "duplicate-durable-state-changed")
    selected = hashlib.sha256(original["outbox"]["id"].encode()).hexdigest()
    rows = [row["observation"] for row in workers if row["observation"].get("outbox_sha256") == selected]
    require(len(rows) == 1 and rows[0].get("idempotency") == "durable-skipped"
        and ADMISSION.utc(original["observed_at"]) <= ADMISSION.utc(rows[0]["observed_at"]) <= ADMISSION.utc(repeated["observed_at"]),
        "duplicate-worker-skip-not-confirmed")
    return {"outbox_sha256": selected, "worker_request_id": rows[0]["request_id"],
        "original_completed_at": original["processing"]["completion"]["completed_at"]}


def preserved_entity(*, before, after, before_purge, after_completion, untouched=False):
    owner = proof_semantics()
    owner.proof_snapshot(before, scope="entity-smoke")
    owner.proof_snapshot(after, scope="entity-smoke", selection=before["selection"])
    require(ADMISSION.utc(before["observed_at"]) <= ADMISSION.utc(before_purge)
        < ADMISSION.utc(after_completion) <= ADMISSION.utc(after["observed_at"])
        and all(before[key] == after[key] for key in ("schedule", "outbox", "processing", "application"))
        and after["application"]["present"] is True and after["outbox"] is None and after["processing"] is None,
        "entity-control-not-preserved")
    if untouched:
        require(after["schedule"] is None and after["application"]["lifecycle_state"] == "active", "untouched-control-invalid")
    else:
        require(after["schedule"] is not None and after["schedule"]["state"] == "waiting"
            and ADMISSION.utc(after["observed_at"]) < ADMISSION.utc(after["schedule"]["due_at"]), "future-control-invalid")
    return {"selection": after["selection"], "observed_at": after["observed_at"]}


def alert_proof(packet, *, context, failure, recovery_window, topic_arn, historical=False):
    """Join the real failed dispatch, its alert episode and observed recovery."""
    control = control_owner()
    owner = control.module("scheduling_final_alerts",
        "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts.py")
    selected = {key: failure[key] for key in ("operation_id", "request_id", "invoked_at", "request_sha256")}
    expected = {key: value for key, value in context["runtime"]["dispatch"].items() if key != "purpose"}
    expected.update(scope=context["binding"]["scope"], topic_arn=topic_arn)
    require(isinstance(packet, dict) and packet.get("recovery_window") == recovery_window, "alert-recovery-window-mismatch")
    checked = owner.validate_scheduling_alert(packet, expected=expected, failure=selected)
    if not historical:
        actual = owner.capture_scheduling_alert(context["provider"], expected=expected, failure=selected,
            recovery_window=recovery_window, started_at=packet["started_at"], ended_at=packet["ended_at"])
        # Collection time is not a new alarm episode. Human confirmation is
        # supplied only by the existing explicit notification-confirmation path.
        require(all(actual[key] == packet[key] for key in actual if key not in {"collected_at", "notification"}),
            "alert-original-not-confirmed")
        require(ADMISSION.utc(packet["collected_at"]) <= ADMISSION.utc(actual["collected_at"]), "alert-time-invalid")
    return checked


def validate_acceptance_evidence(evidence, *, expected, historical=False):
    """Canonical profile delegate: validate all connected proof, never mutate AWS.

    Live input is reauthenticated through the original operation/task owners.
    Historical replay is only for evidence already retained by the canonical
    accepted-release owner; it is not a provider mutation permission.
    """
    semantics, control = proof_semantics(), control_owner()
    fields = {"schema", "evidence_class", "target", "scope", "source_revision", "primary_image_digest", "observed_at", "components", "observations"}
    require(isinstance(evidence, dict) and set(evidence) == fields and evidence["schema"] == semantics.RUNTIME_SCHEMA
        and evidence["evidence_class"] == expected["evidence_class"] == "live"
        and all(evidence[key] == expected[key] for key in ("target", "scope", "source_revision", "primary_image_digest"))
        and len(canonical(evidence)) <= semantics.LIMIT, "acceptance-envelope-invalid")
    observations = evidence["observations"]
    require(isinstance(observations, dict) and set(observations) == semantics.CASES, "cases-incomplete")
    common = observations["cost-and-idle"]
    require(isinstance(common, dict) and set(common) == {"materials", "phases", "qualified_path", "connections", "cost", "alert"},
        "acceptance-material-selection-invalid")
    qualified_path = common["qualified_path"]
    require(isinstance(qualified_path, str) and bool(qualified_path) and not Path(qualified_path).is_absolute()
        and ".." not in Path(qualified_path).parts, "native-qualified-path-invalid")
    original, consumed = archive_materials(common["materials"])
    require(isinstance(common["phases"], dict) and set(common["phases"]) == set(control.CONTROL_PHASES) - {"accepted-enable"},
        "control-sequence-incomplete")
    phases = {phase: original(reference, "phase") for phase, reference in common["phases"].items()}
    context = release_context(phases, expected=expected, historical=historical)
    observed = ADMISSION.utc(evidence["observed_at"])
    require(ADMISSION.utc(context["phases"]["proof-disable"]["completed_at"]) <= observed, "acceptance-controls-not-disabled")
    require(evidence["components"] == {purpose: {"program_id": expected["components"][purpose]["program_id"],
        "image_digest": expected["components"][purpose]["image_digest"], "version_arn": runtime["version_arn"]}
        for purpose, runtime in context["runtime"].items()}, "acceptance-components-mismatch")
    context.update(phase_packets=phases, qualified_path=qualified_path)
    provider = store = None
    if not historical:
        require(0 <= (datetime.now(timezone.utc) - observed).total_seconds() <= 900, "acceptance-observation-stale")
        provider = control.Provider(context["binding"])
        git_dir = control.subprocess.run(["git", "-C", str(control.ROOT), "rev-parse", "--absolute-git-dir"],
            check=True, text=True, capture_output=True).stdout.strip()
        store = control.Store(Path(git_dir) / "scheduling-control")
        context.update(provider=provider, effect_store=store, preflight_store=control.PreflightStore(store.root))
        for packet in phases.values(): control.authenticate_phase_evidence(provider, store, context["binding"], packet)
        require(control.disabled_phase(provider, store, context["binding"], "proof-disable") == phases["proof-disable"],
            "acceptance-controls-changed")
        # The retained template is not evidence that live queue/function
        # safety settings still match. Reuse the existing read-only observer.
        control.observe_current(provider, context["binding"])
        budget = control.cost_intent(store, context["binding"])
        require(budget is not None and budget["source_revision"] == expected["source_revision"], "acceptance-original-budget-missing")
        selected = budget["scopes"][expected["scope"]]
        name = "qualified_path" if expected["scope"] == "core-server-persistence" else "receipt_path"
        require(selected["selection"].get(name) == str((control.ROOT / qualified_path).absolute())
            and selected["maintenance"]["image_digest"] == expected["primary_image_digest"], "acceptance-maintenance-mismatch")
    read, _ = case_materials(common["materials"], context=context, qualified_path=qualified_path,
        historical=historical, archives=(original, consumed))
    connection_proof(common["connections"], context=context, read=read, observed_at=evidence["observed_at"])
    cases = runtime_cases(observations, context=context, read=read, original=original, historical=historical)
    cost = original(common["cost"], "cost")
    require(isinstance(cost, dict) and isinstance(cost.get("components"), dict)
        and cost["components"].get(expected["scope"]) == context["runtime"]
        and cost.get("endpoint_id") == context["endpoint_id"], "acceptance-cost-binding-mismatch")
    parameters = phases["scope-create-disabled"]["intent"]["parameters"]
    require(cost.get("notification_topic_arn") == parameters["AlarmTopicArn"], "acceptance-cost-topic-mismatch")
    authenticate_cost_evidence(provider, store, context["binding"], cost, components=cost["components"],
        database=cost["database"], notification_topic_arn=cost["notification_topic_arn"], endpoint_id=context["endpoint_id"], historical=historical)
    projection = cost["projection"]
    require(projection["expected"]["within_ceiling"] is True and projection["expected"]["capacity_supported"] is True,
        "acceptance-monthly-cost-not-admitted")
    recovery = original(observations["failure-recovery"]["delivery"]["dispatch"], "dispatch")
    alert_proof(original(common["alert"], "alert"), context=context, failure=cases["failure"], recovery_window=recovery,
        topic_arn=cost["notification_topic_arn"], historical=historical)
    require(consumed == set(common["materials"]), "material-unused")
    if not historical:
        require(control.disabled_phase(provider, store, context["binding"], "proof-disable") == phases["proof-disable"],
            "acceptance-controls-changed")
    return evidence


def assemble_acceptance_evidence(provider, store, binding, *, package_paths, qualified_path, selection):
    """Assemble selected originals deterministically, then authenticate all of them.

    Selection names are merely local labels. They cannot select executable
    code, override deployed bindings or substitute an asserted success flag.
    Actual invocation/native capture remains with each existing evidence owner.
    """
    control, semantics = control_owner(), proof_semantics()
    require(isinstance(selection, dict) and set(selection) == {"schema", "materials", "observations", "connections", "cost", "alert"}
        and selection["schema"] == "deploy/scheduling-runtime-selection/v1"
        and isinstance(selection["materials"], dict)
        and 1 <= len(selection["materials"]) <= semantics.ARCHIVE_ROOT_LIMIT - (len(control.CONTROL_PHASES) - 1),
        "assembly-selection-invalid")
    require(isinstance(package_paths, dict) and set(package_paths) == {"dispatch", "worker"}, "assembly-packages-invalid")
    packages = control.qualified_pair(binding, package_paths)
    budget = control.cost_intent(store, binding)
    require(budget is not None and budget["source_revision"] == packages["dispatch"]["source_revision"], "assembly-budget-mismatch")
    expected = {"target": binding["target"], "scope": binding["scope"], "source_revision": budget["source_revision"],
        "primary_image_digest": budget["scopes"][binding["scope"]]["maintenance"]["image_digest"],
        "components": packages, "evidence_class": "live"}
    materials, labels, used = {}, {}, set()
    kinds = {"native", "preparation", "dispatch", "worker", "automatic", "preflight", "effect", "cost", "alert"}
    for name, source in selection["materials"].items():
        require(isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name)
            and isinstance(source, dict) and set(source) == {"kind", "path"} and source["kind"] in kinds
            and isinstance(source["path"], str), "assembly-material-invalid")
        packet = semantics.read(source["path"])
        if source["kind"] in semantics.ARCHIVE_KINDS:
            reference = semantics.pack_archive(packet, materials, kind=source["kind"])
        else:
            entry = {"kind": source["kind"], "packet": packet}
            reference = semantics.digest(entry)
            materials[reference] = entry
        labels[name] = reference
    nodes = 0
    def resolve(value, depth=0):
        nonlocal nodes
        nodes += 1
        require(depth <= 32 and nodes <= 4096, "assembly-selection-too-complex")
        if isinstance(value, dict):
            if value.get("schema") == "deploy/scheduling-material-selection/v1":
                require(set(value) == {"schema", "name"} and isinstance(value["name"], str)
                    and value["name"] in labels, "assembly-reference-invalid")
                used.add(value["name"])
                return labels[value["name"]]
            return {key: resolve(item, depth + 1) for key, item in value.items()}
        if isinstance(value, list): return [resolve(item, depth + 1) for item in value]
        require(value is None or type(value) in {str, int, float, bool}, "assembly-value-invalid")
        return value
    require(isinstance(selection["observations"], dict) and set(selection["observations"]) == semantics.CASES - {"cost-and-idle"},
        "assembly-cases-incomplete")
    observations = resolve(selection["observations"])
    common = {key: resolve(selection[key]) for key in ("connections", "cost", "alert")}
    require(used == set(labels), "assembly-material-unused")
    phases = {phase: control.capture_phase(provider, store, binding, phase) for phase in control.CONTROL_PHASES if phase != "accepted-enable"}
    context = release_context(phases, expected=expected)
    common.update(materials=materials, qualified_path=qualified_path,
        phases={phase: semantics.pack_archive(packet, materials, kind="phase") for phase, packet in phases.items()})
    observations["cost-and-idle"] = common
    evidence = {"schema": semantics.RUNTIME_SCHEMA, "evidence_class": "live", **{key: expected[key] for key in (
        "target", "scope", "source_revision", "primary_image_digest")},
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "components": {purpose: {"program_id": packages[purpose]["program_id"], "image_digest": packages[purpose]["image_digest"],
            "version_arn": runtime["version_arn"]} for purpose, runtime in context["runtime"].items()}, "observations": observations}
    return validate_acceptance_evidence(evidence, expected=expected)


def paid_rates(region):
    require(region == "eu-west-1", "region-unpriced")
    return {"endpoint_az_hour": Decimal("0.011"), "endpoint_gb": Decimal("0.01"),
            "lambda_gb_second": Decimal("0.0000166667"), "lambda_request": Decimal("0.0000002"),
            "sqs_request": Decimal("0.0000004"), "scheduler_tick": Decimal("0.000001"),
            "alarm_month": Decimal("0.10"), "ecr_gb_month": Decimal("0.10"),
            # Conservative combined ingestion+retention allowance, not a measured
            # bill or an assertion that both meters have the same AWS unit rate.
            "logs_gb_allowance": Decimal("0.60"),
            "fargate_vcpu_hour": Decimal("0.04048"), "fargate_gb_hour": Decimal("0.004445"),
            "rds_credit_vcpu_hour": Decimal("0.075"), "sns_request": Decimal("0.0000005"),
            "sns_email_delivery": Decimal("0.00002"), "sns_https_delivery": Decimal("0.0000006")}


def native_workload_context():
    """Reuse the existing native check, compiler-input projector and hasher."""
    import subprocess
    root = Path(__file__).resolve().parents[6]
    spec = importlib.util.spec_from_file_location("scheduling_cost_check_inputs", root / "scripts/repo/check-selection/script.py")
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    catalog = owner.coverage.document(root / "scripts/repo/check-selection/checks.yml")
    check = catalog.get("checks", {}).get("postgresql-disposable-diagnostics", {})
    command = ["bash", "scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-integration-check.sh"]
    require(check.get("argv") == command and check.get("stage") == "package"
        and isinstance(check.get("inputs"), list), "native-measurement-owner-mismatch")
    request = {"scripts": [{"npmScript": "platform:adapter:aws:persistence:postgresql:integration", "ignoreScripts": None}]}
    try:
        result = subprocess.run(["node", "scripts/repo/check-selection/check-inputs.mjs"], cwd=root,
            input=json.dumps(request), text=True, capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError): raise ProofFailure("native-measurement-inputs-unavailable") from None
    require(result.returncode == 0 and len(result.stdout) <= 2 * 1024**2, "native-measurement-inputs-unavailable")
    try: projected = json.loads(result.stdout)
    except (ValueError, RecursionError): raise ProofFailure("native-measurement-inputs-unavailable") from None
    require(isinstance(projected, dict) and isinstance(projected.get("contexts"), dict), "native-measurement-inputs-unavailable")
    context = projected["contexts"].get("platform:adapter:aws:persistence:postgresql:integration|inherit", {})
    require(isinstance(context.get("references"), list) and isinstance(projected.get("discoveryInputs"), list), "native-measurement-inputs-unavailable")
    references = set(check["inputs"]) | set(context["references"]) | set(projected["discoveryInputs"]) | {
        "scripts/repo/check-selection/check-inputs.mjs", "scripts/repo/check-selection/script.py", command[1]}
    return {"check_id": "postgresql-disposable-diagnostics", "command": command,
        "input_sha256": owner.fingerprint(root, references), "contract_sha256": hashlib.sha256(canonical(check)).hexdigest()}


def validate_native_workload_measurement(packet, *, expected_context=None):
    require(isinstance(packet, dict) and set(packet) == {"schema", "context", "completed_at", "elapsed_seconds", "cleanup_confirmed", "measurement"}
        and packet["schema"] == "deploy/scheduling-native-workload-receipt/v1" and packet["cleanup_confirmed"] is True,
        "native-measurement-packet-invalid")
    context = packet["context"]
    require(isinstance(context, dict) and set(context) == {"check_id", "command", "input_sha256", "contract_sha256"}
        and context["check_id"] == "postgresql-disposable-diagnostics"
        and context["command"] == ["bash", "scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-integration-check.sh"]
        and all(isinstance(context[key], str) and re.fullmatch(r"[a-f0-9]{64}", context[key]) for key in ("input_sha256", "contract_sha256")), "native-measurement-context-invalid")
    require(expected_context is None or context == expected_context, "native-measurement-inputs-changed")
    ADMISSION.utc(packet["completed_at"])
    require(0 < amount(packet["elapsed_seconds"]) <= 90, "native-measurement-time-invalid")
    measurement = packet["measurement"]
    require(isinstance(measurement, dict) and set(measurement) == {"event", "schema", "samples"}
        and measurement["event"] == "postgresql-disposable-scheduling-workload-measured"
        and measurement["schema"] == "kanbien/scheduling-native-workload/v1"
        and isinstance(measurement["samples"], list) and len(measurement["samples"]) == 2, "native-measurement-invalid")
    scopes = set()
    for row in measurement["samples"]:
        require(isinstance(row, dict) and set(row) == {"scope", "occurrences", "retained_bytes", "wal_bytes", "retained_bytes_per_occurrence",
            "wal_bytes_per_occurrence", "server_version_num", "block_size", "full_page_writes"}
            and row["scope"] in {"core-server-persistence", "entity-smoke"} and row["scope"] not in scopes
            and row["occurrences"] == 128 and row["block_size"] == 8192 and row["full_page_writes"] is True
            and type(row["server_version_num"]) is int and 170000 <= row["server_version_num"] < 190000, "native-measurement-sample-invalid")
        scopes.add(row["scope"])
        for name, limit in (("retained_bytes", 8192), ("wal_bytes", 262144)):
            require(type(row[name]) is int and 0 < row[name] <= 128 * limit
                and type(row[name + "_per_occurrence"]) is int and row[name + "_per_occurrence"] == (row[name] + 127) // 128,
                "native-measurement-allowance-exceeded")
    return measurement


def capture_native_workload_measurement():
    """Run the already-governed native owner once; no imported success JSON.

    Prior native execution took about 30 seconds. Ninety seconds includes its
    compiler, the additional 256 small transactions and bounded engine cleanup;
    the existing runner's own 20-second assertion deadline is unchanged.
    The controller retains this packet in existing cost/acceptance material.
    """
    import subprocess
    import time
    root = Path(__file__).resolve().parents[6]
    context = native_workload_context()
    began = time.monotonic()
    try:
        result = subprocess.run(context["command"], cwd=root, text=True, capture_output=True, timeout=90, check=False)
    except (OSError, subprocess.SubprocessError): raise ProofFailure("native-measurement-execution-unconfirmed") from None
    elapsed = time.monotonic() - began
    require(result.returncode == 0 and len(result.stdout) + len(result.stderr) <= 1024**2, "native-measurement-execution-unconfirmed")
    lines = result.stdout.splitlines()
    require(all(label in lines for label in ("PostgreSQL disposable integration proof passed.",
        "PostgreSQL disposable fixture engine cleanup passed.", "PostgreSQL disposable fixture directory cleanup passed.")), "native-measurement-cleanup-unconfirmed")
    records = []
    for line in lines:
        if not line.startswith('{"event":"postgresql-disposable-scheduling-workload-measured"'): continue
        try: records.append(json.loads(line))
        except (ValueError, RecursionError): raise ProofFailure("native-measurement-invalid") from None
    require(len(records) == 1 and native_workload_context() == context, "native-measurement-inputs-changed")
    packet = {"schema": "deploy/scheduling-native-workload-receipt/v1", "context": context,
        "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "elapsed_seconds": elapsed,
        "cleanup_confirmed": True, "measurement": records[0]}
    validate_native_workload_measurement(packet, expected_context=context)
    return packet


def regional_price_facts(*, fetch=None, now=None):
    """Read fixed official regional offers; never follow a caller-supplied URL.

    The five selected public prices are retained with SKU, unit and effective
    date. Other already-recorded paid rates remain conservative assumptions.
    A new offer does not silently change the admitted Fargate sizing arithmetic.
    """
    import urllib.error
    import urllib.request
    selected = {
        "AmazonECS": {"EU-Fargate-vCPU-Hours:perCPU": ("fargate_vcpu_hour", "hours"),
                      "EU-Fargate-GB-Hours": ("fargate_gb_hour", "hours")},
        "AmazonRDS": {"EU-RDS:GP3-Storage": ("storage_gb_month", "GB-Mo"),
                      "EU-RDS:ChargedBackupUsage": ("backup_gb_month", "GB-Mo"),
                      "EU-InstanceUsage:db.t4g.micro": ("rds_t4g_micro_instance_hour", "Hrs")},
    }
    def read(url):
        with urllib.request.urlopen(url, timeout=15) as response:
            require(response.geturl() == url, "price-source-redirected")
            return response.read(32 * 1024**2 + 1)
    current, facts = now or datetime.now(timezone.utc), {}
    for service, usages in selected.items():
        url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/" + service + "/current/eu-west-1/index.json"
        try:
            raw = (fetch or read)(url)
            require(isinstance(raw, bytes) and len(raw) <= 32 * 1024**2, "price-source-too-large")
            value = json.loads(raw)
        except (OSError, ValueError, RecursionError, UnicodeError):
            raise ProofFailure("price-source-unavailable") from None
        require(isinstance(value, dict) and value.get("offerCode") == service
            and isinstance(value.get("products"), dict) and isinstance(value.get("terms"), dict), "price-source-invalid")
        publication = value.get("publicationDate")
        # A current offer can legitimately remain unchanged for months. The
        # freshness boundary is this fixed HTTPS fetch, not AWS's release date.
        require(ADMISSION.utc(publication) <= current, "price-publication-in-future")
        for sku, product in value["products"].items():
            attributes = product.get("attributes", {}) if isinstance(product, dict) else {}
            usage = attributes.get("usagetype")
            if usage not in usages or attributes.get("regionCode") != "eu-west-1" or attributes.get("location") != "EU (Ireland)": continue
            if service == "AmazonRDS" and (attributes.get("databaseEngine") != "PostgreSQL" or attributes.get("deploymentOption") != "Single-AZ"): continue
            name, unit = usages[usage]
            if name == "rds_t4g_micro_instance_hour" and not (product.get("productFamily") == "Database Instance"
                and attributes.get("instanceType") == "db.t4g.micro" and attributes.get("operation") == "CreateDBInstance:0014"
                and attributes.get("licenseModel") == "No license required" and attributes.get("vcpu") == "2"):
                continue
            require(name not in facts and isinstance(sku, str) and re.fullmatch(r"[A-Z0-9]{16}", sku), "price-product-ambiguous")
            terms = value["terms"].get("OnDemand", {}).get(sku, {})
            require(isinstance(terms, dict) and len(terms) == 1, "price-term-ambiguous")
            term = next(iter(terms.values()))
            require(isinstance(term, dict) and term.get("sku") == sku and ADMISSION.utc(term.get("effectiveDate")) <= current,
                "price-term-invalid")
            dimensions = term.get("priceDimensions", {})
            require(isinstance(dimensions, dict) and len(dimensions) == 1, "price-dimension-ambiguous")
            dimension = next(iter(dimensions.values()))
            require(dimension.get("unit") == unit and dimension.get("beginRange") == "0"
                and dimension.get("endRange") == "Inf" and dimension.get("appliesTo") == [], "price-dimension-invalid")
            price = amount(dimension.get("pricePerUnit", {}).get("USD"))
            require(price > 0, "price-rate-invalid")
            facts[name] = {"sku": sku, "region": "eu-west-1", "unit": unit, "usd": str(price),
                "effective_at": term["effectiveDate"], "published_at": publication,
                "fetched_at": current.isoformat().replace("+00:00", "Z"), "source": url}
    require(set(facts) == {"fargate_vcpu_hour", "fargate_gb_hour", "storage_gb_month", "backup_gb_month", "rds_t4g_micro_instance_hour"}, "price-products-incomplete")
    rates = paid_rates("eu-west-1")
    require(all(amount(facts[key]["usd"]) == rates[key] for key in ("fargate_vcpu_hour", "fargate_gb_hour")), "price-rate-changed")
    return facts


# Bounded parsing capacity accommodates the 132-task mandatory proof route.
# This is neither launch permission nor a budget; the $10 arithmetic still gates every effect.
MAINTENANCE_CENSUS_LIMIT = 256


def maintenance_costs(provider, *, reservations, started_at, expires_at):
    """Size native originals, including uncertain tasks, without refunding them.

    The caller must read the complete original task-journal census under its
    existing operation lock. This function does not authenticate a supplied list
    or stop tasks. Every admitted task reserves its full remaining proof window.
    """
    start, expiry = ADMISSION.utc(started_at), ADMISSION.utc(expires_at)
    require(0 < (expiry - start).total_seconds() <= 86400, "maintenance-window-invalid")
    require(isinstance(reservations, list) and len(reservations) <= MAINTENANCE_CENSUS_LIMIT, "maintenance-census-invalid")
    rates, tasks, definitions = paid_rates("eu-west-1"), {}, {}
    for row in reservations:
        require(isinstance(row, dict) and set(row) == {"operation_id", "task_definition_arn", "reserved_at", "request_sha256"}, "maintenance-reservation-invalid")
        identity, arn = row["operation_id"], row["task_definition_arn"]
        require(isinstance(identity, str) and re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", identity) and identity not in tasks
            and isinstance(arn, str) and re.fullmatch(r"arn:aws:ecs:eu-west-1:[0-9]{12}:task-definition/[A-Za-z0-9_-]+:[1-9][0-9]*", arn)
            and isinstance(row["request_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", row["request_sha256"]), "maintenance-reservation-invalid")
        # Some original task owners never recorded a reservation timestamp. Do
        # not manufacture one: charge the whole budget window and retain null.
        stamp = row["reserved_at"]
        # Native Entity attempts write +00:00; preserve that original string in
        # the result and normalize only for this local UTC comparison.
        normalized = stamp[:-6] + "Z" if isinstance(stamp, str) and stamp.endswith("+00:00") else stamp
        try:
            reserved = start if stamp is None else ADMISSION.utc(normalized)
        except ADMISSION.AdmissionFailure:
            raise ProofFailure("maintenance-reservation-time-invalid") from None
        require(start <= reserved < expiry, "maintenance-reservation-time-invalid")
        if arn not in definitions:
            value = provider("ecs", "describe-task-definition", taskDefinition=arn).get("taskDefinition", {})
            require(value.get("taskDefinitionArn") == arn and value.get("cpu") == "256" and value.get("memory") == "512"
                and value.get("runtimePlatform", {}).get("operatingSystemFamily", "LINUX") == "LINUX"
                and value.get("runtimePlatform", {}).get("cpuArchitecture", "X86_64") == "X86_64"
                and "FARGATE" in value.get("requiresCompatibilities", [])
                and value.get("ephemeralStorage", {}).get("sizeInGiB", 20) == 20, "maintenance-task-size-unpriced")
            definitions[arn] = {"task_definition_arn": arn, "cpu_units": 256, "memory_mib": 512,
                "platform": "LINUX/X86_64", "ephemeral_gib": 20}
        seconds = max(60, int((expiry - reserved).total_seconds()) + 1)
        cost = Decimal(seconds) / 3600 * (Decimal("0.25") * rates["fargate_vcpu_hour"] + Decimal("0.5") * rates["fargate_gb_hour"])
        tasks[identity] = {**definitions[arn], "reserved_at": row["reserved_at"], "request_sha256": row["request_sha256"],
            "reservation_time_basis": "budget-window-upper-bound" if row["reserved_at"] is None else "original-reservation",
            "reserved_seconds": seconds, "reserved_usd": dollars(cost)}
    return {"schema": "deploy/scheduling-maintenance-cost/v1", "expires_at": expires_at, "tasks": tasks}


def cost_environment(provider, *, database, notification_topic_arn, region="eu-west-1", price_fetch=None, now=None):
    """Observe exact existing infrastructure and price its bounded proof use.

    No subscription endpoint, environment value or raw provider error is retained.
    Unsupported subscriptions/storage/task sizes are unpriced, never free.
    """
    paid_rates(region)
    require(isinstance(database, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,62}", database)
        and isinstance(notification_topic_arn, str) and re.fullmatch(r"arn:aws:sns:eu-west-1:[0-9]{12}:[A-Za-z0-9_-]+", notification_topic_arn), "cost-environment-selection-invalid")
    values = provider("rds", "describe-db-instances", DBInstanceIdentifier=database).get("DBInstances", [])
    require(len(values) == 1, "cost-database-ambiguous")
    value = values[0]
    require(value.get("DBInstanceIdentifier") == database and value.get("DBInstanceStatus") == "available"
        and value.get("Engine") == "postgres" and value.get("DBInstanceClass") == "db.t4g.micro"
        and value.get("MultiAZ") is False and value.get("StorageType") == "gp3"
        and value.get("AllocatedStorage") == 20 and value.get("MaxAllocatedStorage", 0) in (0, 20)
        and type(value.get("BackupRetentionPeriod")) is int and 0 <= value["BackupRetentionPeriod"] <= 7
        and isinstance(value.get("DbiResourceId"), str) and re.fullmatch(r"db-[A-Z0-9]+", value["DbiResourceId"]), "cost-database-unpriced")
    db = {"identifier": database, "resource_id": value["DbiResourceId"], "class": "db.t4g.micro",
        "allocated_gib": 20, "backup_days": value["BackupRetentionPeriod"], "storage_type": "gp3"}
    subscriptions = {"email": 0, "https": 0}
    rows = ADMISSION.collection(provider, "sns", "list-subscriptions-by-topic", "Subscriptions", TopicArn=notification_topic_arn)
    for row in rows:
        require(isinstance(row, dict) and row.get("TopicArn") == notification_topic_arn and row.get("Protocol") in subscriptions,
            "cost-subscription-unpriced")
        # Pending subscriptions still consume their full potential allowance.
        subscriptions[row["Protocol"]] += 1
    require(sum(subscriptions.values()) <= 20, "cost-subscription-limit")
    facts = regional_price_facts(fetch=price_fetch, now=now)
    material = {"database": db, "topic_arn": notification_topic_arn, "subscriptions": subscriptions, "price_facts": facts}
    return {"schema": "deploy/scheduling-cost-environment/v1", "database": db, "subscriptions": subscriptions,
        "prices": {key: facts[key]["usd"] for key in ("storage_gb_month", "backup_gb_month")},
        "evidence_sha256": hashlib.sha256(canonical(material)).hexdigest(), "material": material}


def resource_costs(*, reservations, environment, started_at, expires_at, now=None):
    """Price authenticated native originals; this function grants no effects.

    The controller owns the complete census, source/template observations and
    positive cleanup evidence under its existing admission mutex. Unknown
    operations remain charged. A two-hour clone target is not a provider TTL:
    obligations grow after it and new paid work must then stop. Successful
    recovery snapshots persist; the proof reserves their daily storage through
    the original budget window, while the monthly scenario prices retention.

    Backup storage is daily prorated, not second-billed. Charge every UTC date
    touched and use the shortest calendar month (28 days), conservatively.
    Clone backups reserve a full allocated copy for every inherited retention
    day, not an invented two-copy limit or free backup credit. Exported logs use
    the original proof's explicit shared allowance, not an asserted hard cap.
    """
    start, expiry = ADMISSION.utc(started_at), ADMISSION.utc(expires_at)
    current = now or datetime.now(timezone.utc)
    require(0 < (expiry - start).total_seconds() <= 86400 and current >= start, "resource-window-invalid")
    require(isinstance(environment, dict) and environment.get("schema") == "deploy/scheduling-cost-environment/v1"
        and isinstance(environment.get("material"), dict)
        and hashlib.sha256(canonical(environment["material"])).hexdigest() == environment.get("evidence_sha256")
        and environment.get("database") == environment["material"].get("database"), "cost-environment-mismatch")
    db, facts, rates = environment["database"], environment["material"].get("price_facts", {}), paid_rates("eu-west-1")
    require(isinstance(db, dict) and db.get("class") == "db.t4g.micro" and db.get("storage_type") == "gp3"
        and type(db.get("allocated_gib")) is int and db["allocated_gib"] == 20
        and type(db.get("backup_days")) is int and 0 <= db["backup_days"] <= 7
        and isinstance(db.get("resource_id"), str) and re.fullmatch(r"db-[A-Z0-9]+", db["resource_id"]), "resource-database-unpriced")
    prices = {}
    for key, unit in (("rds_t4g_micro_instance_hour", "Hrs"), ("storage_gb_month", "GB-Mo"), ("backup_gb_month", "GB-Mo")):
        fact = facts.get(key, {})
        require(isinstance(fact, dict) and set(fact) == {"sku", "region", "unit", "usd", "effective_at", "published_at", "fetched_at", "source"}
            and isinstance(fact["sku"], str) and re.fullmatch(r"[A-Z0-9]{16}", fact["sku"])
            and fact["region"] == "eu-west-1" and fact["unit"] == unit
            and fact["source"] == "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/eu-west-1/index.json"
            and ADMISSION.utc(fact["effective_at"]) <= ADMISSION.utc(fact["fetched_at"])
            and ADMISSION.utc(fact["published_at"]) <= ADMISSION.utc(fact["fetched_at"])
            and 0 <= (current - ADMISSION.utc(fact["fetched_at"])).total_seconds() <= 7 * 86400,
            "resource-price-invalid")
        prices[key] = amount(fact["usd"])
        require(prices[key] > 0, "resource-price-invalid")
    require(isinstance(reservations, list) and len(reservations) <= 100, "resource-census-invalid")
    resources, overdue = {}, []
    for row in reservations:
        require(isinstance(row, dict) and set(row) == {"operation_id", "request_sha256", "reserved_at", "kind", "source_resource_id",
            "allocated_gib", "instance_class", "backup_days", "log_exports", "absent_at"}, "resource-reservation-invalid")
        identity, kind = row["operation_id"], row["kind"]
        require(isinstance(identity, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", identity) and identity not in resources
            and isinstance(row["request_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", row["request_sha256"])
            and isinstance(kind, str) and kind in {"clone", "snapshot"} and row["source_resource_id"] == db["resource_id"]
            and type(row["allocated_gib"]) is int and row["allocated_gib"] == db["allocated_gib"]
            and type(row["backup_days"]) is int and row["backup_days"] == (db["backup_days"] if kind == "clone" else 0)
            and row["instance_class"] == (db["class"] if kind == "clone" else None)
            and isinstance(row["log_exports"], list) and all(isinstance(value, str) for value in row["log_exports"])
            and row["log_exports"] == sorted(set(row["log_exports"]))
            and set(row["log_exports"]) <= ({"postgresql", "iam-db-auth-error"} if kind == "clone" else set()), "resource-reservation-invalid")
        reserved = ADMISSION.utc(row["reserved_at"])
        absent = ADMISSION.utc(row["absent_at"]) if row["absent_at"] is not None else None
        require(start <= reserved <= current and (absent is None or reserved <= absent <= current), "resource-reservation-time-invalid")
        observed_end = absent or current
        target_end = reserved + timedelta(hours=2) if kind == "clone" else expiry
        charged_end = max(target_end, observed_end)
        seconds = int(Decimal(str((charged_end - reserved).total_seconds())).to_integral_value(rounding=ROUND_CEILING))
        days = (charged_end.date() - reserved.date()).days + 1
        hours = Decimal(seconds) / 3600
        if kind == "clone" and absent is None and current > target_end:
            overdue.append(identity)
        costs = ({"instance": hours * prices["rds_t4g_micro_instance_hour"],
            "cpu": hours * 2 * rates["rds_credit_vcpu_hour"],
            "storage": row["allocated_gib"] * prices["storage_gb_month"] * hours / (28 * 24),
            "backup": row["allocated_gib"] * row["backup_days"] * prices["backup_gb_month"] * days / 28}
            if kind == "clone" else {"snapshot": row["allocated_gib"] * prices["backup_gb_month"] * days / 28})
        priced = {key: dollars(value) for key, value in costs.items()}
        resources[identity] = {"request_sha256": row["request_sha256"], "kind": kind, "reserved_seconds": seconds,
            "backup_billed_dates": days, "costs_usd": priced, "reserved_usd": dollars(sum(amount(value) for value in priced.values()))}
    sources = sorted(reservations, key=lambda row: row["operation_id"])
    observed_at = current.isoformat().replace("+00:00", "Z")
    material = {"reservations": sources, "environment": environment, "started_at": started_at,
        "expires_at": expires_at, "observed_at": observed_at}
    return {"schema": "deploy/scheduling-proof-resource-cost/v1", "started_at": started_at, "expires_at": expires_at,
        "observed_at": observed_at, "reservations": sources,
        "resources": resources, "overdue_operation_ids": sorted(overdue),
        "inputs_sha256": hashlib.sha256(canonical(material)).hexdigest()}


def initial_cost_projection(*, region, image_bytes, maintenance, environment, resources, started_at):
    """Bounded proof worksheet; the effect owner enforces these resource limits.

    Maintenance entries are sized from native original task reservations. Unknown
    tasks retain their complete operator-managed lifetime allowance, never a
    refund based on a local observation timeout. Database/notification quantities
    come from cost_environment, not an arbitrary caller-written USD allowance.
    """
    rates = paid_rates(region)
    require(type(image_bytes) is int and 0 < image_bytes <= 4 * 1024**3, "image-envelope-exceeded")
    # Two one-minute dispatchers can produce 2,880 calls in the maximum day.
    # Reserve 4,000 total calls, including bounded workers/preflight/retries.
    limits = {"endpoint_hours": 24, "endpoint_azs": 2, "lambda_invocations": 4000,
              "lambda_timeout_seconds": 60, "lambda_memory_mb": 512,
              "sqs_requests": 50000, "log_gb": 1, "endpoint_gb": 1,
              "alarm_count": 8}
    require(isinstance(maintenance, dict) and set(maintenance) == {"schema", "expires_at", "tasks"}
        and maintenance["schema"] == "deploy/scheduling-maintenance-cost/v1" and isinstance(maintenance["tasks"], dict), "maintenance-cost-invalid")
    require(len(maintenance["tasks"]) <= MAINTENANCE_CENSUS_LIMIT, "maintenance-census-invalid")
    start, expiry = ADMISSION.utc(started_at), ADMISSION.utc(maintenance["expires_at"])
    require(0 < (expiry - start).total_seconds() <= 86400, "maintenance-window-invalid")
    for identity, task in maintenance["tasks"].items():
        require(isinstance(identity, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", identity)
            and isinstance(task, dict) and set(task) == {"task_definition_arn", "cpu_units", "memory_mib", "platform", "ephemeral_gib",
                "reserved_at", "request_sha256", "reservation_time_basis", "reserved_seconds", "reserved_usd"}
            and task["cpu_units"] == 256 and task["memory_mib"] == 512 and task["platform"] == "LINUX/X86_64"
            and task["ephemeral_gib"] == 20 and type(task["reserved_seconds"]) is int and 60 <= task["reserved_seconds"] <= 86401,
            "maintenance-cost-invalid")
        require(task["reservation_time_basis"] == ("budget-window-upper-bound" if task["reserved_at"] is None else "original-reservation"),
            "maintenance-cost-mismatch")
        expected = Decimal(task["reserved_seconds"]) / 3600 * (Decimal(".25") * rates["fargate_vcpu_hour"] + Decimal(".5") * rates["fargate_gb_hour"])
        require(task["reserved_usd"] == dollars(expected), "maintenance-cost-mismatch")
    require(isinstance(environment, dict) and set(environment) == {"schema", "database", "subscriptions", "prices", "evidence_sha256", "material"}
        and environment["schema"] == "deploy/scheduling-cost-environment/v1", "cost-environment-invalid")
    require(hashlib.sha256(canonical(environment["material"])).hexdigest() == environment["evidence_sha256"]
        and environment["material"].get("database") == environment["database"]
        and environment["material"].get("subscriptions") == environment["subscriptions"], "cost-environment-mismatch")
    db, subscriptions, prices = environment["database"], environment["subscriptions"], environment["prices"]
    require(isinstance(db, dict) and type(db.get("allocated_gib")) is int and 0 < db["allocated_gib"] <= 20
        and type(db.get("backup_days")) is int and 0 <= db["backup_days"] <= 7, "cost-database-invalid")
    require(isinstance(subscriptions, dict) and set(subscriptions) == {"email", "https"}
        and all(type(value) is int and 0 <= value <= 20 for value in subscriptions.values()), "cost-notifications-invalid")
    require(isinstance(prices, dict) and set(prices) == {"storage_gb_month", "backup_gb_month"}
        and all(amount(value) > 0 for value in prices.values()), "cost-database-pricing-required")
    require(all(environment["material"].get("price_facts", {}).get(key, {}).get("usd") == value for key, value in prices.items()), "cost-environment-mismatch")
    require(isinstance(resources, dict) and resources == resource_costs(reservations=resources.get("reservations"), environment=environment,
        started_at=started_at, expires_at=maintenance["expires_at"], now=ADMISSION.utc(resources.get("observed_at"))), "resource-cost-mismatch")
    require(not resources["overdue_operation_ids"], "resource-cleanup-overdue")
    costs = {
        "endpoint": 24 * 2 * rates["endpoint_az_hour"],
        "lambda_compute": 4000 * 60 * Decimal("0.5") * rates["lambda_gb_second"],
        "lambda_requests": 4000 * rates["lambda_request"],
        "scheduler_ticks": 2 * 1440 * rates["scheduler_tick"],
        "queue_requests": 50000 * rates["sqs_request"],
        "logs": rates["logs_gb_allowance"],
        "endpoint_data": rates["endpoint_gb"],
        "alarms": 8 * rates["alarm_month"] / 31,
        "images": Decimal(image_bytes) / 1024**3 * rates["ecr_gb_month"] / 31,
        # The original authenticated intent bounds this proof's source CPU use;
        # both vCPUs are charged fully, without borrowing any accrued credits.
        "database_cpu": 2 * Decimal(str((expiry - start).total_seconds())) / 3600 * rates["rds_credit_vcpu_hour"],
        "database_storage_and_backup": db["allocated_gib"] * (amount(prices["storage_gb_month"])
            + db["backup_days"] * amount(prices["backup_gb_month"])) / 31,
        # Every alarm could change state each minute. No subscription free tier.
        "notifications": 8 * 1440 * (rates["sns_request"] + sum(subscriptions[protocol] * rates["sns_" + protocol + "_delivery"] for protocol in subscriptions)),
        **{"maintenance:" + identity: amount(value["reserved_usd"]) for identity, value in maintenance["tasks"].items()},
        **{"resource:" + identity: amount(value["reserved_usd"]) for identity, value in resources["resources"].items()},
    }
    costs = {key: amount(dollars(value)) for key, value in costs.items()}
    total = sum(costs.values())
    require(total <= 10, "proof-budget-exceeded")
    return {"schema": "deploy/scheduling-proof-cost-envelope/v1", "region": region,
            "free_tier_assumed": False, "limits": limits, "costs_usd": {k: dollars(v) for k, v in costs.items()},
            "projected_usd": dollars(total), "ceiling_usd": "10.00",
            "started_at": started_at, "expires_at": maintenance["expires_at"],
            "inputs_sha256": hashlib.sha256(canonical({"image_bytes": image_bytes, "maintenance": maintenance,
                "environment": environment, "resources": resources, "started_at": started_at})).hexdigest(),
            "qualification": "operator-managed-lifetimes-and-complete-native-reservations-required"}


def admit_cost_effect(*, projection, retained, operation_id, started_at, now=None):
    """Return a cost field to reserve in the EXISTING original operation request.

    Fixed owners must collect every native original, including uncertain effects,
    and serialize census+reservation across ALL participating effect owners.
    Per-file exclusive creation does not provide that cross-operation lock. A
    supplied list alone is not proof of census completeness. Shared infrastructure is
    counted once; prior maxima and unique task reserves can never be refunded.
    """
    current, start = now or datetime.now(timezone.utc), ADMISSION.utc(started_at)
    require(isinstance(projection, dict) and projection.get("schema") == "deploy/scheduling-proof-cost-envelope/v1"
        and projection.get("region") == "eu-west-1" and projection.get("ceiling_usd") == "10.00"
        and projection.get("started_at") == started_at, "cost-projection-invalid")
    expiry = ADMISSION.utc(projection.get("expires_at"))
    require(start <= current < expiry and 0 < (expiry - start).total_seconds() <= 86400, "cost-budget-expired")
    require(isinstance(operation_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", operation_id)
        and isinstance(retained, list) and len(retained) <= 500, "cost-reservations-invalid")
    costs = {key: amount(value) for key, value in projection.get("costs_usd", {}).items()}
    require(costs and dollars(sum(costs.values())) == projection.get("projected_usd"), "cost-projection-mismatch")
    seen = set()
    for previous in retained:
        require(isinstance(previous, dict) and set(previous) == {"schema", "operation_id", "started_at", "expires_at", "projection_sha256", "costs_usd", "reserved_usd"}
            and previous["schema"] == "deploy/scheduling-cost-reservation/v1"
            and previous["started_at"] == started_at and previous["expires_at"] == projection["expires_at"]
            and isinstance(previous["operation_id"], str) and previous["operation_id"] not in seen
            and previous["operation_id"] != operation_id and isinstance(previous["projection_sha256"], str)
            and re.fullmatch(r"[a-f0-9]{64}", previous["projection_sha256"]), "cost-reservation-mismatch")
        seen.add(previous["operation_id"])
        old = {key: amount(value) for key, value in previous["costs_usd"].items()}
        require(dollars(sum(old.values())) == previous["reserved_usd"], "cost-reservation-mismatch")
        for key, value in old.items(): costs[key] = max(costs.get(key, Decimal(0)), value)
    total = sum(costs.values())
    require(total <= 10, "proof-budget-exceeded")
    return {"schema": "deploy/scheduling-cost-reservation/v1", "operation_id": operation_id, "started_at": started_at,
        "expires_at": projection["expires_at"], "projection_sha256": hashlib.sha256(canonical(projection)).hexdigest(),
        "costs_usd": {key: dollars(value) for key, value in costs.items()}, "reserved_usd": dollars(total)}


def monthly_cost_projection(*, region, samples, image_bytes, priced_extras):
    """Project 100k combined jobs using actual billed-time samples from both scopes.

    Caller must authenticate the original invocation/report evidence and extra
    cost-source digests. A returned projection alone never admits activation.
    Full due-dispatch cost is charged per job, in addition to every idle minute;
    this deliberately overcounts batching. A 25% compute/request margin is added.
    The controlled failure's timeout is not represented as normal job performance.
    """
    rates = paid_rates(region)
    require(type(image_bytes) is int and 0 < image_bytes <= 4 * 1024**3, "image-envelope-exceeded")
    require(isinstance(samples, list) and 6 <= len(samples) <= 1000, "cost-samples-incomplete")
    groups, requests = {}, set()
    for sample in samples:
        require(isinstance(sample, dict) and set(sample) == {
            "scope", "kind", "version_arn", "request_id", "billed_duration_ms", "memory_mb", "evidence_sha256"}, "cost-sample-invalid")
        scope, kind = sample["scope"], sample["kind"]
        require(isinstance(scope, str) and re.fullmatch(r"[a-z][a-z0-9-]{1,63}", scope), "cost-scope-invalid")
        require(kind in {"idle-dispatch", "due-dispatch", "worker"}, "cost-sample-kind-invalid")
        require(isinstance(sample["version_arn"], str) and re.fullmatch(
            r"arn:aws:lambda:eu-west-1:[0-9]{12}:function:[A-Za-z0-9_-]+:[1-9][0-9]*", sample["version_arn"]), "cost-function-invalid")
        require(isinstance(sample["request_id"], str) and re.fullmatch(
            r"[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}", sample["request_id"]), "cost-request-invalid")
        request = (sample["version_arn"], sample["request_id"])
        require(request not in requests, "cost-sample-duplicated")
        requests.add(request)
        require(isinstance(sample["evidence_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", sample["evidence_sha256"]), "cost-provenance-missing")
        require(type(sample["memory_mb"]) is int and sample["memory_mb"] == 512, "cost-memory-mismatch")
        duration = amount(sample["billed_duration_ms"])
        require(0 < duration <= 120000, "cost-duration-invalid")
        groups.setdefault(scope, {}).setdefault(kind, []).append(duration / 1000 * Decimal(sample["memory_mb"]) / 1024)
    require(len(groups) == 2 and all(set(value) == {"idle-dispatch", "due-dispatch", "worker"} for value in groups.values()), "cost-samples-incomplete")
    extra_names = {"database_cpu", "database_storage_and_backup", "recovery_snapshots", "notifications", "data_transfer"}
    require(isinstance(priced_extras, dict) and set(priced_extras) == extra_names, "cost-extras-incomplete")
    extras = {}
    for name, item in priced_extras.items():
        require(isinstance(item, dict) and set(item) == {"usd", "evidence_sha256"}
                and isinstance(item["evidence_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", item["evidence_sha256"]), "cost-extras-unpriced")
        extras[name] = amount(item["usd"])
    minutes = 31 * 24 * 60
    jobs = 100000
    margin = Decimal("1.25")
    idle = sum(max(group["idle-dispatch"]) for group in groups.values()) * minutes
    due = max(max(group["due-dispatch"]) for group in groups.values()) * jobs
    worker = max(max(group["worker"]) for group in groups.values()) * jobs
    gb_seconds = (idle + due + worker) * margin
    costs = {
        "endpoint": 31 * 24 * 2 * rates["endpoint_az_hour"],
        "alarms": 8 * rates["alarm_month"],
        "scheduler_ticks": 2 * minutes * rates["scheduler_tick"],
        "lambda_compute": gb_seconds * rates["lambda_gb_second"],
        "lambda_requests": (2 * minutes + 2 * jobs) * margin * rates["lambda_request"],
        "queue_requests_allowance": 2000000 * rates["sqs_request"],
        "logs_allowance": 2 * rates["logs_gb_allowance"],
        "endpoint_data_allowance": 10 * rates["endpoint_gb"],
        "images": Decimal(image_bytes) / 1024**3 * rates["ecr_gb_month"],
        **extras,
    }
    total = sum(costs.values())
    return {"schema": "deploy/scheduling-monthly-cost-projection/v1", "region": region, "days": 31,
            "combined_jobs": jobs, "free_tier_assumed": False, "compute_request_margin": str(margin),
            "billed_gb_seconds": dollars(gb_seconds), "costs_usd": {k: dollars(v) for k, v in costs.items()},
            "projected_usd": dollars(total), "ceiling_usd": "25.00", "within_ceiling": total <= 25,
            "inputs_sha256": hashlib.sha256(canonical({"samples": samples, "image_bytes": image_bytes, "priced_extras": priced_extras})).hexdigest()}


def observed_monthly_cost_projection(provider, *, components, database, notification_topic_arn,
                                     endpoint_id, started_at, ended_at, native_measurement=None, price_fetch=None, now=None):
    """Capture an expected fixed-workload forecast, not an arbitrary-load ceiling.

    The native packet must come from capture_native_workload_measurement and the
    controller's original retained material, never a caller's numeric estimate.
    Reuse checks its current compiler/check inputs. Historical validation instead
    uses the accepted material's existing immutable custody, without live reads.
    Shared paired metrics remain an attribution assumption, stated in the result.
    """
    current = now or datetime.now(timezone.utc)
    start, end = cost_observation_window(started_at, ended_at, current)
    native = native_measurement if native_measurement is not None else capture_native_workload_measurement()
    validate_native_workload_measurement(native, expected_context=native_workload_context())
    require(isinstance(components, dict) and set(components) == {"core-server-persistence", "entity-smoke"}, "cost-components-incomplete")
    windows, image_uris = {}, set()
    for scope, pair in components.items():
        require(isinstance(pair, dict) and set(pair) == {"dispatch", "worker"}, "cost-components-incomplete")
        for purpose, expected in pair.items():
            require(isinstance(expected, dict) and expected.get("purpose") == purpose, "cost-component-invalid")
            packet = capture_runtime_window(provider, expected=expected, started_at=started_at, ended_at=ended_at)
            windows[scope + ":" + purpose] = packet
            image_uris.add(expected["image_uri"])
    images, total_image_bytes = {}, 0
    for uri in sorted(image_uris):
        match = re.fullmatch(r"([0-9]{12})\.dkr\.ecr\.eu-west-1\.amazonaws\.com/([a-z0-9][a-z0-9._/-]*)@(sha256:[a-f0-9]{64})", uri)
        require(match is not None, "cost-image-invalid")
        account, repository, digest = match.groups()
        rows = provider("ecr", "describe-images", registryId=account, repositoryName=repository,
            imageIds=[{"imageDigest": digest}]).get("imageDetails", [])
        require(len(rows) == 1 and rows[0].get("imageDigest") == digest
            and rows[0].get("registryId") == account and rows[0].get("repositoryName") == repository
            and type(rows[0].get("imageSizeInBytes")) is int and rows[0]["imageSizeInBytes"] > 0, "cost-image-observation-invalid")
        images[uri] = rows[0]["imageSizeInBytes"]
        total_image_bytes += images[uri]
    environment = cost_environment(provider, database=database, notification_topic_arn=notification_topic_arn,
        price_fetch=price_fetch, now=current)
    require(isinstance(endpoint_id, str) and re.fullmatch(r"vpce-[a-f0-9]{8,17}", endpoint_id), "cost-endpoint-invalid")
    rows = provider("ec2", "describe-vpc-endpoints", VpcEndpointIds=[endpoint_id]).get("VpcEndpoints", [])
    require(len(rows) == 1 and rows[0].get("VpcEndpointId") == endpoint_id and rows[0].get("State") == "available"
        and rows[0].get("VpcEndpointType") == "Interface" and rows[0].get("ServiceName") == "com.amazonaws.eu-west-1.sqs"
        and isinstance(rows[0].get("VpcId"), str) and re.fullmatch(r"vpc-[a-f0-9]{8,17}", rows[0]["VpcId"]), "cost-endpoint-mismatch")
    endpoint = {key: rows[0][key] for key in ("VpcEndpointId", "VpcId", "ServiceName", "VpcEndpointType")}
    metrics = {}
    def measured(name, namespace, dimensions, statistic, *, period="work"):
        beginning, ending = {"work": (start, end), "idle": (start - timedelta(seconds=900), start),
            "baseline": (start - timedelta(days=1), start)}[period]
        lower, upper = (value.isoformat().replace("+00:00", "Z") for value in (beginning, ending))
        value = provider("cloudwatch", "get-metric-statistics", Namespace=namespace, MetricName=name,
            Dimensions=dimensions, StartTime=lower, EndTime=upper, Period=300, Statistics=[statistic])
        points = value.get("Datapoints", [])
        count = int((ending - beginning).total_seconds()) // 300
        require(isinstance(points, list) and 1 <= len(points) <= count, "cost-metric-missing")
        selected, stamps = [], set()
        for point in points:
            stamp = point.get("Timestamp")
            if isinstance(stamp, datetime): stamp = stamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            elif isinstance(stamp, str) and stamp.endswith("+00:00"): stamp = stamp[:-6] + "Z"
            parsed = ADMISSION.utc(stamp)
            require(beginning <= parsed < ending and parsed not in stamps and int(parsed.timestamp()) % 300 == 0, "cost-metric-time-invalid")
            stamps.add(parsed)
            selected.append({"timestamp": stamp, "value": str(amount(point.get(statistic)))})
        # RDS emits every five minutes; absent continuous samples are not zeros.
        # PrivateLink emits only for traffic. Its missing periods remain covered
        # by the independent fixed endpoint-data allowance in the final model.
        if namespace == "AWS/RDS":
            require(len(stamps) == count, "cost-metric-incomplete")
        selected.sort(key=lambda point: point["timestamp"])
        metrics[period + ":" + name] = {"namespace": namespace, "dimensions": dimensions, "statistic": statistic,
            "started_at": lower, "ended_at": upper, "points": selected}
        return [amount(point["value"]) for point in selected]
    db_dimensions = [{"Name": "DBInstanceIdentifier", "Value": database}]
    for period in ("work", "idle", "baseline"):
        measured("CPUCreditUsage", "AWS/RDS", db_dimensions, "Sum", period=period)
    for name, statistic in (("FreeStorageSpace", "Minimum"), ("CPUCreditBalance", "Minimum"), ("CPUUtilization", "Average")):
        measured(name, "AWS/RDS", db_dimensions, statistic, period="baseline")
    measured("FreeStorageSpace", "AWS/RDS", db_dimensions, "Minimum")
    for name in ("NetworkReceiveThroughput", "NetworkTransmitThroughput"):
        for period in ("work", "idle"):
            measured(name, "AWS/RDS", db_dimensions, "Maximum", period=period)
    measured("BytesProcessed", "AWS/PrivateLinkEndpoints", [
        {"Name": "Endpoint Type", "Value": "Interface"}, {"Name": "Service Name", "Value": endpoint["ServiceName"]},
        {"Name": "VPC Endpoint Id", "Value": endpoint_id}, {"Name": "VPC Id", "Value": endpoint["VpcId"]}], "Sum")
    alarms = []
    periods = {"dispatch-silence": 3, "dispatch-errors": 1, "queue-age": 2, "dead-letter": 1}
    for scope in components:
        names = ["kanbien-core-platform-" + scope + "-scheduling-" + suffix for suffix in periods]
        rows = provider("cloudwatch", "describe-alarms", AlarmNames=names).get("MetricAlarms", [])
        require(isinstance(rows, list) and len(rows) == 4 and {row.get("AlarmName") for row in rows} == set(names), "cost-alarm-policy-missing")
        for row in rows:
            suffix = row["AlarmName"].split("-scheduling-", 1)[1]
            require(row.get("Period") == 60 and row.get("EvaluationPeriods") == periods[suffix]
                and row.get("DatapointsToAlarm", periods[suffix]) == periods[suffix]
                and row.get("AlarmActions") == [notification_topic_arn] and row.get("OKActions") == [notification_topic_arn]
                and row.get("InsufficientDataActions", []) == [], "cost-alarm-policy-mismatch")
            alarms.append({"name": row["AlarmName"], "period": 60, "evaluation_periods": periods[suffix], "transitions": ["ALARM", "OK"]})
    deliveries = []
    for row in ADMISSION.collection(provider, "sns", "list-subscriptions-by-topic", "Subscriptions", TopicArn=notification_topic_arn):
        protocol, arn = row.get("Protocol"), row.get("SubscriptionArn")
        require(protocol in {"email", "https"} and isinstance(arn, str) and arn.startswith(notification_topic_arn + ":"), "cost-subscription-unconfirmed")
        attributes = provider("sns", "get-subscription-attributes", SubscriptionArn=arn).get("Attributes", {})
        require(attributes.get("TopicArn") == notification_topic_arn and attributes.get("Protocol") == protocol
            and attributes.get("PendingConfirmation", "false") == "false" and not attributes.get("RedrivePolicy"), "cost-subscription-policy-unpriced")
        attempts = 50
        if protocol == "https":
            try: policy = json.loads(attributes.get("EffectiveDeliveryPolicy", ""))
            except (ValueError, TypeError): raise ProofFailure("cost-subscription-policy-unpriced") from None
            retries = policy.get("healthyRetryPolicy", {}).get("numRetries") if isinstance(policy, dict) else None
            require(type(retries) is int and 0 <= retries <= 100, "cost-subscription-policy-unpriced")
            attempts = 1 + retries
        deliveries.append({"protocol": protocol, "maximum_delivery_attempts": attempts})
    require({protocol: sum(row["protocol"] == protocol for row in deliveries) for protocol in ("email", "https")} == environment["subscriptions"], "cost-subscriptions-changed")
    material = {"environment": environment, "runtime_windows": windows, "images": images, "endpoint": endpoint,
        "started_at": started_at, "ended_at": ended_at, "observed_at": current.isoformat().replace("+00:00", "Z"),
        "metrics": metrics, "alarms": sorted(alarms, key=lambda row: row["name"]), "deliveries": deliveries, "native_measurement": native}
    return project_observed_monthly_cost(material)


def project_observed_monthly_cost(material):
    """Replay retained, already-custodied observations; this is not provenance.

    Assumptions describe only the two fixed jobs. Paired shared metrics are an
    engineering estimate, not causal isolation; sensitivity and retained-space
    runway are reported separately. No completed-metadata cleanup is assumed.
    """
    require(isinstance(material, dict) and set(material) == {"environment", "runtime_windows", "images", "endpoint",
        "started_at", "ended_at", "observed_at", "metrics", "alarms", "deliveries", "native_measurement"}, "cost-material-invalid")
    observed = ADMISSION.utc(material["observed_at"])
    start, end = cost_observation_window(material["started_at"], material["ended_at"], observed)
    validate_native_workload_measurement(material["native_measurement"])
    environment = material["environment"]
    require(isinstance(environment, dict) and set(environment) == {"schema", "database", "subscriptions", "prices", "evidence_sha256", "material"}
        and environment["schema"] == "deploy/scheduling-cost-environment/v1"
        and hashlib.sha256(canonical(environment["material"])).hexdigest() == environment["evidence_sha256"]
        and environment["database"] == environment["material"].get("database")
        and environment["subscriptions"] == environment["material"].get("subscriptions"), "cost-environment-mismatch")
    db, rates = environment["database"], paid_rates("eu-west-1")
    require(db.get("class") == "db.t4g.micro" and db.get("allocated_gib") == 20 and db.get("storage_type") == "gp3"
        and type(db.get("backup_days")) is int and 0 <= db["backup_days"] <= 7, "cost-database-unpriced")
    for key in ("storage_gb_month", "backup_gb_month"):
        fact = environment["material"].get("price_facts", {}).get(key, {})
        require(fact.get("region") == "eu-west-1" and fact.get("unit") == "GB-Mo"
            and amount(fact.get("usd")) == amount(environment["prices"].get(key))
            and ADMISSION.utc(fact.get("effective_at")) <= ADMISSION.utc(fact.get("fetched_at"))
            and ADMISSION.utc(fact.get("published_at")) <= ADMISSION.utc(fact.get("fetched_at"))
            and 0 <= (observed - ADMISSION.utc(fact.get("fetched_at"))).total_seconds() <= 7 * 86400,
            "cost-price-mismatch")
    scopes = {"core-server-persistence", "entity-smoke"}
    windows, samples, images = material["runtime_windows"], [], set()
    require(isinstance(windows, dict) and set(windows) == {scope + ":" + purpose for scope in scopes for purpose in ("dispatch", "worker")}, "cost-components-incomplete")
    for key, packet in windows.items():
        scope, purpose = key.split(":")
        require(packet.get("started_at") == material["started_at"] and packet.get("ended_at") == material["ended_at"]
            and packet.get("expected", {}).get("purpose") == purpose, "cost-runtime-window-mismatch")
        expected = packet["expected"]; images.add(expected["image_uri"])
        for row in validate_runtime_window(packet, expected=expected):
            observation = row["observation"]
            if purpose == "worker":
                if observation["idempotency"] != "durable-processed": continue
                kind = "worker"
            else:
                result, delivery = observation["result"], observation["result"]["delivery"]
                if delivery is not None and delivery["deliveryCreated"] > 0 and result["published"] > 0: kind = "due-dispatch"
                elif (delivery is None or delivery["inspected"] == 0) and result["relayAttempts"] == result["published"] == 0: kind = "idle-dispatch"
                else: continue
            samples.append({"scope": scope, "kind": kind, "version_arn": expected["version_arn"], "request_id": observation["request_id"],
                "billed_duration_ms": row["billed_duration_ms"], "memory_mb": row["memory_mb"], "evidence_sha256": row["evidence_sha256"]})
    require(isinstance(material["images"], dict) and set(material["images"]) == images
        and all(type(value) is int and value > 0 for value in material["images"].values()), "cost-image-observation-invalid")
    metrics, parsed_metrics = material["metrics"], {}
    expected_metrics = {period + ":CPUCreditUsage": "Sum" for period in ("work", "idle", "baseline")}
    expected_metrics.update({"baseline:" + name: statistic for name, statistic in
        (("FreeStorageSpace", "Minimum"), ("CPUCreditBalance", "Minimum"), ("CPUUtilization", "Average"))})
    expected_metrics.update({period + ":" + name: "Maximum" for period in ("work", "idle")
        for name in ("NetworkReceiveThroughput", "NetworkTransmitThroughput")})
    expected_metrics.update({"work:FreeStorageSpace": "Minimum", "work:BytesProcessed": "Sum"})
    require(isinstance(metrics, dict) and set(metrics) == set(expected_metrics), "cost-metrics-incomplete")
    endpoint = material["endpoint"]
    require(isinstance(endpoint, dict) and set(endpoint) == {"VpcEndpointId", "VpcId", "ServiceName", "VpcEndpointType"}
        and endpoint["ServiceName"] == "com.amazonaws.eu-west-1.sqs" and endpoint["VpcEndpointType"] == "Interface", "cost-endpoint-mismatch")
    for key, statistic in expected_metrics.items():
        period, name = key.split(":")
        beginning, ending = {"work": (start, end), "idle": (start - timedelta(minutes=15), start), "baseline": (start - timedelta(days=1), start)}[period]
        row = metrics[key]
        require(isinstance(row, dict) and set(row) == {"namespace", "dimensions", "statistic", "started_at", "ended_at", "points"}
            and row["statistic"] == statistic and ADMISSION.utc(row["started_at"]) == beginning
            and ADMISSION.utc(row["ended_at"]) == ending and isinstance(row["points"], list), "cost-metric-invalid")
        private = name == "BytesProcessed"
        dimensions = ([{"Name": "Endpoint Type", "Value": "Interface"}, {"Name": "Service Name", "Value": endpoint["ServiceName"]},
            {"Name": "VPC Endpoint Id", "Value": endpoint["VpcEndpointId"]}, {"Name": "VPC Id", "Value": endpoint["VpcId"]}]
            if private else [{"Name": "DBInstanceIdentifier", "Value": db["identifier"]}])
        count = int((ending - beginning).total_seconds()) // 300
        require(row["namespace"] == ("AWS/PrivateLinkEndpoints" if private else "AWS/RDS") and row["dimensions"] == dimensions
            and (1 <= len(row["points"]) <= count if private else len(row["points"]) == count), "cost-metric-incomplete")
        stamps, values = set(), []
        for point in row["points"]:
            require(isinstance(point, dict) and set(point) == {"timestamp", "value"}, "cost-metric-invalid")
            stamp = ADMISSION.utc(point["timestamp"])
            require(beginning <= stamp < ending and stamp not in stamps and int(stamp.timestamp()) % 300 == 0, "cost-metric-time-invalid")
            stamps.add(stamp); values.append(amount(point["value"]))
        parsed_metrics[key] = values
    periods = {"dispatch-silence": 3, "dispatch-errors": 1, "queue-age": 2, "dead-letter": 1}
    expected_alarms = [{"name": "kanbien-core-platform-" + scope + "-scheduling-" + suffix,
        "period": 60, "evaluation_periods": count, "transitions": ["ALARM", "OK"]} for scope in scopes for suffix, count in periods.items()]
    require(material["alarms"] == sorted(expected_alarms, key=lambda row: row["name"]), "cost-alarm-policy-mismatch")
    deliveries = material["deliveries"]
    require(isinstance(deliveries, list) and len(deliveries) <= 20, "cost-subscription-policy-unpriced")
    for row in deliveries:
        require(isinstance(row, dict) and set(row) == {"protocol", "maximum_delivery_attempts"}
            and row["protocol"] in {"email", "https"} and type(row["maximum_delivery_attempts"]) is int
            and (row["maximum_delivery_attempts"] == 50 if row["protocol"] == "email" else 1 <= row["maximum_delivery_attempts"] <= 101), "cost-subscription-policy-unpriced")
    require({protocol: sum(row["protocol"] == protocol for row in deliveries) for protocol in ("email", "https")} == environment["subscriptions"], "cost-subscriptions-changed")
    processed = sum(sample["kind"] == "worker" for sample in samples)
    require(processed > 0, "cost-work-samples-missing")
    fingerprint = hashlib.sha256(canonical(material)).hexdigest()
    baseline_credits = sum(parsed_metrics["baseline:CPUCreditUsage"])
    incremental_credits = max(Decimal(0), sum(parsed_metrics["work:CPUCreditUsage"]) - sum(parsed_metrics["idle:CPUCreditUsage"]))
    free_bytes = min(parsed_metrics["baseline:FreeStorageSpace"] + parsed_metrics["work:FreeStorageSpace"])
    baseline_utilization = max(parsed_metrics["baseline:CPUUtilization"])
    require(baseline_utilization <= 100 and free_bytes <= 20 * 1024**3, "cost-database-metric-invalid")
    def scenario(retry_fraction):
        attempts = Decimal(100000) * (1 + retry_fraction)
        factor = attempts / processed
        retained = attempts * 8192
        backup_gib = (retained / 2 + attempts * 262144 * db["backup_days"] / 31) / 1024**3
        # db.t4g.micro's paid baseline earns 12 credits/hour. Count only the
        # additional over-baseline credits; existing paid CPU is not free tier.
        existing_month, earned_month = baseline_credits * 31, Decimal(12 * 24 * 31)
        added_month = incremental_credits * factor * Decimal("1.25")
        charged = max(Decimal(0), existing_month + added_month - earned_month) - max(Decimal(0), existing_month - earned_month)
        notifications = 8 + Decimal(100000) * retry_fraction * 8 * 2
        # Each affected occurrence is pessimistically allowed to trigger all
        # alarms and their recovery. Delivery failure is the same explicit
        # scenario fraction, charged through each observed retry policy.
        notification_rate = rates["sns_request"] + sum(rates["sns_" + row["protocol"] + "_delivery"]
            * (1 + retry_fraction * (row["maximum_delivery_attempts"] - 1)) for row in deliveries)
        added_network = sum(max(Decimal(0), max(parsed_metrics["work:" + name]) - max(parsed_metrics["idle:" + name]))
            for name in ("NetworkReceiveThroughput", "NetworkTransmitThroughput")) * 900 * factor
        # Protocol traffic allowance is an explicit engineering assumption, not
        # a claim that WAL bytes equal network bytes. Paired measurements can
        # increase it. Both cross-AZ sides are charged without locality credit.
        added_network = max(added_network, attempts * 262144)
        endpoint_gib = sum(parsed_metrics["work:BytesProcessed"]) * (31 * 86400 / Decimal(900)) / 1024**3
        extra = {"database_cpu": charged / 60 * rates["rds_credit_vcpu_hour"],
            "database_storage_and_backup": backup_gib * amount(environment["prices"]["backup_gb_month"]),
            # One retained canonical recovery point per accepted scope. This
            # source-owned forecast is not proof that the live census is exact;
            # activation must independently reconcile both original identities
            # and reject extra/unknown survivors or a remaining proof clone.
            "recovery_snapshots": 2 * db["allocated_gib"] * amount(environment["prices"]["backup_gb_month"]),
            "notifications": notifications * notification_rate,
            "data_transfer": added_network / 1024**3 * 2 * rates["endpoint_gb"]
                + max(Decimal(0), endpoint_gib - 10) * rates["endpoint_gb"]}
        # Existing arithmetic already adds 25% to compute/requests; explicitly
        # add the scenario's retries too, without altering the 100k originals.
        scaled = [{**sample, "billed_duration_ms": str(amount(sample["billed_duration_ms"]) * (1 + retry_fraction))} for sample in samples]
        projected = monthly_cost_projection(region="eu-west-1", samples=scaled, image_bytes=sum(material["images"].values()),
            priced_extras={key: {"usd": dollars(value), "evidence_sha256": fingerprint} for key, value in extra.items()})
        # Additional retry request fees are not duration based.
        retry_requests = Decimal(200000) * retry_fraction * Decimal("1.25") * rates["lambda_request"]
        projected["costs_usd"]["lambda_requests"] = dollars(amount(projected["costs_usd"]["lambda_requests"]) + retry_requests)
        total = sum(amount(value) for value in projected["costs_usd"].values())
        supported = free_bytes >= retained + 2 * 1024**3 and existing_month + added_month <= 2 * 60 * 24 * 31
        return {"retry_attention_fraction": str(retry_fraction), "costs_usd": projected["costs_usd"], "projected_usd": dollars(total),
            "within_ceiling": total <= 25, "capacity_supported": supported, "retained_growth_gib": dollars(retained / 1024**3),
            "backup_allowance_gib": dollars(backup_gib), "notification_publications": int(notifications),
            "database_added_cpu_credits": dollars(added_month), "database_extra_charged_credits": dollars(charged),
            "retention_runway_months": dollars(max(Decimal(0), free_bytes - 2 * 1024**3) / retained)}
    expected, sensitivity = scenario(Decimal("0.01")), scenario(Decimal("0.10"))
    return {"schema": "deploy/scheduling-monthly-cost-observation/v1", "region": "eu-west-1", "days": 31,
        "combined_jobs": 100000, "free_tier_assumed": False, "compute_request_margin": "1.25", "expected": expected,
        "sensitivity": sensitivity, "projected_usd": expected["projected_usd"], "ceiling_usd": "25.00", "projection_complete": True,
        "within_ceiling": expected["within_ceiling"], "capacity_supported": expected["capacity_supported"],
        "assumptions": {"workload": "two-fixed-source-owned-jobs", "retained_bytes_per_attempt": 8192, "wal_bytes_per_attempt": 262144,
            "protocol_bytes_per_attempt": 262144, "retained_metadata_cleanup": False, "storage_safety_gib": 2,
            "retained_recovery_snapshots": 2, "recovery_snapshot_gib_each": db["allocated_gib"],
            "cpu_credit_basis": "paired-shared-window-delta-plus-25-percent;12-paid-baseline-credits-per-hour",
            "baseline_cpu_peak_percent": str(baseline_utilization), "baseline_minimum_cpu_credit_balance": str(min(parsed_metrics["baseline:CPUCreditBalance"])),
            "shared_traffic_basis": "whole-endpoint-time-rate;paired-database-delta-with-protocol-allowance",
            "backup_basis": "half-month-retained-growth-plus-retained-WAL-engineering-allowance;no-free-backup-credit"},
        "observed_inputs": material, "observed_inputs_sha256": fingerprint,
        "qualification": "expected-declared-workload-with-assumptions;not-a-guaranteed-spend-ceiling"}


def validate_monthly_cost_observation(packet, *, components, native_context, database, notification_topic_arn, endpoint_id):
    """Pure historical replay. Original source/material custody is caller-owned."""
    require(isinstance(packet, dict) and isinstance(packet.get("observed_inputs"), dict), "cost-packet-invalid")
    require(isinstance(components, dict) and set(components) == {"core-server-persistence", "entity-smoke"}, "cost-components-incomplete")
    material = packet["observed_inputs"]
    require(isinstance(native_context, dict), "cost-native-custody-missing")
    validate_native_workload_measurement(material.get("native_measurement"), expected_context=native_context)
    require(material.get("environment", {}).get("database", {}).get("identifier") == database
        and material.get("environment", {}).get("material", {}).get("topic_arn") == notification_topic_arn
        and material.get("endpoint", {}).get("VpcEndpointId") == endpoint_id, "cost-environment-custody-mismatch")
    for scope, pair in components.items():
        require(isinstance(pair, dict) and set(pair) == {"dispatch", "worker"}, "cost-components-incomplete")
        for purpose, expected in pair.items():
            value = material.get("runtime_windows", {}).get(scope + ":" + purpose, {})
            require(value.get("expected") == expected, "cost-runtime-custody-mismatch")
    require(project_observed_monthly_cost(material) == packet, "cost-projection-mismatch")
    require(packet["within_ceiling"] is True and packet["capacity_supported"] is True, "monthly-cost-or-capacity-exceeded")
    return packet


def cost_observation_window(started_at, ended_at, observed):
    """One guard shared by fresh capture, retained replay and early admission."""
    start, end = ADMISSION.utc(started_at), ADMISSION.utc(ended_at)
    require((end - start).total_seconds() == 900 and end <= observed <= end + timedelta(hours=1)
        and int(start.timestamp()) % 300 == 0, "cost-observation-window-invalid")
    return start, end


def cost_evidence_paths(store, binding):
    """Fixed companions to one original cost intent, not a new operation store."""
    control = control_owner()
    require(binding.get("target") == "kanbien-core-platform" and binding.get("scope") in {"core-server-persistence", "entity-smoke"}, "cost-capture-binding-invalid")
    paths = [store.root / (binding["target"] + suffix) for suffix in ("-monthly-cost.json", "-monthly-native.json")]
    for path in paths: control.RESERVATIONS.no_symlinks(path)
    return paths


def read_cost_evidence(path):
    """Read bounded private material without echoing paths or provider content."""
    import os
    try:
        control_owner().RESERVATIONS.no_symlinks(path)
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as handle:
            info = os.fstat(handle.fileno())
            require(info.st_uid == os.getuid() and not info.st_mode & 0o077 and info.st_nlink == 1
                and info.st_size <= 4 * 1024**2, "cost-capture-material-unsafe")
            return json.loads(handle.read())
    except ProofFailure:
        raise
    except (OSError, ValueError, RecursionError):
        raise ProofFailure("cost-capture-material-unavailable") from None


def cost_evidence_context(intent, phases, binding, *, components, database, notification_topic_arn, endpoint_id):
    """Pure binding of the original budget, shared endpoint and two workloads."""
    control = control_owner()
    scopes = {"core-server-persistence", "entity-smoke"}
    require(isinstance(intent, dict) and intent.get("schema") == "deploy/scheduling-cost-intent/v1"
        and intent.get("target") == binding["target"] and intent.get("database") == database
        and intent.get("notification_topic_arn") == notification_topic_arn
        and isinstance(intent.get("scopes"), dict) and set(intent["scopes"]) == scopes
        and isinstance(phases, dict) and set(phases) == {"network-create", *scopes}
        and isinstance(components, dict) and set(components) == scopes, "cost-capture-original-binding-invalid")
    source = intent["source_revision"]
    network = phases["network-create"]
    checked_network = control.validate_phase_evidence(network, target=binding["target"], scope="shared",
        source_revision=source, predecessor_sha256=None)
    require(checked_network["phase"] == "network-create"
        and checked_network["state"]["resources"]["SchedulingSqsEndpoint"] == {"ResourceType": "AWS::EC2::VPCEndpoint", "PhysicalResourceId": endpoint_id}, "cost-capture-endpoint-mismatch")
    require(ADMISSION.utc(intent["started_at"]) <= ADMISSION.utc(network["intent"]["created_at"])
        and ADMISSION.utc(intent["started_at"]) < ADMISSION.utc(intent["expires_at"]), "cost-capture-original-time-invalid")
    resources = set()
    for scope in sorted(scopes):
        packet = phases[scope]
        checked = control.validate_phase_evidence(packet, target=binding["target"], scope=scope, source_revision=source,
            predecessor_sha256=control.digest(network["intent"]))
        parameters = checked["parameters"]
        require(checked["phase"] == "scope-create-disabled" and parameters.get("Scope") == scope
            and parameters.get("SourceRevision") == source and parameters.get("AlarmTopicArn") == notification_topic_arn
            and parameters.get("VpcId") == checked_network["parameters"].get("VpcId")
            and parameters.get("PrivateSubnetIds") == checked_network["parameters"].get("PrivateSubnetIds")
            and parameters.get("EndpointSecurityGroupId") == checked_network["state"]["resources"]["SchedulingEndpointSecurityGroup"]["PhysicalResourceId"]
            and ADMISSION.utc(checked_network["completed_at"].replace("+00:00", "Z")) <= ADMISSION.utc(packet["intent"]["created_at"]), "cost-capture-scope-mismatch")
        resources.add(parameters["DatabaseResourceId"])
        pair, packages = components[scope], intent["scopes"][scope]["packages"]
        require(isinstance(pair, dict) and set(pair) == {"dispatch", "worker"}
            and isinstance(packages, dict) and set(packages) == {"dispatch", "worker"}, "cost-components-incomplete")
        logs = checked["state"]["resources"].get("RuntimeLogs", {})
        require(logs.get("ResourceType") == "AWS::Logs::LogGroup"
            and isinstance(logs.get("PhysicalResourceId"), str) and logs["PhysicalResourceId"], "cost-capture-log-group-missing")
        for purpose in ("dispatch", "worker"):
            versions = [row["PhysicalResourceId"] for name, row in checked["state"]["resources"].items()
                if name.startswith(purpose.title() + "Version") and row["ResourceType"] == "AWS::Lambda::Version"]
            package = packages[purpose]
            require(len(versions) == 1 and package.get("source_revision") == source
                and parameters[purpose.title() + "ImageUri"].endswith("@" + package["image_digest"]), "cost-capture-package-mismatch")
            expected = {"purpose": purpose, "source_revision": source, "version_arn": versions[0],
                "image_uri": parameters[purpose.title() + "ImageUri"],
                "log_group": logs["PhysicalResourceId"]}
            require(pair[purpose] == expected, "cost-capture-runtime-mismatch")
    require(len(resources) == 1, "cost-capture-database-mismatch")
    return {"resource_id": next(iter(resources)), "vpc_id": checked_network["parameters"]["VpcId"]}


def cost_capture_current_source(intent):
    """A read-only source check; historical replay deliberately never calls it."""
    import subprocess
    control = control_owner()
    try:
        head = subprocess.run(["git", "-C", str(control.ROOT), "rev-parse", "HEAD"], check=True, text=True, capture_output=True, timeout=10).stdout.strip()
        changes = subprocess.run(["git", "-C", str(control.ROOT), "status", "--porcelain", "--untracked-files=normal", "--",
            "apps", "packages", "platform", "infra", "scripts", ".github"], check=True, text=True, capture_output=True, timeout=10).stdout
        require(head == intent["source_revision"] and not changes.strip(), "cost-capture-source-changed")
        for selected in intent["scopes"].values():
            require(all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == checksum
                for path, checksum in selected["receipt_files"].items()), "cost-capture-package-changed")
    except (OSError, subprocess.SubprocessError):
        raise ProofFailure("cost-capture-source-unavailable") from None


def validate_cost_evidence(packet, binding, *, components, database, notification_topic_arn, endpoint_id):
    """Pure accepted-material replay, not an authority to trust imported JSON."""
    require(isinstance(packet, dict) and set(packet) == {"schema", "target", "intent", "intent_sha256", "phases", "components", "database",
        "notification_topic_arn", "endpoint_id", "started_at", "ended_at", "native_context", "projection", "captured_at", "recovery_resources"}
        and packet["schema"] == "deploy/scheduling-cost-evidence/v1" and packet["target"] == binding["target"]
        and packet["intent_sha256"] == control_owner().digest(packet["intent"])
        and packet["components"] == components and packet["database"] == database
        and packet["notification_topic_arn"] == notification_topic_arn and packet["endpoint_id"] == endpoint_id, "cost-capture-packet-mismatch")
    selected = cost_evidence_context(packet["intent"], packet["phases"], binding, components=components,
        database=database, notification_topic_arn=notification_topic_arn, endpoint_id=endpoint_id)
    projection = packet["projection"]
    validate_monthly_cost_observation(projection, components=components, native_context=packet["native_context"],
        database=database, notification_topic_arn=notification_topic_arn, endpoint_id=endpoint_id)
    material = projection["observed_inputs"]
    validate_cost_recovery_resources(packet["recovery_resources"], intent=packet["intent"],
        resource_id=selected["resource_id"], captured_at=packet["captured_at"])
    require(projection["assumptions"]["retained_recovery_snapshots"] == len(packet["recovery_resources"]["snapshots"])
        and projection["assumptions"]["recovery_snapshot_gib_each"] == 20, "cost-capture-recovery-price-mismatch")
    require(material["started_at"] == packet["started_at"] and material["ended_at"] == packet["ended_at"]
        and material["environment"]["database"]["resource_id"] == selected["resource_id"]
        and material["endpoint"]["VpcId"] == selected["vpc_id"]
        and ADMISSION.utc(material["observed_at"]) <= ADMISSION.utc(packet["captured_at"])
        and ADMISSION.utc(packet["started_at"]) >= max(ADMISSION.utc(packet["phases"][scope]["terminal"]["Timestamp"].replace("+00:00", "Z"))
            for scope in components), "cost-capture-observation-mismatch")
    return packet


def authenticate_cost_evidence(provider, store, binding, packet, *, components, database, notification_topic_arn, endpoint_id, historical=False):
    """Reuse original observations; live reads never rerun metrics/prices/native SQL."""
    validate_cost_evidence(packet, binding, components=components, database=database,
        notification_topic_arn=notification_topic_arn, endpoint_id=endpoint_id)
    if historical:
        return packet
    control = control_owner()
    path, native_path = cost_evidence_paths(store, binding)
    require(read_cost_evidence(path) == packet and control.cost_intent(store, binding) == packet["intent"], "cost-capture-original-mismatch")
    native = read_cost_evidence(native_path)
    require(native == {"schema": "deploy/scheduling-cost-native/v1", "target": binding["target"], "intent_sha256": packet["intent_sha256"],
        "measurement": packet["projection"]["observed_inputs"]["native_measurement"]}, "cost-capture-native-original-mismatch")
    current = datetime.now(timezone.utc)
    require(0 <= (current - ADMISSION.utc(packet["ended_at"])).total_seconds() <= 3600
        and ADMISSION.utc(packet["captured_at"]) <= current, "cost-capture-stale")
    cost_capture_current_source(packet["intent"])
    require(native_workload_context() == packet["native_context"], "native-measurement-inputs-changed")
    for key, phase in packet["phases"].items():
        selected = binding if key == "network-create" else control.load_binding(binding["target"], key)
        control.authenticate_phase_evidence(provider, store, selected, phase)
    for pair in components.values():
        for expected in pair.values():
            runtime_function(provider("lambda", "get-function", FunctionName=expected["version_arn"]), expected)
    rows = provider("rds", "describe-db-instances", DBInstanceIdentifier=database).get("DBInstances", [])
    require(len(rows) == 1 and rows[0].get("DBInstanceIdentifier") == database
        and rows[0].get("DbiResourceId") == packet["projection"]["observed_inputs"]["environment"]["database"]["resource_id"]
        and rows[0].get("DBInstanceStatus") == "available", "cost-capture-database-changed")
    require(control.recovery_acceptance_resources(provider, store, binding) == packet["recovery_resources"],
        "cost-capture-recovery-resources-changed")
    return packet


def collect_cost_evidence(provider, store, binding, *, components, database, notification_topic_arn, endpoint_id, started_at, ended_at):
    """Capture once per original cost intent; immutable evidence is never refreshed.

    This distinct capture mutex may span bounded read-only measurements. It does
    not hold the target effect-admission lock or prevent safe control shutdown.
    A failed later read keeps the immediately retained native result for reuse.
    """
    import os
    control = control_owner()
    path, native_path = cost_evidence_paths(store, binding)
    marker = b"scheduling-monthly-cost-capture/v1\n"
    try:
        with control.JOURNAL.locked(path, path.with_suffix(".lock"), marker, read_cost_evidence) as (_path, descriptor, retained):
            if retained is not None:
                require(retained.get("started_at") == started_at and retained.get("ended_at") == ended_at, "cost-capture-window-changed")
                return authenticate_cost_evidence(provider, store, binding, retained, components=components, database=database,
                    notification_topic_arn=notification_topic_arn, endpoint_id=endpoint_id)
            cost_observation_window(started_at, ended_at, datetime.now(timezone.utc))
            intent = control.cost_intent(store, binding)
            require(intent is not None, "cost-capture-original-required")
            cost_capture_current_source(intent)
            phases = {"network-create": control.capture_phase(provider, store, binding, "network-create")}
            for scope in ("core-server-persistence", "entity-smoke"):
                selected = control.load_binding(binding["target"], scope)
                phases[scope] = control.capture_phase(provider, store, selected, "scope-create-disabled")
            cost_evidence_context(intent, phases, binding, components=components, database=database,
                notification_topic_arn=notification_topic_arn, endpoint_id=endpoint_id)
            for key, phase in phases.items():
                selected = binding if key == "network-create" else control.load_binding(binding["target"], key)
                control.authenticate_phase_evidence(provider, store, selected, phase)
            recovery = control.recovery_acceptance_resources(provider, store, binding)
            context = native_workload_context()
            if native_path.exists():
                native = read_cost_evidence(native_path)
                require(isinstance(native, dict) and set(native) == {"schema", "target", "intent_sha256", "measurement"}
                    and native["schema"] == "deploy/scheduling-cost-native/v1" and native["target"] == binding["target"]
                    and native["intent_sha256"] == control.digest(intent), "cost-capture-native-original-mismatch")
            else:
                native = {"schema": "deploy/scheduling-cost-native/v1", "target": binding["target"], "intent_sha256": control.digest(intent),
                    "measurement": capture_native_workload_measurement()}
                validate_native_workload_measurement(native["measurement"], expected_context=context)
                require(control.RESERVATIONS.write_exclusive(native_path, native), "cost-capture-native-retention-uncertain")
            validate_native_workload_measurement(native["measurement"], expected_context=context)
            projection = observed_monthly_cost_projection(provider, components=components, database=database,
                notification_topic_arn=notification_topic_arn, endpoint_id=endpoint_id, started_at=started_at, ended_at=ended_at,
                native_measurement=native["measurement"])
            packet = {"schema": "deploy/scheduling-cost-evidence/v1", "target": binding["target"], "intent": intent,
                "intent_sha256": control.digest(intent), "phases": phases, "components": components, "database": database,
                "notification_topic_arn": notification_topic_arn, "endpoint_id": endpoint_id, "started_at": started_at, "ended_at": ended_at,
                "native_context": context, "projection": projection, "recovery_resources": recovery,
                "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
            validate_cost_evidence(packet, binding, components=components, database=database, notification_topic_arn=notification_topic_arn, endpoint_id=endpoint_id)
            require(control.cost_intent(store, binding) == intent and native_workload_context() == context, "cost-capture-inputs-changed")
            require(control.recovery_acceptance_resources(provider, store, binding) == recovery, "cost-capture-recovery-resources-changed")
            cost_capture_current_source(intent)
            require(len(canonical(packet)) <= 2 * 1024**2 and control.RESERVATIONS.write_exclusive(path, packet), "cost-capture-retention-uncertain")
            os.write(descriptor, marker); os.fsync(descriptor)
            return packet
    except control.JOURNAL.JournalFailure:
        raise ProofFailure("cost-capture-busy-or-metadata-invalid") from None


def validate_cost_recovery_resources(value, *, intent, resource_id, captured_at):
    """Replay the fixed native owner's retained census, without live reads.

    Accepted-material custody authenticates this original observation. Live
    collection and reuse separately call the native owner, including positive
    clone cleanup and current absence; a summary alone grants no authority.
    """
    require(isinstance(value, dict) and set(value) == {"schema", "intent_sha256", "snapshots", "clones"}
        and value["schema"] == "deploy/scheduling-retained-recovery-resources/v1"
        and value["intent_sha256"] == control_owner().digest(intent)
        and isinstance(value["snapshots"], dict) and set(value["snapshots"]) == {"core-server-persistence", "entity-smoke"}
        and isinstance(value["clones"], list) and 2 <= len(value["clones"]) <= 100, "cost-capture-recovery-resources-invalid")
    identities, snapshots, clone_ids = set(), set(), []
    start, captured = ADMISSION.utc(intent["started_at"]), ADMISSION.utc(captured_at)
    for kind, row in [("snapshot", row) for row in value["snapshots"].values()] + [("clone", row) for row in value["clones"]]:
        fields = {"operation_id", "request_sha256"} | ({"snapshot", "source_resource_id", "allocated_gib"} if kind == "snapshot" else {"absent_at"})
        require(isinstance(row, dict) and set(row) == fields
            and isinstance(row["operation_id"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", row["operation_id"])
            and row["operation_id"] not in identities and isinstance(row["request_sha256"], str)
            and re.fullmatch(r"[a-f0-9]{64}", row["request_sha256"]), "cost-capture-recovery-resources-invalid")
        identities.add(row["operation_id"])
        if kind == "snapshot":
            require(isinstance(row["snapshot"], str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,254}", row["snapshot"])
                and row["snapshot"] not in snapshots and row["source_resource_id"] == resource_id
                and type(row["allocated_gib"]) is int and row["allocated_gib"] == 20, "cost-capture-recovery-resources-invalid")
            snapshots.add(row["snapshot"])
        else:
            require(isinstance(row["absent_at"], str) and start <= ADMISSION.utc(row["absent_at"]) <= captured,
                "cost-capture-recovery-cleanup-time-invalid")
            clone_ids.append(row["operation_id"])
    require(clone_ids == sorted(clone_ids), "cost-capture-recovery-resources-invalid")
    return value
