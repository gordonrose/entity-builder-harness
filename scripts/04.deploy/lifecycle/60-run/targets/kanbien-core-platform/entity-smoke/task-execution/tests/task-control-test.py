#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.task-control
#   version: 4
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove reservation durability, exact task binding and no replay after lost provider responses with local doubles.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

SPEC = importlib.util.spec_from_file_location("entity_smoke_task_control", (Path(__file__).resolve().parents[2] / "task-execution/implementation/task-control.py"))
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)
if not __debug__:
    raise SystemExit("ENTITY_SMOKE_TASK_CONTROL_ASSERTIONS_DISABLED")
REQUEST = {
    "workload": "verifier", "definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-verifier:1",
    "image_digest": "sha256:" + "a" * 64, "source_revision": "b" * 40, "security_group": "sg-" + "c" * 17,
    "configuration_contract_sha256": "sha256:" + "4" * 64, "permission_contract_sha256": "sha256:" + "5" * 64,
    "dependency_incarnation_sha256": "sha256:" + "6" * 64,
    "subnets": ["subnet-" + "d" * 17], "environment": {"ENTITY_SMOKE_VERIFICATION_OPERATION": "create", "ENTITY_SMOKE_PROOF_LABEL": "entity-smoke-" + "e" * 24},
    "deadline_seconds": 180, "proof_label": "entity-smoke-" + "e" * 24,
}
CANARY = "credential-and-provider-message-canary"
RECORD_FIELDS = {"schema", "operation_id", "request", "request_sha256", "reserved_at"}


class MemoryStorage:
    def __init__(self):
        self.records, self.calls = {}, []

    def read(self, key):
        self.calls.append(("read", key))
        return copy.deepcopy(self.records.get(key))

    def create(self, key, record):
        self.calls.append(("create", key))
        if key in self.records: return False
        self.records[key] = copy.deepcopy(record)
        return True


def fails(call, code):
    try: call()
    except CONTROL.TaskFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected closed rejection")


def task(reservation):
    return {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "f" * 32,
            "taskDefinitionArn": REQUEST["definition"], "startedBy": reservation["operation_id"],
            "overrides": CONTROL.overrides(REQUEST), "lastStatus": "STOPPED"}


# Construct observations independently of the production request/override builder.
# A differently named container exercises the reusable predicate, both actual
# caller bindings, and the unchanged feature diagnostic boundary.
BASE_SPEC = importlib.util.spec_from_file_location("baseline_ecs_evidence", Path(__file__).resolve().parents[3] / "core-server-persistence/ecs-task-evidence.py")
BASE = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(BASE)
expected_environment = {"A": "one", "B": "two"}
observed_container = {"name": "entity-smoke-renamed", "environment": [{"name": "B", "value": "two"}, {"name": "A", "value": "one"}]}
expected_reservation = {"operation_id": "es-" + "1" * 32, "request": {"workload": "renamed", "definition": "fixture-definition", "environment": expected_environment}}
observation = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "2" * 32,
               "taskDefinitionArn": "fixture-definition", "startedBy": "es-" + "1" * 32,
               "overrides": {"containerOverrides": [observed_container]}}
for inert_default in ({}, {"inferenceAcceleratorOverrides": []}):
    valid = {**observation, "overrides": {**observation["overrides"], **inert_default}}
    assert BASE.task_overrides_match(valid, "entity-smoke-renamed", expected_environment)
    assert CONTROL.exact_task(valid, expected_reservation) is valid
invalid_overrides = [None, {}, {"containerOverrides": None}, {"containerOverrides": []},
    {"containerOverrides": [observed_container, observed_container]},
    {"containerOverrides": [None]},
    {"containerOverrides": [observed_container], "taskRoleArn": CANARY},
    {"containerOverrides": [observed_container], "inferenceAcceleratorOverrides": None},
    {"containerOverrides": [observed_container], "inferenceAcceleratorOverrides": [CANARY]}]
invalid_containers = [
    {**observed_container, "command": [CANARY]}, {**observed_container, "name": "wrong"},
    {"name": "entity-smoke-renamed"},
    *[{**observed_container, "environment": entries} for entries in [None, [],
      [{"name": "A", "value": "one"}],
      [{"name": "A", "value": "one"}, {"name": "A", "value": "one"}],
      [{"name": "A", "value": "one"}, {"name": "B", "value": CANARY}],
      [{"name": "A", "value": "one", "unknown": CANARY}, {"name": "B", "value": "two"}],
      [{"name": "A", "value": 1}, {"name": "B", "value": "two"}],
      [{"name": 1, "value": "one"}, {"name": "B", "value": "two"}],
      [None, {"name": "B", "value": "two"}], observed_container["environment"] + [{"name": "C", "value": CANARY}]]]]
for invalid in invalid_overrides + [{"containerOverrides": [container]} for container in invalid_containers]:
    changed = {**observation, "overrides": invalid}
    assert not BASE.task_overrides_match(changed, "entity-smoke-renamed", expected_environment)
    fails(lambda: CONTROL.exact_task(changed, expected_reservation), "task-observation-overrides-mismatch")
assert not BASE.task_overrides_match(None, "entity-smoke-renamed", expected_environment)
assert not BASE.task_overrides_match({}, "entity-smoke-renamed", expected_environment)
empty = {**observation, "overrides": {"containerOverrides": [{"name": "entity-smoke-renamed", "environment": []}]}}
assert BASE.task_overrides_match(empty, "entity-smoke-renamed", {})
assert CONTROL.exact_task(empty, {**expected_reservation, "request": {**expected_reservation["request"], "environment": {}}}) is empty

with tempfile.TemporaryDirectory(prefix="entity-smoke-task-control-") as temporary:
    base = Path(temporary)
    store = CONTROL.AttemptStore(base / "lost")
    calls = []
    def lost(service, operation, **parameters):
        calls.append((service, operation, parameters))
        assert operation == "run-task"
        reservations = list(store.root.glob("*.json"))
        assert len(reservations) == 1, "reservation must exist before the provider mutation"
        assert reservations[0].stat().st_mode & 0o777 == 0o600
        raise OSError(CANARY)
    fails(lambda: CONTROL.invoke_once(lost, store, "first-attempt", REQUEST), "task-submission-uncertain-reconcile-required")
    saved = next(store.root.glob("*.json")).read_bytes()
    reservation = json.loads(saved)
    assert set(reservation) == RECORD_FIELDS and reservation["schema"] == "deploy/entity-smoke-task-reservation/v1"
    remote = task(reservation)
    def reconciled(service, operation, **parameters):
        calls.append((service, operation, parameters))
        assert operation != "run-task", "an alternate key cannot repeat a create for an already reserved label"
        if operation == "list-tasks":
            assert "startedBy" not in parameters, "AWS family/status observation must not use an invalid mixed startedBy filter"
            return {"taskArns": [remote["taskArn"]] if parameters["desiredStatus"] == "STOPPED" else []}
        assert operation == "describe-tasks"
        return {"tasks": [remote]}
    observed, found = CONTROL.invoke_once(reconciled, store, "alternate-attempt", REQUEST)
    assert observed == reservation and found == remote
    assert next(store.root.glob("*.json")).read_bytes() == saved
    assert sum(operation == "run-task" for _, operation, _ in calls) == 1
    def empty(service, operation, **parameters):
        assert operation == "list-tasks"
        return {"taskArns": []}
    fails(lambda: CONTROL.invoke_once(empty, store, "third-attempt", REQUEST), "task-reconciliation-unresolved-no-replay")
    def uncertain(service, operation, **parameters):
        raise RuntimeError(CANARY)
    fails(lambda: CONTROL.invoke_once(uncertain, store, "fourth-attempt", REQUEST), "task-reconciliation-unavailable")
    for changes in [{"source_revision": "1" * 40}, {"image_digest": "sha256:" + "2" * 64}, {"security_group": "sg-" + "3" * 17}, {"permission_contract_sha256": "sha256:" + "6" * 64}]:
        fails(lambda changes=changes: store.reserve("other-key", {**REQUEST, **changes}), "attempt-reservation-mismatch")
    for change, code in [
        ({"startedBy": "es-" + "0" * 32}, "task-observation-identity-mismatch"),
        ({"taskDefinitionArn": REQUEST["definition"][:-1] + "2"}, "task-observation-identity-mismatch"),
        ({"taskArn": CANARY}, "task-observation-invalid"),
        ({"overrides": {**remote["overrides"], "taskRoleArn": CANARY}}, "task-observation-overrides-mismatch"),
    ]:
        fails(lambda change=change: CONTROL.exact_task({**remote, **change}, reservation), code)
    inert = copy.deepcopy(remote)
    inert["overrides"]["inferenceAcceleratorOverrides"] = []
    assert CONTROL.exact_task(inert, reservation) == inert
    duplicate = copy.deepcopy(remote)
    duplicate["overrides"]["containerOverrides"][0]["environment"].append(duplicate["overrides"]["containerOverrides"][0]["environment"][0])
    fails(lambda: CONTROL.exact_task(duplicate, reservation), "task-observation-overrides-mismatch")
    for changes in [
        {"workload": []}, {"deadline_seconds": True}, {"deadline_seconds": 901},
        {"subnets": [CANARY]}, {"environment": {"PERSISTENCE_ADMINISTRATOR_CREDENTIALS": CANARY}},
        {"environment": {**REQUEST["environment"], "ENTITY_SMOKE_EXPECTED_SOURCE": "0" * 40}},
    ]:
        fails(lambda changes=changes: CONTROL.validate_request({**REQUEST, **changes}), "task-request-invalid")
    link = base / "symlink"
    link.symlink_to(store.root, target_is_directory=True)
    fails(lambda: CONTROL.AttemptStore(link), "attempt-path-invalid")
    clean = CONTROL.AttemptStore(base / "successful")
    def success(service, operation, **parameters):
        assert operation == "run-task" and parameters["count"] == 1
        assert parameters["startedBy"] == parameters["clientToken"]
        created = json.loads(next(clean.root.glob("*.json")).read_bytes())
        return {"tasks": [task(created)]}
    assert CONTROL.invoke_once(success, clean, "new-attempt", REQUEST)[1]["lastStatus"] == "STOPPED"
    for invalid in (Path("relative"), base / "parent" / ".." / "escape"):
        fails(lambda: CONTROL.AttemptStore(invalid), "attempt-path-invalid")
    local = CONTROL.AttemptStore(base / "invalid-file")
    local.root.mkdir()
    path = local.path_for("attempt", REQUEST)
    path.symlink_to(next(clean.root.glob("*.json")))
    fails(lambda: local.read("attempt", REQUEST), "attempt-path-invalid")
    path.unlink()
    for raw in (b"{", b" " * 65537):
        path.write_bytes(raw)
        fails(lambda: local.read("attempt", REQUEST), "attempt-reservation-unavailable")

    # Both backends derive the same canonical alias before retaining anything.
    memory = MemoryStorage()
    injected = CONTROL.AttemptStore(None, storage=memory)
    for workload, operation, suffix in (("verifier", "create", "create"), ("verifier", "lifecycle", "lifecycle"),
            ("verifier", "cleanup", "cleanup"), ("verifier", "ready", "verifier-preflight"),
            ("verifier", "unready", "verifier-unready"), ("migration", "preflight", "migration-preflight"),
            ("administration", "preflight", "administration-preflight"),
            ("database-proof", "preflight", "database-proof-preflight"),
            ("restore-reader", "preflight", "restore-reader-preflight")):
        selector = CONTROL.OPERATIONS[workload][0]
        environment = {selector: operation}
        if workload in {"verifier", "database-proof", "restore-reader"}:
            environment["ENTITY_SMOKE_PROOF_LABEL"] = REQUEST["proof_label"]
        if operation == "cleanup": environment["ENTITY_SMOKE_EXPECTED_DIGEST"] = "1" * 64
        selected = {**REQUEST, "workload": workload, "definition": REQUEST["definition"].replace("-verifier:", "-" + workload + ":"),
                    "deadline_seconds": 90, "environment": environment}
        filename = REQUEST["proof_label"] + "-" + suffix + ".json"
        assert injected.path_for("first", selected) == local.path_for("second", selected).name == filename
        original, fresh = injected.reserve("first", selected)
        assert fresh and set(original) == RECORD_FIELDS
        assert injected.reserve("second", selected) == (original, False)
    fails(lambda: injected.reserve("first", {**REQUEST, "deadline_seconds": True}), "task-request-invalid")
    assert len(memory.records) == 9

# The shared default is unchanged; the entity binding overrides only its shape.
assert issubclass(CONTROL.AttemptStore, CONTROL.RESERVATIONS.ImmutableReservationStore)
class DefaultStore(CONTROL.RESERVATIONS.ImmutableReservationStore):
    schema, operation_prefix = "fixture/default/v1", "fixture-"
    def path_for(self, phase, request): return phase
    def validate_time(self, value): CONTROL.datetime.fromisoformat(value)
default = DefaultStore(None, storage=MemoryStorage())
record, fresh = default.reserve("create", {"value": 1})
assert fresh and set(record) == RECORD_FIELDS | {"phase"} and record["phase"] == "create"
assert default.reserve("create", {"value": 1}) == (record, False)

memory = MemoryStorage()
injected = CONTROL.AttemptStore(None, storage=memory)
submissions = []
def remote_success(service, operation, **parameters):
    assert operation == "run-task"
    retained = memory.read(injected.path_for("ignored", REQUEST))
    assert retained and retained["operation_id"] == parameters["clientToken"] == parameters["startedBy"]
    submissions.append(operation)
    return {"tasks": [task(retained)]}
retained, observed = CONTROL.invoke_once(remote_success, injected, "first", REQUEST)
assert submissions == ["run-task"] and observed == task(retained)
def remote_reconcile(service, operation, **parameters):
    assert operation != "run-task", "retained intent never grants replay"
    if operation == "list-tasks": return {"taskArns": [observed["taskArn"]] if parameters["desiredStatus"] == "STOPPED" else []}
    assert operation == "describe-tasks"
    return {"tasks": [observed]}
assert CONTROL.invoke_once(remote_reconcile, CONTROL.AttemptStore(None, storage=memory), "alias", REQUEST) == (retained, observed)

class LostWrite(MemoryStorage):
    def create(self, key, record):
        super().create(key, record)
        raise OSError(CANARY)
memory = LostWrite()
injected = CONTROL.AttemptStore(None, storage=memory)
def never_send(*args, **kwargs): raise AssertionError("provider must not be invoked")
fails(lambda: CONTROL.invoke_once(never_send, injected, "first", REQUEST), "attempt-reservation-unavailable")
retained = next(iter(memory.records.values()))
observed = task(retained)
# A fresh client using the same retained intent can observe, never resubmit.
memory.create = lambda key, record: False
assert CONTROL.invoke_once(remote_reconcile, CONTROL.AttemptStore(None, storage=memory), "alias", REQUEST) == (retained, observed)

for result in (None, 1, "yes", False):
    invalid = MemoryStorage()
    invalid.create = lambda key, record, result=result: result
    fails(lambda: CONTROL.invoke_once(never_send, CONTROL.AttemptStore(None, storage=invalid), "attempt", REQUEST), "attempt-reservation-unavailable")
for exception in (OSError(CANARY), CONTROL.RESERVATIONS.ReservationFailure(CANARY)):
    invalid = MemoryStorage()
    def unavailable(key, exception=exception): raise exception
    invalid.read = unavailable
    fails(lambda: CONTROL.AttemptStore(None, storage=invalid).read("attempt", REQUEST), "attempt-reservation-unavailable")
fails(lambda: CONTROL.AttemptStore(None, storage=object()), "attempt-reservation-unavailable")

for changed, code in [(None, None), ({}, "attempt-reservation-mismatch"),
        *[({**retained, **change}, "attempt-reservation-mismatch") for change in (
            {"schema": CANARY}, {"operation_id": CANARY}, {"request_sha256": CANARY}, {"request": {}},
            {"phase": "unexpected"}, {"reserved_at": "2026-11-27T12:00:00"})],
        ({key: value for key, value in retained.items() if key != "reserved_at"}, "attempt-reservation-mismatch"),
        *[({**retained, "reserved_at": value}, "attempt-reservation-unavailable") for value in (CANARY, None, 7)]]:
    invalid = MemoryStorage()
    invalid.read = lambda key, changed=changed: changed
    selected = CONTROL.AttemptStore(None, storage=invalid)
    if code is None: assert selected.read("attempt", REQUEST) is None
    else: fails(lambda: selected.read("attempt", REQUEST), code)

# A caller's final admission gate still executes after retention but before send.
memory = MemoryStorage()
def blocked(reservation):
    assert next(iter(memory.records.values())) == reservation
    raise CONTROL.SubmissionNotStarted("fixture-admission-closed")
fails(lambda: CONTROL.invoke_once(never_send, CONTROL.AttemptStore(None, storage=memory), "attempt", REQUEST,
                                 before_submit=blocked), "fixture-admission-closed")
assert len(memory.records) == 1
binding_spec = importlib.util.spec_from_file_location("entity_runtime_binding_fixture", Path(__file__).with_name("task-binding-test.py"))
BINDING = importlib.util.module_from_spec(binding_spec); binding_spec.loader.exec_module(BINDING)
selected_request = BINDING.bound_request(REQUEST)
assert CONTROL.runtime(REQUEST)["cluster"] == "kanbien-core-platform"
original_validator, delegation = CONTROL.TASKS.runtime_binding, []
def delegated(value, **arguments):
    delegation.append(arguments)
    return original_validator(value, **arguments)
CONTROL.TASKS.runtime_binding = delegated
try:
    selected_runtime = CONTROL.runtime(selected_request)
    assert delegation == [{"account": CONTROL.ACCOUNT, "region": CONTROL.REGION}]
finally: CONTROL.TASKS.runtime_binding = original_validator
selected_runtime["container_name"] = "changed-copy"
assert selected_request["runtime"]["container_name"] == "renamed-verifier"
for changed in (None, {}, {**selected_request["runtime"], "unknown": CANARY},
                *[{**selected_request["runtime"], field: CANARY} for field in ("session_id", "source_plan_sha256", "binding_sha256", "stack_id", "cluster_arn")],
                {**selected_request["runtime"], "log_group": "/aws/../escape"},
                {**selected_request["runtime"], "family": "x" * 256}):
    fails(lambda: CONTROL.invoke_once(never_send, CONTROL.AttemptStore(None, storage=MemoryStorage()), "runtime", {**selected_request, "runtime": changed}), "runtime-binding-invalid")
memory = MemoryStorage()
injected = CONTROL.AttemptStore(None, storage=memory)
runtime_calls = []
def runtime_lost(service, operation, **parameters):
    runtime_calls.append(operation)
    assert operation == "run-task" and parameters["cluster"] == "arn:aws:ecs:eu-west-1:337159794548:cluster/session-check"
    assert parameters["taskDefinition"] == selected_request["definition"]
    assert parameters["overrides"]["containerOverrides"][0]["name"] == "renamed-verifier"
    assert next(iter(memory.records.values()))["request"] == selected_request
    raise OSError(CANARY)
fails(lambda: CONTROL.invoke_once(runtime_lost, injected, "first", selected_request), "task-submission-uncertain-reconcile-required")
retained = next(iter(memory.records.values()))
runtime_task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/session-check/" + "f" * 32,
                "taskDefinitionArn": selected_request["definition"], "startedBy": retained["operation_id"], "lastStatus": "STOPPED",
                "overrides": {"containerOverrides": [{"name": "renamed-verifier", "environment": [{"name": key, "value": value} for key, value in sorted(REQUEST["environment"].items())]}]}}
def runtime_reconcile(service, operation, **parameters):
    runtime_calls.append(operation)
    assert operation != "run-task" and parameters["cluster"] == selected_request["runtime"]["cluster_arn"]
    if operation == "list-tasks":
        assert parameters["family"] == "session-checked-verifier"
        return {"taskArns": [runtime_task["taskArn"]] if parameters["desiredStatus"] == "STOPPED" else []}
    assert operation == "describe-tasks"
    return {"tasks": [runtime_task]}
assert CONTROL.invoke_once(runtime_reconcile, CONTROL.AttemptStore(None, storage=memory), "alias", selected_request) == (retained, runtime_task)
assert runtime_calls.count("run-task") == 1
for field, value in (("session_id", "9" * 32), ("binding_sha256", "sha256:" + "9" * 64),
                     ("stack_id", selected_request["runtime"]["stack_id"] + "9"),
                     ("cluster_arn", selected_request["runtime"]["cluster_arn"] + "9"),
                     ("container_name", "different"), ("log_group", "/different"), ("log_stream_prefix", "different")):
    changed = {**selected_request, "runtime": {**selected_request["runtime"], field: value}}
    fails(lambda: CONTROL.invoke_once(never_send, injected, "alias", changed), "attempt-reservation-mismatch")
fails(lambda: CONTROL.exact_task({**runtime_task, "taskArn": runtime_task["taskArn"].replace("/session-check/", "/kanbien-core-platform/")}, retained), "task-observation-invalid")
print(json.dumps({"schema": "deploy/entity-smoke-task-control-fixture/v1", "verdict": "passed", "provider_observation": False, "cases": ["reserve-before-submit", "lost-response-reconciliation", "alternate-key-no-replay", "empty-is-not-replay-permission", "uncertain-observation", "immutable-inputs", "exact-task", "shared-predicate-both-bindings", "independent-override-negatives", "inert-provider-default", "duplicate-environment", "invalid-input", "symlink", "one-successful-submission", "shared-default-record", "historical-five-field-record", "injected-retention-before-submit", "lost-write-no-replay", "canonical-local-remote-aliases", "finite-storage-failures", "request-time-validation", "preserved-pre-send-gate"]}))
