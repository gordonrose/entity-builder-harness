#!/usr/bin/env python3
"""Fail closed when the declared Kanbien staging deployment state is not live."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.reconcile-platform-shell-staging
#   version: 6
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Safely reconcile declared Kanbien staging controls before mutation and on a recurring read-only cadence.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network
#   used_by:
#   - id: package.script.platform-shell-deployment-reconciliation
#     path: package.json

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import re
from pathlib import Path
import subprocess
import sys
import time
from collections.abc import Callable
from typing import Any


DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
SAFE_SCHEMA = "deploy/platform-shell-reconciliation-result/v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
AWS_MAX_ATTEMPTS = 3
AWS_RETRY_BACKOFF_SECONDS = (1, 2)
BOOTSTRAP_EFFECTS_RECONCILIATION_STAGE = "bootstrap_effects_reconciliation"
BOOTSTRAP_EFFECTS_ASSESSMENT_STAGE = "bootstrap_effects_assessment"
BOOTSTRAP_EFFECTS_FACT_LABELS = {
    "bootstrap_effects_facts_one": "kb-pg6-be-f1-r5-a1",
    "bootstrap_effects_facts_two": "kb-pg6-be-f2-r5-a1",
}
RECOVERABLE_INTERRUPTED_SCHEMA_SETUP = {
    "migration_role_exists": True, "runtime_role_exists": True, "bootstrap_has_migration_membership": False,
    "migration_database_connect": True, "migration_database_create": True, "migration_database_temporary": True,
    "runtime_database_connect": True, "schema_exists": False, "schema_owned_by_migration": False,
    "runtime_schema_usage": False, "runtime_schema_create_restricted": False, "runtime_existing_table_dml": False,
}


class ReconciliationError(Exception):
    """Represent one bounded failure without exposing a provider payload."""


def parse_arguments() -> argparse.Namespace:
    """Accept only a static check, a recurring check, or a reviewed pre-change-set check."""

    parser = argparse.ArgumentParser(description="Safely reconcile the declared Kanbien staging deployment state.")
    parser.add_argument("--validate", action="store_true", help="Validate source only; make no AWS call.")
    parser.add_argument("--mode", choices=("continuous", "pre-foundation-change-set", "pre-foundation-egress-remediation-change-set", "pre-relational-stage6-foundation-change-set", "pre-relational-stage6-service-change-set", "pre-relational-stage6-bootstrap-recovery-service-change-set", "pre-candidate-execution-preflight-onboarding-change-set", "pre-candidate-execution-preflight-image-change-set", "role-policy-alignment"), default="continuous")
    parser.add_argument("--foundation-change-set", help="The reviewed Foundation change-set name, required only for a Foundation preflight mode.")
    parser.add_argument("--service-change-set", help="The reviewed service change-set name, required only for the isolated relational Stage 6 service preflight.")
    parser.add_argument("--service-drift-evidence", help="New /tmp safe Service-drift evidence, required only for the isolated relational Stage 6 service preflight.")
    parser.add_argument("--known-foundation-drift-evidence", help="A new safe /tmp evidence record, required only for the exact egress-remediation preflight.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE)
    parser.add_argument("--aws-cli", default="aws")
    parser.add_argument("--aws-credential-source", choices=("target-profile", "environment"), default="target-profile")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--json", action="store_true", help="Emit only the safe structured reconciliation verdict.")
    arguments = parser.parse_args()
    if not 1 <= arguments.timeout_seconds <= 30:
        parser.error("--timeout-seconds must be between 1 and 30")
    preflight_modes = {"pre-foundation-change-set", "pre-foundation-egress-remediation-change-set", "pre-relational-stage6-foundation-change-set"}
    relational_service_preflight_modes = {"pre-relational-stage6-service-change-set", "pre-relational-stage6-bootstrap-recovery-service-change-set"}
    candidate_preflight_modes = {"pre-candidate-execution-preflight-onboarding-change-set", "pre-candidate-execution-preflight-image-change-set"}
    service_preflight_modes = relational_service_preflight_modes | candidate_preflight_modes
    service_preflight_mode = arguments.mode in service_preflight_modes
    if arguments.validate and (arguments.foundation_change_set or arguments.service_change_set or arguments.known_foundation_drift_evidence or arguments.service_drift_evidence):
        parser.error("--validate cannot inspect a change set or evidence record")
    if arguments.mode in preflight_modes and not arguments.validate and not arguments.foundation_change_set:
        parser.error("--foundation-change-set is required for a Foundation preflight mode")
    if arguments.mode not in preflight_modes and arguments.foundation_change_set:
        parser.error("--foundation-change-set is permitted only for a Foundation preflight mode")
    if service_preflight_mode and not arguments.validate and not arguments.service_change_set:
        parser.error("--service-change-set is required for the isolated relational Stage 6 service preflight")
    if not service_preflight_mode and arguments.service_change_set:
        parser.error("--service-change-set is permitted only for the isolated relational Stage 6 service preflight")
    if arguments.mode in {"pre-foundation-egress-remediation-change-set", "pre-relational-stage6-foundation-change-set", *relational_service_preflight_modes} and not arguments.validate:
        if not arguments.known_foundation_drift_evidence:
            parser.error("--known-foundation-drift-evidence is required for the exact egress-remediation preflight")
        evidence = Path(arguments.known_foundation_drift_evidence)
        if not evidence.is_absolute() or evidence.parent != Path("/tmp"):
            parser.error("--known-foundation-drift-evidence must be a direct child of /tmp")
    if arguments.mode not in {"pre-foundation-egress-remediation-change-set", "pre-relational-stage6-foundation-change-set", *relational_service_preflight_modes} and arguments.known_foundation_drift_evidence:
        parser.error("--known-foundation-drift-evidence is permitted only for a relational Foundation preflight with classified drift")
    if service_preflight_mode and not arguments.validate:
        if not arguments.service_drift_evidence:
            parser.error("--service-drift-evidence is required for the isolated relational Stage 6 service preflight")
        evidence = Path(arguments.service_drift_evidence)
        if not evidence.is_absolute() or evidence.parent != Path("/tmp"):
            parser.error("--service-drift-evidence must be a direct child of /tmp")
    if not service_preflight_mode and arguments.service_drift_evidence:
        parser.error("--service-drift-evidence is permitted only for the isolated relational Stage 6 service preflight")
    if arguments.mode == "role-policy-alignment" and not arguments.validate and arguments.aws_credential_source != "target-profile":
        parser.error("role-policy-alignment requires the declared administrator target-profile credentials")
    if arguments.mode in {"pre-foundation-egress-remediation-change-set", "pre-relational-stage6-foundation-change-set"} and not arguments.validate and arguments.aws_credential_source != "target-profile":
        parser.error("a relational Foundation preflight requires declared administrator target-profile credentials")
    if service_preflight_mode and not arguments.validate and arguments.aws_credential_source != "target-profile":
        parser.error("a controlled Service preflight requires declared administrator target-profile credentials")
    return arguments


def load_yaml(path: Path) -> dict[str, Any]:
    """Load one reviewed target profile and reject any malformed source."""

    try:
        import yaml
    except ImportError as exception:
        raise ReconciliationError("source-parser-unavailable") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise ReconciliationError("target-profile-unreadable") from exception
    if not isinstance(document, dict):
        raise ReconciliationError("target-profile-invalid")
    return document


def mapping(value: Any, code: str) -> dict[str, Any]:
    """Require a map rather than adopting a default for deployment control data."""

    if not isinstance(value, dict):
        raise ReconciliationError(code)
    return value


def text(value: Any, code: str) -> str:
    """Require one non-empty trusted source string."""

    if not isinstance(value, str) or not value:
        raise ReconciliationError(code)
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract exactly the small set of non-secret controls that can be reconciled."""

    cloud = mapping(profile.get("cloud"), "cloud-policy-missing")
    deployment = mapping(profile.get("deployment"), "deployment-policy-missing")
    cloudformation = mapping(deployment.get("cloudformation"), "cloudformation-policy-missing")
    reconciliation = mapping(deployment.get("reconciliation"), "reconciliation-policy-missing")
    operations = mapping(profile.get("operations"), "operations-policy-missing")
    budget = mapping(operations.get("budget"), "budget-policy-missing")
    allocation = mapping(budget.get("cost_allocation"), "budget-allocation-policy-missing")
    account_id = text(cloud.get("account_id"), "account-id-missing")
    region = text(cloud.get("region"), "region-missing")
    aws_profile = text(cloud.get("profile"), "aws-profile-missing")
    foundation_stack = text(cloudformation.get("foundation_stack"), "foundation-stack-missing")
    service_stack = text(cloudformation.get("service_stack"), "service-stack-missing")
    artifact_stack = text(cloudformation.get("deployment_artifact_store_stack"), "artifact-stack-missing")
    artifact_bucket = text(cloudformation.get("deployment_artifact_bucket_name"), "artifact-bucket-missing")
    if not account_id.isdigit() or len(account_id) != 12 or region != "eu-west-1":
        raise ReconciliationError("target-account-or-region-invalid")
    drift_evidence = mapping(reconciliation.get("drift_evidence"), "drift-evidence-policy-missing")
    live_role_policy_alignment = mapping(reconciliation.get("live_role_policy_alignment"), "live-role-policy-alignment-missing")
    operation_authorization_contract = text(
        reconciliation.get("operation_authorization_contract"),
        "operation-authorization-contract-missing",
    )
    expected_drift_evidence = {
        "strategy": "separate-target-scoped-detector",
        "github_role_may_start_detection": False,
        "github_role_evidence": "fresh-in-sync-stack-summary-only",
        "maximum_evidence_age_seconds": 21600,
        "resource_read_contract": "infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/resource-read-contract.yml",
        "detector_deployment_status": "source-planned-not-deployed",
        "administrator_active_assessment_contract": "infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/administrator-active-foundation-assessment-contract.yml",
        "administrator_active_assessment": {
            "status": "approved-administrator-only-foundation-drift-classification",
            "command": "npm run platform:shell:foundation-active-drift-assessment -- --execute-approved-active-foundation-drift-assessment --evidence-file /tmp/new-safe-evidence.json --json",
            "execution_identity": "target-profile-administrator-only-not-github",
            "scope": "foundation-stack-only-structural-drift-classification-no-resource-policy-role-or-workload-change",
            "allowed_operations": [
                "cloudformation:DetectStackDrift",
                "cloudformation:DescribeStackDriftDetectionStatus",
                "cloudformation:DescribeStackResourceDrifts",
                "cloudformation:DescribeStacks",
                "rds:DescribeDBInstances",
                "rds:DescribeDBParameters",
            ],
            "success_condition": "detection-complete-and-in-sync-or-only-known-relational-database-egress-property-addition-plus-declared-tls-normalization-and-effective-tls-required",
            "output_policy": "safe-check-identifiers-verdicts-and-safe-subprocess-failure-class-and-only-logical-resource-type-and-change-category-no-detection-id-provider-response-physical-id-or-property-values",
        },
        "artifact_active_assessment": {
            "status": "approved-administrator-only-artifact-drift-assessment",
            "command": "npm run platform:shell:artifact-active-drift-assessment -- --execute-approved-active-artifact-drift-assessment --evidence-file /tmp/new-safe-evidence.json --json",
            "execution_identity": "target-profile-administrator-only-not-github",
            "scope": "deployment-artifact-stack-only-detect-and-status-poll-no-resource-detail-read-or-mutation",
            "allowed_operations": ["sts:GetCallerIdentity", "cloudformation:DescribeStacks", "cloudformation:DetectStackDrift", "cloudformation:DescribeStackDriftDetectionStatus"],
            "success_condition": "detection-complete-and-deployment-artifact-stack-in-sync",
            "output_policy": "safe-check-identifiers-and-verdicts-only-no-detection-id-provider-response-resource-detail-or-property-values",
            "maximum_evidence_age_seconds": 900,
        },
        "operational_coverage": "administrator-only-foundation-artifact-and-service-assessments-available-detector-role-workload-cost-and-live-proof-pending",
        "service_active_assessment": {
            "status": "approved-administrator-only-service-drift-assessment",
            "command": "npm run platform:shell:service-active-drift-assessment -- --execute-approved-active-service-drift-assessment --evidence-file /tmp/new-safe-evidence.json --json",
            "execution_identity": "target-profile-administrator-only-not-github",
            "scope": "service-stack-only-detect-and-status-poll-no-resource-detail-read-or-mutation",
            "allowed_operations": ["sts:GetCallerIdentity", "cloudformation:DescribeStacks", "cloudformation:DetectStackDrift", "cloudformation:DescribeStackDriftDetectionStatus"],
            "success_condition": "detection-complete-and-service-stack-in-sync",
            "output_policy": "safe-check-identifiers-and-verdicts-only-no-detection-id-provider-response-resource-detail-or-property-values",
            "maximum_evidence_age_seconds": 900,
        },
        "candidate_preflight_baseline_assessment": {
            "status": "approved-administrator-only-candidate-preflight-baseline-assessment",
            "command": "npm run platform:shell:service-active-drift-assessment -- --candidate-onboarding --execute-approved-active-service-drift-assessment --evidence-file /tmp/new-safe-evidence.json --json",
            "execution_identity": "target-profile-administrator-only-not-github",
            "scope": "service-stack-detect-and-status-poll-plus-fixed-source-service-steady-state-read-no-resource-detail-or-mutation",
            "allowed_operations": ["sts:GetCallerIdentity", "cloudformation:DescribeStacks", "cloudformation:DetectStackDrift", "cloudformation:DescribeStackDriftDetectionStatus", "ecs:DescribeServices"],
            "accepted_service_stack_statuses": ["UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"],
            "source_service": "kanbien-staging-platform-shell",
            "success_condition": "detection-complete-and-service-stack-in-sync-and-source-service-steady",
            "output_policy": "safe-check-identifiers-and-verdicts-only-no-detection-id-provider-response-resource-detail-or-property-values",
            "maximum_evidence_age_seconds": 900,
        },
    }
    if drift_evidence != expected_drift_evidence:
        raise ReconciliationError("drift-evidence-policy-not-reviewed")
    expected_live_role_policy_alignment = {
        "role_name": "github-platform-shell-staging-reconciliation",
        "inline_policy_name": "ReadDeclaredStagingControls",
        "desired_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json",
        "status": "live-policy-aligned-and-identity-proof-passed",
        "command": "npm run platform:shell:deployment-reconciliation:role-policy-alignment",
        "required_before_foundation_change_set_execution": True,
        "output_policy": "safe-check-identifier-and-verdict-only-no-live-policy-content",
    }
    if live_role_policy_alignment != expected_live_role_policy_alignment:
        raise ReconciliationError("live-role-policy-alignment-not-reviewed")
    if operation_authorization_contract != "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/reconciliation-operation-authorization-contract.yml":
        raise ReconciliationError("operation-authorization-contract-not-reviewed")
    if reconciliation != {
        "status": "source-implemented-live-role-alignment-and-detector-pending",
        "command": "npm run platform:shell:deployment-reconciliation",
        "policy_check": "npm run platform:shell:deployment-reconciliation:policy-check",
        "modes": {
            "continuous": "scheduled-read-only-verification-of-declared-live-controls",
            "pre_foundation_change_set": "required-immediately-before-any-foundation-change-set-execution",
            "pre_foundation_egress_remediation_change_set": "administrator-only-preflight-for-one-reviewed-non-replacement-relational-database-egress-correction",
            "pre_relational_stage6_foundation_change_set": "administrator-only-preflight-for-isolated-relational-queue-and-task-composition",
            "pre_relational_stage6_service_change_set": "administrator-only-preflight-for-isolated-relational-task-definitions-and-normal-immutable-image-revisions",
            "pre_relational_stage6_bootstrap_recovery_service_change_set": "administrator-only-preflight-for-corrected-image-existing-relational-task-definition-revisions-only",
            "pre_candidate_execution_preflight_onboarding_change_set": "administrator-only-preflight-for-one-dormant-candidate-task-definition-addition-without-service-routing-change",
            "pre_candidate_execution_preflight_image_change_set": "administrator-only-preflight-for-one-dormant-candidate-task-definition-immutable-image-revision-without-service-routing-change",
            "role_policy_alignment": "admin-only-source-to-live-inline-policy-comparison",
        },
        "workflow": ".github/workflows/reconcile-platform-shell-staging.yml",
        "schedule_cron_utc": "15 */4 * * *",
        "execution_identity": "github-platform-shell-staging-reconciliation",
        "role_arn": f"arn:aws:iam::{account_id}:role/github-platform-shell-staging-reconciliation",
        "role_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-policy.json",
        "trust_policy_source": "infra/04.deploy/03.product/targets/kanbien/staging/iam/github-oidc/github-platform-shell-staging-reconciliation-trust.json",
        "operation_authorization_contract": operation_authorization_contract,
        "output_policy": "safe-check-identifiers-and-verdicts-only-no-provider-response-secret-endpoint-or-resource-content",
        "fail_closed": True,
        "drift_evidence": expected_drift_evidence,
        "live_role_policy_alignment": expected_live_role_policy_alignment,
        "foundation_change_set_scope": reconciliation.get("foundation_change_set_scope"),
        "foundation_egress_remediation_scope": reconciliation.get("foundation_egress_remediation_scope"),
        "foundation_relational_stage6_change_set_scope": reconciliation.get("foundation_relational_stage6_change_set_scope"),
        "service_relational_stage6_change_set_scope": reconciliation.get("service_relational_stage6_change_set_scope"),
        "service_relational_stage6_bootstrap_recovery_image_change_set_scope": reconciliation.get("service_relational_stage6_bootstrap_recovery_image_change_set_scope"),
        "candidate_execution_preflight_onboarding_change_set_scope": reconciliation.get("candidate_execution_preflight_onboarding_change_set_scope"),
        "candidate_execution_preflight_image_change_set_scope": reconciliation.get("candidate_execution_preflight_image_change_set_scope"),
    }:
        raise ReconciliationError("reconciliation-policy-not-reviewed")
    if budget.get("name") != "kanbien-staging-platform-shell-monthly" or budget.get("amount_usd") != 25 or budget.get("period") != "monthly":
        raise ReconciliationError("budget-policy-not-reviewed")
    if allocation != {
        "resource_tag_key": "service",
        "resource_tag_value": "platform-shell",
        "billing_report_dimension": "user:service",
        "activation_status": allocation.get("activation_status"),
        "live_configuration_proof": allocation.get("live_configuration_proof"),
        "budget_proof_requirement": allocation.get("budget_proof_requirement"),
    }:
        raise ReconciliationError("budget-allocation-policy-not-reviewed")
    scope = mapping(reconciliation.get("foundation_change_set_scope"), "change-set-scope-missing")
    additions = scope.get("additions")
    modifications = scope.get("modifications")
    if not isinstance(additions, list) or not isinstance(modifications, list) or len(additions) != 22 or len(modifications) != 1:
        raise ReconciliationError("change-set-scope-invalid")
    expected_additions = {
        ("RelationalBootstrapTaskRole", "AWS::IAM::Role"),
        ("RelationalDatabaseConnectionsHighAlarm", "AWS::CloudWatch::Alarm"),
        ("RelationalDatabaseCpuHighAlarm", "AWS::CloudWatch::Alarm"),
        ("RelationalDatabaseEgressFromRelay", "AWS::EC2::SecurityGroupEgress"),
        ("RelationalDatabaseEgressFromServer", "AWS::EC2::SecurityGroupEgress"),
        ("RelationalDatabaseEgressFromWorker", "AWS::EC2::SecurityGroupEgress"),
        ("RelationalDatabaseEventSubscription", "AWS::RDS::EventSubscription"),
        ("RelationalDatabaseFreeStorageLowAlarm", "AWS::CloudWatch::Alarm"),
        ("RelationalDatabaseIngressFromRelay", "AWS::EC2::SecurityGroupIngress"),
        ("RelationalDatabaseIngressFromServer", "AWS::EC2::SecurityGroupIngress"),
        ("RelationalDatabaseIngressFromWorker", "AWS::EC2::SecurityGroupIngress"),
        ("RelationalDatabaseParameterGroup", "AWS::RDS::DBParameterGroup"),
        ("RelationalDatabaseSecurityGroup", "AWS::EC2::SecurityGroup"),
        ("RelationalDatabaseSubnetGroup", "AWS::RDS::DBSubnetGroup"),
        ("RelationalDatabase", "AWS::RDS::DBInstance"),
        ("RelationalMigrationSecretAttachment", "AWS::SecretsManager::SecretTargetAttachment"),
        ("RelationalMigrationSecret", "AWS::SecretsManager::Secret"),
        ("RelationalMigrationTaskRole", "AWS::IAM::Role"),
        ("RelationalRuntimeSecretAttachment", "AWS::SecretsManager::SecretTargetAttachment"),
        ("RelationalRuntimeSecret", "AWS::SecretsManager::Secret"),
        ("RelationalRuntimeTaskRole", "AWS::IAM::Role"),
        ("RelationalTargetConfiguration", "AWS::SSM::Parameter"),
    }
    declared_additions = {(item.get("logical_id"), item.get("resource_type")) for item in additions if isinstance(item, dict)}
    declared_modifications = {(item.get("logical_id"), item.get("resource_type"), item.get("replacement")) for item in modifications if isinstance(item, dict)}
    if declared_additions != expected_additions or declared_modifications != {("AlarmTopicPolicy", "AWS::SNS::TopicPolicy", False)}:
        raise ReconciliationError("change-set-scope-not-reviewed")
    remediation_scope = mapping(reconciliation.get("foundation_egress_remediation_scope"), "egress-remediation-scope-missing")
    expected_remediation_evidence = {
        "schema": "deploy/platform-shell-foundation-known-drift-evidence/v1",
        "maximum_age_seconds": 900,
        "classification": "known-remediation-required",
        "known_change_sets": [
            [{"logical_resource_id": "RelationalDatabaseParameterGroup", "resource_type": "AWS::RDS::DBParameterGroup", "change_categories": ["remove"]}],
            [
                {"logical_resource_id": "RelationalDatabaseParameterGroup", "resource_type": "AWS::RDS::DBParameterGroup", "change_categories": ["remove"]},
                {"logical_resource_id": "RelationalDatabaseSecurityGroup", "resource_type": "AWS::EC2::SecurityGroup", "change_categories": ["add", "not_equal"]},
            ],
        ],
        "tls_enforcement": "required",
    }
    if remediation_scope.get("evidence") != expected_remediation_evidence or remediation_scope.get("modifications") != [
        {"logical_id": "RelationalDatabaseSecurityGroup", "resource_type": "AWS::EC2::SecurityGroup", "replacement": False},
    ]:
        raise ReconciliationError("egress-remediation-scope-not-reviewed")
    stage_six_scope = mapping(reconciliation.get("foundation_relational_stage6_change_set_scope"), "relational-stage6-scope-missing")
    expected_stage_six_evidence = {
        "schema": "deploy/platform-shell-foundation-known-drift-evidence/v1",
        "maximum_age_seconds": 900,
        "classification": "known-remediation-required",
        "known_change_sets": [[{"logical_resource_id": "RelationalDatabaseParameterGroup", "resource_type": "AWS::RDS::DBParameterGroup", "change_categories": ["remove"]}]],
        "tls_enforcement": "required",
    }
    expected_stage_six_additions = {
        ("RelationalTaskExecutionRole", "AWS::IAM::Role"),
        ("RelationalRelayTaskRole", "AWS::IAM::Role"),
        ("RelationalWorkerTaskRole", "AWS::IAM::Role"),
        ("RelationalRestoreVerificationTaskRole", "AWS::IAM::Role"),
        ("RelationalSmokeQueue", "AWS::SQS::Queue"),
        ("RelationalSmokeDeadLetterQueue", "AWS::SQS::Queue"),
        ("RelationalSmokeQueueTransportPolicy", "AWS::SQS::QueuePolicy"),
        ("RelationalSmokeDeadLetterQueueTransportPolicy", "AWS::SQS::QueuePolicy"),
    }
    stage_six_additions = {(item.get("logical_id"), item.get("resource_type")) for item in stage_six_scope.get("additions", []) if isinstance(item, dict)}
    if stage_six_scope.get("evidence") != expected_stage_six_evidence or stage_six_additions != expected_stage_six_additions or stage_six_scope.get("modifications") != [{"logical_id": "ServiceDeploymentExecutionRole", "resource_type": "AWS::IAM::Role", "replacement": False}]:
        raise ReconciliationError("relational-stage6-scope-not-reviewed")
    service_stage_six_scope = mapping(reconciliation.get("service_relational_stage6_change_set_scope"), "relational-stage6-service-scope-missing")
    expected_service_stage_six_foundation_evidence = expected_stage_six_evidence
    expected_service_stage_six_service_evidence = {
        "schema": "deploy/platform-shell-service-active-drift-evidence/v1",
        "maximum_age_seconds": 900,
        "classification": "in-sync",
    }
    expected_candidate_preflight_baseline_evidence = {
        "schema": "deploy/platform-shell-candidate-preflight-baseline-evidence/v1",
        "maximum_age_seconds": 900,
        "classification": "in-sync-steady",
    }
    expected_service_stage_six_additions = {
        ("RelationalBootstrapTaskDefinition", "AWS::ECS::TaskDefinition"),
        ("RelationalMigrationTaskDefinition", "AWS::ECS::TaskDefinition"),
        ("RelationalRelayTaskDefinition", "AWS::ECS::TaskDefinition"),
        ("RelationalWorkerTaskDefinition", "AWS::ECS::TaskDefinition"),
        ("RelationalRestoreVerificationTaskDefinition", "AWS::ECS::TaskDefinition"),
    }
    expected_service_stage_six_modifications = {
        ("TaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("WorkerTaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("RelayTaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("Service", "AWS::ECS::Service", False),
        ("WorkerService", "AWS::ECS::Service", False),
    }
    actual_service_stage_six_additions = {(item.get("logical_id"), item.get("resource_type")) for item in service_stage_six_scope.get("additions", []) if isinstance(item, dict)}
    actual_service_stage_six_modifications = {(item.get("logical_id"), item.get("resource_type"), item.get("replacement")) for item in service_stage_six_scope.get("modifications", []) if isinstance(item, dict)}
    if service_stage_six_scope.get("foundation_evidence") != expected_service_stage_six_foundation_evidence or service_stage_six_scope.get("service_evidence") != expected_service_stage_six_service_evidence or actual_service_stage_six_additions != expected_service_stage_six_additions or actual_service_stage_six_modifications != expected_service_stage_six_modifications:
        raise ReconciliationError("relational-stage6-service-scope-not-reviewed")
    bootstrap_recovery_scope = mapping(reconciliation.get("service_relational_stage6_bootstrap_recovery_image_change_set_scope"), "relational-stage6-bootstrap-recovery-service-scope-missing")
    expected_bootstrap_recovery_modifications = {
        ("TaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("WorkerTaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("RelayTaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("RelationalBootstrapTaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("RelationalMigrationTaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("RelationalRelayTaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("RelationalWorkerTaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("RelationalRestoreVerificationTaskDefinition", "AWS::ECS::TaskDefinition", True),
        ("Service", "AWS::ECS::Service", False),
        ("WorkerService", "AWS::ECS::Service", False),
    }
    actual_bootstrap_recovery_additions = {(item.get("logical_id"), item.get("resource_type")) for item in bootstrap_recovery_scope.get("additions", []) if isinstance(item, dict)}
    actual_bootstrap_recovery_modifications = {(item.get("logical_id"), item.get("resource_type"), item.get("replacement")) for item in bootstrap_recovery_scope.get("modifications", []) if isinstance(item, dict)}
    if bootstrap_recovery_scope.get("foundation_evidence") != expected_service_stage_six_foundation_evidence or bootstrap_recovery_scope.get("service_evidence") != expected_service_stage_six_service_evidence or actual_bootstrap_recovery_additions or actual_bootstrap_recovery_modifications != expected_bootstrap_recovery_modifications:
        raise ReconciliationError("relational-stage6-bootstrap-recovery-service-scope-not-reviewed")
    candidate_onboarding_scope = mapping(reconciliation.get("candidate_execution_preflight_onboarding_change_set_scope"), "candidate-preflight-onboarding-scope-missing")
    candidate_image_scope = mapping(reconciliation.get("candidate_execution_preflight_image_change_set_scope"), "candidate-preflight-image-scope-missing")
    expected_candidate_onboarding_additions = {("CandidatePreflightTaskDefinition", "AWS::ECS::TaskDefinition")}
    expected_candidate_image_modifications = {("CandidatePreflightTaskDefinition", "AWS::ECS::TaskDefinition", True)}
    actual_candidate_onboarding_additions = {(item.get("logical_id"), item.get("resource_type")) for item in candidate_onboarding_scope.get("additions", []) if isinstance(item, dict)}
    actual_candidate_onboarding_modifications = {(item.get("logical_id"), item.get("resource_type"), item.get("replacement")) for item in candidate_onboarding_scope.get("modifications", []) if isinstance(item, dict)}
    actual_candidate_image_additions = {(item.get("logical_id"), item.get("resource_type")) for item in candidate_image_scope.get("additions", []) if isinstance(item, dict)}
    actual_candidate_image_modifications = {(item.get("logical_id"), item.get("resource_type"), item.get("replacement")) for item in candidate_image_scope.get("modifications", []) if isinstance(item, dict)}
    if candidate_onboarding_scope.get("service_evidence") != expected_candidate_preflight_baseline_evidence or actual_candidate_onboarding_additions != expected_candidate_onboarding_additions or actual_candidate_onboarding_modifications:
        raise ReconciliationError("candidate-preflight-onboarding-scope-not-reviewed")
    if candidate_image_scope.get("service_evidence") != expected_candidate_preflight_baseline_evidence or actual_candidate_image_additions or actual_candidate_image_modifications != expected_candidate_image_modifications:
        raise ReconciliationError("candidate-preflight-image-scope-not-reviewed")
    return {
        "account_id": account_id,
        "region": region,
        "aws_profile": aws_profile,
        "artifact_stack": artifact_stack,
        "artifact_bucket": artifact_bucket,
        "foundation_stack": foundation_stack,
        "service_stack": service_stack,
        "maximum_drift_evidence_age_seconds": expected_drift_evidence["maximum_evidence_age_seconds"],
        "maximum_remediation_evidence_age_seconds": expected_remediation_evidence["maximum_age_seconds"],
        "reconciliation_role_name": expected_live_role_policy_alignment["role_name"],
        "reconciliation_inline_policy_name": expected_live_role_policy_alignment["inline_policy_name"],
        "reconciliation_policy_source": expected_live_role_policy_alignment["desired_policy_source"],
        "budget_name": budget["name"],
        "budget_arn": f"arn:aws:budgets::{account_id}:budget/{budget['name']}",
        "expected_changes": {
            *( ("Add", logical_id, resource_type, None) for logical_id, resource_type in expected_additions ),
            ("Modify", "AlarmTopicPolicy", "AWS::SNS::TopicPolicy", False),
        },
        "expected_remediation_changes": {("Modify", "RelationalDatabaseSecurityGroup", "AWS::EC2::SecurityGroup", False)},
        "expected_relational_stage6_changes": {
            *(("Add", logical_id, resource_type, None) for logical_id, resource_type in expected_stage_six_additions),
            ("Modify", "ServiceDeploymentExecutionRole", "AWS::IAM::Role", False),
        },
        "expected_relational_stage6_service_changes": {
            *(("Add", logical_id, resource_type, None) for logical_id, resource_type in expected_service_stage_six_additions),
            *(("Modify", logical_id, resource_type, replacement) for logical_id, resource_type, replacement in expected_service_stage_six_modifications),
        },
        "expected_relational_stage6_bootstrap_recovery_service_changes": {
            *(("Modify", logical_id, resource_type, replacement) for logical_id, resource_type, replacement in expected_bootstrap_recovery_modifications),
        },
        "expected_candidate_execution_preflight_onboarding_changes": {
            *(("Add", logical_id, resource_type, None) for logical_id, resource_type in expected_candidate_onboarding_additions),
        },
        "expected_candidate_execution_preflight_image_changes": {
            *(("Modify", logical_id, resource_type, replacement) for logical_id, resource_type, replacement in expected_candidate_image_modifications),
        },
        "maximum_stage_six_evidence_age_seconds": expected_stage_six_evidence["maximum_age_seconds"],
        "maximum_service_stage_six_evidence_age_seconds": expected_service_stage_six_service_evidence["maximum_age_seconds"],
    }


def run_aws(
    arguments: argparse.Namespace,
    policy: dict[str, Any],
    command: list[str],
    failure_code: str = "aws-verification-unavailable",
) -> Any:
    """Run one fixed AWS operation with small bounded retries and no error-payload output."""

    invocation = [arguments.aws_cli, *command, "--region", policy["region"], "--output", "json"]
    if arguments.aws_credential_source == "target-profile":
        invocation.extend(["--profile", policy["aws_profile"]])
    for attempt in range(AWS_MAX_ATTEMPTS):
        try:
            completed = subprocess.run(invocation, check=True, capture_output=True, text=True, timeout=arguments.timeout_seconds)
            return json.loads(completed.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exception:
            if attempt == AWS_MAX_ATTEMPTS - 1:
                raise ReconciliationError(failure_code) from exception
            time.sleep(AWS_RETRY_BACKOFF_SECONDS[attempt])
    raise AssertionError("bounded AWS verification retry loop did not return")


def require(condition: bool, code: str) -> None:
    """Fail closed with a stable safe result code."""

    if not condition:
        raise ReconciliationError(code)


def run_check(check_id: str, check: Callable[[], None]) -> None:
    """Preserve a safe owning-control identifier when a provider call is unavailable."""

    try:
        check()
    except ReconciliationError as exception:
        if str(exception) == "aws-verification-unavailable":
            raise ReconciliationError(f"{check_id}-verification-unavailable") from exception
        raise


def bootstrap_effects_receipt_path() -> Path:
    """Locate the shared durable Stage 6 receipt without accepting a caller path."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            check=True,
            cwd=REPOSITORY_ROOT,
            text=True,
            timeout=5,
        )
        common = Path(result.stdout.strip())
    except (OSError, subprocess.SubprocessError) as exception:
        raise ReconciliationError("bootstrap-effect-reconciliation-receipt-unavailable") from exception
    if not common.is_absolute() or common.name != ".git":
        raise ReconciliationError("bootstrap-effect-reconciliation-receipt-unavailable")
    return common / "postgresql-stage6-receipts" / "stage-attempts.json"


def check_bootstrap_effects_reconciliation_receipt(receipt_path: Path | None = None) -> None:
    """Require the one successful pre-promotion no-write reconciliation receipt."""

    path = bootstrap_effects_receipt_path() if receipt_path is None else receipt_path
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exception:
        raise ReconciliationError("bootstrap-effect-reconciliation-receipt-unavailable") from exception
    stages = ledger.get("stages") if isinstance(ledger, dict) else None
    receipt = stages.get(BOOTSTRAP_EFFECTS_ASSESSMENT_STAGE) if isinstance(stages, dict) else None
    if not isinstance(receipt, dict) or receipt.get("state") != "succeeded" or receipt.get("assessment_state") not in {"pristine", "fully-ready", "recoverable-interrupted-schema-setup"}:
        raise ReconciliationError("bootstrap-effect-reconciliation-receipt-missing")
    facts = receipt.get("facts")
    fact_receipts = receipt.get("fact_receipts")
    if not isinstance(facts, dict) or not isinstance(fact_receipts, list) or len(fact_receipts) != 2:
        raise ReconciliationError("bootstrap-effect-reconciliation-receipt-missing")
    observed = {item.get("stage"): item.get("label") for item in fact_receipts if isinstance(item, dict)}
    if observed != BOOTSTRAP_EFFECTS_FACT_LABELS:
        raise ReconciliationError("bootstrap-effect-reconciliation-receipt-missing")
    images = set()
    for item in fact_receipts:
        if not isinstance(item, dict) or not isinstance(item.get("task_definition_revision"), int) or item["task_definition_revision"] < 1 or not isinstance(item.get("image"), str) or "@sha256:" not in item["image"] or not isinstance(item.get("diagnostic_code_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", item["diagnostic_code_sha256"]):
            raise ReconciliationError("bootstrap-effect-reconciliation-receipt-missing")
        images.add(item["image"])
    if len(images) != 1:
        raise ReconciliationError("bootstrap-effect-reconciliation-receipt-missing")
    if receipt.get("assessment_state") == "recoverable-interrupted-schema-setup" and facts != RECOVERABLE_INTERRUPTED_SCHEMA_SETUP:
        raise ReconciliationError("bootstrap-effect-reconciliation-receipt-missing")


def check_identity(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Verify that credentials are for the one declared AWS account."""

    payload = run_aws(arguments, policy, ["sts", "get-caller-identity"])
    require(payload.get("Account") == policy["account_id"], "aws-account-mismatch")


def check_stack_status(arguments: argparse.Namespace, policy: dict[str, Any], stack: str, expected_status: str, check_id: str) -> None:
    """Require a stable stack state before relying on a target control."""

    payload = run_aws(arguments, policy, ["cloudformation", "describe-stacks", "--stack-name", stack, "--query", "Stacks[0].StackStatus"])
    require(payload == expected_status, check_id)


def check_stack_drift_evidence(arguments: argparse.Namespace, policy: dict[str, Any], stack: str, check_id: str) -> None:
    """Require fresh passive IN_SYNC evidence without giving GitHub an active detector permission."""

    payload = run_aws(
        arguments,
        policy,
        ["cloudformation", "describe-stacks", "--stack-name", stack, "--query", "Stacks[0].DriftInformation.{status:StackDriftStatus,checked:LastCheckTimestamp}"],
        f"{check_id}-summary-unavailable",
    )
    if not isinstance(payload, dict):
        raise ReconciliationError(check_id)
    if payload.get("status") != "IN_SYNC":
        raise ReconciliationError(check_id)
    try:
        checked_at = datetime.fromisoformat(str(payload.get("checked")).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exception:
        raise ReconciliationError(f"{check_id}-evidence-missing") from exception
    age_seconds = (datetime.now(timezone.utc) - checked_at).total_seconds()
    if age_seconds < 0 or age_seconds > policy["maximum_drift_evidence_age_seconds"]:
        raise ReconciliationError(f"{check_id}-evidence-stale")


def check_known_remediation_evidence(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Accept only a just-created, safe record from the dedicated fixed-stack classifier."""

    path = Path(arguments.known_foundation_drift_evidence)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exception:
        raise ReconciliationError("known-foundation-drift-evidence-unreadable") from exception
    # The active classifier emits a bounded list because CloudFormation can
    # report both the accepted parameter-group normalisation and the reviewed
    # security-group correction during the same assessment.  Do not retain an
    # obsolete singular shape check here: it would reject the only safe
    # evidence the classifier is permitted to produce.
    if not isinstance(document, dict) or not isinstance(document.get("known_changes"), list):
        raise ReconciliationError("known-foundation-drift-evidence-not-reviewed")
    expected = {
        "schema": "deploy/platform-shell-foundation-known-drift-evidence/v1",
        "target": "kanbien/staging",
        "account_id": policy["account_id"],
        "region": policy["region"],
        "foundation_stack": policy["foundation_stack"],
        "classification": "known-remediation-required",
        "tls_enforcement": "required",
    }
    allowed_changes = [
        [{"logical_resource_id": "RelationalDatabaseParameterGroup", "resource_type": "AWS::RDS::DBParameterGroup", "change_category": "remove"}],
        [
            {"logical_resource_id": "RelationalDatabaseParameterGroup", "resource_type": "AWS::RDS::DBParameterGroup", "change_category": "remove"},
            {"logical_resource_id": "RelationalDatabaseSecurityGroup", "resource_type": "AWS::EC2::SecurityGroup", "change_category": "add"},
        ],
        [
            {"logical_resource_id": "RelationalDatabaseParameterGroup", "resource_type": "AWS::RDS::DBParameterGroup", "change_category": "remove"},
            {"logical_resource_id": "RelationalDatabaseSecurityGroup", "resource_type": "AWS::EC2::SecurityGroup", "change_category": "not_equal"},
        ],
    ]
    if arguments.mode in {"pre-relational-stage6-foundation-change-set", "pre-relational-stage6-service-change-set", "pre-relational-stage6-bootstrap-recovery-service-change-set"}:
        allowed_changes = [allowed_changes[0]]
    if any(document.get(key) != value for key, value in expected.items()) or document.get("known_changes") not in allowed_changes:
        raise ReconciliationError("known-foundation-drift-evidence-not-reviewed")
    try:
        issued_at = datetime.fromisoformat(str(document.get("issued_at_utc")).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exception:
        raise ReconciliationError("known-foundation-drift-evidence-timestamp-invalid") from exception
    age_seconds = (datetime.now(timezone.utc) - issued_at).total_seconds()
    maximum_age = policy["maximum_stage_six_evidence_age_seconds"] if arguments.mode in {"pre-relational-stage6-foundation-change-set", "pre-relational-stage6-service-change-set", "pre-relational-stage6-bootstrap-recovery-service-change-set"} else policy["maximum_remediation_evidence_age_seconds"]
    if age_seconds < 0 or age_seconds > maximum_age:
        raise ReconciliationError("known-foundation-drift-evidence-stale")


def check_service_drift_evidence(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Accept only the new, fixed-stack, in-sync Service assessment record."""

    path = Path(arguments.service_drift_evidence)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exception:
        raise ReconciliationError("service-drift-evidence-unreadable") from exception
    expected = {
        "schema": "deploy/platform-shell-service-active-drift-evidence/v1",
        "target": "kanbien/staging",
        "account_id": policy["account_id"],
        "region": policy["region"],
        "service_stack": policy["service_stack"],
        "classification": "in-sync",
    }
    if not isinstance(document, dict) or any(document.get(key) != value for key, value in expected.items()):
        raise ReconciliationError("service-drift-evidence-not-reviewed")
    try:
        issued_at = datetime.fromisoformat(str(document.get("issued_at_utc")).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exception:
        raise ReconciliationError("service-drift-evidence-timestamp-invalid") from exception
    age_seconds = (datetime.now(timezone.utc) - issued_at).total_seconds()
    if age_seconds < 0 or age_seconds > policy["maximum_service_stage_six_evidence_age_seconds"]:
        raise ReconciliationError("service-drift-evidence-stale")


def check_candidate_preflight_baseline_evidence(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Accept only a new, read-only proof of a stable onboarding baseline."""

    path = Path(arguments.service_drift_evidence)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exception:
        raise ReconciliationError("candidate-preflight-baseline-evidence-unreadable") from exception
    expected = {
        "schema": "deploy/platform-shell-candidate-preflight-baseline-evidence/v1",
        "target": "kanbien/staging",
        "account_id": policy["account_id"],
        "region": policy["region"],
        "service_stack": policy["service_stack"],
        "classification": "in-sync-steady",
        "source_service": "kanbien-staging-platform-shell",
        "source_service_steady": True,
    }
    if not isinstance(document, dict) or any(document.get(key) != value for key, value in expected.items()):
        raise ReconciliationError("candidate-preflight-baseline-evidence-not-reviewed")
    if document.get("service_stack_status") not in {"UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"}:
        raise ReconciliationError("candidate-preflight-baseline-stack-status-not-reviewed")
    try:
        issued_at = datetime.fromisoformat(str(document.get("issued_at_utc")).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exception:
        raise ReconciliationError("candidate-preflight-baseline-evidence-timestamp-invalid") from exception
    age_seconds = (datetime.now(timezone.utc) - issued_at).total_seconds()
    if age_seconds < 0 or age_seconds > policy["maximum_service_stage_six_evidence_age_seconds"]:
        raise ReconciliationError("candidate-preflight-baseline-evidence-stale")


def check_reconciliation_live_role_policy(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Require the administrator pre-change identity to prove the role matches reviewed source."""

    source_path = REPOSITORY_ROOT / policy["reconciliation_policy_source"]
    try:
        with source_path.open(encoding="utf-8") as handle:
            desired_policy = json.load(handle)
    except (OSError, json.JSONDecodeError) as exception:
        raise ReconciliationError("reconciliation-role-policy-source-unreadable") from exception
    live_policy = run_aws(
        arguments,
        policy,
        [
            "iam",
            "get-role-policy",
            "--role-name",
            policy["reconciliation_role_name"],
            "--policy-name",
            policy["reconciliation_inline_policy_name"],
            "--query",
            "PolicyDocument",
        ],
        "reconciliation-live-role-policy-unavailable",
    )
    require(live_policy == desired_policy, "reconciliation-live-role-policy")


def artifact_bucket_checks(arguments: argparse.Namespace, policy: dict[str, Any]) -> list[tuple[str, Callable[[], None]]]:
    """Return each private artifact-store control as one independently attributable check."""

    bucket = policy["artifact_bucket"]
    return [
        (
            "artifact-bucket-public-access-control",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-public-access-block", "--bucket", bucket, "--query", "PublicAccessBlockConfiguration"])
                == {"BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True},
                "artifact-bucket-public-access-control",
            ),
        ),
        (
            "artifact-bucket-encryption",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-bucket-encryption", "--bucket", bucket, "--query", "ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm"])
                == "AES256",
                "artifact-bucket-encryption",
            ),
        ),
        (
            "artifact-bucket-ownership",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-bucket-ownership-controls", "--bucket", bucket, "--query", "OwnershipControls.Rules[0].ObjectOwnership"])
                == "BucketOwnerEnforced",
                "artifact-bucket-ownership",
            ),
        ),
        (
            "artifact-bucket-lifecycle",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-bucket-lifecycle-configuration", "--bucket", bucket, "--query", "Rules"])
                == [{"ID": "expire-reviewed-change-set-templates", "Status": "Enabled", "Filter": {"Prefix": "change-sets/"}, "Expiration": {"Days": 30}, "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 1}}],
                "artifact-bucket-lifecycle",
            ),
        ),
        (
            "artifact-bucket-policy-status",
            lambda: require(
                run_aws(arguments, policy, ["s3api", "get-bucket-policy-status", "--bucket", bucket, "--query", "PolicyStatus.IsPublic"])
                is False,
                "artifact-bucket-policy-status",
            ),
        ),
    ]


def check_budget(arguments: argparse.Namespace, policy: dict[str, Any]) -> None:
    """Require the one declared 25 USD monthly service-tag-scoped budget."""

    payload = run_aws(arguments, policy, ["budgets", "describe-budget", "--account-id", policy["account_id"], "--budget-name", policy["budget_name"], "--query", "Budget.{name:BudgetName,limit:BudgetLimit,period:TimeUnit,type:BudgetType,filters:CostFilters}"])
    try:
        amount = Decimal(str(payload.get("limit", {}).get("Amount")))
    except (AttributeError, InvalidOperation):
        raise ReconciliationError("platform-shell-budget")
    require(
        payload.get("name") == policy["budget_name"]
        and amount == Decimal("25")
        and payload.get("limit", {}).get("Unit") == "USD"
        and payload.get("period") == "MONTHLY"
        and payload.get("type") == "COST"
        and payload.get("filters") == {"TagKeyValue": ["user:service$platform-shell"]},
        "platform-shell-budget",
    )


def normalized_replacement(value: Any) -> Any:
    """Convert CloudFormation's boolean-like replacement fields to source booleans."""

    return {"True": True, "False": False}.get(value, value)


def check_change_set(arguments: argparse.Namespace, policy: dict[str, Any], stack: str, change_set: str, expected_changes: set[tuple[Any, ...]], check_id: str) -> None:
    """Require exactly the already-reviewed target stack change-set scope before execution."""

    payload = run_aws(arguments, policy, ["cloudformation", "describe-change-set", "--stack-name", stack, "--change-set-name", change_set, "--query", "{status:Status,execution:ExecutionStatus,changes:Changes[].ResourceChange.{action:Action,logicalId:LogicalResourceId,resourceType:ResourceType,replacement:Replacement}}"])
    require(payload.get("status") == "CREATE_COMPLETE" and payload.get("execution") == "AVAILABLE", f"{check_id}-state")
    changes = payload.get("changes")
    require(isinstance(changes, list), check_id)
    actual_changes = set()
    for change in changes:
        if not isinstance(change, dict):
            raise ReconciliationError(check_id)
        replacement = normalized_replacement(change.get("replacement"))
        actual_changes.add((change.get("action"), change.get("logicalId"), change.get("resourceType"), replacement))
    require(actual_changes == expected_changes and len(changes) == len(expected_changes), check_id)


def result(mode: str, checks: list[dict[str, str]], verdict: str) -> dict[str, Any]:
    """Build the sole safe output envelope for local and CI execution."""

    return {"schema": SAFE_SCHEMA, "target": "kanbien/staging", "mode": mode, "verdict": verdict, "checks": checks}


def main() -> int:
    """Validate source, then run each declared non-secret control check in order."""

    arguments = parse_arguments()
    checks: list[dict[str, str]] = []
    try:
        policy = resolve_policy(load_yaml(Path(arguments.target_profile)))
        checks.append({"id": "source-policy", "verdict": "passed"})
        if not arguments.validate and arguments.mode == "role-policy-alignment":
            run_check(
                "reconciliation-live-role-policy",
                lambda: check_reconciliation_live_role_policy(arguments, policy),
            )
            checks.append({"id": "reconciliation-live-role-policy", "verdict": "passed"})
        elif not arguments.validate:
            core_checks = [
                ("aws-account", lambda: check_identity(arguments, policy)),
                ("artifact-stack-status", lambda: check_stack_status(arguments, policy, policy["artifact_stack"], "CREATE_COMPLETE", "artifact-stack-status")),
                ("artifact-stack-drift-evidence", lambda: check_stack_drift_evidence(arguments, policy, policy["artifact_stack"], "artifact-stack-drift")),
                ("foundation-stack-status", lambda: check_stack_status(arguments, policy, policy["foundation_stack"], "UPDATE_COMPLETE", "foundation-stack-status")),
                *artifact_bucket_checks(arguments, policy),
                ("platform-shell-budget", lambda: check_budget(arguments, policy)),
            ]
            if arguments.mode in {"pre-relational-stage6-service-change-set", "pre-relational-stage6-bootstrap-recovery-service-change-set"}:
                core_checks = [
                    ("aws-account", lambda: check_identity(arguments, policy)),
                    ("artifact-stack-status", lambda: check_stack_status(arguments, policy, policy["artifact_stack"], "CREATE_COMPLETE", "artifact-stack-status")),
                    ("foundation-stack-status", lambda: check_stack_status(arguments, policy, policy["foundation_stack"], "UPDATE_COMPLETE", "foundation-stack-status")),
                    ("known-foundation-drift-evidence", lambda: check_known_remediation_evidence(arguments, policy)),
                    ("service-stack-status", lambda: check_stack_status(arguments, policy, policy["service_stack"], "UPDATE_COMPLETE", "service-stack-status")),
                    ("service-active-drift-evidence", lambda: check_service_drift_evidence(arguments, policy)),
                    *artifact_bucket_checks(arguments, policy),
                    ("platform-shell-budget", lambda: check_budget(arguments, policy)),
                ]
                if arguments.mode == "pre-relational-stage6-bootstrap-recovery-service-change-set":
                    core_checks.insert(6, ("bootstrap-effect-reconciliation-receipt", check_bootstrap_effects_reconciliation_receipt))
            elif arguments.mode in {"pre-candidate-execution-preflight-onboarding-change-set", "pre-candidate-execution-preflight-image-change-set"}:
                core_checks = [
                    ("aws-account", lambda: check_identity(arguments, policy)),
                    ("artifact-stack-status", lambda: check_stack_status(arguments, policy, policy["artifact_stack"], "CREATE_COMPLETE", "artifact-stack-status")),
                    ("foundation-stack-status", lambda: check_stack_status(arguments, policy, policy["foundation_stack"], "UPDATE_COMPLETE", "foundation-stack-status")),
                    ("candidate-preflight-baseline-evidence", lambda: check_candidate_preflight_baseline_evidence(arguments, policy)),
                    *artifact_bucket_checks(arguments, policy),
                    ("platform-shell-budget", lambda: check_budget(arguments, policy)),
                ]
            if arguments.mode in {"pre-foundation-egress-remediation-change-set", "pre-relational-stage6-foundation-change-set"}:
                core_checks.insert(4, ("known-foundation-drift-evidence", lambda: check_known_remediation_evidence(arguments, policy)))
            elif arguments.mode not in {"pre-relational-stage6-service-change-set", "pre-relational-stage6-bootstrap-recovery-service-change-set", "pre-candidate-execution-preflight-onboarding-change-set", "pre-candidate-execution-preflight-image-change-set"}:
                core_checks.insert(4, ("foundation-stack-drift-evidence", lambda: check_stack_drift_evidence(arguments, policy, policy["foundation_stack"], "foundation-stack-drift")))
            for check_id, check in core_checks:
                run_check(check_id, check)
                checks.append({"id": check_id, "verdict": "passed"})
            if arguments.mode in {"pre-foundation-change-set", "pre-foundation-egress-remediation-change-set", "pre-relational-stage6-foundation-change-set", "pre-relational-stage6-service-change-set", "pre-relational-stage6-bootstrap-recovery-service-change-set", "pre-candidate-execution-preflight-onboarding-change-set", "pre-candidate-execution-preflight-image-change-set"}:
                run_check(
                    "reconciliation-live-role-policy",
                    lambda: check_reconciliation_live_role_policy(arguments, policy),
                )
                checks.append({"id": "reconciliation-live-role-policy", "verdict": "passed"})
                if arguments.mode == "pre-foundation-change-set":
                    run_check(
                        "foundation-change-set-scope",
                        lambda: check_change_set(arguments, policy, policy["foundation_stack"], arguments.foundation_change_set, policy["expected_changes"], "foundation-change-set-scope"),
                    )
                    checks.append({"id": "foundation-change-set-scope", "verdict": "passed"})
                elif arguments.mode == "pre-foundation-egress-remediation-change-set":
                    run_check(
                        "foundation-egress-remediation-change-set-scope",
                        lambda: check_change_set(arguments, policy, policy["foundation_stack"], arguments.foundation_change_set, policy["expected_remediation_changes"], "foundation-egress-remediation-change-set-scope"),
                    )
                    checks.append({"id": "foundation-egress-remediation-change-set-scope", "verdict": "passed"})
                elif arguments.mode == "pre-relational-stage6-foundation-change-set":
                    run_check(
                        "relational-stage6-foundation-change-set-scope",
                        lambda: check_change_set(arguments, policy, policy["foundation_stack"], arguments.foundation_change_set, policy["expected_relational_stage6_changes"], "relational-stage6-foundation-change-set-scope"),
                    )
                    checks.append({"id": "relational-stage6-foundation-change-set-scope", "verdict": "passed"})
                elif arguments.mode == "pre-relational-stage6-service-change-set":
                    run_check(
                        "relational-stage6-service-change-set-scope",
                        lambda: check_change_set(arguments, policy, policy["service_stack"], arguments.service_change_set, policy["expected_relational_stage6_service_changes"], "relational-stage6-service-change-set-scope"),
                    )
                    checks.append({"id": "relational-stage6-service-change-set-scope", "verdict": "passed"})
                elif arguments.mode == "pre-candidate-execution-preflight-onboarding-change-set":
                    run_check(
                        "candidate-preflight-onboarding-change-set-scope",
                        lambda: check_change_set(arguments, policy, policy["service_stack"], arguments.service_change_set, policy["expected_candidate_execution_preflight_onboarding_changes"], "candidate-preflight-onboarding-change-set-scope"),
                    )
                    checks.append({"id": "candidate-preflight-onboarding-change-set-scope", "verdict": "passed"})
                elif arguments.mode == "pre-candidate-execution-preflight-image-change-set":
                    run_check(
                        "candidate-preflight-image-change-set-scope",
                        lambda: check_change_set(arguments, policy, policy["service_stack"], arguments.service_change_set, policy["expected_candidate_execution_preflight_image_changes"], "candidate-preflight-image-change-set-scope"),
                    )
                    checks.append({"id": "candidate-preflight-image-change-set-scope", "verdict": "passed"})
                else:
                    run_check(
                        "relational-stage6-bootstrap-recovery-service-change-set-scope",
                        lambda: check_change_set(arguments, policy, policy["service_stack"], arguments.service_change_set, policy["expected_relational_stage6_bootstrap_recovery_service_changes"], "relational-stage6-bootstrap-recovery-service-change-set-scope"),
                    )
                    checks.append({"id": "relational-stage6-bootstrap-recovery-service-change-set-scope", "verdict": "passed"})
        print(json.dumps(result(arguments.mode, checks, "passed"), sort_keys=True))
        return 0
    except ReconciliationError as exception:
        checks.append({"id": str(exception), "verdict": "blocked"})
        print(json.dumps(result(arguments.mode, checks, "blocked"), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
