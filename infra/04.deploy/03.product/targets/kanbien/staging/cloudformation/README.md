<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.targets.kanbien.staging.cloudformation.readme
version: 2
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

`foundation.yml` is the composition manifest for the dedicated resources that
are safe to review as one unit. Its focused source files live in
[`foundation/`](foundation/README.md): public ingress, edge protection,
workload IAM, shared rate limiting, logging, alerting, and stack outputs. The
renderer combines them into one transient CloudFormation template, so AWS still
receives one foundation stack and no nested-stack or resource-ownership change
is introduced.

[`deployment-artifact-store.yml`](deployment-artifact-store.yml) is deliberately
outside that foundation stack. It is a tiny bootstrap stack for an encrypted,
private, target-owned S3 bucket that holds transient reviewed CloudFormation
templates when a rendered foundation exceeds AWS's 51,200-byte inline limit.
It holds deployment blueprints only—not application records, database data,
credentials, or product documents—and expires `change-sets/` objects after 30
days. Separating it prevents a circular dependency: the bucket must exist
before CloudFormation can fetch the larger foundation template.

The foundation takes every pre-existing AWS resource as an input. The WAF
association is a shared-ALB operation, so its host scope and the live listener
priority must be reviewed in an AWS change set before it is applied.

Render the deployable template locally with:

```bash
bash scripts/04.deploy/render-platform-shell-foundation-template/script.sh --output /tmp/platform-shell-foundation.yml
```

The renderer is run by the static policy gate and GitHub workflow before AWS
template validation. Do not edit or commit the rendered output.

`service.yml` creates or updates the Fargate task definition and ECS service,
plus the alarms whose metric dimensions belong to that one service: running
task count, CPU utilisation, and memory utilisation. It accepts only an
immutable `repository@sha256:...` image reference. It cannot select a mutable
image tag, inject a Cognito client secret, or use an arbitrary security group.
The final task has no writeable root filesystem and no ECS exec session access.

The prepared metric-delivery update adds a second, task-local ADOT collector
container. The application sends OTLP/HTTP only to `127.0.0.1:4318`; the
collector signs the onward CloudWatch request using the ECS task role. Its
non-secret pipeline configuration is a named SSM Parameter Store record, read
by the ECS execution role at task startup. This avoids storing AWS credentials
or a large opaque configuration blob in application code. ECS task roles are
shared by all containers in a task, so the fixed loopback listener and reviewed
task definition are important complementary controls. None of this is live
until a separately reviewed CloudFormation change set is applied.

This is intentionally different from `foundation/alerting.yml`. The foundation
owns the shared SNS topic and ALB target-group alarms because they are shared
dependencies. The service stack owns alarms that name this service and derive
their `ClusterName` and `ServiceName` dimensions from its inputs. The
target-profile alarm definitions are the source of the complete policy; the
static policy check verifies that both CloudFormation stacks implement them
without drift.

The foundation also creates `kanbien-staging-platform-shell-service-deploy`, a
CloudFormation execution role that can manage the ECS task definition and this
service while passing only its two task roles. The GitHub deployment identity
is deliberately not given direct access to the shared ALB, DNS, WAF, database,
or task roles. It may pass this execution role only for the service stack.

Both templates are **draft infrastructure** until the execution checklist in
the deployment plan has been satisfied. Running a CloudFormation operation is
an AWS mutation and requires a separately reviewed, explicit approval in the
current chat.
