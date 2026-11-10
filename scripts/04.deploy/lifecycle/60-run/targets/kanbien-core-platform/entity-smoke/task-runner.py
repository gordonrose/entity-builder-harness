#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-runner
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Observe one reserved private task to a bounded terminal result and retain exact proof without rerunning completed work.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import importlib.util


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


CONTROL = module("entity_smoke_runner_control", Path(__file__).with_name("task-control.py"))
EVIDENCE = module("entity_smoke_runner_evidence", Path(__file__).with_name("task-evidence.py"))
PREFLIGHT = module("entity_smoke_runner_preflight", Path(__file__).with_name("preflight-control.py"))
UNREADY = module("entity_smoke_runner_unready", Path(__file__).with_name("unready-control.py"))


class RunnerFailure(Exception):
    def __init__(self, code, operation_id=None, task_arn=None):
        super().__init__(code)
        self.code, self.operation_id, self.task_arn = code, operation_id, task_arn


def require(allowed, code, reservation=None, task=None):
    if not allowed:
        raise RunnerFailure(code, reservation.get("operation_id") if reservation else None, task.get("taskArn") if task else None)


def receipt_path(root, request, reservation):
    operation = request["environment"][CONTROL.OPERATIONS[request["workload"]][0]]
    path = Path(root) / (request["workload"] + "-" + operation + "-" + reservation["operation_id"] + ".json")
    CONTROL.no_symlinks(path)
    return path


def read_receipt(path, reservation):
    CONTROL.no_symlinks(path)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream: raw = stream.read(1048577)
        require(len(raw) <= 1048576, "task-retained-receipt-unavailable", reservation)
        return EVIDENCE.validate_retained(json.loads(raw), reservation)
    except FileNotFoundError: return None
    except (RunnerFailure, EVIDENCE.EvidenceFailure): raise
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError): raise RunnerFailure("task-retained-receipt-unavailable", reservation["operation_id"]) from None


def retain(path, value, reservation):
    CONTROL.no_symlinks(path)
    EVIDENCE.validate_retained(value, reservation)
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            previous = read_receipt(path, reservation)
            comparable = lambda item: {key: content for key, content in item.items() if key != "collected_at"}
            require(previous is not None and comparable(previous) == comparable(value), "task-retained-receipt-conflict", reservation)
            return previous
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(CONTROL.canonical(value) + b"\n")
            stream.flush(); os.fsync(stream.fileno())
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
        return value
    except (RunnerFailure, EVIDENCE.EvidenceFailure): raise
    except (OSError, ValueError, TypeError, UnicodeError): raise RunnerFailure("task-receipt-retention-not-confirmed", reservation["operation_id"]) from None


def fresh_enough(receipt, required_after):
    if required_after is not None:
        require(EVIDENCE.timestamp(receipt["task"]["created_at"]) >= EVIDENCE.timestamp(required_after), "task-state-observation-not-fresh")


def run_owned_task(provider, store, key, request, receipt_root, *, required_after=None, preflight=None, revocation=None,
                   clock=lambda: datetime.now(timezone.utc).isoformat(), monotonic=time.monotonic, sleep=time.sleep, on_progress=None):
    """Only the owning gated route may supply the live provider capability.

    An immutable retained receipt is historical proof for this exact reserved
    step, not a claim about current dependency state. New state observations
    require a separately labelled key and may require a minimum creation time.
    A deadline never authorizes another task or implicit provider recovery.
    """
    CONTROL.validate_request(request)
    state_required_after = required_after
    selector = CONTROL.OPERATIONS[request["workload"]][0]
    is_preflight = request["environment"][selector] == ("ready" if request["workload"] == "verifier" else "preflight")
    is_unready = request["workload"] == "verifier" and request["environment"][selector] == "unready"
    require(revocation is None or is_unready, "task-revocation-context-not-applicable")
    require(not is_unready or preflight is None, "task-unready-not-readiness-admission")
    if is_preflight:
        try: PREFLIGHT.validate_launch(request)
        except (PREFLIGHT.PreflightFailure, PREFLIGHT.CONTROL.TaskFailure) as failure: raise RunnerFailure(failure.code) from None
    CONTROL.no_symlinks(Path(receipt_root))
    previous = store.read(key, request)
    def guarded_admission(call):
        try: return call()
        except (PREFLIGHT.PreflightFailure, PREFLIGHT.CONTROL.TaskFailure, PREFLIGHT.EVIDENCE.EvidenceFailure, UNREADY.UnreadyFailure) as failure: raise RunnerFailure(failure.code) from None
    if is_unready:
        if previous is None:
            after = guarded_admission(lambda: UNREADY.validate_launch(request, revocation))
        else:
            after = guarded_admission(lambda: UNREADY.read_admission(receipt_root, previous, revocation))
        required_after = max([after, *([] if required_after is None else [required_after])], key=EVIDENCE.timestamp)
    if previous is not None:
        if not is_preflight and not is_unready:
            original_after = guarded_admission(lambda: PREFLIGHT.read_admission(receipt_root, previous))
            required_after = max([original_after, *([] if required_after is None else [required_after])], key=EVIDENCE.timestamp)
        path = receipt_path(receipt_root, request, previous)
        retained = read_receipt(path, previous)
        if retained is not None:
            fresh_enough(retained, required_after)
            return {"receipt": retained, "path": path, "reused": True}
    if previous is None and not is_preflight and not is_unready:
        require(isinstance(preflight, dict) and set(preflight) == {"reservation", "receipt", "label"} and required_after is not None, "task-preflight-receipt-required")
        checked = guarded_admission(lambda: PREFLIGHT.require_receipt(request, preflight["reservation"], preflight["receipt"], expected_preflight_label=preflight["label"], current_time=clock(), required_after=required_after))
        # A fabricated provider creation time before the actual preflight may
        # not become successful business evidence, even with correct bindings.
        required_after = max(required_after, checked["task"]["stopped_at"], key=EVIDENCE.timestamp)
    def before_submit(reservation):
        if is_unready:
            guarded_admission(lambda: UNREADY.retain_admission(receipt_root, reservation, revocation, clock()))
        elif not is_preflight:
            guarded_admission(lambda: PREFLIGHT.retain_admission(receipt_root, reservation, preflight, state_required_after, clock()))
    reservation, current = CONTROL.invoke_once(provider, store, key, request, before_submit=before_submit)
    if is_unready:
        after = guarded_admission(lambda: UNREADY.read_admission(receipt_root, reservation, revocation))
        required_after = max(required_after, after, key=EVIDENCE.timestamp)
    elif not is_preflight:
        # Another process may reserve between the initial read and reserve.
        # Its original admission is still required before collecting evidence.
        original_after = guarded_admission(lambda: PREFLIGHT.read_admission(receipt_root, reservation))
        required_after = max([original_after, *([] if required_after is None else [required_after])], key=EVIDENCE.timestamp)
    path = receipt_path(receipt_root, request, reservation)
    deadline = monotonic() + request["deadline_seconds"]
    def progress(phase):
        if on_progress is not None:
            try: on_progress({"phase": phase, "operation_id": reservation["operation_id"], "task": current["taskArn"]})
            except Exception: pass
    while current.get("lastStatus") != "STOPPED":
        require(monotonic() < deadline, "task-deadline-remote-operation-not-terminal", reservation, current)
        progress("waiting-for-terminal-state")
        try: described = provider("ecs", "describe-tasks", cluster=CONTROL.CLUSTER, tasks=[current["taskArn"]])
        except Exception: raise RunnerFailure("task-observation-unavailable-reconcile-only", reservation["operation_id"], current["taskArn"]) from None
        tasks = described.get("tasks") if isinstance(described, dict) else None
        require(isinstance(tasks, list) and len(tasks) == 1 and not described.get("failures"), "task-observation-unavailable-reconcile-only", reservation, current)
        observed = CONTROL.exact_task(tasks[0], reservation)
        require(observed["taskArn"] == current["taskArn"], "task-observation-identity-mismatch", reservation, current)
        current = observed
        if current.get("lastStatus") != "STOPPED": sleep(2)
    EVIDENCE.reject_failed_start(current)
    progress("collecting-terminal-evidence")
    try: response = EVIDENCE.read_logs(provider, request, current["taskArn"])
    except (EVIDENCE.EvidenceFailure, RunnerFailure): raise
    except Exception: raise RunnerFailure("task-log-observation-unavailable", reservation["operation_id"], current["taskArn"]) from None
    observation = EVIDENCE.collect(current, reservation, response, clock())
    fresh_enough(observation, required_after)
    retained = retain(path, observation, reservation)
    progress("terminal-proof-retained")
    return {"receipt": retained, "path": path, "reused": False}
