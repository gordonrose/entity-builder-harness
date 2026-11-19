#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.target-alignment.implementation
#   version: 3
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-19"
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
CONTROLLER_DIRECTORY = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/"
CONTROLLER_REPAIR_FILES = frozenset({
    "scripts/04.deploy/shared/provider-adapters/aws/response.py",
    "scripts/04.deploy/shared/provider-adapters/aws/cli.py",
    "scripts/04.deploy/shared/provider-adapters/aws/tasks.py",
    "scripts/04.deploy/shared/provider-adapters/aws/resource_reservation.py",
    "scripts/04.deploy/shared/provider-adapters/aws/snapshots.py",
    "scripts/04.deploy/shared/provider-adapters/aws/change_sets.py",
    "scripts/04.deploy/lifecycle/60-run/release-succession/script.py",
    "scripts/04.deploy/shared/provider-adapters/aws/recovery-test.py",
    "scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh",
    "scripts/04.deploy/operational-realization-gate/script.py",
    "scripts/04.deploy/operational-realization-gate/service-graph-test.py",
    ".agentic/04.deploy/schemas/operational-realization-contract.v2.schema.yml",
    "scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/script.py",
    "scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/alignment-test.py",
    ".agentic/aws/standards/operational-realization-applicability.md",
    "scripts/repo/diagnostic-coverage/reviews.v1.json",
})
READS = {
    ("sts", "get-caller-identity"), ("cloudformation", "describe-stacks"),
    ("ec2", "describe-vpcs"), ("ec2", "describe-subnets"), ("ec2", "describe-vpc-endpoints"),
    ("ec2", "describe-managed-prefix-lists"), ("servicediscovery", "get-service"),
    ("servicediscovery", "get-namespace"), ("route53", "get-hosted-zone"),
    ("rds", "describe-db-instances"), ("rds", "describe-db-parameters"),
    ("ecr", "describe-repositories"), ("ecr", "describe-images"), ("ecr", "batch-get-image"), ("ecr", "describe-image-scan-findings"),
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


CLI = module("entity_smoke_alignment_cli", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cli.py")
IMAGE_CHECKS = module("entity_smoke_image_checks", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py")
FOUNDATION_CHECKS = module("entity_smoke_foundation_checks", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/foundation-checks.py")
PARAMETERS = module("alignment_stack_parameters", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/change_sets.py")
INPUT_OWNER = module("feature_preparation_inputs", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py")
try:
    INPUTS = INPUT_OWNER.load(ROOT, "kanbien-core-platform", "entity-smoke")
    require("database" in INPUTS["dependencies"], "preparation-inputs-database-dependency-missing")
    INPUT_ERROR = None
except (INPUT_OWNER.InputFailure, AlignmentFailure) as failure:
    INPUTS, INPUT_ERROR = {}, failure.code
ACCOUNT, REGION, PROFILE = (INPUTS.get(key) for key in ("account", "region", "profile"))
REPOSITORY, REPOSITORY_URI, FOUNDATION = (INPUTS.get(key) for key in ("repository", "repository_uri", "foundation_template"))
DATABASE_BINDING = INPUTS.get("dependencies", {}).get("database", {})
DATABASE = DATABASE_BINDING.get("identifier")


def preparation_ready():
    if INPUT_ERROR: raise AlignmentFailure(INPUT_ERROR)


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
    preparation_ready()
    require((service, operation) in READS, "alignment-provider-operation-prohibited")
    arguments = ["aws", service, operation, *(["--profile", PROFILE] if PROFILE else []), "--region", REGION, "--output", "json",
                 "--cli-connect-timeout", "5", "--cli-read-timeout", "20", "--no-cli-pager", "--no-paginate", "--cli-input-json", json.dumps(parameters)]
    try:
        return CLI.invoke_json(arguments, cwd=ROOT, timeout=30, empty_body="reject", object_only=True,
                               environment={**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    except CLI.CliFailure as failure:
        if failure.code in {"aws-credentials-expired", "aws-access-denied"}:
            raise AlignmentFailure(failure.code) from None
        code = {"process": "alignment-command-unavailable", "service": "alignment-command-not-confirmed", "response": "alignment-provider-observation-invalid"}[failure.phase]
        raise AlignmentFailure(code) from None
    except (OSError, subprocess.SubprocessError): raise AlignmentFailure("alignment-command-unavailable") from None
    except (ValueError, TypeError): raise AlignmentFailure("alignment-provider-observation-invalid") from None


def only(response, field):
    values = response.get(field) if isinstance(response, dict) else None
    require(isinstance(values, list) and len(values) == 1 and isinstance(values[0], dict), "alignment-provider-observation-invalid")
    return values[0]


def read_receipt(path):
    preparation_ready()
    require(path.is_absolute() and not path.is_symlink() and not any(part.is_symlink() for part in path.parents), "alignment-receipt-path-invalid")
    try:
        with path.open("rb") as stream: raw = stream.read(65537)
        require(len(raw) <= 65536, "alignment-receipt-invalid")
        value = json.loads(raw)
        owner = module("entity_smoke_alignment_custody", ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py")
        owner.validate(value, argparse.Namespace(expected_target=INPUTS["target"], expected_candidate=INPUTS["candidate"], expected_package_contract=INPUTS["package"], expected_program=INPUTS["program"]))
    except AlignmentFailure: raise
    except Exception: raise AlignmentFailure("alignment-qualified-custody-not-confirmed") from None
    require(value["provider_region_alias"] == "aws-" + REGION, "alignment-custody-region-mismatch")
    return value


def retained_evidence_files(receipt, selection):
    require(isinstance(selection, dict) and set(selection) == {"source_revision", "image_digest", "files"}
            and selection["source_revision"] == receipt["source_revision"] and selection["image_digest"] == receipt["image_digest"], "alignment-retained-evidence-invalid")
    files = selection["files"]
    prefix = str(Path(SCOPE).parent.parent / "30-release-evidence") + "/"
    patterns = [re.escape(prefix) + r"proof-receipts/entity-smoke-[a-f0-9]{64}\.json",
                re.escape(prefix) + r"release-candidates/release-[a-f0-9]{24}\.yml"]
    require(isinstance(files, dict) and len(files) == 2
            and all(sum(isinstance(name, str) and re.fullmatch(pattern, name) is not None for name in files) == 1 for pattern in patterns), "alignment-retained-evidence-invalid")
    for name, expected in files.items():
        require(isinstance(expected, dict) and set(expected) == {"sha256", "size_bytes"}
                and isinstance(expected["sha256"], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", expected["sha256"]) is not None
                and type(expected["size_bytes"]) is int and expected["size_bytes"] > 0, "alignment-retained-evidence-invalid")
        path = ROOT / name
        require(not path.is_symlink() and not any(parent.is_symlink() for parent in path.parents), "alignment-retained-evidence-invalid")
        if not path.exists(): continue
        try:
            require(path.is_file() and path.stat().st_size == expected["size_bytes"], "alignment-retained-evidence-changed")
            with path.open("rb") as stream:
                observed = "sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()
            require(observed == expected["sha256"], "alignment-retained-evidence-changed")
        except OSError: raise AlignmentFailure("alignment-retained-evidence-unavailable") from None
    return files


def repaired_foundation(original):
    """Closed semantic delta; preserve every other part of the original template."""
    import copy
    result = copy.deepcopy(original)
    try:
        for name in ("EcrApiEndpoint", "EcrDkrEndpoint"):
            resource = result["Resources"][name]
            require(resource["Type"] == "AWS::EC2::VPCEndpoint", "alignment-foundation-repair-invalid")
            statements = resource["Properties"]["PolicyDocument"]["Statement"]
            matches = [row for row in statements if row.get("Resource") == {"Ref": "ExistingRepositoryArn"}]
            require(len(matches) == 1 and set(matches[0]["Action"]) == {"ecr:BatchCheckLayerAvailability", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"}, "alignment-foundation-repair-invalid")
            matches[0]["Resource"] = [{"Ref": "ExistingRepositoryArn"}, {"Fn::Sub": "arn:aws:ecr:${AWS::Region}:${AWS::AccountId}:repository/kanbien-core-platform/entity-smoke"}]
    except (KeyError, TypeError): raise AlignmentFailure("alignment-foundation-repair-invalid") from None
    return result


def foundation_sources(source, current):
    parser = module("entity_smoke_foundation_parser", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
    try:
        before = parser.template(command(["git", "show", source + ":" + FOUNDATION]))
        after = parser.template(command(["git", "show", current + ":" + FOUNDATION]))
        require(canonical(after) == canonical(repaired_foundation(before)), "alignment-foundation-repair-invalid")
        return before, after
    except ValueError: raise AlignmentFailure("alignment-foundation-repair-invalid") from None


def source_checkpoint(receipt):
    current = command(["git", "rev-parse", "HEAD"]).strip()
    source = receipt["source_revision"]
    require(all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value) is not None for value in (source, current)), "alignment-source-checkpoint-mismatch")
    if current != source:
        try: command(["git", "merge-base", "--is-ancestor", source, current])
        except AlignmentFailure: raise AlignmentFailure("alignment-source-checkpoint-mismatch") from None
        changed = command(["git", "diff", "--no-renames", "--name-only", "-z", source, current, "--"])
        require(changed.endswith("\0"), "alignment-source-checkpoint-mismatch")
        paths = changed.split("\0")[:-1]
        def controller(path):
            relative = path.removeprefix(CONTROLLER_DIRECTORY)
            return path.startswith(CONTROLLER_DIRECTORY) and "/" not in relative and relative.endswith((".py", ".sh"))
        require(all(path.startswith("commitLogs/") or path in CONTROLLER_REPAIR_FILES or controller(path) or path == FOUNDATION for path in paths), "alignment-source-checkpoint-mismatch")
        if FOUNDATION in paths: foundation_sources(source, current)
        checked = [path for path in paths if not path.startswith("commitLogs/")]
        if checked:
            rows = command(["git", "ls-tree", "-z", current, "--", *checked]).split("\0")[:-1]
            require(len(rows) == len(checked) and all(row.startswith(("100644 blob ", "100755 blob ")) for row in rows), "alignment-source-checkpoint-mismatch")
    return {"package_source_revision": source, "controller_revision": current}


def source_preflight(receipt, *, retained_source_evidence=None):
    source_checkpoint(receipt)
    allowed = {} if retained_source_evidence is None else retained_evidence_files(receipt, retained_source_evidence)
    status = command(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", ".", ":!commitLogs"])
    require(not status or status.endswith("\0") and all(entry.startswith("?? ") and entry[3:] in allowed for entry in status.split("\0")[:-1]), "alignment-committed-source-required")
    coverage = json.loads(command(["bash", "scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh", "--scope-contract", SCOPE, "--json"], 60))
    require(coverage.get("verdict") == "covered" and coverage.get("findings") == [], "alignment-declaration-coverage-not-confirmed")
    inventory = json.loads(command(["python3", "-B", "scripts/04.deploy/inventory-deploy-control/script.py", "--delivery", "--check", "--json"], 60))
    require(inventory.get("verdict") == "covered" and inventory.get("findings") == [], "alignment-delivery-coverage-not-confirmed")


def database_facts(database, administrator_secret):
    require(database.get("DBInstanceIdentifier") == DATABASE and database.get("DBInstanceStatus") == "available", "alignment-dependency-not-available")
    require(database.get("Engine") == DATABASE_BINDING["engine"], "alignment-engine-not-confirmed")
    try: INPUT_OWNER.PG.compatible(database.get("EngineVersion"), DATABASE_BINDING["engine_major"])
    except INPUT_OWNER.PG.VersionFailure as failure: raise AlignmentFailure(failure.code) from None
    require(database.get("StorageEncrypted") is True and database.get("PubliclyAccessible") is False and database.get("IAMDatabaseAuthenticationEnabled") is True, "alignment-dependency-security-not-confirmed")
    incarnation, name = database.get("DbiResourceId"), database.get("DBName")
    require(isinstance(incarnation, str) and re.fullmatch(r"db-[A-Za-z0-9]+", incarnation) is not None and isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,62}", name) is not None, "alignment-dependency-incarnation-invalid")
    require(name == DATABASE_BINDING["database_name"], "alignment-dependency-name-not-confirmed")
    groups = database.get("VpcSecurityGroups")
    require(isinstance(groups, list) and len(groups) == 1 and groups[0].get("Status") == "active" and isinstance(groups[0].get("VpcSecurityGroupId"), str), "alignment-dependency-network-not-confirmed")
    subnet = database.get("DBSubnetGroup")
    require(isinstance(subnet, dict) and subnet.get("SubnetGroupStatus") == "Complete" and isinstance(subnet.get("DBSubnetGroupName"), str), "alignment-dependency-network-not-confirmed")
    require(isinstance(administrator_secret, str) and re.fullmatch(re.escape("arn:aws:secretsmanager:" + REGION + ":" + ACCOUNT + ":secret:" + DATABASE_BINDING["administrator_secret_name"]) + r"-[A-Za-z0-9]{6}", administrator_secret) is not None, "alignment-administrative-reference-not-confirmed")
    parameters = database.get("DBParameterGroups")
    require(isinstance(parameters, list) and len(parameters) == 1 and parameters[0].get("ParameterApplyStatus") == "in-sync", "alignment-dependency-parameters-not-confirmed")
    endpoint = database.get("Endpoint")
    require(isinstance(endpoint, dict) and isinstance(endpoint.get("Address"), str) and endpoint.get("Port") == 5432, "alignment-dependency-route-not-confirmed")
    return {"DatabaseEndpoint": endpoint["Address"], "DatabaseName": name, "DatabaseResourceId": incarnation,
            "DatabaseSecurityGroupId": groups[0]["VpcSecurityGroupId"], "AdministratorSecretArn": administrator_secret,
            "engine_version": database["EngineVersion"], "database_subnet_group": subnet["DBSubnetGroupName"], "database_vpc": subnet.get("VpcId"),
            "parameter_group": parameters[0].get("DBParameterGroupName")}


def check_endpoint_policy(endpoint, declarations, parameters, outputs, required_resource):
    service = endpoint["ServiceName"].removeprefix("com.amazonaws." + REGION + ".")
    condition = {"ecr.api": "alignment-ecr-api-policy-not-confirmed", "ecr.dkr": "alignment-ecr-registry-policy-not-confirmed",
                 "secretsmanager": "alignment-secret-delivery-policy-not-confirmed"}[service]
    declared = declarations.get(endpoint["ServiceName"])
    require(declared is not None, "alignment-endpoint-policy-declaration-missing")
    try:
        expected = INPUT_OWNER.policy_values(declared, parameters, outputs)
        FOUNDATION_CHECKS.endpoint_policy(endpoint.get("PolicyDocument"), expected, service, ACCOUNT, REGION, required_resource)
    except INPUT_OWNER.InputFailure as failure:
        raise AlignmentFailure(failure.code) from None
    except FOUNDATION_CHECKS.FoundationFailure:
        raise AlignmentFailure(condition) from None


def inspect(provider, receipt, now):
    preparation_ready()
    caller = provider("sts", "get-caller-identity")
    require(caller.get("Account") == ACCOUNT and isinstance(caller.get("Arn"), str) and caller["Arn"].startswith("arn:aws:sts::" + ACCOUNT + ":assumed-role/"), "alignment-account-not-confirmed")
    try:
        foundation = provider("cloudformation", "describe-stacks", StackName=INPUTS["foundation_stack"])
        outputs = FOUNDATION_CHECKS.foundation(foundation, FOUNDATION_CHECKS.NETWORK_OUTPUTS, INPUTS["foundation_expected"])
        network = FOUNDATION_CHECKS.private_network(provider, outputs, INPUTS["foundation_expected"]["namespace"], REGION)
    except FOUNDATION_CHECKS.FoundationFailure as failure:
        raise AlignmentFailure(failure.code) from None
    services = {"com.amazonaws." + REGION + "." + suffix for suffix in ("ecr.api", "ecr.dkr", "logs", "secretsmanager")}
    try:
        selected, endpoint_group = FOUNDATION_CHECKS.private_endpoints(provider, outputs["VpcId"], services)
    except FOUNDATION_CHECKS.FoundationFailure as failure:
        raise AlignmentFailure(failure.code) from None
    parameters = PARAMETERS.parameter_values(foundation["Stacks"][0].get("Parameters"))
    require(parameters is not None, "alignment-foundation-parameters-not-confirmed")
    for endpoint in selected:
        if endpoint["ServiceName"].endswith((".ecr.api", ".ecr.dkr")):
            check_endpoint_policy(endpoint, INPUTS["foundation_endpoint_policies"], parameters, outputs,
                                  "arn:aws:ecr:" + REGION + ":" + ACCOUNT + ":repository/" + REPOSITORY)
    try:
        prefix_id = FOUNDATION_CHECKS.s3_prefix_list(provider, REGION)
    except FOUNDATION_CHECKS.FoundationFailure as failure:
        raise AlignmentFailure(failure.code) from None
    database = only(provider("rds", "describe-db-instances", DBInstanceIdentifier=DATABASE), "DBInstances")
    dependency_document = provider("cloudformation", "describe-stacks", StackName=DATABASE_BINDING["stack"])
    dependency_stack = only(dependency_document, "Stacks")
    require(dependency_stack.get("StackStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}, "alignment-dependency-stack-not-ready")
    try:
        dependency_outputs = FOUNDATION_CHECKS.stack_outputs(dependency_document, {DATABASE_BINDING["output"], "PersistenceDatabaseEndpoint", "AdministratorCredentialsSecretArn"})
    except FOUNDATION_CHECKS.FoundationFailure as failure:
        raise AlignmentFailure(failure.code) from None
    require(dependency_outputs.get(DATABASE_BINDING["output"]) == DATABASE and dependency_outputs.get("PersistenceDatabaseEndpoint") == database.get("Endpoint", {}).get("Address"), "alignment-dependency-ownership-not-confirmed")
    dependency = database_facts(database, dependency_outputs.get("AdministratorCredentialsSecretArn"))
    secret = provider("secretsmanager", "describe-secret", SecretId=dependency["AdministratorSecretArn"])
    require(secret.get("ARN") == dependency["AdministratorSecretArn"] and secret.get("Name") == DATABASE_BINDING["administrator_secret_name"] and not secret.get("DeletedDate"), "alignment-administrative-reference-not-confirmed")
    secrets_endpoint = next(item for item in selected if item["ServiceName"].endswith(".secretsmanager"))
    check_endpoint_policy(secrets_endpoint, DATABASE_BINDING["endpoint_policies"], {}, dependency_outputs, dependency["AdministratorSecretArn"])
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
    try: IMAGE_CHECKS.check_image(provider, REPOSITORY, receipt["image_digest"])
    except IMAGE_CHECKS.ScanFailure as failure: raise AlignmentFailure(str(failure)) from None
    budget = provider("budgets", "describe-budget", AccountId=ACCOUNT, BudgetName=INPUTS["budget"]["BudgetName"])
    try: FOUNDATION_CHECKS.budget(budget.get("Budget") if isinstance(budget, dict) else None, INPUTS["budget"])
    except FOUNDATION_CHECKS.FoundationFailure as failure: raise AlignmentFailure(failure.code) from None
    parameters = {key: dependency[key] for key in ("DatabaseEndpoint", "DatabaseName", "DatabaseResourceId", "DatabaseSecurityGroupId", "AdministratorSecretArn")}
    parameters.update(**network,
                      EndpointSecurityGroupId=endpoint_group, S3ArtifactPrefixListId=prefix_id,
                      ImageRepositoryUri=REPOSITORY_URI, ImageRepositoryArn="arn:aws:ecr:" + REGION + ":" + ACCOUNT + ":repository/" + REPOSITORY,
                      ImageDigest=receipt["image_digest"], SourceRevision=receipt["source_revision"], ServerDesiredCount="0")
    # Private parameters are consumed in-memory by the future change producer.
    # The retained/public report contains identifiers and fingerprints only.
    safe = {"schema": "deploy/entity-smoke-target-alignment/v1", "target": "kanbien-core-platform", "scope": "entity-smoke", "verdict": "aligned",
            "source_revision": receipt["source_revision"], "image_digest": receipt["image_digest"], "package_custody_reference": receipt["receipt_reference"],
            "dependency_incarnation_sha256": fingerprint({"resource_id": dependency["DatabaseResourceId"], "database": dependency["DatabaseName"], "schema": "entity_smoke"}),
            "parameters_sha256": fingerprint(parameters), "database_subnet_group_sha256": fingerprint(dependency["database_subnet_group"]),
            "engine_version": dependency["engine_version"], "checked_at": now, "provider_mutation": False, "acceptance_evidence": False}
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
