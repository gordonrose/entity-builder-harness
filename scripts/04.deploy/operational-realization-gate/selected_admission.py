"""Bind selected baseline/candidate declarations; source output never admits execution."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.selected-admission
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Compile closed selected release admission requests from immutable source results without execution authority.
#   portability: {class: internal, targets: [kanbien-staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.selected-admission-cli
#     path: scripts/04.deploy/operational-realization-gate/selected_admission_cli.py
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

import blueprint_cli
import release_compiler as release
import selected_operation as operation

SCHEMA = Path(__file__).resolve().parents[3] / "infra/04.deploy/contracts/release-control/v1/selected-admission-result.schema.yml"
GATES = (
    "scope-risk", "acceptance-contract", "source-contracts", "unit-contract-tests",
    "integration-tests", "exact-artifact-tests", "supply-chain-proof",
    "iac-static-validation", "change-set-review", "drift-dependency-preflight",
    "candidate-runtime-proof", "per-task-live-preflight", "controlled-state-change",
    "post-change-verification", "rollback-recovery", "evidence-retention",
    "continuous-operation",
)
SAFE_CODES = frozenset((
    "admission-authority-unavailable", "admission-baseline-invalid", "admission-candidate-invalid",
    "admission-immutable-release-rebound", "admission-operation-binding-invalid",
    "admission-result-invalid", "admission-schema-invalid", "admission-schema-unreadable",
))


class AdmissionFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def fail(code):
    raise AdmissionFailure(code if code in SAFE_CODES else "admission-result-invalid")


@lru_cache(maxsize=1)
def load_schema():
    try:
        schema = release.load_document(SCHEMA, "admission-schema-unreadable")
        stack = [schema]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                if ("$dynamicRef" in value or "$recursiveRef" in value
                        or "$ref" in value and not str(value["$ref"]).startswith("#/")):
                    fail("admission-schema-invalid")
                if value.get("type") == "object" and value.get("additionalProperties") is not False:
                    fail("admission-schema-invalid")
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
        if (schema.get("$id") != "urn:release-control:selected-admission-result:v1"
                or schema.get("properties", {}).get("schema") != {"const": "selected-admission-result/v1"}):
            fail("admission-schema-invalid")
        Draft202012Validator.check_schema(schema)
        return schema
    except AdmissionFailure:
        raise
    except Exception:
        fail("admission-schema-invalid")


def digest(value):
    return release.digest_document(value)


def _source_result(value, code):
    try:
        compiler = blueprint_cli.load_compiler()
        blueprint_cli.validate_result(value, compiler)
        compiled = value["compiled_release"]
        if (compiled.get("schema") != "release-control-result/v1" or compiled.get("scope") != "release-definition"
                or compiled.get("verdict") != "compiled" or compiled.get("authorized") is not False
                or compiled.get("findings") != [] or len(compiled.get("acceptance_matrix", [])) != 17):
            fail(code)
        rows = compiled["acceptance_matrix"]
        if any(row.get("stage") != index or row.get("gate") != GATES[index - 1]
               or row.get("verdict") != "not-started" for index, row in enumerate(rows, 1)):
            fail(code)
        return compiled
    except AdmissionFailure:
        raise
    except Exception:
        fail(code)


def _binding(compiled):
    rows = compiled["acceptance_matrix"]
    bindings = rows[0]["bindings"]
    return {
        "release_id": bindings["release_id"],
        "release_digest": bindings["release_digest"],
        "source_revision": bindings["source_revision"],
        "target_composition_revision": bindings["target_composition_revision"],
        "artifact_bindings_digest": digest(bindings["artifact_digests"]),
    }


def _acceptance(compiled):
    rows = compiled["acceptance_matrix"]
    return [{"stage": row["stage"], "gate": row["gate"],
             "binding_digest": digest(row["bindings"]),
             "operation_count": len(row["operation_bindings"])} for row in rows]


def _requests(compiled, baseline):
    row = compiled["acceptance_matrix"][0]
    candidate = _binding(compiled)
    policy = operation.policy()
    items = []
    for binding in row["operation_bindings"]:
        items.append({
            "operation_id": binding["operation_id"], "owner": row["owner"],
            "operation_profile": binding["operation_profile"], "acting_identity": binding["acting_identity"],
            "command_ref": binding["command_ref"], "recovery_route": binding["recovery_route"],
            "cleanup_route": binding["cleanup_route"], "artifact_digest": binding["artifact_digest"],
            "candidate_release_digest": candidate["release_digest"],
            "baseline_release_digest": baseline["release_digest"],
            "source_revision": candidate["source_revision"],
            "target_composition_revision": candidate["target_composition_revision"],
            "cost_ceiling_usd": policy["total_monthly_ceiling_usd"],
            "max_effect_attempts": policy["max_effect_attempts"],
            "authority_window_ms": policy["authority_window_ms"], "authority_status": "not-granted",
        })
    if len({item["operation_id"] for item in items}) != len(items):
        fail("admission-operation-binding-invalid")
    return items


def compile_admission(baseline_result, candidate_result):
    """Compile an immutable request set; missing live evidence/authority stays blocked."""
    baseline_compiled = _source_result(baseline_result, "admission-baseline-invalid")
    candidate_compiled = _source_result(candidate_result, "admission-candidate-invalid")
    baseline, candidate = _binding(baseline_compiled), _binding(candidate_compiled)
    if (baseline["release_id"] == candidate["release_id"]
            and baseline["release_digest"] != candidate["release_digest"]):
        fail("admission-immutable-release-rebound")
    result = {
        "schema": "selected-admission-result/v1", "scope": "selected-staging-admission", "verdict": "compiled",
        "authorized": False, "release_eligibility": "blocked", "operation_authorization": "blocked",
        "qualification_verdict": "blocked", "baseline": baseline, "candidate": candidate,
        "acceptance": _acceptance(candidate_compiled), "operation_requests": _requests(candidate_compiled, baseline),
        "policy_digest": digest(operation.policy()),
        "findings": [{"code": "admission-evidence-unavailable"}, {"code": "admission-authority-unavailable"}],
    }
    result["result_digest"] = digest(result)
    return validate_result(result)


def validate_result(value):
    try:
        release.bounded_json(value)
        schema = load_schema()
        if next(Draft202012Validator(schema).iter_errors(value), None):
            fail("admission-result-invalid")
        if (value["baseline"]["release_id"] == value["candidate"]["release_id"]
                and value["baseline"]["release_digest"] != value["candidate"]["release_digest"]):
            fail("admission-immutable-release-rebound")
        if any(row["stage"] != index or row["gate"] != GATES[index - 1]
               for index, row in enumerate(value["acceptance"], 1)):
            fail("admission-result-invalid")
        requests = value["operation_requests"]
        if (len({row["operation_id"] for row in requests}) != len(requests)
                or any(row["candidate_release_digest"] != value["candidate"]["release_digest"]
                       or row["baseline_release_digest"] != value["baseline"]["release_digest"]
                       or row["source_revision"] != value["candidate"]["source_revision"]
                       or row["target_composition_revision"] != value["candidate"]["target_composition_revision"]
                       for row in requests)):
            fail("admission-operation-binding-invalid")
        if digest({key: item for key, item in value.items() if key != "result_digest"}) != value["result_digest"]:
            fail("admission-result-invalid")
        return value
    except AdmissionFailure:
        raise
    except Exception:
        fail("admission-result-invalid")



def require_execution_authority(value):
    """Source-only admission records can never act as execution authority."""
    validate_result(value)
    fail("admission-authority-unavailable")
