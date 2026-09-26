#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-deployment-artifact-store
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Statically prove the private, encrypted, short-retention CloudFormation artifact-store boundary for Kanbien staging.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import yaml


class CfnLoader(yaml.SafeLoader):
    pass


def intrinsic(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
    else:
        value = loader.construct_mapping(node)
    return {f"!{tag_suffix}": value}


CfnLoader.add_multi_constructor("!", intrinsic)

path = Path("infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/deployment-artifact-store.yml")
if path.stat().st_size > 51200:
    raise SystemExit("ERROR: artifact-store template must remain below CloudFormation's 51,200-byte inline limit")
with path.open(encoding="utf-8") as handle:
    template = yaml.load(handle, Loader=CfnLoader)
with Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml").open(encoding="utf-8") as handle:
    target_profile = yaml.safe_load(handle)

failures = []


def fail(message):
    failures.append(message)


resources = template.get("Resources", {})
if set(resources) != {"PlatformShellDeploymentArtifactBucket", "PlatformShellDeploymentArtifactBucketPolicy"}:
    fail("artifact store must contain only the bucket and its TLS-only policy")

bucket_resource = resources.get("PlatformShellDeploymentArtifactBucket", {})
bucket = bucket_resource.get("Properties", {})
if bucket_resource.get("Type") != "AWS::S3::Bucket":
    fail("artifact store bucket must be AWS::S3::Bucket")
if bucket_resource.get("DeletionPolicy") != "RetainExceptOnCreate" or bucket_resource.get("UpdateReplacePolicy") != "Retain":
    fail("artifact store bucket must delete only an initial creation rollback and retain established deployment evidence")
if bucket.get("BucketName") != "kanbien-staging-platform-shell-cfn-artifacts-337159794548":
    fail("artifact store bucket must retain its target-specific name")
if bucket.get("BucketEncryption") != {"ServerSideEncryptionConfiguration": [{"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}:
    fail("artifact store bucket must use default SSE-S3 encryption")
if bucket.get("OwnershipControls") != {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]}:
    fail("artifact store bucket must disable ACL ownership ambiguity")
if bucket.get("PublicAccessBlockConfiguration") != {"BlockPublicAcls": True, "BlockPublicPolicy": True, "IgnorePublicAcls": True, "RestrictPublicBuckets": True}:
    fail("artifact store bucket must block all public access paths")
expected_lifecycle = {"Rules": [{"Id": "expire-reviewed-change-set-templates", "Status": "Enabled", "Prefix": "change-sets/", "ExpirationInDays": 30, "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 1}}]}
if bucket.get("LifecycleConfiguration") != expected_lifecycle:
    fail("artifact store bucket must retain only bounded change-set artifacts")

policy_resource = resources.get("PlatformShellDeploymentArtifactBucketPolicy", {})
policy = policy_resource.get("Properties", {})
if policy_resource.get("Type") != "AWS::S3::BucketPolicy" or policy.get("Bucket") != {"!Ref": "PlatformShellDeploymentArtifactBucket"}:
    fail("artifact store policy must attach only to the target-owned bucket")
expected_statement = {
    "Sid": "DenyInsecureTransport",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": [{"!GetAtt": "PlatformShellDeploymentArtifactBucket.Arn"}, {"!Sub": "${PlatformShellDeploymentArtifactBucket.Arn}/*"}],
    "Condition": {"Bool": {"aws:SecureTransport": "false"}},
}
if policy.get("PolicyDocument", {}).get("Statement") != [expected_statement]:
    fail("artifact store policy must only deny non-TLS access and grant no additional principal")

outputs = template.get("Outputs", {})
if set(outputs) != {"DeploymentArtifactBucketName", "DeploymentArtifactBucketArn"}:
    fail("artifact store may expose only its non-secret bucket name and ARN")

cloudformation = target_profile.get("deployment", {}).get("cloudformation", {})
expected_configuration = {
    "deployment_artifact_store_stack": "kanbien-staging-platform-shell-deployment-artifacts",
    "deployment_artifact_store_template": str(path),
    "deployment_artifact_bucket_name": "kanbien-staging-platform-shell-cfn-artifacts-337159794548",
    "deployment_artifact_store_check": "npm run platform:shell:deployment-artifact-store:check",
    "deployment_artifact_store_status": "deployed-and-verified",
}
for key, expected in expected_configuration.items():
    if cloudformation.get(key) != expected:
        fail(f"target profile must retain reviewed artifact-store {key}")

if failures:
    for message in failures:
        print(f"ERROR: {message}")
    raise SystemExit(1)
print("Platform-shell deployment-artifact store static policy check passed.")
PY
