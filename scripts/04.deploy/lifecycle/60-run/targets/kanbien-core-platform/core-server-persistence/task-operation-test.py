#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-persistence.task-operations
#   version: 1
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
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import yaml
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
        self.receipts = load("actual_task_receipts", BASE / "proof-receipts.py")
        self.receipts.RECEIPTS = self.root / "receipts"
        self.receipts.EVIDENCE_CLASS = "simulated"
        self.control.ROOT = self.migration.ROOT = self.root
        self.control.deadline = lambda: 5
        self.migration.proof_receipts = lambda: self.receipts
        if kind == "administration": self.control.RECEIPTS = self.receipts
        self.control.aws = self.migration.aws = self.aws
        self.tasks, self.calls = [], []
        self.runtime, self.storage = None, None
        self.lost, self.missing, self.running, self.corrupt = False, False, False, False
        self.exit_code, self.revision = 0, 7
        def outputs(_stack):
            return {"CoreServerPersistenceMigrationTaskDefinitionArn": self.definition,
                    "CoreServerPersistenceAdministrationTaskDefinitionArn": f"arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:{self.revision}",
                    "PersistenceMigrationSecurityGroupId": "sg-migration", "PersistenceAdministrationSecurityGroupId": "sg-administrator",
                    "PrivateSubnetIds": "subnet-private"}, "ok"
        self.migration.outputs = outputs
        self.control.outputs = outputs

    @property
    def definition(self):
        family = self.runtime["family"] if self.runtime is not None else "kanbien-core-platform-persistence-" + self.kind
        return f"arn:aws:ecs:eu-west-1:337159794548:task-definition/{family}:{self.revision}"

    def state_path(self, operation):
        return self.root / ".git" / ("persistence-" + self.kind) / (operation + ".json")

    def aws(self, *arguments):
        self.calls.append(arguments)
        operation = arguments[1]
        def value(flag): return arguments[arguments.index(flag) + 1]
        if operation == "run-task":
            overrides = json.loads(value("--overrides"))
            mode = overrides["containerOverrides"][0]["environment"][0]["value"]
            journal = self.storage.value if self.storage is not None else json.loads(self.state_path(mode).read_text())
            assert journal["operation_id"] == value("--started-by") == value("--client-token")
            if self.storage is None:
                assert self.state_path(mode).with_suffix(".lock").read_bytes(), "durable sentinel before launch"
            else:
                assert self.storage.events[-1] == "admitted", "exact retained admission before launch"
            cluster = self.runtime["cluster_arn"].rsplit("/", 1)[-1] if self.runtime is not None else "kanbien-core-platform"
            container = self.runtime["container_name"] if self.runtime is not None else "persistence-" + self.kind
            task = {"taskArn": f"arn:aws:ecs:eu-west-1:337159794548:task/{cluster}/" + f"{len(self.tasks)+1:032x}",
                    "taskDefinitionArn": value("--task-definition"), "startedBy": value("--started-by"), "overrides": overrides,
                    "lastStatus": "PENDING", "startedAt": "2026-11-15T00:00:00Z", "stoppedAt": "2026-11-15T00:00:01Z",
                    "containers": [{"name": container, "exitCode": self.exit_code}]}
            self.tasks.append(task)
            return (False, None, "aws-response-invalid") if self.lost else (True, {"tasks": [copy.deepcopy(task)]}, "ok")
        if operation == "list-tasks":
            return True, {"taskArns": [] if self.missing or value("--desired-status") != ("RUNNING" if self.running else "STOPPED") else [task["taskArn"] for task in self.tasks]}, "ok"
        if operation == "describe-tasks":
            wanted = arguments[arguments.index("--tasks")+1:]
            tasks = [] if self.missing else [dict(copy.deepcopy(task), lastStatus="RUNNING" if self.running else "STOPPED") for task in self.tasks if task["taskArn"] in wanted]
            if self.corrupt and tasks: tasks[0]["overrides"] = {"containerOverrides": []}
            return True, {"tasks": tasks}, "ok"
        if operation == "describe-task-definition":
            definition = {"taskDefinitionArn": getattr(self, "returned_definition", value("--task-definition")), "containerDefinitions": [{"name": self.runtime["container_name"] if self.runtime is not None else "persistence-" + self.kind, "image": "fixture/image@sha256:" + "a"*64}]}
            if getattr(self, "returned_definition", None) == "missing": definition.pop("taskDefinitionArn")
            return True, {"taskDefinition": definition}, "ok"
        if operation == "get-log-events":
            task_id = value("--log-stream-name").rsplit("/", 1)[1]
            task = next(task for task in self.tasks if task["taskArn"].endswith(task_id))
            mode = task["overrides"]["containerOverrides"][0]["environment"][0]["value"]
            code = self.control.SUCCESS[mode]
            if not isinstance(code, str): code = code[-1]
            return True, {"events": [{"message": json.dumps({"verdict": "accepted", "code": code})}]}, "ok"
        raise AssertionError(("unmocked provider operation", arguments))

    def invoke(self, operation=None, *extra):
        mode = operation or ("apply" if self.kind == "migration" else "revoke-runtime")
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


class RetainedJournalTests(unittest.TestCase):
    """Controlled storage only; actual binding still validates journal records."""
    def setUp(self):
        self.fixture = Fixture("migration")
        self.addCleanup(self.fixture.close)
        self.fixture.invoke()
        self.original = json.loads(self.fixture.state_path("apply").read_text())
        self.operations = self.fixture.control.task_operations()
        self.journal = self.operations.JOURNAL
        self.binding = self.operations.BoundOperation(root=self.fixture.root,
            proof_type="migration", family="kanbien-core-platform-persistence-migration",
            container="persistence-migration", selector="PERSISTENCE_MIGRATION_OPERATION",
            results=self.fixture.control.SUCCESS, aws=self.fixture.aws, report=None,
            accept=None, receipts=self.fixture.receipts)
        self.proofs = []

    def validate(self, value):
        return self.binding.validate_record(value, "apply")

    def completed(self, value):
        self.proofs.append(copy.deepcopy(value))
        return self.binding.completion(value)

    class Storage:
        def __init__(self, value=None, outcome=True):
            self.value, self.outcome = copy.deepcopy(value), outcome
            self.reads, self.writes, self.history = [], [], []
            self.readback = "exact"

        def read(self, key):
            self.reads.append(key)
            if self.readback == "throw" and self.writes: raise OSError(CANARY)
            if self.readback == "missing" and self.writes: return None
            if self.readback == "different" and self.writes: return self.history[-1]
            return copy.deepcopy(self.value)

        def compare_and_reserve(self, key, expected, proposed):
            self.writes.append((key, copy.deepcopy(expected), copy.deepcopy(proposed)))
            if self.outcome == "throw-before": raise OSError(CANARY)
            if expected != self.value: return False
            if self.outcome is True or self.outcome == "throw-after":
                self.history.append(copy.deepcopy(expected))
                self.value = copy.deepcopy(proposed)
                if self.outcome == "throw-after": raise OSError(CANARY)
            return self.outcome

    def reserve(self, storage, **changes):
        arguments = dict(schema=self.binding.schema, mode="apply", request=copy.deepcopy(self.original["request"]),
                         new_operation=False, expected=None, completed=self.completed, validate_record=self.validate)
        arguments.update(changes)
        return self.journal.reserve_retained(storage, "workflow-step", **arguments)

    def test_retained_freshness_requires_exact_readback_and_reuse_never_reserves(self):
        storage = self.Storage()
        value, fresh = self.reserve(storage)
        self.assertTrue(fresh)
        self.assertEqual(value, storage.value)
        self.assertEqual(self.validate(value), value)
        self.assertEqual(set(value), set(self.original))
        self.assertIsNone(value["task_arn"])
        self.assertEqual(len(storage.reads), 2)
        self.assertEqual(storage.writes[0][1], None)
        self.assertEqual(storage.writes[0][2], value)
        again, fresh = self.reserve(storage)
        self.assertFalse(fresh)
        self.assertEqual(again, value)
        self.assertEqual(len(storage.writes), 1)
        self.assertEqual(self.proofs, [])
        self.assertEqual(self.fixture.launches(), 1)  # Setup only; helper never launches.

    def test_retained_successor_checks_actual_completion_once_and_retains_exact_history(self):
        storage = self.Storage(self.original)
        value, fresh = self.reserve(storage, new_operation=True, expected=self.original["operation_id"])
        self.assertTrue(fresh)
        self.assertEqual(value["predecessor"], self.original["operation_id"])
        self.assertNotEqual(value["operation_id"], self.original["operation_id"])
        self.assertEqual(self.proofs, [self.original])
        self.assertEqual(storage.history, [self.original])
        self.assertEqual(storage.writes[0][1], self.original)
        again, fresh = self.reserve(storage, new_operation=True, expected=self.original["operation_id"])
        self.assertEqual(again, value)
        self.assertFalse(fresh)
        self.assertEqual(len(self.proofs), 1)
        self.assertEqual(len(storage.writes), 1)

    def test_retained_request_predecessor_and_incomplete_proof_reject_before_write(self):
        changed = {**self.original["request"], "deadline_seconds": 6}
        cases = [(self.original, {"request": changed}, "operation-request-changed"),
                 (None, {"new_operation": True, "expected": self.original["operation_id"]}, "operation-predecessor-missing"),
                 (self.original, {"new_operation": True, "expected": "kp-" + "f"*32}, "operation-predecessor-mismatch"),
                 (self.original, {"new_operation": True, "expected": self.original["operation_id"], "completed": lambda _value: None}, "prior-operation-not-complete")]
        for original, arguments, code in cases:
            with self.subTest(code=code):
                storage = self.Storage(original)
                with self.assertRaisesRegex(self.journal.JournalFailure, "^" + code + "$"):
                    self.reserve(storage, **arguments)
                self.assertEqual(storage.writes, [])
                self.assertEqual(storage.value, original)
        self.assertEqual(self.proofs, [])

    def test_retained_conflict_malformed_and_lost_writes_never_grant_freshness_or_retry(self):
        for outcome in (False, None, 1, "true", "throw-before", "throw-after"):
            with self.subTest(outcome=outcome):
                storage = self.Storage(outcome=outcome)
                with self.assertRaisesRegex(self.journal.JournalFailure, "^operation-retention-not-confirmed$") as caught:
                    self.reserve(storage)
                self.assertNotIn(CANARY, str(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__ or caught.exception.__context__ is None)
                self.assertEqual(len(storage.writes), 1)
                self.assertEqual(len(storage.reads), 1)
                if outcome == "throw-after":
                    storage.outcome = True
                    _, fresh = self.reserve(storage)
                    self.assertFalse(fresh)
                    self.assertEqual(len(storage.writes), 1)
        storage = self.Storage()
        original_compare = storage.compare_and_reserve
        def concurrent(key, expected, proposed):
            storage.value = copy.deepcopy(self.original)
            return original_compare(key, expected, proposed)
        storage.compare_and_reserve = concurrent
        with self.assertRaisesRegex(self.journal.JournalFailure, "^operation-retention-not-confirmed$"):
            self.reserve(storage)
        self.assertEqual(storage.value, self.original)
        self.assertEqual(storage.history, [])
        self.assertEqual(len(storage.writes), 1)

    def test_retained_lost_or_changed_readback_stays_uncertain_without_replay(self):
        for readback, code in (("missing", "operation-retention-not-confirmed"),
                               ("different", "operation-retention-not-confirmed"),
                               ("throw", "operation-store-unavailable")):
            with self.subTest(readback=readback):
                storage = self.Storage(self.original)
                storage.readback = readback
                with self.assertRaisesRegex(self.journal.JournalFailure, "^" + code + "$") as caught:
                    self.reserve(storage, new_operation=True, expected=self.original["operation_id"])
                self.assertNotIn(CANARY, str(caught.exception))
                self.assertEqual(len(storage.writes), 1)
                self.assertEqual(len(storage.reads), 2)
                storage.readback = "exact"
                _, fresh = self.reserve(storage, new_operation=True, expected=self.original["operation_id"])
                self.assertFalse(fresh)
                self.assertEqual(len(storage.writes), 1)

    def test_retained_actual_validator_and_proof_failures_preserve_safe_owner_reason(self):
        invalid = copy.deepcopy(self.original)
        invalid["request"]["deadline_seconds"] = CANARY
        storage = self.Storage(invalid)
        with self.assertRaisesRegex(self.operations.OperationFailure, "^operation-metadata-invalid$"):
            self.reserve(storage)
        self.assertEqual(storage.writes, [])
        invalid = copy.deepcopy(self.original)
        invalid["proof_sha256"] = "f" * 64
        storage = self.Storage(self.journal.with_integrity(invalid))
        with self.assertRaisesRegex(self.operations.OperationFailure, "^terminal-proof-unavailable$"):
            self.reserve(storage, new_operation=True, expected=invalid["operation_id"])
        self.assertEqual(storage.writes, [])
        for validator in (lambda _value: None, lambda value: {**value, "mode": "changed"}):
            storage = self.Storage()
            with self.assertRaisesRegex(self.journal.JournalFailure, "^operation-metadata-invalid$"):
                self.reserve(storage, validate_record=validator)
            self.assertEqual(storage.writes, [])
        storage = self.Storage()
        storage.read = lambda _key: (_ for _ in ()).throw(OSError(CANARY))
        with self.assertRaisesRegex(self.journal.JournalFailure, "^operation-store-unavailable$"):
            self.reserve(storage)
        self.assertEqual(storage.writes, [])

    def test_both_routes_use_the_same_pure_selector_and_storage_contract_is_required(self):
        storage = self.Storage()
        with patch.object(self.journal, "select_reservation", side_effect=self.journal.JournalFailure("operation-predecessor-mismatch")) as selected:
            with self.assertRaisesRegex(self.journal.JournalFailure, "^operation-predecessor-mismatch$"):
                self.reserve(storage)
            with self.assertRaisesRegex(self.journal.JournalFailure, "^operation-predecessor-mismatch$"):
                self.journal.reserve(None, None, None, schema=self.binding.schema, marker=self.binding.marker,
                    mode="apply", request=self.original["request"], new_operation=False, expected=None, completed=self.completed)
            self.assertEqual(selected.call_count, 2)
        self.assertEqual(storage.writes, [])
        for invalid in (object(), type("ReadOnly", (), {"read": lambda *_: None})()):
            with self.assertRaisesRegex(self.journal.JournalFailure, "^operation-storage-invalid$"):
                self.reserve(invalid)


class RetainedTaskConsumerTests(unittest.TestCase):
    class Storage(RetainedJournalTests.Storage):
        def __init__(self, journal):
            super().__init__()
            self.journal, self.events, self.receipts = journal, [], {}
            self.fail, self.guard = None, True

        def before_submit(self, key, expected):
            assert expected == self.value
            self.events.append("admitted")
            if self.guard == "throw": raise OSError(CANARY)
            return self.guard

        def attach(self, method, expected, **fields):
            assert expected == self.value
            self.events.append(method)
            if self.fail == method: raise OSError(CANARY)
            self.value = self.journal.with_integrity({**expected, **fields})
            if self.fail == method + "-lost": raise OSError(CANARY)
            if self.fail == method + "-malformed": return {**self.value, "request": {}}
            return copy.deepcopy(self.value)

        def retain_task(self, key, expected, arn):
            return self.attach("task", expected, task_arn=arn)

        def retain_proof(self, key, expected, reference):
            return self.attach("proof", expected, proof_receipt=reference["path"], proof_sha256=reference["sha256"])

        def retain_receipt(self, label, raw):
            self.events.append("receipt")
            if self.fail == "receipt": raise OSError(CANARY)
            self.receipts.setdefault(label, raw)
            return self.receipts[label]

        def read_receipt(self, label):
            if self.fail == "read-receipt": raise OSError(CANARY)
            return self.receipts[label]

    def fixture(self, kind):
        fixture = Fixture(kind); self.addCleanup(fixture.close)
        fixture.runtime = {"schema": "deploy/aws-task-runtime/v1", "session_id": "1" * 32,
            "source_plan_sha256": "a" * 64, "binding_sha256": "sha256:" + "b" * 64,
            "stack_id": "arn:aws:cloudformation:eu-west-1:337159794548:stack/test-session/" + "a" * 36,
            "cluster_arn": "arn:aws:ecs:eu-west-1:337159794548:cluster/test-session",
            "family": "test-session-" + kind, "container_name": "renamed-" + kind,
            "log_group": "/test/session", "log_stream_prefix": "session-" + kind}
        fixture.operations = fixture.migration.task_operations()
        fixture.storage = self.Storage(fixture.operations.JOURNAL)
        return fixture

    def invoke(self, fixture, *, runtime=None, storage=True, **options):
        kind = fixture.kind
        context = fixture.runtime if runtime is None else runtime
        binding = fixture.operations.BoundOperation(root=fixture.root, proof_type=kind,
            family="kanbien-core-platform-persistence-" + kind, container="persistence-" + kind,
            selector="PERSISTENCE_" + kind.upper() + "_OPERATION", results=fixture.control.SUCCESS,
            aws=fixture.aws, report=fixture.control.report,
            accept=fixture.control.accepted_completion if kind == "migration" else fixture.control.accept,
            receipts=fixture.receipts, runtime=context, storage=fixture.storage if storage else None, step_id=kind)
        mode = "apply" if kind == "migration" else "revoke-runtime"
        overrides = {"containerOverrides": [{"name": context["container_name"], "environment": [{"name": binding.selector, "value": mode}]}]}
        output, error = io.StringIO(), io.StringIO()
        with patch.object(binding, "paths", side_effect=AssertionError("no local paths")), \
                patch.object(fixture.operations.JOURNAL, "save", side_effect=AssertionError("no local saves")), \
                patch.object(fixture.receipts, "persist", side_effect=AssertionError("no local receipt")), \
                patch.object(fixture.migration, "aws", side_effect=AssertionError("no default provider")), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = binding.run(mode=mode, definition=fixture.definition, network="session-network", overrides=json.dumps(overrides), seconds=5,
                historical=lambda: (_ for _ in ()).throw(AssertionError("no production scan")), **options)
        self.assertNotIn(CANARY, output.getvalue() + error.getvalue())
        result = json.loads(output.getvalue())
        self.assertEqual(status == 0, result["verdict"] == "accepted")
        self.assertFalse(fixture.receipts.RECEIPTS.exists())
        return result

    def test_actual_acceptance_uses_runtime_routes_and_retained_first_proof(self):
        for kind in ("migration", "administration"):
            fixture = self.fixture(kind)
            first = self.invoke(fixture)
            self.assertEqual(first["verdict"], "accepted", first)
            self.assertEqual(fixture.storage.value["request"]["runtime"], fixture.runtime)
            self.assertEqual(fixture.storage.events, ["admitted", "task", "receipt", "proof"])
            original = copy.deepcopy(fixture.storage.receipts)
            calls = len(fixture.calls)
            again = self.invoke(fixture)
            self.assertEqual(again["verdict"], "accepted", again)
            self.assertEqual(again["facts"]["evidence_reuse"], "historical-completion")
            self.assertEqual(fixture.storage.receipts, original)
            self.assertEqual(len(fixture.calls), calls)
            self.assertEqual(fixture.launches(), 1)
            for call in fixture.calls:
                if call[1] in {"run-task", "describe-tasks", "list-tasks"}:
                    self.assertEqual(call[call.index("--cluster") + 1], fixture.runtime["cluster_arn"])
                if call[1] == "get-log-events":
                    self.assertEqual(call[call.index("--log-group-name") + 1], fixture.runtime["log_group"])
                    self.assertTrue(call[call.index("--log-stream-name") + 1].startswith(fixture.runtime["log_stream_prefix"] + "/" + fixture.runtime["container_name"] + "/"))

    def test_lost_launch_recovers_only_original_cluster_and_request_drift_never_sends(self):
        for kind in ("migration", "administration"):
            fixture = self.fixture(kind); fixture.lost = True
            self.assertEqual(self.invoke(fixture)["verdict"], "uncertain")
            for field, value in (("cluster_arn", fixture.runtime["cluster_arn"] + "-other"),
                                 ("session_id", "2" * 32), ("binding_sha256", "sha256:" + "c" * 64)):
                changed = {**fixture.runtime, field: value}
                self.assertEqual(self.invoke(fixture, runtime=changed)["verdict"], "blocked")
            fixture.lost = False
            recovered = self.invoke(fixture)
            self.assertEqual(recovered["verdict"], "accepted", recovered)
            self.assertEqual(fixture.launches(), 1)
            self.assertEqual(fixture.storage.events.count("admitted"), 1)

    def test_no_storage_or_false_malformed_missing_guard_cannot_launch(self):
        for guard in (False, None, 1, "throw"):
            fixture = self.fixture("migration"); fixture.storage.guard = guard
            observed = self.invoke(fixture)
            self.assertEqual(observed["verdict"], "blocked", observed)
            self.assertEqual(observed["findings"][0]["code"], "persistence-migration-operation-admission-not-confirmed")
            fixture.storage.guard = True
            self.assertEqual(self.invoke(fixture)["verdict"], "uncertain")
            self.assertEqual(fixture.launches(), 0)
        for missing in (None, "before_submit"):
            fixture = self.fixture("migration")
            if missing: fixture.storage.before_submit = None
            result = self.invoke(fixture, storage=missing is not None)
            self.assertEqual(result["verdict"], "blocked", result)
            self.assertEqual(fixture.launches(), 0)
            self.assertEqual(fixture.storage.writes, [])

    def test_task_proof_and_receipt_uncertainty_never_replays(self):
        for kind in ("migration", "administration"):
            for failure in ("task", "task-lost", "task-malformed", "proof", "proof-lost", "proof-malformed", "receipt"):
                fixture = self.fixture(kind); fixture.storage.fail = failure
                observed = self.invoke(fixture)
                self.assertEqual(observed["verdict"], "uncertain", (failure, observed))
                original_receipts = copy.deepcopy(fixture.storage.receipts)
                fixture.storage.fail = None
                recovered = self.invoke(fixture)
                self.assertEqual(recovered["verdict"], "accepted", (failure, recovered))
                self.assertEqual(fixture.launches(), 1)
                for label, raw in original_receipts.items(): self.assertEqual(fixture.storage.receipts[label], raw)

    def test_completed_successor_preserves_explicit_authorization_and_exact_predecessor(self):
        for kind in ("migration", "administration"):
            fixture = self.fixture(kind)
            first = self.invoke(fixture)
            prior = first["facts"]["operation_id"]
            calls = []
            def authorize(value, proof):
                calls.append((value["operation_id"], proof["task"]["arn"]))
                raise fixture.operations.OperationFailure("successor-not-authorized")
            denied = self.invoke(fixture, new_operation=True, expected_operation=prior, authorize_successor=authorize)
            self.assertEqual(denied["verdict"], "blocked")
            self.assertEqual(fixture.launches(), 1)
            self.assertEqual(len(calls), 1)
            accepted = self.invoke(fixture, new_operation=True, expected_operation=prior, authorize_successor=lambda value, proof: calls.append((value["operation_id"], proof["task"]["arn"])))
            self.assertEqual(accepted["verdict"], "accepted", accepted)
            self.assertEqual(fixture.storage.value["predecessor"], prior)
            self.assertEqual(fixture.launches(), 2)
            self.assertEqual(self.invoke(fixture, new_operation=True, expected_operation=prior)["verdict"], "accepted")
            self.assertEqual(fixture.launches(), 2)

    def test_failed_completion_retains_proof_and_storage_read_failure_is_finite(self):
        for kind in ("migration", "administration"):
            fixture = self.fixture(kind); fixture.exit_code = 1
            failed = self.invoke(fixture)
            self.assertEqual(failed["verdict"], "failed", failed)
            self.assertIsNotNone(fixture.storage.value["proof_receipt"])
            fixture.storage.fail = "read-receipt"
            self.assertEqual(self.invoke(fixture)["verdict"], "uncertain")
            fixture.storage.fail = None
            self.assertEqual(self.invoke(fixture)["verdict"], "failed")
            self.assertEqual(fixture.launches(), 1)

    def test_actual_task_and_proof_attachments_use_shared_journal_owner(self):
        for kind in ("migration", "administration"):
            for method in ("retain_task", "retain_proof"):
                fixture = self.fixture(kind)
                original = fixture.operations.JOURNAL.attach_retained
                calls = []
                def checked(*args, **kwargs):
                    calls.append(kwargs["method"])
                    if kwargs["method"] == method:
                        raise fixture.operations.JOURNAL.JournalFailure("operation-retention-not-confirmed")
                    return original(*args, **kwargs)
                with patch.object(fixture.operations.JOURNAL, "attach_retained", side_effect=checked):
                    result = self.invoke(fixture)
                self.assertEqual(result["verdict"], "uncertain", result)
                self.assertIn(method, calls)
                self.assertEqual(fixture.launches(), 1)
                self.assertEqual(self.invoke(fixture)["verdict"], "accepted")
                self.assertEqual(fixture.launches(), 1)

    def test_direct_readers_reject_invalid_runtime_and_missing_provider_before_any_read(self):
        for kind in ("migration", "administration"):
            fixture = self.fixture(kind)
            self.assertEqual(self.invoke(fixture)["verdict"], "accepted")
            task = copy.deepcopy(fixture.tasks[0])
            mode = "apply" if kind == "migration" else "revoke-runtime"
            readers = [(lambda **kw: fixture.migration.image_digest(fixture.definition, **kw), None)]
            if kind == "migration":
                readers.extend([(lambda **kw: fixture.control.migration_log_accepted(task, mode, **kw), (False, "persistence-migration-evidence-unavailable")),
                                (lambda **kw: fixture.control.migration_log_rejection(task, **kw), (None, "persistence-migration-evidence-unavailable"))])
            else:
                readers.append((lambda **kw: fixture.control.accepted_log(task, mode, **kw), (None, "persistence-administration-evidence-unavailable")))
            cases = [(fixture.runtime, provider) for provider in (None, False, object())]
            cases += [(runtime, fixture.aws) for runtime in ({}, CANARY, {**fixture.runtime, "cluster_arn": CANARY})]
            before = len(fixture.calls), copy.deepcopy(fixture.storage.events)
            with patch.object(fixture.migration, "aws", side_effect=AssertionError(CANARY)), \
                    patch.object(fixture.receipts, "persist", side_effect=AssertionError(CANARY)):
                for runtime, provider in cases:
                    for read, expected in readers:
                        observed = read(runtime=runtime, provider=provider)
                        self.assertEqual(observed, expected)
                        self.assertNotIn(CANARY, str(observed))
            self.assertEqual((len(fixture.calls), fixture.storage.events), before)

    def test_direct_acceptance_requires_store_provider_callback_and_exact_terminal_container(self):
        for kind in ("migration", "administration"):
            fixture = self.fixture(kind)
            self.assertEqual(self.invoke(fixture)["verdict"], "accepted")
            task = copy.deepcopy(fixture.tasks[0]); task["lastStatus"] = "STOPPED"
            mode = "apply" if kind == "migration" else "revoke-runtime"
            accept = fixture.control.accepted_completion if kind == "migration" else fixture.control.accept
            references = []
            base = {"runtime": fixture.runtime, "provider": fixture.aws,
                    "receipt_storage": fixture.storage, "on_receipt": references.append}
            cases = [({"runtime": runtime}, task, "operation-runtime-invalid") for runtime in ({}, CANARY, {**fixture.runtime, "family": CANARY + "!"})]
            cases += [({key: value}, task, "operation-storage-invalid") for key, value in
                      (("provider", None), ("provider", False), ("receipt_storage", None), ("on_receipt", None), ("on_receipt", False))]
            foreign = copy.deepcopy(task); foreign["containers"][0]["name"] = CANARY
            cases.append(({}, foreign, "controller-task-identity-mismatch"))
            before = len(fixture.calls), copy.deepcopy(fixture.storage.events)
            with patch.object(fixture.migration, "aws", side_effect=AssertionError(CANARY)), \
                    patch.object(fixture.receipts, "persist", side_effect=AssertionError(CANARY)):
                for changes, observed_task, code in cases:
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output): status = accept(observed_task, 5, mode, **{**base, **changes})
                    self.assertNotEqual(status, 0)
                    self.assertNotIn(CANARY, output.getvalue())
                    report = json.loads(output.getvalue())
                    self.assertEqual(report["findings"][0]["code"], "persistence-" + kind + "-" + code)
                    self.assertEqual(report["verdict"], "uncertain" if code == "controller-task-identity-mismatch" else "blocked")
            self.assertEqual((len(fixture.calls), fixture.storage.events), before)
            self.assertEqual(references, [])

    def test_falsey_explicit_provider_is_used_by_every_direct_reader_and_acceptance(self):
        class FalseyProvider:
            def __init__(self, invoke): self.invoke = invoke
            def __bool__(self): return False
            def __call__(self, *parts): return self.invoke(*parts)
        for kind in ("migration", "administration"):
            fixture = self.fixture(kind)
            self.assertEqual(self.invoke(fixture)["verdict"], "accepted")
            task = copy.deepcopy(fixture.tasks[0]); task["lastStatus"] = "STOPPED"
            mode = "apply" if kind == "migration" else "revoke-runtime"
            provider = FalseyProvider(fixture.aws)
            selected = {"runtime": fixture.runtime, "provider": provider}
            references, output = [], io.StringIO()
            raw = copy.deepcopy(fixture.storage.receipts)
            before = len(fixture.calls)
            with patch.object(fixture.migration, "aws", side_effect=AssertionError(CANARY)), \
                    patch.object(fixture.receipts, "persist", side_effect=AssertionError(CANARY)), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(fixture.migration.image_digest(fixture.definition, **selected), "sha256:" + "a" * 64)
                if kind == "migration":
                    self.assertEqual(fixture.control.migration_log_accepted(task, mode, **selected), (True, "ok"))
                    self.assertEqual(fixture.control.migration_log_rejection(task, **selected), (None, "persistence-migration-rejection-not-confirmed"))
                    accept = fixture.control.accepted_completion
                else:
                    self.assertEqual(fixture.control.accepted_log(task, mode, **selected), (fixture.control.SUCCESS[mode], "ok"))
                    accept = fixture.control.accept
                status = accept(task, 5, mode, on_receipt=references.append, receipt_storage=fixture.storage, **selected)
            self.assertEqual(status, 0, output.getvalue())
            self.assertEqual(len(references), 1)
            self.assertEqual(references[0], {"path": fixture.storage.value["proof_receipt"], "sha256": fixture.storage.value["proof_sha256"]})
            self.assertEqual(fixture.storage.receipts, raw)
            self.assertEqual(len(fixture.calls) - before, 5 if kind == "migration" else 4)
            self.assertNotIn(CANARY, output.getvalue())
            self.assertFalse(fixture.receipts.RECEIPTS.exists())

    def test_direct_completion_rejects_wrong_or_missing_returned_definition_before_receipt(self):
        fixture = self.fixture("migration"); fixture.lost = True
        self.assertEqual(self.invoke(fixture)["verdict"], "uncertain")
        task = copy.deepcopy(fixture.tasks[0]); task["lastStatus"] = "STOPPED"
        events, references = copy.deepcopy(fixture.storage.events), []
        for returned in (fixture.definition + "0", "missing"):
            fixture.returned_definition = returned; output = io.StringIO()
            with contextlib.redirect_stdout(output), patch.object(fixture.migration, "aws", side_effect=AssertionError(CANARY)):
                status = fixture.migration.accepted_completion(task, 5, "apply", runtime=fixture.runtime, provider=fixture.aws,
                    receipt_storage=fixture.storage, on_receipt=references.append)
                self.assertEqual(fixture.migration.image_digest(fixture.definition, provider=fixture.aws), "sha256:" + "a" * 64)
            result = json.loads(output.getvalue())
            self.assertNotEqual(status, 0); self.assertEqual(result["verdict"], "blocked")
            self.assertEqual([row["code"] for row in result["findings"]], ["persistence-migration-receipt-identity-unavailable"])
            self.assertEqual(fixture.storage.events, events); self.assertEqual(fixture.storage.receipts, {})
            self.assertEqual(references, []); self.assertEqual(fixture.launches(), 1)


class CheckedRuntimeProducerTests(unittest.TestCase):
    """Actual captured templates and concrete persistence producer; no provider authority."""
    @classmethod
    def setUpClass(cls):
        cls.root = BASE.parents[6]
        cls.owner = load("actual_persistence_runtime_producer", BASE / "task-operations.py")
        cls.shared = load("actual_shared_runtime_comparison", cls.root / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
        preparation = load("actual_binding_preparation", cls.root / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py")
        document = {"schema": "deploy/environment-session-intent/v1", "target": "kanbien-core-platform", "scope": "core-server-persistence",
                    "session_id": "a" * 32, "starts_at": 1000, "expires_at": 8200,
                    "environment_lifecycle": {"mode": "temporary", "data_retention": "discard", "max_duration_seconds": 7200}}
        cls.plan = preparation.load_session_plan(cls.root, document["target"], document["scope"], document, 1000, 7200)
        cls.binding_source = yaml.safe_load((cls.root / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/10-workload-binding/workload-binding.yml").read_text())

    def fixture(self, workload, *, renamed=False):
        s = self.shared; plan = self.plan; views = {}
        for index, component in enumerate(("foundation", "core-server-persistence")):
            stack = dict(plan["stack_names"])[component]; reference = dict(plan["stack_templates"])[stack]
            template = json.loads(dict(plan["projected_templates"])[reference])
            parameters = {name: str(row.get("Default", "fixture")) for name, row in template["Parameters"].items()}
            parameters.update({name: value for name, value in {
                "VpcId": "vpc-" + "1" * 17, "VpcCidr": "10.0.0.0/16", "PrivateSubnetIds": "subnet-" + "2" * 17,
                "ClusterArn": "arn:aws:ecs:eu-west-1:337159794548:cluster/checked-session",
                "LogGroupName": "/checked/session", "ImageRepositoryArn": "arn:aws:ecr:eu-west-1:337159794548:repository/fixture",
                "ImageRepositoryUri": "337159794548.dkr.ecr.eu-west-1.amazonaws.com/fixture",
                "ImageDigest": "sha256:" + "a" * 64, "SupportImageDigest": "sha256:" + "a" * 64,
                "RestoreVerifierImageDigest": "sha256:" + "a" * 64, "SourceRevision": "a" * 40,
                "S3ArtifactPrefixListId": "pl-" + "3" * 17}.items() if name in parameters})
            parameters.update(dict(dict(plan["creation_parameters"])[reference]))
            resources = {}
            for number, (name, row) in enumerate(template["Resources"].items(), 1):
                kind = row["Type"]; physical = "owned-" + str(index) + "-" + str(number)
                if kind == "AWS::EC2::SecurityGroup": physical = "sg-" + format(index * 100 + number, "017x")
                resources[name] = {"type": kind, "physical_id": physical}
            for name, row in template["Resources"].items():
                properties = row.get("Properties", {}); kind = row["Type"]
                if kind in ("AWS::ECS::TaskDefinition", "AWS::IAM::Role", "AWS::RDS::DBInstance", "AWS::SecretsManager::Secret"):
                    field = {"AWS::ECS::TaskDefinition": "Family", "AWS::IAM::Role": "RoleName", "AWS::RDS::DBInstance": "DBInstanceIdentifier", "AWS::SecretsManager::Secret": "Name"}[kind]
                    identity = s.runtime_resolve(properties[field], parameters, resources, workload, account=self.owner.ACCOUNT, region=self.owner.REGION)
                    if kind == "AWS::ECS::TaskDefinition": identity = "arn:aws:ecs:eu-west-1:337159794548:task-definition/" + identity + ":7"
                    if kind == "AWS::SecretsManager::Secret": identity = "arn:aws:secretsmanager:eu-west-1:337159794548:secret:" + identity + "-Ab1234"
                    resources[name]["physical_id"] = identity
            views[component] = {"schema": "deploy/aws-session-runtime-view/v1", "binding": {"target": "kanbien-core-platform", "scope": "core-server-persistence",
                "session_id": "a" * 32, "source_inputs_sha256": plan["binding"].source_inputs_sha256, "starts_at": 1000, "expires_at": 8200},
                "source_plan_sha256": "b" * 64, "account": self.owner.ACCOUNT, "region": self.owner.REGION, "component": component,
                "stack": stack, "stack_id": "arn:aws:cloudformation:eu-west-1:337159794548:stack/" + stack + "/" + "a" * 36,
                "phase": "creation", "template_reference": reference, "template": template, "parameters": parameters, "resources": resources, "outputs": {},
                "custody": {name: "c" * 64 for name in ("creation_request_sha256", "change_set_id_sha256", "template_sha256", "parameters_sha256", "resources_sha256")}, "observed_at": 1000}
        foundation, view = views["foundation"], views["core-server-persistence"]
        for parameter, resource in (("VerifierSecurityGroupId", "VerifierSecurityGroup"), ("EndpointSecurityGroupId", "EndpointSecurityGroup")):
            view["parameters"][parameter] = foundation["resources"][resource]["physical_id"]
            foundation["outputs"][parameter] = view["parameters"][parameter]
        binding = copy.deepcopy(self.binding_source)
        if renamed:
            row = next(row for row in binding["workloads"] if row["id"] == workload)
            old, new = row["provider_reference"], "RenamedSelectedDefinition"
            view["template"]["Resources"][new] = view["template"]["Resources"].pop(old)
            view["resources"][new] = view["resources"].pop(old)
            view["template"] = json.loads(json.dumps(view["template"]).replace('"' + old + '"', '"' + new + '"'))
            row["provider_reference"] = new
            group = row["security_group"]; owner = views[group["component"]]; old, new = group["resource"], "RenamedSelectedGroup"
            owner["template"] = json.loads(json.dumps(owner["template"]).replace('"' + old + '"', '"' + new + '"'))
            owner["resources"][new] = owner["resources"].pop(old); group["resource"] = new
        database = view["resources"]["PersistenceDatabase"]["physical_id"]
        state = {"calls": [], "database": {"DBInstanceIdentifier": database, "DBInstanceArn": "arn:aws:rds:eu-west-1:337159794548:db:" + database,
                 "DBInstanceStatus": "available", "Endpoint": {"Address": "owned.checked.rds.amazonaws.com", "Port": 5432}, "DbiResourceId": "db-" + "A" * 26},
                 "tasks": {}, "tags": {}, "roles": {}, "policies": {}, "groups": {}, "secrets": {}}
        attributes = {("PersistenceDatabase", "Endpoint.Address"): state["database"]["Endpoint"]["Address"],
                      ("PersistenceDatabase", "Endpoint.Port"): "5432", ("PersistenceDatabase", "DbiResourceId"): state["database"]["DbiResourceId"]}
        view["outputs"].update(PersistenceDatabaseEndpoint=attributes[("PersistenceDatabase", "Endpoint.Address")], PersistenceDatabaseResourceId=attributes[("PersistenceDatabase", "DbiResourceId")])
        def resolved(value, selected=view):
            return s.runtime_resolve(value, selected["parameters"], selected["resources"], workload, account=self.owner.ACCOUNT, region=self.owner.REGION, _attributes=attributes)
        def permission(row):
            result = {"IpProtocol": str(row["IpProtocol"]), "FromPort": row["FromPort"], "ToPort": row["ToPort"], "IpRanges": [], "Ipv6Ranges": [], "UserIdGroupPairs": [], "PrefixListIds": []}
            for key, collection, field in (("SourceSecurityGroupId", "UserIdGroupPairs", "GroupId"), ("DestinationSecurityGroupId", "UserIdGroupPairs", "GroupId"),
                    ("CidrIp", "IpRanges", "CidrIp"), ("DestinationPrefixListId", "PrefixListIds", "PrefixListId")):
                if key in row: result[collection].append({field: row[key], **({"UserId": self.owner.ACCOUNT} if collection == "UserIdGroupPairs" else {})})
            return result
        selected_row = next(row for row in binding["workloads"] if row["id"] == workload)
        definition = selected_row["provider_reference"]
        properties = view["template"]["Resources"][definition]["Properties"]
        task = s.runtime_expected_task(definition, workload, view["parameters"], view["resources"], view["template"], account=self.owner.ACCOUNT, region=self.owner.REGION, _attributes=attributes)
        arn = view["resources"][definition]["physical_id"]
        state["tags"][arn] = task.pop("tags")
        task.update(taskDefinitionArn=arn, status="ACTIVE", revision=7, compatibilities=["FARGATE"])
        state["tasks"][arn] = task
        for field in ("ExecutionRoleArn", "TaskRoleArn"):
            if field not in properties: continue
            logical = properties[field]["Fn::GetAtt"][0]; name = view["resources"][logical]["physical_id"]
            expected = resolved(view["template"]["Resources"][logical]["Properties"])
            state["roles"][name] = {"RoleName": name, "Arn": "arn:aws:iam::337159794548:role/" + name, "Path": "/", "AssumeRolePolicyDocument": expected["AssumeRolePolicyDocument"]}
            state["policies"][name] = {row["PolicyName"]: row["PolicyDocument"] for row in expected.get("Policies", [])}
        for name, row in view["template"]["Resources"].items():
            if row["Type"] == "AWS::SecretsManager::Secret":
                identity = view["resources"][name]["physical_id"]
                state["secrets"][identity] = {"ARN": identity, "Name": resolved(row["Properties"]["Name"])}
        for selected in views.values():
            for name, row in selected["template"]["Resources"].items():
                if row["Type"] != "AWS::EC2::SecurityGroup": continue
                identity = selected["resources"][name]["physical_id"]; properties = resolved(row["Properties"], selected)
                state["groups"][identity] = {"GroupId": identity, "OwnerId": self.owner.ACCOUNT, "VpcId": selected["parameters"]["VpcId"],
                    "IpPermissions": [permission(rule) for rule in properties.get("SecurityGroupIngress", [])],
                    "IpPermissionsEgress": [permission(rule) for rule in properties.get("SecurityGroupEgress", [])]}
        for selected in views.values():
            for row in selected["template"]["Resources"].values():
                if row["Type"] not in ("AWS::EC2::SecurityGroupIngress", "AWS::EC2::SecurityGroupEgress"): continue
                rule = resolved(row["Properties"], selected)
                state["groups"][rule["GroupId"]]["IpPermissions" if row["Type"].endswith("Ingress") else "IpPermissionsEgress"].append(permission(rule))
        class Provider:
            def __bool__(self): return False
            def __call__(self, service, operation, **arguments):
                state["calls"].append((service, operation, arguments))
                if operation == "describe-db-instances": return {"DBInstances": [copy.deepcopy(state["database"])]}
                if operation == "describe-secret": return copy.deepcopy(state["secrets"][arguments["SecretId"]])
                if operation == "describe-task-definition":
                    assert arguments["include"] == ["TAGS"]
                    return {"taskDefinition": copy.deepcopy(state["tasks"][arguments["taskDefinition"]]), "tags": copy.deepcopy(state["tags"][arguments["taskDefinition"]])}
                if operation == "describe-security-groups": return {"SecurityGroups": [copy.deepcopy(state["groups"][name]) for name in arguments["GroupIds"]]}
                if operation == "get-role": return {"Role": copy.deepcopy(state["roles"][arguments["RoleName"]])}
                if operation == "list-role-policies": return {"PolicyNames": list(state["policies"][arguments["RoleName"]]), "IsTruncated": False}
                if operation == "list-attached-role-policies": return {"AttachedPolicies": [], "IsTruncated": False}
                if operation == "get-role-policy": return {**arguments, "PolicyDocument": copy.deepcopy(state["policies"][arguments["RoleName"]][arguments["PolicyName"]])}
                raise AssertionError(CANARY)
        return view, foundation, binding, Provider(), state

    def invoke(self, fixture, workload):
        view, foundation, binding, provider, _ = fixture
        return self.owner.checked_runtime(provider, view=view, workload_binding=binding, workload=workload, related_views=(foundation,))

    def rejected(self, fixture, workload, code):
        try: self.invoke(fixture, workload)
        except Exception as failure:
            self.assertEqual(getattr(failure, "code", None), code)
            self.assertNotIn(CANARY, str(failure)); self.assertNotIn(CANARY, repr(vars(failure)))
        else: self.fail("unchecked runtime binding accepted")

    def test_actual_source_three_consumers_and_renamed_logical_selection(self):
        for workload in ("persistence-migration-task", "persistence-administration-task", "private-release-verifier-task"):
            for renamed in (False, True):
                fixture = self.fixture(workload, renamed=renamed); result = self.invoke(fixture, workload)
                view, foundation, binding, _, state = fixture
                row = next(row for row in binding["workloads"] if row["id"] == workload)
                self.assertEqual(result["definition"], view["resources"][row["provider_reference"]]["physical_id"])
                self.assertEqual(result["security_group"], (foundation if row["security_group"]["component"] == "foundation" else view)["resources"][row["security_group"]["resource"]]["physical_id"])
                self.assertEqual(result["runtime"]["schema"], "deploy/aws-task-runtime/v1")
                self.assertEqual(result["runtime"]["cluster_arn"], view["parameters"]["ClusterArn"])
                self.assertNotIn("secret:", json.dumps(result)); self.assertNotIn("owned.checked.rds", json.dumps(result))
                self.assertTrue(any(operation == "get-role-policy" for _, operation, _ in state["calls"]))
                self.assertEqual(any(operation == "describe-secret" for _, operation, _ in state["calls"]), workload == "persistence-administration-task")

    def test_foreign_view_and_group_selection_fail_before_provider(self):
        for mutation in ("session", "plan", "group-output", "group-parameter", "definition", "association"):
            fixture = self.fixture("private-release-verifier-task"); view, foundation, binding, _, state = fixture
            if mutation == "session": foundation["binding"]["session_id"] = "b" * 32
            if mutation == "plan": foundation["source_plan_sha256"] = "c" * 64
            if mutation == "group-output": foundation["outputs"]["VerifierSecurityGroupId"] = "sg-" + "f" * 17
            if mutation == "group-parameter": view["parameters"]["VerifierSecurityGroupId"] = "sg-" + "f" * 17
            row = next(row for row in binding["workloads"] if row["id"] == "private-release-verifier-task")
            if mutation == "definition": row["provider_reference"] = "PersistenceDatabase"
            if mutation == "association": row["security_group"]["parameter"] = "EndpointSecurityGroupId"
            self.rejected(fixture, row["id"], "runtime-binding-invalid" if mutation in ("session", "plan") else
                          "task-binding-resources-not-confirmed" if mutation.startswith("group-") else "task-binding-selection-invalid")
            self.assertEqual(state["calls"], [])

    def test_native_database_secret_task_policy_and_network_counterexamples(self):
        for mutation in ("db-identity", "db-resource", "db-endpoint", "db-port", "secret", "revision", "tags", "logging", "policy", "boundary", "egress"):
            fixture = self.fixture("persistence-administration-task"); view, _, binding, _, state = fixture
            task = next(iter(state["tasks"].values()))
            code = "task-binding-resources-not-confirmed"
            if mutation == "db-identity": state["database"]["DBInstanceArn"] += "-foreign"
            if mutation == "db-resource": state["database"]["DbiResourceId"] = "db-" + "B" * 26
            if mutation == "db-endpoint": state["database"]["Endpoint"]["Address"] = "foreign.rds.amazonaws.com"
            if mutation == "db-port": state["database"]["Endpoint"]["Port"] = True
            if mutation == "secret": next(iter(state["secrets"].values()))["ARN"] += "-foreign"
            if mutation == "revision": task["revision"] = 8; code = "task-binding-definition-not-confirmed"
            if mutation == "tags": next(iter(state["tags"].values()))[0]["value"] = "foreign"; code = "task-binding-definition-not-confirmed"
            if mutation == "logging": task["containerDefinitions"][0]["logConfiguration"]["options"]["awslogs-group"] = "/foreign"; code = "task-binding-container-not-confirmed"
            if mutation == "policy": next(iter(next(iter(state["policies"].values())).values()))["Statement"][0]["Action"] = "*"; code = "task-binding-policy-not-confirmed"
            if mutation == "boundary": next(iter(state["roles"].values()))["PermissionsBoundary"] = {}; code = "task-binding-role-not-confirmed"
            if mutation == "egress":
                group = view["resources"]["AdministrationSecurityGroup"]["physical_id"]
                state["groups"][group]["IpPermissionsEgress"].append({"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]})
                code = "task-binding-network-not-confirmed"
            self.rejected(fixture, "persistence-administration-task", code)

    def test_source_role_authority_is_not_satisfied_by_observed_absence(self):
        for field, value in (("PermissionsBoundary", "arn:aws:iam::337159794548:policy/declared"), ("ManagedPolicyArns", []), ("RoleName", "different-owned-role")):
            fixture = self.fixture("persistence-migration-task"); view, _, _, _, state = fixture
            view["template"]["Resources"]["MigrationExecutionRole"]["Properties"][field] = value
            self.assertNotIn("PermissionsBoundary", next(iter(state["roles"].values())))
            self.rejected(fixture, "persistence-migration-task", "task-binding-role-not-confirmed" if field == "RoleName" else "task-binding-source-not-supported")
            self.assertFalse(any(operation == "get-role" for _, operation, _ in state["calls"]))

    def test_task_tag_shape_reports_definition_identity_not_container_failure(self):
        workload = "persistence-administration-task"
        for mutation in ("missing", "null", "wrong-type", "wrong-key", "duplicate", "empty"):
            with self.subTest(mutation=mutation):
                view, foundation, binding, native, state = self.fixture(workload)
                def provider(service, operation, **arguments):
                    response = native(service, operation, **arguments)
                    if operation == "describe-task-definition":
                        if mutation == "missing": response.pop("tags")
                        if mutation == "null": response["tags"] = None
                        if mutation == "wrong-type": response["tags"] = {"unsafe": CANARY}
                        if mutation == "wrong-key": response["tags"] = [{"key": None, "value": CANARY}]
                        if mutation == "duplicate": response["tags"].append(copy.deepcopy(response["tags"][0]))
                        if mutation == "empty": response["tags"] = []
                    return response
                try: self.invoke((view, foundation, binding, provider, state), workload)
                except Exception as failure:
                    self.assertEqual((getattr(failure, "code", None), getattr(failure, "workload", None),
                                      getattr(failure, "field", None), getattr(failure, "item", None)),
                                     ("task-binding-definition-not-confirmed", workload, "identity", "identity"))
                    self.assertNotIn(CANARY, str(failure) + repr(vars(failure)))
                else: self.fail("invalid task tags accepted")
                self.assertFalse(any(operation == "get-role" for _, operation, _ in state["calls"]))
        with self.assertRaises(self.shared.BindingFailure) as raised:
            self.shared.sorted_entries([{"name": "same"}, {"name": "same"}], "name", "migration")
        self.assertEqual((raised.exception.code, raised.exception.workload, raised.exception.field, raised.exception.item),
                         ("task-binding-container-not-confirmed", "migration", "container", "container"))


if __name__ == "__main__": unittest.main(verbosity=2)
