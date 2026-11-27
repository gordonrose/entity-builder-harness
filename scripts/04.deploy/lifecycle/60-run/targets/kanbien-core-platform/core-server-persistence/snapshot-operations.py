#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.core-persistence.snapshot-operations
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.core-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind fixed baseline recovery snapshots to shared immutable intent and single-submission mechanics.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.create-persistence-recovery-point.impl
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/create-recovery-point/script.py
"""New executions have lineage; historical observation stays with its reader."""
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import re
import subprocess


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


SHARED = Path(__file__).resolve().parents[5] / "shared/provider-adapters/aws"
RESERVATIONS = module("persistence_snapshot_reservations", SHARED / "resource_reservation.py")
SNAPSHOTS = module("persistence_snapshot_execution", SHARED / "snapshots.py")
DATABASE = "kanbien-core-platform-persistence"
PATTERN = re.compile(r"^kanbien-core-platform-persistence-recovery-[0-9]{8}(?:-[a-z0-9]{1,8})?$")
ROOT = Path(__file__).resolve().parents[7]


class OperationFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None: raise ValueError()
        return parsed
    except (ValueError, TypeError, AttributeError):
        raise OperationFailure("persistence-recovery-point-time-invalid") from None


class Store(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/persistence-snapshot-reservation/v1"
    operation_prefix = "kp-"
    failure = staticmethod(lambda code: OperationFailure("persistence-recovery-point-" + code))

    def path_for(self, phase, request):
        if (phase != "create-recovery-point" or not isinstance(request, dict)
                or set(request) != {"database", "snapshot", "source_resource_id"}
                or request["database"] != DATABASE or not isinstance(request["snapshot"], str)
                or PATTERN.fullmatch(request["snapshot"]) is None
                or not isinstance(request["source_resource_id"], str)
                or re.fullmatch(r"db-[A-Za-z0-9]+", request["source_resource_id"]) is None):
            raise self.failure("request-invalid")
        return self.root / (request["snapshot"] + ".json")

    def validate_time(self, value):
        timestamp(value)


def store(root):
    try:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "--absolute-git-dir"],
            capture_output=True, text=True, check=True, timeout=10)
        location = Path(result.stdout.strip())
        if not location.is_absolute(): raise ValueError()
        return Store(location / "persistence-snapshots")
    except (OSError, ValueError, subprocess.SubprocessError, UnicodeError):
        raise OperationFailure("persistence-recovery-point-store-unavailable") from None


def reserve_resource_cost(phase, request, reserve):
    """Price the original under the existing goal budget, never submit here."""
    native_failure = None
    def original():
        nonlocal native_failure
        try: return reserve()
        except Exception as failure:
            native_failure = failure
            raise
    try:
        owner = module("persistence_recovery_cost", Path(__file__).resolve().parents[4] / "50-deploy/capabilities/scheduling-control/script.py")
        return owner.reserve_recovery_cost_admission(target="kanbien-core-platform", scope="core-server-persistence",
            phase=phase, request=request, reserve=original)
    except Exception as failure:
        if failure is native_failure: raise
        raise OperationFailure("persistence-recovery-cost-admission-not-confirmed") from None


def scheduling_resource_census():
    return store(ROOT).records()


def proof_cleanup_admission(original, *, required=False):
    """Only a new proof-budget original can select the expanded cleanup rule."""
    try:
        owner = module("persistence_recovery_cleanup", Path(__file__).resolve().parents[4] / "50-deploy/capabilities/scheduling-control/script.py")
        if not required and not owner.cost_intent_active(target="kanbien-core-platform"): return
        if owner.recovery_cleanup_admission(target="kanbien-core-platform", scope="core-server-persistence", original=original) != original:
            raise ValueError()
    except Exception:
        raise OperationFailure("persistence-recovery-cleanup-admission-not-confirmed") from None


def create(m, root, snapshot, resource_id, emit, observe):
    request = {"database": DATABASE, "snapshot": snapshot, "source_resource_id": resource_id}
    facts = {"snapshot": snapshot}
    def precondition(reservation):
        ok, _, code = m.aws("rds", "describe-db-snapshots", "--db-snapshot-identifier", snapshot)
        if ok: raise OperationFailure("persistence-recovery-point-already-exists")
        if code != "aws-resource-missing": raise OperationFailure(code)
    def provider(service, operation, **arguments):
        if service != "rds" or operation != "create-db-snapshot":
            raise OperationFailure("persistence-recovery-point-operation-invalid")
        ok, value, code = m.aws(service, operation, "--db-instance-identifier", arguments["DBInstanceIdentifier"],
            "--db-snapshot-identifier", arguments["DBSnapshotIdentifier"], "--tags", json.dumps(arguments["Tags"], sort_keys=True))
        if not ok: raise SNAPSHOTS.ProviderFailure(code)
        return value
    def arguments(reservation):
        return {"DBInstanceIdentifier": DATABASE, "DBSnapshotIdentifier": snapshot, "Tags": [
            {"Key": "Target", "Value": "kanbien-core-platform"},
            {"Key": "Scope", "Value": "core-server-persistence"},
            {"Key": "Operation", "Value": reservation["operation_id"]}]}
    def observation(reservation, fresh):
        if fresh: return emit("pending", "persistence-recovery-point-submitted", facts=facts)
        return observe(m, snapshot, reservation=reservation)
    try:
        owned = store(root)
        return SNAPSHOTS.create(provider, owned, phase="create-recovery-point", request=request,
            arguments=arguments, precondition=precondition,
            validate_reservation=lambda reservation: None, observe=observation,
            reserve=lambda: reserve_resource_cost("create-recovery-point", request,
                lambda: owned.reserve("create-recovery-point", request)))
    except OperationFailure as failure:
        return emit("blocked", failure.code, facts=facts)
    except SNAPSHOTS.SnapshotFailure as failure:
        return emit("uncertain", failure.provider_code or "persistence-recovery-point-submission-uncertain", facts=facts)
    except RESERVATIONS.ReservationFailure:
        return emit("blocked", "persistence-recovery-point-store-unavailable", facts=facts)
