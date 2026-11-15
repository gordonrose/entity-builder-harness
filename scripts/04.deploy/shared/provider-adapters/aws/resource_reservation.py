#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.resource-reservation
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Retain immutable resource-operation intent before a single submission while workload bindings own request validation and file identity.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.library.entity-smoke.resource-control
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/resource-control.py
"""Extracted resource reservation mechanics, not approval or completion evidence.

Bindings supply a closed request/path validator, timestamp reader and historical
schema/operation prefix. Existing files are never replaced, including after an
uncertain write or provider outcome. No credentials or provider calls live here.
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
    """Subclass only the workload binding, never the write/read/reuse protocol."""
    schema = None
    operation_prefix = None
    failure = ReservationFailure

    def __init__(self, root):
        self.root = Path(root)
        if not isinstance(self.schema, str) or not self.schema or not isinstance(self.operation_prefix, str) or re.fullmatch(r"[a-z][a-z0-9-]*-", self.operation_prefix) is None:
            raise self.failure("reservation-binding-invalid")
        no_symlinks(self.root)

    def path_for(self, phase, request):
        """Validate the closed request, then return its one canonical file path."""
        raise NotImplementedError

    def validate_time(self, value):
        raise NotImplementedError

    def read(self, phase, request):
        path = self.path_for(phase, request)
        no_symlinks(path)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as stream: raw = stream.read(65537)
            if len(raw) > 65536: raise self.failure("reservation-unavailable")
            previous = json.loads(raw)
        except FileNotFoundError: return None
        except (OSError, ValueError, TypeError, UnicodeError): raise self.failure("reservation-unavailable") from None
        if not (isinstance(previous, dict) and set(previous) == {"schema", "phase", "operation_id", "request", "request_sha256", "reserved_at"} and previous.get("schema") == self.schema and previous.get("phase") == phase and previous.get("request") == request and previous.get("request_sha256") == hashlib.sha256(canonical(request)).hexdigest() and isinstance(previous.get("operation_id"), str) and re.fullmatch(re.escape(self.operation_prefix) + r"[a-f0-9]{32}", previous["operation_id"]) is not None):
            raise self.failure("reservation-mismatch")
        self.validate_time(previous.get("reserved_at"))
        return previous

    def reserve(self, phase, request):
        path = self.path_for(phase, request)
        value = {"schema": self.schema, "phase": phase,
                 "operation_id": self.operation_prefix + uuid.uuid4().hex, "request": request,
                 "request_sha256": hashlib.sha256(canonical(request)).hexdigest(),
                 "reserved_at": datetime.now(timezone.utc).isoformat()}
        try: fresh = write_exclusive(path, value)
        except ReservationFailure as failure: raise self.failure(failure.code) from None
        if fresh: return value, True
        previous = self.read(phase, request)
        if previous is None: raise self.failure("reservation-unavailable")
        return previous, False
