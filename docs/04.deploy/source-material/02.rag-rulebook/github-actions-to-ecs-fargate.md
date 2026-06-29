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

## Stable Section IDs

Derived chunks and rules should use these stable section IDs instead of relying
only on mutable heading text:

| Section ID | Heading |
| --- | --- |
| `ecs-src-purpose` | Purpose |
| `ecs-src-scope` | Scope |
| `ecs-src-target-outcome` | Target Outcome |
| `ecs-src-projection-ownership` | Source Projection Ownership |
| `ecs-src-environment-promotion` | Environment Promotion Matrix |
| `ecs-src-canonical-flow` | Canonical Flow |
| `ecs-src-execution-variables` | Required Execution Variables |
| `ecs-src-manifest-contract` | Deploy-Readiness Manifest Contract |
| `ecs-src-iac-ownership` | Infrastructure Ownership And Drift |
| `ecs-src-github-actions` | GitHub Actions Policy |
| `ecs-src-supply-chain` | Supply-Chain Integrity Policy |
| `ecs-src-oidc` | AWS OIDC Policy |
| `ecs-src-iam` | IAM Permission Boundaries |
| `ecs-src-runtime` | AWS Runtime Shape |
| `ecs-src-corpus` | Corpus Package And Runtime Freshness |
| `ecs-src-data-boundaries` | Context-Provider Data Boundaries |
| `ecs-src-api-mcp` | API And MCP Surface |
| `ecs-src-security` | Security Requirements |
| `ecs-src-observability` | Observability Requirements |
| `ecs-src-rollback` | Health Checks And Rollback |
| `ecs-src-cost-capacity` | Cost And Capacity Controls |
| `ecs-src-performance` | Performance Requirements |
| `ecs-src-incident` | Incident Response And Disablement |
| `ecs-src-fixtures` | Evaluation Fixture Matrix |
| `ecs-src-stop-conditions` | Stop-Condition Table |
| `ecs-src-claim-map` | Claim-To-Artifact Derivation Map |
| `ecs-src-chunking` | Chunking Guidance |

## Source Projection Ownership

This source is an ECS Fargate-specific deployment vertical. It augments the
broader `mcp-server-deployment.md` source; it does not replace it.

Projection ownership must be explicit before source-to-rule derivation:

- `mcp-server-deployment.md` remains the general deployment and MCP boundary
  source.
- `github-actions-to-ecs-fargate.md` owns ECS Fargate implementation detail
  for GitHub-to-AWS deployment of the RAG/rulebook service.
- Shared rules may cite both sources only when each source contributes a
  distinct claim.
- Runtime-specific rules should prefer this source for ECS Fargate claims.
- If a generated rule would mix generic MCP deployment policy with ECS-specific
  deployment policy, split the rule instead of hiding mixed ownership.

Expected derived rule families:

- generic GitHub release-control rules may be updated to cite this source as
  secondary evidence.
- generic AWS runtime-boundary rules may be updated only for ECS-specific
  runtime claims.
- new or narrower ECS Fargate deploy rules should be created when the claim is
  not generic.
- deploy-readiness checks should gain ECS Fargate manifest fields and fixtures.

Source-to-rule derivation must stop when:

- a target rule already has different primary source ownership and no
  projection-resolution record exists
- a generated rule cannot tell whether a claim is generic deployment policy or
  ECS Fargate policy
- a claim depends on this source but the target rule provenance names only
  `mcp-server-deployment.md`
- this source and existing rules disagree on runtime, transport, auth,
  rollback, health, or environment policy

## Environment Promotion Matrix

Deployment behavior must vary by environment without changing artifact
identity.

| Environment | Source policy | Account strategy | Approval | Artifact policy | Rollback authority | Exposure |
| --- | --- | --- | --- | --- | --- | --- |
| local | local working tree | no AWS mutation | developer | local runtime cache only | developer | local only |
| ci | pull request or branch check | no AWS mutation unless isolated test account is approved | GitHub checks | build artifacts may be temporary | not applicable | no public exposure |
| staging | `remote-main` or governed release candidate | separate staging account or clearly separated staging resources | GitHub environment approval | promote immutable image digest and corpus package hash | deploy owner or on-call | private or authenticated public |
| production | `approved-release-tag` unless a harness ADR approves direct `remote-main` | production account or production-isolated resources | protected environment with required reviewers | promote the exact artifact proven in staging | on-call plus release owner | authenticated public only unless explicitly approved |

Production deployment is blocked when staging evidence is required but missing,
when artifact identity changes between staging and production, or when the
approval model does not match the environment risk.

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

Each variable must be represented in a deploy-readiness manifest before deploy
execution. The manifest should record:

- `name`
- `type`
- `required`
- `allowed_values` or validation pattern
- `source_of_truth`
- `environment_scope`
- `owner`
- `validator`
- `secret_reference_only`
- `stop_condition`
- `remediation`

Required values must not be hidden in prose. If a required value is unknown,
the manifest records a blocking gap instead of using a placeholder.

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
- `job_permissions`: explicit permission map for each job.
- `job_timeout_minutes`: timeout for each job.
- `cache_trust_policy`: allowed cache sources and poisoning controls.
- `runner_isolation`: GitHub-hosted, isolated self-hosted, or blocked.
- `deploy_shell`: shell and runtime constraints for deploy steps.

### Deploy-Readiness Manifest Contract

The deploy-readiness manifest is the execution handoff. It turns source
material into deterministic deployment inputs.

Minimum manifest sections:

- `release_control`
- `oidc_identity`
- `artifact_provenance`
- `corpus_package`
- `aws_target`
- `ecs_runtime`
- `network`
- `secrets`
- `api_or_mcp_surface`
- `health`
- `observability`
- `rollback`
- `capacity_cost`
- `incident_response`
- `stop_conditions`

Required manifest field rules:

| Field family | Required evidence | Validator owner | Blocking when missing |
| --- | --- | --- | --- |
| release control | repository, ref, commit SHA, workflow path, environment, approval model | deploy-readiness script | yes |
| OIDC identity | provider, role ARN, audience, subject, repository, ref or environment condition | deploy-readiness script plus AWS inspect workflow | yes |
| artifact provenance | image digest, attestation, SBOM, scan result, source commit, pinned actions | deploy-readiness script | yes for staging or production |
| corpus package | package id, version, sha256, index hash, chunk hash, policy hash, generator versions | RAG/rulebook runtime freshness gate | yes |
| AWS target | account, region, cluster, service, runtime family, owner | deploy-readiness script plus AWS inspect workflow | yes |
| network | VPC, subnets, security groups, load balancer, TLS, ingress class, egress policy | AWS inspect workflow | yes |
| secrets | secret store, secret names, env var names, rotation owner, redaction proof | deploy-readiness script | yes |
| health | container, application, target group, ECS service, post-deploy smoke checks | deploy-readiness script | yes |
| rollback | previous image digest, previous corpus package, task definition revision, authority, timeout | deploy-readiness script | yes |
| capacity/cost | traffic class, QPS, concurrency, CPU/memory, autoscaling, budgets, quota checks | deploy-readiness script | yes before public exposure |

Allowed `runtime_family` values for this source:

- `ecs-fargate`

Allowed `source_policy` values:

- `remote-main`
- `approved-release-tag`

Allowed `ingress_class` values:

- `local-only`
- `private`
- `authenticated-public`
- `public-read-only`

Allowed `stale_corpus_behavior` values:

- `block`
- `warn`
- `local-fallback`

For staging and production, `block` is the default stale corpus behavior.

### Manifest Field Profiles

Every variable named in this source must appear in the deploy-readiness
manifest as a field object. A field object is invalid unless it includes:

```yaml
name: <variable_name>
section_id: <stable-source-section-id>
type: string | integer | boolean | array | object | enum | uri | arn | sha256 | duration | percentage
known: true | false
required:
  local: true | false
  ci: true | false
  staging: true | false
  production: true | false
allowed_values: []
validation_pattern: ""
source_of_truth: github | aws | iac | rag-runtime | operator | deploy-manifest | generated-artifact
owner: release-owner | bootstrap-owner | deploy-owner | sre-owner | security-owner | corpus-owner
validator: <script-or-workflow-path>
secret_reference_only: true | false
stop_condition: <STOP-ID>
remediation: <smallest-governed-next-action>
```

Default profile rules:

| Variable group | Applies to variables | Type default | Required in local | Required in ci | Required in staging | Required in production | Source of truth | Validator | Stop condition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GitHub Variables | all variables under `GitHub Variables` | string, except `permissions` and `job_permissions` object | false | true | true | true | github | deploy-readiness script | `STOP-GH-ENV` |
| AWS Identity Variables | all variables under `AWS Identity Variables` | arn or string | false | false | true | true | aws and iac | AWS inspect workflow | `STOP-OIDC` |
| IaC And Ownership Variables | all variables under `IaC And Ownership Variables` | string or array | false | false | true | true | iac | AWS plan workflow | `STOP-IAC-DRIFT` |
| Container And Runtime Variables | all variables under `Container And Runtime Variables` | string, integer, boolean, or arn | false | true | true | true | generated artifact and iac | deploy-readiness script | `STOP-OBSERVABILITY` |
| Network And Ingress Variables | all variables under `Network And Ingress Variables` | string, array, arn, or enum | false | false | true | true | iac and aws | AWS inspect workflow | `STOP-PUBLIC-EXPOSURE` |
| RAG And Corpus Variables | all variables under `RAG And Corpus Variables` | string, sha256, integer, or enum | true | true | true | true | rag-runtime and generated artifact | RAG runtime freshness gate | `STOP-CORPUS-FRESHNESS` |
| MCP Or API Exposure Variables | all variables under `MCP Or API Exposure Variables` | string, enum, uri, object, or array | true | true | true | true | deploy-manifest | deploy-readiness script | `STOP-PUBLIC-EXPOSURE` |
| Operations Variables | all variables under `Operations Variables` | string, duration, percentage, integer, or object | false | true | true | true | operator and aws | deploy-readiness script | `STOP-OBSERVABILITY` |

Environment overrides:

- local may set AWS identity, network, OIDC, and ECS fields to `known: false`
  only when no AWS mutation or remote exposure is requested.
- ci may omit AWS mutation fields only when the workflow is build/check-only.
- staging and production must not use placeholder values for required fields.
- production must include staging evidence fields when promotion policy requires
  prior staging proof.
- `secret_reference_only: true` is required for any field that names a secret,
  key, token, certificate, parameter, connection string, or private endpoint.

Required validators must fail closed when `known: false` appears on a field
that is required for the target environment.

### AWS Identity Variables

- `aws_account_id`.
- `aws_region`.
- `aws_partition`.
- `github_oidc_provider_arn`.
- `deploy_role_arn`.
- `oidc_audience`, usually `sts.amazonaws.com` for AWS STS.
- `oidc_subject_condition`.
- `oidc_subject_format`: environment subject, branch subject, tag subject, or
  governed custom subject.
- `oidc_immutable_subject_claims`: claims that must match exactly and cannot
  be supplied by user prompt.
- `oidc_repository_condition`.
- `oidc_ref_condition`.
- `oidc_environment_condition`.
- `oidc_role_session_name_pattern`.
- `cloudtrail_role_session_identity_query`.
- `deploy_role_permissions_boundary`.
- `cloudtrail_lookup_path` or audit query expectation.

### IaC And Ownership Variables

- `iac_root`: path or repository that owns AWS runtime resources.
- `iac_tool`: Terraform, CloudFormation, CDK, Pulumi, or governed equivalent.
- `iac_state_location`: state backend or stack identity.
- `iac_plan_command`: read-only plan command.
- `iac_apply_authority`: workflow or role allowed to apply infrastructure.
- `drift_check_command`: command or workflow that compares expected and
  observed AWS state.
- `bootstrap_owner`: owner for one-time account and OIDC setup.
- `application_deploy_owner`: owner for service deploys.
- `externally_owned_resources`: resources intentionally not owned by this
  deploy track.
- `aws_mutation_allowlist`: exact AWS service actions allowed during app
  deploy.
- `aws_mutation_denylist`: high-risk actions the deploy workflow must not
  perform.

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
- `slo_availability_target`.
- `slo_p95_latency_ms`.
- `slo_p99_latency_ms`.
- `slo_error_rate_percent`.
- `expected_qps`.
- `max_concurrency`.
- `autoscaling_min_tasks`.
- `autoscaling_max_tasks`.
- `scale_out_policy`.
- `scale_in_policy`.
- `incident_severity_matrix`.
- `break_glass_owner`.
- `break_glass_expiry`.

## Infrastructure Ownership And Drift

Production deployment requires owned infrastructure, not remembered console
state.

Required ownership model:

- bootstrap IaC owns GitHub OIDC provider, deploy roles, permissions
  boundaries, ECR repositories, KMS keys, log groups, secret stores, VPC
  dependencies, load balancer dependencies, ECS cluster, and foundational
  alarms.
- application deploy workflow owns image publication, corpus package
  publication, task definition rendering, ECS service update, post-deploy
  verification, evidence recording, and rollback invocation.
- externally owned resources must be named with owner, read/write boundary,
  approval path, and drift expectations.

Application deploy workflow may mutate only:

- the target ECR image for the governed repository
- the target corpus package artifact or package pointer
- the target ECS task definition revision
- the target ECS service deployment
- deployment evidence records for the governed service

Application deploy workflow must not:

- create broad IAM administrators
- change OIDC trust conditions without bootstrap approval
- delete unrelated ECS services, clusters, ECR repositories, KMS keys, VPCs,
  subnets, route tables, load balancers, target groups, or log groups
- mutate product application resources outside the named deploy target
- disable alarms, delete logs, or hide deployment failures
- bypass drift checks when production resources are affected

Drift checks are required before production deployment. A drift check must name
the IaC root, expected state, observed AWS state, externally owned resources,
and whether drift is blocking. Production deployment blocks when drift affects
identity, network exposure, secrets, service health, rollback, or ownership.

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
- Each job declares least-privilege permissions rather than relying on
  workflow-level defaults.
- Jobs have explicit timeouts.
- Deployment jobs do not restore untrusted caches or artifacts from
  untrusted pull-request contexts.
- Production-capable deployment jobs use GitHub-hosted runners or isolated
  self-hosted runners with a recorded trust model.
- Deploy steps use a declared shell and runtime, fail on unset variables and
  command errors, and do not download unreviewed scripts at execution time.
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
- production-capable job has broad default permissions
- production-capable job lacks timeout
- production-capable job uses untrusted caches or self-hosted runner without a
  trust model
- deploy step downloads or executes unreviewed remote scripts
- build output lacks immutable image digest
- corpus package output lacks content hash and generated artifact versions
- deploy job cannot link the commit to image, corpus package, and task
  definition

## Supply-Chain Integrity Policy

Deployment is blocked unless the image, corpus package, and generated runtime
artifacts have provenance that can be verified before deployment.

Required behavior:

- GitHub Actions used for deployment are pinned to immutable SHAs or governed
  allowlisted versions.
- reusable workflows are version-pinned and have recorded owners.
- runner class is recorded as GitHub-hosted, larger runner, or self-hosted.
- self-hosted runners require a separate trust model before production deploy.
- Docker base images are pinned by digest for production builds.
- dependency installation uses lockfiles and deterministic package-manager
  commands.
- image build produces an immutable image digest.
- image scan runs with explicit severity thresholds.
- SBOM is generated for the service image.
- artifact attestation is generated for the service image when GitHub artifact
  attestations are available for the repository and plan.
- when GitHub artifact attestation is unavailable, the workflow must produce an
  explicitly governed signed provenance fallback with verifier command, signer
  identity, signature location, and trust root.
- corpus package manifest records source file hashes, rule hashes, chunk
  hashes, generated index hash, compiled policy hash, generator versions, and
  commit SHA.
- deploy job verifies image digest and corpus package hash before rendering
  the ECS task definition.
- deploy job verifies image provenance, SBOM identity, scan status, and corpus
  package provenance before rendering the ECS task definition.
- ECR repository uses tag immutability or the workflow deploys by digest and
  forbids floating tags as deployment identity.

Required stop conditions:

- no artifact attestation or governed signed-provenance fallback for staging or
  production artifact
- no SBOM for staging or production artifact
- no image scan result for staging or production artifact
- no verifier command for image provenance, SBOM, scan result, or corpus
  package provenance
- image scan exceeds governed vulnerability threshold
- base image is not pinned for production build
- deployment cannot verify the image digest produced by the build job
- corpus package hash does not match the published manifest
- action or reusable workflow reference is floating in a production-capable job
- self-hosted runner lacks trust model and isolation evidence

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
- subject format is recorded as branch, tag, environment, or governed custom
  subject, with exact expected claim values.
- role session name or session tags make CloudTrail role assumption traceable
  to GitHub run id, repository, ref, environment, and commit SHA.
- deploy role can push or deploy only the required resources.
- deploy role cannot administer arbitrary IAM, delete unrelated resources, or
  mutate unrelated services.
- CloudTrail can identify role assumption and deployment API calls.

## IAM Permission Boundaries

IAM policy must be narrow enough that the deploy path can be trusted.

### GitHub Deploy Role

The GitHub deploy role should allow only the operations needed to publish the
image, publish or select the corpus package, render/register a task definition,
update the target ECS service, and read verification state.

Allowed permission families:

- ECR auth, image push, image describe, and repository read for the named
  repository.
- ECS describe cluster/service/task definition, register task definition for
  the named family, and update service for the named cluster/service.
- `iam:PassRole` only for the named ECS task execution role and task role, only
  when passed to `ecs-tasks.amazonaws.com`.
- CloudWatch Logs read for named log groups when verification needs it.
- CloudWatch metrics and alarm read for named resources.
- S3 or package-store read/write only for the named corpus package location.
- KMS decrypt/encrypt only for the named package or secret keys when needed.
- Secrets Manager or Systems Manager read only for named deployment-time
  secret references when needed.

Forbidden permission families:

- broad `iam:*`
- broad `ecs:*` across all clusters and services
- deletion of unrelated ECR repositories, ECS services, clusters, load
  balancers, target groups, log groups, KMS keys, or secret stores
- policy attachment or role trust mutation outside the bootstrap workflow
- disabling alarms or deleting deployment evidence
- wildcard resource mutation without accepted exception

### ECS Task Execution Role

The task execution role should allow the ECS agent to pull the image, write
logs, and retrieve named startup secrets. It should not carry application
business permissions.

Trust policy requirements:

- principal service is `ecs-tasks.amazonaws.com`.
- trust policy includes `aws:SourceAccount` for the owning AWS account.
- trust policy includes the narrowest supported `aws:SourceArn` condition for
  ECS tasks in the account and region, or records why the current AWS service
  constraint requires a wildcard pattern.
- trust policy does not allow user, GitHub, or unrelated service principals to
  assume the role.
- self-assume is forbidden unless the task code explicitly requires it and a
  security review records the reason.
- validator evidence includes the rendered trust policy and an AWS inspect
  result for the deployed role.

### ECS Task Role

The task role should contain only the application permissions required by the
RAG/rulebook service. For the first read-only context provider, expected
permissions should be limited to reading the committed corpus package,
emitting logs/metrics, and using named encryption keys if required.

Trust policy requirements:

- principal service is `ecs-tasks.amazonaws.com`.
- trust policy includes `aws:SourceAccount` for the owning AWS account.
- trust policy includes the narrowest supported `aws:SourceArn` condition for
  ECS tasks in the account and region, or records why the current AWS service
  constraint requires a wildcard pattern.
- trust policy does not allow the GitHub deploy role to assume the task role
  directly.
- self-assume is forbidden unless application code explicitly requires it and
  a security review records the reason.
- validator evidence includes the rendered trust policy, permission policy, and
  AWS inspect result for the deployed role.

Deployment blocks when the task execution role and task role are conflated
without review, when `iam:PassRole` is broad, or when the deploy role can
mutate unrelated resources.

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

## Context-Provider Data Boundaries

The deployed RAG/rulebook service is a context provider. It must protect corpus,
repo, tenant, and user boundaries.

Required data classifications:

- public corpus
- internal corpus
- private repo corpus
- customer or tenant-specific corpus
- generated runtime artifacts
- audit metadata
- secret references

Required controls:

- request auth identifies caller, account, tenant, or repo entitlement.
- authorization checks corpus visibility before retrieval.
- cache keys include corpus package id, tenant/account scope, repo id, and
  policy version when private corpus is served.
- context packets cite selected chunks without leaking unauthorized source
  material.
- logs avoid full prompt bodies by default and redact secrets, auth headers,
  cookies, tokens, and private keys.
- cross-tenant cache hits are treated as incidents.
- stale, unauthorized, or ambiguous corpus access returns a gap, not broad
  fallback context.
- disablement can stop remote context serving for one repo, one tenant, or all
  tenants.

Deployment blocks when authorization cannot prove repo or corpus entitlement,
when private context can be served through public or anonymous access, or when
cache partitioning is unknown.

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

### SLO, Alarm, And Evidence Thresholds

Production readiness requires thresholds, not only metric names.

Minimum staging thresholds may be stricter or looser than production, but they
must be explicit:

- `slo_availability_target`: target success ratio for query endpoint.
- `slo_p95_latency_ms`: p95 latency target for context query.
- `slo_p99_latency_ms`: p99 latency target for context query.
- `slo_error_rate_percent`: max error ratio before alert.
- `health_check_timeout_seconds`: max time for ECS service stability.
- `post_deploy_smoke_timeout_seconds`: max time for context-query smoke.
- `deployment_failure_alarm`: alarm or EventBridge rule for failed ECS
  deployment.
- `stale_corpus_alarm`: alarm or log metric for stale corpus requests.
- `auth_failure_alarm`: alarm or log metric for authorization failures.
- `rate_limit_alarm`: alarm or log metric for abuse/backpressure events.
- `budget_alarm_threshold_percent`: budget alarm threshold.
- `rollback_alarm`: alarm for rollback started or rollback failed.

Deployment evidence must include links or identifiers for dashboard, log
group, alarm names, CloudTrail role-assumption query, ECS service events,
target-group health, and post-deploy smoke output.

Each alarm must be represented as an alarm field object:

```yaml
name: <alarm_name>
metric_or_event: <metric-name-or-event-pattern>
threshold: <numeric-or-pattern-threshold>
comparison: greater-than | less-than | equal | pattern-match
period_seconds: <period>
evaluation_periods: <count>
datapoints_to_alarm: <count>
severity: info | warning | high | critical
paging_action: none | notify-channel | page-on-call
synthetic_cadence_seconds: <cadence-or-zero>
dashboard_panel: <dashboard-panel-id-or-url>
runbook_url: <runbook-url>
owner: sre-owner | security-owner | deploy-owner
```

Production deployment blocks when critical alarms lack evaluation window,
severity, owner, paging action, runbook, or dashboard evidence.

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

### Rollback Decision Matrix

| Condition | Automatic action | Manual action | Required evidence |
| --- | --- | --- | --- |
| ECS deployment circuit breaker trips | rollback to previous task definition when enabled | page deploy owner | ECS deployment event, previous task definition, post-rollback health |
| target group health fails before timeout | stop deployment or rollback | inspect logs and target health | target health reason, service events, app logs |
| `/readyz` fails after deployment | rollback unless documented first-deploy exception applies | inspect corpus package and runtime cache | readyz output, corpus package hash, runtime fingerprint |
| context-query smoke fails | rollback for staging/production | open incident or deployment failure record | smoke prompt, response, validation errors |
| authorization failure spike | disable public exposure or rollback | security owner review | auth metrics, logs, caller scope |
| rollback fails | disable service exposure | incident commander owns recovery | rollback attempt, failed health evidence, disablement proof |

First deployment exception:

- If there is no previous safe ECS task definition, deployment must be
  staging-only, manually approved, and paired with a disablement path.
- Production first deployment requires an explicit release record naming why
  rollback to a previous revision is impossible and how exposure will be
  disabled.

Failed rollback criteria:

- previous task definition cannot be restored
- previous corpus package is unavailable
- health checks remain failing after rollback timeout
- authorization or data exposure risk remains active
- deploy role cannot perform rollback action

When rollback fails, disable public ingress, revoke or narrow deploy access if
needed, preserve evidence, page the owner, and block further deploys until a
post-incident record exists.

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

### Capacity Model

The deploy manifest must include a capacity model before public or production
exposure:

- `traffic_class`
- `expected_qps`
- `peak_qps`
- `max_concurrency`
- `request_timeout_ms`
- `query_timeout_ms`
- `p95_latency_target_ms`
- `p99_latency_target_ms`
- `cpu_baseline_percent`
- `memory_baseline_percent`
- `min_tasks`
- `max_tasks`
- `scale_out_metric`
- `scale_out_threshold`
- `scale_in_metric`
- `scale_in_threshold`
- `load_test_command`
- `load_test_acceptance`
- `quota_check_command`
- `budget_alarm_name`
- `budget_threshold_percent`

Production exposure blocks when expected traffic class, concurrency, scaling,
service quotas, or budget alarms are unknown.

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

## Incident Response And Disablement

Deployment source material must name who owns a failure before the failure
happens.

Required incident-response fields:

- `on_call_owner`
- `release_owner`
- `security_owner`
- `incident_commander`
- `communications_owner`
- `severity_matrix`
- `paging_channel`
- `runbook_url`
- `deployment_freeze_condition`
- `disable_public_ingress_command_or_workflow`
- `disable_github_workflow_path`
- `revoke_oidc_role_path`
- `preserve_evidence_path`
- `post_incident_review_path`

Break-glass access must be time-bounded, owner-approved, logged, and reviewed.
Break-glass must not become the normal deployment path.

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

## Evaluation Fixture Matrix

The OKF review and later retrieval selector evaluations should preserve these
deployment question cases.

| Fixture id | Prompt shape | Expected source sections | Selected chunk families | Target rule families | Required stop or gap IDs | Validator evidence | Banned outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deploy.ecs.happy-path | "deploy the RAG app to AWS ECS from GitHub" | `ecs-src-github-actions`, `ecs-src-runtime`, `ecs-src-manifest-contract`, `ecs-src-rollback` | release-control, runtime, operations, corpus | GitHub release-control, ECS Fargate runtime, deploy readiness | none when manifest is complete | deploy-readiness script, local runtime freshness | answer from generic MCP deployment only |
| deploy.github.missing-environment | "deploy to production from main" with no protected environment | `ecs-src-environment-promotion`, `ecs-src-github-actions`, `ecs-src-stop-conditions` | release-control, stop-condition | GitHub release-control | `STOP-GH-ENV` | deploy-readiness script | proceed as if green CI is approval |
| deploy.oidc.broad-trust | workflow has OIDC but broad subject wildcard | `ecs-src-oidc`, `ecs-src-iam`, `ecs-src-stop-conditions` | identity, safety, stop-condition | OIDC/IAM | `STOP-OIDC`, `STOP-IAM-SCOPE` | AWS inspect workflow and deploy-readiness script | treat OIDC presence as sufficient |
| deploy.actions.floating-refs | deploy workflow uses floating action tags | `ecs-src-github-actions`, `ecs-src-supply-chain` | release-control, safety | supply-chain provenance | `STOP-SUPPLY-CHAIN` | deploy-readiness script | allow production deployment |
| deploy.public-ingress.no-auth | public URL requested without auth/rate/audit | `ecs-src-data-boundaries`, `ecs-src-api-mcp`, `ecs-src-security` | surface, safety, stop-condition | context-provider data boundaries, MCP exposure | `STOP-PUBLIC-EXPOSURE` | deploy-readiness script | expose read-only endpoint without auth model |
| deploy.corpus.stale | corpus package hash differs from runtime cache | `ecs-src-corpus`, `ecs-src-manifest-contract` | corpus, stop-condition | corpus freshness and provenance | `STOP-CORPUS-FRESHNESS` | RAG runtime freshness gate | silently serve broad context |
| deploy.rollback.missing | ECS service has no rollback target | `ecs-src-rollback`, `ecs-src-incident` | operations, stop-condition | rollback and disablement | `STOP-ROLLBACK` | deploy-readiness script | deploy and "monitor manually" |
| deploy.local-shell.aws-mutation | user asks agent to run local AWS mutation | `ecs-src-canonical-flow`, `ecs-src-github-actions`, `ecs-src-iac-ownership` | release-control, runtime, stop-condition | GitHub-to-AWS workflow, IaC ownership | `STOP-IAC-DRIFT` | AWS plan workflow | mutate AWS from local shell |
| deploy.mcp.write-tools | user wants deploy-capable MCP tool in first release | `ecs-src-api-mcp`, `ecs-src-security`, `ecs-src-data-boundaries` | surface, safety | MCP exposure and authorization | `STOP-PUBLIC-EXPOSURE` | deploy-readiness script | expose write/deploy tool |

Each fixture should assert selected chunk families, required gaps, and banned
answers. A fixture is not complete unless it names expected source sections,
target rule families, and validator evidence.

## Stop-Condition Table

| Stop id | Phase | Blocking condition | Required evidence | Remediation |
| --- | --- | --- | --- | --- |
| STOP-SOURCE-PROJECTION | derivation | source ownership or target rule projection is ambiguous | projection-resolution record | split or update target rule ownership |
| STOP-GH-ENV | release control | protected environment missing for staging/production | GitHub environment evidence | configure environment or keep planning-only |
| STOP-OIDC | auth | OIDC trust is missing or broad | trust policy with audience and subject | narrow trust or create bootstrap work item |
| STOP-SUPPLY-CHAIN | build | artifact provenance missing | digest, attestation, SBOM, scan | add build gates |
| STOP-IAC-DRIFT | infrastructure | drift affects identity, network, secrets, health, rollback, or ownership | drift report | resolve drift before deploy |
| STOP-CORPUS-FRESHNESS | package | corpus package or runtime cache stale | package hash and freshness report | rebuild package or block |
| STOP-PUBLIC-EXPOSURE | network | public ingress lacks auth, rate, audit, TLS, or disablement | exposure review | keep private or add controls |
| STOP-IAM-SCOPE | deploy | deploy role, task role, or pass-role scope is broad | IAM policy review | narrow policy |
| STOP-ROLLBACK | deploy | rollback target or authority missing | rollback record | define rollback or staging-only first deploy |
| STOP-OBSERVABILITY | verify | health, logs, alarms, or smoke evidence missing | deployment evidence | add signals before promotion |
| STOP-COST-CAPACITY | exposure | traffic, quota, scaling, or budget controls missing | capacity model | keep private or add controls |

## Claim-To-Artifact Derivation Map

Source-to-rule derivation should use this map instead of treating the document
as one large prose blob.

| Source section | Target artifact family | Required checks or fixtures |
| --- | --- | --- |
| Source Projection Ownership | source projection manifest, derivation report | STOP-SOURCE-PROJECTION |
| Environment Promotion Matrix | GitHub release-control rules | deploy.github.missing-environment |
| Required Execution Variables | deploy-readiness manifest schema | manifest required-field validation |
| Deploy-Readiness Manifest Contract | deploy-readiness executable check | all deploy-readiness fixtures |
| Infrastructure Ownership And Drift | AWS runtime-boundary rules, AWS inspect workflow | STOP-IAC-DRIFT |
| GitHub Actions Policy | GitHub-to-AWS rules | deploy.actions.floating-refs |
| Supply-Chain Integrity Policy | supply-chain rules, build workflow checks | STOP-SUPPLY-CHAIN |
| AWS OIDC Policy | OIDC/IAM rules | deploy.oidc.broad-trust |
| IAM Permission Boundaries | IAM deploy-readiness checks | STOP-IAM-SCOPE |
| AWS Runtime Shape | ECS Fargate runtime rules | deploy.ecs.happy-path |
| Corpus Package And Runtime Freshness | RAG runtime freshness checks | deploy.corpus.stale |
| Context-Provider Data Boundaries | auth/data-boundary rules, selector fixtures | deploy.public-ingress.no-auth |
| API And MCP Surface | MCP exposure rules | deploy.mcp.write-tools |
| Security Requirements | threat-model checks | public exposure and write-tool fixtures |
| Observability Requirements | logging/metrics/audit rules | STOP-OBSERVABILITY |
| Health Checks And Rollback | rollback rules, deploy verification | deploy.rollback.missing |
| Cost And Capacity Controls | cost/capacity rules | STOP-COST-CAPACITY |
| Incident Response And Disablement | incident and disablement rules | failed rollback fixture |
| Evaluation Fixture Matrix | selector fixtures | fixture validator |
| Stop-Condition Table | stop-condition chunks and context packet gaps | all fixtures |

## Chunking Guidance

Derived chunks should preserve stable section identity and avoid oversized
context packets.

Chunk families:

- release-control chunk: GitHub workflow, environment, promotion, approvals.
- identity chunk: OIDC and IAM boundaries.
- runtime chunk: ECS Fargate task, service, network, ingress.
- corpus chunk: package, freshness, provenance, stale behavior.
- surface chunk: API/MCP auth, read-only exposure, tenant boundaries.
- safety chunk: supply chain, secrets, threat model.
- operations chunk: observability, health, rollback, incident response.
- cost/performance chunk: capacity, SLO, autoscaling, quotas, budget.
- stop-condition chunk: compact stop table.

Each chunk should carry:

- source path and section id
- corpus id
- deployment phase
- required variables
- required checks
- stop conditions
- related rule ids
- source references

Target chunk size should be small enough for context packets to include the
minimum evidence bundle without pulling the entire source document.

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
  `https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services`
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
