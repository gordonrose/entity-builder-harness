<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.targets.kanbien.staging.cloudformation.readme
version: 1
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- security
- sre
- architecture
kind: capability-readme
purpose: Explain the target-specific CloudFormation boundary for the Kanbien staging platform-shell deployment.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: aws.plan.kanbien-staging-platform-shell-initial-deployment
  path: docs/aws/kanbien-staging-platform-shell-initial-deployment-plan.md
-->
# Kanbien Staging Platform-Shell CloudFormation

These templates define a new platform-smoke workload. They do not manage or
replace the legacy public-site service, its data stores, the shared ALB, the
wildcard certificate, the existing Cognito machine client, or the existing ECR
repository.

`foundation.yml` creates the dedicated resources that are safe to review as one
unit: the task security group, target group, hostname rule and DNS alias,
rate-limit table, task roles, log group, host-scoped WAF policy, and alarms.
It takes every pre-existing AWS resource as an input. The WAF association is a
shared-ALB operation, so its host scope and the live listener priority must be
reviewed in an AWS change set before it is applied.

`service.yml` creates or updates the Fargate task definition and ECS service.
It accepts only an immutable `repository@sha256:...` image reference. It cannot
select a mutable image tag, inject a Cognito client secret, or use an arbitrary
security group. The final task has no writeable root filesystem and no ECS exec
session access.

The foundation also creates `kanbien-staging-platform-shell-service-deploy`, a
CloudFormation execution role that can manage the ECS task definition and this
service while passing only its two task roles. The GitHub deployment identity
is deliberately not given direct access to the shared ALB, DNS, WAF, database,
or task roles. It may pass this execution role only for the service stack.

Both templates are **draft infrastructure** until the execution checklist in
the deployment plan has been satisfied. Running a CloudFormation operation is
an AWS mutation and requires a separately reviewed, explicit approval in the
current chat.
