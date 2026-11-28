#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.resource-reservation
#   version: 4
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Retain immutable resource-operation intent before a single submission while workload bindings own request validation and file identity.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.library.entity-smoke.resource-control
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/implementation/resource-control.py
#   - id: deploy.library.aws.session-records
#     path: scripts/04.deploy/shared/provider-adapters/aws/session_records.py
#   - id: deploy.library.entity-smoke.task-control
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/implementation/task-control.py
"""Extracted resource reservation mechanics, not approval or completion evidence.

Bindings supply a closed request/path validator, timestamp reader and historical
schema/operation prefix. Existing local files are never replaced, including after
an uncertain write or provider outcome. Optional storage owns remote retention;
credentials and provider transport remain at that adapter, not this protocol.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import uuid


class ReservationFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def no_symlinks(path):
    if not path.is_absolute() or ".." in path.parts or any(part.is_symlink() for part in (path, *path.parents)):
        raise ReservationFailure("path-invalid")


def write_exclusive(path, value):
    no_symlinks(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical(value) + b"\n"); stream.flush(); os.fsync(stream.fileno())
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
    except FileExistsError: return False
    except (OSError, ValueError, TypeError, UnicodeError): raise ReservationFailure("retention-not-confirmed") from None
    return True


class ImmutableReservationStore:
    """Bind requests; optional storage owns retention, not reserve/reuse policy."""
    schema = None
    operation_prefix = None
    failure = ReservationFailure

    def __init__(self, root, *, storage=None):
        self.root = Path(root) if storage is None else root
        self._storage = storage
        if not isinstance(self.schema, str) or not self.schema or not isinstance(self.operation_prefix, str) or re.fullmatch(r"[a-z][a-z0-9-]*-", self.operation_prefix) is None:
            raise self.failure("reservation-binding-invalid")
        if storage is None:
            no_symlinks(self.root)
        elif not callable(getattr(storage, "read", None)) or not callable(getattr(storage, "create", None)):
            raise self.failure("reservation-storage-invalid")

    def path_for(self, phase, request):
        """Validate the closed request, then return its one canonical file path."""
        raise NotImplementedError

    def validate_time(self, value):
        raise NotImplementedError

    def read(self, phase, request):
        path = self.path_for(phase, request)
        if self._storage is not None:
            try: previous = self._storage.read(path)
            except ReservationFailure as failure: raise self.failure(failure.code) from None
            if previous is None: return None
            return self.validate_record(phase, request, previous, validate_time=self.validate_time)
        no_symlinks(path)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as stream: raw = stream.read(65537)
            if len(raw) > 65536: raise self.failure("reservation-unavailable")
            previous = json.loads(raw)
        except FileNotFoundError: return None
        except (OSError, ValueError, TypeError, UnicodeError): raise self.failure("reservation-unavailable") from None
        return self.validate_record(phase, request, previous, validate_time=self.validate_time)

    @classmethod
    def validate_record(cls, phase, request, previous, *, validate_time):
        """Validate captured immutable bytes without claiming they remain stored."""
        if not (isinstance(previous, dict) and set(previous) == {"schema", "phase", "operation_id", "request", "request_sha256", "reserved_at"} and previous.get("schema") == cls.schema and previous.get("phase") == phase and previous.get("request") == request and previous.get("request_sha256") == hashlib.sha256(canonical(request)).hexdigest() and isinstance(previous.get("operation_id"), str) and re.fullmatch(re.escape(cls.operation_prefix) + r"[a-f0-9]{32}", previous["operation_id"]) is not None):
            raise cls.failure("reservation-mismatch")
        validate_time(previous.get("reserved_at"))
        return previous

    def make_record(self, phase, request):
        """Bindings may preserve a historical shape without copying retention."""
        return {"schema": self.schema, "phase": phase,
                "operation_id": self.operation_prefix + uuid.uuid4().hex, "request": request,
                "request_sha256": hashlib.sha256(canonical(request)).hexdigest(),
                "reserved_at": datetime.now(timezone.utc).isoformat()}

    def reserve(self, phase, request):
        path = self.path_for(phase, request)
        value = self.make_record(phase, request)
        try: fresh = write_exclusive(path, value) if self._storage is None else self._storage.create(path, value)
        except ReservationFailure as failure: raise self.failure(failure.code) from None
        if type(fresh) is not bool: raise self.failure("retention-not-confirmed")
        if fresh: return value, True
        previous = self.read(phase, request)
        if previous is None: raise self.failure("reservation-unavailable")
        return previous, False
