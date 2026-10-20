#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.verify-runtime-release
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Verify the deployed immutable runtime and run its fixed private release verifier exactly once.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.verify-candidate.wrapper
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/script.sh
#   effects: [aws-mutation]
from __future__ import annotations
import argparse, json, subprocess, sys
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
def out(verdict,*codes,facts=None):
 report={"schema":"deploy/private-runtime-verification-report/v1","target":"kanbien-core-platform","verdict":verdict,"findings":[{"code":c} for c in codes]}
 if facts: report["facts"]=facts
 print(json.dumps(report,sort_keys=True))
def candidate(path):
 v=ROOT/"scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
 r=subprocess.run(["bash",str(v),"--receipt",str(path),"--expected-target","kanbien-core-platform","--expected-candidate","kanbien-core-server-candidate","--expected-package-contract","kanbien-core-server-image","--expected-program","kanbien-core-server","--json"],capture_output=True,text=True)
 return json.loads(r.stdout) if not r.returncode else None
def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument("--receipt",type=Path);p.add_argument("--json",action="store_true");a,u=p.parse_known_args()
 if u or a.receipt is None:out("blocked","private-verification-arguments-invalid");return 1
 c=candidate(a.receipt)
 if not c:out("blocked","package-custody-receipt-invalid");return 1
 ok, stack, code=aws("cloudformation","describe-stacks","--stack-name",RUNTIME)
 if not ok:out("blocked",code);return 1
 outputs={x.get("OutputKey"):x.get("OutputValue") for x in stack.get("Stacks",[{}])[0].get("Outputs",[]) if isinstance(x,dict)}
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
 network=f"awsvpcConfiguration={{subnets=[{subnets}],securityGroups=[{sg}],assignPublicIp=DISABLED}}"
 ok, run, code=aws("ecs","run-task","--cluster",CLUSTER,"--task-definition",verifier,"--launch-type","FARGATE","--count","1","--network-configuration",network)
 tasks=run.get("tasks",[]) if ok else []
 if not ok or len(tasks)!=1 or not tasks[0].get("taskArn"):out("blocked",code if not ok else "private-verifier-not-started");return 1
 arn=tasks[0]["taskArn"]
 waited=subprocess.run(["aws","ecs","wait","tasks-stopped","--cluster",CLUSTER,"--tasks",arn,"--profile",PROFILE,"--region",REGION],capture_output=True,text=True)
 if waited.returncode:out("blocked","private-verifier-not-stopped");return 1
 ok, finished, code=aws("ecs","describe-tasks","--cluster",CLUSTER,"--tasks",arn)
 exited=finished.get("tasks",[{}])[0].get("containers",[]) if ok else []
 if not ok or not exited or exited[0].get("exitCode")!=0:out("blocked","private-release-verification-failed");return 1
 out("accepted","runtime-digest-and-private-verifier-accepted",facts={"source_revision":c["source_revision"],"image_digest":c["image_digest"],"runtime_task_definition":taskdef,"verifier_task_definition":verifier});return 0
if __name__=="__main__":sys.exit(main())
