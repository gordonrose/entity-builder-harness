#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.task-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
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

SPEC = importlib.util.spec_from_file_location("entity_smoke_task_control", Path(__file__).with_name("task-control.py"))
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
print(json.dumps({"schema": "deploy/entity-smoke-task-control-fixture/v1", "verdict": "passed", "provider_observation": False, "cases": ["reserve-before-submit", "lost-response-reconciliation", "alternate-key-no-replay", "empty-is-not-replay-permission", "uncertain-observation", "immutable-inputs", "exact-task", "inert-provider-default", "duplicate-environment", "invalid-input", "symlink", "one-successful-submission"]}))
