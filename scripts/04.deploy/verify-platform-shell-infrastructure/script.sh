#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-infrastructure
#   version: 3
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
#   - id: deploy.rules.03-product.platform-target-alerting-policy
#     path: docs/04.deploy/rules/03.product/platform-target-alerting-policy.yml

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

RENDERED_FOUNDATION="$(mktemp "${TMPDIR:-/tmp}/platform-shell-foundation.XXXXXX.yml")"
trap 'rm -f "$RENDERED_FOUNDATION"' EXIT
bash scripts/04.deploy/render-platform-shell-foundation-template/script.sh \
  --output "$RENDERED_FOUNDATION" >/dev/null
bash -n scripts/04.deploy/verify-platform-shell-observability-prerequisites/script.sh
export RENDERED_FOUNDATION

python3 - <<'PY'
import os
from pathlib import Path
import sys
import json

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


def dimensions_by_name(alarm):
    dimensions = alarm.get("Dimensions", [])
    if not isinstance(dimensions, list):
        return {}
    return {item.get("Name"): item.get("Value") for item in dimensions if isinstance(item, dict)}


def require_alarm_tags(alarm, alarm_id):
    expected_tags = [
        {"Key": "service", "Value": "platform-shell"},
        {"Key": "environment", "Value": "staging"},
        {"Key": "managed-by", "Value": "cloudformation"},
    ]
    if alarm.get("Tags") != expected_tags:
        fail(f"{alarm_id} must carry the reviewed platform-shell ownership tags")


def expected_dimension_value(resolver):
    values = {
        "existing-alb-resource-suffix": {"!Select": [1, {"!Split": ["loadbalancer/", {"!Ref": "ExistingAlbArn"}]}]},
        "foundation-target-group-full-name": {"!GetAtt": "TargetGroup.TargetGroupFullName"},
        "cluster-name-from-cluster-arn": {"!Select": [1, {"!Split": ["/", {"!Ref": "ClusterArn"}]}]},
        "service-name": {"!Ref": "ServiceName"},
    }
    return values.get(resolver)


def expected_threshold(value):
    if isinstance(value, dict) and value.get("value_source") == "service-desired-count":
        return {"!Ref": "DesiredCount"}
    if isinstance(value, dict):
        return value.get("value")
    return None


def check_profile_alarm(definition, foundation, service, severity_vocabulary):
    alarm_id = definition.get("id", "<missing-id>")
    implementation = definition.get("implementation", {})
    stack = implementation.get("stack")
    template = {"foundation": foundation, "service": service}.get(stack)
    if template is None:
        fail(f"{alarm_id} must name foundation or service as its implementation stack")
        return

    logical_resource = implementation.get("logical_resource")
    alarm = properties(template, logical_resource or f"{alarm_id}-missing-resource", "AWS::CloudWatch::Alarm")
    signal = definition.get("signal", {})
    condition = definition.get("condition", {})
    evaluation = definition.get("evaluation", {})
    response = definition.get("response", {})

    if not isinstance(definition.get("purpose"), str) or not definition["purpose"].strip():
        fail(f"{alarm_id} target-profile definition must state its operational purpose")
    if response.get("severity") not in severity_vocabulary:
        fail(f"{alarm_id} target-profile definition must use a declared target-policy severity")

    expected_properties = {
        "AlarmName": implementation.get("alarm_name"),
        "AlarmDescription": implementation.get("alarm_description"),
        "Namespace": signal.get("namespace"),
        "MetricName": signal.get("metric"),
        "Statistic": condition.get("statistic"),
        "ComparisonOperator": condition.get("comparison_operator"),
        "Threshold": expected_threshold(condition.get("threshold")),
        "Unit": condition.get("unit"),
        "Period": evaluation.get("period_seconds"),
        "EvaluationPeriods": evaluation.get("evaluation_periods"),
        "DatapointsToAlarm": evaluation.get("datapoints_to_alarm"),
        "TreatMissingData": evaluation.get("treat_missing_data"),
    }
    for key, expected in expected_properties.items():
        if expected is None:
            fail(f"{alarm_id} target-profile definition must set {key}")
        elif alarm.get(key) != expected:
            fail(f"{logical_resource} {key} must match target-profile alarm {alarm_id}")

    declared_dimensions = signal.get("dimensions")
    if not isinstance(declared_dimensions, list):
        fail(f"{alarm_id} target-profile definition must list metric dimensions")
    else:
        actual_dimensions = dimensions_by_name(alarm)
        expected_names = [item.get("name") for item in declared_dimensions if isinstance(item, dict)]
        if set(actual_dimensions) != set(expected_names) or len(actual_dimensions) != len(expected_names):
            fail(f"{logical_resource} metric dimensions must match target-profile alarm {alarm_id}")
        for dimension in declared_dimensions:
            if not isinstance(dimension, dict):
                fail(f"{alarm_id} target-profile dimensions must be objects")
                continue
            name = dimension.get("name")
            expected_value = expected_dimension_value(dimension.get("resolver"))
            if expected_value is None:
                fail(f"{alarm_id} has an unsupported or missing dimension resolver for {name}")
            elif actual_dimensions.get(name) != expected_value:
                fail(f"{logical_resource} dimension {name} must use the target-profile resolver")

    if response.get("alarm_destination") != "foundation-alarm-topic":
        fail(f"{alarm_id} must use the reviewed foundation-alarm-topic destination")
    elif stack == "foundation" and not contains_intrinsic(alarm.get("AlarmActions", []), "!Ref", "AlarmTopic"):
        fail(f"{logical_resource} must notify the foundation AlarmTopic")
    elif stack == "service" and not contains_intrinsic(
        alarm.get("AlarmActions", []),
        "!Sub",
        "${FoundationStackName}-AlarmTopicArn",
    ):
        fail(f"{logical_resource} must import and notify the foundation AlarmTopic")

    runbook = response.get("runbook")
    if not isinstance(runbook, str) or not Path(runbook).is_file():
        fail(f"{alarm_id} must reference a repository runbook")
    require_alarm_tags(alarm, logical_resource or alarm_id)


foundation = load(os.environ["RENDERED_FOUNDATION"])
service = load("infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml")
target_profile = load("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
github_workflow = Path(".github/workflows/deploy-platform-shell-staging.yml").read_text(encoding="utf-8")
with Path("infra/04.deploy/03.product/targets/kanbien/staging/iam/github-platform-shell-staging-deploy-policy.json").open(encoding="utf-8") as handle:
    github_deployment_policy = json.load(handle)
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
    "PlatformHostnameCertificate",
    "PlatformHostnameCertificateAttachment",
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
    "PlatformHostnameCertificateArn",
}
expected_service_resources = {
    "TaskDefinition",
    "Service",
    "EcsRunningCountAlarm",
    "EcsHighCpuAlarm",
    "EcsHighMemoryAlarm",
}
if set(foundation.get("Parameters", {})) != expected_foundation_parameters:
    fail("rendered foundation must retain the reviewed parameter interface")
if set(foundation.get("Resources", {})) != expected_foundation_resources:
    fail("rendered foundation must contain exactly the reviewed resource set")
if set(foundation.get("Outputs", {})) != expected_foundation_outputs:
    fail("rendered foundation must retain the reviewed service-stack output interface")
if set(service.get("Resources", {})) != expected_service_resources:
    fail("service template must contain exactly the reviewed workload and service-alarm resources")

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

platform_certificate = properties(foundation, "PlatformHostnameCertificate", "AWS::CertificateManager::Certificate")
platform_certificate_profile = target_profile.get("aws", {}).get("alb", {}).get("platform_hostname_certificate", {})
if platform_certificate.get("DomainName") != platform_certificate_profile.get("primary_domain"):
    fail("PlatformHostnameCertificate must use the target-profile primary domain")
if platform_certificate.get("SubjectAlternativeNames") != platform_certificate_profile.get("subject_alternative_names"):
    fail("PlatformHostnameCertificate SANs must match the target profile")
if platform_certificate.get("ValidationMethod") != "DNS":
    fail("PlatformHostnameCertificate must use DNS validation")
if not contains_intrinsic(platform_certificate.get("DomainValidationOptions", []), "!Ref", "HostedZoneId"):
    fail("PlatformHostnameCertificate must validate in the declared existing hosted zone")
if platform_certificate.get("CertificateTransparencyLoggingPreference") != "ENABLED":
    fail("PlatformHostnameCertificate must enable certificate-transparency logging")

platform_certificate_attachment = properties(
    foundation,
    "PlatformHostnameCertificateAttachment",
    "AWS::ElasticLoadBalancingV2::ListenerCertificate",
)
if platform_certificate_attachment.get("ListenerArn") != {"!Ref": "ExistingHttpsListenerArn"}:
    fail("PlatformHostnameCertificateAttachment must use only the declared existing HTTPS listener")
if not contains_intrinsic(platform_certificate_attachment.get("Certificates", []), "!Ref", "PlatformHostnameCertificate"):
    fail("PlatformHostnameCertificateAttachment must attach the foundation-owned certificate")

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

observability = target_profile.get("observability", {})
alarm_policy = observability.get("policy", {})
severity_vocabulary = []
expected_alarm_policy = {
    "standard": "docs/04.deploy/rules/03.product/platform-target-alerting-policy.yml",
    "catalogue_index": "infra/04.deploy/03.product/targets/README.md",
    "canonical_catalogue": "observability.alarms",
}
if not isinstance(alarm_policy, dict):
    fail("target profile must declare an observability alarm-policy object")
else:
    for key, expected in expected_alarm_policy.items():
        if alarm_policy.get(key) != expected:
            fail(f"target profile alarm policy must set {key} to the governed value")
    candidate_severity_vocabulary = alarm_policy.get("severity_vocabulary")
    if not isinstance(candidate_severity_vocabulary, list) or not all(isinstance(value, str) for value in candidate_severity_vocabulary):
        fail("target profile alarm policy severities must be strings")
    elif set(candidate_severity_vocabulary) != {"critical", "warning"} or len(candidate_severity_vocabulary) != 2:
        fail("target profile alarm policy must declare exactly critical and warning severities")
    else:
        severity_vocabulary = candidate_severity_vocabulary

catalogue_index_path = Path(expected_alarm_policy["catalogue_index"])
if not catalogue_index_path.is_file():
    fail("target profile alarm catalogue index must exist")
else:
    catalogue_index = catalogue_index_path.read_text(encoding="utf-8")
    for required_catalogue_text in (
        "kanbien/staging/target-profile.yml",
        "kanbien/staging/cloudformation/foundation/alerting.yml",
        "kanbien/staging/cloudformation/service.yml",
        "platform-shell-staging-alarms.md",
    ):
        if required_catalogue_text not in catalogue_index:
            fail("target alarm catalogue index must link the staging policy, implementation, and runbook")

alarm_destination = observability.get("alarm_destination", {})
if alarm_destination.get("id") != "foundation-alarm-topic":
    fail("target profile must identify the foundation alarm topic as its alarm destination")
if target_profile.get("deployment", {}).get("cloudformation", {}).get("validation", {}).get("service_observability_prerequisite_check") != "scripts/04.deploy/verify-platform-shell-observability-prerequisites/script.sh":
    fail("target profile must declare the governed service observability prerequisite check")

target_cluster_arn = target_profile.get("aws", {}).get("cluster", "")
target_cluster_name = target_cluster_arn.rsplit("/", 1)[-1]
target_service_name = target_profile.get("runtime", {}).get("server", {}).get("service")
for required_workflow_text in (
    "OBSERVABILITY_PREREQUISITE_CHECK: scripts/04.deploy/verify-platform-shell-observability-prerequisites/script.sh",
    f"ECS_CLUSTER: {target_cluster_name}",
    f"ECS_SERVICE: {target_service_name}",
    'bash "$OBSERVABILITY_PREREQUISITE_CHECK"',
    '--cluster "$ECS_CLUSTER"',
    '--service "$ECS_SERVICE"',
):
    if required_workflow_text not in github_workflow:
        fail("GitHub deployment workflow must run the reviewed ECS telemetry prerequisite check before service deployment")

github_cluster_telemetry_statement = next(
    (item for item in github_deployment_policy.get("Statement", []) if item.get("Sid") == "ReadSelectedPlatformShellClusterTelemetryPrerequisite"),
    None,
)
if github_cluster_telemetry_statement is None:
    fail("GitHub deployment identity policy must include the selected-cluster telemetry read statement")
elif github_cluster_telemetry_statement.get("Effect") != "Allow" or github_cluster_telemetry_statement.get("Action") != ["ecs:DescribeClusters"] or github_cluster_telemetry_statement.get("Resource") != target_cluster_arn:
    fail("GitHub deployment identity must read ECS telemetry settings only from the selected cluster")

github_metric_telemetry_statement = next(
    (item for item in github_deployment_policy.get("Statement", []) if item.get("Sid") == "DiscoverCloudWatchTelemetryPrerequisiteMetric"),
    None,
)
if github_metric_telemetry_statement is None:
    fail("GitHub deployment identity policy must include the CloudWatch metric-discovery read statement")
elif github_metric_telemetry_statement.get("Effect") != "Allow" or github_metric_telemetry_statement.get("Action") != ["cloudwatch:ListMetrics"] or github_metric_telemetry_statement.get("Resource") != "*":
    fail("GitHub deployment identity must use only the required CloudWatch metric-discovery read")

telemetry_prerequisites = observability.get("telemetry_prerequisites")
if not isinstance(telemetry_prerequisites, list) or len(telemetry_prerequisites) != 1:
    fail("target profile must declare one enhanced Container Insights prerequisite for the running-count alarm")
else:
    telemetry_prerequisite = telemetry_prerequisites[0]
    expected_telemetry_prerequisite = {
        "id": "ecs-container-insights-enhanced",
        "owner": "existing-ecs-cluster",
        "required_for": ["ecs-running-count-mismatch"],
        "configuration": {
            "cluster_arn_source": "aws.cluster",
            "setting": "containerInsights",
            "required_value": "enhanced",
        },
        "expected_signal": {
            "namespace": "ECS/ContainerInsights",
            "metric": "RunningTaskCount",
            "dimensions": ["ClusterName", "ServiceName"],
        },
        "deployment_preflight": {
            "method": "aws-ecs-describe-clusters-settings",
            "cluster_name_source": "aws.cluster",
            "service_name_source": "runtime.server.service",
            "failure_mode": "block-service-stack-update",
        },
    }
    for key, expected in expected_telemetry_prerequisite.items():
        if not isinstance(telemetry_prerequisite, dict) or telemetry_prerequisite.get(key) != expected:
            fail(f"target profile Container Insights prerequisite must set {key} to the reviewed value")
    if telemetry_prerequisite.get("current_status") not in {"pending-read-only-verification", "verified"}:
        fail("target profile Container Insights prerequisite must state whether read-only verification is pending or verified")

alarm_definitions = observability.get("alarms")
expected_alarm_ids = {
    "alb-unhealthy-targets",
    "alb-5xx-spike",
    "ecs-running-count-mismatch",
    "ecs-high-cpu",
    "ecs-high-memory",
}
if not isinstance(alarm_definitions, list):
    fail("target profile observability alarms must be a structured list")
else:
    alarms_by_id = {}
    for definition in alarm_definitions:
        if not isinstance(definition, dict) or not isinstance(definition.get("id"), str):
            fail("each target-profile alarm must be an object with a stable id")
            continue
        alarm_id = definition["id"]
        if alarm_id in alarms_by_id:
            fail(f"target-profile alarm id is duplicated: {alarm_id}")
        alarms_by_id[alarm_id] = definition
    if set(alarms_by_id) != expected_alarm_ids:
        fail("target profile must declare exactly the reviewed platform-shell alarms")
    for definition in alarms_by_id.values():
        check_profile_alarm(definition, foundation, service, severity_vocabulary)

service_deployment_policy = properties(foundation, "ServiceDeploymentExecutionRole", "AWS::IAM::Role").get("Policies", [{}])[0].get("PolicyDocument", {}).get("Statement", [])
expected_service_alarm_arns = {
    "arn:${AWS::Partition}:cloudwatch:${AWS::Region}:${AWS::AccountId}:alarm:kanbien-staging-platform-shell-ecs-running-count-mismatch",
    "arn:${AWS::Partition}:cloudwatch:${AWS::Region}:${AWS::AccountId}:alarm:kanbien-staging-platform-shell-ecs-high-cpu",
    "arn:${AWS::Partition}:cloudwatch:${AWS::Region}:${AWS::AccountId}:alarm:kanbien-staging-platform-shell-ecs-high-memory",
}
put_alarm_statement = next((item for item in service_deployment_policy if item.get("Sid") == "CreateOnlyPlatformShellServiceAlarmDefinitions"), None)
if put_alarm_statement is None:
    fail("ServiceDeploymentExecutionRole must have a bounded service-alarm creation statement")
else:
    resources = {item.get("!Sub") for item in put_alarm_statement.get("Resource", []) if isinstance(item, dict)}
    if put_alarm_statement.get("Action") != ["cloudwatch:PutMetricAlarm"] or resources != expected_service_alarm_arns:
        fail("ServiceDeploymentExecutionRole must create only the three reviewed service alarms")
    if put_alarm_statement.get("Condition", {}).get("ForAllValues:StringEquals", {}).get("cloudwatch:AlarmActions") != [{"!Ref": "AlarmTopic"}]:
        fail("ServiceDeploymentExecutionRole must restrict new service alarms to AlarmTopic")

alarm_lifecycle_statement = next((item for item in service_deployment_policy if item.get("Sid") == "ManageOnlyPlatformShellServiceAlarmLifecycle"), None)
if alarm_lifecycle_statement is None:
    fail("ServiceDeploymentExecutionRole must have a bounded service-alarm lifecycle statement")
else:
    resources = {item.get("!Sub") for item in alarm_lifecycle_statement.get("Resource", []) if isinstance(item, dict)}
    expected_actions = {
        "cloudwatch:DeleteAlarms",
        "cloudwatch:DescribeAlarms",
        "cloudwatch:ListTagsForResource",
        "cloudwatch:TagResource",
        "cloudwatch:UntagResource",
    }
    if set(alarm_lifecycle_statement.get("Action", [])) != expected_actions or resources != expected_service_alarm_arns:
        fail("ServiceDeploymentExecutionRole must manage only the reviewed service-alarm lifecycle actions")

image_parameter = service.get("Parameters", {}).get("ImageUri", {})
if "@sha256" not in image_parameter.get("AllowedPattern", ""):
    fail("service ImageUri must require an immutable digest")

container = properties(service, "TaskDefinition", "AWS::ECS::TaskDefinition").get("ContainerDefinitions", [{}])[0]
if container.get("ReadonlyRootFilesystem") is not True:
    fail("platform-shell container must use a read-only root filesystem")
if container.get("Secrets"):
    fail("platform-shell task must not receive a Cognito client secret")
health_check = container.get("HealthCheck", {})
if health_check.get("Command", [])[:3] != ["CMD", "/nodejs/bin/node", "-e"]:
    fail("platform-shell ECS health check must use exec-form Node commands without a shell")
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

dockerfile = Path("infra/04.deploy/03.product/image/Dockerfile").read_text(encoding="utf-8")
for required_text, message in {
    "ARG RUNTIME_NODE_IMAGE=gcr.io/distroless/nodejs22-debian12:nonroot": "platform-shell Dockerfile must declare the reviewed minimal runtime image",
    "FROM ${RUNTIME_NODE_IMAGE}": "platform-shell Dockerfile must use the separate runtime image stage",
    "COPY --chown=nonroot:nonroot --from=build": "platform-shell runtime payload must be owned by nonroot",
    "USER nonroot": "platform-shell Dockerfile must run as nonroot",
    'CMD ["/nodejs/bin/node", "-e"': "platform-shell Dockerfile health check must use Node exec form without a shell",
    'CMD [".cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.js"]': "platform-shell Dockerfile must pass only the application path to the Distroless Node entrypoint",
}.items():
    if required_text not in dockerfile:
        fail(message)
if 'ENTRYPOINT ["dumb-init", "--"]' in dockerfile:
    fail("platform-shell Dockerfile must not require a shell-capable runtime init wrapper")
if 'CMD ["node", ".cache/platform-shell-image-build/' in dockerfile:
    fail("platform-shell Dockerfile must not repeat the Node executable supplied by the Distroless entrypoint")

if failures:
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    raise SystemExit(1)

print("Platform-shell infrastructure static policy check passed.")
PY
