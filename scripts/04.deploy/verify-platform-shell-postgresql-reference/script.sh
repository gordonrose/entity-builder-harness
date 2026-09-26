#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-postgresql-reference
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: persistence.operations
#   disciplines:
#   - security
#   - sre
#   - architecture
#   kind: script
#   purpose: Statically prove the reviewed Kanbien staging PostgreSQL relational-reference source boundary before an AWS change set is created.
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
RENDERED_FOUNDATION="$(mktemp /tmp/platform-shell-relational-reference.XXXXXX.yml)"
trap 'rm -f "$RENDERED_FOUNDATION"' EXIT
bash scripts/04.deploy/render-platform-shell-foundation-template/script.sh --output "$RENDERED_FOUNDATION" >/dev/null

RENDERED_FOUNDATION="$RENDERED_FOUNDATION" python3 - <<'PY'
import os
import sys
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

def load_cfn(path):
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.load(handle, Loader=CfnLoader)

def load_yaml(path):
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)

failures = []
def fail(message):
    failures.append(message)

def props(template, name, kind):
    value = template.get("Resources", {}).get(name)
    if not isinstance(value, dict):
        fail(f"missing resource {name}")
        return {}
    if value.get("Type") != kind:
        fail(f"{name} must be {kind}")
    return value.get("Properties", {})

def statements(role):
    return {
        statement.get("Sid"): statement
        for policy in role.get("Policies", [])
        for statement in policy.get("PolicyDocument", {}).get("Statement", [])
        if isinstance(statement, dict)
    }

foundation = load_cfn(os.environ["RENDERED_FOUNDATION"])
manifest = load_yaml("infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation.yml")
profile = load_yaml("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")

required_fragments = {
    "foundation/relational-persistence.yml",
    "foundation/relational-access.yml",
    "foundation/relational-workload-configuration.yml",
    "foundation/relational-operations.yml",
}
if not required_fragments.issubset(set(manifest.get("fragments", []))):
    fail("foundation must retain the relational responsibility-focused source fragments")
if foundation.get("Parameters", {}).get("PrivateSubnetIds", {}).get("Type") != "List<AWS::EC2::Subnet::Id>":
    fail("private subnet identifiers must be typed deployment inputs, not source values")

subnets = props(foundation, "RelationalDatabaseSubnetGroup", "AWS::RDS::DBSubnetGroup")
if subnets.get("DBSubnetGroupName") != "kanbien-staging-platform-relational-private" or subnets.get("SubnetIds") != {"!Ref": "PrivateSubnetIds"}:
    fail("RDS subnet group must use only the supplied private subnet list")
group = props(foundation, "RelationalDatabaseSecurityGroup", "AWS::EC2::SecurityGroup")
if group.get("VpcId") != {"!Ref": "VpcId"} or group.get("SecurityGroupEgress") != [] or "SecurityGroupIngress" in group:
    fail("database group must be VPC-local, have no egress, and use separate ingress rules")
parameters = props(foundation, "RelationalDatabaseParameterGroup", "AWS::RDS::DBParameterGroup")
if parameters.get("Family") != "postgres17" or parameters.get("Parameters") != {"rds.force_ssl": "1"}:
    fail("database parameter group must enforce TLS")

db_resource = foundation.get("Resources", {}).get("RelationalDatabase", {})
db = props(foundation, "RelationalDatabase", "AWS::RDS::DBInstance")
expected_db = {
    "DBInstanceIdentifier": "kanbien-staging-platform-relational",
    "DBName": "platformsmoke",
    "Engine": "postgres",
    "EngineVersion": "17.11",
    "DBInstanceClass": "db.t4g.micro",
    "AllocatedStorage": "20",
    "MaxAllocatedStorage": 30,
    "StorageType": "gp3",
    "StorageEncrypted": True,
    "MultiAZ": False,
    "PubliclyAccessible": False,
    "BackupRetentionPeriod": 7,
    "CopyTagsToSnapshot": True,
    "DeleteAutomatedBackups": True,
    "DeletionProtection": True,
    "EnableIAMDatabaseAuthentication": False,
    "EnablePerformanceInsights": False,
    "MonitoringInterval": 0,
    "ManageMasterUserPassword": True,
    "MasterUsername": "psmokeadmin",
    "CACertificateIdentifier": "rds-ca-rsa2048-g1",
    "DBSubnetGroupName": {"!Ref": "RelationalDatabaseSubnetGroup"},
    "VPCSecurityGroups": [{"!Ref": "RelationalDatabaseSecurityGroup"}],
    "DBParameterGroupName": {"!Ref": "RelationalDatabaseParameterGroup"},
}
for key, expected in expected_db.items():
    if db.get(key) != expected:
        fail(f"RelationalDatabase must retain reviewed {key}")
if db_resource.get("DeletionPolicy") != "Snapshot" or db_resource.get("UpdateReplacePolicy") != "Snapshot":
    fail("RDS must snapshot rather than silently discard persistent data")
if "EnableCloudwatchLogsExports" in db:
    fail("RDS engine logs must remain unexported in v1")

for name, username in (("RelationalMigrationSecret", "psmokemigrate"), ("RelationalRuntimeSecret", "psmokeruntime")):
    secret = props(foundation, name, "AWS::SecretsManager::Secret")
    generated = secret.get("GenerateSecretString", {})
    if generated.get("SecretStringTemplate") != f'{{"username":"{username}"}}' or generated.get("GenerateStringKey") != "password" or generated.get("PasswordLength") != 32 or generated.get("ExcludePunctuation") is not True or generated.get("RequireEachIncludedType") is not True or "SecretString" in secret:
        fail(f"{name} must generate—not commit—its credential")

for name, workload in {
    "RelationalDatabaseIngressFromServer": "ServiceSecurityGroup",
    "RelationalDatabaseIngressFromWorker": "WorkerSecurityGroup",
    "RelationalDatabaseIngressFromRelay": "RelaySecurityGroup",
}.items():
    rule = props(foundation, name, "AWS::EC2::SecurityGroupIngress")
    if rule.get("GroupId") != {"!Ref": "RelationalDatabaseSecurityGroup"} or rule.get("SourceSecurityGroupId") != {"!Ref": workload} or [rule.get("IpProtocol"), rule.get("FromPort"), rule.get("ToPort")] != ["tcp", 5432, 5432] or "CidrIp" in rule:
        fail(f"{name} must permit only one source security group on TCP 5432")
for name, workload in {
    "RelationalDatabaseEgressFromServer": "ServiceSecurityGroup",
    "RelationalDatabaseEgressFromWorker": "WorkerSecurityGroup",
    "RelationalDatabaseEgressFromRelay": "RelaySecurityGroup",
}.items():
    rule = props(foundation, name, "AWS::EC2::SecurityGroupEgress")
    if rule.get("GroupId") != {"!Ref": workload} or rule.get("DestinationSecurityGroupId") != {"!Ref": "RelationalDatabaseSecurityGroup"} or [rule.get("IpProtocol"), rule.get("FromPort"), rule.get("ToPort")] != ["tcp", 5432, 5432] or "CidrIp" in rule:
        fail(f"{name} must permit only the relational database group on TCP 5432")

config = props(foundation, "RelationalTargetConfiguration", "AWS::SSM::Parameter")
if config.get("Name") != "/kanbien/staging/platform-shell/relational-persistence/config" or config.get("Type") != "String" or config.get("DataType") != "text" or not isinstance(config.get("Value"), dict) or "!Sub" not in config.get("Value"):
    fail("relational configuration must be a non-secret SSM parameter with deployment-time references")

bootstrap = props(foundation, "RelationalBootstrapTaskRole", "AWS::IAM::Role")
migration = props(foundation, "RelationalMigrationTaskRole", "AWS::IAM::Role")
runtime = props(foundation, "RelationalRuntimeTaskRole", "AWS::IAM::Role")
for name, role in (("bootstrap", bootstrap), ("migration", migration), ("runtime", runtime)):
    if role.get("AssumeRolePolicyDocument", {}).get("Statement") != [{"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}]:
        fail(f"{name} task role must be ECS-task-only")
bootstrap_statement = statements(bootstrap).get("ReadOnlyRelationalBootstrapAndRoleCredentials", {})
if set(statements(bootstrap)) != {"ReadOnlyRelationalBootstrapAndRoleCredentials"} or bootstrap_statement.get("Action") != ["secretsmanager:GetSecretValue"] or bootstrap_statement.get("Resource") != [{"!GetAtt": "RelationalDatabase.MasterUserSecret.SecretArn"}, {"!Ref": "RelationalMigrationSecret"}, {"!Ref": "RelationalRuntimeSecret"}]:
    fail("bootstrap role must have only the three exact credential reads")
for role, secret in ((migration, "RelationalMigrationSecret"), (runtime, "RelationalRuntimeSecret")):
    actual = statements(role)
    if len(actual) != 2 or not any(statement.get("Action") == ["ssm:GetParameter"] and statement.get("Resource") == {"!GetAtt": "RelationalTargetConfiguration.Arn"} for statement in actual.values()) or not any(statement.get("Action") == ["secretsmanager:GetSecretValue"] and statement.get("Resource") == {"!Ref": secret} for statement in actual.values()):
        fail("migration/runtime roles must read only their configuration and their own credential")

for name, metric, statistic, operator, threshold, unit in (
    ("RelationalDatabaseCpuHighAlarm", "CPUUtilization", "Average", "GreaterThanOrEqualToThreshold", 80, None),
    ("RelationalDatabaseFreeStorageLowAlarm", "FreeStorageSpace", "Minimum", "LessThanOrEqualToThreshold", 3221225472, "Bytes"),
    ("RelationalDatabaseConnectionsHighAlarm", "DatabaseConnections", "Maximum", "GreaterThanOrEqualToThreshold", 60, None),
):
    alarm = props(foundation, name, "AWS::CloudWatch::Alarm")
    if [alarm.get("Namespace"), alarm.get("MetricName"), alarm.get("Statistic"), alarm.get("ComparisonOperator"), alarm.get("Threshold")] != ["AWS/RDS", metric, statistic, operator, threshold] or [alarm.get("Period"), alarm.get("EvaluationPeriods"), alarm.get("DatapointsToAlarm"), alarm.get("TreatMissingData")] != [300, 3, 3, "breaching"] or alarm.get("AlarmActions") != [{"!Ref": "AlarmTopic"}] or (unit and alarm.get("Unit") != unit):
        fail(f"{name} must retain reviewed RDS metric alarm policy")
    if alarm.get("Dimensions") != [{"Name": "DBInstanceIdentifier", "Value": {"!Ref": "RelationalDatabase"}}]:
        fail(f"{name} must be scoped only to the relational database")
events = props(foundation, "RelationalDatabaseEventSubscription", "AWS::RDS::EventSubscription")
if events.get("SnsTopicArn") != {"!Ref": "AlarmTopic"} or events.get("SourceType") != "db-instance" or events.get("SourceIds") != [{"!Ref": "RelationalDatabase"}] or events.get("EventCategories") != ["availability", "backup", "failure", "low storage", "maintenance", "recovery"]:
    fail("RDS events must be limited to the relational instance and existing alert destination")

reference = profile.get("persistence", {}).get("relational_reference", {})
if reference.get("status") != "stage-4-source-defined-change-set-pending" or reference.get("stage_3_disposable_local_real_engine_proof", {}).get("result") != "passed" or reference.get("stage_4_source_definition", {}).get("database_name") != "platformsmoke":
    fail("target profile must record passed real-engine proof and source-defined unprovisioned target")

if failures:
    for message in failures:
        print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)
print("PostgreSQL relational-reference static policy check passed.")
PY
