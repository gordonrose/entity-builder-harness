#!/usr/bin/env python3
"""Govern one fixed isolated native PostgreSQL restore proof."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[8]
DATABASE="kanbien-core-platform-persistence"; CLUSTER="kanbien-core-platform"; SERVICE="kanbien-core-platform-core-server-persistence"; STACK="kanbien-core-platform-core-server-persistence"; FOUNDATION="kanbien-core-platform-foundation"; LOG_GROUP="/aws/ecs/kanbien-core-platform"
EVIDENCE_CLASS="live"  # Only isolated imported test harnesses may change this; no CLI bypass.
SNAPSHOT=re.compile(r"^kanbien-core-platform-persistence-recovery-(?P<day>[0-9]{8})(?P<suffix>-[a-z0-9]{1,8})?$"); RECORD_ID="core-persistence-acceptance-v1"; FACT_DIGEST=hashlib.sha256(b"kanbien-core-persistence-acceptance-v1").hexdigest(); DEADLINE=120
RESTORE_ACCEPTED_RESULT="KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED"
RESTORE_REJECTED_RESULTS={
 "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_RECORD_MISMATCH",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_CONTENT_UNAVAILABLE",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE",
}
def load():
 p=ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"; s=importlib.util.spec_from_file_location("prepare",p); m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m); return m
def proof_receipts():
 p=ROOT/"scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py"; s=importlib.util.spec_from_file_location("persistence_proof_receipts",p); m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m); return m
def task_evidence():
    path = Path(__file__).resolve().parents[1] / "ecs-task-evidence.py"
    spec = importlib.util.spec_from_file_location("persistence_ecs_task_evidence", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def emit(verdict,*codes,facts=None):
 v={"schema":"deploy/isolated-persistence-restore-rehearsal-report/v1","target":"kanbien-core-platform","scope":"core-server-persistence","verdict":verdict,"findings":[{"code":c} for c in codes]};
 if facts:v["facts"]=facts
 print(json.dumps(v,sort_keys=True)); return 0 if verdict in {"restored","accepted","cleaned-up"} else 1
def outputs(m,name):
 ok,d,c=m.aws("cloudformation","describe-stacks","--stack-name",name); xs=d.get("Stacks") if ok and isinstance(d,dict) else None
 return ({x.get("OutputKey"):x.get("OutputValue") for x in xs[0].get("Outputs",[]) if isinstance(x,dict) and isinstance(x.get("OutputKey"),str) and isinstance(x.get("OutputValue"),str)},"ok") if isinstance(xs,list) and len(xs)==1 and isinstance(xs[0],dict) else (None,c if not ok else "persistence-restore-stack-outputs-unavailable")
def db(m,identifier):
 ok,d,c=m.aws("rds","describe-db-instances","--db-instance-identifier",identifier); xs=d.get("DBInstances") if ok and isinstance(d,dict) else None
 return (xs[0],"ok") if isinstance(xs,list) and len(xs)==1 and isinstance(xs[0],dict) else (None,c if not ok else "persistence-restore-database-unavailable")
def snapshot(m,identifier):
 ok,d,c=m.aws("rds","describe-db-snapshots","--db-snapshot-identifier",identifier); xs=d.get("DBSnapshots") if ok and isinstance(d,dict) else None
 return (xs[0],"ok") if isinstance(xs,list) and len(xs)==1 and isinstance(xs[0],dict) else (None,c if not ok else "persistence-recovery-point-unavailable")
def restore_id(snapshot_id):
 x=SNAPSHOT.fullmatch(snapshot_id); return f"kanbien-core-platform-persistence-restore-{x.group('day')}{x.group('suffix') or ''}" if x else None
def source(m):
 if not m.live_budget()[0]:return None,"target-budget-live-configuration-invalid"
 v,c=db(m,DATABASE)
 if not isinstance(v,dict) or v.get("DBInstanceStatus")!="available" or v.get("PubliclyAccessible") is not False or v.get("StorageEncrypted") is not True:return None,c if v is None else "persistence-restore-source-not-healthy"
 ok,d,c=m.aws("ecs","describe-services","--cluster",CLUSTER,"--services",SERVICE); xs=d.get("services") if ok and isinstance(d,dict) else None; s=xs[0] if isinstance(xs,list) and len(xs)==1 and isinstance(xs[0],dict) else None
 return (v,"ok") if isinstance(s,dict) and s.get("desiredCount")==1 and s.get("runningCount")==1 else (None,c if not ok else "persistence-restore-source-service-not-healthy")
def controls(m):
 s,c=outputs(m,STACK); f,_=outputs(m,FOUNDATION)
 needed={"CoreServerPersistenceRestorationVerifierTaskDefinitionArn","PersistenceRestorationVerifierSecurityGroupId","PersistenceRestoredDatabaseSecurityGroupId","PersistenceRestorationVerifierTaskRoleName"}
 if not isinstance(s,dict) or not needed<=s.keys() or any(not s[k] for k in needed):return None,"persistence-restore-control-surface-unavailable"
 if not isinstance(f,dict) or not isinstance(f.get("PrivateSubnetIds"),str) or not f["PrivateSubnetIds"]:return None,"persistence-restore-private-network-unavailable"
 s["PrivateSubnetIds"]=f["PrivateSubnetIds"];return s,"ok"
def correct(restored,src,group):
 attached=[x.get("VpcSecurityGroupId") for x in restored.get("VpcSecurityGroups",[]) if isinstance(x,dict)]; a=src.get("DBSubnetGroup",{}).get("DBSubnetGroupName") if isinstance(src.get("DBSubnetGroup"),dict) else None; b=restored.get("DBSubnetGroup",{}).get("DBSubnetGroupName") if isinstance(restored.get("DBSubnetGroup"),dict) else None
 return restored.get("DBInstanceStatus")=="available" and restored.get("PubliclyAccessible") is False and restored.get("StorageEncrypted") is True and restored.get("IAMDatabaseAuthenticationEnabled") is True and restored.get("Engine")=="postgres" and attached==[group] and isinstance(a,str) and a==b
def parsed_time(value):
 if not isinstance(value,str):return None
 try:
  parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
  return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
 except (ValueError,TypeError,OverflowError):return None

def read_record_proof(path):
 """A retained successful create/read proves this fixed record existed by stop."""
 try:
  receipt=proof_receipts().validate(json.loads(Path(path).read_text(encoding="utf-8")))
 except (OSError,UnicodeError,ValueError,TypeError,KeyError):return None,"persistence-restore-record-proof-invalid"
 task=receipt["task"]; context=receipt["context"]; provenance=receipt["provenance"]
 results={"create":"KANBIEN_CORE_PERSISTENCE_RECORD_ACCEPTED","read":"KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED"}
 operation=receipt.get("operation")
 if receipt.get("proof_type")!="verifier" or not isinstance(operation,str) or operation not in results or context.get("record_id")!=RECORD_ID or task.get("result_code")!=results[operation] or task.get("exit_code")!=0:return None,"persistence-restore-record-proof-binding-invalid"
 if provenance.get("controller")!="verify-candidate" or provenance.get("collection_method")!="ecs-terminal-task+task-definition+safe-log" or provenance.get("evidence_class","live")!=EVIDENCE_CLASS:return None,"persistence-restore-record-proof-provenance-invalid"
 definition=task.get("definition"); image=task.get("image_digest")
 if not isinstance(definition,str) or re.fullmatch(r"arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:[1-9][0-9]*",definition) is None or not isinstance(image,str) or re.fullmatch(r"sha256:[a-f0-9]{64}",image) is None:return None,"persistence-restore-record-proof-identity-invalid"
 started=parsed_time(task.get("started_at")); stopped=parsed_time(task.get("stopped_at")); collected=parsed_time(provenance.get("collected_at"))
 deadline=context.get("completion_deadline_seconds"); duration=context.get("completion_duration_seconds")
 if started is None or stopped is None or collected is None or not started<=stopped<=collected or type(deadline) is not int or deadline<=0 or type(duration) is not int or duration!=int((stopped-started).total_seconds()) or duration>deadline:return None,"persistence-restore-record-proof-time-invalid"
 return receipt,"ok"

def recovery_point_binding(src,point,sid,rid,proof):
 """Bind source incarnation, retained record and exact snapshot before restore."""
 if not isinstance(src,dict) or not isinstance(point,dict) or rid!=restore_id(sid):return None,"persistence-restore-rehearsal-identity-invalid"
 resource=src.get("DbiResourceId")
 if src.get("DBInstanceIdentifier")!=DATABASE or point.get("DBSnapshotIdentifier")!=sid or point.get("DBInstanceIdentifier")!=DATABASE or not isinstance(resource,str) or not resource or point.get("DbiResourceId")!=resource:return None,"persistence-restore-snapshot-source-mismatch"
 created=parsed_time(src.get("InstanceCreateTime")); taken=parsed_time(point.get("SnapshotCreateTime"))
 original=parsed_time(point.get("OriginalSnapshotCreateTime")) if "OriginalSnapshotCreateTime" in point else taken
 started=parsed_time(proof["task"].get("started_at")); stopped=parsed_time(proof["task"].get("stopped_at"))
 if created is None or taken is None or original is None or started is None or stopped is None or original>taken:return None,"persistence-restore-recovery-time-invalid"
 if created>started:return None,"persistence-restore-record-source-incarnation-mismatch"
 if stopped>original:return None,"persistence-restore-snapshot-precedes-retained-record"
 tags={"Target":"kanbien-core-platform","Purpose":"isolated-persistence-restore-rehearsal","RecoverySnapshot":sid,"SourceDatabaseResourceId":resource,"RetainedRecordId":RECORD_ID,"RecordProofDigest":proof["integrity"]["payload_sha256"]}
 facts={"snapshot":sid,"restored_database":rid,"record_id":RECORD_ID,"record_proof_digest":proof["integrity"]["payload_sha256"],"source_database_resource_id":resource,"record_proven_at":stopped.isoformat().replace("+00:00","Z"),"snapshot_recovery_time":original.isoformat().replace("+00:00","Z")}
 return (tags,facts),"ok"

def existing_restore_binding(value,rid,expected):
 if value.get("DBInstanceIdentifier")!=rid:return "persistence-restore-operation-binding-mismatch"
 tags=value.get("TagList")
 if not isinstance(tags,list) or not all(isinstance(item,dict) and isinstance(item.get("Key"),str) and isinstance(item.get("Value"),str) for item in tags):return "persistence-restore-operation-binding-unproven"
 actual={item["Key"]:item["Value"] for item in tags}
 if len(actual)!=len(tags) or not set(expected)<=set(actual):return "persistence-restore-operation-binding-unproven"
 return "ok" if all(actual[key]==value for key,value in expected.items()) else "persistence-restore-operation-binding-mismatch"

def restore(m,sid,rid,observe_only=False,record_proof_path=None):
 proof,code=read_record_proof(record_proof_path)
 if proof is None:return emit("blocked",code)
 src,c=source(m); point,pc=snapshot(m,sid); ctl,cc=controls(m)
 if src is None:return emit("blocked",c)
 if point is None or point.get("Status")!="available" or point.get("Encrypted") is not True or point.get("DBInstanceIdentifier")!=DATABASE:return emit("blocked",pc if point is None else "persistence-recovery-point-invalid")
 binding,code=recovery_point_binding(src,point,sid,rid,proof)
 if binding is None:return emit("blocked",code)
 tags,facts=binding
 if ctl is None:return emit("blocked",cc)
 value,status=db(m,rid)
 if value is None:
  if status!="aws-resource-missing":return emit("uncertain",status,facts=facts)
  if observe_only:return emit("uncertain","persistence-restore-operation-not-observed",facts=facts)
  subnet=src.get("DBSubnetGroup",{}).get("DBSubnetGroupName") if isinstance(src.get("DBSubnetGroup"),dict) else None; cls=src.get("DBInstanceClass")
  if not isinstance(subnet,str) or not isinstance(cls,str):return emit("blocked","persistence-restore-source-shape-invalid")
  ok,_,c=m.aws("rds","restore-db-instance-from-db-snapshot","--db-instance-identifier",rid,"--db-snapshot-identifier",sid,"--db-instance-class",cls,"--db-subnet-group-name",subnet,"--vpc-security-group-ids",ctl["PersistenceRestoredDatabaseSecurityGroupId"],"--no-publicly-accessible","--no-multi-az","--copy-tags-to-snapshot","--tags",*[f"Key={key},Value={value}" for key,value in tags.items()])
  return emit("pending" if ok else "uncertain","persistence-restore-submitted-awaiting-provider-observation" if ok else c,facts=facts)
 bound=existing_restore_binding(value,rid,tags)
 if bound!="ok":return emit("uncertain" if bound.endswith("unproven") else "blocked",bound,facts=facts)
 if value.get("DBInstanceStatus") in {"creating","backing-up","modifying","rebooting","configuring-enhanced-monitoring"}:return emit("pending","persistence-restore-still-provisioning",facts=facts)
 if value.get("DBInstanceStatus") in {"failed","incompatible-restore","inaccessible-encryption-credentials","storage-full"}:return emit("failed","persistence-restore-provider-failed",facts=facts)
 if value.get("DBInstanceStatus")!="available":return emit("uncertain","persistence-restore-provider-status-unknown",facts=facts)
 return emit("restored","persistence-restored-database-ready",facts=facts) if correct(value,src,ctl["PersistenceRestoredDatabaseSecurityGroupId"]) else emit("blocked","persistence-restored-database-posture-invalid")
def task_def_valid(m,arn):
 ok,d,_=m.aws("ecs","describe-task-definition","--task-definition",arn); t=d.get("taskDefinition") if ok and isinstance(d,dict) else None; cs=t.get("containerDefinitions") if isinstance(t,dict) else None
 if not isinstance(cs,list) or len(cs)!=1 or not isinstance(cs[0],dict):return False
 # ECS describes task-definition environment and secret fields as lower-case
 # ``name``/``value``/``valueFrom``.  Keep this parser deliberately narrow:
 # only the exact verifier shape may reach an isolated restored database.
 c=cs[0]; environment=c.get("environment",[]); secret_entries=c.get("secrets",[])
 if not isinstance(environment,list) or not isinstance(secret_entries,list) or not all(isinstance(item,dict) and isinstance(item.get("name"),str) for item in environment+secret_entries):return False
 env={x["name"]:x.get("value") for x in environment}; secrets={x["name"] for x in secret_entries}
 required={"PERSISTENCE_POSTGRES_PORT":"5432","PERSISTENCE_POSTGRES_DATABASE":"kanbienpersistence","PERSISTENCE_POSTGRES_SCHEMA":"platform","PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME":"core_runtime","PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE":"restoration-identity-supplied-at-governed-task-run"}
 return c.get("name")=="persistence-restoration-verifier" and c.get("command")==["artifacts/kanbien-core-server-persistence-restore-verifier.main.js"] and not secrets and "PERSISTENCE_POSTGRES_HOST" not in env and all(env.get(key)==value for key,value in required.items()) and isinstance(env.get("PERSISTENCE_POSTGRES_IAM_REGION"),str)

def restore_identity_resource(restored):
 resource=restored.get("DbiResourceId") if isinstance(restored,dict) else None
 return f"arn:aws:rds-db:eu-west-1:337159794548:dbuser:{resource}/core_runtime" if isinstance(resource,str) and resource else None

def temporary_restore_identity_policy(m, controls, restored, observe_only=False):
 """Grant only this restored instance; do not retain source-database access."""
 resource=restore_identity_resource(restored); role=controls.get("PersistenceRestorationVerifierTaskRoleName") if isinstance(controls,dict) else None
 if not isinstance(resource,str) or not isinstance(role,str) or not role:return "persistence-restoration-identity-binding-unavailable",None
 name="kanbien-core-platform-restoration-verifier-current-instance"
 policy={"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"rds-db:connect","Resource":resource}]}
 ok,value,code=m.aws("iam","get-role-policy","--role-name",role,"--policy-name",name)
 if ok:
  actual=value.get("PolicyDocument") if isinstance(value,dict) else None
  return ("ok",resource) if actual==policy else ("persistence-restoration-temporary-identity-policy-mismatch",None)
 if code!="aws-resource-missing":return code,None
 if observe_only:return "persistence-restoration-temporary-identity-policy-not-observed",None
 ok,_,code=m.aws("iam","put-role-policy","--role-name",role,"--policy-name",name,"--policy-document",json.dumps(policy,separators=(",",":")))
 return ("persistence-restoration-temporary-identity-policy-submitted",resource) if ok else (code,None)

def remove_temporary_restore_identity_policy(m, controls, observe_only=False):
 role=controls.get("PersistenceRestorationVerifierTaskRoleName") if isinstance(controls,dict) else None
 if not isinstance(role,str) or not role:return "persistence-restoration-identity-binding-unavailable"
 name="kanbien-core-platform-restoration-verifier-current-instance";ok,_,code=m.aws("iam","get-role-policy","--role-name",role,"--policy-name",name)
 if not ok:return "ok" if code=="aws-resource-missing" else code
 if observe_only:return "persistence-restoration-temporary-identity-policy-removal-not-observed"
 ok,_,code=m.aws("iam","delete-role-policy","--role-name",role,"--policy-name",name)
 return "persistence-restoration-temporary-identity-policy-removal-submitted" if ok else code
def task_image_digest(m,arn):
 ok,d,_=m.aws("ecs","describe-task-definition","--task-definition",arn); t=d.get("taskDefinition") if ok and isinstance(d,dict) else None; cs=t.get("containerDefinitions") if isinstance(t,dict) else None; c=cs[0] if isinstance(cs,list) and len(cs)==1 and isinstance(cs[0],dict) else None; image=c.get("image") if isinstance(c,dict) else None
 return image.rsplit("@",1)[1] if isinstance(image,str) and image.count("@")==1 and image.rsplit("@",1)[1].startswith("sha256:") else None
def task_duration(task):
 try:
  a=datetime.fromisoformat(task["startedAt"].replace("Z","+00:00")); b=datetime.fromisoformat(task["stoppedAt"].replace("Z","+00:00")); return int((b-a).total_seconds()) if b>=a else None
 except (KeyError,ValueError,TypeError,OverflowError):return None
def terminal_result(m,arn):
 """Read only the verifier's closed result envelope, never raw provider output."""
 tid=arn.rsplit("/",1)[-1]; ok,d,c=m.aws("logs","get-log-events","--log-group-name",LOG_GROUP,"--log-stream-name",f"persistence-restoration-verifier/persistence-restoration-verifier/{tid}","--start-from-head"); xs=d.get("events") if ok and isinstance(d,dict) else None
 if not isinstance(xs,list):return "unavailable",None
 results=[]
 for event in xs:
  try:value=json.loads(event.get("message", "")) if isinstance(event,dict) else None
  except (json.JSONDecodeError,TypeError):continue
  if not isinstance(value,dict) or set(value)!={"verdict","code"}:continue
  verdict,code=value.get("verdict"),value.get("code")
  if verdict=="accepted" and code==RESTORE_ACCEPTED_RESULT:results.append(("accepted",code))
  elif verdict=="rejected" and code in RESTORE_REJECTED_RESULTS:results.append(("rejected",code))
 if len(results)!=1:return "unavailable",None
 return results[0]
def verifier_tasks(m,operation,definition):
 arns = []
 family = definition.rsplit("/", 1)[-1].split(":", 1)[0]
 for state in ("RUNNING", "STOPPED"):
     # AWS forbids combining startedBy with another ListTasks filter.
     ok, listed, code = m.aws("ecs", "list-tasks", "--cluster", CLUSTER, "--family", family, "--desired-status", state)
     values = listed.get("taskArns") if ok and isinstance(listed, dict) else None
     if not isinstance(values, list) or listed.get("nextToken") or not all(isinstance(value, str) for value in values):
         return None, "persistence-restoration-verifier-observation-uncertain"
     arns.extend(values)
 arns = list(dict.fromkeys(arns))
 matching = []
 for offset in range(0, len(arns), 100):
     batch = arns[offset:offset + 100]
     ok, described, code = m.aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", *batch)
     tasks = described.get("tasks") if ok and isinstance(described, dict) else None
     if not isinstance(tasks, list) or described.get("failures") or len(tasks) != len(batch) or not all(isinstance(task, dict) and isinstance(task.get("taskArn"), str) for task in tasks) or {task["taskArn"] for task in tasks} != set(batch):
         return None, "persistence-restoration-verifier-observation-uncertain"
     matching.extend(task["taskArn"] for task in tasks if task.get("startedBy") == operation)
 return matching,"ok"
def restore_run_identity(restored):
 # A snapshot can be restored more than once.  The ECS started-by value must
 # identify this particular isolated database incarnation, not merely the
 # snapshot date, otherwise historical verifier tasks block a clean rerun.
 resource=restored.get("DbiResourceId") if isinstance(restored,dict) else None
 return f"kanbien-restore-{hashlib.sha256(resource.encode()).hexdigest()[:16]}" if isinstance(resource,str) and resource else None
def verify(m,sid,rid,observe_only=False):
 src,c=source(m); ctl,cc=controls(m); restored,rc=db(m,rid)
 if src is None:return emit("blocked",c)
 if ctl is None:return emit("blocked",cc)
 if restored is None:return emit("blocked",rc)
 # A restore normally appears as ``creating`` before it has an endpoint. That
 # is an in-flight governed operation, not a malformed restored target. Do
 # not turn a normal provider lifecycle state into a false hard failure.
 status=restored.get("DBInstanceStatus")
 if status in {"creating","backing-up","modifying","rebooting","configuring-enhanced-monitoring"}:return emit("pending","persistence-restore-still-provisioning",facts={"snapshot":sid,"restored_database":rid})
 if status in {"failed","incompatible-restore","inaccessible-encryption-credentials","storage-full"}:return emit("failed","persistence-restore-provider-failed",facts={"snapshot":sid,"restored_database":rid})
 if status!="available":return emit("uncertain","persistence-restore-provider-status-unknown",facts={"snapshot":sid,"restored_database":rid})
 if not correct(restored,src,ctl["PersistenceRestoredDatabaseSecurityGroupId"]):return emit("blocked","persistence-restored-database-posture-invalid")
 endpoint=restored.get("Endpoint",{}).get("Address") if isinstance(restored.get("Endpoint"),dict) else None; td=ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"]
 if not isinstance(endpoint,str) or not task_def_valid(m,td):return emit("blocked","persistence-restoration-verifier-definition-invalid")
 identity_status,identity_reference=temporary_restore_identity_policy(m,ctl,restored,observe_only)
 if identity_status!="ok":return emit("pending" if identity_status.endswith("submitted") else "uncertain" if identity_status.endswith("not-observed") else "blocked",identity_status,facts={"snapshot":sid,"restored_database":rid})
 started=restore_run_identity(restored)
 if started is None:return emit("blocked","persistence-restored-database-identity-unavailable")
 arns,c=verifier_tasks(m,started,ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"])
 if arns is None:return emit("uncertain",c)
 if arns:
  ok,d,c=m.aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",*arns); observed=d.get("tasks") if ok and isinstance(d,dict) else None; xs=[x for x in observed if isinstance(x,dict) and x.get("taskDefinitionArn")==td] if isinstance(observed,list) else []
  if len(arns)!=1 or len(xs)!=1 or d.get("failures"):return emit("uncertain","persistence-restoration-verifier-task-identity-ambiguous")
  t=xs[0]
  facts={"snapshot":sid,"restored_database":rid,"operation_id":started}
  if t.get("taskArn")!=arns[0] or t.get("startedBy")!=started:return emit("blocked","persistence-restoration-verifier-task-binding-invalid",facts=facts)
  expected_env={"PERSISTENCE_POSTGRES_HOST":endpoint,"PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE":identity_reference,"PERSISTENCE_ACCEPTANCE_RECORD_ID":RECORD_ID,"PERSISTENCE_ACCEPTANCE_FACT_DIGEST":FACT_DIGEST}
  if not task_evidence().task_overrides_match(t,"persistence-restoration-verifier",expected_env):return emit("blocked","persistence-restoration-verifier-task-binding-invalid",facts=facts)
  if t.get("lastStatus") in {"PROVISIONING","PENDING","ACTIVATING","RUNNING","DEACTIVATING","STOPPING","DEPROVISIONING"}:return emit("pending","persistence-restoration-verifier-still-running",facts=facts)
  if t.get("lastStatus")!="STOPPED":return emit("uncertain","persistence-restoration-verifier-status-unknown",facts=facts)
  containers=t.get("containers"); exit_code=containers[0].get("exitCode") if isinstance(containers,list) and len(containers)==1 and isinstance(containers[0],dict) else None; duration=task_duration(t); arn=t.get("taskArn")
  if type(exit_code) is not int or duration is None or not isinstance(arn,str):return emit("uncertain","persistence-restoration-verifier-completion-evidence-unavailable",facts=facts)
  if duration>DEADLINE:return emit("failed","persistence-restoration-verifier-completion-invalid",facts=facts)
  evidence,result=terminal_result(m,arn)
  if exit_code!=0:
   return emit("failed","persistence-restoration-verifier-rejected" if evidence=="rejected" else "persistence-restoration-verifier-completion-invalid",facts={**facts,**({"safe_result_code":result} if evidence=="rejected" and result is not None else {})})
  # CloudWatch delivery can lag a stopped task.  A clean exit without the
  # closed acceptance envelope is therefore pending evidence, not proof; the
  # reconciler will never manufacture a receipt from it.
  if evidence!="accepted":return emit("pending","persistence-restoration-verifier-log-evidence-unavailable",facts=facts)
  digest=task_image_digest(m,td)
  if digest is None:return emit("blocked","persistence-restoration-verifier-receipt-identity-unavailable")
  try:
   receipt=proof_receipts().make(proof_type="restore",operation="isolated-restore",task=t,image_digest=digest,result_code="KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED",context={"snapshot":sid,"restored_database":rid,"completion_deadline_seconds":DEADLINE,"completion_duration_seconds":duration},controller="rehearse-isolated-database-restore",collected_at=datetime.now().astimezone().isoformat().replace("+00:00","Z"));path=proof_receipts().persist(receipt)
  except Exception:return emit("blocked","persistence-restoration-verifier-receipt-persistence-failed")
  return emit("accepted","persistence-isolated-restoration-record-retrieved",facts={**facts,"verifier_task":arn.rsplit("/",1)[-1],"completion_duration_seconds":duration,"proof_receipt":str(path.relative_to(ROOT))})
 if observe_only:return emit("uncertain","persistence-restoration-verifier-operation-not-observed",facts={"snapshot":sid,"restored_database":rid,"operation_id":started})
 net=f"awsvpcConfiguration={{subnets=[{ctl['PrivateSubnetIds']}],securityGroups=[{ctl['PersistenceRestorationVerifierSecurityGroupId']}],assignPublicIp=DISABLED}}"; overrides=json.dumps({"containerOverrides":[{"name":"persistence-restoration-verifier","environment":[{"name":"PERSISTENCE_POSTGRES_HOST","value":endpoint},{"name":"PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE","value":identity_reference},{"name":"PERSISTENCE_ACCEPTANCE_RECORD_ID","value":RECORD_ID},{"name":"PERSISTENCE_ACCEPTANCE_FACT_DIGEST","value":FACT_DIGEST}]}]})
 ok,_,c=m.aws("ecs","run-task","--cluster",CLUSTER,"--task-definition",td,"--launch-type","FARGATE","--count","1","--started-by",started,"--client-token",started,"--network-configuration",net,"--overrides",overrides)
 return emit("pending" if ok else "uncertain","persistence-restoration-verifier-submitted-awaiting-provider-observation" if ok else c,facts={"snapshot":sid,"restored_database":rid,"operation_id":started})
def cleanup(m,sid,rid,observe_only=False):
 if not m.live_budget()[0]:return emit("blocked","target-budget-live-configuration-invalid")
 restored,c=db(m,rid)
 if restored is None:return emit("cleaned-up","persistence-restored-database-absent",facts={"snapshot":sid,"restored_database":rid}) if c=="aws-resource-missing" else emit("blocked",c)
 ctl,cc=controls(m)
 if ctl is None:return emit("blocked",cc)
 attached=[x.get("VpcSecurityGroupId") for x in restored.get("VpcSecurityGroups",[]) if isinstance(x,dict)]
 if attached!=[ctl["PersistenceRestoredDatabaseSecurityGroupId"]] or restored.get("PubliclyAccessible") is not False:return emit("blocked","persistence-restored-database-cleanup-target-invalid")
 if restored.get("DBInstanceStatus")=="deleting":return emit("pending","persistence-restored-database-deletion-pending",facts={"snapshot":sid,"restored_database":rid})
 if observe_only:return emit("uncertain","persistence-restored-database-deletion-not-observed",facts={"snapshot":sid,"restored_database":rid})
 started=restore_run_identity(restored)
 if started is None:return emit("blocked","persistence-restored-database-identity-unavailable")
 tasks,code=verifier_tasks(m,started,ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"])
 if tasks is None:return emit("uncertain",code)
 if tasks:
  ok,described,code=m.aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",*tasks)
  listed=described.get("tasks") if ok and isinstance(described,dict) else None
  if not isinstance(listed,list) or len(listed)!=len(tasks) or described.get("failures"):return emit("uncertain","persistence-restore-cleanup-task-state-uncertain")
  if any(not isinstance(task,dict) or task.get("lastStatus")!="STOPPED" for task in listed):return emit("pending","persistence-restore-cleanup-verifier-still-running")
 removed=remove_temporary_restore_identity_policy(m,ctl,observe_only)
 if removed!="ok":return emit("pending" if removed.endswith("submitted") else "uncertain" if removed.endswith("not-observed") else "blocked",removed,facts={"snapshot":sid,"restored_database":rid})
 ok,_,c=m.aws("rds","delete-db-instance","--db-instance-identifier",rid,"--skip-final-snapshot")
 return emit("pending" if ok else "uncertain","persistence-restored-database-deletion-submitted" if ok else c,facts={"snapshot":sid,"restored_database":rid})
def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument("--operation");p.add_argument("--snapshot-id");p.add_argument("--record-proof-receipt",type=Path);p.add_argument("--json",action="store_true");p.add_argument("--observe-only",action="store_true");p.add_argument("--validate-arguments",action="store_true");a,u=p.parse_known_args();rid=restore_id(a.snapshot_id) if isinstance(a.snapshot_id,str) else None
 if u or a.operation not in {"restore","verify","cleanup"} or rid is None or (a.operation=="restore")!=(a.record_proof_receipt is not None):return emit("blocked","persistence-isolated-restore-arguments-invalid")
 if a.validate_arguments:
  print(json.dumps({"schema":"deploy/command-arguments-report/v1","verdict":"valid","findings":[],"proof_contract": {"proof_type":"restore","operation":"isolated-restore","result_code":"KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED","family":"kanbien-core-platform-persistence-restoration-verifier","deadline_workload":"persistence-restoration-verifier"} if a.operation=="verify" else None}));return 0
 m=load();return restore(m,a.snapshot_id,rid,a.observe_only,a.record_proof_receipt) if a.operation=="restore" else verify(m,a.snapshot_id,rid,a.observe_only) if a.operation=="verify" else cleanup(m,a.snapshot_id,rid,a.observe_only)
if __name__=="__main__":raise SystemExit(main())
