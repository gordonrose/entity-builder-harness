#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.template
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject unsafe feature-template counterexamples without inspecting or changing AWS.
#   portability: {class: internal, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh

import copy
import importlib.util
import json
import re
import shlex
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[5]
SPEC = importlib.util.spec_from_file_location("entity_smoke_cf", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
CF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CF)
TEMPLATE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke.yml"
RESTORE_TEMPLATE = TEMPLATE.with_name("entity-smoke-isolated-restore.yml")
REALIZATION_SPEC = importlib.util.spec_from_file_location("entity_smoke_realization", ROOT / "scripts/04.deploy/operational-realization-gate/script.py")
REALIZATION = importlib.util.module_from_spec(REALIZATION_SPEC)
REALIZATION_SPEC.loader.exec_module(REALIZATION)
CONFIGURATION_SPEC = importlib.util.spec_from_file_location("entity_smoke_configuration", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/entity-smoke-runtime-configuration.py")
CONFIGURATION = importlib.util.module_from_spec(CONFIGURATION_SPEC)
CONFIGURATION_SPEC.loader.exec_module(CONFIGURATION)


def check_realization(value, graph, restore=None):
    """Bind the actual draft runtime/task source, not a hypothetical fixture."""
    try:
        REALIZATION.validate_contract(graph)
    except REALIZATION.ContractFailure as error:
        return [error.code]
    if restore is None:
        restore = CF.template(RESTORE_TEMPLATE.read_text())
    workloads = {"feature-runtime": "ServerTaskDefinition", "feature-migration": "MigrationTaskDefinition",
                 "feature-administration": "AdministrationTaskDefinition", "feature-verifier": "VerifierTaskDefinition",
                 "feature-database-proof": "DatabaseProofTaskDefinition", "feature-restore-reader": "RestoreReaderTaskDefinition"}
    if graph["schema"] != REALIZATION.SERVICE_CONTRACT_SCHEMA or {unit["id"] for unit in graph["execution_units"]} != set(workloads):
        return ["realization-workload-set-mismatch"]
    artifacts = {item["id"]: item for item in graph["artifacts"]}
    connections = {item["id"]: item for item in graph["connections"]}
    if len(artifacts) != 5 or len(connections) != 6 or {store["id"] for store in graph["state_stores"]} != {"feature-record-store", "feature-restored-record-store"}:
        return ["realization-component-set-mismatch"]
    findings = set()
    tasks = {name for template in (value, restore) for name, item in template["Resources"].items() if item["Type"] == "AWS::ECS::TaskDefinition"}
    if tasks != set(workloads.values()): findings.add("realization-workload-set-mismatch")
    for unit in graph["execution_units"]:
        entrypoint = artifacts[unit["artifact"]]["entrypoint"]
        template = restore if unit["id"] == "feature-restore-reader" else value
        task = template["Resources"][workloads[unit["id"]]]["Properties"]
        if task["ContainerDefinitions"][0]["Command"] != [entrypoint]: findings.add("realization-workload-binding-mismatch")
        expected = "feature-runtime" if unit["id"] == "feature-verifier" else "feature-restored-record-store" if unit["id"] == "feature-restore-reader" else "feature-record-store"
        if len(unit["connections"]) != 1 or connections[unit["connections"][0]]["destination"] != expected:
            findings.add("realization-connection-binding-mismatch")
        expected_stores = [] if unit["id"] == "feature-verifier" else [expected]
        if unit["state_stores"] != expected_stores: findings.add("realization-direct-storage-binding-mismatch")
        name = Path(entrypoint).name
        source = ROOT / "infra/04.deploy/03.product/entrypoints" / name.replace(".js", ".ts")
        if entrypoint != "artifacts/" + name or not source.is_file(): findings.add("realization-entrypoint-source-missing")
    return sorted(findings)


def check(value):
    """Focused static invariants only, not a provider execution preflight."""
    findings = set()
    resources = value.get("Resources", {})
    expected = {
        "FeatureService": "AWS::ECS::Service",
        "FeatureServiceDiscovery": "AWS::ServiceDiscovery::Service",
        "ServerIngressFromVerifier": "AWS::EC2::SecurityGroupIngress",
    }
    for name in ("Server", "Migration", "Administration", "Verifier", "DatabaseProof"):
        expected[name + "SecurityGroup"] = "AWS::EC2::SecurityGroup"
        expected[name + "ExecutionRole"] = "AWS::IAM::Role"
        expected[name + "TaskDefinition"] = "AWS::ECS::TaskDefinition"
        expected["EndpointIngressFrom" + name] = "AWS::EC2::SecurityGroupIngress"
    for name in ("Server", "Migration", "Administration", "DatabaseProof"):
        expected["DatabaseIngressFrom" + name] = "AWS::EC2::SecurityGroupIngress"
    for name in ("Server", "Migration", "DatabaseProof"):
        expected[name + "TaskRole"] = "AWS::IAM::Role"
    if {key: item.get("Type") for key, item in resources.items()} != expected:
        findings.add("resource-set-mismatch")
        return sorted(findings)
    props = {name: resource["Properties"] for name, resource in resources.items()}
    service = props["FeatureService"]
    if value["Parameters"]["ServerDesiredCount"].get("Default") != 0 or service.get("DesiredCount") != {"Ref": "ServerDesiredCount"}:
        findings.add("initial-workload-not-stopped")
    if service.get("DeploymentConfiguration", {}).get("DeploymentCircuitBreaker") != {"Enable": True, "Rollback": False}:
        findings.add("automatic-release-restoration-not-prohibited")
    if service.get("NetworkConfiguration", {}).get("AwsvpcConfiguration") != {"AssignPublicIp": "DISABLED", "Subnets": {"Ref": "PrivateSubnetIds"}, "SecurityGroups": [{"Ref": "ServerSecurityGroup"}]} or "LoadBalancers" in service:
        findings.add("private-service-boundary-mismatch")
    if service.get("TaskDefinition") != {"Ref": "ServerTaskDefinition"}:
        findings.add("server-task-binding-mismatch")
    for name in ("Server", "Migration", "Administration", "Verifier", "DatabaseProof"):
        task = props[name + "TaskDefinition"]
        containers = task["ContainerDefinitions"]
        if len(containers) != 1:
            findings.add("container-set-mismatch")
            continue
        container = containers[0]
        if container.get("ReadonlyRootFilesystem") is not True or container.get("Privileged", False) is not False or container.get("LinuxParameters") != {"Capabilities": {"Drop": ["ALL"]}}:
            findings.add("container-security-boundary-mismatch")
        if container.get("Image") != {"Fn::Sub": "${ImageRepositoryUri}@${ImageDigest}"} or "EntryPoint" in container:
            findings.add("immutable-image-binding-mismatch")
        entry = "" if name == "Server" else "-database-proof" if name == "DatabaseProof" else "-" + name.lower()
        if container.get("Command") != ["artifacts/kanbien-entity-smoke" + entry + ".main.js"]:
            findings.add("exec-entrypoint-mismatch")
        if task.get("ExecutionRoleArn") != {"Fn::GetAtt": [name + "ExecutionRole", "Arn"]}:
            findings.add("execution-role-binding-mismatch")
        role = {"Fn::GetAtt": [name + "TaskRole", "Arn"]} if name in {"Server", "Migration", "DatabaseProof"} else None
        if task.get("TaskRoleArn") != role:
            findings.add("task-role-boundary-mismatch")
        secrets = container.get("Secrets", [])
        if secrets != ([{"Name": "PERSISTENCE_ADMINISTRATOR_CREDENTIALS", "ValueFrom": {"Ref": "AdministratorSecretArn"}}] if name == "Administration" else []):
            findings.add("credential-delivery-boundary-mismatch")
        environment = container.get("Environment", [])
        env = {item["Name"]: item["Value"] for item in environment}
        if len(env) != len(environment) or any("password" in key.lower() or "credential" in key.lower() for key in env):
            findings.add("environment-secret-or-ambiguity")
        if env.get("NODE_ENV") != "production" or env.get("PLATFORM_SOURCE_COMMIT_SHA") != {"Ref": "SourceRevision"}:
            findings.add("source-identity-binding-mismatch")
        if name == "Verifier":
            if set(env) != {"NODE_ENV", "PLATFORM_SOURCE_COMMIT_SHA", "ENTITY_SMOKE_VERIFICATION_URL", "ENTITY_SMOKE_EXPECTED_SOURCE"}:
                findings.add("verifier-database-configuration")
        elif env.get("PERSISTENCE_POSTGRES_SCHEMA") != "entity_smoke" or env.get("PERSISTENCE_POSTGRES_HOST") != {"Ref": "DatabaseEndpoint"}:
            findings.add("database-scope-binding-mismatch")
        dns = [{"IpProtocol": protocol, "FromPort": 53, "ToPort": 53, "CidrIp": {"Ref": "VpcCidr"}} for protocol in ("udp", "tcp")]
        common = dns + [
            {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "DestinationSecurityGroupId": {"Ref": "EndpointSecurityGroupId"}},
            {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "DestinationPrefixListId": {"Ref": "S3ArtifactPrefixListId"}},
        ]
        dependency = {"IpProtocol": "tcp", "FromPort": 3000 if name == "Verifier" else 5432, "ToPort": 3000 if name == "Verifier" else 5432, "DestinationSecurityGroupId": {"Ref": "ServerSecurityGroup" if name == "Verifier" else "DatabaseSecurityGroupId"}}
        group = props[name + "SecurityGroup"]
        if group.get("SecurityGroupEgress") != common + [dependency] or group.get("SecurityGroupIngress", []) != []:
            findings.add("network-boundary-mismatch")
        endpoint = props["EndpointIngressFrom" + name]
        if endpoint != {"GroupId": {"Ref": "EndpointSecurityGroupId"}, "IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "SourceSecurityGroupId": {"Ref": name + "SecurityGroup"}}:
            findings.add("endpoint-ingress-boundary-mismatch")
        if name != "Verifier" and props["DatabaseIngressFrom" + name] != {"GroupId": {"Ref": "DatabaseSecurityGroupId"}, "IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "SourceSecurityGroupId": {"Ref": name + "SecurityGroup"}}:
            findings.add("database-ingress-boundary-mismatch")
    for name, username in (("Server", "entity_smoke_runtime"), ("Migration", "entity_smoke_migration"), ("DatabaseProof", "entity_smoke_runtime")):
        policies = props[name + "TaskRole"]["Policies"]
        statements = [statement for policy in policies for statement in policy["PolicyDocument"]["Statement"]]
        if statements != [{"Effect": "Allow", "Action": "rds-db:connect", "Resource": {"Fn::Sub": "arn:aws:rds-db:${AWS::Region}:${AWS::AccountId}:dbuser:${DatabaseResourceId}/" + username}}]:
            findings.add("database-role-scope-mismatch")
    return sorted(findings)


def check_restore(value):
    """The restore task gets only its newly restored database, never source access."""
    expected = {
        "RestoreDatabaseSecurityGroup": "AWS::EC2::SecurityGroup",
        "RestoredDatabase": "AWS::RDS::DBInstance",
        "RestoreReaderSecurityGroup": "AWS::EC2::SecurityGroup",
        "EndpointIngressFromRestoreReader": "AWS::EC2::SecurityGroupIngress",
        "RestoreReaderExecutionRole": "AWS::IAM::Role",
        "RestoreReaderTaskRole": "AWS::IAM::Role",
        "RestoreReaderTaskDefinition": "AWS::ECS::TaskDefinition",
        "RestoreDatabaseIngressFromReader": "AWS::EC2::SecurityGroupIngress",
    }
    resources = value.get("Resources", {})
    if {name: item.get("Type") for name, item in resources.items()} != expected:
        return ["restore-resource-set-mismatch"]
    findings = set(check_parameter_patterns(value))
    props = {name: resource["Properties"] for name, resource in resources.items()}
    database = props["RestoredDatabase"]
    expected_database = {
        "DBInstanceIdentifier": {"Ref": "RestoredDatabaseIdentifier"},
        "DBSnapshotIdentifier": {"Ref": "SourceSnapshotArn"}, "DBInstanceClass": "db.t4g.micro",
        "DBSubnetGroupName": {"Ref": "DatabaseSubnetGroupName"},
        "VPCSecurityGroups": [{"Fn::GetAtt": ["RestoreDatabaseSecurityGroup", "GroupId"]}],
        "PubliclyAccessible": False, "MultiAZ": False, "EnableIAMDatabaseAuthentication": True,
        "DeletionProtection": False, "CopyTagsToSnapshot": True,
        "Tags": [{"Key": "Target", "Value": "kanbien-core-platform"}, {"Key": "Scope", "Value": "entity-smoke"},
                 {"Key": "Purpose", "Value": "isolated-restore-proof"}, {"Key": "ProofLabel", "Value": {"Ref": "ProofLabel"}}],
    }
    if database != expected_database or resources["RestoredDatabase"].get("DeletionPolicy") != "Delete" or resources["RestoredDatabase"].get("UpdateReplacePolicy") != "Retain":
        findings.add("restore-database-boundary-mismatch")
    ingress = props["RestoreDatabaseIngressFromReader"]
    if ingress != {"GroupId": {"Ref": "RestoreDatabaseSecurityGroup"}, "IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "SourceSecurityGroupId": {"Ref": "RestoreReaderSecurityGroup"}}:
        findings.add("restore-database-ingress-mismatch")
    dns = [{"IpProtocol": protocol, "FromPort": 53, "ToPort": 53, "CidrIp": {"Ref": "VpcCidr"}} for protocol in ("udp", "tcp")]
    if props["RestoreDatabaseSecurityGroup"].get("SecurityGroupEgress") != dns or props["RestoreDatabaseSecurityGroup"].get("SecurityGroupIngress", []) != []:
        findings.add("restore-database-network-mismatch")
    reader_network = dns + [
        {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "DestinationSecurityGroupId": {"Ref": "EndpointSecurityGroupId"}},
        {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "DestinationPrefixListId": {"Ref": "S3ArtifactPrefixListId"}},
        {"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "DestinationSecurityGroupId": {"Ref": "RestoreDatabaseSecurityGroup"}},
    ]
    if props["RestoreReaderSecurityGroup"].get("SecurityGroupEgress") != reader_network or props["RestoreReaderSecurityGroup"].get("SecurityGroupIngress", []) != []:
        findings.add("restore-reader-network-mismatch")
    task = props["RestoreReaderTaskDefinition"]
    containers = task.get("ContainerDefinitions", [])
    if len(containers) != 1:
        return sorted(findings | {"restore-reader-container-set-mismatch"})
    container = containers[0]
    environment = container.get("Environment", [])
    env = {item["Name"]: item["Value"] for item in environment}
    required = {
        "PERSISTENCE_POSTGRES_HOST": {"Fn::GetAtt": ["RestoredDatabase", "Endpoint.Address"]},
        "PERSISTENCE_POSTGRES_DATABASE": {"Ref": "RestoredDatabaseName"},
        "PERSISTENCE_POSTGRES_SCHEMA": "entity_smoke", "PERSISTENCE_RUNTIME_DATABASE_USERNAME": "entity_smoke_runtime",
        "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE": {"Fn::Sub": "arn:aws:rds-db:${AWS::Region}:${AWS::AccountId}:dbuser:${RestoredDatabase.DbiResourceId}/entity_smoke_runtime"},
        "ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "restore-read", "PLATFORM_DEPLOYMENT_EXPOSURE": "private",
        "NODE_ENV": "production", "PLATFORM_SOURCE_COMMIT_SHA": {"Ref": "SourceRevision"},
        "PERSISTENCE_POSTGRES_PORT": "5432", "PERSISTENCE_POSTGRES_CA_PATH": "/app/assets/rds-eu-west-1-bundle.crt",
        "PERSISTENCE_POSTGRES_IAM_REGION": {"Ref": "AWS::Region"},
    }
    if env != required or len(environment) != len(env) or container.get("Secrets", []) != []:
        findings.add("restore-reader-configuration-mismatch")
    if task.get("TaskRoleArn") != {"Fn::GetAtt": ["RestoreReaderTaskRole", "Arn"]} or task.get("ExecutionRoleArn") != {"Fn::GetAtt": ["RestoreReaderExecutionRole", "Arn"]}:
        findings.add("restore-reader-identity-mismatch")
    if container.get("Command") != ["artifacts/kanbien-entity-smoke-database-proof.main.js"] or container.get("Image") != {"Fn::Sub": "${ImageRepositoryUri}@${ImageDigest}"} or container.get("ReadonlyRootFilesystem") is not True or container.get("LinuxParameters") != {"Capabilities": {"Drop": ["ALL"]}} or "EntryPoint" in container or container.get("Privileged", False) is not False:
        findings.add("restore-reader-payload-mismatch")
    policies = props["RestoreReaderTaskRole"]["Policies"]
    statements = [item for policy in policies for item in policy["PolicyDocument"]["Statement"]]
    if statements != [{"Effect": "Allow", "Action": "rds-db:connect", "Resource": required["PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE"]}]:
        findings.add("restore-reader-database-authority-mismatch")
    execution = [item for policy in props["RestoreReaderExecutionRole"]["Policies"] for item in policy["PolicyDocument"]["Statement"]]
    if execution != [
        {"Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*"},
        {"Effect": "Allow", "Action": ["ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"], "Resource": {"Ref": "ImageRepositoryArn"}},
        {"Effect": "Allow", "Action": ["logs:CreateLogStream", "logs:PutLogEvents"], "Resource": {"Fn::Sub": "arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:${LogGroupName}:log-stream:entity-smoke-*"}},
    ]:
        findings.add("restore-reader-delivery-authority-mismatch")
    return sorted(findings)


def check_parameter_patterns(value):
    # Exercise parsed YAML patterns against actual non-secret delivery shapes;
    # textual comparison alone missed over-escaped dots in the restore source.
    samples = {
        "VpcCidr": ("10.71.0.0/16", "10x71x0x0/16"),
        "ImageRepositoryUri": ("337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/entity-smoke", "337159794548xdkrxecrxeu-west-1xamazonawsxcom/kanbien-core-platform/entity-smoke"),
    }
    try:
        for key, (accepted, rejected) in samples.items():
            pattern = value["Parameters"][key]["AllowedPattern"]
            if re.fullmatch(pattern, accepted) is None or re.fullmatch(pattern, rejected) is not None:
                return ["delivery-parameter-pattern-invalid"]
    except (KeyError, TypeError, re.error):
        return ["delivery-parameter-pattern-invalid"]
    return []


def check_image_environment(source, contract):
    """Known source form only; effective inherited ENV is checked in the image."""
    declarations = [line for line in source.splitlines() if line.startswith("ENV ")]
    if len(declarations) != 1:
        return ["shared-image-environment-mismatch"]
    try:
        entries = [item.split("=", 1) for item in shlex.split(declarations[0][4:])]
        actual = dict(entries)
        expected = {key: "${SOURCE_COMMIT_SHA}" if value == "build-argument" else str(value) for key, value in contract["runtime"]["non_secret_defaults"].items()}
    except (ValueError, KeyError, TypeError):
        return ["shared-image-environment-mismatch"]
    if len(actual) != len(entries) or actual != expected or any(key.startswith("PERSISTENCE_") or key == "ENTITY_SMOKE_LOCAL_QUALIFICATION_TOKEN" for key in actual):
        return ["shared-image-environment-mismatch"]
    return []


OPERATIONAL_WRAPPERS = (
    "task-plan.sh", "task-execute.sh", "failure-plan.sh", "failure-stop.sh",
    "replacement.sh", "restart.sh", "snapshot.sh", "restore.sh", "restore-reader.sh",
)


def missing_scope_commands(scope):
    """Directory impact alone does not bind an executable to its owning scope."""
    requirements = scope["change_impact"]["requirements"]
    bound = {path for item in requirements for path in item["required_by"]}
    prefix = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/"
    return [prefix + name for name in OPERATIONAL_WRAPPERS if prefix + name not in bound]


def main():
    if not __debug__:
        raise SystemExit("ENTITY_SMOKE_TEMPLATE_ASSERTIONS_DISABLED")
    scope = yaml.safe_load((ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml").read_text())
    assert missing_scope_commands(scope) == [], "operational commands must be explicitly owned by the feature scope"
    for name in OPERATIONAL_WRAPPERS:
        changed = copy.deepcopy(scope)
        path = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/" + name
        assert (ROOT / path).is_file(), "declared operational wrapper must exist"
        for requirement in changed["change_impact"]["requirements"]:
            requirement["required_by"] = [item for item in requirement["required_by"] if item != path]
        assert missing_scope_commands(changed) == [path], "directory impact cannot replace explicit command ownership"
    value = CF.template(TEMPLATE.read_text())
    assert check(value) == [], check(value)
    assert check_parameter_patterns(value) == []
    image = yaml.safe_load((ROOT / "infra/04.deploy/03.product/image/entity-smoke/image-contract.yml").read_text())
    dockerfile = (ROOT / "infra/04.deploy/03.product/image/entity-smoke/Dockerfile").read_text()
    assert check_image_environment(dockerfile, image) == []
    contaminated = dockerfile.replace("ENV NODE_ENV=", "ENV PERSISTENCE_POSTGRES_CA_PATH=/app/assets/rds-eu-west-1-bundle.crt NODE_ENV=")
    assert check_image_environment(contaminated, image) == ["shared-image-environment-mismatch"], "database environment cannot leak into the credential-free HTTP verifier"
    assert image["source_realization_contract"] == "infra/04.deploy/03.product/image/entity-smoke/realization-contract.v2.yml"
    graph = yaml.safe_load((ROOT / image["source_realization_contract"]).read_text())
    assert check_realization(value, graph) == [], check_realization(value, graph)
    binding = {"target": "kanbien-core-platform", "scope": "entity-smoke", "program_id": "kanbien-entity-smoke", "workloads": [
        {"id": name, "provider_reference": reference} for name, (_source, reference) in CONFIGURATION.WORKLOADS.items()]}
    normalized = CONFIGURATION.normalize(TEMPLATE, binding)
    assert set(normalized) == set(CONFIGURATION.WORKLOADS)
    assert normalized["entity-smoke-restore-reader-task"][0]["environment"]["PERSISTENCE_POSTGRES_HOST"] == {"Fn::GetAtt": "RestoredDatabase.Endpoint.Address"}
    assert normalized["entity-smoke-database-proof-task"][0]["environment"]["PERSISTENCE_POSTGRES_HOST"] == {"Ref": "DatabaseEndpoint"}
    assert all(not key.startswith("PERSISTENCE_") for key in normalized["entity-smoke-verifier-task"][0]["environment"])
    misbound = copy.deepcopy(binding)
    next(item for item in misbound["workloads"] if item["id"] == "entity-smoke-restore-reader-task")["provider_reference"] = "ServerTaskDefinition"
    try: CONFIGURATION.normalize(TEMPLATE, misbound)
    except ValueError as error: assert str(error) == "entity-smoke-configuration-binding-invalid"
    else: raise AssertionError("restoration may not borrow the source server binding")
    restore = CF.template(RESTORE_TEMPLATE.read_text())
    assert check_restore(restore) == [], check_restore(restore)
    restore_cases = [
        (lambda v: v["Parameters"]["ImageRepositoryUri"].update(AllowedPattern=r"^[0-9]{12}\\.dkr.*$"), "delivery-parameter-pattern-invalid"),
        (lambda v: v["Parameters"]["VpcCidr"].update(AllowedPattern=r"^10\\.71.*$"), "delivery-parameter-pattern-invalid"),
        (lambda v: v["Resources"]["RestoredDatabase"]["Properties"].update(PubliclyAccessible=True), "restore-database-boundary-mismatch"),
        (lambda v: v["Resources"]["RestoredDatabase"]["Properties"].update(DBSnapshotIdentifier="unowned-snapshot"), "restore-database-boundary-mismatch"),
        (lambda v: v["Resources"]["RestoreDatabaseIngressFromReader"]["Properties"].update(GroupId={"Ref": "SourceDatabaseSecurityGroup"}), "restore-database-ingress-mismatch"),
        (lambda v: v["Resources"]["RestoreReaderTaskRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"][0].update(Resource="*"), "restore-reader-database-authority-mismatch"),
        (lambda v: v["Resources"]["RestoreReaderTaskDefinition"]["Properties"]["ContainerDefinitions"][0]["Environment"].append({"Name": "PERSISTENCE_ADMINISTRATOR_CREDENTIALS", "Value": "sensitive-canary"}), "restore-reader-configuration-mismatch"),
        (lambda v: v["Resources"]["RestoreReaderTaskDefinition"]["Properties"]["ContainerDefinitions"][0].update(Command=["artifacts/kanbien-entity-smoke-migration.main.js"]), "restore-reader-payload-mismatch"),
        (lambda v: v["Resources"]["RestoreReaderSecurityGroup"]["Properties"]["SecurityGroupEgress"].append({"IpProtocol": "-1", "CidrIp": "0.0.0.0/0"}), "restore-reader-network-mismatch"),
        (lambda v: v["Resources"]["RestoreReaderExecutionRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"].append({"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": "*"}), "restore-reader-delivery-authority-mismatch"),
    ]
    for mutation, code in restore_cases:
        changed = copy.deepcopy(restore)
        mutation(changed)
        assert code in check_restore(changed), code
        assert "sensitive-canary" not in json.dumps(check_restore(changed))
    cases = [
        (lambda v: v["Resources"]["FeatureService"]["Properties"]["DeploymentConfiguration"]["DeploymentCircuitBreaker"].update(Rollback=True), "automatic-release-restoration-not-prohibited"),
        (lambda v: v["Resources"]["VerifierTaskDefinition"]["Properties"].update(TaskRoleArn={"Fn::GetAtt": ["ServerTaskRole", "Arn"]}), "task-role-boundary-mismatch"),
        (lambda v: v["Resources"]["VerifierTaskDefinition"]["Properties"]["ContainerDefinitions"][0]["Environment"].append({"Name": "PERSISTENCE_POSTGRES_HOST", "Value": "sensitive-canary"}), "verifier-database-configuration"),
        (lambda v: v["Resources"]["ServerTaskDefinition"]["Properties"]["ContainerDefinitions"][0].update(LinuxParameters={}), "container-security-boundary-mismatch"),
        (lambda v: v["Resources"]["ServerTaskDefinition"]["Properties"]["ContainerDefinitions"][0].update(Image="unqualified:latest"), "immutable-image-binding-mismatch"),
        (lambda v: v["Parameters"]["ServerDesiredCount"].update(Default=1), "initial-workload-not-stopped"),
        (lambda v: v["Resources"]["VerifierSecurityGroup"]["Properties"]["SecurityGroupEgress"].append({"IpProtocol": "-1", "CidrIp": "0.0.0.0/0"}), "network-boundary-mismatch"),
        (lambda v: v["Resources"].update(UnreviewedDatabase={"Type": "AWS::RDS::DBInstance", "Properties": {}}), "resource-set-mismatch"),
        (lambda v: v["Resources"]["ServerTaskRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"][0].update(Resource="*"), "database-role-scope-mismatch"),
    ]
    for mutation, code in cases:
        changed = copy.deepcopy(value)
        mutation(changed)
        assert code in check(changed), code
        assert "sensitive-canary" not in json.dumps(check(changed))
    changed = copy.deepcopy(value)
    changed["Resources"]["VerifierTaskDefinition"]["Properties"]["ContainerDefinitions"][0]["Command"] = ["artifacts/kanbien-entity-smoke-migration.main.js"]
    assert "realization-workload-binding-mismatch" in check_realization(changed, graph)
    changed_graph = copy.deepcopy(graph)
    verifier = next(unit for unit in changed_graph["execution_units"] if unit["id"] == "feature-verifier")
    verifier["state_stores"] = ["feature-record-store"]
    connection = next(item for item in changed_graph["connections"] if item["id"] == "feature-verifier-private-call")
    connection["destination"] = "feature-record-store"
    changed_graph["edges"] = [edge for edge in changed_graph["edges"] if edge["from"] != connection["id"]]
    changed_graph["edges"].extend([{"from": connection["id"], "to": "feature-record-store", "purpose": "incorrect-direct-store"},
                                  {"from": "feature-verifier", "to": "feature-record-store", "purpose": "incorrect-direct-store"}])
    # Structurally valid does not mean it matches the actual HTTP-only task.
    REALIZATION.validate_contract(changed_graph)
    assert set(check_realization(value, changed_graph)) == {"realization-connection-binding-mismatch", "realization-direct-storage-binding-mismatch"}
    print(json.dumps({"verdict": "passed", "scope": "entity-smoke-static-template", "negative_cases": len(cases), "restore_negative_cases": len(restore_cases), "realization_binding_negative_cases": 2, "image_environment_negative_cases": 1, "multi_template_configuration_negative_cases": 1, "provider_observation": False}))


if __name__ == "__main__":
    main()
