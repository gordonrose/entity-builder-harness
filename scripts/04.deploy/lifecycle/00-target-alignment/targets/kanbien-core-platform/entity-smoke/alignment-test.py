#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.target-alignment
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject engine, dependency, private delivery, custody and budget misalignment through controlled responses, never cloud proof.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

if not __debug__: raise SystemExit("ENTITY_SMOKE_ALIGNMENT_ASSERTIONS_DISABLED")
SPEC = importlib.util.spec_from_file_location("entity_smoke_alignment_test", Path(__file__).with_name("script.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
CANARY = "credential-row-provider-canary"
VPC, GROUP = "vpc-" + "1" * 17, "sg-" + "2" * 17
SECRET = "arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien-core-platform-persistence-migration-aBc123"
RECEIPT = {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64, "receipt_reference": "github-actions-run:123"}


def fixture():
    outputs = {"VpcId": VPC, "PrivateSubnetIds": "subnet-" + "3" * 17, "ClusterArn": "arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-core-platform", "LogGroupName": "/aws/ecs/kanbien-core-platform", "ServiceDiscoveryArn": "arn:aws:servicediscovery:eu-west-1:337159794548:service/srv-abc123"}
    as_outputs = lambda values: [{"OutputKey": key, "OutputValue": value} for key, value in values.items()]
    data = {
        "identity": {"Account": M.ACCOUNT, "Arn": "arn:aws:sts::337159794548:assumed-role/ApprovedInspection/session"},
        "foundation": {"Stacks": [{"StackStatus": "UPDATE_COMPLETE", "Outputs": as_outputs(outputs)}]},
        "dependency_stack": {"Stacks": [{"StackStatus": "UPDATE_COMPLETE", "Outputs": as_outputs({"PersistenceDatabaseIdentifier": M.DATABASE, "PersistenceDatabaseEndpoint": "private-provider-canary.internal", "AdministratorCredentialsSecretArn": SECRET})}]},
        "vpc": {"Vpcs": [{"VpcId": VPC, "State": "available", "CidrBlock": "10.71.0.0/16"}]},
        "subnets": {"Subnets": [{"SubnetId": outputs["PrivateSubnetIds"], "VpcId": VPC, "State": "available", "MapPublicIpOnLaunch": False}]},
        "service": {"Service": {"DnsConfig": {"NamespaceId": "ns-abc123"}}},
        "namespace": {"Namespace": {"Id": "ns-abc123", "Name": "kanbien-core-platform.internal", "Type": "DNS_PRIVATE", "Properties": {"DnsProperties": {"HostedZoneId": "Z1234"}}}},
        "zone": {"HostedZone": {"Config": {"PrivateZone": True}}, "VPCs": [{"VPCId": VPC, "VPCRegion": M.REGION}]},
        "endpoints": {"VpcEndpoints": [{"ServiceName": "com.amazonaws.eu-west-1." + name, "State": "available", "VpcId": VPC, "VpcEndpointType": "Interface", "PrivateDnsEnabled": True, "Groups": [{"GroupId": GROUP}], **({"PolicyDocument": json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "secretsmanager:GetSecretValue", "Resource": [SECRET]}]})} if name == "secretsmanager" else {})} for name in ("ecr.api", "ecr.dkr", "logs", "secretsmanager")]},
        "prefix": {"PrefixLists": [{"PrefixListId": "pl-abc123"}]},
        "database": {"DBInstances": [{"DBInstanceIdentifier": M.DATABASE, "DBInstanceStatus": "available", "Engine": "postgres", "EngineVersion": "18.3", "StorageEncrypted": True, "PubliclyAccessible": False, "IAMDatabaseAuthenticationEnabled": True, "DbiResourceId": "db-ABCDEFGHIJKLMNOP", "DBName": "kanbienpersistence", "VpcSecurityGroups": [{"Status": "active", "VpcSecurityGroupId": "sg-" + "4" * 17}], "DBSubnetGroup": {"SubnetGroupStatus": "Complete", "DBSubnetGroupName": "private-database-group", "VpcId": VPC}, "DBParameterGroups": [{"ParameterApplyStatus": "in-sync", "DBParameterGroupName": "default.postgres18"}], "Endpoint": {"Address": "private-provider-canary.internal", "Port": 5432}}]},
        "secret": {"ARN": SECRET, "Name": "kanbien-core-platform-persistence-migration"},
        "ssl": {"Parameters": [{"ParameterName": "rds.force_ssl", "ParameterValue": "1"}]},
        "repository": {"repositories": [{"repositoryName": M.REPOSITORY, "repositoryUri": M.REPOSITORY_URI, "imageTagMutability": "IMMUTABLE", "imageScanningConfiguration": {"scanOnPush": True}}]},
        "image": {"imageDetails": [{"imageDigest": RECEIPT["image_digest"], "repositoryName": M.REPOSITORY}]},
        "scan": {"imageScanStatus": {"status": "COMPLETE"}, "imageScanFindings": {"findingSeverityCounts": {"LOW": 2}}},
        "budget": {"Budget": {"BudgetLimit": {"Amount": "100.0", "Unit": "USD"}, "CostFilters": {"TagKeyValue": ["user:Target$kanbien-core-platform"]}}},
    }
    calls = []
    def provider(service, operation, **parameters):
        calls.append((service, operation, parameters))
        assert (service, operation) in M.READS
        key = {"get-caller-identity": "identity", "describe-vpcs": "vpc", "describe-subnets": "subnets", "get-service": "service", "get-namespace": "namespace", "get-hosted-zone": "zone", "describe-vpc-endpoints": "endpoints", "describe-managed-prefix-lists": "prefix", "describe-db-instances": "database", "describe-secret": "secret", "describe-db-parameters": "ssl", "describe-repositories": "repository", "describe-images": "image", "describe-image-scan-findings": "scan", "describe-budget": "budget"}.get(operation)
        if operation == "describe-stacks": key = "foundation" if parameters["StackName"] == "kanbien-core-platform-foundation" else "dependency_stack"
        assert key in data
        return copy.deepcopy(data[key])
    return data, calls, provider


def observed(data_provider):
    return M.inspect(data_provider, RECEIPT, "2026-11-08T13:00:00+00:00")


data, calls, provider = fixture()
safe, parameters, group = observed(provider)
assert safe["verdict"] == "aligned" and safe["provider_mutation"] is False and safe["acceptance_evidence"] is False
assert safe["parameters_sha256"] == M.fingerprint(parameters)
assert parameters["ServerDesiredCount"] == "0" and parameters["AdministratorSecretArn"] == SECRET
assert all(marker not in json.dumps(safe) for marker in (CANARY, "private-provider-canary.internal", SECRET))
original_incarnation = safe["dependency_incarnation_sha256"]
data["database"]["DBInstances"][0]["DbiResourceId"] = "db-ZYXWVUTSRQPONMLK"
assert observed(provider)[0]["dependency_incarnation_sha256"] != original_incarnation
negatives = [
    (lambda d: d["identity"].update(Account="123456789012"), "alignment-account-not-confirmed"),
    (lambda d: d["foundation"]["Stacks"][0].update(StackStatus="UPDATE_IN_PROGRESS"), "alignment-foundation-not-ready"),
    (lambda d: d["subnets"]["Subnets"][0].update(MapPublicIpOnLaunch=True), "alignment-private-subnets-not-confirmed"),
    (lambda d: d["namespace"]["Namespace"].update(Type="DNS_PUBLIC"), "alignment-private-namespace-not-confirmed"),
    (lambda d: d["zone"]["HostedZone"]["Config"].update(PrivateZone=False), "alignment-private-namespace-vpc-mismatch"),
    (lambda d: d["endpoints"]["VpcEndpoints"].pop(), "alignment-private-delivery-not-confirmed"),
    (lambda d: d["endpoints"]["VpcEndpoints"][-1].update(PolicyDocument={"Statement": []}), "alignment-secret-delivery-policy-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0].update(EngineVersion="16.9"), "alignment-engine-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0].update(EngineVersion="18.4"), "alignment-engine-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0].update(StorageEncrypted=False), "alignment-dependency-security-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0].update(PubliclyAccessible=True), "alignment-dependency-security-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0].update(IAMDatabaseAuthenticationEnabled=False), "alignment-dependency-security-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0]["DBSubnetGroup"].update(VpcId="vpc-other"), "alignment-dependency-vpc-mismatch"),
    (lambda d: d["secret"].update(DeletedDate="2026-11-01"), "alignment-administrative-reference-not-confirmed"),
    (lambda d: d["ssl"]["Parameters"][0].update(ParameterValue="0"), "alignment-verified-tls-posture-not-confirmed"),
    (lambda d: d["ssl"].update(Marker="repeated-marker"), "alignment-parameter-observation-incomplete"),
    (lambda d: d["repository"]["repositories"][0].update(imageTagMutability="MUTABLE"), "alignment-immutable-repository-not-confirmed"),
    (lambda d: d["image"]["imageDetails"][0].update(imageDigest="sha256:" + "c" * 64), "alignment-qualified-image-not-observed"),
    (lambda d: d["scan"]["imageScanFindings"]["findingSeverityCounts"].update(HIGH=1), "alignment-clean-scan-not-confirmed"),
    (lambda d: d["budget"]["Budget"]["CostFilters"].update(TagKeyValue=[]), "alignment-target-budget-not-confirmed"),
]
for mutate, code in negatives:
    data, _, provider = fixture(); mutate(data)
    try: observed(provider)
    except M.AlignmentFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected alignment rejection")
try: M.aws("ecs", "run-task", cluster=CANARY)
except M.AlignmentFailure as failure: assert failure.code == "alignment-provider-operation-prohibited"
else: raise AssertionError("read-only adapter must reject task launch")

# Real disposable Git history proves checkpoint classification and the actual
# dirty-source guard. Only the downstream declaration/inventory responses are
# controlled; this is not image qualification or an AWS observation.
old_root, old_command = M.ROOT, M.command
with tempfile.TemporaryDirectory(prefix="entity-smoke-controller-checkpoint-") as temporary, patch.dict(os.environ, {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}, clear=True):
    M.ROOT = Path(temporary)
    def git(*arguments):
        result = subprocess.run(["git", "-c", "user.name=Controller repair fixture", "-c", "user.email=controller-fixture@example.invalid", *arguments], cwd=M.ROOT, text=True, capture_output=True, check=True)
        return result.stdout.strip()
    def write(path, text):
        destination = M.ROOT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)
    def commit(message):
        git("add", "."); git("commit", "--quiet", "-m", message)
        return git("rev-parse", "HEAD")
    def rejected_source(call, code="alignment-source-checkpoint-mismatch"):
        try: call()
        except M.AlignmentFailure as failure: assert failure.code == code, (failure.code, code)
        else: raise AssertionError("expected controller-checkpoint rejection")
    def checked_command(arguments, timeout=30):
        if arguments[0] == "git": return old_command(arguments, timeout)
        if arguments[:2] == ["bash", "scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh"]: return json.dumps({"verdict": "covered", "findings": []})
        if arguments[:3] == ["python3", "-B", "scripts/04.deploy/inventory-deploy-control/script.py"]: return json.dumps({"verdict": "covered", "findings": []})
        raise AssertionError("unexpected checkpoint-fixture command")
    M.command = checked_command
    try:
        git("init", "--quiet", "--initial-branch", "main")
        controller_path = M.CONTROLLER_DIRECTORY + "script.py"
        write(controller_path, "original controller\n")
        write("apps/entity-smoke/fixture.ts", "original application\n")
        source = commit("qualified application source")
        custody = {**RECEIPT, "source_revision": source}
        assert M.source_checkpoint(custody) == {"package_source_revision": source, "controller_revision": source}
        M.source_preflight(custody)
        write(controller_path, "checked controller correction\n")
        repair = commit("controller-only correction")
        assert M.source_checkpoint(custody) == {"package_source_revision": source, "controller_revision": repair}
        M.source_preflight(custody)
        for path in (
            "apps/entity-smoke/fixture.ts", "packages/core/src/shared/index.ts", "package-lock.json",
            "platform/runtime/fixture.ts", "platform/security/fixture.ts",
            "infra/04.deploy/03.product/image/entity-smoke/Dockerfile",
            "infra/04.deploy/03.product/image/entity-smoke/Dockerfile.dockerignore",
            "scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/script.sh",
            ".github/workflows/publish-kanbien-core-platform-entity-smoke.yml",
            M.TARGET + "/30-provider-realization/aws/cloudformation/entity-smoke.yml",
            M.SCOPE, M.CONTROLLER_DIRECTORY + "nested/not-an-admitted-controller.py",
        ):
            write(path, "changed non-controller input\n")
            commit("out-of-scope input")
            rejected_source(lambda: M.source_preflight(custody))
            git("revert", "--no-edit", "HEAD")
            M.source_preflight(custody)
        controller_file = M.ROOT / controller_path
        controller_file.unlink(); controller_file.symlink_to("outside-controller")
        commit("symlink is not a controller repair")
        rejected_source(lambda: M.source_checkpoint(custody))
        controller_file.unlink(); write(controller_path, "checked controller correction\n")
        commit("restore regular controller")
        write(controller_path, "uncommitted repair\n")
        rejected_source(lambda: M.source_preflight(custody), "alignment-committed-source-required")
        write(controller_path, "checked controller correction\n")
        write("unrelated-untracked.txt", CANARY)
        rejected_source(lambda: M.source_preflight(custody), "alignment-committed-source-required")
        (M.ROOT / "unrelated-untracked.txt").unlink()
        write("commitLogs/fixture/README.md", "session audit\n")
        M.source_preflight(custody)
        git("mv", "apps/entity-smoke/fixture.ts", M.CONTROLLER_DIRECTORY + "moved-application.py")
        commit("rename cannot hide changed application")
        rejected_source(lambda: M.source_checkpoint(custody))
        git("revert", "--no-edit", "HEAD")
        repaired_head = git("rev-parse", "HEAD")
        unrelated = git("commit-tree", "HEAD^{tree}", "-m", "same tree without qualified ancestry")
        git("switch", "--quiet", "--detach", unrelated)
        rejected_source(lambda: M.source_checkpoint(custody))
        git("switch", "--quiet", "--detach", repaired_head)
        M.source_preflight(custody)
    finally:
        M.ROOT, M.command = old_root, old_command

print(json.dumps({"schema": "deploy/entity-smoke-alignment-fixture/v1", "verdict": "passed", "negative_cases": len(negatives), "provider_observation": False, "checks": ["private-reference-projection", "actual-engine-boundary", "dependency-incarnation-binding", "no-provider-mutation", "real-git-controller-only-checkpoint", "image-template-runtime-and-custody-input-changes-rejected", "rename-symlink-dirty-untracked-and-nonancestor-rejected"]}))
