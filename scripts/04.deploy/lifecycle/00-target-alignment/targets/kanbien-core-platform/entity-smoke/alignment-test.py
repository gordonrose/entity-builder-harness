#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.target-alignment
#   version: 4
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-26"
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
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

if not __debug__: raise SystemExit("ENTITY_SMOKE_ALIGNMENT_ASSERTIONS_DISABLED")
SPEC = importlib.util.spec_from_file_location("entity_smoke_alignment_test", Path(__file__).with_name("script.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
CANARY = "credential-row-provider-canary"
VPC, GROUP = "vpc-" + "1" * 17, "sg-" + "2" * 17
SECRET = "arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien-core-platform-persistence-migration-aBc123"
RECEIPT = {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64, "receipt_reference": "github-actions-run:123"}


# Exercise the actual read-only CLI binding, not a substituted alignment provider.
expected_argv = ["aws", "sts", "get-caller-identity", "--profile", "kanbien-dev", "--region", "eu-west-1", "--output", "json",
                 "--cli-connect-timeout", "5", "--cli-read-timeout", "20", "--no-cli-pager", "--no-paginate", "--cli-input-json", "{}"]
expected_options = {"cwd": M.ROOT, "capture_output": True, "text": True, "timeout": 30,
                    "env": {**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "1", "PYTHONDONTWRITEBYTECODE": "1"}}
for stdout in ('{}', '', ' \n', '[]', 'null', CANARY):
    with patch.object(M.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=stdout, stderr="")) as call:
        if stdout == '{}': assert M.aws("sts", "get-caller-identity") == {}
        else:
            try: M.aws("sts", "get-caller-identity")
            except M.AlignmentFailure as failure: assert failure.code == "alignment-provider-observation-invalid"
            else: raise AssertionError("alignment requires a JSON object, including for empty responses")
        call.assert_called_once_with(expected_argv, **expected_options)
for value, code in [(SimpleNamespace(returncode=254, stdout='', stderr=CANARY), "alignment-command-not-confirmed"),
                    (SimpleNamespace(returncode=254, stdout='', stderr='An error occurred (ExpiredToken) when calling the GetCallerIdentity operation: '+CANARY), "aws-credentials-expired"),
                    (SimpleNamespace(returncode=254, stdout='', stderr='An error occurred (ExpiredTokenException) when calling the GetCallerIdentity operation: '+CANARY), "aws-credentials-expired"),
                    (SimpleNamespace(returncode=254, stdout='', stderr='An error occurred (AccessDenied) when calling the GetCallerIdentity operation: '+CANARY), "aws-access-denied"),
                    (OSError(CANARY), "alignment-command-unavailable"),
                    (UnicodeDecodeError('utf8', b'\xff', 0, 1, CANARY), "alignment-command-unavailable"),
                    (subprocess.TimeoutExpired(expected_argv, 30), "alignment-command-unavailable"),
                    (subprocess.SubprocessError(CANARY), "alignment-command-unavailable")]:
    with patch.object(M.subprocess, "run", **({"side_effect": value} if isinstance(value, Exception) else {"return_value": value})) as call:
        try: M.aws("sts", "get-caller-identity")
        except M.AlignmentFailure as failure:
            assert failure.code == code and CANARY not in str(failure)
        else: raise AssertionError("alignment CLI failure must retain its original finite code")
        call.assert_called_once_with(expected_argv, **expected_options)
with patch.object(M.subprocess, "run") as call:
    try: M.aws("ecs", "run-task")
    except M.AlignmentFailure as failure: assert failure.code == "alignment-provider-operation-prohibited"
    else: raise AssertionError("shared invocation does not grant mutation authority")
    call.assert_not_called()


def fixture():
    outputs = {"VpcId": VPC, "PrivateSubnetIds": "subnet-" + "3" * 17, "ClusterArn": "arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-core-platform", "LogGroupName": "/aws/ecs/kanbien-core-platform", "ServiceDiscoveryArn": "arn:aws:servicediscovery:eu-west-1:337159794548:service/srv-abc123"}
    as_outputs = lambda values: [{"OutputKey": key, "OutputValue": value} for key, value in values.items()]
    data = {
        "identity": {"Account": M.ACCOUNT, "Arn": "arn:aws:sts::337159794548:assumed-role/ApprovedInspection/session"},
        "foundation": {"Stacks": [{"StackStatus": "UPDATE_COMPLETE", "Outputs": as_outputs(outputs), "Parameters": [{"ParameterKey": "ExistingRepositoryArn", "ParameterValue": "arn:aws:ecr:eu-west-1:337159794548:repository/kanbien-core-platform/core-server"}]}]},
        "dependency_stack": {"Stacks": [{"StackStatus": "UPDATE_COMPLETE", "Outputs": as_outputs({"PersistenceDatabaseIdentifier": M.DATABASE, "PersistenceDatabaseEndpoint": "private-provider-canary.internal", "AdministratorCredentialsSecretArn": SECRET, "MigrationCredentialsSecretArn": SECRET})}]},
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
        "manifest": {"images": [{"imageId": {"imageDigest": RECEIPT["image_digest"]}, "imageManifest": json.dumps({"mediaType": "application/vnd.oci.image.manifest.v1+json"})}]},
        "scan": {"repositoryName": M.REPOSITORY, "imageId": {"imageDigest": RECEIPT["image_digest"]}, "imageScanStatus": {"status": "COMPLETE"}, "imageScanFindings": {"findingSeverityCounts": {"LOW": 2}}},
        "budget": {"Budget": {"BudgetName": "kanbien-core-platform-monthly", "BudgetType": "COST", "TimeUnit": "MONTHLY", "BudgetLimit": {"Amount": "100.0", "Unit": "USD"}, "CostFilters": {"TagKeyValue": ["user:Target$kanbien-core-platform"]}}},
    }
    image_read = {"Effect": "Allow", "Principal": "*", "Action": ["ecr:BatchCheckLayerAvailability", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
                  "Resource": ["arn:aws:ecr:eu-west-1:337159794548:repository/kanbien-core-platform/" + name for name in ("core-server", "entity-smoke")]}
    for endpoint in data["endpoints"]["VpcEndpoints"]:
        if endpoint["ServiceName"].endswith((".ecr.api", ".ecr.dkr")):
            rows = [copy.deepcopy(image_read)]
            if endpoint["ServiceName"].endswith(".ecr.api"):
                rows.append({"Effect": "Allow", "Principal": "*", "Action": "ecr:GetAuthorizationToken", "Resource": "*"})
            endpoint["PolicyDocument"] = {"Version": "2012-10-17", "Statement": rows}
    calls = []
    def provider(service, operation, **parameters):
        calls.append((service, operation, parameters))
        assert (service, operation) in M.READS
        key = {"get-caller-identity": "identity", "describe-vpcs": "vpc", "describe-subnets": "subnets", "get-service": "service", "get-namespace": "namespace", "get-hosted-zone": "zone", "describe-vpc-endpoints": "endpoints", "describe-managed-prefix-lists": "prefix", "describe-db-instances": "database", "describe-secret": "secret", "describe-db-parameters": "ssl", "describe-repositories": "repository", "describe-images": "image", "describe-image-scan-findings": "scan", "describe-budget": "budget"}.get(operation)
        if operation == "describe-stacks": key = "foundation" if parameters["StackName"] == "kanbien-core-platform-foundation" else "dependency_stack"
        if operation == "batch-get-image": key = "manifest"
        assert key in data
        return copy.deepcopy(data[key])
    return data, calls, provider


def observed(data_provider):
    return M.inspect(data_provider, RECEIPT, "2026-11-08T13:00:00+00:00")


data, calls, provider = fixture()
with patch.object(M.FOUNDATION_CHECKS, "private_endpoints", wraps=M.FOUNDATION_CHECKS.private_endpoints) as shared, patch.object(M.FOUNDATION_CHECKS, "s3_prefix_list", wraps=M.FOUNDATION_CHECKS.s3_prefix_list) as prefix:
    safe, parameters, group = observed(provider)
    shared.assert_called_once_with(provider, VPC, {"com.amazonaws." + M.REGION + "." + name for name in ("ecr.api", "ecr.dkr", "logs", "secretsmanager")})
    prefix.assert_called_once_with(provider, M.REGION)
assert (parameters["EndpointSecurityGroupId"], parameters["S3ArtifactPrefixListId"]) == (GROUP, "pl-abc123")
assert safe["verdict"] == "aligned" and safe["provider_mutation"] is False and safe["acceptance_evidence"] is False
assert safe["parameters_sha256"] == M.fingerprint(parameters)
assert parameters["ServerDesiredCount"] == "0" and parameters["AdministratorSecretArn"] == SECRET
assert all(marker not in json.dumps(safe) for marker in (CANARY, "private-provider-canary.internal", SECRET))
original_incarnation = safe["dependency_incarnation_sha256"]
for version in ("18.4", "18.12", "18.4-rds.20261116"):
    changed, _, changed_provider = fixture()
    changed["database"]["DBInstances"][0]["EngineVersion"] = version
    report, _, _ = observed(changed_provider)
    assert report["engine_version"] == version, "report actual observation, not the qualification baseline"
with patch.object(M.FOUNDATION_CHECKS, "private_network", side_effect=M.FOUNDATION_CHECKS.FoundationFailure("foundation-vpc-mismatch")) as shared:
    try: observed(provider)
    except M.AlignmentFailure as failure: assert failure.code == "foundation-vpc-mismatch"
    else: raise AssertionError("alignment must use shared private-network checking")
    assert shared.call_count == 1
assert [(operation, arguments["repositoryName"]) for service, operation, arguments in calls if operation in ("batch-get-image", "describe-image-scan-findings")] == [("batch-get-image", M.REPOSITORY), ("describe-image-scan-findings", M.REPOSITORY)]
assert next(arguments for _, operation, arguments in calls if operation == "batch-get-image")["imageIds"] == [{"imageDigest": RECEIPT["image_digest"]}]
assert next(arguments for _, operation, arguments in calls if operation == "describe-image-scan-findings")["imageId"] == {"imageDigest": RECEIPT["image_digest"]}
with patch.object(M.IMAGE_CHECKS, "check_image", side_effect=M.IMAGE_CHECKS.ScanFailure("ecr-scan-identity-mismatch")) as shared:
    try: observed(provider)
    except M.AlignmentFailure as failure: assert failure.code == "ecr-scan-identity-mismatch"
    else: raise AssertionError("alignment must consume the shared image check")
    shared.assert_called_once_with(provider, M.REPOSITORY, RECEIPT["image_digest"])
data["database"]["DBInstances"][0]["DbiResourceId"] = "db-ZYXWVUTSRQPONMLK"
assert observed(provider)[0]["dependency_incarnation_sha256"] != original_incarnation
negatives = [
    (lambda d: d['database']['DBInstances'][0].update(DBName='other_valid_database'), 'alignment-dependency-name-not-confirmed'),
    (lambda d: d['database']['DBInstances'][0].update(DBName=None), 'alignment-dependency-incarnation-invalid'),
    (lambda d: d['database']['DBInstances'][0].update(Engine='mysql'), 'alignment-engine-not-confirmed'),
    (lambda d: d['secret'].update(Name='other-secret'), 'alignment-administrative-reference-not-confirmed'),
    (lambda d: d["foundation"]["Stacks"][0].pop("Parameters"), "alignment-foundation-parameters-not-confirmed"),
    (lambda d: d["foundation"]["Stacks"][0]["Parameters"].append(copy.deepcopy(d["foundation"]["Stacks"][0]["Parameters"][0])), "alignment-foundation-parameters-not-confirmed"),
    (lambda d: d["foundation"]["Stacks"][0].update(Parameters=[]), "preparation-inputs-endpoint-policy-reference-missing"),
    (lambda d: d["foundation"]["Stacks"][0]["Parameters"][0].update(ParameterValue=CANARY), "preparation-inputs-endpoint-policy-parameter-mismatch"),
    (lambda d: d["dependency_stack"]["Stacks"][0]["Outputs"][-1].update(OutputValue=CANARY), "preparation-inputs-endpoint-policy-output-mismatch"),
    (lambda d: d["dependency_stack"]["Stacks"][0]["Outputs"].pop(), "preparation-inputs-endpoint-policy-reference-missing"),
    (lambda d: d["identity"].update(Account="123456789012"), "alignment-account-not-confirmed"),
    (lambda d: d["foundation"]["Stacks"][0].update(StackStatus="UPDATE_IN_PROGRESS"), "foundation-stack-not-ready"),
    (lambda d: d["subnets"]["Subnets"][0].update(MapPublicIpOnLaunch=True), "foundation-subnet-not-private"),
    (lambda d: d["namespace"]["Namespace"].update(Type="DNS_PUBLIC"), "foundation-namespace-not-private"),
    (lambda d: d["zone"]["HostedZone"]["Config"].update(PrivateZone=False), "foundation-zone-not-private"),
    (lambda d: d["endpoints"]["VpcEndpoints"].pop(), "foundation-endpoint-missing"),
    (lambda d: d["endpoints"]["VpcEndpoints"][-1].update(PolicyDocument={"Statement": []}), "alignment-secret-delivery-policy-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0].update(EngineVersion="16.9"), "postgresql-version-major-incompatible"),
    (lambda d: d["database"]["DBInstances"][0].update(EngineVersion="18.4canary"), "postgresql-version-observation-invalid"),
    (lambda d: d["database"]["DBInstances"][0].update(StorageEncrypted=False), "alignment-dependency-security-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0].update(PubliclyAccessible=True), "alignment-dependency-security-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0].update(IAMDatabaseAuthenticationEnabled=False), "alignment-dependency-security-not-confirmed"),
    (lambda d: d["database"]["DBInstances"][0]["DBSubnetGroup"].update(VpcId="vpc-other"), "alignment-dependency-vpc-mismatch"),
    (lambda d: d["secret"].update(DeletedDate="2026-11-01"), "alignment-administrative-reference-not-confirmed"),
    (lambda d: d["ssl"]["Parameters"][0].update(ParameterValue="0"), "alignment-verified-tls-posture-not-confirmed"),
    (lambda d: d["ssl"].update(Marker="repeated-marker"), "alignment-parameter-observation-incomplete"),
    (lambda d: d["repository"]["repositories"][0].update(imageTagMutability="MUTABLE"), "alignment-immutable-repository-not-confirmed"),
    (lambda d: d["image"]["imageDetails"][0].update(imageDigest="sha256:" + "c" * 64), "alignment-qualified-image-not-observed"),
    (lambda d: d["scan"]["imageScanFindings"]["findingSeverityCounts"].update(HIGH=1), "ecr-scan-blocked-severity"),
    (lambda d: d["scan"].update(repositoryName=CANARY), "ecr-scan-identity-mismatch"),
    (lambda d: d["scan"]["imageScanStatus"].update(status="IN_PROGRESS"), "ecr-scan-not-complete"),
    (lambda d: d["manifest"]["images"][0]["imageId"].update(imageDigest="sha256:" + "c" * 64), "ecr-manifest-identity-mismatch"),
    (lambda d: d["budget"]["Budget"]["CostFilters"].update(TagKeyValue=[]), "foundation-budget-configuration-invalid"),
    (lambda d: d["budget"]["Budget"].pop("BudgetName"), "foundation-budget-configuration-invalid"),
    (lambda d: d["budget"]["Budget"].update(TimeUnit="ANNUALLY"), "foundation-budget-configuration-invalid"),
]
for mutate, code in negatives:
    data, _, provider = fixture(); mutate(data)
    try: observed(provider)
    except M.AlignmentFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected alignment rejection")
for owner, reason, last_call in [("private_endpoints", "foundation-endpoint-group-invalid", "get-hosted-zone"), ("s3_prefix_list", "foundation-s3-prefix-missing", "describe-vpc-endpoints"), ("endpoint_policy", "alignment-ecr-api-policy-not-confirmed", "describe-vpc-endpoints")]:
    data, calls, provider = fixture()
    with patch.object(M.FOUNDATION_CHECKS, owner, side_effect=M.FOUNDATION_CHECKS.FoundationFailure(reason)):
        try: observed(provider)
        except M.AlignmentFailure as failure: assert failure.code == reason
        else: raise AssertionError("shared endpoint failure must stop alignment")
    assert calls[-1][1] == last_call
for operation in ("describe-vpc-endpoints", "describe-managed-prefix-lists"):
    data, calls, provider = fixture(); failure = M.AlignmentFailure("alignment-command-not-confirmed")
    def denied(service, action, **parameters):
        if action == operation:
            calls.append((service, action, parameters)); raise failure
        return provider(service, action, **parameters)
    try: observed(denied)
    except M.AlignmentFailure as caught: assert caught is failure
    else: raise AssertionError("provider failure must be preserved")
    assert calls[-1][1] == operation

# Actual alignment consumes changed resolved budget settings and the shared check.
data, calls, provider = fixture()
expected_budget = copy.deepcopy(M.INPUTS['budget'])
expected_budget.update(BudgetName='another-monthly')
expected_budget['BudgetLimit'] = {'Amount':250, 'Unit':'EUR'}
expected_budget['CostFilters'] = {'TagKeyValue':['user:Target$another']}
data['budget']['Budget'] = copy.deepcopy(expected_budget)
with patch.dict(M.INPUTS, budget=expected_budget):
    observed(provider)
    assert calls[-1][2]['BudgetName'] == 'another-monthly'
    with patch.object(M.FOUNDATION_CHECKS, 'budget', side_effect=M.FOUNDATION_CHECKS.FoundationFailure('foundation-budget-configuration-mismatch')) as shared:
        try: observed(provider)
        except M.AlignmentFailure as failure: assert failure.code == 'foundation-budget-configuration-mismatch'
        else: raise AssertionError('alignment must use shared budget validation')
        shared.assert_called_once_with(data['budget']['Budget'], expected_budget)

# Changed resolved settings reach the full alignment path, not just database_facts.
data, calls, provider = fixture()
new_name = 'another/admin.secret+name'
new_secret = SECRET.replace('kanbien-core-platform-persistence-migration', new_name)
data['database']['DBInstances'][0]['DBName'] = 'another_database'
data['secret'].update(ARN=new_secret, Name=new_name)
for row in data['dependency_stack']['Stacks'][0]['Outputs']:
    if row['OutputValue'] == SECRET: row['OutputValue'] = new_secret
data['endpoints']['VpcEndpoints'][-1]['PolicyDocument'] = data['endpoints']['VpcEndpoints'][-1]['PolicyDocument'].replace(SECRET, new_secret)
with patch.dict(M.DATABASE_BINDING, database_name='another_database', administrator_secret_name=new_name):
    safe, parameters, _ = observed(provider)
    assert parameters['DatabaseName'] == 'another_database' and parameters['AdministratorSecretArn'] == new_secret
    assert new_secret not in json.dumps(safe) and new_name not in json.dumps(safe)
    data['secret']['Name'] = 'kanbien-core-platform-persistence-migration'
    try: observed(provider)
    except M.AlignmentFailure as failure: assert failure.code == 'alignment-administrative-reference-not-confirmed'
    else: raise AssertionError('secret metadata must match the declared name')

# Project changed declarations through the same owner and real alignment caller.
document = M.INPUT_OWNER.CF.template((M.ROOT / M.FOUNDATION).read_text())
extra = ["arn:aws:ecr:" + M.REGION + ":" + M.ACCOUNT + ":repository/another/" + name for name in ("one", "two")]
for resource in document["Resources"].values():
    if resource.get("Type") == "AWS::EC2::VPCEndpoint":
        for row in resource["Properties"]["PolicyDocument"]["Statement"]:
            if isinstance(row["Resource"], list): row["Resource"].extend(extra)
declared = M.INPUT_OWNER.endpoint_policies(document, M.ACCOUNT, M.REGION)
with patch.dict(M.INPUTS, {"foundation_endpoint_policies": declared}):
    data, calls, provider = fixture()
    for endpoint in data["endpoints"]["VpcEndpoints"][:2]:
        endpoint["PolicyDocument"]["Statement"][0]["Resource"].extend(extra)
    assert observed(provider)[0]["verdict"] == "aligned"
    for mutation in ("missing", "extra", "unsafe-source", "selected-repository-absent"):
        changed = copy.deepcopy(data); inputs = copy.deepcopy(declared)
        if mutation == "missing": changed["endpoints"]["VpcEndpoints"][0]["PolicyDocument"]["Statement"][0]["Resource"].pop()
        elif mutation == "extra": changed["endpoints"]["VpcEndpoints"][0]["PolicyDocument"]["Statement"][0]["Resource"].append(extra[0] + "-other")
        else:
            replacements = ["*"] if mutation == "unsafe-source" else extra
            for policy in inputs.values():
                for row in policy["Statement"]:
                    if row["Action"] != "ecr:GetAuthorizationToken": row["Resource"] = replacements
            for endpoint in changed["endpoints"]["VpcEndpoints"][:2]: endpoint["PolicyDocument"]["Statement"][0]["Resource"] = replacements
        original = copy.deepcopy(data); data.clear(); data.update(changed)
        with patch.dict(M.INPUTS, {"foundation_endpoint_policies": inputs}):
            try: observed(provider)
            except M.AlignmentFailure as failure: assert failure.code == "alignment-ecr-api-policy-not-confirmed"
            else: raise AssertionError(mutation)
        data.clear(); data.update(original)
try: M.aws("ecs", "run-task", cluster=CANARY)
except M.AlignmentFailure as failure: assert failure.code == "alignment-provider-operation-prohibited"
else: raise AssertionError("read-only adapter must reject task launch")

for index in (0, 1):
    for mutation in ("old-repository-only", "missing-action", "wildcard-action", "wildcard-resource", "unknown-condition", "wrong-principal", "missing-policy", "malformed-json", "duplicate-json-key", "wrong-type", "duplicate-resource"):
        data, calls, provider = fixture()
        endpoint = data["endpoints"]["VpcEndpoints"][index]
        row = endpoint["PolicyDocument"]["Statement"][0]
        if mutation == "old-repository-only": row["Resource"] = row["Resource"][0]
        if mutation == "missing-action": row["Action"].remove("ecr:BatchGetImage")
        if mutation == "wildcard-action": row["Action"] = "ecr:*"
        if mutation == "wildcard-resource": row["Resource"] = "*"
        if mutation == "unknown-condition": row["Condition"] = {"fixture": CANARY}
        if mutation == "wrong-principal": row["Principal"] = CANARY
        if mutation == "missing-policy": endpoint.pop("PolicyDocument")
        if mutation == "malformed-json": endpoint["PolicyDocument"] = CANARY
        if mutation == "duplicate-json-key": endpoint["PolicyDocument"] = '{"Version":"2012-10-17","Statement":[],"Statement":[]}'
        if mutation == "wrong-type": row["Resource"] = [False]
        if mutation == "duplicate-resource": row["Resource"].append(row["Resource"][0])
        try: observed(provider)
        except M.AlignmentFailure as failure:
            assert failure.code == ("alignment-ecr-api-policy-not-confirmed" if index == 0 else "alignment-ecr-registry-policy-not-confirmed"), (mutation, failure.code)
            assert CANARY not in str(failure)
        else: raise AssertionError("the private image route must be checked before launch")
        assert not any(operation in {"describe-images", "run-task"} for _, operation, _ in calls)
data, _, provider = fixture()
for endpoint in data["endpoints"]["VpcEndpoints"][:2]:
    rows = endpoint["PolicyDocument"]["Statement"]
    rows.reverse()
    for row in rows:
        for key in ("Action", "Resource"):
            if isinstance(row[key], list): row[key].reverse()
    endpoint["PolicyDocument"] = json.dumps(endpoint["PolicyDocument"])
assert observed(provider)[0]["verdict"] == "aligned", "encoded policies and irrelevant ordering must not change route identity"

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
        assert M.source_checkpoint(custody, controller_revision=source)["controller_revision"] == source
        evidence = str(Path(M.SCOPE).parent.parent / "30-release-evidence")
        write(evidence + "/proof-receipts/entity-smoke-" + "a" * 64 + ".json", "retained proof\n")
        write(evidence + "/release-candidates/release-" + "b" * 24 + ".yml", "retained candidate\n")
        repair = commit("retain generated evidence")
        assert M.source_checkpoint(custody)["controller_revision"] == repair
        M.source_preflight(custody)
        controller_spec = importlib.util.spec_from_file_location("retained_controller_fixture", old_root / M.CONTROLLER_DIRECTORY / "orchestration/commands/script.py")
        controller = importlib.util.module_from_spec(controller_spec); controller_spec.loader.exec_module(controller)
        with patch.object(controller, "ROOT", M.ROOT), patch.object(controller, "ALIGN", M), \
             patch.object(controller, "source_paths", lambda revision=None: [M.ROOT / controller_path]):
            original_digest = controller.historical_source_digest(source)
            assert original_digest == controller.DEPLOY.fingerprint({controller_path: "sha256:" + hashlib.sha256(b"original controller\n").hexdigest()})
            current_digest = controller.source_digest()
            packet = {"binding": {"source_revision": source}, "plan": {"controller_sha256": original_digest}}
            assert controller.retained_controller(packet, current_digest) == original_digest
            packet["plan"]["controller_sha256"] = "sha256:" + "0" * 64
            try: controller.retained_controller(packet, current_digest)
            except controller.InfrastructureFailure as failure: assert failure.code == "task-step-completion-artifacts-mismatch"
            else: raise AssertionError("unknown historical controller admitted")
        moved_controller = M.CONTROLLER_DIRECTORY + "orchestration/commands/script.py"
        (M.ROOT / moved_controller).parent.mkdir(parents=True)
        git("mv", controller_path, moved_controller)
        moved = commit("approved controller-only path relocation")
        assert M.source_checkpoint(custody) == {"package_source_revision": source, "controller_revision": moved}
        M.source_preflight(custody)
        with patch.object(controller, "ROOT", M.ROOT), patch.object(controller, "ALIGN", M), \
             patch.object(controller, "source_paths", lambda revision=None: [M.ROOT / (controller_path if revision else moved_controller)]):
            controller.historical_source_digest.cache_clear()
            assert controller.historical_source_digest(source) == original_digest
            assert controller.retained_controller({"binding": {"source_revision": source}, "plan": {"controller_sha256": original_digest}}, controller.source_digest()) == original_digest
        git("revert", "--no-edit", "HEAD")
        # Deletion alone, ambiguous destinations and replacement of an already
        # existing nested file are not evidence of a controller relocation.
        for destinations in ((), ("orchestration/commands/script.py", "orchestration/implementation/script.py"),
                             ("orchestration/commands/different-name.py",)):
            (M.ROOT / controller_path).unlink()
            for destination in destinations: write(M.CONTROLLER_DIRECTORY + destination, "controller replacement\n")
            commit("unpaired or ambiguous controller deletion")
            rejected_source(lambda: M.source_checkpoint(custody))
            git("revert", "--no-edit", "HEAD")
        write(moved_controller, "existing nested controller\n")
        nested_source = commit("nested controller already exists")
        (M.ROOT / controller_path).unlink()
        commit("deletion cannot borrow an existing destination")
        rejected_source(lambda: M.source_checkpoint({**custody, "source_revision": nested_source}))
        git("revert", "--no-edit", "HEAD")
        (M.ROOT / moved_controller).unlink()
        commit("remove fixture-only existing nested controller")
        M.source_preflight(custody)
        for path in ("scripts/04.deploy/shared/provider-adapters/aws/response.py", "scripts/04.deploy/shared/provider-adapters/aws/cli.py", "scripts/04.deploy/shared/provider-adapters/aws/tasks.py", "scripts/04.deploy/shared/provider-adapters/aws/resource_reservation.py", "scripts/04.deploy/shared/provider-adapters/aws/snapshots.py", "scripts/04.deploy/shared/provider-adapters/aws/change_sets.py", "scripts/04.deploy/shared/provider-adapters/aws/recovery-test.py", "scripts/04.deploy/lifecycle/60-run/release-succession/script.py", "scripts/04.deploy/lifecycle/60-run/release-succession/proof-policy.py"):
            write(path, "checked controller response correction\n")
            rejected_source(lambda: M.source_preflight(custody), "alignment-committed-source-required")
            repair = commit("shared response controller-only correction")
            assert M.source_checkpoint(custody) == {"package_source_revision": source, "controller_revision": repair}
            M.source_preflight(custody)
        for path in (
            "scripts/04.deploy/shared/provider-adapters/aws/foreign-adapter.py",
            "apps/entity-smoke/fixture.ts", "packages/core/src/shared/index.ts", "package-lock.json",
            "platform/runtime/fixture.ts", "platform/security/fixture.ts",
            "infra/04.deploy/03.product/image/entity-smoke/Dockerfile",
            "infra/04.deploy/03.product/image/entity-smoke/Dockerfile.dockerignore",
            "scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/script.sh",
            ".github/workflows/publish-kanbien-core-platform-entity-smoke.yml",
            M.TARGET + "/30-provider-realization/aws/cloudformation/entity-smoke.yml",
            M.SCOPE, M.CONTROLLER_DIRECTORY + "nested/not-an-admitted-controller.py",
            M.CONTROLLER_DIRECTORY + "orchestration/commands/nested/not-admitted.py",
            M.CONTROLLER_DIRECTORY + "bindings/local-qualification/entity-smoke-proof/binding.py",
            M.CONTROLLER_DIRECTORY + "administrator-recovery/implementation/administrator-recovery.js",
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

# The registered alignment unit also exercises the bounded shared-endpoint
# repair that must succeed before a real image-delivery alignment can pass.
repair_spec = importlib.util.spec_from_file_location("entity_image_repair_regression", M.ROOT / M.CONTROLLER_DIRECTORY / "image-delivery-repair/tests/image-delivery-repair-test.py")
repair_fixture = importlib.util.module_from_spec(repair_spec)
repair_spec.loader.exec_module(repair_fixture)

print(json.dumps({"schema": "deploy/entity-smoke-alignment-fixture/v1", "verdict": "passed", "negative_cases": len(negatives) + 22, "private_image_policy_negative_cases": 22, "provider_observation": False, "checks": ["private-reference-projection", "actual-engine-boundary", "dependency-incarnation-binding", "no-provider-mutation", "real-git-controller-only-checkpoint", "approved-controller-relocation-retains-historical-digest", "unpaired-ambiguous-and-existing-destination-deletion-rejected", "image-template-runtime-and-custody-input-changes-rejected", "rename-symlink-dirty-untracked-and-nonancestor-rejected"]}))
