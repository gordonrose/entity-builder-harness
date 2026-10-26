#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.deployment-operation-diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
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
import re
import subprocess
import sys
import yaml
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
assert classification == "provider-details-unavailable" and facts == {"provider_status": "CREATE_IN_PROGRESS"} and outcome == "pending"

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
# Historical records remain valid; only bounded, typed optional facts are added.
execution={"phase":"pool_connect","elapsed_ms":12,"code_status":"recognized","classification":"authentication_rejected"}
extended=valid(execution=execution,collection={"status":"collected","observation":"incomplete","attempts":3,"task_observation":"malformed","task_attempts":2})
diagnostics.validate(extended)
for field,value in [("phase",[]),("phase","authentication-completed"),("elapsed_ms",True),("elapsed_ms",3600001),("elapsed_ms",-1),("classification",[]),("classification","password=synthetic-canary"),("code_status","provider-code")]:
 bad=valid(execution={**execution,field:value});fails(bad)
for field in ["message","stack","endpoint","credential","sql","values","certificate","connection_string"]:
 fails(valid(execution={**execution,field:"synthetic-sensitive-canary"}))
for collection in [{"status":"collected","observation":[]},{"status":"collected","attempts":0},{"status":"collected","attempts":True},{"status":"collected","task_observation":"guessed"},{"status":"collected","task_attempts":4}]:fails(valid(collection=collection))
fails(valid(execution={**execution,"phase":"unknown"}))
fails(valid(execution={**execution,"code_status":"absent"}))
schema=yaml.safe_load((ROOT/'.agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.schema.yml').read_text())
assert set(schema['execution']['allowed_phases'])==diagnostics.EXECUTION_PHASES
assert set(schema['execution']['allowed_code_statuses'])==diagnostics.CODE_STATUSES
assert set(schema['execution']['allowed_classifications'])==diagnostics.FAILURE_CLASSIFICATIONS
assert set(schema['collection']['allowed_observations'])==diagnostics.COLLECTION_OBSERVATIONS
adapter=(ROOT/'platform/adapters/aws/persistence/postgresql/src/errors.ts').read_text()
assert set(re.findall(r'"([a-z_]+)"',re.search(r'postgreSqlFailureClassifications = \[(.*?)\] as const',adapter,re.S).group(1)))==diagnostics.FAILURE_CLASSIFICATIONS
assert set(re.findall(r'"([a-z_]+)"',re.search(r'PostgreSqlObservedPhase = ([^;]+)',adapter).group(1)))==diagnostics.EXECUTION_PHASES
for status in ["absent", "unrecognized"]:
 diagnostics.validate_execution({**execution,"classification":"authentication_material_invalid","code_status":status})
for value in [{"verdict":"rejected","code":"SAFE_REJECTED"},{"schema":"deploy/persistence-restore-verifier-result/v2","verdict":"rejected","code":"SAFE_REJECTED","execution":execution}]:diagnostics.validate_verifier_result(value)
for value in [{"verdict":"accepted","code":"SAFE_RESULT","provider_message":"synthetic-canary"},{"schema":"deploy/persistence-restore-verifier-result/v2","verdict":"accepted","code":"SAFE_RESULT","execution":execution}]:
 try:diagnostics.validate_verifier_result(value)
 except diagnostics.DiagnosticFailure:pass
 else:raise AssertionError('unsafe result envelope accepted')
with tempfile.TemporaryDirectory() as directory:
 path=Path(directory)/'report.json'
 command=[sys.executable,str(ROOT/'scripts/04.deploy/shared/deployment-operation-diagnostics.py'),'record','--target','test-target','--scope','test-scope','--operation-id','test-operation','--stage','run','--original-code','SAFE_REJECTED','--exit-status','7','--outcome','failed','--classification','test-classified','--evidence-reference','provider-operation:test-operation','--next-decision','inspect-retained-evidence','--collection-observation','incomplete','--collection-attempts','3','--task-log-observation','malformed','--task-log-attempts','2','--execution-phase','pool_connect','--execution-elapsed-ms','12','--execution-code-status','recognized','--execution-classification','authentication_rejected','--report',str(path)]
 result=subprocess.run(command,capture_output=True,text=True,timeout=10);assert result.returncode==0,result.stderr
 retained=json.loads(path.read_text());assert retained['execution']==execution and retained['original_failure']['exit_status']==7
 result=subprocess.run([sys.executable,str(ROOT/'scripts/04.deploy/shared/deployment-operation-diagnostics.py'),'validate','--report',str(path)],capture_output=True,text=True,timeout=10);assert result.returncode==0
 # A failed retained write gets a closed CLI failure, never a raw traceback.
 path.unlink();path.mkdir()
 result=subprocess.run(command,capture_output=True,text=True,timeout=10);assert result.returncode!=0 and 'Traceback' not in result.stderr
print("Deployment-operation diagnostics regression tests passed (historical/v2 readers, typed observations, secrecy and actual CLI).")
