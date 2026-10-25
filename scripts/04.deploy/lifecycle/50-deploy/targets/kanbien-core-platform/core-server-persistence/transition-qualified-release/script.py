#!/usr/bin/env python3
"""Update or roll back only the qualified persistence application image."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.transition-qualified-persistence-release.impl
#   version: 3
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Execute a receipt-bound persistence image transition after an exact CloudFormation review.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.transition-qualified-persistence-release
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.sh
#   effects: [aws-mutation]
from __future__ import annotations
import argparse, importlib.util, json, subprocess, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
STACK, CLUSTER, SERVICE = "kanbien-core-platform-core-server-persistence", "kanbien-core-platform", "kanbien-core-platform-core-server-persistence"
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml"
ALLOWED = {"AWS::ECS::TaskDefinition", "AWS::ECS::Service"}
STABLE_STACK_STATES = {"CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"}
DIAGNOSTICS = ROOT / "scripts/04.deploy/shared/deployment-operation-diagnostics.py"
DIAGNOSTIC_DIRECTORY = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/operation-diagnostics"

def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path); value=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(value); return value
def diagnostic_controls():
    return load(DIAGNOSTICS,"deployment_operation_diagnostics")
def retain_failure_diagnostic(prepare,name,digest,code,outcome):
    """Retain an allowlisted failed/uncertain diagnosis, never raw events."""
    try:
        diagnostics=diagnostic_controls()
        diagnostic_outcome="unknown" if outcome=="uncertain" else outcome
        classification,facts,_outcome,collection=diagnostics.collect_cloudformation_failure(prepare.aws,stack_name=STACK,change_set_name=name)
        facts={**facts,"change_set_id":name,"artifact_identity":digest}
        report=diagnostics.build_report(
            target="kanbien-core-platform",scope="core-server-persistence",operation_id=name,
            stage="deploy",original_code=code,exit_status=1,outcome=diagnostic_outcome,
            classification=classification if collection!="failed" else diagnostics.classify_aws_error("aws-command-failed"),
            evidence_reference=f"receipt-path:operation-diagnostics/{name}.json",
            next_decision="inspect-retained-evidence" if diagnostic_outcome=="failed" else "observe-current-operation",
            collection_status=collection,facts=facts,
        )
        diagnostics.write_report(DIAGNOSTIC_DIRECTORY/f"{name}.json",report)
    except Exception:
        return "persistence-release-transition-diagnostic-collection-failed"
    return None
def emit(verdict,*codes,facts=None):
    value={"schema":"deploy/persistence-release-transition-report/v1","target":"kanbien-core-platform","scope":"core-server-persistence","verdict":verdict,"findings":[{"code":code} for code in codes]}
    if facts: value["facts"]=facts
    print(json.dumps(value,sort_keys=True)); return 0 if verdict=="transitioned" else 1
def reviewable(change, status, name, digest, revision):
    if not isinstance(change,dict) or status not in STABLE_STACK_STATES: return False
    if not (change.get("ChangeSetName")==name or (isinstance(change.get("ChangeSetName"),str) and change["ChangeSetName"].startswith("arn:aws:cloudformation:") and change["ChangeSetName"].split(":changeSet/",1)[-1].split("/",1)[0]==name)) or change.get("Status")!="CREATE_COMPLETE" or change.get("ChangeSetType") not in {None,"UPDATE"}: return False
    params={x.get("ParameterKey"):x.get("ParameterValue") for x in change.get("Parameters",[]) if isinstance(x,dict)}
    if params.get("ImageDigest")!=digest or params.get("SupportImageDigest")!=digest or params.get("RestoreVerifierImageDigest")!=digest or params.get("SourceRevision")!=revision: return False
    changes=[x.get("ResourceChange",{}) for x in change.get("Changes",[]) if isinstance(x,dict)]
    return bool(changes) and {x.get("ResourceType") for x in changes} <= ALLOWED
def wait_reviewable(prepare,name,status,digest,revision):
    for attempt in range(6):
        ok,change,code=prepare.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
        if not ok: return None,code
        if reviewable(change,status,name,digest,revision): return change,"ok"
        if attempt<5: time.sleep(2)
    return None,"persistence-release-transition-not-reviewable"
def reconcile(prepare,name,digest,revision):
    verdict,code=prepare.observe_update(name,{"ImageDigest":digest,"SupportImageDigest":digest,"RestoreVerifierImageDigest":digest,"SourceRevision":revision},lambda change:reviewable(change,"UPDATE_COMPLETE",name,digest,revision))
    finding=retain_failure_diagnostic(prepare,name,digest,code,verdict) if verdict in {"failed","uncertain"} else None
    return emit("transitioned" if verdict=="complete" else verdict,code,*((finding,) if finding else ()),facts={"change_set":name,"image_digest":digest,"source_revision":revision})
def main():
    parser=argparse.ArgumentParser(add_help=False); parser.add_argument("--receipt",type=Path); parser.add_argument("--operation",choices=("update","rollback")); parser.add_argument("--json",action="store_true"); parser.add_argument("--reconcile",action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args,unknown=parser.parse_known_args()
    if unknown or args.receipt is None or args.operation is None: return emit("blocked","persistence-release-transition-arguments-invalid")
    if args.validate_arguments: print(json.dumps({"schema":"deploy/command-arguments-report/v1","verdict":"valid","findings":[]})); return 0
    prepare=load(ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py","prepare")
    create=load(ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py","create")
    receipt=prepare.validate_receipt(args.receipt)
    if receipt is None:return emit("blocked","package-custody-receipt-invalid")
    digest,revision=receipt["image_digest"],receipt["source_revision"]
    name=f"kanbien-core-platform-persistence-{args.operation}-{digest[7:19]}"
    if args.reconcile:return reconcile(prepare,name,digest,revision)
    if not create.package_gates(args.receipt) or not prepare.live_budget()[0]: return emit("blocked","persistence-release-transition-preconditions-not-proven")
    ok,stack,code=prepare.aws("cloudformation","describe-stacks","--stack-name",STACK); status=stack.get("Stacks",[{}])[0].get("StackStatus") if ok and isinstance(stack,dict) else None
    if not ok or status not in STABLE_STACK_STATES: return emit("blocked",code if not ok else "persistence-release-transition-stack-not-healthy")
    current_parameters={item.get("ParameterKey"):item.get("ParameterValue") for item in stack.get("Stacks",[{}])[0].get("Parameters",[]) if isinstance(item,dict)}
    ok,service,code=prepare.aws("ecs","describe-services","--cluster",CLUSTER,"--services",SERVICE); services=service.get("services",[]) if ok and isinstance(service,dict) else []
    if len(services)!=1 or not isinstance(services[0],dict) or services[0].get("desiredCount")!=1 or services[0].get("runningCount")!=1: return emit("blocked","persistence-release-transition-service-not-healthy")
    outputs,code=prepare.foundation_outputs(); infra,code2=prepare.infrastructure_parameters(outputs) if outputs else (None,code)
    if infra is None or not prepare.candidate_image(receipt)[0]: return emit("blocked","persistence-release-transition-alignment-not-proven")
    digest,revision=receipt["image_digest"],receipt["source_revision"]
    name=f"kanbien-core-platform-persistence-{args.operation}-{digest[7:19]}"
    parameters=[{"ParameterKey":k,"ParameterValue":v} for k,v in prepare.candidate_parameters(outputs,infra,receipt).items()]
    ok,_,code=prepare.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
    if not ok:
        if code!="aws-resource-missing": return emit("blocked",code)
        with tempfile.NamedTemporaryFile(mode="w",suffix=".json",encoding="utf-8") as file:
            json.dump(parameters,file); file.flush(); ok,_,code=prepare.aws("cloudformation","create-change-set","--stack-name",STACK,"--change-set-name",name,"--change-set-type","UPDATE","--template-body",f"file://{TEMPLATE}","--parameters",f"file://{file.name}","--capabilities","CAPABILITY_NAMED_IAM")
        if not ok: return emit("uncertain",code,facts={"change_set":name})
    change,code=wait_reviewable(prepare,name,status,digest,revision)
    if change is None: return reconcile(prepare,name,digest,revision)
    if change.get("ExecutionStatus")!="AVAILABLE":return reconcile(prepare,name,digest,revision)
    expected=prepare.candidate_parameters(outputs,infra,receipt)
    actual={item.get("ParameterKey"):item.get("ParameterValue") for item in change.get("Parameters",[]) if isinstance(item,dict)}
    if not prepare.update_parameters_match(actual,expected,current_parameters):return emit("blocked","persistence-update-live-parameters-mismatch")
    ok,_,code=prepare.aws("cloudformation","execute-change-set","--stack-name",STACK,"--change-set-name",name)
    if not ok:return emit("uncertain",code,facts={"change_set":name})
    return reconcile(prepare,name,digest,revision)

if __name__=="__main__": raise SystemExit(main())
