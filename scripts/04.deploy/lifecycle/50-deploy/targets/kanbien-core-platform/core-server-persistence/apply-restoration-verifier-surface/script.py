#!/usr/bin/env python3
"""Add only the isolated restore-verifier CloudFormation resources."""
from __future__ import annotations
import argparse, importlib.util, json, subprocess, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[8]; STACK="kanbien-core-platform-core-server-persistence"; TEMPLATE=ROOT/"infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
ADDED={"RestorationVerifierSecurityGroup","RestoredDatabaseSecurityGroup","RestorationVerifierDnsUdpEgress","RestorationVerifierDnsTcpEgress","RestorationVerifierEndpointEgress","RestorationVerifierArtifactObjectStoreEgress","RestorationVerifierRestoredDatabaseEgress","RestoredDatabaseIngressFromRestorationVerifier","EndpointIngressFromRestorationVerifier","RestorationVerifierExecutionRole","CoreServerPersistenceRestorationVerifierTaskDefinition"}
def load():
 p=ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py";s=importlib.util.spec_from_file_location("prepare",p);m=importlib.util.module_from_spec(s);assert s and s.loader;s.loader.exec_module(m);return m
def emit(v,*codes,facts=None):
 r={"schema":"deploy/persistence-restoration-surface-report/v1","target":"kanbien-core-platform","scope":"core-server-persistence","verdict":v,"findings":[{"code":c} for c in codes]};
 if facts:r["facts"]=facts
 print(json.dumps(r,sort_keys=True));return 0 if v=="applied" else 1
def review(change,name,digest):
 if not isinstance(change,dict) or change.get("Status")!="CREATE_COMPLETE" or change.get("ChangeSetType") not in {None,"UPDATE"} or name not in str(change.get("ChangeSetName","")):return False
 params={x.get("ParameterKey"):x.get("ParameterValue") for x in change.get("Parameters",[]) if isinstance(x,dict)}
 if params.get("RestoreVerifierImageDigest")!=digest:return False
 seen=set()
 for x in change.get("Changes",[]):
  c=x.get("ResourceChange",{}) if isinstance(x,dict) else {};seen.add(c.get("LogicalResourceId"))
  if c.get("LogicalResourceId") not in ADDED or c.get("Action")!="Add" or c.get("ResourceType") not in {"AWS::EC2::SecurityGroup","AWS::EC2::SecurityGroupIngress","AWS::EC2::SecurityGroupEgress","AWS::IAM::Role","AWS::ECS::TaskDefinition"}:return False
 return seen==ADDED
def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument("--receipt",type=Path);p.add_argument("--json",action="store_true");a,u=p.parse_known_args()
 if u or a.receipt is None:return emit("blocked","persistence-restoration-surface-arguments-invalid")
 m=load();receipt=m.validate_receipt(a.receipt)
 if receipt is None or not m.live_budget()[0] or not m.candidate_image(receipt)[0]:return emit("blocked","persistence-restoration-surface-preconditions-not-proven")
 ok,stack,code=m.aws("cloudformation","describe-stacks","--stack-name",STACK);items=stack.get("Stacks") if ok and isinstance(stack,dict) else None; state=items[0] if isinstance(items,list) and len(items)==1 and isinstance(items[0],dict) else None
 if not isinstance(state,dict) or state.get("StackStatus") not in {"CREATE_COMPLETE","UPDATE_COMPLETE"}:return emit("blocked",code if not ok else "persistence-restoration-surface-stack-not-healthy")
 digest=receipt["image_digest"];name=f"kanbien-core-platform-persistence-restore-surface-{digest[7:19]}"
 ok,change,code=m.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
 if not ok:
  if code!="aws-resource-missing":return emit("blocked",code)
  params=[{"ParameterKey":x["ParameterKey"],"UsePreviousValue":True} for x in state.get("Parameters",[]) if isinstance(x,dict) and isinstance(x.get("ParameterKey"),str)] + [{"ParameterKey":"RestoreVerifierImageDigest","ParameterValue":digest}]
  with tempfile.NamedTemporaryFile(mode="w",suffix=".json") as f:
   json.dump(params,f);f.flush();ok,_,code=m.aws("cloudformation","create-change-set","--stack-name",STACK,"--change-set-name",name,"--change-set-type","UPDATE","--template-body",f"file://{TEMPLATE}","--parameters",f"file://{f.name}","--capabilities","CAPABILITY_NAMED_IAM")
  if not ok:return emit("blocked",code)
  for _ in range(6):
   time.sleep(2);ok,change,code=m.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
   if ok and isinstance(change,dict) and change.get("Status")!="CREATE_PENDING":break
 if not review(change,name,digest):return emit("blocked","persistence-restoration-surface-change-set-not-reviewable")
 ok,_,code=m.aws("cloudformation","execute-change-set","--stack-name",STACK,"--change-set-name",name)
 if not ok:return emit("blocked",code)
 wait=subprocess.run(["aws","cloudformation","wait","stack-update-complete","--stack-name",STACK,"--profile",m.PROFILE,"--region",m.REGION],capture_output=True,text=True)
 return emit("applied","persistence-restoration-surface-update-executed",facts={"change_set":name,"restore_verifier_image_digest":digest}) if wait.returncode==0 else emit("blocked","persistence-restoration-surface-update-not-complete")
if __name__=="__main__":raise SystemExit(main())
