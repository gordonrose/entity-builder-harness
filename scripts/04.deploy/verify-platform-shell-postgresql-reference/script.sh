#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-postgresql-reference
#   version: 3
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
    "foundation/relational-work-queue.yml",
}
if not required_fragments.issubset(set(manifest.get("fragments", []))):
    fail("foundation must retain the relational responsibility-focused source fragments")
if foundation.get("Parameters", {}).get("PrivateSubnetIds", {}).get("Type") != "List<AWS::EC2::Subnet::Id>":
    fail("private subnet identifiers must be typed deployment inputs, not source values")

subnets = props(foundation, "RelationalDatabaseSubnetGroup", "AWS::RDS::DBSubnetGroup")
if subnets.get("DBSubnetGroupName") != "kanbien-staging-platform-relational-private" or subnets.get("SubnetIds") != {"!Ref": "PrivateSubnetIds"}:
    fail("RDS subnet group must use only the supplied private subnet list")
group = props(foundation, "RelationalDatabaseSecurityGroup", "AWS::EC2::SecurityGroup")
expected_database_egress = [{
    "Description": "Loopback-only rule that prevents default external database egress.",
    "IpProtocol": "-1",
    "CidrIp": "127.0.0.1/32",
}]
if group.get("VpcId") != {"!Ref": "VpcId"} or group.get("SecurityGroupEgress") != expected_database_egress or "SecurityGroupIngress" in group:
    fail("database group must be VPC-local, loopback-only outbound, and use separate ingress rules")
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
relay = props(foundation, "RelationalRelayTaskRole", "AWS::IAM::Role")
worker = props(foundation, "RelationalWorkerTaskRole", "AWS::IAM::Role")
restore_verification = props(foundation, "RelationalRestoreVerificationTaskRole", "AWS::IAM::Role")
execution = props(foundation, "RelationalTaskExecutionRole", "AWS::IAM::Role")
for name, role in (("bootstrap", bootstrap), ("migration", migration), ("runtime", runtime), ("relay", relay), ("worker", worker), ("restore-verification", restore_verification), ("execution", execution)):
    if role.get("AssumeRolePolicyDocument", {}).get("Statement") != [{"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}]:
        fail(f"{name} task role must be ECS-task-only")
bootstrap_statement = statements(bootstrap).get("ReadOnlyRelationalBootstrapAndRoleCredentials", {})
if set(statements(bootstrap)) != {"ReadOnlyRelationalBootstrapAndRoleCredentials"} or bootstrap_statement.get("Action") != ["secretsmanager:GetSecretValue"] or bootstrap_statement.get("Resource") != [{"!GetAtt": "RelationalDatabase.MasterUserSecret.SecretArn"}, {"!Ref": "RelationalMigrationSecret"}, {"!Ref": "RelationalRuntimeSecret"}]:
    fail("bootstrap role must have only the three exact credential reads")
for role, secret in ((migration, "RelationalMigrationSecret"), (runtime, "RelationalRuntimeSecret")):
    actual = statements(role)
    if len(actual) != 2 or not any(statement.get("Action") == ["ssm:GetParameter"] and statement.get("Resource") == {"!GetAtt": "RelationalTargetConfiguration.Arn"} for statement in actual.values()) or not any(statement.get("Action") == ["secretsmanager:GetSecretValue"] and statement.get("Resource") == {"!Ref": secret} for statement in actual.values()):
        fail("migration/runtime roles must read only their configuration and their own credential")
restore_statements = statements(restore_verification)
if len(restore_statements) != 2 or not any(statement.get("Action") == ["ssm:GetParameter"] and statement.get("Resource") == {"!GetAtt": "RelationalTargetConfiguration.Arn"} for statement in restore_statements.values()) or not any(statement.get("Action") == ["secretsmanager:GetSecretValue"] and statement.get("Resource") == {"!Ref": "RelationalRuntimeSecret"} for statement in restore_statements.values()):
    fail("restore verification must read only its configuration and runtime credential")

for role, sid, action in (
    (relay, "SendOnlyTheRelationalSmokeQueue", ["sqs:SendMessage"]),
    (worker, "ConsumeOnlyTheRelationalSmokeQueue", ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:ChangeMessageVisibility", "sqs:GetQueueAttributes"]),
):
    actual = statements(role)
    if len(actual) != 3 or not any(statement.get("Action") == ["ssm:GetParameter"] and statement.get("Resource") == {"!GetAtt": "RelationalTargetConfiguration.Arn"} for statement in actual.values()) or not any(statement.get("Action") == ["secretsmanager:GetSecretValue"] and statement.get("Resource") == {"!Ref": "RelationalRuntimeSecret"} for statement in actual.values()) or actual.get(sid, {}).get("Action") != action or actual.get(sid, {}).get("Resource") != {"!GetAtt": "RelationalSmokeQueue.Arn"}:
        fail("relay and worker roles must separate their exact relational queue permissions")

execution_statements = statements(execution)
if set(execution_statements) != {"ReadOnlyRelationalTaskConfiguration", "ReadOnlyRelationalTaskCredentials"} or execution_statements.get("ReadOnlyRelationalTaskConfiguration", {}).get("Action") != ["ssm:GetParameters"] or execution_statements.get("ReadOnlyRelationalTaskConfiguration", {}).get("Resource") != {"!GetAtt": "RelationalTargetConfiguration.Arn"} or execution_statements.get("ReadOnlyRelationalTaskCredentials", {}).get("Action") != ["secretsmanager:GetSecretValue"] or execution_statements.get("ReadOnlyRelationalTaskCredentials", {}).get("Resource") != [{"!GetAtt": "RelationalDatabase.MasterUserSecret.SecretArn"}, {"!Ref": "RelationalMigrationSecret"}, {"!Ref": "RelationalRuntimeSecret"}]:
    fail("relational task execution must inject only the reviewed configuration and three target-owned credentials")
if execution.get("ManagedPolicyArns") != ["arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"]:
    fail("relational task execution must retain only the reviewed ECS execution managed policy")

for name, expected_name, retention, visibility in (
    ("RelationalSmokeQueue", "kanbien-staging-platform-relational-smoke", 345600, 120),
    ("RelationalSmokeDeadLetterQueue", "kanbien-staging-platform-relational-smoke-dlq", 1209600, None),
):
    queue = props(foundation, name, "AWS::SQS::Queue")
    if queue.get("QueueName") != expected_name or queue.get("MessageRetentionPeriod") != retention or queue.get("ReceiveMessageWaitTimeSeconds") != 20 or queue.get("SqsManagedSseEnabled") is not True:
        fail("relational smoke queues must retain reviewed names, long-poll, retention, and managed encryption")
    if visibility is not None and (queue.get("VisibilityTimeout") != visibility or queue.get("MaximumMessageSize") != 262144 or queue.get("DelaySeconds") != 0 or queue.get("RedrivePolicy") != {"deadLetterTargetArn": {"!GetAtt": "RelationalSmokeDeadLetterQueue.Arn"}, "maxReceiveCount": 5}):
        fail("relational source queue must retain its bounded delivery and redrive policy")
for name, queue_name in (("RelationalSmokeQueueTransportPolicy", "RelationalSmokeQueue"), ("RelationalSmokeDeadLetterQueueTransportPolicy", "RelationalSmokeDeadLetterQueue")):
    policy = props(foundation, name, "AWS::SQS::QueuePolicy")
    if policy.get("Queues") != [{"!Ref": queue_name}] or policy.get("PolicyDocument") != {"Version": "2012-10-17", "Statement": [{"Sid": "DenyInsecureTransport", "Effect": "Deny", "Principal": "*", "Action": "sqs:*", "Resource": {"!GetAtt": f"{queue_name}.Arn"}, "Condition": {"Bool": {"aws:SecureTransport": False}}}]}:
        fail("relational queue policies must deny non-TLS transport only for their reviewed queue")

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
if reference.get("status") != "stage-5-live-boundary-proven-stage-6-bootstrap-recovery-4-source-ready" or reference.get("stage_3_disposable_local_real_engine_proof", {}).get("result") != "passed" or reference.get("stage_4_source_definition", {}).get("database_name") != "platformsmoke" or reference.get("connection_security", {}).get("database_egress") != "explicit-loopback-only-127-0-0-1-32-no-external-ipv4-ipv6-prefix-list-or-security-group-destination" or reference.get("stage_5_database_egress_remediation", {}).get("status") != "executed-and-live-boundary-proven" or reference.get("stage_5_database_egress_remediation", {}).get("parameter_group_representation") != "rds-force-ssl-required-provider-normalization-classified-safe":
    fail("target profile must record the passed real-engine proof and exact default-egress remediation boundary")
stage_six = reference.get("stage_6_relational_smoke_composition", {})
if stage_six.get("status") != "candidate-preflight-dormant-definition-deployed-current-image-attempt-terminal-new-immutable-candidate-required" or stage_six.get("fixed_acceptance") != "one-opaque-harmless-work-item-only" or stage_six.get("task_security", {}).get("database_tls") != "verify-full-with-pinned-public-eu-west-1-rds-ca-bundle" or stage_six.get("task_security", {}).get("relay_permission") != "send-only-to-isolated-relational-queue" or stage_six.get("task_security", {}).get("worker_permission") != "receive-delete-visibility-and-attributes-only-on-isolated-relational-queue":
    fail("target profile must define the reviewed isolated relational smoke task boundary")
diagnostic = stage_six.get("control", {}).get("bootstrap_recovery_diagnostic", {})
if diagnostic != {
    "metadata_fallback": "allowlisted-task-stop-code-and-bootstrap-container-reason-classification-only-after-direct-and-derived-log-stream-unavailable",
    "derived_log_stream_prefix": "relational-bootstrap/relational-bootstrap/",
    "output_policy": "safe-failure-category-only-no-stop-code-reason-task-identifier-log-text-or-provider-payload",
    "categories": [
        "bootstrap-task-log-stream-unavailable", "bootstrap-task-log-events-unavailable", "bootstrap-task-log-stream-empty",
        "bootstrap-runtime-module-unavailable", "bootstrap-certificate-authority-unavailable", "bootstrap-database-authentication-failure",
        "bootstrap-database-authorization-failure", "bootstrap-database-connectivity-failure", "bootstrap-database-tls-failure",
        "bootstrap-input-validation-failure", "bootstrap-password-quotation-failure", "bootstrap-role-provisioning-failure",
        "bootstrap-database-grant-failure", "bootstrap-schema-provisioning-failure", "bootstrap-schema-grant-failure",
        "bootstrap-workload-failure-unclassified", "bootstrap-workload-failure-log-marker-unavailable", "bootstrap-image-retrieval-failure",
        "bootstrap-secret-injection-failure", "bootstrap-log-driver-initialization-failure", "bootstrap-resource-initialization-failure",
        "bootstrap-task-startup-failure", "bootstrap-essential-container-exited-without-log-stream", "bootstrap-task-terminal-metadata-unclassified",
    ],
}:
    fail("target profile must retain the reviewed no-log-stream terminal-metadata diagnostic boundary")

certificate = Path("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt")
if not certificate.is_file() or __import__("hashlib").sha256(certificate.read_bytes()).hexdigest() != "a11cf9a1d0aadd7db86f92cbaa496466daeb501bf1c5e429d8ce8914a01c15d6":
    fail("the public eu-west-1 RDS CA bundle must be present and pinned by digest")
task_helper = Path("infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-task.ts").read_text(encoding="utf-8")
if 'readFileSync("/app/assets/rds-eu-west-1-bundle.crt", "utf8")' not in task_helper or 'mode: "verify-full"' not in task_helper:
    fail("relational task helper must require the pinned RDS CA bundle and verify-full TLS")
if 'const dbname = stringField(candidate, "dbname")' in task_helper or 'database: "platformsmoke"' not in task_helper:
    fail("relational task helper must use the reviewed configuration database name rather than require an optional secret dbname field")

# Local CA binding is source qualification only; no selected target descriptor
# may activate it. Its fixed path cannot become an arbitrary file reader.
for descriptor in Path("infra/04.deploy/03.product/targets/kanbien/staging").rglob("*"):
    if descriptor.is_file() and descriptor.suffix in {".yml", ".yaml", ".json"}:
        if any(field in descriptor.read_text() for field in ("RELATIONAL_TLS_CA_MODE", "RELATIONAL_LOCAL_QUALIFICATION_ID", "/run/release-control/ca.crt")):
            fail("local qualification TLS inputs must never appear in staging target descriptors")

bootstrap_entrypoint = Path("infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts").read_text(encoding="utf-8")
migration_entrypoint = Path("infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-migration.main.ts").read_text(encoding="utf-8")
if 'ALTER DEFAULT PRIVILEGES FOR ROLE' in bootstrap_entrypoint or 'ALTER DEFAULT PRIVILEGES IN SCHEMA platform_smoke GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psmokeruntime' not in migration_entrypoint:
    fail("default privileges must be owned by the migration identity rather than the bootstrap identity")
if 'writeOutcome("bootstrap_completed", "failed", bootstrapFailureCategory(error, phase))' not in bootstrap_entrypoint or 'bootstrap-database-authentication-failure' not in bootstrap_entrypoint or 'bootstrap-role-provisioning-failure' not in bootstrap_entrypoint:
    fail("bootstrap must emit only its reviewed safe failure category rather than raw workload details")

if failures:
    for message in failures:
        print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)
print("PostgreSQL relational-reference static policy check passed.")
PY
