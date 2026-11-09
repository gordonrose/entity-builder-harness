#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.target-alignment
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject engine, dependency, private delivery, custody and budget misalignment through controlled responses, never cloud proof.
#   portability: {class: internal, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
import importlib.util
import json
from pathlib import Path

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
print(json.dumps({"schema": "deploy/entity-smoke-alignment-fixture/v1", "verdict": "passed", "negative_cases": len(negatives), "provider_observation": False, "checks": ["private-reference-projection", "actual-engine-boundary", "dependency-incarnation-binding", "no-provider-mutation"]}))
