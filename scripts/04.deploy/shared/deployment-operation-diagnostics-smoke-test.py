#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.deployment-operation-diagnostics
#   version: 4
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-11-23"
#   layer: 04.deploy
#   domain: deployment.diagnostics
#   disciplines: [security, sre, agentic]
#   kind: script
#   purpose: Prove shared failure classification, generic retained report validation, command-line handling, and wrapper dispatch remain safe and fail closed.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.deployment-operation-diagnostics.wrapper
#     path: scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.sh
"""Focused regressions for retained deployment-operation diagnostics."""
from __future__ import annotations

import importlib.util
import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import yaml
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

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
diagnostics.validate(valid(collection={"status": "collected", "observation": "incomplete", "attempts": 3}))
try:
    diagnostics.validate(valid(), extension_validators={"target": lambda value: value})
except diagnostics.DiagnosticFailure as error:
    assert error.codes == ("report-extension-profile-invalid",)
else:
    raise AssertionError("an extension profile replaced a generic report field")
fails(valid(collection={"status": "pending"}))
fails(valid(collection={"status": "partial"}))

bad = valid(); bad["facts"]["provider_message"] = "synthetic provider response"; fails(bad)
bad = valid(); bad["facts"]["resource_logical_id"] = "password=synthetic-only"; fails(bad)
bad = valid(); bad["operation_outcome"] = "unknown"; bad["next_action"] = {"decision": "correct-and-create-new-operation"}; fails(bad)
bad = valid(); bad["evidence"] = {"reference": "https://unsafe.invalid/evidence"}; fails(bad)

property_change = {"Status": "FAILED", "StatusReason": "Property validation error at Properties.ContainerDefinitions[0].Image password=synthetic-only"}
classification, facts, outcome = diagnostics.classify_cloudformation_failure(property_change, [])
assert classification == "provider-property-rejection" and outcome == "rejected"
assert facts == {"provider_status": "FAILED", "property_path": "Properties.ContainerDefinitions"}

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

def expired_provider(*parts):
    return False, None, "aws-credentials-expired"
classification, facts, outcome, collection = diagnostics.collect_cloudformation_failure(expired_provider, stack_name="test-stack", change_set_name="test-change-set")
assert (classification, facts, outcome, collection) == ("provider-credentials-expired", {}, "unknown", "failed")
expired_report = valid(classification={"code": classification}, facts=facts,
                       operation_outcome=outcome,
                       next_action={"decision": "observe-current-operation"})
diagnostics.validate(expired_report)
fails({**expired_report, "next_action": {"decision": "correct-and-create-new-operation"}})
assert diagnostics.classify_aws_error("aws-access-denied") == "provider-access-denied"

calls = []
def event_collection_fails(*parts):
    calls.append(parts)
    if parts[1] == "describe-change-set":
        return True, {"Status": "FAILED", "StatusReason": "ValidationError"}, "ok"
    return False, None, "aws-access-denied"
classification, facts, outcome, collection = diagnostics.collect_cloudformation_failure(event_collection_fails, stack_name="test-stack", change_set_name="test-change-set")
assert classification == "provider-property-rejection" and outcome == "rejected" and collection == "unavailable"
assert calls == [("cloudformation", "describe-change-set", "--stack-name", "test-stack", "--change-set-name", "test-change-set"), ("cloudformation", "describe-stack-events", "--stack-name", "test-stack")]
historical = [{"ResourceStatus": "DELETE_FAILED", "ResourceStatusReason": "AccessDenied PRIVATE_CF_CANARY", "LogicalResourceId": "OldResource", "ResourceType": "AWS::RDS::DBInstance"}]
assert diagnostics.classify_cloudformation_failure(property_change, historical) == ("provider-property-rejection", {"provider_status": "FAILED", "property_path": "Properties.ContainerDefinitions"}, "rejected")
assert "synthetic-only" not in json.dumps(diagnostics.classify_cloudformation_failure(property_change, historical))
assert diagnostics.classify_cloudformation_failure({"Status": "FAILED"}, historical) == ("provider-details-unavailable", {"provider_status": "FAILED"}, "rejected")
assert diagnostics.classify_cloudformation_failure({"Status": "PRIVATE_CF_CANARY"}, historical) == ("provider-details-unavailable", {}, "unknown")

surface_spec = importlib.util.spec_from_file_location("restoration_verifier_surface", ROOT / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface/script.py")
surface = importlib.util.module_from_spec(surface_spec)
assert surface_spec and surface_spec.loader
surface_spec.loader.exec_module(surface)
digest="sha256:"+"a"*64;name=surface.change_name(digest,"image");parameters={"RestoreVerifierImageDigest":digest}
rejected_review={"Status":"CREATE_COMPLETE","ExecutionStatus":"AVAILABLE","ChangeSetName":name,"Parameters":[{"ParameterKey":key,"ParameterValue":value} for key,value in parameters.items()],"Changes":[]}
for failed_delete in (True,False):
 calls=[]
 def provider(*parts):
  calls.append(parts)
  if parts[1]=="delete-change-set":return (not failed_delete),None,"aws-command-timeout" if failed_delete else "ok"
  return True,rejected_review,"ok"
 capture=io.StringIO()
 with patch.object(surface.time,"sleep") as pause,redirect_stdout(capture):
  assert surface.discard_rejected_image_review(SimpleNamespace(aws=provider),name,digest,parameters)==1
 body=json.loads(capture.getvalue());assert body["verdict"]=="uncertain"
 assert body["facts"]=={"change_set":name,"restore_verifier_image_digest":digest,"mode":"image"}
 assert [parts[1] for parts in calls]==["describe-change-set","delete-change-set"]+([] if failed_delete else ["describe-change-set"]*6)
 assert pause.call_count==(0 if failed_delete else 5)
 assert all(item.args==(2,) and item.kwargs=={} for item in pause.call_args_list)
 assert body["findings"]==[{"code":"aws-command-timeout" if failed_delete else "persistence-restoration-image-review-discard-not-confirmed"}]
calls=[]
def restricted(*parts):calls.append(parts);return True,rejected_review,"ok"
capture=io.StringIO()
with redirect_stdout(capture):assert surface.discard_rejected_image_review(SimpleNamespace(aws=restricted),name,digest,{"RestoreVerifierImageDigest":"sha256:"+"b"*64})==1
assert len(calls)==1 and json.loads(capture.getvalue())["verdict"]=="blocked"

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
runtime=diagnostics.runtime_contract()
assert runtime.persistence_vocabulary('phase')==diagnostics.EXECUTION_PHASES
assert runtime.persistence_vocabulary('codeStatus')==diagnostics.CODE_STATUSES
assert runtime.persistence_vocabulary('classification')==diagnostics.FAILURE_CLASSIFICATIONS
assert schema['execution']['vocabulary_source']=='platform/persistence/contracts/diagnostics.v1.json'
assert set(schema['collection']['allowed_observations'])==diagnostics.COLLECTION_OBSERVATIONS
assert set(schema['allowed_collection_statuses'])==diagnostics.COLLECTION=={'collected','unavailable','failed'}
assert set(schema['allowed_operation_outcomes'])==diagnostics.OUTCOMES=={'rejected','failed','pending','unknown'}
for status in ["absent", "unrecognized"]:
 diagnostics.validate_execution({**execution,"classification":"authentication_material_invalid","code_status":status})
with tempfile.TemporaryDirectory() as directory:
 path=Path(directory)/'report.json'
 command=[sys.executable,str(ROOT/'scripts/04.deploy/shared/deployment-operation-diagnostics.py'),'record','--target','test-target','--scope','test-scope','--operation-id','test-operation','--stage','run','--original-code','SAFE_REJECTED','--exit-status','7','--outcome','failed','--classification','test-classified','--evidence-reference','provider-operation:test-operation','--next-decision','inspect-retained-evidence','--collection-observation','incomplete','--collection-attempts','3','--task-log-observation','malformed','--task-log-attempts','2','--execution-phase','pool_connect','--execution-elapsed-ms','12','--execution-code-status','recognized','--execution-classification','authentication_rejected','--report',str(path)]
 result=subprocess.run(command,capture_output=True,text=True,timeout=10);assert result.returncode==0,result.stderr
 retained=json.loads(path.read_text());assert retained['execution']==execution and retained['original_failure']['exit_status']==7
 result=subprocess.run([sys.executable,str(ROOT/'scripts/04.deploy/shared/deployment-operation-diagnostics.py'),'validate','--report',str(path)],capture_output=True,text=True,timeout=10);assert result.returncode==0
 # Parser errors keep argparse's status 2 but never echo rejected input.
 canary='controlled-cli-secret\nsecond-private-line'
 for option in ['--exit-status','--collection-attempts','--task-log-attempts','--execution-elapsed-ms']:
  rejected=command.copy();rejected[rejected.index(option)+1]=canary
  result=subprocess.run(rejected,capture_output=True,text=True,timeout=10)
  assert result.returncode==2 and result.stdout==''
  assert result.stderr=='ERROR: deployment-operation-diagnostic-arguments-invalid\n'
 for arguments in [[canary],['record'],['validate','--report']]:
  result=subprocess.run(command[:2]+arguments,capture_output=True,text=True,timeout=10)
  assert result.returncode==2 and result.stdout==''
  assert result.stderr=='ERROR: deployment-operation-diagnostic-arguments-invalid\n'
 # parse_known_args' existing unknown-argument failure remains diagnostic exit 1.
 result=subprocess.run(command+['--'+canary],capture_output=True,text=True,timeout=10)
 assert result.returncode==1 and result.stderr==''
 assert json.loads(result.stdout)['findings']==[{'code':'arguments-invalid'}]
 assert canary not in result.stdout+result.stderr
 malformed=Path(directory)/'malformed.json'
 malformed.write_text('{"private": "'+canary+'"')
 result=subprocess.run(command[:2]+['validate','--report',str(malformed)],capture_output=True,text=True,timeout=10)
 assert result.returncode==1 and result.stderr==''
 assert json.loads(result.stdout)['findings']==[{'code':'report-unreadable'}]
 assert 'controlled-cli-secret' not in result.stdout+result.stderr and 'Traceback' not in result.stdout+result.stderr
 # A failed retained write gets a closed CLI failure, never a raw traceback.
 path.unlink();path.mkdir()
 result=subprocess.run(command,capture_output=True,text=True,timeout=10);assert result.returncode!=0 and 'Traceback' not in result.stderr
 # Execute the real wrapper, substituting only its children/root discovery.
 # The fake Python child prevents recursive execution of this same fixture.
 fixture=Path(directory)/'dispatch';binary=fixture/'bin';binary.mkdir(parents=True)
 children=fixture/'scripts/04.deploy/shared';children.mkdir(parents=True)
 log=fixture/'calls'
 scripts={
  binary/'git':'#!/usr/bin/env bash\n[[ "$*" == "rev-parse --show-toplevel" ]] || exit 99\nprintf "%s\\n" "$B10_FIXTURE_ROOT"\n',
  binary/'python3':'#!/usr/bin/env bash\nprintf "python:%s\\n" "$*" >>"$B10_FIXTURE_LOG"\nexit "$B10_FIRST_STATUS"\n',
  children/'safe-command-diagnostics-smoke-test.sh':'#!/usr/bin/env bash\nprintf "bash-suite\\n" >>"$B10_FIXTURE_LOG"\nexit "$B10_SECOND_STATUS"\n',
 }
 for child,content in scripts.items():child.write_text(content);child.chmod(0o755)
 for first,second,status in [(0,0,0),(17,0,17),(0,23,23)]:
  log.unlink(missing_ok=True)
  environment={**os.environ,'PATH':str(binary)+os.pathsep+os.environ['PATH'],'B10_FIXTURE_ROOT':str(fixture),'B10_FIXTURE_LOG':str(log),'B10_FIRST_STATUS':str(first),'B10_SECOND_STATUS':str(second)}
  result=subprocess.run([shutil.which('bash'),str(ROOT/'scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.sh')],env=environment,capture_output=True,text=True,timeout=10)
  assert result.returncode==status and result.stdout==result.stderr==''
  binding_path=fixture/'scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/deployment-diagnostics/tests/binding-test.py'
  expected=['python:-B '+str(children/'deployment-operation-diagnostics-smoke-test.py')]
  if not first:expected+=['python:-B '+str(binding_path),'bash-suite']
  assert log.read_text().splitlines()==expected
print("Shared deployment-operation diagnostics tests passed (report, CloudFormation, safe CLI and wrapper dispatch).")
