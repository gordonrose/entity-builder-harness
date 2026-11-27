#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.task-control
#   version: 2
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
# This primitive fixture controls cost admission; the owner has separate
# complete-census/lock tests and these tests never inspect a real budget.
CONTROL.reserve_task_cost = lambda request, reserve, **_options: reserve()


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


with tempfile.TemporaryDirectory(prefix="entity-smoke-task-cost-") as temporary:
    store = CONTROL.AttemptStore(Path(temporary))
    calls = []
    def refuse(request, reserve, **options):
        calls.append(options)
        CONTROL.reject("task-cost-admission-not-confirmed")
    original = CONTROL.reserve_task_cost
    CONTROL.reserve_task_cost = refuse
    fails(lambda: CONTROL.invoke_once(lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no provider call before admission")), store, "budget", REQUEST), "task-cost-admission-not-confirmed")
    assert store.read("budget", REQUEST) is None
    reserved, _ = store.reserve("budget", REQUEST)
    reconcile = CONTROL.reconcile_reserved
    CONTROL.reconcile_reserved = lambda provider, value: (value, task(value))
    assert CONTROL.invoke_once(None, store, "budget", REQUEST)[0] == reserved
    assert len(calls) == 1, "existing original uses reconciliation, not new budget admission"
    CONTROL.reconcile_reserved, CONTROL.reserve_task_cost = reconcile, original


with tempfile.TemporaryDirectory(prefix="entity-smoke-task-census-") as temporary:
    store = CONTROL.AttemptStore(Path(temporary))
    assert store.reservations() == []
    original, _ = store.reserve("original", REQUEST)
    assert store.reservations() == [original], "unresolved original remains in cost census"
    path = store.path_for("original", REQUEST)
    changed = copy.deepcopy(original); changed["request_sha256"] = "0" * 64
    path.write_text(json.dumps(changed))
    fails(store.reservations, "attempt-reservation-mismatch")


for operation in ("scheduling-delete", "scheduling-restore"):
    selected = {**REQUEST, "environment": {**REQUEST["environment"], "ENTITY_SMOKE_VERIFICATION_OPERATION": operation,
        "ENTITY_SMOKE_EXPECTED_ID": "00000000-0000-4000-8000-000000000123", "ENTITY_SMOKE_EXPECTED_DIGEST": "1" * 64}}
    assert CONTROL.validate_request(selected) == selected
    for value in (None, "", CANARY):
        altered = copy.deepcopy(selected)
        if value is None: altered["environment"].pop("ENTITY_SMOKE_EXPECTED_ID")
        else: altered["environment"]["ENTITY_SMOKE_EXPECTED_ID"] = value
        fails(lambda: CONTROL.validate_request(altered), "task-scheduling-selection-invalid")
    with tempfile.TemporaryDirectory(prefix="entity-smoke-synthetic-original-") as temporary:
        store = CONTROL.AttemptStore(Path(temporary))
        first, created = store.reserve("caller-first", selected)
        second, created_again = store.reserve("caller-second", selected)
        assert created and not created_again and first == second
        altered = copy.deepcopy(selected); altered["environment"]["ENTITY_SMOKE_EXPECTED_ID"] = "00000000-0000-4000-8000-000000000124"
        fails(lambda: store.reserve("caller-third", altered), "attempt-reservation-mismatch")


migration = {**REQUEST, "workload": "migration", "definition": REQUEST["definition"].replace("-verifier:", "-migration:"),
    "environment": {"ENTITY_SMOKE_MIGRATION_OPERATION": "apply"}}
original_migration = CONTROL.canonical(migration)
assert CONTROL.validate_request(migration) == migration and CONTROL.canonical(migration) == original_migration
scheduled = {**migration, "environment": {**migration["environment"], "PERSISTENCE_MIGRATION_PROFILE": "scheduling"}}
assert CONTROL.validate_request(scheduled) == scheduled and CONTROL.canonical(scheduled) != original_migration
for profile in ("baseline", "unknown", CANARY):
    fails(lambda profile=profile: CONTROL.validate_request({**scheduled, "environment": {**scheduled["environment"], "PERSISTENCE_MIGRATION_PROFILE": profile}}), "task-migration-profile-invalid")
fails(lambda: CONTROL.validate_request({**scheduled, "environment": {"ENTITY_SMOKE_MIGRATION_OPERATION": "preflight", "PERSISTENCE_MIGRATION_PROFILE": "scheduling"}}), "task-migration-profile-invalid")
fails(lambda: CONTROL.validate_request({**REQUEST, "environment": {**REQUEST["environment"], "PERSISTENCE_MIGRATION_PROFILE": "scheduling"}}), "task-migration-profile-invalid")
with tempfile.TemporaryDirectory(prefix="entity-smoke-migration-profile-") as temporary:
    store = CONTROL.AttemptStore(Path(temporary))
    reservation, _ = store.reserve("migration-profile", scheduled)
    fails(lambda: store.read("migration-profile", migration), "attempt-reservation-mismatch")
    observed = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "2" * 32,
        "taskDefinitionArn": scheduled["definition"], "startedBy": reservation["operation_id"], "overrides": CONTROL.overrides(scheduled)}
    assert CONTROL.exact_task(observed, reservation) == observed
    fails(lambda: CONTROL.exact_task({**observed, "overrides": CONTROL.overrides(migration)}, reservation), "task-observation-overrides-mismatch")


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
print(json.dumps({"schema": "deploy/entity-smoke-task-control-fixture/v1", "verdict": "passed", "provider_observation": False, "cases": ["reserve-before-submit", "lost-response-reconciliation", "alternate-key-no-replay", "empty-is-not-replay-permission", "uncertain-observation", "immutable-inputs", "exact-task", "shared-predicate-both-bindings", "independent-override-negatives", "inert-provider-default", "duplicate-environment", "invalid-input", "symlink", "one-successful-submission"]}))
