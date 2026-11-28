#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.capability.environment-lifecycle.session-binding
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Check immutable temporary-session intent and bind captured source identities without granting provider or cleanup authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.library.aws.preparation-inputs
#     path: scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py
"""Source-plan binding, not durable ownership, expiry delivery or execution proof."""
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import re

SPEC = importlib.util.spec_from_file_location("session_lifecycle_policy", Path(__file__).parents[1] / "policy/implementation.py")
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)


class SessionFailure(ValueError):
    def __init__(self, condition):
        self.code = "environment-session-" + condition
        super().__init__(self.code)


def require(value, reason):
    if not value:
        raise SessionFailure(reason)


@dataclass(frozen=True)
class SessionIntent:
    target: str
    scope: str
    session_id: str
    starts_at: int
    expires_at: int
    lifecycle: object


@dataclass(frozen=True)
class SessionBinding:
    intent: SessionIntent
    source_inputs: tuple
    scopes: tuple
    source_inputs_sha256: str


def _read_context(document, *, target, scope, now, approved_max_duration_seconds):
    """Check the original lifetime and real clock without granting admission."""
    require(isinstance(document, dict), "document-type-invalid")
    fields = {"schema", "target", "scope", "session_id", "starts_at", "expires_at", "environment_lifecycle"}
    require(set(document) == fields, "document-fields-invalid")
    require(document["schema"] == "deploy/environment-session-intent/v1", "schema-unsupported")
    for name, expected in (("target", target), ("scope", scope)):
        value = document[name]
        require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value) is not None, name + "-invalid")
        require(value == expected, name + "-mismatch")
    identity = document["session_id"]
    require(isinstance(identity, str) and re.fullmatch(r"[a-f0-9]{32}", identity) is not None, "identity-invalid")
    require(type(now) is int and now >= 0, "clock-invalid")
    require(type(approved_max_duration_seconds) is int and approved_max_duration_seconds > 0, "approved-duration-invalid")
    for name in ("starts_at", "expires_at"):
        require(type(document[name]) is int and document[name] >= 0, name.replace("_", "-") + "-invalid")
    start, end = document["starts_at"], document["expires_at"]
    require(end > start, "expiry-order-invalid")
    require(start <= now, "start-in-future")
    return target, scope, identity, start, end


def _intent(document, context, approved_max_duration_seconds):
    start, end = context[-2:]
    try:
        lifecycle = POLICY.read({"environment_lifecycle": document["environment_lifecycle"]})
    except POLICY.PolicyFailure as failure:
        raise SessionFailure(failure.code) from None
    require(lifecycle.explicit and lifecycle.mode == "temporary", "temporary-policy-required")
    require(end - start <= lifecycle.max_duration_seconds, "policy-duration-exceeded")
    require(end - start <= approved_max_duration_seconds, "approved-duration-exceeded")
    return SessionIntent(*context, lifecycle)


def read(document, *, target, scope, now, approved_max_duration_seconds):
    """Accept a new unexpired lifecycle overlay, never supplied hashes."""
    context = _read_context(document, target=target, scope=scope, now=now,
                            approved_max_duration_seconds=approved_max_duration_seconds)
    require(now < context[-1], "expired")
    return _intent(document, context, approved_max_duration_seconds)


def read_existing(document, *, target, scope, now, approved_max_duration_seconds):
    """Recheck an original lifetime after expiry; never reopen admission."""
    context = _read_context(document, target=target, scope=scope, now=now,
                            approved_max_duration_seconds=approved_max_duration_seconds)
    return _intent(document, context, approved_max_duration_seconds)


def bind_sources(intent, source_inputs, scopes):
    """Bind adapter-captured identities; this function does not read source files."""
    require(isinstance(intent, SessionIntent), "intent-invalid")
    require(isinstance(source_inputs, tuple) and bool(source_inputs), "source-inputs-invalid")
    require(all(isinstance(row, tuple) and len(row) == 2 and isinstance(row[0], str) and bool(row[0])
                and isinstance(row[1], str) and re.fullmatch(r"[a-f0-9]{64}", row[1]) is not None
                for row in source_inputs), "source-inputs-invalid")
    require(tuple(sorted(source_inputs)) == source_inputs and len({row[0] for row in source_inputs}) == len(source_inputs), "source-inputs-ambiguous")
    require(isinstance(scopes, tuple) and bool(scopes) and all(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value) is not None for value in scopes), "scopes-invalid")
    require(tuple(sorted(set(scopes))) == scopes and intent.scope in scopes, "scopes-ambiguous")
    digest = hashlib.sha256(json.dumps(source_inputs, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    return SessionBinding(intent, source_inputs, scopes, digest)
