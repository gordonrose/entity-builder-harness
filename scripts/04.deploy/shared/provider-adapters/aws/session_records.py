#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.session-records
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Serialize temporary-session admission and immutable operation intent through conditional versioned S3 retention.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.library.aws.environment-sessions
#     path: scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py
"""One target object, no retry, reopening, completion claim or provider factory.

The caller must check actual storage protection and operation authority in guard.
This helper cannot establish IAM deadlines, lifecycle mode or cleanup completion.
Lost/conflicting writes never grant submission authority, even if later observed.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLI = _load("aws_session_cli", "cli.py")
RESERVATIONS = _load("aws_session_reservations", "resource_reservation.py")
LIMIT = 65536
SCHEMA = "aws-temporary-session/v1"
_NAME = r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}"
_OPERATION = r"(?:creation|activation|prepare-discard):[A-Za-z][A-Za-z0-9-]{0,127}:(?:prepare|execute)"
CLI_FAILURE_CODES = ("aws-access-denied", "aws-credentials-expired", "aws-command-timeout",
                     "aws-command-unavailable", "aws-response-invalid", "aws-parameter-invalid", "aws-command-failed")


class SessionRecordFailure(RESERVATIONS.ReservationFailure):
    """Finite owner-level failure; no provider body, key or credential content."""


def _duplicate_safe(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SessionRecordFailure("session-record-invalid")
        result[key] = value
    return result


def _opaque(value, limit):
    return isinstance(value, str) and 0 < len(value) <= limit and value != "null" and all(32 <= ord(char) < 127 for char in value)


class SessionRecords:
    """Checked caller context plus a single conditional versioned target record.

    guard(action, binding) must return None only after checking observed storage
    protections and applicable authority; a boolean never proves those checks.
    It runs before every remote use. Creation and activation additionally need
    the caller's effective AWS deadline, which this software clock cannot replace.
    """
    def __init__(self, *, bucket, key, account, region, profile, environment,
                 binding, guard, clock):
        if not (isinstance(bucket, str) and re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket)
                and isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9/._=-]{0,1023}", key)
                and ".." not in key.split("/") and "//" not in key
                and isinstance(account, str) and re.fullmatch(r"[0-9]{12}", account)
                and isinstance(region, str) and re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region)
                and isinstance(profile, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@+=,-]{0,127}", profile)
                and isinstance(environment, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in environment.items())
                and callable(guard) and callable(clock)):
            raise SessionRecordFailure("session-context-invalid")
        if not (isinstance(binding, dict) and set(binding) == {"target", "scope", "session_id", "source_inputs_sha256", "starts_at", "expires_at"}
                and all(isinstance(binding[field], str) and re.fullmatch(_NAME, binding[field]) for field in ("target", "scope", "session_id"))
                and isinstance(binding["source_inputs_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", binding["source_inputs_sha256"])
                and all(type(binding[field]) is int and binding[field] >= 0 for field in ("starts_at", "expires_at"))
                and binding["starts_at"] < binding["expires_at"]):
            raise SessionRecordFailure("session-binding-invalid")
        self.bucket, self.key, self.account, self.region, self.profile = bucket, key, account, region, profile
        self._binding, self._guard, self._clock = copy.deepcopy(binding), guard, clock
        self._environment = {**environment, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": "",
                             "AWS_CLI_AUTO_PROMPT": "off", "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS": "true"}

    @property
    def binding(self):
        return copy.deepcopy(self._binding)

    def _authorize(self, action):
        try:
            if self._guard(action, self.binding) is not None:
                raise SessionRecordFailure("session-protection-unconfirmed")
        except Exception:
            raise SessionRecordFailure("session-protection-unconfirmed") from None

    def _now(self):
        try:
            value = self._clock()
        except Exception:
            raise SessionRecordFailure("session-clock-invalid") from None
        if type(value) is not int or value < 0:
            raise SessionRecordFailure("session-clock-invalid")
        return value

    def _open(self, document):
        now = self._now()
        if document["state"] != "open" or not self._binding["starts_at"] <= now < self._binding["expires_at"]:
            raise SessionRecordFailure("session-admission-closed")

    def _bytes(self, document):
        try:
            raw = RESERVATIONS.canonical(document)
        except (TypeError, ValueError, UnicodeError, RecursionError):
            raise SessionRecordFailure("session-record-invalid") from None
        if len(raw) > LIMIT:
            raise SessionRecordFailure("session-record-too-large")
        return raw

    def _validate(self, document):
        if not (isinstance(document, dict) and set(document) == {"schema", "binding", "account", "region", "state", "operations"}
                and document["schema"] == SCHEMA and document["state"] in ("open", "sealed")
                and isinstance(document["operations"], dict)
                and all(isinstance(key, str) and re.fullmatch(_OPERATION, key) and isinstance(value, dict)
                        for key, value in document["operations"].items())):
            raise SessionRecordFailure("session-record-invalid")
        if self._bytes(document["binding"]) != self._bytes(self._binding) or document["account"] != self.account or document["region"] != self.region:
            raise SessionRecordFailure("session-binding-mismatch")
        self._bytes(document)
        return document

    def _arguments(self, operation):
        return ["aws", "s3api", operation, "--bucket", self.bucket, "--key", self.key,
                "--expected-bucket-owner", self.account, "--profile", self.profile,
                "--region", self.region, "--output", "json", "--no-cli-pager",
                "--no-cli-auto-prompt", "--cli-connect-timeout", "10", "--cli-read-timeout", "20"]

    def _invoke(self, arguments):
        return CLI.invoke_json(arguments, timeout=35, empty_body="reject", object_only=True,
                               environment=self._environment)

    def _read(self):
        self._authorize("read")
        try:
            with tempfile.TemporaryDirectory(prefix="aws-session-record-") as directory:
                os.chmod(directory, 0o700)
                path = Path(directory) / "record.json"
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                os.close(descriptor)
                metadata = self._invoke(self._arguments("get-object") + ["--range", "bytes=0-65536", str(path)])
                descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(descriptor, "rb") as stream:
                    raw = stream.read(LIMIT + 1)
                if len(raw) > LIMIT:
                    raise SessionRecordFailure("session-record-too-large")
                content_range = re.fullmatch(r"bytes 0-([0-9]+)/([0-9]+)", metadata.get("ContentRange", "")) if isinstance(metadata.get("ContentRange"), str) else None
                if not (raw and type(metadata.get("ContentLength")) is int and metadata["ContentLength"] == len(raw)
                        and content_range and int(content_range[1]) + 1 == len(raw) == int(content_range[2])
                        and _opaque(metadata.get("ETag"), 256) and _opaque(metadata.get("VersionId"), 1024)):
                    raise SessionRecordFailure("session-record-unconfirmed")
                document = json.loads(raw.decode("utf-8"), object_pairs_hook=_duplicate_safe,
                                      parse_constant=lambda _: (_ for _ in ()).throw(SessionRecordFailure("session-record-invalid")))
                return self._validate(document), metadata["ETag"], metadata["VersionId"]
        except CLI.CliFailure as failure:
            if failure.code == "aws-resource-missing":
                return None
            code = failure.code if failure.code in CLI_FAILURE_CODES else "aws-command-failed"
            raise SessionRecordFailure("session-record-unavailable:" + code) from None
        except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
            raise SessionRecordFailure("session-record-invalid") from None

    def _write(self, document, prior, action):
        raw = self._bytes(self._validate(document))
        self._authorize(action)
        try:
            with tempfile.TemporaryDirectory(prefix="aws-session-record-") as directory:
                os.chmod(directory, 0o700)
                path = Path(directory) / "record.json"
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(raw); stream.flush(); os.fsync(stream.fileno())
                condition = ["--if-none-match", "*"] if prior is None else ["--if-match", prior[1]]
                metadata = self._invoke(self._arguments("put-object") + ["--body", str(path), "--content-type", "application/json"] + condition)
        except CLI.CliFailure as failure:
            reason = failure.code if failure.code in CLI_FAILURE_CODES else "aws-command-failed"
            code = "session-record-conflict" if failure.code == "aws-condition-conflict" else "session-retention-unconfirmed:" + reason
            raise SessionRecordFailure(code) from None
        except (OSError, ValueError, TypeError, UnicodeError):
            raise SessionRecordFailure("session-retention-unconfirmed") from None
        if not (_opaque(metadata.get("ETag"), 256) and _opaque(metadata.get("VersionId"), 1024)):
            raise SessionRecordFailure("session-retention-unconfirmed")
        observed = self._read()
        if observed is None or observed[1:] != (metadata["ETag"], metadata["VersionId"]) or self._bytes(observed[0]) != raw:
            raise SessionRecordFailure("session-retention-unconfirmed")
        return observed[0]

    def initialize(self):
        """Retain the first binding; an existing binding never reopens or resets."""
        self._authorize("initialize")
        prior = self._read()
        if prior is not None:
            return copy.deepcopy(prior[0])
        document = {"schema": SCHEMA, "binding": self.binding, "account": self.account,
                    "region": self.region, "state": "open", "operations": {}}
        self._open(document)
        return self._write(document, None, "initialize")

    def seal(self):
        """Close admission without dropping or claiming completion of any intent."""
        self._authorize("seal")
        prior = self._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        document = copy.deepcopy(prior[0])
        if document["state"] == "sealed":
            return document
        document["state"] = "sealed"
        return self._write(document, prior, "seal")

    def storage(self, kind):
        if kind not in ("creation", "activation", "prepare-discard"):
            raise SessionRecordFailure("session-operation-invalid")
        return _Storage(self, kind)


class _Storage:
    """Transport seam only; the existing reservation owner validates its records."""
    def __init__(self, owner, kind):
        self.owner, self.kind = owner, kind

    def _key(self, key):
        if not isinstance(key, str) or re.fullmatch(_OPERATION, self.kind + ":" + key) is None:
            raise SessionRecordFailure("session-operation-invalid")
        return self.kind + ":" + key

    def read(self, key):
        key = self._key(key)
        prior = self.owner._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        return copy.deepcopy(prior[0]["operations"].get(key))

    def create(self, key, record):
        key = self._key(key)
        if not isinstance(record, dict):
            raise SessionRecordFailure("session-operation-invalid")
        prior = self.owner._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        document = copy.deepcopy(prior[0])
        if key in document["operations"]:
            return False
        if self.kind in ("creation", "activation"):
            self.owner._open(document)
        elif document["state"] != "sealed":
            raise SessionRecordFailure("session-admission-open")
        document["operations"][key] = copy.deepcopy(record)
        self.owner._write(document, prior, "reserve-" + self.kind)
        return True
