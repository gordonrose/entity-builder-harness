#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.runtime-alignment
#   version: 1
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the AWS runtime alignment adapter recognises only stable successful CloudFormation states.
#   portability: { class: reusable, targets: [entity-builder] }
#   used_by:
#   - id: deploy.adapter.aws.runtime-alignment
#     path: scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.py
#   effects: [read-only]

ROOT="$(git rev-parse --show-toplevel)"
python3 - "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.py" <<'PY'
import contextlib, importlib.util, io, json, sys, tempfile
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
def fake(command, **_):
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
responses["task"] = {"taskDefinition": {"containerDefinitions": [{"name": "kanbien-core-server", "image": "repo@sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"}]}}
sys.argv = argv; stream = io.StringIO()
with contextlib.redirect_stdout(stream): assert module.main() == 1
sys.argv = old
assert "accepted-runtime-not-healthy" in stream.getvalue()
accepted.unlink()
PY

echo "AWS runtime-alignment state tests passed."
