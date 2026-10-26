#!/usr/bin/env python3
"""Govern one fixed isolated native PostgreSQL restore proof."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, time
try:import fcntl
except ImportError:fcntl=None
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[8]
REGION="eu-west-1"; DATABASE="kanbien-core-platform-persistence"; CLUSTER="kanbien-core-platform"; SERVICE="kanbien-core-platform-core-server-persistence"; STACK="kanbien-core-platform-core-server-persistence"; FOUNDATION="kanbien-core-platform-foundation"; LOG_GROUP="/aws/ecs/kanbien-core-platform"
EVIDENCE_CLASS="live"  # Only isolated imported test harnesses may change this; no CLI bypass.
SNAPSHOT=re.compile(r"^kanbien-core-platform-persistence-recovery-(?P<day>[0-9]{8})(?P<suffix>-[a-z0-9]{1,8})?$"); RECORD_ID="core-persistence-acceptance-v1"; FACT_DIGEST=hashlib.sha256(b"kanbien-core-persistence-acceptance-v1").hexdigest(); DEADLINE=120
RESTORE_ACCEPTED_RESULT="KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED"
OPERATION_DIAGNOSTICS=ROOT/"infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/operation-diagnostics"
# IAM policy observation confirms the target binding, but RDS IAM database
# authentication is separately eventually consistent.  This is a bounded
# *pre-launch stabilization wait*, not an automatic retry of a verifier that
# has already started or completed.
RESTORATION_IDENTITY_STABILIZATION_SECONDS=60
# IAM is global.  CloudTrail Event History records its management events in
# the global-event region rather than this target's regional RDS control plane.
IAM_CLOUDTRAIL_REGION="us-east-1"
# RDS exports server logs asynchronously.  The controller makes one bounded
# *read-only* observation for a completed verifier task and never retains the
# raw events, log-stream names, endpoint, or any provider text.  A later
# reconciliation may make the same read-only observation if delivery lagged.
RESTORE_SERVER_LOG_LOOKBACK_SECONDS=30
RESTORE_SERVER_LOG_TAIL_SECONDS=300
RESTORE_SERVER_LOG_EVENT_LIMIT=100
LOG_READ_LIMIT=3
DIAGNOSTIC_RESULT="KANBIEN_CORE_PERSISTENCE_CONNECTION_DIAGNOSED"
DIAGNOSTIC_COMPLETION_SCHEMA="deploy/persistence-connection-diagnostic-completion/v1"
RESTORE_REJECTED_RESULTS={
 "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_RECORD_MISMATCH",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_IAM_TOKEN_UNAVAILABLE",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_IAM_TOKEN_MATERIAL_INVALID",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_CONTENT_UNAVAILABLE",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_TRANSPORT_UNAVAILABLE",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_NEGOTIATION_UNAVAILABLE",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_DATABASE_HANDSHAKE_UNAVAILABLE",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_QUERY_UNAVAILABLE",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID",
 "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE",
}
def load():
 p=ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"; s=importlib.util.spec_from_file_location("prepare",p); m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m); return m
def proof_receipts():
 p=Path(__file__).resolve().parents[8]/"scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py"; s=importlib.util.spec_from_file_location("persistence_proof_receipts",p); m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m); return m
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
 print(json.dumps(v,sort_keys=True)); return 0 if verdict in {"restored","accepted","cleaned-up","diagnosed"} else 1
def restored_postgresql_log_group(restored_database):
 """Return the PostgreSQL group for compatibility with existing callers."""
 return f"/aws/rds/instance/{restored_database}/postgresql" if restored_database==restore_id_from_database(restored_database) else None

def restored_log_groups(restored_database):
 """Return only the two target-owned exports needed for IAM DB diagnosis."""
 if restored_database!=restore_id_from_database(restored_database):return ()
 prefix=f"/aws/rds/instance/{restored_database}/"
 return (prefix+"postgresql",prefix+"iam-db-auth-error")

def restore_id_from_database(restored_database):
 """Validate the deterministic restored identifier without accepting free text."""
 prefix="kanbien-core-platform-persistence-restore-"
 if not isinstance(restored_database,str) or not restored_database.startswith(prefix): return None
 suffix=restored_database[len(prefix):]
 return restored_database if re.fullmatch(r"[0-9]{8}(?:-[a-z0-9]{1,8})?",suffix) else None

def diagnostics():
 spec=importlib.util.spec_from_file_location("deployment_operation_diagnostics",Path(__file__).resolve().parents[8]/"scripts/04.deploy/shared/deployment-operation-diagnostics.py")
 module=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module); return module

def classify_restored_postgresql_log_events(events):
 """Closed observations only; provider text never crosses this boundary."""
 if not isinstance(events,list) or any(not isinstance(event,dict) or not isinstance(event.get("message"),str) for event in events):return "persistence-restore-server-log-observation-invalid"
 if not events:return "persistence-restore-server-log-empty"
 for event in events[:RESTORE_SERVER_LOG_EVENT_LIMIT*LOG_READ_LIMIT]:
  text=event["message"].lower()
  if "password authentication failed" in text or "pam authentication failed" in text:return "persistence-restore-server-log-authentication-rejected"
  if "no pg_hba.conf entry" in text:return "persistence-restore-server-log-client-authentication-policy-rejected"
  if "role " in text and " does not exist" in text:return "persistence-restore-server-log-role-state-invalid"
 return "persistence-restore-server-log-no-classified-event"

def collect_log_group(m, group, start, end):
 """Read one allowlisted group and reduce it to bounded diagnostic facts."""
 events=[]; token=None; observation="incomplete"
 for attempt in range(1,LOG_READ_LIMIT+1):
  args=("--next-token",token) if token else ()
  ok,value,code=m.aws("logs","filter-log-events","--log-group-name",group,"--start-time",str(start),"--end-time",str(end),"--limit",str(RESTORE_SERVER_LOG_EVENT_LIMIT),"--no-paginate",*args)
  if not ok:
   unavailable=code=="aws-resource-missing"
   return {"classification":"persistence-restore-server-log-export-unavailable" if unavailable else "persistence-restore-server-log-observation-unavailable","status":"unavailable" if unavailable else "failed","observation":"unavailable" if unavailable else "failed","attempts":attempt}
  page=value.get("events") if isinstance(value,dict) else None
  if not isinstance(page,list) or len(page)>RESTORE_SERVER_LOG_EVENT_LIMIT or any(not isinstance(event,dict) or not isinstance(event.get("message"),str) or len(event["message"])>65536 for event in page):return {"classification":"persistence-restore-server-log-observation-invalid","status":"collected","observation":"malformed","attempts":attempt}
  events.extend(page)
  next_token=value.get("nextToken")
  if next_token is not None and (not isinstance(next_token,str) or not next_token):return {"classification":"persistence-restore-server-log-observation-invalid","status":"collected","observation":"malformed","attempts":attempt}
  if not next_token:
   observation="incomplete" if len(page)>=RESTORE_SERVER_LOG_EVENT_LIMIT else "complete"
   break
  if next_token==token:break
  token=next_token
 classification=classify_restored_postgresql_log_events(events)
 if observation=="complete":observation="empty" if not events else "unrecognized" if classification.endswith("no-classified-event") else "complete"
 return {"classification":classification,"status":"collected","observation":observation,"attempts":attempt}

def collect_server_logs(m, restored_database, task):
 groups=restored_log_groups(restored_database)
 started=parsed_time(task.get("startedAt")) if isinstance(task,dict) else None
 stopped=parsed_time(task.get("stoppedAt")) if isinstance(task,dict) else None
 if not groups or started is None or stopped is None or stopped<started:return {"classification":"persistence-restore-server-log-time-invalid","status":"failed","observation":"malformed","attempts":1}
 start=int((started-timedelta(seconds=RESTORE_SERVER_LOG_LOOKBACK_SECONDS)).timestamp()*1000)
 end=int((stopped+timedelta(seconds=RESTORE_SERVER_LOG_TAIL_SECONDS)).timestamp()*1000)
 observations=[collect_log_group(m,group,start,end) for group in groups]
 for value in observations:
  if value["status"]!="collected":return value
 classifications=[value["classification"] for value in observations]
 known=[value for value in classifications if value not in {"persistence-restore-server-log-empty","persistence-restore-server-log-no-classified-event"}]
 classification=known[0] if known else "persistence-restore-server-log-empty" if all(value=="persistence-restore-server-log-empty" for value in classifications) else "persistence-restore-server-log-no-classified-event"
 values=[value["observation"] for value in observations]
 observation="malformed" if "malformed" in values else "incomplete" if "incomplete" in values else "unrecognized" if "unrecognized" in values else "empty" if all(value=="empty" for value in values) else "complete"
 # The tail window is still open; export completion cannot be claimed yet.
 if stopped+timedelta(seconds=RESTORE_SERVER_LOG_TAIL_SECONDS)>datetime.now(timezone.utc) and observation=="complete":observation="incomplete"
 return {"classification":classification,"status":"collected","observation":observation,"attempts":max(value["attempts"] for value in observations)}

def collect_restored_postgresql_log_classification(m, restored_database, task):
 value=collect_server_logs(m,restored_database,task); return value["classification"],value["status"]

def persist_observation(module, report):
 encoded=json.dumps(report,sort_keys=True,separators=(",",":")); digest=hashlib.sha256(encoded.encode()).hexdigest()[:24]
 path=OPERATION_DIAGNOSTICS/f"{report['operation_id']}-{digest}.json"
 try:module.write_report(path,report,exclusive=True)
 except FileExistsError:
  if json.loads(path.read_text(encoding="utf-8"))!=report:raise ValueError("diagnostic-observation-collision")
 return path

def diagnostic_completion_path(operation):
 return OPERATION_DIAGNOSTICS/f"{operation}-completion.json"

def persist_diagnostic_completion(operation, restored_database, task):
 """Retain a terminal, allowlisted completion fact for cleanup reconciliation.

 This is deliberately not acceptance evidence: it only establishes that the
 owned one-shot diagnostic finished successfully, so a later ECS retention
 expiry cannot make cleanup permanently impossible.
 """
 containers=task.get("containers") if isinstance(task,dict) else None
 container=containers[0] if isinstance(containers,list) and len(containers)==1 and isinstance(containers[0],dict) else None
 task_arn=task.get("taskArn") if isinstance(task,dict) else None
 digest=container.get("imageDigest") if isinstance(container,dict) else None
 if not isinstance(operation,str) or not re.fullmatch(r"kanbien-connect-[a-f0-9]{16}",operation) or restore_id_from_database(restored_database)!=restored_database or not isinstance(task_arn,str) or re.fullmatch(rf"arn:aws:ecs:{re.escape(REGION)}:[0-9]{{12}}:task/{re.escape(CLUSTER)}/[a-f0-9]{{32}}",task_arn) is None or not isinstance(digest,str) or re.fullmatch(r"sha256:[a-f0-9]{64}",digest) is None:
  raise ValueError("diagnostic-completion-input-invalid")
 value={"schema":DIAGNOSTIC_COMPLETION_SCHEMA,"target":"kanbien-core-platform","scope":"core-server-persistence","operation_id":operation,"resource_logical_id":restored_database,"task_id":task_arn.rsplit("/",1)[-1],"artifact_identity":digest,"result_code":DIAGNOSTIC_RESULT}
 path=diagnostic_completion_path(operation)
 encoded=json.dumps(value,sort_keys=True,separators=(",",":"))
 if path.exists():
  if path.is_symlink() or path.stat().st_size>65536 or path.read_text(encoding="utf-8")!=encoded:raise ValueError("diagnostic-completion-conflict")
  return path
 path.parent.mkdir(parents=True,exist_ok=True)
 temporary=path.with_name("."+path.name+".pending")
 try:
  temporary.write_text(encoded,encoding="utf-8")
  temporary.replace(path)
 finally:temporary.unlink(missing_ok=True)
 return path

def diagnostic_completion_resolves(operation, restored_database):
 """Read only retained, closed facts; launch reservations never resolve themselves."""
 if not isinstance(operation,str) or restore_id_from_database(restored_database)!=restored_database:return False
 completion=diagnostic_completion_path(operation)
 try:
  if completion.is_file() and not completion.is_symlink() and completion.stat().st_size<=65536:
   value=json.loads(completion.read_text(encoding="utf-8"))
   if isinstance(value,dict) and set(value)=={"schema","target","scope","operation_id","resource_logical_id","task_id","artifact_identity","result_code"} and value.get("schema")==DIAGNOSTIC_COMPLETION_SCHEMA and value.get("target")=="kanbien-core-platform" and value.get("scope")=="core-server-persistence" and value.get("operation_id")==operation and value.get("resource_logical_id")==restored_database and value.get("result_code")==DIAGNOSTIC_RESULT and isinstance(value.get("task_id"),str) and re.fullmatch(r"[a-f0-9]{32}",value["task_id"]) and isinstance(value.get("artifact_identity"),str) and re.fullmatch(r"sha256:[a-f0-9]{64}",value["artifact_identity"]):return True
  # Older completed diagnostics predate the compact completion receipt. Their
  # already-validated terminal diagnostic reports are equivalent evidence;
  # an unknown launch reservation remains explicitly unresolved.
  for path in OPERATION_DIAGNOSTICS.glob(f"{operation}-*.json"):
   if path.name in {f"{operation}-launch.json",f"{operation}-completion.json"} or path.is_symlink() or path.stat().st_size>65536:continue
   report=diagnostics().validate(json.loads(path.read_text(encoding="utf-8")))
   if report.get("target")=="kanbien-core-platform" and report.get("scope")=="core-server-persistence" and report.get("operation_id")==operation and report.get("operation_outcome") in {"failed","rejected"} and report.get("facts",{}).get("resource_logical_id")==restored_database and report.get("evidence",{}).get("reference","").startswith(f"provider-operation:{operation}/"):return True
 except Exception:return False
 return False

def retain_verifier_rejection(m, operation, result, restored_database, task, execution=None, task_observation=None):
 """Report collection independently; never erase the safe operation failure."""
 if result not in RESTORE_REJECTED_RESULTS|{"persistence-restoration-verifier-completion-invalid"}:return ("persistence-diagnostic-original-result-invalid",)
 try:
  module=diagnostics()
  try:observation=collect_server_logs(m,restored_database,task)
  except Exception:observation={"classification":"persistence-restore-server-log-collection-failed","status":"failed","observation":"failed","attempts":1}
  containers=task.get("containers",[]); container=containers[0] if isinstance(containers,list) and len(containers)==1 and isinstance(containers[0],dict) else {}
  exit_status=container.get("exitCode"); exit_status=exit_status if type(exit_status) is int and 1<=exit_status<=255 else 1
  facts={"resource_logical_id":restored_database}
  artifact=container.get("imageDigest")
  if isinstance(artifact,str) and re.fullmatch(r"sha256:[a-f0-9]{64}",artifact):facts["artifact_identity"]=artifact
  task_id=task.get("taskArn","").rsplit("/",1)[-1] if isinstance(task.get("taskArn"),str) else ""
  evidence_reference=f"provider-operation:{operation}"+(f"/{task_id}" if re.fullmatch(r"[a-f0-9]{32}",task_id) else "")
  report=module.build_report(target="kanbien-core-platform",scope="core-server-persistence",operation_id=operation,stage="run",original_code=result,exit_status=exit_status,outcome="failed",classification=observation["classification"],evidence_reference=evidence_reference,next_decision="inspect-retained-evidence",collection_status=observation["status"],collection_observation=observation["observation"],collection_attempts=observation["attempts"],execution=execution,facts=facts,task_observation=("complete" if task_observation["status"] in {"accepted","rejected","diagnosed","diagnostic-failed"} else task_observation["status"]) if task_observation else None,task_attempts=task_observation["attempts"] if task_observation else None)
  persist_observation(module,report)
  findings=[]
  if observation["status"]!="collected":findings.append("persistence-diagnostic-collection-"+observation["status"])
  if task_observation and task_observation["status"] in {"failed","unavailable"}:findings.append("persistence-verifier-log-collection-"+task_observation["status"])
  return tuple(findings)
 except Exception:return ("persistence-diagnostic-report-write-failed",)

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
 exports=restored.get("EnabledCloudwatchLogsExports")
 return restored.get("DBInstanceStatus")=="available" and restored.get("PubliclyAccessible") is False and restored.get("StorageEncrypted") is True and restored.get("IAMDatabaseAuthenticationEnabled") is True and restored.get("Engine")=="postgres" and attached==[group] and isinstance(a,str) and a==b and isinstance(exports,list) and set(exports)=={"postgresql","iam-db-auth-error"}
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
  # IAM database authentication is not retained by an RDS snapshot restore.
  # It is required for the deliberately credential-free restoration verifier,
  # so establish it as part of the isolated copy's initial posture.
  ok,_,c=m.aws("rds","restore-db-instance-from-db-snapshot","--db-instance-identifier",rid,"--db-snapshot-identifier",sid,"--db-instance-class",cls,"--db-subnet-group-name",subnet,"--vpc-security-group-ids",ctl["PersistenceRestoredDatabaseSecurityGroupId"],"--no-publicly-accessible","--no-multi-az","--enable-iam-database-authentication","--enable-cloudwatch-logs-exports","postgresql","iam-db-auth-error","--copy-tags-to-snapshot","--tags",*[f"Key={key},Value={value}" for key,value in tags.items()])
  return emit("pending" if ok else "uncertain","persistence-restore-submitted-awaiting-provider-observation" if ok else c,facts=facts)
 bound=existing_restore_binding(value,rid,tags)
 if bound!="ok":return emit("uncertain" if bound.endswith("unproven") else "blocked",bound,facts=facts)
 if value.get("DBInstanceStatus") in {"creating","backing-up","modifying","rebooting","configuring-enhanced-monitoring","configuring-log-exports"}:return emit("pending","persistence-restore-still-provisioning",facts=facts)
 if value.get("DBInstanceStatus") in {"failed","incompatible-restore","inaccessible-encryption-credentials","storage-full"}:return emit("failed","persistence-restore-provider-failed",facts=facts)
 if value.get("DBInstanceStatus")!="available":return emit("uncertain","persistence-restore-provider-status-unknown",facts=facts)
 if value.get("IAMDatabaseAuthenticationEnabled") is not True:
  # Reconcile an older in-flight restore created before the initial posture
  # control existed. This changes only the disposable restored instance.
  if observe_only:return emit("uncertain","persistence-restored-database-iam-authentication-not-observed",facts=facts)
  ok,_,c=m.aws("rds","modify-db-instance","--db-instance-identifier",rid,"--enable-iam-database-authentication","--apply-immediately")
  return emit("pending" if ok else "uncertain","persistence-restored-database-iam-authentication-submitted" if ok else c,facts=facts)
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
 return c.get("name")=="persistence-restoration-verifier" and c.get("command")==["artifacts/kanbien-core-server-persistence-restore-verifier.main.js"] and not secrets and "PERSISTENCE_POSTGRES_HOST" not in env and "PERSISTENCE_RESTORE_DIAGNOSTIC_MODE" not in env and all(env.get(key)==value for key,value in required.items()) and isinstance(env.get("PERSISTENCE_POSTGRES_IAM_REGION"),str)

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

def remove_temporary_restore_identity_policy(m, controls, observe_only=False, restored=None):
 role=controls.get("PersistenceRestorationVerifierTaskRoleName") if isinstance(controls,dict) else None
 if not isinstance(role,str) or not role:return "persistence-restoration-identity-binding-unavailable"
 name="kanbien-core-platform-restoration-verifier-current-instance";ok,value,code=m.aws("iam","get-role-policy","--role-name",role,"--policy-name",name)
 if not ok:return "ok" if code=="aws-resource-missing" else code
 resource=restore_identity_resource(restored)
 expected={"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"rds-db:connect","Resource":resource}]}
 if resource is None or not isinstance(value,dict) or value.get("PolicyDocument")!=expected:return "persistence-restoration-temporary-identity-policy-mismatch"
 if observe_only:return "persistence-restoration-temporary-identity-policy-removal-not-observed"
 ok,_,code=m.aws("iam","delete-role-policy","--role-name",role,"--policy-name",name)
 return "persistence-restoration-temporary-identity-policy-removal-submitted" if ok else code
def temporary_restore_identity_policy_stable(m, controls):
 """Require the exact policy mutation to age before the one verifier launch."""
 role=controls.get("PersistenceRestorationVerifierTaskRoleName") if isinstance(controls,dict) else None
 name="kanbien-core-platform-restoration-verifier-current-instance"
 if not isinstance(role,str) or not role:return False
 ok,value,_=m.aws_in_region(IAM_CLOUDTRAIL_REGION,"cloudtrail","lookup-events","--lookup-attributes","AttributeKey=EventName,AttributeValue=PutRolePolicy","--max-results","50")
 events=value.get("Events") if ok and isinstance(value,dict) else None
 if not isinstance(events,list):return False
 cutoff=datetime.now(timezone.utc)-timedelta(seconds=RESTORATION_IDENTITY_STABILIZATION_SECONDS)
 for event in events:
  raw=event.get("CloudTrailEvent") if isinstance(event,dict) else None; observed=parsed_time(event.get("EventTime")) if isinstance(event,dict) else None
  try:
   decoded=json.loads(raw) if isinstance(raw,str) else None
   request=decoded.get("requestParameters") if isinstance(decoded,dict) else None
  except (json.JSONDecodeError,TypeError):request=None
  if isinstance(request,dict) and request.get("roleName")==role and request.get("policyName")==name and observed is not None and observed<=cutoff:return True
 return False

def temporary_restore_identity_policy_effective(m, controls, restored):
 """Require IAM's decision for the exact task role and restored DB identity.

 A retained policy and its CloudTrail observation only establish that a policy
 mutation happened.  Before a controller starts the one governed verifier or
 diagnostic task, it must also establish that IAM allows *this* role to use
 rds-db:connect against *this* restored database user resource.
 """
 resource=restore_identity_resource(restored); role=controls.get("PersistenceRestorationVerifierTaskRoleName") if isinstance(controls,dict) else None
 if not isinstance(resource,str) or not isinstance(role,str) or not role:return "persistence-restoration-identity-binding-unavailable"
 ok,value,code=m.aws("iam","get-role","--role-name",role)
 actual=value.get("Role") if ok and isinstance(value,dict) else None; arn=actual.get("Arn") if isinstance(actual,dict) else None
 if not isinstance(arn,str) or not re.fullmatch(r"arn:aws:iam::[0-9]{12}:role/"+re.escape(role),arn):return "persistence-restoration-temporary-identity-role-unavailable" if ok else code
 ok,value,code=m.aws("iam","simulate-principal-policy","--policy-source-arn",arn,"--action-names","rds-db:connect","--resource-arns",resource)
 results=value.get("EvaluationResults") if ok and isinstance(value,dict) else None
 if not ok:return code
 if not isinstance(results,list) or len(results)!=1 or not isinstance(results[0],dict):return "persistence-restoration-temporary-identity-simulation-invalid"
 result=results[0]
 return "ok" if result.get("EvalActionName")=="rds-db:connect" and result.get("EvalResourceName")==resource and result.get("EvalDecision")=="allowed" else "persistence-restoration-temporary-identity-not-authorized"
def task_image_digest(m,arn):
 ok,d,_=m.aws("ecs","describe-task-definition","--task-definition",arn); t=d.get("taskDefinition") if ok and isinstance(d,dict) else None; cs=t.get("containerDefinitions") if isinstance(t,dict) else None; c=cs[0] if isinstance(cs,list) and len(cs)==1 and isinstance(cs[0],dict) else None; image=c.get("image") if isinstance(c,dict) else None
 return image.rsplit("@",1)[1] if isinstance(image,str) and image.count("@")==1 and image.rsplit("@",1)[1].startswith("sha256:") else None
def task_duration(task):
 try:
  a=datetime.fromisoformat(task["startedAt"].replace("Z","+00:00")); b=datetime.fromisoformat(task["stoppedAt"].replace("Z","+00:00")); return int((b-a).total_seconds()) if b>=a else None
 except (KeyError,ValueError,TypeError,OverflowError):return None
def observe_terminal_result(m,arn,diagnostic=False):
 """At most three read-only log pages/observations; never replay a task."""
 tid=arn.rsplit("/",1)[-1]; token=None; results=[]; malformed=False; unrecognized=False
 try:contract=diagnostics()
 except Exception:return {"status":"failed","result":None,"execution":None,"attempts":1}
 def finish(status,attempt):
  failures=[result for result in results if result["verdict"] in {"rejected","diagnostic-failed"}]
  codes={result["code"] for result in failures}
  retained=failures[0] if len(codes)==1 else results[0] if len(results)==1 and status in {"accepted","diagnosed"} else None
  execution=retained.get("execution") if retained and all(value.get("execution")==retained.get("execution") for value in failures) else None
  return {"status":status,"result":retained["code"] if retained else None,"execution":execution,"attempts":attempt}
 for attempt in range(1,LOG_READ_LIMIT+1):
  args=("--next-token",token) if token else ()
  ok,value,code=m.aws("logs","get-log-events","--log-group-name",LOG_GROUP,"--log-stream-name",f"persistence-restoration-verifier/persistence-restoration-verifier/{tid}","--start-from-head","--limit",str(RESTORE_SERVER_LOG_EVENT_LIMIT),*args)
  if not ok:return finish("unavailable" if code=="aws-resource-missing" else "failed",attempt)
  events=value.get("events") if isinstance(value,dict) else None
  if not isinstance(events,list) or len(events)>RESTORE_SERVER_LOG_EVENT_LIMIT:return finish("malformed",attempt)
  for event in events:
   try:
    message=event.get("message") if isinstance(event,dict) else None
    if not isinstance(message,str) or len(message)>65536:raise ValueError()
    result=contract.validate_verifier_result(json.loads(message))
   except Exception:
    malformed=True; continue
   verdict,code=result["verdict"],result["code"]
   if (not diagnostic and ((verdict=="accepted" and code==RESTORE_ACCEPTED_RESULT) or (verdict=="rejected" and code in RESTORE_REJECTED_RESULTS))) or (diagnostic and ((verdict=="diagnosed" and code==DIAGNOSTIC_RESULT) or (verdict=="diagnostic-failed" and code in RESTORE_REJECTED_RESULTS))):results.append(result)
   else:unrecognized=True
  next_token=value.get("nextForwardToken")
  if next_token is not None and (not isinstance(next_token,str) or not next_token):malformed=True
  complete=(next_token is None or next_token==token) and len(events)<RESTORE_SERVER_LOG_EVENT_LIMIT
  if complete and (token is not None or events or results or malformed or unrecognized):break
  if next_token is None and len(events)>=RESTORE_SERVER_LOG_EVENT_LIMIT:break
  if next_token is not None:token=next_token
 else:
  complete=not token
 status="malformed" if malformed else "unrecognized" if unrecognized else "incomplete" if not complete else "empty" if not results else "incomplete" if len(results)!=1 else results[0]["verdict"]
 return finish(status,attempt)

def terminal_result(m,arn):
 observation=observe_terminal_result(m,arn); return observation["status"],observation["result"]

def verifier_tasks(m,operation,definition):
 arns = []
 family = definition.rsplit("/", 1)[-1].split(":", 1)[0]
 for state in ("RUNNING", "STOPPED"):
     # AWS forbids combining startedBy with another ListTasks filter.
     ok, listed, code = m.aws("ecs", "list-tasks", "--cluster", CLUSTER, "--family", family, "--max-results", "100", "--no-paginate", "--desired-status", state)
     values = listed.get("taskArns") if ok and isinstance(listed, dict) else None
     if not isinstance(values, list) or len(values)>100 or listed.get("nextToken") or not all(isinstance(value, str) for value in values):
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
     matching.extend(task["taskArn"] for task in tasks if operation is None or task.get("startedBy") == operation)
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
 if status in {"creating","backing-up","modifying","rebooting","configuring-enhanced-monitoring","configuring-log-exports"}:return emit("pending","persistence-restore-still-provisioning",facts={"snapshot":sid,"restored_database":rid})
 if status in {"failed","incompatible-restore","inaccessible-encryption-credentials","storage-full"}:return emit("failed","persistence-restore-provider-failed",facts={"snapshot":sid,"restored_database":rid})
 if status!="available":return emit("uncertain","persistence-restore-provider-status-unknown",facts={"snapshot":sid,"restored_database":rid})
 if not correct(restored,src,ctl["PersistenceRestoredDatabaseSecurityGroupId"]):return emit("blocked","persistence-restored-database-posture-invalid")
 endpoint=restored.get("Endpoint",{}).get("Address") if isinstance(restored.get("Endpoint"),dict) else None; td=ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"]
 if not isinstance(endpoint,str) or not task_def_valid(m,td):return emit("blocked","persistence-restoration-verifier-definition-invalid")
 diagnostic_operation=diagnostic_run_identity(restored)
 diagnostic_tasks,diagnostic_code=verifier_tasks(m,diagnostic_operation,td)
 if diagnostic_tasks is None:return emit("uncertain",diagnostic_code)
 if not tasks_stopped(m,diagnostic_tasks) or (not diagnostic_tasks and diagnostic_operation is not None and (OPERATION_DIAGNOSTICS/f"{diagnostic_operation}-launch.json").exists()):return emit("pending","persistence-restoration-connection-diagnostic-reconciliation-required")
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
  observation=observe_terminal_result(m,arn); evidence,result=observation["status"],observation["result"]
  facts={**facts,"log_observation":evidence,"log_read_attempts":observation["attempts"]}
  if exit_code!=0:
   original=result if result in RESTORE_REJECTED_RESULTS else "persistence-restoration-verifier-completion-invalid"
   collection=retain_verifier_rejection(m,started,original,rid,t,observation["execution"],observation)
   return emit("failed",original,*collection,*(("persistence-restoration-verifier-deadline-exceeded",) if duration>DEADLINE else ()),facts={**facts,**({"safe_result_code":result} if result is not None else {})})
  if duration>DEADLINE:return emit("failed","persistence-restoration-verifier-completion-invalid",facts=facts)
  # CloudWatch delivery can lag a stopped task.  A clean exit without the
  # closed acceptance envelope is therefore pending evidence, not proof; the
  # reconciler will never manufacture a receipt from it.
  if evidence!="accepted":return emit("pending","persistence-restoration-verifier-log-"+evidence,facts=facts)
  digest=task_image_digest(m,td)
  if digest is None:return emit("blocked","persistence-restoration-verifier-receipt-identity-unavailable")
  try:
   receipt=proof_receipts().make(proof_type="restore",operation="isolated-restore",task=t,image_digest=digest,result_code="KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED",context={"snapshot":sid,"restored_database":rid,"completion_deadline_seconds":DEADLINE,"completion_duration_seconds":duration},controller="rehearse-isolated-database-restore",collected_at=datetime.now().astimezone().isoformat().replace("+00:00","Z"));path=proof_receipts().persist(receipt)
  except Exception:return emit("blocked","persistence-restoration-verifier-receipt-persistence-failed")
  return emit("accepted","persistence-isolated-restoration-record-retrieved",facts={**facts,"verifier_task":arn.rsplit("/",1)[-1],"completion_duration_seconds":duration,"proof_receipt":str(path.relative_to(ROOT))})
 if observe_only:return emit("uncertain","persistence-restoration-verifier-operation-not-observed",facts={"snapshot":sid,"restored_database":rid,"operation_id":started})
 # A policy can be visible to IAM before it is usable by RDS IAM database
 # authentication.  Do not turn the resulting first connection into a
 # misleading retryable verifier failure.  Re-observe the exact policy after
 # one bounded stabilization interval, then launch at most one task for this
 # restored database incarnation.
 if not temporary_restore_identity_policy_stable(m,ctl):return emit("pending","persistence-restoration-temporary-identity-policy-stabilizing",facts={"snapshot":sid,"restored_database":rid,"operation_id":started})
 identity_status,identity_reference=temporary_restore_identity_policy(m,ctl,restored,True)
 if identity_status!="ok" or identity_reference!=restore_identity_resource(restored):return emit("uncertain","persistence-restoration-temporary-identity-policy-not-stable",facts={"snapshot":sid,"restored_database":rid,"operation_id":started})
 effective=temporary_restore_identity_policy_effective(m,ctl,restored)
 if effective!="ok":return emit("blocked","persistence-restoration-temporary-identity-not-effective" if effective=="persistence-restoration-temporary-identity-not-authorized" else effective,facts={"snapshot":sid,"restored_database":rid,"operation_id":started})
 net=f"awsvpcConfiguration={{subnets=[{ctl['PrivateSubnetIds']}],securityGroups=[{ctl['PersistenceRestorationVerifierSecurityGroupId']}],assignPublicIp=DISABLED}}"; overrides=json.dumps({"containerOverrides":[{"name":"persistence-restoration-verifier","environment":[{"name":"PERSISTENCE_POSTGRES_HOST","value":endpoint},{"name":"PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE","value":identity_reference},{"name":"PERSISTENCE_ACCEPTANCE_RECORD_ID","value":RECORD_ID},{"name":"PERSISTENCE_ACCEPTANCE_FACT_DIGEST","value":FACT_DIGEST}]}]})
 ok,_,c=m.aws("ecs","run-task","--cluster",CLUSTER,"--task-definition",td,"--launch-type","FARGATE","--count","1","--started-by",started,"--client-token",started,"--network-configuration",net,"--overrides",overrides)
 return emit("pending" if ok else "uncertain","persistence-restoration-verifier-submitted-awaiting-provider-observation" if ok else c,facts={"snapshot":sid,"restored_database":rid,"operation_id":started})
def emit_diagnostic(verdict,*codes,facts=None):
 value={"schema":"deploy/persistence-connection-diagnostic-report/v1","target":"kanbien-core-platform","scope":"core-server-persistence","verdict":verdict,"acceptance_evidence":False,"findings":[{"code":code} for code in codes]}
 if facts:value["facts"]=facts
 print(json.dumps(value,sort_keys=True)); return 0 if verdict=="diagnosed" else 1

def diagnostic_run_identity(restored):
 resource=restored.get("DbiResourceId") if isinstance(restored,dict) else None
 return "kanbien-connect-"+hashlib.sha256(resource.encode()).hexdigest()[:16] if isinstance(resource,str) and resource else None

def tasks_stopped(m, arns):
 if not arns:return True
 ok,value,_=m.aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",*arns)
 tasks=value.get("tasks") if ok and isinstance(value,dict) else None
 return isinstance(tasks,list) and len(tasks)==len(arns) and not value.get("failures") and all(isinstance(task,dict) and isinstance(task.get("taskArn"),str) and task.get("lastStatus")=="STOPPED" for task in tasks) and {task.get("taskArn") for task in tasks}==set(arns)

def diagnose_connection(m,sid,rid,observe_only=False,record_proof_path=None):
 """One separately bound diagnostic launch per owned restored incarnation."""
 proof,code=read_record_proof(record_proof_path)
 if proof is None:return emit_diagnostic("blocked",code)
 src,code=source(m); ctl,cc=controls(m); restored,rc=db(m,rid); point,pc=snapshot(m,sid)
 if src is None:return emit_diagnostic("blocked",code)
 if ctl is None:return emit_diagnostic("blocked",cc)
 if restored is None:return emit_diagnostic("blocked",rc)
 if point is None:return emit_diagnostic("blocked",pc)
 binding,code=recovery_point_binding(src,point,sid,rid,proof)
 if binding is None:return emit_diagnostic("blocked",code)
 tags,_=binding; bound=existing_restore_binding(restored,rid,tags)
 if bound!="ok":return emit_diagnostic("blocked",bound)
 if not correct(restored,src,ctl["PersistenceRestoredDatabaseSecurityGroupId"]):return emit_diagnostic("blocked","persistence-connection-diagnostic-target-posture-invalid")
 operation=diagnostic_run_identity(restored); definition=ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"]
 endpoint=restored.get("Endpoint",{}).get("Address") if isinstance(restored.get("Endpoint"),dict) else None
 identity=restore_identity_resource(restored)
 if operation is None or not isinstance(endpoint,str) or identity is None or not task_def_valid(m,definition):return emit_diagnostic("blocked","persistence-connection-diagnostic-identity-invalid")
 facts={"operation_id":operation,"snapshot":sid,"restored_database":rid,"maximum_attempts":1,"deadline_seconds":DEADLINE}
 reservation=OPERATION_DIAGNOSTICS/f"{operation}-launch.json"
 arns,code=verifier_tasks(m,operation,definition)
 if arns is None:return emit_diagnostic("uncertain",code,facts=facts)
 expected_env={"PERSISTENCE_POSTGRES_HOST":endpoint,"PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE":identity,"PERSISTENCE_RESTORE_DIAGNOSTIC_MODE":"connection"}
 if arns:
  if len(arns)!=1:return emit_diagnostic("uncertain","persistence-connection-diagnostic-task-ambiguous",facts=facts)
  ok,value,code=m.aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",*arns)
  tasks=value.get("tasks") if ok and isinstance(value,dict) else None
  if not isinstance(tasks,list) or len(tasks)!=1 or not isinstance(tasks[0],dict) or value.get("failures"):return emit_diagnostic("uncertain","persistence-connection-diagnostic-observation-unavailable",facts=facts)
  task=tasks[0]
  if task.get("taskArn")!=arns[0] or task.get("startedBy")!=operation or task.get("taskDefinitionArn")!=definition or not task_evidence().task_overrides_match(task,"persistence-restoration-verifier",expected_env):return emit_diagnostic("blocked","persistence-connection-diagnostic-task-binding-invalid",facts=facts)
  try:
   reserved=diagnostics().validate(json.loads(reservation.read_text(encoding="utf-8")))
   expected_artifact=reserved.get("facts",{}).get("artifact_identity")
   containers=task.get("containers")
   actual_artifact=containers[0].get("imageDigest") if isinstance(containers,list) and len(containers)==1 and isinstance(containers[0],dict) else None
   if reserved.get("operation_id")!=operation or reserved.get("target")!="kanbien-core-platform" or reserved.get("scope")!="core-server-persistence" or reserved.get("classification",{}).get("code")!="persistence-connection-diagnostic-launch-reserved" or not isinstance(expected_artifact,str):raise ValueError()
   if task.get("lastStatus")=="STOPPED" and actual_artifact!=expected_artifact:raise ValueError()
  except Exception:return emit_diagnostic("uncertain","persistence-connection-diagnostic-reservation-binding-unproven",facts=facts)
  facts["task_id"]=arns[0].rsplit("/",1)[-1]
  status=task.get("lastStatus")
  if status!="STOPPED":
   if status not in {"PROVISIONING","PENDING","ACTIVATING","RUNNING","DEACTIVATING","STOPPING","DEPROVISIONING"}:return emit_diagnostic("uncertain","persistence-connection-diagnostic-status-unknown",facts=facts)
   created=parsed_time(task.get("createdAt")) or parsed_time(task.get("startedAt"))
   if created is None:return emit_diagnostic("uncertain","persistence-connection-diagnostic-time-unavailable",facts=facts)
   if (datetime.now(timezone.utc)-created).total_seconds()>DEADLINE:
    if observe_only:return emit_diagnostic("pending","persistence-connection-diagnostic-deadline-stop-required",facts=facts)
    ok,_,_=m.aws("ecs","stop-task","--cluster",CLUSTER,"--task",arns[0],"--reason","connection-diagnostic-deadline")
    return emit_diagnostic("pending" if ok else "uncertain","persistence-connection-diagnostic-stop-submitted" if ok else "persistence-connection-diagnostic-stop-uncertain",facts=facts)
   return emit_diagnostic("pending","persistence-connection-diagnostic-running",facts=facts)
  duration=task_duration(task); containers=task.get("containers")
  exit_status=containers[0].get("exitCode") if isinstance(containers,list) and len(containers)==1 and isinstance(containers[0],dict) else None
  if duration is None or type(exit_status) is not int:return emit_diagnostic("uncertain","persistence-connection-diagnostic-completion-unavailable",facts=facts)
  observation=observe_terminal_result(m,arns[0],True)
  facts.update(log_observation=observation["status"],log_read_attempts=observation["attempts"])
  if observation["execution"] is not None:facts["execution"]=observation["execution"]
  extra=()
  if exit_status!=0:
   original=observation["result"] or "persistence-restoration-verifier-completion-invalid"
   extra=retain_verifier_rejection(m,operation,original,rid,task,observation["execution"],observation)
  # This role is used only by completed verifier tasks. Never revoke while
  # another invocation is running or its state cannot be established.
  recovery_tasks,code=verifier_tasks(m,restore_run_identity(restored),definition)
  if recovery_tasks is None or not tasks_stopped(m,recovery_tasks):return emit_diagnostic("pending","persistence-connection-diagnostic-cleanup-task-state-unproven",facts=facts)
  cleanup=remove_temporary_restore_identity_policy(m,ctl,observe_only,restored)
  if cleanup!="ok":return emit_diagnostic("blocked" if cleanup.endswith("mismatch") else "pending",cleanup,*extra,facts=facts)
  if exit_status!=0:return emit_diagnostic("failed",observation["result"] or "persistence-connection-diagnostic-task-failed",*extra,facts=facts)
  if duration>DEADLINE:return emit_diagnostic("failed","persistence-connection-diagnostic-deadline-exceeded",facts=facts)
  if observation["status"]!="diagnosed":return emit_diagnostic("pending","persistence-connection-diagnostic-log-"+observation["status"],facts=facts)
  try:persist_diagnostic_completion(operation,rid,task)
  except Exception:return emit_diagnostic("blocked","persistence-connection-diagnostic-completion-receipt-write-failed",facts=facts)
  return emit_diagnostic("diagnosed",DIAGNOSTIC_RESULT,facts=facts)
 reservation=OPERATION_DIAGNOSTICS/f"{operation}-launch.json"
 if reservation.exists():return emit_diagnostic("uncertain","persistence-connection-diagnostic-reserved-reconcile-only",facts=facts)
 if observe_only:return emit_diagnostic("uncertain","persistence-connection-diagnostic-operation-not-observed",facts=facts)
 recovery_tasks,code=verifier_tasks(m,restore_run_identity(restored),definition)
 if recovery_tasks is None or not tasks_stopped(m,recovery_tasks):return emit_diagnostic("blocked","persistence-connection-diagnostic-recovery-task-not-terminal",facts=facts)
 access,_=temporary_restore_identity_policy(m,ctl,restored,False)
 if access!="ok":return emit_diagnostic("pending" if access.endswith("submitted") else "uncertain" if access.endswith("not-observed") else "blocked",access,facts=facts)
 if not temporary_restore_identity_policy_stable(m,ctl):return emit_diagnostic("pending","persistence-restoration-temporary-identity-policy-stabilizing",facts=facts)
 access,observed_identity=temporary_restore_identity_policy(m,ctl,restored,True)
 if access!="ok" or observed_identity!=identity:return emit_diagnostic("uncertain","persistence-connection-diagnostic-access-unproven",facts=facts)
 effective=temporary_restore_identity_policy_effective(m,ctl,restored)
 if effective!="ok":return emit_diagnostic("blocked","persistence-restoration-temporary-identity-not-effective" if effective=="persistence-restoration-temporary-identity-not-authorized" else effective,facts=facts)
 artifact=task_image_digest(m,definition)
 if not isinstance(artifact,str) or re.fullmatch(r"sha256:[a-f0-9]{64}",artifact) is None:return emit_diagnostic("blocked","persistence-connection-diagnostic-artifact-unavailable",facts=facts)
 try:
  module=diagnostics()
  report=module.build_report(target="kanbien-core-platform",scope="core-server-persistence",operation_id=operation,stage="run",original_code="persistence-connection-diagnostic-not-complete",exit_status=1,outcome="unknown",classification="persistence-connection-diagnostic-launch-reserved",evidence_reference=f"provider-operation:{operation}",next_decision="observe-current-operation",facts={"artifact_identity":artifact,"resource_logical_id":rid})
  module.write_report(reservation,report,exclusive=True)
 except FileExistsError:return emit_diagnostic("uncertain","persistence-connection-diagnostic-reserved-reconcile-only",facts=facts) if reservation.is_file() else emit_diagnostic("blocked","persistence-diagnostic-report-write-failed",facts=facts)
 except Exception:return emit_diagnostic("blocked","persistence-diagnostic-report-write-failed",facts=facts)
 net=f"awsvpcConfiguration={{subnets=[{ctl['PrivateSubnetIds']}],securityGroups=[{ctl['PersistenceRestorationVerifierSecurityGroupId']}],assignPublicIp=DISABLED}}"
 overrides=json.dumps({"containerOverrides":[{"name":"persistence-restoration-verifier","environment":[{"name":key,"value":value} for key,value in expected_env.items()]}]})
 ok,_,_=m.aws("ecs","run-task","--cluster",CLUSTER,"--task-definition",definition,"--launch-type","FARGATE","--count","1","--started-by",operation,"--client-token",operation,"--network-configuration",net,"--overrides",overrides)
 return emit_diagnostic("pending" if ok else "uncertain","persistence-connection-diagnostic-submitted" if ok else "persistence-connection-diagnostic-launch-uncertain",facts=facts)

def absent_database_reservations_resolved(rid, tasks):
 """An absent database does not prove a reserved task launch never happened."""
 if OPERATION_DIAGNOSTICS.exists() and not OPERATION_DIAGNOSTICS.is_dir():return False
 try:
  paths=sorted(OPERATION_DIAGNOSTICS.glob("kanbien-connect-*-launch.json"))
  if len(paths)>100:return False
  for path in paths:
   if path.is_symlink() or path.stat().st_size>65536:return False
   reservation=diagnostics().validate(json.loads(path.read_text(encoding="utf-8")))
   target=reservation.get("facts",{}).get("resource_logical_id")
   if not isinstance(target,str) or restore_id_from_database(target)!=target:return False
   if target!=rid:continue
   operation=reservation.get("operation_id")
   if path.name!=f"{operation}-launch.json" or reservation.get("target")!="kanbien-core-platform" or reservation.get("scope")!="core-server-persistence" or reservation.get("classification",{}).get("code")!="persistence-connection-diagnostic-launch-reserved":return False
   matching=[task for task in tasks if task.get("startedBy")==operation]
   if len(matching)==1 and matching[0].get("lastStatus")=="STOPPED":continue
   if not diagnostic_completion_resolves(operation,rid):return False
  return True
 except Exception:return False

def cleanup(m,sid,rid,observe_only=False):
 """Prove database, verifier-family and temporary authority cleanup separately."""
 facts={"snapshot":sid,"restored_database":rid}
 if not m.live_budget()[0]:return emit("blocked","target-budget-live-configuration-invalid")
 restored,code=db(m,rid)
 if restored is None and code!="aws-resource-missing":return emit("uncertain",code,facts=facts)
 ctl,code=controls(m)
 if ctl is None:return emit("uncertain",code,facts=facts)
 definition=ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"]
 if restored is not None:
  attached=[item.get("VpcSecurityGroupId") for item in restored.get("VpcSecurityGroups",[]) if isinstance(item,dict)]
  if attached!=[ctl["PersistenceRestoredDatabaseSecurityGroupId"]] or restored.get("PubliclyAccessible") is not False:return emit("blocked","persistence-restored-database-cleanup-target-invalid")
  started=restore_run_identity(restored)
  if started is None:return emit("blocked","persistence-restored-database-identity-unavailable")
 else:started=None
 tasks,code=verifier_tasks(m,started,definition)
 if tasks is None:return emit("uncertain",code,facts=facts)
 if restored is not None:
  operation=diagnostic_run_identity(restored)
  diagnostic_tasks,code=verifier_tasks(m,operation,definition)
  if diagnostic_tasks is None:return emit("uncertain",code,facts=facts)
  if not diagnostic_tasks and (OPERATION_DIAGNOSTICS/f"{operation}-launch.json").exists():return emit("uncertain","persistence-connection-diagnostic-reserved-reconcile-only",facts=facts)
  tasks=list(dict.fromkeys(tasks+diagnostic_tasks))
 listed=[]
 if tasks:
  ok,response,code=m.aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",*tasks)
  listed=response.get("tasks") if ok and isinstance(response,dict) else None
  if not isinstance(listed,list) or len(listed)!=len(tasks) or response.get("failures") or not all(isinstance(task,dict) and isinstance(task.get("taskArn"),str) for task in listed) or {task["taskArn"] for task in listed}!=set(tasks):return emit("uncertain","persistence-restore-cleanup-task-state-uncertain",facts=facts)
  states={"PROVISIONING","PENDING","ACTIVATING","RUNNING","DEACTIVATING","STOPPING","DEPROVISIONING","STOPPED"}
  if any(task.get("lastStatus") not in states for task in listed):return emit("uncertain","persistence-restore-cleanup-task-state-uncertain",facts=facts)
  if any(task["lastStatus"]!="STOPPED" for task in listed):return emit("pending","persistence-restore-cleanup-verifier-still-running",facts=facts)
 if restored is None and not absent_database_reservations_resolved(rid,listed):return emit("uncertain","persistence-connection-diagnostic-reservation-binding-unproven",facts=facts)
 # If the database is absent its resource identity cannot own a remaining
 # policy. Only independently observed policy absence can complete cleanup.
 removed=remove_temporary_restore_identity_policy(m,ctl,observe_only,restored)
 if removed!="ok":return emit("pending" if removed.endswith("submitted") else "uncertain" if removed.endswith("not-observed") else "blocked",removed,facts=facts)
 if restored is None:return emit("cleaned-up","persistence-restore-all-temporary-effects-absent",facts={**facts,"database":"absent","temporary_authority":"absent","verifier_tasks":"none-active"})
 if restored.get("DBInstanceStatus")=="deleting":return emit("pending","persistence-restored-database-deletion-pending",facts=facts)
 if observe_only:return emit("uncertain","persistence-restored-database-deletion-not-observed",facts=facts)
 ok,_,code=m.aws("rds","delete-db-instance","--db-instance-identifier",rid,"--skip-final-snapshot")
 return emit("pending" if ok else "uncertain","persistence-restored-database-deletion-submitted" if ok else code,facts=facts)

def run_locked(action):
 """Serialize this checkout's shared verifier-role launch/cleanup decisions."""
 if fcntl is None:return emit("blocked","persistence-restoration-controller-lock-unavailable")
 # Local coordination only; ECS client tokens and retained launch reservations
 # preserve per-operation identity across interrupted controller processes.
 lock_path=ROOT/".cache/04.deploy/persistence-restoration-controller.lock"
 handle=None
 try:
  lock_path.parent.mkdir(parents=True,exist_ok=True)
  handle=lock_path.open("a")
  fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:
  if handle:handle.close()
  return emit("pending","persistence-restoration-controller-busy")
 except OSError:
  if handle:handle.close()
  return emit("blocked","persistence-restoration-controller-lock-unavailable")
 try:return action()
 finally:
  fcntl.flock(handle,fcntl.LOCK_UN);handle.close()

def diagnose_rejected(m,sid,rid,operation):
 """Re-observe one closed rejected verifier without restoring or rerunning it."""
 if not isinstance(operation,str) or re.fullmatch(r"kanbien-restore-[a-f0-9]{16}",operation) is None:return emit("blocked","persistence-restore-diagnostic-operation-invalid")
 ctl,cc=controls(m)
 if ctl is None:return emit("blocked",cc)
 arns,code=verifier_tasks(m,operation,ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"])
 if arns is None:return emit("uncertain",code)
 if len(arns)!=1:return emit("uncertain","persistence-restoration-verifier-task-identity-ambiguous",facts={"snapshot":sid,"restored_database":rid,"operation_id":operation})
 ok,value,code=m.aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",arns[0]);tasks=value.get("tasks") if ok and isinstance(value,dict) else None
 task=tasks[0] if isinstance(tasks,list) and len(tasks)==1 and isinstance(tasks[0],dict) else None
 if task is None or value.get("failures") or task.get("taskArn")!=arns[0] or task.get("taskDefinitionArn")!=ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"] or task.get("startedBy")!=operation:return emit("uncertain","persistence-restoration-verifier-task-binding-unavailable",facts={"snapshot":sid,"restored_database":rid,"operation_id":operation})
 if task.get("lastStatus")!="STOPPED":return emit("pending","persistence-restoration-verifier-still-running",facts={"snapshot":sid,"restored_database":rid,"operation_id":operation})
 containers=task.get("containers");exit_code=containers[0].get("exitCode") if isinstance(containers,list) and len(containers)==1 and isinstance(containers[0],dict) else None
 observation=observe_terminal_result(m,arns[0]);result=observation["result"]
 if type(exit_code) is not int or exit_code==0 or result not in RESTORE_REJECTED_RESULTS:return emit("blocked","persistence-restoration-verifier-rejection-evidence-invalid",facts={"snapshot":sid,"restored_database":rid,"operation_id":operation})
 findings=retain_verifier_rejection(m,operation,result,rid,task,execution=observation["execution"],task_observation=observation)
 facts={"snapshot":sid,"restored_database":rid,"operation_id":operation,"safe_result_code":result}
 if findings:return emit("blocked",result,*findings,facts=facts)
 return emit("diagnosed","persistence-restoration-verifier-rejection-reobserved",facts=facts)

def main(argv=None):
 p=argparse.ArgumentParser(add_help=False);p.add_argument("--operation");p.add_argument("--operation-id");p.add_argument("--snapshot-id");p.add_argument("--record-proof-receipt",type=Path);p.add_argument("--json",action="store_true");p.add_argument("--observe-only",action="store_true");p.add_argument("--validate-arguments",action="store_true");a,u=p.parse_known_args(argv);rid=restore_id(a.snapshot_id) if isinstance(a.snapshot_id,str) else None
 if u or a.operation not in {"restore","verify","cleanup","diagnose-connection","diagnose-rejected"} or rid is None or (a.operation in {"restore","diagnose-connection"})!=(a.record_proof_receipt is not None) or (a.operation=="diagnose-rejected")!=(a.operation_id is not None) or (a.operation_id is not None and re.fullmatch(r"kanbien-restore-[a-f0-9]{16}",a.operation_id) is None):return emit("blocked","persistence-isolated-restore-arguments-invalid")
 if a.validate_arguments:
  print(json.dumps({"schema":"deploy/command-arguments-report/v1","verdict":"valid","findings":[],"runtime_input_contract":{"workload":"persistence-restoration-verifier-task","names":["PERSISTENCE_POSTGRES_HOST"],"observation_required":True} if a.operation in {"verify","diagnose-connection"} else None,"proof_contract": {"proof_type":"restore","operation":"isolated-restore","result_code":"KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED","family":"kanbien-core-platform-persistence-restoration-verifier","deadline_workload":"persistence-restoration-verifier"} if a.operation=="verify" else None}));return 0
 m=load();return run_locked(lambda: restore(m,a.snapshot_id,rid,a.observe_only,a.record_proof_receipt) if a.operation=="restore" else verify(m,a.snapshot_id,rid,a.observe_only) if a.operation=="verify" else diagnose_connection(m,a.snapshot_id,rid,a.observe_only,a.record_proof_receipt) if a.operation=="diagnose-connection" else diagnose_rejected(m,a.snapshot_id,rid,a.operation_id) if a.operation=="diagnose-rejected" else cleanup(m,a.snapshot_id,rid,a.observe_only))
if __name__=="__main__":raise SystemExit(main())
