#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.connected-controlled-workload
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Connect an isolated renamed package and migration to shared deployment operations and retained proof identity without Docker or AWS.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.prepare-runtime-payload.wrapper
#     path: scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/script.sh
"""Controlled reuse, not PostgreSQL execution, image qualification or live proof.

The provider double executes the real assembled program. Its database adapter
models only this fixture's three SQL statements; it cannot qualify PostgreSQL.
The candidate constructor is exercised in memory, never accepted or published.
"""
import copy
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

if not __debug__: raise SystemExit("CONNECTED_WORKLOAD_ASSERTIONS_DISABLED")

ROOT = Path(__file__).resolve().parents[5]
AWS = ROOT / "scripts/04.deploy/shared/provider-adapters/aws"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


RESERVATIONS = module("connected_reservations", AWS / "resource_reservation.py")
CHANGES = module("connected_changes", AWS / "change_sets.py")
TASKS = module("connected_tasks", AWS / "tasks.py")
SNAPSHOTS = module("connected_snapshots", AWS / "snapshots.py")
SUCCESSION = module("connected_succession", ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py")
NAME = "ledger-probe"
DEFINITION = "arn:aws:ecs:eu-west-1:000000000000:task-definition/ledger-probe-worker:1"
NETWORK = {"awsvpcConfiguration": {"subnets": ["subnet-fixture-private"], "securityGroups": ["sg-ledger-probe"], "assignPublicIp": "DISABLED"}}
SQL = "CREATE TABLE ledger_probe (id uuid PRIMARY KEY, amount integer NOT NULL);"

PROGRAM = r'''
const fs = require('node:fs');
const assert = require('node:assert/strict');
const migration = require('./migration.json');
exports.run = () => {
  const file = process.env.CONTROLLED_DATABASE;
  const state = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file)) : {schema: null, records: {}, writes: 0};
  // Explicit finite SQL double, not a PostgreSQL parser or database adapter.
  function query(sql, parameters = []) {
    if (sql === 'CREATE TABLE ledger_probe (id uuid PRIMARY KEY, amount integer NOT NULL);') {
      assert.equal(state.schema, null); state.schema = 'ledger_probe'; return;
    }
    assert.equal(state.schema, 'ledger_probe');
    if (sql === 'INSERT INTO ledger_probe(id, amount) VALUES ($1, $2)') {
      assert.equal(state.records[parameters[0]], undefined); assert.equal(Number.isInteger(parameters[1]), true);
      state.records[parameters[0]] = parameters[1]; state.writes++; return;
    }
    assert.equal(sql, 'SELECT amount FROM ledger_probe WHERE id = $1');
    return state.records[parameters[0]];
  }
  const operation = process.env.LEDGER_OPERATION;
  const id = '12345678-1234-4234-8234-123456789abc';
  if (operation === 'migration') query(migration.sql);
  else if (operation === 'write') query('INSERT INTO ledger_probe(id, amount) VALUES ($1, $2)', [id, 17]);
  else { assert.equal(operation, 'read'); assert.equal(query('SELECT amount FROM ledger_probe WHERE id = $1', [id]), 17); assert.equal(state.writes, 1); }
  fs.writeFileSync(file, JSON.stringify(state));
  console.log(JSON.stringify({workload: 'ledger-probe', operation, schema: state.schema, writes: state.writes,
    sql_sha256: require('node:crypto').createHash('sha256').update(migration.sql).digest('hex')}));
};
'''


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class Store(RESERVATIONS.ImmutableReservationStore):
    schema = "controlled/ledger-probe-intent/v1"
    operation_prefix = "lp-"

    def path_for(self, phase, request):
        if phase not in {"prepare", "execute", "migration", "write", "read", "snapshot"} or set(request) != {"workload", "image_digest", "definition", "migration_sha256"} or request["workload"] != NAME or request["definition"] != DEFINITION:
            raise self.failure("fixture-binding-invalid")
        for key in ("image_digest", "migration_sha256"):
            SUCCESSION.sha(request[key])
        return self.root / (phase + ".json")

    def validate_time(self, value):
        if datetime.fromisoformat(value).tzinfo is None:
            raise self.failure("fixture-time-invalid")


class Workload:
    def __init__(self, directory):
        self.root = Path(directory)
        self.payload = self.root / "isolated-payload"
        source = self.payload / "apps/ledger-probe"
        source.mkdir(parents=True)
        (source / "index.js").write_text(PROGRAM)
        (source / "migration.json").write_text(json.dumps({"sql": SQL}))
        self.database = self.root / "controlled-database.json"
        self.calls, self.tasks, self.proofs = [], [], []
        self.change = self.stack = self.snapshot = None
        self.lose_write = False
        self.store = Store(self.root / "reservations")

    def assemble(self):
        assembler = (ROOT / "scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/assemble.mjs").as_uri()
        binding = {"compiledRoot": str(self.payload), "packages": {"@fixture/ledger-probe": {".": "apps/ledger-probe/index.js", "./migration.json": "apps/ledger-probe/migration.json"}},
            "entrypoints": [{"target": "apps/ledger-probe/index.js", "output": "ledger-probe.js", "source": "require('@fixture/ledger-probe').run();\n"}],
            "manifest": {"path": "ledger-probe-payload.json", "newline": True}}
        source = "import { assembleRuntimePayload } from " + json.dumps(assembler) + "; assembleRuntimePayload(" + json.dumps(binding) + ", {});"
        subprocess.run(["node", "--input-type=module", "-e", source], check=True, capture_output=True, text=True, timeout=15)
        self.image = self.package_digest()  # Controlled package identity, not an OCI digest receipt.
        self.request = {"workload": NAME, "image_digest": self.image, "definition": DEFINITION, "migration_sha256": digest(SQL.encode())}

    def package_digest(self):
        entries = {str(file.relative_to(self.payload)): digest(file.read_bytes()) for file in sorted(self.payload.rglob('*')) if file.is_file()}
        return digest(RESERVATIONS.canonical(entries))

    def provider(self, service, operation, **parameters):
        self.calls.append((service, operation, copy.deepcopy(parameters)))
        if service == "cloudformation":
            assert parameters["StackName"] == "ledger-probe-private"
            if operation == "create-change-set":
                reservation = self.store.read("prepare", self.request)
                assert parameters["ClientToken"] == parameters["Description"] == reservation["operation_id"]
                self.change = {"stack": parameters["StackName"], "image": self.image, "token": reservation["operation_id"]}
            else:
                assert operation == "execute-change-set" and self.change is not None
                assert parameters["ClientRequestToken"] == self.store.read("execute", self.request)["operation_id"]
                self.stack = {"definition": DEFINITION, "image": self.image, "network": NETWORK}
            return {}
        if service == "rds":
            assert operation == "create-db-snapshot" and parameters["DBInstanceIdentifier"] == "ledger-probe-db"
            assert parameters["DBSnapshotIdentifier"] == "ledger-probe-point"
            assert parameters["Tags"] == [{"Key": "Operation", "Value": self.store.read("snapshot", self.request)["operation_id"]}]
            self.snapshot = {"source": parameters["DBInstanceIdentifier"], "state": json.loads(self.database.read_text())}
            return {}
        assert service == "ecs" and parameters["cluster"] == "controlled-private-cluster"
        if operation == "run-task":
            assert self.stack is not None and self.package_digest() == self.image
            assert parameters["taskDefinition"] == DEFINITION and parameters["networkConfiguration"] == NETWORK
            assert parameters["count"] == 1 and parameters["launchType"] == "FARGATE"
            container = parameters["overrides"]["containerOverrides"][0]
            mode = container["environment"][0]["value"]
            assert container == {"name": NAME, "environment": [{"name": "LEDGER_OPERATION", "value": mode}]}
            reservation = self.store.read(mode, self.request)
            assert parameters["startedBy"] == parameters["clientToken"] == reservation["operation_id"]
            result = subprocess.run(["node", "ledger-probe.js"], cwd=self.payload, text=True, capture_output=True, timeout=15,
                env={**os.environ, "NODE_PATH": "", "NODE_OPTIONS": "", "LEDGER_OPERATION": mode, "CONTROLLED_DATABASE": str(self.database)})
            task = {"taskArn": "arn:controlled:task/" + reservation["operation_id"], "taskDefinitionArn": DEFINITION,
                "startedBy": reservation["operation_id"], "overrides": parameters["overrides"], "lastStatus": "STOPPED",
                "containers": [{"name": NAME, "imageDigest": self.image, "exitCode": result.returncode}], "stdout": result.stdout}
            self.tasks.append(task)
            if self.lose_write and mode == "write": raise TimeoutError("controlled-lost-response")
            return {"tasks": [copy.deepcopy(task)]}
        if operation == "list-tasks":
            assert parameters["family"] == "ledger-probe-worker"
            return {"taskArns": [task["taskArn"] for task in self.tasks] if parameters["desiredStatus"] == "STOPPED" else []}
        assert operation == "describe-tasks"
        return {"tasks": [copy.deepcopy(task) for task in self.tasks if task["taskArn"] in parameters["tasks"]]}

    def deploy(self):
        def absent(_): assert self.change is None
        CHANGES.prepare(self.provider, self.store, phase="prepare", request=self.request,
            arguments={"StackName": "ledger-probe-private", "ChangeSetName": "ledger-probe-create", "ChangeSetType": "CREATE", "Capabilities": ["CAPABILITY_IAM"]},
            precondition=absent, observe=lambda reservation: self.change)
        CHANGES.execute(self.provider, self.store, phase="execute", request=self.request,
            arguments={"StackName": "ledger-probe-private", "ChangeSetName": "ledger-probe-create"},
            precondition=lambda reservation: self.require(self.change["image"] == self.image), observe=lambda reservation: self.stack)

    @staticmethod
    def require(condition):
        if not condition: raise ValueError("controlled-binding-not-confirmed")

    def task(self, mode):
        self.require(self.package_digest() == self.image)
        reservation, fresh = self.store.reserve(mode, self.request)
        overrides = {"containerOverrides": [{"name": NAME, "environment": [{"name": "LEDGER_OPERATION", "value": mode}]}]}
        def validate(task):
            self.require(task["taskDefinitionArn"] == DEFINITION and task["startedBy"] == reservation["operation_id"] and task["overrides"] == overrides)
            self.require(task["containers"] == [{"name": NAME, "imageDigest": self.image, "exitCode": 0}])
            result = json.loads(task["stdout"])
            self.require(result["workload"] == NAME and result["operation"] == mode and result["sql_sha256"] == digest(SQL.encode())[7:])
            return task
        if fresh:
            task = TASKS.submit_task(self.provider, cluster="controlled-private-cluster", definition=DEFINITION,
                operation_id=reservation["operation_id"], network=NETWORK, overrides=overrides, validate_task=validate)
        else:
            task = TASKS.reconcile_task(self.provider, cluster="controlled-private-cluster", definition=DEFINITION,
                operation_id=reservation["operation_id"], validate_task=validate)
        proof = {"reservation": reservation, "task": task, "package_sha256": self.image}
        self.proofs.append(proof)
        return proof

    def recovery_point(self):
        return SNAPSHOTS.create(self.provider, self.store, phase="snapshot", request=self.request,
            arguments=lambda reservation: {"DBInstanceIdentifier": "ledger-probe-db", "DBSnapshotIdentifier": "ledger-probe-point", "Tags": [{"Key": "Operation", "Value": reservation["operation_id"]}]},
            precondition=lambda reservation: self.require(self.snapshot is None), validate_reservation=lambda reservation: self.require(reservation["request"] == self.request),
            observe=lambda reservation, fresh: self.snapshot)


class ConnectedWorkloadTests(unittest.TestCase):
    def test_package_migration_task_recovery_and_candidate_are_connected(self):
        with tempfile.TemporaryDirectory(prefix="connected-ledger-probe-") as directory:
            workload = Workload(directory); workload.assemble(); workload.deploy()
            migration = workload.task("migration")
            self.assertEqual(json.loads(migration["task"]["stdout"])["schema"], "ledger_probe")
            workload.lose_write = True
            with self.assertRaises(TASKS.TaskFailure): workload.task("write")
            written = workload.task("write")  # Reconcile the executed program; never execute INSERT twice.
            readback = workload.task("read")
            point = workload.recovery_point()
            self.assertEqual(point["state"]["writes"], 1)
            self.assertEqual(json.loads(readback["task"]["stdout"])["writes"], 1)
            workload.deploy(); workload.recovery_point(); workload.task("read")
            self.assertEqual([op for _, op, _ in workload.calls].count("run-task"), 3)
            self.assertEqual([op for _, op, _ in workload.calls].count("create-change-set"), 1)
            self.assertEqual([op for _, op, _ in workload.calls].count("execute-change-set"), 1)
            self.assertEqual([op for _, op, _ in workload.calls].count("create-db-snapshot"), 1)
            proof = {"evidence_class": "controlled-fixture-not-live", "migration": migration, "write": written, "read": readback, "snapshot": point}
            proof_file = workload.root / "proof-receipts/ledger-probe.json"
            self.assertTrue(RESERVATIONS.write_exclusive(proof_file, proof))
            candidate = SUCCESSION.candidate_document(target="controlled-private-cluster", scope=NAME, source_revision="a" * 40,
                image_digest=workload.image, configuration_contract={"path": "controlled-config.yml", "sha256": digest(RESERVATIONS.canonical(NETWORK))},
                permission_contract={"path": "controlled-permissions.yml", "sha256": digest(b"fixture-private-only")},
                proofs={"ledger-probe": {"path": "proof-receipts/ledger-probe.json", "sha256": digest(proof_file.read_bytes())}}, accepted_at="2026-11-15T00:00:00Z")
            self.assertEqual(SUCCESSION.candidate_identity(candidate, workload.root, current_contracts=False)[:3], ("controlled-private-cluster", NAME, workload.image))
            # Pure envelope construction is NOT promotion or validation of live evidence.
            self.assertFalse((workload.root / "release-candidates").exists())
            altered = copy.deepcopy(candidate); altered["release"]["image_digest"] = "sha256:" + "f" * 64
            with self.assertRaises(SUCCESSION.SuccessionFailure): SUCCESSION.candidate_identity(altered)
            proof_file.write_text('{}')
            with self.assertRaises(SUCCESSION.SuccessionFailure): SUCCESSION.candidate_identity(candidate, workload.root, current_contracts=False)
            workload.tasks[-1]["taskDefinitionArn"] = DEFINITION[:-1] + "2"
            with self.assertRaises(ValueError): workload.task("read")
            (workload.payload / "apps/ledger-probe/index.js").write_text(PROGRAM + "\n// altered\n")
            with self.assertRaises(ValueError): workload.task("read")

    def test_missing_package_and_failed_program_cannot_make_proof(self):
        with tempfile.TemporaryDirectory(prefix="connected-ledger-negative-") as directory:
            workload = Workload(directory)
            path = workload.payload / "apps/ledger-probe/index.js"
            path.unlink()
            with self.assertRaises(subprocess.CalledProcessError): workload.assemble()
            self.assertEqual(workload.calls, [])
            path.write_text(PROGRAM); workload.assemble(); workload.deploy()
            with self.assertRaises(ValueError): workload.task("read")  # Real program rejects missing migration.
            self.assertEqual(workload.proofs, [])
            self.assertEqual(workload.tasks[-1]["containers"][0]["exitCode"], 1)


if __name__ == "__main__": unittest.main()
