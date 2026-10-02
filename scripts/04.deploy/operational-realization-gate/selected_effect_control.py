"""Route selected callers through source admission and the live-control receipt boundary."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.selected-effect-control
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind each selected caller to declared admission, durable-store and evidence receipts before an effect.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

import release_compiler as release
import selected_admission as admission

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "infra/04.deploy/contracts/release-control/v1/selected-effect-route.schema.yml"
REQUIRED_RECEIPTS = (
    "selected-admission-result/v1",
    "selected-operation-record/v2",
    "selected-store-event/v2",
    "selected-operation-evidence/v2",
    "selected-control-plane-result/v1",
    "authenticated-selected-transport/v1",
)
ROUTES = {
    "candidate-execution-preflight": {
        "execute": ("candidate-server",),
    },
    "postgresql-relational-smoke": {
        "execute": ("bootstrap", "migration", "relational-relay", "relational-worker", "restore-verify"),
        "execute-bootstrap-recovery": ("bootstrap",),
        "execute-recovery-continuation": ("migration", "relational-relay", "relational-worker", "restore-verify"),
        "diagnose-bootstrap-recovery": ("bootstrap",),
    },
}


class EffectControlFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def fail(code):
    raise EffectControlFailure(code)


def _control_plane():
    directory = Path(__file__).resolve().parents[1] / "release-control"
    sys.path.insert(0, str(directory))
    try:
        import selected_control_plane
        return selected_control_plane
    except Exception:
        fail("selected-control-plane-unavailable")
    finally:
        sys.path.remove(str(directory))


def _route(route, mode):
    if type(route) is not str or type(mode) is not str or route not in ROUTES or mode not in ROUTES[route]:
        fail("selected-effect-route-invalid")
    return ROUTES[route][mode]


def _schema():
    try:
        value = release.load_document(SCHEMA, "selected-effect-route-schema-unreadable")
        Draft202012Validator.check_schema(value)
        return value
    except EffectControlFailure:
        raise
    except Exception:
        fail("selected-effect-route-schema-invalid")


def _bind_admission(admission_result, operation_ids):
    if admission_result is None:
        return None
    try:
        admission.validate_result(admission_result)
    except Exception:
        fail("selected-effect-admission-invalid")
    rows = {row["operation_id"]: row for row in admission_result["operation_requests"]}
    if set(operation_ids) - set(rows) or any(rows[name]["authority_status"] != "not-granted" for name in operation_ids):
        fail("selected-effect-admission-binding-invalid")
    return admission_result["result_digest"]


def validate_route(value):
    try:
        release.bounded_json(value)
        if type(value) is not dict or next(Draft202012Validator(_schema()).iter_errors(value), None):
            fail("selected-effect-route-invalid")
        expected = _route(value["route"], value["mode"])
        if (tuple(value["operation_ids"]) != expected or tuple(value["required_receipts"]) != REQUIRED_RECEIPTS
                or value["authorized"] is not False or value["release_eligibility"] != "blocked"
                or value["operation_authorization"] != "blocked"
                or value["findings"] != [{"code": "selected-live-control-receipt-required"}]
                or release.digest_document({key: item for key, item in value.items() if key != "result_digest"}) != value["result_digest"]):
            fail("selected-effect-route-invalid")
        return value
    except EffectControlFailure:
        raise
    except Exception:
        fail("selected-effect-route-invalid")


def source_route(route, mode, admission_result=None):
    """Compile the fixed receipt requirements. It never creates or accepts authority."""
    operation_ids = _route(route, mode)
    plane = _control_plane().compile_control_plane()
    admission_digest = _bind_admission(admission_result, operation_ids)
    value = {
        "schema": "selected-effect-route/v1",
        "route": route,
        "mode": mode,
        "operation_ids": list(operation_ids),
        "control_plane_result_digest": plane["result_digest"],
        "admission_digest": admission_digest,
        "required_receipts": list(REQUIRED_RECEIPTS),
        "authorized": False,
        "release_eligibility": "blocked",
        "operation_authorization": "blocked",
        "findings": [{"code": "selected-live-control-receipt-required"}],
    }
    value["result_digest"] = release.digest_document(value)
    return validate_route(value)


def require_effect_authority(route, mode, admission_result=None):
    """Fail closed until P18/P21 provide independently checked live receipts."""
    source_route(route, mode, admission_result)
    fail("selected-live-control-receipt-required")

