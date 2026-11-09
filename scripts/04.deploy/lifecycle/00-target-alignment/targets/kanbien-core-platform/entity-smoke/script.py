#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.target-alignment.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind safe fresh alignment to exact source, immutable custody and the existing dependency incarnation without granting execution authority.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.entity-smoke.target-alignment
#     path: scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/script.sh
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[7]
TARGET = "infra/04.deploy/03.product/targets/kanbien-core-platform"
SCOPE = TARGET + "/20-scopes/entity-smoke/00-declaration/declaration-contract.yml"
ACCOUNT, REGION, PROFILE = "337159794548", "eu-west-1", "kanbien-dev"
DATABASE = "kanbien-core-platform-persistence"
REPOSITORY = "kanbien-core-platform/entity-smoke"
REPOSITORY_URI = ACCOUNT + ".dkr.ecr." + REGION + ".amazonaws.com/" + REPOSITORY
READS = {
    ("sts", "get-caller-identity"), ("cloudformation", "describe-stacks"),
    ("ec2", "describe-vpcs"), ("ec2", "describe-subnets"), ("ec2", "describe-vpc-endpoints"),
    ("ec2", "describe-managed-prefix-lists"), ("servicediscovery", "get-service"),
    ("servicediscovery", "get-namespace"), ("route53", "get-hosted-zone"),
    ("rds", "describe-db-instances"), ("rds", "describe-db-parameters"),
    ("ecr", "describe-repositories"), ("ecr", "describe-images"), ("ecr", "describe-image-scan-findings"),
    ("budgets", "describe-budget"),
    ("secretsmanager", "describe-secret"),
}


class AlignmentFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(allowed, code):
    if not allowed: raise AlignmentFailure(code)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def fingerprint(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def command(arguments, timeout=30):
    try:
        result = subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                                env={**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    except (OSError, UnicodeError, subprocess.SubprocessError): raise AlignmentFailure("alignment-command-unavailable") from None
    require(result.returncode == 0, "alignment-command-not-confirmed")
    return result.stdout


def aws(service, operation, **parameters):
    require((service, operation) in READS, "alignment-provider-operation-prohibited")
    arguments = ["aws", service, operation, "--profile", PROFILE, "--region", REGION, "--output", "json",
                 "--cli-connect-timeout", "5", "--cli-read-timeout", "20", "--no-cli-pager", "--no-paginate", "--cli-input-json", json.dumps(parameters)]
    try: value = json.loads(command(arguments))
    except (ValueError, TypeError): raise AlignmentFailure("alignment-provider-observation-invalid") from None
    require(isinstance(value, dict), "alignment-provider-observation-invalid")
    return value


def only(response, field):
    values = response.get(field) if isinstance(response, dict) else None
    require(isinstance(values, list) and len(values) == 1 and isinstance(values[0], dict), "alignment-provider-observation-invalid")
    return values[0]


def read_receipt(path):
    require(path.is_absolute() and not path.is_symlink() and not any(part.is_symlink() for part in path.parents), "alignment-receipt-path-invalid")
    try:
        with path.open("rb") as stream: raw = stream.read(65537)
        require(len(raw) <= 65536, "alignment-receipt-invalid")
        value = json.loads(raw)
        owner = module("entity_smoke_alignment_custody", ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py")
        owner.validate(value, argparse.Namespace(expected_target="kanbien-core-platform", expected_candidate="kanbien-entity-smoke-candidate", expected_package_contract="kanbien-entity-smoke-image", expected_program="kanbien-entity-smoke"))
    except AlignmentFailure: raise
    except Exception: raise AlignmentFailure("alignment-qualified-custody-not-confirmed") from None
    require(value["provider_region_alias"] == "aws-eu-west-1", "alignment-custody-region-mismatch")
    return value


def source_preflight(receipt):
    require(command(["git", "rev-parse", "HEAD"]).strip() == receipt["source_revision"], "alignment-source-checkpoint-mismatch")
    require(not command(["git", "status", "--porcelain", "--untracked-files=all", "--", ".", ":!commitLogs"]).strip(), "alignment-committed-source-required")
    coverage = json.loads(command(["bash", "scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh", "--scope-contract", SCOPE, "--json"], 60))
    require(coverage.get("verdict") == "covered" and coverage.get("findings") == [], "alignment-declaration-coverage-not-confirmed")
    inventory = json.loads(command(["python3", "-B", "scripts/04.deploy/inventory-deploy-control/script.py", "--delivery", "--check", "--json"], 60))
    require(inventory.get("verdict") == "covered" and inventory.get("findings") == [], "alignment-delivery-coverage-not-confirmed")


def database_facts(database, administrator_secret):
    require(database.get("DBInstanceIdentifier") == DATABASE and database.get("DBInstanceStatus") == "available", "alignment-dependency-not-available")
    require(database.get("Engine") == "postgres" and database.get("EngineVersion") == "18.3", "alignment-engine-not-confirmed")
    require(database.get("StorageEncrypted") is True and database.get("PubliclyAccessible") is False and database.get("IAMDatabaseAuthenticationEnabled") is True, "alignment-dependency-security-not-confirmed")
    incarnation, name = database.get("DbiResourceId"), database.get("DBName")
    require(isinstance(incarnation, str) and re.fullmatch(r"db-[A-Za-z0-9]+", incarnation) is not None and isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,62}", name) is not None, "alignment-dependency-incarnation-invalid")
    groups = database.get("VpcSecurityGroups")
    require(isinstance(groups, list) and len(groups) == 1 and groups[0].get("Status") == "active" and isinstance(groups[0].get("VpcSecurityGroupId"), str), "alignment-dependency-network-not-confirmed")
    subnet = database.get("DBSubnetGroup")
    require(isinstance(subnet, dict) and subnet.get("SubnetGroupStatus") == "Complete" and isinstance(subnet.get("DBSubnetGroupName"), str), "alignment-dependency-network-not-confirmed")
    require(isinstance(administrator_secret, str) and re.fullmatch("arn:aws:secretsmanager:" + REGION + ":" + ACCOUNT + r":secret:kanbien-core-platform-persistence-migration-[A-Za-z0-9]{6}", administrator_secret) is not None, "alignment-administrative-reference-not-confirmed")
    parameters = database.get("DBParameterGroups")
    require(isinstance(parameters, list) and len(parameters) == 1 and parameters[0].get("ParameterApplyStatus") == "in-sync", "alignment-dependency-parameters-not-confirmed")
    endpoint = database.get("Endpoint")
    require(isinstance(endpoint, dict) and isinstance(endpoint.get("Address"), str) and endpoint.get("Port") == 5432, "alignment-dependency-route-not-confirmed")
    return {"DatabaseEndpoint": endpoint["Address"], "DatabaseName": name, "DatabaseResourceId": incarnation,
            "DatabaseSecurityGroupId": groups[0]["VpcSecurityGroupId"], "AdministratorSecretArn": administrator_secret,
            "database_subnet_group": subnet["DBSubnetGroupName"], "database_vpc": subnet.get("VpcId"),
            "parameter_group": parameters[0].get("DBParameterGroupName")}


def inspect(provider, receipt, now):
    caller = provider("sts", "get-caller-identity")
    require(caller.get("Account") == ACCOUNT and isinstance(caller.get("Arn"), str) and caller["Arn"].startswith("arn:aws:sts::" + ACCOUNT + ":assumed-role/"), "alignment-account-not-confirmed")
    foundation = only(provider("cloudformation", "describe-stacks", StackName="kanbien-core-platform-foundation"), "Stacks")
    require(foundation.get("StackStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}, "alignment-foundation-not-ready")
    output_items = foundation.get("Outputs")
    require(isinstance(output_items, list) and all(isinstance(item, dict) and isinstance(item.get("OutputKey"), str) and isinstance(item.get("OutputValue"), str) for item in output_items), "alignment-foundation-observation-invalid")
    outputs = {item["OutputKey"]: item["OutputValue"] for item in output_items}
    require(len(outputs) == len(output_items) and {"VpcId", "PrivateSubnetIds", "ClusterArn", "LogGroupName", "ServiceDiscoveryArn"} <= set(outputs), "alignment-foundation-observation-invalid")
    require(outputs["ClusterArn"] == "arn:aws:ecs:" + REGION + ":" + ACCOUNT + ":cluster/kanbien-core-platform" and outputs["LogGroupName"] == "/aws/ecs/kanbien-core-platform", "alignment-target-boundary-not-confirmed")
    vpc = only(provider("ec2", "describe-vpcs", VpcIds=[outputs["VpcId"]]), "Vpcs")
    require(vpc.get("VpcId") == outputs["VpcId"] and vpc.get("State") == "available", "alignment-vpc-not-confirmed")
    subnets = outputs["PrivateSubnetIds"].split(",")
    response = provider("ec2", "describe-subnets", SubnetIds=subnets)
    actual = response.get("Subnets")
    require(isinstance(actual, list) and len(actual) == len(subnets) and {item.get("SubnetId") for item in actual} == set(subnets) and all(item.get("VpcId") == outputs["VpcId"] and item.get("State") == "available" and item.get("MapPublicIpOnLaunch") is False for item in actual), "alignment-private-subnets-not-confirmed")
    service = provider("servicediscovery", "get-service", Id=outputs["ServiceDiscoveryArn"].rsplit("/", 1)[-1]).get("Service")
    namespace = service.get("DnsConfig", {}).get("NamespaceId") if isinstance(service, dict) else None
    require(isinstance(namespace, str) and re.fullmatch(r"ns-[a-z0-9]+", namespace) is not None, "alignment-private-namespace-not-confirmed")
    namespace_facts = provider("servicediscovery", "get-namespace", Id=namespace).get("Namespace")
    require(isinstance(namespace_facts, dict) and namespace_facts.get("Id") == namespace and namespace_facts.get("Name") == "kanbien-core-platform.internal" and namespace_facts.get("Type") == "DNS_PRIVATE", "alignment-private-namespace-not-confirmed")
    zone = namespace_facts.get("Properties", {}).get("DnsProperties", {}).get("HostedZoneId")
    require(isinstance(zone, str) and re.fullmatch(r"[A-Z0-9]+", zone) is not None, "alignment-private-namespace-not-confirmed")
    hosted_zone = provider("route53", "get-hosted-zone", Id=zone)
    require(hosted_zone.get("HostedZone", {}).get("Config", {}).get("PrivateZone") is True and {item.get("VPCId") for item in hosted_zone.get("VPCs", []) if item.get("VPCRegion") == REGION} == {outputs["VpcId"]}, "alignment-private-namespace-vpc-mismatch")
    endpoints = provider("ec2", "describe-vpc-endpoints", Filters=[{"Name": "vpc-id", "Values": [outputs["VpcId"]]}]).get("VpcEndpoints")
    services = {"com.amazonaws." + REGION + "." + suffix for suffix in ("ecr.api", "ecr.dkr", "logs", "secretsmanager")}
    require(isinstance(endpoints, list), "alignment-private-delivery-not-confirmed")
    selected = [item for item in endpoints if item.get("ServiceName") in services]
    require(len(selected) == 4 and {item.get("ServiceName") for item in selected} == services and all(item.get("VpcId") == outputs["VpcId"] and item.get("State") == "available" and item.get("VpcEndpointType") == "Interface" and item.get("PrivateDnsEnabled") is True and isinstance(item.get("Groups"), list) and len(item["Groups"]) == 1 for item in selected), "alignment-private-delivery-not-confirmed")
    groups = {item["Groups"][0].get("GroupId") for item in selected}
    require(len(groups) == 1 and isinstance(next(iter(groups)), str), "alignment-private-delivery-not-confirmed")
    prefix = only(provider("ec2", "describe-managed-prefix-lists", Filters=[{"Name": "prefix-list-name", "Values": ["com.amazonaws." + REGION + ".s3"]}]), "PrefixLists")
    require(isinstance(prefix.get("PrefixListId"), str), "alignment-image-layer-route-not-confirmed")
    database = only(provider("rds", "describe-db-instances", DBInstanceIdentifier=DATABASE), "DBInstances")
    dependency_stack = only(provider("cloudformation", "describe-stacks", StackName="kanbien-core-platform-core-server-persistence"), "Stacks")
    require(dependency_stack.get("StackStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}, "alignment-dependency-stack-not-ready")
    dependency_outputs = {item["OutputKey"]: item["OutputValue"] for item in dependency_stack.get("Outputs", [])}
    require(dependency_outputs.get("PersistenceDatabaseIdentifier") == DATABASE and dependency_outputs.get("PersistenceDatabaseEndpoint") == database.get("Endpoint", {}).get("Address"), "alignment-dependency-ownership-not-confirmed")
    dependency = database_facts(database, dependency_outputs.get("AdministratorCredentialsSecretArn"))
    secret = provider("secretsmanager", "describe-secret", SecretId=dependency["AdministratorSecretArn"])
    require(secret.get("ARN") == dependency["AdministratorSecretArn"] and secret.get("Name") == "kanbien-core-platform-persistence-migration" and not secret.get("DeletedDate"), "alignment-administrative-reference-not-confirmed")
    secrets_endpoint = next(item for item in selected if item["ServiceName"].endswith(".secretsmanager"))
    policy = secrets_endpoint.get("PolicyDocument")
    if isinstance(policy, str): policy = json.loads(policy)
    require(isinstance(policy, dict) and policy.get("Statement") == [{"Effect": "Allow", "Principal": "*", "Action": "secretsmanager:GetSecretValue", "Resource": [dependency["AdministratorSecretArn"]]}], "alignment-secret-delivery-policy-not-confirmed")
    require(dependency["database_vpc"] == outputs["VpcId"], "alignment-dependency-vpc-mismatch")
    ssl = provider("rds", "describe-db-parameters", DBParameterGroupName=dependency["parameter_group"], MaxRecords=100)
    # A filtered AWS CLI projection is insufficient: absence on a partial page
    # cannot establish the force-SSL value. Walk only this selected group.
    parameters, marker = list(ssl.get("Parameters", [])), ssl.get("Marker")
    seen = set()
    for _ in range(20):
        if not marker: break
        require(isinstance(marker, str) and marker not in seen, "alignment-parameter-observation-incomplete")
        seen.add(marker)
        ssl = provider("rds", "describe-db-parameters", DBParameterGroupName=dependency["parameter_group"], MaxRecords=100, Marker=marker)
        parameters.extend(ssl.get("Parameters", [])); marker = ssl.get("Marker")
    require(not marker and [item.get("ParameterValue") for item in parameters if item.get("ParameterName") == "rds.force_ssl"] == ["1"], "alignment-verified-tls-posture-not-confirmed")
    repository = only(provider("ecr", "describe-repositories", repositoryNames=[REPOSITORY]), "repositories")
    require(repository.get("repositoryName") == REPOSITORY and repository.get("repositoryUri") == REPOSITORY_URI and repository.get("imageTagMutability") == "IMMUTABLE" and repository.get("imageScanningConfiguration", {}).get("scanOnPush") is True, "alignment-immutable-repository-not-confirmed")
    image = only(provider("ecr", "describe-images", repositoryName=REPOSITORY, imageIds=[{"imageDigest": receipt["image_digest"]}]), "imageDetails")
    require(image.get("imageDigest") == receipt["image_digest"] and image.get("repositoryName") == REPOSITORY, "alignment-qualified-image-not-observed")
    scan = provider("ecr", "describe-image-scan-findings", repositoryName=REPOSITORY, imageId={"imageDigest": receipt["image_digest"]})
    counts = scan.get("imageScanFindings", {}).get("findingSeverityCounts")
    require(scan.get("imageScanStatus", {}).get("status") == "COMPLETE" and isinstance(counts, dict) and all(type(value) is int and value >= 0 for value in counts.values()) and counts.get("HIGH", 0) == 0 and counts.get("CRITICAL", 0) == 0, "alignment-clean-scan-not-confirmed")
    budget = provider("budgets", "describe-budget", AccountId=ACCOUNT, BudgetName="kanbien-core-platform-monthly").get("Budget")
    require(isinstance(budget, dict) and budget.get("BudgetLimit", {}).get("Unit") == "USD" and str(budget.get("BudgetLimit", {}).get("Amount")) in {"100", "100.0", "100.00"} and budget.get("CostFilters", {}).get("TagKeyValue") == ["user:Target$kanbien-core-platform"], "alignment-target-budget-not-confirmed")
    parameters = {key: dependency[key] for key in ("DatabaseEndpoint", "DatabaseName", "DatabaseResourceId", "DatabaseSecurityGroupId", "AdministratorSecretArn")}
    parameters.update(VpcId=outputs["VpcId"], VpcCidr=vpc["CidrBlock"], PrivateSubnetIds=outputs["PrivateSubnetIds"], ClusterArn=outputs["ClusterArn"], NamespaceId=namespace,
                      EndpointSecurityGroupId=next(iter(groups)), S3ArtifactPrefixListId=prefix["PrefixListId"], LogGroupName=outputs["LogGroupName"],
                      ImageRepositoryUri=REPOSITORY_URI, ImageRepositoryArn="arn:aws:ecr:" + REGION + ":" + ACCOUNT + ":repository/" + REPOSITORY,
                      ImageDigest=receipt["image_digest"], SourceRevision=receipt["source_revision"], ServerDesiredCount="0")
    # Private parameters are consumed in-memory by the future change producer.
    # The retained/public report contains identifiers and fingerprints only.
    safe = {"schema": "deploy/entity-smoke-target-alignment/v1", "target": "kanbien-core-platform", "scope": "entity-smoke", "verdict": "aligned",
            "source_revision": receipt["source_revision"], "image_digest": receipt["image_digest"], "package_custody_reference": receipt["receipt_reference"],
            "dependency_incarnation_sha256": fingerprint({"resource_id": dependency["DatabaseResourceId"], "database": dependency["DatabaseName"], "schema": "entity_smoke"}),
            "parameters_sha256": fingerprint(parameters), "database_subnet_group_sha256": fingerprint(dependency["database_subnet_group"]),
            "engine_version": "18.3", "checked_at": now, "provider_mutation": False, "acceptance_evidence": False}
    return safe, parameters, dependency["database_subnet_group"]


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.error = lambda _message: parser.exit(2, "ENTITY_SMOKE_ALIGNMENT_ARGUMENTS_INVALID\n")
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args()
    if args.validate_arguments:
        print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
    receipt = read_receipt(args.receipt.absolute())
    source_preflight(receipt)
    result, _, _ = inspect(aws, receipt, datetime.now(timezone.utc).isoformat())
    print(json.dumps(result, sort_keys=True)); return 0


if __name__ == "__main__":
    try: status = main()
    except (AlignmentFailure, OSError, ValueError, TypeError, KeyError, AttributeError, ImportError) as failure:
        print(json.dumps({"schema": "deploy/entity-smoke-target-alignment/v1", "verdict": "blocked", "code": "ENTITY_SMOKE_ALIGNMENT_NOT_CONFIRMED", "condition": failure.code if isinstance(failure, AlignmentFailure) else "alignment-boundary-failed", "effect": "not-started", "provider_mutation": False})); status = 1
    raise SystemExit(status)
