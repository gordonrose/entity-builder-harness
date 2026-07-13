# Chat Session: 2026-07-12-17-52 create-reusable-platform-shell-target-profile-before-first-a

<!-- agentic-session
id: 2026-07-12-17-52-create-reusable-platform-shell-target-profile-before-first-a
task: create reusable platform shell target profile before first AWS deploy
branch: chat/2026-07-12-17-52-create-reusable-platform-shell-target-profile-before-first-a
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-12-17-52-create-reusable-platform-shell-target-profile-before-first-a-2476334825
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-07-12T16:52:36Z
transcript_provider:
transcript_path:
transcript_bytes:
transcript_source:
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

create reusable platform shell target profile before first AWS deploy

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made

- Add `target-profile.yml` as the reusable non-secret decision feed for the
  Kanbien staging product platform shell before first AWS mutation.
- Keep `deploy-readiness.yml` as the proof/blocker manifest and reference the
  target profile instead of making readiness the only source of target
  decisions.
- Use `gordonrose164@hotmail.com` as the Kanbien staging platform shell budget
  alert email destination.
- Allow `http://localhost:3000` as a local development CORS origin in addition
  to the selected Kanbien production/staging origin policy.
- Use `/livez` as the ALB health-check path for first AWS deploy, while keeping
  `/readyz` authenticated and covered by deployed smoke proof.
- Use manual GitHub deployment approval for Kanbien staging platform shell
  deploys from `main`.
- Keep the initial Cognito scope mapping minimal:
  `platform-shell/smoke.read` maps to `smoke:read`.
- Use AWS Secrets Manager for Cognito client secret material.
- Use previous ECS task definition as the primary rollback target and previous
  image digest as the fallback target.
- Send CloudWatch alarm notifications to `gordonrose164@hotmail.com`.
- Use hybrid AWS mutation style: governed manual AWS CLI for narrowly approved
  bootstrap prerequisites, then GitHub Actions/OIDC for repeatable build and
  deploy.

## Context Hygiene

- Kept this slice planning-only: no AWS resources, DNS records, Cognito pools,
  secrets, budgets, or ECS services were created.
- Stored only non-secret config decisions and secret reference names; no secret
  values were requested or committed.
- On 2026-07-13, performed the approved governed manual AWS bootstrap mutation
  to create the ECR repository `platform-shell`; no DNS, Cognito, ECS, ALB,
  secrets, or budget resources were created.
- On 2026-07-13, performed the approved governed manual AWS bootstrap mutation
  to create the GitHub OIDC deploy role
  `github-platform-shell-staging-deploy`; no DNS, Cognito, ECS, ALB, secrets,
  or budget resources were created.
- On 2026-07-13, performed the approved AWS mutations to create the Cognito
  machine-auth target and store the generated app client secret in AWS Secrets
  Manager without printing or committing the secret value.

## Activity Log

### 2026-07-12T16:52:36Z - Session started

Initial intent: create reusable platform shell target profile before first AWS deploy

### 2026-07-12T16:52:36Z - Added reusable target profile slice

- Added `infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml`
  for reusable client/environment/product/runtime/auth/CORS/secrets/ops
  decisions.
- Updated platform shell deploy readiness to reference the target profile as a
  reusable decision feed.
- Updated the platform shell readiness verifier to validate the optional target
  profile path and schema when present.

### 2026-07-12T16:58:32Z - Verified reusable target profile slice

- Ran `git diff --check`.
- Ran the governed platform shell deploy-readiness verifier in blocked planning
  mode against the Kanbien staging manifest; it remained blocked with 13 known
  blockers and accepted the target profile reference.
- Ran `scripts/04.deploy/verify-platform-shell-deploy-readiness/smoke-test.sh`.

### 2026-07-12T17:17:16Z - Recorded budget alert and local CORS decisions

- Updated the target profile budget alert destination to the selected email
  address.
- Added `http://localhost:3000` as the selected local development CORS origin.
- Mirrored selected CORS and operations ownership/budget/rollback fields into
  deploy readiness so remaining blockers reflect unresolved proof and runbook
  work instead of already-selected decisions.

### 2026-07-12T17:20:22Z - Selected ALB health-check path

- Set the platform shell target profile ALB health check to `/livez`.
- Kept `/readyz` authenticated in the readiness manifest and recorded deployed
  smoke tests as the path for proving deeper application readiness.

### 2026-07-13T13:16:19Z - Recorded deploy policy and rollback decisions

- Updated the target profile and readiness manifest for manual GitHub staging
  deployment approval from `main`.
- Confirmed the minimal Cognito machine scope mapping and AWS Secrets Manager
  secret source.
- Added `docs/aws/runbooks/platform-shell-staging-rollback.md` and wired it as
  the rollback runbook.
- Recorded CloudWatch alarm notifications to the selected email destination.
- Left the manual-AWS-vs-GitHub-OIDC execution style unresolved pending
  explanation.

### 2026-07-13T13:22:31Z - Selected hybrid AWS mutation style

- Recorded governed manual AWS CLI as the bootstrap mutation style for narrowly
  approved prerequisites such as creating the `platform-shell` ECR repository.
- Recorded GitHub Actions/OIDC as the repeatable build and deploy path after
  the OIDC role is selected.
- Kept the repeatable GitHub OIDC role and trust as explicit readiness
  blockers.

### 2026-07-13T13:29:10Z - Created platform shell ECR repository

- Refreshed AWS SSO for profile `kanbien-dev`.
- Verified `platform-shell` did not exist in ECR account `337159794548` region
  `eu-west-1`.
- Ran the approved governed manual bootstrap mutation:
  `aws ecr create-repository --profile kanbien-dev --region eu-west-1 --repository-name platform-shell --image-tag-mutability IMMUTABLE --image-scanning-configuration scanOnPush=true --encryption-configuration encryptionType=AES256`.
- Verified the created repository:
  - ARN: `arn:aws:ecr:eu-west-1:337159794548:repository/platform-shell`
  - URI: `337159794548.dkr.ecr.eu-west-1.amazonaws.com/platform-shell`
  - Created at: `2026-07-13T13:28:30.347000Z`
  - Tag mutability: `IMMUTABLE`
  - Scan on push: `true`
  - Encryption: `AES256`
- Updated target profile and deploy readiness evidence for the created ECR
  repository.

### 2026-07-13T13:37:19Z - Created platform shell GitHub OIDC deploy role

- Verified the AWS account already had the GitHub OIDC provider:
  `arn:aws:iam::337159794548:oidc-provider/token.actions.githubusercontent.com`.
- Verified no existing role named `github-platform-shell-staging-deploy`
  existed.
- Added auditable IAM trust and permission policy documents under
  `infra/04.deploy/03.product/targets/kanbien/staging/iam/`.
- Created role:
  `arn:aws:iam::337159794548:role/github-platform-shell-staging-deploy`.
- Attached inline policy `platform-shell-staging-deploy`.
- Tightened the live trust policy to require:
  - audience `sts.amazonaws.com`
  - repository `gordonrose/entity-builder-harness`
  - ref `refs/heads/main`
  - subject `repo:gordonrose/entity-builder-harness:environment:staging`
- Verified the live role, trust policy, and inline policy from AWS.
- Updated target profile and deploy readiness evidence for the created role.

### 2026-07-13T13:44:44Z - Created Cognito machine-auth target

- Verified no existing Cognito user pool named `kanbien-staging-platform-shell`
  existed in `kanbien-dev` `eu-west-1`.
- Verified the secret name
  `kanbien/staging/platform-shell/cognito-machine-client` did not exist before
  creation.
- Created Cognito user pool:
  - ID: `eu-west-1_EQaXioA1n`
  - ARN: `arn:aws:cognito-idp:eu-west-1:337159794548:userpool/eu-west-1_EQaXioA1n`
  - Name: `kanbien-staging-platform-shell`
- Created Cognito resource server `platform-shell` with scope `smoke.read`.
- Created hosted Cognito domain
  `kanbien-staging-platform-shell-337159794548`; verified status `ACTIVE`.
- Created confidential app client:
  - Name: `platform-shell-staging-machine-client`
  - Client ID: `4n7kuqstbvb97ur3btbur8afjt`
  - Grant: `client_credentials`
  - Scope: `platform-shell/smoke.read`
- Piped the Cognito app client secret directly into AWS Secrets Manager without
  printing it:
  `arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-machine-client-ibNhn5`.
- Recorded issuer, JWKS URI, token URL, app client ID, and secret ARN in the
  target profile and readiness manifest.

### 2026-07-13T13:48:27Z - Ran commit-prep validation

- Ran `git diff --check`.
- Parsed the platform shell IAM trust and permission JSON artifacts with
  Node's JSON parser.
- Ran the governed platform shell deploy-readiness verifier in blocked planning
  mode; readiness remained blocked with 7 known blockers.
- Ran `scripts/04.deploy/verify-platform-shell-deploy-readiness/smoke-test.sh`.
- Attempted `npm run check:static`; the repository does not define that script.
- Attempted `npm run platform:shell:image:smoke`; Docker was not running or
  reachable in this environment.
- Ran `scripts/04.deploy/smoke-test-platform-shell-image/script.sh
  --allow-skip-without-engine`, which skipped because Docker was unavailable.
- Refreshed generated artifact recognition sources after the commit gate found
  the new rollback runbook artifact was not indexed yet.

## Sub-Agent Activity

- None recorded yet.

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This slice separates target-specific deployment decisions from
readiness evidence under the existing product/platform and AWS deployment
boundaries; it does not change runtime architecture or authorize AWS mutation.

## RAG Knowledge Disposition

Status: covered
Reason: Platform shell target profile decision-feed knowledge is captured in
the deploy target profile and readiness verifier evidence.
Evidence:
- `infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml`
- `infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml`
- `scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh`
- `docs/aws/runbooks/platform-shell-staging-rollback.md`
- `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-platform-shell-staging-deploy-trust.json`
- `infra/04.deploy/03.product/targets/kanbien/staging/iam/github-platform-shell-staging-deploy-policy.json`
Corpus gaps:
- None.

## Session Metrics

Raised at UTC: 2026-07-12T16:52:36Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.
