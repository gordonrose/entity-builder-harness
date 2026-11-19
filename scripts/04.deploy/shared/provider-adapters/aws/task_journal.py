#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.task-journal
#   version: 2
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Preserve the existing locked task-operation journal and predecessor protocol before a single submission.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.library.core-persistence.task-operations
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/task-operations.py
#   - id: deploy.command.kanbien-core-platform.verify-core-server-persistence-candidate
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh
"""Existing baseline journal mechanics; bindings retain schemas and proof readers.

This is not a provider capability or another release ledger. A caller must hold
the lock throughout reservation/submission/observation. A missing initialized
journal never grants permission to submit again.
"""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid


class JournalFailure(Exception):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def directory(parent, name):
    parent = Path(parent)
    if not parent.is_absolute() or not parent.is_dir():
        raise JournalFailure("operation-store-unavailable")
    path = parent / name
    try:
        path.mkdir(mode=0o700)
        descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
    except FileExistsError: pass
    if path.is_symlink() or path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
        raise JournalFailure("operation-store-unsafe")
    return path


def save(path, value):
    body = {key: item for key, item in value.items() if key != "integrity"}
    value = {**body, "integrity": hashlib.sha256(canonical(body)).hexdigest()}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(canonical(value)); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)


def read(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor) as handle:
        info = os.fstat(handle.fileno())
        if info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1 or info.st_size > 65536:
            raise ValueError()
        return json.load(handle)


@contextlib.contextmanager
def locked(path, lock_path, marker, read_value):
    if path.exists() and not lock_path.exists():
        raise JournalFailure("operation-metadata-missing")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try: fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise JournalFailure("operation-busy") from None
        info = os.fstat(descriptor)
        if info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1:
            raise JournalFailure("operation-store-unsafe")
        observed = os.read(descriptor, 128)
        if observed not in {b"", marker}: raise JournalFailure("operation-metadata-invalid")
        if observed and not path.exists(): raise JournalFailure("operation-metadata-missing")
        value = read_value(path) if path.exists() else None
        if value is not None and not observed:
            os.write(descriptor, marker); os.fsync(descriptor)
        yield path, descriptor, value
    finally: os.close(descriptor)


def reserve(path, descriptor, value, *, schema, marker, mode, request, new_operation,
            expected, completed):
    """Compare-and-reserve with the caller's validated terminal proof reader."""
    if value is not None:
        if new_operation and value["operation_id"] == expected:
            if completed(value) is None: raise JournalFailure("prior-operation-not-complete")
            # Preserve the original operation before advancing the existing
            # journal. Recovery may still need its failed candidate evidence.
            history = directory(path.parent, "history")
            retained = history / (value["operation_id"] + ".json")
            if retained.exists():
                if read(retained) != value: raise JournalFailure("operation-metadata-invalid")
            else:
                raw = canonical(value)
                fd = os.open(retained, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(raw); stream.flush(); os.fsync(stream.fileno())
                fd = os.open(history, os.O_RDONLY | os.O_DIRECTORY)
                try: os.fsync(fd)
                finally: os.close(fd)
            predecessor = value["operation_id"]
        else:
            if new_operation and value["predecessor"] != expected:
                raise JournalFailure("operation-predecessor-mismatch")
            if value["request"] != request: raise JournalFailure("operation-request-changed")
            return value, False
    else:
        if new_operation and expected is not None: raise JournalFailure("operation-predecessor-missing")
        predecessor = None
    value = {"schema": schema, "mode": mode, "operation_id": "kp-" + uuid.uuid4().hex,
             "predecessor": predecessor, "request": request, "task_arn": None,
             "proof_receipt": None, "proof_sha256": None}
    save(path, value)
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.write(descriptor, marker); os.fsync(descriptor)
    return value, True
