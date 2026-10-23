#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.core-platform-target-declaration.implementation
#   version: 8
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Implement a fail-closed static check for planned core-platform target declarations.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.command.core-platform-target-declaration
#     path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


TARGET = "kanbien-core-platform"
REQUIRED_E0_FACTS = {
    "provider-account-profile",
    "provider-region",
    "runtime-family",
    "private-network-placement",
    "image-custody-destination",
    "private-verifier-placement",
    "logging-destination",
    "cost-allocation-tag",
    "target-budget",
    "delivery-identity",
    "workload-startup-identity",
    "rollback-custody",
}
REQUIRED_EXCLUSIONS = {
    "public-ingress",
    "persistence",
    "application-identity",
    "product-capabilities",
    "queues-and-workers",
    "provider-adapters",
    "full-observability-delivery",
}
SAFE_RECEIPT_FIELDS = {
    "target",
    "environment_class",
    "provider_region_alias",
    "program_id",
    "image_contract_id",
    "source_revision",
    "image_digest",
    "release_identity",
    "checked_at",
    "health_verdict",
    "verification_verdict",
    "receipt_reference",
}
SAFE_CONFIG_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")


class DeclarationFailure(Exception):
    def __init__(self, *codes: str) -> None:
        self.codes = tuple(dict.fromkeys(codes))
        super().__init__(", ".join(self.codes))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--target-root")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args, unknown = parser.parse_known_args()
    if args.help:
        print("Usage: script.py [--target-root <path>] [--json]")
        raise SystemExit(0)
    if unknown:
        raise DeclarationFailure("arguments-invalid")
    return args


def mapping(path: Path, code: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        raise DeclarationFailure(code) from None
    if not isinstance(value, dict):
        raise DeclarationFailure(code)
    return value


def non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def provider_resource_types(template: Path) -> dict[str, str]:
    try:
        text = template.read_text(encoding="utf-8")
    except OSError:
        raise DeclarationFailure("provider-runtime-template-unreadable") from None
    return {
        match.group("id"): match.group("type")
        for match in re.finditer(
            r"^  (?P<id>[A-Za-z][A-Za-z0-9]+):\n    Type: (?P<type>AWS::[A-Za-z0-9:]+)$",
            text,
            re.MULTILINE,
        )
    }


def required_mapping(document: dict[str, Any], key: str, code: str) -> dict[str, Any]:
    value = document.get(key)
    if not isinstance(value, dict):
        raise DeclarationFailure(code)
    return value


def check_profile(profile: dict[str, Any]) -> None:
    if profile.get("schema") != "deploy/target-profile/v1" or profile.get("id") != TARGET:
        raise DeclarationFailure("target-profile-invalid")
    if profile.get("status") != "healthy-runtime-accepted":
        raise DeclarationFailure("target-status-invalid")
    if profile.get("baseline") != "accepted-immutable-release" or profile.get("repository_declaration") != "repository-declaration-complete":
        raise DeclarationFailure("target-baseline-invalid")
    if profile.get("live_alignment") != "fresh-update-or-restore-alignment-required":
        raise DeclarationFailure("live-alignment-state-invalid")
    provider = required_mapping(profile, "provider", "provider-declaration-missing")
    if provider.get("family") != "aws" or provider.get("selection_status") != "selected-and-live-verified":
        raise DeclarationFailure("provider-selection-invalid")
    mutation = required_mapping(profile, "target_mutation", "target-mutation-missing")
    if mutation.get("status") != "blocked" or mutation.get("allowed_operation") != "update-or-restore":
        raise DeclarationFailure("target-mutation-not-controlled")
    facts = profile.get("e0_required_facts")
    if not isinstance(facts, list):
        raise DeclarationFailure("e0-fact-missing")
    found: set[str] = set()
    allowed_fact_statuses = {"live-verified-fresh-alignment-required", "selected-and-live-verified", "inactive-tag-waiver-renewal-required-before-mutation", "cost-control-waiver-active", "cost-control-verified-fresh-alignment-required", "target-budget-provisioning-required-before-mutation", "accepted-release-retained-and-private-verified"}
    for fact in facts:
        if not isinstance(fact, dict) or not non_empty(fact.get("id")):
            raise DeclarationFailure("e0-fact-invalid")
        fact_id = fact["id"]
        found.add(fact_id)
        if fact.get("status") not in allowed_fact_statuses:
            raise DeclarationFailure("e0-fact-status-invalid")
        if not non_empty(fact.get("owner")):
            raise DeclarationFailure("e0-fact-unowned")
        if not non_empty(fact.get("evidence")):
            raise DeclarationFailure("e0-fact-evidence-missing")
    if found != REQUIRED_E0_FACTS:
        raise DeclarationFailure("e0-fact-missing")


def check_foundation(root: Path) -> None:
    foundation_root = root / "10-foundation"
    index = mapping(foundation_root / "foundation-index.yml", "foundation-index-unreadable")
    if index.get("schema") != "deploy/target-foundation-index/v1" or index.get("target") != TARGET:
        raise DeclarationFailure("foundation-index-invalid")
    resources = index.get("resources")
    if not isinstance(resources, list) or not resources:
        raise DeclarationFailure("foundation-resource-missing")
    for item in resources:
        if not isinstance(item, dict) or not non_empty(item.get("id")) or not non_empty(item.get("declaration")):
            raise DeclarationFailure("foundation-resource-invalid")
        if item.get("status") not in {"live-verified-fresh-alignment-required", "inactive-tag-waiver-renewal-required-before-mutation", "cost-control-waiver-active", "cost-control-verified-fresh-alignment-required", "target-budget-provisioning-required-before-mutation"}:
            raise DeclarationFailure("foundation-resource-status-invalid")
        if not non_empty(item.get("owner")):
            raise DeclarationFailure("foundation-resource-unowned")
    network = mapping(foundation_root / "network.yml", "network-declaration-unreadable")
    route = required_mapping(network, "private_verifier_route", "private-verifier-missing")
    if network.get("public_ingress") != "prohibited" or route.get("status") != "established-e2c-fresh-e4-evidence-required" or route.get("permitted_caller") != "selected-private-verifier-only":
        raise DeclarationFailure("private-verifier-invalid")
    access = mapping(foundation_root / "technical-access.yml", "technical-access-unreadable")
    intents = access.get("access_intents")
    if not isinstance(intents, list) or {item.get("id") for item in intents if isinstance(item, dict)} != {"delivery-custody", "workload-startup"}:
        raise DeclarationFailure("technical-access-invalid")
    for intent in intents:
        if not isinstance(intent, dict) or not isinstance(intent.get("provider_identity"), str) or not intent["provider_identity"].endswith("fresh-e4-evidence-required") or not non_empty(intent.get("owner")):
            raise DeclarationFailure("technical-access-invalid")
    cost = mapping(foundation_root / "cost-control.yml", "cost-control-unreadable")
    expected_controls = {"one-task-only", "no-autoscaling", "no-nat", "no-public-ingress", "no-data-services", "no-new-cost-category"}
    if (
        cost.get("schema") != "deploy/provider-condition-declaration/v1"
        or cost.get("target") != TARGET
        or cost.get("condition_id") != "target-cost-allocation-tag-active"
        or cost.get("status") not in {"not-requested", "requested", "waiting-on-provider", "verified", "expired", "waived-by-approved-exception"}
        or not non_empty(cost.get("owner"))
        or not non_empty(cost.get("required_evidence"))
        or cost.get("evidence_validator") != "scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.sh"
        or cost.get("evidence") != "evidence/target-cost-allocation-tag.yml"
    ):
        raise DeclarationFailure("cost-control-invalid")
    evidence = mapping(foundation_root / cost["evidence"], "cost-control-evidence-unreadable")
    if (
        evidence.get("schema") != "deploy/provider-condition-evidence/v1"
        or evidence.get("condition_id") != "target-cost-allocation-tag-active"
        or evidence.get("target") != TARGET
        or evidence.get("status") != cost.get("status")
        or (cost.get("status") != "waived-by-approved-exception" and ("waiver" in cost or "waiver" in evidence))
    ):
        raise DeclarationFailure("cost-control-evidence-invalid")
    if cost.get("status") == "waived-by-approved-exception":
        waiver = required_mapping(cost, "waiver", "cost-control-invalid")
        evidence_waiver = required_mapping(evidence, "waiver", "cost-control-evidence-invalid")
        if (
            set(waiver.get("compensating_controls", [])) != expected_controls
            or not non_empty(waiver.get("follow_up_owner"))
            or evidence_waiver.get("authority_reference") != waiver.get("current_authority_reference")
            or evidence_waiver.get("expires_at") != waiver.get("current_expiry")
            or set(evidence_waiver.get("compensating_controls", [])) != expected_controls
            or evidence_waiver.get("follow_up_owner") != waiver.get("follow_up_owner")
        ):
            raise DeclarationFailure("cost-control-evidence-invalid")


def check_scope(root: Path) -> None:
    scope_root = root / "20-scopes" / "bootstrap-runtime"
    inventory = Path(__file__).resolve().parents[5] / "scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.py"
    inventory_check = subprocess.run(
        [sys.executable, str(inventory), "--target-root", str(root / "20-scopes"), "--json"],
        capture_output=True, check=False, text=True,
    )
    if inventory_check.returncode != 0:
        raise DeclarationFailure("active-workload-health-recovery-inventory-invalid")
    contract = mapping(scope_root / "00-declaration" / "declaration-contract.yml", "scope-contract-unreadable")
    if contract.get("schema") != "deploy/target-scope-contract/v1" or contract.get("target") != TARGET or contract.get("id") != "kanbien-core-platform-bootstrap-runtime":
        raise DeclarationFailure("scope-contract-invalid")
    if not non_empty(contract.get("owner")):
        raise DeclarationFailure("scope-unowned")
    program = required_mapping(contract, "program", "scope-program-missing")
    if program.get("id") != "kanbien-core-server" or program.get("contract") != "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml" or program.get("image_contract") != "infra/04.deploy/03.product/image/core-server/image-contract.yml":
        raise DeclarationFailure("scope-program-invalid")
    workload = required_mapping(contract, "workload", "scope-workload-missing")
    if workload.get("operation") != "controlled-update-or-restoration" or workload.get("runtime_selection") != "ecs-fargate-private-immutable-digest" or workload.get("startup_access") != "10-foundation/technical-access.yml#workload-startup" or workload.get("network") != "10-foundation/network.yml#private-verifier-route":
        raise DeclarationFailure("scope-workload-invalid")
    configuration = required_mapping(contract, "configuration", "scope-configuration-missing")
    if configuration.get("value_policy") != "names-and-shapes-only-no-values" or configuration.get("secret_names") != []:
        raise DeclarationFailure("scope-configuration-invalid")
    names = configuration.get("required_names", []) + configuration.get("optional_names", [])
    if not names or not all(isinstance(name, str) and SAFE_CONFIG_NAME.fullmatch(name) for name in names):
        raise DeclarationFailure("scope-configuration-invalid")
    verification = required_mapping(contract, "verification", "scope-verification-missing")
    if verification.get("route_exposure") != "private-verifier-only" or verification.get("status") != "accepted-baseline-private-verification-complete-and-required-after-every-mutation" or not non_empty(verification.get("owner")):
        raise DeclarationFailure("scope-verification-invalid")
    binding_path = scope_root / "10-workload-binding" / "workload-binding.yml"
    binding = mapping(binding_path, "workload-binding-unreadable")
    validator = Path(__file__).resolve().parents[5] / "scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.py"
    health_check = subprocess.run(
        [sys.executable, str(validator), "--scope-contract", str(scope_root / "00-declaration" / "declaration-contract.yml"), "--workload-binding", str(binding_path), "--json"],
        capture_output=True,
        check=False,
        text=True,
    )
    if health_check.returncode != 0:
        raise DeclarationFailure("health-recovery-declaration-invalid")
    health_recovery = required_mapping(contract, "health_recovery", "health-recovery-declaration-invalid")
    workloads = health_recovery.get("workloads", [])
    server = next((item for item in workloads if isinstance(item, dict) and item.get("id") == "core-server"), None)
    verifier_workload = next((item for item in workloads if isinstance(item, dict) and item.get("id") == "private-release-verifier"), None)
    liveness = required_mapping(server, "liveness", "health-recovery-declaration-invalid")
    readiness = required_mapping(server, "readiness", "health-recovery-declaration-invalid")
    if liveness.get("path") != verification.get("liveness_path") or readiness.get("path") != verification.get("readiness_path"):
        raise DeclarationFailure("health-recovery-verification-path-mismatch")
    verifier_completion = required_mapping(verifier_workload, "completion", "health-recovery-declaration-invalid")
    success = required_mapping(verifier_completion, "success", "health-recovery-declaration-invalid")
    completion = required_mapping(required_mapping(verifier_workload, "proof", "health-recovery-declaration-invalid"), "completion", "health-recovery-declaration-invalid")
    evidence_reference = completion.get("evidence_reference")
    if not non_empty(evidence_reference):
        raise DeclarationFailure("verifier-completion-evidence-invalid")
    rehearsal = mapping(scope_root / "00-declaration" / evidence_reference, "verifier-completion-evidence-unreadable")
    verification_evidence = required_mapping(rehearsal, "fresh_private_verification", "verifier-completion-evidence-invalid")
    rehearsal = required_mapping(rehearsal, "rehearsal", "verifier-completion-evidence-invalid")
    boundary = timestamp(rehearsal.get("original_task_stopped_at"))
    started = timestamp(verification_evidence.get("verifier_started_at"))
    completed = timestamp(verification_evidence.get("verifier_completed_at"))
    if (
        completion.get("exit_code") != success.get("exit_code")
        or completion.get("result_code") != success.get("result_code")
        or completion.get("exit_code") != verification_evidence.get("exit_code")
        or completion.get("result_code") != verification_evidence.get("code")
        or completion.get("fresh_after") != rehearsal.get("original_task_stopped_at")
        or completion.get("observed_at") != verification_evidence.get("verifier_completed_at")
        or boundary is None
        or started is None
        or completed is None
        or completed < boundary
        or completed < started
        or (completed - started).total_seconds() > verifier_completion.get("deadline_seconds", 0)
    ):
        raise DeclarationFailure("verifier-completion-evidence-invalid")
    dependencies = required_mapping(contract, "dependencies", "scope-dependencies-missing")
    if dependencies.get("required") != [] or dependencies.get("optional") != [] or dependencies.get("persistence") != [] or set(dependencies.get("excluded", [])) != {"persistence", "queue", "product-application", "provider-adapter"}:
        raise DeclarationFailure("scope-dependencies-invalid")
    if set(contract.get("excludes", [])) != REQUIRED_EXCLUSIONS:
        raise DeclarationFailure("scope-exclusions-invalid")
    for section, code in (("receipt", "receipt-declaration-invalid"), ("rollback", "rollback-declaration-invalid")):
        value = required_mapping(contract, section, code)
        if value.get("status") not in {"qualified-receipt-required-before-update-or-restore", "retained-accepted-immutable-release-required-for-restoration"} or not non_empty(value.get("owner")):
            raise DeclarationFailure(code)
    receipt = required_mapping(contract, "receipt", "receipt-declaration-invalid")
    receipt_fields = receipt.get("safe_fields")
    if not isinstance(receipt_fields, list) or not receipt_fields or not set(receipt_fields).issubset(SAFE_RECEIPT_FIELDS):
        raise DeclarationFailure("receipt-declaration-invalid")
    mutation = required_mapping(binding, "mutation", "workload-binding-invalid")
    expected_workloads = {("core-server-service", "long-running-server", "service"), ("private-release-verifier-task", "run-to-completion-task", "task")}
    actual_workloads = {(item.get("id"), item.get("workload_type"), item.get("runtime_class")) for item in binding.get("workloads", []) if isinstance(item, dict)}
    provider_binding = required_mapping(binding, "proposed_provider_binding", "workload-binding-invalid")
    if provider_binding.get("template") != "30-provider-realization/aws/cloudformation/bootstrap-runtime.yml":
        raise DeclarationFailure("workload-binding-invalid")
    template_path = root / provider_binding["template"]
    provider_types = provider_resource_types(template_path)
    expected_provider_resources = {
        "core-server-service": ("BootstrapRuntimeService", "AWS::ECS::Service"),
        "private-release-verifier-task": ("ReleaseVerifierTaskDefinition", "AWS::ECS::TaskDefinition"),
    }
    provider_resources = {
        item.get("id"): (item.get("provider_reference"), provider_types.get(item.get("provider_reference")))
        for item in binding.get("workloads", [])
        if isinstance(item, dict)
    }
    if binding.get("target") != TARGET or binding.get("program_id") != "kanbien-core-server" or binding.get("status") != "healthy-runtime-accepted" or actual_workloads != expected_workloads or mutation.get("status") != "blocked" or mutation.get("allowed_operation") != "update-or-restore-after-fresh-alignment-and-reviewed-change-set":
        raise DeclarationFailure("workload-binding-invalid")
    if provider_resources != expected_provider_resources:
        raise DeclarationFailure("workload-provider-reference-invalid")
    expected_execution = {
        "core-server-service": {
            "kind": "compiled-entrypoint",
            "source_reference": "infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts",
            "command_description": "node artifacts/kanbien-core-server.main.js",
        },
        "private-release-verifier-task": {
            "kind": "inline-command",
            "source_reference": "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml#ReleaseVerifierTaskDefinition.private-release-verifier.command",
            "command_description": "node -e private release verification request",
        },
    }
    executions = {
        item.get("id"): item.get("execution")
        for item in binding.get("workloads", [])
        if isinstance(item, dict)
    }
    try:
        template_text = template_path.read_text(encoding="utf-8")
    except OSError:
        raise DeclarationFailure("workload-execution-source-invalid") from None
    repo_root = Path(__file__).resolve().parents[5]
    if (
        executions != expected_execution
        or "artifacts/kanbien-core-server.main.js" not in (repo_root / "infra/04.deploy/03.product/image/core-server/image-contract.yml").read_text(encoding="utf-8")
        or "KANBIEN_CORE_RELEASE_VERIFIED" not in template_text
        or "KANBIEN_CORE_RELEASE_VERIFICATION_FAILED" not in template_text
    ):
        raise DeclarationFailure("workload-execution-source-invalid")


def check_accepted_release(root: Path) -> None:
    evidence_root = root / "20-scopes" / "bootstrap-runtime" / "30-release-evidence"
    record = mapping(evidence_root / "accepted-release.yml", "accepted-release-unreadable")
    release = required_mapping(record, "release", "accepted-release-invalid")
    acceptance = required_mapping(record, "acceptance", "accepted-release-invalid")
    verification = required_mapping(release, "private_verification", "accepted-release-invalid")
    cost_condition = required_mapping(record, "cost_condition", "accepted-release-invalid")
    if (
        record.get("schema") != "deploy/accepted-release/v1"
        or record.get("target") != TARGET
        or record.get("scope") != "bootstrap-runtime"
        or record.get("status") != "accepted"
        or not isinstance(release.get("source_revision"), str)
        or not __import__("re").fullmatch(r"sha256:[a-f0-9]{64}", str(release.get("image_digest")))
        or not all(non_empty(release.get(field)) for field in ("runtime_stack", "service", "runtime_task_definition", "verifier_task_definition", "package_custody_reference"))
        or verification.get("verdict") != "accepted"
        or verification.get("code") != "runtime-digest-and-private-verifier-accepted"
        or acceptance.get("retained_for_restoration") is not True
        or cost_condition.get("condition_id") != "target-cost-allocation-tag-active"
        or cost_condition.get("evidence") != "10-foundation/evidence/target-cost-allocation-tag.yml"
        or not non_empty(cost_condition.get("disposition"))
    ):
        raise DeclarationFailure("accepted-release-invalid")
    rehearsal_path = acceptance.get("last_rehearsal")
    if not non_empty(rehearsal_path):
        raise DeclarationFailure("accepted-release-rehearsal-missing")
    rehearsal = mapping(evidence_root / rehearsal_path, "accepted-release-rehearsal-unreadable")
    if rehearsal.get("schema") == "deploy/release-rehearsal-evidence/v1":
        restored = required_mapping(rehearsal, "restored_release_a", "accepted-release-rehearsal-invalid")
        restored_verification = required_mapping(restored, "private_verification", "accepted-release-rehearsal-invalid")
        valid = (
            rehearsal.get("target") == TARGET
            and rehearsal.get("scope") == "bootstrap-runtime"
            and rehearsal.get("status") == "restored-and-verified"
            and restored.get("source_revision") == release.get("source_revision")
            and restored.get("image_digest") == release.get("image_digest")
            and restored.get("runtime_task_definition") == release.get("runtime_task_definition")
            and restored.get("verifier_task_definition") == release.get("verifier_task_definition")
            and restored_verification.get("code") == "runtime-digest-and-private-verifier-accepted"
        )
    elif rehearsal.get("schema") == "deploy/workload-recovery-rehearsal-evidence/v1":
        accepted = required_mapping(rehearsal, "accepted_release", "accepted-release-rehearsal-invalid")
        final = required_mapping(rehearsal, "final_workload", "accepted-release-rehearsal-invalid")
        verified = required_mapping(rehearsal, "fresh_private_verification", "accepted-release-rehearsal-invalid")
        valid = (
            rehearsal.get("target") == TARGET
            and rehearsal.get("scope") == "bootstrap-runtime"
            and rehearsal.get("status") == "accepted"
            and accepted.get("source_revision") == release.get("source_revision")
            and accepted.get("image_digest") == release.get("image_digest")
            and accepted.get("runtime_task_definition") == release.get("runtime_task_definition")
            and accepted.get("verifier_task_definition") == release.get("verifier_task_definition")
            and final.get("image_digest") == release.get("image_digest")
            and final.get("runtime_task_definition") == release.get("runtime_task_definition")
            and final.get("health_status") == "HEALTHY"
            and verified.get("exit_code") == 0
            and verified.get("verdict") == "accepted"
            and verified.get("code") == "KANBIEN_CORE_RELEASE_VERIFIED"
        )
    else:
        valid = False
    if not valid:
        raise DeclarationFailure("accepted-release-rehearsal-invalid")
    restoration_path = acceptance.get("last_restoration_rehearsal")
    if not non_empty(restoration_path):
        raise DeclarationFailure("accepted-release-restoration-rehearsal-missing")
    restoration = mapping(evidence_root / restoration_path, "accepted-release-restoration-rehearsal-unreadable")
    restored = required_mapping(restoration, "restored_release_a", "accepted-release-restoration-rehearsal-invalid")
    restored_verification = required_mapping(restored, "private_verification", "accepted-release-restoration-rehearsal-invalid")
    if (
        restoration.get("schema") != "deploy/release-rehearsal-evidence/v1"
        or restoration.get("target") != TARGET
        or restoration.get("scope") != "bootstrap-runtime"
        or restoration.get("status") != "restored-and-verified"
        or restored.get("source_revision") != release.get("source_revision")
        or restored.get("image_digest") != release.get("image_digest")
        or restored.get("runtime_task_definition") != release.get("runtime_task_definition")
        or restored.get("verifier_task_definition") != release.get("verifier_task_definition")
        or restored_verification.get("code") != "runtime-digest-and-private-verifier-accepted"
    ):
        raise DeclarationFailure("accepted-release-restoration-rehearsal-invalid")


def check_pipeline(root: Path) -> None:
    catalogue = mapping(root / "40-package-custody" / "github-actions" / "pipeline-index.yml", "pipeline-index-unreadable")
    if catalogue.get("schema") != "deploy/pipeline-index/v1" or catalogue.get("target") != TARGET:
        raise DeclarationFailure("pipeline-index-invalid")
    pipelines = catalogue.get("pipelines")
    if not isinstance(pipelines, list) or len(pipelines) != 1 or not isinstance(pipelines[0], dict):
        raise DeclarationFailure("pipeline-record-missing")
    pipeline = pipelines[0]
    if pipeline.get("id") != "core-server-package-custody" or pipeline.get("type") != "package-publication" or pipeline.get("state") != "active" or pipeline.get("executable_workflow") != ".github/workflows/publish-kanbien-core-platform-core-server.yml" or pipeline.get("delivery_access_contract") != "core-server-package-custody.delivery-access.yml" or pipeline.get("trigger") != "workflow_dispatch" or pipeline.get("permitted_source_ref") != "refs/heads/main" or pipeline.get("approval") != "github-environment:kanbien-core-platform" or pipeline.get("provider_identity") != "github-kanbien-core-platform-delivery" or pipeline.get("package_destination") != "kanbien-core-platform/core-server" or pipeline.get("provider_region_alias") != "aws-eu-west-1" or pipeline.get("receipt_contract") != ".agentic/04.deploy/40-package/schemas/package-custody-receipt.v1.schema.yml":
        raise DeclarationFailure("pipeline-record-invalid")
    if not non_empty(pipeline.get("owner")):
        raise DeclarationFailure("pipeline-unowned")
    if pipeline.get("permitted_operations") != ["qualify-local-image", "publish-immutable-image", "vulnerability-scan", "sbom", "provenance-attestation", "write-safe-package-custody-receipt"] or pipeline.get("outputs") != ["immutable-image-digest", "package-custody-receipt"] or pipeline.get("used_by_scopes") != ["bootstrap-runtime"] or "delivery-access-coverage" not in pipeline.get("required_proofs", []) or pipeline.get("deployment_boundary") != "target-bound-deploy-capability-not-this-pipeline":
        raise DeclarationFailure("pipeline-authority-invalid")


def report(verdict: str, codes: tuple[str, ...]) -> str:
    return json.dumps({"schema": "deploy/target-declaration-report/v1", "target": TARGET, "scope": "repository-declaration", "verdict": verdict, "findings": [{"code": code} for code in codes]}, sort_keys=True)


def main() -> int:
    try:
        args = parse_args()
        root = Path(args.target_root) if args.target_root else Path(__file__).resolve().parents[5] / "infra/04.deploy/03.product/targets" / TARGET
        profile = mapping(root / "00-target" / "target-profile.yml", "target-profile-unreadable")
        check_profile(profile)
        check_foundation(root)
        check_scope(root)
        check_accepted_release(root)
        check_pipeline(root)
        print(report("repository-declaration-complete", ()))
        return 0
    except DeclarationFailure as failure:
        print(report("failed", failure.codes))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
