#!/usr/bin/env python3
"""Govern one fixed isolated native PostgreSQL restore proof."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re
from datetime import datetime
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[8]
DATABASE="kanbien-core-platform-persistence"; CLUSTER="kanbien-core-platform"; SERVICE="kanbien-core-platform-core-server-persistence"; STACK="kanbien-core-platform-core-server-persistence"; FOUNDATION="kanbien-core-platform-foundation"; LOG_GROUP="/aws/ecs/kanbien-core-platform"
SNAPSHOT=re.compile(r"^kanbien-core-platform-persistence-recovery-(?P<day>[0-9]{8})$"); RECORD_ID="core-persistence-acceptance-v1"; FACT_DIGEST=hashlib.sha256(b"kanbien-core-persistence-acceptance-v1").hexdigest(); DEADLINE=120
def load():
 p=ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"; s=importlib.util.spec_from_file_location("prepare",p); m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m); return m
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
 x=SNAPSHOT.fullmatch(snapshot_id); return f"kanbien-core-platform-persistence-restore-{x.group('day')}" if x else None
def source(m):
 if not m.live_budget()[0]:return None,"target-budget-live-configuration-invalid"
 v,c=db(m,DATABASE)
 if not isinstance(v,dict) or v.get("DBInstanceStatus")!="available" or v.get("PubliclyAccessible") is not False or v.get("StorageEncrypted") is not True:return None,c if v is None else "persistence-restore-source-not-healthy"
 ok,d,c=m.aws("ecs","describe-services","--cluster",CLUSTER,"--services",SERVICE); xs=d.get("services") if ok and isinstance(d,dict) else None; s=xs[0] if isinstance(xs,list) and len(xs)==1 and isinstance(xs[0],dict) else None
 return (v,"ok") if isinstance(s,dict) and s.get("desiredCount")==1 and s.get("runningCount")==1 else (None,c if not ok else "persistence-restore-source-service-not-healthy")
def controls(m):
 s,c=outputs(m,STACK); f,_=outputs(m,FOUNDATION)
 needed={"CoreServerPersistenceRestorationVerifierTaskDefinitionArn","PersistenceRestorationVerifierSecurityGroupId","PersistenceRestoredDatabaseSecurityGroupId"}
 if not isinstance(s,dict) or not needed<=s.keys() or any(not s[k] for k in needed):return None,"persistence-restore-control-surface-unavailable"
 if not isinstance(f,dict) or not isinstance(f.get("PrivateSubnetIds"),str) or not f["PrivateSubnetIds"]:return None,"persistence-restore-private-network-unavailable"
 s["PrivateSubnetIds"]=f["PrivateSubnetIds"];return s,"ok"
def correct(restored,src,group):
 attached=[x.get("VpcSecurityGroupId") for x in restored.get("VpcSecurityGroups",[]) if isinstance(x,dict)]; a=src.get("DBSubnetGroup",{}).get("DBSubnetGroupName") if isinstance(src.get("DBSubnetGroup"),dict) else None; b=restored.get("DBSubnetGroup",{}).get("DBSubnetGroupName") if isinstance(restored.get("DBSubnetGroup"),dict) else None
 return restored.get("DBInstanceStatus")=="available" and restored.get("PubliclyAccessible") is False and restored.get("StorageEncrypted") is True and restored.get("Engine")=="postgres" and attached==[group] and isinstance(a,str) and a==b
def restore(m,sid,rid,observe_only=False):
 src,c=source(m); point,pc=snapshot(m,sid); ctl,cc=controls(m)
 if src is None:return emit("blocked",c)
 if point is None or point.get("Status")!="available" or point.get("Encrypted") is not True or point.get("DBInstanceIdentifier")!=DATABASE:return emit("blocked",pc if point is None else "persistence-recovery-point-invalid")
 if ctl is None:return emit("blocked",cc)
 value,status=db(m,rid)
 if value is None:
  if status!="aws-resource-missing":return emit("uncertain",status)
  if observe_only:return emit("uncertain","persistence-restore-operation-not-observed",facts={"snapshot":sid,"restored_database":rid})
  subnet=src.get("DBSubnetGroup",{}).get("DBSubnetGroupName") if isinstance(src.get("DBSubnetGroup"),dict) else None; cls=src.get("DBInstanceClass")
  if not isinstance(subnet,str) or not isinstance(cls,str):return emit("blocked","persistence-restore-source-shape-invalid")
  ok,_,c=m.aws("rds","restore-db-instance-from-db-snapshot","--db-instance-identifier",rid,"--db-snapshot-identifier",sid,"--db-instance-class",cls,"--db-subnet-group-name",subnet,"--vpc-security-group-ids",ctl["PersistenceRestoredDatabaseSecurityGroupId"],"--no-publicly-accessible","--no-multi-az","--copy-tags-to-snapshot","--tags","Key=Target,Value=kanbien-core-platform","Key=Purpose,Value=isolated-persistence-restore-rehearsal")
  return emit("pending" if ok else "uncertain","persistence-restore-submitted-awaiting-provider-observation" if ok else c,facts={"snapshot":sid,"restored_database":rid})
 if value.get("DBInstanceStatus") in {"creating","backing-up","modifying","rebooting","configuring-enhanced-monitoring"}:return emit("pending","persistence-restore-still-provisioning",facts={"snapshot":sid,"restored_database":rid})
 if value.get("DBInstanceStatus") in {"failed","incompatible-restore","inaccessible-encryption-credentials","storage-full"}:return emit("failed","persistence-restore-provider-failed",facts={"snapshot":sid,"restored_database":rid})
 if value.get("DBInstanceStatus")!="available":return emit("uncertain","persistence-restore-provider-status-unknown",facts={"snapshot":sid,"restored_database":rid})
 return emit("restored","persistence-restored-database-ready",facts={"snapshot":sid,"restored_database":rid}) if correct(value,src,ctl["PersistenceRestoredDatabaseSecurityGroupId"]) else emit("blocked","persistence-restored-database-posture-invalid")
def task_def_valid(m,arn):
 ok,d,_=m.aws("ecs","describe-task-definition","--task-definition",arn); t=d.get("taskDefinition") if ok and isinstance(d,dict) else None; cs=t.get("containerDefinitions") if isinstance(t,dict) else None
 if not isinstance(cs,list) or len(cs)!=1 or not isinstance(cs[0],dict):return False
 # ECS describes task-definition environment and secret fields as lower-case
 # ``name``/``value``/``valueFrom``.  Keep this parser deliberately narrow:
 # only the exact verifier shape may reach an isolated restored database.
 c=cs[0]; env={x.get("name"):x.get("value") for x in c.get("environment",[]) if isinstance(x,dict)}; secrets={x.get("name") for x in c.get("secrets",[]) if isinstance(x,dict)}
 return c.get("name")=="persistence-restoration-verifier" and c.get("command")==["artifacts/kanbien-core-server-persistence-restore-verifier.main.js"] and secrets=={"PERSISTENCE_RESTORE_RUNTIME_CREDENTIALS"} and "PERSISTENCE_POSTGRES_HOST" not in env and env.get("PERSISTENCE_POSTGRES_DATABASE")=="kanbienpersistence" and env.get("PERSISTENCE_POSTGRES_SCHEMA")=="platform"
def task_duration(task):
 try:
  a=datetime.fromisoformat(task["startedAt"].replace("Z","+00:00")); b=datetime.fromisoformat(task["stoppedAt"].replace("Z","+00:00")); return int((b-a).total_seconds()) if b>=a else None
 except (KeyError,ValueError,TypeError,OverflowError):return None
def accepted_log(m,arn):
 tid=arn.rsplit("/",1)[-1]; ok,d,c=m.aws("logs","get-log-events","--log-group-name",LOG_GROUP,"--log-stream-name",f"persistence-restoration-verifier/persistence-restoration-verifier/{tid}","--start-from-head"); xs=d.get("events") if ok and isinstance(d,dict) else None
 if not isinstance(xs,list):return "uncertain"
 for event in xs:
  try:value=json.loads(event.get("message", "")) if isinstance(event,dict) else None
  except (json.JSONDecodeError,TypeError):continue
  if isinstance(value,dict) and value.get("verdict")=="accepted" and value.get("code")=="KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED":return "accepted"
 return "pending"
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
     if not isinstance(tasks, list) or described.get("failures") or len(tasks) != len(batch) or {task.get("taskArn") for task in tasks if isinstance(task, dict)} != set(batch):
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
 if restored is None or not correct(restored,src,ctl["PersistenceRestoredDatabaseSecurityGroupId"]):return emit("blocked",rc if restored is None else "persistence-restored-database-posture-invalid")
 endpoint=restored.get("Endpoint",{}).get("Address") if isinstance(restored.get("Endpoint"),dict) else None; td=ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"]
 if not isinstance(endpoint,str) or not task_def_valid(m,td):return emit("blocked","persistence-restoration-verifier-definition-invalid")
 started=restore_run_identity(restored)
 if started is None:return emit("blocked","persistence-restored-database-identity-unavailable")
 arns,c=verifier_tasks(m,started,ctl["CoreServerPersistenceRestorationVerifierTaskDefinitionArn"])
 if arns is None:return emit("uncertain",c)
 if arns:
  ok,d,c=m.aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",*arns); xs=[x for x in d.get("tasks",[]) if isinstance(x,dict) and x.get("taskDefinitionArn")==td] if ok and isinstance(d,dict) else []
  if len(arns)!=1 or len(xs)!=1 or d.get("failures"):return emit("uncertain","persistence-restoration-verifier-task-identity-ambiguous")
  t=xs[0]
  facts={"snapshot":sid,"restored_database":rid,"operation_id":started}
  if t.get("taskArn")!=arns[0] or t.get("startedBy")!=started:return emit("blocked","persistence-restoration-verifier-task-binding-invalid",facts=facts)
  overrides=t.get("overrides",{}).get("containerOverrides",[]) if isinstance(t.get("overrides"),dict) and set(t["overrides"])=={"containerOverrides"} else []
  expected_env={"PERSISTENCE_POSTGRES_HOST":endpoint,"PERSISTENCE_ACCEPTANCE_RECORD_ID":RECORD_ID,"PERSISTENCE_ACCEPTANCE_FACT_DIGEST":FACT_DIGEST}
  actual_env={x.get("name"):x.get("value") for x in overrides[0].get("environment",[]) if isinstance(x,dict)} if len(overrides)==1 and isinstance(overrides[0],dict) and overrides[0].get("name")=="persistence-restoration-verifier" else {}
  if actual_env!=expected_env or len(overrides[0].get("environment",[]))!=len(expected_env) or set(overrides[0])!={"name","environment"}:return emit("blocked","persistence-restoration-verifier-task-binding-invalid",facts=facts)
  if t.get("lastStatus") in {"PROVISIONING","PENDING","ACTIVATING","RUNNING","DEACTIVATING","STOPPING","DEPROVISIONING"}:return emit("pending","persistence-restoration-verifier-still-running",facts=facts)
  if t.get("lastStatus")!="STOPPED":return emit("uncertain","persistence-restoration-verifier-status-unknown",facts=facts)
  containers=t.get("containers"); exit_code=containers[0].get("exitCode") if isinstance(containers,list) and len(containers)==1 and isinstance(containers[0],dict) else None; duration=task_duration(t); arn=t.get("taskArn")
  if type(exit_code) is not int or duration is None or not isinstance(arn,str):return emit("uncertain","persistence-restoration-verifier-completion-evidence-unavailable",facts=facts)
  if exit_code!=0 or duration>DEADLINE:return emit("failed","persistence-restoration-verifier-completion-invalid",facts=facts)
  evidence=accepted_log(m,arn)
  if evidence!="accepted":return emit(evidence,"persistence-restoration-verifier-log-evidence-unavailable",facts=facts)
  return emit("accepted","persistence-isolated-restoration-record-retrieved",facts={**facts,"verifier_task":arn.rsplit("/",1)[-1],"completion_duration_seconds":duration})
 if observe_only:return emit("uncertain","persistence-restoration-verifier-operation-not-observed",facts={"snapshot":sid,"restored_database":rid,"operation_id":started})
 net=f"awsvpcConfiguration={{subnets=[{ctl['PrivateSubnetIds']}],securityGroups=[{ctl['PersistenceRestorationVerifierSecurityGroupId']}],assignPublicIp=DISABLED}}"; overrides=json.dumps({"containerOverrides":[{"name":"persistence-restoration-verifier","environment":[{"name":"PERSISTENCE_POSTGRES_HOST","value":endpoint},{"name":"PERSISTENCE_ACCEPTANCE_RECORD_ID","value":RECORD_ID},{"name":"PERSISTENCE_ACCEPTANCE_FACT_DIGEST","value":FACT_DIGEST}]}]})
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
 ok,_,c=m.aws("rds","delete-db-instance","--db-instance-identifier",rid,"--skip-final-snapshot")
 return emit("pending" if ok else "uncertain","persistence-restored-database-deletion-submitted" if ok else c,facts={"snapshot":sid,"restored_database":rid})
def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument("--operation");p.add_argument("--snapshot-id");p.add_argument("--json",action="store_true");p.add_argument("--observe-only",action="store_true");a,u=p.parse_known_args();rid=restore_id(a.snapshot_id) if isinstance(a.snapshot_id,str) else None
 if u or a.operation not in {"restore","verify","cleanup"} or rid is None:return emit("blocked","persistence-isolated-restore-arguments-invalid")
 m=load();return restore(m,a.snapshot_id,rid,a.observe_only) if a.operation=="restore" else verify(m,a.snapshot_id,rid,a.observe_only) if a.operation=="verify" else cleanup(m,a.snapshot_id,rid,a.observe_only)
if __name__=="__main__":raise SystemExit(main())
