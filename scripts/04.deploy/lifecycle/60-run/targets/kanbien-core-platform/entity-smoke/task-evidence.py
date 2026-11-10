#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-evidence
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind terminal task facts and safe code-exported observations to one reserved feature operation without retaining raw task logs.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[7]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


CONTROL = module("entity_smoke_evidence_control", Path(__file__).with_name("task-control.py"))
DIAGNOSTICS = module("entity_smoke_runtime_contract", ROOT / "scripts/repo/diagnostic-coverage/runtime_contract.py")
OWN_CATALOGS = [ROOT / "infra/04.deploy/03.product/entrypoints/contracts/entity-smoke-target-diagnostics.v1.json",
                ROOT / "apps/entity-smoke/contracts/diagnostics.v1.json", DIAGNOSTICS.PERSISTENCE_TASK_OPERATION_CATALOG]
HTTP_CODES = {"create": "ENTITY_SMOKE_RECORD_CREATED", "read": "ENTITY_SMOKE_RECORD_RETRIEVED", "observe-create": "ENTITY_SMOKE_RECORD_RECONCILED", "cleanup": "ENTITY_SMOKE_SYNTHETIC_RECORD_LOGICALLY_DELETED", "lifecycle": "ENTITY_SMOKE_LIFECYCLE_PROVEN", "ready": "ENTITY_SMOKE_HEALTHY", "unready": "ENTITY_SMOKE_LIVE_NOT_READY"}
HTTP_STEPS = {
    "create": ["release", "liveness", "readiness", "create", "read"],
    "read": ["release", "liveness", "readiness", "read"],
    "observe-create": ["release", "liveness", "readiness", "read"],
    "cleanup": ["release", "liveness", "readiness", "read", "delete"],
    "lifecycle": ["release", "liveness", "readiness", "create", "read", "update", "list", "archive", "restore-archive", "delete", "restore-deleted", "purge-eligibility"],
    "ready": ["release", "liveness", "readiness"], "unready": ["release", "liveness", "readiness"],
}


class EvidenceFailure(Exception):
    def __init__(self, code, diagnostic=None, related=None, observations=None):
        super().__init__(code)
        self.code, self.diagnostic, self.related = code, diagnostic, related
        self.observations = observations or []


def require(allowed, code):
    if not allowed: raise EvidenceFailure(code)


def timestamp(value):
    require(isinstance(value, str), "task-evidence-time-invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(parsed.tzinfo is not None, "task-evidence-time-invalid")
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError): raise EvidenceFailure("task-evidence-time-invalid") from None


def record(value):
    for catalog in OWN_CATALOGS:
        try: return DIAGNOSTICS.validate_record(value, catalog)
        except DIAGNOSTICS.DiagnosticContractError: pass
        except (OSError, ValueError, TypeError, KeyError): raise EvidenceFailure("task-diagnostic-contract-unavailable") from None
    try: return DIAGNOSTICS.validate_selected_record(value)
    except (OSError, ValueError, TypeError, KeyError): raise EvidenceFailure("task-diagnostic-not-confirmed") from None


def failure_bundle(value):
    require(isinstance(value, dict) and {"verdict", "code", "diagnostic"} <= set(value) and not set(value) - {"verdict", "code", "diagnostic", "related_diagnostics"} and value["verdict"] == "failed" and value["code"] == "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "task-failure-envelope-invalid")
    primary = record(value["diagnostic"])
    companions = value.get("related_diagnostics", [])
    try: limit = json.loads(DIAGNOSTICS.CORE_CATALOG.read_text())["delivery"]["maxRelatedRecords"]
    except (OSError, ValueError, TypeError, KeyError): raise EvidenceFailure("task-diagnostic-contract-unavailable") from None
    require(type(limit) is int and limit >= 0 and isinstance(companions, list) and len(companions) <= limit, "task-failure-companions-invalid")
    related = [record(item) for item in companions]
    identities = [CONTROL.canonical(item) for item in [primary, *related]]
    require(len(set(identities)) == len(identities), "task-failure-companions-invalid")
    return {"diagnostic": primary, "related_diagnostics": related}


def failure_report(failure):
    """Preserve selected meaning at real CLI callers, never native error data."""
    if failure.diagnostic is None and not failure.observations and not failure.related: return {}
    try:
        def checked(bundle):
            require(isinstance(bundle, dict), "task-diagnostic-not-confirmed")
            return failure_bundle({"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", **bundle})
        primary = checked({"diagnostic": failure.diagnostic, "related_diagnostics": [] if failure.related is None else failure.related})
        require(isinstance(failure.observations, list) and len(failure.observations) <= 3, "task-diagnostic-not-confirmed")
        observations = [checked(bundle) for bundle in failure.observations]
        return {**primary, **({"observations": observations} if observations else {})}
    except Exception:
        # This is diagnostic-processing failure only. The caller preserves the
        # original finite operation condition/effect and never retries it.
        return {"diagnostic_processing_condition": "task-diagnostic-not-confirmed"}


def success(value, request, start, stop):
    workload = request["workload"]
    operation = request["environment"][CONTROL.OPERATIONS[workload][0]]
    require(type(value) is dict and value.get("verdict") == "passed" and isinstance(value.get("code"), str), "task-result-invalid")
    if operation == "preflight":
        fields = {"verdict", "code", "operation"} if workload == "administration" else {"verdict", "code"}
        require(set(value) == fields and value["code"] == "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED"
                and (workload != "administration" or value["operation"] == "preflight"), "task-preflight-result-invalid")
        return {"verdict": "passed", "code": value["code"], "operation": "preflight"}
    if workload == "administration":
        codes = {"PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED", "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED"} if operation == "observe-migration-state" else {"ENTITY_SMOKE_ADMINISTRATION_CONFIRMED"}
        require(set(value) == {"verdict", "code", "operation"} and value.get("operation") == operation and value.get("code") in codes, "task-result-invalid")
        return {"verdict": "passed", "code": value["code"], "operation": operation}
    if workload == "migration":
        require(set(value) == {"verdict", "code"} and value.get("code") in {"ENTITY_SMOKE_MIGRATION_APPLIED", "ENTITY_SMOKE_MIGRATION_ALREADY_APPLIED"}, "task-result-invalid")
        return {"verdict": "passed", "code": value["code"], "operation": operation}
    digest_required = workload == "restore-reader" or operation == "collision" or workload == "verifier" and operation not in {"ready", "unready"}
    fields = {"schema", "verdict", "operation", "code", "proof_label_sha256", "steps", "checked_at"}
    if digest_required: fields.add("record_digest")
    if workload == "verifier": fields.add("source_revision")
    require(set(value) == fields and value.get("operation") == operation, "task-result-fields-invalid")
    require(value.get("proof_label_sha256") == hashlib.sha256(request["proof_label"].encode()).hexdigest(), "task-result-label-mismatch")
    checked = timestamp(value["checked_at"])
    require(start.timestamp() - 60 <= checked.timestamp() <= stop.timestamp() + 60, "task-result-time-mismatch")
    if digest_required:
        require(isinstance(value.get("record_digest"), str) and re.fullmatch(r"[a-f0-9]{64}", value["record_digest"]) is not None, "task-result-digest-invalid")
        if "ENTITY_SMOKE_EXPECTED_DIGEST" in request["environment"]:
            require(value["record_digest"] == request["environment"]["ENTITY_SMOKE_EXPECTED_DIGEST"], "task-result-digest-mismatch")
    if workload == "verifier":
        require(value["schema"] == "deploy/entity-smoke-task-proof/v1" and value["source_revision"] == request["source_revision"] and value["code"] == HTTP_CODES[operation] and value["steps"] == HTTP_STEPS[operation], "task-http-result-not-confirmed")
    else:
        require(value["schema"] == "deploy/entity-smoke-database-proof/v1", "task-database-result-not-confirmed")
        expected_code = "ENTITY_SMOKE_RESTORED_RECORD_RETRIEVED" if workload == "restore-reader" else "ENTITY_SMOKE_IDENTIFIER_COLLISION_PROVEN" if operation == "collision" else "ENTITY_SMOKE_EFFECTIVE_PRIVILEGES_PROVEN"
        steps = ["identity", "read"] if workload == "restore-reader" else ["identity", "read", "collision", "read"] if operation == "collision" else ["identity", "delete", "truncate", "create-table", "alter-table", "drop-table", "history-write"]
        require(value["code"] == expected_code and value["steps"] == steps, "task-database-result-not-confirmed")
    # Reconstruct only validated fields; never persist the provider dictionary.
    return json.loads(CONTROL.canonical(value))


def read_logs(provider, request, task_arn):
    """At most three pages; a partial/empty page is not stream completion.

    Tokens and raw messages are ephemeral inputs to collect, never retained
    proof. An unavailable/incomplete observation authorizes only later reads.
    """
    CONTROL.validate_request(request)
    require(isinstance(task_arn, str) and re.fullmatch(r"arn:aws:ecs:" + CONTROL.REGION + ":" + CONTROL.ACCOUNT + ":task/" + CONTROL.CLUSTER + r"/[a-f0-9]{32}", task_arn) is not None, "task-log-identity-invalid")
    token, events = None, []
    for _page in range(3):
        response = provider("logs", "get-log-events", logGroupName="/aws/ecs/kanbien-core-platform",
                            logStreamName="entity-smoke-" + request["workload"] + "/entity-smoke-" + request["workload"] + "/" + task_arn.rsplit("/", 1)[1],
                            startFromHead=True, limit=1000, **({"nextToken": token} if token is not None else {}))
        batch = response.get("events") if isinstance(response, dict) else None
        next_token = response.get("nextForwardToken") if isinstance(response, dict) else None
        require(isinstance(batch, list) and len(batch) <= 1000 and len(events) + len(batch) <= 1000, "task-log-observation-invalid")
        require(isinstance(next_token, str) and 0 < len(next_token) <= 4096, "task-log-pagination-invalid")
        events.extend(batch)
        if next_token == token: return {"events": events}
        token = next_token
    raise EvidenceFailure("task-log-observation-incomplete")


def reject_failed_start(task):
    """Reject explicit provider startup failure before expecting an application."""
    if task.get("stopCode") != "TaskFailedToStart": return
    reason = task.get("stoppedReason")
    if isinstance(reason, str) and len(reason) <= 65536 and reason.startswith("CannotPullContainerError:"):
        raise EvidenceFailure("task-image-pull-access-denied" if "403 Forbidden" in reason else "task-image-pull-not-confirmed")
    raise EvidenceFailure("task-provider-startup-not-confirmed")


def collect(task, reservation, response, collected_at):
    require(isinstance(reservation, dict) and set(reservation) == {"schema", "operation_id", "request", "request_sha256", "reserved_at"} and reservation.get("schema") == "deploy/entity-smoke-task-reservation/v1" and isinstance(reservation.get("operation_id"), str) and re.fullmatch(r"es-[a-f0-9]{32}", reservation["operation_id"]) is not None, "task-reservation-invalid")
    try:
        request = CONTROL.validate_request(reservation["request"])
        CONTROL.exact_task(task, reservation)
    except CONTROL.TaskFailure: raise EvidenceFailure("task-identity-not-confirmed") from None
    require(reservation.get("request_sha256") == hashlib.sha256(CONTROL.canonical(request)).hexdigest(), "task-reservation-input-mismatch")
    require(task.get("lastStatus") == "STOPPED" and task.get("launchType") == "FARGATE", "task-terminal-state-not-confirmed")
    reject_failed_start(task)
    containers = task.get("containers")
    require(isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict), "task-container-evidence-invalid")
    container = containers[0]
    require(container.get("name") == "entity-smoke-" + request["workload"] and container.get("imageDigest") == request["image_digest"] and type(container.get("exitCode")) is int, "task-container-identity-not-confirmed")
    created, start, stop = (timestamp(task.get(key)) for key in ("createdAt", "startedAt", "stoppedAt"))
    reserved = timestamp(reservation["reserved_at"])
    collected = timestamp(collected_at)
    require(reserved.timestamp() <= created.timestamp() + 60 and created <= start <= stop and collected.timestamp() >= stop.timestamp() - 60, "task-evidence-time-order-invalid")
    elapsed = (stop - created).total_seconds()
    require(elapsed <= request["deadline_seconds"], "task-completion-deadline-exceeded")
    events = response.get("events") if isinstance(response, dict) else None
    require(isinstance(events, list) and len(events) <= 1000, "task-log-observation-invalid")
    successes, failures = [], []
    for event in events:
        require(isinstance(event, dict) and isinstance(event.get("message"), str), "task-log-observation-invalid")
        try: size = len(event["message"].encode("utf-8"))
        except UnicodeError: raise EvidenceFailure("task-log-observation-invalid") from None
        require(size <= 65536, "task-log-observation-invalid")
        try: value = json.loads(event["message"])
        except (ValueError, TypeError, RecursionError): continue
        if isinstance(value, dict) and value.get("verdict") == "failed":
            failures.append(failure_bundle(value))
            # Current entrypoints emit at most body, rollback and pool-close
            # failures. More is a broken protocol, never silent truncation.
            require(len(failures) <= 3, "task-failure-observation-limit")
        if isinstance(value, dict) and value.get("verdict") == "passed": successes.append(success(value, request, start, stop))
    if failures:
        # The supported entrypoints emit rollback failure before rethrowing
        # the body error, and pool-close failure afterwards. Preserve the body
        # as primary while retaining every original bundle and its companions.
        meaningful = [bundle for bundle in failures if not (
            bundle["diagnostic"]["code"] == "entity-smoke-target.boundary-failed" and bundle["diagnostic"]["detail"].get("operation") == "close"
            or bundle["diagnostic"]["code"] == "entity-smoke-target.database-proof-failed" and bundle["diagnostic"]["detail"].get("step") == "rollback")]
        primary = meaningful[-1] if meaningful else failures[0]
        raise EvidenceFailure("task-unsuccessful-completion", primary["diagnostic"], primary["related_diagnostics"], failures)
    require(container["exitCode"] == 0, "task-unsuccessful-completion")
    require(len(successes) == 1, "task-success-observation-not-confirmed")
    return {"schema": "deploy/entity-smoke-task-proof-receipt/v1", "target": "kanbien-core-platform", "scope": "entity-smoke",
            "source_revision": request["source_revision"], "image_digest": request["image_digest"], "workload": request["workload"],
            "configuration_contract_sha256": request["configuration_contract_sha256"], "permission_contract_sha256": request["permission_contract_sha256"],
            "dependency_incarnation_sha256": request["dependency_incarnation_sha256"],
            "operation": request["environment"][CONTROL.OPERATIONS[request["workload"]][0]], "request_sha256": reservation["request_sha256"],
            "reserved_at": reservation["reserved_at"],
            "task": {"arn": task["taskArn"], "definition": task["taskDefinitionArn"], "operation_id": reservation["operation_id"],
                     "created_at": created.isoformat(), "started_at": start.isoformat(), "stopped_at": stop.isoformat(),
                     "exit_code": 0, "completion_duration_seconds": elapsed}, "result": successes[0], "collected_at": collected.isoformat()}


def validate_retained(value, reservation):
    """Validate previously captured immutable facts, never claim a fresh read.

    Reconstruct only the producer's validated projection for the same reserved
    request. No collected time is advanced and no provider state is inferred.
    """
    try:
        require(isinstance(value, dict) and isinstance(value.get("task"), dict), "task-retained-receipt-invalid")
        task = value["task"]
        observed = {"taskArn": task["arn"], "taskDefinitionArn": task["definition"], "startedBy": task["operation_id"],
                    "overrides": CONTROL.overrides(reservation["request"]), "lastStatus": "STOPPED", "launchType": "FARGATE",
                    "createdAt": task["created_at"], "startedAt": task["started_at"], "stoppedAt": task["stopped_at"],
                    "containers": [{"name": "entity-smoke-" + value["workload"], "imageDigest": value["image_digest"], "exitCode": task["exit_code"]}]}
        result = value["result"]
        if isinstance(result, dict) and (value["workload"] == "migration" or result.get("operation") == "preflight" and value["workload"] != "administration"):
            # Migration stdout has no operation field; the collector adds the
            # reserved invocation's operation to its retained projection.
            result = {key: content for key, content in result.items() if key != "operation"}
        expected = collect(observed, reservation, {"events": [{"message": json.dumps(result)}]}, value["collected_at"])
        require(expected == value, "task-retained-receipt-mismatch")
        return expected
    except EvidenceFailure: raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError): raise EvidenceFailure("task-retained-receipt-invalid") from None
