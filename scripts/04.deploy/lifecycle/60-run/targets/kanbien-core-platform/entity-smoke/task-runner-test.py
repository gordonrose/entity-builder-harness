#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.task-runner
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove terminal proof retention, unchanged historical reuse and lost-response reconciliation with a simulated provider.
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

if not __debug__: raise SystemExit("ENTITY_SMOKE_TASK_RUNNER_ASSERTIONS_DISABLED")
SPEC = importlib.util.spec_from_file_location("entity_smoke_task_runner", Path(__file__).with_name("task-runner.py"))
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)
CANARY = "credential-row-provider-canary"
LABEL, SOURCE, IMAGE = "entity-smoke-" + "a" * 24, "b" * 40, "sha256:" + "c" * 64
REQUEST = {"workload": "verifier", "definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-verifier:1",
           "image_digest": IMAGE, "source_revision": SOURCE, "configuration_contract_sha256": "sha256:" + "4" * 64, "permission_contract_sha256": "sha256:" + "5" * 64,
           "dependency_incarnation_sha256": "sha256:" + "6" * 64,
           "security_group": "sg-" + "e" * 17, "subnets": ["subnet-" + "f" * 17], "environment": {"ENTITY_SMOKE_VERIFICATION_OPERATION": "ready", "ENTITY_SMOKE_PROOF_LABEL": LABEL, "ENTITY_SMOKE_EXPECTED_SOURCE": SOURCE}, "deadline_seconds": 90, "proof_label": LABEL}
base = datetime.now(timezone.utc)
instant = lambda seconds: (base + timedelta(seconds=seconds)).isoformat()


class Provider:
    def __init__(self, lost=False, running=False, failed=False, offset=0):
        self.calls, self.remote, self.lost, self.running, self.failed = [], None, lost, running, failed
        self.offset, self.operation = offset, "ready"
    def __call__(self, service, operation, **parameters):
        self.calls.append((service, operation, parameters))
        if operation == "run-task":
            self.operation = next(item["value"] for item in parameters["overrides"]["containerOverrides"][0]["environment"] if item["name"] == "ENTITY_SMOKE_VERIFICATION_OPERATION")
            self.remote = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "2" * 32, "taskDefinitionArn": REQUEST["definition"], "startedBy": parameters["startedBy"], "overrides": parameters["overrides"],
                           "lastStatus": "RUNNING", "launchType": "FARGATE", "createdAt": instant(1 + self.offset), "startedAt": instant(2 + self.offset), "stoppedAt": instant(3 + self.offset), "stoppedReason": CANARY,
                           "containers": [{"name": "entity-smoke-verifier", "imageDigest": IMAGE, "exitCode": 1 if self.failed else 0}]}
            if self.lost: raise OSError(CANARY)
            return {"tasks": [copy.deepcopy(self.remote)]}
        if operation == "list-tasks": return {"taskArns": [self.remote["taskArn"]] if parameters["desiredStatus"] == "STOPPED" else []}
        if operation == "describe-tasks":
            self.remote["lastStatus"] = "RUNNING" if self.running else "STOPPED"
            return {"tasks": [copy.deepcopy(self.remote)]}
        assert (service, operation) == ("logs", "get-log-events")
        assert parameters["limit"] == 1000 and parameters["logStreamName"].startswith("entity-smoke-verifier/entity-smoke-verifier/")
        if self.failed:
            records = [{"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "diagnostic": {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.proof-failed", "definitionVersion": 1, "detail": {"operation": "ready", "step": "readiness", "condition": "status-mismatch", "effect": "not-assessed"}}}]
            if parameters.get("nextToken") == "body-page":
                records = [{"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "diagnostic": {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.boundary-failed", "definitionVersion": 1, "detail": {"operation": "close", "effect": "not-assessed"}}}]
            if parameters.get("nextToken") == "close-page": records = []
            return {"events": [{"message": json.dumps(item)} for item in records], "nextForwardToken": "body-page" if "nextToken" not in parameters else "close-page"}
        result = {"schema": "deploy/entity-smoke-task-proof/v1", "verdict": "passed", "operation": self.operation, "code": "ENTITY_SMOKE_HEALTHY", "source_revision": SOURCE,
                  "proof_label_sha256": hashlib.sha256(LABEL.encode()).hexdigest(), "steps": ["release", "liveness", "readiness"], "checked_at": instant(2.5 + self.offset)}
        if self.operation == "create": result.update(code="ENTITY_SMOKE_RECORD_CREATED", steps=["release", "liveness", "readiness", "create", "read"], record_digest="5" * 64)
        if self.operation == "unready": result["code"] = "ENTITY_SMOKE_LIVE_NOT_READY"
        return {"events": [] if "nextToken" in parameters else [{"message": json.dumps(result)}], "nextForwardToken": "terminal-page"}


def fails(call, code, kind=RUNNER.RunnerFailure):
    try: call()
    except kind as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
        return failure
    else: raise AssertionError("expected bounded runner rejection")


def revocation_packet(operation="revoke-runtime", offset=-20):
    request = {**REQUEST, "workload": "administration", "definition": REQUEST["definition"].replace("-verifier:", "-administration:"),
               "environment": {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": operation}}
    reservation = {"schema": "deploy/entity-smoke-task-reservation/v1", "operation_id": "es-" + "9" * 32, "request": request,
                   "request_sha256": hashlib.sha256(RUNNER.CONTROL.canonical(request)).hexdigest(), "reserved_at": instant(offset)}
    task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "8" * 32, "taskDefinitionArn": request["definition"],
            "startedBy": reservation["operation_id"], "overrides": RUNNER.CONTROL.overrides(request), "lastStatus": "STOPPED", "launchType": "FARGATE",
            "createdAt": instant(offset + 1), "startedAt": instant(offset + 2), "stoppedAt": instant(offset + 3),
            "containers": [{"name": "entity-smoke-administration", "imageDigest": IMAGE, "exitCode": 0}]}
    result = {"verdict": "passed", "operation": operation, "code": "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED"}
    receipt = RUNNER.EVIDENCE.collect(task, reservation, {"events": [{"message": json.dumps(result)}]}, instant(offset + 4))
    return {"reservation": reservation, "receipt": receipt, "label": LABEL}


with tempfile.TemporaryDirectory(prefix="entity-smoke-task-runner-") as temporary:
    root = Path(temporary)
    store, receipts = RUNNER.CONTROL.AttemptStore(root / "attempts"), root / "receipts"
    provider = Provider()
    ticks = [0]
    def monotonic(): ticks[0] += 1; return ticks[0]
    def observer(_value): raise RuntimeError(CANARY)
    result = RUNNER.run_owned_task(provider, store, "ready", REQUEST, receipts, clock=lambda: instant(4), monotonic=monotonic, sleep=lambda _seconds: None, on_progress=observer)
    assert result["reused"] is False and result["receipt"]["result"]["code"] == "ENTITY_SMOKE_HEALTHY"
    assert result["path"].is_file()
    assert CANARY not in result["path"].read_text()
    original = result["path"].read_bytes()
    count = len(provider.calls)
    repeated = RUNNER.run_owned_task(provider, store, "ready", REQUEST, receipts)
    assert repeated["reused"] is True and repeated["receipt"] == result["receipt"] and repeated["path"].read_bytes() == original
    assert len(provider.calls) == count, "historical receipt reuse is not a fresh AWS observation"
    fails(lambda: RUNNER.run_owned_task(provider, store, "ready", REQUEST, receipts, required_after=instant(5)), "task-state-observation-not-fresh")
    assert len(provider.calls) == count
    lost = Provider(lost=True)
    lost_store = RUNNER.CONTROL.AttemptStore(root / "lost-attempts")
    fails(lambda: RUNNER.run_owned_task(lost, lost_store, "lost", REQUEST, root / "lost-receipts", clock=lambda: instant(4), monotonic=monotonic, sleep=lambda _seconds: None), "task-submission-uncertain-reconcile-required", RUNNER.CONTROL.TaskFailure)
    reconciled = RUNNER.run_owned_task(lost, lost_store, "lost", REQUEST, root / "lost-receipts", clock=lambda: instant(4), monotonic=monotonic, sleep=lambda _seconds: None)
    assert reconciled["receipt"]["result"]["code"] == "ENTITY_SMOKE_HEALTHY"
    assert sum(op == "run-task" for _, op, _ in lost.calls) == 1
    slow = Provider(running=True)
    short = {**REQUEST, "deadline_seconds": 1}
    fails(lambda: RUNNER.run_owned_task(slow, RUNNER.CONTROL.AttemptStore(root / "slow-attempts"), "slow", short, root / "slow-receipts", monotonic=monotonic, sleep=lambda _seconds: None), "task-deadline-remote-operation-not-terminal")
    assert [op for _, op, _ in slow.calls] == ["run-task"], "a deadline authorizes neither stop nor another launch"
    assert not (root / "slow-receipts").exists()
    broken = Provider(failed=True)
    failure = fails(lambda: RUNNER.run_owned_task(broken, RUNNER.CONTROL.AttemptStore(root / "failed-attempts"), "failed", REQUEST, root / "failed-receipts", clock=lambda: instant(4), monotonic=monotonic, sleep=lambda _seconds: None), "task-unsuccessful-completion", RUNNER.EVIDENCE.EvidenceFailure)
    assert len(failure.observations) == 2 and failure.diagnostic["code"] == "entity-smoke-target.proof-failed"
    assert sum(op == "get-log-events" for _, op, _ in broken.calls) == 3
    assert not (root / "failed-receipts").exists()
    business = copy.deepcopy(REQUEST); business["environment"]["ENTITY_SMOKE_VERIFICATION_OPERATION"] = "create"
    launch = Provider(offset=5); business_store = RUNNER.CONTROL.AttemptStore(root / "business-attempts")
    fails(lambda: RUNNER.run_owned_task(launch, business_store, "create", business, root / "business-receipts"), "task-preflight-receipt-required")
    assert launch.calls == [] and not business_store.root.exists(), "missing preflight must reject before reservation or provider effects"
    prerequisite = {"reservation": store.read("ready", REQUEST), "receipt": result["receipt"], "label": LABEL}
    fails(lambda: RUNNER.run_owned_task(launch, business_store, "create", business, root / "business-receipts", preflight=prerequisite, required_after=instant(0), clock=lambda: instant(1000)), "preflight-observation-not-fresh")
    assert launch.calls == [] and not business_store.root.exists()
    admitted = RUNNER.run_owned_task(launch, business_store, "create", business, root / "business-receipts", preflight=prerequisite, required_after=instant(0), clock=lambda: instant(9), monotonic=monotonic, sleep=lambda _seconds: None)
    assert admitted["receipt"]["result"]["code"] == "ENTITY_SMOKE_RECORD_CREATED"
    assert sum(op == "run-task" for _, op, _ in launch.calls) == 1
    assert RUNNER.run_owned_task(launch, business_store, "other-key", business, root / "business-receipts")["reused"] is True
    assert sum(op == "run-task" for _, op, _ in launch.calls) == 1, "historical completed proof is not a new effect needing a fresh preflight"
    business_reservation = business_store.read("create", business)
    admission = RUNNER.PREFLIGHT.admission_path(root / "business-receipts", business_reservation)
    original_admission = admission.read_bytes(); before_calls = len(launch.calls)
    moved = admission.with_suffix(".temporarily-moved")
    admission.rename(moved)
    fails(lambda: RUNNER.run_owned_task(launch, business_store, "create", business, root / "business-receipts"), "preflight-admission-not-retained")
    class ConcurrentStore:
        def read(self, key, request): return None
        def reserve(self, key, request): return business_store.reserve(key, request)
    fails(lambda: RUNNER.run_owned_task(launch, ConcurrentStore(), "create", business, root / "business-receipts", preflight=prerequisite, required_after=instant(0), clock=lambda: instant(9)), "preflight-admission-not-retained")
    assert sum(op == "run-task" for _, op, _ in launch.calls) == 1
    before_calls = len(launch.calls)
    moved.rename(admission)
    tampered = json.loads(original_admission); tampered["reservation_sha256"] = "0" * 64
    admission.write_text(json.dumps(tampered))
    fails(lambda: RUNNER.run_owned_task(launch, business_store, "create", business, root / "business-receipts"), "preflight-admission-binding-mismatch")
    admission.write_bytes(original_admission)
    assert len(launch.calls) == before_calls and CANARY not in admission.read_text()
    uncertain_business = Provider(lost=True, offset=5)
    uncertain_store = RUNNER.CONTROL.AttemptStore(root / "uncertain-business-attempts")
    uncertain_receipts = root / "uncertain-business-receipts"
    def admitted_provider(service, operation, **parameters):
        if operation == "run-task":
            retained = uncertain_receipts / "admissions" / (parameters["startedBy"] + ".json")
            assert retained.is_file() and retained.stat().st_mode & 0o777 == 0o600, "admission must be durably retained before the provider call"
        return uncertain_business(service, operation, **parameters)
    fails(lambda: RUNNER.run_owned_task(admitted_provider, uncertain_store, "create", business, uncertain_receipts, preflight=prerequisite, required_after=instant(0), clock=lambda: instant(9), monotonic=monotonic, sleep=lambda _seconds: None), "task-submission-uncertain-reconcile-required", RUNNER.CONTROL.TaskFailure)
    historical_admission = next((uncertain_receipts / "admissions").glob("*.json")).read_bytes()
    observed_business = RUNNER.run_owned_task(admitted_provider, uncertain_store, "another-key", business, uncertain_receipts, clock=lambda: instant(1000), monotonic=monotonic, sleep=lambda _seconds: None)
    assert observed_business["receipt"]["result"]["code"] == "ENTITY_SMOKE_RECORD_CREATED"
    assert sum(op == "run-task" for _, op, _ in uncertain_business.calls) == 1
    assert next((uncertain_receipts / "admissions").glob("*.json")).read_bytes() == historical_admission, "original admission is not restamped after its freshness window"
    negative = copy.deepcopy(REQUEST); negative["environment"]["ENTITY_SMOKE_VERIFICATION_OPERATION"] = "unready"
    revoked = revocation_packet()
    negative_store = RUNNER.CONTROL.AttemptStore(root / "negative-attempts"); negative_root = root / "negative-receipts"
    negative_provider = Provider()
    def observe(selected=negative, **changes):
        return RUNNER.run_owned_task(negative_provider, negative_store, "negative", selected, negative_root,
                                    **{"clock": lambda: instant(4), "monotonic": monotonic, "sleep": lambda _seconds: None, **changes})
    fails(lambda: observe(), "unready-revocation-required")
    fails(lambda: observe(revocation=revocation_packet("bootstrap")), "unready-revocation-operation-mismatch")
    for field, value in (("source_revision", "0" * 40), ("image_digest", "sha256:" + "0" * 64), ("configuration_contract_sha256", "sha256:" + "0" * 64),
                         ("permission_contract_sha256", "sha256:" + "0" * 64), ("dependency_incarnation_sha256", "sha256:" + "0" * 64)):
        changed = copy.deepcopy(negative); changed[field] = value
        if field == "source_revision": changed["environment"]["ENTITY_SMOKE_EXPECTED_SOURCE"] = value
        fails(lambda: observe(changed, revocation=revoked), "unready-revocation-binding-mismatch")
    fails(lambda: observe(revocation={**revoked, "label": "entity-smoke-" + "0" * 24}), "unready-revocation-label-mismatch")
    fails(lambda: observe({**negative, "deadline_seconds": 91}, revocation=revoked), "unready-deadline-exceeds-bound")
    extra = copy.deepcopy(negative); extra["environment"]["ENTITY_SMOKE_EXPECTED_DIGEST"] = "0" * 64
    fails(lambda: observe(extra, revocation=revoked), "unready-overrides-not-closed")
    fails(lambda: observe(revocation=revoked, preflight=prerequisite), "task-unready-not-readiness-admission")
    fails(lambda: observe(REQUEST, revocation=revoked), "task-revocation-context-not-applicable")
    malformed = copy.deepcopy(revoked); malformed["receipt"]["result"]["operation"] = "bootstrap"
    fails(lambda: observe(revocation=malformed), "task-result-invalid")
    assert negative_provider.calls == [] and not negative_store.root.exists(), "invalid recovery evidence must reject before reservation or effects"
    def negative_transport(service, operation, **parameters):
        if operation == "run-task":
            admission = negative_root / "unready" / "admissions" / (parameters["startedBy"] + ".json")
            assert admission.is_file() and admission.stat().st_mode & 0o777 == 0o600
        return negative_provider(service, operation, **parameters)
    negative_result = RUNNER.run_owned_task(negative_transport, negative_store, "negative", negative, negative_root, revocation=revoked, clock=lambda: instant(4), monotonic=monotonic, sleep=lambda _seconds: None)
    assert negative_result["receipt"]["result"]["code"] == "ENTITY_SMOKE_LIVE_NOT_READY"
    assert observe()["reused"] is True
    reserved_negative = negative_store.read("another-key", negative)
    negative_admission = RUNNER.UNREADY.path_for(negative_root, reserved_negative)
    admission_bytes = negative_admission.read_bytes(); negative_calls = len(negative_provider.calls)
    fails(lambda: observe(revocation=revocation_packet(offset=-30)), "unready-admission-revocation-changed")
    negative_moved = negative_admission.with_suffix(".temporarily-moved"); negative_admission.rename(negative_moved)
    fails(lambda: observe(), "unready-admission-not-retained")
    negative_moved.rename(negative_admission)
    tampered_negative = json.loads(admission_bytes); tampered_negative["reservation_sha256"] = "0" * 64
    negative_admission.write_text(json.dumps(tampered_negative))
    fails(lambda: observe(), "unready-admission-binding-mismatch")
    negative_admission.write_bytes(admission_bytes)
    assert len(negative_provider.calls) == negative_calls
    blocked = Provider()
    bad_readiness = {"reservation": reserved_negative, "receipt": negative_result["receipt"], "label": LABEL}
    fails(lambda: RUNNER.run_owned_task(blocked, RUNNER.CONTROL.AttemptStore(root / "unready-as-ready"), "create", business, root / "unready-as-ready-receipts",
                                       preflight=bad_readiness, required_after=instant(-20), clock=lambda: instant(4)), "preflight-operation-not-read-only")
    assert blocked.calls == [], "expected unready must never admit feature work"
    negative_lost = Provider(lost=True); negative_lost_store = RUNNER.CONTROL.AttemptStore(root / "negative-lost-attempts")
    def lost_observe(key, **changes):
        return RUNNER.run_owned_task(negative_lost, negative_lost_store, key, negative, root / "negative-lost-receipts",
                                    **{"clock": lambda: instant(4), "monotonic": monotonic, "sleep": lambda _seconds: None, **changes})
    fails(lambda: lost_observe("first", revocation=revoked), "task-submission-uncertain-reconcile-required", RUNNER.CONTROL.TaskFailure)
    assert lost_observe("alternate")["receipt"]["result"]["code"] == "ENTITY_SMOKE_LIVE_NOT_READY"
    assert sum(op == "run-task" for _, op, _ in negative_lost.calls) == 1
    early = Provider(offset=-30)
    fails(lambda: RUNNER.run_owned_task(early, RUNNER.CONTROL.AttemptStore(root / "early-negative"), "negative", negative, root / "early-negative-receipts",
                                       revocation=revoked, clock=lambda: instant(4), monotonic=monotonic, sleep=lambda _seconds: None), "task-state-observation-not-fresh")
    assert sum(op == "run-task" for _, op, _ in early.calls) == 1
    stale_negative = Provider()
    fails(lambda: RUNNER.run_owned_task(stale_negative, RUNNER.CONTROL.AttemptStore(root / "stale-negative"), "negative", negative, root / "stale-negative-receipts",
                                       revocation=revocation_packet(offset=-1000), clock=lambda: instant(4)), "unready-revocation-not-fresh")
    assert stale_negative.calls == []
    healthy_instead = Provider()
    def wrong_negative_result(service, operation, **parameters):
        response = healthy_instead(service, operation, **parameters)
        if operation == "get-log-events":
            for event in response["events"]:
                value = json.loads(event["message"]); value["code"] = "ENTITY_SMOKE_HEALTHY"; event["message"] = json.dumps(value)
        return response
    fails(lambda: RUNNER.run_owned_task(wrong_negative_result, RUNNER.CONTROL.AttemptStore(root / "healthy-not-unready"), "negative", negative, root / "healthy-not-unready-receipts",
                                       revocation=revoked, clock=lambda: instant(4), monotonic=monotonic, sleep=lambda _seconds: None), "task-http-result-not-confirmed", RUNNER.EVIDENCE.EvidenceFailure)
    assert not list((root / "healthy-not-unready-receipts").glob("verifier-*.json"))
print(json.dumps({"schema": "deploy/entity-smoke-task-runner-fixture/v1", "verdict": "passed", "provider_observation": False,
                  "cases": ["terminal-proof-retained", "unchanged-historical-reuse", "minimum-observer-time", "lost-launch-reconciliation", "no-second-launch", "deadline-no-implicit-recovery", "all-bounded-failure-observations", "reporter-isolation", "business-preflight-before-reservation", "stale-proof-no-effects", "durable-admission-before-provider", "missing-or-changed-admission-blocks", "lost-business-launch-original-admission-only", "unready-matching-collected-revocation", "unready-invalid-evidence-before-effects", "unready-bound-and-closed-overrides", "unready-durable-admission", "unready-unchanged-historical-reuse", "unready-changed-or-missing-admission-blocks", "unready-cannot-admit-business", "unready-lost-response-alternate-key-no-replay", "unready-after-revocation", "unready-stale-revocation-no-launch"]}))
