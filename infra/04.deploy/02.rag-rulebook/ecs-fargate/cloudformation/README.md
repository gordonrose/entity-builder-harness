<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.02-rag-rulebook.ecs-fargate.cloudformation.readme
version: 1
status: active
created_on: "2026-07-01"
updated_on: "2026-10-25"
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

The hosted RAG target is retired. These templates preserve its teardown and
shared-resource ownership; do not use them to recreate the deployment.

- `service.yml` permits only `DesiredCount=0`.
- `foundation.yml` retains the CloudWatch log group and service-token secret,
  keeps log retention at 14 days, and explicitly deletes ECR images with the
  dedicated repository. Schedule the retained secret for deletion with recovery
  after deleting the stack.
- `github-oidc-bootstrap.yml` preserves the account-wide GitHub OIDC provider
  and removes the dedicated RAG deployment role. Never delete its stack wholesale.

The cluster, ALB/listener, wildcard certificate, VPC/subnets and DNS hosted zone
are shared and remain intact. Compare these templates with live templates and
inspect bounded change sets before applying any update. Use the
[hosted staging retirement procedure](../../../../../.agentic/aws/workflows/deploy-rag-rulebook-service.md#hosted-staging-retirement)
for account verification, inventory, ordering, local retrieval proof and results.

Historical bootstrap/deployment instructions and evidence remain in Git history
and commit logs. Restoring deployment requires a new reviewed and approved change.
