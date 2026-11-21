#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.preflight-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise bounded task admission, collector-backed prerequisite matching and no replay across keys without cloud effects.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

if not __debug__: raise SystemExit("ENTITY_SMOKE_PREFLIGHT_CONTROL_ASSERTIONS_DISABLED")
SPEC = importlib.util.spec_from_file_location("entity_smoke_preflight_control_fixture", Path(__file__).with_name("preflight-control.py"))
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
CANARY = "credential-provider-preflight-canary"
LABEL = "entity-smoke-" + "a" * 24


def fixture(workload):
    selector = M.CONTROL.OPERATIONS[workload][0]
    operation = "ready" if workload == "verifier" else "preflight"
    environment = {selector: operation}
    if workload in {"verifier", "database-proof", "restore-reader"}: environment["ENTITY_SMOKE_PROOF_LABEL"] = LABEL
    if workload == "verifier": environment["ENTITY_SMOKE_EXPECTED_SOURCE"] = "b" * 40
    request = {"workload": workload, "definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-" + workload + ":1",
               "source_revision": "b" * 40, "image_digest": "sha256:" + "c" * 64, "configuration_contract_sha256": "sha256:" + "d" * 64,
               "permission_contract_sha256": "sha256:" + "e" * 64, "dependency_incarnation_sha256": "sha256:" + "f" * 64,
               "security_group": "sg-" + "1" * 17, "subnets": ["subnet-" + "2" * 17], "environment": environment, "deadline_seconds": 90, "proof_label": LABEL}
    reservation = {"schema": "deploy/entity-smoke-task-reservation/v1", "operation_id": "es-" + "3" * 32, "request": request,
                   "request_sha256": hashlib.sha256(M.CONTROL.canonical(request)).hexdigest(), "reserved_at": "2026-11-08T12:00:00Z"}
    task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "4" * 32, "taskDefinitionArn": request["definition"], "startedBy": reservation["operation_id"],
            "overrides": M.CONTROL.overrides(request), "lastStatus": "STOPPED", "launchType": "FARGATE", "createdAt": "2026-11-08T12:00:01Z", "startedAt": "2026-11-08T12:00:02Z", "stoppedAt": "2026-11-08T12:00:05Z",
            "containers": [{"name": "entity-smoke-" + workload, "imageDigest": request["image_digest"], "exitCode": 0}]}
    result = {"verdict": "passed", "code": "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED"}
    if workload == "administration": result["operation"] = "preflight"
    if workload == "verifier": result = {"schema": "deploy/entity-smoke-task-proof/v1", "verdict": "passed", "operation": "ready", "code": "ENTITY_SMOKE_HEALTHY", "source_revision": request["source_revision"],
                                         "proof_label_sha256": hashlib.sha256(LABEL.encode()).hexdigest(), "steps": ["release", "liveness", "readiness"], "checked_at": "2026-11-08T12:00:04Z"}
    receipt = M.EVIDENCE.collect(task, reservation, {"events": [{"message": json.dumps(result)}]}, "2026-11-08T12:00:06Z")
    return request, reservation, task, receipt


def fails(call, code, kind=M.PreflightFailure):
    try: call()
    except kind as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected closed preflight rejection")


for workload in M.CONTROL.OPERATIONS:
    request, reservation, task, receipt = fixture(workload)
    assert M.validate_launch(request) == request
    business = copy.deepcopy(request)
    selector = M.CONTROL.OPERATIONS[workload][0]
    operation = {"administration": "bootstrap", "migration": "apply", "verifier": "create", "database-proof": "permissions", "restore-reader": "restore-read"}[workload]
    business["environment"][selector] = operation
    if workload == "restore-reader": business["environment"]["ENTITY_SMOKE_EXPECTED_DIGEST"] = "5" * 64
    def admit(selected=business, **changes):
        return M.require_receipt(selected, reservation, receipt, **{"expected_preflight_label": LABEL, "current_time": "2026-11-08T12:00:10Z", "required_after": "2026-11-08T12:00:00Z", **changes})
    assert admit() == receipt
    fails(lambda: M.validate_launch(business), "preflight-operation-not-read-only")
    for key, value in [("image_digest", "sha256:" + "0" * 64), ("source_revision", "0" * 40), ("configuration_contract_sha256", "sha256:" + "0" * 64),
                       ("permission_contract_sha256", "sha256:" + "0" * 64), ("dependency_incarnation_sha256", "sha256:" + "0" * 64), ("security_group", "sg-" + "0" * 17),
                       ("subnets", ["subnet-" + "0" * 17]), ("definition", request["definition"][:-1] + "2")]:
        changed = {**business, key: value, "environment": copy.deepcopy(business["environment"])}
        if key == "source_revision" and workload == "verifier": changed["environment"]["ENTITY_SMOKE_EXPECTED_SOURCE"] = value
        fails(lambda changed=changed: admit(changed), "preflight-operation-binding-mismatch")
    fails(lambda: admit(expected_preflight_label="entity-smoke-" + "0" * 24), "preflight-label-not-selected")
    fails(lambda: admit(current_time="2026-11-08T12:20:00Z"), "preflight-observation-not-fresh")
    fails(lambda: admit(current_time="2026-11-08T11:58:00Z"), "preflight-predates-required-state")
    fails(lambda: admit(required_after="2026-11-08T12:00:03Z"), "preflight-predates-required-state")
    over = {**request, "deadline_seconds": 91}
    fails(lambda: M.validate_launch(over), "preflight-deadline-exceeds-bound" if workload == "verifier" else "task-preflight-request-invalid", M.PreflightFailure if workload == "verifier" else M.CONTROL.TaskFailure)
    if workload == "verifier":
        extra = copy.deepcopy(request); extra["environment"]["ENTITY_SMOKE_EXPECTED_DIGEST"] = "0" * 64
        fails(lambda: M.validate_launch(extra), "preflight-overrides-not-closed")
    with tempfile.TemporaryDirectory(prefix="entity-smoke-preflight-reservation-") as temporary:
        store = M.CONTROL.AttemptStore(Path(temporary)); calls = []
        def lost(service, operation, **parameters):
            calls.append(operation)
            assert operation == "run-task" and parameters["count"] == 1
            assert len(list(Path(temporary).glob("*.json"))) == 1
            raise OSError(CANARY)
        fails(lambda: M.CONTROL.invoke_once(lost, store, "first", request), "task-submission-uncertain-reconcile-required", M.CONTROL.TaskFailure)
        def absent(service, operation, **parameters):
            calls.append(operation); assert operation == "list-tasks", "alternate key cannot submit another preflight"
            return {"taskArns": []}
        fails(lambda: M.CONTROL.invoke_once(absent, store, "alternate", request), "task-reconciliation-unresolved-no-replay", M.CONTROL.TaskFailure)
        assert calls.count("run-task") == 1
        assert CANARY not in next(Path(temporary).glob("*.json")).read_text()
print(json.dumps({"verdict": "passed", "evidence_class": "controlled-task-protocol", "provider_observation": False, "workloads": 5,
                  "checks": ["read-only-mode-only", "ninety-second-bound", "immutable-matching", "source-owned-collector-result", "freshness-and-order", "alternate-key-no-replay"]}))
