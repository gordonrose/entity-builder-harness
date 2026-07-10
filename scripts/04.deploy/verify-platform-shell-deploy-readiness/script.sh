#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-deploy-readiness
#   version: 1
#   status: active
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
#   used_by:
#     - id: deploy.script.verify-platform-shell-deploy-readiness.readme
#       path: scripts/04.deploy/verify-platform-shell-deploy-readiness/README.md
#     - id: deploy.script.verify-platform-shell-deploy-readiness.smoke-test
#       path: scripts/04.deploy/verify-platform-shell-deploy-readiness/smoke-test.sh
#     - id: infra.04-deploy.03-product.environments.staging.deploy-readiness
#       path: infra/04.deploy/03.product/environments/staging/deploy-readiness.yml

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MANIFEST=""
JSON=false
ALLOW_BLOCKED=false
CALLER_INTENT=""

usage() {
  cat <<'EOF'
Usage:
  verify-platform-shell-deploy-readiness/script.sh --manifest <path> [--json]
  verify-platform-shell-deploy-readiness/script.sh --manifest <path> --allow-blocked --caller-intent <planning|explanation> [--json]

Validates a deploy-readiness manifest for the product platform shell.
The command is read-only and fails closed when required deploy proof is missing.
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
      echo "ERROR: unknown argument: $1" >&2
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

python3 - "$MANIFEST" "$JSON" "$ALLOW_BLOCKED" "$CALLER_INTENT" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - surfaced in shell usage
    print(f"ERROR: PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

ROOT = Path.cwd()
manifest_path = Path(sys.argv[1])
emit_json = sys.argv[2] == "true"
allow_blocked = sys.argv[3] == "true"
caller_intent = sys.argv[4]

SCHEMA = "deploy/platform-shell-readiness-manifest/v1"
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
]


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"manifest does not exist: {path}")
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
        block(path, f"value has invalid shape: {value}", f"Set `{path}` to the governed expected format.")


def require_bool_ready(data: dict[str, Any], path: str) -> None:
    value = get(data, path)
    if value is not True:
        block(path, "required boolean proof is not true", f"Set `{path}: true` only after proof exists.")


def require_file(data: dict[str, Any], path: str) -> None:
    value = get(data, path)
    if not isinstance(value, str) or is_pending(value):
        block(path, "required local file path is missing or pending", f"Set `{path}` to a repo-relative file path.")
        return
    target = ROOT / value
    if not target.is_file():
        block(path, f"referenced file does not exist: {value}", f"Create the referenced file or update `{path}`.")


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
    if data.get("schema") != SCHEMA:
        block("schema", "manifest schema is missing or unsupported", f"Use schema `{SCHEMA}`.")

    status = data.get("status")
    if status not in {"ready", "blocked"}:
        block("status", "status must be ready or blocked", "Set `status` to `ready` or `blocked`.")

    require_string(data, "deployment.service_id")
    if get(data, "deployment.service_id") != "platform-shell":
        block("deployment.service_id", "service_id must be platform-shell", "Use the product platform shell service id.")
    require_string(data, "deployment.environment")
    require_string(data, "deployment.runtime_target")
    if get(data, "deployment.mutation_authorized") is not False:
        block(
            "deployment.mutation_authorized",
            "readiness proof must not authorize deployment mutation",
            "Keep mutation authorization in a separate governed execution workflow.",
        )

    require_string(data, "github.repository", pattern=r"[^/\s]+/[^/\s]+")
    require_string(data, "github.ref")
    require_string(data, "github.oidc.audience")
    require_string(data, "github.oidc.repository_condition")
    require_string(data, "github.oidc.ref_condition")
    require_string(data, "github.oidc.environment_condition")

    require_string(data, "runtime.family")
    if get(data, "runtime.family") != "ecs-fargate":
        block(
            "runtime.family",
            "Milestone 9 selected ecs-fargate for the first platform shell planning target",
            "Use `ecs-fargate` or update the governed runtime-family decision first.",
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

    blocked_paths = blocker_paths(data)
    if status == "blocked":
        if not blocked_paths:
            block("blockers", "blocked manifest needs at least one blocker", "Add explicit blocking evidence gaps.")
        validate_blocked_coverage(data, blocked_paths)
    elif blocked_paths:
        block("blockers", "ready manifest must not carry blockers", "Remove blockers only after all proof fields are ready.")

    if status == "ready":
        for path in REQUIRED_BLOCKED_PATHS:
            if is_pending(get(data, path)):
                block(path, "ready manifest contains unresolved deploy proof", f"Resolve `{path}` before setting status ready.")
        for path in (
            "github.commit_sha",
            "artifacts.source_commit_sha",
        ):
            require_string(data, path, pattern=r"[0-9a-f]{40}")
        for path in (
            "artifacts.image.image_digest",
            "artifacts.image.base_image_digest",
        ):
            require_string(data, path, pattern=r"sha256:[0-9a-f]{64}")
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
    else:
        if get(data, "proof.image_smoke") != "passed-local":
            warn("proof.image_smoke", "local image smoke proof is not recorded as passed-local")
        if get(data, "proof.local_runtime_smoke") != "passed-server-health-only":
            warn("proof.local_runtime_smoke", "local runtime smoke proof is not recorded as passed-server-health-only")


try:
    manifest = load_manifest(manifest_path)
except Exception as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    sys.exit(2)

if allow_blocked and caller_intent not in ALLOWED_BLOCKED_CALLER_INTENTS:
    print("ERROR: --caller-intent must be planning or explanation when --allow-blocked is used.", file=sys.stderr)
    sys.exit(2)

validate(manifest)

status = "ready" if not blocking_gaps and manifest.get("status") == "ready" else "blocked"
ok = status == "ready"
exit_overridden = bool(allow_blocked and status == "blocked")
report = {
    "schema": REPORT_SCHEMA,
    "ok": ok,
    "status": status,
    "caller_intent": caller_intent or None,
    "exit_overridden_for_planning": exit_overridden,
    "manifest": manifest_path.as_posix(),
    "summary": {
        "deployment": {
            "service_id": get(manifest, "deployment.service_id"),
            "environment": get(manifest, "deployment.environment"),
            "runtime_target": get(manifest, "deployment.runtime_target"),
            "mutation_authorized": get(manifest, "deployment.mutation_authorized"),
        },
        "runtime": {
            "family": get(manifest, "runtime.family"),
            "server_health": get(manifest, "runtime.server.health"),
            "worker_status": get(manifest, "runtime.worker.status"),
        },
        "proof": manifest.get("proof", {}),
        "blocker_count": len(manifest.get("blockers") or []),
    },
    "blocking_gaps": blocking_gaps,
    "warnings": warnings,
}

if emit_json:
    print(json.dumps(report, indent=2, sort_keys=True))
else:
    print(f"Platform shell deploy readiness: {status}")
    print(f"Manifest: {manifest_path.as_posix()}")
    print(f"Runtime family: {get(manifest, 'runtime.family')}")
    print(f"Blockers: {len(manifest.get('blockers') or [])}")
    if blocking_gaps:
        print("Blocking gaps:")
        for gap in blocking_gaps:
            print(f"- {gap['path']}: {gap['message']}")
    if exit_overridden:
        print(f"Blocked exit overridden for caller intent: {caller_intent}")

if ok or exit_overridden:
    sys.exit(0)
sys.exit(1)
PY
