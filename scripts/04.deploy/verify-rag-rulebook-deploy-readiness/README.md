<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-rag-rulebook-deploy-readiness.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Explain the read-only RAG/rulebook deploy-readiness verification command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.script.verify-rag-rulebook-deploy-readiness
  path: scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh
- id: deploy.script.verify-rag-rulebook-deploy-readiness.smoke-test
  path: scripts/04.deploy/verify-rag-rulebook-deploy-readiness/smoke-test.sh
- id: aws.workflows.deploy-rag-rulebook-service
  path: .agentic/aws/workflows/deploy-rag-rulebook-service.md
-->
# Verify RAG/Rulebook Deploy Readiness

`script.sh` validates a deployment-readiness manifest for the RAG/rulebook MCP
service. It is a read-only preflight check. It does not call GitHub, call AWS,
deploy software, publish artifacts, or read secret values.

## Usage

```bash
bash scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh \
  --manifest /path/to/deploy-readiness.yml \
  --json
```

For planning workflows where a blocked report should be printed without failing
the shell command, use an explicit non-execution caller intent:

```bash
bash scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh \
  --manifest /path/to/deploy-readiness.yml \
  --allow-blocked \
  --caller-intent planning \
  --json
```

Execution workflows must not use `--allow-blocked`. A deploy job must reject
any report where `ok` is not `true`, even if the command exited `0` for a
planning or explanation caller.

## Manifest

The manifest schema is `deploy/rag-rulebook-readiness-manifest/v1`.

The current staging manifest lives at:

```bash
infra/04.deploy/02.rag-rulebook/environments/staging/deploy-readiness.yml
```

It is expected to remain blocked until the remote `main` commit, protected
GitHub environment, OIDC role, immutable image digest, ECS service evidence,
runtime artifact hashes, rollback target, and health check proof exist.

The manifest names the concrete deployment candidate:

- GitHub repository, source policy, ref, commit SHA, workflow, environment,
  protection model, OIDC role, OIDC audience, OIDC repository/ref/environment
  conditions, and artifact provenance requirements. For GitHub Environments,
  the OIDC subject may be environment-scoped when the environment deployment
  branch policy restricts deploys to the governed ref.
- immutable deployable artifacts and generated RAG/rulebook corpus artifacts
- AWS account, region, runtime family, service target, network boundary, secret
  store, health check, and rollback target
- runtime-specific target proof for `app-runner`, `ecs-fargate`, `lambda`, or
  `eks`
- MCP specification version, transport, authentication, authorization, exposed
  capabilities, audit, and rate limits; the current governed MCP specification
  version is `2025-11-25`, and the first remote MCP exposure currently allows
  only `streamable-http`
- operational owner, escalation path, budgets, quotas, throttling, and local
  readiness gates, including proof that the local RAG/runtime freshness check
  passed before packaging or deployment

## Exit Behavior

- exits `0` when the manifest is deploy-ready
- exits `1` when deploy execution is blocked
- exits `0` with `--allow-blocked --caller-intent planning|explanation` even
  when blocked, so non-execution workflows can display the report without
  treating the planning command as failed
- emits `exit_overridden_for_planning: true` only for blocked reports whose
  non-zero exit was intentionally overridden for planning or explanation

## Effects

Read-only. This command validates manifest content only.
