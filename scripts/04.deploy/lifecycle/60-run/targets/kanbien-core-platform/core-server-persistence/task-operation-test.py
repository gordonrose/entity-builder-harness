#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-persistence.task-operations
#   version: 2
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.core-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual migration and administration callers through durable single-submission, reconciliation and explicit successor transitions using simulated providers.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.private-persistence-verifier-isolation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/smoke-test.sh
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

BASE = Path(__file__).parent
CANARY = "TASK_PROVIDER_CREDENTIAL_CANARY"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class Fixture:
    def __init__(self, kind):
        self.kind = kind
        self.temp = tempfile.TemporaryDirectory(prefix="baseline-reserved-task-")
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        self.control = load("actual_" + kind, BASE / ("run-" + kind) / "script.py")
        self.migration = self.control if kind == "migration" else self.control.MIGRATION
        # These task protocol fixtures isolate the cost owner; its trusted
        # projection/lock is covered by the scheduling controller fixtures.
        operations = self.migration.task_operations()
        operations.reserve_task_cost = lambda request, reserve, **_options: reserve()
        self.migration.task_operations = lambda: operations
        self.receipts = load("actual_task_receipts", BASE / "proof-receipts.py")
        self.receipts.RECEIPTS = self.root / "receipts"
        self.receipts.EVIDENCE_CLASS = "simulated"
        self.control.ROOT = self.migration.ROOT = self.root
        self.control.deadline = lambda: 5
        self.migration.proof_receipts = lambda: self.receipts
        if kind == "administration": self.control.RECEIPTS = self.receipts
        self.control.aws = self.migration.aws = self.aws
        self.tasks, self.calls = [], []
        self.lost, self.missing, self.running, self.corrupt = False, False, False, False
        self.exit_code, self.revision = 0, 7
        self.task_started_at, self.task_stopped_at = "2026-11-15T00:00:00Z", "2026-11-15T00:00:01Z"
        self.scheduling = None
        self.synthetic_result = None
        self.database_state = {"schema": "kanbien/scheduling-database-state/v1", "manifest_sha256": "a" * 64,
                               "migration_count": 7, "work_inventory": {"waiting_schedules": 0, "pending_outbox": 0, "active_processing": 0}}
        self.migration_prefix = {"schema": "kanbien/scheduling-migration-prefix/v1", "manifest_sha256": "a" * 64,
            "manifest_migration_count": 7, "minimum_applied_migrations": 2, "applied_migrations": 2,
            "applied_prefix_sha256": "b" * 64, "state": "partial"}
        def outputs(_stack):
            return {"CoreServerPersistenceMigrationTaskDefinitionArn": self.definition,
                    "CoreServerPersistenceAdministrationTaskDefinitionArn": f"arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:{self.revision}",
                    "PersistenceMigrationSecurityGroupId": "sg-migration", "PersistenceAdministrationSecurityGroupId": "sg-administrator",
                    "PersistenceDatabaseIdentifier": "fixed-database", "PersistenceDatabaseEndpoint": "fixed.database.internal",
                    "PrivateSubnetIds": "subnet-private"}, "ok"
        self.migration.outputs = outputs
        self.control.outputs = outputs

    @property
    def definition(self):
        return f"arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-{self.kind}:{self.revision}"

    def state_path(self, operation):
        return self.root / ".git" / ("persistence-" + self.kind) / (operation + ".json")

    def aws(self, *arguments):
        self.calls.append(arguments)
        operation = arguments[1]
        def value(flag): return arguments[arguments.index(flag) + 1]
        if operation == "run-task":
            overrides = json.loads(value("--overrides"))
            mode = overrides["containerOverrides"][0]["environment"][0]["value"]
            journal = json.loads(self.state_path(mode).read_text())
            assert journal["operation_id"] == value("--started-by") == value("--client-token")
            assert self.state_path(mode).with_suffix(".lock").read_bytes(), "durable sentinel before launch"
            task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + f"{len(self.tasks)+1:032x}",
                    "taskDefinitionArn": value("--task-definition"), "startedBy": value("--started-by"), "overrides": overrides,
                    "lastStatus": "PENDING", "startedAt": self.task_started_at, "stoppedAt": self.task_stopped_at,
                    "containers": [{"name": "persistence-" + self.kind, "exitCode": self.exit_code}]}
            self.tasks.append(task)
            return (False, None, "aws-response-invalid") if self.lost else (True, {"tasks": [copy.deepcopy(task)]}, "ok")
        if operation == "list-tasks":
            return True, {"taskArns": [] if self.missing or value("--desired-status") != ("RUNNING" if self.running else "STOPPED") else [task["taskArn"] for task in self.tasks]}, "ok"
        if operation == "describe-tasks":
            wanted = arguments[arguments.index("--tasks")+1:]
            tasks = [] if self.missing else [dict(copy.deepcopy(task), lastStatus="RUNNING" if self.running else "STOPPED") for task in self.tasks if task["taskArn"] in wanted]
            if self.corrupt and tasks: tasks[0]["overrides"] = {"containerOverrides": []}
            if self.scheduling is not None and self.scheduling["observer"]["taskArn"] in wanted:
                tasks.append(copy.deepcopy(self.scheduling["observer"]))
            return True, {"tasks": tasks}, "ok"
        if operation == "describe-task-definition":
            if self.scheduling is not None:
                return True, {"taskDefinition": copy.deepcopy(self.scheduling["definitions"][value("--task-definition")])}, "ok"
            return True, {"taskDefinition": {"containerDefinitions": [{"image": "fixture/image@sha256:" + "a"*64}]}}, "ok"
        if operation == "get-log-events":
            task_id = value("--log-stream-name").rsplit("/", 1)[1]
            if self.scheduling is not None and self.scheduling["observer"]["taskArn"].endswith(task_id):
                return True, {"events": [{"message": json.dumps(self.scheduling["result"])}]}, "ok"
            task = next(task for task in self.tasks if task["taskArn"].endswith(task_id))
            mode = task["overrides"]["containerOverrides"][0]["environment"][0]["value"]
            code = self.control.SUCCESS[mode]
            if not isinstance(code, str): code = code[-1]
            result = {"verdict": "accepted", "code": code}
            if mode in self.receipts.SCHEDULING_STATE.RESULTS: result["database_state"] = self.database_state
            if mode == self.receipts.SCHEDULING_STATE.PREFIX_OPERATION: result["migration_prefix"] = self.migration_prefix
            if mode in self.receipts.SCHEDULING_PROOF.PROOF_OPERATIONS:
                result.update(self.synthetic_result)
            return True, {"events": [{"message": json.dumps(result)}]}, "ok"
        if self.scheduling is not None and operation == "describe-stacks":
            return True, {"Stacks": [{"StackStatus": "UPDATE_COMPLETE", "Parameters": [{"ParameterKey": key, "ParameterValue": item} for key, item in self.scheduling["parameters"].items()]}]}, "ok"
        if self.scheduling is not None and operation == "get-template":
            return True, {"TemplateBody": self.scheduling["template"]}, "ok"
        if self.scheduling is not None and operation == "describe-db-instances":
            return True, {"DBInstances": [copy.deepcopy(self.scheduling["database"])]}, "ok"
        raise AssertionError(("unmocked provider operation", arguments))

    def invoke(self, operation=None, *extra):
        mode = operation or ("apply" if self.kind == "migration" else "revoke-runtime")
        if self.kind == "administration" and (mode in self.receipts.SCHEDULING_STATE.RESULTS or mode == self.receipts.SCHEDULING_STATE.PREFIX_OPERATION or mode in self.receipts.SCHEDULING_PROOF.PROOF_OPERATIONS):
            if self.scheduling is None: self.scheduling_receipt(retain=False)
            extra = (*extra, "--qualified-receipt", str(self.root / "qualified.json"))
        flag = "--migration-operation" if self.kind == "migration" else "--operation"
        output, error = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["actual-controller", flag, mode, "--json", *extra]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = self.control.main()
        result = json.loads(output.getvalue())
        assert CANARY not in output.getvalue() + error.getvalue()
        assert (status == 0) == (result["verdict"] == "accepted")
        return result

    def launches(self): return sum(call[1] == "run-task" for call in self.calls)
    def close(self): self.temp.cleanup()

    def scheduling_receipt(self, *, complete=False, age=1, retain=True):
        """Only package authentication is injected; task/DB admission is actual."""
        qualified = {"source_revision": "b" * 40, "image_digest": "sha256:" + "a" * 64}
        self.authentication_calls = 0
        def authenticated(_path):
            self.authentication_calls += 1
            return qualified
        self.receipts.qualified_maintenance = authenticated
        observed_at = (datetime.now(timezone.utc) - timedelta(seconds=age)).isoformat()
        definition = f"arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:{self.revision}"
        observer = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "f" * 32,
            "taskDefinitionArn": definition, "lastStatus": "STOPPED", "startedAt": observed_at, "stoppedAt": observed_at,
            "containers": [{"name": "persistence-administration", "exitCode": 0}],
            "overrides": {"containerOverrides": [{"name": "persistence-administration", "environment": [{"name": "PERSISTENCE_ADMINISTRATION_OPERATION", "value": "observe-scheduling-prefix"}]}]}}
        prefix = {**self.migration_prefix, **({"state": "complete", "applied_migrations": 7, "applied_prefix_sha256": "a" * 64} if complete else {})}
        if retain:
            receipt = self.receipts.make(proof_type="administration", operation="observe-scheduling-prefix", task=observer,
                image_digest=qualified["image_digest"], result_code="PERSISTENCE_SCHEDULING_PREFIX_CONFIRMED",
                context={"completion_deadline_seconds": 5, "completion_duration_seconds": 0, "migration_prefix": prefix,
                         "scheduling_binding": {**qualified, "dependency_incarnation_sha256": self.receipts.digest({"resource_id": "db-FIXED", "database": "kanbienpersistence", "schema": "platform"})}},
                controller="run-administration", collected_at=observed_at)
            receipt["provenance"]["evidence_class"] = "live"
            receipt["integrity"]["payload_sha256"] = self.receipts.digest({key: item for key, item in receipt.items() if key != "integrity"})
            path = self.receipts.persist(receipt)
        template_path = Path("infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml")
        raw = (self.receipts.ROOT / template_path).read_text()
        target = self.root / template_path
        target.parent.mkdir(parents=True, exist_ok=True); target.write_text(raw)
        parameters = {"SourceRevision": qualified["source_revision"], "SupportImageDigest": qualified["image_digest"], "ImageRepositoryUri": "fixture/image"}
        database = {"DBInstanceIdentifier": "fixed-database", "DBInstanceStatus": "available", "DBName": "kanbienpersistence",
            "Endpoint": {"Address": "fixed.database.internal"}, "IAMDatabaseAuthenticationEnabled": True, "DbiResourceId": "db-FIXED"}
        definitions = {}
        for arn, username in ((self.definition, "core_schema_migration"), (definition, "core_runtime")):
            environment = {"PERSISTENCE_POSTGRES_HOST": database["Endpoint"]["Address"], "PERSISTENCE_POSTGRES_DATABASE": "kanbienpersistence",
                "PERSISTENCE_POSTGRES_SCHEMA": "platform", "PERSISTENCE_POSTGRES_IAM_REGION": "eu-west-1",
                "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE": "arn:aws:rds-db:eu-west-1:337159794548:dbuser:db-FIXED/" + username}
            definitions[arn] = {"taskDefinitionArn": arn, "containerDefinitions": [{"image": "fixture/image@" + qualified["image_digest"],
                "environment": [{"name": key, "value": item} for key, item in environment.items()]}]}
        self.scheduling = {"observer": observer, "result": {"verdict": "accepted", "code": "PERSISTENCE_SCHEDULING_PREFIX_CONFIRMED", "migration_prefix": prefix},
            "parameters": parameters, "database": database, "definitions": definitions, "template": raw}
        if retain: return ("--migration-profile", "scheduling", "--qualified-receipt", str(self.root / "qualified.json"), "--migration-state-receipt", str(path))

    def replay_receipt(self, *, index=100, result="PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED", started="2026-11-15T00:00:02Z", digest=None, definition=None, evidence_class=None, duration=1):
        task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + f"{index:032x}",
                "taskDefinitionArn": definition or f"arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:{self.revision}",
                "lastStatus": "STOPPED", "startedAt": started, "stoppedAt": "2026-11-15T00:00:03Z", "containers": [{"exitCode": 0}]}
        value = self.receipts.make(proof_type="administration", operation="observe-migration-state", task=task,
            image_digest=digest or "sha256:" + "a"*64, result_code=result,
            context={"completion_deadline_seconds": 5, "completion_duration_seconds": duration}, controller="run-administration", collected_at="2026-11-15T00:00:04Z")
        if evidence_class is not None:
            value["provenance"]["evidence_class"] = evidence_class
            value["integrity"]["payload_sha256"] = self.receipts.digest({key: item for key, item in value.items() if key != "integrity"})
        return self.receipts.persist(value)


class TaskOperationTests(unittest.TestCase):
    def test_synthetic_seed_preserves_original_selection_after_lost_submission(self):
        fixture = Fixture("administration"); self.addCleanup(fixture.close)
        identity, due = "8c65621e-6003-4b00-a742-576055e26c1b", "2026-11-15T00:05:00.000Z"
        seed = {"schema": "kanbien/scheduling-proof-seed/v1", "schedule_id": identity,
                "job_name": fixture.receipts.SCHEDULING_PROOF.PROOF_JOBS["core-server-persistence"], "due_at": due, "disposition": "created"}
        fixture.synthetic_result = {"scheduling_seed": seed}
        arguments = ("--scheduling-proof-id", identity, "--scheduling-proof-due-at", due)
        fixture.lost = True
        self.assertEqual(fixture.invoke("seed-scheduling-proof", *arguments)["verdict"], "uncertain")
        reserved = json.loads(fixture.state_path("seed-scheduling-proof").read_text())
        original_binding = reserved["request"]["scheduling_binding"]
        fixture.scheduling["database"]["DbiResourceId"] = "db-CHANGED-AFTER-SUBMISSION"
        second = fixture.invoke("seed-scheduling-proof", *arguments)
        self.assertEqual(second["verdict"], "accepted", second)
        self.assertEqual(fixture.launches(), 1)
        receipt = fixture.receipts.validate(json.loads((fixture.root / second["facts"]["proof_receipt"]).read_text()))
        self.assertEqual(receipt["context"]["scheduling_seed"], seed)
        self.assertEqual(receipt["context"]["scheduling_binding"], original_binding)
        self.assertEqual(fixture.authentication_calls, 1, "reconciliation does not invent a new original identity")
        self.assertEqual(fixture.invoke("seed-scheduling-proof", "--scheduling-proof-id", identity,
            "--scheduling-proof-due-at", "2026-11-15T00:06:00.000Z")["verdict"], "blocked")
        self.assertEqual(fixture.launches(), 1)

    def test_synthetic_observation_binds_exact_original_id_and_task_time(self):
        fixture = Fixture("administration"); self.addCleanup(fixture.close)
        identity = "8c65621e-6003-4b00-a742-576055e26c1b"
        observed = {"schema": "kanbien/scheduling-proof-observation/v1", "selection": {"kind": "schedule", "id": identity},
            "observed_at": "2026-11-15T00:00:00.500Z", "schedule": None, "outbox": None, "processing": None,
            "application": {"kind": "acceptance", "present": False}, "delivery_message": None}
        fixture.synthetic_result = {"scheduling_observation": observed}
        result = fixture.invoke("observe-scheduling-proof", "--scheduling-proof-id", identity)
        self.assertEqual(result["verdict"], "accepted", result)
        original = json.loads((fixture.root / result["facts"]["proof_receipt"]).read_text())
        self.assertEqual(original["context"]["scheduling_observation"], observed)
        state = json.loads(fixture.state_path("observe-scheduling-proof").read_text())
        second = fixture.invoke("observe-scheduling-proof", "--scheduling-proof-id", identity,
            "--new-operation", "--expected-operation", state["operation_id"])
        self.assertEqual(second["verdict"], "accepted", second)
        self.assertEqual(fixture.launches(), 2)
        checked = fixture.control.observe_scheduling_proof_receipt(fixture.root / result["facts"]["proof_receipt"],
            qualified_path=fixture.root / "qualified.json", required_after="2026-11-15T00:00:00Z",
            source_revision="b" * 40, image_digest="sha256:" + "a" * 64)
        self.assertEqual(checked["packet"]["journal"]["operation_id"], state["operation_id"], "read the immutable original history after another snapshot")
        self.assertEqual(checked["packet"]["receipt"], original)
        self.assertEqual(fixture.launches(), 2)
        self.assertEqual(fixture.control.reobserve_scheduling_proof_packet(checked["packet"], qualified_path="qualified.json",
            expected_binding=checked["binding"], required_after="2026-11-15T00:00:00Z"), checked)
        for path in ("../qualified.json", str(fixture.root / "qualified.json")):
            with self.assertRaisesRegex(fixture.receipts.ReceiptError, "persistence-scheduling-proof-not-confirmed"):
                fixture.control.reobserve_scheduling_proof_packet(checked["packet"], qualified_path=path,
                    expected_binding=checked["binding"], required_after="2026-11-15T00:00:00Z")
        self.assertEqual(fixture.launches(), 2, "live packet authentication cannot submit a task")
        with patch.object(fixture.migration, "aws", side_effect=AssertionError("historical archive cannot use AWS")):
            self.assertEqual(fixture.control.validate_scheduling_proof_packet(checked["packet"], expected_binding=checked["binding"],
                required_after="2026-11-15T00:00:00Z"), checked)
            changed = copy.deepcopy(checked["packet"])
            changed["journal"]["request"]["scheduling_binding"]["dependency_incarnation_sha256"] = "sha256:" + "d" * 64
            changed["journal"]["integrity"] = fixture.receipts.digest({key: item for key, item in changed["journal"].items() if key != "integrity"}).removeprefix("sha256:")
            with self.assertRaisesRegex(fixture.receipts.ReceiptError, "persistence-scheduling-proof-packet-invalid"):
                fixture.control.validate_scheduling_proof_packet(changed, expected_binding=checked["binding"], required_after="2026-11-15T00:00:00Z")
        for patcher in (
            lambda value: value["selection"].update(id="4e09f131-9956-43e1-b5dc-dc482c459cac"),
            lambda value: value.update(observed_at="2026-11-15T01:00:00.000Z"),
            lambda value: value["application"].update(private_value=CANARY),
        ):
            changed = copy.deepcopy(observed); patcher(changed)
            fixture.synthetic_result = {"scheduling_observation": changed}
            task = dict(fixture.tasks[-1], lastStatus="STOPPED")
            self.assertIsNone(fixture.control.accepted_log(task, "observe-scheduling-proof")[0])

    def test_cost_admission_precedes_reservation_and_unknown_original_only_reconciles(self):
        for fixture in self.fixtures():
            operations = fixture.migration.task_operations()
            calls = []
            def refused(request, reserve, **options):
                calls.append(options)
                raise operations.OperationFailure("task-cost-admission-not-confirmed")
            operations.reserve_task_cost = refused
            blocked = fixture.invoke()
            self.assertEqual(blocked["verdict"], "blocked")
            self.assertEqual(fixture.launches(), 0)
            mode = "apply" if fixture.kind == "migration" else "revoke-runtime"
            self.assertFalse(fixture.state_path(mode).exists())
            operations.reserve_task_cost = lambda request, reserve, **options: reserve()
            fixture.lost = True
            self.assertEqual(fixture.invoke()["verdict"], "uncertain")
            operations.reserve_task_cost = refused
            self.assertEqual(fixture.invoke()["verdict"], "accepted")
            self.assertEqual(fixture.launches(), 1)
            self.assertEqual(len(calls), 1, "unknown originals reconcile even if new costs cannot be admitted")

    def test_native_cost_adapter_preserves_callback_error_and_sanitizes_owner_failure(self):
        operations = load("native_cost_adapter_fixture", BASE / "task-operations.py")
        request = {"task_definition": "fixed-definition"}
        calls = []
        class Owner:
            @staticmethod
            def reserve_cost_admission(**values):
                calls.append(values)
                return values["reserve"]()
        sentinel = ValueError(CANARY)
        def reserve(): raise sentinel
        with patch.object(operations, "module", return_value=Owner):
            with self.assertRaises(ValueError) as failure:
                operations.reserve_task_cost(request, reserve, required=True)
            self.assertIs(failure.exception, sentinel)
        self.assertTrue(calls[0]["required"])
        self.assertEqual((calls[0]["target"], calls[0]["scope"], calls[0]["task_definition_arn"]),
            ("kanbien-core-platform", "core-server-persistence", "fixed-definition"))
        with patch.object(Owner, "reserve_cost_admission", side_effect=ValueError(CANARY)), patch.object(operations, "module", return_value=Owner):
            with self.assertRaisesRegex(operations.OperationFailure, "^task-cost-admission-not-confirmed$"):
                operations.reserve_task_cost(request, lambda: self.fail("cannot reserve after refusal"))

    def test_native_reservation_census_preserves_unknowns_and_rejects_invalid_history(self):
        for fixture in self.fixtures():
            first = fixture.invoke()
            self.assertEqual(first["verdict"], "accepted")
            mode = "apply" if fixture.kind == "migration" else "revoke-runtime"
            original = json.loads(fixture.state_path(mode).read_text())
            binding = fixture.control.operation_binding(None)
            values = binding.reservation_census([original["request"]["task_definition"]])
            self.assertEqual(len(values), 1)
            self.assertIsNone(values[0]["reserved_at"], "legacy records contain no authentic reservation time")
            self.assertEqual(values[0]["operation_id"], original["operation_id"])
            self.assertEqual(values[0]["task_arn"], original["task_arn"])
            journal = fixture.control.task_operations().JOURNAL if fixture.kind == "migration" else fixture.control.MIGRATION.task_operations().JOURNAL
            self.assertEqual(values[0]["request_sha256"], hashlib.sha256(journal.canonical(original["request"])).hexdigest())
            history = fixture.state_path(mode).parent / "history"
            history.mkdir(mode=0o700, exist_ok=True)
            retained = history / (original["operation_id"] + ".json")
            journal.save(retained, original)
            self.assertEqual(binding.reservation_census([original["request"]["task_definition"]]), values)
            bad = copy.deepcopy(original); bad["task_arn"] = None
            journal.save(retained, bad)
            with self.assertRaisesRegex(Exception, "reservation-census-not-confirmed"):
                binding.reservation_census([original["request"]["task_definition"]])

    def test_scheduling_admits_one_actual_migration_and_reconciles_original_admission(self):
        fixture = Fixture("migration"); self.addCleanup(fixture.close)
        arguments = fixture.scheduling_receipt()
        fixture.lost = True
        first = fixture.invoke(None, *arguments)
        self.assertEqual(first["verdict"], "uncertain", first)
        self.assertEqual(fixture.authentication_calls, 1)
        fixture.scheduling["database"]["DbiResourceId"] = "db-CHANGED"
        second = fixture.invoke(None, *arguments)
        self.assertEqual(second["verdict"], "accepted", second)
        self.assertEqual(fixture.authentication_calls, 1)
        self.assertEqual(fixture.launches(), 1)
        retained = json.loads(fixture.state_path("apply").read_text())
        self.assertIsNotNone(retained["request"]["admission"])
        proof = fixture.receipts.validate(json.loads((fixture.root / second["facts"]["proof_receipt"]).read_text()))
        self.assertEqual(proof["context"]["prefix_receipt_sha256"], "sha256:" + retained["request"]["admission"]["sha256"])
        self.assertEqual(proof["context"]["scheduling_binding"], {
            "source_revision": "b" * 40, "image_digest": "sha256:" + "a" * 64,
            "dependency_incarnation_sha256": fixture.receipts.digest({"resource_id": "db-FIXED", "database": "kanbienpersistence", "schema": "platform"})})
        self.assertEqual(fixture.invoke(None, *arguments)["facts"]["evidence_reuse"], "historical-completion")

    def test_scheduling_prefix_is_not_qualified_by_shape_or_checksums_alone(self):
        mutations = (
            lambda value: value["database"].update(DbiResourceId="db-REPLACED"),
            lambda value: value["parameters"].update(SourceRevision="c" * 40),
            lambda value: value["observer"].update(lastStatus="RUNNING"),
            lambda value: value["result"]["migration_prefix"].update(manifest_sha256="c" * 64),
            lambda value: value.update(template="Resources: {}"),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                fixture = Fixture("migration"); self.addCleanup(fixture.close)
                arguments = fixture.scheduling_receipt(); mutate(fixture.scheduling)
                result = fixture.invoke(None, *arguments)
                self.assertEqual(result["findings"], [{"code": "persistence-migration-scheduling-admission-invalid"}], result)
                self.assertEqual(fixture.launches(), 0)
                self.assertFalse(fixture.state_path("apply").exists())
        fixture = Fixture("migration"); self.addCleanup(fixture.close)
        self.assertEqual(fixture.invoke(None, *fixture.scheduling_receipt(age=901))["verdict"], "blocked")
        self.assertEqual(fixture.authentication_calls, 0)

    def test_complete_scheduling_prefix_submits_nothing_and_failed_apply_cannot_replay(self):
        fixture = Fixture("migration"); self.addCleanup(fixture.close)
        arguments = fixture.scheduling_receipt(complete=True)
        result = fixture.invoke(None, *arguments)
        self.assertEqual(result["verdict"], "accepted", result)
        self.assertIs(result["facts"]["migration_submitted"], False)
        self.assertFalse(fixture.state_path("apply").exists())
        self.assertEqual(fixture.launches(), 0)
        failed = Fixture("migration"); self.addCleanup(failed.close)
        arguments = failed.scheduling_receipt(); failed.exit_code = 1
        result = failed.invoke(None, *arguments)
        self.assertEqual(result["verdict"], "failed", result)
        operation = json.loads(failed.state_path("apply").read_text())["operation_id"]
        result = failed.invoke(None, *arguments, "--new-operation", "--expected-operation", operation)
        self.assertEqual(result["findings"], [{"code": "persistence-migration-scheduling-successor-prefix-required"}], result)
        self.assertEqual(failed.launches(), 1)

    def test_migration_profile_is_closed_before_any_provider_call(self):
        fixture = Fixture("migration"); self.addCleanup(fixture.close)
        for extra in [("--migration-profile", "scheduling"),
                      ("--migration-profile", "scheduling", "--new-operation", "--expected-operation", "none", "--migration-state-receipt", "/missing-legacy-observer.json")]:
            result = fixture.invoke(None, *extra)
            self.assertEqual(result["findings"], [{"code": "persistence-migration-scheduling-prefix-observation-required"}])
            self.assertEqual(fixture.calls, [])
        result = fixture.invoke(None, "--migration-profile", CANARY)
        self.assertEqual(result["findings"], [{"code": "persistence-migration-profile-invalid"}])
        self.assertEqual(fixture.calls, [])
        output = io.StringIO()
        with patch.object(sys, "argv", ["controller", "--migration-profile", "scheduling", "--validate-arguments"]), contextlib.redirect_stdout(output):
            self.assertEqual(fixture.control.main(), 0)
        self.assertEqual(json.loads(output.getvalue())["verdict"], "valid")
        self.assertEqual(fixture.calls, [])

    def test_migration_profile_exact_request_receipt_and_reconciliation(self):
        fixture = Fixture("migration"); self.addCleanup(fixture.close)
        control = fixture.control
        self.assertEqual(control.migration_environment("apply"), {"PERSISTENCE_MIGRATION_OPERATION": "apply"})
        environment = control.migration_environment("apply", "scheduling")
        self.assertEqual(environment, {"PERSISTENCE_MIGRATION_OPERATION": "apply", "PERSISTENCE_MIGRATION_PROFILE": "scheduling"})
        operations = control.task_operations()
        binding = operations.BoundOperation(root=fixture.root, proof_type="migration", family="kanbien-core-platform-persistence-migration",
            container="persistence-migration", selector="PERSISTENCE_MIGRATION_OPERATION", results=control.SUCCESS,
            aws=fixture.aws, report=control.report, accept=lambda task, seconds, mode, on_receipt=None: control.accepted_completion(task, seconds, mode, on_receipt, "scheduling"), receipts=fixture.receipts)
        overrides = {"containerOverrides": [{"name": "persistence-migration", "environment": [{"name": key, "value": value} for key, value in environment.items()]}]}
        def run(selected=overrides):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(io.StringIO()):
                binding.run(mode="apply", definition=fixture.definition, network="private", overrides=json.dumps(selected), seconds=5,
                    authorize_submission=lambda previous, proof: None)
            return json.loads(stream.getvalue())
        fixture.lost = True
        self.assertEqual(run()["verdict"], "uncertain")
        first = run()
        self.assertEqual(first["verdict"], "accepted", first)
        self.assertEqual(fixture.launches(), 1)
        receipt = fixture.receipts.validate(json.loads((fixture.root / first["facts"]["proof_receipt"]).read_text()))
        self.assertEqual(receipt["context"]["migration_profile"], "scheduling")
        self.assertEqual(run()["facts"]["evidence_reuse"], "historical-completion")
        baseline = copy.deepcopy(overrides); baseline["containerOverrides"][0]["environment"].pop()
        self.assertEqual(run(baseline)["verdict"], "blocked")
        state = json.loads(fixture.state_path("apply").read_text())
        self.assertEqual(state["request"]["overrides"], overrides)
        wrong = {**fixture.tasks[0], "overrides": baseline}
        with self.assertRaises(operations.TASKS.TaskFailure): binding.exact(wrong, state)
        self.assertFalse(control.task_operation_bound(wrong, "apply", "scheduling"))
        self.assertFalse(control.task_operation_bound(fixture.tasks[0], "apply", "baseline"))
        for bad in ["baseline", CANARY, None]:
            context = {**receipt["context"], "migration_profile": bad}
            with self.assertRaises(fixture.receipts.ReceiptError): fixture.receipts._context("migration", context, "apply", "PERSISTENCE_MIGRATION_APPLIED")
        with self.assertRaises(fixture.receipts.ReceiptError): fixture.receipts._context("administration", receipt["context"], "revoke-runtime", "PERSISTENCE_RUNTIME_REVOKED")
        self.assertEqual(fixture.launches(), 1)

    def test_scheduling_state_is_retained_without_claiming_freshness(self):
        fixture = Fixture("administration")
        self.addCleanup(fixture.close)
        fixture.task_started_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        fixture.task_stopped_at = datetime.now(timezone.utc).isoformat()
        for operation in fixture.receipts.SCHEDULING_STATE.RESULTS:
            first = fixture.invoke(operation)
            self.assertEqual(first["verdict"], "accepted", first)
            path = fixture.root / first["facts"]["proof_receipt"]
            receipt = fixture.receipts.validate(json.loads(path.read_text()))
            self.assertEqual(receipt["context"]["database_state"], fixture.database_state)
            self.assertEqual(receipt["context"]["scheduling_binding"], {
                "source_revision": "b" * 40, "image_digest": "sha256:" + "a" * 64,
                "dependency_incarnation_sha256": fixture.receipts.digest({"resource_id": "db-FIXED", "database": "kanbienpersistence", "schema": "platform"})})
            captured = fixture.control.observe_scheduling_preparation_receipt(path, qualified_path=fixture.root / "qualified.json",
                required_after=fixture.task_started_at, source_revision="b" * 40, image_digest="sha256:" + "a" * 64)
            self.assertEqual(captured["operation"], operation)
            self.assertEqual(captured["result"], {"database_state": fixture.database_state})
            self.assertIsNone(captured["selection"])
            self.assertEqual(fixture.control.reobserve_scheduling_preparation_packet(captured["packet"], qualified_path="qualified.json",
                expected_binding=captured["binding"], required_after=fixture.task_started_at), captured)
            with patch.object(fixture.control.MIGRATION, "aws", side_effect=AssertionError("historical proof touched provider")):
                self.assertEqual(fixture.control.validate_scheduling_preparation_packet(captured["packet"],
                    expected_binding=captured["binding"], required_after=fixture.task_started_at), captured)
            changed = copy.deepcopy(captured["packet"])
            changed["receipt"]["operation"] = "grant-runtime-application-access"
            with self.assertRaises(fixture.receipts.ReceiptError):
                fixture.control.validate_scheduling_preparation_packet(changed, expected_binding=captured["binding"], required_after=fixture.task_started_at)
            if operation == "observe-scheduling-state":
                observed = fixture.control.observe_scheduling_state_receipt(path, qualified_path=fixture.root / "qualified.json",
                    required_after=fixture.task_started_at, source_revision="b" * 40, image_digest="sha256:" + "a" * 64)
                self.assertEqual(observed["database_state"], fixture.database_state)
                self.assertEqual(observed["packet"]["receipt"], receipt)
                with self.assertRaisesRegex(fixture.receipts.ReceiptError, "persistence-scheduling-proof-not-confirmed"):
                    fixture.control.observe_scheduling_state_receipt(path, qualified_path=fixture.root / "qualified.json",
                        required_after=(datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat(), source_revision="b" * 40, image_digest="sha256:" + "a" * 64)
            again = fixture.invoke(operation)
            self.assertEqual(again["facts"]["evidence_reuse"], "historical-completion")
        self.assertEqual(fixture.launches(), 3)

    def test_scheduling_administration_requires_custody_before_provider_and_keeps_binding_closed(self):
        fixture = Fixture("administration"); self.addCleanup(fixture.close)
        output = io.StringIO()
        with patch.object(sys, "argv", ["controller", "--operation", "observe-scheduling-state", "--json"]), contextlib.redirect_stdout(output):
            self.assertEqual(fixture.control.main(), 1)
        self.assertEqual(json.loads(output.getvalue())["findings"], [{"code": "persistence-administration-scheduling-custody-required"}])
        self.assertEqual(fixture.calls, [])
        result = fixture.invoke("observe-scheduling-state")
        receipt = fixture.receipts.validate(json.loads((fixture.root / result["facts"]["proof_receipt"]).read_text()))
        for mutation in ({"private": CANARY}, {"source_revision": CANARY}, {"dependency_incarnation_sha256": "a" * 64}):
            binding = {**receipt["context"]["scheduling_binding"], **mutation}
            with self.assertRaisesRegex(fixture.receipts.ReceiptError, "scheduling-binding-invalid"):
                fixture.receipts.validate_scheduling_binding(binding)

    def test_initial_readiness_reconciles_real_tasks_and_final_zero_inventory(self):
        fixture = Fixture("administration"); self.addCleanup(fixture.close)
        fixture.receipts.EVIDENCE_CLASS = "live"  # Controlled provider only, not live evidence.
        fixture.scheduling_receipt(retain=False)
        now, paths = datetime.now(timezone.utc), {}
        for index, (name, operation) in enumerate((("state", "observe-scheduling-state"), ("grant", "grant-scheduling-access"), ("prove", "prove-scheduling-access"))):
            fixture.task_started_at = fixture.task_stopped_at = (now - timedelta(seconds=20-index)).isoformat()
            result = fixture.invoke(operation)
            self.assertEqual(result["verdict"], "accepted", result)
            paths[name] = fixture.root / result["facts"]["proof_receipt"]
        arguments = {"required_after": (now - timedelta(seconds=30)).isoformat(), "source_revision": "b" * 40,
                     "image_digest": "sha256:" + "a" * 64}
        def read(**changes):
            return fixture.control.scheduling_database_readiness(fixture.root / "qualified.json", paths, **{**arguments, **changes})
        observed = read()
        self.assertEqual(observed["scope"], "core-server-persistence")
        self.assertEqual(observed["work_inventory"], {"waiting_schedules": 0, "pending_outbox": 0, "active_processing": 0})
        self.assertEqual(set(observed["proofs"]), set(paths))
        self.assertEqual(observed["proofs"]["prove"]["receipt_sha256"], "sha256:" + fixture.control.hashlib.sha256(paths["prove"].read_bytes()).hexdigest())
        for changes in ({"source_revision": "c" * 40}, {"required_after": now.isoformat()}):
            with self.assertRaisesRegex(fixture.receipts.ReceiptError, "readiness-not-confirmed"): read(**changes)
        fixture.scheduling["database"]["DbiResourceId"] = "db-REPLACED"
        with self.assertRaisesRegex(fixture.receipts.ReceiptError, "readiness-not-confirmed"): read()
        fixture.scheduling["database"]["DbiResourceId"] = "db-FIXED"
        original = paths["prove"].read_bytes()
        altered = json.loads(original)
        altered["context"]["database_state"]["work_inventory"]["pending_outbox"] = 1
        altered["integrity"]["payload_sha256"] = fixture.receipts.digest({key: item for key, item in altered.items() if key != "integrity"})
        paths["prove"].write_bytes(fixture.receipts.document_bytes(altered))
        # Shape/integrity alone cannot substitute for the actual result.
        with self.assertRaisesRegex(fixture.receipts.ReceiptError, "readiness-not-confirmed"): read()
        native = fixture.aws
        def final_nonzero(*parts):
            if parts[1] == "get-log-events" and parts[parts.index("--log-stream-name")+1].endswith(altered["task"]["arn"].rsplit("/", 1)[1]):
                return True, {"events": [{"message": json.dumps({"verdict": "accepted", "code": "PERSISTENCE_SCHEDULING_PRIVILEGE_PROVEN", "database_state": altered["context"]["database_state"]})}]}, "ok"
            return native(*parts)
        with patch.object(fixture.migration, "aws", side_effect=final_nonzero):
            with self.assertRaisesRegex(fixture.receipts.ReceiptError, "readiness-unrelated-work"): read()
        paths["prove"].write_bytes(original)
        policy = fixture.receipts.owner("readiness_fixture_policy", "scripts/04.deploy/lifecycle/60-run/release-succession/proof-policy.py")
        native_observations = {name: {**proof, "database_state": copy.deepcopy(fixture.database_state)} for name, proof in observed["proofs"].items()}
        binding = {key: observed[key] for key in ("source_revision", "image_digest", "dependency_incarnation_sha256")}
        for change in ("stale", "duplicate", "order", "manifest"):
            values = copy.deepcopy(native_observations)
            checked = (now + timedelta(seconds=901)).isoformat() if change == "stale" else now.isoformat()
            if change == "duplicate": values["prove"]["task_arn"] = values["state"]["task_arn"]
            if change == "order": values["prove"]["started_at"] = values["state"]["started_at"]
            if change == "manifest": values["prove"]["database_state"]["manifest_sha256"] = "c" * 64
            with self.assertRaisesRegex(ValueError, "readiness-invalid"):
                fixture.receipts.SCHEDULING_STATE.initial_readiness(binding, values, target="kanbien-core-platform", scope="core-server-persistence",
                    required_after=arguments["required_after"], checked_at=checked, timestamp=fixture.migration.timestamp,
                    observation_expired=policy.observation_expired)
        self.assertEqual(fixture.launches(), 3, "readiness never submits or retries work")

    def test_scheduling_state_rejects_private_or_incomplete_inventory(self):
        fixture = Fixture("administration")
        self.addCleanup(fixture.close)
        fixture.database_state["work_inventory"]["private"] = CANARY
        first = fixture.invoke("observe-scheduling-state")
        self.assertNotEqual(first["verdict"], "accepted")
        self.assertFalse(list((fixture.root / "receipts").glob("*.json")))
        self.assertEqual(fixture.launches(), 1)
        # A failed observation cannot create another task implicitly.
        fixture.invoke("observe-scheduling-state")
        self.assertEqual(fixture.launches(), 1)

    def test_scheduling_prefix_actual_caller_retains_partial_and_complete_without_replay(self):
        for complete in (False, True):
            fixture = Fixture("administration"); self.addCleanup(fixture.close)
            if complete: fixture.migration_prefix.update(applied_migrations=7, applied_prefix_sha256="a" * 64, state="complete")
            first = fixture.invoke("observe-scheduling-prefix")
            self.assertEqual(first["verdict"], "accepted", first)
            receipt = fixture.receipts.validate(json.loads((fixture.root / first["facts"]["proof_receipt"]).read_text()))
            self.assertEqual(receipt["context"]["migration_prefix"], fixture.migration_prefix)
            self.assertNotIn("database_state", receipt["context"])
            second = fixture.invoke("observe-scheduling-prefix")
            self.assertEqual(second["facts"]["evidence_reuse"], "historical-completion")
            self.assertEqual(fixture.launches(), 1)
            altered = copy.deepcopy(receipt["context"])
            altered["database_state"] = fixture.database_state
            with self.assertRaises(fixture.receipts.ReceiptError):
                fixture.receipts._context("administration", altered, "observe-scheduling-prefix", "PERSISTENCE_SCHEDULING_PREFIX_CONFIRMED")

    def test_scheduling_prefix_invalid_observation_never_creates_success_or_replays(self):
        fixture = Fixture("administration"); self.addCleanup(fixture.close)
        fixture.migration_prefix["minimum_applied_migrations"] = 1
        first = fixture.invoke("observe-scheduling-prefix")
        self.assertNotEqual(first["verdict"], "accepted")
        self.assertFalse(list((fixture.root / "receipts").glob("*.json")))
        self.assertNotEqual(fixture.invoke("observe-scheduling-prefix")["verdict"], "accepted")
        self.assertEqual(fixture.launches(), 1)

    def fixtures(self):
        for kind in ("migration", "administration"):
            fixture = Fixture(kind)
            self.addCleanup(fixture.close)
            yield fixture

    def test_actual_callers_reuse_proof_and_compare_successor(self):
        for fixture in self.fixtures():
            first = fixture.invoke()
            self.assertEqual(first["verdict"], "accepted", first)
            prior = first["facts"]["operation_id"]
            proof = fixture.root / first["facts"]["proof_receipt"]
            original = proof.read_bytes()
            again = fixture.invoke()
            self.assertEqual(again["facts"]["evidence_reuse"], "historical-completion")
            self.assertEqual(proof.read_bytes(), original)
            self.assertEqual(fixture.launches(), 1)
            successor = fixture.invoke(None, "--new-operation", "--expected-operation", prior)
            self.assertEqual(successor["verdict"], "accepted", successor)
            self.assertNotEqual(successor["facts"]["operation_id"], prior)
            fixture.invoke(None, "--new-operation", "--expected-operation", prior)
            self.assertEqual(fixture.launches(), 2)
            rejected = fixture.invoke(None, "--new-operation", "--expected-operation", "kp-" + "f"*32)
            self.assertEqual(rejected["verdict"], "blocked")
            self.assertEqual(fixture.launches(), 2)

    def test_lost_response_missing_observation_and_identity_never_replay(self):
        for fixture in self.fixtures():
            fixture.lost = True
            first = fixture.invoke()
            self.assertEqual(first["verdict"], "uncertain", first)
            fixture.missing = True
            self.assertEqual(fixture.invoke()["verdict"], "uncertain")
            self.assertEqual(fixture.launches(), 1)
            fixture.missing, fixture.corrupt = False, True
            self.assertEqual(fixture.invoke()["verdict"], "uncertain")
            fixture.corrupt = False
            self.assertEqual(fixture.invoke()["verdict"], "accepted")
            self.assertEqual(fixture.launches(), 1)

    def test_pending_missing_metadata_and_changed_request_block_successors(self):
        for fixture in self.fixtures():
            fixture.lost = True
            first = fixture.invoke()
            prior = first["facts"]["operation_id"]
            fixture.revision += 1
            self.assertEqual(fixture.invoke()["verdict"], "blocked")
            self.assertEqual(fixture.invoke(None, "--new-operation", "--expected-operation", prior)["verdict"], "blocked")
            mode = "apply" if fixture.kind == "migration" else "revoke-runtime"
            fixture.state_path(mode).unlink()
            self.assertEqual(fixture.invoke(None, "--new-operation", "--expected-operation", "none")["verdict"], "blocked")
            self.assertEqual(fixture.launches(), 1)

    def test_retention_failure_after_submission_remains_uncertain_and_never_replays(self):
        for kind in ("migration", "administration"):
            for failure_at in (2, 4):
                fixture = Fixture(kind); self.addCleanup(fixture.close)
                factory_owner = fixture.control if kind == "migration" else fixture.control.MIGRATION
                operations = factory_owner.task_operations()
                original_save = operations.JOURNAL.save
                writes = []
                def failing_save(path, value):
                    writes.append(value["operation_id"])
                    if len(writes) == failure_at: raise OSError(CANARY)
                    return original_save(path, value)
                with patch.object(factory_owner, "task_operations", return_value=operations), patch.object(operations.JOURNAL, "save", side_effect=failing_save):
                    observed = fixture.invoke()
                self.assertEqual(observed["verdict"], "uncertain", observed)
                self.assertEqual(observed["facts"]["operation_id"], writes[0])
                self.assertEqual(fixture.launches(), 1)
                reconciled = fixture.invoke()
                self.assertEqual(reconciled["verdict"], "accepted", reconciled)
                self.assertEqual(reconciled["facts"]["operation_id"], writes[0])
                self.assertEqual(fixture.launches(), 1)

    def test_interruption_before_submission_and_lock_contention_never_replay(self):
        import fcntl
        for fixture in self.fixtures():
            factory_owner = fixture.control if fixture.kind == "migration" else fixture.control.MIGRATION
            operations = factory_owner.task_operations()
            with patch.object(factory_owner, "task_operations", return_value=operations), patch.object(operations.TASKS, "submit_task", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt): fixture.invoke()
            self.assertEqual(fixture.launches(), 0)
            observed = fixture.invoke()
            self.assertEqual(observed["verdict"], "uncertain")
            self.assertEqual(fixture.launches(), 0)
            mode = "apply" if fixture.kind == "migration" else "revoke-runtime"
            with fixture.state_path(mode).with_suffix(".lock").open("r+") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.assertEqual(fixture.invoke()["verdict"], "pending")
            self.assertEqual(fixture.launches(), 0)

    def test_argument_and_request_rejection_precedes_submission(self):
        for fixture in self.fixtures():
            invalid = fixture.invoke(None, "--new-operation")
            self.assertEqual(invalid["verdict"], "blocked")
            self.assertEqual(fixture.calls, [])
            if fixture.kind == "administration":
                self.assertEqual(fixture.invoke(None, "--fresh")["verdict"], "blocked")
                self.assertEqual(fixture.calls, [])
            fixture.revision = CANARY
            self.assertEqual(fixture.invoke()["verdict"], "blocked")
            self.assertEqual(fixture.launches(), 0)

    def test_failed_terminal_proof_requires_explicit_successor(self):
        for fixture in self.fixtures():
            fixture.exit_code = 1
            first = fixture.invoke()
            self.assertNotEqual(first["verdict"], "accepted")
            retained = fixture.invoke()
            self.assertEqual(retained["verdict"], "failed", retained)
            self.assertEqual(fixture.launches(), 1)
            fixture.exit_code = 0
            next_attempt = fixture.invoke(None, "--new-operation", "--expected-operation", retained["facts"]["operation_id"])
            if fixture.kind == "migration":
                self.assertEqual(next_attempt["verdict"], "blocked", next_attempt)
                self.assertEqual(fixture.launches(), 1)
                observer = fixture.replay_receipt()
                next_attempt = fixture.invoke(None, "--new-operation", "--expected-operation", retained["facts"]["operation_id"], "--migration-state-receipt", str(observer))
            self.assertEqual(next_attempt["verdict"], "accepted", next_attempt)
            self.assertEqual(fixture.launches(), 2)

    def test_failed_migration_requires_exact_fresh_replay_permission(self):
        fixture = Fixture("migration"); self.addCleanup(fixture.close)
        fixture.exit_code = 1
        fixture.invoke()
        prior = fixture.invoke()["facts"]["operation_id"]
        fixture.exit_code = 0
        invalid = [
            {"result": "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED"},
            {"started": "2026-11-15T00:00:00Z"},
            {"digest": "sha256:" + "b"*64},
            {"definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:8"},
            {"evidence_class": "live"},
            {"duration": 6},
        ]
        for index, changes in enumerate(invalid, 101):
            observer = fixture.replay_receipt(index=index, **changes)
            report = fixture.invoke(None, "--new-operation", "--expected-operation", prior, "--migration-state-receipt", str(observer))
            self.assertEqual(report["verdict"], "blocked", report)
            self.assertEqual(fixture.launches(), 1)
        observer = fixture.replay_receipt(index=107)
        args = ("--new-operation", "--expected-operation", prior, "--migration-state-receipt", str(observer))
        self.assertEqual(fixture.invoke(None, *args)["verdict"], "accepted")
        journal = json.loads(fixture.state_path("apply").read_text())
        self.assertEqual(journal["request"]["admission"]["path"], observer.relative_to(fixture.root).as_posix())
        self.assertEqual(len(journal["request"]["admission"]["sha256"]), 64)
        self.assertEqual(fixture.invoke(None, *args)["verdict"], "accepted")
        self.assertEqual(fixture.launches(), 2)
        self.assertEqual(fixture.invoke(None, "--new-operation", "--expected-operation", prior)["verdict"], "blocked")
        self.assertEqual(fixture.launches(), 2)

    def test_declared_administration_phases_require_fresh_same_mode_successors(self):
        import yaml
        root = BASE.parents[6]
        route = yaml.safe_load((root / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/acceptance-route-contract.yml").read_text())
        resolver = load("actual_acceptance_resolver", root / "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py")
        fixture = Fixture("administration"); self.addCleanup(fixture.close)
        phases = ["migration-state-observation", "effective-privilege", "runtime-identity-initial-access", "credential-revocation", "credential-recovery", "runtime-identity-access-route"]
        latest = {}
        for name in phases:
            argv = route["commands"][name]["argv"]
            mode = argv[argv.index("--operation") + 1]
            key = name.replace("-", "_") + "_predecessor"
            self.assertEqual(route["inputs"][key], {"kind": "identifier", "owner": "run-administration", "example": "none"})
            self.assertEqual(argv[argv.index("--expected-operation") + 1], "{" + key + "}")
            resolved = resolver.resolve(argv, {key: latest.get(mode, "none")})
            self.assertIsNotNone(resolved)
            extra = resolved[resolved.index("--new-operation"):resolved.index("--json")]
            before = fixture.launches()
            fresh = fixture.invoke(mode, *extra)
            self.assertEqual(fresh["verdict"], "accepted", fresh)
            self.assertEqual(fresh["facts"]["evidence_reuse"], "fresh-terminal-observation")
            self.assertEqual(fixture.launches(), before + 1)
            current = fresh["facts"]["operation_id"]
            self.assertNotEqual(current, latest.get(mode))
            latest[mode] = current
            reused = fixture.invoke(mode, *extra)
            self.assertEqual(reused["facts"]["operation_id"], current)
            self.assertEqual(reused["facts"]["evidence_reuse"], "historical-completion")
            self.assertEqual(fixture.invoke(mode)["facts"]["evidence_reuse"], "historical-completion")
            self.assertEqual(fixture.invoke(mode, "--new-operation", "--expected-operation", "kp-" + "f"*32)["verdict"], "blocked")
            self.assertEqual(fixture.launches(), before + 1)
        self.assertEqual(fixture.launches(), 6)

    def test_credential_caller_resumes_uncertainty_then_requests_next_transition(self):
        fixture = Fixture("administration"); self.addCleanup(fixture.close)
        lifecycle = load("actual_credential_lifecycle", BASE / "rehearse-runtime-credential-lifecycle/script.py")
        def child(_command, *arguments):
            mode = arguments[arguments.index("--operation") + 1]
            extra = arguments[arguments.index("--new-operation"):] if "--new-operation" in arguments else ()
            observed = fixture.invoke(mode, *extra)
            if observed["verdict"] != "accepted": lifecycle.CHILD_CHECKPOINT = observed; return None
            return observed
        lifecycle.child = child
        fixture.lost = True
        self.assertFalse(lifecycle.administer("revoke-runtime"))
        self.assertTrue(lifecycle.administer("revoke-runtime"))
        self.assertEqual(fixture.launches(), 1)
        fixture.lost = False
        self.assertTrue(lifecycle.administer("restore-runtime"))
        self.assertTrue(lifecycle.administer("revoke-runtime"))
        self.assertTrue(lifecycle.administer("restore-runtime"))
        self.assertEqual(fixture.launches(), 4)

    def test_shared_observer_never_reads_after_deadline(self):
        execution = load("actual_ecs_execution", BASE.parents[4] / "shared/provider-adapters/aws/tasks.py")
        for initial in (None, {"lastStatus": "RUNNING"}):
            clock, reads, pauses = [0], [], []
            def read(_previous): reads.append(clock[0]); return {"lastStatus": "RUNNING"}
            def sleep(seconds): pauses.append(seconds); clock[0] += seconds
            task, terminal = execution.observe_until_terminal(read, initial=initial, seconds=5, interval=2,
                monotonic=lambda: clock[0], sleep=sleep)
            self.assertFalse(terminal)
            self.assertEqual(reads, [0, 2, 4])
            self.assertEqual(pauses, [2, 2, 1])
            self.assertEqual(task["lastStatus"], "RUNNING")


class RecoveryResourceTests(unittest.TestCase):
    def setUp(self):
        self.binding = load("resource_snapshot_binding", BASE / "snapshot-operations.py")
        self.temp = tempfile.TemporaryDirectory(prefix="resource-originals-")
        self.addCleanup(self.temp.cleanup)
        self.store = self.binding.Store(Path(self.temp.name))
        self.request = {"database": self.binding.DATABASE,
            "snapshot": "kanbien-core-platform-persistence-recovery-20261127-cost",
            "source_resource_id": "db-SOURCE"}

    def test_resource_cost_adapter_preserves_native_failure_and_hides_owner_text(self):
        sentinel = RuntimeError(CANARY)
        class Owner:
            @staticmethod
            def reserve_recovery_cost_admission(**values): return values["reserve"]()
        def fail(): raise sentinel
        with patch.object(self.binding, "module", return_value=Owner):
            with self.assertRaises(RuntimeError) as raised:
                self.binding.reserve_resource_cost("create-recovery-point", self.request, fail)
        self.assertIs(raised.exception, sentinel)
        with patch.object(Owner, "reserve_recovery_cost_admission", side_effect=ValueError(CANARY)), patch.object(self.binding, "module", return_value=Owner):
            with self.assertRaisesRegex(self.binding.OperationFailure, "^persistence-recovery-cost-admission-not-confirmed$"):
                self.binding.reserve_resource_cost("create-recovery-point", self.request, lambda: self.fail("no reserve after refusal"))

    def test_callback_retains_original_and_cannot_reclassify_it_as_fresh(self):
        calls = []
        def execute(callback):
            return self.binding.SNAPSHOTS.create(lambda *a, **k: calls.append(k), self.store,
                phase="create-recovery-point", request=self.request, arguments=lambda value: {"token": value["operation_id"]},
                precondition=lambda value: None, validate_reservation=lambda value: None,
                observe=lambda value, fresh: (value, fresh), reserve=callback)
        original, fresh = execute(lambda: self.store.reserve("create-recovery-point", self.request))
        self.assertTrue(fresh)
        self.assertEqual(len(calls), 1)
        self.assertEqual(execute(lambda: self.store.reserve("create-recovery-point", self.request)), (original, False))
        with self.assertRaisesRegex(self.binding.SNAPSHOTS.SnapshotFailure, "reservation-not-retained"):
            execute(lambda: (original, True))
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.store.records(), [original])
        # Uncertain originals remain in the census; a foreign file is not ignored.
        (Path(self.temp.name) / "foreign.json").write_text(json.dumps(original))
        with self.assertRaisesRegex(self.binding.OperationFailure, "reservation-census-invalid"):
            self.store.records()

    def test_change_set_callback_failure_occurs_before_submission_and_never_replays(self):
        changes = load("resource_cost_changes", self.binding.SHARED / "change_sets.py")
        calls = []
        def execute(callback):
            return changes.execute(lambda *a, **k: calls.append(k), self.store,
                phase="create-recovery-point", request=self.request, arguments={}, precondition=lambda value: None,
                observe=lambda value: value, reserve=callback)
        sentinel = RuntimeError(CANARY)
        def fail(): raise sentinel
        with self.assertRaises(RuntimeError) as raised: execute(fail)
        self.assertIs(raised.exception, sentinel)
        self.assertEqual(calls, [])
        original = execute(lambda: self.store.reserve("create-recovery-point", self.request))
        self.assertEqual(execute(lambda: self.store.reserve("create-recovery-point", self.request)), original)
        with self.assertRaisesRegex(changes.ChangeSetFailure, "reservation-not-retained"):
            execute(lambda: (original, True))
        self.assertEqual(len(calls), 1)


if __name__ == "__main__": unittest.main(verbosity=2)
