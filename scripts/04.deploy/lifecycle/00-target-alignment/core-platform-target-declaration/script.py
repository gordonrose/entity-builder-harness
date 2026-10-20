#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.core-platform-target-declaration.implementation
#   version: 2
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
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
    "cost-guard",
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
SAFE_CONFIG_NAME = __import__("re").compile(r"^[A-Z][A-Z0-9_]*$")


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


def required_mapping(document: dict[str, Any], key: str, code: str) -> dict[str, Any]:
    value = document.get(key)
    if not isinstance(value, dict):
        raise DeclarationFailure(code)
    return value


def check_profile(profile: dict[str, Any]) -> None:
    if profile.get("schema") != "deploy/target-profile/v1" or profile.get("id") != TARGET:
        raise DeclarationFailure("target-profile-invalid")
    if profile.get("status") != "planned-not-live-selected":
        raise DeclarationFailure("target-status-invalid")
    if profile.get("baseline") != "absent" or profile.get("repository_declaration") != "repository-declaration-complete":
        raise DeclarationFailure("target-baseline-invalid")
    if profile.get("live_alignment") != "not-checked":
        raise DeclarationFailure("live-alignment-falsely-ready")
    provider = required_mapping(profile, "provider", "provider-declaration-missing")
    if provider.get("family") != "aws" or provider.get("selection_status") != "unresolved-e0-required":
        raise DeclarationFailure("provider-selection-invalid")
    mutation = required_mapping(profile, "target_mutation", "target-mutation-missing")
    if mutation.get("status") != "blocked" or mutation.get("allowed_operation") != "create-only":
        raise DeclarationFailure("target-mutation-not-create-only")
    facts = profile.get("e0_required_facts")
    if not isinstance(facts, list):
        raise DeclarationFailure("e0-fact-missing")
    found: set[str] = set()
    for fact in facts:
        if not isinstance(fact, dict) or not non_empty(fact.get("id")):
            raise DeclarationFailure("e0-fact-invalid")
        fact_id = fact["id"]
        found.add(fact_id)
        if fact.get("status") != "unresolved-e0-required":
            raise DeclarationFailure("e0-fact-status-invalid")
        if not non_empty(fact.get("owner")):
            raise DeclarationFailure("e0-fact-unowned")
        if not non_empty(fact.get("evidence")):
            raise DeclarationFailure("e0-fact-evidence-missing")
    if found != REQUIRED_E0_FACTS:
        raise DeclarationFailure("e0-fact-missing")


def check_foundation(root: Path) -> None:
    index = mapping(root / "foundation" / "foundation-index.yml", "foundation-index-unreadable")
    if index.get("schema") != "deploy/target-foundation-index/v1" or index.get("target") != TARGET:
        raise DeclarationFailure("foundation-index-invalid")
    resources = index.get("resources")
    if not isinstance(resources, list) or not resources:
        raise DeclarationFailure("foundation-resource-missing")
    for item in resources:
        if not isinstance(item, dict) or not non_empty(item.get("id")) or not non_empty(item.get("declaration")):
            raise DeclarationFailure("foundation-resource-invalid")
        if item.get("status") != "unresolved-e0-required":
            raise DeclarationFailure("foundation-resource-status-invalid")
        if not non_empty(item.get("owner")):
            raise DeclarationFailure("foundation-resource-unowned")
    network = mapping(root / "foundation" / "network.yml", "network-declaration-unreadable")
    route = required_mapping(network, "private_verifier_route", "private-verifier-missing")
    if network.get("public_ingress") != "prohibited" or route.get("status") != "unresolved-e0-required" or route.get("permitted_caller") != "selected-private-verifier-only":
        raise DeclarationFailure("private-verifier-invalid")
    access = mapping(root / "foundation" / "technical-access.yml", "technical-access-unreadable")
    intents = access.get("access_intents")
    if not isinstance(intents, list) or {item.get("id") for item in intents if isinstance(item, dict)} != {"delivery-custody", "workload-startup"}:
        raise DeclarationFailure("technical-access-invalid")
    for intent in intents:
        if not isinstance(intent, dict) or intent.get("provider_identity") != "unresolved-e0-required" or not non_empty(intent.get("owner")):
            raise DeclarationFailure("technical-access-invalid")
    cost = mapping(root / "foundation" / "cost-control.yml", "cost-control-unreadable")
    waiver = required_mapping(cost, "waiver", "cost-control-invalid")
    expected_controls = {"one-task-only", "no-autoscaling", "no-nat", "no-public-ingress", "no-data-services", "no-new-cost-category"}
    if (
        cost.get("schema") != "deploy/provider-condition-declaration/v1"
        or cost.get("target") != TARGET
        or cost.get("condition_id") != "target-cost-allocation-tag-active"
        or cost.get("status") not in {"not-requested", "requested", "waiting-on-provider", "verified", "expired", "waived-by-approved-exception"}
        or not non_empty(cost.get("owner"))
        or not non_empty(cost.get("required_evidence"))
        or cost.get("evidence_validator") != "scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.sh"
        or set(waiver.get("compensating_controls", [])) != expected_controls
        or not non_empty(waiver.get("follow_up_owner"))
    ):
        raise DeclarationFailure("cost-control-invalid")


def check_scope(root: Path) -> None:
    scope_root = root / "scopes" / "bootstrap-runtime"
    contract = mapping(scope_root / "declaration-contract.yml", "scope-contract-unreadable")
    if contract.get("schema") != "deploy/target-scope-contract/v1" or contract.get("target") != TARGET or contract.get("id") != "kanbien-core-platform-bootstrap-runtime":
        raise DeclarationFailure("scope-contract-invalid")
    if not non_empty(contract.get("owner")):
        raise DeclarationFailure("scope-unowned")
    program = required_mapping(contract, "program", "scope-program-missing")
    if program.get("id") != "kanbien-core-server" or program.get("contract") != "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml" or program.get("image_contract") != "infra/04.deploy/03.product/image/core-server/image-contract.yml":
        raise DeclarationFailure("scope-program-invalid")
    workload = required_mapping(contract, "workload", "scope-workload-missing")
    if workload.get("operation") != "create-only" or workload.get("runtime_selection") != "unresolved-e0-required" or workload.get("startup_access") != "foundation/technical-access.yml#workload-startup" or workload.get("network") != "foundation/network.yml#private-verifier-route":
        raise DeclarationFailure("scope-workload-invalid")
    configuration = required_mapping(contract, "configuration", "scope-configuration-missing")
    if configuration.get("value_policy") != "names-and-shapes-only-no-values" or configuration.get("secret_names") != []:
        raise DeclarationFailure("scope-configuration-invalid")
    names = configuration.get("required_names", []) + configuration.get("optional_names", [])
    if not names or not all(isinstance(name, str) and SAFE_CONFIG_NAME.fullmatch(name) for name in names):
        raise DeclarationFailure("scope-configuration-invalid")
    verification = required_mapping(contract, "verification", "scope-verification-missing")
    if verification.get("route_exposure") != "private-verifier-only" or verification.get("status") != "unresolved-e0-required" or not non_empty(verification.get("owner")):
        raise DeclarationFailure("scope-verification-invalid")
    dependencies = required_mapping(contract, "dependencies", "scope-dependencies-missing")
    if dependencies.get("required") != [] or dependencies.get("optional") != [] or set(dependencies.get("excluded", [])) != {"persistence", "queue", "product-application", "provider-adapter"}:
        raise DeclarationFailure("scope-dependencies-invalid")
    if set(contract.get("excludes", [])) != REQUIRED_EXCLUSIONS:
        raise DeclarationFailure("scope-exclusions-invalid")
    for section, code in (("receipt", "receipt-declaration-invalid"), ("rollback", "rollback-declaration-invalid")):
        value = required_mapping(contract, section, code)
        if value.get("status") != "unresolved-e0-required" or not non_empty(value.get("owner")):
            raise DeclarationFailure(code)
    receipt = required_mapping(contract, "receipt", "receipt-declaration-invalid")
    receipt_fields = receipt.get("safe_fields")
    if not isinstance(receipt_fields, list) or not receipt_fields or not set(receipt_fields).issubset(SAFE_RECEIPT_FIELDS):
        raise DeclarationFailure("receipt-declaration-invalid")
    binding = mapping(scope_root / "workload-binding.yml", "workload-binding-unreadable")
    mutation = required_mapping(binding, "mutation", "workload-binding-invalid")
    if binding.get("target") != TARGET or binding.get("program_id") != "kanbien-core-server" or binding.get("status") != "unresolved-e0-required" or mutation.get("status") != "blocked" or mutation.get("allowed_operation") != "create-only":
        raise DeclarationFailure("workload-binding-invalid")


def check_pipeline(root: Path) -> None:
    catalogue = mapping(root / "pipelines" / "github-actions" / "pipeline-index.yml", "pipeline-index-unreadable")
    if catalogue.get("schema") != "deploy/pipeline-index/v1" or catalogue.get("target") != TARGET:
        raise DeclarationFailure("pipeline-index-invalid")
    pipelines = catalogue.get("pipelines")
    if not isinstance(pipelines, list) or len(pipelines) != 1 or not isinstance(pipelines[0], dict):
        raise DeclarationFailure("pipeline-record-missing")
    pipeline = pipelines[0]
    if pipeline.get("id") != "core-server-package-custody" or pipeline.get("type") != "package-publication" or pipeline.get("state") != "active" or pipeline.get("executable_workflow") != ".github/workflows/publish-kanbien-core-platform-core-server.yml" or pipeline.get("delivery_access_contract") != "core-server-package-custody.delivery-access.yml" or pipeline.get("trigger") != "workflow_dispatch" or pipeline.get("permitted_source_ref") != "refs/heads/main" or pipeline.get("approval") != "github-environment:kanbien-core-platform" or pipeline.get("provider_identity") != "github-kanbien-core-platform-delivery" or pipeline.get("package_destination") != "kanbien-core-platform/core-server" or pipeline.get("provider_region_alias") != "aws-eu-west-1" or pipeline.get("receipt_contract") != ".agentic/04.deploy/schemas/package-custody-receipt.v1.schema.yml":
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
        profile = mapping(root / "target-profile.yml", "target-profile-unreadable")
        check_profile(profile)
        check_foundation(root)
        check_scope(root)
        check_pipeline(root)
        print(report("repository-declaration-complete", ()))
        return 0
    except DeclarationFailure as failure:
        print(report("failed", failure.codes))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
