#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.resource-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject replay, wrong ownership, premature stopped-state claims and snapshots not bound to the original record and dependency incarnation.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
from datetime import datetime, timedelta, timezone
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

if not __debug__: raise SystemExit("ENTITY_SMOKE_RESOURCE_CONTROL_ASSERTIONS_DISABLED")
SPEC = importlib.util.spec_from_file_location("entity_smoke_resource_control_test", Path(__file__).with_name("resource-control.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
CANARY = "credential-row-provider-canary"
PREFIX = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/"
ORIGINAL, SUCCESSOR = PREFIX + "1" * 32, PREFIX + "2" * 32
DEFINITION = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-server:1"
RESOURCE_ID = "db-ABCDEFGHIJKLMNOP"
base = datetime.now(timezone.utc)
instant = lambda seconds: (base + timedelta(seconds=seconds)).isoformat()
BINDING = {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64,
           "configuration_contract_sha256": "sha256:" + "c" * 64, "permission_contract_sha256": "sha256:" + "d" * 64,
           "dependency_incarnation_sha256": "sha256:" + hashlib.sha256(M.CONTROL.canonical({"resource_id": RESOURCE_ID, "database": "kanbienpersistence", "schema": "entity_smoke"})).hexdigest(),
           "proof_label": "entity-smoke-" + "e" * 24, "record_digest": "f" * 64}


class Provider:
    def __init__(self, lost=False, delayed=False):
        self.calls, self.lost, self.delayed = [], lost, delayed
        self.desired, self.running = 1, 1
        self.original_status, self.successor = "RUNNING", False
        self.current = [ORIGINAL]
        self.snapshot = None
        self.stray = False
        self.paginated = False
        self.wrong_image = False
        self.starting = False
        self.wrong_snapshot_source = False
        self.stop_reason = None
        self.tags = [{"Key": "Target", "Value": M.CLUSTER}, {"Key": "Scope", "Value": "entity-smoke"}, {"Key": "ProofLabel", "Value": BINDING["proof_label"]}, {"Key": "aws:cloudformation:stack-name", "Value": "owned-source-stack"}]
    def __call__(self, service_name, operation, **parameters):
        self.calls.append((service_name, operation, copy.deepcopy(parameters)))
        if operation == "describe-services":
            assert parameters == {"cluster": M.CLUSTER, "services": [M.SERVICE]}
            return {"services": [{"serviceName": M.SERVICE, "clusterArn": "arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-core-platform", "taskDefinition": DEFINITION, "status": "ACTIVE", "desiredCount": self.desired, "runningCount": self.running, "pendingCount": 0}]}
        if operation == "list-tasks":
            assert parameters["cluster"] == M.CLUSTER
            if "family" in parameters:
                arns = [PREFIX + "3" * 32] if self.stray and parameters["family"].endswith("-migration") and parameters["desiredStatus"] == "STOPPED" else []
                return {"taskArns": arns, **({"nextToken": CANARY} if self.paginated else {})}
            assert parameters["serviceName"] == M.SERVICE and parameters["desiredStatus"] == "RUNNING"
            return {"taskArns": list(self.current)}
        if operation == "describe-tasks":
            tasks = []
            for arn in parameters["tasks"]:
                if arn == PREFIX + "3" * 32:
                    tasks.append({"taskArn": arn, "taskDefinitionArn": DEFINITION.replace("-server:", "-migration:"), "lastStatus": "STOPPING"}); continue
                assert arn in {ORIGINAL, SUCCESSOR}
                tasks.append({"taskArn": arn, "taskDefinitionArn": DEFINITION, "group": "service:" + M.SERVICE,
                              "launchType": "FARGATE", "lastStatus": self.original_status if arn == ORIGINAL else "RUNNING", "healthStatus": "HEALTHY",
                              "createdAt": instant(-30) if arn == ORIGINAL else instant(10), "startedAt": instant(-29) if arn == ORIGINAL else instant(11),
                              "stoppedAt": instant(9), "stoppedReason": self.stop_reason, "containers": [{"name": "entity-smoke-server", "imageDigest": "sha256:" + "0" * 64 if self.wrong_image else BINDING["image_digest"]}]})
                if arn == SUCCESSOR and self.starting:
                    tasks[-1]["lastStatus"] = "PENDING"
                    tasks[-1]["containers"][0].pop("imageDigest")
            return {"tasks": tasks}
        if operation == "stop-task":
            assert parameters["cluster"] == M.CLUSTER and parameters["task"] == ORIGINAL and parameters["reason"].startswith("es-")
            self.stop_reason = parameters["reason"]
            self.original_status = "STOPPING" if self.delayed else "STOPPED"
            self.current = [ORIGINAL] if self.delayed else [SUCCESSOR]
            if self.lost: raise OSError(CANARY)
            return {}
        if operation == "update-service":
            assert parameters["cluster"] == M.CLUSTER and parameters["service"] == M.SERVICE and parameters["desiredCount"] in {0, 1}
            self.desired = parameters["desiredCount"]
            self.running = self.desired
            self.current = [SUCCESSOR] if self.desired else []
            self.original_status = "STOPPING" if self.delayed else "STOPPED"
            if self.lost: raise OSError(CANARY)
            return {}
        if operation == "describe-db-instances":
            assert parameters == {"DBInstanceIdentifier": M.SOURCE_DATABASE}
            return {"DBInstances": [{"DBInstanceIdentifier": M.SOURCE_DATABASE, "DbiResourceId": RESOURCE_ID, "DBInstanceStatus": "available", "StorageEncrypted": True, "PubliclyAccessible": False, "DBName": "kanbienpersistence"}]}
        if operation == "describe-db-snapshots":
            assert parameters == {"DBSnapshotIdentifier": "kanbien-core-platform-" + BINDING["proof_label"]}
            if self.snapshot is None: raise M.ResourceMissing()
            value = copy.deepcopy(self.snapshot)
            if self.wrong_snapshot_source: value["DbiResourceId"] = "db-OTHERINCARNATION"
            return {"DBSnapshots": [value]}
        if operation == "create-db-snapshot":
            assert parameters["DBInstanceIdentifier"] == M.SOURCE_DATABASE and parameters["DBSnapshotIdentifier"] == "kanbien-core-platform-" + BINDING["proof_label"]
            name = parameters["DBSnapshotIdentifier"]
            self.snapshot = {"DBSnapshotIdentifier": name, "DBSnapshotArn": "arn:aws:rds:eu-west-1:337159794548:snapshot:" + name, "DBInstanceIdentifier": M.SOURCE_DATABASE,
                             "DbiResourceId": RESOURCE_ID, "Encrypted": True, "SnapshotType": "manual", "SnapshotCreateTime": instant(10), "Status": "creating" if self.delayed else "available"}
            if self.lost: raise OSError(CANARY)
            return {}
        assert (service_name, operation) == ("rds", "list-tags-for-resource")
        return {"TagList": copy.deepcopy(self.tags)}


def fails(call, code):
    try: call()
    except M.ResourceFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected resource-control rejection")


with tempfile.TemporaryDirectory(prefix="entity-smoke-resource-controls-") as temporary:
    root = Path(temporary)
    def store(name): return M.ResourceStore(root / name)
    provider = Provider(); owner = store("replacement")
    first = M.replace_runtime(provider, owner, BINDING, DEFINITION, ORIGINAL)
    assert first["status"] == "completed" and first["facts"]["successor_task"] == SUCCESSOR
    repeated = M.replace_runtime(provider, owner, BINDING, DEFINITION, ORIGINAL)
    assert repeated["reservation"] == first["reservation"]
    assert sum(op == "stop-task" for _, op, _ in provider.calls) == 1
    assert (root / "replacement" / (BINDING["proof_label"] + "-server-replacement.json")).stat().st_mode & 0o777 == 0o600
    changed = {**BINDING, "record_digest": "0" * 64}
    fails(lambda: M.replace_runtime(provider, owner, changed, DEFINITION, ORIGINAL), "resource-reservation-mismatch")
    assert sum(op == "stop-task" for _, op, _ in provider.calls) == 1
    lost = Provider(lost=True); owner = store("lost-replacement")
    fails(lambda: M.replace_runtime(lost, owner, BINDING, DEFINITION, ORIGINAL), "resource-submission-uncertain-reconcile-only")
    assert M.replace_runtime(lost, owner, BINDING, DEFINITION, ORIGINAL)["status"] == "completed"
    assert sum(op == "stop-task" for _, op, _ in lost.calls) == 1
    lost.stop_reason = "another-actor"
    fails(lambda: M.replace_runtime(lost, owner, BINDING, DEFINITION, ORIGINAL), "resource-replacement-cause-not-confirmed")
    assert sum(op == "stop-task" for _, op, _ in lost.calls) == 1
    delayed = Provider(delayed=True); owner = store("pending-replacement")
    assert M.replace_runtime(delayed, owner, BINDING, DEFINITION, ORIGINAL)["status"] == "pending"
    delayed.original_status, delayed.current = "STOPPED", [SUCCESSOR]
    assert M.replace_runtime(delayed, owner, BINDING, DEFINITION, ORIGINAL)["status"] == "completed"
    assert sum(op == "stop-task" for _, op, _ in delayed.calls) == 1
    cold = Provider(); cold.starting = True; cold_owner = store("cold-replacement")
    for _ in range(2): assert M.replace_runtime(cold, cold_owner, BINDING, DEFINITION, ORIGINAL)["status"] == "pending"
    fails(lambda: M.task(cold, SUCCESSOR, DEFINITION, BINDING["image_digest"]), "resource-server-task-identity-not-confirmed")
    def wrong_starting(service, operation, **parameters):
        result = cold(service, operation, **parameters)
        if operation == "describe-tasks":
            for row in result["tasks"]:
                if row["taskArn"] == SUCCESSOR: row["containers"][0]["imageDigest"] = "sha256:" + "0" * 64
        return result
    fails(lambda: M.replace_runtime(wrong_starting, cold_owner, BINDING, DEFINITION, ORIGINAL), "resource-server-task-identity-not-confirmed")
    cold.starting = False
    assert M.replace_runtime(cold, cold_owner, BINDING, DEFINITION, ORIGINAL)["status"] == "completed"
    assert sum(op == "stop-task" for _, op, _ in cold.calls) == 1
    wrong = Provider(); wrong.wrong_image = True
    fails(lambda: M.replace_runtime(wrong, store("wrong-image"), BINDING, DEFINITION, ORIGINAL), "resource-server-task-identity-not-confirmed")
    assert not any(op == "stop-task" for _, op, _ in wrong.calls)
    rejected = Provider(); denial = M.SubmissionNotStarted("resource-preflight-denied")
    def before_submit(service, operation, **parameters):
        if operation == "stop-task": raise denial
        return rejected(service, operation, **parameters)
    try: M.replace_runtime(before_submit, store("not-submitted"), BINDING, DEFINITION, ORIGINAL)
    except M.SubmissionNotStarted as failure: assert failure is denial
    else: raise AssertionError("known non-submission must not become remote uncertainty")
    assert not any(op == "stop-task" for _, op, _ in rejected.calls)
    for field, code in (("old", "resource-predecessor-predates-reservation"), ("new", "resource-successor-start-precedes-creation")):
        skewed = Provider(); skew_owner = store("skew-" + field)
        def skew(service, operation, **parameters):
            result = skewed(service, operation, **parameters)
            if operation == "describe-tasks":
                for row in result["tasks"]:
                    if field == "old" and row["taskArn"] == ORIGINAL: row["stoppedAt"] = instant(-180)
                    if field == "new" and row["taskArn"] == SUCCESSOR: row["startedAt"] = instant(-60)
            return result
        fails(lambda: M.replace_runtime(skew, skew_owner, BINDING, DEFINITION, ORIGINAL), code)
        fails(lambda: M.replace_runtime(skew, skew_owner, BINDING, DEFINITION, ORIGINAL), code)
        assert sum(op == "stop-task" for _, op, _ in skewed.calls) == 1
    fails(lambda: M.replace_runtime(provider, store("foreign"), BINDING, DEFINITION, ORIGINAL.replace(M.CLUSTER, "kanbien-staging")), "resource-server-task-invalid")
    # STOPPING with desired STOPPED must not be mistaken for a terminal task.
    stray = Provider(); stray.stray = True
    fails(lambda: M.control_runtime_count(stray, store("stray"), BINDING, DEFINITION, [ORIGINAL]), "resource-owned-completion-task-not-terminal")
    assert not any(op == "update-service" for _, op, _ in stray.calls)
    stopped = Provider(delayed=True); owner = store("stop")
    assert M.control_runtime_count(stopped, owner, BINDING, DEFINITION, [ORIGINAL])["status"] == "pending"
    stopped.original_status = "STOPPED"
    assert M.control_runtime_count(stopped, owner, BINDING, DEFINITION, [ORIGINAL])["status"] == "completed"
    assert sum(op == "update-service" for _, op, _ in stopped.calls) == 1
    assert M.control_runtime_count(stopped, owner, BINDING, DEFINITION, [], start=True)["status"] == "completed"
    assert M.control_runtime_count(stopped, owner, BINDING, DEFINITION, [], start=True)["status"] == "completed"
    assert sum(op == "update-service" for _, op, _ in stopped.calls) == 2
    cold_start = Provider(); cold_start.desired = cold_start.running = 0; cold_start.current = []; cold_start.starting = True
    cold_start_owner = store("cold-start")
    for _ in range(2): assert M.control_runtime_count(cold_start, cold_start_owner, BINDING, DEFINITION, [], start=True)["status"] == "pending"
    cold_start.starting = False
    assert M.control_runtime_count(cold_start, cold_start_owner, BINDING, DEFINITION, [], start=True)["status"] == "completed"
    assert sum(op == "update-service" for _, op, _ in cold_start.calls) == 1
    denied_count = Provider()
    def deny_count(service_name, operation, **parameters):
        if operation == "update-service": raise denial
        return denied_count(service_name, operation, **parameters)
    try: M.control_runtime_count(deny_count, store("count-not-submitted"), BINDING, DEFINITION, [ORIGINAL])
    except M.SubmissionNotStarted as failure: assert failure is denial
    else: raise AssertionError("known count-control non-submission must remain exact")
    assert not any(op == "update-service" for _, op, _ in denied_count.calls)
    paginated = Provider(); paginated.paginated = True
    fails(lambda: M.control_runtime_count(paginated, store("paginated"), BINDING, DEFINITION, [ORIGINAL]), "resource-owned-completion-task-observation-incomplete")
    # A lost snapshot response is reconciled, never created twice. Extra
    # provider/system tags are not projected into retained proof.
    snapshot = Provider(lost=True); owner = store("snapshot")
    fails(lambda: M.create_recovery_point(snapshot, owner, BINDING, RESOURCE_ID, instant(-5)), "resource-submission-uncertain-reconcile-only")
    result = M.create_recovery_point(snapshot, owner, BINDING, RESOURCE_ID, instant(-5))
    assert result["status"] == "completed" and result["facts"]["source_resource_id"] == RESOURCE_ID
    assert sum(op == "create-db-snapshot" for _, op, _ in snapshot.calls) == 1
    snapshot.wrong_snapshot_source = True
    fails(lambda: M.create_recovery_point(snapshot, owner, BINDING, RESOURCE_ID, instant(-5)), "resource-snapshot-identity-not-confirmed")
    wrong_binding = {**BINDING, "dependency_incarnation_sha256": "sha256:" + "0" * 64}
    fails(lambda: M.create_recovery_point(Provider(), store("wrong-incarnation"), wrong_binding, RESOURCE_ID, instant(-5)), "resource-source-incarnation-not-confirmed")
    old = Provider(); old.snapshot = {"Status": "available"}
    fails(lambda: M.create_recovery_point(old, store("old-snapshot"), BINDING, RESOURCE_ID, instant(-5)), "resource-snapshot-already-exists")
    assert not any(op == "create-db-snapshot" for _, op, _ in old.calls)
    # A rejected preexisting object must not become adoptable on resume merely
    # because the first attempt durably reserved its own intent before reading.
    preexisting = Provider(); owner = store("preexisting-resume")
    preexisting.snapshot = copy.deepcopy(snapshot.snapshot)
    preexisting.snapshot["SnapshotCreateTime"] = instant(-1)
    fails(lambda: M.create_recovery_point(preexisting, owner, BINDING, RESOURCE_ID, instant(-5)), "resource-snapshot-already-exists")
    fails(lambda: M.create_recovery_point(preexisting, owner, BINDING, RESOURCE_ID, instant(-5)), "resource-snapshot-predates-reservation")
    assert not any(op == "create-db-snapshot" for _, op, _ in preexisting.calls)
    ongoing = Provider(delayed=True); owner = store("pending-snapshot")
    assert M.create_recovery_point(ongoing, owner, BINDING, RESOURCE_ID, instant(-5))["status"] == "pending"
    ongoing.snapshot["Status"] = "available"
    assert M.create_recovery_point(ongoing, owner, BINDING, RESOURCE_ID, instant(-5))["status"] == "completed"
    assert sum(op == "create-db-snapshot" for _, op, _ in ongoing.calls) == 1
    for path in root.rglob("*.json"): assert CANARY not in path.read_text()
print(json.dumps({"schema": "deploy/entity-smoke-resource-control-fixture/v1", "verdict": "passed", "provider_observation": False,
                  "cases": ["exact-owned-replacement", "durable-intent", "changed-inputs-rejected", "lost-stop-no-replay", "pending-replacement-resume", "cold-replacement-no-replay", "strict-original-image-check", "pending-wrong-image-rejected", "cold-start-no-replay", "count-prewrite-identity-preserved", "wrong-image-no-mutation", "known-prewrite-preserved", "predecessor-after-reservation", "successor-time-order", "foreign-target-rejected", "completion-task-stopping-not-terminal", "stop-preserves-other-workloads", "explicit-start-no-replay", "incomplete-observation-blocks", "lost-snapshot-no-replay", "snapshot-incarnation", "existing-object-not-adopted", "preexisting-snapshot-not-adopted-on-resume", "pending-snapshot-resume"]}))
