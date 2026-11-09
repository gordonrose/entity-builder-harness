#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.entity-smoke-runtime-configuration
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Normalize the isolated runtime and separate restore templates through the existing provider-adapter interface without merging their identities or database routes.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import importlib.util
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[6]
SOURCE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation"
MAIN = SOURCE / "entity-smoke.yml"
RESTORE = SOURCE / "entity-smoke-isolated-restore.yml"
WORKLOADS = {
    "entity-smoke-server-service": (MAIN, "FeatureService"),
    "entity-smoke-migration-task": (MAIN, "MigrationTaskDefinition"),
    "entity-smoke-administration-task": (MAIN, "AdministrationTaskDefinition"),
    "entity-smoke-verifier-task": (MAIN, "VerifierTaskDefinition"),
    "entity-smoke-database-proof-task": (MAIN, "DatabaseProofTaskDefinition"),
    "entity-smoke-restore-reader-task": (RESTORE, "RestoreReaderTaskDefinition"),
}


def checked(path):
    value = Path(path).absolute()
    if value not in {MAIN, RESTORE} or value.is_symlink() or any(part.is_symlink() for part in value.parents):
        raise ValueError("entity-smoke-configuration-source-invalid")
    return value


def adapter():
    spec = importlib.util.spec_from_file_location("entity_smoke_generic_ecs_configuration", Path(__file__).with_name("ecs-runtime-configuration.py"))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def normalize(path, binding):
    """Source shape proof only; no provider call, live permission or secret read."""
    checked(path)
    if Path(path).absolute() != MAIN or not isinstance(binding, dict) or binding.get("target") != "kanbien-core-platform" or binding.get("scope") != "entity-smoke" or binding.get("program_id") != "kanbien-entity-smoke":
        raise ValueError("entity-smoke-configuration-binding-invalid")
    workloads = binding.get("workloads")
    if not isinstance(workloads, list) or len(workloads) != len(WORKLOADS) or any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in workloads) or {item["id"] for item in workloads} != set(WORKLOADS):
        raise ValueError("entity-smoke-configuration-workloads-invalid")
    if any(item.get("provider_reference") != WORKLOADS[item["id"]][1] for item in workloads):
        raise ValueError("entity-smoke-configuration-binding-invalid")
    generic, result = adapter(), {}
    try:
        for source in (MAIN, RESTORE):
            selected = [item for item in workloads if WORKLOADS[item["id"]][0] == source]
            normalized = generic.normalize(checked(source), {**binding, "workloads": selected})
            if set(result) & set(normalized): raise ValueError("entity-smoke-configuration-workloads-invalid")
            result.update(normalized)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, yaml.YAMLError):
        raise ValueError("entity-smoke-configuration-source-invalid") from None
    return result


def package_projection(path, selector):
    return adapter().package_projection(checked(path), selector)
