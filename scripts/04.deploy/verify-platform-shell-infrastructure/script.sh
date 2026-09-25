#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-infrastructure
#   version: 32
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Statically enforce the Kanbien staging platform-shell infrastructure and selected capability-observability policy invariants.
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
bash scripts/04.deploy/verify-platform-shell-synthetic-scheduler/script.sh
bash scripts/04.deploy/verify-platform-shell-metric-coverage/script.sh
bash scripts/04.deploy/provision-platform-shell-negative-authz-client/smoke-test.sh
bash scripts/04.deploy/run-platform-shell-negative-authz-smoke/smoke-test.sh
bash scripts/04.deploy/provision-platform-shell-persistence-write-client/smoke-test.sh
bash scripts/04.deploy/run-platform-shell-persistence-smoke/smoke-test.sh
bash scripts/04.deploy/run-platform-shell-persistence-admission-probe/smoke-test.sh
bash scripts/04.deploy/run-platform-shell-rate-limit-smoke/smoke-test.sh
bash scripts/04.deploy/run-platform-shell-ingress-smoke/smoke-test.sh
bash scripts/04.deploy/run-platform-shell-worker-smoke/smoke-test.sh
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
with Path("infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-deploy-policy.json").open(encoding="utf-8") as handle:
    github_deployment_policy = json.load(handle)
failures = []

auth_policy = target_profile.get("auth", {})
negative_test_client = auth_policy.get("negative_test_client", {}) if isinstance(auth_policy, dict) else {}
persistence_write_test_client = auth_policy.get("persistence_write_test_client", {}) if isinstance(auth_policy, dict) else {}
expected_negative_test_client = {
    "name": "platform-shell-staging-negative-authz-client",
    "type": "confidential",
    "grant_type": "client_credentials",
    "access_token_validity_minutes": 5,
    "token_revocation": "enabled",
    "prevent_user_existence_errors": "enabled",
    "resource_server": {
        "identifier": "platform-shell-authz-probe",
        "name": "Platform Shell Authorization Negative Probe",
        "scope_name": "deny",
        "scope": "platform-shell-authz-probe/deny",
        "permission_mapping": "intentionally-unmapped",
    },
    "secret": {
        "name": "kanbien/staging/platform-shell/cognito-negative-authz-client",
        "delivery": "bounded-negative-authz-smoke-only-not-ecs-task-environment",
        "value_format": "opaque-raw-string",
    },
}
if not isinstance(negative_test_client, dict):
    fail("target profile must declare the governed negative authorization client policy")
else:
    for key, expected in expected_negative_test_client.items():
        if negative_test_client.get(key) != expected:
            fail(f"target profile negative authorization client must retain {key}")
    status = negative_test_client.get("status")
    if status not in {"pending-provisioning", "provisioned-pending-service-deployment", "deployed-pending-403-proof", "deployed-and-403-proven"}:
        fail("target profile negative authorization client must use a governed lifecycle status")
    client_id = negative_test_client.get("client_id")
    if status == "pending-provisioning":
        if client_id is not None:
            fail("target profile must not record a negative authorization client ID before provisioning")
    elif not isinstance(client_id, str) or not client_id:
        fail("target profile negative authorization client ID must be a non-empty string after provisioning")
    secret_arn = negative_test_client.get("secret_arn")
    if status == "pending-provisioning":
        if secret_arn is not None:
            fail("target profile must not record a negative authorization secret ARN before provisioning")
    elif not isinstance(secret_arn, str) or not secret_arn.startswith("arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-negative-authz-client-"):
        fail("target profile negative authorization secret ARN must remain target-scoped when provisioned")
    if status != "pending-provisioning" and isinstance(client_id, str) and isinstance(secret_arn, str):
        config = target_profile.get("config", {})
        secret_refs = config.get("secret_refs", {}) if isinstance(config, dict) else {}
        if secret_refs.get("cognito_negative_authz_client_secret") != {
            "name": "kanbien/staging/platform-shell/cognito-negative-authz-client",
            "arn": secret_arn,
            "delivery": "bounded-negative-authz-smoke-only-not-ecs-task-environment",
            "value_format": "opaque-raw-string",
        }:
            fail("target profile must retain the bounded negative authorization secret reference")
    if status in {"deployed-pending-403-proof", "deployed-and-403-proven"}:
        evidence = negative_test_client.get("deployment_evidence")
        expected_evidence = {
            "source_commit": "37a3151d4c405481c603537b56473ea75fd51a12",
            "image_uri": "337159794548.dkr.ecr.eu-west-1.amazonaws.com/platform-shell@sha256:7377505e91b0854a6f83628d406dc9298cd25eac70fc56ebdef21b63d868df17",
            "github_workflow_run_id": "35850734084",
            "service_stack_status": "UPDATE_COMPLETE",
            "task_definition_revision": 5,
            "service_rollout": "COMPLETED",
            "target_health": "healthy",
            "alarm_states": "five-ok",
        }
        if evidence != expected_evidence:
            fail("target profile must retain the reviewed post-deployment negative authorization evidence")
    if status == "deployed-and-403-proven":
        expected_proof = {
            "executed_at_utc": "2026-09-23T10:59:16Z",
            "command": "npm run platform:shell:negative-authz-smoke -- --execute",
            "result": "passed",
            "http_status": 403,
            "duration_ms": 220,
            "output_policy": "status-and-safe-latency-only-no-token-secret-or-response-body",
            "post_proof_health": "stack-update-complete-revision-5-completed-healthy-target-five-ok-alarms",
        }
        if negative_test_client.get("authorization_proof") != expected_proof:
            fail("target profile must retain the safe successful negative authorization proof")

expected_persistence_write_test_client = {
    "name": "platform-shell-staging-persistence-write-client",
    "type": "confidential",
    "grant_type": "client_credentials",
    "access_token_validity_minutes": 5,
    "token_revocation": "enabled",
    "prevent_user_existence_errors": "enabled",
    "resource_server": {
        "identifier": "platform-shell",
        "name": "Platform Shell",
        "scope_name": "smoke.write",
        "scope": "platform-shell/smoke.write",
        "permission_mapping": "platform-smoke.persistence.work-item:create",
    },
    "secret": {
        "name": "kanbien/staging/platform-shell/cognito-persistence-write-client",
        "delivery": "bounded-persistence-smoke-only-not-ecs-task-environment",
        "value_format": "opaque-raw-string",
    },
}
if not isinstance(persistence_write_test_client, dict):
    fail("target profile must declare the governed persistence write client policy")
else:
    for key, expected in expected_persistence_write_test_client.items():
        if persistence_write_test_client.get(key) != expected:
            fail(f"target profile persistence write client must retain {key}")
    persistence_status = persistence_write_test_client.get("status")
    if persistence_status not in {"pending-provisioning", "provisioned-pending-service-deployment", "deployed-pending-write-proof", "write-proof-failed-non-committing-remediation-pending", "write-proof-failed-non-committing-remediation-deployed-fresh-approval-pending", "write-proof-failed-non-committing-replacement-pre-server-diagnosis-pending", "write-proof-failed-non-committing-admission-probe-source-ready-deployment-pending", "write-proof-failed-non-committing-admission-probe-deployed-pending-execution", "write-proof-failed-non-committing-admission-probe-passed-fresh-acceptance-pending", "write-proof-failed-non-committing-iam-remediation-source-ready-deployment-pending", "write-proof-failed-non-committing-iam-remediation-deployed-authorization-proven-fresh-acceptance-pending", "deployed-and-write-proven"}:
        fail("target profile persistence write client must use a governed lifecycle status")
    persistence_client_id = persistence_write_test_client.get("client_id")
    persistence_secret_arn = persistence_write_test_client.get("secret_arn")
    if persistence_status == "pending-provisioning":
        if persistence_client_id is not None or persistence_secret_arn is not None:
            fail("target profile must not record persistence write client references before provisioning")
    else:
        if not isinstance(persistence_client_id, str) or not persistence_client_id:
            fail("target profile persistence write client ID must be a non-empty string after provisioning")
        if not isinstance(persistence_secret_arn, str) or not persistence_secret_arn.startswith("arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-persistence-write-client-"):
            fail("target profile persistence write secret ARN must remain target-scoped when provisioned")

    resource_server = auth_policy.get("resource_server", {})
    permission_mapping = auth_policy.get("permission_mapping", {})
    expected_scopes = [
        {"name": "smoke.read", "maps_to_permission": "platform-smoke.smoke:read"},
        {"name": "smoke.write", "maps_to_permission": "platform-smoke.persistence.work-item:create"},
    ]
    if resource_server != {"identifier": "platform-shell", "scopes": expected_scopes}:
        fail("target profile resource server must retain the reviewed read and persistence-write scope declarations")
    if permission_mapping.get("scope_permissions") != {
        "platform-shell/smoke.read": ["platform-smoke.smoke:read"],
        "platform-shell/smoke.write": ["platform-smoke.persistence.work-item:create"],
    }:
        fail("target profile must map only the reviewed read and persistence-write scopes to app permissions")

    config = target_profile.get("config", {})
    non_secret_env = config.get("non_secret_env", {}) if isinstance(config, dict) else {}
    secret_refs = config.get("secret_refs", {}) if isinstance(config, dict) else {}
    expected_client_allowlist = [negative_test_client.get("client_id")]
    if persistence_status == "pending-provisioning":
        if "cognito_persistence_write_client_secret" in secret_refs:
            fail("target profile must not record a persistence-write secret reference before provisioning")
    else:
        expected_persistence_secret_ref = {
            "name": "kanbien/staging/platform-shell/cognito-persistence-write-client",
            "arn": persistence_secret_arn,
            "delivery": "bounded-persistence-smoke-only-not-ecs-task-environment",
            "value_format": "opaque-raw-string",
        }
        if secret_refs.get("cognito_persistence_write_client_secret") != expected_persistence_secret_ref:
            fail("target profile must retain the bounded persistence-write secret reference after provisioning")
    if persistence_status in {"deployed-pending-write-proof", "write-proof-failed-non-committing-remediation-pending", "write-proof-failed-non-committing-remediation-deployed-fresh-approval-pending", "write-proof-failed-non-committing-replacement-pre-server-diagnosis-pending", "write-proof-failed-non-committing-admission-probe-source-ready-deployment-pending", "write-proof-failed-non-committing-admission-probe-deployed-pending-execution", "write-proof-failed-non-committing-admission-probe-passed-fresh-acceptance-pending", "write-proof-failed-non-committing-iam-remediation-source-ready-deployment-pending", "write-proof-failed-non-committing-iam-remediation-deployed-authorization-proven-fresh-acceptance-pending", "deployed-and-write-proven"}:
        expected_client_allowlist.append(persistence_client_id)
    if not all(isinstance(client_id, str) and client_id for client_id in expected_client_allowlist):
        fail("target profile must retain all deployed proof-client identifiers")
    if non_secret_env.get("PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS") != json.dumps(expected_client_allowlist, separators=(",", ":")):
        fail("target profile must allowlist exactly the proof clients deployed to the service")
    admission_probe_base = {
        "route": "POST /smoke/work-items/admission",
        "permission": "platform-smoke.persistence.work-item:create",
        "request_body": "none",
        "persistence_side_effects": "prohibited",
        "expected_http_status": 204,
        "output_policy": "status-and-safe-latency-only-no-token-secret-request-id-or-response-body",
    }
    if persistence_status == "write-proof-failed-non-committing-admission-probe-source-ready-deployment-pending":
        expected_admission_probe = {
            **admission_probe_base,
            "status": "source-ready-deployment-pending",
            "next_guard": "reviewed-service-deployment-and-health-before-one-execution",
        }
        if persistence_write_test_client.get("admission_probe") != expected_admission_probe:
            fail("target profile must retain the fixed source-ready non-mutating admission probe")
    if persistence_status in {"write-proof-failed-non-committing-admission-probe-deployed-pending-execution", "write-proof-failed-non-committing-admission-probe-passed-fresh-acceptance-pending", "write-proof-failed-non-committing-iam-remediation-source-ready-deployment-pending", "write-proof-failed-non-committing-iam-remediation-deployed-authorization-proven-fresh-acceptance-pending"}:
        expected_admission_probe = {
            **admission_probe_base,
            "status": "deployed-pending-one-execution" if persistence_status == "write-proof-failed-non-committing-admission-probe-deployed-pending-execution" else "executed-passed-fresh-acceptance-pending" if persistence_status == "write-proof-failed-non-committing-admission-probe-passed-fresh-acceptance-pending" else "executed-passed-iam-remediation-pending",
            "next_guard": "one-execution-only-then-record-safe-result-before-any-fresh-persistence-write" if persistence_status == "write-proof-failed-non-committing-admission-probe-deployed-pending-execution" else "one-fresh-acceptance-with-new-fixed-identity-before-relay-or-worker-action" if persistence_status in {"write-proof-failed-non-committing-admission-probe-passed-fresh-acceptance-pending", "write-proof-failed-non-committing-iam-remediation-deployed-authorization-proven-fresh-acceptance-pending"} else "deploy-and-prove-least-privilege-iam-remediation-before-one-new-fixed-identity-acceptance",
        }
        if persistence_write_test_client.get("admission_probe") != expected_admission_probe:
            fail("target profile must retain the fixed deployed non-mutating admission probe")
        expected_admission_probe_deployment = {
            "executed_on_utc": "2026-09-25",
            "source_commit_sha": "9b2aeb33153911eb507b83d30e362214445c0e3b",
            "github_workflow_run_id": "36117931464",
            "image_digest": "sha256:ce90ea8725a7743296ffce1a624b778bfedd2f391f29994d831227597ef80dfa",
            "image_scan": "zero-critical-zero-high",
            "change_set_review": "three-task-definition-revisions-and-two-in-place-service-references-only",
            "post_deployment_verification": {
                "service_stack": "UPDATE_COMPLETE",
                "public_server": "desired-one-running-one-rollout-complete",
                "public_target_health": "healthy",
                "public_liveness": "http-200",
                "protected_read_smoke": "http-200-safe-redacted-result",
                "worker": "desired-zero-running-zero-rollout-complete",
                "source_and_dead_letter_queues": "empty",
                "alarms": "five-ok",
            },
            "evidence_hygiene": "safe-image-and-aggregate-runtime-facts-only-no-task-identifiers-secrets-tokens-headers-bodies-or-provider-payloads",
        }
        if persistence_write_test_client.get("admission_probe_deployment") != expected_admission_probe_deployment:
            fail("target profile must retain safe deployed admission-probe evidence")
    if persistence_status in {"write-proof-failed-non-committing-admission-probe-passed-fresh-acceptance-pending", "write-proof-failed-non-committing-iam-remediation-source-ready-deployment-pending", "write-proof-failed-non-committing-iam-remediation-deployed-authorization-proven-fresh-acceptance-pending"}:
        expected_admission_probe_execution = {
            "executed_on_utc": "2026-09-25",
            "status": "passed",
            "http_status": 204,
            "duration_ms": 95,
            "structured_application_observations": 1,
            "observability_query_scope": "exact-capability-and-http-status-aggregate-count-only",
            "persistence_side_effects": "prohibited",
            "post_execution_state": "server-one-running-one-worker-zero-source-and-dead-letter-queues-empty-five-alarms-ok",
            "evidence_hygiene": "safe-status-latency-and-aggregate-observation-only-no-token-secret-request-id-response-body-record-message-or-provider-payload",
        }
        if persistence_write_test_client.get("admission_probe_execution") != expected_admission_probe_execution:
            fail("target profile must retain the safe successful admission-probe evidence")
    if persistence_status in {"write-proof-failed-non-committing-iam-remediation-source-ready-deployment-pending", "write-proof-failed-non-committing-iam-remediation-deployed-authorization-proven-fresh-acceptance-pending"}:
        expected_fresh_acceptance_attempt = {
            "executed_on_utc": "2026-09-25",
            "status": "failed-non-committing",
            "http_status": 503,
            "duration_ms": 146,
            "structured_failure_observations": 1,
            "error_class": "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
            "aggregate_commit_result": "not-committed",
            "post_attempt_state": "server-one-running-one-worker-zero-source-and-dead-letter-queues-empty-five-alarms-ok",
            "follow_up": "deploy-and-prove-least-privilege-iam-remediation-before-one-new-fixed-identity-acceptance",
        }
        if persistence_write_test_client.get("fresh_acceptance_attempt") != expected_fresh_acceptance_attempt:
            fail("target profile must retain the safe non-committing fresh-acceptance evidence")
        expected_iam_remediation = {
            "status": "source-ready-deployment-pending" if persistence_status == "write-proof-failed-non-committing-iam-remediation-source-ready-deployment-pending" else "deployed-authorization-proven-fresh-acceptance-pending",
            "transaction_api": "dynamodb:TransactWriteItems",
            "required_member_authorization": "dynamodb:PutItem",
            "member_operation_shape": "three-conditional-put-members-no-condition-check-member",
            "scope": "PlatformPersistenceTable-only",
            "live_pre_remediation_simulation": "dynamodb-put-item-implicit-deny",
            "source_change": "replace-non-authorizing-transaction-api-action-with-put-item-on-the-one-table",
            "deployment_guard": "reviewed-foundation-stack-change-set-and-post-deployment-live-iam-simulation-required-before-one-new-acceptance",
            "evidence_hygiene": "safe-authorization-decision-only-no-role-arn-policy-document-provider-payload-or-record-data",
        }
        if persistence_status == "write-proof-failed-non-committing-iam-remediation-deployed-authorization-proven-fresh-acceptance-pending":
            expected_iam_remediation["post_deployment_simulation"] = "dynamodb-put-item-allowed"
            expected_iam_remediation["post_deployment_health"] = "server-one-running-one-worker-zero-source-and-dead-letter-queues-empty-five-alarms-ok"
        if persistence_write_test_client.get("iam_remediation") != expected_iam_remediation:
            fail("target profile must retain the bounded IAM remediation and authorization evidence")
    if persistence_status in {"write-proof-failed-non-committing-remediation-pending", "write-proof-failed-non-committing-remediation-deployed-fresh-approval-pending", "write-proof-failed-non-committing-replacement-pre-server-diagnosis-pending"}:
        expected_failed_acceptance = {
            "executed_on_utc": "2026-09-24",
            "status": "failed-non-committing",
            "http_status": 503,
            "duration_ms": 229,
            "aggregate_commit_result": "not-committed",
            "pre_remediation_error_class": "unavailable",
            "read_only_diagnosis": {
                "task_configuration": "complete",
                "persistence_table": "active-required-indexes-present",
                "atomic_transaction_permission": "allowed",
                "audit_trail_data_event": "unavailable",
            },
            "follow_up": "deploy-profile-governed-error-class-remediation-before-fresh-approved-replacement-acceptance",
        }
        if persistence_status in {"write-proof-failed-non-committing-remediation-deployed-fresh-approval-pending", "write-proof-failed-non-committing-replacement-pre-server-diagnosis-pending"}:
            expected_failed_acceptance["follow_up"] = "fresh-explicit-approval-required-for-one-replacement-acceptance-after-remediation-deployment"
            expected_remediation_deployment = {
                "executed_on_utc": "2026-09-24",
                "source_commit_sha": "af07a79f4be3285b423770476e1e4b97256bafb4",
                "github_workflow_run_id": "36064013450",
                "image_digest": "sha256:dd8f8e6d4a6131eea2a9d40954ed6b1cf8d20fc1734c109e7658631b578067fc",
                "image_scan": "zero-critical-zero-high",
                "change_set_review": "three-task-definition-revisions-and-two-in-place-service-references-only",
                "post_deployment_verification": {
                    "service_stack": "UPDATE_COMPLETE",
                    "public_server": "desired-one-running-one-rollout-complete",
                    "public_target_health": "healthy",
                    "public_liveness": "http-200",
                    "protected_read_smoke": "http-200-safe-redacted-result",
                    "worker": "desired-zero-running-zero-rollout-complete",
                    "source_and_dead_letter_queues": "empty",
                    "alarms": "five-ok",
                },
                "evidence_hygiene": "safe-image-and-aggregate-runtime-facts-only-no-task-identifiers-secrets-tokens-headers-bodies-or-provider-payloads",
            }
        if persistence_write_test_client.get("acceptance_attempt") != expected_failed_acceptance:
            fail("target profile must retain only the safe non-committing acceptance diagnostic evidence")
        if persistence_status in {"write-proof-failed-non-committing-remediation-deployed-fresh-approval-pending", "write-proof-failed-non-committing-replacement-pre-server-diagnosis-pending"} and persistence_write_test_client.get("remediation_deployment") != expected_remediation_deployment:
            fail("target profile must retain only the safe deployed remediation evidence")
        if persistence_status == "write-proof-failed-non-committing-replacement-pre-server-diagnosis-pending":
            expected_replacement_acceptance = {
                "executed_on_utc": "2026-09-24",
                "status": "failed-non-committing",
                "http_status": 503,
                "duration_ms": 148,
                "aggregate_commit_result": "not-committed",
                "server_observation": "no-matching-structured-request-observed",
                "post_attempt_state": "server-one-running-one-worker-zero-queues-empty",
                "follow_up": "diagnose-possible-pre-server-or-ingress-path-before-any-additional-write-relay-or-worker-action",
            }
            if persistence_write_test_client.get("replacement_acceptance_attempt") != expected_replacement_acceptance:
                fail("target profile must retain only safe replacement-acceptance stop evidence")

expected_foundation_resources = {
    "PlatformShellLogGroup",
    "PlatformShellOtelCollectorLogGroup",
    "PlatformShellWorkerLogGroup",
    "PlatformShellWorkerOtelCollectorLogGroup",
    "PlatformShellRelayLogGroup",
    "PlatformShellRelayOtelCollectorLogGroup",
    "OtelCollectorConfigurationParameter",
    "RateLimitTable",
    "PlatformPersistenceTable",
    "TaskExecutionRole",
    "TaskRole",
    "WorkerTaskRole",
    "RelayTaskRole",
    "ServiceDeploymentExecutionRole",
    "ServiceSecurityGroup",
    "WorkerSecurityGroup",
    "RelaySecurityGroup",
    "WorkerQueue",
    "WorkerDeadLetterQueue",
    "WorkerQueueTransportPolicy",
    "WorkerDeadLetterQueueTransportPolicy",
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
    "PlatformShellMonthlyBudget",
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
    "OtelCollectorLogGroupName",
    "WorkerLogGroupName",
    "WorkerOtelCollectorLogGroupName",
    "RelayLogGroupName",
    "RelayOtelCollectorLogGroupName",
    "OtelCollectorConfigurationParameterArn",
    "RateLimitTableName",
    "RateLimitTableArn",
    "PlatformPersistenceTableName",
    "PlatformPersistenceTableArn",
    "PlatformPersistenceOutboxDueIndexName",
    "PlatformPersistenceLineageCauseIndexName",
    "TaskExecutionRoleArn",
    "TaskRoleArn",
    "WorkerTaskRoleArn",
    "RelayTaskRoleArn",
    "ServiceDeploymentExecutionRoleArn",
    "ServiceSecurityGroupId",
    "WorkerSecurityGroupId",
    "RelaySecurityGroupId",
    "WorkerQueueUrl",
    "WorkerQueueArn",
    "WorkerDeadLetterQueueUrl",
    "WorkerDeadLetterQueueArn",
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
    "WorkerTaskDefinition",
    "WorkerService",
    "RelayTaskDefinition",
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

persistence_table_resource = resource(foundation, "PlatformPersistenceTable")
if persistence_table_resource.get("DeletionPolicy") != "Retain" or persistence_table_resource.get("UpdateReplacePolicy") != "Retain":
    fail("PlatformPersistenceTable must retain data on stack deletion or replacement")
persistence_table = properties(foundation, "PlatformPersistenceTable", "AWS::DynamoDB::Table")
if persistence_table.get("TableName") != "kanbien-staging-platform-shell-persistence":
    fail("PlatformPersistenceTable must retain the reviewed staging table name")
if persistence_table.get("BillingMode") != "PAY_PER_REQUEST" or persistence_table.get("TableClass") != "STANDARD":
    fail("PlatformPersistenceTable must use on-demand standard-class billing for the bounded initial target")
if persistence_table.get("DeletionProtectionEnabled") is not True:
    fail("PlatformPersistenceTable must enable deletion protection")
if persistence_table.get("SSESpecification") != {"SSEEnabled": True}:
    fail("PlatformPersistenceTable must enable the reviewed DynamoDB server-side encryption")
if persistence_table.get("PointInTimeRecoverySpecification") != {"PointInTimeRecoveryEnabled": True}:
    fail("PlatformPersistenceTable must enable point-in-time recovery")
if "TimeToLiveSpecification" in persistence_table:
    fail("PlatformPersistenceTable must not claim DynamoDB TTL as a retention policy")
if persistence_table.get("AttributeDefinitions") != [
    {"AttributeName": "PK", "AttributeType": "S"},
    {"AttributeName": "SK", "AttributeType": "S"},
    {"AttributeName": "DueKey", "AttributeType": "S"},
    {"AttributeName": "DueSort", "AttributeType": "S"},
    {"AttributeName": "CauseKey", "AttributeType": "S"},
    {"AttributeName": "CauseSort", "AttributeType": "S"},
]:
    fail("PlatformPersistenceTable must declare only the adapter-required primary and index attributes")
if persistence_table.get("KeySchema") != [
    {"AttributeName": "PK", "KeyType": "HASH"},
    {"AttributeName": "SK", "KeyType": "RANGE"},
]:
    fail("PlatformPersistenceTable must retain the adapter-private PK/SK primary key")
if persistence_table.get("GlobalSecondaryIndexes") != [
    {
        "IndexName": "OutboxDueIndex",
        "KeySchema": [
            {"AttributeName": "DueKey", "KeyType": "HASH"},
            {"AttributeName": "DueSort", "KeyType": "RANGE"},
        ],
        "Projection": {"ProjectionType": "ALL"},
    },
    {
        "IndexName": "LineageCauseIndex",
        "KeySchema": [
            {"AttributeName": "CauseKey", "KeyType": "HASH"},
            {"AttributeName": "CauseSort", "KeyType": "RANGE"},
        ],
        "Projection": {"ProjectionType": "ALL"},
    },
]:
    fail("PlatformPersistenceTable must retain the reviewed due and direct-cause indexes")
expected_persistence_tags = [
    {"Key": "service", "Value": "platform-shell"},
    {"Key": "component", "Value": "persistence-smoke"},
    {"Key": "environment", "Value": "staging"},
    {"Key": "data-classification", "Value": "operational-safe-identifiers"},
    {"Key": "managed-by", "Value": "cloudformation"},
]
if persistence_table.get("Tags") != expected_persistence_tags:
    fail("PlatformPersistenceTable must retain the reviewed ownership and data-classification tags")

expected_persistence_profile = {
    "smoke_transactional_outbox": {
        "status": "foundation-and-service-deployed-iam-remediation-authorization-proven-fresh-acceptance-pending",
        "provider": "aws-dynamodb",
        "adapter_package": "@kanbien/platform-adapter-aws-persistence-dynamodb",
        "composition_entrypoint": "infra/04.deploy/03.product/entrypoints/kanbien-platform-persistence.ts",
        "region": "eu-west-1",
        "table": {
            "resource": "PlatformPersistenceTable",
            "name": "kanbien-staging-platform-shell-persistence",
            "output_name": "PlatformPersistenceTableName",
        },
        "indexes": {
            "outbox_due": {"name": "OutboxDueIndex", "output_name": "PlatformPersistenceOutboxDueIndexName"},
            "lineage_cause": {"name": "LineageCauseIndex", "output_name": "PlatformPersistenceLineageCauseIndexName"},
        },
        "protection": {
            "billing_mode": "PAY_PER_REQUEST",
            "encryption": "dynamodb-server-side-encryption",
            "point_in_time_recovery": "enabled",
            "deletion_protection": "enabled",
            "cloudformation_deletion_policy": "retain",
            "ttl": "deliberately-not-configured-not-a-retention-policy",
        },
        "foundation_evidence": {
            "deployed_on_utc": "2026-09-24",
            "stack_status": "UPDATE_COMPLETE",
            "table_status": "ACTIVE",
            "verified_protections": [
                "on-demand-billing",
                "server-side-encryption",
                "point-in-time-recovery",
                "deletion-protection",
                "retain-on-delete",
            ],
            "verified_indexes": ["OutboxDueIndex", "LineageCauseIndex"],
            "verified_workload_boundary": {
                "server": "atomic-persistence-transaction-only",
                "worker": "source-queue-settlement-and-processing-state-only",
                "relay": "due-index-query-outbox-lease-source-queue-send-and-safe-metrics-only",
            },
            "verified_network_boundary": "relay-no-ingress-and-reviewed-tls-dns-egress-only",
            "preserved_runtime_state": {
                "public_server": "desired-one-running-one",
                "worker": "desired-zero-running-zero",
                "source_and_dead_letter_queues": "empty",
                "worker_visibility_timeout_seconds": 120,
            },
            "evidence_hygiene": "safe-configuration-and-aggregate-runtime-facts-only-no-records-messages-task-identifiers-or-provider-payloads",
        },
        "service_change_set_review": {
            "status": "executed-and-post-deployment-verified",
            "reviewed_on_utc": "2026-09-24",
            "reviewed_changes": {
                "relay_task_definition": "add-dormant-one-shot-task-definition-only",
                "public_server_service": "task-definition-reference-update-only-no-service-replacement",
                "public_server_task_definition": "normal-ecs-revision-replacement-container-definitions-only",
                "worker_service": "task-definition-reference-update-only-no-service-replacement",
                "worker_task_definition": "normal-ecs-revision-replacement-container-definitions-only",
            },
            "executed_on_utc": "2026-09-24",
            "post_execution_verification": {
                "service_stack": "UPDATE_COMPLETE",
                "public_server": "desired-one-running-one-rollout-complete",
                "public_target_health": "healthy",
                "public_liveness": "http-200",
                "protected_read_smoke": "http-200-safe-redacted-result",
                "active_image": "immutable-persistence-capable-digest-verified",
                "worker": "desired-zero-running-zero-rollout-complete",
                "relay_running_task_count": "zero",
                "source_and_dead_letter_queues": "empty",
            },
            "next_execution_guard": "execute-one-new-fixed-identity-acceptance-then-record-safe-transaction-evidence-before-relay-or-worker-action",
            "execution_exclusions": "no-relay-run-no-worker-scale-no-cognito-change-no-additional-write-after-the-one-new-acceptance",
        },
        "activation": {
            "server_acceptance": "fresh-acceptance-failed-non-committing-iam-remediation-deployed-authorization-proven-one-new-acceptance-pending",
            "outbox_relay": "prohibited-no-committed-outbox-obligation",
            "durable_worker_processing": "prohibited-no-relay-created-delivery-worker-remains-zero",
            "iam": "server-persistence-member-permission-remediation-deployed-and-live-put-item-authorization-proven",
            "required_identity_scope": "platform-shell/smoke.write",
            "identity_scope_status": "provisioned-separate-write-client-trusted-by-exact-server-allowlist-one-new-acceptance-after-iam-remediation-proof",
            "observability": "admission-profile-proved-and-fresh-acceptance-store-operation-failure-observed-with-safe-normalized-error-class",
        },
    },
}
if target_profile.get("persistence") != expected_persistence_profile:
    fail("target profile must retain the reviewed deployed-foundation and pending-service acceptance boundary")

task_execution_policy = properties(foundation, "TaskExecutionRole", "AWS::IAM::Role").get("Policies", [])
task_execution_configuration_statement = next(
    (
        statement
        for policy in task_execution_policy
        for statement in policy.get("PolicyDocument", {}).get("Statement", [])
        if statement.get("Sid") == "ReadOnlyThePlatformShellOtelCollectorConfiguration"
    ),
    None,
)
if task_execution_configuration_statement is None:
    fail("TaskExecutionRole must include the narrow collector-configuration read statement")
elif task_execution_configuration_statement.get("Effect") != "Allow" or task_execution_configuration_statement.get("Action") != ["ssm:GetParameters"] or task_execution_configuration_statement.get("Resource") != {"!GetAtt": "OtelCollectorConfigurationParameter.Arn"}:
    fail("TaskExecutionRole must read only the reviewed OTel collector configuration parameter")

task_policy = properties(foundation, "TaskRole", "AWS::IAM::Role").get("Policies", [])
task_statements = [statement for policy in task_policy for statement in policy.get("PolicyDocument", {}).get("Statement", [])]
task_statements_by_sid = {statement.get("Sid"): statement for statement in task_statements}
rate_limit_statement = task_statements_by_sid.get("UpdateOnlyThePlatformShellRateLimitTable")
metric_delivery_statement = task_statements_by_sid.get("PublishOnlyCloudWatchMetricData")
persistence_acceptance_statement = task_statements_by_sid.get("PutOnlyThePlatformSmokePersistenceTable")
if rate_limit_statement is None or rate_limit_statement.get("Effect") != "Allow" or rate_limit_statement.get("Action") != ["dynamodb:UpdateItem"] or rate_limit_statement.get("Resource") != {"!GetAtt": "RateLimitTable.Arn"}:
    fail("TaskRole must retain only the reviewed DynamoDB rate-limit write statement")
if persistence_acceptance_statement is None or persistence_acceptance_statement.get("Effect") != "Allow" or persistence_acceptance_statement.get("Action") != ["dynamodb:PutItem"] or persistence_acceptance_statement.get("Resource") != {"!GetAtt": "PlatformPersistenceTable.Arn"}:
    fail("TaskRole must grant only the DynamoDB PutItem member permission required by the reviewed atomic acceptance transaction")
if metric_delivery_statement is None or metric_delivery_statement.get("Effect") != "Allow" or metric_delivery_statement.get("Action") != ["cloudwatch:PutMetricData"] or metric_delivery_statement.get("Resource") != "*":
    fail("TaskRole must grant only the reviewed CloudWatch OTel metric-delivery action")
if set(task_statements_by_sid) != {"UpdateOnlyThePlatformShellRateLimitTable", "PutOnlyThePlatformSmokePersistenceTable", "PublishOnlyCloudWatchMetricData"}:
    fail("TaskRole must contain exactly the reviewed rate-limit, persistence acceptance, and metric-delivery statements")

worker_task_policy = properties(foundation, "WorkerTaskRole", "AWS::IAM::Role").get("Policies", [])
worker_task_statements = [statement for policy in worker_task_policy for statement in policy.get("PolicyDocument", {}).get("Statement", [])]
worker_task_statements_by_sid = {statement.get("Sid"): statement for statement in worker_task_statements}
worker_delivery_statement = worker_task_statements_by_sid.get("ReceiveAndSettleOnlyThePlatformShellWorkerQueue")
if worker_delivery_statement is None or worker_delivery_statement.get("Effect") != "Allow" or set(worker_delivery_statement.get("Action", [])) != {"sqs:ChangeMessageVisibility", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ReceiveMessage"} or worker_delivery_statement.get("Resource") != {"!GetAtt": "WorkerQueue.Arn"}:
    fail("WorkerTaskRole must receive and settle only the reviewed source queue")
worker_metric_statement = worker_task_statements_by_sid.get("PublishOnlyCloudWatchWorkerMetricData")
if worker_metric_statement is None or worker_metric_statement.get("Effect") != "Allow" or worker_metric_statement.get("Action") != ["cloudwatch:PutMetricData"] or worker_metric_statement.get("Resource") != "*":
    fail("WorkerTaskRole must grant only the reviewed CloudWatch worker metric-delivery action")
worker_processing_statement = worker_task_statements_by_sid.get("ReadAndRecordOnlyThePlatformPersistenceProcessingState")
if worker_processing_statement is None or worker_processing_statement.get("Effect") != "Allow" or set(worker_processing_statement.get("Action", [])) != {"dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"} or worker_processing_statement.get("Resource") != {"!GetAtt": "PlatformPersistenceTable.Arn"}:
    fail("WorkerTaskRole must read and record only reviewed durable processing state")
if set(worker_task_statements_by_sid) != {"ReceiveAndSettleOnlyThePlatformShellWorkerQueue", "ReadAndRecordOnlyThePlatformPersistenceProcessingState", "PublishOnlyCloudWatchWorkerMetricData"}:
    fail("WorkerTaskRole must contain exactly the reviewed queue-delivery, processing-state, and metric-delivery statements")

relay_task_policy = properties(foundation, "RelayTaskRole", "AWS::IAM::Role").get("Policies", [])
relay_task_statements = [statement for policy in relay_task_policy for statement in policy.get("PolicyDocument", {}).get("Statement", [])]
relay_task_statements_by_sid = {statement.get("Sid"): statement for statement in relay_task_statements}
relay_due_query_statement = relay_task_statements_by_sid.get("QueryOnlyThePlatformPersistenceDueIndex")
if relay_due_query_statement is None or relay_due_query_statement.get("Effect") != "Allow" or relay_due_query_statement.get("Action") != ["dynamodb:Query"] or relay_due_query_statement.get("Resource") != {"!Sub": "${PlatformPersistenceTable.Arn}/index/OutboxDueIndex"}:
    fail("RelayTaskRole must query only the reviewed persistence due index")
relay_outbox_state_statement = relay_task_statements_by_sid.get("ReadAndUpdateOnlyThePlatformPersistenceOutboxRecords")
if relay_outbox_state_statement is None or relay_outbox_state_statement.get("Effect") != "Allow" or set(relay_outbox_state_statement.get("Action", [])) != {"dynamodb:GetItem", "dynamodb:UpdateItem"} or relay_outbox_state_statement.get("Resource") != {"!GetAtt": "PlatformPersistenceTable.Arn"}:
    fail("RelayTaskRole must read and update only reviewed persistence outbox state")
relay_queue_send_statement = relay_task_statements_by_sid.get("SendOnlyThePlatformShellWorkerQueue")
if relay_queue_send_statement is None or relay_queue_send_statement.get("Effect") != "Allow" or relay_queue_send_statement.get("Action") != ["sqs:SendMessage"] or relay_queue_send_statement.get("Resource") != {"!GetAtt": "WorkerQueue.Arn"}:
    fail("RelayTaskRole must send only to the reviewed worker source queue")
relay_metric_statement = relay_task_statements_by_sid.get("PublishOnlyCloudWatchRelayMetricData")
if relay_metric_statement is None or relay_metric_statement.get("Effect") != "Allow" or relay_metric_statement.get("Action") != ["cloudwatch:PutMetricData"] or relay_metric_statement.get("Resource") != "*":
    fail("RelayTaskRole must grant only the reviewed CloudWatch relay metric-delivery action")
if set(relay_task_statements_by_sid) != {"QueryOnlyThePlatformPersistenceDueIndex", "ReadAndUpdateOnlyThePlatformPersistenceOutboxRecords", "SendOnlyThePlatformShellWorkerQueue", "PublishOnlyCloudWatchRelayMetricData"}:
    fail("RelayTaskRole must contain exactly the reviewed due-query, outbox, queue-send, and metric-delivery statements")

for queue_name, expected_queue_name, expected_retention, expected_visibility in (
    ("WorkerQueue", "kanbien-staging-platform-shell-worker", 345600, 120),
    ("WorkerDeadLetterQueue", "kanbien-staging-platform-shell-worker-dlq", 1209600, None),
):
    queue = properties(foundation, queue_name, "AWS::SQS::Queue")
    if queue.get("QueueName") != expected_queue_name or queue.get("MessageRetentionPeriod") != expected_retention or queue.get("ReceiveMessageWaitTimeSeconds") != 20 or queue.get("SqsManagedSseEnabled") is not True:
        fail(f"{queue_name} must retain the reviewed name, long-poll, retention, and SQS-managed encryption")
    if expected_visibility is not None and queue.get("VisibilityTimeout") != expected_visibility:
        fail("WorkerQueue must retain the reviewed two-minute visibility timeout")

worker_queue = properties(foundation, "WorkerQueue", "AWS::SQS::Queue")
if worker_queue.get("MaximumMessageSize") != 262144 or worker_queue.get("DelaySeconds") != 0 or worker_queue.get("RedrivePolicy") != {"deadLetterTargetArn": {"!GetAtt": "WorkerDeadLetterQueue.Arn"}, "maxReceiveCount": 5}:
    fail("WorkerQueue must retain the reviewed bounded payload and SQS redrive policy")

for policy_name, queue_name in (("WorkerQueueTransportPolicy", "WorkerQueue"), ("WorkerDeadLetterQueueTransportPolicy", "WorkerDeadLetterQueue")):
    queue_policy = properties(foundation, policy_name, "AWS::SQS::QueuePolicy")
    if queue_policy.get("Queues") != [{"!Ref": queue_name}] or queue_policy.get("PolicyDocument") != {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "DenyInsecureTransport",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "sqs:*",
            "Resource": {"!GetAtt": f"{queue_name}.Arn"},
            "Condition": {"Bool": {"aws:SecureTransport": False}},
        }],
    }:
        fail(f"{policy_name} must deny non-TLS transport for only its reviewed queue")

service_deployment_role = properties(foundation, "ServiceDeploymentExecutionRole", "AWS::IAM::Role")
service_deployment_policy = service_deployment_role.get("Policies", [{}])[0].get("PolicyDocument", {}).get("Statement", [])
if not contains_value(service_deployment_policy, "ecs:RegisterTaskDefinition"):
    fail("ServiceDeploymentExecutionRole must be able to register only the service task definition")
if not contains_intrinsic(service_deployment_policy, "!GetAtt", "TaskExecutionRole.Arn") or not contains_intrinsic(service_deployment_policy, "!GetAtt", "TaskRole.Arn") or not contains_intrinsic(service_deployment_policy, "!GetAtt", "WorkerTaskRole.Arn") or not contains_intrinsic(service_deployment_policy, "!GetAtt", "RelayTaskRole.Arn"):
    fail("ServiceDeploymentExecutionRole must pass only the reviewed platform-shell server, worker, and relay task roles")

security_group = properties(foundation, "ServiceSecurityGroup", "AWS::EC2::SecurityGroup")
for ingress in security_group.get("SecurityGroupIngress", []):
    if ingress.get("SourceSecurityGroupId") != {"!Ref": "ExistingAlbSecurityGroupId"}:
        fail("ServiceSecurityGroup ingress must come only from ExistingAlbSecurityGroupId")
    if ingress.get("FromPort") != 3000 or ingress.get("ToPort") != 3000:
        fail("ServiceSecurityGroup ingress must allow only TCP 3000")
if any(rule.get("CidrIp") == "0.0.0.0/0" and rule.get("FromPort") != 443 for rule in security_group.get("SecurityGroupEgress", [])):
    fail("ServiceSecurityGroup may use public egress only for TLS port 443")

worker_security_group = properties(foundation, "WorkerSecurityGroup", "AWS::EC2::SecurityGroup")
if worker_security_group.get("SecurityGroupIngress") not in (None, []):
    fail("WorkerSecurityGroup must accept no inbound network traffic")
expected_worker_egress = [
    {"Description": "TLS egress for ECR image pulls, CloudWatch Logs, DynamoDB, SQS, and CloudWatch metric delivery.", "IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "CidrIp": "0.0.0.0/0"},
    {"Description": "UDP DNS only to the VPC resolver address range.", "IpProtocol": "udp", "FromPort": 53, "ToPort": 53, "CidrIp": {"!Ref": "VpcCidr"}},
    {"Description": "TCP DNS fallback only to the VPC resolver address range.", "IpProtocol": "tcp", "FromPort": 53, "ToPort": 53, "CidrIp": {"!Ref": "VpcCidr"}},
]
if worker_security_group.get("SecurityGroupEgress") != expected_worker_egress:
    fail("WorkerSecurityGroup must retain only reviewed TLS and VPC DNS egress")

relay_security_group = properties(foundation, "RelaySecurityGroup", "AWS::EC2::SecurityGroup")
if relay_security_group.get("SecurityGroupIngress") not in (None, []):
    fail("RelaySecurityGroup must accept no inbound network traffic")
expected_relay_egress = [
    {"Description": "TLS egress for ECR image pulls, CloudWatch Logs, DynamoDB, SQS, and CloudWatch metric delivery.", "IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "CidrIp": "0.0.0.0/0"},
    {"Description": "UDP DNS only to the VPC resolver address range.", "IpProtocol": "udp", "FromPort": 53, "ToPort": 53, "CidrIp": {"!Ref": "VpcCidr"}},
    {"Description": "TCP DNS fallback only to the VPC resolver address range.", "IpProtocol": "tcp", "FromPort": 53, "ToPort": 53, "CidrIp": {"!Ref": "VpcCidr"}},
]
if relay_security_group.get("SecurityGroupEgress") != expected_relay_egress:
    fail("RelaySecurityGroup must retain only reviewed TLS and VPC DNS egress")

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

alarm_topic_policy = properties(foundation, "AlarmTopicPolicy", "AWS::SNS::TopicPolicy")
if alarm_topic_policy.get("Topics") != [{"!Ref": "AlarmTopic"}]:
    fail("AlarmTopicPolicy must apply only to the reviewed foundation alarm topic")
topic_policy_statements = alarm_topic_policy.get("PolicyDocument", {}).get("Statement", [])
expected_topic_principals = {
    "AllowCloudWatchAlarmsToPublish": "cloudwatch.amazonaws.com",
    "AllowBudgetsToPublish": "budgets.amazonaws.com",
}
actual_topic_statements = {statement.get("Sid"): statement for statement in topic_policy_statements if isinstance(statement, dict)}
if set(actual_topic_statements) != set(expected_topic_principals):
    fail("AlarmTopicPolicy must allow only CloudWatch alarms and Budgets to publish")
for statement_id, principal in expected_topic_principals.items():
    statement = actual_topic_statements.get(statement_id, {})
    if statement.get("Effect") != "Allow" or statement.get("Principal") != {"Service": principal} or statement.get("Action") != "sns:Publish" or statement.get("Resource") != {"!Ref": "AlarmTopic"} or statement.get("Condition") != {"StringEquals": {"aws:SourceAccount": {"!Ref": "AWS::AccountId"}}}:
        fail(f"AlarmTopicPolicy {statement_id} must retain the reviewed same-account publish boundary")

budget = properties(foundation, "PlatformShellMonthlyBudget", "AWS::Budgets::Budget")
if budget.get("Budget") != {
    "BudgetName": "kanbien-staging-platform-shell-monthly",
    "BudgetLimit": {"Amount": "25", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST",
    "CostFilters": {"TagKeyValue": ["user:service$platform-shell"]},
}:
    fail("PlatformShellMonthlyBudget must retain the reviewed 25 USD monthly service-tag budget")
expected_budget_notifications = [
    ("ACTUAL", 50),
    ("ACTUAL", 80),
    ("ACTUAL", 100),
    ("FORECASTED", 100),
]
actual_budget_notifications = budget.get("NotificationsWithSubscribers")
expected_budget_subscriptions = [
    {
        "Notification": {
            "NotificationType": notification_type,
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": threshold,
            "ThresholdType": "PERCENTAGE",
        },
        "Subscribers": [{"SubscriptionType": "SNS", "Address": {"!Ref": "AlarmTopic"}}],
    }
    for notification_type, threshold in expected_budget_notifications
]
if actual_budget_notifications != expected_budget_subscriptions:
    fail("PlatformShellMonthlyBudget must send only the reviewed actual and forecast thresholds to AlarmTopic")

log_group = properties(foundation, "PlatformShellLogGroup", "AWS::Logs::LogGroup")
if log_group.get("RetentionInDays") != {"!Ref": "LogRetentionDays"}:
    fail("PlatformShellLogGroup must use the reviewed retention parameter")
collector_log_group = properties(foundation, "PlatformShellOtelCollectorLogGroup", "AWS::Logs::LogGroup")
if collector_log_group.get("LogGroupName") != "/ecs/kanbien-staging-platform-shell-otel-collector" or collector_log_group.get("RetentionInDays") != {"!Ref": "LogRetentionDays"}:
    fail("PlatformShellOtelCollectorLogGroup must use the reviewed separate collector log destination and retention")
worker_log_group = properties(foundation, "PlatformShellWorkerLogGroup", "AWS::Logs::LogGroup")
if worker_log_group.get("LogGroupName") != "/ecs/kanbien-staging-platform-shell-worker" or worker_log_group.get("RetentionInDays") != {"!Ref": "LogRetentionDays"}:
    fail("PlatformShellWorkerLogGroup must use the reviewed worker log destination and retention")
worker_collector_log_group = properties(foundation, "PlatformShellWorkerOtelCollectorLogGroup", "AWS::Logs::LogGroup")
if worker_collector_log_group.get("LogGroupName") != "/ecs/kanbien-staging-platform-shell-worker-otel-collector" or worker_collector_log_group.get("RetentionInDays") != {"!Ref": "LogRetentionDays"}:
    fail("PlatformShellWorkerOtelCollectorLogGroup must use the reviewed worker collector log destination and retention")
relay_log_group = properties(foundation, "PlatformShellRelayLogGroup", "AWS::Logs::LogGroup")
if relay_log_group.get("LogGroupName") != "/ecs/kanbien-staging-platform-shell-relay" or relay_log_group.get("RetentionInDays") != {"!Ref": "LogRetentionDays"}:
    fail("PlatformShellRelayLogGroup must use the reviewed relay log destination and retention")
relay_collector_log_group = properties(foundation, "PlatformShellRelayOtelCollectorLogGroup", "AWS::Logs::LogGroup")
if relay_collector_log_group.get("LogGroupName") != "/ecs/kanbien-staging-platform-shell-relay-otel-collector" or relay_collector_log_group.get("RetentionInDays") != {"!Ref": "LogRetentionDays"}:
    fail("PlatformShellRelayOtelCollectorLogGroup must use the reviewed relay collector log destination and retention")
collector_configuration_parameter = properties(foundation, "OtelCollectorConfigurationParameter", "AWS::SSM::Parameter")
if collector_configuration_parameter.get("Name") != "/kanbien/staging/platform-shell/observability/collector-config" or collector_configuration_parameter.get("Type") != "String" or collector_configuration_parameter.get("Tier") != "Standard" or collector_configuration_parameter.get("DataType") != "text":
    fail("OtelCollectorConfigurationParameter must be the reviewed non-secret standard SSM String")
collector_configuration_value = collector_configuration_parameter.get("Value", {}).get("!Sub") if isinstance(collector_configuration_parameter.get("Value"), dict) else ""
for required_collector_configuration in (
    "endpoint: 127.0.0.1:4318",
    "service: monitoring",
    "metrics_endpoint: https://monitoring.${AWS::Region}.amazonaws.com/v1/metrics",
    "authenticator: sigv4auth",
    "memory_limiter",
    "exporters: [otlphttp/cloudwatch]",
):
    if required_collector_configuration not in collector_configuration_value:
        fail("OtelCollectorConfigurationParameter must retain the reviewed local OTLP, SigV4, bounded-memory, and CloudWatch metrics pipeline")

observability = target_profile.get("observability", {})
alarm_policy = observability.get("policy", {})
severity_vocabulary = []
expected_alarm_policy = {
    "standard": "docs/04.deploy/rules/03.product/platform-target-alerting-policy.yml",
    "catalogue_index": "infra/04.deploy/03.product/targets/README.md",
    "canonical_catalogue": "observability.alarms",
    "metric_series_catalogue": "observability.metric_series",
    "slo_catalogue": "observability.slos",
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


metric_delivery = observability.get("metric_delivery", {})
if not isinstance(metric_delivery, dict):
    fail("target profile metric delivery must be a mapping")
else:
    metric_delivery_status = metric_delivery.get("status")
    if metric_delivery_status not in {"prepared-not-deployed", "deployed-and-query-proven"}:
        fail("target profile metric delivery must declare a governed delivery status")
    for key, expected in {
        "adr": "docs/04.deploy/adrs/0029-use-task-local-otel-collector-for-cloudwatch-metrics.md",
        "provider": "aws",
        "adapter_package": "@kanbien/platform-adapter-aws-observability-cloudwatch",
        "adapter_implementation": "cloudwatch-otel",
        "protocol": "otlp-http-protobuf",
    }.items():
        if metric_delivery.get(key) != expected:
            fail(f"target profile metric delivery must set {key} to the reviewed initial value")
    live_proof = metric_delivery.get("live_proof")
    if metric_delivery_status == "deployed-and-query-proven":
        if not isinstance(live_proof, dict) or live_proof.get("query_interface") != "cloudwatch-promql":
            fail("deployed metric delivery must declare its CloudWatch PromQL proof interface")
        elif not isinstance(live_proof.get("protected_route_outcomes_observed"), list) or set(live_proof["protected_route_outcomes_observed"]) != {"denied-401", "succeeded-200"}:
            fail("deployed metric delivery must record the safe denied-401 and succeeded-200 proof outcomes")
        elif not isinstance(live_proof.get("series_observed"), list) or set(live_proof["series_observed"]) != {"kanbien.platform.server.request.outcome", "kanbien.platform.server.request.duration"}:
            fail("deployed metric delivery must record both approved CloudWatch metric series")
        elif not isinstance(live_proof.get("verified_at_utc"), str) or not live_proof["verified_at_utc"]:
            fail("deployed metric delivery must record a non-secret proof date")
        coverage = metric_delivery.get("coverage", {})
        if not isinstance(coverage, dict) or coverage.get("current_status") != "delivery-and-independent-coverage-verdict-path-and-exporter-loss-rollback-and-operator-alert-receipt-proven":
            fail("deployed metric delivery must retain the explicit SLO and exporter-loss coverage proof state")
        elif coverage.get("closure_plan") != {
            "coverage_signal": "target-owned-metric-freshness-check-outside-the-application-exporter-path",
            "rehearsal": "separately-approved-disposable-staging-task-revision-with-collector-receiver-mismatch-and-fixed-application-endpoint",
            "request_expectation": "protected-request-succeeds-while-telemetry-is-best-effort",
            "counter_semantics": "a-fresh-cumulative-counter-needs-an-exported-baseline-and-a-later-advancing-request-before-promql-increase-can-observe-freshness",
            "evidence_expectation": "coverage-check-marks-slo-insufficient-confidence-and-proves-alert-delivery",
            "recovery": "restore-normal-task-revision-through-governed-rollback-path",
        }:
            fail("deployed metric delivery must retain its governed exporter-loss closure plan")
    elif live_proof is not None:
        fail("prepared metric delivery must not claim live metric proof")
    if not Path(metric_delivery.get("adr", "")).is_file():
        fail("target profile metric delivery must reference its accepted deployment ADR")
    collector = metric_delivery.get("collector", {})
    if not isinstance(collector, dict) or collector.get("topology") != "ecs-task-sidecar" or collector.get("endpoint") != "http://127.0.0.1:4318/v1/metrics":
        fail("target profile metrics must use only the reviewed task-local ECS collector endpoint")
    elif collector.get("image") != "public.ecr.aws/aws-observability/aws-otel-collector@sha256:198e84d58236b3885919e721040b90dce29dec557783ff0fa0956f7ccc78f625" or collector.get("image_version") != "v0.48.0" or collector.get("cpu_units") != 128 or collector.get("memory_reservation_mib") != 256:
        fail("target profile metrics must pin the reviewed collector image and bounded sidecar capacity")
    elif collector.get("configuration") != {
        "source": "cloudformation-foundation-ssm-string-parameter",
        "parameter_name": "/kanbien/staging/platform-shell/observability/collector-config",
        "parameter_resource": "OtelCollectorConfigurationParameter",
        "delivery_environment_key": "AOT_CONFIG_CONTENT",
        "log_group_resource": "PlatformShellOtelCollectorLogGroup",
        "worker_log_group_resource": "PlatformShellWorkerOtelCollectorLogGroup",
        "relay_log_group_resource": "PlatformShellRelayOtelCollectorLogGroup",
        "output_parameter_arn": "OtelCollectorConfigurationParameterArn",
    }:
        fail("target profile metrics must declare the reviewed target-owned collector configuration record")
    metric_task = metric_delivery.get("task")
    if metric_task != {
        "cpu_units": 512,
        "memory_mib": 1024,
        "application_cpu_units": 384,
        "application_memory_reservation_mib": 512,
        "collector_dependency": "platform-shell-depends-on-otel-collector-start",
    }:
        fail("target profile metrics must declare the reviewed application and collector task capacity")
    worker_metric_task = metric_delivery.get("worker_task")
    if worker_metric_task != {
        "cpu_units": 512,
        "memory_mib": 1024,
        "application_cpu_units": 384,
        "application_memory_reservation_mib": 512,
        "collector_dependency": "platform-shell-worker-depends-on-otel-collector-start",
    }:
        fail("target profile metrics must declare the reviewed worker and collector task capacity")
    relay_metric_task = metric_delivery.get("relay_task")
    if relay_metric_task != {
        "cpu_units": 512,
        "memory_mib": 1024,
        "application_cpu_units": 384,
        "application_memory_reservation_mib": 512,
        "collector_dependency": "platform-shell-relay-depends-on-otel-collector-start",
    }:
        fail("target profile metrics must declare the reviewed relay and collector task capacity")
    metric_iam = metric_delivery.get("iam", {})
    if not isinstance(metric_iam, dict) or metric_iam.get("task_execution_role", {}).get("action") != "ssm:GetParameters" or metric_iam.get("task_execution_role", {}).get("resource") != "OtelCollectorConfigurationParameter" or metric_iam.get("task_role", {}).get("action") != "cloudwatch:PutMetricData" or metric_iam.get("task_role", {}).get("resource") != "*":
        fail("target profile metrics must declare its narrow SSM configuration and CloudWatch delivery IAM requirements")
    worker_metric_iam = metric_delivery.get("worker_iam", {})
    if not isinstance(worker_metric_iam, dict) or worker_metric_iam.get("task_execution_role", {}).get("action") != "ssm:GetParameters" or worker_metric_iam.get("task_execution_role", {}).get("resource") != "OtelCollectorConfigurationParameter" or worker_metric_iam.get("task_role", {}).get("action") != "cloudwatch:PutMetricData" or worker_metric_iam.get("task_role", {}).get("resource") != "*":
        fail("target profile metrics must declare narrow worker SSM configuration and CloudWatch delivery IAM requirements")
    relay_metric_iam = metric_delivery.get("relay_iam", {})
    if not isinstance(relay_metric_iam, dict) or relay_metric_iam.get("task_execution_role", {}).get("action") != "ssm:GetParameters" or relay_metric_iam.get("task_execution_role", {}).get("resource") != "OtelCollectorConfigurationParameter" or relay_metric_iam.get("task_role", {}).get("action") != "cloudwatch:PutMetricData" or relay_metric_iam.get("task_role", {}).get("resource") != "*":
        fail("target profile metrics must declare narrow relay SSM configuration and CloudWatch delivery IAM requirements")
    export = metric_delivery.get("export", {})
    if not isinstance(export, dict) or export.get("eligible_slo_measurement_sampling") != "none":
        fail("target profile metrics must preserve every eligible initial SLO measurement")
    if not isinstance(export, dict) or not isinstance(export.get("interval_ms"), int) or export["interval_ms"] < 1_000 or not isinstance(export.get("timeout_ms"), int) or export["timeout_ms"] <= 0 or export["timeout_ms"] > export["interval_ms"]:
        fail("target profile metrics must declare a bounded valid export interval and timeout")


metric_series = observability.get("metric_series")
if not isinstance(metric_series, list) or len(metric_series) == 0:
    fail("target profile must declare at least one target metric series")
    metric_series = []
worker_metric_coverage = observability.get("worker_metric_coverage")
if not isinstance(worker_metric_coverage, dict):
    fail("target profile must declare the reviewed worker metric-observation policy")
    worker_metric_coverage = {}
worker_metric_status = worker_metric_coverage.get("status")
if worker_metric_status != "deployed-and-query-proven":
    fail("target profile worker metric-observation policy must retain its observed deployed evidence state")
if worker_metric_coverage.get("live_proof") != {
    "executed_on_utc": "2026-09-23",
    "command": "npm run platform:shell:metric-coverage -- --coverage-target worker",
    "result": "observed",
    "worker_task_definition_revision": "1",
    "retained_evidence": "safe-verdict-task-revision-and-bounded-count-duration-only-no-queue-message-or-provider-payload",
}:
    fail("target profile worker metric-observation policy must retain its bounded live proof")
persistence_transition_metric_delivery = observability.get("persistence_transition_metric_delivery")
if not isinstance(persistence_transition_metric_delivery, dict) or persistence_transition_metric_delivery.get("status") != "source-composed-not-deployed" or persistence_transition_metric_delivery.get("runtime_targets") != ["worker", "relay"] or persistence_transition_metric_delivery.get("output_policy") != "approved-capability-action-execution-context-outcome-and-bounded-error-class-only":
    fail("target profile must retain the source-only persistence transition metric-delivery policy")
persistence_transition_metric_status = persistence_transition_metric_delivery.get("status") if isinstance(persistence_transition_metric_delivery, dict) else None
metric_series_by_id = {}
source_names = set()
instrument_names = set()
for series in metric_series:
    if not isinstance(series, dict):
        fail("target metric series entries must be mappings")
        continue
    series_id = series.get("id")
    if not isinstance(series_id, str) or not series_id or series_id in metric_series_by_id:
        fail("target metric series IDs must be non-empty and unique")
        continue
    metric_series_by_id[series_id] = series
    runtime_target = series.get("runtime_target")
    if runtime_target not in {"server", "worker", "relay"}:
        fail(f"target metric series {series_id} must identify server, worker, or relay delivery ownership")
    elif runtime_target == "server" and series.get("status") != metric_delivery.get("status"):
        fail(f"target server metric series {series_id} must use its delivery catalogue status")
    source = series.get("source", {})
    otel = series.get("otel", {})
    if not isinstance(source, dict) or not isinstance(otel, dict):
        fail(f"target metric series {series_id} must declare source and otel mappings")
        continue
    source_name = source.get("name")
    source_kind = source.get("kind")
    source_unit = source.get("unit")
    instrument_name = otel.get("instrument_name")
    if not isinstance(source_name, str) or not source_name.startswith("platform.") or source_name in source_names:
        fail(f"target metric series {series_id} must use a unique platform-owned source name")
    source_names.add(source_name)
    if source_name.startswith("platform.persistence.") and runtime_target in {"worker", "relay"}:
        if series.get("status") != persistence_transition_metric_status:
            fail(f"target persistence metric series {series_id} must retain its source-only transition-delivery status")
    elif runtime_target == "worker" and series.get("status") != worker_metric_status:
        fail(f"target worker metric series {series_id} must use the worker metric-observation evidence state")
    if source_kind not in {"counter", "gauge", "histogram", "timer"}:
        fail(f"target metric series {series_id} must declare a supported Core metric kind")
    if not isinstance(source_unit, str) or not source_unit:
        fail(f"target metric series {series_id} must declare a source unit")
    if not isinstance(instrument_name, str) or not instrument_name.startswith("kanbien.platform.") or instrument_name in instrument_names:
        fail(f"target metric series {series_id} must use a unique Kanbien OTel instrument name")
    instrument_names.add(instrument_name)
    labels = series.get("labels", {})
    allowed_names = labels.get("allowed_names") if isinstance(labels, dict) else None
    prohibited_names = labels.get("prohibited_names") if isinstance(labels, dict) else None
    if not isinstance(allowed_names, list) or not allowed_names or len(allowed_names) != len(set(allowed_names)) or not all(isinstance(name, str) and name.replace("_", "").isalnum() and name == name.lower() for name in allowed_names):
        fail(f"target metric series {series_id} must declare unique lowercase snake_case metric label names")
    if not isinstance(prohibited_names, list) or not all(isinstance(name, str) for name in prohibited_names) or set(allowed_names or []).intersection(prohibited_names or []):
        fail(f"target metric series {series_id} must distinguish allowed and prohibited labels")
    cardinality_limit = series.get("cardinality_limit")
    if not isinstance(cardinality_limit, int) or cardinality_limit <= 0 or cardinality_limit > 1_000:
        fail(f"target metric series {series_id} must set a positive cardinality limit no greater than 1000")
    histogram = series.get("histogram")
    if source_kind in {"timer", "histogram"}:
        boundaries = histogram.get("bucket_boundaries_ms") if isinstance(histogram, dict) else None
        if not isinstance(boundaries, list) or not boundaries or not all(isinstance(value, (int, float)) and value > 0 for value in boundaries) or any(current <= previous for previous, current in zip(boundaries, boundaries[1:])):
            fail(f"target metric series {series_id} must declare strictly increasing positive histogram bucket boundaries")
    elif histogram is not None:
        fail(f"target metric series {series_id} must not declare histogram buckets for a non-distribution metric")


slos = observability.get("slos")
if not isinstance(slos, list) or len(slos) == 0:
    fail("target profile must declare at least one target SLO")
    slos = []
slo_ids = set()
for slo in slos:
    if not isinstance(slo, dict):
        fail("target SLO entries must be mappings")
        continue
    slo_id = slo.get("id")
    if not isinstance(slo_id, str) or not slo_id or slo_id in slo_ids:
        fail("target SLO IDs must be non-empty and unique")
        continue
    slo_ids.add(slo_id)
    if slo.get("status") != "selected-not-evaluable":
        fail(f"target SLO {slo_id} must not claim evaluation before delivery is provisioned")
    population = slo.get("population", {})
    objective = slo.get("objective", {})
    confidence = slo.get("confidence", {})
    if not isinstance(population, dict) or not isinstance(objective, dict) or not isinstance(confidence, dict):
        fail(f"target SLO {slo_id} must declare population, objective, and confidence mappings")
        continue
    series_id = population.get("metric_series")
    series = metric_series_by_id.get(series_id)
    if series is None:
        fail(f"target SLO {slo_id} must reference a declared target metric series")
        continue
    required_dimensions = population.get("required_dimensions")
    if not isinstance(required_dimensions, dict) or not required_dimensions:
        fail(f"target SLO {slo_id} must declare a bounded eligible population")
    elif not set(required_dimensions).issubset(set(series.get("labels", {}).get("allowed_names", []))):
        fail(f"target SLO {slo_id} population dimensions must be allowed by its metric series")
    if not isinstance(slo.get("rolling_window_days"), int) or slo["rolling_window_days"] <= 0:
        fail(f"target SLO {slo_id} must declare a positive rolling window")
    if not isinstance(confidence.get("minimum_eligible_observations"), int) or confidence["minimum_eligible_observations"] <= 0 or confidence.get("below_minimum_state") != "insufficient-confidence" or not isinstance(confidence.get("synthetic_check"), str):
        fail(f"target SLO {slo_id} must declare low-volume and synthetic-check behaviour")
    if objective.get("kind") == "percentile_threshold":
        maximum_ms = objective.get("maximum_ms")
        boundaries = series.get("histogram", {}).get("bucket_boundaries_ms", [])
        if objective.get("percentile") not in {"p95", "p99"} or not isinstance(maximum_ms, (int, float)) or maximum_ms not in boundaries:
            fail(f"target latency SLO {slo_id} must use p95 or p99 and an exact histogram bucket threshold")
    elif objective.get("kind") == "success_ratio":
        if not isinstance(objective.get("good_outcome"), str) or not isinstance(objective.get("target_percent"), (int, float)) or not 0 < objective["target_percent"] <= 100:
            fail(f"target availability SLO {slo_id} must define a bounded successful outcome and percentage")
    else:
        fail(f"target SLO {slo_id} must declare a supported objective kind")

synthetic_checks = observability.get("synthetic_checks")
if not isinstance(synthetic_checks, list) or len(synthetic_checks) != 1:
    fail("target profile must declare exactly one initial controlled synthetic check")
else:
    synthetic_check = synthetic_checks[0]
    expected_synthetic_check = {
        "id": "platform-smoke-protected-read",
        "status": "active-manual-first-run-proven-scheduled-trigger-pending",
        "command": "npm run platform:shell:controlled-smoke",
        "cadence_target": "nominal-every-4-hours-best-effort",
        "identity": "dedicated-least-privilege-machine-client",
        "request": {
            "method": "GET",
            "route_pattern": "/smoke/<safe-synthetic-id>",
            "expected_http_status": 200,
        },
        "output_policy": "status-and-safe-latency-only-no-token-secret-or-response-body",
        "metric_coverage_sequence": {
            "request_count": 2,
            "inter_request_wait_seconds": 75,
            "purpose": "establish-and-advance-the-cumulative-counter-after-a-fresh-task-start",
        },
        "evidence_interpretation": "synthetic-boundary-evidence-not-unqualified-customer-traffic",
        "scheduler": "github-actions-temporary-active-manual-first-run-proven-scheduled-trigger-pending",
        "scheduler_execution_policy": "deployment.execution_policy.temporary_synthetic_scheduler",
    }
    if synthetic_check != expected_synthetic_check:
        fail("target profile controlled synthetic check must retain the governed safe command policy")
    else:
        referenced_synthetic_checks = {
            slo.get("confidence", {}).get("synthetic_check")
            for slo in slos
            if isinstance(slo, dict) and isinstance(slo.get("confidence"), dict)
        }
        if referenced_synthetic_checks != {synthetic_check["id"]}:
            fail("target SLOs must all reference the one governed controlled synthetic check")

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

target_execution_policy = target_profile.get("deployment", {}).get("execution_policy", {})
if not isinstance(target_execution_policy, dict):
    fail("target profile deployment execution policy must be a mapping")
    target_execution_policy = {}

image_publication = target_execution_policy.get("repeatable_image_publication", {})
expected_image_publication = {
    "mutation_style": "github-actions-oidc-ecr-publication-only",
    "workflow": ".github/workflows/deploy-platform-shell-staging.yml",
    "approval": "github-environment-manual",
    "role_name": "github-platform-shell-staging-deploy",
    "role_arn": "arn:aws:iam::337159794548:role/github-platform-shell-staging-deploy",
    "role_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-deploy-policy.json",
    "role_policy_deployment_status": "deployed-and-live-inspected",
}
if not isinstance(image_publication, dict):
    fail("target profile must define a repeatable GitHub image-publication policy")
else:
    for key, expected in expected_image_publication.items():
        if image_publication.get(key) != expected:
            fail(f"target GitHub image-publication policy must set {key} to the reviewed value")
    live_policy_proof = image_publication.get("live_policy_proof")
    if not isinstance(live_policy_proof, dict) or live_policy_proof.get("inspection") != "aws-iam-get-role-policy" or live_policy_proof.get("allowed_mutation_scope") != "ecr-image-publication-only" or not isinstance(live_policy_proof.get("verified_at_utc"), str) or not live_policy_proof["verified_at_utc"]:
        fail("target GitHub image-publication policy must retain safe live ECR-only policy-inspection evidence")

service_stack_change = target_execution_policy.get("repeatable_service_stack_change", {})
expected_service_stack_change = {
    "mutation_style": "governed-manual-aws-cli-change-set",
    "aws_profile": "kanbien-dev",
    "governing_workflow": ".agentic/aws/workflows/execute-approved-aws-change.md",
    "execution_gate": "reviewed-cloudformation-change-set-and-explicit-current-chat-approval",
}
if not isinstance(service_stack_change, dict):
    fail("target profile must define a separately governed repeatable service-stack change policy")
else:
    for key, expected in expected_service_stack_change.items():
        if service_stack_change.get(key) != expected:
            fail(f"target governed service-stack-change policy must set {key} to the reviewed value")

for forbidden_workflow_command in (
    "aws cloudformation deploy",
    "aws cloudformation create-change-set",
    "aws cloudformation execute-change-set",
    "aws ecs update-service",
    "aws ecs register-task-definition",
):
    if forbidden_workflow_command in github_workflow:
        fail(f"GitHub image-publication workflow must not contain service mutation command: {forbidden_workflow_command}")

github_policy_statements = github_deployment_policy.get("Statement", [])
if not isinstance(github_policy_statements, list):
    fail("GitHub image-publication identity policy must contain a statement list")
    github_policy_statements = []
expected_github_policy_sids = {"EcrAuth", "PlatformShellEcrImageAccess"}
actual_github_policy_sids = {
    statement.get("Sid")
    for statement in github_policy_statements
    if isinstance(statement, dict)
}
if actual_github_policy_sids != expected_github_policy_sids:
    fail("GitHub image-publication identity policy must contain only the reviewed ECR statements")
for statement in github_policy_statements:
    if not isinstance(statement, dict):
        fail("GitHub image-publication identity policy statements must be mappings")
        continue
    actions = statement.get("Action", [])
    if isinstance(actions, str):
        actions = [actions]
    if not isinstance(actions, list) or not actions or any(not isinstance(action, str) or not action.startswith("ecr:") for action in actions):
        fail("GitHub image-publication identity policy must allow only ECR actions")

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
    if telemetry_prerequisite.get("current_status") != "verified-enhanced-2026-09-22":
        fail("target profile Container Insights prerequisite must retain the verified enhanced evidence state")

operations = target_profile.get("operations", {})
readiness_closure = operations.get("readiness_closure", {}) if isinstance(operations, dict) else {}
if readiness_closure != {
    "authorization_403": {
        "status": "deployed-and-403-proven",
        "prerequisite": "separate-valid-machine-client-without-platform-smoke-read-permission",
        "authentication_boundary": "primary-client-plus-exact-additional-client-id-allowlist-no-wildcards",
        "target_configuration": "PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS-json-array",
        "negative_client_scope": "dedicated-unmapped-resource-server-scope",
        "proof_command": "npm run platform:shell:negative-authz-smoke",
        "safe_result": "status-code-only-403",
    },
    "rate_limit_429": {
        "status": "deployed-and-429-proven",
        "command": "npm run platform:shell:rate-limit-smoke",
        "request_bound": "fresh-fixed-window-declared-limit-plus-one-sequential-requests-stop-on-first-429",
        "fixed_window_alignment": "wait-for-next-window-boundary-and-return-inconclusive-on-rollover",
        "safe_result": "aggregate-counts-and-final-status-only",
        "request": {
            "method": "GET",
            "path": "/livez",
            "credentials": "none",
            "expected_allowed_status": 200,
            "expected_limited_status": 429,
            "slo_population_effect": "none-protected-capability-metrics-are-not-emitted-for-liveness",
        },
    },
    "waf_and_routing": {
        "status": "deployed-and-waf-routing-and-ingress-proven",
        "command": "npm run platform:shell:ingress-smoke",
        "proof": "read-only-waf-association-and-listener-host-rule-inspection-plus-bounded-public-host-check",
        "request": {
            "method": "GET",
            "path": "/livez",
            "credentials": "none",
            "expected_http_status": 200,
            "output_policy": "safe-facts-only-no-response-body-address-or-provider-payload",
        },
    },
    "worker_consumer": {
        "status": "deployed-and-consumer-and-metric-proven",
        "command": "npm run platform:shell:worker-smoke",
        "execution_guard": "--execute-and-approve-live-worker-smoke",
        "proof": "two-side-effect-free-direct-sqs-platform-smoke-rebuild-messages-through-the-dormant-worker-service-for-fresh-counter-evidence",
        "preconditions": {
            "worker_desired_count": 0,
            "worker_running_count": 0,
            "source_queue_visible_messages": 0,
            "dead_letter_queue_visible_messages": 0,
        },
        "bounded_action": {
            "worker_desired_count": 1,
            "message_type": "platform-smoke.rebuild",
            "payload": '{"rebuild":true}',
            "message_count": 2,
            "inter_message_wait_seconds": 75,
            "maximum_wait_seconds": 360,
            "metric_export_settlement_wait_seconds": 75,
        },
        "success": {
            "worker_started": True,
            "source_queue_visible_messages": 0,
            "dead_letter_queue_visible_messages": 0,
            "cleanup_worker_desired_count": 0,
        },
        "safe_result": "status-counts-duration-and-task-revision-only-no-message-body-id-receipt-queue-url-or-provider-payload",
        "limitation": "direct-consumer-proof-only-not-a-producer-transaction-outbox-or-durable-business-idempotency-proof",
    },
    "alarm_and_rollback": {
        "status": "planned",
        "alert_proof": "explicitly-marked-notification-receipt-without-email-content-in-repository",
        "rollback_proof": "reversible-task-definition-revision-and-governed-restore",
    },
}:
    fail("target profile must retain the governed remaining public-boundary and operational closure plan")

worker_consumer_live_evidence = operations.get("worker_consumer_live_evidence") if isinstance(operations, dict) else {}
if worker_consumer_live_evidence != {
    "executed_on_utc": "2026-09-23",
    "command": "npm run platform:shell:worker-smoke -- --execute --approve-live-worker-smoke",
    "result": "passed",
    "worker_task_definition_revision": "1",
    "duration_ms": 278716,
    "message_count": 2,
    "inter_message_wait_seconds": 75,
    "metric_export_settlement_wait_seconds": 75,
    "post_proof_state": "worker-desired-and-running-zero-source-and-dead-letter-queues-empty",
    "metric_observation": "observed-by-fixed-worker-coverage-target",
    "retained_evidence": "safe-status-count-duration-task-revision-and-verdict-only-no-message-body-id-receipt-queue-url-or-provider-payload",
}:
    fail("target profile must retain the safe, bounded worker consumer and metric-observation evidence")

public_boundary_live_evidence = operations.get("public_boundary_live_evidence") if isinstance(operations, dict) else {}
if public_boundary_live_evidence != {
    "executed_on_utc": "2026-09-23",
    "rate_limit_429": {
        "command": "npm run platform:shell:rate-limit-smoke -- --execute",
        "result": "passed",
        "attempted_request_count": 121,
        "allowed_request_count": 120,
        "first_429_request": 121,
        "final_status": 429,
        "total_duration_ms": 12213,
    },
    "waf_routing_and_ingress": {
        "command": "npm run platform:shell:ingress-smoke -- --execute",
        "result": "passed",
        "http_status": 200,
        "duration_ms": 163,
        "host_rule_priority": 20,
    },
    "retained_evidence": "aggregate-status-count-duration-and-rule-priority-only-no-address-response-body-header-or-provider-payload",
}:
    fail("target profile must retain the safe, bounded public-boundary evidence")

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

task_definition = properties(service, "TaskDefinition", "AWS::ECS::TaskDefinition")
task_cpu_parameter = service.get("Parameters", {}).get("Cpu", {})
task_memory_parameter = service.get("Parameters", {}).get("Memory", {})
if task_definition.get("Cpu") != {"!Ref": "Cpu"} or task_definition.get("Memory") != {"!Ref": "Memory"} or task_cpu_parameter.get("Default") != "512" or task_cpu_parameter.get("AllowedValues") != ["512"] or task_memory_parameter.get("Default") != "1024" or task_memory_parameter.get("AllowedValues") != ["1024"]:
    fail("TaskDefinition must use the reviewed 512 CPU and 1024 MiB sidecar-capable task capacity")
containers = task_definition.get("ContainerDefinitions", [])
containers_by_name = {item.get("Name"): item for item in containers if isinstance(item, dict)}
container = containers_by_name.get("platform-shell", {})
collector_container = containers_by_name.get("otel-collector", {})
if container.get("ReadonlyRootFilesystem") is not True:
    fail("platform-shell container must use a read-only root filesystem")
if container.get("Secrets"):
    fail("platform-shell task must not receive a Cognito client secret")
if container.get("Cpu") != 384 or container.get("MemoryReservation") != 512:
    fail("platform-shell container must retain the reviewed application CPU and memory reservation")
if container.get("DependsOn") != [{"ContainerName": "otel-collector", "Condition": "START"}]:
    fail("platform-shell container must depend on the collector starting before it starts")
health_check = container.get("HealthCheck", {})
if health_check.get("Command", [])[:3] != ["CMD", "/nodejs/bin/node", "-e"]:
    fail("platform-shell ECS health check must use exec-form Node commands without a shell")
if collector_container.get("Image") != "public.ecr.aws/aws-observability/aws-otel-collector@sha256:198e84d58236b3885919e721040b90dce29dec557783ff0fa0956f7ccc78f625" or collector_container.get("Essential") is not True or collector_container.get("ReadonlyRootFilesystem") is not True or collector_container.get("Cpu") != 128 or collector_container.get("MemoryReservation") != 256:
    fail("otel-collector must use the reviewed immutable image, read-only filesystem, and bounded capacity")
if collector_container.get("PortMappings"):
    fail("otel-collector must not publish a task-facing metrics port")
collector_secrets = collector_container.get("Secrets")
if collector_secrets != [{"Name": "AOT_CONFIG_CONTENT", "ValueFrom": {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-OtelCollectorConfigurationParameterArn"}}}]:
    fail("otel-collector must read only the reviewed target configuration through ECS SSM value injection")
collector_environment = {entry.get("Name"): entry.get("Value") for entry in collector_container.get("Environment", [])}
if collector_environment != {"AWS_REGION": "eu-west-1"}:
    fail("otel-collector must retain only the reviewed CloudWatch region environment value")
collector_log_options = collector_container.get("LogConfiguration", {}).get("Options", {})
if collector_container.get("LogConfiguration", {}).get("LogDriver") != "awslogs" or collector_log_options.get("awslogs-stream-prefix") != "otel-collector" or collector_log_options.get("awslogs-group") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-OtelCollectorLogGroupName"}}:
    fail("otel-collector must use its separate reviewed operational log destination")
environment = {entry.get("Name"): entry.get("Value") for entry in container.get("Environment", [])}
required_environment = {
    "PLATFORM_DEPLOYMENT_EXPOSURE": "public",
    "PLATFORM_AUTH_PROVIDER": "cognito",
    "PLATFORM_RATE_LIMIT_PROVIDER": "dynamodb",
    "PLATFORM_PERSISTENCE_PROVIDER": "dynamodb",
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
    elif key == "PLATFORM_PERSISTENCE_DYNAMODB_TABLE":
        if not contains_intrinsic(environment.get(key), "!Sub", "${FoundationStackName}-PlatformPersistenceTableName"):
            fail("platform-shell task must obtain the persistence table name from the foundation stack")
    elif key == "PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX":
        if not contains_intrinsic(environment.get(key), "!Sub", "${FoundationStackName}-PlatformPersistenceOutboxDueIndexName"):
            fail("platform-shell task must obtain the persistence due index from the foundation stack")
    elif key == "PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX":
        if not contains_intrinsic(environment.get(key), "!Sub", "${FoundationStackName}-PlatformPersistenceLineageCauseIndexName"):
            fail("platform-shell task must obtain the persistence lineage index from the foundation stack")
    elif environment.get(key) != value:
        fail(f"service template must match target-profile non-secret value for {key}")

def metric_series_environment(series):
    source = series.get("source", {})
    otel = series.get("otel", {})
    expected_series = {
        "sourceName": source.get("name"),
        "sourceKind": source.get("kind"),
        "sourceUnit": source.get("unit"),
        "instrumentName": otel.get("instrument_name"),
        "description": otel.get("description"),
        "allowedLabelNames": series.get("labels", {}).get("allowed_names"),
        "cardinalityLimit": series.get("cardinality_limit"),
    }
    if "histogram" in series:
        expected_series["histogramBucketBoundaries"] = series.get("histogram", {}).get("bucket_boundaries_ms")
    return expected_series

expected_metric_series_environment = [
    metric_series_environment(series)
    for series in metric_series
    if series.get("runtime_target") == "server"
]
try:
    actual_metric_series_environment = json.loads(environment.get("PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON", ""))
except (TypeError, json.JSONDecodeError):
    fail("platform-shell task must provide valid JSON metric-series configuration")
else:
    if actual_metric_series_environment != expected_metric_series_environment:
        fail("platform-shell task metric-series JSON must be a mechanical projection of the reviewed target catalogue")

worker_task_definition = properties(service, "WorkerTaskDefinition", "AWS::ECS::TaskDefinition")
if worker_task_definition.get("Family") != "kanbien-staging-platform-shell-worker" or worker_task_definition.get("Cpu") != "512" or worker_task_definition.get("Memory") != "1024":
    fail("WorkerTaskDefinition must retain the reviewed worker family and sidecar-capable capacity")
if worker_task_definition.get("ExecutionRoleArn") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-TaskExecutionRoleArn"}} or worker_task_definition.get("TaskRoleArn") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-WorkerTaskRoleArn"}}:
    fail("WorkerTaskDefinition must use the reviewed execution and least-privilege worker task roles")
worker_containers = {item.get("Name"): item for item in worker_task_definition.get("ContainerDefinitions", []) if isinstance(item, dict)}
worker_container = worker_containers.get("platform-shell-worker", {})
worker_collector = worker_containers.get("otel-collector", {})
if worker_container.get("Image") != {"!Ref": "ImageUri"} or worker_container.get("Command") != [".cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/kanbien-platform-worker.main.js"] or worker_container.get("ReadonlyRootFilesystem") is not True or worker_container.get("Cpu") != 384 or worker_container.get("MemoryReservation") != 512 or worker_container.get("PortMappings") or worker_container.get("HealthCheck") or worker_container.get("Secrets"):
    fail("platform-shell-worker must be a non-public read-only worker without ports, health endpoint, or task secrets")
if worker_container.get("DependsOn") != [{"ContainerName": "otel-collector", "Condition": "START"}]:
    fail("platform-shell-worker must depend on the collector starting before it starts")
if worker_collector.get("Image") != collector_container.get("Image") or worker_collector.get("ReadonlyRootFilesystem") is not True or worker_collector.get("Cpu") != 128 or worker_collector.get("MemoryReservation") != 256 or worker_collector.get("PortMappings"):
    fail("worker collector must retain the reviewed immutable image, read-only filesystem, and bounded capacity")
if worker_collector.get("Secrets") != [{"Name": "AOT_CONFIG_CONTENT", "ValueFrom": {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-OtelCollectorConfigurationParameterArn"}}}]:
    fail("worker collector must read only the reviewed target configuration through ECS SSM value injection")
worker_collector_options = worker_collector.get("LogConfiguration", {}).get("Options", {})
if worker_collector.get("LogConfiguration", {}).get("LogDriver") != "awslogs" or worker_collector_options.get("awslogs-stream-prefix") != "worker-otel-collector" or worker_collector_options.get("awslogs-group") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-WorkerOtelCollectorLogGroupName"}}:
    fail("worker collector must use its separate reviewed worker collector log destination")
worker_environment = {entry.get("Name"): entry.get("Value") for entry in worker_container.get("Environment", [])}
worker_target_environment = target_profile.get("config", {}).get("worker_non_secret_env", {})
if not isinstance(worker_target_environment, dict):
    fail("target profile must declare worker non-secret deployment configuration")
else:
    for key, value in worker_target_environment.items():
        if key in {"PLATFORM_PERSISTENCE_DYNAMODB_TABLE", "PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX", "PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX"}:
            continue
        if worker_environment.get(key) != value:
            fail(f"worker task must match target-profile worker non-secret value for {key}")
if worker_environment.get("PLATFORM_PERSISTENCE_DYNAMODB_TABLE") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-PlatformPersistenceTableName"}}:
    fail("worker task must obtain the persistence table name from the foundation stack")
if worker_environment.get("PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-PlatformPersistenceOutboxDueIndexName"}}:
    fail("worker task must obtain the persistence due index from the foundation stack")
if worker_environment.get("PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-PlatformPersistenceLineageCauseIndexName"}}:
    fail("worker task must obtain the persistence lineage index from the foundation stack")
if worker_environment.get("PLATFORM_WORKER_SQS_QUEUE_URL") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-WorkerQueueUrl"}}:
    fail("worker task must obtain the source queue URL from the foundation stack")
expected_worker_metric_series_environment = [
    metric_series_environment(series)
    for series in metric_series
    if series.get("runtime_target") == "worker"
]
try:
    actual_worker_metric_series_environment = json.loads(worker_environment.get("PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON", ""))
except (TypeError, json.JSONDecodeError):
    fail("worker task must provide valid JSON metric-series configuration")
else:
    if actual_worker_metric_series_environment != expected_worker_metric_series_environment:
        fail("worker task metric-series JSON must be a mechanical projection of the reviewed target catalogue")

worker_desired_count_parameter = service.get("Parameters", {}).get("WorkerDesiredCount", {})
if worker_desired_count_parameter.get("Default") != 0 or worker_desired_count_parameter.get("MinValue") != 0 or worker_desired_count_parameter.get("MaxValue") != 1:
    fail("WorkerDesiredCount must default to zero and permit only the reviewed bounded proof scale")
worker_service = properties(service, "WorkerService", "AWS::ECS::Service")
if worker_service.get("ServiceName") != "kanbien-staging-platform-shell-worker" or worker_service.get("DesiredCount") != {"!Ref": "WorkerDesiredCount"} or worker_service.get("TaskDefinition") != {"!Ref": "WorkerTaskDefinition"} or worker_service.get("LoadBalancers") or worker_service.get("EnableExecuteCommand") is not False:
    fail("WorkerService must retain its non-public, bounded worker deployment shape")
if worker_service.get("DeploymentConfiguration") != {"MinimumHealthyPercent": 0, "MaximumPercent": 100, "DeploymentCircuitBreaker": {"Enable": True, "Rollback": True}}:
    fail("WorkerService must retain the reviewed zero-to-one worker rollout configuration")
worker_network = worker_service.get("NetworkConfiguration", {}).get("AwsvpcConfiguration", {})
if worker_network.get("AssignPublicIp") != "ENABLED" or worker_network.get("SecurityGroups") != [{"Fn::ImportValue": {"!Sub": "${FoundationStackName}-WorkerSecurityGroupId"}}]:
    fail("WorkerService must use only the reviewed worker security group and controlled outbound network path")

relay_task_definition = properties(service, "RelayTaskDefinition", "AWS::ECS::TaskDefinition")
if relay_task_definition.get("Family") != "kanbien-staging-platform-shell-relay" or relay_task_definition.get("Cpu") != "512" or relay_task_definition.get("Memory") != "1024":
    fail("RelayTaskDefinition must retain the reviewed one-pass relay family and sidecar-capable capacity")
if relay_task_definition.get("ExecutionRoleArn") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-TaskExecutionRoleArn"}} or relay_task_definition.get("TaskRoleArn") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-RelayTaskRoleArn"}}:
    fail("RelayTaskDefinition must use the reviewed execution and least-privilege relay task roles")
relay_containers = {item.get("Name"): item for item in relay_task_definition.get("ContainerDefinitions", []) if isinstance(item, dict)}
relay_container = relay_containers.get("platform-shell-relay", {})
relay_collector = relay_containers.get("otel-collector", {})
if relay_container.get("Image") != {"!Ref": "ImageUri"} or relay_container.get("Command") != [".cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/kanbien-platform-relay.main.js"] or relay_container.get("ReadonlyRootFilesystem") is not True or relay_container.get("Cpu") != 384 or relay_container.get("MemoryReservation") != 512 or relay_container.get("PortMappings") or relay_container.get("HealthCheck") or relay_container.get("Secrets"):
    fail("platform-shell-relay must be a one-pass non-public read-only task without ports, health endpoint, or task secrets")
if relay_container.get("DependsOn") != [{"ContainerName": "otel-collector", "Condition": "START"}]:
    fail("platform-shell-relay must depend on the collector starting before it starts")
if relay_collector.get("Image") != collector_container.get("Image") or relay_collector.get("ReadonlyRootFilesystem") is not True or relay_collector.get("Cpu") != 128 or relay_collector.get("MemoryReservation") != 256 or relay_collector.get("PortMappings"):
    fail("relay collector must retain the reviewed immutable image, read-only filesystem, and bounded capacity")
if relay_collector.get("Secrets") != [{"Name": "AOT_CONFIG_CONTENT", "ValueFrom": {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-OtelCollectorConfigurationParameterArn"}}}]:
    fail("relay collector must read only the reviewed target configuration through ECS SSM value injection")
relay_collector_options = relay_collector.get("LogConfiguration", {}).get("Options", {})
if relay_collector.get("LogConfiguration", {}).get("LogDriver") != "awslogs" or relay_collector_options.get("awslogs-stream-prefix") != "relay-otel-collector" or relay_collector_options.get("awslogs-group") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-RelayOtelCollectorLogGroupName"}}:
    fail("relay collector must use its separate reviewed relay collector log destination")
relay_environment = {entry.get("Name"): entry.get("Value") for entry in relay_container.get("Environment", [])}
relay_target_environment = target_profile.get("config", {}).get("relay_non_secret_env", {})
if not isinstance(relay_target_environment, dict):
    fail("target profile must declare relay non-secret deployment configuration")
else:
    for key, value in relay_target_environment.items():
        if key in {"PLATFORM_PERSISTENCE_DYNAMODB_TABLE", "PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX", "PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX"}:
            continue
        if relay_environment.get(key) != value:
            fail(f"relay task must match target-profile relay non-secret value for {key}")
if relay_environment.get("PLATFORM_PERSISTENCE_DYNAMODB_TABLE") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-PlatformPersistenceTableName"}}:
    fail("relay task must obtain the persistence table name from the foundation stack")
if relay_environment.get("PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-PlatformPersistenceOutboxDueIndexName"}}:
    fail("relay task must obtain the persistence due index from the foundation stack")
if relay_environment.get("PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-PlatformPersistenceLineageCauseIndexName"}}:
    fail("relay task must obtain the persistence lineage index from the foundation stack")
if relay_environment.get("PLATFORM_RELAY_SQS_QUEUE_URL") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-WorkerQueueUrl"}}:
    fail("relay task must obtain the source queue URL from the foundation stack")
expected_relay_metric_series_environment = [
    metric_series_environment(series)
    for series in metric_series
    if series.get("runtime_target") == "relay"
]
try:
    actual_relay_metric_series_environment = json.loads(relay_environment.get("PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON", ""))
except (TypeError, json.JSONDecodeError):
    fail("relay task must provide valid JSON metric-series configuration")
else:
    if actual_relay_metric_series_environment != expected_relay_metric_series_environment:
        fail("relay task metric-series JSON must be a mechanical projection of the reviewed target catalogue")
relay_log_options = relay_container.get("LogConfiguration", {}).get("Options", {})
if relay_container.get("LogConfiguration", {}).get("LogDriver") != "awslogs" or relay_log_options.get("awslogs-stream-prefix") != "platform-shell-relay" or relay_log_options.get("awslogs-group") != {"Fn::ImportValue": {"!Sub": "${FoundationStackName}-RelayLogGroupName"}}:
    fail("relay task must use its separate reviewed relay log destination")

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
