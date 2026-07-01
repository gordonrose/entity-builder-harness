<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.02-rag-rulebook.ecs-fargate.cloudformation.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Explain the CloudFormation templates for the RAG/rulebook ECS Fargate staging deployment.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: infra.04-deploy.02-rag-rulebook.ecs-fargate.readme
  path: infra/04.deploy/02.rag-rulebook/ecs-fargate/README.md
- id: github.workflow.deploy-rag-rulebook-staging
  path: .github/workflows/deploy-rag-rulebook-staging.yml
-->
# CloudFormation

These templates define the first staging deployment path for the
RAG/rulebook service on ECS Fargate.

## Templates

- `github-oidc-bootstrap.yml` creates the GitHub Actions deployment role and,
  when needed, the GitHub OIDC provider. This is a one-time bootstrap template
  and must be applied from an already-approved AWS administrator session.
- `foundation.yml` creates reusable staging service foundations: ECR
  repository, log group, service token secret, ECS task roles, service security
  group, target group, host rule, and `rag.kanbien.com` Route53 alias.
- `service.yml` creates or updates the ECS task definition and service using
  an immutable image digest.

The templates intentionally reuse the existing `kanbien-staging-alb` and
wildcard `*.kanbien.com` certificate to avoid a second ALB for this MSP.

## Execution Order

1. Apply `github-oidc-bootstrap.yml` from a local approved AWS admin session.
2. Configure the GitHub `staging` environment and repository variable
   `RAG_RULEBOOK_AWS_DEPLOY_ROLE_ARN` with the bootstrap output.
3. Run `.github/workflows/deploy-rag-rulebook-staging.yml` after the branch is
   merged to remote `main`.

The GitHub workflow applies `foundation.yml`, builds and pushes the image to
ECR, resolves the immutable ECR digest, and applies `service.yml`.

## Bootstrap Command

The current AWS account inspection found no existing GitHub OIDC provider, so
the first bootstrap can create one:

```bash
aws cloudformation deploy \
  --profile gordon-kanbien \
  --region eu-west-1 \
  --stack-name rag-rulebook-staging-github-oidc \
  --template-file infra/04.deploy/02.rag-rulebook/ecs-fargate/cloudformation/github-oidc-bootstrap.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    GitHubRepository=gordonrose/entity-builder-harness \
    GitHubEnvironment=staging \
    DeployRoleName=github-rag-rulebook-staging-deploy
```

After bootstrap, get the role ARN:

```bash
aws cloudformation describe-stacks \
  --profile gordon-kanbien \
  --region eu-west-1 \
  --stack-name rag-rulebook-staging-github-oidc \
  --query "Stacks[0].Outputs[?OutputKey=='DeployRoleArn'].OutputValue | [0]" \
  --output text
```

Add that value as the GitHub repository/environment variable:

```text
RAG_RULEBOOK_AWS_DEPLOY_ROLE_ARN
```

The GitHub `staging` environment must exist before the workflow can deploy.
Configure it with branch restriction to `main`. If required reviewers are not
enabled for staging, keep the readiness manifest's reviewer fields false and
treat them as remaining risk until a human approval path is added.

## Runtime Shape

The first MSP image embeds the deterministic RAG/rulebook runtime cache during
the Docker build. That keeps ECS simple for the first hosted test. A later
corpus-package split can move runtime artifacts to a separate immutable package
once package storage and freshness checks are mature.

## Stop Conditions

Do not apply these templates when:

- the AWS profile/account is not `337159794548`
- the region is not `eu-west-1`
- the deploy is not for `staging`
- the GitHub environment is missing or unprotected
- the image is not addressed by digest for the ECS service update
- rollback target evidence is not recorded after the first successful deploy
