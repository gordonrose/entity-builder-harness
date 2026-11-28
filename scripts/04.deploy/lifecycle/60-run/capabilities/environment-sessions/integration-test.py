#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.environment-session-controller
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise controller ordering, interrupted cleanup and retained completion through actual session owners and isolated providers.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.command.environment-sessions
#     path: scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/script.py
from copy import deepcopy
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).resolve().parent
CONTROLLER = load("tested_session_controller", HERE / "script.py")
ASSEMBLY = load("tested_session_assembly", HERE / "aws.py")


class ControlledAssembly:
    """Immediate synthetic operations expose ordering independently of AWS timing."""
    def __init__(self):
        self.plan = {"stack_order": ("network", "workload"),
            "stack_templates": (("network", "network.yml"), ("workload", "workload.yml")),
            "stack_names": (("network", "network"), ("workload", "workload")),
            "activation_templates": (("workload.yml", "{}"),),
            "task_selections": (("workload", {"kind": "ordered-commands/v1", "steps": (
                {"id": "migrate", "phase": "before-activation"}, {"id": "verify", "phase": "after-activation"})}),)}
        self.document = {"state": "open", "operations": {}, "operation_outcomes": {}, "incarnations": {}}
        self.records = SimpleNamespace(observe_existing=lambda: {"document": deepcopy(self.document)})
        self.operations = self
        self.events, self.phases, self.saved = [], {}, None
        self.active, self.pending = False, None
        self.task_status, self.quiescence, self.cleanup_status = "succeeded", "ready", "completed"

    def initialize(self):
        return deepcopy(self.document)

    def functional_result(self):
        return deepcopy(self.saved)

    def retain_functional(self, result):
        assert self.saved is None or self.saved == result
        self.saved = deepcopy(result)
        self.events.append(("retain", result["status"]))

    def retain_cleanup(self, result):
        self.events.append(("cleanup-report", result["status"]))

    def handoff_cleanup(self):
        return None

    def prepare_stack(self, stack):
        return {"status": "ready"}

    def reconcile_operation(self, *, kind, stack, phase):
        return {"status": self.phases.get((kind, stack, phase), "unreserved")}

    def prepare(self, kind, *, stack, template_reference):
        assert template_reference == dict(self.plan["stack_templates"])[stack]
        self.events.append(("prepare", kind, stack))
        self.document["operations"][kind + ":" + stack + ":prepare"] = {}
        self.phases[kind, stack, "prepare"] = "pending" if self.pending == (kind, stack) else "ready"

    def execute(self, kind, *, stack, template_reference):
        assert self.phases[kind, stack, "prepare"] == "ready"
        self.events.append(("execute", kind, stack))
        self.phases[kind, stack, "execute"] = "succeeded"
        self.document["operations"][kind + ":" + stack + ":execute"] = {}
        if kind == "creation":
            self.document["incarnations"][stack] = "owned-" + stack
        elif kind == "activation":
            self.active = True
        elif kind == "prepare-discard":
            self.active = False

    def run_task(self, component, row):
        self.events.append(("task", row["id"]))
        return {"status": self.task_status}

    def seal(self):
        self.document["state"] = "sealed"
        self.events.append(("seal",))

    def reconcile_tasks(self):
        return {"status": self.quiescence}

    def reconcile_stops(self):
        return [{"stack": stack, "status": ("stop-required" if stack == "workload" and self.active else "stopped")
                 if stack in self.document["incarnations"] else "not-started"} for stack in reversed(self.plan["stack_order"])]

    def retain_physical_observation(self, *, stack, stack_id):
        assert stack_id == "owned-" + stack

    def delete(self, *, stack, stack_id):
        assert not self.active and self.document["state"] == "sealed"
        self.events.append(("delete", stack))
        self.phases["delete", stack, "delete"] = "succeeded"

    def complete_cleanup(self):
        assert [event[1] for event in self.events if event[0] == "delete"] == ["workload", "network"]
        return {"status": self.cleanup_status}

    def failure_code(self, failure):
        return "environment-session-controller-operation-failed"


class ControllerTests(unittest.TestCase):
    def test_foreground_seals_and_hands_off_without_using_cleanup_permissions(self):
        fixture = ControlledAssembly()
        def handoff():
            self.assertEqual(fixture.document["state"], "sealed")
            self.assertEqual(fixture.saved, {"status": "succeeded"})
            return {"status": "pending", "reason": "cleanup-worker-running"}
        fixture.handoff_cleanup = handoff
        result = CONTROLLER.Controller(fixture).advance()
        self.assertEqual(result["cleanup"]["status"], "pending")
        self.assertFalse(any(event[0] == "delete" or event[:2] == ("prepare", "prepare-discard") for event in fixture.events))

    def test_complete_order_retains_verdict_before_reverse_cleanup(self):
        fixture = ControlledAssembly()
        result = CONTROLLER.Controller(fixture).advance()
        self.assertEqual(result, {"functional": {"status": "succeeded"}, "cleanup": {"status": "completed"}})
        events = fixture.events
        self.assertLess(events.index(("execute", "creation", "network")), events.index(("execute", "creation", "workload")))
        self.assertLess(events.index(("task", "migrate")), events.index(("execute", "activation", "workload")))
        self.assertLess(events.index(("execute", "activation", "workload")), events.index(("task", "verify")))
        self.assertLess(events.index(("retain", "succeeded")), events.index(("delete", "workload")))
        self.assertEqual([event[1] for event in events if event[0] == "delete"], ["workload", "network"])

    def test_pending_preparation_does_not_seal_or_consume_execution_on_resume(self):
        fixture = ControlledAssembly()
        fixture.pending = ("creation", "network")
        controller = CONTROLLER.Controller(fixture)
        for _ in range(2):
            result = controller.advance()
            self.assertEqual(result, {"functional": {"status": "pending"}, "cleanup": {"status": "not-started"}})
            self.assertEqual(fixture.document["state"], "open")
        self.assertEqual(fixture.events, [("prepare", "creation", "network")])

    def test_failed_test_still_cleans_up_without_activation(self):
        fixture = ControlledAssembly()
        fixture.task_status = "failed"
        result = CONTROLLER.Controller(fixture).advance()
        self.assertEqual(result["functional"], {"status": "failed", "reason": "functionality-failed"})
        self.assertEqual(result["cleanup"], {"status": "completed"})
        self.assertFalse(any(event[:2] == ("execute", "activation") for event in fixture.events))

    def test_pending_discard_prevents_every_deletion(self):
        fixture = ControlledAssembly()
        fixture.pending = ("prepare-discard", "workload")
        result = CONTROLLER.Controller(fixture).advance()
        self.assertEqual(result["cleanup"]["status"], "pending")
        self.assertFalse(any(event[0] == "delete" for event in fixture.events))

    def test_unknown_tasks_or_resources_cannot_become_cleanup_success(self):
        for field in ("quiescence", "cleanup_status"):
            with self.subTest(field=field):
                fixture = ControlledAssembly()
                setattr(fixture, field, "unknown")
                result = CONTROLLER.Controller(fixture).advance()
                self.assertEqual(result["cleanup"]["status"], "unknown")
                if field == "quiescence":
                    self.assertFalse(any(event[0] == "delete" for event in fixture.events))

    def test_required_task_cannot_be_silently_skipped(self):
        fixture = ControlledAssembly()
        fixture.task_status = "skipped"
        result = CONTROLLER.Controller(fixture).advance()
        self.assertEqual(result["functional"]["reason"], "environment-session-controller-required-task-skipped")
        self.assertEqual(result["cleanup"]["status"], "completed")


class CommandTests(unittest.TestCase):
    def test_run_success_and_failure_keep_their_original_exit_verdict(self):
        with tempfile.TemporaryDirectory(prefix="session-command-") as directory:
            path = Path(directory) / "input.json"
            path.write_text('{}')
            for status, expected in (("succeeded", 0), ("failed", 1)):
                fixture = ControlledAssembly()
                fixture.task_status = status
                output = io.StringIO()
                with patch.object(CONTROLLER, "command_assembly", return_value=fixture), contextlib.redirect_stdout(output):
                    self.assertEqual(CONTROLLER.main(["run", "--input", str(path), "--max-seconds", "1"]), expected)
                self.assertEqual(json.loads(output.getvalue())["functional"]["status"], status)

    def test_run_time_budget_closes_creation_and_requests_cleanup(self):
        fixture = ControlledAssembly()
        fixture.pending = ("creation", "network")
        fixture.handoff_cleanup = lambda: {"status": "pending", "reason": "cleanup-worker-running"}
        with tempfile.TemporaryDirectory(prefix="session-command-") as directory:
            path = Path(directory) / "input.json"
            path.write_text('{}')
            output = io.StringIO()
            with patch.object(CONTROLLER, "command_assembly", return_value=fixture), patch.object(CONTROLLER.time, "monotonic", side_effect=[0, 2]), contextlib.redirect_stdout(output):
                self.assertEqual(CONTROLLER.main(["run", "--input", str(path), "--max-seconds", "1"]), 2)
        report = json.loads(output.getvalue())
        self.assertEqual(fixture.document["state"], "sealed")
        self.assertEqual(report["functional"], {"status": "interrupted"})
        self.assertEqual(report["cleanup"]["status"], "pending")
        self.assertEqual([row for row in fixture.events if row[0] == "prepare"], [("prepare", "creation", "network")])

    def test_cleanup_command_uses_cleanup_only_and_emits_terminal_result(self):
        fixture = ControlledAssembly()
        fixture.document["operations"] = {"creation:" + name + ":prepare": {} for name in fixture.plan["stack_order"]}
        fixture.document["incarnations"] = {name: "owned-" + name for name in fixture.plan["stack_order"]}
        with tempfile.TemporaryDirectory(prefix="session-command-") as directory:
            path = Path(directory) / "input.json"
            path.write_text('{"input":"sentinel"}')
            output = io.StringIO()
            with patch.object(CONTROLLER, "command_assembly", return_value=fixture) as factory, contextlib.redirect_stdout(output):
                self.assertEqual(CONTROLLER.main(["cleanup", "--input", str(path), "--max-seconds", "1"]), 0)
            factory.assert_called_once_with({"input": "sentinel"}, "cleanup")
        report = json.loads(output.getvalue())
        self.assertEqual(report["cleanup"]["status"], "completed")
        self.assertEqual(report["functional"], {"status": "interrupted"})
        self.assertFalse(any(event[0] in ("prepare", "execute", "task") for event in fixture.events))

    def test_bad_input_and_construction_errors_never_leak_raw_values(self):
        with tempfile.TemporaryDirectory(prefix="session-command-") as directory:
            path = Path(directory) / "input.json"
            for raw in ('{"secret":"private-canary","secret":2}', '{"value":NaN}', 'not-json'):
                path.write_text(raw)
                output = io.StringIO()
                with patch.object(CONTROLLER, "command_assembly", side_effect=AssertionError("must not construct")), contextlib.redirect_stdout(output):
                    self.assertEqual(CONTROLLER.main(["cleanup", "--input", str(path)]), 1)
                self.assertEqual(json.loads(output.getvalue())["reason"], "environment-session-command-input-invalid")
                self.assertNotIn("private-canary", output.getvalue())
            path.write_text('{}')
            output = io.StringIO()
            with patch.object(CONTROLLER, "command_assembly", side_effect=RuntimeError("private-canary")), contextlib.redirect_stdout(output):
                self.assertEqual(CONTROLLER.main(["cleanup", "--input", str(path)]), 1)
            self.assertEqual(json.loads(output.getvalue())["reason"], "environment-session-construction-unconfirmed")
            self.assertNotIn("private-canary", output.getvalue())

    def test_factory_rejects_untyped_inputs_before_loading_any_native_owner(self):
        with patch.object(ASSEMBLY, "module", side_effect=AssertionError("must not load")):
            for document in ({}, {"authority_ok": True}, []):
                with self.assertRaises(ASSEMBLY.TaskAssemblyFailure):
                    ASSEMBLY.existing_assembly(root=HERE.parents[5], document=document, environment={})


class CleanupObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner = load("cleanup_observation_owner", HERE.parents[5] / "scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py")

    def test_only_original_ecs_resources_can_complete_as_inactive(self):
        records = self.owner.RECORDS.SessionRecords.__new__(self.owner.RECORDS.SessionRecords)
        records._binding = {"target": "fixture"}
        index = {"Task": "AWS::ECS::TaskDefinition"}
        document = {"state": "sealed", "functional_result": {"status": "interrupted"},
            "base": {"source_plan_sha256": "a" * 64, "cleanup_shapes": {"owned": {"resource_count": 1,
                "resources_sha256": self.owner._digest(index)}}},
            "operations": {"creation:owned:prepare": {}}, "operation_outcomes": {"delete:owned:delete": {"status": "DELETE_COMPLETE"}}}
        resource = {"logical_id": "Task", "resource_type": "AWS::ECS::TaskDefinition", "status": "inactive"}
        evidence = {"schema": "deploy/environment-session-cleanup/v1", "binding": records.binding,
            "source_plan_sha256": "a" * 64, "stacks": {"owned": {"status": "removed", "resources": [resource]}}}
        self.assertIsInstance(records._cleanup_evidence(document, evidence), bytes)
        for field, wrong in (("resource_type", "AWS::RDS::DBInstance"), ("logical_id", "Foreign"), ("status", "present")):
            previous = resource[field]
            resource[field] = wrong
            with self.assertRaises(self.owner.RECORDS.SessionRecordFailure): records._cleanup_evidence(document, evidence)
            resource[field] = previous
        resource["artifacts"] = [{"kind": "backup", "status": "inactive"}]
        with self.assertRaises(self.owner.RECORDS.SessionRecordFailure): records._cleanup_evidence(document, evidence)

    def test_native_cross_region_reads_count_lineage_and_never_enable_regional_writes(self):
        native = self.owner.SESSION_CLI
        provider = native.SessionProvider(profile=None, region="eu-west-1", environment={})
        operations = self.owner.SessionOperations.__new__(self.owner.SessionOperations)
        operations.records = SimpleNamespace(region="eu-west-1", account="337159794548")
        operations._provider = provider
        lineage = self.owner._digest("db-ORIGINAL")
        present, malformed = False, False
        calls = []
        def invoke(arguments, **options):
            service, operation = arguments[1:3]
            region = arguments[arguments.index("--region") + 1]
            parameters = json.loads(Path(arguments[arguments.index("--cli-input-json") + 1].removeprefix("file://")).read_text())
            calls.append((service, operation, region))
            if service == "ec2":
                self.assertEqual(parameters, {"AllRegions": False})
                return {"Regions": [{"RegionName": name, "OptInStatus": "opt-in-not-required"} for name in ("eu-west-1", "us-east-1")]}
            self.assertEqual(service, "rds")
            if operation == "describe-db-instance-automated-backups": return {"DBInstanceAutomatedBackups": []}
            rows = [{"DBSnapshotArn": "arn:aws:rds:us-east-1:337159794548:snapshot:copy", "DbiResourceId": "db-ORIGINAL"}] if present and region == "us-east-1" and parameters["SnapshotType"] == "manual" else []
            return {"DBSnapshots": rows, **({"NextToken": "unread"} if malformed else {})}
        with patch.object(native.CLI, "invoke_json", side_effect=invoke):
            self.assertEqual(operations._database_artifacts(lineage)[-1], {"kind": "cross-region-backups", "status": "absent", "count": 0, "regions": 1})
            present = True
            self.assertEqual(operations._database_artifacts(lineage)[-1]["status"], "present")
            before = len(calls)
            with self.assertRaises(native.SessionProviderFailure): provider.observe_region("us-east-1", "cloudformation", "delete-stack")
            self.assertEqual(len(calls), before)
            malformed = True
            with self.assertRaises(native.SessionProviderFailure): operations._database_artifacts(lineage)



class StartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = load("tested_session_setup", HERE / "setup.py")

    def fixture(self, *, lose_create=False, publication=False):
        helper = self.setup
        selected = helper.PublicationStartup if publication else helper.Startup
        startup = selected.__new__(selected)
        startup.root = HERE.parents[5]
        startup.environment = {}
        startup.configuration = {"account": "337159794548", "region": "eu-west-1", "profile": "kanbien-dev"}
        startup.binding = {"expires_at": 7200}
        startup.operator = "arn:aws:iam::337159794548:user/test-setup"
        startup.clock = lambda: 1000
        startup.realization = helper.module("fixture_setup_evidence",
            startup.root / "scripts/04.deploy/operational-realization-gate/evidence.py")
        startup.realization_contract = helper.OWNER.CF.template((startup.root /
            "infra/04.deploy/03.product/image/environment-session-controller/setup-realization-contract.v2.yml").read_text())
        startup.source_files = (HERE / "setup.py", Path(startup.realization.__file__))
        startup.source_artifact = startup._source_artifact()
        startup.custody = {"receipt": {"verdict": "qualified", "checks": {"local_image_smoke": "passed"}}}
        base = "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/"
        startup.control = {"records_stack": "kanbien-environment-session-records",
            "records_template": base + "environment-session-records.yml",
            "stack": "s-" + "a" * 19 + "-session-control", "template": base + "environment-sessions.yml"}
        if publication:
            startup.control = {"stack": "kanbien-environment-session-controller-publication",
                "template": base + "environment-session-controller-publication.yml"}
            startup.control.update(records_stack=startup.control["stack"], records_template=startup.control["template"])
            startup.source_qualification, startup.custody = startup.source_artifact, None
        directory = tempfile.TemporaryDirectory(prefix="session-startup-test-")
        self.addCleanup(directory.cleanup)
        startup.store = helper.SetupStore(Path(directory.name))
        source = helper.OWNER.CF.template((startup.root / startup.control["records_template"]).read_text())
        state = {"phase": "absent", "sends": [], "token": None}
        arn = "arn:aws:cloudformation:eu-west-1:337159794548:stack/" + startup.control["records_stack"] + "/original"
        values = ({"ExistingGitHubOidcProviderArn": "arn:aws:iam::337159794548:oidc-provider/token.actions.githubusercontent.com"}
            if publication else {"SetupOperatorArn": startup.operator})
        rows = [{"ParameterKey": key, "ParameterValue": value} for key, value in values.items()]
        def provider(service, operation, **arguments):
            if (service, operation) == ("sts", "get-caller-identity"):
                return {"Account": "337159794548", "Arn": startup.operator, "UserId": "operator"}
            if (service, operation) == ("iam", "simulate-principal-policy"):
                return {"EvaluationResults": [{"EvalActionName": action,
                    "EvalResourceName": arn, "EvalDecision": "allowed", "MissingContextValues": []}
                    for action in arguments["ActionNames"]]}
            self.assertEqual(service, "cloudformation")
            if operation == "validate-template":
                return {"Parameters": deepcopy(rows), "Capabilities": ["CAPABILITY_NAMED_IAM"] if publication else []}
            if operation == "describe-stacks":
                if state["phase"] == "absent":
                    raise helper.OWNER.SESSION_CLI.SessionProviderFailure("aws-resource-missing")
                return {"Stacks": [{"StackName": startup.control["records_stack"], "StackId": arn,
                    "StackStatus": "CREATE_COMPLETE" if state["phase"] == "complete" else "REVIEW_IN_PROGRESS",
                    "Parameters": rows}]}
            if operation == "describe-change-set":
                return {"Status": "CREATE_COMPLETE", "ChangeSetName": startup.control["records_stack"] + "-create",
                    "ExecutionStatus": "AVAILABLE", "StackName": startup.control["records_stack"], "StackId": arn,
                    "Description": state["prepare_token"], "Parameters": rows, "Capabilities": ["CAPABILITY_NAMED_IAM"],
                    "Changes": [{"Type": "Resource", "ResourceChange": {"Action": "Add",
                        "LogicalResourceId": key, "ResourceType": row["Type"]}} for key, row in source["Resources"].items()]}
            if operation == "get-template":
                return {"TemplateBody": deepcopy(source)}
            if operation == "execute-change-set":
                self.assertNotIn("RoleARN", arguments)
                state["sends"].append("execute")
                state["token"], state["phase"] = arguments["ClientRequestToken"], "complete"
                return {}
            if operation == "describe-stack-events":
                return {"StackEvents": [{"PhysicalResourceId": arn, "ClientRequestToken": state["token"],
                    "ResourceStatus": "CREATE_COMPLETE", "ResourceType": "AWS::CloudFormation::Stack"}]}
            self.fail("Unexpected setup read")
        def cli(command, **arguments):
            self.assertEqual(command[:3], ["aws", "cloudformation", "create-change-set"])
            self.assertNotIn("--role-arn", command)
            state["sends"].append("prepare")
            state["prepare_token"] = command[command.index("--client-token") + 1]
            state["phase"] = "prepared"
            if lose_create:
                raise helper.OWNER.SESSION_CLI.CLI.CliFailure("aws-command-timeout")
            return {"Id": "original-change-set", "StackId": arn}
        startup.provider = provider
        return startup, state, cli


    def test_invalid_start_settings_are_rejected_before_provider_or_upload(self):
        helper = self.setup
        binding = SimpleNamespace(target="kanbien-core-platform", scope="entity-smoke", session_id="a" * 32,
            starts_at=1000, expires_at=7200, source_inputs_sha256="f" * 64)
        plan = {"binding": binding, "execution_parameters": (("stack", "VpcCidr",
            (("kind", "choice"), ("contract", "private-network/v1"))),),
            "publication_selections": (("stack", (("pipeline", "fixture-pipeline"),)),)}
        preparation = SimpleNamespace(load_session_plan=lambda *_: plan,
            load=lambda *_: {"region": "eu-west-1"})
        valid = {"schema": "deploy/environment-session-start/v1",
            "intent": {"target": binding.target, "scope": binding.scope},
            "choices": {"private-network/v1": {"vpc_cidr": "10.10.0.0/16", "subnet_one_cidr": "10.10.1.0/24",
                "subnet_two_cidr": "10.10.2.0/24", "availability_zone_one": "eu-west-1a", "availability_zone_two": "eu-west-1b"}},
            "publications": {"fixture-pipeline": {"run_id": 1, "source_revision": "a" * 40}},
            "controller_publication": {"run_id": 1, "source_revision": "a" * 40}}
        cases = []
        for field, value in (("vpc_cidr", "private-canary"), ("availability_zone_one", "private-canary"),
                             ("extra-secret", "private-canary")):
            changed = deepcopy(valid)
            changed["choices"]["private-network/v1"][field] = value
            cases.append(changed)
        changed = deepcopy(valid)
        changed["publications"]["fixture-pipeline"]["secret"] = "private-canary"
        cases.append(changed)
        for document in cases:
            with self.subTest(fields=list(document["choices"]["private-network/v1"])):
                with patch.object(helper, "module", return_value=preparation), \
                        patch.object(helper.OWNER.SESSION_CLI, "SessionProvider", side_effect=AssertionError("must not call")) as provider, \
                        patch.object(helper.OWNER.RECORDS.SessionRecords, "_write_bytes", side_effect=AssertionError("must not upload")) as upload:
                    with self.assertRaises((helper.OWNER.SessionOperationFailure, helper.OWNER.FOUNDATION.FoundationFailure)) as rejected:
                        helper.Startup(root=HERE.parents[5], document=document, environment={})
                provider.assert_not_called()
                upload.assert_not_called()
                self.assertNotIn("private-canary", str(rejected.exception))
        # Normal initialization and startup consume the same canonical owner.
        with patch.object(helper.OWNER.FOUNDATION, "private_network_choice_syntax",
                side_effect=helper.OWNER.FOUNDATION.FoundationFailure("foundation-network-choices-invalid")) as syntax:
            with self.assertRaises(helper.OWNER.FOUNDATION.FoundationFailure):
                helper.OWNER.FOUNDATION.private_network_choices(lambda *_a, **_k: self.fail("No provider before syntax"),
                    valid["choices"]["private-network/v1"], "eu-west-1")
        syntax.assert_called_once()

    def test_source_bound_setup_resumes_uncertain_create_without_resubmission(self):
        for lost in (False, True):
            with self.subTest(lost=lost):
                startup, state, cli = self.fixture(lose_create=lost)
                args = ("records", startup.control["records_stack"], startup.control["records_template"],
                    {"SetupOperatorArn": startup.operator})
                with patch.object(self.setup.OWNER.SESSION_CLI.CLI, "invoke_json", side_effect=cli):
                    if lost:
                        with self.assertRaises(self.setup.OWNER.CHANGE_SETS.ChangeSetFailure) as unknown:
                            startup._stack(*args)
                        self.assertEqual(unknown.exception.code, "create-change-set-submission-uncertain")
                    self.assertEqual(startup._stack(*args)["StackStatus"], "CREATE_COMPLETE")
                    self.assertEqual(startup._stack(*args)["StackStatus"], "CREATE_COMPLETE")
                self.assertEqual(state["sends"], ["prepare", "execute"])
                with self.assertRaises(self.setup.SetupFailure):
                    startup._stack("records", "production", args[2], args[3])
                self.assertEqual(state["sends"], ["prepare", "execute"])

    def test_realization_preflight_rejects_before_execute_and_retains_original_intent(self):
        for fault in ("template", "permissions", "pagination", "source", "components", "storage"):
            with self.subTest(fault=fault):
                startup, state, cli = self.fixture()
                original = startup.provider
                def provider(service, operation, **arguments):
                    if fault == "template" and operation == "validate-template":
                        return {"Parameters": [{"ParameterKey": "private-canary"}], "Capabilities": []}
                    if fault == "permissions" and operation == "simulate-principal-policy":
                        return {"IsTruncated": False, "EvaluationResults": []}
                    if fault == "pagination" and operation == "simulate-principal-policy":
                        return {**original(service, operation, **arguments), "IsTruncated": True, "Marker": "private-canary"}
                    return original(service, operation, **arguments)
                startup.provider = provider
                if fault == "source":
                    startup.source_artifact = "sha256:" + "0" * 64
                if fault == "components":
                    startup.realization_contract["identities"].append({"id": "unobserved-extra", "permissions": ["unobserved"]})
                args = ("records", startup.control["records_stack"], startup.control["records_template"],
                    {"SetupOperatorArn": startup.operator})
                write = self.setup.OWNER.RESERVATIONS.write_exclusive
                def retain(path, value):
                    if fault == "storage" and "realization" in path.parts:
                        raise self.setup.OWNER.RESERVATIONS.ReservationFailure("retention-not-confirmed")
                    return write(path, value)
                with patch.object(self.setup.OWNER.SESSION_CLI.CLI, "invoke_json", side_effect=cli), \
                        patch.object(self.setup.OWNER.RESERVATIONS, "write_exclusive", side_effect=retain):
                    with self.assertRaises(self.setup.SetupFailure) as blocked:
                        startup._stack(*args)
                self.assertNotIn("execute", state["sends"])
                self.assertTrue(list(startup.store.root.glob("*-prepare.json")))
                expected = {"source": "setup-authority-unconfirmed", "components": "realization-components-unsupported",
                    "storage": "realization-evidence-unavailable"}
                self.assertEqual(blocked.exception.code, "environment-session-setup-" +
                    expected.get(fault, "execution-preflight-unconfirmed"))
                self.assertNotIn("private-canary", str(blocked.exception))

    def test_publication_bootstrap_is_source_qualified_without_waiving_worker_custody(self):
        startup, state, cli = self.fixture(publication=True)
        with patch.object(self.setup.OWNER.SESSION_CLI.CLI, "invoke_json", side_effect=cli):
            self.assertEqual(startup.advance()["StackStatus"], "CREATE_COMPLETE")
            self.assertEqual(startup.advance()["StackStatus"], "CREATE_COMPLETE")
        self.assertEqual(state["sends"], ["prepare", "execute"])
        completed = list(startup.store.root.glob("realization/*/completed.json"))
        self.assertEqual(len(completed), 1)
        receipt = json.loads(completed[0].read_text())
        evidence = completed[0].parent / receipt["evidence"]
        value = json.loads(evidence.read_text())
        self.assertEqual([row["gate"] for row in value["facts"]["gate_evidence"]],
            list(startup.realization.GATE.GATE_ORDER[:7]))
        evidence.unlink()
        with self.assertRaises(self.setup.SetupFailure) as blocked:
            startup.advance()
        self.assertEqual(blocked.exception.code, "environment-session-setup-execution-evidence-unconfirmed")
        self.assertEqual(state["sends"], ["prepare", "execute"])
        self.assertEqual(set(self.setup.OWNER.CF.template((startup.root / startup.control["template"]).read_text())["Resources"]),
            {"ControllerRepository", "ControllerPublisherRole"})
        startup, state, cli = self.fixture()
        startup.custody = None
        startup.source_qualification = startup.source_artifact
        with patch.object(self.setup.OWNER.SESSION_CLI.CLI, "invoke_json", side_effect=cli):
            with self.assertRaises(self.setup.SetupFailure) as blocked:
                startup._stack("records", startup.control["records_stack"], startup.control["records_template"],
                    {"SetupOperatorArn": startup.operator})
        self.assertEqual(blocked.exception.code, "environment-session-setup-artifact-unconfirmed")
        self.assertEqual(state["sends"], [])


    def test_bootstrap_preflight_repair_reuses_review_and_reserves_a_separate_execution(self):
        startup, state, cli = self.fixture(publication=True)
        provider = startup.provider
        def denied(service, operation, **arguments):
            if operation == "simulate-principal-policy":
                return {"EvaluationResults": []}
            return provider(service, operation, **arguments)
        startup.provider = denied
        with patch.object(self.setup.OWNER.SESSION_CLI.CLI, "invoke_json", side_effect=cli):
            with self.assertRaises(self.setup.SetupFailure):
                startup.advance()
            old = startup.store
            previous = json.loads((old.root / "control-prepare.json").read_text())["request"]
            original_execution = old.read("execute", previous)
            startup._read_predecessor(old)
            witness = old.root / "control-execution-not-submitted.json"
            value = json.loads(witness.read_text())
            self.assertEqual(value["origin"], "setup-pre-provider-guard")
            self.assertEqual(value["operation_id"], original_execution["operation_id"])
            witness.unlink()
            with self.assertRaises(self.setup.SetupFailure):
                startup._read_predecessor(old)
            self.assertEqual(state["sends"], ["prepare"])
            self.setup.OWNER.RESERVATIONS.write_exclusive(witness, value)
            startup._read_predecessor(old)
            startup.store = self.setup.SetupStore(old.root / "qualified-repair")
            startup.provider = provider
            self.assertEqual(startup.advance()["StackStatus"], "CREATE_COMPLETE")
            self.assertEqual(startup.advance()["StackStatus"], "CREATE_COMPLETE")
        self.assertEqual(state["sends"], ["prepare", "execute"])
        self.assertNotEqual(state["token"], original_execution["operation_id"])
        self.assertEqual(old.read("execute", previous), original_execution)
        current = json.loads((startup.store.root / "control-execute.json").read_text())
        self.assertEqual(current["request"]["predecessor_operation_id"], original_execution["operation_id"])
        startup.original_preparation["request"]["parameters"] = {"foreign": "private-canary"}
        with self.assertRaises(self.setup.SetupFailure) as blocked:
            startup.advance()
        self.assertEqual(blocked.exception.code, "environment-session-setup-predecessor-inputs-changed")
        self.assertEqual(state["sends"], ["prepare", "execute"])
        startup, state, cli = self.fixture(publication=True)
        provider = startup.provider
        def uncertain(service, operation, **arguments):
            if operation == "execute-change-set":
                state["sends"].append("execute")
                raise self.setup.OWNER.SESSION_CLI.SessionProviderFailure("aws-command-timeout")
            return provider(service, operation, **arguments)
        startup.provider = uncertain
        with patch.object(self.setup.OWNER.SESSION_CLI.CLI, "invoke_json", side_effect=cli):
            with self.assertRaises(self.setup.OWNER.CHANGE_SETS.ChangeSetFailure) as unknown:
                startup.advance()
        self.assertEqual(unknown.exception.code, "execute-change-set-submission-uncertain")
        with self.assertRaises(self.setup.SetupFailure):
            startup._read_predecessor(startup.store)
        self.assertFalse((startup.store.root / "control-execution-not-submitted.json").exists())
        self.assertEqual(state["sends"], ["prepare", "execute"])

    def test_retirement_requires_completion_and_stops_original_execution_before_one_exact_delete(self):
        helper = self.setup
        startup, _, _ = self.fixture()
        startup.root = startup.store.root
        startup.binding = {"target": "kanbien-core-platform", "session_id": "b" * 32}
        prefix = "s-" + "a" * 19
        stack_id = "arn:aws:cloudformation:eu-west-1:337159794548:stack/" + prefix + "-session-control/original"
        version = "arn:aws:states:eu-west-1:337159794548:stateMachine:" + prefix + "-expiry:1"
        document = {"binding": {"target": "kanbien-core-platform", "session_id": "a" * 32},
            "base": {"provider_facts": {"qualified-session-control/v1": "f" * 64}}}
        completed = False
        records = SimpleNamespace(account="337159794548", region="eu-west-1",
            observe_existing=lambda: {"document": deepcopy(document)},
            observe_cleanup_completion=lambda: {"status": "completed"} if completed else None)
        phases = {"execution": "RUNNING", "stack": "CREATE_COMPLETE", "build_complete": False}
        sent = []
        def provider(service, operation, **arguments):
            if (service, operation) == ("sts", "get-caller-identity"):
                return {"Account": records.account, "Arn": startup.operator, "UserId": "operator"}
            if (service, operation) == ("cloudformation", "describe-stacks"):
                if phases["stack"] == "missing":
                    raise helper.OWNER.SESSION_CLI.SessionProviderFailure("aws-resource-missing")
                return {"Stacks": [{"StackName": prefix + "-session-control", "StackId": stack_id,
                    "StackStatus": phases["stack"]}]}
            if (service, operation) == ("iam", "get-role"):
                raise helper.OWNER.SESSION_CLI.SessionProviderFailure("aws-resource-missing")
            if (service, operation) == ("cloudformation", "get-template"):
                return {"TemplateBody": {"Resources": {"Fixture": {"Type": "AWS::IAM::Role"}}}}
            if (service, operation) == ("stepfunctions", "describe-execution"):
                if ":cleanup-" in arguments["executionArn"]:
                    raise helper.OWNER.SESSION_CLI.SessionProviderFailure("aws-resource-missing")
                return {"executionArn": arguments["executionArn"], "stateMachineVersionArn": version,
                    "input": "{}", "status": phases["execution"]}
            if (service, operation) == ("stepfunctions", "stop-execution"):
                sent.append(("stop", arguments["executionArn"]))
                phases["execution"] = "ABORTED"
                return {}
            if (service, operation) == ("codebuild", "list-builds-for-project"):
                return {"ids": [prefix + "-cleanup:original"]}
            if (service, operation) == ("codebuild", "batch-get-builds"):
                return {"builds": [{"id": arguments["ids"][0], "projectName": prefix + "-cleanup",
                    "buildComplete": phases["build_complete"]}]}
            self.fail("Unexpected retirement operation")
        startup.provider = provider
        qualified = SimpleNamespace(version=version, stack_id=stack_id,
            project={"name": prefix + "-cleanup"}, parameters={"SetupOperatorArn": startup.operator},
            activate=lambda actor: self.assertEqual(actor, "requester"),
            require_predecessor_stacks_deleted=lambda old: self.assertEqual(old, document))
        def delete(command, **arguments):
            self.assertEqual(command[:5], ["aws", "cloudformation", "delete-stack", "--stack-name", stack_id])
            self.assertNotIn("--role-arn", command)
            sent.append(("delete", stack_id))
            raise helper.OWNER.SESSION_CLI.CLI.CliFailure("aws-command-timeout")
        with patch.object(helper.NATIVE, "NativeControl", return_value=qualified) as qualify, \
                patch.object(helper.OWNER.SESSION_CLI.CLI, "invoke_json", side_effect=delete):
            with self.assertRaises(helper.SetupFailure) as incomplete:
                startup.retire(records, document)
            self.assertEqual(incomplete.exception.code, "environment-session-setup-cleanup-not-completed")
            self.assertEqual(sent, [])
            completed = True
            self.assertFalse(startup.retire(records, document))
            self.assertEqual(sent, [("stop", version.rsplit(":", 1)[0].replace(":stateMachine:", ":execution:") + ":expiry-" + "a" * 32)])
            self.assertFalse(startup.retire(records, document))
            self.assertEqual(len(sent), 1)
            phases["build_complete"] = True
            with self.assertRaises(helper.OWNER.CHANGE_SETS.ChangeSetFailure):
                startup.retire(records, document)
            self.assertFalse(startup.retire(records, document))
            self.assertEqual([row for row in sent if row[0] == "delete"], [("delete", stack_id)])
            self.assertEqual(qualify.call_args.kwargs["_original_fingerprint"], "f" * 64)
            phases["stack"] = "missing"
            self.assertTrue(startup.retire(records, document))

    def test_start_command_waits_for_protection_and_preserves_functional_verdict(self):
        fixture = ControlledAssembly()
        fixture.task_status = "failed"
        setup = SimpleNamespace(advance=lambda: fixture, finish=lambda: True)
        with tempfile.TemporaryDirectory(prefix="session-start-command-") as directory:
            path = Path(directory) / "input.json"
            path.write_text("{}")
            output = io.StringIO()
            with patch.object(CONTROLLER, "start_setup", return_value=setup), contextlib.redirect_stdout(output):
                self.assertEqual(CONTROLLER.main(["start", "--input", str(path), "--max-seconds", "1"]), 1)
            self.assertEqual(json.loads(output.getvalue())["functional"]["status"], "failed")
            output = io.StringIO()
            with patch.object(CONTROLLER, "start_setup", return_value=SimpleNamespace(advance=lambda: None)), \
                    patch.object(CONTROLLER.time, "monotonic", side_effect=[0, 2]), contextlib.redirect_stdout(output):
                self.assertEqual(CONTROLLER.main(["start", "--input", str(path), "--max-seconds", "1"]), 2)
            self.assertEqual(json.loads(output.getvalue())["stage"], "setup")

class NativeControlTests(unittest.TestCase):
    def test_distinct_sessions_cannot_retarget_each_others_control_or_cleanup_version(self):
        root = HERE.parents[5]
        preparation = load("isolated_control_source", root / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py")
        base = "infra/04.deploy/03.product/targets/kanbien-core-platform"
        profile = preparation.read_document(root, base + "/00-target/target-profile.yml")
        controls = [preparation.session_control(root, base, profile, "s-" + sid * 19) for sid in ("a", "b")]
        self.assertNotEqual(controls[0]["stack"], controls[1]["stack"])
        self.assertEqual(controls[0]["records_stack"], controls[1]["records_stack"])
        self.assertEqual(controls[0]["record_key"], controls[1]["record_key"])
        runtime = load("isolated_control_runtime", root / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
        source = preparation.read_document(root, controls[0]["template"])
        names = [{key: runtime.runtime_resolve(source["Resources"][key]["Properties"][field],
            {"ResourceNamePrefix": "s-" + sid * 19}, {}, "fixture", account="337159794548", region="eu-west-1")
            for key, field in (("Cleanup", "Name"), ("Expiry", "StateMachineName"))} for sid in ("a", "b")]
        self.assertTrue(all(names[0][key] != names[1][key] for key in ("Cleanup", "Expiry")))
        records = SimpleNamespace(binding={"session_id": "a" * 32}, region="eu-west-1", account="337159794548")
        operations = SimpleNamespace(records=records)
        prefix = "arn:aws:states:eu-west-1:337159794548:stateMachine:"
        ASSEMBLY.NativeCleanup(operations=operations, owner=None, provider=None, version_arn=prefix + names[0]["Expiry"] + ":1")
        with self.assertRaises(ASSEMBLY.TaskAssemblyFailure):
            ASSEMBLY.NativeCleanup(operations=operations, owner=None, provider=None, version_arn=prefix + names[1]["Expiry"] + ":1")

    def test_workload_image_fence_matches_actual_publication_repositories(self):
        root = HERE.parents[5]
        documents = load("image_fence_documents", root / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
        runtime = load("image_fence_runtime", root / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
        source = documents.template((root / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/environment-sessions.yml").read_text())
        policy = runtime.runtime_resolve(source["Resources"]["WorkloadBoundary"]["Properties"]["PolicyDocument"],
            {"SessionId": "a" * 32, "ResourceNamePrefix": "s-" + "a" * 19, "ExpiresAt": "2030-01-01T02:00:00Z"}, {}, "fixture",
            account="337159794548", region="eu-west-1")
        repositories = next(row["Resource"] for row in policy["Statement"] if row.get("Sid") == "QualifiedImagesReadOnly")
        for name in ("core-server-persistence", "entity-smoke"):
            binding = load("fenced_" + name, root / ("scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/" + name + "-package-custody/publication.py")).PUBLISHER.binding
            self.assertIn("arn:aws:ecr:" + binding.region + ":" + binding.account + ":repository/" + binding.repository, repositories)
        self.assertNotIn("arn:aws:ecr:eu-west-1:337159794548:repository/kanbien-core-platform/environment-session-controller", repositories)

    def test_complete_native_control_snapshot_and_effective_build_identity(self):
        root = HERE.parents[5]
        owner = load("native_control_fixture_owner", root / "scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py")
        runtime = load("native_control_fixture_runtime", root / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
        reference = "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/environment-sessions.yml"
        source = owner.CF.template((root / reference).read_text())
        records_reference = reference.replace("environment-sessions.yml", "environment-session-records.yml")
        records_source = owner.CF.template((root / records_reference).read_text())
        account, region, prefix = "337159794548", "eu-west-1", "s-" + "a" * 19
        control = {"schema": "deploy/aws-session-control/v1", "stack": prefix + "-session-control", "template": reference,
            "records_stack": "kanbien-environment-session-records", "records_template": records_reference,
            "record_key": "sessions/kanbien-core-platform/current.json"}
        binding = {"session_id": "a" * 32, "expires_at": 1893463200}
        parameters = {"SessionId": "a" * 32, "ResourceNamePrefix": prefix, "WorkerReady": "true", "ExpiresAt": "2030-01-01T02:00:00Z",
            "Records": "kanbien-session-records-" + account + "-" + region,
            "SourceKey": "sources/" + "f" * 64 + ".zip", "SourceVersion": "source-version", "WorkerImage": "python@sha256:" + "f" * 64,
            "SetupOperatorArn": "arn:aws:iam::" + account + ":role/setup"}
        physical = {"Records": "kanbien-session-records-" + account + "-" + region,
            "RecordsPolicy": "kanbien-session-records-" + account + "-" + region,
            "WorkerLogs": "/aws/codebuild/" + prefix + "-cleanup", "Cleanup": prefix + "-cleanup",
            "Expiry": "arn:aws:states:" + region + ":" + account + ":stateMachine:" + prefix + "-expiry"}
        physical["ExpiryVersion"] = physical["Expiry"] + ":1"
        for key, row in source["Resources"].items():
            if row["Type"] in ("AWS::IAM::Role", "AWS::IAM::ManagedPolicy"):
                field = "RoleName" if row["Type"] == "AWS::IAM::Role" else "ManagedPolicyName"
                name = runtime.runtime_resolve(row["Properties"][field], parameters, {}, "fixture", account=account, region=region)
                physical[key] = name if field == "RoleName" else "arn:aws:iam::" + account + ":policy/" + name
        resources = {key: {"physical_id": physical[key], "type": row["Type"]} for key, row in source["Resources"].items()}
        attributes = {("Records", "Arn"): "arn:aws:s3:::" + physical["Records"],
            ("WorkerLogs", "Arn"): "arn:aws:logs:" + region + ":" + account + ":log-group:" + physical["WorkerLogs"] + ":*",
            ("Cleanup", "Arn"): "arn:aws:codebuild:" + region + ":" + account + ":project/" + physical["Cleanup"]}
        resolve = lambda value: runtime.runtime_resolve(value, {**parameters, **physical}, resources, "fixture", account=account, region=region, _attributes=attributes)
        records_resolve = lambda value: runtime.runtime_resolve(value,
            {"Records": parameters["Records"], "SetupOperatorArn": parameters["SetupOperatorArn"]}, {}, "fixture",
            account=account, region=region, _attributes={("Records", "Arn"): "arn:aws:s3:::" + parameters["Records"]})
        roles = {physical[key]: (key, resolve(row["Properties"])) for key, row in source["Resources"].items() if row["Type"] == "AWS::IAM::Role"}
        policies = {physical[key]: resolve(row["Properties"]["PolicyDocument"]) for key, row in source["Resources"].items() if row["Type"] == "AWS::IAM::ManagedPolicy"}
        selected = resolve(source["Resources"]["Cleanup"]["Properties"])
        project = {"name": selected["Name"], "arn": attributes["Cleanup", "Arn"], "serviceRole": selected["ServiceRole"], "sourceVersion": selected["SourceVersion"],
            "source": {"type": selected["Source"]["Type"], "location": selected["Source"]["Location"], "buildspec": selected["Source"]["BuildSpec"]},
            "environment": {key[:1].lower() + key[1:]: value for key, value in selected["Environment"].items()}, "artifacts": {"type": "NO_ARTIFACTS"},
            "timeoutInMinutes": 10, "queuedTimeoutInMinutes": 10, "concurrentBuildLimit": 1, "autoRetryLimit": 0, "projectVisibility": "PRIVATE"}
        build_arn = project["arn"].replace(":project/", ":build/") + ":fixture"
        build = {**deepcopy(project), "arn": build_arn, "projectName": selected["Name"], "buildStatus": "IN_PROGRESS", "artifacts": {}}
        stack_id = "arn:aws:cloudformation:" + region + ":" + account + ":stack/" + control["stack"] + "/fixture"
        calls = []
        def provider(service, operation, **arguments):
            calls.append((service, operation))
            if service == "cloudformation":
                if control["records_stack"] in arguments["StackName"]:
                    if operation == "describe-stacks": return {"Stacks": [{"StackId": "arn:aws:cloudformation:" + region + ":" + account + ":stack/" + control["records_stack"] + "/fixture",
                        "StackName": control["records_stack"], "StackStatus": "CREATE_COMPLETE", "Parameters": [{"ParameterKey": "SetupOperatorArn", "ParameterValue": parameters["SetupOperatorArn"]}]}]}
                    if operation == "get-template": return {"TemplateBody": records_source}
                    if operation == "list-stack-resources": return {"StackResourceSummaries": [{"LogicalResourceId": key, "ResourceType": row["Type"], "PhysicalResourceId": parameters["Records"]} for key, row in records_source["Resources"].items()]}
                if operation == "describe-stacks": return {"Stacks": [{"StackId": stack_id, "StackName": control["stack"], "StackStatus": "CREATE_COMPLETE", "Parameters": [{"ParameterKey": k, "ParameterValue": v} for k, v in parameters.items()]}]}
                if operation == "get-template": return {"TemplateBody": source}
                if operation == "list-stack-resources": return {"StackResourceSummaries": [{"LogicalResourceId": key, "ResourceType": row["Type"], "PhysicalResourceId": physical[key]} for key, row in source["Resources"].items()]}
            if service == "backup": return {"BackupPlansList": []}
            if service == "iam":
                if operation == "get-policy": return {"Policy": {"Arn": arguments["PolicyArn"], "IsAttachable": True, "DefaultVersionId": "v1"}}
                if operation == "get-policy-version": return {"PolicyVersion": {"VersionId": "v1", "IsDefaultVersion": True, "Document": policies[arguments["PolicyArn"]]}}
                key, properties = roles[arguments["RoleName"]]
                if operation == "get-role": return {"Role": {"RoleName": arguments["RoleName"], "Arn": "arn:aws:iam::" + account + ":role/" + arguments["RoleName"], "RoleId": "AROA" + key, "Path": "/", "MaxSessionDuration": properties.get("MaxSessionDuration", 3600), "AssumeRolePolicyDocument": properties["AssumeRolePolicyDocument"]}}
                if operation == "list-attached-role-policies": return {"AttachedPolicies": [{"PolicyArn": physical[name], "PolicyName": physical[name].rsplit("/", 1)[-1]} for name, row in source["Resources"].items() if row["Type"] == "AWS::IAM::ManagedPolicy" and {"Ref": key} in row["Properties"].get("Roles", [])], "IsTruncated": False}
                inline = {row["PolicyName"]: row["PolicyDocument"] for row in properties.get("Policies", [])}
                if operation == "list-role-policies": return {"PolicyNames": list(inline), "IsTruncated": False}
                if operation == "get-role-policy": return {**arguments, "PolicyDocument": inline[arguments["PolicyName"]]}
            if service == "stepfunctions": return {"type": "STANDARD", "roleArn": "arn:aws:iam::" + account + ":role/" + physical["ExpiryRole"], "definition": json.dumps(resolve(source["Resources"]["Expiry"]["Properties"]["Definition"]))}
            if service == "s3api":
                return {"get-bucket-versioning": {"Status": "Enabled"}, "get-public-access-block": {"PublicAccessBlockConfiguration": records_source["Resources"]["Records"]["Properties"]["PublicAccessBlockConfiguration"]},
                    "get-bucket-ownership-controls": {"OwnershipControls": records_source["Resources"]["Records"]["Properties"]["OwnershipControls"]},
                    "get-bucket-encryption": {"ServerSideEncryptionConfiguration": {"Rules": records_source["Resources"]["Records"]["Properties"]["BucketEncryption"]["ServerSideEncryptionConfiguration"]}},
                    "get-bucket-policy": {"Policy": json.dumps(records_resolve(records_source["Resources"]["RecordsPolicy"]["Properties"]["PolicyDocument"]))}}[operation]
            if service == "codebuild": return {"projects": [project]} if operation == "batch-get-projects" else {"builds": [build]}
            if service == "sts": return {"Account": account, "Arn": "arn:aws:sts::" + account + ":assumed-role/" + physical["WorkerRole"] + "/fixture", "UserId": "AROAWorkerRole:fixture"}
            self.fail((service, operation))
        qualified = ASSEMBLY.NativeControl(root=root, configuration={"account": account, "region": region}, binding=binding, control=control, owner=owner, provider=provider)
        self.assertEqual(len(qualified.fingerprint), 64)
        original = ASSEMBLY.NativeControl(root=root, configuration={"account": account, "region": region}, binding=binding,
            control=control, owner=owner, provider=provider, _source=source, _original_fingerprint=qualified.fingerprint)
        self.assertEqual(original.fingerprint, qualified.fingerprint)
        source["Metadata"] = {"unapproved-change": True}
        with self.assertRaises(ASSEMBLY.TaskAssemblyFailure) as changed:
            ASSEMBLY.NativeControl(root=root, configuration={"account": account, "region": region}, binding=binding,
                control=control, owner=owner, provider=provider, _source=source, _original_fingerprint=qualified.fingerprint)
        self.assertEqual(changed.exception.code, "environment-session-task-control-original-context-changed")
        del source["Metadata"]
        qualified.activate("worker", environment={"CODEBUILD_BUILD_ARN": build_arn})
        qualified.guard("observe", binding)
        build["sourceVersion"] = "foreign-version"
        with self.assertRaises(ASSEMBLY.TaskAssemblyFailure): qualified.activate("worker", environment={"CODEBUILD_BUILD_ARN": build_arn})
        self.assertTrue(all(operation.startswith(("get-", "list-", "describe-", "batch-get-")) for _, operation in calls))

    def test_effective_worker_source_image_role_and_environment_cannot_be_overridden(self):
        control = ASSEMBLY.NativeControl.__new__(ASSEMBLY.NativeControl)
        control.expected_project = {"ServiceRole": "arn:aws:iam::337159794548:role/worker", "SourceVersion": "version-1",
            "TimeoutInMinutes": 10, "QueuedTimeoutInMinutes": 10, "ConcurrentBuildLimit": 1, "AutoRetryLimit": 0, "Visibility": "PRIVATE",
            "Source": {"Type": "S3", "Location": "private/sources/source.zip", "BuildSpec": "fixed command"},
            "Environment": {"Type": "LINUX_CONTAINER", "ComputeType": "BUILD_GENERAL1_SMALL", "Image": "python@sha256:" + "a" * 64,
                "ImagePullCredentialsType": "SERVICE_ROLE", "PrivilegedMode": False}}
        original = {"serviceRole": control.expected_project["ServiceRole"], "sourceVersion": "version-1",
            "timeoutInMinutes": 10, "queuedTimeoutInMinutes": 10, "concurrentBuildLimit": 1, "autoRetryLimit": 0, "projectVisibility": "PRIVATE",
            "source": {"type": "S3", "location": "private/sources/source.zip", "buildspec": "fixed command"},
            "environment": {key[:1].lower() + key[1:]: value for key, value in control.expected_project["Environment"].items()},
            "artifacts": {"type": "NO_ARTIFACTS"}}
        control._project_configuration(original)
        for field, key, value in (("source", "location", "foreign/source.zip"), ("source", "buildspec", "other command"),
                ("environment", "image", "other@sha256:" + "b" * 64), ("environment", "privilegedMode", True),
                ("environment", "environmentVariables", [{"name": "AWS_CONFIG_FILE", "value": "foreign"}])):
            changed = deepcopy(original)
            changed[field][key] = value
            with self.assertRaises(ASSEMBLY.TaskAssemblyFailure): control._project_configuration(changed)
        for key, value in (("serviceRole", "foreign"), ("sourceVersion", "other-version"), ("timeoutInMinutes", 480), ("concurrentBuildLimit", 5), ("projectVisibility", "PUBLIC")):
            changed = {**original, key: value}
            with self.assertRaises(ASSEMBLY.TaskAssemblyFailure): control._project_configuration(changed)
        build = {**original, "artifacts": {}}
        control._project_configuration(build, build=True)
        build["artifacts"] = {"location": "arn:aws:s3:::foreign/output"}
        with self.assertRaises(ASSEMBLY.TaskAssemblyFailure): control._project_configuration(build, build=True)


class NativeRoleBoundaryTests(unittest.TestCase):
    def test_managed_policy_requires_actual_matching_default_version(self):
        runtime = load("checked_managed_policy", HERE.parents[5] / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
        arn = "arn:aws:iam::337159794548:policy/session-metadata"
        expected = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "ec2:DescribeVpcs", "Resource": "*"}]}
        metadata = {"Arn": arn, "IsAttachable": True, "DefaultVersionId": "v2"}
        version = {"VersionId": "v2", "IsDefaultVersion": True, "Document": deepcopy(expected)}
        calls = []
        def provider(service, operation, **arguments):
            calls.append((service, operation, arguments))
            return {"Policy": deepcopy(metadata)} if operation == "get-policy" else {"PolicyVersion": deepcopy(version)}
        self.assertIsInstance(runtime.runtime_managed_policy(provider, arn, expected, "fixture"), str)
        self.assertEqual(calls[-1], ("iam", "get-policy-version", {"PolicyArn": arn, "VersionId": "v2"}))
        for field, wrong in (("VersionId", "v1"), ("IsDefaultVersion", False), ("Document", {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]})):
            original = version[field]
            version[field] = wrong
            with self.assertRaises(runtime.BindingFailure):
                runtime.runtime_managed_policy(provider, arn, expected, "fixture")
            version[field] = original

    def test_runtime_role_requires_exact_declared_boundary_and_preserves_unbounded_source(self):
        runtime = load("checked_role_boundary", HERE.parents[5] / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
        account, region = "337159794548", "eu-west-1"
        trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "sts:AssumeRole", "Principal": {"Service": "ecs-tasks.amazonaws.com"}}]}
        boundary = "arn:aws:iam::" + account + ":policy/session-workloads"
        properties = {"RoleName": "checked-role", "AssumeRolePolicyDocument": trust, "PermissionsBoundary": boundary}
        observed = {"RoleName": "checked-role", "Arn": "arn:aws:iam::" + account + ":role/checked-role", "Path": "/", "AssumeRolePolicyDocument": trust}
        def provider(service, operation, **arguments):
            self.assertEqual((service, arguments), ("iam", {"RoleName": "checked-role"}))
            return {"Role": deepcopy(observed)} if operation == "get-role" else ({"AttachedPolicies": [], "IsTruncated": False} if operation == "list-attached-role-policies" else {"PolicyNames": [], "IsTruncated": False})
        def check():
            return runtime.runtime_role(provider, "Role", {}, {"Role": {"physical_id": "checked-role"}}, "fixture",
                {"Resources": {"Role": {"Properties": properties}}}, account=account, region=region)
        for wrong in (None, {"PermissionsBoundaryType": "Policy", "PermissionsBoundaryArn": boundary + "-foreign"},
                      {"PermissionsBoundaryType": "Other", "PermissionsBoundaryArn": boundary}):
            if wrong is None: observed.pop("PermissionsBoundary", None)
            else: observed["PermissionsBoundary"] = wrong
            with self.assertRaises(runtime.BindingFailure): check()
        observed["PermissionsBoundary"] = {"PermissionsBoundaryType": "Policy", "PermissionsBoundaryArn": boundary}
        self.assertIsInstance(check(), str)
        properties.pop("PermissionsBoundary")
        with self.assertRaises(runtime.BindingFailure): check()
        observed.pop("PermissionsBoundary")
        self.assertIsInstance(check(), str)


class ConnectedRecordsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = HERE.parents[5]
        cls.native = load("session_controller_native_fixture", root / "scripts/04.deploy/shared/provider-adapters/aws/environment-sessions-test.py")
        cls.native.SessionHandoffTests.setUpClass()

    def fixture(self):
        fixture = self.native.SessionHandoffTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.enterContext(fixture.in_process_aws())
        return fixture

    def test_completed_predecessor_requires_native_admission_and_is_replaced_only_by_cas(self):
        fixture = self.fixture()
        fixture.initialize()
        fixture.records.retain_functional({"status": "interrupted"})
        fixture.adapter.seal()
        self.assertEqual(fixture.adapter.complete_cleanup()["status"], "completed")
        old = fixture.read()
        intent = {**fixture.session_document, "session_id": "b" * 32}
        plan = fixture.preparation.load_session_plan(HERE.parents[5], intent["target"], intent["scope"], intent, 1000, 7200)
        fixture.select_plan(plan)
        calls = []
        def admit(prior, document):
            calls.append(document["binding"]["session_id"])
            self.assertEqual(prior.binding, document["binding"])
            self.assertEqual(prior.observe_cleanup_completion()["status"], "completed")
        rejected = fixture.make_records(successor=lambda *_: True)
        with self.assertRaises(self.native.OWNER.RECORDS.SessionRecordFailure) as invalid:
            rejected.observe_initialization()
        self.assertEqual(invalid.exception.code, "session-predecessor-unconfirmed")
        self.assertEqual(fixture.read()["raw"], old["raw"])
        writes = 0
        def competing_writer(action, binding):
            nonlocal writes
            fixture.guard(action, binding)
            if action == "initialize":
                writes += 1
                if writes == 2:
                    state = fixture.read()
                    state["version"] += 1
                    fixture.write(state)
        competing = fixture.make_records(successor=admit, guard=competing_writer)
        competing_operations = fixture.make_adapter(plan, competing, provider=fixture.provider, preflight=fixture.preflight)
        with self.assertRaises(self.native.OWNER.RECORDS.SessionRecordFailure) as conflict:
            fixture.initialize(competing_operations)
        self.assertEqual(conflict.exception.code, "session-record-conflict")
        self.assertEqual(fixture.read()["raw"], old["raw"])
        records = fixture.make_records(successor=admit)
        operations = fixture.make_adapter(plan, records, provider=fixture.provider, preflight=fixture.preflight)
        document = fixture.initialize(operations)
        self.assertEqual(document["binding"]["session_id"], "b" * 32)
        self.assertGreater(len(calls), 0)
        self.assertIn(old["raw"], fixture.read()["history"])
        self.assertEqual(fixture.read()["submissions"], [])
        self.assertEqual(fixture.initialize(operations), document)

    def test_native_successor_rejects_live_or_unknown_previous_authority(self):
        owner = self.native.OWNER
        control = ASSEMBLY.NativeControl.__new__(ASSEMBLY.NativeControl)
        control.actor, control.owner = "foreground", owner
        control.binding = {"target": "kanbien-core-platform", "session_id": "b" * 32}
        document = {"binding": {"target": "kanbien-core-platform", "session_id": "a" * 32}, "incarnations": {}}
        calls = []
        def absent(service, operation, **arguments):
            calls.append((service, operation, arguments))
            raise owner.SESSION_CLI.SessionProviderFailure("aws-resource-missing")
        control.setup_provider = absent
        self.assertIsNone(control.admit_successor(None, document))
        self.assertEqual(len(calls), 6)
        for value in ({}, owner.SESSION_CLI.SessionProviderFailure("aws-access-denied")):
            def rejected(*_args, **_arguments):
                if isinstance(value, Exception): raise value
                return value
            control.setup_provider = rejected
            with self.assertRaises(ASSEMBLY.TaskAssemblyFailure):
                control.admit_successor(None, document)

    def test_qualified_setup_fingerprint_is_retained_and_changed_cold_setup_rejects(self):
        fixture = self.fixture()
        def adapter(fingerprint):
            return fixture.make_adapter(fixture.plan, fixture.make_records(), provider=fixture.provider,
                preflight=fixture.preflight, qualified_facts={"qualified-session-control/v1": fingerprint})
        selected = adapter("a" * 64)
        document = fixture.initialize(selected)
        self.assertEqual(document["base"]["provider_facts"]["qualified-session-control/v1"], "a" * 64)
        without = deepcopy(document)
        without["base"]["provider_facts"].pop("qualified-session-control/v1")
        growth = fixture.records._completion_size(document) - fixture.records._completion_size(without)
        self.assertEqual(growth, len(json.dumps({"qualified-session-control/v1": "a" * 64}, separators=(",", ":"))) - 1)
        before = deepcopy(fixture.read()["history"])
        self.assertEqual(fixture.initialize(adapter("a" * 64)), document)
        self.assertEqual(fixture.read()["history"], before)
        with self.assertRaises(self.native.OWNER.SessionOperationFailure) as changed:
            fixture.initialize(adapter("b" * 64))
        self.assertEqual(changed.exception.code, "environment-session-operation-control-facts-mismatch")
        self.assertEqual(fixture.read()["history"], before)

    def test_network_role_binding_uses_original_output_and_never_replays_retained_intent(self):
        fixture = self.fixture()
        document = fixture.initialize()
        operations = fixture.adapter
        row = next(row for row in operations._plan["stack_parameter_sources"] if row[1] == "VpcId")
        stack, _, producer, output = row
        arn = document["base"]["execution_roles"]["creation"]
        control = ASSEMBLY.NativeControl.__new__(ASSEMBLY.NativeControl)
        control.actor, control.roles, control.role_ids = "foreground", {"CreationRole": arn}, {"CreationRole": "AROAoriginal"}
        control.require_expiry = lambda: None
        tags, sends = [], []
        def observe(service, operation, **arguments):
            self.assertEqual((service, operation, arguments), ("iam", "get-role", {"RoleName": arn.rsplit("/", 1)[-1]}))
            return {"Role": {"Arn": arn, "RoleId": "AROAoriginal", "Tags": deepcopy(tags)}}
        def submit(service, operation, **arguments):
            self.assertIsNotNone(fixture.records.observe_task_state(operations._task_selections)["network_binding"])
            self.assertEqual((service, operation), ("iam", "tag-role"))
            sends.append(deepcopy(arguments))
            tags[:] = arguments["Tags"]
            raise RuntimeError("private-response-lost")
        control.provider, control.setup_provider = observe, submit
        view = {"outputs": {output: "vpc-12345678"}}
        with patch.object(operations, "runtime_view", return_value=view) as runtime:
            self.assertEqual(control.bind_network(operations, stack), {"status": "ready"})
            runtime.assert_called_once_with(stack=producer, required_outputs=[output])
            self.assertEqual(control.bind_network(operations, stack), {"status": "ready"})
            self.assertEqual(len(sends), 1)
            # Missing native confirmation after a retained send is observation
            # only, even when the response was lost or a process restarted.
            tags.clear()
            self.assertEqual(control.bind_network(operations, stack)["status"], "pending")
            self.assertEqual(len(sends), 1)
            tags[:] = [{"Key": "kanbien:session-vpc-id", "Value": "vpc-87654321"}]
            with self.assertRaises(ASSEMBLY.TaskAssemblyFailure) as conflict:
                control.bind_network(operations, stack)
            self.assertEqual(conflict.exception.code, "environment-session-task-control-network-binding-conflict")
            self.assertEqual(len(sends), 1)
            tags.clear()
            view["outputs"][output] = "vpc-87654321"
            with self.assertRaises(self.native.OWNER.RECORDS.SessionRecordFailure) as changed:
                control.bind_network(operations, stack)
            self.assertEqual(changed.exception.code, "session-network-binding-conflict")
            self.assertEqual(len(sends), 1)
        fixture.adapter.seal()
        with self.assertRaises(self.native.OWNER.RECORDS.SessionRecordFailure) as sealed:
            control.bind_network(operations, stack)
        self.assertEqual(sealed.exception.code, "session-admission-closed")
        self.assertEqual(len(sends), 1)

    def test_expired_worker_factory_uses_original_native_record_and_integer_clock(self):
        fixture = self.fixture()
        state = fixture.read()
        key = fixture.plan["control"]["record_key"]
        state["parent_key"] = key
        fixture.write(state)
        fixture.records = fixture.make_records(key=key, profile=None)
        selected = fixture.make_adapter(fixture.plan, fixture.records, provider=fixture.provider, preflight=fixture.preflight,
            qualified_facts={"qualified-session-control/v1": "a" * 64})
        fixture.initialize(selected)
        class QualifiedSnapshot:
            def __init__(self, **arguments):
                self.bucket, self.fingerprint = fixture.records.bucket, "a" * 64
                self.guard, self.preflight = fixture.guard, fixture.preflight
            def activate(self, actor, **arguments):
                if actor != "worker": raise AssertionError("worker required")
        document = {"schema": "deploy/environment-session-command/v1", "intent": deepcopy(fixture.session_document),
            "source_inputs_sha256": fixture.binding["source_inputs_sha256"], "choices": fixture.choices, "publications": fixture.publications}
        environment = {**fixture.environment, "CODEBUILD_BUILD_ARN": "qualified-by-separate-native-metadata-test"}
        with patch.object(ASSEMBLY, "NativeControl", QualifiedSnapshot):
            assembly = ASSEMBLY.existing_assembly(root=HERE.parents[5], document=document, environment=environment)
            self.assertIsInstance(assembly.records._now(), int)
            self.assertGreater(assembly.records._now(), fixture.binding["expires_at"])
            result = CONTROLLER.Controller(assembly).advance("cleanup")
        self.assertEqual(result["cleanup"]["status"], "completed")
        self.assertEqual(result["functional"], {"status": "interrupted"})
        self.assertFalse(fixture.read()["submissions"])

    def test_fixed_cleanup_handoff_reserves_once_and_requires_native_physical_completion(self):
        fixture = self.fixture()
        fixture.initialize()
        calls = []
        version = "arn:aws:states:" + fixture.records.region + ":" + fixture.records.account + ":stateMachine:" + fixture.plan["resource_name_prefix"] + "-expiry:1"
        def provider(service, operation, **arguments):
            self.assertEqual(service, "stepfunctions")
            calls.append(operation)
            if operation == "start-execution":
                self.assertIsNotNone(fixture.records.read_report(fixture.adapter._task_selections, "functional")["cleanup_invocation"])
                return {"executionArn": selected.cleanup.execution}
            return {"executionArn": selected.cleanup.execution, "stateMachineVersionArn": version,
                    "input": '{"cleanup_now":true}', "status": "SUCCEEDED"}
        def assembly(remote):
            operations = fixture.make_adapter(fixture.plan, fixture.make_records(), provider=fixture.provider, preflight=fixture.preflight)
            tasks = ASSEMBLY.NativeTasks(root=HERE.parents[5], plan=fixture.plan, operations=operations,
                owner=self.native.OWNER, aws=lambda *_: self.fail("An unallocated session must not launch tasks"))
            cleanup = ASSEMBLY.NativeCleanup(operations=operations, owner=self.native.OWNER, provider=provider, version_arn=version) if remote else None
            return ASSEMBLY.SessionAssembly(plan=fixture.plan, operations=operations, owner=self.native.OWNER,
                tasks=tasks, choices=fixture.choices, publications=fixture.publications, cleanup=cleanup)
        selected = assembly(True)
        selected.retain_functional({"status": "interrupted"})
        result = CONTROLLER.Controller(selected).advance("cleanup")
        self.assertEqual(result["cleanup"]["status"], "blocked")
        self.assertIsNone(fixture.records.observe_cleanup_completion())
        self.assertEqual(calls.count("start-execution"), 1)
        cold = CONTROLLER.Controller(assembly(True)).advance("cleanup")
        self.assertEqual(cold["cleanup"]["status"], "blocked")
        self.assertEqual(calls.count("start-execution"), 1)
        worker = CONTROLLER.Controller(assembly(False)).advance("cleanup")
        self.assertEqual(worker["cleanup"]["status"], "completed")
        before = list(calls)
        final = CONTROLLER.Controller(assembly(True)).advance("cleanup")
        self.assertEqual(final["cleanup"], fixture.records.observe_cleanup_completion())
        self.assertEqual(calls, before)
        self.assertEqual(final["functional"], {"status": "interrupted"})

    def test_failed_functional_diagnostic_survives_cleanup_and_fresh_expired_worker(self):
        fixture = self.fixture()
        fixture.select_plan(fixture.entity_plan)
        fixture.initialize()
        def assembly():
            operations = fixture.make_adapter(fixture.plan, fixture.make_records(),
                provider=fixture.provider, preflight=fixture.preflight)
            tasks = ASSEMBLY.NativeTasks(root=HERE.parents[5], plan=fixture.plan, operations=operations,
                owner=self.native.OWNER, aws=lambda *_: self.fail("An unallocated session must not launch a task"))
            return ASSEMBLY.SessionAssembly(plan=fixture.plan, operations=operations,
                owner=self.native.OWNER, tasks=tasks, choices=fixture.choices, publications=fixture.publications)
        selected = assembly()
        row = next(row for row in dict(fixture.plan["task_selections"])["entity-smoke"]["steps"]
            if row["workload"] == "verifier" and row["phase"] == "preflight")
        selected.tasks.current = {"component": "entity-smoke", "step": row["key"]}
        diagnostic = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.proof-failed",
            "definitionVersion": 1, "detail": {"operation": "ready", "step": "readiness",
                "condition": "status-mismatch", "effect": "not-assessed"}}
        failure = selected.tasks.entity_runner.EVIDENCE.EvidenceFailure("task-success-observation-not-confirmed", diagnostic=diagnostic)
        reason = selected.failure_code(failure)
        selected.retain_functional({"status": "failed", "reason": reason})
        result = CONTROLLER.Controller(selected).advance("cleanup")
        self.assertEqual(result["functional"], {"status": "failed", "reason": reason})
        self.assertEqual(result["cleanup"]["status"], "completed")
        report = fixture.records.read_report(fixture.adapter._task_selections, "functional")
        self.assertEqual(report["diagnostics"]["diagnostic"], diagnostic)
        self.assertEqual(report["task"], selected.tasks.current)
        original = deepcopy(fixture.read()["history"])
        fixture.now = 8200
        cold = CONTROLLER.Controller(assembly()).advance("cleanup")
        self.assertEqual(cold["functional"], result["functional"])
        self.assertEqual(cold["cleanup"]["status"], "completed")
        self.assertEqual(fixture.records.read_report(fixture.adapter._task_selections, "functional"), report)
        self.assertEqual(fixture.read()["history"], original)
        self.assertFalse(fixture.read()["submissions"])

    def test_empty_task_state_still_requires_exact_session_and_complete_slot_set(self):
        fixture = self.fixture()
        fixture.initialize()
        tasks = ASSEMBLY.NativeTasks(root=HERE.parents[5], plan=fixture.plan, operations=fixture.adapter,
            owner=self.native.OWNER, aws=lambda *_: self.fail("No task may launch"))
        self.assertEqual(tasks.reconcile(), {"status": "ready"})
        original = fixture.read()
        checked = fixture.records.observe_task_state(fixture.adapter._task_selections)
        for field in ("schema", "binding", "base_sha256", "source_plan_sha256", "slots"):
            with self.subTest(field=field):
                changed = deepcopy(checked)
                changed[field] = [] if field == "slots" else None
                reference = fixture.records._retain_child(self.native.OWNER.RESERVATIONS.canonical(changed),
                    max_bytes=self.native.OWNER.RECORDS.CHILD_LIMIT)
                state = fixture.read()
                document = json.loads(state["raw"])
                document["task_state"] = reference
                state["raw"] = json.dumps(document)
                fixture.write(state)
                with self.assertRaises(self.native.OWNER.RECORDS.SessionRecordFailure) as denied:
                    tasks.reconcile()
                self.assertEqual(denied.exception.code, "session-task-state-invalid")
                fixture.write(original)

    def entity_fixture(self, *, task_status="STOPPED", stop_lost=False):
        fixture = self.fixture()
        fixture.select_plan(fixture.entity_plan)
        fixture.task_identities(native=True)
        fixture.create_graph()
        component = "entity-smoke"
        selections = dict(fixture.plan["task_selections"])[component]["steps"]
        launched = []
        fixture.task_stops = []
        def aws(service, operation, *arguments):
            def value(flag):
                return arguments[arguments.index(flag) + 1]
            if (service, operation) == ("ecs", "run-task"):
                state = fixture.records.observe_task_state(fixture.adapter._task_selections)
                record, slot = next((json.loads(fixture.records._read_child(slot["current"])), slot)
                    for slot in state["slots"] if slot is not None
                    and json.loads(fixture.records._read_child(slot["current"]))["operation_id"] == value("--started-by"))
                self.assertEqual(slot["admission"], "admitted")
                request = record["request"]
                probe = "ready" if request["workload"] == "verifier" else "preflight"
                if request["environment"][tasks.entity_runner.CONTROL.OPERATIONS[request["workload"]][0]] != probe:
                    self.assertIsNotNone(slot["context"])
                stamp = datetime.now(timezone.utc).isoformat()
                task = {"taskArn": value("--cluster").replace(":cluster/", ":task/") + "/" + f"{len(launched)+1:032x}",
                    "taskDefinitionArn": value("--task-definition"), "startedBy": value("--started-by"),
                    "overrides": json.loads(value("--overrides")), "lastStatus": task_status, "launchType": "FARGATE",
                    "createdAt": stamp, "startedAt": stamp, "stoppedAt": stamp,
                    "containers": [{"name": request["runtime"]["container_name"], "imageDigest": request["image_digest"], "exitCode": 0}]}
                launched.append((task, request))
                return True, {"tasks": [deepcopy(task)]}, "ok"
            if (service, operation) == ("ecs", "stop-task"):
                fixture.task_stops.append(value("--task"))
                self.assertEqual(value("--reason"), "temporary-session-cleanup")
                task = next(task for task, _ in launched if task["taskArn"] == value("--task"))
                task["lastStatus"] = "STOPPING"
                return (False, None, "aws-command-timeout") if stop_lost else (True, {"task": deepcopy(task)}, "ok")
            if (service, operation) == ("ecs", "describe-tasks"):
                return True, {"tasks": [deepcopy(task) for task, _ in launched if task["taskArn"] == value("--tasks")]}, "ok"
            if (service, operation) == ("ecs", "list-tasks"):
                return True, {"taskArns": [task["taskArn"] for task, _ in launched
                    if value("--desired-status") == ("STOPPED" if task["lastStatus"] == "STOPPED" else "RUNNING")
                    and value("--family") in task["taskDefinitionArn"]]}, "ok"
            if (service, operation) == ("logs", "get-log-events"):
                task, request = next((task, request) for task, request in launched
                    if task["taskArn"].endswith(value("--log-stream-name").rsplit("/", 1)[1]))
                selected_operation = request["environment"][tasks.entity_runner.CONTROL.OPERATIONS[request["workload"]][0]]
                result = {"verdict": "passed", "operation": selected_operation,
                          "code": "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED" if selected_operation == "preflight" else "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED"}
                workload = request["workload"]
                if workload == "migration" and selected_operation != "preflight":
                    result["code"] = "ENTITY_SMOKE_MIGRATION_APPLIED"
                if selected_operation == "preflight" or workload == "migration":
                    if workload != "administration":
                        del result["operation"]
                elif workload in {"verifier", "database-proof"}:
                    evidence = tasks.entity_runner.EVIDENCE
                    verifier = workload == "verifier"
                    steps = evidence.HTTP_STEPS[selected_operation] if verifier else (
                        ["identity", "read", "collision", "read"] if selected_operation == "collision" else
                        ["identity", "delete", "truncate", "create-table", "alter-table", "drop-table", "history-write"])
                    result = {"schema": "deploy/entity-smoke-task-proof/v1" if verifier else "deploy/entity-smoke-database-proof/v1",
                        "verdict": "passed", "operation": selected_operation,
                        "code": evidence.HTTP_CODES[selected_operation] if verifier else (
                            "ENTITY_SMOKE_IDENTIFIER_COLLISION_PROVEN" if selected_operation == "collision" else "ENTITY_SMOKE_EFFECTIVE_PRIVILEGES_PROVEN"),
                        "steps": steps, "checked_at": task["stoppedAt"],
                        "proof_label_sha256": hashlib.sha256(request["proof_label"].encode()).hexdigest()}
                    if verifier:
                        result["source_revision"] = request["source_revision"]
                    if not verifier and selected_operation == "collision" or verifier and selected_operation != "ready":
                        result["record_digest"] = request["environment"].get("ENTITY_SMOKE_EXPECTED_DIGEST", "a" * 64)
                elif workload != "administration":
                    del result["operation"]
                return True, {"events": [] if "--next-token" in arguments else [{"message": json.dumps(result)}],
                              "nextForwardToken": "done"}, "ok"
            self.fail(f"Unexpected fixture operation: {service} {operation}")
        def consumer():
            return ASSEMBLY.NativeTasks(root=HERE.parents[5], plan=fixture.plan, operations=fixture.adapter,
                owner=self.native.OWNER, aws=aws)
        tasks = consumer()
        return fixture, tasks, consumer, selections, launched


    def test_sealed_unadmitted_intent_closes_without_inventing_a_task_or_sending_stop(self):
        fixture, tasks, consumer, selections, launched = self.entity_fixture()
        with patch.object(tasks.entity_runner.CONTROL.TASKS, "submit_task", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                tasks.run("entity-smoke", selections[0])
        self.assertEqual(launched, [])
        with self.assertRaises(self.native.OWNER.RECORDS.SessionRecordFailure) as open_admission:
            tasks.reconcile()
        self.assertEqual(open_admission.exception.code, "session-task-admission-open")
        fixture.adapter.seal()
        self.assertEqual(tasks.reconcile(), {"status": "ready"})
        self.assertEqual(consumer().reconcile(), {"status": "ready"})
        state = fixture.records.observe_task_state(fixture.adapter._task_selections)
        self.assertEqual([slot["admission"] for slot in state["slots"] if slot is not None], ["not-submitted"])
        self.assertEqual(launched, [])
        self.assertEqual(fixture.task_stops, [])

    def test_hung_task_stop_is_owned_sealed_and_never_replayed_after_uncertainty(self):
        for lost in (False, True):
            with self.subTest(lost=lost):
                fixture, tasks, consumer, selections, launched = self.entity_fixture(task_status="RUNNING", stop_lost=lost)
                with patch.object(tasks.entity_runner.CONTROL.TASKS, "observe_until_terminal",
                        side_effect=lambda read, **kw: (kw["initial"], False)):
                    with self.assertRaises(tasks.entity_runner.RunnerFailure) as hung:
                        tasks.run("entity-smoke", selections[0])
                self.assertEqual(hung.exception.code, "task-deadline-remote-operation-not-terminal")
                with self.assertRaises(self.native.OWNER.RECORDS.SessionRecordFailure) as open_admission:
                    tasks.reconcile()
                self.assertEqual(open_admission.exception.code, "session-task-admission-open")
                self.assertFalse(fixture.task_stops)
                fixture.adapter.seal()
                original = deepcopy(launched[0][0])
                launched[0][0]["startedBy"] = "foreign"
                with self.assertRaises(Exception):
                    tasks.reconcile()
                self.assertFalse(fixture.task_stops)
                launched[0][0].update(original)
                if lost:
                    with self.assertRaises(tasks.binding.TASKS.TaskFailure) as uncertain:
                        tasks.reconcile()
                    self.assertEqual(uncertain.exception.code, "submission-uncertain")
                else:
                    self.assertEqual(tasks.reconcile()["status"], "pending")
                self.assertEqual(fixture.task_stops, [original["taskArn"]])
                self.assertEqual(consumer().reconcile()["status"], "pending")
                self.assertEqual(fixture.task_stops, [original["taskArn"]])
                launched[0][0]["lastStatus"] = "STOPPED"
                self.assertEqual(consumer().reconcile(), {"status": "ready"})
                self.assertEqual(fixture.task_stops, [original["taskArn"]])

    def test_entity_preflight_and_business_receipts_survive_cold_worker_without_local_files(self):
        fixture, tasks, consumer, selections, launched = self.entity_fixture()
        component = "entity-smoke"
        for row in selections[:2]:
            self.assertEqual(tasks.run(component, row)["status"], "succeeded")
        self.assertEqual(len(launched), 2)
        cold = consumer()
        for row in selections[:2]:
            self.assertEqual(cold.run(component, row), {"status": "succeeded", "reused": True})
        self.assertEqual(cold.reconcile(), {"status": "ready"})
        self.assertEqual(len(launched), 2)
        # A complete receipt is insufficient if its original admission vanished.
        original = fixture.read()
        state = fixture.records.observe_task_state(fixture.adapter._task_selections)
        index = next(index for index, row in enumerate(state["selections"])
            if (row["component"], row["step"]) == (component, selections[1]["key"]))
        state["slots"][index]["context"] = None
        reference = fixture.records._retain_child(self.native.OWNER.RESERVATIONS.canonical(state),
            max_bytes=self.native.OWNER.RECORDS.CHILD_LIMIT)
        changed = fixture.read()
        document = json.loads(changed["raw"]); document["task_state"] = reference
        changed["raw"] = json.dumps(document); fixture.write(changed)
        with self.assertRaises(cold.entity_runner.RunnerFailure) as missing:
            cold.run(component, selections[1])
        self.assertEqual(missing.exception.code, "preflight-admission-not-retained")
        self.assertEqual(len(launched), 2)
        fixture.write(original)
        # A failed native admission callback is positively before RunTask.
        self.assertEqual(cold.run(component, selections[2])["status"], "succeeded")
        with patch.object(cold.entity_runner.PREFLIGHT, "retain_admission",
                side_effect=cold.entity_runner.PREFLIGHT.PreflightFailure("preflight-admission-unavailable")):
            with self.assertRaises(cold.entity_runner.RunnerFailure) as denied:
                cold.run(component, selections[3])
        self.assertEqual(denied.exception.code, "preflight-admission-unavailable")
        state = fixture.records.observe_task_state(fixture.adapter._task_selections)
        slot = next(slot for row, slot in zip(state["selections"], state["slots"], strict=True)
            if (row["component"], row["step"]) == (component, selections[3]["key"]))
        self.assertEqual(slot["admission"], "not-submitted")
        self.assertEqual(len(launched), 3)
        self.assertEqual(consumer().reconcile(), {"status": "ready"})

    def test_complete_entity_baseline_crosses_activation_and_cold_final_read_never_replays(self):
        fixture, tasks, consumer, selections, launched = self.entity_fixture()
        component = "entity-smoke"
        activated = False
        for row in selections:
            if row["activation"] == "after-activation" and not activated:
                stack = dict(fixture.plan["stack_names"])[component]
                parameters = {"stack": stack, "template_reference": dict(fixture.plan["stack_templates"])[stack]}
                fixture.adapter.prepare("activation", **parameters)
                fixture.adapter.execute("activation", **parameters)
                activated = True
            with self.subTest(operation=row["operation"], phase=row["phase"]):
                result = tasks.run(component, row)
                self.assertEqual(result["status"], "skipped" if row["condition"] != "always" else "succeeded")
        self.assertTrue(activated)
        self.assertEqual(len(launched), sum(row["condition"] == "always" for row in selections))
        self.assertEqual(consumer().run(component, selections[-1]), {"status": "succeeded", "reused": True})
        self.assertEqual(len(launched), 16)
        self.assertEqual(consumer().reconcile(), {"status": "ready"})

    def test_ordered_native_tasks_retain_actual_receipts_and_cold_replay_never_resubmits(self):
        fixture = self.fixture()
        fixture.task_identities(native=True)
        fixture.create_graph()
        original_provider = fixture.adapter._provider
        def provider(service, operation, **arguments):
            if (service, operation) == ("secretsmanager", "describe-secret"):
                identity = arguments["SecretId"]
                return {"ARN": identity, "Name": identity.split(":secret:", 1)[1].rsplit("-", 1)[0]}
            return original_provider(service, operation, **arguments)
        fixture.adapter._provider = provider
        component = "core-server-persistence"
        selections = dict(fixture.plan["task_selections"])[component]["steps"]
        launched = []
        def aws(service, operation, *arguments):
            def value(flag):
                return arguments[arguments.index(flag) + 1]
            if (service, operation) == ("ecs", "describe-task-definition"):
                return True, fixture.provider(service, operation, taskDefinition=value("--task-definition"), include=["TAGS"]), "ok"
            if (service, operation) == ("ecs", "run-task"):
                overrides = json.loads(value("--overrides"))
                container = overrides["containerOverrides"][0]
                arn = value("--cluster").replace(":cluster/", ":task/") + "/" + f"{len(launched)+1:032x}"
                task = {"taskArn": arn, "taskDefinitionArn": value("--task-definition"),
                    "startedBy": value("--started-by"), "overrides": overrides, "lastStatus": "STOPPED",
                    "startedAt": "2026-11-27T00:00:00Z", "stoppedAt": "2026-11-27T00:00:01Z",
                    "containers": [{"name": container["name"], "exitCode": 0}]}
                # The real record owner must already have adopted exact admission.
                state = fixture.records.observe_task_state(fixture.adapter._task_selections)
                self.assertEqual(sum(slot is not None and slot["admission"] == "admitted" for slot in state["slots"]), len(launched)+1)
                self.assertEqual(value("--client-token"), task["startedBy"])
                launched.append(task)
                return True, {"tasks": [deepcopy(task)]}, "ok"
            if (service, operation) == ("ecs", "describe-tasks"):
                return True, {"tasks": [deepcopy(task) for task in launched if task["taskArn"] == value("--tasks")]}, "ok"
            if (service, operation) == ("logs", "get-log-events"):
                task = next(task for task in launched if task["taskArn"].endswith(value("--log-stream-name").rsplit("/", 1)[1]))
                mode = task["overrides"]["containerOverrides"][0]["environment"][0]["value"]
                proof = next(row["proof"] for row in selections if row["proof"]["operation"] == mode)
                return True, {"events": [{"message": json.dumps({"verdict": "accepted", "code": proof["result_code"]})}]}, "ok"
            self.fail(f"Unexpected fixture operation: {service} {operation}")
        def consumer():
            return ASSEMBLY.NativeTasks(root=HERE.parents[5], plan=fixture.plan, operations=fixture.adapter,
                owner=self.native.OWNER, aws=aws)
        tasks = consumer()
        for row in selections:
            with self.subTest(step=row["id"]):
                self.assertEqual(tasks.run(component, row)["status"], "succeeded", tasks.last_result)
        self.assertEqual(len(launched), len(selections))
        self.assertEqual(consumer().reconcile(), {"status": "ready"})
        for row in selections:
            self.assertEqual(consumer().run(component, row)["status"], "succeeded")
        self.assertEqual(len(launched), len(selections))

    def test_interrupted_unallocated_session_completes_and_cold_worker_reuses_record(self):
        native = self.native
        fixture = native.SessionHandoffTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.initialize()

        class EmptyTasks:
            def run(self, *_):
                raise AssertionError("Cleanup must not launch a task")
            def reconcile(self):
                state = fixture.records.observe_task_state(fixture.adapter._task_selections)
                if any(slot is not None for slot in state["slots"]):
                    raise AssertionError("This fixture admits no native tasks")
                return {"status": "ready"}
            def report_context(self):
                return {}
            def failure_code(self, _failure):
                return "environment-session-controller-operation-failed"

        def assembly():
            return ASSEMBLY.SessionAssembly(plan=fixture.plan, operations=fixture.make_adapter(fixture.plan,
                fixture.make_records(), provider=fixture.provider, preflight=fixture.preflight), owner=native.OWNER,
                tasks=EmptyTasks(), choices=fixture.choices, publications=fixture.publications)

        result = CONTROLLER.Controller(assembly()).advance("cleanup")
        self.assertEqual(result["functional"], {"status": "interrupted"})
        self.assertEqual(result["cleanup"]["status"], "completed", result)
        document = fixture.records.observe_existing()["document"]
        self.assertEqual(document["functional_result"], {"status": "interrupted"})
        self.assertEqual(document["cleanup_completion"], result["cleanup"]["reference"])
        history = deepcopy(fixture.read()["history"])
        fixture.now = 8200
        cold = CONTROLLER.Controller(assembly()).advance("cleanup")
        self.assertEqual(cold["cleanup"]["status"], "completed", cold)
        self.assertEqual(fixture.read()["history"], history)
        self.assertFalse(fixture.read()["submissions"])
        with self.assertRaises(native.OWNER.RECORDS.SessionRecordFailure) as conflict:
            fixture.records.retain_functional({"status": "succeeded"})
        self.assertEqual(conflict.exception.code, "session-functional-result-conflict")


if __name__ == "__main__":
    unittest.main()
