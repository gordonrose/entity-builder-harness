"""Closed selected-candidate start/stop intent and safe identity observations."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.candidate-lifecycle
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind source-only selected admission to durable local start/stop reservations without provider authority.
#   portability: {class: internal, targets: [kanbien-staging]}
#   effects: [read-only]
from copy import deepcopy

from jsonschema import Draft202012Validator

import operation_journal as journal
import selected_admission as admission

SCHEMAS = ("candidate-lifecycle-attempt", "candidate-lifecycle-observation")
DISPATCH_ACTIONS = frozenset({"start", "stop"})
ACTION_LIMITS = {"start": 1, "stop": 1}
BLOCKED = {"authorized": False, "release_eligibility": "blocked", "operation_authorization": "blocked"}


def fail(code):
    journal.fail("candidate-lifecycle-" + code)


def _schema(name):
    if name not in SCHEMAS:
        fail("schema-invalid")
    return journal._parse_schema(name, journal.read_source(journal.SCHEMA_DIR / (name + ".schema.yml")))


def _validate(name, value):
    journal.canonical(value)
    if next(Draft202012Validator(_schema(name)).iter_errors(value), None):
        fail("record-invalid")
    return value


def _request(result):
    try:
        admission.validate_result(result)
    except admission.AdmissionFailure:
        fail("admission-invalid")
    rows = [row for row in result["operation_requests"] if row["operation_id"] == "candidate-server"]
    if len(rows) != 1:
        fail("request-invalid")
    return deepcopy(rows[0])


def make_attempt(admission_result, expected_identity):
    """Make a closed selected-candidate attachment; no authority is conferred."""
    request = _request(admission_result)
    profile = {"artifact": {"image_id": request["artifact_digest"]}, "operation_profile": request["operation_profile"],
               "acting_identity": request["acting_identity"], "command_ref": request["command_ref"]}
    value = {
        "schema": "candidate-lifecycle-attempt/v1",
        "operation_id": "candidate-server",
        "admission_digest": admission_result["result_digest"],
        "request": request,
        "profile": profile,
        "expected_identity": deepcopy(expected_identity),
        "limits": {"recovery_timeout_ms": 30000, "action_limits": dict(ACTION_LIMITS)},
        **BLOCKED,
    }
    return validate_attempt(value)


def validate_attempt(value):
    _validate("candidate-lifecycle-attempt", value)
    request = value["request"]
    if (value["admission_digest"] == request["candidate_release_digest"]
            or value["expected_identity"]["image_digest"] != request["artifact_digest"]
            or value["profile"] != {"artifact": {"image_id": request["artifact_digest"]},
                                    "operation_profile": request["operation_profile"],
                                    "acting_identity": request["acting_identity"], "command_ref": request["command_ref"]}
            or request["authority_status"] != "not-granted"):
        fail("attempt-binding-invalid")
    return value


def make_control_intent(attempt):
    """Map the selected attempt into the existing local-conformance journal only."""
    validate_attempt(attempt)
    scope = {"provider": "local-fixture", "namespace": "candidate-lifecycle",
             "target": "candidate-server", "resource": "candidate-server-effect"}
    scope = {"scope_id": journal.digest(scope), **scope}
    policy = {"scope": "local-conformance", "lease_ms": 1000, "operation_timeout_ms": 10000,
              "call_timeout_ms": 500, "max_attempts": 1, "evidence_lifetime_ms": 5000}
    value = {
        "schema": "operation-control/v1", "operation_id": attempt["operation_id"],
        "idempotency_key": journal.digest(attempt),
        "release_digest": attempt["request"]["candidate_release_digest"],
        "profile_digest": journal.digest(attempt["profile"]),
        "artifact_digest": attempt["request"]["artifact_digest"],
        "environment_digest": attempt["request"]["target_composition_revision"],
        "authority_policy_digest": journal.digest(policy), "recovery_route": "local-fixture-reconcile",
        "scopes": [scope], "policy": policy,
    }
    return journal.validate("operation-control", value)


def observation(attempt, state, task_id_digest, cluster_digest, task_revision_digest, image_digest):
    value = {
        "schema": "candidate-lifecycle-observation/v1", "operation_id": attempt["operation_id"],
        "attempt_digest": journal.digest(attempt), "state": state, "resource_id": task_id_digest,
        "task_id_digest": task_id_digest,
        "cluster_digest": cluster_digest, "task_revision_digest": task_revision_digest,
        "image_digest": image_digest, **BLOCKED,
    }
    return validate_observation(value, attempt)


def validate_observation(value, attempt):
    validate_attempt(attempt)
    _validate("candidate-lifecycle-observation", value)
    if (value["attempt_digest"] != journal.digest(attempt)
            or value["operation_id"] != attempt["operation_id"] or value["resource_id"] != value["task_id_digest"]
            or any(value[name] != attempt["expected_identity"][name]
                   for name in ("cluster_digest", "task_revision_digest", "image_digest"))):
        fail("observation-binding-invalid")
    return value


def validate_action_observation(action, value, attempt):
    validate_observation(value, attempt)
    states = {"start": "running", "stop": "stopped"}
    if action not in states or value["state"] != states[action]:
        fail("action-observation-invalid")
    return value


def validate_action_preconditions(action, attempt, history, state, mode):
    validate_attempt(attempt)
    if action not in ACTION_LIMITS:
        fail("action-invalid")
    counts = history["counts"]
    observations = history["observations"]
    last = observations[-1]["observation"] if observations else None
    fresh = bool(history["records"] and history["records"][-1]["event"] == "observed")
    if action == "start":
        if counts["start"] or counts["stop"] or history["known_resource_id"] is not None:
            fail("dispatch-precondition")
    elif (counts["start"] != 1 or counts["stop"] or not fresh or last is None
          or last["state"] != "running" or history["known_resource_id"] is None):
        fail("dispatch-precondition")
    return True


def request_token(ticket):
    """Return the one durable reservation digest a future adapter must present."""
    if (type(ticket) is not dict or ticket.get("event") != "reserved"
            or ticket.get("action") not in DISPATCH_ACTIONS
            or type(ticket.get("event_digest")) is not str
            or not journal.DIGEST.fullmatch(ticket["event_digest"])):
        fail("request-token-invalid")
    return ticket["event_digest"]


def require_execution_authority(value):
    """Source-local records are never provider execution authority."""
    validate_attempt(value)
    fail("authority-unavailable")
