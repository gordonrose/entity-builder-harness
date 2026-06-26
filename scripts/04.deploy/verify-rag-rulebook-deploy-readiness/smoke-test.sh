#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-rag-rulebook-deploy-readiness.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#     - agentic
#     - sre
#   kind: script
#   purpose: Smoke test the RAG/rulebook deploy-readiness verification command.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: deploy.script.verify-rag-rulebook-deploy-readiness
#       path: scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

VALID="$TMP_DIR/valid.yml"
INVALID="$TMP_DIR/invalid.yml"
READY_REPORT="$TMP_DIR/ready.json"
BLOCKED_REPORT="$TMP_DIR/blocked.json"

cat > "$VALID" <<'YAML'
schema: deploy/rag-rulebook-readiness-manifest/v1
deployment:
  service_id: rag-rulebook-mcp
  environment: staging
  runtime_target: aws.app-runner.rag-rulebook-staging
github:
  repository: owner/entity-builder-harness-001
  source_policy: remote-main
  ref: refs/heads/main
  commit_sha: 0123456789abcdef0123456789abcdef01234567
  workflow_path: .github/workflows/deploy-rag-rulebook-service.yml
  workflow_name: Deploy RAG Rulebook Service
  trigger: workflow_dispatch
  environment:
    name: staging
    protection_rules:
      required_reviewers: true
      deployment_branch_policy: true
      prevent_self_review: true
  oidc:
    role_arn: arn:aws:iam::123456789012:role/github-rag-rulebook-deploy
    audience: sts.amazonaws.com
    subject_condition: repo:owner/entity-builder-harness-001:environment:staging
    repository_condition: owner/entity-builder-harness-001
    ref_condition: refs/heads/main
    environment_condition: staging
    trust_scoped_to_repository: true
    trust_scoped_to_ref: true
    workflow_has_id_token_permission: true
  artifact_provenance:
    attestation_required: true
    immutable_artifact_required: true
  deployment_history_required: true
artifacts:
  source_commit_sha: 0123456789abcdef0123456789abcdef01234567
  image_digest: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  corpus_package_version: corpus.02.rag-rulebook@0123456789abcdef0123456789abcdef01234567
  rulebook_index_sha: sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  chunk_set_sha: sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
aws:
  account_id: "123456789012"
  region: eu-west-1
  runtime_family: app-runner
  service_name: rag-rulebook-staging
  iam_role_name: github-rag-rulebook-deploy
  network_boundary: private-ingress-vpc-connector
  secret_store: aws-secrets-manager
  health_check: /healthz
  rollback_target: previous-app-runner-service-version
  app_runner:
    service_arn: arn:aws:apprunner:eu-west-1:123456789012:service/rag-rulebook-staging/0123456789abcdef0123456789abcdef
    auto_scaling_configuration_arn: arn:aws:apprunner:eu-west-1:123456789012:autoscalingconfiguration/rag-rulebook-staging/1/0123456789abcdef0123456789abcdef
mcp:
  spec_version: "2025-11-25"
  transport: streamable-http
  authentication_model: signed-internal-client
  authorization_boundary: read-only-context-query
  audit_log: cloudwatch-log-group:/aws/rag-rulebook/mcp
  exposed_capabilities:
    - resources.read
    - prompts.read
    - context.query
operations:
  owner: platform
  escalation_path: platform-on-call
  budget_name: rag-rulebook-staging-budget
  quotas_checked: true
  rate_limit: 60rpm
  concurrency_limit: "10"
  token_budget_limit: "20000"
  throttle_strategy: return-429-with-retry-after
  rollback_runbook: .agentic/aws/workflows/deploy-rag-rulebook-service.md#rollback
  disablement_runbook: .agentic/aws/workflows/deploy-rag-rulebook-service.md#disablement
checks:
  rag_rulebook_commit_gate_passed: true
  generated_sources_current: true
  local_runtime_built: true
  remote_main_sha_verified: true
  branch_protection_verified: true
  github_environment_protection_verified: true
  aws_target_verified: true
  rollback_verified: true
  health_check_verified: true
YAML

cat > "$INVALID" <<'YAML'
schema: deploy/rag-rulebook-readiness-manifest/v1
deployment:
  service_id: rag-rulebook-mcp
  environment: production
github:
  repository: owner/entity-builder-harness-001
  ref: refs/heads/main
  commit_sha: not-a-sha
  workflow_path: deploy.yml
  trigger: push
aws:
  runtime_family: elastic-beanstalk
mcp:
  spec_version: bad-version
  transport: stdio
  exposed_capabilities:
    - tools.deploy
YAML

bash scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh \
  --manifest "$VALID" \
  --json > "$READY_REPORT"

if bash scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh \
  --manifest "$INVALID" \
  --json > "$TMP_DIR/should-not-pass.json"; then
  echo "ERROR: invalid manifest unexpectedly passed." >&2
  exit 1
fi

if bash scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh \
  --manifest "$INVALID" \
  --allow-blocked \
  --json > "$TMP_DIR/allow-blocked-without-intent.json" 2> "$TMP_DIR/allow-blocked-without-intent.err"; then
  echo "ERROR: --allow-blocked passed without --caller-intent." >&2
  exit 1
fi

bash scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh \
  --manifest "$INVALID" \
  --allow-blocked \
  --caller-intent planning \
  --json > "$BLOCKED_REPORT"

python3 - "$READY_REPORT" "$BLOCKED_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

ready = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
blocked = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

assert ready["schema"] == "deploy/rag-rulebook-readiness-report/v1"
assert ready["ok"] is True
assert ready["status"] == "ready"
assert ready["exit_overridden_for_planning"] is False
assert ready["blocking_gaps"] == []
assert ready["summary"]["github"]["source_policy"] == "remote-main"
assert ready["summary"]["github"]["ref"] == "refs/heads/main"
assert ready["summary"]["github"]["workflow_path"] == ".github/workflows/deploy-rag-rulebook-service.yml"
assert ready["summary"]["aws"]["runtime_family"] == "app-runner"

assert blocked["ok"] is False
assert blocked["status"] == "blocked"
assert blocked["caller_intent"] == "planning"
assert blocked["exit_overridden_for_planning"] is True
gap_ids = {item["id"] for item in blocked["blocking_gaps"]}
assert "gap.deploy.readiness.github-commit-sha" in gap_ids
assert "gap.deploy.readiness.github-source-policy" in gap_ids
assert "gap.deploy.readiness.aws-runtime-family" in gap_ids
assert "gap.deploy.readiness.mcp-spec-version" in gap_ids
assert "gap.deploy.readiness.mcp-transport" in gap_ids
assert "gap.deploy.readiness.mcp-exposed-capabilities" in gap_ids
PY

echo "RAG/rulebook deploy-readiness verification smoke test passed."
