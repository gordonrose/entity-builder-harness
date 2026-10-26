#!/usr/bin/env python3
"""Apply only an enumerated isolated restoration-verifier provider correction."""
from __future__ import annotations
import argparse, importlib.util, json, subprocess, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[8]; STACK="kanbien-core-platform-core-server-persistence"; TEMPLATE=ROOT/"infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
ADDED={"RestorationVerifierSecurityGroup","RestoredDatabaseSecurityGroup","RestorationVerifierDnsUdpEgress","RestorationVerifierDnsTcpEgress","RestorationVerifierEndpointEgress","RestorationVerifierArtifactObjectStoreEgress","RestorationVerifierRestoredDatabaseEgress","RestoredDatabaseIngressFromRestorationVerifier","EndpointIngressFromRestorationVerifier","RestorationVerifierExecutionRole","CoreServerPersistenceRestorationVerifierTaskDefinition"}
EGRESS_ONLY={"RestorationVerifierRestoredDatabaseEgress"}
IMAGE_ONLY={"CoreServerPersistenceRestorationVerifierTaskDefinition"}
def load():
 p=ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py";s=importlib.util.spec_from_file_location("prepare",p);m=importlib.util.module_from_spec(s);assert s and s.loader;s.loader.exec_module(m);return m
def emit(v,*codes,facts=None):
 r={"schema":"deploy/persistence-restoration-surface-report/v1","target":"kanbien-core-platform","scope":"core-server-persistence","verdict":v,"findings":[{"code":c} for c in codes]};
 if facts:r["facts"]=facts
 print(json.dumps(r,sort_keys=True));return 0 if v in {"applied","discarded"} else 1
def parameter_values(value):
 if not isinstance(value,dict):return None
 items=value.get("Parameters")
 if not isinstance(items,list):return None
 result={}
 for item in items:
  if not isinstance(item,dict) or not isinstance(item.get("ParameterKey"),str) or not isinstance(item.get("ParameterValue"),str):return None
  key=item["ParameterKey"]
  if key in result:return None
  result[key]=item["ParameterValue"]
 return result
def expected_parameters(state,digest):
 values=parameter_values(state)
 if values is None:return None
 values["RestoreVerifierImageDigest"]=digest
 return values
def review(change,name,digest,mode="surface",expected=None):
 if not isinstance(change,dict) or change.get("Status")!="CREATE_COMPLETE" or change.get("ChangeSetType") not in {None,"UPDATE"} or not (change.get("ChangeSetName")==name or (isinstance(change.get("ChangeSetName"),str) and change["ChangeSetName"].startswith("arn:aws:cloudformation:") and change["ChangeSetName"].split(":changeSet/",1)[-1].split("/",1)[0]==name)):return False
 params=parameter_values(change)
 if params is None or params.get("RestoreVerifierImageDigest")!=digest:return False
 if expected is not None and params!=expected:return False
 allowed=EGRESS_ONLY if mode=="egress" else IMAGE_ONLY if mode=="image" else ADDED
 action="Modify" if mode=="image" else "Add"
 types={"AWS::ECS::TaskDefinition"} if mode=="image" else {"AWS::EC2::SecurityGroup","AWS::EC2::SecurityGroupIngress","AWS::EC2::SecurityGroupEgress","AWS::IAM::Role","AWS::ECS::TaskDefinition"}
 seen=set()
 for x in change.get("Changes",[]):
  c=x.get("ResourceChange",{}) if isinstance(x,dict) else {};seen.add(c.get("LogicalResourceId"))
  if c.get("LogicalResourceId") not in allowed or c.get("Action")!=action or c.get("ResourceType") not in types:return False
 return seen==allowed
def surface_parameters(state,digest):
 return [{"ParameterKey":x["ParameterKey"],"UsePreviousValue":True} for x in state.get("Parameters",[]) if isinstance(x,dict) and isinstance(x.get("ParameterKey"),str) and x["ParameterKey"]!="RestoreVerifierImageDigest"] + [{"ParameterKey":"RestoreVerifierImageDigest","ParameterValue":digest}]
def change_name(digest,mode):
 kind="egress" if mode=="egress" else "image" if mode=="image" else "surface"
 return f"kanbien-core-platform-persistence-restore-{kind}-{digest[7:19]}"
def reconcile(m,name,digest,mode="surface",expected=None):
 observed_identity=expected or {"RestoreVerifierImageDigest":digest}
 verdict,code=m.observe_update(name,observed_identity,lambda change:review(change,name,digest,mode,expected))
 return emit("applied" if verdict=="complete" else verdict,code,facts={"change_set":name,"restore_verifier_image_digest":digest,"mode":mode})
def discard_rejected_image_review(m,name,digest,expected):
 """Remove only an exact, unexecuted image review our guard has rejected."""
 ok,change,code=m.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
 if not ok and code=="aws-resource-missing":return emit("discarded","persistence-restoration-image-review-already-absent",facts={"change_set":name,"restore_verifier_image_digest":digest,"mode":"image"})
 if not ok or not isinstance(change,dict):return emit("blocked",code if not ok else "persistence-restoration-image-review-observation-invalid")
 if change.get("Status")!="CREATE_COMPLETE" or change.get("ExecutionStatus")!="AVAILABLE":return emit("blocked","persistence-restoration-image-review-not-unexecuted")
 if parameter_values(change)!=expected or review(change,name,digest,"image",expected):return emit("blocked","persistence-restoration-image-review-not-guard-rejected")
 ok,_,code=m.aws("cloudformation","delete-change-set","--stack-name",STACK,"--change-set-name",name)
 if not ok:return emit("blocked",code)
 for attempt in range(6):
  exists,_,observed=m.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
  if not exists and observed=="aws-resource-missing":return emit("discarded","persistence-restoration-image-review-discarded",facts={"change_set":name,"restore_verifier_image_digest":digest,"mode":"image"})
  if attempt<5:time.sleep(2)
 return emit("blocked","persistence-restoration-image-review-discard-not-confirmed")
def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument("--receipt",type=Path);p.add_argument("--mode",choices=("surface","egress","image"),default="surface");p.add_argument("--json",action="store_true");p.add_argument("--reconcile",action="store_true");p.add_argument("--discard-rejected-image-review",action="store_true");a,u=p.parse_known_args()
 if u or a.receipt is None or (a.reconcile and a.discard_rejected_image_review) or (a.discard_rejected_image_review and a.mode!="image"):return emit("blocked","persistence-restoration-surface-arguments-invalid")
 m=load();receipt=m.validate_receipt(a.receipt)
 if receipt is None:return emit("blocked","package-custody-receipt-invalid")
 digest=receipt["image_digest"];name=change_name(digest,a.mode)
 ok,stack,code=m.aws("cloudformation","describe-stacks","--stack-name",STACK);items=stack.get("Stacks") if ok and isinstance(stack,dict) else None; state=items[0] if isinstance(items,list) and len(items)==1 and isinstance(items[0],dict) else None
 if not isinstance(state,dict) or state.get("StackStatus") not in {"CREATE_COMPLETE","UPDATE_COMPLETE"}:return emit("blocked",code if not ok else "persistence-restoration-surface-stack-not-healthy")
 expected=expected_parameters(state,digest)
 if expected is None:return emit("blocked","persistence-restoration-surface-parameters-invalid")
 if a.discard_rejected_image_review:return discard_rejected_image_review(m,name,digest,expected)
 if a.reconcile:return reconcile(m,name,digest,a.mode,expected)
 if not m.declaration_covered() or not m.live_budget()[0] or not m.candidate_image(receipt)[0]:return emit("blocked","persistence-restoration-surface-preconditions-not-proven")
 ok,change,code=m.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
 if not ok:
  if code!="aws-resource-missing":return emit("blocked",code)
  params=surface_parameters(state,digest)
  with tempfile.NamedTemporaryFile(mode="w",suffix=".json") as f:
   json.dump(params,f);f.flush();command=["cloudformation","create-change-set","--stack-name",STACK,"--change-set-name",name,"--change-set-type","UPDATE"]
   command += ["--use-previous-template"] if a.mode=="image" else ["--template-body",f"file://{TEMPLATE}"]
   ok,_,code=m.aws(*command,"--parameters",f"file://{f.name}","--capabilities","CAPABILITY_NAMED_IAM")
  if not ok:return emit("uncertain",code,facts={"change_set":name})
  for _ in range(6):
   time.sleep(2);ok,change,code=m.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
   if ok and isinstance(change,dict) and change.get("Status")!="CREATE_PENDING":break
 if not review(change,name,digest,a.mode,expected):return reconcile(m,name,digest,a.mode,expected)
 if change.get("ExecutionStatus")!="AVAILABLE":return reconcile(m,name,digest,a.mode,expected)
 ok,_,code=m.aws("cloudformation","execute-change-set","--stack-name",STACK,"--change-set-name",name)
 if not ok:return emit("uncertain",code,facts={"change_set":name})
 return reconcile(m,name,digest,a.mode,expected)

if __name__=="__main__":raise SystemExit(main())
