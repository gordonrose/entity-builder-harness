#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-deploy-readiness.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#     - agentic
#     - sre
#   kind: script
#   purpose: Smoke test the platform shell deploy-readiness verification command.
#   portability:
#     class: internal
#     targets: []
#   effects:
#     - writes-files
#   used_by:
#     - id: deploy.script.verify-platform-shell-deploy-readiness
#       path: scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

VALID="$TMP_DIR/valid.yml"
INVALID="$TMP_DIR/invalid.yml"
READY_REPORT="$TMP_DIR/ready.json"
BLOCKED_REPORT="$TMP_DIR/blocked.json"

cat > "$VALID" <<'YAML'
schema: deploy/platform-shell-readiness-manifest/v1
status: ready
client:
  id: kanbien
  display_name: Kanbien
environment:
  id: staging
  class: staging
deployment:
  service_id: platform-shell
  environment: staging
  runtime_target: aws.ecs-fargate.platform-shell-staging
  source_policy: remote-main
  mutation_authorized: false
source:
  provider: github
  repository: owner/entity-builder-harness
  ref: refs/heads/main
  commit_sha: 0123456789abcdef0123456789abcdef01234567
  workflow_path: .github/workflows/deploy-platform-shell-staging.yml
  workflow_run_id: "1234567890"
github:
  repository: owner/entity-builder-harness
  source_policy: remote-main
  ref: refs/heads/main
  commit_sha: 0123456789abcdef0123456789abcdef01234567
  workflow_path: .github/workflows/deploy-platform-shell-staging.yml
  workflow_run_id: "1234567890"
  environment:
    name: staging
    protection_rules:
      required_reviewers: true
      deployment_branch_policy: true
      prevent_self_review: true
  oidc:
    role_arn: arn:aws:iam::123456789012:role/github-platform-shell-staging-deploy
    audience: sts.amazonaws.com
    subject_condition: repo:owner/entity-builder-harness:environment:staging
    repository_condition: owner/entity-builder-harness
    ref_condition: refs/heads/main
    environment_condition: staging
    trust_scoped_to_repository: true
    trust_scoped_to_ref: true
    workflow_has_id_token_permission: true
artifacts:
  source_commit_sha: 0123456789abcdef0123456789abcdef01234567
  image:
    dockerfile: infra/04.deploy/03.product/image/Dockerfile
    build_context: .
    local_smoke_script: scripts/04.deploy/smoke-test-platform-shell-image/script.sh
    local_smoke_passed: true
    image_digest: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    base_image_digest: sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    sbom: sbom://platform-shell/0123456789abcdef0123456789abcdef01234567
    vulnerability_scan: scan://platform-shell/0123456789abcdef0123456789abcdef01234567
    provenance_or_attestation: attest://platform-shell/0123456789abcdef0123456789abcdef01234567
runtime:
  provider: aws
  family: ecs-fargate
  adapter: platform/adapters/aws/runtime/ecs-fargate/
  decision: infra/04.deploy/03.product/aws-runtime-family.decision.yml
  server:
    health:
      liveness: /livez
      readiness: /readyz
    container_port: 3000
    task_definition: arn:aws:ecs:eu-west-1:123456789012:task-definition/platform-shell-server:1
    service: arn:aws:ecs:eu-west-1:123456789012:service/platform/platform-shell-server
  worker:
    status: ready
    task_definition: arn:aws:ecs:eu-west-1:123456789012:task-definition/platform-shell-worker:1
    service: arn:aws:ecs:eu-west-1:123456789012:service/platform/platform-shell-worker
    queue_adapter: platform/adapters/aws/queue/sqs/
auth:
  provider: cognito
  provider_decision: docs/aws/architecture/adrs/0002-select-cognito-for-platform-shell-auth.md
  token_validation:
    mode: jwt-jwks
    issuer: https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_EXAMPLE
    jwks_uri: https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_EXAMPLE/.well-known/jwks.json
    app_client_id: 1example23456789
    token_use: access
    validator: platform/security.createCognitoAccessTokenVerifier
    local_tests_passed: true
  permission_mapping:
    source: target-profile
    group_permissions_env: PLATFORM_AUTHZ_GROUP_PERMISSIONS
    scope_permissions_env: PLATFORM_AUTHZ_SCOPE_PERMISSIONS
    claim_permissions_env: PLATFORM_AUTHZ_CLAIM_PERMISSIONS
    validates_against_app_permissions: true
    declared_app_permissions_source: products/kanbien-platform/product.manifest.ts
  route_exposure:
    app_routes_default: authenticated
    unauthenticated_app_routes_denied_by_default: true
    protected_dummy_route:
      local_401_test: true
      local_403_test: true
      local_success_test: true
      deployment_smoke: passed
  health_exposure:
    livez: public
    readyz: authenticated
    reason: Liveness is minimal; readiness is authenticated for internet-facing targets.
  cors:
    allowlist_source: target-profile-env
    env: PLATFORM_CORS_ALLOWLIST
    allowed_origins:
      - https://staging.kanbien.example
  rate_limiting:
    keying: principal-token-or-forwarded-ip
    fallback: anonymous-local-only
    local_tests_passed: true
  secrets:
    source: aws-secrets-manager
    committed_secret_values: false
cloud:
  provider: aws
  account_id: "123456789012"
  profile_or_oidc_role: arn:aws:iam::123456789012:role/github-platform-shell-staging-deploy
  region: eu-west-1
aws:
  account_id: "123456789012"
  profile_or_oidc_role: arn:aws:iam::123456789012:role/github-platform-shell-staging-deploy
  region: eu-west-1
  cluster: arn:aws:ecs:eu-west-1:123456789012:cluster/platform
  vpc: vpc-0123456789abcdef0
  subnets:
    - subnet-0123456789abcdef0
    - subnet-11111111111111111
  security_groups:
    - sg-0123456789abcdef0
  alb: arn:aws:elasticloadbalancing:eu-west-1:123456789012:loadbalancer/app/platform/1234567890abcdef
  target_group: arn:aws:elasticloadbalancing:eu-west-1:123456789012:targetgroup/platform-shell/1234567890abcdef
  tls_certificate: arn:aws:acm:eu-west-1:123456789012:certificate/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
  dns_hostname: platform.example.com
  secret_store: aws-secrets-manager
  log_group: /aws/ecs/platform-shell
  alarms:
    - platform-shell-unhealthy-hosts
operations:
  owner: platform
  escalation_path: platform-on-call
  budget_name: platform-shell-staging-budget
  cost_limit: 25-usd-monthly
  rollback_target: previous-ecs-task-definition-and-image-digest
  rollback_authority: platform-on-call
  rollback_runbook: .agentic/aws/workflows/execute-approved-aws-change.md
proof:
  static_validation: passed-local
  policy_checks: passed
  generated_output_review: passed
  image_smoke: passed-local
  local_runtime_smoke: passed-server-health-only
  aws_read_only_inspection: passed
  deployment_smoke: passed
  rollback_proof: passed
blockers: []
YAML

cat > "$INVALID" <<'YAML'
schema: deploy/platform-shell-readiness-manifest/v1
status: blocked
deployment:
  service_id: platform-shell
  environment: staging
  runtime_target: aws.ecs-fargate.platform-shell-staging
  source_policy: local-planning
  mutation_authorized: false
github:
  repository: owner/entity-builder-harness
  ref: refs/heads/main
  oidc:
    audience: sts.amazonaws.com
    repository_condition: owner/entity-builder-harness
    ref_condition: refs/heads/main
    environment_condition: staging
artifacts:
  image:
    dockerfile: infra/04.deploy/03.product/image/Dockerfile
    build_context: .
    local_smoke_script: scripts/04.deploy/smoke-test-platform-shell-image/script.sh
    local_smoke_passed: true
runtime:
  provider: aws
  family: ecs-fargate
  adapter: platform/adapters/aws/runtime/ecs-fargate/
  decision: infra/04.deploy/03.product/aws-runtime-family.decision.yml
  server:
    health:
      liveness: /livez
      readiness: /readyz
    container_port: 3000
proof:
  image_smoke: passed-local
  local_runtime_smoke: passed-server-health-only
blockers:
  - id: incomplete
    severity: blocking
    path: aws.account_id
    reason: Missing AWS target.
    resolution: Record the AWS target.
YAML

bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
  --manifest "$VALID" \
  --json > "$READY_REPORT"

if bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
  --manifest "$INVALID" \
  --json > "$TMP_DIR/should-not-pass.json"; then
  echo "ERROR: invalid manifest unexpectedly passed." >&2
  exit 1
fi

if bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
  --manifest "$INVALID" \
  --allow-blocked \
  --json > "$TMP_DIR/allow-blocked-without-intent.json" 2> "$TMP_DIR/allow-blocked-without-intent.err"; then
  echo "ERROR: --allow-blocked passed without --caller-intent." >&2
  exit 1
fi

bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
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

assert ready["schema"] == "deploy/platform-shell-readiness-report/v1"
assert ready["ok"] is True
assert ready["status"] == "ready"
assert ready["exit_overridden_for_planning"] is False
assert ready["blocking_gaps"] == []
assert ready["summary"]["target"]["client"] == "kanbien"
assert ready["summary"]["target"]["environment"] == "staging"
assert ready["summary"]["target"]["source_provider"] == "github"
assert ready["summary"]["target"]["cloud_provider"] == "aws"
assert ready["summary"]["deployment"]["service_id"] == "platform-shell"
assert ready["summary"]["runtime"]["provider"] == "aws"
assert ready["summary"]["runtime"]["family"] == "ecs-fargate"
assert ready["summary"]["runtime"]["adapter"] == "platform/adapters/aws/runtime/ecs-fargate/"
assert ready["summary"]["runtime"]["server_health"]["liveness"] == "/livez"

assert blocked["ok"] is False
assert blocked["status"] == "blocked"
assert blocked["caller_intent"] == "planning"
assert blocked["exit_overridden_for_planning"] is True
gap_ids = {item["id"] for item in blocked["blocking_gaps"]}
assert "gap.deploy.platform-shell-readiness.client-id" in gap_ids
assert "gap.deploy.platform-shell-readiness.environment-id" in gap_ids
assert "gap.deploy.platform-shell-readiness.source-provider" in gap_ids
assert "gap.deploy.platform-shell-readiness.cloud-provider" in gap_ids
assert "gap.deploy.platform-shell-readiness.github-source-policy" in gap_ids
assert "gap.deploy.platform-shell-readiness.github-commit-sha" in gap_ids
assert "gap.deploy.platform-shell-readiness-artifacts-source-commit-sha" not in gap_ids
assert "gap.deploy.platform-shell-readiness.artifacts-source-commit-sha" in gap_ids
assert "gap.deploy.platform-shell-readiness.auth-provider" in gap_ids
assert "gap.deploy.platform-shell-readiness.auth-token-validation-local-tests-passed" in gap_ids
PY

echo "Platform shell deploy-readiness verification smoke test passed."
