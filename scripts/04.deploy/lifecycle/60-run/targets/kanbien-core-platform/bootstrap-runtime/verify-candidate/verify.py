#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.verify-runtime-release
#   version: 6
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Verify the deployed immutable runtime through one fixed private release verifier, optionally requiring evidence created after a supplied safe time boundary.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.verify-candidate.wrapper
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/script.sh
#   effects: [aws-mutation]
from __future__ import annotations
import argparse, json, re, subprocess, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[8]
PROFILE, REGION = "kanbien-dev", "eu-west-1"
FOUNDATION, RUNTIME, CLUSTER, SERVICE = "kanbien-core-platform-foundation", "kanbien-core-platform-bootstrap-runtime", "kanbien-core-platform", "kanbien-core-platform-bootstrap-runtime"
def aws(*p: str):
 r=subprocess.run(["aws",*p,"--profile",PROFILE,"--region",REGION,"--output","json"],capture_output=True,text=True)
 if r.returncode:
  t=r.stderr.lower(); return False,None,"aws-access-denied" if "accessdenied" in t or "not authorized" in t else "aws-command-failed"
 try:return True,json.loads(r.stdout),"ok"
 except json.JSONDecodeError:return False,None,"aws-response-invalid"
LOG_GROUP = "/aws/ecs/kanbien-core-platform"
TASK_ARN = re.compile(r"arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/[a-f0-9]{32}")
OBSERVATION_MAX_AGE = timedelta(minutes=10)
SCOPE_CONTRACT = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml"

def out(verdict,*codes,facts=None):
 report={"schema":"deploy/private-runtime-verification-report/v1","target":"kanbien-core-platform","verdict":verdict,"findings":[{"code":c} for c in codes]}
 if facts: report["facts"]=facts
 print(json.dumps(report,sort_keys=True))
def candidate(path):
 v=ROOT/"scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
 r=subprocess.run(["bash",str(v),"--receipt",str(path),"--expected-target","kanbien-core-platform","--expected-candidate","kanbien-core-server-candidate","--expected-package-contract","kanbien-core-server-image","--expected-program","kanbien-core-server","--json"],capture_output=True,text=True)
 return json.loads(r.stdout) if not r.returncode else None

def timestamp(value):
 if not isinstance(value, str): return None
 try:
  parsed=datetime.fromisoformat(value.replace("Z", "+00:00"))
  return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
 except (ValueError, TypeError, OverflowError): return None


def verifier_completion_deadline():
 try:
  contract=yaml.safe_load(SCOPE_CONTRACT.read_text(encoding="utf-8"))
 except (OSError, yaml.YAMLError): return None
 if not isinstance(contract,dict): return None
 workloads=contract.get("health_recovery",{}).get("workloads",[])
 verifier=next((item for item in workloads if isinstance(item,dict) and item.get("id")=="private-release-verifier"),None)
 deadline=verifier.get("completion",{}).get("deadline_seconds") if isinstance(verifier,dict) else None
 return deadline if isinstance(deadline,int) and deadline>0 else None


def verifier_duration_seconds(task):
 started=timestamp(task.get("startedAt")) if isinstance(task,dict) else None
 stopped=timestamp(task.get("stoppedAt")) if isinstance(task,dict) else None
 if started is None or stopped is None or stopped < started: return None
 return int((stopped-started).total_seconds())


def completed_within_deadline(task, deadline_seconds):
 duration=verifier_duration_seconds(task)
 if duration is None: return False, "private-verifier-duration-unavailable"
 if duration>deadline_seconds: return False, "private-verifier-completion-deadline-exceeded"
 return True, "ok"


def wait_for_verifier_stop(task_arn, deadline_seconds, inspect_task, *, monotonic=time.monotonic, sleep=time.sleep, poll_seconds=5):
 """Wait only to the declared controller deadline; never retry an uncertain task."""
 started=monotonic()
 latest=None
 while True:
  state, task=inspect_task(task_arn)
  if state != "ok" or not isinstance(task,dict): return "uncertain", None
  latest=task
  if task.get("lastStatus")=="STOPPED": return "stopped", task
  remaining=deadline_seconds-(monotonic()-started)
  if remaining<=0: return "still-running", latest
  sleep(min(poll_seconds, remaining))


def inspect_verifier_task(task_arn):
 ok, described, code=aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",task_arn)
 tasks=described.get("tasks",[]) if ok else []
 if not ok or len(tasks)!=1: return code if not ok else "task-not-returned", None
 return "ok", tasks[0]

def completed_verifier_after(tasks, verifier, not_before):
 """Return the latest verifier task created by this deployment, if any."""
 boundary=timestamp(not_before)
 matching=[]
 for task in tasks:
  if not isinstance(task, dict) or task.get("taskDefinitionArn") != verifier: continue
  stopped=timestamp(task.get("stoppedAt"))
  if boundary is not None and (stopped is None or stopped < boundary): continue
  matching.append(task)
 return max(matching, key=lambda task: str(task.get("stoppedAt", ""))) if matching else None

def verifier_log_accepts(task):
 arn=task.get("taskArn")
 if not isinstance(arn, str) or not arn.rsplit("/", 1)[-1]: return False, "private-verifier-evidence-unavailable"
 task_id=arn.rsplit("/", 1)[-1]
 ok, events, code=aws("logs","get-log-events","--log-group-name",LOG_GROUP,"--log-stream-name",f"release-verifier/private-release-verifier/{task_id}","--start-from-head")
 if not ok: return False, code
 messages=[event.get("message") for event in events.get("events",[]) if isinstance(event,dict)]
 if any(isinstance(message,str) and '"verdict":"accepted"' in message and '"code":"KANBIEN_CORE_RELEASE_VERIFIED"' in message for message in messages): return True, "ok"
 return False, "private-verifier-evidence-mismatch"

def task_exited_successfully(task):
 containers=task.get("containers",[]) if isinstance(task,dict) else []
 return bool(containers) and containers[0].get("exitCode") == 0
def current_runtime_task(task_definition, image_digest):
 """Observe the exact healthy task at the acceptance boundary."""
 ok, listed, code=aws("ecs","list-tasks","--cluster",CLUSTER,"--service-name",SERVICE,"--desired-status","RUNNING")
 arns=listed.get("taskArns") if ok and isinstance(listed,dict) else None
 if not ok: return None,code
 if not isinstance(arns,list) or len(arns)!=1 or not isinstance(arns[0],str) or TASK_ARN.fullmatch(arns[0]) is None: return None,"runtime-observation-task-invalid"
 ok, described, code=aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",arns[0])
 tasks=described.get("tasks") if ok and isinstance(described,dict) else None
 if not ok: return None,code
 task=tasks[0] if isinstance(tasks,list) and len(tasks)==1 and isinstance(tasks[0],dict) else None
 if task is None or task.get("taskArn")!=arns[0] or task.get("taskDefinitionArn")!=task_definition or task.get("group")!="service:"+SERVICE or task.get("lastStatus")!="RUNNING" or task.get("healthStatus")!="HEALTHY": return None,"runtime-observation-task-invalid"
 containers=task.get("containers")
 expected_image="337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server@"+image_digest
 if not isinstance(containers,list) or len(containers)!=1 or not isinstance(containers[0],dict) or containers[0].get("name")!="kanbien-core-server" or containers[0].get("image")!=expected_image: return None,"runtime-observation-image-mismatch"
 return arns[0],"ok"


def accept_observation(candidate, runtime_definition, verifier_definition, task, expected_arn, mode, deadline):
 now=datetime.now(timezone.utc)
 stopped=timestamp(task.get("stoppedAt")) if isinstance(task,dict) else None
 if not isinstance(expected_arn,str) or TASK_ARN.fullmatch(expected_arn) is None or not isinstance(task,dict) or task.get("taskArn")!=expected_arn or task.get("taskDefinitionArn")!=verifier_definition or task.get("lastStatus")!="STOPPED":
  out("blocked","private-verifier-task-identity-invalid"); return 1
 if stopped is None or not now-OBSERVATION_MAX_AGE<=stopped<=now:
  out("blocked","private-verifier-observation-stale-or-invalid"); return 1
 runtime_arn,code=current_runtime_task(runtime_definition,candidate["image_digest"])
 if runtime_arn is None: out("blocked",code); return 1
 out("accepted","runtime-digest-and-private-verifier-accepted",facts={"source_revision":candidate["source_revision"],"image_digest":candidate["image_digest"],"runtime_task_definition":runtime_definition,"verifier_task_definition":verifier_definition,"runtime_task_arn":runtime_arn,"verifier_task_arn":expected_arn,"observed_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"verification_mode":mode,"completion_deadline_seconds":deadline,"completion_duration_seconds":verifier_duration_seconds(task)})
 return 0


def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument("--receipt",type=Path);p.add_argument("--not-before");p.add_argument("--json",action="store_true");p.add_argument("--validate-arguments",action="store_true");a,u=p.parse_known_args()
 if u or a.receipt is None:out("blocked","private-verification-arguments-invalid");return 1
 if a.not_before is not None and timestamp(a.not_before) is None:out("blocked","private-verification-not-before-invalid");return 1
 if a.validate_arguments:print(json.dumps({"schema":"deploy/command-arguments-report/v1","verdict":"valid","findings":[],"proof_contract":{"proof_type":"private-runtime-verification","operation":"verify","result_code":"runtime-digest-and-private-verifier-accepted"}})); return 0
 c=candidate(a.receipt)
 if not c:out("blocked","package-custody-receipt-invalid");return 1
 deadline=verifier_completion_deadline()
 if deadline is None:out("blocked","private-verifier-deadline-contract-invalid");return 1
 ok, stack, code=aws("cloudformation","describe-stacks","--stack-name",RUNTIME)
 if not ok:out("blocked",code);return 1
 runtime_stack=stack.get("Stacks",[{}])[0]
 outputs={x.get("OutputKey"):x.get("OutputValue") for x in runtime_stack.get("Outputs",[]) if isinstance(x,dict)}
 taskdef, verifier=outputs.get("BootstrapRuntimeTaskDefinitionArn"),outputs.get("ReleaseVerifierTaskDefinitionArn")
 if not taskdef or not verifier:out("blocked","runtime-verification-outputs-unavailable");return 1
 ok, service, code=aws("ecs","describe-services","--cluster",CLUSTER,"--services",SERVICE)
 if not ok:out("blocked",code);return 1
 services=service.get("services",[])
 if not services or services[0].get("runningCount") != 1 or services[0].get("taskDefinition") != taskdef or any(d.get("rolloutState") != "COMPLETED" for d in services[0].get("deployments",[])):
  out("blocked","runtime-service-not-healthy");return 1
 ok, td, code=aws("ecs","describe-task-definition","--task-definition",taskdef)
 containers=td.get("taskDefinition",{}).get("containerDefinitions",[]) if ok else []
 if not ok or not any(cn.get("name")=="kanbien-core-server" and cn.get("image","").endswith("@"+c["image_digest"]) for cn in containers):out("blocked","runtime-task-image-mismatch");return 1
 ok, foundation, code=aws("cloudformation","describe-stacks","--stack-name",FOUNDATION)
 if not ok:out("blocked",code);return 1
 outputs={x.get("OutputKey"):x.get("OutputValue") for x in foundation.get("Stacks",[{}])[0].get("Outputs",[]) if isinstance(x,dict)}
 subnets, sg=outputs.get("PrivateSubnetIds"),outputs.get("VerifierSecurityGroupId")
 if not subnets or not sg:out("blocked","foundation-verifier-network-unavailable");return 1
 family=verifier.rsplit("/",1)[-1].rsplit(":",1)[0]
 ok, listed, code=aws("ecs","list-tasks","--cluster",CLUSTER,"--family",family,"--desired-status","STOPPED","--max-results","100")
 existing_arns=listed.get("taskArns",[]) if ok else []
 if not ok: out("blocked",code);return 1
 existing=[]
 if existing_arns:
  ok, described, code=aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",*existing_arns)
  if not ok: out("blocked",code);return 1
  existing=described.get("tasks",[])
 # A caller may require evidence produced after a controlled recovery action.
 # Otherwise the stack update time remains the safe reuse boundary.
 reuse_boundary=timestamp(a.not_before or runtime_stack.get("LastUpdatedTime"))
 freshness_boundary=datetime.now(timezone.utc)-OBSERVATION_MAX_AGE
 reuse_boundary=max(reuse_boundary,freshness_boundary) if reuse_boundary is not None else freshness_boundary
 reuse_boundary=reuse_boundary.isoformat()
 prior=completed_verifier_after(existing, verifier, reuse_boundary)
 if prior:
  within, code=completed_within_deadline(prior, deadline)
  if not within: out("blocked",code);return 1
  if not task_exited_successfully(prior): out("blocked","private-release-verification-failed");return 1
  accepted, code=verifier_log_accepts(prior)
  if not accepted: out("blocked",code);return 1
  return accept_observation(c,taskdef,verifier,prior,prior.get("taskArn"),"reused-completed-private-task",deadline)
 network=f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{sg}],assignPublicIp=DISABLED}}"
 ok, run, code=aws("ecs","run-task","--cluster",CLUSTER,"--task-definition",verifier,"--launch-type","FARGATE","--count","1","--network-configuration",network)
 tasks=run.get("tasks",[]) if ok else []
 if not ok or len(tasks)!=1 or not tasks[0].get("taskArn"):out("blocked",code if not ok else "private-verifier-not-started");return 1
 arn=tasks[0]["taskArn"]
 state, completed=wait_for_verifier_stop(arn, deadline, inspect_verifier_task)
 if state=="still-running":out("blocked","private-verifier-controller-deadline-remote-task-still-running");return 1
 if state!="stopped":out("blocked","private-verifier-controller-deadline-remote-task-uncertain");return 1
 within, code=completed_within_deadline(completed, deadline)
 if not within:out("blocked",code);return 1
 if not task_exited_successfully(completed):out("blocked","private-release-verification-failed");return 1
 accepted, code=verifier_log_accepts(completed)
 if not accepted:out("blocked",code);return 1
 return accept_observation(c,taskdef,verifier,completed,arn,"fresh-private-task",deadline)
if __name__=="__main__":sys.exit(main())
