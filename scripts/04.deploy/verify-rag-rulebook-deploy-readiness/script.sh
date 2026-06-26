#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-rag-rulebook-deploy-readiness
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#     - agentic
#     - sre
#   kind: script
#   purpose: Validate a RAG/rulebook GitHub-to-AWS deploy-readiness manifest without mutating GitHub or AWS.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: deploy.script.verify-rag-rulebook-deploy-readiness.readme
#       path: scripts/04.deploy/verify-rag-rulebook-deploy-readiness/README.md
#     - id: deploy.script.verify-rag-rulebook-deploy-readiness.smoke-test
#       path: scripts/04.deploy/verify-rag-rulebook-deploy-readiness/smoke-test.sh
#     - id: aws.workflows.deploy-rag-rulebook-service
#       path: .agentic/aws/workflows/deploy-rag-rulebook-service.md

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MANIFEST=""
JSON=false
ALLOW_BLOCKED=false
CALLER_INTENT=""

usage() {
  cat <<'EOF'
Usage:
  verify-rag-rulebook-deploy-readiness/script.sh --manifest <path> [--json]
  verify-rag-rulebook-deploy-readiness/script.sh --manifest <path> --allow-blocked --caller-intent <planning|explanation> [--json]

Validates a deploy-readiness manifest for the RAG/rulebook MCP service.
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

try:
    import yaml
except Exception as exc:  # pragma: no cover - surfaced in shell usage
    print(f"ERROR: PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

manifest_path = Path(sys.argv[1])
emit_json = sys.argv[2] == "true"
allow_blocked = sys.argv[3] == "true"
caller_intent = sys.argv[4]


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"manifest does not exist: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("manifest must be a YAML object")
    return data


def get(data: dict, dotted: str):
    current = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def slug(path: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")


blocking_gaps: list[dict[str, str]] = []
warnings: list[dict[str, str]] = []

ALLOWED_RUNTIME_FAMILIES = {"app-runner", "ecs-fargate", "lambda", "eks"}
ALLOWED_SOURCE_POLICIES = {"remote-main", "approved-release-tag"}
ALLOWED_MCP_SPEC_VERSIONS = {"2025-11-25"}
ALLOWED_MCP_TRANSPORTS = {"streamable-http"}
ALLOWED_BLOCKED_CALLER_INTENTS = {"planning", "explanation"}


def block(path: str, message: str, resolution: str) -> None:
    blocking_gaps.append(
        {
            "id": f"gap.deploy.readiness.{slug(path)}",
            "path": path,
            "message": message,
            "suggested_resolution": resolution,
        }
    )


def warn(path: str, message: str) -> None:
    warnings.append({"path": path, "message": message})


def require_string(data: dict, path: str, *, pattern: str | None = None, resolution: str | None = None) -> None:
    value = get(data, path)
    if not isinstance(value, str) or not value.strip():
        block(path, "required string is missing", resolution or f"Set `{path}` in the deploy-readiness manifest.")
        return
    if pattern and not re.fullmatch(pattern, value.strip()):
        block(path, f"value has invalid shape: {value}", resolution or f"Set `{path}` to the governed expected format.")


def require_true(data: dict, path: str, *, resolution: str | None = None) -> None:
    value = get(data, path)
    if value is not True:
        block(path, "required deploy-readiness proof is not true", resolution or f"Set `{path}: true` only after proof exists.")


def require_list(data: dict, path: str, *, min_count: int = 1, allowed: set[str] | None = None, banned: set[str] | None = None) -> None:
    value = get(data, path)
    if not isinstance(value, list) or len(value) < min_count:
        block(path, "required non-empty list is missing", f"Add at least {min_count} item(s) to `{path}`.")
        return
    for item in value:
        if not isinstance(item, str) or not item.strip():
            block(path, "list items must be non-empty strings", f"Use stable string values in `{path}`.")
            continue
        normalized = item.strip()
        if allowed and normalized not in allowed:
            block(path, f"unsupported capability: {normalized}", f"Use only allowed first-exposure capabilities: {sorted(allowed)}.")
        if banned and normalized in banned:
            block(path, f"banned first-exposure capability: {normalized}", "Keep first remote MCP exposure read-only.")


def validate(data: dict) -> None:
    if data.get("schema") != "deploy/rag-rulebook-readiness-manifest/v1":
        block(
            "schema",
            "manifest schema is missing or unsupported",
            "Use schema `deploy/rag-rulebook-readiness-manifest/v1`.",
        )

    require_string(data, "deployment.service_id")
    require_string(data, "deployment.environment")
    require_string(data, "deployment.runtime_target")
    require_string(data, "github.repository", pattern=r"[^/\s]+/[^/\s]+")
    require_string(data, "github.source_policy")
    require_string(data, "github.ref")
    require_string(data, "github.commit_sha", pattern=r"[0-9a-f]{40}")
    require_string(data, "github.workflow_path", pattern=r"\.github/workflows/[^/]+\.ya?ml")
    require_string(data, "github.workflow_name")
    require_string(data, "github.trigger")
    require_string(data, "github.environment.name")
    require_true(data, "github.environment.protection_rules.required_reviewers")
    require_true(data, "github.environment.protection_rules.deployment_branch_policy")
    require_true(data, "github.environment.protection_rules.prevent_self_review")
    require_string(data, "github.oidc.role_arn", pattern=r"arn:aws:iam::[0-9]{12}:role/.+")
    require_string(data, "github.oidc.audience")
    require_string(data, "github.oidc.subject_condition")
    require_string(data, "github.oidc.repository_condition")
    require_string(data, "github.oidc.ref_condition")
    require_string(data, "github.oidc.environment_condition")
    require_true(data, "github.oidc.trust_scoped_to_repository")
    require_true(data, "github.oidc.trust_scoped_to_ref")
    require_true(data, "github.oidc.workflow_has_id_token_permission")
    require_true(data, "github.artifact_provenance.attestation_required")
    require_true(data, "github.artifact_provenance.immutable_artifact_required")
    require_true(data, "github.deployment_history_required")

    require_string(data, "artifacts.source_commit_sha", pattern=r"[0-9a-f]{40}")
    require_string(data, "artifacts.image_digest", pattern=r"sha256:[0-9a-f]{64}")
    require_string(data, "artifacts.corpus_package_version")
    require_string(data, "artifacts.rulebook_index_sha")
    require_string(data, "artifacts.chunk_set_sha")

    require_string(data, "aws.account_id", pattern=r"[0-9]{12}")
    require_string(data, "aws.region", pattern=r"[a-z]{2}-[a-z]+-[0-9]")
    require_string(data, "aws.runtime_family")
    require_string(data, "aws.service_name")
    require_string(data, "aws.iam_role_name")
    require_string(data, "aws.network_boundary")
    require_string(data, "aws.secret_store")
    require_string(data, "aws.health_check")
    require_string(data, "aws.rollback_target")

    require_string(data, "mcp.spec_version")
    require_string(data, "mcp.transport")
    require_string(data, "mcp.authentication_model")
    require_string(data, "mcp.authorization_boundary")
    require_string(data, "mcp.audit_log")
    require_list(
        data,
        "mcp.exposed_capabilities",
        allowed={"resources.read", "prompts.read", "context.query"},
        banned={"tools.write", "tools.deploy", "tools.destructive"},
    )

    require_string(data, "operations.owner")
    require_string(data, "operations.escalation_path")
    require_string(data, "operations.budget_name")
    require_true(data, "operations.quotas_checked")
    require_string(data, "operations.rate_limit")
    require_string(data, "operations.concurrency_limit")
    require_string(data, "operations.token_budget_limit")
    require_string(data, "operations.throttle_strategy")
    require_string(data, "operations.rollback_runbook")
    require_string(data, "operations.disablement_runbook")

    require_true(data, "checks.rag_rulebook_commit_gate_passed")
    require_true(data, "checks.generated_sources_current")
    require_true(data, "checks.local_runtime_built")
    require_true(data, "checks.remote_main_sha_verified")
    require_true(data, "checks.branch_protection_verified")
    require_true(data, "checks.github_environment_protection_verified")
    require_true(data, "checks.aws_target_verified")
    require_true(data, "checks.rollback_verified")
    require_true(data, "checks.health_check_verified")

    source_sha = get(data, "artifacts.source_commit_sha")
    github_sha = get(data, "github.commit_sha")
    if isinstance(source_sha, str) and isinstance(github_sha, str) and source_sha != github_sha:
        block(
            "artifacts.source_commit_sha",
            "source commit SHA does not match GitHub deployment commit SHA",
            "Deploy the exact commit that produced the verified artifacts.",
        )

    if get(data, "deployment.environment") != get(data, "github.environment.name"):
        block(
            "deployment.environment",
            "deployment environment does not match GitHub environment name",
            "Use one environment identity across deployment and GitHub release control.",
        )

    source_policy = get(data, "github.source_policy")
    github_ref = get(data, "github.ref")
    if isinstance(source_policy, str) and source_policy not in ALLOWED_SOURCE_POLICIES:
        block(
            "github.source_policy",
            f"unsupported source policy: {source_policy}",
            f"Use one of the governed source policies: {sorted(ALLOWED_SOURCE_POLICIES)}.",
        )
    elif source_policy == "remote-main" and github_ref != "refs/heads/main":
        block(
            "github.ref",
            "remote-main source policy requires refs/heads/main",
            "Use github.ref: refs/heads/main when github.source_policy is remote-main.",
        )
    elif source_policy == "approved-release-tag" and (
        not isinstance(github_ref, str) or not re.fullmatch(r"refs/tags/v[0-9][A-Za-z0-9._-]*", github_ref)
    ):
        block(
            "github.ref",
            "approved-release-tag source policy requires an approved version tag ref",
            "Use a governed release tag shaped like refs/tags/v1.2.3 or return to remote-main deployment.",
        )

    repository = get(data, "github.repository")
    environment = get(data, "github.environment.name")
    subject_condition = get(data, "github.oidc.subject_condition")
    repository_condition = get(data, "github.oidc.repository_condition")
    ref_condition = get(data, "github.oidc.ref_condition")
    environment_condition = get(data, "github.oidc.environment_condition")
    audience = get(data, "github.oidc.audience")

    if audience != "sts.amazonaws.com":
        block(
            "github.oidc.audience",
            "GitHub-to-AWS OIDC audience must be sts.amazonaws.com",
            "Set github.oidc.audience to sts.amazonaws.com for AWS role assumption.",
        )
    if isinstance(repository, str) and isinstance(repository_condition, str) and repository_condition != repository:
        block(
            "github.oidc.repository_condition",
            "OIDC repository condition does not match the deploy repository",
            "Set github.oidc.repository_condition to the exact github.repository value.",
        )
    if isinstance(github_ref, str) and isinstance(ref_condition, str) and ref_condition != github_ref:
        block(
            "github.oidc.ref_condition",
            "OIDC ref condition does not match the deploy ref",
            "Set github.oidc.ref_condition to the exact github.ref value.",
        )
    if isinstance(environment, str) and isinstance(environment_condition, str) and environment_condition != environment:
        block(
            "github.oidc.environment_condition",
            "OIDC environment condition does not match the GitHub environment",
            "Set github.oidc.environment_condition to the exact github.environment.name value.",
        )
    if isinstance(repository, str) and isinstance(subject_condition, str):
        expected_prefix = f"repo:{repository}:"
        contains_environment = isinstance(environment, str) and f"environment:{environment}" in subject_condition
        contains_ref = isinstance(github_ref, str) and f"ref:{github_ref}" in subject_condition
        if not subject_condition.startswith(expected_prefix) or not (contains_environment or contains_ref):
            block(
                "github.oidc.subject_condition",
                "OIDC subject condition must bind to the deploy repository and environment or ref",
                "Use a GitHub OIDC subject condition such as repo:owner/repo:environment:staging or repo:owner/repo:ref:refs/heads/main.",
            )

    mcp_spec_version = get(data, "mcp.spec_version")
    if isinstance(mcp_spec_version, str) and mcp_spec_version not in ALLOWED_MCP_SPEC_VERSIONS:
        block(
            "mcp.spec_version",
            f"unsupported MCP specification version: {mcp_spec_version}",
            f"Use one of the governed MCP specification versions: {sorted(ALLOWED_MCP_SPEC_VERSIONS)}.",
        )

    mcp_transport = get(data, "mcp.transport")
    if isinstance(mcp_transport, str) and mcp_transport not in ALLOWED_MCP_TRANSPORTS:
        block(
            "mcp.transport",
            f"unsupported remote MCP transport: {mcp_transport}",
            f"Use one of the governed remote MCP transports: {sorted(ALLOWED_MCP_TRANSPORTS)}.",
        )

    runtime_family = get(data, "aws.runtime_family")
    if runtime_family == "undecided":
        block(
            "aws.runtime_family",
            "runtime family is undecided",
            "Select the governed AWS runtime family before deploy execution.",
        )
    elif isinstance(runtime_family, str) and runtime_family not in ALLOWED_RUNTIME_FAMILIES:
        block(
            "aws.runtime_family",
            f"unsupported runtime family: {runtime_family}",
            f"Use one of the governed runtime families: {sorted(ALLOWED_RUNTIME_FAMILIES)}.",
        )
    elif runtime_family == "app-runner":
        require_string(data, "aws.app_runner.service_arn", pattern=r"arn:aws:apprunner:[a-z]{2}-[a-z]+-[0-9]:[0-9]{12}:service/.+")
        require_string(data, "aws.app_runner.auto_scaling_configuration_arn", pattern=r"arn:aws:apprunner:[a-z]{2}-[a-z]+-[0-9]:[0-9]{12}:autoscalingconfiguration/.+")
    elif runtime_family == "ecs-fargate":
        require_string(data, "aws.ecs.cluster_arn", pattern=r"arn:aws:ecs:[a-z]{2}-[a-z]+-[0-9]:[0-9]{12}:cluster/.+")
        require_string(data, "aws.ecs.service_arn", pattern=r"arn:aws:ecs:[a-z]{2}-[a-z]+-[0-9]:[0-9]{12}:service/.+")
        require_string(data, "aws.ecs.task_definition_arn", pattern=r"arn:aws:ecs:[a-z]{2}-[a-z]+-[0-9]:[0-9]{12}:task-definition/.+")
        require_true(data, "aws.ecs.deployment_circuit_breaker_enabled")
    elif runtime_family == "lambda":
        require_string(data, "aws.lambda.function_arn", pattern=r"arn:aws:lambda:[a-z]{2}-[a-z]+-[0-9]:[0-9]{12}:function:.+")
        require_string(data, "aws.lambda.alias")
    elif runtime_family == "eks":
        require_string(data, "aws.eks.cluster_arn", pattern=r"arn:aws:eks:[a-z]{2}-[a-z]+-[0-9]:[0-9]{12}:cluster/.+")
        require_string(data, "aws.eks.namespace")
        require_string(data, "aws.eks.workload_name")

    if get(data, "deployment.environment") == "production" and get(data, "github.trigger") == "push":
        warn(
            "github.trigger",
            "production push-triggered deployment should be reviewed carefully; protected environment approval is mandatory",
        )


try:
    manifest = load_manifest(manifest_path)
except Exception as exc:
    report = {
        "schema": "deploy/rag-rulebook-readiness-report/v1",
        "ok": False,
        "status": "blocked",
        "caller_intent": caller_intent or None,
        "exit_overridden_for_planning": False,
        "manifest_path": str(manifest_path),
        "blocking_gaps": [
            {
                "id": "gap.deploy.readiness.manifest-load",
                "path": str(manifest_path),
                "message": str(exc),
                "suggested_resolution": "Provide a readable YAML deploy-readiness manifest.",
            }
        ],
        "warnings": [],
    }
else:
    validate(manifest)
    ok = not blocking_gaps
    exit_overridden_for_planning = (
        (not ok)
        and allow_blocked
        and caller_intent in ALLOWED_BLOCKED_CALLER_INTENTS
    )
    report = {
        "schema": "deploy/rag-rulebook-readiness-report/v1",
        "ok": ok,
        "status": "ready" if ok else "blocked",
        "caller_intent": caller_intent or None,
        "exit_overridden_for_planning": exit_overridden_for_planning,
        "manifest_path": str(manifest_path),
        "blocking_gaps": blocking_gaps,
        "warnings": warnings,
        "summary": {
            "deployment": manifest.get("deployment", {}),
            "github": {
                "repository": get(manifest, "github.repository"),
                "source_policy": get(manifest, "github.source_policy"),
                "ref": get(manifest, "github.ref"),
                "commit_sha": get(manifest, "github.commit_sha"),
                "workflow_path": get(manifest, "github.workflow_path"),
                "environment": get(manifest, "github.environment.name"),
            },
            "aws": {
                "account_id": get(manifest, "aws.account_id"),
                "region": get(manifest, "aws.region"),
                "runtime_family": get(manifest, "aws.runtime_family"),
                "service_name": get(manifest, "aws.service_name"),
            },
        },
    }

if emit_json:
    print(json.dumps(report, indent=2, sort_keys=True))
else:
    print(f"RAG/rulebook deploy readiness: {report['status']}")
    if report["blocking_gaps"]:
        print("Blocking gaps:")
        for gap in report["blocking_gaps"]:
            print(f"- {gap['id']}: {gap['message']} ({gap['path']})")
    if report["warnings"]:
        print("Warnings:")
        for item in report["warnings"]:
            print(f"- {item['path']}: {item['message']}")

if report["ok"]:
    sys.exit(0)
if allow_blocked and caller_intent in ALLOWED_BLOCKED_CALLER_INTENTS:
    sys.exit(0)
sys.exit(1)
PY
