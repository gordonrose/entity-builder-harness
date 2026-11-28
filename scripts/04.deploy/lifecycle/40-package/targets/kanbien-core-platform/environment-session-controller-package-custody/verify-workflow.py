#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.validation.environment-session-controller.package-workflow
#   version: 1
#   status: draft
#   created_on: "2026-11-28"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Protect qualification, registry-only publication and immutable controller custody.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-environment-session-controller
#     path: .github/workflows/publish-kanbien-core-platform-environment-session-controller.yml
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shlex

ROOT = Path(__file__).resolve().parents[7]
BASE = "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/environment-session-controller-package-custody"
WORKFLOW = ".github/workflows/publish-kanbien-core-platform-environment-session-controller.yml"
IMAGE = "infra/04.deploy/03.product/image/environment-session-controller"
TARGET = "infra/04.deploy/03.product/targets/kanbien-core-platform"
STEM = "environment-session-controller"
BUILDER = "scripts/04.deploy/lifecycle/40-package/build-environment-session-controller-image/script.sh"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def require(value, reason):
    if not value:
        raise ValueError(reason)


def policy(source, access):
    resources = source["Resources"]
    require(set(resources) == {"ControllerRepository", "ControllerPublisherRole"}, "publisher-resources-invalid")
    repository = resources["ControllerRepository"]
    require(repository["Type"] == "AWS::ECR::Repository"
        and repository["DeletionPolicy"] == repository["UpdateReplacePolicy"] == "Retain"
        and repository["Properties"]["RepositoryName"] == "kanbien-core-platform/" + STEM
        and set(repository["Properties"]) == {"RepositoryName", "ImageTagMutability", "ImageScanningConfiguration", "EncryptionConfiguration", "Tags"}
        and repository["Properties"]["EncryptionConfiguration"] == {"EncryptionType": "AES256"}
        and repository["Properties"]["ImageTagMutability"] == "IMMUTABLE"
        and repository["Properties"]["ImageScanningConfiguration"] == {"ScanOnPush": True}, "publisher-repository-invalid")
    role = resources["ControllerPublisherRole"]["Properties"]
    require(resources["ControllerPublisherRole"]["Type"] == "AWS::IAM::Role"
        and role["RoleName"] == "github-kanbien-core-platform-session-publisher"
        and set(role) == {"RoleName", "Tags", "AssumeRolePolicyDocument", "Policies"}
        and len(role["Policies"]) == 1, "publisher-role-invalid")
    require(role["AssumeRolePolicyDocument"]["Statement"] == [{"Effect": "Allow",
        "Principal": {"Federated": {"Ref": "ExistingGitHubOidcProviderArn"}},
        "Action": "sts:AssumeRoleWithWebIdentity", "Condition": {"StringEquals": {
            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
            "token.actions.githubusercontent.com:sub": "repo:gordonrose/entity-builder-harness:environment:kanbien-core-platform"}}}], "publisher-trust-invalid")
    statements = role["Policies"][0]["PolicyDocument"]["Statement"]
    actions = {"ecr:" + name for name in ("BatchCheckLayerAvailability", "BatchGetImage", "CompleteLayerUpload",
        "DescribeImageScanFindings", "DescribeImages", "DescribeRepositories", "GetDownloadUrlForLayer",
        "InitiateLayerUpload", "PutImage", "UploadLayerPart")}
    require(len(statements) == 2 and statements[0] == {"Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*"}
        and statements[1] == {"Effect": "Allow", "Action": sorted(actions), "Resource": {"Fn::GetAtt": ["ControllerRepository", "Arn"]}},
        "publisher-permissions-invalid")
    require(access["schema"] == "deploy/delivery-access-contract/v1"
        and access["actor"] == role["RoleName"] and access["pipeline"] == STEM + "-package-custody"
        and access["workflow"] == WORKFLOW
        and access["provider_policy_source"] == TARGET + "/30-provider-realization/aws/cloudformation/" + STEM + "-publication.yml#ControllerPublisherRole"
        and {row["provider_action"] for row in access["operations"]} == actions | {"ecr:GetAuthorizationToken"},
        "publisher-access-contract-invalid")


def check(text=None):
    documents = module("session_package_documents", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
    guard = module("session_package_workflow_guard", ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/workflow_guard.py")
    publisher = module("session_package_publication", ROOT / BASE / "publication.py").PUBLISHER
    publisher.source_selection()
    text = (ROOT / WORKFLOW).read_text() if text is None else text
    workflow = guard.workflow_document(text)
    require(set(workflow) <= {"name", "on", True, "permissions", "concurrency", "env", "jobs"}
        and workflow.get("on", workflow.get(True)) == {"workflow_dispatch": {}}
        and workflow["permissions"] == {"contents": "read", "id-token": "write", "attestations": "write", "artifact-metadata": "write"}
        and workflow["concurrency"] == {"group": "kanbien-core-platform-environment-session-controller-publication", "cancel-in-progress": False}
        and workflow["env"] == {"AWS_REGION": "eu-west-1", "AWS_ROLE_ARN": "arn:aws:iam::337159794548:role/" + publisher.binding.role,
            "ECR_REPOSITORY": publisher.binding.repository, "ECR_URI": publisher.binding.uri}
        and set(workflow["jobs"]) == {"qualify-and-publish"}, "workflow-routing-invalid")
    job = workflow["jobs"]["qualify-and-publish"]
    require(set(job) == {"runs-on", "timeout-minutes", "environment", "steps"}
        and job["runs-on"] == "ubuntu-latest" and job["environment"] == "kanbien-core-platform"
        and job["timeout-minutes"] == 35, "workflow-job-invalid")
    steps = guard.job_steps(text, "qualify-and-publish")
    order = ["@actions/checkout@v4", "Install script dependencies", "Enforce approved source",
        "Enforce controller package contract", "Qualify declarations and actual candidate payload",
        "@aws-actions/configure-aws-credentials@v4", "Prove fixed delivery read access",
        "Retain pre-publication identity", "Log in to Amazon ECR", "Publish immutable image",
        "Require clean ECR scan", "Generate SBOM", "Attest image provenance", "Attest image SBOM",
        "Write and validate safe package-custody receipt", "Upload safe package-custody evidence",
        "Retain safe failed-operation evidence"]
    require([step.get("name", "@" + str(step.get("uses"))) for step in steps] == order
        and steps[0] == {"uses": "actions/checkout@v4", "with": {"persist-credentials": False}}, "workflow-steps-invalid")
    guard.protected_step(steps, "Install script dependencies", [["python3", "-m", "pip", "install", "PyYAML==6.0.3"]])
    guard.protected_step(steps, "Enforce approved source", [["python3", "-B", BASE + "/publication.py", "--operation", "validate-source"]])
    guard.protected_step(steps, "Enforce controller package contract", [["python3", "-B", BASE + "/verify-workflow.py", "--json"]])
    qualification, selected = guard.protected_step(steps, "Qualify declarations and actual candidate payload",
        [["bash", BUILDER, "--tag", publisher.binding.local_image, "--receipt", "$RUNNER_TEMP/qualified-image.json"]])
    require(selected.get("id") == "qualification", "qualification-outcome-invalid")
    published = guard.reserved_publication_binding(steps, qualification, command=BASE + "/publication.py", stem=STEM, target="kanbien-core-platform")
    scanned = guard.scan_step(steps, shlex.split('python3 scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py --repository "$ECR_REPOSITORY" --image-digest "${{ steps.image.outputs.digest }}" --report "$RUNNER_TEMP/ecr-scan.json"'), "Require clean ECR scan")
    require(published < scanned, "scan-precedes-publication")
    guard.custody_tail(steps, published_index=scanned, target="kanbien-core-platform", environment="temporary-session-controller",
        region="aws-eu-west-1", candidate="environment-session-cleanup-controller", contract="environment-session-controller-image",
        program="environment-session-controller", stem=STEM,
        artifact_name="kanbien-core-platform-environment-session-controller-package-custody-${{ github.run_id }}",
        qualification_outcome="${{ steps.qualification.outcome }}", scan_outcome="${{ steps.scan.outcome }}", scan_check="ecr_scan",
        provenance_name="Attest image provenance", attestation_name="Attest image SBOM",
        capture_name="Write and validate safe package-custody receipt", upload_name="Upload safe package-custody evidence",
        receipt_filename="package-custody-receipt.json",
        extra_artifacts=["${{ runner.temp }}/qualified-image.json", "${{ runner.temp }}/ecr-scan.json"], registry_expression="${{ env.ECR_URI }}")
    source = documents.template((ROOT / TARGET / "30-provider-realization/aws/cloudformation/environment-session-controller-publication.yml").read_text())
    source["Resources"]["ControllerPublisherRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"][1]["Action"].sort()
    policy(source, documents.template((ROOT / TARGET / "40-package-custody/github-actions/environment-session-controller-package-custody.delivery-access.yml").read_text()))
    contract = documents.template((ROOT / IMAGE / "image-contract.yml").read_text())
    docker = (ROOT / IMAGE / "Dockerfile").read_text()
    require(contract["schema"] == "deploy/controller-image-contract/v1"
        and contract["id"] == "environment-session-controller-image"
        and contract["entrypoint"] == "scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/script.py"
        and contract["source_root"] == "/opt/controller" and contract["platform"] == "linux/amd64"
        and contract["runtime_user"] == "65532:65532" and "USER 65532:65532\n" in docker
        and contract["source_paths"] == ["scripts/04.deploy", "scripts/repo/diagnostic-coverage/runtime_contract.py",
            "infra/04.deploy", ".github/workflows", "platform/*/contracts", "packages/core/contracts", "apps/platform-smoke/contracts"]
        and "FROM " + contract["aws_cli_base"] + " AS awscli\n" in docker
        and "FROM " + contract["python_base"] + "\n" in docker
        and all(re.fullmatch(r"[A-Za-z0-9_./:-]+@sha256:[a-f0-9]{64}", contract[key]) for key in ("aws_cli_base", "python_base"))
        and 'ENTRYPOINT ["/usr/local/bin/python3", "-I", "-B", "/opt/controller/' + contract["entrypoint"] + '"]' in docker,
        "image-contract-invalid")
    return {"verdict": "passed", "publication_performed": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.parse_args()
    try:
        print(json.dumps(check()))
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, ImportError):
        print(json.dumps({"verdict": "failed", "code": "session-package-contract-unconfirmed"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
