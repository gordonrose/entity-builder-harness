#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.verify-runtime-release
#   version: 4
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-21"
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
import argparse, json, subprocess, sys
from datetime import datetime
from pathlib import Path

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
 try: return datetime.fromisoformat(value.replace("Z", "+00:00"))
 except ValueError: return None

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
def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument("--receipt",type=Path);p.add_argument("--not-before");p.add_argument("--json",action="store_true");a,u=p.parse_known_args()
 if u or a.receipt is None:out("blocked","private-verification-arguments-invalid");return 1
 if a.not_before is not None and timestamp(a.not_before) is None:out("blocked","private-verification-not-before-invalid");return 1
 c=candidate(a.receipt)
 if not c:out("blocked","package-custody-receipt-invalid");return 1
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
 reuse_boundary=a.not_before or runtime_stack.get("LastUpdatedTime")
 prior=completed_verifier_after(existing, verifier, reuse_boundary)
 if prior:
  if not task_exited_successfully(prior): out("blocked","private-release-verification-failed");return 1
  accepted, code=verifier_log_accepts(prior)
  if not accepted: out("blocked",code);return 1
  out("accepted","runtime-digest-and-private-verifier-accepted",facts={"source_revision":c["source_revision"],"image_digest":c["image_digest"],"runtime_task_definition":taskdef,"verifier_task_definition":verifier,"verification_mode":"reused-completed-private-task"});return 0
 network=f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{sg}],assignPublicIp=DISABLED}}"
 ok, run, code=aws("ecs","run-task","--cluster",CLUSTER,"--task-definition",verifier,"--launch-type","FARGATE","--count","1","--network-configuration",network)
 tasks=run.get("tasks",[]) if ok else []
 if not ok or len(tasks)!=1 or not tasks[0].get("taskArn"):out("blocked",code if not ok else "private-verifier-not-started");return 1
 arn=tasks[0]["taskArn"]
 waited=subprocess.run(["aws","ecs","wait","tasks-stopped","--cluster",CLUSTER,"--tasks",arn,"--profile",PROFILE,"--region",REGION],capture_output=True,text=True)
 if waited.returncode:out("blocked","private-verifier-not-stopped");return 1
 ok, finished, code=aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",arn)
 completed=finished.get("tasks",[{}])[0] if ok else {}
 if not ok or not task_exited_successfully(completed):out("blocked","private-release-verification-failed");return 1
 accepted, code=verifier_log_accepts(completed)
 if not accepted:out("blocked",code);return 1
 out("accepted","runtime-digest-and-private-verifier-accepted",facts={"source_revision":c["source_revision"],"image_digest":c["image_digest"],"runtime_task_definition":taskdef,"verifier_task_definition":verifier,"verification_mode":"fresh-private-task"});return 0
if __name__=="__main__":sys.exit(main())
