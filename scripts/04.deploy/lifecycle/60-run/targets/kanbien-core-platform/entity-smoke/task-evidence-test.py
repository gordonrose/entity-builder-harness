#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.task-evidence
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove exact terminal task and result binding and source-exported diagnostic preservation without cloud observations.
#   portability: {class: internal, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

if not __debug__: raise SystemExit("ENTITY_SMOKE_TASK_EVIDENCE_ASSERTIONS_DISABLED")
SPEC = importlib.util.spec_from_file_location("entity_smoke_task_evidence", Path(__file__).with_name("task-evidence.py"))
EVIDENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVIDENCE)
CANARY = "credential-row-provider-canary"
LABEL, SOURCE, IMAGE, DIGEST = "entity-smoke-" + "a" * 24, "b" * 40, "sha256:" + "c" * 64, "d" * 64


def fixture(workload="verifier", operation="create"):
    selector = {"verifier": "ENTITY_SMOKE_VERIFICATION_OPERATION", "migration": "ENTITY_SMOKE_MIGRATION_OPERATION", "administration": "ENTITY_SMOKE_ADMINISTRATION_OPERATION", "database-proof": "ENTITY_SMOKE_DATABASE_PROOF_OPERATION", "restore-reader": "ENTITY_SMOKE_DATABASE_PROOF_OPERATION"}[workload]
    environment = {selector: operation}
    if workload in {"verifier", "database-proof", "restore-reader"}: environment["ENTITY_SMOKE_PROOF_LABEL"] = LABEL
    if operation in {"read", "restore-read", "cleanup", "collision"}: environment["ENTITY_SMOKE_EXPECTED_DIGEST"] = DIGEST
    request = {"workload": workload, "definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-" + workload + ":1", "image_digest": IMAGE, "source_revision": SOURCE,
               "configuration_contract_sha256": "sha256:" + "4" * 64, "permission_contract_sha256": "sha256:" + "5" * 64,
               "dependency_incarnation_sha256": "sha256:" + "6" * 64,
               "security_group": "sg-" + "e" * 17, "subnets": ["subnet-" + "f" * 17], "environment": environment, "deadline_seconds": 90 if operation == "preflight" else 180, "proof_label": LABEL}
    reservation = {"schema": "deploy/entity-smoke-task-reservation/v1", "operation_id": "es-" + "1" * 32, "request": request,
                   "request_sha256": hashlib.sha256(EVIDENCE.CONTROL.canonical(request)).hexdigest(), "reserved_at": "2026-11-08T12:00:00Z"}
    task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "2" * 32, "taskDefinitionArn": request["definition"], "startedBy": reservation["operation_id"], "overrides": EVIDENCE.CONTROL.overrides(request),
            "lastStatus": "STOPPED", "launchType": "FARGATE", "createdAt": "2026-11-08T12:00:01Z", "startedAt": "2026-11-08T12:00:02Z", "stoppedAt": "2026-11-08T12:00:05Z", "stoppedReason": CANARY,
            "containers": [{"name": "entity-smoke-" + workload, "imageDigest": IMAGE, "exitCode": 0, "reason": CANARY}]}
    result = {"schema": "deploy/entity-smoke-task-proof/v1", "verdict": "passed", "operation": operation, "code": "ENTITY_SMOKE_RECORD_CREATED", "source_revision": SOURCE,
              "proof_label_sha256": hashlib.sha256(LABEL.encode()).hexdigest(), "record_digest": DIGEST,
              "steps": ["release", "liveness", "readiness", "create", "read"], "checked_at": "2026-11-08T12:00:04Z"}
    if workload == "administration": result = {"verdict": "passed", "code": "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED" if operation == "observe-migration-state" else "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED", "operation": operation}
    if workload == "migration": result = {"verdict": "passed", "code": "ENTITY_SMOKE_MIGRATION_APPLIED"}
    if workload in {"database-proof", "restore-reader"}:
        result.pop("source_revision"); result["schema"] = "deploy/entity-smoke-database-proof/v1"
        result["code"] = "ENTITY_SMOKE_RESTORED_RECORD_RETRIEVED" if workload == "restore-reader" else "ENTITY_SMOKE_EFFECTIVE_PRIVILEGES_PROVEN"
        result["steps"] = ["identity", "read"] if workload == "restore-reader" else ["identity", "delete", "truncate", "create-table", "alter-table", "drop-table", "history-write"]
        if workload == "database-proof" and operation != "collision": result.pop("record_digest")
        if workload == "database-proof" and operation == "collision":
            result["code"] = "ENTITY_SMOKE_IDENTIFIER_COLLISION_PROVEN"
            result["steps"] = ["identity", "read", "collision", "read"]
    if workload == "verifier" and operation in {"read", "observe-create"}:
        result["code"] = "ENTITY_SMOKE_RECORD_RETRIEVED" if operation == "read" else "ENTITY_SMOKE_RECORD_RECONCILED"
        result["steps"] = ["release", "liveness", "readiness", "read"]
    if workload == "verifier" and operation in {"ready", "unready"}:
        result["code"] = "ENTITY_SMOKE_HEALTHY" if operation == "ready" else "ENTITY_SMOKE_LIVE_NOT_READY"
        result.pop("record_digest"); result["steps"] = ["release", "liveness", "readiness"]
    if workload == "verifier" and operation == "lifecycle":
        result["code"] = "ENTITY_SMOKE_LIFECYCLE_PROVEN"
        result["steps"] = ["release", "liveness", "readiness", "create", "read", "update", "list", "archive", "restore-archive", "delete", "restore-deleted", "purge-eligibility"]
    if workload == "verifier" and operation == "cleanup":
        result["code"] = "ENTITY_SMOKE_SYNTHETIC_RECORD_LOGICALLY_DELETED"
        result["steps"] = ["release", "liveness", "readiness", "read", "delete"]
    if operation == "preflight":
        result = {"verdict": "passed", "code": "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED"}
        if workload == "administration": result["operation"] = "preflight"
    return task, reservation, result


def collect(task, reservation, *records):
    return EVIDENCE.collect(task, reservation, {"events": [{"message": json.dumps(record)} for record in records]}, "2026-11-08T12:00:06Z")


def fails(call, code):
    try: call()
    except EVIDENCE.EvidenceFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
        return failure
    else: raise AssertionError("expected finite task-evidence rejection")


cases = [("administration", operation) for operation in ["bootstrap", "grant-runtime", "observe-permissions", "observe-migration-state", "revoke-runtime", "restore-runtime"]]
cases += [("migration", "apply"), ("database-proof", "permissions"), ("database-proof", "collision"), ("restore-reader", "restore-read")]
cases += [("verifier", operation) for operation in ["create", "read", "observe-create", "cleanup", "lifecycle", "ready", "unready"]]
cases += [(workload, "preflight") for workload in ["administration", "migration", "database-proof", "restore-reader"]]
for workload, operation in cases:
    task, reservation, result = fixture(workload, operation)
    proof = collect(task, reservation, result)
    assert proof["result"]["code"] == result["code"] and proof["operation"] == operation and proof["workload"] == workload
    assert proof["task"]["completion_duration_seconds"] == 4
    assert CANARY not in json.dumps(proof) and LABEL not in json.dumps(proof)
    assert EVIDENCE.validate_retained(proof, reservation) == proof

for reason, expected in (("CannotPullContainerError: 403 Forbidden " + CANARY, "task-image-pull-access-denied"),
                         ("CannotPullContainerError: " + CANARY, "task-image-pull-not-confirmed"),
                         ("ResourceInitializationError: " + CANARY, "task-provider-startup-not-confirmed"),
                         (None, "task-provider-startup-not-confirmed")):
    task, reservation, result = fixture("administration", "preflight")
    task.update(stopCode="TaskFailedToStart", stoppedReason=reason)
    task.pop("startedAt")
    task["containers"] = [{"name": "entity-smoke-administration"}]
    fails(lambda: collect(task, reservation), expected)
    changed = copy.deepcopy(task); changed["startedBy"] = "es-" + "0" * 32
    fails(lambda: collect(changed, reservation), "task-identity-not-confirmed")
task, reservation, result = fixture("administration", "preflight")
task.update(stopCode="EssentialContainerExited", stoppedReason="CannotPullContainerError: 403 Forbidden " + CANARY)
assert collect(task, reservation, result)["result"]["code"] == result["code"], "unrelated native text must not replace the authoritative task outcome"

for workload in ["administration", "migration", "database-proof", "restore-reader"]:
    task, reservation, result = fixture(workload, "preflight")
    fails(lambda: collect(task, reservation, {**result, "code": "ENTITY_SMOKE_MIGRATION_APPLIED"}), "task-preflight-result-invalid")
    fails(lambda: collect(task, reservation, {**result, "native_error": CANARY}), "task-preflight-result-invalid")

task, reservation, result = fixture("migration", "preflight")
task["containers"][0]["exitCode"] = 1
preflight_diagnostic = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.preflight-rejected", "definitionVersion": 1,
                        "detail": {"identity": "migration", "field": "identity", "condition": "mismatch", "effect": "not-started"}}
preflight_failure = fails(lambda: collect(task, reservation, {"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "diagnostic": preflight_diagnostic}), "task-unsuccessful-completion")
assert preflight_failure.diagnostic == preflight_diagnostic, "the Python collector must use the generated executable target catalogue"

task, reservation, result = fixture()
for change, code in [
    ({"lastStatus": "RUNNING"}, "task-terminal-state-not-confirmed"),
    ({"launchType": "EC2"}, "task-terminal-state-not-confirmed"),
    ({"startedBy": "es-" + "0" * 32}, "task-identity-not-confirmed"),
    ({"stoppedAt": "2026-11-08T12:05:00Z"}, "task-evidence-time-order-invalid"),
    ({"containers": []}, "task-container-evidence-invalid"),
    ({"containers": [{"name": "entity-smoke-verifier", "imageDigest": "sha256:" + "0" * 64, "exitCode": 0}]}, "task-container-identity-not-confirmed"),
]:
    fails(lambda change=change: collect({**task, **change}, reservation, result), code)
for change, code in [
    ({"source_revision": "0" * 40}, "task-http-result-not-confirmed"),
    ({"record_digest": CANARY}, "task-result-digest-invalid"),
    ({"proof_label_sha256": "0" * 64}, "task-result-label-mismatch"),
    ({"steps": ["create"]}, "task-http-result-not-confirmed"),
    ({"code": []}, "task-result-invalid"),
    ({"checked_at": "2026-11-08T11:00:00Z"}, "task-result-time-mismatch"),
    ({"native_error": CANARY}, "task-result-fields-invalid"),
]:
    fails(lambda change=change: collect(task, reservation, {**result, **change}), code)
fails(lambda: collect(task, reservation), "task-success-observation-not-confirmed")
fails(lambda: collect(task, reservation, result, result), "task-success-observation-not-confirmed")
fails(lambda: collect(task, {**reservation, "request_sha256": "0" * 64}, result), "task-reservation-input-mismatch")
retained = collect(task, reservation, result)
fails(lambda: EVIDENCE.validate_retained({**retained, "permission_contract_sha256": "sha256:" + "0" * 64}, reservation), "task-retained-receipt-mismatch")
failed = copy.deepcopy(task); failed["containers"][0]["exitCode"] = 1
fails(lambda: collect(failed, reservation, result), "task-unsuccessful-completion")
primary = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.proof-failed", "definitionVersion": 1, "detail": {"operation": "create", "step": "create", "condition": "request-failed", "effect": "unknown"}}
companion = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.boundary-failed", "definitionVersion": 1, "detail": {"operation": "close", "effect": "not-assessed"}}
envelope = {"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "diagnostic": primary, "related_diagnostics": [companion]}
observed = fails(lambda: collect(failed, reservation, envelope), "task-unsuccessful-completion")
assert observed.diagnostic == primary and observed.related == [companion]
second = {"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "diagnostic": companion}
multiple = fails(lambda: collect(failed, reservation, envelope, second), "task-unsuccessful-completion")
assert len(multiple.observations) == 2 and multiple.observations[0]["related_diagnostics"] == [companion]
rollback = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.database-proof-failed", "definitionVersion": 1, "detail": {"operation": "permissions", "step": "rollback", "condition": "unexpected-failure", "effect": "unknown"}}
rollback_envelope = {"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "diagnostic": rollback}
preserved = fails(lambda: collect(failed, reservation, rollback_envelope, envelope, second), "task-unsuccessful-completion")
assert preserved.diagnostic == primary and preserved.related == [companion] and len(preserved.observations) == 3
fails(lambda: collect(failed, reservation, {**envelope, "native_error": CANARY}), "task-failure-envelope-invalid")
fails(lambda: collect(failed, reservation, {**envelope, "related_diagnostics": [primary]}), "task-failure-companions-invalid")
unsafe = copy.deepcopy(envelope); unsafe["diagnostic"]["detail"]["condition"] = CANARY
fails(lambda: collect(failed, reservation, unsafe), "task-diagnostic-not-confirmed")

def paginated(pages):
    calls = []
    def provider(service, operation, **parameters):
        assert (service, operation) == ("logs", "get-log-events") and parameters["startFromHead"] is True and parameters["limit"] == 1000
        if calls: assert parameters["nextToken"] == pages[len(calls) - 1]["nextForwardToken"]
        else: assert "nextToken" not in parameters
        calls.append(parameters)
        return pages[len(calls) - 1]
    return provider, calls
provider, calls = paginated([{"events": [], "nextForwardToken": "partial-empty"}, {"events": [{"message": json.dumps(result)}], "nextForwardToken": "terminal"}, {"events": [], "nextForwardToken": "terminal"}])
all_logs = EVIDENCE.read_logs(provider, reservation["request"], task["taskArn"])
assert len(calls) == 3 and EVIDENCE.collect(task, reservation, all_logs, "2026-11-08T12:00:06Z")["result"]["code"] == result["code"]
provider, calls = paginated([{"events": [{"message": json.dumps(result)}], "nextForwardToken": "success-prefix"}, {"events": [{"message": json.dumps(envelope)}], "nextForwardToken": "failure-page"}, {"events": [], "nextForwardToken": "failure-page"}])
all_logs = EVIDENCE.read_logs(provider, reservation["request"], task["taskArn"])
observed_failure = fails(lambda: EVIDENCE.collect(task, reservation, all_logs, "2026-11-08T12:00:06Z"), "task-unsuccessful-completion")
assert observed_failure.diagnostic == primary, "a success prefix cannot hide a failure on the next page"
for pages, code in [
    ([{"events": []}], "task-log-pagination-invalid"),
    ([{"events": [], "nextForwardToken": []}], "task-log-pagination-invalid"),
    ([{"events": [], "nextForwardToken": str(index)} for index in range(3)], "task-log-observation-incomplete"),
    ([{"events": [{}] * 1000, "nextForwardToken": "more"}, {"events": [{}], "nextForwardToken": "end"}], "task-log-observation-invalid"),
]:
    provider, calls = paginated(pages)
    fails(lambda: EVIDENCE.read_logs(provider, reservation["request"], task["taskArn"]), code)
    assert len(calls) <= 3
provider, calls = paginated([])
fails(lambda: EVIDENCE.read_logs(provider, reservation["request"], CANARY), "task-log-identity-invalid")
assert calls == []
primary = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.preflight-rejected", "definitionVersion": 1,
           "detail": {"identity": "runtime", "field": "identity", "condition": "mismatch", "effect": "not-started"}}
task, reservation, _ = fixture("database-proof", "preflight")
task["containers"][0]["exitCode"] = 1
envelope = {"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "diagnostic": primary}
observed = fails(lambda: collect(task, reservation, envelope), "task-unsuccessful-completion")
projection = EVIDENCE.failure_report(observed)
assert projection["diagnostic"] == primary and projection["related_diagnostics"] == [] and projection["observations"] == observed.observations
malformed = EVIDENCE.EvidenceFailure(observed.code, {"native": CANARY}, [], observed.observations)
assert EVIDENCE.failure_report(malformed) == {"diagnostic_processing_condition": "task-diagnostic-not-confirmed"}
old_record = EVIDENCE.record
EVIDENCE.record = lambda value: (_ for _ in ()).throw(RuntimeError(CANARY))
assert EVIDENCE.failure_report(observed) == {"diagnostic_processing_condition": "task-diagnostic-not-confirmed"}
assert observed.diagnostic == primary and observed.code == "task-unsuccessful-completion"
EVIDENCE.record = old_record
print(json.dumps({"schema": "deploy/entity-smoke-task-evidence-fixture/v1", "verdict": "passed", "success_protocol_cases": len(cases),
                  "checks": ["terminal-identity", "source-and-digest", "complete-steps", "times", "one-result", "no-native-values", "source-exported-diagnostics", "all-normal-failure-bundles", "bounded-forward-pagination", "success-prefix-cannot-hide-later-failure", "selected-primary-report-projection", "malformed-or-thrown-projection-safe"], "provider_observation": False}))
