#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.scheduling-control
#   version: 3
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.scheduling
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove exact scheduler release/network declarations and single-submission reconciliation with a controlled provider.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.capability.scheduling-control
#     path: scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py
import copy
import base64
import hashlib
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import zipfile
import uuid
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("scheduler_control_test_subject", Path(__file__).with_name("script.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def rejects(fn, code=None):
    try:
        fn()
    except (M.Failure, M.ADMISSION.AdmissionFailure, AssertionError) as failure:
        if code is not None:
            assert failure.code == code, (failure.code, code)
        return
    raise AssertionError("unsafe counterexample accepted")


def check_templates(scheduling=None, network=None):
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    scheduling = scheduling or M.CF.template((M.ROOT / binding["template"]).read_text())
    network = network or M.CF.template((M.ROOT / binding["network_template"]).read_text())
    for control in ("TickEnabled", "WorkerEnabled", "DenyDispatcherSend"):
        assert scheduling["Parameters"][control]["Default"] == "false"
    resources = scheduling["Resources"]
    fault = resources["QueueTransportPolicy"]["Properties"]["PolicyDocument"]["Statement"][1]["Fn::If"]
    assert fault == ["DispatcherSendDenied", {"Effect": "Deny", "Principal": "*", "Action": "sqs:SendMessage",
        "Resource": {"Fn::GetAtt": ["JobQueue", "Arn"]}, "Condition": {"ArnEquals": {"aws:PrincipalArn": {"Fn::GetAtt": ["DispatchRole", "Arn"]}}}}, {"Ref": "AWS::NoValue"}]
    assert resources["WorkerMapping"]["Properties"]["Enabled"] == {"Fn::If": ["WorkerActivated", True, False]}
    assert resources["FixedTick"]["Properties"]["State"] == {"Fn::If": ["TickActivated", "ENABLED", "DISABLED"]}
    assert resources["WorkerMapping"]["Properties"]["FunctionName"] == {"Ref": "WorkerVersion"}
    assert resources["FixedTick"]["Properties"]["Target"]["Arn"] == {"Ref": "DispatchVersion"}
    assert resources["DispatchAsyncFailure"]["Properties"]["Qualifier"] == {"Fn::GetAtt": ["DispatchVersion", "Version"]}
    assert resources["DispatchAsyncFailure"]["UpdateReplacePolicy"] == resources["DispatchAsyncFailure"]["DeletionPolicy"] == "Retain"
    assert resources["WorkerMapping"]["Properties"]["BatchSize"] == 1
    assert resources["WorkerMapping"]["Properties"]["FunctionResponseTypes"] == ["ReportBatchItemFailures"]
    assert resources["JobQueue"]["Properties"]["VisibilityTimeout"] == 360
    assert resources["JobQueue"]["Properties"]["RedrivePolicy"]["maxReceiveCount"] == 5
    for purpose in ("Dispatch", "Worker"):
        assert resources[purpose + "Version"]["DeletionPolicy"] == "Retain"
        assert resources[purpose + "Function"]["Properties"]["Timeout"] == 60
        assert resources[purpose + "Function"]["Properties"]["MemorySize"] == 512
    assert resources["FixedTick"]["Properties"]["ScheduleExpression"] == "rate(1 minute)"
    assert not {row["Type"] for row in resources.values()} & {"AWS::RDS::DBInstance", "AWS::EC2::VPCEndpoint", "AWS::EC2::NatGateway", "AWS::ECS::Service"}
    alarms = [row["Properties"] for row in resources.values() if row["Type"] == "AWS::CloudWatch::Alarm"]
    assert len(alarms) == 4
    assert {row["MetricName"] for row in alarms} == {"Invocations", "Errors", "ApproximateAgeOfOldestMessage", "ApproximateNumberOfMessagesVisible"}
    assert all(row["AlarmActions"] == row["OKActions"] == [{"Ref": "AlarmTopicArn"}] for row in alarms)
    assert resources["DispatchSilenceAlarm"]["Properties"]["ActionsEnabled"] == {"Fn::If": ["TickActivated", True, False]}
    endpoint = network["Resources"]["SchedulingSqsEndpoint"]["Properties"]
    assert endpoint["PrivateDnsEnabled"] is True
    assert endpoint["SecurityGroupIds"] == [{"Ref": "SchedulingEndpointSecurityGroup"}]
    assert set(network["Resources"]) == {"SchedulingEndpointSecurityGroup", "SchedulingSqsEndpoint"}
    ingress = network["Resources"]["SchedulingEndpointSecurityGroup"]["Properties"]["SecurityGroupIngress"]
    assert ingress == [{"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "SourceSecurityGroupId": {"Ref": key}}
                       for key in ("LegacyWorkerSecurityGroupId", "LegacyRelaySecurityGroupId")]
    statements = endpoint["PolicyDocument"]["Statement"]
    assert len(statements) == 5
    assert statements[0]["Resource"] == [{"Fn::Sub": "arn:${AWS::Partition}:sqs:${AWS::Region}:${AWS::AccountId}:kanbien-core-platform-" + scope + "-scheduling" + suffix} for scope in ("core-server-persistence", "entity-smoke") for suffix in ("", "-dlq")]
    for row, queue, role, actions in zip(statements[1:],
            ["LegacyWorkerQueueArn"] * 2 + ["LegacyRelationalQueueArn"] * 2,
            ["LegacyRelayRoleArn", "LegacyWorkerRoleArn", "LegacyRelationalRelayRoleArn", "LegacyRelationalWorkerRoleArn"],
            ["sqs:SendMessage", ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"]] * 2):
        assert row["Resource"] == {"Ref": queue}
        assert row["Action"] == actions
        assert row["Condition"] == {"ArnEquals": {"aws:PrincipalArn": {"Ref": role}},
            "StringEquals": {"aws:PrincipalAccount": {"Ref": "AWS::AccountId"}}, "Bool": {"aws:SecureTransport": "true"}}
    return scheduling, network


class FakeProvider:
    def __init__(self, template, parameters):
        self.template, self.parameters = template, parameters
        self.calls, self.preparation, self.execution = [], None, None
        self.status = "CREATE_COMPLETE"
        self.lose_prepare = self.lose_execute = False
        self.mutate = lambda row: row

    def __call__(self, service, operation, **args):
        self.calls.append((service, operation, args))
        if operation == "create-change-set":
            assert self.preparation is None
            self.preparation = args["ClientToken"]
            assert args["Description"] == self.preparation
            if self.lose_prepare:
                raise M.Failure("aws-command-timeout", "unknown")
            return {}
        if operation == "execute-change-set":
            assert self.execution is None
            self.execution = args["ClientRequestToken"]
            if self.lose_execute:
                raise M.Failure("aws-command-timeout", "unknown")
            return {}
        if operation == "describe-change-set":
            if self.preparation is None:
                raise M.Failure("aws-resource-missing", "unknown")
            return self.mutate({"Description": self.preparation, "Status": "CREATE_COMPLETE",
                "ExecutionStatus": "EXECUTE_COMPLETE" if self.execution else "AVAILABLE",
                "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in self.parameters.items()],
                "Changes": [{"ResourceChange": {"LogicalResourceId": key, "ResourceType": value["Type"], "Action": "Add", "Replacement": "False"}} for key, value in self.template["Resources"].items()]})
        if operation == "get-template":
            return {"TemplateBody": self.template}
        if operation == "describe-stacks":
            return {"Stacks": [{"StackId": "stack-id", "StackStatus": self.status}]}
        if operation == "describe-stack-events":
            return {"StackEvents": [{"PhysicalResourceId": "stack-id", "ClientRequestToken": self.execution, "ResourceStatus": self.status}]}
        raise AssertionError(operation)


def test_reservations():
    template = {"Resources": {"Queue": {"Type": "AWS::SQS::Queue"}}}
    parameters = {"Scope": "sample"}
    request = {"stack": "sample-scheduling", "change_set": "scheduling-scope-create-disabled", "control_phase": "scope-create-disabled", "inputs_sha256": "a" * 64}
    for lost in ("prepare", "execute", None):
        with tempfile.TemporaryDirectory() as scratch:
            provider = FakeProvider(template, parameters)
            store = M.Store(Path(scratch))
            setattr(provider, "lose_" + (lost or "prepare"), lost is not None)
            args = dict(request=request, template=template, parameters=parameters, mode="CREATE", action="execute", target="sample", admit=lambda: None)
            if lost:
                rejects(lambda: M.control(provider, store, **args), "aws-command-timeout")
            result = M.control(provider, store, **args)
            assert result == {"verdict": "completed", "code": "stack-operation-completed"}
            assert sum(row[1] == "create-change-set" for row in provider.calls) == 1
            assert sum(row[1] == "execute-change-set" for row in provider.calls) == 1
            # Re-running after success only observes the same original operation.
            M.control(provider, store, **args)
            assert sum(row[1] == "execute-change-set" for row in provider.calls) == 1
    with tempfile.TemporaryDirectory() as scratch:
        provider = FakeProvider(template, parameters)
        store = M.Store(Path(scratch))
        args = dict(request=request, template=template, parameters=parameters, mode="CREATE", action="prepare", target="sample", admit=lambda: None)
        assert M.control(provider, store, **args)["verdict"] == "reviewed"
        assert not any(row[1] == "execute-change-set" for row in provider.calls)
        for mutation, code in [
            (lambda row: {**row, "Description": "foreign"}, "change-set-lineage-mismatch"),
            (lambda row: {**row, "Parameters": []}, "change-set-parameters-mismatch"),
            (lambda row: {**row, "Changes": [{"ResourceChange": {"LogicalResourceId": "Foreign", "ResourceType": "AWS::RDS::DBInstance", "Action": "Add"}}]}, "change-set-resource-unowned"),
            (lambda row: {**row, "Changes": [{"ResourceChange": {"LogicalResourceId": "Queue", "ResourceType": "AWS::SQS::Queue", "Action": "Modify", "Replacement": "True"}}]}, "change-set-replacement-rejected"),
        ]:
            provider.mutate = mutation
            rejects(lambda: M.control(provider, store, **{**args, "action": "execute"}), code)
        assert not any(row[1] == "execute-change-set" for row in provider.calls)
        rejects(lambda: store.read("prepare", {**request, "inputs_sha256": "b" * 64}), "reservation-reservation-mismatch")


def test_phase_engine():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    _binding, network_parameters, network_provider, _calls, _mutations, _documents = network_fixture()
    source = "a" * 40
    templates = {
        "network": M.CF.template((M.ROOT / binding["network_template"]).read_text()),
        "scope": {"Parameters": {key: {} for key in ("TickEnabled", "WorkerEnabled", "DenyDispatcherSend", "OpaqueSecret")}, "Resources": {
            "FixedTick": {"Type": "AWS::Scheduler::Schedule"}, "WorkerMapping": {"Type": "AWS::Lambda::EventSourceMapping"}, "QueueTransportPolicy": {"Type": "AWS::SQS::QueuePolicy"}}},
    }
    declared = M.CF.template((M.ROOT / binding["template"]).read_text())
    templates["scope"]["Conditions"] = {"TickActivated": declared["Conditions"]["TickActivated"]}
    templates["scope"]["Resources"]["DispatchSilenceAlarm"] = declared["Resources"]["DispatchSilenceAlarm"]
    class PhaseProvider:
        def __init__(self):
            self.stacks, self.changes, self.calls = {}, {}, []
            self.lose_prepare = self.lose_execute = False
        def __call__(self, _service, operation, **args):
            if _service != "cloudformation":
                return network_provider(_service, operation, **args)
            self.calls.append((operation, args))
            name = args["StackName"]
            name = next((key for key, value in self.stacks.items() if value["StackId"] == name), name)
            stack = self.stacks.get(name)
            if operation == "create-change-set":
                assert args["ChangeSetName"] not in self.changes
                if stack is None:
                    stack = self.stacks[name] = {"StackName": name, "StackId": "stack-id-" + name, "StackStatus": "REVIEW_IN_PROGRESS", "Parameters": [], "events": []}
                previous = M.CHANGES.parameter_values(stack["Parameters"])
                parameters = {row["ParameterKey"]: previous[row["ParameterKey"]] if row.get("UsePreviousValue") else row["ParameterValue"] for row in args["Parameters"]}
                self.changes[args["ChangeSetName"]] = {"Description": args["ClientToken"], "ChangeSetType": args["ChangeSetType"], "Status": "CREATE_COMPLETE",
                    "StackId": stack["StackId"], "ExecutionStatus": "AVAILABLE", "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in parameters.items()],
                    "template": json.loads(args["TemplateBody"])}
                if self.lose_prepare:
                    raise M.Failure("aws-command-timeout", "unknown")
                return {}
            if operation == "execute-change-set":
                change = self.changes[args["ChangeSetName"]]
                assert change["ExecutionStatus"] == "AVAILABLE"
                change["ExecutionStatus"] = "EXECUTE_COMPLETE"
                stack.update(Parameters=change["Parameters"], template=change["template"], StackStatus=change["ChangeSetType"] + "_COMPLETE")
                stack["events"].append({"EventId": str(uuid.uuid4()), "StackId": stack["StackId"], "LogicalResourceId": name,
                    "ResourceType": "AWS::CloudFormation::Stack", "PhysicalResourceId": stack["StackId"], "ClientRequestToken": args["ClientRequestToken"],
                    "ResourceStatus": stack["StackStatus"], "Timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
                if self.lose_execute:
                    raise M.Failure("aws-command-timeout", "unknown")
                return {}
            if operation == "describe-change-set":
                change = self.changes.get(args["ChangeSetName"])
                if change is None:
                    raise M.Failure("aws-resource-missing")
                allowed = set(change["template"]["Resources"]) if change["ChangeSetType"] == "CREATE" else {"QueueTransportPolicy"} if args["ChangeSetName"] in {"scheduling-fault-on", "scheduling-fault-off"} else {"FixedTick", "WorkerMapping", "DispatchSilenceAlarm"}
                return {**{key: value for key, value in change.items() if key not in {"ChangeSetType", "template"}}, "Changes": [{"ResourceChange": {"LogicalResourceId": key, "ResourceType": value["Type"],
                    "Action": "Add" if change["ChangeSetType"] == "CREATE" else "Modify", "Replacement": "False",
                    **({"Details": [{"Target": {"Attribute": "Properties", "Name": "ActionsEnabled", "RequiresRecreation": "Never"}}]} if key == "DispatchSilenceAlarm" else {})}} for key, value in change["template"]["Resources"].items() if key in allowed]}
            if operation == "describe-stacks":
                if stack is None:
                    raise M.Failure("aws-resource-missing")
                return {"Stacks": [stack]}
            if operation == "describe-stack-events":
                return {"StackEvents": stack["events"]}
            if operation == "get-template":
                return {"TemplateBody": self.changes[args["ChangeSetName"]]["template"] if "ChangeSetName" in args else stack["template"]}
            if operation == "list-stack-resources":
                return {"StackResourceSummaries": [{"LogicalResourceId": key, "ResourceType": value["Type"], "PhysicalResourceId": name + "-" + key,
                    "ResourceStatus": stack["StackStatus"]} for key, value in stack["template"]["Resources"].items()]}
            raise AssertionError(operation)
    with tempfile.TemporaryDirectory() as scratch:
        store, provider = M.Store(Path(scratch)), PhaseProvider()
        built, admitted = [], []
        def inputs(phase):
            built.append(phase)
            controls = M.CONTROL_PHASES[phase][1]
            return (templates["network"], network_parameters, source) if controls is None else (templates["scope"],
                {**dict(zip(("TickEnabled", "WorkerEnabled", "DenyDispatcherSend"), controls)), "OpaqueSecret": "****"}, source)
        def run(phase, action, builder=None):
            return M.phase_control(provider, store, binding, phase, action=action,
                build_inputs=builder or (lambda: inputs(phase)), admit=lambda intent: admitted.append(intent["phase"]),
                maintenance_selection={"qualified_path": "/controlled/core-package.json"})
        rejects(lambda: run("proof-enable", "prepare"), "phase-predecessor-required")
        rejects(lambda: run("scope-create-disabled", "execute"), "phase-intent-required")
        for phase in M.CONTROL_PHASES:
            assert run(phase, "prepare")["verdict"] == "reviewed"
            # Candidate/source evaluation is forbidden once original intent exists.
            forbidden = lambda: (_ for _ in ()).throw(AssertionError("rebuilt retained intent"))
            provider.lose_execute = phase == "fault-on"
            if provider.lose_execute:
                rejects(lambda: run(phase, "execute", forbidden), "aws-command-timeout")
            assert run(phase, "execute", forbidden)["verdict"] == "completed"
            assert run(phase, "observe", forbidden)["verdict"] == "completed"
            packet = M.capture_phase(provider, store, binding, phase)
            checked = M.validate_phase_evidence(packet, target=binding["target"], scope="shared" if phase == "network-create" else binding["scope"],
                source_revision=source, predecessor_sha256=packet["intent"]["predecessor_sha256"])
            assert checked["phase"] == phase and checked["packet_sha256"] == M.digest(packet)
            changed = copy.deepcopy(packet)
            changed["terminal"]["ClientRequestToken"] = "scheduling-" + "f" * 32
            rejects(lambda: M.validate_phase_evidence(changed, target=binding["target"], scope=packet["intent"]["scope"],
                source_revision=source, predecessor_sha256=packet["intent"]["predecessor_sha256"]), "phase-evidence-terminal-mismatch")
            provider.lose_execute = False
        # Historical packet remains usable after later phases change controls.
        original_packet = M.capture_phase(provider, store, binding, "scope-create-disabled")
        assert original_packet["intent"]["parameters"]["TickEnabled"] == "false"
        live_history = M.authenticate_phase_evidence(provider, store, binding, original_packet)
        assert live_history["current_phase"] == "accepted-enable"
        event = provider.stacks[binding["stack"]]["events"][0]
        token = event["ClientRequestToken"]
        event["ClientRequestToken"] = "foreign"
        rejects(lambda: M.authenticate_phase_evidence(provider, store, binding, original_packet), "phase-evidence-original-terminal-unconfirmed")
        event["ClientRequestToken"] = token
        assert built == list(M.CONTROL_PHASES)
        assert len([row for row in provider.calls if row[0] == "create-change-set"]) == len(M.CONTROL_PHASES)
        assert len([row for row in provider.calls if row[0] == "execute-change-set"]) == len(M.CONTROL_PHASES)
        updates = [args for operation, args in provider.calls if operation == "create-change-set" and args["ChangeSetType"] == "UPDATE"]
        assert all({"ParameterKey": "OpaqueSecret", "UsePreviousValue": True} in args["Parameters"] for args in updates)
        alarm_request = M.phase_request(M.phase_read(store, binding, "proof-enable"))
        alarm_preparation = store.read("prepare", alarm_request)
        alarm_parameters = M.phase_read(store, binding, "proof-enable")["parameters"]
        def wrong_alarm(service, operation, **arguments):
            result = provider(service, operation, **arguments)
            if operation == "describe-change-set":
                result = copy.deepcopy(result)
                for row in result["Changes"]:
                    if row["ResourceChange"]["LogicalResourceId"] == "DispatchSilenceAlarm":
                        row["ResourceChange"]["Details"][0]["Target"]["Name"] = "Threshold"
            return result
        rejects(lambda: M.review(wrong_alarm, alarm_request, alarm_preparation, templates["scope"], alarm_parameters, "UPDATE"), "phase-alarm-change-unowned")
        retained = M.phase_read(store, binding, "accepted-enable")
        request = M.phase_request(retained)
        rejects(lambda: store.path_for("prepare", {**request, "change_set": "new-label"}), "reservation-phase-name-mismatch")
        rejects(lambda: run("retry-2", "prepare"), "control-phase-invalid")
        # A later provider edit cannot inherit a completed phase's success.
        provider.stacks[binding["stack"]]["Parameters"][0]["ParameterValue"] = "foreign"
        rejects(lambda: run("accepted-enable", "observe", forbidden), "phase-parameters-mismatch")


def test_cost_reservation_boundary():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    now = datetime.now(timezone.utc)
    start, expiry = ((now + timedelta(seconds=offset)).isoformat().replace("+00:00", "Z") for offset in (-5, 3600))
    revision = "a" * 40
    definition = "arn:aws:ecs:eu-west-1:337159794548:task-definition/maintenance:7"
    projection = {"schema": "deploy/scheduling-proof-cost-envelope/v1", "region": "eu-west-1", "ceiling_usd": "10.00",
        "started_at": start, "expires_at": expiry, "costs_usd": {"endpoint": "1.000000"}, "projected_usd": "1.000000"}
    with tempfile.TemporaryDirectory() as scratch:
        store = M.Store(Path(scratch))
        scopes = {}
        for scope in ("core-server-persistence", "entity-smoke"):
            paths = {}
            for purpose in ("dispatch", "worker", "maintenance"):
                path = Path(scratch) / (scope + "-" + purpose + ".receipt.json")
                path.write_text("{}")
                paths[purpose] = str(path)
            scopes[scope] = {"selection": {}, "maintenance": {"source_revision": revision, "task_definition_arns": [definition]},
                "packages": {purpose: {"source_revision": revision} for purpose in ("dispatch", "worker")},
                "receipt_paths": {purpose: paths[purpose] for purpose in ("dispatch", "worker")},
                "receipt_files": {path: hashlib.sha256(b"{}").hexdigest() for path in paths.values()}}
        intent = {"schema": "deploy/scheduling-cost-intent/v1", "target": binding["target"], "source_revision": revision,
            "started_at": start, "expires_at": expiry, "scopes": scopes, "database": "fixture", "notification_topic_arn": "fixture",
            "image_bytes": 1024, "initial_projection": projection}
        path = M.cost_path(store, binding["target"])
        marker = b"scheduling-cost-intent/v1\n"
        with M.JOURNAL.locked(path, path.with_suffix(".lock"), marker, M.read_json) as (_, descriptor, _):
            assert M.RESERVATIONS.write_exclusive(path, intent)
            M.os.write(descriptor, marker); M.os.fsync(descriptor)
        native, calls = [], []
        request = {"task_definition": definition, "operation": "fixture"}
        def reserve():
            # The native identity is allocated while the shared budget lock is
            # held. A competing owner cannot slip another reservation between.
            try:
                with M.JOURNAL.locked(path, path.with_suffix(".lock"), marker, M.read_json):
                    raise AssertionError("competing owner obtained budget lock")
            except M.JOURNAL.JournalFailure as error:
                assert str(error) == "operation-busy"
            record = {"operation_id": "kp-" + uuid.uuid4().hex, "request": request}
            native.append({"operation_id": record["operation_id"], "task_definition_arn": definition,
                "reserved_at": None, "request_sha256": M.digest(request), "task_arn": None})
            calls.append(record)
            return record, True
        def calculate(_provider, _intent, _rows, **_kwargs):
            return projection, lambda _actual, _resources=None: projection
        source_status = [""]
        with patch.object(M.subprocess, "run", side_effect=lambda argv, **_kwargs: SimpleNamespace(stdout=source_status[0] if "status" in argv else revision)), \
                patch.object(M, "cost_native_census", side_effect=lambda _intent, _store: copy.deepcopy(native)), \
                patch.object(M, "recovery_native_census", return_value=[]), \
                patch.object(M, "cost_resource_census", return_value=[]), patch.object(M, "cost_projection", side_effect=calculate):
            record, fresh = M.reserve_cost_original(None, store, binding, request=request, reserve=reserve, task_definition_arn=definition)
            assert fresh and len(calls) == 1
            companion = M.read_json(store.root / ("cost-" + record["operation_id"] + ".admission.json"))
            assert companion["request_sha256"] == M.digest(request) and companion["cost"]["operation_id"] == record["operation_id"]
            assert companion["cost"]["reserved_usd"] == "1.000000"
            # An uncertain native reservation is not another paid submission.
            existing, new = M.reserve_cost_original(None, store, binding, request=request, reserve=lambda: (record, False), task_definition_arn=definition)
            assert existing == record and not new and len(calls) == 1
            generated = next((M.ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts").glob("administration-*.json")).relative_to(M.ROOT).as_posix()
            source_status[0] = "?? " + generated + "\0"
            existing, new = M.reserve_cost_original(None, store, binding, request=request, reserve=lambda: (record, False), task_definition_arn=definition)
            assert existing == record and not new and len(calls) == 1
            source_status[0] = " M platform/private-canary.ts\0"
            rejects(lambda: M.reserve_cost_original(None, store, binding, request=request, reserve=reserve, task_definition_arn=definition), "cost-source-uncommitted")
            assert len(calls) == 1
            source_status[0] = ""
            # Ordinary cost rejection precedes native reservation.
            expensive = {**projection, "costs_usd": {"endpoint": "11.000000"}, "projected_usd": "11.000000"}
            with patch.object(M, "cost_projection", return_value=(expensive, lambda _rows: expensive)):
                rejects(lambda: M.reserve_cost_original(None, store, binding, request=request, reserve=reserve, task_definition_arn=definition), "scheduling-runtime-proof-proof-budget-exceeded")
            assert len(calls) == 1
            # Removed native originals cannot erase their retained spend.
            with patch.object(M, "cost_native_census", return_value=[]):
                rejects(lambda: M.reserve_cost_original(None, store, binding, request=request, reserve=reserve, task_definition_arn=definition), "cost-original-companion-mismatch")
            assert len(calls) == 1
            # Failure to retain cost after native reservation means no caller
            # receives permission to submit; its original remains unresolved.
            with patch.object(M.RESERVATIONS, "write_exclusive", return_value=False):
                rejects(lambda: M.reserve_cost_original(None, store, binding, request=request, reserve=reserve, task_definition_arn=definition), "cost-admission-retention-uncertain")
            assert len(calls) == 2 and native[-1]["operation_id"] == calls[-1]["operation_id"]
            # The same mutex owns a resource reservation and its immutable
            # priced footprint; neither the native caller nor a USD flag can
            # bypass it. The resource cost arithmetic has its own owner tests.
            resources = []
            resource_request = {"database": "fixture", "snapshot": "owned-snapshot", "source_resource_id": "db-CONTROLLED"}
            def reserve_resource():
                try:
                    with M.JOURNAL.locked(path, path.with_suffix(".lock"), marker, M.read_json):
                        raise AssertionError("resource reserved outside shared budget lock")
                except M.JOURNAL.JournalFailure as error:
                    assert str(error) == "operation-busy"
                original = {"schema": "deploy/persistence-snapshot-reservation/v1", "phase": "create-recovery-point",
                    "operation_id": "kp-" + uuid.uuid4().hex, "request": resource_request,
                    "request_sha256": M.digest(resource_request), "reserved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
                resources.append({"scope": binding["scope"], "original": original})
                return original, True
            cost_owner = M.cost_owner()
            environment = {"database": {"resource_id": "db-CONTROLLED", "class": "db.t4g.micro", "allocated_gib": 20, "backup_days": 7}}
            with patch.object(M, "recovery_native_census", side_effect=lambda _intent: copy.deepcopy(resources)), \
                    patch.object(M, "cost_owner", return_value=cost_owner), patch.object(cost_owner, "cost_environment", return_value=environment):
                created, fresh = M.reserve_cost_original(None, store, binding, request=resource_request, reserve=reserve_resource,
                    recovery_phase="create-recovery-point")
                assert fresh and len(resources) == 1
                resource_companion = M.read_json(store.root / ("cost-" + created["operation_id"] + ".admission.json"))
                assert resource_companion["resource"]["operation_id"] == created["operation_id"]
                assert resource_companion["resource"]["reserved_at"] == created["reserved_at"]
                assert resource_companion["resource"]["kind"] == "snapshot" and resource_companion["resource"]["absent_at"] is None
                assert M.reserve_cost_original(None, store, binding, request=resource_request, reserve=lambda: (created, False),
                    recovery_phase="create-recovery-point") == (created, False)
                with patch.object(M, "cost_projection", return_value=(expensive, lambda *_args: expensive)):
                    rejects(lambda: M.reserve_cost_original(None, store, binding, request=resource_request, reserve=reserve_resource,
                        recovery_phase="create-recovery-point"), "scheduling-runtime-proof-proof-budget-exceeded")
                assert len(resources) == 1, "resource ceiling rejection precedes original reservation"
        with tempfile.TemporaryDirectory() as empty:
            assert M.reserve_cost_original(None, M.Store(Path(empty)), binding, request=request,
                reserve=lambda: (record, True), task_definition_arn=definition) == (record, True)
            assert M.reserve_cost_original(None, M.Store(Path(empty)), binding, request=request,
                reserve=lambda: (record, False), task_definition_arn=definition, required=False) == (record, False)


def test_task_cost_rollover_census():
    """Real native originals survive revision changes without a second authorizer."""
    base = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/"
    core = M.module("scheduling_cost_native_core_fixture", base + "core-server-persistence/run-administration/script.py")
    verifier = M.module("scheduling_cost_native_verifier_fixture", base + "core-server-persistence/verify-candidate/script.py")
    entity = M.module("scheduling_cost_native_entity_fixture", base + "entity-smoke/task-execution/implementation/task-route.py")
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    entity_binding = M.load_binding(binding["target"], "entity-smoke")
    now = datetime.now(timezone.utc)
    start, expiry = ((now + timedelta(seconds=offset)).isoformat().replace("+00:00", "Z") for offset in (-5, 3600))
    revision = "a" * 40
    prefix = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-"
    initial = {"core-server-persistence": prefix + "persistence-verifier:1", "entity-smoke": prefix + "entity-smoke-verifier:1"}
    projection = {"schema": "deploy/scheduling-proof-cost-envelope/v1", "region": "eu-west-1", "ceiling_usd": "10.00",
        "started_at": start, "expires_at": expiry, "costs_usd": {"endpoint": "1.000000"}, "projected_usd": "1.000000"}
    owner, module = M.cost_owner(), M.module
    measured = []
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        store = M.Store(root / "cost")
        store.root.mkdir()
        core.ROOT = core.MIGRATION.ROOT = root
        history = root / ".git/private-persistence-verifier/history"
        history.mkdir(parents=True)
        entity_root = root / "entity"
        native = entity.RUNNER.CONTROL.AttemptStore(entity_root / "task-attempts")
        scopes = {scope: {"selection": {"proof_label": "entity-smoke-" + "e" * 24} if scope == "entity-smoke" else {},
            "maintenance": {"source_revision": revision, "task_definition_arns": [definition]},
            "packages": {purpose: {"source_revision": revision} for purpose in ("dispatch", "worker")},
            "receipt_paths": {purpose: str(root / (scope + purpose)) for purpose in ("dispatch", "worker")},
            "receipt_files": {str(root / (scope + purpose)): hashlib.sha256(b"{}").hexdigest()
                for purpose in ("dispatch", "worker", "maintenance")}}
            for scope, definition in initial.items()}
        for selected in scopes.values():
            for path in selected["receipt_files"]: Path(path).write_text("{}")
        intent = {"schema": "deploy/scheduling-cost-intent/v1", "target": binding["target"], "source_revision": revision,
            "started_at": start, "expires_at": expiry, "scopes": scopes, "database": "fixture", "notification_topic_arn": "fixture",
            "image_bytes": 1024, "initial_projection": projection}
        intent_path = M.cost_path(store, binding["target"])
        marker = b"scheduling-cost-intent/v1\n"
        with M.JOURNAL.locked(intent_path, intent_path.with_suffix(".lock"), marker, M.read_json) as (_, descriptor, _):
            assert M.RESERVATIONS.write_exclusive(intent_path, intent)
            M.os.write(descriptor, marker); M.os.fsync(descriptor)
        def load(name, path):
            if name == "scheduling_cost_core_census": return core
            if name == "scheduling_cost_entity_census": return entity
            return module(name, path)
        def command(argv, **_options):
            return SimpleNamespace(stdout=str(root / ".git") if "--absolute-git-dir" in argv else "" if "status" in argv else revision)
        def provider(service, operation, **arguments):
            assert (service, operation) == ("ecs", "describe-task-definition")
            return {"taskDefinition": {"taskDefinitionArn": arguments["taskDefinition"], "cpu": "256", "memory": "512",
                "requiresCompatibilities": ["FARGATE"], "runtimePlatform": {"cpuArchitecture": "X86_64", "operatingSystemFamily": "LINUX"}}}
        def calculate(_provider, _intent, rows, **_options):
            def recalculate(selected, _resources=None):
                result = owner.maintenance_costs(provider,
                    reservations=[{key: row[key] for key in ("operation_id", "task_definition_arn", "reserved_at", "request_sha256")} for row in selected],
                    started_at=start, expires_at=expiry)
                measured.append(result)
                return projection
            return recalculate(rows), recalculate
        def core_request(number):
            return {"task_definition": prefix + "persistence-verifier:" + str(number), "network": "owned-private-network",
                "deadline_seconds": 120, "overrides": {"containerOverrides": [{"name": "private-persistence-verifier", "environment": [
                    {"name": "PERSISTENCE_VERIFIER_MODE", "value": "health-ready"}, {"name": "PERSISTENCE_ACCEPTANCE_RECORD_ID", "value": verifier.RECORD_ID},
                    {"name": "PERSISTENCE_ACCEPTANCE_FACT", "value": verifier.FACT}]}]}}
        def reserve_core(request):
            original = {"schema": "deploy/private-persistence-verifier-operation/v1", "mode": "health-ready", "operation_id": "kp-" + uuid.uuid4().hex,
                "predecessor": None, "request": request, "task_arn": None, "proof_receipt": None, "proof_sha256": None}
            path = history / (original["operation_id"] + ".json")
            M.JOURNAL.save(path, original)
            return verifier.load_operation(path, "health-ready"), True
        # A genuine older original on the later rollback revision is not this
        # budget's work, even when that exact revision is subsequently queried.
        unrelated, _ = reserve_core(core_request(8))
        with patch.object(M, "module", side_effect=load), patch.object(M.subprocess, "run", side_effect=command), \
                patch.object(core.MIGRATION, "proof_receipts", return_value=core.RECEIPTS), \
                patch.object(entity.C, "delivery_cache", return_value=entity_root), \
                patch.object(M, "recovery_native_census", return_value=[]), patch.object(M, "cost_resource_census", return_value=[]), \
                patch.object(M, "cost_projection", side_effect=calculate):
            assert M.cost_native_census(intent, store) == []
            admitted = []
            for number in (7, 8, 9):  # candidate, rollback, then replacement
                request = core_request(number)
                record, fresh = M.reserve_cost_original(provider, store, binding, request=request,
                    reserve=lambda: reserve_core(request), task_definition_arn=request["task_definition"], required=False)
                assert fresh
                admitted.append(record)
                assert {row["operation_id"] for row in M.cost_native_census(intent, store)} == {row["operation_id"] for row in admitted}
            assert unrelated["operation_id"] not in {row["operation_id"] for row in M.cost_native_census(intent, store)}
            # The future isolated reader uses its real native request/store,
            # not an initial revision guess or fabricated qualification.
            request = {"workload": "restore-reader", "definition": prefix + "entity-smoke-restore-reader:17",
                "image_digest": "sha256:" + "b" * 64, "source_revision": revision, "security_group": "sg-" + "c" * 17,
                "configuration_contract_sha256": "sha256:" + "4" * 64, "permission_contract_sha256": "sha256:" + "5" * 64,
                "dependency_incarnation_sha256": "sha256:" + "6" * 64, "subnets": ["subnet-" + "d" * 17],
                "environment": {"ENTITY_SMOKE_RESTORE_OPERATION": "preflight", "ENTITY_SMOKE_PROOF_LABEL": "entity-smoke-" + "e" * 24},
                "deadline_seconds": 90, "proof_label": "entity-smoke-" + "e" * 24}
            selector = entity.RUNNER.CONTROL.OPERATIONS["restore-reader"][0]
            request["environment"] = {selector: "preflight", "ENTITY_SMOKE_PROOF_LABEL": request["proof_label"]}
            assert entity.RUNNER.CONTROL.validate_request(request) == request
            record, fresh = M.reserve_cost_original(provider, store, entity_binding, request=request,
                reserve=lambda: native.reserve("restored-reader", request), task_definition_arn=request["definition"], required=False)
            assert fresh and record["reserved_at"].endswith("+00:00"), "exercise actual native timestamp, not a normalized fixture"
            assert len(M.cost_native_census(intent, store)) == 4 and measured, "post-reservation cost recalculation consumed native +00:00"
            # Native uncertainty remains included; a changed or removed native
            # original cannot erase its companion or spend after rollover.
            assert all(row["task_arn"] is None for row in M.cost_native_census(intent, store))
            companion_path = store.root / ("cost-" + record["operation_id"] + ".admission.json")
            companion = M.read_json(companion_path)
            altered = copy.deepcopy(companion); altered["task"]["task_definition_arn"] = initial["entity-smoke"]
            companion_path.write_text(json.dumps(altered))
            rejects(lambda: M.cost_native_census(intent, store), "cost-task-original-missing")
            companion_path.write_text(json.dumps(companion))
            native_path = native.path_for("restored-reader", request)
            original_bytes = native_path.read_bytes()
            native_path.unlink()
            rejects(lambda: M.cost_native_census(intent, store), "cost-task-original-missing")
            native_path.write_bytes(original_bytes)
            expensive = {**projection, "costs_usd": {"endpoint": "11.000000"}, "projected_usd": "11.000000"}
            with patch.object(M, "cost_projection", return_value=(expensive, lambda *_args: expensive)):
                rejects(lambda: M.reserve_cost_original(provider, store, binding, request=core_request(10),
                    reserve=lambda: (_ for _ in ()).throw(AssertionError("unselected revision bypassed cost")),
                    task_definition_arn=core_request(10)["task_definition"], required=False), "scheduling-runtime-proof-proof-budget-exceeded")
            rejects(lambda: M.reserve_cost_original(provider, store, entity_binding, request=request,
                reserve=lambda: (_ for _ in ()).throw(AssertionError("mismatched request reserved")),
                task_definition_arn=initial["entity-smoke"], required=False), "cost-task-request-mismatch")


def test_recovery_resource_boundary():
    scope = "core-server-persistence"
    now = datetime.now(timezone.utc)
    stamp = lambda offset: (now + timedelta(seconds=offset)).isoformat().replace("+00:00", "Z")
    request = {"database": "fixture", "snapshot": "owned-snapshot", "source_resource_id": "db-CONTROLLED"}
    original = {"schema": "deploy/persistence-snapshot-reservation/v1", "phase": "create-recovery-point",
        "operation_id": "kp-" + "1" * 32, "request": request, "request_sha256": M.digest(request), "reserved_at": stamp(-1)}
    intent = {"started_at": stamp(-5), "scopes": {scope: {"maintenance": {}}}}
    db = {"resource_id": "db-CONTROLLED", "class": "db.t4g.micro", "allocated_gib": 20, "backup_days": 7}
    descriptor = M.recovery_descriptor(None, intent, scope, original, {"database": db})
    assert descriptor["kind"] == "snapshot" and descriptor["allocated_gib"] == 20 and descriptor["backup_days"] == 0
    wrong = copy.deepcopy(original); wrong["request"]["source_resource_id"] = "db-FOREIGN"
    rejects(lambda: M.recovery_descriptor(None, intent, scope, wrong, {"database": db}), "recovery-source-incarnation-mismatch")
    with tempfile.TemporaryDirectory() as scratch:
        store = M.Store(Path(scratch))
        selected = [{"scope": scope, "original": original}]
        rejects(lambda: M.recovery_cost_rows(None, store, intent, selected), "recovery-current-original-unadmitted")
        old = copy.deepcopy(original); old["reserved_at"] = stamp(-10)
        with patch.object(M, "recovery_lookup", return_value={"Status": "available"}):
            assert M.recovery_cost_rows(None, store, intent, [{"scope": scope, "original": old}]) == [], "old protected snapshot is not adopted"
        with patch.object(M, "recovery_identity", return_value=("clone", "old-clone")), patch.object(M, "recovery_lookup", return_value={"DBInstanceStatus": "available"}):
            rejects(lambda: M.recovery_cost_rows(None, store, intent, [{"scope": scope, "original": old}]), "recovery-prior-operation-unresolved")
        companion = {"schema": "deploy/scheduling-cost-admission/v1", "intent_sha256": M.digest(intent),
            "operation_id": original["operation_id"], "request_sha256": original["request_sha256"], "cost": {}, "resource": descriptor}
        path = store.root / ("cost-" + original["operation_id"] + ".admission.json")
        assert M.RESERVATIONS.write_exclusive(path, companion)
        assert M.recovery_cost_rows(None, store, intent, selected) == [descriptor]
        with patch.object(M, "recovery_identity", return_value=("clone", "owned-clone")):
            rejects(lambda: M.recovery_cost_rows(None, store, intent, selected), "recovery-original-descriptor-mismatch")
        clone_descriptor = {**descriptor, "kind": "clone", "instance_class": "db.t4g.micro", "backup_days": 7}
        clone_companion = {**companion, "resource": clone_descriptor}
        owner = SimpleNamespace(scheduling_resource_cleanup=lambda _original: {"observed_at": stamp(0)})
        with patch.object(M, "read_json", return_value=clone_companion), patch.object(M, "recovery_identity", return_value=("clone", "owned-clone")), \
                patch.object(M, "recovery_resource_owner", return_value=owner), patch.object(M, "recovery_lookup", return_value=None):
            assert M.recovery_cost_rows(None, store, intent, selected)[0]["absent_at"] == stamp(0)
            with patch.object(M, "recovery_lookup", return_value={"DBInstanceStatus": "available"}):
                rejects(lambda: M.recovery_cost_rows(None, store, intent, selected), "recovery-cleanup-not-current")


def test_recovery_acceptance_pair():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    intent = {"source_revision": "a" * 40}
    originals, rows = [], []
    for index, scope in enumerate(("core-server-persistence", "entity-smoke")):
        for kind in ("snapshot", "clone"):
            identity = scope + "-" + kind
            original = {"operation_id": identity, "kind": kind, "request": {"identity": identity}}
            originals.append({"scope": scope, "original": original})
            rows.append({"operation_id": identity, "request_sha256": "a" * 64, "allocated_gib": 20,
                "absent_at": "2026-11-27T01:00:00Z" if kind == "clone" else None, "source_resource_id": "db-CONTROLLED"})
    with patch.object(M, "cost_intent", return_value=intent), patch.object(M, "recovery_native_census", return_value=originals), \
            patch.object(M, "recovery_cost_rows", return_value=rows), \
            patch.object(M, "recovery_identity", side_effect=lambda _scope, original: (original["kind"], original["request"]["identity"])), \
            patch.object(M, "recovery_lookup", return_value={"Status": "available", "Engine": "postgres", "AllocatedStorage": 20, "DbiResourceId": "db-CONTROLLED"}):
        result = M.recovery_acceptance_resources(None, None, binding)
        assert set(result["snapshots"]) == {"core-server-persistence", "entity-smoke"} and len(result["clones"]) == 2
        with patch.object(M, "recovery_lookup", return_value=None):
            rejects(lambda: M.recovery_acceptance_resources(None, None, binding), "recovery-retained-snapshot-mismatch")
        with patch.object(M, "recovery_cost_rows", return_value=rows[:-1]):
            rejects(lambda: M.recovery_acceptance_resources(None, None, binding), "recovery-accepted-resources-incomplete")
        changed = copy.deepcopy(rows); changed[1]["absent_at"] = None
        with patch.object(M, "recovery_cost_rows", return_value=changed):
            rejects(lambda: M.recovery_acceptance_resources(None, None, binding), "recovery-clone-cleanup-required")


def test_initial_database_join():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    intent = {"phase": "network-create", "created_at": "2026-11-27T00:00:00Z", "source_revision": "a" * 40}
    boundary = dict(intent)
    selections = {"core-server-persistence": {"qualified_path": "/data/core-package.json", "receipt_paths": {key: "/data/" + key for key in ("state", "grant", "prove")}, "image_digest": "sha256:" + "b" * 64},
        "entity-smoke": {"receipt_path": "/data/entity-package.json", "proof_label": "entity-smoke-" + "a" * 24, "image_digest": "sha256:" + "c" * 64, "expected_predecessor": None}}
    calls = []
    def owner(name, path):
        assert path.startswith("scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/")
        scope = "core-server-persistence" if path.endswith("core-server-persistence/run-administration/script.py") else "entity-smoke"
        assert path.endswith("run-administration/script.py" if scope == "core-server-persistence" else "acceptance-evaluation/implementation/acceptance-evidence.py")
        def read(*args, **kwargs):
            calls.append((scope, args, kwargs))
            assert kwargs["required_after"] == boundary["created_at"] and kwargs["source_revision"] == intent["source_revision"]
            return {"schema": "kanbien/scheduling-database-readiness/v1", "target": binding["target"], "scope": scope,
                "source_revision": kwargs["source_revision"], "image_digest": kwargs["image_digest"], "required_after": kwargs["required_after"]}
        return SimpleNamespace(scheduling_database_readiness=read, T=SimpleNamespace(Provider=lambda: "fixed-owned-provider"))
    with tempfile.TemporaryDirectory() as scratch, patch.object(M, "phase_read", side_effect=lambda _store, _binding, phase: boundary if phase == "network-create" else intent), patch.object(M, "module", side_effect=owner):
        store = M.Store(Path(scratch))
        rejects(lambda: M.initial_database_readiness(store, binding, intent, selections), "initial-database-phase-invalid")
        intent["network_before"] = {"snapshot": "original"}
        with patch.object(M, "cost_intent", return_value={"source_revision": intent["source_revision"]}), \
                patch.object(M, "initial_phase_inputs", return_value=({}, {}, intent["source_revision"])), \
                patch.object(M.ADMISSION, "network_facts", return_value={"snapshot": "original"}) as network, \
                patch.object(M, "initial_database_readiness", side_effect=AssertionError("network creation read database readiness")):
            intent.update(template={}, parameters={})
            M.admit_initial_phase(None, store, binding, intent, None)
            assert network.call_count == 1
            intent["network_before"]["snapshot"] = "changed"
            rejects(lambda: M.admit_initial_phase(None, store, binding, intent, None), "network-before-create-changed")
        assert not calls
        intent["phase"] = "scope-create-disabled"
        intent["created_at"] = "2026-11-27T00:01:00Z"
        assert set(M.initial_database_readiness(store, binding, intent, {"core-server-persistence": selections["core-server-persistence"]})) == {"core-server-persistence"}
        assert [call[0] for call in calls] == ["core-server-persistence"]
        rejects(lambda: M.initial_database_readiness(store, binding, intent, selections), "initial-database-selection-invalid")
        binding = {**binding, "scope": "entity-smoke"}
        assert set(M.initial_database_readiness(store, binding, intent, {"entity-smoke": selections["entity-smoke"]})) == {"entity-smoke"}
        assert calls[-1][1][-1] == "fixed-owned-provider"
        binding = {**binding, "scope": "core-server-persistence"}
        assert calls[-1][2]["required_after"] != intent["created_at"], "unchanged grant proof is reused from original network boundary"
        with patch.object(M, "module", side_effect=RuntimeError("private provider failure")):
            rejects(lambda: M.initial_database_readiness(store, binding, intent, {"core-server-persistence": selections["core-server-persistence"]}), "initial-database-readiness-unconfirmed")
        intent["phase"] = "proof-enable"
        rejects(lambda: M.initial_database_readiness(store, binding, intent, selections), "initial-database-phase-invalid")


def test_current_database_join():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    intent = {"phase": "fault-disable", "created_at": "2026-11-27T00:00:00Z", "source_revision": "a" * 40,
        "template": {"Resources": {"FixedTick": {"Properties": {"Target": {"Input": "owned-input"}}}}}}
    packet = {"intent": intent, "terminal": {"Timestamp": "2026-11-27T00:00:10+00:00"}}
    selection = {"qualified_path": "/data/core-package.json", "receipt_path": "/data/current-state.json", "image_digest": "sha256:" + "b" * 64}
    resources = {"WorkerMapping": {"ResourceType": "AWS::Lambda::EventSourceMapping", "PhysicalResourceId": "mapping"},
        **{purpose + "Versionabc": {"ResourceType": "AWS::Lambda::Version", "PhysicalResourceId": purpose + ":7"} for purpose in ("Dispatch", "Worker")}}
    calls = []
    enabled = False
    def provider(service, operation, **args):
        calls.append(operation)
        if service == "lambda":
            return {"UUID": "mapping", "State": "Enabled" if enabled else "Disabled", "FunctionArn": "Worker:7"}
        assert service == "scheduler" and operation == "get-schedule"
        return {"State": "DISABLED", "Target": {"Arn": "Dispatch:7", "Input": "owned-input"}}
    def reader(path, **kwargs):
        calls.append("native-reader")
        assert path == selection["receipt_path"] and kwargs["required_after"] == "2026-11-27T00:00:10Z"
        return {"schema": "kanbien/scheduling-database-observation/v1", "target": binding["target"], "scope": binding["scope"],
            "binding": {"source_revision": intent["source_revision"], "image_digest": selection["image_digest"]}, "required_after": kwargs["required_after"]}
    with tempfile.TemporaryDirectory() as scratch, patch.object(M, "phase_read", return_value=intent), \
         patch.object(M, "phase_completed", return_value={"state": {"resources": resources}}), \
         patch.object(M, "capture_phase", return_value=packet), patch.object(M, "module", return_value=SimpleNamespace(observe_scheduling_state_receipt=reader)):
        store = M.Store(Path(scratch))
        assert M.current_database_observation(provider, store, binding, intent, selection)["scope"] == binding["scope"]
        assert calls == ["get-event-source-mapping", "get-schedule", "native-reader", "get-event-source-mapping", "get-schedule"]
        # A queue-policy-only control step does not invalidate the original
        # state task: the selected disabled work boundary stays unchanged.
        intent["phase"] = "fault-on"
        with patch.object(M, "authenticate_phase_evidence", return_value={"current_phase": "fault-on"}):
            assert M.current_database_observation(provider, store, binding, intent,
                {**selection, "scheduling_control_phase": "fault-disable"})["scope"] == binding["scope"]
        intent["phase"] = "proof-disable"
        rejects(lambda: M.current_database_observation(provider, store, binding, intent,
            {**selection, "scheduling_control_phase": "fault-disable"}), "database-observation-work-boundary-crossed")
        intent["phase"] = "fault-disable"
        calls.clear()
        enabled = True
        rejects(lambda: M.current_database_observation(provider, store, binding, intent, selection), "database-observation-controls-not-disabled")
        assert "native-reader" not in calls
        intent["phase"] = "proof-enable"
        rejects(lambda: M.current_database_observation(provider, store, binding, intent, selection), "database-observation-controls-not-disabled")


def test_bounded_work_join():
    fixtures = M.module("scheduling_owned_join_fixtures", "scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/proof-test.py")
    owner = M.cost_owner()
    for scope in ("core-server-persistence", "entity-smoke"):
        binding = M.load_binding("kanbien-core-platform", scope)
        package_key = "qualified_path" if scope == "core-server-persistence" else "receipt_path"
        qualified = str(M.ROOT / ".cache" / (scope + "-qualified.json"))
        package_selection = {package_key: qualified, **({"proof_label": "synthetic-proof", "expected_predecessor": None} if scope == "entity-smoke" else {})}
        phases, _ = fixtures.release_fixture(scope, maintenance_selection=package_selection)
        intent = phases["scope-create-disabled"]["intent"]
        native_binding = {"source_revision": intent["source_revision"], "image_digest": "sha256:" + "b" * 64,
            "dependency_incarnation_sha256": owner.proof_semantics().digest({"resource_id": intent["parameters"]["DatabaseResourceId"],
                "database": intent["parameters"]["DatabaseName"], "schema": intent["template"]["Mappings"]["Scopes"][scope]["Schema"]})}
        selection = {**package_selection, "image_digest": native_binding["image_digest"]}
        if scope == "core-server-persistence": selection["receipt_path"] = "/data/current-native-state.json"
        observed, work = {"native-owner": "actual-boundary-fixture"}, {"selection": "not-an-approval"}
        calls = []
        def reduce(value, **kwargs):
            calls.append(kwargs)
            assert value is work and kwargs["database_observation"] is observed and kwargs["historical"] is False
            assert kwargs["qualified_path"] == Path(qualified).relative_to(M.ROOT).as_posix() and kwargs["context"]["native_binding"] == native_binding
            assert kwargs["context"]["required_after"] == phases["network-create"]["terminal"]["Timestamp"].replace("+00:00", "Z")
            return {"owned-count": 1}
        with tempfile.TemporaryDirectory() as scratch, patch.object(M, "cost_intent", side_effect=AssertionError("bounded work read upfront cost")), \
             patch.object(M, "maintenance_cost_binding", return_value=native_binding) as maintenance, \
             patch.object(M, "cost_owner", return_value=owner), patch.object(M, "capture_phase", return_value=phases["network-create"]), \
             patch.object(M, "authenticate_phase_evidence", return_value={}), patch.object(M, "current_database_observation", return_value=observed) as native, \
             patch.object(owner, "owned_work_selection", side_effect=reduce):
            store = M.Store(Path(scratch))
            assert M.current_owned_work(None, store, binding, intent, selection, work) == {"owned-count": 1}
            maintenance.assert_called_once_with(None, binding, package_selection)
            assert native.call_count == 1 and len(calls) == 1
            rejects(lambda: M.current_owned_work(None, store, binding, intent, {**selection, package_key: "/data/other-package"}, work), "proof-work-package-selection-mismatch")
            rejects(lambda: M.current_owned_work(None, store, binding, intent, {**selection, "image_digest": "sha256:" + "f" * 64}, work), "proof-work-package-selection-mismatch")
            assert native.call_count == 1, "mismatched caller selectors cannot reach the native owner"
            with patch.object(owner, "owned_work_selection", side_effect=owner.ProofFailure("owned-work-unexplained")):
                rejects(lambda: M.current_owned_work(None, store, binding, intent, selection, work), "scheduling-runtime-proof-owned-work-unexplained")
        for phase in ("proof-enable", "missed-tick-recovery-enable", "fault-on", "failure-recovery-enable"):
            intent = phases[phase]["intent"]
            previous = phases[M.CONTROL_PHASES[phase][0]]["intent"]
            calls = []
            with patch.object(M, "phase_read", return_value=previous), patch.object(M, "control_phase_inputs", return_value=(intent["template"], intent["parameters"], intent["source_revision"])), \
                 patch.object(M, "disabled_phase", side_effect=lambda *_args: calls.append("disabled")), \
                 patch.object(M, "network_preservation", side_effect=lambda *_args: calls.append("network")), \
                 patch.object(M, "checked_connection_pair", side_effect=lambda *_args, **kwargs: calls.append(("connection", kwargs["fresh"]))), \
                 patch.object(M, "current_owned_work", side_effect=lambda *_args: calls.append("native-owned-work")):
                M.admit_bounded_phase(None, None, binding, intent, {scope: selection}, work)
                assert calls == ["disabled", "network", ("connection", phase == "proof-enable"), "native-owned-work", "disabled"]
                calls.clear()
                rejects(lambda: M.admit_bounded_phase(None, None, binding, intent, {"passed": True}, work), "proof-database-selection-invalid")
                assert not calls
        rejects(lambda: M.admit_bounded_phase(None, None, binding, {**phases["proof-disable"]["intent"], "phase": "accepted-enable"}, {scope: selection}, work), "trusted-admission-required")
    # Both canonical readers select the fixed implementation, not an input root.
    with patch.object(M, "cost_owner", return_value=SimpleNamespace(validate_acceptance_evidence=lambda value, **kwargs: (value, kwargs))):
        assert M.validate_acceptance_evidence({"proof": "data"}, expected={"source": "bound"}, historical=True) == (
            {"proof": "data"}, {"expected": {"source": "bound"}, "historical": True})


def test_accepted_enable_join():
    fixtures = M.module("scheduling_accepted_fixture", "scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/proof-test.py")
    owner = M.cost_owner()
    scopes = ("core-server-persistence", "entity-smoke")
    fixtures_by_scope = {scope: fixtures.release_fixture(scope) for scope in scopes}
    budget = {"source_revision": "a" * 40, "database": "owned-db", "notification_topic_arn": "controlled", "scopes": {}}
    accepted, materials = {}, {}
    subscriptions = [{"protocol": "email", "subscription_sha256": "f" * 64}]
    for scope, (phases, expected) in fixtures_by_scope.items():
        budget["scopes"][scope] = {"maintenance": {"image_digest": expected["primary_image_digest"]}, "packages": expected["components"]}
        materials[scope] = {**phases, "alert": {"subscriptions": subscriptions}}
        accepted[scope] = {"reference": {"release_id": scope}, "qualification": {**expected, "profile": "scheduling-a2-v1",
            "evidence": {"observations": {"cost-and-idle": {"materials": scope,
                "phases": {phase: phase for phase in phases}, "cost": "cost", "alert": "alert"}}}},
            "recovery": {"snapshot": "owned-" + scope, "source_resource_id": "db-CONTROLLED"}}
    cost = {"intent": budget, "notification_topic_arn": "controlled",
        "recovery_resources": {"snapshots": {scope: {**value["recovery"], "allocated_gib": 20}
            for scope, value in accepted.items()}}}
    for value in materials.values(): value["cost"] = cost
    observed = []
    fake_owner = SimpleNamespace(archive_materials=lambda value: (lambda reference, _kind: materials[value][reference], set()),
        release_context=owner.release_context, authenticate_cost_evidence=lambda *_args, **kwargs: observed.append(("cost", kwargs)))
    def canonical(scope, *, reference_only=False):
        return accepted[scope]["reference"] if reference_only else accepted[scope]
    def intent_for(scope):
        previous = fixtures_by_scope[scope][0]["proof-disable"]["intent"]
        return {**previous, "phase": "accepted-enable", "parameters": {**previous["parameters"], "TickEnabled": "true", "WorkerEnabled": "true"},
            "predecessor_sha256": M.digest(previous)}
    for scope in scopes:
        binding, intent = M.load_binding("kanbien-core-platform", scope), intent_for(scope)
        peer = next(item for item in scopes if item != scope)
        peer_enabled = False
        def phase_read(_store, selected, phase):
            return intent_for(selected["scope"]) if phase == "accepted-enable" else fixtures_by_scope[selected["scope"]][0][phase]["intent"]
        def disabled(_provider, _store, selected, _phase):
            observed.append(("disabled", selected["scope"]))
            return fixtures_by_scope[selected["scope"]][0]["proof-disable"]
        with tempfile.TemporaryDirectory() as scratch, patch.object(M, "cost_owner", return_value=fake_owner), \
             patch.object(M, "cost_intent", return_value=budget), patch.object(M, "phase_read", side_effect=phase_read), \
             patch.object(M, "control_phase_inputs", return_value=(intent["template"], intent["parameters"], intent["source_revision"])), \
             patch.object(M, "canonical_scheduling_acceptance", side_effect=canonical), patch.object(M, "disabled_phase", side_effect=disabled), \
             patch.object(M, "authenticate_phase_evidence", side_effect=lambda _p, _s, selected, _packet: {"current_phase": "accepted-enable" if peer_enabled and selected["scope"] == peer else "proof-disable"}), \
             patch.object(M, "observe_current", side_effect=lambda _p, selected: observed.append(("wiring", selected["scope"]))), \
             patch.object(M, "module", return_value=SimpleNamespace(scheduling_subscriptions=lambda *_args: subscriptions)), \
             patch.object(M, "network_preservation", return_value={}), patch.object(M, "current_owned_work", return_value={}) as work:
            store = M.Store(Path(scratch))
            M.admit_accepted_phase(None, store, binding, intent, {scope: {}}, {})
            assert work.call_count == 1 and ("wiring", scope) in observed and ("wiring", peer) in observed
            path = M.phase_path(store, binding, "accepted-enable").with_suffix(".acceptance.json")
            retained = M.read_json(path)
            assert retained["request_sha256"] == M.digest(M.phase_request(intent)) and retained["references"] == {key: value["reference"] for key, value in accepted.items()}
            # A second scope may enable after the first, but only from the same
            # original canonical references and cost packet.
            M.acceptance_companion(store, M.load_binding(binding["target"], peer), intent_for(peer), retained["references"], cost, retain=True)
            peer_enabled = True
            M.admit_accepted_phase(None, store, binding, intent, {scope: {}}, {})
            for selected in scopes:
                recovery = copy.deepcopy(accepted[selected]["recovery"])
                for key, different in (("snapshot", "owned-valid-but-different-original"), ("source_resource_id", "db-DIFFERENT")):
                    accepted[selected]["recovery"][key] = different
                    work_count = work.call_count
                    rejects(lambda: M.admit_accepted_phase(None, store, binding, intent, {scope: {}}, {}), "accepted-recovery-cost-identity-mismatch")
                    assert work.call_count == work_count, "different accepted and priced originals must stop before final activation admission"
                    accepted[selected]["recovery"] = copy.deepcopy(recovery)
            original = copy.deepcopy(accepted[peer])
            for key, bad in (("profile", "http-only"), ("source_revision", "e" * 40), ("components", {}), ("primary_image_digest", "sha256:" + "e" * 64)):
                accepted[peer]["qualification"][key] = bad
                rejects(lambda: M.admit_accepted_phase(None, store, binding, intent, {scope: {}}, {}), "accepted-release-binding-mismatch")
                accepted[peer] = copy.deepcopy(original)
            accepted[peer]["reference"] = {"release_id": "new-current"}
            rejects(lambda: M.admit_accepted_phase(None, store, binding, intent, {scope: {}}, {}), "accepted-original-reference-changed")
            accepted[peer] = original
            with patch.object(fake_owner, "authenticate_cost_evidence", side_effect=M.Failure("cost-capture-stale")):
                rejects(lambda: M.admit_accepted_phase(None, store, binding, intent, {scope: {}}, {}), "cost-capture-stale")
            with patch.object(M, "canonical_scheduling_acceptance", side_effect=lambda selected, reference_only=False: {"release_id": "changed-during-check"} if reference_only else accepted[selected]):
                rejects(lambda: M.admit_accepted_phase(None, store, binding, intent, {scope: {}}, {}), "accepted-current-reference-changed")
    # Actual fixed owner selection never receives caller paths or rehearsal flags.
    reference = {"release_id": "accepted"}
    common = {"qualification_profile": "scheduling-a2-v1", "evidence_class": "live", "scheduling_qualification": {"fixed": True}}
    core_record = {**common, "provider_observation": {"database": {"snapshot": "owned-core-recovery", "source_resource_id": "db-CONTROLLED"}}}
    entity_record = {**common, "controls": {"snapshot": {"facts": {
        "snapshot_arn": "arn:aws:rds:eu-west-1:337159794548:snapshot:owned-entity-recovery", "source_resource_id": "db-CONTROLLED"}}}}
    core = SimpleNamespace(EVIDENCE_ROOT=Path("fixed-core"), succession_module=lambda: SimpleNamespace(current=lambda path: reference),
        owner=lambda: "fixed-core-owner", updates=lambda: SimpleNamespace(accepted=lambda selected, identifier: (core_record, {})))
    entity = SimpleNamespace(State=lambda: SimpleNamespace(root=Path("fixed-entity"), current=lambda **kwargs: {"reference": reference, "packet": entity_record}),
        S=SimpleNamespace(current=lambda path: reference))
    with patch.object(M, "module", side_effect=lambda _name, path: core if "core-server-persistence/collect" in path else entity):
        for scope, snapshot in zip(scopes, ("owned-core-recovery", "owned-entity-recovery")):
            assert M.canonical_scheduling_acceptance(scope) == {"reference": reference, "qualification": common["scheduling_qualification"],
                "recovery": {"snapshot": snapshot, "source_resource_id": "db-CONTROLLED"}}
            assert M.canonical_scheduling_acceptance(scope, reference_only=True) == reference
        controls = entity_record.pop("controls")
        rejects(lambda: M.canonical_scheduling_acceptance(scopes[1]), "accepted-recovery-evidence-required")
        assert M.canonical_scheduling_acceptance(scopes[1], reference_only=True) == reference
        entity_record["controls"] = controls
        core_record["evidence_class"] = "simulated"
        rejects(lambda: M.canonical_scheduling_acceptance(scopes[0]), "accepted-scheduling-profile-required")
        entity_record["qualification_profile"] = None
        rejects(lambda: M.canonical_scheduling_acceptance(scopes[1]), "accepted-scheduling-profile-required")


def test_recovery_cleanup_original():
    target, scope = "kanbien-core-platform", "core-server-persistence"
    request = {"snapshot": "owned", "database": "owned-clone"}
    original = {"schema": "deploy/persistence-restore-reservation/v1", "phase": "restore-database", "operation_id": "kp-" + "a" * 32,
        "request": request, "request_sha256": M.digest(request), "reserved_at": "2026-11-27T00:00:00Z"}
    budget = {"expires_at": "2026-11-27T00:00:01Z"}
    with tempfile.TemporaryDirectory() as scratch, patch.object(M.subprocess, "run", return_value=SimpleNamespace(stdout=scratch)), \
         patch.object(M, "cost_intent", return_value=budget), patch.object(M, "recovery_native_census", return_value=[{"scope": scope, "original": original}]):
        store = M.Store(Path(scratch) / "scheduling-control")
        companion = {"schema": "deploy/scheduling-cost-admission/v1", "intent_sha256": M.digest(budget), "operation_id": original["operation_id"],
            "request_sha256": original["request_sha256"], "cost": {"operation_id": original["operation_id"]}}
        assert M.RESERVATIONS.write_exclusive(store.root / ("cost-" + original["operation_id"] + ".admission.json"), companion)
        assert M.recovery_cleanup_admission(target=target, scope=scope, original=original) == original, "expiry cannot prevent owned cleanup"
        rejects(lambda: M.recovery_cleanup_admission(target=target, scope="entity-smoke", original=original), "recovery-cleanup-original-unconfirmed")
        changed = {**original, "request": {**request, "database": "other"}}
        rejects(lambda: M.recovery_cleanup_admission(target=target, scope=scope, original=changed), "recovery-cleanup-original-unconfirmed")
        with patch.object(M, "cost_intent", return_value={**budget, "source_revision": "new"}):
            rejects(lambda: M.recovery_cleanup_admission(target=target, scope=scope, original=original), "recovery-cleanup-budget-mismatch")


def test_capture_and_effect_routes():
    fixtures = M.module("scheduling_capture_fixtures", "scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/proof-test.py")
    actual_owner = M.cost_owner()
    for scope in ("core-server-persistence", "entity-smoke"):
        binding = M.load_binding("kanbien-core-platform", scope)
        phases, _ = fixtures.release_fixture(scope)
        phase = phases["proof-enable"]
        native_context = {"binding": binding, "native_binding": {"source_revision": "a" * 40, "image_digest": "sha256:" + "d" * 64},
            "required_after": phases["network-create"]["terminal"]["Timestamp"]}
        calls = []
        def expected(_provider, _binding, parameters, purpose):
            assert parameters == phase["intent"]["parameters"]
            return {"source_revision": "a" * 40, "function_arn": f"arn:aws:lambda:eu-west-1:337159794548:function:kc-{scope}-schedule-{purpose}:1",
                "image_uri": parameters[purpose.title() + "ImageUri"]}
        with tempfile.TemporaryDirectory() as scratch, patch.object(M, "capture_phase", return_value=phase), \
             patch.object(M, "authenticate_phase_evidence", return_value={}), patch.object(M, "owned_scope_context", return_value=(native_context, ".cache/qualified.json")), \
             patch.object(M, "preflight_expected", side_effect=expected):
            store = M.Store(Path(scratch))
            context = M.proof_capture_context(None, store, binding, "proof-enable")
            assert context["runtime"]["worker"]["purpose"] == "worker" and context["qualified_path"] == ".cache/qualified.json"
            assert context["trigger"]["function_arn"] == context["runtime"]["dispatch"]["version_arn"]
            assert context["queue_url"] == phase["readback"]["resources"]["JobQueue"]["PhysicalResourceId"]
            rejects(lambda: M.proof_capture_context(None, store, binding, "network-create"), "proof-capture-phase-invalid")
            original = {"original-native-archive": scope}
            if scope == "core-server-persistence":
                def observe(path, **kwargs):
                    calls.append((path, kwargs)); return {"packet": original}
                native_owner = SimpleNamespace(observe_scheduling_proof_receipt=observe, observe_scheduling_preparation_receipt=observe)
                selection = {"receipt_path": "/data/original-native-receipt.json"}
                budget = None
            else:
                def parse(arguments):
                    assert "--execute" not in arguments
                    calls.append(arguments); return "original-selection"
                def capture(*args, **kwargs):
                    assert args[2] == "original-selection"; return {"archive": original}
                native_owner = SimpleNamespace(SYNTHETIC_TASKS={"observe-scheduling-proof": ("scheduling-proof", "administration", ["observe-scheduling-proof"])},
                    T=SimpleNamespace(parse=parse, prepare=lambda *_: "native-context", Provider=lambda: "native-readonly"), capture_scheduling_proof=capture)
                selection = {"operation": "observe-scheduling-proof", "case": "duplicate-delivery", "snapshot": "after"}
                budget = {"scopes": {scope: {"selection": {"proof_label": "fixed-proof", "expected_predecessor": "release-" + "a" * 24}}}}
            with patch.object(M, "cost_owner", return_value=SimpleNamespace(native_owner=lambda selected: native_owner)), patch.object(M, "cost_intent", return_value=budget):
                assert M.capture_native_proof(None, store, binding, "proof-enable", selection) is original
                assert len(calls) == 1
                rejects(lambda: M.capture_native_proof(None, store, binding, "proof-enable", {**selection, "passed": True}), "proof-capture-native-selection-invalid")
            calls.clear()
            def once(_provider, guarded, selected, **kwargs):
                assert isinstance(guarded, M.CostAdmittedStore) and isinstance(guarded.original, M.ProofEffectStore)
                assert selected == binding and kwargs["native_packet"] is original
                kwargs["admit"]()
                calls.append("one-original-effect")
                return {"retained-original": True}
            with patch.object(M, "proof_capture_context", return_value=context), patch.object(M, "network_preservation", side_effect=lambda *_: calls.append("network")), \
                 patch.object(M, "checked_connection_pair", side_effect=lambda *_args, **_kwargs: calls.append("original-connections")), \
                 patch.object(M, "current_owned_work", side_effect=lambda *_: calls.append("native-owned-work")), patch.object(M, "proof_effect_once", side_effect=once):
                assert M.run_proof_effect(None, store, binding, case="duplicate", native_packet=original) == {"retained-original": True}
                assert calls == ["network", "original-connections", "one-original-effect"]
                calls.clear()
                rejects(lambda: M.run_proof_effect(None, store, binding, case="send-failure", native_packet=original), "proof-effect-owned-work-required")
                assert "one-original-effect" not in calls
                calls.clear()
                M.run_proof_effect(None, store, binding, case="send-failure", native_packet=original, database_selections={scope: {}}, work_selection={})
                assert calls == ["network", "original-connections", "native-owned-work", "one-original-effect"]
        # The public automatic capture route calls the actual read owner for
        # both the immutable dispatch window and enabled scheduler evidence.
        calls, stream = [], io.StringIO()
        def capture_window(_provider, **kwargs):
            calls.append(("window", kwargs)); return {"window": "original"}
        def capture_trigger(_provider, **kwargs):
            calls.append(("trigger", kwargs)); return {"automatic": "original"}
        owner = SimpleNamespace(ProofFailure=actual_owner.ProofFailure, capture_runtime_window=capture_window,
            validate_runtime_window=lambda packet, **kwargs: [{"dispatch": "original"}], capture_automatic_trigger=capture_trigger)
        with tempfile.TemporaryDirectory() as scratch, patch.object(M, "Provider", return_value="read-only-provider"), \
             patch.object(M.subprocess, "run", return_value=SimpleNamespace(stdout=scratch)), patch.object(M, "cost_owner", return_value=owner), \
             patch.object(M, "proof_capture_context", return_value=context), redirect_stdout(stream):
            assert M.main(["--target", binding["target"], "--scope", scope, "--operation", "capture-automatic-trigger", "--phase", "proof-enable",
                "--started-at", "2026-11-27T00:00:00Z", "--ended-at", "2026-11-27T00:01:00Z"]) == 0
        assert [row[0] for row in calls] == ["window", "trigger"] and json.loads(stream.getvalue()) == {"automatic": "original"}
        assert calls[1][1]["dispatches"] == [{"dispatch": "original"}] and calls[1][1]["expected"] == context["trigger"]
        stream, calls = io.StringIO(), []
        owner.collect_cost_evidence = lambda *_args, **kwargs: calls.append(kwargs) or {"cost": "original"}
        budget = {"scopes": {"core-server-persistence": {}, "entity-smoke": {}}, "database": "original-db", "notification_topic_arn": "original-topic"}
        with tempfile.TemporaryDirectory() as scratch, patch.object(M, "Provider", return_value="read-only-provider"), \
             patch.object(M.subprocess, "run", return_value=SimpleNamespace(stdout=scratch)), patch.object(M, "cost_owner", return_value=owner), \
             patch.object(M, "proof_capture_context", return_value=context), patch.object(M, "cost_intent", return_value=budget), \
             patch.object(M, "capture_phase", return_value={"readback": {"resources": {"SchedulingSqsEndpoint": {"PhysicalResourceId": "original-endpoint"}}}}), \
             patch.object(M, "authenticate_phase_evidence", return_value={}), redirect_stdout(stream):
            assert M.main(["--target", binding["target"], "--scope", scope, "--operation", "capture-cost",
                "--started-at", "2026-11-27T00:00:00Z", "--ended-at", "2026-11-27T00:15:00Z"]) == 0
        assert json.loads(stream.getvalue()) == {"cost": "original"} and len(calls) == 1
        assert calls[0]["database"] == "original-db" and calls[0]["endpoint_id"] == "original-endpoint"
        assert calls[0]["notification_topic_arn"] == "original-topic" and set(calls[0]["components"]) == set(budget["scopes"])


def test_release_bindings():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    template = M.CF.template((M.ROOT / binding["template"]).read_text())
    parameters = {key: "fixture" for key in template["Parameters"]}
    parameters.update(TickEnabled="false", WorkerEnabled="false")
    first = M.rendered_template(binding, "scope", parameters)
    versions = {key for key in first["Resources"] if key.startswith(("DispatchVersion", "WorkerVersion"))}
    assert len(versions) == 2 and "DispatchVersion" not in versions
    second = M.rendered_template(binding, "scope", {**parameters, "TickEnabled": "true"})
    assert first == second, "control toggles must retain immutable runtime version identity"
    changed = M.rendered_template(binding, "scope", {**parameters, "DispatchImageUri": "different-immutable-image"})
    assert not versions & set(changed["Resources"]), "new image must publish distinct versions"
    serialized = json.dumps(first)
    assert '"Ref": "DispatchVersion"' not in serialized and "${DispatchVersion." not in serialized


def test_version_transition():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    source = M.CF.template((M.ROOT / binding["template"]).read_text())
    parameters = {key: "fixture" for key in source["Parameters"]}
    prior = M.rendered_template(binding, "scope", parameters)
    desired = M.rendered_template(binding, "scope", {**parameters, "DispatchImageUri": "new-digest"})
    old = next(key for key in prior["Resources"] if key.startswith("DispatchVersion"))
    new = next(key for key in desired["Resources"] if key.startswith("DispatchVersion"))
    replacement = {"LogicalResourceId": "DispatchAsyncFailure", "ResourceType": "AWS::Lambda::EventInvokeConfig", "Action": "Modify", "Replacement": "True"}
    changes = [{"ResourceChange": replacement}, {"ResourceChange": {"LogicalResourceId": new, "Action": "Add", "ResourceType": "AWS::Lambda::Version"}},
        {"ResourceChange": {"LogicalResourceId": old, "Action": "Remove", "PolicyAction": "Retain", "ResourceType": "AWS::Lambda::Version"}}]
    request = {"stack": "sample", "change_set": "sample"}
    def provider(_service, operation, **args):
        assert operation == "get-template" and args == {"StackName": "sample", "TemplateStage": "Original"}
        return {"TemplateBody": prior}
    assert M.version_configuration_replacement(provider, request, desired, changes, replacement, "UPDATE")
    for changed, rows, entry, mode in [
        (desired, changes, replacement, "CREATE"),
        (desired, changes[:-1], replacement, "UPDATE"),
        (desired, changes, {**replacement, "LogicalResourceId": "WorkerFunction"}, "UPDATE"),
        (desired, changes, {**replacement, "Replacement": "Conditional"}, "UPDATE"),
        (prior, changes, replacement, "UPDATE"),
    ]:
        assert not M.version_configuration_replacement(provider, request, changed, rows, entry, mode)
    for key, value in [("FunctionName", {"Ref": "WorkerFunction"}), ("MaximumRetryAttempts", 2), ("DestinationConfig", {})]:
        changed = copy.deepcopy(desired)
        changed["Resources"]["DispatchAsyncFailure"]["Properties"][key] = value
        assert not M.version_configuration_replacement(provider, request, changed, changes, replacement, "UPDATE")
    changed = copy.deepcopy(desired)
    changed["Resources"]["DispatchAsyncFailure"]["UpdateReplacePolicy"] = "Delete"
    assert not M.version_configuration_replacement(provider, request, changed, changes, replacement, "UPDATE")
    def reviewed(_service, operation, **args):
        if operation == "describe-change-set":
            return {"Description": "reserved", "Status": "CREATE_COMPLETE", "ExecutionStatus": "AVAILABLE", "Parameters": [], "Changes": changes}
        return {"TemplateBody": desired if "ChangeSetName" in args else prior}
    assert M.review(reviewed, request, {"operation_id": "reserved"}, desired, {}, "UPDATE")["verdict"] == "reviewed"
    rejects(lambda: M.review(reviewed, request, {"operation_id": "foreign"}, desired, {}, "UPDATE"), "change-set-lineage-mismatch")
    rejects(lambda: M.review(reviewed, request, {"operation_id": "reserved"}, desired, {}, "DELETE"), "change-set-lineage-mismatch")


def test_qualified_source_binding():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    revision = "a" * 40
    def receipt(purpose):
        program = binding["programs"][purpose]
        return {"schema": M.CUSTODY.SCHEMA, "target": binding["target"], "environment_class": "staging", "provider_region_alias": "aws-eu-west-1",
            "candidate_id": program + "-candidate", "package_contract_id": program + "-image", "program_id": program,
            "source_revision": revision, "image_digest": "sha256:" + ("b" if purpose == "dispatch" else "c") * 64,
            "release_identity": "proof", "checked_at": "2026-11-27T05:00:00Z", "checks": {name: "passed" for name in M.CUSTODY.BASE_CHECKS | {"ecr_scan"}},
            "verdict": "qualified", "receipt_reference": "github-actions-run:1"}
    def source(argv, **_options):
        if "status" in argv:
            return SimpleNamespace(stdout="")
        if argv[-1] == "HEAD":
            return SimpleNamespace(stdout=revision)
        return SimpleNamespace(stdout=(M.ROOT / argv[-1].split(":", 1)[1]).read_bytes())
    documents, get = publication_fixture(binding, revision, receipt)
    with patch.object(M, "read_json", side_effect=receipt), patch.object(M.subprocess, "run", side_effect=source), patch.object(M.ARTIFACT, "api", side_effect=get):
        assert M.qualified_pair(binding, {purpose: purpose for purpose in ("dispatch", "worker")})["dispatch"]["source_revision"] == revision
    with patch.object(M, "read_json", side_effect=receipt), patch.object(M.subprocess, "run", return_value=SimpleNamespace(stdout="d" * 40)):
        rejects(lambda: M.qualified_pair(binding, {purpose: purpose for purpose in ("dispatch", "worker")}), "package-checkout-source-mismatch")
    def stale(argv, **options):
        return source(argv, **options) if argv[-1] == "HEAD" or "status" in argv else SimpleNamespace(stdout=b"stale-template-private-canary")
    with patch.object(M, "read_json", side_effect=receipt), patch.object(M.subprocess, "run", side_effect=stale):
        rejects(lambda: M.qualified_pair(binding, {purpose: purpose for purpose in ("dispatch", "worker")}), "package-configuration-source-changed")
    def dirty(argv, **options):
        return SimpleNamespace(stdout=" M platform/private-canary.ts\0") if "status" in argv else source(argv, **options)
    with patch.object(M, "read_json", side_effect=receipt), patch.object(M.subprocess, "run", side_effect=dirty), patch.object(M.ARTIFACT, "documents") as remote:
        rejects(lambda: M.qualified_pair(binding, {purpose: purpose for purpose in ("dispatch", "worker")}), "package-checkout-uncommitted-inputs")
        remote.assert_not_called()
    generated = next((M.ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts").glob("administration-*.json")).relative_to(M.ROOT).as_posix()
    def generated_receipt(argv, **options):
        return SimpleNamespace(stdout="?? " + generated + "\0") if "status" in argv else source(argv, **options)
    with patch.object(M, "read_json", side_effect=receipt), patch.object(M.subprocess, "run", side_effect=generated_receipt), patch.object(M.ARTIFACT, "api", side_effect=get):
        assert M.qualified_pair(binding, {purpose: purpose for purpose in ("dispatch", "worker")})["dispatch"]["source_revision"] == revision
    def malformed(argv, **options):
        return SimpleNamespace(stdout="?? private-canary-no-terminator") if "status" in argv else source(argv, **options)
    stream = io.StringIO()
    with patch.object(M, "read_json", side_effect=receipt), patch.object(M.subprocess, "run", side_effect=malformed), patch.object(M.ARTIFACT, "documents") as remote, redirect_stdout(stream):
        assert M.main(["--target", binding["target"], "--scope", binding["scope"], "--operation", "inspect-disabled",
            "--dispatch-receipt", "dispatch", "--worker-receipt", "worker"]) == 1
    assert json.loads(stream.getvalue())["code"] == "control-input-or-observation-invalid" and "private-canary" not in stream.getvalue()
    remote.assert_not_called()
    for key, bad, code in [
        ("program_id", binding["programs"]["worker"], "publication-runtime-proof-mismatch"),
        ("source_revision", "f" * 40, "publication-runtime-proof-mismatch"),
        ("cases", {}, "publication-runtime-proof-incomplete"),
        ("image_bytes", True, "publication-runtime-image-invalid"),
        ("image_id", "sha256:" + "e" * 64, "publication-qualified-image-mismatch"),
    ]:
        altered = copy.deepcopy(documents["dispatch"])
        altered["managed-runtime-qualification.json"][key] = bad
        with patch.object(M.ARTIFACT, "documents", return_value=altered):
            rejects(lambda: M.authenticated_package(binding, "dispatch", receipt("dispatch")), code)
    altered = copy.deepcopy(documents["dispatch"])
    altered["package-custody-receipt.json"]["image_digest"] = "sha256:" + "f" * 64
    with patch.object(M.ARTIFACT, "documents", return_value=altered):
        rejects(lambda: M.authenticated_package(binding, "dispatch", receipt("dispatch")), "publication-receipt-content-mismatch")
    altered = copy.deepcopy(documents["dispatch"])
    altered["qualified-image.json"]["configuration_inputs"] = []
    with patch.object(M.ARTIFACT, "documents", return_value=altered):
        rejects(lambda: M.authenticated_package(binding, "dispatch", receipt("dispatch")), "publication-configuration-mismatch")


def artifact_archive(documents):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, value in documents.items():
            archive.writestr(name, json.dumps(value))
    return output.getvalue()


def publication_fixture(binding, revision, receipt):
    repo = "gordonrose/entity-builder-harness"
    workflow = "publish-kanbien-core-platform-scheduling.yml"
    prefix = "repos/" + repo + "/actions/"
    run = {"id": 1, "run_attempt": 1, "repository": {"id": 2, "full_name": repo}, "head_repository": {"id": 2, "full_name": repo},
        "head_branch": "main", "head_sha": revision, "path": ".github/workflows/" + workflow, "event": "workflow_dispatch",
        "status": "completed", "conclusion": "success", "run_started_at": "2026-11-27T05:00:00Z", "updated_at": "2026-11-27T05:10:00Z"}
    all_documents, artifacts, archives = {}, [], {}
    for number, purpose in enumerate(("dispatch", "worker"), 3):
        program = binding["programs"][purpose]
        selected = M.PUBLICATION.binding(program)
        inputs = {path: hashlib.sha256((M.ROOT / path).read_bytes()).hexdigest() for path in
            (binding["program_contract"], binding["image_contract"], "scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification.py")}
        configurations = [{"adapter": adapter, "source": source, "selector": selector,
            "adapter_sha256": hashlib.sha256((M.ROOT / adapter).read_bytes()).hexdigest(),
            "projection_sha256": M.digest(M.CONFIGURATION.package_projection(M.ROOT / source, selector))}
            for adapter, source, selector in selected.configuration]
        runtime = {"schema": "deploy/managed-runtime-qualification/v1", "verdict": "passed", "program_id": program,
            "image_id": "sha256:" + "d" * 64, "source_revision": revision, "cases": {"invalid": M.QUALIFICATION.CASES["invalid"], "valid": M.QUALIFICATION.CASES[purpose]},
            "runtime_interface": "official-aws-lambda-client", "network": "none", "filesystem": "read-only-with-tmpfs", "user": "10001:10001", "image_bytes": 1024, "duration_seconds": 1}
        docs = {"package-custody-receipt.json": receipt(purpose), "managed-runtime-qualification.json": runtime,
            "qualified-image.json": {"schema": "deploy/local-image-qualification/v1", "image_id": runtime["image_id"], "inputs": inputs, "configuration_inputs": configurations}}
        raw = artifact_archive(docs)
        artifacts.append({"id": number, "name": program + "-package-custody-1", "size_in_bytes": len(raw), "expired": False,
            "digest": "sha256:" + hashlib.sha256(raw).hexdigest(), "created_at": "2026-11-27T05:09:00Z", "updated_at": "2026-11-27T05:09:00Z",
            "workflow_run": {"id": 1, "repository_id": 2, "head_repository_id": 2, "head_branch": "main", "head_sha": revision}})
        archives[prefix + "artifacts/" + str(number) + "/zip"] = raw
        all_documents[purpose] = docs
    replies = {prefix + "runs/1": run, prefix + "runs/1/artifacts?per_page=100": {"total_count": 2, "artifacts": artifacts}}
    def get(path):
        return archives[path] if path in archives else json.dumps(replies[path]).encode()
    get.replies, get.archives = replies, archives
    return all_documents, get


def test_publication_artifact():
    binding = M.load_binding("kanbien-core-platform", "entity-smoke")
    revision = "a" * 40
    docs, get = publication_fixture(binding, revision, lambda purpose: {"purpose": purpose})
    arguments = dict(repository="gordonrose/entity-builder-harness", workflow="publish-kanbien-core-platform-scheduling.yml",
        source_revision=revision, run_id="1", artifact_name=binding["programs"]["dispatch"] + "-package-custody-1",
        members=("package-custody-receipt.json", "qualified-image.json", "managed-runtime-qualification.json"))
    assert M.ARTIFACT.documents(**arguments, get=get) == docs["dispatch"]
    prefix = "repos/gordonrose/entity-builder-harness/actions/"
    run_key, list_key = prefix + "runs/1", prefix + "runs/1/artifacts?per_page=100"
    get.replies[run_key]["path"] += "@main"
    assert M.ARTIFACT.documents(**arguments, get=get) == docs["dispatch"]
    def rejected(mutate, expected):
        _, changed = publication_fixture(binding, revision, lambda purpose: {"purpose": purpose})
        mutate(changed)
        try:
            M.ARTIFACT.documents(**arguments, get=changed)
        except M.ARTIFACT.ArtifactFailure as failure:
            assert failure.code == expected, (failure.code, expected)
            assert "private-canary" not in str(failure)
            return
        raise AssertionError("untrusted archive accepted")
    for field, value, code in [
        ("head_branch", "topic-private-canary", "custody-publication-run-mismatch"),
        ("head_sha", "f" * 40, "custody-publication-run-mismatch"),
        ("path", ".github/workflows/untrusted.yml", "custody-publication-run-mismatch"),
        ("conclusion", "failure", "custody-publication-not-successful"),
        ("head_repository", {"id": 3, "full_name": "fork/private-canary"}, "custody-publication-repository-mismatch"),
        ("path", ".github/workflows/publish-kanbien-core-platform-scheduling.yml@topic", "custody-publication-run-mismatch"),
        ("run_attempt", None, "custody-publication-attempt-unsupported"),
        ("run_attempt", True, "custody-publication-attempt-unsupported"),
        ("run_attempt", 2, "custody-publication-attempt-unsupported"),
    ]:
        rejected(lambda changed: changed.replies[run_key].update({field: value}), code)
    for field, value, code in [
        ("expired", True, "custody-publication-artifact-unavailable"),
        ("digest", "sha256:" + "0" * 64, "custody-publication-artifact-content-mismatch"),
        ("created_at", "2026-11-26T05:09:00Z", "custody-publication-artifact-attempt-mismatch"),
        ("workflow_run", {"id": 2}, "custody-publication-artifact-lineage-mismatch"),
    ]:
        rejected(lambda changed: changed.replies[list_key]["artifacts"][0].update({field: value}), code)
    rejected(lambda changed: changed.replies[list_key].update(total_count=101), "custody-publication-artifact-list-incomplete")
    rejected(lambda changed: changed.replies[list_key]["artifacts"][1].update(name=arguments["artifact_name"]), "custody-publication-artifact-not-unique")
    def unsafe_archive(changed):
        raw = artifact_archive({"../private-canary.json": {"private": True}})
        changed.archives[prefix + "artifacts/3/zip"] = raw
        changed.replies[list_key]["artifacts"][0].update(size_in_bytes=len(raw), digest="sha256:" + hashlib.sha256(raw).hexdigest())
    rejected(unsafe_archive, "custody-publication-archive-invalid")
    def corrupt_archive(changed):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("package-custody-receipt.json", '{"secret":"private-canary"}')
            archive.writestr("qualified-image.json", '{}')
            archive.writestr("managed-runtime-qualification.json", '{}')
        raw = bytearray(output.getvalue())
        # Invalid DEFLATE block type, while the central-directory identity,
        # archive digest and declared document names are all otherwise valid.
        start = 30 + len("package-custody-receipt.json")
        raw[start] = 7
        raw = bytes(raw)
        changed.archives[prefix + "artifacts/3/zip"] = raw
        changed.replies[list_key]["artifacts"][0].update(size_in_bytes=len(raw), digest="sha256:" + hashlib.sha256(raw).hexdigest())
    rejected(corrupt_archive, "custody-publication-archive-invalid")
    # Parser recursion limits vary by Python version; inject this dependency
    # failure separately from the real malformed JSON and ZIP counterexamples.
    with patch.object(M.ARTIFACT.json, "loads", side_effect=RecursionError("private-canary")):
        try:
            M.ARTIFACT.document(b'{"fixture":true}')
        except M.ARTIFACT.ArtifactFailure as failure:
            assert str(failure) == "custody-publication-document-invalid"
        else:
            raise AssertionError("parser failure escaped safe boundary")
    try:
        M.ARTIFACT.document(b'{"private-canary":')
    except M.ARTIFACT.ArtifactFailure as failure:
        assert str(failure) == "custody-publication-document-invalid"
    else:
        raise AssertionError("malformed document accepted")
    with patch.object(M.ARTIFACT.subprocess, "run", side_effect=OSError("private-canary")):
        try:
            M.ARTIFACT.api(run_key)
        except M.ARTIFACT.ArtifactFailure as failure:
            assert str(failure) == "custody-publication-read-unavailable"
        else:
            raise AssertionError("missing read accepted")


def test_initial_inputs_without_upfront_cost():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    packages = {purpose: {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64} for purpose in ("dispatch", "worker")}
    paths = {purpose: "/controlled/" + purpose + ".json" for purpose in packages}
    with patch.object(M, "cost_intent", side_effect=AssertionError("initial creation read upfront cost")), \
            patch.object(M, "qualified_pair", return_value=packages) as qualify, \
            patch.object(M, "network_parameters", return_value={"network": "preserved"}), \
            patch.object(M, "scope_parameters", return_value={"TickEnabled": "false", "WorkerEnabled": "false"}) as scoped, \
            patch.object(M, "rendered_template", side_effect=lambda _binding, component, _parameters: {"component": component}):
        for phase in ("network-create", "scope-create-disabled"):
            template, parameters, revision = M.initial_phase_inputs(None, None, binding, phase, paths)
            assert revision == "a" * 40
            assert template["component"] == ("network" if phase == "network-create" else "scope")
        assert qualify.call_count == 2
        scoped.assert_called_once_with(None, binding, packages, False, False)
        rejects(lambda: M.initial_phase_inputs(None, None, binding, "network-create"), "package-receipts-required")
        with patch.object(M, "qualified_pair", side_effect=M.Failure("package-custody-rejected")):
            rejects(lambda: M.initial_phase_inputs(None, None, binding, "network-create", paths), "package-custody-rejected")


def test_closed_admission():
    for phase in M.CONTROL_PHASES:
        for operation in ("prepare", "execute"):
            stream = io.StringIO()
            cleanup = phase in {"missed-tick-disable", "fault-disable", "fault-off", "proof-disable"}
            with tempfile.TemporaryDirectory() as scratch, patch.object(M.subprocess, "run", return_value=SimpleNamespace(stdout=scratch)), \
                    patch.object(M, "Provider") as provider, redirect_stdout(stream):
                assert M.main(["--target", "kanbien-core-platform", "--scope", "core-server-persistence", "--operation", operation, "--phase", phase]) == 1
                if cleanup or phase == "network-create": provider.return_value.assert_not_called()
                else: provider.assert_not_called()
            expected = "phase-predecessor-required" if cleanup and operation == "prepare" else "phase-intent-required" if cleanup else "trusted-admission-required"
            if phase == "network-create":
                expected = "package-receipts-required"
            assert json.loads(stream.getvalue())["code"] == expected
    with tempfile.TemporaryDirectory() as scratch:
        provider = FakeProvider({"Resources": {"Queue": {"Type": "AWS::SQS::Queue"}}}, {})
        request = {"stack": "sample", "change_set": "scheduling-network-create", "control_phase": "network-create", "inputs_sha256": "a" * 64}
        rejects(lambda: M.control(provider, M.Store(Path(scratch)), request=request, template=provider.template,
            parameters={}, mode="CREATE", action="prepare", target="sample", admit=M.trusted_admission_required), "trusted-admission-required")
        assert not provider.calls



def test_observed_wiring():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    prefix = "arn:aws:lambda:" + binding["provider"]["region"] + ":" + binding["provider"]["account_id"] + ":function:kc-core-server-persistence-schedule-"
    values = {"DispatchVersionArn": prefix + "dispatch:2", "WorkerVersionArn": prefix + "worker:3",
              "JobQueueUrl": "queue-url", "JobQueueArn": "queue-arn", "DeadLetterQueueArn": "dead-letter-arn", "WorkerMappingId": "mapping"}
    parameters = {"Scope": binding["scope"], "DispatchImageUri": "image@sha256:" + "a" * 64, "WorkerImageUri": "image@sha256:" + "b" * 64,
                  "SourceRevision": "c" * 40, "WorkerEnabled": "false", "TickEnabled": "false"}
    calls = []
    mutation = lambda service, operation, value: value
    def provider(service, operation, **args):
        calls.append((service, operation, args))
        if operation == "describe-stacks":
            value = {"Stacks": [{"StackStatus": "CREATE_COMPLETE", "Outputs": [{"OutputKey": key, "OutputValue": item} for key, item in values.items()],
                      "Parameters": [{"ParameterKey": key, "ParameterValue": item} for key, item in parameters.items()]}]}
        elif operation == "get-function":
            purpose = "Dispatch" if args["FunctionName"] == values["DispatchVersionArn"] else "Worker"
            value = {"Configuration": {"FunctionArn": args["FunctionName"], "Version": args["FunctionName"].rsplit(":", 1)[1], "State": "Active",
                     "LastUpdateStatus": "Successful", "Timeout": 60, "MemorySize": 512, "Architectures": ["x86_64"],
                     "Environment": {"Variables": {"PLATFORM_SOURCE_COMMIT_SHA": parameters["SourceRevision"], "SCHEDULING_QUEUE_ARN": values["JobQueueArn"], "SCHEDULING_QUEUE_URL": values["JobQueueUrl"]}}},
                     "Code": {"ResolvedImageUri": parameters[purpose + "ImageUri"]},
                     "Concurrency": {"ReservedConcurrentExecutions": 1 if purpose == "Dispatch" else 2}}
        elif operation == "get-event-source-mapping":
            value = {"FunctionArn": values["WorkerVersionArn"], "EventSourceArn": values["JobQueueArn"], "State": "Disabled", "BatchSize": 1, "FunctionResponseTypes": ["ReportBatchItemFailures"]}
        elif operation == "get-schedule":
            value = {"Target": {"Arn": values["DispatchVersionArn"], "Input": M.CF.template((M.ROOT / binding["template"]).read_text())["Resources"]["FixedTick"]["Properties"]["Target"]["Input"]}, "State": "DISABLED", "ScheduleExpression": "rate(1 minute)",
                     "ScheduleExpressionTimezone": "UTC", "FlexibleTimeWindow": {"Mode": "OFF"}}
        elif operation == "get-queue-attributes":
            value = {"Attributes": {"QueueArn": values["JobQueueArn"], "VisibilityTimeout": "360",
                     "RedrivePolicy": json.dumps({"deadLetterTargetArn": values["DeadLetterQueueArn"], "maxReceiveCount": 5})}}
        elif operation == "get-function-event-invoke-config":
            value = {"MaximumRetryAttempts": 0, "MaximumEventAgeInSeconds": 60, "DestinationConfig": {"OnFailure": {"Destination": values["DeadLetterQueueArn"]}}}
        else:
            raise AssertionError(operation)
        return mutation(service, operation, value)
    assert M.observe_current(provider, binding)["verdict"] == "observed"
    assert all(operation.startswith(("get-", "describe-")) for _, operation, _ in calls)
    for selected, key, bad, code in [
        ("get-event-source-mapping", "FunctionArn", prefix + "worker:$LATEST", "worker-mapping-mismatch"),
        ("get-event-source-mapping", "EventSourceArn", "other-scope-queue", "worker-mapping-mismatch"),
        ("get-schedule", "Target", {"Arn": prefix + "dispatch:$LATEST"}, "tick-mapping-mismatch"),
        ("get-function", "Code", {"ResolvedImageUri": "different-digest"}, "function-image-mismatch"),
        ("get-function", "Concurrency", {"ReservedConcurrentExecutions": 100}, "function-concurrency-mismatch"),
        ("get-function", "Concurrency", {}, "function-concurrency-mismatch"),
        ("get-function-event-invoke-config", "MaximumRetryAttempts", 2, "dispatch-failure-route-mismatch"),
    ]:
        mutation = lambda _service, operation, value: {**value, key: bad} if operation == selected else value
        rejects(lambda: M.observe_current(provider, binding), code)


def network_fixture():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    account, region = binding["provider"]["account_id"], binding["provider"]["region"]
    role_prefix, queue_prefix = f"arn:aws:iam::{account}:role/", f"arn:aws:sqs:{region}:{account}:"
    parameters = {"VpcId": "vpc-fixture", "PrivateSubnetIds": "subnet-a,subnet-b", "LegacyWorkerSecurityGroupId": "sg-worker", "LegacyRelaySecurityGroupId": "sg-relay",
        "LegacyWorkerQueueArn": queue_prefix + "legacy-worker", "LegacyRelationalQueueArn": queue_prefix + "legacy-relational",
        "LegacyWorkerRoleArn": role_prefix + "legacy-worker", "LegacyRelayRoleArn": role_prefix + "legacy-relay",
        "LegacyRelationalWorkerRoleArn": role_prefix + "legacy-relational-worker", "LegacyRelationalRelayRoleArn": role_prefix + "legacy-relational-relay"}
    role_documents = {}
    for queue, worker, relay in (("legacy-worker", "legacy-worker", "legacy-relay"), ("legacy-relational", "legacy-relational-worker", "legacy-relational-relay")):
        role_documents[worker] = {"Statement": [{"Effect": "Allow", "Action": ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"], "Resource": queue_prefix + queue}]}
        role_documents[relay] = {"Statement": [{"Effect": "Allow", "Action": "sqs:SendMessage", "Resource": queue_prefix + queue}]}
    role_documents["http"] = {"Statement": [{"Effect": "Allow", "Action": "rds-db:connect", "Resource": "database-user"}]}
    interface = {"NetworkInterfaceId": "eni-http", "VpcId": "vpc-fixture", "SubnetId": "subnet-a", "Description": f"arn:aws:ecs:{region}:{account}:attachment/fixture",
        "Groups": [{"GroupId": "sg-http"}], "InterfaceType": "interface", "RequesterManaged": True}
    definition = {"taskDefinitionArn": "definition", "networkMode": "awsvpc", "taskRoleArn": role_prefix + "http", "containerDefinitions": [{"environment": []}]}
    calls, mutations = [], {}
    def provider(service, operation, **arguments):
        calls.append((service, operation, arguments))
        assert operation.startswith(("describe-", "get-", "list-")), "fact reader attempted mutation"
        if operation == "describe-vpc-endpoints":
            value = {"VpcEndpoints": []}
        elif operation == "describe-network-interfaces":
            value = {"NetworkInterfaces": [copy.deepcopy(interface)]}
        elif operation == "describe-route-tables":
            value = {"RouteTables": [{"RouteTableId": "route", "VpcId": "vpc-fixture", "Associations": [{"Main": True}],
                "Routes": [{"GatewayId": "local", "DestinationCidrBlock": "10.0.0.0/16", "State": "active"},
                    {"NatGatewayId": "nat-fixture", "DestinationCidrBlock": "0.0.0.0/0", "State": "active"}]}]}
        elif operation == "describe-subnets":
            value = {"Subnets": [{"SubnetId": subnet, "VpcId": "vpc-fixture", "CidrBlock": f"10.0.{index}.0/24", "AvailableIpAddressCount": 250}
                for index, subnet in enumerate(("subnet-a", "subnet-b"))]}
        elif operation == "describe-network-acls":
            value = {"NetworkAcls": [{"NetworkAclId": "acl-fixture", "VpcId": "vpc-fixture", "IsDefault": True,
                "Associations": [{"SubnetId": subnet, "NetworkAclAssociationId": "aclassoc-" + subnet} for subnet in ("subnet-a", "subnet-b")],
                "Entries": [{"RuleNumber": number, "Protocol": "-1", "RuleAction": action, "Egress": egress, "CidrBlock": "0.0.0.0/0"}
                    for egress in (False, True) for number, action in ((100, "allow"), (32767, "deny"))]}]}
        elif operation == "list-queues":
            value = {"QueueUrls": [f"https://sqs.{region}.amazonaws.com/{account}/" + name for name in ("legacy-worker", "legacy-relational")]}
        elif operation == "get-queue-url":
            value = {"QueueUrl": f"https://sqs.{region}.amazonaws.com/{account}/" + arguments["QueueName"]}
        elif operation == "get-queue-attributes":
            value = {"Attributes": {"QueueArn": queue_prefix + arguments["QueueUrl"].rsplit("/", 1)[1], "Policy": json.dumps({"Statement": []}), "VisibilityTimeout": "30"}}
        elif operation == "get-role":
            name = arguments["RoleName"]
            value = {"Role": {"Arn": role_prefix + name, "RoleName": name, "RoleId": "id-" + name}}
        elif operation == "list-role-policies":
            value = {"PolicyNames": ["access"]}
        elif operation == "get-role-policy":
            value = {"RoleName": arguments["RoleName"], "PolicyName": "access", "PolicyDocument": copy.deepcopy(role_documents[arguments["RoleName"]])}
        elif operation == "list-attached-role-policies":
            value = {"AttachedPolicies": []}
        elif operation == "list-clusters":
            value = {"clusterArns": ["cluster"]}
        elif operation == "list-tasks":
            value = {"taskArns": ["task"]}
        elif operation == "describe-tasks":
            value = {"tasks": [{"taskArn": "task", "taskDefinitionArn": "definition", "attachments": [{"details": [{"name": "networkInterfaceId", "value": "eni-http"}]}]}]}
        elif operation == "describe-task-definition":
            value = {"taskDefinition": copy.deepcopy(definition)}
        elif operation == "list-functions":
            value = {"Functions": []}
        elif operation == "describe-security-groups":
            value = {"SecurityGroups": [{"GroupId": group, "VpcId": "vpc-fixture", "IpPermissions": [], "IpPermissionsEgress": []} for group in arguments["GroupIds"]]}
        else:
            raise AssertionError(operation)
        return mutations.get(operation, lambda result, _arguments: result)(value, arguments)
    return binding, parameters, provider, calls, mutations, role_documents


def test_network_admission():
    binding, parameters, provider, calls, mutations, documents = network_fixture()
    observation = M.ADMISSION.network_facts(provider, binding, parameters)
    assert observation["verdict"] == "observed" and observation["consumer_count"] == 1
    assert observation["legacy_role_count"] == 4 and observation["legacy_queue_count"] == 2
    assert len(observation["preservation_sha256"]) == 64
    original = observation["preservation_sha256"]
    mutations["describe-security-groups"] = lambda value, _: {"SecurityGroups": [{**row, "Description": "changed"} for row in value["SecurityGroups"]]}
    assert M.ADMISSION.network_facts(provider, binding, parameters)["preservation_sha256"] != original
    mutations.clear()
    for operation, change, code in [
        ("describe-vpc-endpoints", lambda value, _: {"VpcEndpoints": [{"ServiceName": "com.amazonaws.eu-west-1.sqs"}]}, "admission-existing-queue-endpoint"),
        ("describe-network-interfaces", lambda value, _: {"NetworkInterfaces": [*value["NetworkInterfaces"], {"NetworkInterfaceId": "unknown", "VpcId": "vpc-fixture", "Description": "unknown"}]}, "admission-unmapped-compute-interface"),
        ("list-tasks", lambda value, _: {"taskArns": []}, "admission-unmapped-compute-interface"),
        ("describe-tasks", lambda value, _: {"tasks": [], "failures": [{}]}, "admission-task-observation-incomplete"),
        ("list-functions", lambda value, _: {"Functions": [{"VpcConfig": {"VpcId": "vpc-fixture"}}]}, "admission-function-consumer-unreviewed"),
        ("describe-route-tables", lambda value, _: {"RouteTables": [{"Routes": [{"TransitGatewayId": "other"}]}]}, "admission-external-network-consumer"),
        ("get-queue-attributes", lambda value, _: {"Attributes": {**value["Attributes"], "Policy": json.dumps({"Statement": [{"Condition": {"StringEquals": {"aws:SourceVpce": "other"}}}]})}}, "admission-queue-network-condition"),
        ("describe-task-definition", lambda value, _: {"taskDefinition": {**value["taskDefinition"], "containerDefinitions": [{"environment": [{"name": "AWS_ACCESS_KEY_ID", "value": "do-not-print"}]}]}}, "admission-unresolved-credentials"),
    ]:
        mutations[operation] = change
        rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), code)
        mutations.clear()
    for action, resource, code in [("sqs:*", parameters["LegacyWorkerQueueArn"], "admission-unbounded-queue-permission"),
        ("sqs:SendMessage", "*", "admission-unbounded-queue-permission"),
        ("sqs:SendMessage", parameters["LegacyWorkerQueueArn"], "admission-unknown-queue-consumer"),
        ("sts:AssumeRole", "other", "admission-indirect-identity")]:
        documents["http"] = {"Statement": [{"Effect": "Allow", "Action": action, "Resource": resource}]}
        rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), code)
    for effect in ("Allow", "Deny"):
        for key in ("aws:SourceIp", "aws:SourceVpc", "aws:SourceVpce", "aws:VpcSourceIp", "aws:VpceAccount", "aws:VpceOrgID", "aws:VpceOrgPaths"):
            documents["http"] = {"Statement": [{"Effect": effect, "Action": "sqs:SendMessage", "Resource": parameters["LegacyWorkerQueueArn"],
                "Condition": {"StringNotEqualsIfExists": {key: "network-context"}}}]}
            rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), "admission-role-network-condition")
    # A boundary does not grant access, but its network-context deny can still
    # change behavior when private DNS begins routing requests through SQS.
    binding, parameters, provider, calls, mutations, documents = network_fixture()
    boundary_arn = "arn:aws:iam::337159794548:policy/boundary"
    mutations["get-role"] = lambda value, _: {"Role": {**value["Role"], "PermissionsBoundary": {"PermissionsBoundaryType": "Policy", "PermissionsBoundaryArn": boundary_arn}}}
    def boundary_provider(service, operation, **arguments):
        if operation == "get-policy":
            return {"Policy": {"Arn": boundary_arn, "DefaultVersionId": "v1"}}
        if operation == "get-policy-version":
            return {"PolicyVersion": {"VersionId": "v1", "IsDefaultVersion": True, "Document": {"Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*", "Condition": {"IpAddress": {"aws:SourceIp": "10.0.0.0/8"}}}]}}}
        return provider(service, operation, **arguments)
    rejects(lambda: M.ADMISSION.network_facts(boundary_provider, binding, parameters), "admission-role-network-condition")
    # Current CLI reads through the actual helper, never takes a caller verdict.
    binding, parameters, provider, calls, mutations, documents = network_fixture()
    stream = io.StringIO()
    with patch.object(M, "Provider", return_value=provider), patch.object(M, "network_parameters", return_value=parameters), redirect_stdout(stream):
        assert M.main(["--target", binding["target"], "--scope", binding["scope"], "--operation", "inspect-network"]) == 0
    report = json.loads(stream.getvalue())
    assert report["code"] == "network-compatibility-observed" and "snapshot" not in report and "documents" not in stream.getvalue()
    assert all(operation.startswith(("get-", "list-", "describe-")) for _, operation, _ in calls)
    # Bounded service-specific pagination does not miss a later unknown consumer.
    count = 0
    def paginated(_service, _operation, **arguments):
        nonlocal count
        count += 1
        return {"Functions": [count], **({"NextMarker": "next"} if count == 1 else {})}
    assert M.ADMISSION.collection(paginated, "lambda", "list-functions", "Functions") == [1, 2]
    rejects(lambda: M.ADMISSION.collection(lambda *_args, **_kw: {"taskArns": [], "nextToken": "same"}, "ecs", "list-tasks", "taskArns"), "admission-pagination-invalid")


def test_network_preservation():
    binding, parameters, base, calls, mutations, documents = network_fixture()
    template = M.CF.template((M.ROOT / binding["network_template"]).read_text())
    before = M.ADMISSION.network_facts(base, binding, parameters)
    account = binding["provider"]["account_id"]
    endpoint = {"VpcEndpointId": "vpce-owned", "VpcId": parameters["VpcId"], "ServiceName": "com.amazonaws.eu-west-1.sqs",
        "VpcEndpointType": "Interface", "State": "available", "PrivateDnsEnabled": True, "SubnetIds": parameters["PrivateSubnetIds"].split(","),
        "Groups": [{"GroupId": "sg-owned"}], "NetworkInterfaceIds": ["eni-endpoint-a", "eni-endpoint-b"],
        "PolicyDocument": json.dumps(M.network_policy_value(template["Resources"]["SchedulingSqsEndpoint"]["Properties"]["PolicyDocument"],
            {**parameters, "AWS::Region": "eu-west-1", "AWS::AccountId": account, "AWS::Partition": "aws"}))}
    group = {"GroupId": "sg-owned", "VpcId": parameters["VpcId"],
        "IpPermissions": [{"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "UserIdGroupPairs": [{"GroupId": parameters[key], "UserId": account} for key in ("LegacyWorkerSecurityGroupId", "LegacyRelaySecurityGroupId")]}],
        "IpPermissionsEgress": [{"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "IpRanges": [{"CidrIp": "127.0.0.1/32"}]}]}
    with tempfile.TemporaryDirectory() as scratch:
        store = M.Store(Path(scratch) / "scheduling-control")
        intent = {"schema": "deploy/scheduling-phase-intent/v1", "target": binding["target"], "scope": "shared", "phase": "network-create",
            "stack": binding["network_stack"], "mode": "CREATE", "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "template": template, "parameters": parameters, "parameter_inputs": [], "before": None, "predecessor_sha256": None,
            "source_revision": "a" * 40, "network_before": before, "maintenance_selection": None}
        assert M.RESERVATIONS.write_exclusive(M.phase_path(store, binding, "network-create"), intent)
        request = M.phase_request(intent)
        store.reserve("prepare", request)
        executed, _fresh = store.reserve("execute", request)
        def provider(service, operation, **args):
            if service == "cloudformation":
                if operation == "describe-stacks":
                    return {"Stacks": [{"StackName": binding["network_stack"], "StackId": "stack-owned", "StackStatus": "CREATE_COMPLETE",
                        "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in parameters.items()]}]}
                if operation == "describe-stack-events":
                    return {"StackEvents": [{"PhysicalResourceId": "stack-owned", "ClientRequestToken": executed["operation_id"], "ResourceStatus": "CREATE_COMPLETE"}]}
                if operation == "get-template":
                    return {"TemplateBody": template}
                if operation == "list-stack-resources":
                    return {"StackResourceSummaries": [{"LogicalResourceId": key, "PhysicalResourceId": actual,
                        "ResourceType": template["Resources"][key]["Type"], "ResourceStatus": "CREATE_COMPLETE"}
                        for key, actual in (("SchedulingSqsEndpoint", "vpce-owned"), ("SchedulingEndpointSecurityGroup", "sg-owned"))]}
                raise AssertionError(operation)
            if operation == "describe-vpc-endpoints":
                return {"VpcEndpoints": [copy.deepcopy(endpoint)]}
            if operation == "describe-network-interfaces":
                value = base(service, operation, **args)
                value["NetworkInterfaces"].extend({"NetworkInterfaceId": item, "VpcId": parameters["VpcId"], "InterfaceType": "vpc_endpoint",
                    "SubnetId": subnet, "RequesterManaged": True, "Groups": [{"GroupId": "sg-owned"}]}
                    for item, subnet in zip(endpoint["NetworkInterfaceIds"], ("subnet-a", "subnet-b")))
                return value
            if operation == "describe-security-groups" and args["GroupIds"] == ["sg-owned"]:
                return {"SecurityGroups": [copy.deepcopy(group)]}
            return base(service, operation, **args)
        assert M.network_preservation(provider, store, binding)["preservation_sha256"] == before["preservation_sha256"]
        output = io.StringIO()
        with patch.object(M, "Provider", return_value=provider), patch.object(M.subprocess, "run", return_value=SimpleNamespace(stdout=scratch)), redirect_stdout(output):
            assert M.main(["--target", binding["target"], "--scope", binding["scope"], "--operation", "inspect-preservation"]) == 0
        assert json.loads(output.getvalue())["code"] == "network-preservation-observed" and "snapshot" not in output.getvalue()
        original_policy = endpoint["PolicyDocument"]
        endpoint["PolicyDocument"] = json.dumps({"Statement": []})
        rejects(lambda: M.network_preservation(provider, store, binding), "network-endpoint-policy-mismatch")
        endpoint["PolicyDocument"] = original_policy
        group["IpPermissions"][0]["UserIdGroupPairs"].append({"GroupId": "sg-foreign", "UserId": account})
        rejects(lambda: M.network_preservation(provider, store, binding), "network-endpoint-group-rules-mismatch")
        group["IpPermissions"][0]["UserIdGroupPairs"].pop()
        mutations["describe-security-groups"] = lambda value, _: {"SecurityGroups": [{**row, "Description": "unrelated-change"} for row in value["SecurityGroups"]]}
        rejects(lambda: M.network_preservation(provider, store, binding), "network-legacy-preservation-mismatch")
        mutations.clear()
        mutations["list-functions"] = lambda value, _: {"Functions": [{"FunctionArn": "foreign", "VpcConfig": {"VpcId": parameters["VpcId"]}}]}
        rejects(lambda: M.network_preservation(provider, store, binding), "admission-function-consumer-unreviewed")
        mutations.clear()
        # No arbitrary exemption list enters the public preservation reader.
        created = M.created_network(provider, store, binding, intent)
        assert created["functions"] == {} and created["database_ingress"] == []
        function = "arn:aws:lambda:eu-west-1:337159794548:function:owned"
        created["functions"][function] = {"role": "owned-role", "group": "sg-lambda", "subnets": ["subnet-a", "subnet-b"]}
        created["database_ingress"] = [{"target": "sg-http", "source": "sg-lambda"}]
        mutations["list-functions"] = lambda value, _: {"Functions": [{"FunctionArn": function, "Role": "owned-role",
            "VpcConfig": {"VpcId": parameters["VpcId"], "SecurityGroupIds": ["sg-lambda"], "SubnetIds": ["subnet-a", "subnet-b"]}}]}
        def database_rule(value, _args):
            for row in value["SecurityGroups"]:
                if row["GroupId"] == "sg-http":
                    row["IpPermissions"] = [{"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432,
                        "UserIdGroupPairs": [{"GroupId": "sg-lambda", "UserId": account}]}]
            return value
        mutations["describe-security-groups"] = database_rule
        assert M.ADMISSION.network_facts(provider, binding, parameters, created=created)["snapshot"] == before["snapshot"]
        def broad_rule(value, args):
            value = database_rule(value, args)
            for row in value["SecurityGroups"]:
                if row["GroupId"] == "sg-http":
                    row["IpPermissions"][0]["IpRanges"] = [{"CidrIp": "0.0.0.0/0"}]
            return value
        mutations["describe-security-groups"] = broad_rule
        assert M.ADMISSION.network_facts(provider, binding, parameters, created=created)["snapshot"] != before["snapshot"]


def test_resource_policy_and_private_paths():
    binding, parameters, provider, calls, mutations, _documents = network_fixture()
    original = M.ADMISSION.network_facts(provider, binding, parameters)
    account, region = binding["provider"]["account_id"], binding["provider"]["region"]
    http_role = f"arn:aws:iam::{account}:role/http"
    # Same-account resource grants are relevant even without an identity Allow.
    for principal in (http_role, f"arn:aws:sts::{account}:assumed-role/http/session", "id-http:session", "*", f"arn:aws:iam::{account}:root"):
        mutations["get-queue-attributes"] = lambda value, _args, principal=principal: {"Attributes": {**value["Attributes"],
            "Policy": json.dumps({"Statement": [{"Effect": "Allow", "Principal": {"AWS": principal},
                "Action": "sqs:SendMessage", "Resource": value["Attributes"]["QueueArn"]}]})}}
        rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), "admission-resource-only-queue-consumer")
    mutations.clear()
    unrelated_url = f"https://sqs.{region}.amazonaws.com/{account}/not-declared.fifo"
    mutations["list-queues"] = lambda value, _args: {"QueueUrls": [*value["QueueUrls"], unrelated_url]}
    mutations["get-queue-attributes"] = lambda value, args: {"Attributes": {**value["Attributes"],
        "Policy": json.dumps({"Statement": [{"Effect": "Allow", "Principal": {"AWS": http_role},
            "Action": "sqs:SendMessage", "Resource": value["Attributes"]["QueueArn"]}]})}} if args["QueueUrl"] == unrelated_url else value
    rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), "admission-resource-only-queue-consumer")
    mutations.pop("get-queue-attributes")
    without_grant = M.ADMISSION.network_facts(provider, binding, parameters)
    assert without_grant["consumer_count"] == 1 and len(without_grant["snapshot"]["regional_queue_policies"]) == 3
    assert without_grant["preservation_sha256"] != original["preservation_sha256"], "new unrelated queues are not silently exempt"
    mutations.clear()
    mutations["list-queues"] = lambda value, _args: {"QueueUrls": value["QueueUrls"][:1]}
    rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), "admission-queue-inventory-incomplete")
    mutations.clear()
    mutations["get-queue-attributes"] = lambda value, _args: {"Attributes": {**value["Attributes"],
        "Policy": json.dumps({"Statement": [{"Effect": "Allow", "Principal": {"AWS": parameters["LegacyRelayRoleArn"]},
            "Action": "sqs:SendMessage", "Resource": parameters["LegacyWorkerQueueArn"]}]})}}
    assert M.ADMISSION.network_facts(provider, binding, parameters)["verdict"] == "observed"
    mutations.clear()
    for egress in (False, True):
        def restricted(value, _args, egress=egress):
            value["NetworkAcls"][0]["Entries"].append({"RuleNumber": 50, "Protocol": "6", "RuleAction": "deny", "Egress": egress,
                "CidrBlock": "10.0.0.0/16", "PortRange": {"From": 443, "To": 65535}})
            return value
        mutations["describe-network-acls"] = restricted
        rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), "admission-subnet-acl-unreviewed")
    mutations.clear()
    mutations["describe-network-acls"] = lambda value, _args: {"NetworkAcls": []}
    rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), "admission-subnet-acl-incomplete")
    mutations.clear()
    def nonlocal_route(value, _args):
        value["RouteTables"][0]["Routes"].append({"DestinationCidrBlock": "10.0.1.0/24", "NatGatewayId": "nat-other", "State": "active"})
        return value
    mutations["describe-route-tables"] = nonlocal_route
    rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), "admission-private-route-unreviewed")
    mutations.clear()
    def prefix_route(value, _args):
        value["RouteTables"][0]["Routes"].append({"DestinationPrefixListId": "pl-123abc", "GatewayId": "vpce-s3", "State": "active"})
        return value
    mutations["describe-route-tables"] = prefix_route
    prefix_owner, entries, next_token = "AWS", [{"Cidr": "52.218.0.0/17"}], None
    def prefix_provider(service, operation, **arguments):
        if operation == "describe-managed-prefix-lists":
            return {"PrefixLists": [{"PrefixListId": "pl-123abc", "OwnerId": prefix_owner, "AddressFamily": "IPv4", "State": "create-complete"}]}
        if operation == "get-managed-prefix-list-entries":
            return {"Entries": entries, **({"NextToken": next_token} if next_token else {})}
        return provider(service, operation, **arguments)
    public = M.ADMISSION.network_facts(prefix_provider, binding, parameters)
    assert public["snapshot"]["route_prefix_lists"][0]["entries"] == entries
    entries = [{"Cidr": "10.0.1.0/24"}]
    rejects(lambda: M.ADMISSION.network_facts(prefix_provider, binding, parameters), "admission-private-route-unreviewed")
    entries, prefix_owner = [{"Cidr": "52.218.0.0/17"}], account
    rejects(lambda: M.ADMISSION.network_facts(prefix_provider, binding, parameters), "admission-private-prefix-unreviewed")
    prefix_owner, next_token = "AWS", "same"
    rejects(lambda: M.ADMISSION.network_facts(prefix_provider, binding, parameters), "admission-pagination-invalid")
    mutations.clear()
    def no_association(value, _args):
        value["RouteTables"][0]["Associations"] = []
        return value
    mutations["describe-route-tables"] = no_association
    rejects(lambda: M.ADMISSION.network_facts(provider, binding, parameters), "admission-subnet-route-incomplete")
    mutations.clear()
    mutations["describe-subnets"] = lambda value, _args: {"Subnets": [{**row, "AvailableIpAddressCount": 247} for row in value["Subnets"]]}
    assert M.ADMISSION.network_facts(provider, binding, parameters)["preservation_sha256"] == original["preservation_sha256"]


def test_disabled_admission():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    parameters = {"TickEnabled": "false", "WorkerEnabled": "false", "UnownedSecret": "****"}
    desired = {**parameters, "WorkerEnabled": "true"}
    assert M.CHANGES.update_parameter_inputs(parameters, M.ADMISSION.update_overrides(parameters, desired, controls_only=True)) == [
        {"ParameterKey": "TickEnabled", "UsePreviousValue": True}, {"ParameterKey": "UnownedSecret", "UsePreviousValue": True},
        {"ParameterKey": "WorkerEnabled", "ParameterValue": "true"}]
    for changed, code in [({**desired, "UnownedSecret": "replacement"}, "admission-nonowned-parameter-change"),
        ({**desired, "ExtraDefault": "value"}, "admission-parameter-set-changed"),
        ({**parameters, "TickEnabled": "true"}, "admission-worker-required-before-tick")]:
        rejects(lambda: M.ADMISSION.update_overrides(parameters, changed, controls_only=True), code)
    fault_before = {**parameters, "DenyDispatcherSend": "false"}
    fault_after = {**fault_before, "DenyDispatcherSend": "true"}
    fault_parameters = M.CHANGES.update_parameter_inputs(fault_before, M.ADMISSION.update_overrides(fault_before, fault_after, controls_only=False, fault_only=True))
    assert next(row for row in fault_parameters if row["ParameterKey"] == "DenyDispatcherSend") == {"ParameterKey": "DenyDispatcherSend", "ParameterValue": "true"}
    rejects(lambda: M.ADMISSION.update_overrides(fault_before, {**fault_after, "WorkerEnabled": "true"}, controls_only=False, fault_only=True), "admission-nonowned-parameter-change")
    rejects(lambda: M.ADMISSION.update_overrides(fault_after, {**fault_after, "WorkerEnabled": "true"}, controls_only=True), "admission-delivery-fault-not-restored")
    template = {"Parameters": {key: {} for key in parameters}, "Resources": {"Queue": {"Type": "AWS::SQS::Queue"}}}
    mutate = lambda operation, value: value
    def provider(_service, operation, **_arguments):
        if operation == "describe-stacks":
            value = {"Stacks": [{"StackName": binding["stack"], "StackId": "stack-id", "StackStatus": "CREATE_COMPLETE",
                "Parameters": [{"ParameterKey": key, "ParameterValue": item} for key, item in parameters.items()]}]}
        elif operation == "get-template":
            value = {"TemplateBody": template}
        elif operation == "list-stack-resources":
            value = {"StackResourceSummaries": [{"LogicalResourceId": "Queue", "ResourceType": "AWS::SQS::Queue", "PhysicalResourceId": "queue", "ResourceStatus": "CREATE_COMPLETE"}]}
        else:
            raise AssertionError(operation)
        return mutate(operation, value)
    def observed():
        return M.ADMISSION.disabled_facts(provider, binding, parameters, template, normalize=M.CF.template, parameter_values=M.CHANGES.parameter_values)
    assert observed()["qualification"] == "disabled-provider-state-only"
    mutate = lambda operation, value: {"StackResourceSummaries": []} if operation == "list-stack-resources" else value
    rejects(observed, "admission-resource-inventory-mismatch")
    mutate = lambda operation, value: {"TemplateBody": {"Resources": {"Foreign": {"Type": "AWS::IAM::Role"}}}} if operation == "get-template" else value
    rejects(observed, "admission-deployed-template-mismatch")


def test_preflight_custody():
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    expected = {"purpose": "worker", "function_arn": "arn:aws:lambda:eu-west-1:337159794548:function:kc-core-server-persistence-schedule-worker:7",
        "source_revision": "a" * 40, "database": {"name": "database", "schema": "platform", "username": "core_scheduling_worker"},
        "queue": {"arn": "owned-queue", "address_count": 2, "address_sha256": "b" * 64}, "image_uri": "owned-image@sha256:" + "c" * 64,
        "configuration_sha256": "d" * 64, "endpoint_id": "vpce-owned"}
    request = {"scope": binding["scope"], "slot": "disabled", "expected": expected}
    class RuntimeProvider:
        def __init__(self):
            self.binding = binding
            self.invocations = 0
            self.logs = []
            self.lose_response = False
            self.changed_body = lambda body: body
            self.stream = "2026/11/27/kc-core-server-persistence-schedule-worker[7][123456789abcdef]"
        def invoke_preflight(self, arn, operation_id):
            self.invocations += 1
            body = {"schema": "kanbien/scheduling-runtime-preflight/v1", "purpose": "worker", "source_revision": expected["source_revision"],
                "request_id": "12345678-1234-4234-9234-123456789abc", "function_arn": arn, "operation_id": operation_id,
                "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "database": expected["database"], "queue": expected["queue"]}
            body = self.changed_body(body)
            record = {"level": "info", "message": "Scheduling read-only preflight completed.", "fields": {"scheduling_preflight": body}}
            self.logs = [{"timestamp": body["checked_at"], "requestId": body["request_id"], "message": json.dumps(record)},
                {"type": "platform.report", "record": {"requestId": body["request_id"], "status": "success", "metrics": {"billedDurationMs": 321, "memorySizeMB": 512}}}]
            metadata = {"StatusCode": 200, "ExecutedVersion": "7", "LogResult": base64.b64encode("\n".join(json.dumps(row) for row in self.logs).encode()).decode()}
            if self.lose_response:
                raise M.Failure("aws-command-timeout", "unknown")
            return metadata, body
        def __call__(self, service, operation, **arguments):
            assert service == "logs"
            if operation == "filter-log-events":
                return {"events": [{"message": json.dumps(self.logs[0]), "logStreamName": self.stream}]} if self.logs else {"events": []}
            assert operation == "get-log-events"
            return {"events": [{"message": json.dumps(row)} for row in self.logs]}
    for lost in (False, True):
        with tempfile.TemporaryDirectory() as scratch:
            provider = RuntimeProvider()
            provider.lose_response = lost
            store = M.PreflightStore(Path(scratch))
            admitted = []
            if lost:
                rejects(lambda: M.preflight_once(provider, store, request, admit=lambda: admitted.append(True)), "aws-command-timeout")
                rejects(lambda: M.preflight_once(provider, store, request, admit=lambda: admitted.append(True)), "preflight-invocation-uncertain-no-replay")
                result = M.preflight_once(provider, store, request, admit=lambda: admitted.append(True), reconcile=True)
            else:
                result = M.preflight_once(provider, store, request, admit=lambda: admitted.append(True))
            assert provider.invocations == 1 and admitted == [True]
            assert result["evidence"]["billed_duration_ms"] == 321
            again = M.preflight_once(provider, store, request, admit=lambda: admitted.append(True))
            assert again["evidence"]["request_id"] == result["evidence"]["request_id"] and provider.invocations == 1
            captured = M.capture_preflight(provider, store, binding, "disabled", "worker")
            assert M.validate_preflight_evidence(captured, scope=binding["scope"], slot="disabled", expected=expected)["billed_duration_ms"] == 321
            wrong = copy.deepcopy(captured)
            wrong["evidence"]["report"]["record"]["metrics"]["billedDurationMs"] += 1
            rejects(lambda: M.validate_preflight_evidence(wrong, scope=binding["scope"], slot="disabled", expected=expected), "preflight-evidence-report-mismatch")
            provider.stream = provider.stream.replace("[7]", "[8]")
            rejects(lambda: M.capture_preflight(provider, store, binding, "disabled", "worker"), "admission-function-log-stream-mismatch")
            provider.stream = provider.stream.replace("[8]", "[7]")
            provider.logs[1]["record"]["metrics"]["billedDurationMs"] = 999
            rejects(lambda: M.preflight_once(provider, store, request, admit=lambda: None), "preflight-retained-provider-mismatch")
            rejects(lambda: M.preflight_once(provider, store, {**request, "expected": {**expected, "source_revision": "f" * 40}}, admit=lambda: None), "preflight-reservation-reservation-mismatch")
    for change, code in [
        (lambda body: {**body, "queue": {**body["queue"], "address_sha256": "f" * 64}}, "admission-preflight-endpoint-mismatch"),
        (lambda body: {**body, "operation_id": str(uuid.uuid4())}, "admission-preflight-identity-mismatch"),
        (lambda body: {**body, "source_revision": "e" * 40}, "admission-preflight-identity-mismatch"),
        (lambda body: {**body, "checked_at": "2020-01-01T00:00:00Z"}, "admission-preflight-interval-invalid"),
    ]:
        with tempfile.TemporaryDirectory() as scratch:
            provider = RuntimeProvider(); provider.changed_body = change
            store = M.PreflightStore(Path(scratch))
            rejects(lambda: M.preflight_once(provider, store, request, admit=lambda: None), code)
            assert provider.invocations == 1 and not store.result_path(request).exists()
            rejects(lambda: M.preflight_once(provider, store, request, admit=lambda: None), "preflight-invocation-uncertain-no-replay")
    with tempfile.TemporaryDirectory() as scratch:
        provider = RuntimeProvider(); store = M.PreflightStore(Path(scratch))
        rejects(lambda: M.preflight_once(provider, store, request, admit=M.trusted_admission_required), "trusted-admission-required")
        assert provider.invocations == 0 and not store.path_for("invoke", request).exists()
        rejects(lambda: M.preflight_once(provider, store, {**request, "slot": "retry-2"}, admit=lambda: None), "preflight-request-invalid")
        rejects(lambda: M.preflight_once(provider, store, {**request, "slot": "bounded-proof"}, admit=lambda: None), "preflight-predecessor-required")
        assert provider.invocations == 0
        provider.lose_response = True
        rejects(lambda: M.preflight_once(provider, store, request, admit=lambda: None), "aws-command-timeout")
        provider.logs = []
        rejects(lambda: M.preflight_once(provider, store, {**request, "slot": "bounded-proof"}, admit=lambda: None), "preflight-original-result-unresolved")
        assert provider.invocations == 1
    # A final freshness observation does not force an unused intermediate slot.
    with tempfile.TemporaryDirectory() as scratch:
        provider = RuntimeProvider(); store = M.PreflightStore(Path(scratch))
        M.preflight_once(provider, store, request, admit=lambda: None)
        M.preflight_once(provider, store, {**request, "slot": "acceptance"}, admit=lambda: None)
        assert provider.invocations == 2
        assert not store.path_for("invoke", {**request, "slot": "bounded-proof"}).exists()
    # But an actually reserved intermediate attempt cannot be skipped merely
    # because the caller chooses the later slot.
    with tempfile.TemporaryDirectory() as scratch:
        provider = RuntimeProvider(); store = M.PreflightStore(Path(scratch))
        M.preflight_once(provider, store, request, admit=lambda: None)
        store.reserve("invoke", {**request, "slot": "bounded-proof"})
        rejects(lambda: M.preflight_once(provider, store, {**request, "slot": "acceptance"}, admit=lambda: None))
        assert provider.invocations == 1 and not store.path_for("invoke", {**request, "slot": "acceptance"}).exists()
    # Historical reconciliation proves the original bounded interval; it does
    # not become admission for a later effect after the 15-minute freshness cap.
    with tempfile.TemporaryDirectory() as scratch:
        provider = RuntimeProvider(); store = M.PreflightStore(Path(scratch))
        result = M.preflight_once(provider, store, request, admit=lambda: None)
        original = result["evidence"]["response"]
        later = M.ADMISSION.utc(original["checked_at"]) + timedelta(minutes=16)
        assert M.ADMISSION.preflight_body(original, expected, result["reservation"], now=later, fresh=False) == original
        rejects(lambda: M.ADMISSION.preflight_body(original, expected, result["reservation"], now=later), "admission-preflight-stale")
        invalid = {**original, "checked_at": (M.ADMISSION.utc(original["checked_at"]) + timedelta(minutes=3)).isoformat().replace("+00:00", "Z")}
        rejects(lambda: M.ADMISSION.preflight_body(invalid, expected, result["reservation"], fresh=False), "admission-preflight-interval-invalid")
    with tempfile.TemporaryDirectory() as scratch:
        provider = RuntimeProvider(); store = M.PreflightStore(Path(scratch) / "scheduling-control")
        M.preflight_once(provider, store, request, admit=lambda: None)
        output = io.StringIO()
        with patch.object(M, "Provider", return_value=provider), patch.object(M.subprocess, "run", return_value=SimpleNamespace(stdout=scratch)), redirect_stdout(output):
            assert M.main(["--target", binding["target"], "--scope", binding["scope"], "--operation", "reconcile-preflight",
                "--preflight-slot", "disabled", "--purpose", "worker"]) == 0
        assert provider.invocations == 1 and json.loads(output.getvalue())["qualification"] == "historical-runtime-connection-only"
    # Actual transport is still one AWS CLI call, closed event and sync context;
    # the fixture supplies only the transport boundary, not an admission verdict.
    provider = M.Provider(binding)
    calls = []
    def cli(argv, **options):
        calls.append((argv, options))
        assert options["environment"]["AWS_MAX_ATTEMPTS"] == "1"
        if argv[1:3] == ["sts", "get-caller-identity"]:
            return {"Account": binding["provider"]["account_id"]}
        assert argv[1:3] == ["lambda", "invoke"]
        assert argv[argv.index("--payload") + 1] == '{"kind":"scheduling-preflight/v1"}'
        context = json.loads(base64.b64decode(argv[argv.index("--client-context") + 1]))
        assert set(context) == {"custom"} and set(context["custom"]) == {"scheduling_preflight_operation_id"}
        Path(argv[argv.index("--payload") + 2]).write_text('{"fixture":true}')
        return {"StatusCode": 200, "ExecutedVersion": "7"}
    with patch.object(M.RESPONSE, "inventory_covered", return_value=True), patch.object(M.CLI, "invoke_json", side_effect=cli):
        metadata, body = provider.invoke_preflight(expected["function_arn"], str(uuid.uuid4()))
    assert body == {"fixture": True} and metadata["ExecutedVersion"] == "7" and len(calls) == 2


def test_proof_effect_custody():
    # Reuse the existing typed phase/snapshot fixture, not another proof format.
    fixtures = M.module("scheduling_effect_fixtures", "scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/proof-test.py")
    owner = M.cost_owner()
    for scope in ("core-server-persistence", "entity-smoke"):
        binding = M.load_binding("kanbien-core-platform", scope)
        for case, phase, purpose in (("duplicate", "proof-enable", "worker"), ("send-failure", "fault-on", "dispatch")):
            phases, _ = fixtures.release_fixture(scope)
            packet = phases[phase]
            queue = f"https://sqs.eu-west-1.amazonaws.com/{binding['provider']['account_id']}/{binding['target']}-{scope}-scheduling"
            packet["readback"]["resources"]["JobQueue"]["PhysicalResourceId"] = queue
            packet["intent"]["before"]["state"]["resources"]["JobQueue"]["PhysicalResourceId"] = queue
            phase_request = M.phase_request(packet["intent"])
            for key in ("preparation", "execution"):
                packet[key]["request"] = phase_request
                packet[key]["request_sha256"] = M.digest(phase_request)
            fixture = fixtures.delivery_fixture(scope)
            snapshot = fixture["after" if case == "duplicate" else "before"]
            stamp = datetime.now(timezone.utc)
            when = lambda seconds: (stamp + timedelta(seconds=seconds)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            snapshot["observed_at"] = when(0)
            snapshot["schedule"]["due_at"] = when(-3)
            if scope == "entity-smoke": snapshot["selection"]["due_at"] = when(-3)
            if case == "duplicate":
                snapshot["outbox"].update(created_at=when(-3), published_at=when(-1))
                snapshot["processing"]["completion"]["completed_at"] = when(-2)
                snapshot["delivery_message"]["enqueuedAt"] = when(0)
            native = {"controlled_original": "observation"}
            seed = {"controlled_original": "seed"} if scope == "core-server-persistence" else None
            native_result = {"operation": "observe-scheduling-proof", "case": "minute-delivery" if case == "duplicate" else "failure-recovery",
                "result": {"scheduling_observation": snapshot}}
            seed_result = {"operation": "seed-scheduling-proof", "result": {"scheduling_seed": {
                "schedule_id": snapshot["schedule"]["id"], "due_at": snapshot["schedule"]["due_at"]}}, "task": {"stopped_at": when(-5)}}
            def native_reader(value, **_arguments):
                assert value in (native, seed)
                return native_result if value == native else seed_result
            runtime = {"purpose": purpose, "source_revision": packet["intent"]["source_revision"],
                "version_arn": next(row["PhysicalResourceId"] for key, row in packet["readback"]["resources"].items() if key.startswith(purpose.title() + "Version")),
                "image_uri": packet["intent"]["parameters"][purpose.title() + "ImageUri"], "log_group": f"/aws/lambda/{binding['target']}/{scope}/scheduling"}
            expected = {"runtime": runtime, "queue_url": queue, "queue_arn": f"arn:aws:sqs:eu-west-1:{binding['provider']['account_id']}:{binding['target']}-{scope}-scheduling",
                "native_binding": {"source_revision": runtime["source_revision"], "image_digest": "sha256:" + "d" * 64,
                    "dependency_incarnation_sha256": owner.proof_semantics().digest({"resource_id": "db-CONTROLLED", "database": "kanbienpersistence", "schema": "platform" if scope == "core-server-persistence" else "entity_smoke"})},
                "required_after": phases["network-create"]["terminal"]["Timestamp"]}
            class EffectProvider:
                def __init__(self, lost): self.lost, self.sends, self.invocations, self.logs = lost, 0, 0, []
                def invoke_failure_proof(self, arn, operation_id):
                    self.invocations += 1
                    marker = {"schema": "kanbien/scheduling-proof-invocation/v1", "operation_id": operation_id,
                        "source_revision": runtime["source_revision"], "request_id": str(uuid.uuid4()), "function_arn": arn,
                        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
                    self.logs = [{"level": "info", "message": "Scheduling proof invocation.", "fields": {"scheduling_invocation": marker}},
                        {"type": "platform.start", "record": {"requestId": marker["request_id"], "version": "1"}},
                        {"type": "platform.report", "record": {"requestId": marker["request_id"], "status": "error", "metrics": {"billedDurationMs": 321, "memorySizeMB": 512}}}]
                    if self.lost: raise M.Failure("aws-command-timeout", "unknown")
                    return {"StatusCode": 200, "ExecutedVersion": "1", "FunctionError": "Unhandled"}, {"private": "must-not-retain"}
                def __call__(self, service, operation, **arguments):
                    if (service, operation) == ("sqs", "send-message"):
                        self.sends += 1
                        assert arguments == {"QueueUrl": queue, "MessageBody": json.dumps(snapshot["delivery_message"], separators=(",", ":"), ensure_ascii=False)}
                        if self.lost: raise M.Failure("aws-command-timeout", "unknown")
                        return {"MessageId": str(uuid.uuid4()), "MD5OfMessageBody": hashlib.md5(arguments["MessageBody"].encode(), usedforsecurity=False).hexdigest()}
                    assert service == "logs"
                    stream = f"2026/11/27/kc-{scope}-schedule-dispatch[1][controlled-environment]"
                    if operation == "filter-log-events": return {"events": [{"message": json.dumps(self.logs[0]), "logStreamName": stream}]} if self.logs else {"events": []}
                    assert operation == "get-log-events"
                    return {"events": [{"message": json.dumps(row)} for row in self.logs]}
            with patch.object(owner, "native_packet", side_effect=native_reader), patch.object(M, "cost_owner", return_value=owner), \
                 patch.object(M, "reobserve_proof_inputs", return_value=({"current_phase": phase, "phase": phase}, snapshot)), patch.object(M, "disabled_phase"):
                arguments = {"phase_packet": packet, "native_packet": native, "expected": expected, "seed_packet": seed}
                request = M.proof_effect_request(binding=binding, **arguments)
                rejects(lambda: M.proof_effect_request(binding=binding, **{**arguments, "expected": {**expected, "queue_url": queue + "-foreign"}}), "proof-effect-queue-mismatch")
                if scope == "entity-smoke" and case == "duplicate":
                    native_result["case"] = "duplicate-delivery"
                    rejects(lambda: M.proof_effect_request(binding=binding, **arguments), "proof-effect-native-case-mismatch")
                    native_result["case"] = "minute-delivery"
                for lost in (False, True):
                    with tempfile.TemporaryDirectory() as scratch:
                        provider, store, admissions = EffectProvider(lost), M.ProofEffectStore(Path(scratch)), []
                        def run(reconcile=False, admit=None):
                            return M.proof_effect_once(provider, store, binding, **arguments, qualified_path="owned-receipt",
                                admit=admit or (lambda: admissions.append(True)), reconcile=reconcile)
                        rejects(lambda: run(admit=M.trusted_admission_required), "trusted-admission-required")
                        assert provider.sends == provider.invocations == 0 and store.read("submit", request) is None
                        if lost:
                            rejects(run, "aws-command-timeout")
                            rejects(run, "proof-effect-submission-uncertain-no-replay")
                            result = run(True)
                        else: result = run()
                        checked = M.validate_proof_effect(result, binding=binding, **arguments)
                        assert checked["acknowledgement"] == ("unknown" if lost else "retained")
                        assert checked["request_sha256"] == M.digest(request)
                        assert admissions == [True] and provider.sends + provider.invocations == 1
                        assert "must-not-retain" not in json.dumps(result)
                        assert run() == result and provider.sends + provider.invocations == 1
                        tampered = copy.deepcopy(result); tampered["reservation"]["request"]["message"] = '{"foreign":true}'
                        rejects(lambda: M.validate_proof_effect(tampered, binding=binding, **arguments), "proof-effect-reservation-reservation-mismatch")
                        if case == "send-failure":
                            assert checked["request_id"] and checked["invoked_at"]
                            provider.logs[-1]["record"]["status"] = "success"
                            rejects(run, "proof-invocation-failure-unconfirmed")


def test_expired_cleanup_reservation():
    fixtures = M.module("scheduling_cleanup_fixtures", "scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/proof-test.py")
    binding = M.load_binding("kanbien-core-platform", "core-server-persistence")
    phases, _ = fixtures.release_fixture()
    expired = {"source_revision": "a" * 40, "expires_at": "2020-01-01T00:00:00Z"}
    for phase in ("missed-tick-disable", "fault-disable", "fault-off", "proof-disable"):
        with tempfile.TemporaryDirectory() as scratch:
            store = M.Store(Path(scratch))
            path = M.cost_path(store, binding["target"])
            marker = b"scheduling-cost-intent/v1\n"
            with M.JOURNAL.locked(path, path.with_suffix(".lock"), marker, M.read_json) as (_, descriptor, _):
                assert M.RESERVATIONS.write_exclusive(path, expired)
                M.os.write(descriptor, marker); M.os.fsync(descriptor)
            intent = phases[phase]["intent"]
            previous = phases[M.CONTROL_PHASES[phase][0]]["intent"]
            selected = {phase: intent, previous["phase"]: previous}
            with patch.object(M, "cost_intent", return_value=expired), patch.object(M, "phase_read", side_effect=lambda _s, _b, name: selected.get(name)):
                request = M.phase_request(intent)
                guarded = M.CostAdmittedStore(store, None, binding)
                original, fresh = guarded.reserve("prepare", request)
                assert fresh and guarded.reserve("prepare", request) == (original, False)
                assert M.read_json(path) == expired, "shutdown must not reset the budget"
                with patch.object(M, "cost_intent", return_value=None):
                    assert M.cleanup_control_shape(store, binding, intent) is None
                    stopped, fresh = guarded.reserve("execute", request)
                    assert fresh and guarded.reserve("execute", request) == (stopped, False)
                invalid = copy.deepcopy(intent)
                invalid["parameters"]["WorkerEnabled"] = "true"
                rejects(lambda: M.cleanup_control_shape(store, binding, invalid), "cleanup-control-intent-invalid")
                invalid = copy.deepcopy(intent)
                invalid["parameters"]["WorkerImageUri"] += "-changed"
                rejects(lambda: M.cleanup_control_shape(store, binding, invalid), "admission-nonowned-parameter-change")
                rejects(lambda: M.reserve_cleanup_control(None, store, binding, "prepare", {**request, "control_phase": "proof-enable"}), "cleanup-control-unowned")


def main():
    scheduling, network = check_templates()
    for source, path, bad, kind in [
        (scheduling, ["Resources", "WorkerMapping", "Properties", "FunctionName"], {"Ref": "WorkerFunction"}, "scheduling"),
        (scheduling, ["Parameters", "WorkerEnabled", "Default"], "true", "scheduling"),
        (network, ["Resources", "SchedulingSqsEndpoint", "Properties", "PolicyDocument", "Statement"], [], "network"),
        (network, ["Resources", "SchedulingEndpointSecurityGroup", "Properties", "SecurityGroupIngress"], [], "network"),
    ]:
        changed = copy.deepcopy(source)
        target = changed
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = bad
        rejects(lambda: check_templates(**{kind: changed}))
    test_release_bindings()
    test_version_transition()
    test_qualified_source_binding()
    test_publication_artifact()
    test_reservations()
    test_phase_engine()
    test_cost_reservation_boundary()
    test_task_cost_rollover_census()
    test_recovery_resource_boundary()
    test_recovery_acceptance_pair()
    test_initial_database_join()
    test_current_database_join()
    test_bounded_work_join()
    test_accepted_enable_join()
    test_recovery_cleanup_original()
    test_capture_and_effect_routes()
    test_observed_wiring()
    test_initial_inputs_without_upfront_cost()
    test_closed_admission()
    test_network_admission()
    test_network_preservation()
    test_resource_policy_and_private_paths()
    test_disabled_admission()
    test_preflight_custody()
    test_proof_effect_custody()
    test_expired_cleanup_reservation()
    print("scheduling control: template, immutable release, fail-closed activation and retained submission counterexamples passed")


if __name__ == "__main__":
    main()
