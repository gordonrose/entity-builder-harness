<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.02-rag-rulebook.github-actions-to-ecs-fargate
version: 1
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- architecture
- sre
kind: source-material
purpose: Define production-grade source material for deploying the RAG/rulebook service from GitHub Actions to AWS ECS Fargate.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.workflow.review-okf-source-material
  path: .agentic/02.rag-rulebook/workflows/review-okf-source-material.md
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# GitHub Actions To ECS Fargate Source Material

## Purpose

Define the production-grade operating knowledge required to deploy the
RAG/rulebook service from GitHub Actions to AWS ECS Fargate.

This document is source material for the `04.deploy` corpus. It is not a
deployment approval, not an AWS mutation plan, and not a finished executable
workflow. It must pass the OKF source-material review loop before YAML rules,
chunks, selector fixtures, deploy manifests, or runtime implementation are
derived from it.

## Scope

This source covers the deploy vertical for the RAG/rulebook service when the
selected AWS runtime family is `ecs-fargate`.

It covers:

- GitHub Actions as the release-control plane.
- AWS OIDC authentication from GitHub Actions.
- container build and image publication to Amazon ECR.
- immutable artifact promotion.
- versioned RAG/rulebook corpus package publication.
- ECS task definition, service, cluster, deployment, and rollback boundaries.
- Fargate networking, IAM roles, secret references, logging, metrics, alarms,
  and health checks.
- public or private HTTP access through a governed ingress path.
- read-only MCP or API exposure for context-packet retrieval.
- required variables, checks, stop conditions, and review evidence.

It does not cover:

- direct console-click deployment as the normal production path.
- App Runner, Lambda, EKS, EC2 launch type, or non-AWS targets.
- write-capable MCP tools.
- arbitrary AWS mutation from local shells.
- storing secret values in repo files, source material, context packets,
  fixtures, logs, or generated chunks.
- deriving production rules from this source before OKF acceptance.

## Target Outcome

An engineer should be able to move from a committed `main` revision to a
staging ECS Fargate deployment through GitHub Actions with enough evidence to
answer these questions:

- Which commit, image digest, corpus package, and generated rulebook artifacts
  are running?
- Which GitHub workflow, environment, approval path, and OIDC role authorized
  the deployment?
- Which AWS account, region, cluster, service, task definition, network, and
  ingress path are in use?
- Which health checks, logs, metrics, alarms, and rollback target prove the
  deployment is safe?
- Which MCP or API capabilities are exposed, and are they read-only?
- Which budget, quota, scaling, rate-limit, and abuse controls constrain cost
  and blast radius?

The first production-shaped deployment should be a narrow read-only context
provider. It should return validated context packets from a committed corpus
package. It should not mutate repositories, GitHub, AWS, or product state.

## Canonical Flow

The deploy path should be:

```text
developer change
  -> pull request checks
  -> merge to remote main
  -> GitHub Actions deploy workflow on governed ref
  -> build and test service image
  -> build and verify RAG/rulebook runtime artifacts
  -> package corpus and generated indexes/chunks
  -> publish immutable image to ECR
  -> publish immutable corpus package or package digest
  -> protected GitHub environment approval
  -> assume AWS deployment role through OIDC
  -> render ECS task definition with image digest and corpus version
  -> update ECS service
  -> wait for service stability and health checks
  -> run post-deploy context-packet smoke query
  -> record deployment evidence or trigger rollback path
```

Planning may run before every variable is known. Deployment execution must not.

## Required Execution Variables

The deploy corpus must preserve these variables so later rules and workflows do
not require agent inference.

### GitHub Variables

- `github_repository`: owner and repo name.
- `source_policy`: `remote-main` or `approved-release-tag`.
- `deploy_ref`: expected Git ref.
- `commit_sha`: exact commit to deploy.
- `workflow_path`: expected workflow file, for example
  `.github/workflows/deploy-rag-rulebook-ecs.yml`.
- `workflow_name`: human-readable workflow name.
- `workflow_trigger`: push, release, tag, workflow dispatch, or governed
  reusable workflow call.
- `github_environment`: deployment environment, for example `staging`.
- `environment_protection`: required reviewers, branch/tag restrictions, wait
  timers, custom protection rules, or documented blocking gap.
- `concurrency_group`: deploy concurrency key.
- `permissions`: minimum workflow permissions, including `id-token: write`
  when OIDC is used.
- `pinned_actions`: exact action versions or commit SHAs.
- `artifact_retention`: retention period for build and deployment evidence.

### AWS Identity Variables

- `aws_account_id`.
- `aws_region`.
- `aws_partition`.
- `github_oidc_provider_arn`.
- `deploy_role_arn`.
- `oidc_audience`, usually `sts.amazonaws.com` for AWS STS.
- `oidc_subject_condition`.
- `oidc_repository_condition`.
- `oidc_ref_condition`.
- `oidc_environment_condition`.
- `deploy_role_permissions_boundary`.
- `cloudtrail_lookup_path` or audit query expectation.

### Container And Runtime Variables

- `ecr_repository`.
- `image_tag_policy`.
- `image_digest`.
- `dockerfile_path`.
- `build_context`.
- `task_definition_path`.
- `container_name`.
- `container_port`.
- `cpu`.
- `memory`.
- `ephemeral_storage`.
- `platform_version`.
- `runtime_family`: required value `ecs-fargate`.
- `cluster_name`.
- `service_name`.
- `desired_count`.
- `minimum_healthy_percent`.
- `maximum_percent`.
- `deployment_controller`.
- `deployment_circuit_breaker_enabled`.
- `deployment_circuit_breaker_rollback_enabled`.
- `task_execution_role_arn`.
- `task_role_arn`.

### Network And Ingress Variables

- `vpc_id`.
- `subnet_ids`.
- `security_group_ids`.
- `assign_public_ip`.
- `load_balancer_type`: `application` unless a recorded exception requires
  another type.
- `target_group_arn`.
- `target_type`: `ip` for Fargate services behind a load balancer.
- `listener_arn`.
- `listener_rule`.
- `tls_certificate_arn`.
- `domain_name`.
- `route53_zone_id`.
- `ingress_class`: local-only, private, authenticated-public, or public
  read-only.
- `allowed_clients`.
- `egress_policy`.
- `vpc_endpoint_strategy` for ECR, ECS, CloudWatch Logs, Secrets Manager,
  Systems Manager, S3, or other dependencies.

### RAG And Corpus Variables

- `corpus_package_id`.
- `corpus_package_version`.
- `corpus_package_sha256`.
- `rulebook_index_version`.
- `chunk_set_version`.
- `recognition_source_versions`.
- `compiled_policy_version`.
- `runtime_cache_fingerprint`.
- `context_packet_schema_version`.
- `retrieval_policy_version`.
- `minimum_supported_corpus_version`.
- `stale_corpus_behavior`: block, warn, or local fallback.
- `packet_token_budget_default`.
- `packet_token_budget_max`.
- `query_timeout_ms`.

### MCP Or API Exposure Variables

- `interface_type`: REST API, MCP, or both.
- `mcp_spec_version`, currently governed as `2025-11-25` when MCP is exposed.
- `mcp_transport`, currently `streamable-http` for remote MCP exposure.
- `api_base_url`.
- `auth_model`.
- `authorization_model`.
- `tenant_or_account_scope`.
- `read_only_capabilities`.
- `rate_limits`.
- `audit_fields`.
- `disablement_switch`.

### Operations Variables

- `log_group_name`.
- `log_retention_days`.
- `metrics_namespace`.
- `alarm_names`.
- `dashboard_url`.
- `on_call_owner`.
- `escalation_path`.
- `rollback_target`.
- `rollback_command_or_workflow`.
- `post_deploy_smoke_prompt`.
- `budget_name`.
- `monthly_budget_limit`.
- `quota_checks`.
- `capacity_alarm_thresholds`.

## GitHub Actions Policy

GitHub Actions should act as release control, not an opaque shell runner.

Required behavior:

- Deploy workflows run from governed refs only.
- Staging and production jobs use GitHub environments.
- Sensitive environments require protection rules before secrets or OIDC roles
  are reachable.
- Deploy jobs use OIDC rather than long-lived AWS access keys unless an
  explicit temporary exception is recorded.
- The workflow declares `permissions` explicitly.
- Third-party actions are pinned to immutable SHAs or governed version choices.
- Build, package, publish, deploy, verify, and rollback are separate jobs or
  clearly separate phases with named outputs.
- Deploy concurrency prevents two deployments to the same environment from
  racing.
- The workflow records the run id, commit SHA, image digest, corpus package
  hash, task definition revision, ECS service deployment id, and health result.

Required stop conditions:

- missing protected environment for staging or production
- deploy ref does not match `source_policy`
- missing `id-token: write` for OIDC workflow
- OIDC trust policy uses a broad wildcard without an accepted exception
- action versions are floating when production deployment is possible
- build output lacks immutable image digest
- corpus package output lacks content hash and generated artifact versions
- deploy job cannot link the commit to image, corpus package, and task
  definition

## AWS OIDC Policy

The deploy workflow should assume an AWS role using GitHub OIDC.

The AWS trust policy must constrain access by audience and subject. For
environment-based deployments, the subject should include the GitHub
environment. For branch-based deployments, it should include the expected ref.

The source material must never record a secret value. It may record role names,
ARNs, audience values, condition keys, secret names, and parameter names.

Required checks:

- GitHub OIDC provider exists in the target AWS account.
- OIDC audience is known.
- trust policy includes `token.actions.githubusercontent.com:aud`.
- trust policy includes `token.actions.githubusercontent.com:sub`.
- trust policy is scoped to expected repository and ref or environment.
- deploy role can push or deploy only the required resources.
- deploy role cannot administer arbitrary IAM, delete unrelated resources, or
  mutate unrelated services.
- CloudTrail can identify role assumption and deployment API calls.

## AWS Runtime Shape

The selected runtime is ECS Fargate.

Production-shaped infrastructure should include:

- ECR repository for the service image.
- ECS cluster.
- ECS service using Fargate launch type.
- task definition stored as reviewed source or generated IaC output.
- task execution role for image pull, logs, and secret retrieval.
- task role for the application permissions needed at runtime.
- private subnets by default for tasks unless a public subnet exception is
  reviewed.
- Application Load Balancer for HTTP/HTTPS access unless a recorded exception
  requires another load balancer type.
- target group with `ip` target type for Fargate.
- security groups that allow only required ingress and egress.
- TLS termination when traffic crosses a network trust boundary.
- CloudWatch log group with retention.
- metrics and alarms for service health, task health, latency, error rate,
  request rate, CPU, memory, and deployment failure.
- ECS deployment circuit breaker with rollback enabled for rolling-update
  deployments where compatible.

Required stop conditions:

- AWS account, region, cluster, service, network, or role ownership is unclear.
- runtime is not selected as `ecs-fargate`.
- task definition is missing reviewed provenance.
- public ingress exists without auth, rate limits, audit, and TLS expectations.
- task execution role and task role are conflated without review.
- Fargate networking cannot reach ECR, logs, secrets, or corpus package
  storage.
- service cannot prove health at container, ECS service, load balancer, and
  application layers.
- rollback target is not known before deployment.

## Corpus Package And Runtime Freshness

The service must serve a committed corpus package, not whatever happens to be
in a developer's local worktree.

Required behavior:

- local runtime checks pass before package publication
- generated recognition sources are current
- generated rulebook index is current
- generated chunks are current
- compiled retrieval policy is current
- selector evaluations pass
- source projections are current
- source-to-rule derivation records are accepted where production rules depend
  on source material
- corpus package contains a manifest with source file hashes, rule hashes,
  chunk hashes, index hash, policy hash, generator versions, and commit SHA
- service startup verifies package manifest integrity
- service exposes the corpus package version in health and query responses
- stale corpus detection returns a gap rather than silently using broad context

For the MSP, the corpus package may be stored as a local or GitHub build
artifact before S3 or another durable package store is introduced. Production
must name the durable package store and retention policy.

## API And MCP Surface

The first deployed surface should expose a small API for context-packet
retrieval. MCP exposure may be layered on top after the API contract is stable.

Minimum API endpoints:

- `GET /healthz` returns process health and service identity.
- `GET /readyz` verifies corpus package, runtime cache, and dependency
  readiness.
- `POST /v1/context/query` accepts prompt, repo id, commit SHA, focused paths,
  token budget, and optional expected corpus version.
- `GET /v1/corpus/version` returns served corpus package identity.

Minimum MCP resources or prompts, when MCP is enabled:

- retrieve validated context packet
- list corpus versions
- list corpus gaps
- inspect deploy readiness
- expose planning prompts only

MCP tools that mutate repo, GitHub, AWS, or product state are out of scope for
the first deployment.

## Security Requirements

Security is a blocker, not a polish pass.

Required controls:

- OIDC replaces long-lived AWS access keys for deployment.
- GitHub environments protect sensitive deployments.
- least-privilege AWS deploy role is separate from ECS task role.
- ECS task execution role is separate from application task role.
- secret values live in GitHub environment secrets, AWS Secrets Manager, AWS
  Systems Manager Parameter Store, or another governed store.
- logs redact tokens, credentials, private keys, auth headers, cookies,
  session ids, and unrelated prompt content.
- API and MCP endpoints authenticate callers before serving private corpus or
  repo-specific context.
- authorization scopes corpus access by account, repo, tenant, or configured
  entitlement.
- request payload size, token budget, rate, and concurrency are bounded.
- public exposure requires TLS, rate limits, abuse controls, audit logging, and
  disablement path.
- threat model covers prompt injection, corpus poisoning, overbroad retrieval,
  data exfiltration, confused deputy, tool poisoning, and stale package use.

## Observability Requirements

The deployed service is not production-ready unless operators can reconstruct
deployment and retrieval decisions.

Every query should produce audit-safe structured logs with:

- request id
- caller or client id where available
- repo id
- requested commit SHA
- served corpus package version
- retrieval policy version
- selected chunk ids
- emitted gaps
- confidence
- token budget requested and used
- response status
- latency

Deployment should produce evidence with:

- GitHub run id
- commit SHA
- image digest
- corpus package hash
- task definition revision
- ECS deployment id
- cluster and service name
- health status
- rollback target
- post-deploy smoke result

Metrics should include:

- request count
- error count
- latency percentiles
- context packet size
- retrieval gaps by type
- stale corpus requests
- CPU and memory utilization
- ECS running task count
- deployment failures
- rollback events

## Health Checks And Rollback

Health checks must prove more than process start.

Required health checks:

- container process responds on the expected port
- `GET /healthz` succeeds
- `GET /readyz` proves corpus package and runtime cache are usable
- load balancer target health is healthy
- ECS service reaches stable state
- post-deploy context query returns a valid packet for a known smoke prompt

Rollback must be designed before deployment.

Required rollback evidence:

- previous safe image digest
- previous safe corpus package hash
- previous task definition revision
- ECS service rollback mechanism
- expected health checks after rollback
- owner or approval path for manual rollback
- disablement path if rollback cannot complete

For rolling deployments, use ECS deployment circuit breaker with rollback when
the selected deployment controller supports it. If blue/green deployment is
introduced later, the source material must be updated with traffic-shift,
pre-traffic checks, post-traffic checks, and rollback authority.

## Cost And Capacity Controls

Cost controls are part of the deployment design.

Required controls:

- start with the smallest safe desired task count for the environment
- set CPU and memory from measured local/runtime behavior, not guesses
- enforce API rate limits, concurrency limits, packet-size limits, and token
  budget limits
- define CloudWatch log retention and avoid logging full prompts or packet
  bodies by default
- define budget alarms and service quota checks before public or production
  exposure
- avoid NAT gateway cost where private VPC endpoints are more appropriate and
  worth the complexity
- forecast ALB, Fargate, ECR, CloudWatch Logs, data transfer, NAT, Secrets
  Manager, and package storage costs
- define scale-out and scale-in rules before traffic grows beyond private team
  use

## Performance Requirements

The context provider must remain responsive and bounded.

Required expectations:

- query endpoint has explicit timeout
- retrieval has max candidate count, max selected chunks, and max packet tokens
- startup loads or verifies corpus package within a known time budget
- readiness fails when runtime cache is missing or stale
- service degrades by returning gaps when corpus or retrieval confidence is
  insufficient
- large corpus package fetch, unzip, or index load does not block health
  endpoints indefinitely
- ECS CPU, memory, and desired task count match measured local query behavior
- load test or smoke benchmark exists before production exposure

## MSP Sequence

The minimum shippable path should be staged:

1. Keep the local deterministic runtime working.
2. Add a container image for the RAG/rulebook service.
3. Add a GitHub Actions check workflow that builds the local runtime and
   service image without deploying.
4. Add a deploy-readiness manifest for ECS Fargate with placeholder-free
   required variables.
5. Add AWS OIDC role and environment protection documentation.
6. Add ECR publish job.
7. Add ECS task definition and deployment job for staging only.
8. Add post-deploy `healthz`, `readyz`, and context-query smoke checks.
9. Add rollback proof.
10. Only then consider production or remote MCP exposure.

## Derivation Map

When this source is accepted, it should derive into structured artifacts in
these families:

- GitHub release-control rules.
- ECS Fargate runtime-boundary rules.
- OIDC trust and IAM rules.
- corpus package freshness and provenance rules.
- deploy-readiness manifest rules.
- API and MCP read-only exposure rules.
- observability and audit rules.
- cost, capacity, and quota rules.
- rollback and disablement rules.
- selector fixtures for deployment questions.
- deploy-readiness executable checks.

## Source References

Use these references as source evidence when deriving rules:

- GitHub Actions deployment to Amazon ECS:
  `https://docs.github.com/en/actions/how-tos/deploy/deploy-to-third-party-platforms/amazon-elastic-container-service`
- GitHub Actions OIDC in AWS:
  `https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws`
- GitHub deployment environments:
  `https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments`
- GitHub artifact attestations:
  `https://docs.github.com/en/actions/concepts/security/artifact-attestations`
- Amazon ECS deployment circuit breaker:
  `https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html`
- Amazon ECS Fargate task networking:
  `https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html`
- Amazon ECS service load balancing:
  `https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-load-balancing.html`
- Amazon ECS task IAM roles:
  `https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html`

## Acceptance Bar

This source is not ready for source-to-rule derivation until the OKF review
record is accepted with every reviewer role scoring above `9.5/10` and no
blocking gaps remaining.
