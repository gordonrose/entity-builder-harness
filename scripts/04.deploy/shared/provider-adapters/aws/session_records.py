#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.session-records
#   version: 6
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
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
"""One conditional parent and versioned children, no retry or provider factory.

The caller must check actual storage protection and operation authority in guard.
This helper cannot establish IAM deadlines, lifecycle mode or cleanup completion.
Lost/conflicting writes never grant submission authority, even if later observed.
"""
import copy
from datetime import datetime
import hashlib
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
CHILD_LIMIT = 1048576
SCHEMA = "aws-temporary-session/v10"
OPERATION_SCHEMA = "deploy/environment-session-operation/v1"
SHA = re.compile(r"[a-f0-9]{64}")
_NAME = r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}"
_OPERATION = (r"(?:(?:creation|activation|prepare-discard):[A-Za-z][A-Za-z0-9-]{0,127}:(?:prepare|execute)|"
              r"delete:[A-Za-z][A-Za-z0-9-]{0,127}:delete)")
_INPUT = r"(?:creation|activation|prepare-discard):[A-Za-z][A-Za-z0-9-]{0,127}"
CLI_FAILURE_CODES = ("aws-access-denied", "aws-credentials-expired", "aws-command-timeout",
                     "aws-command-unavailable", "aws-response-invalid", "aws-parameter-invalid", "aws-command-failed")
CUSTODY_FIELDS = ("creation_request_sha256", "change_set_id_sha256", "template_sha256",
                  "parameters_sha256", "resources_sha256")
TERMINAL_STATES = {
    "prepare": frozenset(("CREATE_COMPLETE", "FAILED")),
    "creation": frozenset(("CREATE_COMPLETE", "CREATE_FAILED", "ROLLBACK_COMPLETE", "ROLLBACK_FAILED")),
    "activation": frozenset(("UPDATE_COMPLETE", "UPDATE_FAILED", "UPDATE_ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_FAILED")),
    "prepare-discard": frozenset(("UPDATE_COMPLETE", "UPDATE_FAILED", "UPDATE_ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_FAILED")),
    "delete": frozenset(("DELETE_COMPLETE", "DELETE_FAILED")),
}


def operations_sha256(document):
    return hashlib.sha256(RESERVATIONS.canonical({key: value for key, value in document["operations"].items()
                                                if not key.startswith("delete:")})).hexdigest()


def cleanup_terminal(resource):
    """Inactive ECS definitions/services/clusters are not running resources."""
    return isinstance(resource, dict) and (resource.get("status") in ("absent", "never-allocated")
        or resource.get("status") == "inactive" and resource.get("resource_type") in
        {"AWS::ECS::TaskDefinition", "AWS::ECS::Service", "AWS::ECS::Cluster"})


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


def checked_time(value):
    if not (isinstance(value, str) and len(value) <= 32 and re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{6})?\+00:00", value)):
        raise SessionRecordFailure("session-reservation-time-invalid")
    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise SessionRecordFailure("session-reservation-time-invalid") from None


def checked_execution_roles(value, *, account, session_id):
    """Validate captured role identity shape, never effective IAM authority."""
    prefix = "s-" + session_id[:19] + "-"
    if not (isinstance(value, dict) and set(value) == {"creation", "cleanup"}
            and all(isinstance(role, str) and re.fullmatch(
                re.escape("arn:aws:iam::" + account + ":role/" + prefix)
                + r"[A-Za-z0-9][A-Za-z0-9-]*", role)
                and len(role.rsplit("/", 1)[-1]) <= 64 for role in value.values())
            and len({role.casefold() for role in value.values()}) == 2):
        raise SessionRecordFailure("session-record-shape-invalid")
    return copy.deepcopy(value)


def operation_request(document, kind, stack, arguments_sha256, *, resolved_sha256=None, stack_id=None):
    """One closed request shape for actual consumers and the capacity envelope."""
    shape = document["base"]["cleanup_shapes"][stack]
    result = {"kind": kind, "stack": stack, "template_reference": shape["template_reference"],
              "source_plan_sha256": document["base"]["source_plan_sha256"],
              "base_sha256": document["base_sha256"], "arguments_sha256": arguments_sha256}
    if kind == "delete":
        result["stack_id"] = stack_id
    else:
        result.update(change_set=stack + {"creation": "-session-create", "activation": "-session-activate",
                                         "prepare-discard": "-session-discard"}[kind],
                      resolved_inputs_sha256=resolved_sha256, disable_rollback=True)
    return result


class SessionRecords:
    """Checked caller context plus a single conditional versioned target record.

    guard(action, binding) must return None only after checking observed storage
    protections and applicable authority; a boolean never proves those checks.
    It runs before every remote use. Creation and activation additionally need
    the caller's effective AWS deadline, which this software clock cannot replace.
    """
    def __init__(self, *, bucket, key, account, region, profile, environment,
                 binding, guard, clock, successor=None):
        if not (isinstance(bucket, str) and re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket)
                and isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9/._=-]{0,1023}", key)
                and ".." not in key.split("/") and "//" not in key
                and isinstance(account, str) and re.fullmatch(r"[0-9]{12}", account)
                and isinstance(region, str) and re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region)
                and (profile is None or isinstance(profile, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@+=,-]{0,127}", profile))
                and isinstance(environment, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in environment.items())
                and callable(guard) and callable(clock) and (successor is None or callable(successor))):
            raise SessionRecordFailure("session-context-invalid")
        if not (isinstance(binding, dict) and set(binding) == {"target", "scope", "session_id", "source_inputs_sha256", "starts_at", "expires_at"}
                and all(isinstance(binding[field], str) and re.fullmatch(_NAME, binding[field]) for field in ("target", "scope", "session_id"))
                and isinstance(binding["source_inputs_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", binding["source_inputs_sha256"])
                and all(type(binding[field]) is int and binding[field] >= 0 for field in ("starts_at", "expires_at"))
                and binding["starts_at"] < binding["expires_at"]):
            raise SessionRecordFailure("session-binding-invalid")
        self.bucket, self.key, self.account, self.region, self.profile = bucket, key, account, region, profile
        self._binding, self._guard, self._clock = copy.deepcopy(binding), guard, clock
        self._successor = successor
        self._environment = {**environment, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": "",
                             "AWS_CLI_AUTO_PROMPT": "off", "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS": "true"}
        if profile is None:
            self._environment.pop("AWS_PROFILE", None)
            self._environment.pop("AWS_DEFAULT_PROFILE", None)

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
        if not (isinstance(document, dict) and set(document) == {"schema", "binding", "account", "region", "state", "operations", "base", "base_sha256", "resolved", "incarnations", "creation_evidence", "creation_custody", "operation_outcomes", "physical_resources", "task_state", "functional_result", "cleanup_completion"}
                and document["schema"] == SCHEMA and document["state"] in ("open", "sealed", "deleting")
                and (document["functional_result"] is None or document["functional_result"] in
                     ({"status": "succeeded"}, {"status": "failed"}, {"status": "interrupted"}))
                and (document["cleanup_completion"] is None or document["state"] != "open"
                     and document["functional_result"] is not None
                     and self._child_reference(document["cleanup_completion"], CHILD_LIMIT))
                and (document["task_state"] is None or self._child_reference(document["task_state"], CHILD_LIMIT))
                and isinstance(document["base"], dict) and isinstance(document["resolved"], dict)
                and document["base_sha256"] == hashlib.sha256(self._bytes(document["base"])).hexdigest()
                and all(isinstance(key, str) and re.fullmatch(_INPUT, key)
                        and isinstance(row, dict) and set(row) == {"inputs", "sha256"}
                        and isinstance(row["inputs"], dict)
                        and row["sha256"] == hashlib.sha256(self._bytes(row["inputs"])).hexdigest()
                        for key, row in document["resolved"].items())
                and isinstance(document["operations"], dict)
                and all(isinstance(key, str) and re.fullmatch(_OPERATION, key) and isinstance(value, dict)
                        for key, value in document["operations"].items())):
            raise SessionRecordFailure("session-record-invalid")
        if self._bytes(document["binding"]) != self._bytes(self._binding) or document["account"] != self.account or document["region"] != self.region:
            raise SessionRecordFailure("session-binding-mismatch")
        try:
            self._validate_shapes(document)
        except (KeyError, TypeError, ValueError, AttributeError):
            raise SessionRecordFailure("session-record-shape-invalid") from None
        self._bytes(document)
        return document

    def _stack_id(self, stack, value):
        prefix = "arn:aws:cloudformation:" + self.region + ":" + self.account + ":stack/" + stack + "/"
        return isinstance(value, str) and len(value) <= 2048 and re.fullmatch(re.escape(prefix) + r"[A-Za-z0-9][A-Za-z0-9-]*", value) is not None

    def _validate_shapes(self, document):
        def require(condition):
            if not condition:
                raise SessionRecordFailure("session-record-shape-invalid")
        base = document["base"]
        require(set(base) == {"source_plan_sha256", "choices", "publications", "packages", "provider_facts", "cleanup_shapes", "lifecycle_max_duration_seconds", "task_selections_sha256", "task_selection_count", "execution_roles"}
                and isinstance(base["task_selections_sha256"], str) and SHA.fullmatch(base["task_selections_sha256"])
                and type(base["task_selection_count"]) is int and 0 < base["task_selection_count"] <= 256
                and type(base["lifecycle_max_duration_seconds"]) is int
                and base["lifecycle_max_duration_seconds"] >= self.binding["expires_at"] - self.binding["starts_at"]
                and isinstance(base["source_plan_sha256"], str) and SHA.fullmatch(base["source_plan_sha256"]))
        checked_execution_roles(base["execution_roles"], account=self.account, session_id=self.binding["session_id"])
        shapes = base["cleanup_shapes"]
        require(isinstance(shapes, dict) and bool(shapes))
        for stack, shape in shapes.items():
            require(isinstance(stack, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,111}", stack)
                    and isinstance(shape, dict) and set(shape) == {"template_reference", "discard", "resource_count", "resources_sha256", "bindings_sha256", "relationships_count", "databases_count", "namespaces_count"}
                    and isinstance(shape["template_reference"], str) and bool(shape["template_reference"])
                    and type(shape["discard"]) is bool and type(shape["resource_count"]) is int
                    and 0 < shape["resource_count"] <= LIMIT // 64
                    and all(type(shape[key + "_count"]) is int and 0 <= shape[key + "_count"] <= shape["resource_count"] for key in ("relationships", "databases", "namespaces"))
                    and all(isinstance(shape[key], str) and SHA.fullmatch(shape[key]) for key in ("resources_sha256", "bindings_sha256")))
        require(all(isinstance(document[field], dict) for field in
                    ("incarnations", "creation_evidence", "creation_custody", "operation_outcomes", "physical_resources")))
        for stack, value in document["incarnations"].items():
            require(stack in shapes and self._stack_id(stack, value))
        for key, row in document["resolved"].items():
            kind, stack = key.split(":")
            require(stack in shapes)
            inputs = row["inputs"]
            if kind == "creation":
                require(set(inputs) == {"values", "producer_stacks"} and isinstance(inputs["values"], dict)
                        and all(isinstance(k, str) and isinstance(v, str) for k, v in inputs["values"].items())
                        and isinstance(inputs["producer_stacks"], list)
                        and all(isinstance(value, str) and value in document["creation_evidence"] for value in inputs["producer_stacks"])
                        and inputs["producer_stacks"] == sorted(set(inputs["producer_stacks"])))
            else:
                require(set(inputs) == {"observed_values_sha256"} and isinstance(inputs["observed_values_sha256"], str)
                        and SHA.fullmatch(inputs["observed_values_sha256"]) and stack in document["creation_evidence"]
                        and (kind != "prepare-discard" or shapes[stack]["discard"]))
        for key, row in document["operations"].items():
            kind, stack, phase = key.split(":")
            require(stack in shapes and set(row) == {"schema", "phase", "operation_id", "request", "request_sha256", "reserved_at"}
                    and row["schema"] == OPERATION_SCHEMA and row["phase"] == phase
                    and isinstance(row["operation_id"], str) and re.fullmatch(r"es-[a-f0-9]{32}", row["operation_id"]))
            checked_time(row["reserved_at"])
            request = row["request"]
            require(isinstance(request, dict) and isinstance(request.get("arguments_sha256"), str) and SHA.fullmatch(request["arguments_sha256"]))
            if kind == "delete":
                require(self._stack_id(stack, request.get("stack_id"))
                        and document["incarnations"].get(stack) == request["stack_id"]
                        and stack in document["physical_resources"])
                expected = operation_request(document, kind, stack, request["arguments_sha256"], stack_id=request["stack_id"])
            else:
                require(request.get("disable_rollback") is True
                        and (kind != "prepare-discard" or shapes[stack]["discard"]))
                expected = operation_request(document, kind, stack, request["arguments_sha256"],
                                             resolved_sha256=document["resolved"][kind + ":" + stack]["sha256"])
            require(request == expected and row["request_sha256"] == hashlib.sha256(self._bytes(request)).hexdigest())
        require(any(key.startswith("delete:") for key in document["operations"]) == (document["state"] == "deleting"))
        for stack, proof in document["creation_custody"].items():
            require(stack in document["incarnations"] and isinstance(proof, dict) and set(proof) == set(CUSTODY_FIELDS)
                    and all(isinstance(value, str) and SHA.fullmatch(value) for value in proof.values())
                    and document["operations"]["creation:" + stack + ":prepare"]["request_sha256"] == proof["creation_request_sha256"]
                    and proof["resources_sha256"] == shapes[stack]["resources_sha256"])
        for stack, physical in document["physical_resources"].items():
            self._physical_shape(document, stack, physical)
        for key, outcome in document["operation_outcomes"].items():
            require(key in document["operations"]
                    and isinstance(outcome, dict) and set(outcome) == {"request_sha256", "status", "evidence_sha256", "observed_at"}
                    and outcome["request_sha256"] == document["operations"][key]["request_sha256"]
                    and isinstance(outcome["evidence_sha256"], str) and SHA.fullmatch(outcome["evidence_sha256"]))
            kind, _, phase = key.split(":")
            require(outcome["status"] == "not-submitted" or outcome["status"] in TERMINAL_STATES["prepare" if phase == "prepare" else kind])
            checked_time(outcome["observed_at"])
        for stack, proof in document["creation_evidence"].items():
            require(stack in document["incarnations"] and isinstance(proof, dict)
                    and set(proof) == {"creation_request_sha256", "change_set_id_sha256", "creation_event_id_sha256"}
                    and all(isinstance(value, str) and SHA.fullmatch(value) for value in proof.values()))
            prepared = document["operations"]["creation:" + stack + ":prepare"]
            executed = document["operations"]["creation:" + stack + ":execute"]
            require(prepared["request"] == executed["request"] and prepared["request_sha256"] == proof["creation_request_sha256"])
            require(stack in document["creation_custody"] and all(proof[key] == document["creation_custody"][stack][key]
                    for key in ("creation_request_sha256", "change_set_id_sha256")))

    def _physical_shape(self, document, stack, physical):
        shape = document["base"]["cleanup_shapes"].get(stack)
        if not (shape is not None and stack in document["incarnations"] and stack in document["creation_custody"]
                and isinstance(physical, dict) and set(physical) == {"stack_id_sha256", "slots", "observation_sha256", "observed_at", "relationships", "databases", "namespaces"}
                and physical["stack_id_sha256"] == hashlib.sha256(self._bytes(document["incarnations"][stack])).hexdigest()
                and isinstance(physical["observation_sha256"], str) and SHA.fullmatch(physical["observation_sha256"])
                and isinstance(physical["slots"], list) and len(physical["slots"]) == shape["resource_count"]
                and all(isinstance(slot, str) and (slot in ("unknown", "never-allocated") or SHA.fullmatch(slot))
                        for slot in physical["slots"])):
            raise SessionRecordFailure("session-physical-invalid")
        for key in ("relationships", "databases", "namespaces"):
            pattern = re.compile(r"[A-Z0-9]{1,32}") if key == "namespaces" else SHA
            if not (isinstance(physical[key], list) and len(physical[key]) == shape[key + "_count"]
                    and all(isinstance(value, str) and (value == "unknown" or pattern.fullmatch(value)) for value in physical[key])):
                raise SessionRecordFailure("session-physical-invalid")
        checked_time(physical["observed_at"])
        if "never-allocated" in physical["slots"]:
            key = "creation:" + stack + ":execute"
            if (document["state"] not in ("sealed", "deleting")
                    or any(slot != "never-allocated" for slot in physical["slots"])
                    or any(value != "unknown" for key in ("relationships", "databases", "namespaces") for value in physical[key])
                    or key in document["operations"] and document["operation_outcomes"].get(key, {}).get("status") != "not-submitted"):
                raise SessionRecordFailure("session-physical-invalid")

    def _completion_size(self, document):
        """Upper bound for existing admitted stacks, never untouched branches."""
        virtual = copy.deepcopy(document)
        virtual["task_state"] = {"sha256": "f" * 64, "version_id": "\\" * 1024, "bytes": CHILD_LIMIT}
        virtual["functional_result"] = {"status": "interrupted"}
        virtual["cleanup_completion"] = {"sha256": "f" * 64, "version_id": "\\" * 1024, "bytes": CHILD_LIMIT}
        virtual["state"] = "deleting"
        admitted = {key.split(":")[1] for key in document["operations"] if key.startswith("creation:")}
        for stack in sorted(admitted):
            prefix = "arn:aws:cloudformation:" + self.region + ":" + self.account + ":stack/" + stack + "/"
            stack_id = virtual["incarnations"].setdefault(stack, prefix + "x" * (2048 - len(prefix)))
            virtual["creation_evidence"].setdefault(stack, {key: "f" * 64 for key in
                ("creation_request_sha256", "change_set_id_sha256", "creation_event_id_sha256")})
            virtual["creation_custody"].setdefault(stack, {key: "f" * 64 for key in CUSTODY_FIELDS})
            # Expand unknowns even in an already retained partial projection.
            virtual["physical_resources"][stack] = {
                "stack_id_sha256": "f" * 64,
                "slots": ["f" * 64] * document["base"]["cleanup_shapes"][stack]["resource_count"],
                **{key: [("Z" * 32 if key == "namespaces" else "f" * 64)] * document["base"]["cleanup_shapes"][stack][key + "_count"]
                   for key in ("relationships", "databases", "namespaces")},
                "observation_sha256": "f" * 64, "observed_at": "9999-12-31T23:59:59.999999+00:00"}
            kinds = ["delete"]
            if document["base"]["cleanup_shapes"][stack]["discard"]:
                kinds.insert(0, "prepare-discard")
                entry = {"observed_values_sha256": "f" * 64}
                virtual["resolved"].setdefault("prepare-discard:" + stack,
                    {"inputs": entry, "sha256": hashlib.sha256(RESERVATIONS.canonical(entry)).hexdigest()})
            for kind in kinds:
                request = operation_request(virtual, kind, stack, "f" * 64, stack_id=stack_id,
                    resolved_sha256=None if kind == "delete" else virtual["resolved"][kind + ":" + stack]["sha256"])
                for phase in (("delete",) if kind == "delete" else ("prepare", "execute")):
                    virtual["operations"].setdefault(kind + ":" + stack + ":" + phase,
                        {"schema": OPERATION_SCHEMA, "phase": phase, "operation_id": "es-" + "f" * 32,
                         "request": request, "request_sha256": "f" * 64,
                         "reserved_at": "9999-12-31T23:59:59.999999+00:00"})
        for key in virtual["operations"]:
            virtual["operation_outcomes"].setdefault(key, {"request_sha256": "f" * 64,
                "status": "DELETE_COMPLETE" if key.startswith("delete:") else "UPDATE_ROLLBACK_COMPLETE",
                "evidence_sha256": "f" * 64, "observed_at": "9999-12-31T23:59:59.999999+00:00"})
        return len(RESERVATIONS.canonical(virtual))

    def _arguments(self, operation, *, key=None):
        return ["aws", "s3api", operation, "--bucket", self.bucket, "--key", self.key if key is None else key,
                "--expected-bucket-owner", self.account, *(["--profile", self.profile] if self.profile is not None else []),
                "--region", self.region, "--output", "json", "--no-cli-pager",
                "--no-cli-auto-prompt", "--cli-connect-timeout", "10", "--cli-read-timeout", "20"]

    def _invoke(self, arguments):
        return CLI.invoke_json(arguments, timeout=35, empty_body="reject", object_only=True,
                               environment=self._environment)

    def _read_bytes(self, *, key=None, limit=LIMIT, version_id=None, child=False):
        """One private byte transport; callers own binding and payload checks."""
        prefix = "session-child" if child else "session-record"
        with tempfile.TemporaryDirectory(prefix="aws-session-record-") as directory:
            os.chmod(directory, 0o700)
            path = Path(directory) / "record.json"
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.close(descriptor)
            selected = [] if version_id is None else ["--version-id", version_id]
            metadata = self._invoke(self._arguments("get-object", key=key) + selected + ["--range", f"bytes=0-{limit}", str(path)])
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as stream:
                raw = stream.read(limit + 1)
            if len(raw) > limit:
                raise SessionRecordFailure(prefix + "-too-large")
            content_range = re.fullmatch(r"bytes 0-([0-9]+)/([0-9]+)", metadata.get("ContentRange", "")) if isinstance(metadata.get("ContentRange"), str) else None
            if not (raw and type(metadata.get("ContentLength")) is int and metadata["ContentLength"] == len(raw)
                    and content_range and int(content_range[1]) + 1 == len(raw) == int(content_range[2])
                    and _opaque(metadata.get("ETag"), 256) and _opaque(metadata.get("VersionId"), 1024)
                    and (version_id is None or metadata["VersionId"] == version_id)):
                raise SessionRecordFailure(prefix + "-unconfirmed")
            return raw, metadata

    def _write_bytes(self, raw, *, key=None, etag=None, child=False):
        with tempfile.TemporaryDirectory(prefix="aws-session-record-") as directory:
            os.chmod(directory, 0o700)
            path = Path(directory) / "record.json"
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            condition = ["--if-none-match", "*"] if etag is None else ["--if-match", etag]
            return self._invoke(self._arguments("put-object", key=key) + ["--body", str(path), "--content-type",
                "application/octet-stream" if child else "application/json"] + condition)

    def _read(self):
        self._authorize("read")
        try:
            raw, metadata = self._read_bytes()
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
        if self._completion_size(document) > LIMIT:
            raise SessionRecordFailure("session-cleanup-capacity-exceeded")
        self._authorize(action)
        try:
            metadata = self._write_bytes(raw, etag=None if prior is None else prior[1])
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

    def _child_payload(self, raw, max_bytes):
        if type(max_bytes) is not int or max_bytes not in (LIMIT, CHILD_LIMIT):
            raise SessionRecordFailure("session-child-limit-invalid")
        if type(raw) is not bytes or not raw or len(raw) > max_bytes:
            raise SessionRecordFailure("session-child-payload-invalid")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _child_reference(reference, limit):
        return (isinstance(reference, dict) and set(reference) == {"sha256", "version_id", "bytes"}
                and isinstance(reference["sha256"], str) and SHA.fullmatch(reference["sha256"])
                and _opaque(reference["version_id"], 1024) and type(reference["bytes"]) is int
                and 0 < reference["bytes"] <= limit)

    def _child_key(self, digest):
        return "session-children/" + hashlib.sha256(self.key.encode()).hexdigest() + "/" + self._binding["session_id"] + "/" + digest

    def _child_observation(self, digest, size, max_bytes, *, version_id=None, missing=False):
        self.observe_existing()
        self._authorize("read-child")
        try:
            raw, metadata = self._read_bytes(key=self._child_key(digest), limit=max_bytes, version_id=version_id, child=True)
        except CLI.CliFailure as failure:
            if missing and failure.code == "aws-resource-missing":
                return None
            code = failure.code if failure.code in CLI_FAILURE_CODES or failure.code == "aws-resource-missing" else "aws-command-failed"
            raise SessionRecordFailure("session-child-unavailable:" + code) from None
        except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
            raise SessionRecordFailure("session-child-unconfirmed") from None
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
            raise SessionRecordFailure("session-child-reference-mismatch")
        return raw, {"sha256": digest, "version_id": metadata["VersionId"], "bytes": len(raw)}, metadata["ETag"]

    def _observe_child(self, raw, *, max_bytes=LIMIT):
        """Recover exact retained bytes, not freshness or retry authority."""
        digest = self._child_payload(raw, max_bytes)
        observed = self._child_observation(digest, len(raw), max_bytes, missing=True)
        if observed is None:
            return None
        confirmed = self._child_observation(digest, len(raw), max_bytes, version_id=observed[1]["version_id"])
        if confirmed != observed:
            raise SessionRecordFailure("session-child-unconfirmed")
        return observed[1]

    def _read_child(self, reference, *, max_bytes=LIMIT):
        if type(max_bytes) is not int or max_bytes not in (LIMIT, CHILD_LIMIT):
            raise SessionRecordFailure("session-child-limit-invalid")
        if not (isinstance(reference, dict) and set(reference) == {"sha256", "version_id", "bytes"}
                and isinstance(reference["sha256"], str) and SHA.fullmatch(reference["sha256"])
                and _opaque(reference["version_id"], 1024) and type(reference["bytes"]) is int
                and 0 < reference["bytes"] <= max_bytes):
            raise SessionRecordFailure("session-child-reference-invalid")
        return self._child_observation(reference["sha256"], reference["bytes"], max_bytes,
                                       version_id=reference["version_id"])[0]

    def _retain_child(self, raw, *, max_bytes=LIMIT):
        """Create one immutable object; only a later parent CAS can adopt it."""
        digest = self._child_payload(raw, max_bytes)
        self.observe_existing()
        self._authorize("retain-child")
        try:
            metadata = self._write_bytes(raw, key=self._child_key(digest), child=True)
        except CLI.CliFailure as failure:
            if failure.code == "aws-condition-conflict":
                raise SessionRecordFailure("session-child-conflict") from None
            code = failure.code if failure.code in CLI_FAILURE_CODES else "aws-command-failed"
            raise SessionRecordFailure("session-child-retention-unconfirmed:" + code) from None
        except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
            raise SessionRecordFailure("session-child-retention-unconfirmed") from None
        if not (_opaque(metadata.get("ETag"), 256) and _opaque(metadata.get("VersionId"), 1024)):
            raise SessionRecordFailure("session-child-retention-unconfirmed")
        observed = self._child_observation(digest, len(raw), max_bytes, version_id=metadata["VersionId"])
        if observed[0] != raw or observed[2] != metadata["ETag"]:
            raise SessionRecordFailure("session-child-retention-unconfirmed")
        return observed[1]

    def _initialization_prior(self):
        """A trusted native guard may admit a completed foreign predecessor only.

        The same protected/versioned key and its original ETag own the CAS;
        this is not deletion, a reset flag or replacement of historical versions.
        """
        try:
            return self._read()
        except SessionRecordFailure as failure:
            if failure.code != "session-binding-mismatch" or self._successor is None:
                raise
        raw, metadata = self._read_bytes()
        try:
            document = json.loads(raw, object_pairs_hook=_duplicate_safe,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            def readonly(action, _binding):
                if action not in {"read", "read-child"}:
                    raise SessionRecordFailure("session-predecessor-read-only")
                return self._guard(action, self.binding)
            old = SessionRecords(bucket=self.bucket, key=self.key, account=self.account, region=self.region,
                profile=self.profile, environment=self._environment, binding=document["binding"], guard=readonly, clock=self._clock)
            document = old._validate(document)
            if (document["binding"] == self.binding or document["binding"]["target"] != self.binding["target"]
                    or document["state"] not in {"sealed", "deleting"} or document["cleanup_completion"] is None
                    or old.observe_cleanup_completion() is None):
                raise SessionRecordFailure("session-predecessor-unfinished")
            if self._successor(old, copy.deepcopy(document)) is not None:
                raise SessionRecordFailure("session-predecessor-unconfirmed")
            observed = old._read()
            if observed is None or observed[1:] != (metadata["ETag"], metadata["VersionId"]) or self._bytes(observed[0]) != raw:
                raise SessionRecordFailure("session-predecessor-changed")
            return observed
        except SessionRecordFailure: raise
        except Exception:
            raise SessionRecordFailure("session-predecessor-unconfirmed") from None

    def initialize(self, base):
        """Retain new inputs, or CAS past a natively closed completed predecessor."""
        if not isinstance(base, dict):
            raise SessionRecordFailure("session-inputs-invalid")
        base = copy.deepcopy(base)
        self._authorize("initialize")
        prior = self._initialization_prior()
        if prior is not None and prior[0]["binding"] == self.binding:
            if self._bytes(prior[0]["base"]) != self._bytes(base):
                raise SessionRecordFailure("session-inputs-mismatch")
            return copy.deepcopy(prior[0])
        document = {"schema": SCHEMA, "binding": self.binding, "account": self.account,
                    "region": self.region, "state": "open", "operations": {}, "base": base,
                    "base_sha256": hashlib.sha256(self._bytes(base)).hexdigest(), "resolved": {},
                    "incarnations": {}, "creation_evidence": {}, "creation_custody": {}, "operation_outcomes": {},
                    "physical_resources": {}, "task_state": None, "functional_result": None, "cleanup_completion": None}
        self._open(document)
        return self._write(document, prior, "initialize")

    def observe_initialization(self):
        """Read before acquisition; a genuinely absent object still must be open."""
        prior = self._initialization_prior()
        if prior is None or prior[0]["binding"] != self.binding:
            self._open({"state": "open"})
            return None
        return copy.deepcopy(prior[0])

    def check_input_admission(self, kind):
        if kind in ("creation", "activation"):
            self._open(self.observe_existing()["document"])
        elif kind == "prepare-discard":
            if self.observe_existing()["document"]["state"] != "sealed":
                raise SessionRecordFailure("session-admission-open")
        else:
            raise SessionRecordFailure("session-operation-invalid")

    def retain_inputs(self, kind, stack, base_sha256, inputs):
        """Append once, with CAS and positive readback before any reservation."""
        key = kind + ":" + stack if isinstance(kind, str) and isinstance(stack, str) else ""
        if not re.fullmatch(_INPUT, key) or not isinstance(inputs, dict):
            raise SessionRecordFailure("session-inputs-invalid")
        prior = self._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        document = copy.deepcopy(prior[0])
        if document["base_sha256"] != base_sha256:
            raise SessionRecordFailure("session-inputs-mismatch")
        row = {"inputs": copy.deepcopy(inputs), "sha256": hashlib.sha256(self._bytes(inputs)).hexdigest()}
        if key in document["resolved"]:
            if document["resolved"][key] != row:
                raise SessionRecordFailure("session-inputs-mismatch")
            return copy.deepcopy(row)
        if kind in ("creation", "activation"):
            self._open(document)
        elif document["state"] != "sealed":
            raise SessionRecordFailure("session-admission-open")
        document["resolved"][key] = row
        return copy.deepcopy(self._write(document, prior, "resolve-" + kind)["resolved"][key])

    def observe_existing(self):
        """Read a positive versioned record and current clock without any write."""
        prior = self._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        return {"document": copy.deepcopy(prior[0]), "version_id": prior[2], "observed_at": self._now()}

    def retain_ownership(self, stack, stack_id, evidence=None, *, custody=None, outcomes=None, physical=None):
        """Append checked provider custody once; callers own its observation proof."""
        prior = self._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        document = copy.deepcopy(prior[0])
        rows = [("incarnations", stack, stack_id)]
        if evidence is not None:
            rows.append(("creation_evidence", stack, copy.deepcopy(evidence)))
        if custody is not None:
            rows.append(("creation_custody", stack, copy.deepcopy(custody)))
        if outcomes is not None:
            if not isinstance(outcomes, dict):
                raise SessionRecordFailure("session-outcome-invalid")
            rows.extend(("operation_outcomes", key, copy.deepcopy(value)) for key, value in outcomes.items())
        changed = False
        for field, key, value in rows:
            if key in document[field]:
                if document[field][key] != value:
                    raise SessionRecordFailure("session-ownership-mismatch")
            else:
                document[field][key] = value
                changed = True
        if physical is not None:
            physical = copy.deepcopy(physical)
            self._physical_shape(document, stack, physical)
            previous = document["physical_resources"].get(stack)
            if previous is not None:
                for key in ("slots", "relationships", "databases", "namespaces"):
                    merged = []
                    for known, observed in zip(previous[key], physical[key]):
                        if known != "unknown" and observed not in ("unknown", known):
                            raise SessionRecordFailure("session-physical-identity-mismatch")
                        merged.append(observed if known == "unknown" else known)
                    physical[key] = merged
                if all(physical[key] == previous[key] for key in ("slots", "relationships", "databases", "namespaces")):
                    physical = previous
            if previous != physical:
                document["physical_resources"][stack] = physical
                changed = True
        return self._write(document, prior, "retain-ownership") if changed else copy.deepcopy(document)

    def retain_outcome(self, key, outcome):
        """Append a reservation-bound observation; never replace a prior outcome."""
        prior = self._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        document = copy.deepcopy(prior[0])
        if key in document["operation_outcomes"]:
            if document["operation_outcomes"][key] != outcome:
                raise SessionRecordFailure("session-outcome-mismatch")
            return document
        document["operation_outcomes"][key] = copy.deepcopy(outcome)
        return self._write(document, prior, "retain-outcome")

    def seal(self):
        """Close admission without dropping or claiming completion of any intent."""
        self._authorize("seal")
        prior = self._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        document = copy.deepcopy(prior[0])
        if document["state"] in ("sealed", "deleting"):
            return document
        document["state"] = "sealed"
        return self._write(document, prior, "seal")

    def retain_functional(self, result):
        """Retain the terminal test verdict once, independently of cleanup."""
        if result not in ({"status": "succeeded"}, {"status": "failed"}, {"status": "interrupted"}):
            raise SessionRecordFailure("session-functional-result-invalid")
        prior = self._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        document = copy.deepcopy(prior[0])
        if document["functional_result"] is not None:
            if document["functional_result"] != result:
                raise SessionRecordFailure("session-functional-result-conflict")
            return copy.deepcopy(result)
        document["functional_result"] = copy.deepcopy(result)
        return self._write(document, prior, "retain-functional-result")["functional_result"]

    def _cleanup_evidence(self, document, evidence):
        if document["state"] == "open" or document["functional_result"] is None:
            raise SessionRecordFailure("session-completion-unready")
        if not (isinstance(evidence, dict) and set(evidence) == {"schema", "binding", "source_plan_sha256", "stacks"}
                and evidence["schema"] == "deploy/environment-session-cleanup/v1"
                and evidence["binding"] == self.binding
                and evidence["source_plan_sha256"] == document["base"]["source_plan_sha256"]
                and isinstance(evidence["stacks"], dict)
                and set(evidence["stacks"]) == set(document["base"]["cleanup_shapes"])):
            raise SessionRecordFailure("session-completion-evidence-invalid")
        for stack, row in evidence["stacks"].items():
            preparation = "creation:" + stack + ":prepare"
            if preparation not in document["operations"]:
                if row != {"status": "not-started"}:
                    raise SessionRecordFailure("session-completion-evidence-invalid")
                continue
            if (document["operation_outcomes"].get(preparation, {}).get("status") == "not-submitted"
                    and "creation:" + stack + ":execute" not in document["operations"]):
                if row != {"status": "not-submitted"}:
                    raise SessionRecordFailure("session-completion-evidence-invalid")
                continue
            deletion = "delete:" + stack + ":delete"
            resources = row.get("resources") if isinstance(row, dict) else None
            if not (isinstance(row, dict) and set(row) == {"status", "resources"} and row["status"] == "removed"
                    and document["operation_outcomes"].get(deletion, {}).get("status") == "DELETE_COMPLETE"
                    and isinstance(resources, list)
                    and len(resources) == document["base"]["cleanup_shapes"][stack]["resource_count"]
                    and all(cleanup_terminal(resource)
                            and all(isinstance(artifact, dict) and artifact.get("status") in ("absent", "never-allocated")
                                    for artifact in resource.get("artifacts", [])) for resource in resources)):
                raise SessionRecordFailure("session-completion-evidence-invalid")
            if any(resource.get("status") == "inactive" for resource in resources):
                index = {resource.get("logical_id"): resource.get("resource_type") for resource in resources}
                if (len(index) != len(resources) or None in index or None in index.values()
                        or hashlib.sha256(RESERVATIONS.canonical(index)).hexdigest() != document["base"]["cleanup_shapes"][stack]["resources_sha256"]):
                    raise SessionRecordFailure("session-completion-evidence-invalid")
        return RESERVATIONS.canonical(evidence)

    def observe_cleanup_completion(self):
        """Read the original checked completion without granting teardown authority."""
        prior = self._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        reference = prior[0]["cleanup_completion"]
        if reference is None:
            return None
        raw = self._read_child(reference, max_bytes=CHILD_LIMIT)
        try:
            evidence = json.loads(raw, object_pairs_hook=_duplicate_safe,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if self._cleanup_evidence(prior[0], evidence) != raw:
                raise ValueError()
        except SessionRecordFailure:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise SessionRecordFailure("session-completion-evidence-invalid") from None
        return {"status": "completed", "reference": copy.deepcopy(reference)}

    def retain_cleanup_completion(self, evidence):
        """Only the concrete adapter supplies native cleanup evidence here."""
        prior = self._read()
        if prior is None:
            raise SessionRecordFailure("session-record-unavailable")
        document = copy.deepcopy(prior[0])
        raw = self._cleanup_evidence(document, evidence)
        if document["cleanup_completion"] is not None:
            if self._read_child(document["cleanup_completion"], max_bytes=CHILD_LIMIT) != raw:
                raise SessionRecordFailure("session-completion-conflict")
            return copy.deepcopy(document["cleanup_completion"])
        reference = self._observe_child(raw, max_bytes=CHILD_LIMIT)
        document["cleanup_completion"] = reference or self._retain_child(raw, max_bytes=CHILD_LIMIT)
        return self._write(document, prior, "retain-cleanup-completion")["cleanup_completion"]

    def storage(self, kind, *, reconciled_operations_sha256=None, physical_manifest_sha256=None):
        if kind not in ("creation", "activation", "prepare-discard", "delete"):
            raise SessionRecordFailure("session-operation-invalid")
        return _Storage(self, kind, reconciled_operations_sha256, physical_manifest_sha256)

    def task_storage(self, selections, index, *, validate_record, validate_receipt, record_selection, key_for_record=None, before_submit=None):
        return _TaskStorage(self, selections, index, validate_record, validate_receipt, record_selection, key_for_record, before_submit)

    def observe_task_state(self, selections):
        """Observe the same bound task envelope used by every native storage slot."""
        self.check_task_capacity(selections)
        return copy.deepcopy(self._task_state(selections)[1])

    def read_report(self, selections, phase):
        if phase not in ("functional", "cleanup"):
            raise SessionRecordFailure("session-report-phase-invalid")
        prior, state = self._task_state(selections)
        return self._report_value(prior, state, phase)

    def _report_value(self, prior, state, phase):
        reference = state["reports"][phase]
        if reference is None:
            return None
        try:
            report = json.loads(self._read_child(reference, max_bytes=CHILD_LIMIT),
                object_pairs_hook=_duplicate_safe, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if not (isinstance(report, dict) and set(report) == {"schema", "binding", "source_plan_sha256", "phase", "result"}
                    and report["schema"] == "deploy/environment-session-report/v1"
                    and report["binding"] == self.binding
                    and report["source_plan_sha256"] == prior[0]["base"]["source_plan_sha256"]
                    and report["phase"] == phase and isinstance(report["result"], dict)):
                raise ValueError()
        except SessionRecordFailure: raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise SessionRecordFailure("session-report-invalid") from None
        return copy.deepcopy(report["result"])

    def retain_report(self, selections, phase, result):
        """Safe caller projections only; reports never grant provider authority."""
        if phase not in ("functional", "cleanup") or not isinstance(result, dict):
            raise SessionRecordFailure("session-report-invalid")
        prior, state = self._task_state(selections)
        previous = self._report_value(prior, state, phase)
        if previous is not None:
            if previous == result:
                return False
            if phase == "functional":
                raise SessionRecordFailure("session-report-conflict")
        try:
            raw = RESERVATIONS.canonical({"schema": "deploy/environment-session-report/v1",
                "binding": self.binding, "source_plan_sha256": prior[0]["base"]["source_plan_sha256"],
                "phase": phase, "result": copy.deepcopy(result)})
        except (TypeError, ValueError, RecursionError):
            raise SessionRecordFailure("session-report-invalid") from None
        state["reports"][phase] = self._retain_child(raw, max_bytes=CHILD_LIMIT)
        document = copy.deepcopy(prior[0])
        document["task_state"] = self._retain_child(RESERVATIONS.canonical(state), max_bytes=CHILD_LIMIT)
        self._write(document, prior, "retain-session-report")
        return True

    def reserve_network_binding(self, selections, request):
        """Only the confirmed fresh CAS writer may submit this setup effect."""
        prior, state = self._task_state(selections)
        self._open(prior[0])
        if not (isinstance(request, dict) and set(request) == {"RoleArn", "VpcId"}
                and request["RoleArn"] == prior[0]["base"]["execution_roles"]["creation"]
                and isinstance(request["VpcId"], str) and re.fullmatch(r"vpc-[0-9a-f]{8}(?:[0-9a-f]{9})?", request["VpcId"])):
            raise SessionRecordFailure("session-network-binding-invalid")
        raw = RESERVATIONS.canonical({"schema": "deploy/session-network-binding/v1", "binding": self.binding,
            "base_sha256": prior[0]["base_sha256"], "request": request})
        if state["network_binding"] is not None:
            if self._read_child(state["network_binding"], max_bytes=LIMIT) != raw:
                raise SessionRecordFailure("session-network-binding-conflict")
            return False
        state["network_binding"] = self._retain_child(raw, max_bytes=LIMIT)
        document = copy.deepcopy(prior[0])
        document["task_state"] = self._retain_child(RESERVATIONS.canonical(state), max_bytes=CHILD_LIMIT)
        self._write(document, prior, "reserve-network-binding")
        return True

    def _task_state(self, selections):
        def require(value, reason="invalid"):
            if not value: raise SessionRecordFailure("session-task-" + reason)
        prior = self._read()
        require(prior is not None, "parent-unavailable")
        document = prior[0]
        digest = hashlib.sha256(RESERVATIONS.canonical(selections)).hexdigest()
        require(document["base"]["task_selections_sha256"] == digest
                      and document["base"]["task_selection_count"] == len(selections), "selection-mismatch")
        expected = {"schema": "deploy/session-task-state/v5", "binding": self.binding,
                    "base_sha256": document["base_sha256"], "source_plan_sha256": document["base"]["source_plan_sha256"],
                    "selections": selections, "slots": [None] * len(selections),
                    "reports": {"functional": None, "cleanup": None}, "network_binding": None}
        try:
            state = expected if document["task_state"] is None else json.loads(
                self._read_child(document["task_state"], max_bytes=CHILD_LIMIT).decode("utf-8"),
                object_pairs_hook=_duplicate_safe, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except SessionRecordFailure: raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise SessionRecordFailure("session-task-payload-invalid") from None
        require(isinstance(state, dict) and set(state) == set(expected)
                      and all(state[key] == expected[key] for key in expected if key not in ("slots", "reports", "network_binding"))
                      and (state["network_binding"] is None or self._child_reference(state["network_binding"], LIMIT))
                      and isinstance(state["slots"], list) and len(state["slots"]) == len(selections)
                      and isinstance(state["reports"], dict) and set(state["reports"]) == {"functional", "cleanup"}
                      and all(value is None or self._child_reference(value, CHILD_LIMIT) for value in state["reports"].values()),
                      "state-invalid")
        for slot in state["slots"]:
            require(slot is None or isinstance(slot, dict) and set(slot) == {"intent", "current", "receipt", "admission", "context", "stop"}
                and all(self._child_reference(slot[key], LIMIT) for key in ("intent", "current"))
                and slot["admission"] in (None, "admitted", "not-submitted")
                and (slot["context"] is None or self._child_reference(slot["context"], CHILD_LIMIT))
                and (slot["stop"] is None or self._child_reference(slot["stop"], LIMIT))
                and (slot["receipt"] is None or isinstance(slot["receipt"], dict) and set(slot["receipt"]) == {"label", "reference"}
                     and isinstance(slot["receipt"]["label"], str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,255}", slot["receipt"]["label"])
                     and self._child_reference(slot["receipt"]["reference"], CHILD_LIMIT)), "state-invalid")
        return prior, state

    def check_task_capacity(self, selections):
        if not isinstance(selections, list) or not selections or len(selections) > 256:
            raise SessionRecordFailure("session-task-capacity-exceeded")
        reference = {"sha256": "f" * 64, "version_id": "\\" * 1024, "bytes": CHILD_LIMIT}
        state = {"schema": "deploy/session-task-state/v5", "binding": self.binding,
                 "base_sha256": "f" * 64, "source_plan_sha256": "f" * 64, "selections": selections,
                 "reports": {"functional": reference, "cleanup": reference}, "network_binding": {**reference, "bytes": LIMIT},
                 "slots": [{"intent": reference, "current": reference,
                            "receipt": {"label": "x" * 255, "reference": reference}, "admission": "not-submitted", "context": reference, "stop": reference}
                           for _ in selections]}
        try: size = len(RESERVATIONS.canonical(state))
        except (TypeError, ValueError, UnicodeError, RecursionError):
            raise SessionRecordFailure("session-task-capacity-exceeded") from None
        if size > CHILD_LIMIT:
            raise SessionRecordFailure("session-task-capacity-exceeded")


class _TaskStorage:
    """One source-selected slot; native owners validate opaque task payloads.

    Child writes are not reservations. Only the positively observed parent CAS
    adopts a slot. Neither existing heads nor cold readers acquire freshness.
    Native validation/selection callbacks are trusted code seams, not caller
    data. Their controller binding and final authority remain separate duties.
    """
    def __init__(self, owner, selections, index, validate_record, validate_receipt, record_selection, key_for_record, before_submit):
        self.owner = owner
        self.index = index
        self.validate_record, self.validate_receipt = validate_record, validate_receipt
        self.record_selection = record_selection
        self.key_for_record, self.authority = key_for_record, before_submit
        self.fresh = None
        if (not isinstance(selections, list) or not selections or type(index) is not int or not 0 <= index < len(selections)
                or not callable(validate_record) or not callable(validate_receipt) or not callable(record_selection)
                or key_for_record is not None and not callable(key_for_record)
                or before_submit is not None and not callable(before_submit)):
            raise SessionRecordFailure("session-task-selection-invalid")
        try: self.selections = copy.deepcopy(selections)
        except (TypeError, ValueError, RecursionError):
            raise SessionRecordFailure("session-task-selection-invalid") from None
        self.selection = self.selections[index]
        owner.check_task_capacity(self.selections)
        self._state()

    def _require(self, value, reason="invalid"):
        if not value: raise SessionRecordFailure("session-task-" + reason)

    def _decode(self, reference, limit):
        try:
            return json.loads(self.owner._read_child(reference, max_bytes=limit).decode("utf-8"),
                object_pairs_hook=_duplicate_safe, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except SessionRecordFailure: raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise SessionRecordFailure("session-task-payload-invalid") from None

    def _state(self):
        return self.owner._task_state(self.selections)

    def _record(self, document, slot):
        if slot is None: return None
        record = self._decode(slot["current"], LIMIT)
        self._checked(document, record)
        # Identical version-bound references denote the same immutable bytes.
        # Validate a different retained intent, never reread the same version.
        intent = record if slot["intent"] == slot["current"] else self._decode(slot["intent"], LIMIT)
        if intent is not record:
            self._checked(document, intent)
        immutable = set(intent) - {"task_arn", "proof_receipt", "proof_sha256", "integrity"}
        self._require(set(record) == set(intent) and all(record[key] == intent[key] for key in immutable), "intent-mismatch")
        return record

    def _checked(self, document, record):
        try:
            self._require(isinstance(record, dict) and self.validate_record(copy.deepcopy(record)) == record, "record-invalid")
            request = record["request"]
            runtime = request["runtime"]
            stack = self.selection["stack"]
            self._require(runtime["session_id"] == self.owner.binding["session_id"]
                and runtime["source_plan_sha256"] == document["base"]["source_plan_sha256"]
                and runtime["stack_id"] == document["incarnations"].get(stack)
                and stack in document["creation_custody"], "runtime-mismatch")
            binding = {"binding": self.owner.binding, "custody": document["creation_custody"][stack], "stack_id": runtime["stack_id"]}
            self._require(runtime["binding_sha256"] == "sha256:" + hashlib.sha256(RESERVATIONS.canonical(binding)).hexdigest(), "runtime-mismatch")
            definition = request.get("definition", request.get("task_definition"))
            physical = document["physical_resources"].get(stack, {}).get("slots", [])
            position = self.selection["definition_position"]
            self._require(isinstance(definition, str) and type(position) is int and 0 <= position < len(physical)
                          and physical[position] == hashlib.sha256(RESERVATIONS.canonical(definition)).hexdigest(), "runtime-mismatch")
            row = self.selection["selection"]
            if self.selection["kind"] == "ordered-commands/v1":
                self._require(record["mode"] == row["proof"]["operation"] and record["predecessor"] is None, "selection-mismatch")
                selected = {"workload": row["workload"], "operation": row["proof"]["operation"], "proof_type": row["proof"]["proof_type"]}
            else:
                self._require(request["workload"] == row["workload"] and request["proof_label"] == row["label"], "selection-mismatch")
                operation = "ready" if row["workload"] == "verifier" else "preflight"
                if row["phase"] == "operation": operation = row["operation"]
                selected = {"workload": row["workload"], "operation": operation}
            self._require(self.record_selection(copy.deepcopy(record)) == selected, "selection-mismatch")
            return record
        except SessionRecordFailure: raise
        except Exception: raise SessionRecordFailure("session-task-record-invalid") from None

    def _key(self, key, record=None):
        self._require(isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,255}", key), "key-invalid")
        if self.selection["kind"] == "ordered-commands/v1":
            self._require(key == self.selection["step"], "key-mismatch")
        elif record is not None:
            try: expected = self.key_for_record(self.selection["step"], copy.deepcopy(record["request"]))
            except Exception: raise SessionRecordFailure("session-task-key-invalid") from None
            self._require(key == expected, "key-mismatch")

    def observe_selected(self):
        """Observe this source-selected slot without inventing a caller alias."""
        prior, state = self._state()
        record = self._record(prior[0], state["slots"][self.index])
        return copy.deepcopy(record)

    def read(self, key):
        record = self.observe_selected()
        self._key(key, record)
        return record

    def _commit(self, prior, state, action):
        raw = RESERVATIONS.canonical(state)
        self._require(len(raw) <= CHILD_LIMIT, "capacity-exceeded")
        reference = self.owner._retain_child(raw, max_bytes=CHILD_LIMIT)
        document = copy.deepcopy(prior[0]); document["task_state"] = reference
        if action == "reserve-task": self.owner._open(document)
        return self.owner._write(document, prior, action)

    def create(self, key, record):
        return self.compare_and_reserve(key, None, record)

    def compare_and_reserve(self, key, expected, proposed):
        prior, state = self._state()
        self._checked(prior[0], proposed); self._key(key, proposed)
        current = self._record(prior[0], state["slots"][self.index])
        if current is not None:
            self._require(expected is None, "successor-prohibited")
            return False
        self._require(expected is None, "predecessor-mismatch")
        self._require(all(proposed.get(name) is None for name in ("task_arn", "proof_receipt", "proof_sha256")), "initial-record-invalid")
        self.owner._open(prior[0])
        reference = self.owner._retain_child(RESERVATIONS.canonical(proposed))
        state["slots"][self.index] = {"intent": reference, "current": reference, "receipt": None, "admission": None, "context": None, "stop": None}
        confirmed = self._commit(prior, state, "reserve-task")
        self.owner._open(confirmed)
        self.fresh = hashlib.sha256(RESERVATIONS.canonical(proposed)).hexdigest()
        return True

    def close_unadmitted(self):
        """A sealed parent fences admission before declaring an unsent reservation."""
        prior, state = self._state(); slot = state["slots"][self.index]
        self._require(self._record(prior[0], slot) is not None, "record-invalid")
        if slot["admission"] is not None:
            return slot["admission"] == "not-submitted"
        self._require(prior[0]["state"] in ("sealed", "deleting"), "admission-open")
        # RunTask requires positively retained admission. A concurrent foreground
        # admission from an older open head cannot win this sealed parent's CAS.
        slot["admission"] = "not-submitted"
        self._commit(prior, state, "reject-task")
        return True

    def reserve_stop(self, phase, request):
        """Adopt one exact native-task stop intent; cold readers are never fresh."""
        prior, state = self._state(); slot = state["slots"][self.index]
        self._require(prior[0]["state"] in ("sealed", "deleting"), "admission-open")
        record = self._record(prior[0], slot)
        self._require(phase == "cleanup-stop" and record is not None
            and slot["admission"] == "admitted" and isinstance(request, dict)
            and set(request) == {"cluster", "task", "definition", "operation_id"}
            and request["cluster"] == record["request"]["runtime"]["cluster_arn"]
            and request["definition"] == record["request"].get("definition", record["request"].get("task_definition"))
            and request["operation_id"] == record["operation_id"]
            and isinstance(request["task"], str) and re.fullmatch(
                re.escape(request["cluster"].replace(":cluster/", ":task/")) + r"/[a-f0-9]{32}", request["task"])
            and record.get("task_arn") in (None, request["task"]), "stop-binding-invalid")
        if slot["stop"] is not None:
            self._require(self._decode(slot["stop"], LIMIT) == request, "stop-binding-invalid")
            return copy.deepcopy(request), False
        slot["stop"] = self.owner._retain_child(RESERVATIONS.canonical(request))
        self._commit(prior, state, "reserve-task-stop")
        return copy.deepcopy(request), True

    def before_submit(self, key, expected):
        prior, state = self._state(); slot = state["slots"][self.index]
        self._key(key, expected)
        self._require(self._record(prior[0], slot) == expected and self.fresh == hashlib.sha256(RESERVATIONS.canonical(expected)).hexdigest(), "not-fresh")
        self.fresh = None
        try:
            self.owner._open(prior[0]); self.owner._authorize("submit-task")
            self._require(callable(self.authority), "authority-required")
            self._require(self.authority(copy.deepcopy(expected)) is None, "admission-unconfirmed")
        except Exception:
            slot["admission"] = "not-submitted"
            self._commit(prior, state, "reject-task")
            raise SessionRecordFailure("session-task-admission-unconfirmed") from None
        slot["admission"] = "admitted"
        self._commit(prior, state, "admit-task")
        self.owner._open(self.owner.observe_existing()["document"])
        return True

    def reject_submission(self, key, expected):
        """Close only this worker's unused reservation before any provider send."""
        prior, state = self._state(); slot = state["slots"][self.index]
        self._key(key, expected)
        self._require(self._record(prior[0], slot) == expected, "predecessor-mismatch")
        if self.fresh != hashlib.sha256(RESERVATIONS.canonical(expected)).hexdigest():
            return False
        self.fresh = None
        self._require(slot["admission"] is None, "admission-unconfirmed")
        slot["admission"] = "not-submitted"
        self._commit(prior, state, "reject-task")
        return True

    def _attach(self, key, expected, fields):
        prior, state = self._state(); slot = state["slots"][self.index]
        self._key(key, expected)
        current = self._record(prior[0], slot)
        self._require(isinstance(current, dict) and current == expected, "predecessor-mismatch")
        self._require(all(current.get(name) in (None, value) for name, value in fields.items()), "attachment-conflict")
        proposed = {**current, **fields}
        proposed["integrity"] = hashlib.sha256(RESERVATIONS.canonical({name: value for name, value in proposed.items() if name != "integrity"})).hexdigest()
        self._checked(prior[0], proposed)
        if proposed == current: return copy.deepcopy(current)
        slot["current"] = self.owner._retain_child(RESERVATIONS.canonical(proposed))
        self._commit(prior, state, "attach-task")
        return copy.deepcopy(proposed)

    def retain_task(self, key, expected, arn):
        return self._attach(key, expected, {"task_arn": arn})

    def retain_proof(self, key, expected, reference):
        self._require(isinstance(reference, dict) and set(reference) == {"path", "sha256"}, "receipt-invalid")
        raw = self.read_receipt(reference["path"])
        self._require(hashlib.sha256(raw).hexdigest() == reference["sha256"], "receipt-mismatch")
        return self._attach(key, expected, {"proof_receipt": reference["path"], "proof_sha256": reference["sha256"]})

    def retain_receipt(self, label, raw):
        prior, state = self._state(); slot = state["slots"][self.index]
        record = self._record(prior[0], slot)
        self._require(record is not None and isinstance(label, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,255}", label), "receipt-invalid")
        self.owner._child_payload(raw, CHILD_LIMIT)
        try: self._require(self.validate_receipt(label, raw, copy.deepcopy(record)) is None, "receipt-invalid")
        except Exception: raise SessionRecordFailure("session-task-receipt-invalid") from None
        if slot["receipt"] is not None:
            self._require(slot["receipt"]["label"] == label, "receipt-conflict")
            return self.owner._read_child(slot["receipt"]["reference"], max_bytes=CHILD_LIMIT)
        slot["receipt"] = {"label": label, "reference": self.owner._retain_child(raw, max_bytes=CHILD_LIMIT)}
        self._commit(prior, state, "retain-task-receipt")
        return raw

    def observe_receipt(self, label):
        _, state = self._state(); slot = state["slots"][self.index]
        self._require(slot is not None, "receipt-unavailable")
        if slot["receipt"] is None:
            return None
        self._require(slot["receipt"]["label"] == label, "receipt-unavailable")
        return self.owner._read_child(slot["receipt"]["reference"], max_bytes=CHILD_LIMIT)

    def read_receipt(self, label):
        raw = self.observe_receipt(label)
        self._require(raw is not None, "receipt-unavailable")
        return raw

    def read_context(self):
        prior, state = self._state(); slot = state["slots"][self.index]
        self._require(self._record(prior[0], slot) is not None, "context-unavailable")
        return None if slot["context"] is None else self.owner._read_child(slot["context"], max_bytes=CHILD_LIMIT)

    def retain_context(self, raw):
        """One immutable native admission context; never execution authority."""
        prior, state = self._state(); slot = state["slots"][self.index]
        self._require(self._record(prior[0], slot) is not None, "context-unavailable")
        self.owner._child_payload(raw, CHILD_LIMIT)
        if slot["context"] is not None:
            self._require(self.owner._read_child(slot["context"], max_bytes=CHILD_LIMIT) == raw, "context-conflict")
            return False
        slot["context"] = self.owner._retain_child(raw, max_bytes=CHILD_LIMIT)
        self._commit(prior, state, "retain-task-context")
        return True


class _Storage:
    """Transport seam only; the existing reservation owner validates its records."""
    def __init__(self, owner, kind, reconciled_operations_sha256, physical_manifest_sha256):
        self.owner, self.kind = owner, kind
        self.reconciled_operations_sha256 = reconciled_operations_sha256
        self.physical_manifest_sha256 = physical_manifest_sha256

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
        elif self.kind == "delete":
            if document["state"] not in ("sealed", "deleting"):
                raise SessionRecordFailure("session-admission-open")
            if operations_sha256(document) != self.reconciled_operations_sha256:
                raise SessionRecordFailure("session-reconciliation-changed")
            stack = key.split(":")[1]
            physical = document["physical_resources"].get(stack)
            if physical is None or hashlib.sha256(self.owner._bytes(physical)).hexdigest() != self.physical_manifest_sha256:
                raise SessionRecordFailure("session-physical-retention-required")
            document["state"] = "deleting"
        elif document["state"] != "sealed":
            raise SessionRecordFailure("session-admission-open")
        document["operations"][key] = copy.deepcopy(record)
        self.owner._write(document, prior, "reserve-" + self.kind)
        return True
