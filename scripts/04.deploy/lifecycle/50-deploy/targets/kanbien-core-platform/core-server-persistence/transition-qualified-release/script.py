#!/usr/bin/env python3
"""Update or roll back only the qualified persistence application image."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.transition-qualified-persistence-release.impl
#   version: 1
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-24"
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
EVIDENCE_ROOT = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence"
ALLOWED = {"AWS::ECS::TaskDefinition", "AWS::ECS::Service"}

def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path); value=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(value); return value
def emit(verdict,*codes,facts=None):
    value={"schema":"deploy/persistence-release-transition-report/v1","target":"kanbien-core-platform","scope":"core-server-persistence","verdict":verdict,"findings":[{"code":code} for code in codes]}
    if facts: value["facts"]=facts
    print(json.dumps(value,sort_keys=True)); return 0 if verdict=="transitioned" else 1
def reviewable(change, status, name, digest, revision, support_digest):
    if not isinstance(change,dict) or status not in {"CREATE_COMPLETE","UPDATE_COMPLETE"}: return False
    if name not in str(change.get("ChangeSetName","")) or change.get("Status")!="CREATE_COMPLETE" or change.get("ChangeSetType") not in {None,"UPDATE"}: return False
    params={x.get("ParameterKey"):x.get("ParameterValue") for x in change.get("Parameters",[]) if isinstance(x,dict)}
    if params.get("ImageDigest")!=digest or params.get("RestoreVerifierImageDigest")!=digest or params.get("SupportImageDigest")!=support_digest or params.get("SourceRevision")!=revision: return False
    changes=[x.get("ResourceChange",{}) for x in change.get("Changes",[]) if isinstance(x,dict)]
    return bool(changes) and {x.get("ResourceType") for x in changes} <= ALLOWED
def wait_reviewable(prepare,name,status,digest,revision,support_digest):
    for attempt in range(6):
        ok,change,code=prepare.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
        if not ok: return None,code
        if reviewable(change,status,name,digest,revision,support_digest): return change,"ok"
        if attempt<5: time.sleep(2)
    return None,"persistence-release-transition-not-reviewable"
def release_state(expected_predecessor, operation, receipt, compatibility_id):
    succession=load(ROOT/"scripts/04.deploy/lifecycle/60-run/release-succession/script.py","release_succession")
    try: state=succession.current(EVIDENCE_ROOT)
    except succession.SuccessionFailure: return None,"persistence-release-transition-current-release-invalid"
    if state is None or state.get("release_id")!=expected_predecessor: return None,"persistence-release-transition-predecessor-mismatch"
    if operation!="rollback": return state,"ok"
    if not isinstance(compatibility_id, str) or not compatibility_id:
        return None,"persistence-release-transition-rollback-compatibility-required"
    try:
        _, compatibility = succession.compatibility_record(EVIDENCE_ROOT, compatibility_id)
    except succession.SuccessionFailure:
        return None,"persistence-release-transition-rollback-permission-compatibility-unproven"
    identity = compatibility["identity"]
    if identity["target"] != "kanbien-core-platform" or identity["scope"] != "core-server-persistence":
        return None,"persistence-release-transition-rollback-compatibility-mismatch"
    if identity["image_digest"] != receipt.get("image_digest") or identity["source_revision"] != receipt.get("source_revision"):
        return None,"persistence-release-transition-rollback-receipt-mismatch"
    expected_workloads = ["core-server-service", "persistence-restoration-verifier-task", "private-release-verifier-task"]
    if identity["workloads"] != expected_workloads:
        return None,"persistence-release-transition-rollback-workloads-incomplete"
    current_declaration = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"
    current_permissions = TEMPLATE
    for expected, path in ((identity["configuration_contract"], current_declaration), (identity["permission_contract"], current_permissions)):
        if expected["path"] != str(path.relative_to(ROOT)) or expected["sha256"] != succession.sha256_bytes(path.read_bytes()):
            return None,"persistence-release-transition-rollback-contract-mismatch"
    return state,"ok"
def main():
    parser=argparse.ArgumentParser(add_help=False); parser.add_argument("--receipt",type=Path); parser.add_argument("--operation",choices=("update","rollback")); parser.add_argument("--expected-predecessor"); parser.add_argument("--rollback-compatibility"); parser.add_argument("--json",action="store_true")
    args,unknown=parser.parse_known_args()
    if unknown or args.receipt is None or args.operation is None or not isinstance(args.expected_predecessor,str) or not args.expected_predecessor: return emit("blocked","persistence-release-transition-arguments-invalid")
    prepare=load(ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py","prepare")
    create=load(ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.py","create")
    succession=load(ROOT/"scripts/04.deploy/lifecycle/60-run/release-succession/script.py","release_succession")
    receipt=prepare.validate_receipt(args.receipt)
    if receipt is None or not create.package_gates(args.receipt) or not prepare.live_budget()[0]: return emit("blocked","persistence-release-transition-preconditions-not-proven")
    current_state,state_code=release_state(args.expected_predecessor,args.operation,receipt,args.rollback_compatibility)
    if state_code!="ok": return emit("blocked",state_code)
    ok,stack,code=prepare.aws("cloudformation","describe-stacks","--stack-name",STACK); status=stack.get("Stacks",[{}])[0].get("StackStatus") if ok and isinstance(stack,dict) else None
    if not ok or status not in {"CREATE_COMPLETE","UPDATE_COMPLETE"}: return emit("blocked",code if not ok else "persistence-release-transition-stack-not-healthy")
    ok,service,code=prepare.aws("ecs","describe-services","--cluster",CLUSTER,"--services",SERVICE); services=service.get("services",[]) if ok and isinstance(service,dict) else []
    if len(services)!=1 or not isinstance(services[0],dict) or services[0].get("desiredCount")!=1 or services[0].get("runningCount")!=1: return emit("blocked","persistence-release-transition-service-not-healthy")
    outputs,code=prepare.foundation_outputs(); infra,code2=prepare.infrastructure_parameters(outputs) if outputs else (None,code)
    if infra is None or not prepare.candidate_image(receipt)[0]: return emit("blocked","persistence-release-transition-alignment-not-proven")
    digest,revision=receipt["image_digest"],receipt["source_revision"]
    support_digest = digest
    if args.operation == "rollback":
        current_ref = current_state
        if not isinstance(current_ref, dict):
            return emit("blocked", "persistence-release-transition-current-support-image-unavailable")
        try:
            current_history, _ = succession.document(EVIDENCE_ROOT / current_ref["record"]["path"])
            support_digest = current_history["release"]["image_digest"]
        except (KeyError, succession.SuccessionFailure):
            return emit("blocked", "persistence-release-transition-current-support-image-unavailable")
    name=f"kanbien-core-platform-persistence-{args.operation}-{digest[7:19]}"
    parameters=[{"ParameterKey":k,"ParameterValue":v} for k,v in (("VpcId",infra["VpcId"]),("VpcCidr",infra["VpcCidr"]),("PrivateSubnetIds",infra["PrivateSubnetIds"]),("ClusterArn",infra["ClusterArn"]),("NamespaceId",infra["NamespaceId"]),("EndpointSecurityGroupId",infra["EndpointSecurityGroupId"]),("S3ArtifactPrefixListId",infra["S3ArtifactPrefixListId"]),("VerifierSecurityGroupId",infra["VerifierSecurityGroupId"]),("LogGroupName",infra["LogGroupName"]),("ImageRepositoryArn","arn:aws:ecr:eu-west-1:337159794548:repository/kanbien-core-platform/core-server"),("ImageRepositoryUri",outputs["RepositoryUri"]),("ImageDigest",digest),("SupportImageDigest",support_digest),("RestoreVerifierImageDigest",digest),("SourceRevision",revision))]
    ok,_,code=prepare.aws("cloudformation","describe-change-set","--stack-name",STACK,"--change-set-name",name)
    if not ok:
        if code!="aws-resource-missing": return emit("blocked",code)
        with tempfile.NamedTemporaryFile(mode="w",suffix=".json",encoding="utf-8") as file:
            json.dump(parameters,file); file.flush(); ok,_,code=prepare.aws("cloudformation","create-change-set","--stack-name",STACK,"--change-set-name",name,"--change-set-type","UPDATE","--template-body",f"file://{TEMPLATE}","--parameters",f"file://{file.name}","--capabilities","CAPABILITY_NAMED_IAM")
        if not ok: return emit("blocked",code)
    change,code=wait_reviewable(prepare,name,status,digest,revision,support_digest)
    if change is None: return emit("blocked",code)
    ok,_,code=prepare.aws("cloudformation","execute-change-set","--stack-name",STACK,"--change-set-name",name)
    if not ok:return emit("blocked",code)
    waited=subprocess.run(["aws","cloudformation","wait","stack-update-complete","--stack-name",STACK,"--profile",prepare.PROFILE,"--region",prepare.REGION],capture_output=True,text=True)
    if waited.returncode:return emit("blocked","persistence-release-transition-not-complete")
    return emit("transitioned",f"persistence-{args.operation}-transition-executed",facts={"image_digest":digest,"support_image_digest":support_digest,"source_revision":revision,"change_set":name})
if __name__=="__main__": raise SystemExit(main())
