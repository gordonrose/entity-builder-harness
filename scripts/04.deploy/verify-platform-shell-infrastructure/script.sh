#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-infrastructure
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Statically enforce the minimum security and deployment invariants of the Kanbien staging platform-shell CloudFormation templates.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-infrastructure-check
#     path: package.json
#   - id: github.workflow.deploy-platform-shell-staging
#     path: .github/workflows/deploy-platform-shell-staging.yml

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

RENDERED_FOUNDATION="$(mktemp "${TMPDIR:-/tmp}/platform-shell-foundation.XXXXXX.yml")"
trap 'rm -f "$RENDERED_FOUNDATION"' EXIT
bash scripts/04.deploy/render-platform-shell-foundation-template/script.sh \
  --output "$RENDERED_FOUNDATION" >/dev/null
export RENDERED_FOUNDATION

python3 - <<'PY'
import os
from pathlib import Path
import sys

try:
    import yaml
except ImportError as error:
    raise SystemExit("ERROR: PyYAML is required. Install PyYAML==6.0.2 before this check.") from error


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


def load(path):
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.load(handle, Loader=CfnLoader)


def fail(message):
    failures.append(message)


def resource(template, name):
    value = template.get("Resources", {}).get(name)
    if value is None:
        fail(f"missing resource: {name}")
        return {}
    return value


def properties(template, name, expected_type):
    value = resource(template, name)
    if value.get("Type") != expected_type:
        fail(f"{name} must be {expected_type}")
    return value.get("Properties", {})


def contains_intrinsic(value, key, expected=None):
    if isinstance(value, dict):
        if key in value and (expected is None or value[key] == expected):
            return True
        return any(contains_intrinsic(child, key, expected) for child in value.values())
    if isinstance(value, list):
        return any(contains_intrinsic(child, key, expected) for child in value)
    return False


def contains_value(value, expected):
    if value == expected:
        return True
    if isinstance(value, dict):
        return any(contains_value(child, expected) for child in value.values())
    if isinstance(value, list):
        return any(contains_value(child, expected) for child in value)
    return False


foundation = load(os.environ["RENDERED_FOUNDATION"])
service = load("infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml")
target_profile = load("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
failures = []

expected_foundation_resources = {
    "PlatformShellLogGroup",
    "RateLimitTable",
    "TaskExecutionRole",
    "TaskRole",
    "ServiceDeploymentExecutionRole",
    "ServiceSecurityGroup",
    "TargetGroup",
    "HostRule",
    "DnsAlias",
    "WebAcl",
    "WebAclAssociation",
    "AlarmTopic",
    "AlarmTopicPolicy",
    "AlarmSubscription",
    "UnhealthyTargetAlarm",
    "Target5xxAlarm",
}
expected_foundation_parameters = {
    "VpcId",
    "VpcCidr",
    "PublicSubnetIds",
    "ExistingAlbArn",
    "ExistingAlbSecurityGroupId",
    "ExistingHttpsListenerArn",
    "ExistingAlbDnsName",
    "ExistingAlbCanonicalHostedZoneId",
    "HostedZoneId",
    "HostName",
    "ListenerRulePriority",
    "AlarmEmail",
    "LogRetentionDays",
}
expected_foundation_outputs = {
    "LogGroupName",
    "RateLimitTableName",
    "RateLimitTableArn",
    "TaskExecutionRoleArn",
    "TaskRoleArn",
    "ServiceDeploymentExecutionRoleArn",
    "ServiceSecurityGroupId",
    "TargetGroupArn",
    "PublicSubnetIdsCsv",
    "HostName",
    "AlarmTopicArn",
    "WebAclArn",
}
if set(foundation.get("Parameters", {})) != expected_foundation_parameters:
    fail("rendered foundation must retain the reviewed parameter interface")
if set(foundation.get("Resources", {})) != expected_foundation_resources:
    fail("rendered foundation must contain exactly the reviewed resource set")
if set(foundation.get("Outputs", {})) != expected_foundation_outputs:
    fail("rendered foundation must retain the reviewed service-stack output interface")

for forbidden_type in ("AWS::ECR::Repository", "AWS::Cognito::UserPool", "AWS::ElasticLoadBalancingV2::LoadBalancer"):
    if any(item.get("Type") == forbidden_type for item in foundation.get("Resources", {}).values()):
        fail(f"foundation must treat existing infrastructure as inputs, not create {forbidden_type}")

rate_table = properties(foundation, "RateLimitTable", "AWS::DynamoDB::Table")
if rate_table.get("BillingMode") != "PAY_PER_REQUEST":
    fail("RateLimitTable must use PAY_PER_REQUEST for the low-traffic initial target")
if rate_table.get("DeletionProtectionEnabled") is not True:
    fail("RateLimitTable must enable deletion protection")
if rate_table.get("TimeToLiveSpecification") != {"AttributeName": "expiresAt", "Enabled": True}:
    fail("RateLimitTable must expire counter records through expiresAt TTL")
if rate_table.get("SSESpecification", {}).get("SSEEnabled") is not True:
    fail("RateLimitTable must enable server-side encryption")

task_policy = properties(foundation, "TaskRole", "AWS::IAM::Role").get("Policies", [])
task_actions = [action for policy in task_policy for statement in policy.get("PolicyDocument", {}).get("Statement", []) for action in statement.get("Action", [])]
if task_actions != ["dynamodb:UpdateItem"]:
    fail("TaskRole must have only DynamoDB UpdateItem capability for the shared limiter")

service_deployment_role = properties(foundation, "ServiceDeploymentExecutionRole", "AWS::IAM::Role")
service_deployment_policy = service_deployment_role.get("Policies", [{}])[0].get("PolicyDocument", {}).get("Statement", [])
if not contains_value(service_deployment_policy, "ecs:RegisterTaskDefinition"):
    fail("ServiceDeploymentExecutionRole must be able to register only the service task definition")
if not contains_intrinsic(service_deployment_policy, "!GetAtt", "TaskExecutionRole.Arn") or not contains_intrinsic(service_deployment_policy, "!GetAtt", "TaskRole.Arn"):
    fail("ServiceDeploymentExecutionRole must pass only the platform-shell task roles")

security_group = properties(foundation, "ServiceSecurityGroup", "AWS::EC2::SecurityGroup")
for ingress in security_group.get("SecurityGroupIngress", []):
    if ingress.get("SourceSecurityGroupId") != {"!Ref": "ExistingAlbSecurityGroupId"}:
        fail("ServiceSecurityGroup ingress must come only from ExistingAlbSecurityGroupId")
    if ingress.get("FromPort") != 3000 or ingress.get("ToPort") != 3000:
        fail("ServiceSecurityGroup ingress must allow only TCP 3000")
if any(rule.get("CidrIp") == "0.0.0.0/0" and rule.get("FromPort") != 443 for rule in security_group.get("SecurityGroupEgress", [])):
    fail("ServiceSecurityGroup may use public egress only for TLS port 443")

target_group = properties(foundation, "TargetGroup", "AWS::ElasticLoadBalancingV2::TargetGroup")
if target_group.get("TargetType") != "ip" or target_group.get("HealthCheckPath") != "/livez":
    fail("TargetGroup must use IP targets and the public /livez health check")

host_rule = properties(foundation, "HostRule", "AWS::ElasticLoadBalancingV2::ListenerRule")
if not contains_intrinsic(host_rule.get("Conditions", []), "!Ref", "HostName"):
    fail("HostRule must use the target-owned exact HostName condition")

web_acl = properties(foundation, "WebAcl", "AWS::WAFv2::WebACL")
if web_acl.get("Scope") != "REGIONAL" or web_acl.get("DefaultAction") != {"Allow": {}}:
    fail("WebAcl must be a regional default-allow ACL so legacy hosts are unaffected")
for rule in web_acl.get("Rules", []):
    if not contains_intrinsic(rule.get("Statement", {}), "!Ref", "HostName"):
        fail(f"WebAcl rule {rule.get('Name', '<unnamed>')} must be scoped to HostName")

web_acl_association = properties(foundation, "WebAclAssociation", "AWS::WAFv2::WebACLAssociation")
if web_acl_association.get("ResourceArn") != {"!Ref": "ExistingAlbArn"}:
    fail("WebAclAssociation must apply only to the declared existing ALB input")

log_group = properties(foundation, "PlatformShellLogGroup", "AWS::Logs::LogGroup")
if log_group.get("RetentionInDays") != {"!Ref": "LogRetentionDays"}:
    fail("PlatformShellLogGroup must use the reviewed retention parameter")

for alarm_name in ("UnhealthyTargetAlarm", "Target5xxAlarm"):
    alarm = properties(foundation, alarm_name, "AWS::CloudWatch::Alarm")
    if not contains_intrinsic(alarm.get("AlarmActions", []), "!Ref", "AlarmTopic"):
        fail(f"{alarm_name} must notify AlarmTopic")

image_parameter = service.get("Parameters", {}).get("ImageUri", {})
if "@sha256" not in image_parameter.get("AllowedPattern", ""):
    fail("service ImageUri must require an immutable digest")

container = properties(service, "TaskDefinition", "AWS::ECS::TaskDefinition").get("ContainerDefinitions", [{}])[0]
if container.get("ReadonlyRootFilesystem") is not True:
    fail("platform-shell container must use a read-only root filesystem")
if container.get("Secrets"):
    fail("platform-shell task must not receive a Cognito client secret")
environment = {entry.get("Name"): entry.get("Value") for entry in container.get("Environment", [])}
required_environment = {
    "PLATFORM_DEPLOYMENT_EXPOSURE": "public",
    "PLATFORM_AUTH_PROVIDER": "cognito",
    "PLATFORM_RATE_LIMIT_PROVIDER": "dynamodb",
    "PLATFORM_TRUSTED_INGRESS_MODE": "alb-security-group-only",
    "PLATFORM_HEALTH_LIVEZ_EXPOSURE": "public",
    "PLATFORM_HEALTH_READYZ_EXPOSURE": "authenticated",
}
for key, value in required_environment.items():
    if environment.get(key) != value:
        fail(f"platform-shell task must set {key}={value}")

target_environment = target_profile.get("config", {}).get("non_secret_env", {})
for key, value in target_environment.items():
    if key == "PLATFORM_RATE_LIMIT_DYNAMODB_TABLE":
        if not contains_intrinsic(environment.get(key), "!Sub", "${FoundationStackName}-RateLimitTableName"):
            fail("platform-shell task must obtain the shared limiter table name from the foundation stack")
    elif environment.get(key) != value:
        fail(f"service template must match target-profile non-secret value for {key}")

if rate_table.get("TableName") != target_profile.get("rate_limiting", {}).get("shared_adapter", {}).get("table_name"):
    fail("foundation rate-limit table name must match the target profile")
if foundation.get("Parameters", {}).get("HostName", {}).get("Default") != target_profile.get("aws", {}).get("alb", {}).get("host_rule"):
    fail("foundation hostname default must match the target profile")
if foundation.get("Parameters", {}).get("ListenerRulePriority", {}).get("Default") != target_profile.get("aws", {}).get("alb", {}).get("host_rule_priority"):
    fail("foundation listener priority default must match the target profile")

ecs_service = properties(service, "Service", "AWS::ECS::Service")
if ecs_service.get("EnableExecuteCommand") is not False:
    fail("ECS execute-command must remain disabled for the initial public proof")
breaker = ecs_service.get("DeploymentConfiguration", {}).get("DeploymentCircuitBreaker", {})
if breaker != {"Enable": True, "Rollback": True}:
    fail("ECS deployment circuit breaker must be enabled with rollback")

if failures:
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    raise SystemExit(1)

print("Platform-shell infrastructure static policy check passed.")
PY
