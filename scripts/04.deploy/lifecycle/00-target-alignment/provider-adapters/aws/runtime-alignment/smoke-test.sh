#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.runtime-alignment
#   version: 1
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the AWS runtime alignment adapter recognises only stable successful CloudFormation states.
#   portability: { class: reusable, targets: [entity-builder] }
#   used_by:
#   - id: deploy.adapter.aws.runtime-alignment
#     path: scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.py
#   effects: [read-only, writes-files]

ROOT="$(git rev-parse --show-toplevel)"
python3 - "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.py" <<'PY'
import contextlib, copy, importlib.util, io, json, sys, tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("runtime_alignment", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.STABLE_SUCCESSFUL_STACK_STATUSES == {"CREATE_COMPLETE", "UPDATE_COMPLETE"}
assert "UPDATE_IN_PROGRESS" not in module.STABLE_SUCCESSFUL_STACK_STATUSES
assert "UPDATE_ROLLBACK_COMPLETE" not in module.STABLE_SUCCESSFUL_STACK_STATUSES

accepted = Path(tempfile.mkstemp(suffix=".yml")[1])
accepted.write_text("""schema: deploy/accepted-release/v1
status: accepted
release:
  source_revision: "1111111111111111111111111111111111111111"
  image_digest: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
""", encoding="utf-8")

responses = {
    "sts": {"Account": "337159794548"},
    "ecr": {"imageDetails": [{}]},
    "foundation": {"Stacks": [{"StackStatus": "UPDATE_COMPLETE", "Outputs": [{"OutputKey": key} for key in {"VpcId", "PrivateSubnetIds", "RepositoryUri", "ClusterArn", "LogGroupName", "TaskExecutionRoleArn", "ServiceSecurityGroupId", "VerifierSecurityGroupId", "ServiceDiscoveryArn"}]}]},
    "runtime": {"Stacks": [{"StackStatus": "UPDATE_COMPLETE"}]},
    "clusters": {"clusters": [{"status": "ACTIVE"}]},
    "services": {"services": [{"runningCount": 1, "taskDefinition": "kanbien-core-platform-bootstrap-runtime:8", "deployments": [{"rolloutState": "COMPLETED"}]}]},
    "task": {"taskDefinition": {"containerDefinitions": [{"name": "kanbien-core-server", "image": "repo@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]}},
    "iam": {"Role": {"RoleName": "present"}},
}
class Run:
    returncode = 0
    stderr = ""
    def __init__(self, body): self.stdout = json.dumps(body)
original_responses=copy.deepcopy(responses)
calls=[]
def fake(command, **_):
    calls.append(command[:])
    joined = " ".join(command)
    if "sts get-caller-identity" in joined: return Run(responses["sts"])
    if "ecr describe-images" in joined: return Run(responses["ecr"])
    if "cloudformation describe-stacks" in joined: return Run(responses["foundation"] if "foundation" in joined else responses["runtime"])
    if "ecs describe-clusters" in joined: return Run(responses["clusters"])
    if "ecs describe-services" in joined: return Run(responses["services"])
    if "ecs describe-task-definition" in joined: return Run(responses["task"])
    if "iam get-role" in joined: return Run(responses["iam"])
    raise AssertionError(joined)
module.response_adapter()[1].inventory_covered=lambda _root: True
module.subprocess.run = fake
argv = ["script.py", "--profile", "x", "--region", "eu-west-1", "--account-id", "337159794548", "--repository", "repo", "--image-digest", "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "--foundation-stack", "foundation", "--runtime-stack", "runtime", "--cluster", "cluster", "--delivery-role", "delivery", "--execution-role", "execution", "--operation", "update", "--accepted-release", str(accepted)]
old = sys.argv; sys.argv = argv
stream = io.StringIO()
with contextlib.redirect_stdout(stream): status = module.main()
sys.argv = old
report = json.loads(stream.getvalue())
assert status == 0, report
assert report["operation"] == "update"
assert all(item["outcome"] == "match" for item in report["assertions"])
assert [command[:2] for command in calls]==[['aws','sts'],['aws','ecr'],['aws','cloudformation'],['aws','cloudformation'],['aws','ecs'],['aws','ecs'],['aws','ecs'],['aws','iam'],['aws','iam']]
responses["task"] = {"taskDefinition": {"containerDefinitions": [{"name": "kanbien-core-server", "image": "repo@sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"}]}}
sys.argv = argv; stream = io.StringIO()
with contextlib.redirect_stdout(stream): assert module.main() == 1
sys.argv = old
assert "accepted-runtime-not-healthy" in stream.getvalue()
# Differential anchors are the original predicates: later stack/cluster rows
# were ignored, service length short-circuited, restore ignored image mismatch.
def observe(body_changes, operation='update'):
    responses.clear(); responses.update(copy.deepcopy(original_responses)); responses.update(body_changes); calls.clear()
    arguments=argv[:]; arguments[arguments.index('--operation')+1]=operation
    stream=io.StringIO(); sys.argv=arguments
    try:
        with contextlib.redirect_stdout(stream): status=module.main()
    finally: sys.argv=old
    return status,json.loads(stream.getvalue())
for owner in ['foundation','runtime','clusters']:
    body=copy.deepcopy(original_responses[owner]); key='clusters' if owner=='clusters' else 'Stacks'; body[key].extend([None,{'ignored':[]}])
    first=body[key][0]
    assert (first.get('status')=='ACTIVE' if owner=='clusters' else first.get('StackStatus') in module.STABLE_SUCCESSFUL_STACK_STATUSES)
    status,report=observe({owner:body}); assert status==0 and all(item['outcome']=='match' for item in report['assertions']) and len(calls)==9
status,report=observe({'foundation':{'Stacks':{}}})
foundation=next(item for item in report['assertions'] if item['id']=='right-application')
assert status==1 and foundation=={'id':'right-application','outcome':'missing','finding_code':'foundation-runtime-output-missing'} and len(calls)==9
for services in [[None,None], {'ignored-first':None,'ignored-second':None}, [{'runningCount':0,'deployments':None}]]:
    # Preserve the original short-circuit, including never touching entries
    # when length is not one and never iterating deployments when count differs.
    old_ready=len(services)==1 and services[0].get('runningCount')==1 and all(item.get('rolloutState')=='COMPLETED' for item in services[0].get('deployments',[]) if isinstance(item,dict))
    assert old_ready is False
    status,report=observe({'services':{'services':services}})
    baseline=next(item for item in report['assertions'] if item['id']=='known-healthy-baseline')
    assert status==1 and baseline=={'id':'known-healthy-baseline','outcome':'unknown','finding_code':'runtime-task-definition-missing'} and len(calls)==8
for containers in ['', 'ignored', {}, {'ignored':None}]:
    old_match=any(isinstance(item,dict) and item.get('name')=='kanbien-core-server' and str(item.get('image','')).endswith('@'+'sha256:'+'a'*64) for item in containers)
    assert old_match is False
    status,report=observe({'task':{'taskDefinition':{'containerDefinitions':containers}}},'restore')
    baseline=next(item for item in report['assertions'] if item['id']=='known-healthy-baseline')
    assert status==0 and baseline['finding_code']=='restore-source-runtime-healthy' and baseline['outcome']=='match' and len(calls)==9
for owner,body,identifier in [
    ('foundation',{'Stacks':{'not-zero':None}},'right-application'),
    ('foundation',{'Stacks':[None]},'right-application'),
    ('foundation',{'Stacks':[{'Outputs':None}]},'right-application'),
    ('foundation',{'Stacks':[{'Outputs':[{'OutputKey':[]}]}]},'right-application'),
    ('runtime',{'Stacks':[{'StackStatus':{}}]},'known-healthy-baseline'),
    ('services',{'services':[None]},'known-healthy-baseline'),
    ('services',{'services':[{'runningCount':1,'deployments':None}]},'known-healthy-baseline'),
    ('task',{'taskDefinition':None},'known-healthy-baseline'),
    ('task',{'taskDefinition':{'containerDefinitions':None}},'known-healthy-baseline'),
    ('task',{'taskDefinition':{'containerDefinitions':5}},'known-healthy-baseline'),
    ('clusters',{'clusters':[None]},'required-settings'),
]:
    responses.clear(); responses.update(copy.deepcopy(original_responses)); responses[owner]=body; calls.clear()
    sys.argv=argv; stream=io.StringIO()
    with contextlib.redirect_stdout(stream): assert module.main()==1
    sys.argv=old; report=json.loads(stream.getvalue()); item=next(item for item in report['assertions'] if item['id']==identifier)
    assert item['outcome']=='unknown' and item['finding_code']=='invalid-response', item
    assert calls[-2:]==[['aws','iam','get-role','--role-name','delivery','--profile','x','--region','eu-west-1','--output','json'],['aws','iam','get-role','--role-name','execution','--profile','x','--region','eu-west-1','--output','json']]
    assert len(calls)==(8 if owner=='services' else 9)
module.subprocess.run=lambda *_args,**_kwargs: (_ for _ in ()).throw(OSError('https://private.invalid/provider-canary'))
sys.argv=argv; stream=io.StringIO()
with contextlib.redirect_stdout(stream): assert module.main()==1
sys.argv=old
assert 'provider-canary' not in stream.getvalue() and 'unavailable' in stream.getvalue()
accepted.unlink()
PY

echo "AWS runtime-alignment state tests passed."
