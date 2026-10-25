#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.deployment-operation-diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.diagnostics
#   disciplines: [security, sre, agentic]
#   kind: script
#   purpose: Prove failure classification and retained report validation remain safe and fail closed.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.deployment-operation-diagnostics.wrapper
#     path: scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.sh
"""Focused regressions for retained deployment-operation diagnostics."""
from __future__ import annotations

import importlib.util
import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("deployment_diagnostics", ROOT / "scripts/04.deploy/shared/deployment-operation-diagnostics.py")
diagnostics = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(diagnostics)


def valid(**overrides):
    value = diagnostics.build_report(
        target="test-target", scope="test-scope", operation_id="test-operation",
        stage="deploy", original_code="test-operation-failed", exit_status=9,
        outcome="failed", classification="provider-property-rejection",
        evidence_reference="github-actions-artifact:test-diagnostic",
        next_decision="inspect-retained-evidence",
        facts={"resource_logical_id": "ServerTask", "resource_type": "AWS::ECS::TaskDefinition"},
        observed_at="2026-10-25T10:00:00Z",
    )
    value.update(overrides)
    return value


def fails(report):
    try:
        diagnostics.validate(report)
    except diagnostics.DiagnosticFailure:
        return
    raise AssertionError("unsafe or malformed report passed validation")


diagnostics.validate(valid())
bad = valid(); bad["facts"]["provider_message"] = "synthetic provider response"; fails(bad)
bad = valid(); bad["facts"]["resource_logical_id"] = "password=synthetic-only"; fails(bad)
bad = valid(); bad["operation_outcome"] = "unknown"; bad["next_action"] = {"decision": "correct-and-create-new-operation"}; fails(bad)
bad = valid(); bad["evidence"] = {"reference": "https://unsafe.invalid/evidence"}; fails(bad)

property_change = {"Status": "FAILED", "StatusReason": "Property validation error at Properties.ContainerDefinitions[0].Image password=synthetic-only"}
classification, facts, outcome = diagnostics.classify_cloudformation_failure(property_change, [])
assert classification == "provider-property-rejection" and outcome == "rejected"
assert facts == {"provider_status": "FAILED"}

access_change = {"Status": "FAILED", "StatusReason": "AccessDenied: synthetic-only"}
assert diagnostics.classify_cloudformation_failure(access_change, [])[0] == "provider-access-denied"
missing_change = {"Status": "FAILED", "StatusReason": "Resource does not exist: synthetic-only"}
assert diagnostics.classify_cloudformation_failure(missing_change, [])[0] == "provider-resource-missing"
unknown_change = {"Status": "CREATE_IN_PROGRESS", "StatusReason": "x" * 50000}
classification, facts, outcome = diagnostics.classify_cloudformation_failure(unknown_change, [{"ResourceStatus": [], "ResourceStatusReason": {}}])
assert classification == "provider-details-unavailable" and facts == {"provider_status": "CREATE_IN_PROGRESS"} and outcome == "unknown"

def timeout_provider(*_parts): return False, None, "aws-command-timeout"
classification, facts, outcome, collection = diagnostics.collect_cloudformation_failure(timeout_provider, stack_name="test-stack", change_set_name="test-change-set")
assert (classification, facts, outcome, collection) == ("provider-observation-timeout", {}, "unknown", "failed")

calls = []
def event_collection_fails(*parts):
    calls.append(parts)
    if parts[1] == "describe-change-set":
        return True, {"Status": "FAILED", "StatusReason": "ValidationError"}, "ok"
    return False, None, "aws-access-denied"
classification, facts, outcome, collection = diagnostics.collect_cloudformation_failure(event_collection_fails, stack_name="test-stack", change_set_name="test-change-set")
assert classification == "provider-property-rejection" and outcome == "rejected" and collection == "unavailable"

with tempfile.TemporaryDirectory() as directory:
    report_path = Path(directory) / "diagnostic.json"
    diagnostics.write_report(report_path, valid())
    assert json.loads(report_path.read_text()) == valid()

with io.StringIO() as stream, redirect_stdout(stream):
    print(json.dumps({"classification": classification, "facts": facts}, sort_keys=True))
    emitted = stream.getvalue()
assert "synthetic-only" not in emitted and "x" * 200 not in emitted
print("Deployment-operation diagnostics regression tests passed.")
