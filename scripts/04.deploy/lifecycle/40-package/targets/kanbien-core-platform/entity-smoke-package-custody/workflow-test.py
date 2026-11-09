#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.publication-workflow
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject unsafe publication workflow and repository-role counterexamples without provider access.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.publication-contract
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/smoke-test.sh
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import yaml

if not __debug__: raise SystemExit("ENTITY_SMOKE_WORKFLOW_ASSERTIONS_DISABLED")
SPEC = importlib.util.spec_from_file_location("entity_smoke_workflow", Path(__file__).with_name("verify-workflow.py"))
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)
original = (CONTROL.ROOT / CONTROL.WORKFLOW).read_text()
document = yaml.load(original, Loader=CONTROL.WorkflowLoader)
assert CONTROL.inspect(original) == []
assert CONTROL.inspect(yaml.safe_dump(document, sort_keys=False)) == [], "round-trip preserves the real trigger, not YAML-1.1 True"


def step(value, name):
    return next(item for item in value["jobs"]["qualify-and-publish"]["steps"] if item.get("name") == name)


mutations = [
    lambda v: v.update(on={"push": {}}),
    lambda v: v.update(defaults={"run": {"shell": "bash {0}"}}),
    lambda v: v["env"].update(ECR_REPOSITORY="another-repository"),
    lambda v: v["env"].update(AWS_ROLE_ARN="arn:aws:iam::337159794548:role/administrator"),
    lambda v: v["jobs"]["qualify-and-publish"].update(**{"continue-on-error": True}),
    lambda v: step(v, "Enforce protected main source").update(run="true"),
    lambda v: step(v, "Qualify declarations and actual candidate payload").update(**{"if": "false"}),
    lambda v: step(v, "Qualify declarations and actual candidate payload").update(**{"continue-on-error": True}),
    lambda v: step(v, "Qualify declarations and actual candidate payload").update(run=step(v, "Qualify declarations and actual candidate payload")["run"].replace("bash " + CONTROL.BUILD, "true #")),
    lambda v: step(v, "Qualify declarations and actual candidate payload").update(run=step(v, "Qualify declarations and actual candidate payload")["run"] + "\ntrue\n"),
    lambda v: step(v, "Prove fixed delivery read access").update(run="true"),
    lambda v: step(v, "Retain pre-publication identity")["with"].update(overwrite=True),
    lambda v: step(v, "Publish immutable image").update(run="docker push mutable:latest"),
    lambda v: step(v, "Publish immutable image").update(id="not-image"),
    lambda v: step(v, "Require clean ECR scan").update(**{"if": "false"}),
    lambda v: step(v, "Generate SBOM")["with"].update(image="unqualified:latest"),
    lambda v: step(v, "Attest image provenance")["with"].update(**{"subject-digest": "sha256:" + "0" * 64}),
    lambda v: step(v, "Write and validate safe package-custody receipt")["env"].update(QUALIFICATION_OUTCOME="success"),
    lambda v: step(v, "Upload safe package-custody evidence")["with"].update(overwrite=True),
    lambda v: step(v, "Record package-custody summary").update(run='{\necho "$(aws ecs update-service)"\n} >> "$GITHUB_STEP_SUMMARY"'),
    lambda v: step(v, "Retain safe failed-operation evidence")["with"].update(path="credential-row-provider-canary"),
    lambda v: v["jobs"]["qualify-and-publish"]["steps"].append({"name": "Unreviewed deployment", "run": "aws cloudformation execute-change-set"}),
]
for mutation in mutations:
    changed = copy.deepcopy(document); mutation(changed)
    result = CONTROL.inspect(yaml.safe_dump(changed, sort_keys=False))
    assert result == ["entity-smoke-publication-contract-invalid"]
    assert "credential-row-provider-canary" not in json.dumps(result)
assert CONTROL.inspect(original + "\npermissions: {contents: write}\n") == ["entity-smoke-publication-contract-invalid"], "duplicate YAML fields fail closed"
with tempfile.TemporaryDirectory(prefix="entity-smoke-workflow-") as temporary:
    builder = Path(temporary) / "builder.sh"
    builder.write_text((CONTROL.ROOT / CONTROL.BUILD).read_text() + "\n# editorial comment\n")
    assert CONTROL.inspect(original, builder=builder) == []
    builder.write_text("set +e\n" + (CONTROL.ROOT / CONTROL.BUILD).read_text())
    assert CONTROL.inspect(original, builder=builder) == ["entity-smoke-publication-contract-invalid"]
    smoke = Path(temporary) / "smoke.sh"
    smoke.write_text((CONTROL.ROOT / CONTROL.SMOKE).read_text().replace("node scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/verify-image.mjs", "true # node"))
    assert CONTROL.inspect(original, smoke=smoke) == ["entity-smoke-publication-contract-invalid"]

CF_SPEC = importlib.util.spec_from_file_location("entity_smoke_publication_cf", CONTROL.ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
CF = importlib.util.module_from_spec(CF_SPEC)
CF_SPEC.loader.exec_module(CF)
foundation = CF.template((CONTROL.ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke-publication.yml").read_text())


def publication_foundation(value):
    resources = value.get("Resources", {})
    if {name: item.get("Type") for name, item in resources.items()} != {"FeatureRepository": "AWS::ECR::Repository", "FeaturePublisherRole": "AWS::IAM::Role"}: return False
    repository = resources["FeatureRepository"]
    tags = [{"Key": "Target", "Value": "kanbien-core-platform"}, {"Key": "Scope", "Value": "entity-smoke"}]
    if repository.get("DeletionPolicy") != "Retain" or repository.get("UpdateReplacePolicy") != "Retain" or repository["Properties"] != {"RepositoryName": "kanbien-core-platform/entity-smoke", "ImageTagMutability": "IMMUTABLE", "ImageScanningConfiguration": {"ScanOnPush": True}, "EncryptionConfiguration": {"EncryptionType": "AES256"}, "Tags": tags}: return False
    role = resources["FeaturePublisherRole"]["Properties"]
    expected = {"RoleName": "github-kanbien-core-platform-entity-smoke-publisher", "Tags": tags,
                "AssumeRolePolicyDocument": {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Federated": {"Ref": "ExistingGitHubOidcProviderArn"}}, "Action": "sts:AssumeRoleWithWebIdentity", "Condition": {"StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com", "token.actions.githubusercontent.com:sub": "repo:gordonrose/entity-builder-harness:environment:kanbien-core-platform"}}}]},
                "Policies": [{"PolicyName": "publish-entity-smoke-image-only", "PolicyDocument": {"Version": "2012-10-17", "Statement": [
                    {"Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*"},
                    {"Effect": "Allow", "Action": ["ecr:BatchCheckLayerAvailability", "ecr:BatchGetImage", "ecr:CompleteLayerUpload", "ecr:DescribeImageScanFindings", "ecr:DescribeImages", "ecr:DescribeRepositories", "ecr:GetDownloadUrlForLayer", "ecr:InitiateLayerUpload", "ecr:PutImage", "ecr:UploadLayerPart"], "Resource": {"Fn::GetAtt": ["FeatureRepository", "Arn"]}},
                ]}}]}
    return role == expected


assert publication_foundation(foundation)
foundation_cases = [
    lambda v: v["Resources"]["FeatureRepository"]["Properties"].update(ImageTagMutability="MUTABLE"),
    lambda v: v["Resources"]["FeatureRepository"]["Properties"].update(ImageScanningConfiguration={"ScanOnPush": False}),
    lambda v: v["Resources"]["FeatureRepository"].update(DeletionPolicy="Delete"),
    lambda v: v["Resources"]["FeaturePublisherRole"]["Properties"].update(ManagedPolicyArns=["arn:aws:iam::aws:policy/AdministratorAccess"]),
    lambda v: v["Resources"]["FeaturePublisherRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"][1].update(Resource="*"),
    lambda v: v["Resources"]["FeaturePublisherRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"][1]["Action"].append("ecs:UpdateService"),
    lambda v: v["Resources"]["FeaturePublisherRole"]["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]["Condition"]["StringEquals"].update({"token.actions.githubusercontent.com:sub": "repo:*"}),
]
for mutation in foundation_cases:
    changed = copy.deepcopy(foundation); mutation(changed)
    assert not publication_foundation(changed)
print(json.dumps({"schema": "deploy/entity-smoke-publication-workflow-fixture/v1", "verdict": "passed", "workflow_negative_cases": len(mutations) + 3, "foundation_negative_cases": len(foundation_cases), "provider_observation": False}))
