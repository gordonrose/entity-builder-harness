<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.architecture.adr.0003-private-ecs-bootstrap-target-kanbien-core-platform
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.bootstrap-runtime
  disciplines:
  - architecture
  - security
  - sre
  kind: adr
  purpose: Select the private ECS Fargate bootstrap topology for the isolated Kanbien core-platform target.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: aws.plan.kanbien-core-platform-e1-foundation-change-set
    path: docs/aws/kanbien-core-platform-e1-foundation-change-set.md
-->
# ADR 0003: Use a Private ECS Bootstrap Target for Kanbien Core Platform

## Status

Accepted for E1 design. It does not authorise AWS mutation.

## Context

`kanbien-core-platform` starts from an absent baseline and must not reuse the
public staging service, its DNS, its data services, or its runtime access. The
first workload is a dependency-free HTTP server with a private release
verification route.

Read-only inspection identified an available candidate account and region, an
existing private VPC, and two private subnets. Those subnets have no NAT route
and currently have only an S3 gateway endpoint. They cannot currently pull a
private ECR image or send container logs to CloudWatch.

## Decision

Use a dedicated ECS Fargate cluster and a one-task bootstrap service in the
existing private subnets. This is an explicit, limited exception to the
``no staging resource reuse`` rule: the shared VPC and named private subnets
may be used, but no staging service, role, image repository, log group, DNS
record, data store, or security group may be reused or changed. The service
has no public IP, load balancer, DNS record, or public ingress.

The foundation will provide interface endpoints only for the AWS services the
first workload needs: ECR API, ECR DKR, and CloudWatch Logs. It will not add a
NAT gateway. It will not add an STS endpoint because the initial running
server has no AWS application permission; GitHub OIDC assumes its delivery
role outside this private network.

Private Cloud Map discovery and a narrowly scoped verifier task provide the
only route to `/internal/release-verification`. The server security group
accepts TCP 3000 only from that verifier security group.

## Consequences

- The target has a clear, small network and IAM boundary.
- Adding interface endpoints changes the shared VPC's private DNS resolution
  for ECR and CloudWatch Logs. E1 must show the endpoint policy and security
  group diff before this shared-foundation exception is executed.
- The initial workload uses an execution role to pull its image and emit logs,
  but intentionally has no task role and therefore no application AWS access.
- Two-AZ interface endpoints have a recurring charge. A target-specific
  monthly ceiling and alert destination must be approved before E2 execution;
  no staging budget is inherited.
- ECR image publication, target creation, and deployment remain separately
  approved E2--E7 operations.
