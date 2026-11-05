#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.verify-platform-shell-deploy-readiness
#   version: 2
#   status: active
#   created_on: "2026-07-10"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#     - agentic
#     - sre
#   kind: script
#   purpose: Validate platform shell deploy-readiness evidence without mutating GitHub or AWS.
#   portability:
#     class: internal
#     targets: []
#   effects:
#     - read-only
#     - writes-files
#   used_by:
#     - id: deploy.script.verify-platform-shell-deploy-readiness.readme
#       path: scripts/04.deploy/verify-platform-shell-deploy-readiness/README.md
#     - id: deploy.script.verify-platform-shell-deploy-readiness.smoke-test
#       path: scripts/04.deploy/verify-platform-shell-deploy-readiness/smoke-test.sh
#     - id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
#       path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MANIFEST=""
JSON=false
ALLOW_BLOCKED=false
CALLER_INTENT=""
REHEARSAL_ROOT=""
RECORD_COMPATIBILITY=""

usage() {
  cat <<'EOF'
Usage:
  verify-platform-shell-deploy-readiness/script.sh --manifest <path> [--json]
  verify-platform-shell-deploy-readiness/script.sh --manifest <path> --allow-blocked --caller-intent <planning|explanation> [--json]

Validates a deploy-readiness manifest for the product platform shell.
The default command is read-only and fails closed when required deploy proof is missing.
--record-rollback-compatibility <retained-release-id> writes additive local compatibility
evidence only when the retained runtime/package proof matches current source inputs.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --manifest)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --manifest requires a path." >&2
        exit 2
      fi
      MANIFEST="$2"
      shift 2
      ;;
    --record-rollback-compatibility)
      if [ "$#" -lt 2 ]; then echo "ERROR: --record-rollback-compatibility requires a retained release ID." >&2; exit 2; fi
      RECORD_COMPATIBILITY="$2"
      shift 2
      ;;
    --rehearsal-root)
      if [ "$#" -lt 2 ]; then echo "ERROR: --rehearsal-root requires a path." >&2; exit 2; fi
      REHEARSAL_ROOT="$2"
      shift 2
      ;;
    --json)
      JSON=true
      shift
      ;;
    --allow-blocked)
      ALLOW_BLOCKED=true
      shift
      ;;
    --caller-intent)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --caller-intent requires a value." >&2
        exit 2
      fi
      CALLER_INTENT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: readiness-arguments-invalid" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$MANIFEST" ]; then
  echo "ERROR: --manifest is required." >&2
  usage >&2
  exit 2
fi

if [ "$ALLOW_BLOCKED" = true ] && [ -z "$CALLER_INTENT" ]; then
  echo "ERROR: --allow-blocked requires --caller-intent planning or --caller-intent explanation." >&2
  exit 2
fi

python3 - "$MANIFEST" "$JSON" "$ALLOW_BLOCKED" "$CALLER_INTENT" "$REHEARSAL_ROOT" "$RECORD_COMPATIBILITY" <<'PY'
from __future__ import annotations

import json
import importlib.util
from datetime import date
import math
import tempfile
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - surfaced in shell usage
    print("ERROR: readiness-yaml-loader-unavailable", file=sys.stderr)
    sys.exit(2)

ROOT = Path.cwd()
manifest_path = Path(sys.argv[1])
emit_json = sys.argv[2] == "true"
allow_blocked = sys.argv[3] == "true"
caller_intent = sys.argv[4]
try:
    rehearsal_root = Path(sys.argv[5]).resolve() if sys.argv[5] else None
except (OSError, ValueError):
    print("ERROR: readiness-rehearsal-root-unavailable",file=sys.stderr);sys.exit(2)
if rehearsal_root is not None and (not rehearsal_root.is_relative_to(Path(tempfile.gettempdir()).resolve()) or rehearsal_root.is_relative_to(ROOT)):
    print("ERROR: rehearsal root must be temporary and outside repository",file=sys.stderr);sys.exit(2)

record_compatibility = sys.argv[6]

SCHEMA = "deploy/platform-shell-readiness-manifest/v1"
TARGET_PROFILE_SCHEMA = "deploy/platform-shell-target-profile/v1"
REPORT_SCHEMA = "deploy/platform-shell-readiness-report/v1"
ALLOWED_BLOCKED_CALLER_INTENTS = {"planning", "explanation"}
PENDING_VALUES = {
    "",
    "pending",
    "pending-or-deferred",
    "blocked",
    "blocked-until-smoke-app-job-requirements",
}
REQUIRED_BLOCKED_PATHS = [
    "source.commit_sha",
    "source.workflow_path",
    "source.workflow_run_id",
    "github.source_policy",
    "github.commit_sha",
    "github.workflow_path",
    "github.workflow_run_id",
    "github.environment.protection_rules.required_reviewers",
    "github.environment.protection_rules.deployment_branch_policy",
    "github.environment.protection_rules.prevent_self_review",
    "github.oidc.role_arn",
    "github.oidc.subject_condition",
    "github.oidc.trust_scoped_to_repository",
    "github.oidc.trust_scoped_to_ref",
    "github.oidc.workflow_has_id_token_permission",
    "artifacts.source_commit_sha",
    "artifacts.image.image_digest",
    "artifacts.image.base_image_digest",
    "artifacts.image.sbom",
    "artifacts.image.vulnerability_scan",
    "artifacts.image.provenance_or_attestation",
    "runtime.server.task_definition",
    "runtime.server.service",
    "runtime.worker.status",
    "runtime.worker.task_definition",
    "runtime.worker.service",
    "cloud.account_id",
    "cloud.profile_or_oidc_role",
    "cloud.region",
    "aws.account_id",
    "aws.profile_or_oidc_role",
    "aws.region",
    "aws.cluster",
    "aws.vpc",
    "aws.subnets",
    "aws.security_groups",
    "aws.alb",
    "aws.target_group",
    "aws.tls_certificate",
    "aws.dns_hostname",
    "aws.secret_store",
    "aws.log_group",
    "aws.alarms",
    "operations.owner",
    "operations.escalation_path",
    "operations.budget_name",
    "operations.cost_limit",
    "operations.rollback_target",
    "operations.rollback_authority",
    "operations.rollback_runbook",
    "proof.policy_checks",
    "proof.generated_output_review",
    "proof.aws_read_only_inspection",
    "proof.deployment_smoke",
    "proof.rollback_proof",
    "auth.token_validation.issuer",
    "auth.token_validation.jwks_uri",
    "auth.token_validation.app_client_id",
    "auth.permission_mapping.declared_app_permissions_source",
    "auth.route_exposure.protected_dummy_route.deployment_smoke",
    "auth.cors.allowed_origins",
    "auth.secrets.source",
]


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError("readiness-manifest-unavailable")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("manifest must be a YAML object")
    return data


def get(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def slug(path: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")


blocking_gaps: list[dict[str, str]] = []
warnings: list[dict[str, str]] = []


def block(path: str, message: str, resolution: str) -> None:
    blocking_gaps.append(
        {
            "id": f"gap.deploy.platform-shell-readiness.{slug(path)}",
            "path": path,
            "message": message,
            "suggested_resolution": resolution,
        }
    )


def warn(path: str, message: str) -> None:
    warnings.append({"path": path, "message": message})


def is_pending(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in PENDING_VALUES
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False


def require_string(data: dict[str, Any], path: str, *, pattern: str | None = None) -> None:
    value = get(data, path)
    if is_pending(value) or not isinstance(value, str):
        block(path, "required string is missing or pending", f"Set `{path}` in the platform shell readiness manifest.")
        return
    if pattern and not re.fullmatch(pattern, value.strip()):
        block(path, "value has invalid shape", f"Set `{path}` to the governed expected format.")


def require_bool_ready(data: dict[str, Any], path: str) -> None:
    value = get(data, path)
    if value is not True:
        block(path, "required boolean proof is not true", f"Set `{path}: true` only after proof exists.")


def require_file(data: dict[str, Any], path: str) -> None:
    global validation_location
    validation_location = path
    value = get(data, path)
    if not isinstance(value, str) or is_pending(value):
        block(path, "required local file path is missing or pending", f"Set `{path}` to a repo-relative file path.")
        return
    target = ROOT / value
    if not target.is_file():
        block(path, "referenced file does not exist", f"Create the referenced file or update `{path}`.")


def require_github_workflow(data: dict[str, Any], path: str) -> None:
    global validation_location
    validation_location = path
    value = get(data, path)
    if not isinstance(value, str) or is_pending(value):
        block(path, "required GitHub workflow path is missing or pending", f"Set `{path}` to a repo-relative workflow path.")
        return
    if not re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", value):
        block(path, "workflow path has invalid shape", "Use a workflow under `.github/workflows/`.")
        return

    target = ROOT / value
    if not target.is_file():
        block(path, "referenced workflow does not exist", f"Create the referenced workflow or update `{path}`.")
        return

    text = target.read_text(encoding="utf-8")
    has_id_token_write = re.search(r"(?m)^\s*id-token:\s*write\s*$", text) is not None
    if not re.search(r"(?m)^\s*workflow_dispatch:\s*$", text):
        block(path, "workflow must be manually dispatchable", "Add a `workflow_dispatch` trigger for governed staging deploys.")
    if not has_id_token_write:
        block(
            "github.oidc.workflow_has_id_token_permission",
            "workflow does not grant GitHub OIDC id-token permission",
            "Set workflow permissions to include `id-token: write`.",
        )

    environment_name = get(data, "github.environment.name")
    if isinstance(environment_name, str) and environment_name.strip():
        environment_pattern = rf"(?m)^\s*environment:\s*{re.escape(environment_name.strip())}\s*$"
        if not re.search(environment_pattern, text):
            block(
                "github.environment.name",
                "workflow does not use the selected GitHub environment",
                "Set the deploy job environment to the protected staging environment.",
            )


def require_yaml_file(data: dict[str, Any], path: str, *, schema: str | None = None) -> dict[str, Any] | None:
    value = get(data, path)
    if not isinstance(value, str) or is_pending(value):
        block(path, "required local YAML path is missing or pending", f"Set `{path}` to a repo-relative YAML path.")
        return None
    target = ROOT / value
    if not target.is_file():
        block(path, "referenced file does not exist", f"Create the referenced file or update `{path}`.")
        return None
    try:
        with target.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
    except Exception:
        block(path, "referenced YAML could not be read or parsed", f"Inspect the referenced YAML for `{path}`.")
        return None
    if not isinstance(loaded, dict):
        block(path, "referenced YAML must be an object", f"Make the referenced `{path}` YAML an object.")
        return None
    if schema and loaded.get("schema") != schema:
        block(path, f"referenced YAML schema must be `{schema}`", f"Set the referenced YAML schema to `{schema}`.")
    return loaded


def require_matching(data: dict[str, Any], left: str, right: str) -> None:
    left_value = get(data, left)
    right_value = get(data, right)
    if is_pending(left_value) or is_pending(right_value):
        return
    if left_value != right_value:
        block(left, f"value must match `{right}`", f"Keep `{left}` and `{right}` aligned in the target profile.")


def blocker_paths(data: dict[str, Any]) -> set[str]:
    blockers = data.get("blockers")
    if not isinstance(blockers, list):
        block("blockers", "blocked readiness manifests must include a blockers list", "Add explicit blocker objects.")
        return set()

    paths: set[str] = set()
    seen_ids: set[str] = set()
    for index, item in enumerate(blockers):
        base = f"blockers.{index}"
        if not isinstance(item, dict):
            block(base, "blocker must be an object", "Use blocker objects with id, severity, path, reason, and resolution.")
            continue
        blocker_id = item.get("id")
        severity = item.get("severity")
        path = item.get("path")
        if not isinstance(blocker_id, str) or not blocker_id.strip():
            block(f"{base}.id", "blocker id is missing", "Add a stable blocker id.")
        elif blocker_id in seen_ids:
            block(f"{base}.id", "blocker id is duplicated", "Use unique blocker ids.")
        else:
            seen_ids.add(blocker_id)
        if severity != "blocking":
            block(f"{base}.severity", "blocker severity must be blocking", "Use `severity: blocking` for deploy-readiness blockers.")
        if not isinstance(path, str) or not path.strip():
            block(f"{base}.path", "blocker path is missing", "Point the blocker at the unresolved manifest field.")
        else:
            paths.add(path)
        for required in ("reason", "resolution"):
            value = item.get(required)
            if not isinstance(value, str) or not value.strip():
                block(f"{base}.{required}", f"blocker {required} is missing", f"Explain the blocker {required}.")
    return paths


def blocker_covers(blocked_paths: set[str], required_path: str) -> bool:
    return any(required_path == path or required_path.startswith(f"{path}.") for path in blocked_paths)


def validate_blocked_coverage(data: dict[str, Any], blocked_paths: set[str]) -> None:
    for path in REQUIRED_BLOCKED_PATHS:
        value = get(data, path)
        if is_pending(value) and not blocker_covers(blocked_paths, path):
            block(
                path,
                "pending deploy proof is not covered by an explicit blocker",
                "Add a blocker whose `path` is this field or a parent field.",
            )


def validate(data: dict[str, Any]) -> None:
    global validation_location
    validation_location = 'schema'
    if data.get("schema") != SCHEMA:
        block("schema", "manifest schema is missing or unsupported", f"Use schema `{SCHEMA}`.")

    validation_location = 'target_profile'
    profile = get(data, "target_profile")
    if profile is not None:
        if not isinstance(profile, dict):
            block("target_profile", "target_profile must be an object", "Use target_profile.path to reference the reusable decision feed.")
        else:
            if profile.get("schema") != TARGET_PROFILE_SCHEMA:
                block(
                    "target_profile.schema",
                    f"target_profile schema must be `{TARGET_PROFILE_SCHEMA}`",
                    f"Use schema `{TARGET_PROFILE_SCHEMA}` for platform shell target profiles.",
                )
            target_profile = require_yaml_file(data, "target_profile.path", schema=TARGET_PROFILE_SCHEMA)
            if target_profile:
                for left, right in (
                    ("client.id", "client.id"),
                    ("environment.id", "environment.id"),
                    ("deployment.service_id", "deployment.service_id"),
                ):
                    if get(data, left) != get(target_profile, right):
                        block(
                            left,
                            f"value must match target_profile.{right}",
                            f"Keep `{left}` aligned with the reusable target profile.",
                        )

    validation_location = 'status'
    status = data.get("status")
    if status not in {"ready", "blocked"}:
        block("status", "status must be ready or blocked", "Set `status` to `ready` or `blocked`.")

    require_string(data, "deployment.service_id")
    if get(data, "deployment.service_id") != "platform-shell":
        block("deployment.service_id", "service_id must be platform-shell", "Use the product platform shell service id.")
    require_string(data, "deployment.environment")
    require_string(data, "deployment.runtime_target")
    require_string(data, "client.id")
    require_string(data, "environment.id")
    require_matching(data, "deployment.environment", "environment.id")
    if get(data, "deployment.mutation_authorized") is not False:
        block(
            "deployment.mutation_authorized",
            "readiness proof must not authorize deployment mutation",
            "Keep mutation authorization in a separate governed execution workflow.",
        )

    require_string(data, "source.provider")
    if get(data, "source.provider") != "github":
        block("source.provider", "current source profile provider must be github", "Use `source.provider: github` or add a governed source-provider rule.")
    require_string(data, "source.repository", pattern=r"[^/\s]+/[^/\s]+")
    require_string(data, "source.ref")
    require_string(data, "github.repository", pattern=r"[^/\s]+/[^/\s]+")
    require_string(data, "github.ref")
    require_matching(data, "source.repository", "github.repository")
    require_matching(data, "source.ref", "github.ref")
    require_matching(data, "source.commit_sha", "github.commit_sha")
    require_matching(data, "source.workflow_path", "github.workflow_path")
    require_matching(data, "source.workflow_run_id", "github.workflow_run_id")
    require_github_workflow(data, "github.workflow_path")
    require_string(data, "github.oidc.audience")
    require_string(data, "github.oidc.repository_condition")
    require_string(data, "github.oidc.ref_condition")
    require_string(data, "github.oidc.environment_condition")

    require_string(data, "cloud.provider")
    if get(data, "cloud.provider") != "aws":
        block("cloud.provider", "ecs-fargate target profiles must use cloud.provider aws", "Use `cloud.provider: aws` for ecs-fargate or add a separate governed runtime-family rule.")
    require_matching(data, "cloud.account_id", "aws.account_id")
    require_matching(data, "cloud.profile_or_oidc_role", "aws.profile_or_oidc_role")
    require_matching(data, "cloud.region", "aws.region")

    require_string(data, "runtime.provider")
    require_string(data, "runtime.family")
    if get(data, "runtime.provider") != get(data, "cloud.provider"):
        block("runtime.provider", "runtime provider must match cloud provider", "Select a runtime provider that matches the target cloud profile.")
    if get(data, "runtime.family") != "ecs-fargate":
        block(
            "runtime.family",
            "Milestone 9 selected ecs-fargate for the first platform shell planning target",
            "Use `ecs-fargate` or update the governed runtime-family decision first.",
        )
    require_string(data, "runtime.adapter")
    if get(data, "runtime.adapter") != "platform/adapters/aws/runtime/ecs-fargate/":
        block(
            "runtime.adapter",
            "ecs-fargate targets must select the ECS Fargate runtime adapter",
            "Use `platform/adapters/aws/runtime/ecs-fargate/` for this target profile.",
        )
    require_file(data, "runtime.decision")
    require_file(data, "artifacts.image.dockerfile")
    require_file(data, "artifacts.image.local_smoke_script")

    if get(data, "artifacts.image.build_context") != ".":
        block("artifacts.image.build_context", "build context must be repo root for the current image blueprint", "Set build_context to `.`.")
    require_bool_ready(data, "artifacts.image.local_smoke_passed")

    if get(data, "runtime.server.health.liveness") != "/livez":
        block("runtime.server.health.liveness", "liveness health path must be /livez", "Use the platform server liveness path.")
    if get(data, "runtime.server.health.readiness") != "/readyz":
        block("runtime.server.health.readiness", "readiness health path must be /readyz", "Use the platform server readiness path.")
    if get(data, "runtime.server.container_port") != 3000:
        block("runtime.server.container_port", "container port must match the image blueprint", "Set container_port to 3000.")

    validation_location = 'auth'
    require_string(data, "auth.provider")
    if get(data, "auth.provider") != "cognito":
        block("auth.provider", "Milestone 10a selected Cognito for the first platform shell auth path", "Use `auth.provider: cognito` or update the governed auth provider ADR first.")
    require_file(data, "auth.provider_decision")
    if get(data, "auth.token_validation.mode") != "jwt-jwks":
        block("auth.token_validation.mode", "auth token validation mode must be jwt-jwks", "Use provider-neutral JWT/JWKS validation through platform/security.")
    if get(data, "auth.token_validation.token_use") != "access":
        block("auth.token_validation.token_use", "Cognito API route auth must validate access tokens", "Set token_use to `access` for platform API route authorization.")
    require_bool_ready(data, "auth.token_validation.local_tests_passed")
    if get(data, "auth.permission_mapping.source") != "target-profile":
        block("auth.permission_mapping.source", "authz mappings must come from the target profile or equivalent environment config", "Use target-profile authz mapping for Cognito groups, scopes, or claims.")
    require_bool_ready(data, "auth.permission_mapping.validates_against_app_permissions")
    if get(data, "auth.route_exposure.app_routes_default") != "authenticated":
        block("auth.route_exposure.app_routes_default", "internet-facing app routes must default to authenticated", "Keep app routes denied by default unless explicitly public.")
    require_bool_ready(data, "auth.route_exposure.unauthenticated_app_routes_denied_by_default")
    require_bool_ready(data, "auth.route_exposure.protected_dummy_route.local_401_test")
    require_bool_ready(data, "auth.route_exposure.protected_dummy_route.local_403_test")
    require_bool_ready(data, "auth.route_exposure.protected_dummy_route.local_success_test")
    validation_location = 'auth.health_exposure.livez'
    if get(data, "auth.health_exposure.livez") not in {"public", "authenticated"}:
        block("auth.health_exposure.livez", "liveness exposure must be explicit", "Set liveness exposure to public or authenticated.")
    validation_location = 'auth.health_exposure.readyz'
    if get(data, "auth.health_exposure.readyz") not in {"public", "authenticated"}:
        block("auth.health_exposure.readyz", "readiness exposure must be explicit", "Set readiness exposure to public or authenticated.")
    if get(data, "auth.cors.allowlist_source") != "target-profile-env":
        block("auth.cors.allowlist_source", "CORS allowlist must come from target profile or equivalent environment config", "Set CORS allowlist source to target-profile-env.")
    if get(data, "auth.rate_limiting.keying") != "principal-token-or-target-resolved-client-address":
        block("auth.rate_limiting.keying", "rate-limit keying must use a principal, token/session identity, or target-resolved trusted client address", "Use principal-token-or-target-resolved-client-address and keep unverified forwarded headers out of generic server code.")
    if get(data, "auth.rate_limiting.generic_server_peer_address") != "socket-peer-only":
        block("auth.rate_limiting.generic_server_peer_address", "generic server transport must not trust caller-controlled forwarded-address headers", "Record socket-peer-only; select forwarded-address trust only through a target-owned ingress policy.")
    require_bool_ready(data, "auth.rate_limiting.local_tests_passed")
    if get(data, "auth.secrets.committed_secret_values") is not False:
        block("auth.secrets.committed_secret_values", "secret values must not be committed", "Keep Cognito secrets and provider credentials in the target secret store or environment.")

    validation_location = 'blockers'
    blocked_paths = blocker_paths(data)
    if status == "blocked":
        if not blocked_paths:
            block("blockers", "blocked manifest needs at least one blocker", "Add explicit blocking evidence gaps.")
        validate_blocked_coverage(data, blocked_paths)
    elif blocked_paths:
        block("blockers", "ready manifest must not carry blockers", "Remove blockers only after all proof fields are ready.")

    if status == "ready":
        try:
            spec=importlib.util.spec_from_file_location('shell_release_evidence',ROOT/'scripts/04.deploy/verify-platform-shell-deploy-readiness/release_evidence.py')
            evidence=importlib.util.module_from_spec(spec);spec.loader.exec_module(evidence)
            evidence.validate_ready(data,root=rehearsal_root or ROOT,evidence_class='simulated' if rehearsal_root else 'live')
        except Exception as error:
            code=str(error) if 'evidence' in locals() and isinstance(error,getattr(evidence,'ReleaseEvidenceError',())) else 'shell-release-evidence-unavailable'
            block('acceptance',code,'Collect current runtime proof, retain immutable candidate receipts and promote with the generic release-succession command.')
        for path in REQUIRED_BLOCKED_PATHS:
            if is_pending(get(data, path)):
                block(path, "ready manifest contains unresolved deploy proof", f"Resolve `{path}` before setting status ready.")
        for path in (
            "source.commit_sha",
            "github.commit_sha",
            "artifacts.source_commit_sha",
        ):
            require_string(data, path, pattern=r"[0-9a-f]{40}")
        require_string(data, "source.workflow_path", pattern=r"\.github/workflows/[^/]+\.ya?ml")
        require_string(data, "source.workflow_run_id")
        for path in (
            "artifacts.image.image_digest",
            "artifacts.image.base_image_digest",
        ):
            require_string(data, path, pattern=r"sha256:[0-9a-f]{64}")
        require_string(data, "cloud.account_id", pattern=r"[0-9]{12}")
        require_string(data, "cloud.region", pattern=r"[a-z]{2}-[a-z]+-[0-9]")
        require_string(data, "aws.account_id", pattern=r"[0-9]{12}")
        require_string(data, "aws.region", pattern=r"[a-z]{2}-[a-z]+-[0-9]")
        for path in (
            "github.environment.protection_rules.required_reviewers",
            "github.environment.protection_rules.deployment_branch_policy",
            "github.environment.protection_rules.prevent_self_review",
            "github.oidc.trust_scoped_to_repository",
            "github.oidc.trust_scoped_to_ref",
            "github.oidc.workflow_has_id_token_permission",
        ):
            require_bool_ready(data, path)
        require_string(data, "auth.token_validation.issuer", pattern=r"https://cognito-idp\.[a-z]{2}-[a-z]+-[0-9]\.amazonaws\.com/[a-z]{2}-[a-z]+-[0-9]_[A-Za-z0-9]+")
        require_string(data, "auth.token_validation.jwks_uri", pattern=r"https://cognito-idp\.[a-z]{2}-[a-z]+-[0-9]\.amazonaws\.com/[a-z]{2}-[a-z]+-[0-9]_[A-Za-z0-9]+/\.well-known/jwks\.json")
        require_string(data, "auth.token_validation.app_client_id")
        require_string(data, "auth.permission_mapping.declared_app_permissions_source")
        if is_pending(get(data, "auth.cors.allowed_origins")):
            block("auth.cors.allowed_origins", "ready public targets need a concrete CORS allowlist", "Record one or more allowed origins before public deployment.")
        for path in (
            "auth.rate_limiting.shared_adapter.status",
            "auth.rate_limiting.trusted_ingress_client_address_policy.status",
            "auth.rate_limiting.target_transport_limits.status",
            "auth.rate_limiting.edge_protection.status",
        ):
            if get(data, path) != "implemented":
                block(path, "ready public targets require implemented rate-limit and ingress protection", "Select and prove the target-specific shared limiter, ingress address policy, transport limits, and edge protection before setting readiness to ready.")
        require_string(data, "auth.secrets.source")
    else:
        validation_location = 'proof.image_smoke'
        if get(data, "proof.image_smoke") != "passed-local":
            warn("proof.image_smoke", "local image smoke proof is not recorded as passed-local")
        validation_location = 'proof.local_runtime_smoke'
        if get(data, "proof.local_runtime_smoke") not in {"passed-server-health-only", "passed-product-smoke-local"}:
            warn("proof.local_runtime_smoke", "local runtime smoke proof is not recorded as passed locally")


try:
    manifest = load_manifest(manifest_path)
except Exception:
    print("ERROR: readiness-manifest-read-or-parse-failed", file=sys.stderr)
    sys.exit(2)

if allow_blocked and caller_intent not in ALLOWED_BLOCKED_CALLER_INTENTS:
    print("ERROR: --caller-intent must be planning or explanation when --allow-blocked is used.", file=sys.stderr)
    sys.exit(2)

if record_compatibility:
    if allow_blocked or caller_intent:
        print("ERROR: rollback compatibility cannot use a planning override",file=sys.stderr);sys.exit(2)
    try:
        spec=importlib.util.spec_from_file_location('shell_release_evidence',ROOT/'scripts/04.deploy/verify-platform-shell-deploy-readiness/release_evidence.py')
        evidence=importlib.util.module_from_spec(spec);spec.loader.exec_module(evidence)
        facts=evidence.write_compatibility_from_history(manifest,record_compatibility,root=rehearsal_root or ROOT,evidence_class='simulated' if rehearsal_root else 'live')
        print(json.dumps({'schema':'deploy/platform-shell-rollback-compatibility-report/v1','verdict':'recorded','evidence_class':'simulated' if rehearsal_root else 'live','facts':facts},sort_keys=True));sys.exit(0)
    except Exception as error:
        code=str(error) if 'evidence' in globals() and isinstance(error,getattr(evidence,'ReleaseEvidenceError',())) else 'shell-release-compatibility-unavailable'
        print(json.dumps({'schema':'deploy/platform-shell-rollback-compatibility-report/v1','verdict':'blocked','findings':[{'code':code}]}));sys.exit(1)

validation_unavailable = False
validation_location = 'manifest'
try:
    validate(manifest)
except (OSError, ValueError, TypeError, AttributeError, KeyError, IndexError, yaml.YAMLError):
    validation_unavailable = True
    block(validation_location, 'readiness-validation-observation-unavailable', 'Inspect the declared manifest and referenced local proof without changing deployment state.')

# Reviewed report values only; this projection never participates in admission.
PROOF_COUNT = ('nonnegative-integer',)
PROOF_DURATION = ('nonnegative-duration',)
PROOF_UTC_DATE = ('utc-calendar-date',)
PROOF_SOURCE_SHA = ('source-sha40',)
PROOF_DECIMAL_ID = ('decimal-id',)
PROOF_GITHUB_RUN_URL = ('github-run-url',)
PROOF_REPORT_FIELDS = {
    "static_validation": "passed-local",
    "policy_checks": "passed-local",
    "generated_output_review": "public-tls-repair-executed-and-externally-verified-2026-09-06",
    "image_smoke": "passed-local",
    "compiled_runtime_payload": "passed-local-2026-09-06",
    "local_runtime_smoke": "passed-product-smoke-local",
    "aws_read_only_inspection": "container-insights-enhanced-five-platform-alarms-ok-and-both-stacks-update-complete-2026-09-22",
    "deployment_smoke": "public-livez-200-protected-401-and-correctly-scoped-200-and-cloudwatch-otel-counter-histogram-query-proven-2026-09-22",
    "controlled_smoke_command": "implemented-and-locally-validated-2026-09-22",
    "public_boundary": {
        "status": "deployed-and-proven",
        "executed_on_utc": PROOF_UTC_DATE,
        "rate_limit_429": {
            "result": "passed",
            "attempted_request_count": PROOF_COUNT,
            "allowed_request_count": PROOF_COUNT,
            "first_429_request": PROOF_COUNT,
            "final_status": PROOF_COUNT,
            "total_duration_ms": PROOF_DURATION,
        },
        "waf_routing_and_ingress": {
            "result": "passed",
            "http_status": PROOF_COUNT,
            "duration_ms": PROOF_DURATION,
            "host_rule_priority": PROOF_COUNT,
        },
        "retained_evidence": "aggregate-status-count-duration-and-rule-priority-only-no-address-response-body-header-or-provider-payload",
    },
    "worker_consumer_and_metric_observation": {
        "status": "deployed-and-proven",
        "executed_on_utc": PROOF_UTC_DATE,
        "command": "npm run platform:shell:worker-smoke -- --execute --approve-live-worker-smoke",
        "result": "passed",
        "worker_task_definition_revision": PROOF_DECIMAL_ID,
        "duration_ms": PROOF_DURATION,
        "message_count": PROOF_COUNT,
        "inter_message_wait_seconds": PROOF_DURATION,
        "metric_export_settlement_wait_seconds": PROOF_DURATION,
        "metric_coverage": "observed",
        "post_proof_state": "worker-desired-and-running-zero-source-and-dead-letter-queues-empty",
        "retained_evidence": "safe-status-count-duration-task-revision-and-verdict-only-no-message-body-id-receipt-queue-url-or-provider-payload",
    },
    "rollback_proof": "collector-receiver-mismatch-baseline-telemetry-recovery-and-operator-alert-receipt-proven-2026-09-22",
    "exporter_loss_rehearsal": {
        "status": "live-proven-with-operator-alert-receipt",
        "source_commit_sha": PROOF_SOURCE_SHA,
        "baseline_task_definition_revision": PROOF_DECIMAL_ID,
        "disposable_fault_task_definition_revision": PROOF_DECIMAL_ID,
        "fault_boundary": "application-fixed-4318-collector-receiver-only-4319",
        "fault_smoke": {
            "github_run_id": PROOF_DECIMAL_ID,
            "github_run_url": PROOF_GITHUB_RUN_URL,
            "result": "passed",
            "http_status": PROOF_COUNT,
            "duration_ms": PROOF_DURATION,
        },
        "isolated_coverage": {
            "github_run_id": PROOF_DECIMAL_ID,
            "github_run_url": PROOF_GITHUB_RUN_URL,
            "result": "expected-failure",
            "metric_coverage": "missing",
            "affected_slo_confidence": "insufficient-confidence",
            "alert_publish_path": "completed-without-operator-receipt-claim",
        },
        "recovery": {
            "restored_task_definition_revision": PROOF_DECIMAL_ID,
            "baseline_smoke": {
                "github_run_id": PROOF_DECIMAL_ID,
                "github_run_url": PROOF_GITHUB_RUN_URL,
                "result": "passed",
                "http_status": PROOF_COUNT,
                "duration_ms": PROOF_DURATION,
            },
            "counter_advancing_smoke": {
                "github_run_id": PROOF_DECIMAL_ID,
                "github_run_url": PROOF_GITHUB_RUN_URL,
                "result": "passed",
                "http_status": PROOF_COUNT,
                "duration_ms": PROOF_DURATION,
            },
            "coverage_result": "observed",
            "coverage_execution": "governed-local-read-only-query-after-refreshed-sso",
            "counter_semantics": "first-fresh-task-request-establishes-a-cumulative-baseline-second-request-advances-it-for-promql-increase",
        },
        "two_point_synthetic_workflow": {
            "source_commit_sha": PROOF_SOURCE_SHA,
            "github_run_id": PROOF_DECIMAL_ID,
            "github_run_url": PROOF_GITHUB_RUN_URL,
            "result": "passed",
            "request_count": PROOF_COUNT,
            "inter_request_wait_seconds": PROOF_DURATION,
            "metric_coverage": "observed",
            "affected_slo_confidence": "not-determined",
            "coverage_execution": "governed-local-read-only-query-after-five-minute-arrival-grace",
            "meaning": "proves-the-main-only-workflow-establishes-and-advances-the-cumulative-counter-not-clock-trigger",
        },
        "operator_alert_receipt": {
            "status": "confirmed-by-operator",
            "confirmed_on_utc": PROOF_UTC_DATE,
            "event": "declared-metric-coverage-missing-insufficient-confidence",
            "retained_evidence": "human-confirmation-only-no-email-address-subscription-identifier-link-or-message-content",
        },
        "retained_evidence_policy": "no-secrets-tokens-headers-request-bodies-response-bodies-or-raw-provider-responses",
    },
}
PROOF_ALTERNATIVES = {
    "static_validation": {"passed-local"}, "policy_checks": {"passed", "passed-local"},
    "generated_output_review": {"passed"}, "image_smoke": {"passed-local"},
    "local_runtime_smoke": {"passed-server-health-only", "passed-product-smoke-local"},
    "aws_read_only_inspection": {"passed"}, "deployment_smoke": {"passed"}, "rollback_proof": {"passed"},
}


def project_proof(value: Any, rule: Any, field: str = "") -> Any:
    if isinstance(rule, dict):
        if not isinstance(value, dict): return None
        return {key: project_proof(value[key], child_rule, key) for key, child_rule in rule.items() if key in value}
    if rule is PROOF_COUNT:
        return value if type(value) is int and 0 <= value <= 9007199254740991 else None
    if rule is PROOF_DURATION:
        return value if type(value) in (int, float) and 0 <= value <= 9007199254740991 and math.isfinite(value) else None
    if isinstance(value, str):
        if rule is PROOF_UTC_DATE:
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                try: date.fromisoformat(value); return value
                except ValueError: pass
            return None
        if rule is PROOF_SOURCE_SHA: return value if re.fullmatch(r"[a-f0-9]{40}", value) else None
        if rule is PROOF_DECIMAL_ID: return value if re.fullmatch(r"[0-9]{1,20}", value) else None
        if rule is PROOF_GITHUB_RUN_URL: return value if re.fullmatch(r"https://github\.com/gordonrose/entity-builder-harness/actions/runs/[0-9]{1,20}", value) else None
        if value == rule or value in PENDING_VALUES or value in PROOF_ALTERNATIVES.get(field, ()): return value
    return None


def selected(value: Any, *allowed: str) -> str | None:
    return value if isinstance(value, str) and (value in allowed or value in PENDING_VALUES) else None


def report_manifest_path() -> str | None:
    # Retain actual repository artifact identity, not rejected caller text.
    try:
        resolved = manifest_path.resolve()
        if resolved.is_relative_to(ROOT.resolve()) and resolved.is_file():
            return resolved.relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError): pass
    return None

status = "ready" if not blocking_gaps and manifest.get("status") == "ready" else "blocked"
ok = status == "ready"
exit_overridden = bool(allow_blocked and status == "blocked" and not validation_unavailable)
report = {
    "schema": REPORT_SCHEMA,
    "evidence_class": "simulated" if rehearsal_root else "live",
    "ok": ok,
    "status": status,
    "caller_intent": selected(caller_intent, 'planning', 'explanation') or None,
    "exit_overridden_for_planning": exit_overridden,
    "manifest": report_manifest_path(),
    "summary": {
        "target": {
            "client": selected(get(manifest, "client.id"), "kanbien"),
            "environment": selected(get(manifest, "environment.id"), "staging"),
            "source_provider": selected(get(manifest, "source.provider"), "github"),
            "source_repository": selected(get(manifest, "source.repository"), "gordonrose/entity-builder-harness", "owner/entity-builder-harness"),
            "cloud_provider": selected(get(manifest, "cloud.provider"), "aws"),
        },
        "deployment": {
            "service_id": selected(get(manifest, "deployment.service_id"), "platform-shell"),
            "environment": selected(get(manifest, "deployment.environment"), "staging"),
            "runtime_target": selected(get(manifest, "deployment.runtime_target"), "aws.ecs-fargate.platform-shell-staging"),
            "mutation_authorized": get(manifest, "deployment.mutation_authorized") if type(get(manifest, "deployment.mutation_authorized")) is bool else None,
        },
        "runtime": {
            "provider": selected(get(manifest, "runtime.provider"), "aws"),
            "family": selected(get(manifest, "runtime.family"), "ecs-fargate"),
            "adapter": selected(get(manifest, "runtime.adapter"), "platform/adapters/aws/runtime/ecs-fargate/"),
            "server_health": {key: selected(get(manifest, 'runtime.server.health.' + key), expected) for key, expected in (('liveness', '/livez'), ('readiness', '/readyz'))} if isinstance(get(manifest, 'runtime.server.health'), dict) else None,
            "worker_status": selected(get(manifest, "runtime.worker.status"), "ready"),
        },
        "proof": project_proof(manifest.get("proof", {}), PROOF_REPORT_FIELDS),
        "blocker_count": len(manifest.get("blockers") or []) if isinstance(manifest.get("blockers") or [], (list, dict, str)) else None,
    },
    "blocking_gaps": blocking_gaps,
    "warnings": warnings,
}

if emit_json:
    print(json.dumps(report, indent=2, sort_keys=True))
else:
    print(f"Platform shell deploy readiness: {status}")
    print(f"Manifest: {report['manifest'] or 'unavailable'}")
    print(f"Runtime family: {report['summary']['runtime']['family'] or 'unavailable'}")
    print(f"Blockers: {report['summary']['blocker_count']}")
    if blocking_gaps:
        print("Blocking gaps:")
        for gap in blocking_gaps:
            print(f"- {gap['path']}: {gap['message']}")
    if exit_overridden:
        print(f"Blocked exit overridden for caller intent: {report['caller_intent']}")

if ok or exit_overridden:
    sys.exit(0)
sys.exit(1)
PY
