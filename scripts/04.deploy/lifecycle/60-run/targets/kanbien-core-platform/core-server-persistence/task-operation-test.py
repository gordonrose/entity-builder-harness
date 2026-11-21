#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-persistence.task-operations
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-15"
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
                    "lastStatus": "PENDING", "startedAt": "2026-11-15T00:00:00Z", "stoppedAt": "2026-11-15T00:00:01Z",
                    "containers": [{"name": "persistence-" + self.kind, "exitCode": self.exit_code}]}
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
            return True, {"taskDefinition": {"containerDefinitions": [{"image": "fixture/image@sha256:" + "a"*64}]}}, "ok"
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


if __name__ == "__main__": unittest.main(verbosity=2)
