#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.task-journal
#   version: 4
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Share task-operation predecessor decisions across locked local and conditional retained storage before a single submission.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.library.core-persistence.task-operations
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/task-operations.py
#   - id: deploy.command.kanbien-core-platform.verify-core-server-persistence-candidate
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh
"""Existing baseline journal mechanics; bindings retain schemas and proof readers.

This is not a provider capability or another release ledger. Local callers hold
the lock throughout reservation/submission/observation. Retained storage owns
atomic head/history retention and admission; no filesystem lock is imitated.
A missing initialized journal never grants permission to submit again.
"""
import contextlib
import copy
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


def with_integrity(value):
    body = {key: item for key, item in value.items() if key != "integrity"}
    return {**body, "integrity": hashlib.sha256(canonical(body)).hexdigest()}


def attach_retained(storage, key, value, *, method, argument, validate_record):
    """Attach one task/proof fact only after exact positive retained readback.

    The binding owns record/proof validation. Storage owns atomic retention;
    this comparison is neither freshness nor permission to launch a task.
    """
    try:
        expected = copy.deepcopy(value)
        if method == "retain_task" and isinstance(argument, str) and argument:
            fields = {"task_arn": argument}
        elif method == "retain_proof" and isinstance(argument, dict) and set(argument) == {"path", "sha256"} and all(isinstance(item, str) and item for item in argument.values()):
            fields = {"proof_receipt": argument["path"], "proof_sha256": argument["sha256"]}
        else: raise ValueError()
        if any(expected[name] not in (None, item) for name, item in fields.items()): raise ValueError()
        proposed = with_integrity({**expected, **fields})
        if validate_record(copy.deepcopy(proposed)) != proposed: raise ValueError()
        observed = getattr(storage, method)(key, copy.deepcopy(expected), copy.deepcopy(argument))
        checked = validate_record(copy.deepcopy(observed))
        if not isinstance(checked, dict) or checked != proposed: raise ValueError()
    except Exception: raise JournalFailure("operation-retention-not-confirmed") from None
    value.clear(); value.update(checked)


def save(path, value):
    value = with_integrity(value)
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


def select_reservation(value, *, request, new_operation, expected, completed_proof):
    """Pure choice over a checked record and its already-validated proof result."""
    if value is not None:
        if new_operation and value["operation_id"] == expected:
            if completed_proof is None: raise JournalFailure("prior-operation-not-complete")
            return True, value["operation_id"]
        else:
            if new_operation and value["predecessor"] != expected:
                raise JournalFailure("operation-predecessor-mismatch")
            if value["request"] != request: raise JournalFailure("operation-request-changed")
            return False, value["predecessor"]
    else:
        if new_operation and expected is not None: raise JournalFailure("operation-predecessor-missing")
        return True, None


def new_record(schema, mode, request, predecessor):
    return {"schema": schema, "mode": mode, "operation_id": "kp-" + uuid.uuid4().hex,
            "predecessor": predecessor, "request": request, "task_arn": None,
            "proof_receipt": None, "proof_sha256": None}


def reserve(path, descriptor, value, *, schema, marker, mode, request, new_operation,
            expected, completed):
    """Compare-and-reserve with the caller's validated terminal proof reader."""
    proof = completed(value) if value is not None and new_operation and value["operation_id"] == expected else None
    fresh, predecessor = select_reservation(value, request=request, new_operation=new_operation,
                                           expected=expected, completed_proof=proof)
    if not fresh: return value, False
    if value is not None:
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
    value = new_record(schema, mode, request, predecessor)
    save(path, value)
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.write(descriptor, marker); os.fsync(descriptor)
    return value, True


def reserve_retained(storage, key, *, schema, mode, request, new_operation,
                     expected, completed, validate_record):
    """Reserve once through checked storage, without granting runtime admission.

    read(key) returns the current record or None. compare_and_reserve(key,
    expected_record, proposed_record) atomically retains the exact head and any
    predecessor history; only literal True confirms it. The storage adapter also
    owns missing-initialized-head rejection and session admission. A second read
    must positively confirm the proposal. No conflict or uncertainty is retried.
    validate_record is the binding's existing record validator, not a new schema.
    """
    if not all(callable(item) for item in (getattr(storage, "read", None),
            getattr(storage, "compare_and_reserve", None), validate_record, completed)):
        raise JournalFailure("operation-storage-invalid")

    def checked_read():
        try: observed = copy.deepcopy(storage.read(key))
        except Exception: raise JournalFailure("operation-store-unavailable") from None
        if observed is None: return None
        checked = validate_record(copy.deepcopy(observed))
        if not isinstance(checked, dict) or checked != observed:
            raise JournalFailure("operation-metadata-invalid")
        return checked

    value = checked_read()
    proof = completed(copy.deepcopy(value)) if value is not None and new_operation and value["operation_id"] == expected else None
    fresh, predecessor = select_reservation(value, request=request, new_operation=new_operation,
                                           expected=expected, completed_proof=proof)
    if not fresh: return value, False
    proposed = with_integrity(new_record(schema, mode, copy.deepcopy(request), predecessor))
    checked = validate_record(copy.deepcopy(proposed))
    if not isinstance(checked, dict) or checked != proposed:
        raise JournalFailure("operation-metadata-invalid")
    try: retained = storage.compare_and_reserve(key, copy.deepcopy(value), copy.deepcopy(proposed))
    except Exception: raise JournalFailure("operation-retention-not-confirmed") from None
    if retained is not True: raise JournalFailure("operation-retention-not-confirmed")
    observed = checked_read()
    if observed != proposed: raise JournalFailure("operation-retention-not-confirmed")
    return observed, True
