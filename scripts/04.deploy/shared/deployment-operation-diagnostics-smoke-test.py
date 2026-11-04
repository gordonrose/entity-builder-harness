#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.deployment-operation-diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-31"
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

# Private task source bundles are selected independently of own observations;
# old verifier/configuration/native readers are not widened to accept them.
def source(ordinal):
 return {"schema":"core/diagnostic-record/v1","code":"core.persistence.in-memory-boundary-failed","definitionVersion":1,"detail":{"operation":"initialize","phase":"get-id","reason":"boundary-threw","effect":"write-not-reached","ordinal":ordinal}}
sources=[source(index) for index in range(9)]
own={"schema":"core/diagnostic-record/v1","code":"kanbien-core-server.operations.verification-boundary-failed","definitionVersion":1,"detail":{"task":"verification","operation":"verification","phase":"fetch","condition":"rejected","effect":"unknown"}}
failure={"schema":"deploy/persistence-task-failure/v1","task":"verification","verdict":"rejected","code":"KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE","diagnostic":sources[0],"related_diagnostics":sources[1:],"observations":[own]}
checked=diagnostics.validate_persistence_task_failure(failure,"verification")
assert checked==failure and checked is not failure and checked["diagnostic"] is not failure["diagnostic"]
diagnostics.validate(valid(task_failure=failure))
for mutate in [
 lambda v:v.update(extra="PRIVATE_TASK_CANARY"),lambda v:v.update(code="BOOTSTRAP_PRIVATE_TASK_CANARY"),
 lambda v:v.update(task="administration"),lambda v:v.update(observations=[own]*9),
 lambda v:v.update(related_diagnostics=sources),lambda v:v.update(diagnostic=own),
 lambda v:v["diagnostic"]["detail"].update(private="PRIVATE_TASK_CANARY"),
 lambda v:v.update(source_bundles=[{"diagnostic":source(10)}]*9),
 lambda v:v.update(source_bundles=[{"diagnostic":sources[0],"related_diagnostics":sources[1:]}]),
 lambda v:v.update(overflow={"observations":0,"source_bundles":0}),
 lambda v:v.update(overflow={"observations":True,"source_bundles":1}),
 lambda v:v.update(overflow={"observations":-1,"source_bundles":0}),
 lambda v:v.update(overflow={"observations":1,"source_bundles":0,"private":"PRIVATE_TASK_CANARY"}),
]:
 malformed=copy.deepcopy(failure);mutate(malformed)
 try:diagnostics.validate_persistence_task_failure(malformed,"verification")
 except diagnostics.DiagnosticFailure as error:assert error.codes==("persistence-task-failure-invalid",)
 else:raise AssertionError("malformed/unselected private task evidence admitted")
try:diagnostics.validate_verifier_result(failure)
except diagnostics.DiagnosticFailure:pass
else:raise AssertionError("private task envelope widened historical verifier reader")
different_companions={"diagnostic":sources[0],"related_diagnostics":[*sources[1:8],source(9)]}
extended={**failure,"source_bundles":[different_companions],"overflow":{"observations":2,"source_bundles":1}}
assert diagnostics.validate_persistence_task_failure(extended,"verification")==extended
def event(value):return {"message":json.dumps(value)}
selected,observation=diagnostics.collect_persistence_task_failure({"events":[{"message":"PRIVATE_TASK_CANARY"},event(failure),event({"private":"PRIVATE_TASK_CANARY"}),event({**failure,"diagnostic":source(10),"related_diagnostics":sources[1:]})]},"verification")
assert observation=="malformed" and selected["diagnostic"]==sources[0] and selected["related_diagnostics"]==sources[1:]
assert selected["source_bundles"]==[{"diagnostic":source(10),"related_diagnostics":sources[1:]}] and selected["observations"]==[own,own]
full={**failure,"observations":[own]*8,"source_bundles":[{"diagnostic":source(index),"related_diagnostics":sources[1:]} for index in range(10,18)]}
later={**failure,"diagnostic":source(20),"observations":[own,own],"overflow":{"observations":3,"source_bundles":4}}
merged,state=diagnostics.collect_persistence_task_failure({"events":[event(full),event(later)]},"verification")
assert state=="complete" and merged["diagnostic"]==sources[0] and merged["related_diagnostics"]==sources[1:]
assert merged["observations"]==[own]*8 and merged["source_bundles"]==full["source_bundles"] and merged["overflow"]=={"observations":5,"source_bundles":5}
maximum=diagnostics.runtime_contract().persistence_task_failure_contract()["maxOverflowCount"]
first={**failure,"overflow":{"observations":maximum,"source_bundles":0}}
merged,state=diagnostics.collect_persistence_task_failure({"events":[event(first),event({**failure,"overflow":{"observations":1,"source_bundles":0}})]},"verification")
assert state=="incomplete" and merged==first
merged,state=diagnostics.collect_persistence_task_failure({"events":[event(failure)]+[event({})]*100},"verification")
assert state=="incomplete" and merged==failure

run_prefix="scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/"
command=run_prefix+"verify-candidate/script.sh"
task_arn="arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/"+"a"*32
controller_report={"schema":"deploy/private-persistence-verification-report/v1","target":"kanbien-core-platform","scope":"core-server-persistence","verdict":"failed","findings":[{"code":"PRIVATE_TASK_CANARY"}],"facts":{"operation_id":"kp-"+"b"*32,"verifier_task":task_arn,"task_failure":failure}}
checkpoint=diagnostics.validate_persistence_controller_checkpoint(controller_report,command)
assert checkpoint["facts"]==controller_report["facts"]
for key,value in [("operation_id","kp-PRIVATE_TASK_CANARY"),("verifier_task",task_arn.replace("337159794548","000000000000")),("proof_receipt","../PRIVATE_TASK_CANARY.json"),("completed_at","2026-10-31T00:00:00"),("evidence_reuse","PRIVATE_TASK_CANARY")]:
 changed=copy.deepcopy(controller_report);changed["facts"][key]=value
 checked=diagnostics.validate_persistence_controller_checkpoint(changed,command)
 assert key not in checked["facts"] and checked["facts"]["task_failure"]==failure
changed=copy.deepcopy(controller_report);changed["facts"]["task_failure"]["diagnostic"]["detail"]["private"]="PRIVATE_TASK_CANARY"
assert diagnostics.validate_persistence_controller_checkpoint(changed,command)["facts"]=={"operation_id":"kp-"+"b"*32,"verifier_task":task_arn}
assert diagnostics.validate_persistence_controller_checkpoint({**controller_report,"schema":"other"},command) is None
assert diagnostics.validate_persistence_controller_checkpoint(controller_report,run_prefix+"run-administration/script.sh") is None

def load_controller(relative):
 spec=importlib.util.spec_from_file_location("isolated_diagnostic_controller",ROOT/relative)
 result=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(result);return result
identity=load_controller(run_prefix+"rehearse-runtime-credential-lifecycle/script.py")
pending={**controller_report,"verdict":"pending","facts":{"operation_id":"kp-"+"b"*32,"verifier_task":task_arn}}
for timeout in (False,True):
 completed=subprocess.CompletedProcess([],17,json.dumps(controller_report),"PRIVATE_CHILD_CANARY\n"+json.dumps(pending))
 fault=subprocess.TimeoutExpired(["bash"],180,output=completed.stdout.encode(),stderr=completed.stderr.encode()) if timeout else None
 with patch.object(identity.subprocess,"run",side_effect=fault,return_value=completed) as child:
  assert identity.child(command,"--mode","create","--json") is None
  assert child.call_count==1
 assert identity.CHILD_CHECKPOINT["facts"]["task_failure"]==failure
 assert identity.CHILD_CHECKPOINT["facts"]["operation_id"]=="kp-"+"b"*32
 capture=io.StringIO()
 with redirect_stdout(capture):assert identity.report("blocked","outer-original-code")==1
 body=json.loads(capture.getvalue());assert body["verdict"]=="failed" and body["findings"]==[{"code":"outer-original-code"}]
 assert "PRIVATE_CHILD_CANARY" not in capture.getvalue()
 outer=load_controller(run_prefix+"rehearse-observability-readiness/script.py")
 wrapped=body
 expired=subprocess.TimeoutExpired(["bash"],420,output=json.dumps(wrapped).encode(),stderr=b"PRIVATE_CHILD_CANARY")
 with patch.object(outer.subprocess,"run",side_effect=expired) as child:
  try:outer.lifecycle(Path("unused-receipt"),"revoke-await-observability")
  except outer.RehearsalFailure as error:assert str(error)=="observability-rehearsal-lifecycle-outcome-uncertain"
  else:raise AssertionError("outer timeout was accepted")
  assert child.call_count==1
 capture=io.StringIO()
 with redirect_stdout(capture):assert outer.report("blocked","observability-rehearsal-lifecycle-outcome-uncertain")==1
 body=json.loads(capture.getvalue());assert body["verdict"]=="blocked"
 assert body["facts"]["child_checkpoint"]["facts"]["child_checkpoint"]["facts"]["task_failure"]==failure
 assert "PRIVATE_CHILD_CANARY" not in capture.getvalue()

# Finite legacy verdict propagation uses the selected checkpoint only; an
# unknown child verdict cannot replace the outer blocked result or leak text.
for child_verdict in ["pending","failed","uncertain","PRIVATE_CHILD_VERDICT_CANARY"]:
 completed=subprocess.CompletedProcess([],17,json.dumps({**controller_report,"verdict":child_verdict}),"")
 with patch.object(identity.subprocess,"run",return_value=completed):assert identity.child(command,"--json") is None
 capture=io.StringIO()
 with redirect_stdout(capture):assert identity.report("blocked","outer-original-code")==1
 body=json.loads(capture.getvalue())
 assert body["verdict"]==(child_verdict if child_verdict!="PRIVATE_CHILD_VERDICT_CANARY" else "blocked")
 assert body["findings"]==[{"code":"outer-original-code"}]
 assert "PRIVATE_CHILD_VERDICT_CANARY" not in capture.getvalue()
 if child_verdict!="PRIVATE_CHILD_VERDICT_CANARY":assert body["facts"]["child_checkpoint"]["facts"]["task_failure"]==failure

surface=load_controller("scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface/script.py")
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

administration=load_controller(run_prefix+"run-administration/script.py")
admin_own={"schema":"core/diagnostic-record/v1","code":"kanbien-core-server.operations.administration-boundary-failed","definitionVersion":1,"detail":{"task":"administration","operation":"administration","phase":"task-body","condition":"threw","effect":"unknown"}}
admin_failure={**failure,"task":"administration","code":"PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED","observations":[admin_own]}
configuration={"schema":"core/diagnostic-record/v1","code":"kanbien-core-server.configuration-invalid","definitionVersion":1,"detail":{"issues":[{"setting":"database.host","reason":"missing"}]}}
legacy_codes=["PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID","PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED","PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED","PERSISTENCE_ADMINISTRATION_ACCESS_DENIED","PERSISTENCE_ADMINISTRATION_CREDENTIAL_REJECTED"]
legacy=[]
for safe_code in legacy_codes:
 record=configuration if safe_code==legacy_codes[0] else sources[0]
 legacy.append({"verdict":"rejected","code":safe_code,"diagnostic":record,**({"related_diagnostics":sources[1:]} if record is sources[0] else {})})
for rejected in [admin_failure,*legacy]:
 capture=io.StringIO()
 with patch.object(administration.MIGRATION,"duration",return_value=1),patch.object(administration.MIGRATION,"task_exit",return_value=False),patch.object(administration.MIGRATION,"aws",return_value=(True,{"events":[event(rejected)]},"ok")) as provider,redirect_stdout(capture):
  assert administration.accept({"taskArn":task_arn},30,"prove-effective-privilege")==1
 assert provider.call_args.args==("logs","get-log-events","--log-group-name",administration.LOG_GROUP,"--log-stream-name","persistence-administration/persistence-administration/"+"a"*32,"--start-from-head")
 body=json.loads(capture.getvalue());assert body["verdict"]=="blocked" and body["findings"]==[{"code":"persistence-administration-unsuccessful-completion"}]
 assert body["facts"]["administration_task"]=="a"*32 and body["facts"]["safe_result_code"]==rejected["code"]
 if rejected is admin_failure:assert body["facts"]["task_failure"]==admin_failure
 else:
  assert body["facts"]["diagnostic"]==rejected["diagnostic"]
  if "related_diagnostics" in rejected:assert body["facts"]["related_diagnostics"]==sources[1:]

# New task evidence requires positively observed target identity. The old
# unsuccessful-completion verdict and the existing single log call stay intact.
capture=io.StringIO()
with patch.object(administration.MIGRATION,"duration",return_value=1),patch.object(administration.MIGRATION,"task_exit",return_value=False),patch.object(administration.MIGRATION,"aws",return_value=(True,{"events":[event(admin_failure)]},"ok")) as provider,redirect_stdout(capture):
 assert administration.accept({"taskArn":task_arn.replace("337159794548","000000000000")},30,"prove-effective-privilege")==1
assert provider.call_count==1
assert json.loads(capture.getvalue())["facts"]=={"task_log_observation":"unavailable"}

replacement=load_controller(run_prefix+"rehearse-server-replacement/script.py")
for original_arn in [task_arn,task_arn.replace("337159794548","000000000000")]:
 capture=io.StringIO();errors=io.StringIO();calls=[]
 def interrupted_stop(*parts):
  calls.append(parts)
  checkpoint=json.loads(errors.getvalue())
  assert checkpoint["schema"]=="deploy/persistence-server-replacement-report/v1"
  assert checkpoint["target"]=="kanbien-core-platform" and checkpoint["scope"]=="core-server-persistence"
  assert checkpoint["verdict"]=="pending" and "recovery_boundary" in checkpoint["facts"]
  assert (checkpoint["facts"].get("original_task")==task_arn)==(original_arn==task_arn)
  assert diagnostics.validate_persistence_controller_checkpoint(checkpoint,run_prefix+"rehearse-server-replacement/script.sh")["facts"]==checkpoint["facts"]
  raise subprocess.TimeoutExpired(["aws"],30)
 prepare=SimpleNamespace(validate_receipt=lambda _: {},live_budget=lambda:(True,"ok"),aws=interrupted_stop)
 create=SimpleNamespace(package_gates=lambda _:True)
 with patch.object(replacement,"module",side_effect=[prepare,create]),patch.object(replacement,"current_task",return_value=({"taskArn":original_arn},"ok","definition")),patch.object(replacement,"receipt_matches_task",return_value=(True,"ok")),patch.object(sys,"argv",["replacement","--receipt","unused.json"]),redirect_stdout(capture),patch.object(sys,"stderr",errors):
  try:replacement.main()
  except subprocess.TimeoutExpired:pass
  else:raise AssertionError("interrupted stop did not escape unchanged")
 assert calls==[("ecs","stop-task","--cluster",replacement.CLUSTER,"--task",original_arn,"--reason","governed core-server-persistence replacement rehearsal")]

# Choice errors keep argparse's exit 2 without projecting the rejected value.
for owner,args,expected in [(administration,["--operation","PRIVATE_ARGUMENT_CANARY"],"persistence-administration-arguments-invalid"),(identity,["--operation","PRIVATE_ARGUMENT_CANARY"],"persistence-runtime-identity-lifecycle-arguments-invalid"),(outer,["--operation","PRIVATE_ARGUMENT_CANARY"],"observability-rehearsal-arguments-invalid"),(surface,["--mode","PRIVATE_ARGUMENT_CANARY"],"persistence-restoration-surface-arguments-invalid")]:
 capture=io.StringIO();errors=io.StringIO()
 with patch.object(sys,"argv",["isolated-controller",*args]),redirect_stdout(capture),patch.object(sys,"stderr",errors):
  try:owner.main()
  except SystemExit as error:assert error.code==2
  else:raise AssertionError("invalid choice did not retain exit 2")
 assert json.loads(capture.getvalue())["findings"]==[{"code":expected}]
 assert "PRIVATE_ARGUMENT_CANARY" not in capture.getvalue()+errors.getvalue()

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
  assert log.read_text().splitlines()==['python:-B '+str(children/'deployment-operation-diagnostics-smoke-test.py')]+([] if first else ['bash-suite'])
print("Deployment-operation diagnostics regression tests passed (historical/v2 readers, schema parity, safe CLI and actual two-suite dispatch).")
