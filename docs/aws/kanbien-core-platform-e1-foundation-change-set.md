<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.plan.kanbien-core-platform-e1-foundation-change-set
  version: 1
  status: draft
  layer: 04.deploy
  domain: deployment.bootstrap-runtime
  disciplines:
  - architecture
  - security
  - sre
  kind: aws-change-plan
  purpose: Define the exact proposed AWS foundation and workload additions for the isolated Kanbien core-platform rehearsal.
  portability:
    class: internal
    targets: []
  used_by:
  - id: aws.workflows.plan-aws-change
    path: .agentic/aws/workflows/plan-aws-change.md
  - id: aws.workflows.execute-approved-aws-change
    path: .agentic/aws/workflows/execute-approved-aws-change.md
  - id: aws.architecture.adr.0003-private-ecs-bootstrap-target-kanbien-core-platform
    path: docs/aws/architecture/adrs/0003-private-ecs-bootstrap-target-for-kanbien-core-platform.md
-->
# Kanbien Core Platform E1 Foundation Change Set

## Status

**Proposed, not executable.** This records the reviewed technical shape for
E1. It creates no AWS resource, does not publish an image, and does not select
an image digest. E2 may begin only after the two approval inputs at the end of
this document are supplied and the user approves the resulting exact
CloudFormation change sets.

## Selected candidate context

| Concern | Proposed selection | E0 evidence |
| --- | --- | --- |
| Account/profile | `kanbien-dev` candidate account | successful read-only caller identity |
| Region | `eu-west-1` | read-only regional inventory |
| Runtime | ECS Fargate | ADR 0003 |
| Network | Existing project VPC; two existing private subnets; no public IP | route-table and endpoint inspection |
| Public exposure | prohibited | target contract and ADR 0003 |

The target remains `planned-not-live-selected` until E1 approval is complete.
The VPC/subnets are a named shared-foundation exception approved by ADR 0003.
Nothing in this table permits reusing or modifying `kanbien/staging` services,
roles, images, logs, DNS, data, or security groups.

## Phased E2 creation

AWS cannot activate a user-defined cost-allocation tag until that tag has first
been attached to an AWS resource. The read-only activation attempt for `Target`
was rejected because the tag does not yet exist in this account. E2 is therefore
split deliberately:

1. **E2a — introduce the tag:** create only an empty, immutable ECR repository
   tagged `Target=kanbien-core-platform`. It has no image and no running
   workload. Stop after creation; do not create the cluster, endpoints, roles,
   or service.
2. **E2b — activate and wait:** activate the now-known `Target` tag through
   the account billing control, then wait for AWS cost-allocation propagation.
   Re-read the active tag state before continuing. The target budget is not
   treated as a guard before this succeeds.
3. **E2c — create the guarded foundation:** create the remaining foundation,
   with every billable target resource carrying the same `Target` tag and the
   approved USD 100/month budget filter.

Each phase has its own reviewed change set. The bounded E1--E7 execution packet
approved for this target authorizes the ordered phases and their ordinary
verification; it does not authorize resources outside the stated boundary.

## What E2c would add

One dedicated CloudFormation stack, `kanbien-core-platform-foundation`, would
add only the following resources:

| Resource | Why it exists | Boundary |
| --- | --- | --- |
| Immutable ECR repository | Holds only `kanbien-core-server` images | Created empty in E2a; later foundation consumes its exact ARN and URI rather than attempting a second repository |
| ECS cluster | Owns this target's tasks | Dedicated cluster; no staging service membership |
| CloudWatch log group | Receives bootstrap and verifier logs | Short approved retention; no secret or request-payload logging |
| ECS execution role | Lets AWS pull the selected image and write logs | ECR and log-stream permissions only |
| Service and verifier security groups | Limit private traffic | Server TCP 3000 accepts only verifier group; no public inbound rule |
| ECR API, ECR DKR and Logs interface endpoints | Lets private tasks pull images and write logs without NAT | Private DNS; endpoint group accepts HTTPS only from the two task groups |
| Cloud Map private namespace and service | Gives the verifier a private server name | No public DNS record or Route 53 public zone |
| GitHub OIDC delivery role | Lets the approved main-branch workflow publish and submit reviewed stack changes | Existing account OIDC provider only; repository/ref/workflow restricted; no staging access |

The foundation does **not** add a NAT gateway, public subnet route, load
balancer, TLS certificate, public DNS record, database, queue, secret,
application task role, or generic STS endpoint.

## What E4 would add after release A exists

A second stack, `kanbien-core-platform-bootstrap-runtime`, would be created
only with the immutable `repository@sha256:...` image URI recorded by E3.

| Resource | Required setting |
| --- | --- |
| ECS task definition | `kanbien-core-server`; Fargate; `awsvpc`; non-secret environment only; no task role |
| ECS service | Desired count one; private subnets; `AssignPublicIp: DISABLED`; deployment circuit breaker enabled |
| Cloud Map registration | Private name for the running server task |
| ECS verifier task definition | Same approved image, command overridden to make one bounded request to the private release-verification route |

The verifier runs only when E5/E7 asks for evidence. It receives no broad
AWS permission, cannot reach the public internet, and reports only a bounded
release verdict. It is not a standing public service.

## Delivery and permission model

The delivery workflow is manual-dispatch only, runs from protected `main`, and
uses GitHub OIDC. Its role will be narrowed to this target's ECR repository,
CloudFormation stack names, ECS cluster/service/task families, and the named
task execution role it may pass. It must not receive wildcard access to
staging, secrets, databases, queues, DNS, or IAM outside this target prefix.

The first foundation creation is a reviewed change set. The delivery workflow
may not silently create a replacement target or delete any stack. A failed
change set stops and records safe evidence; it does not retry or clean up
automatically.

## Expected E2--E7 sequence

1. E2a--E2c: create and inspect the cost-protected foundation in the three
   phases above.
2. E3: locally qualify release A, publish it to the new ECR repository, and
   record its immutable digest.
3. E4: create the workload stack with exactly that digest.
4. E5: run the private verifier; join workload digest, server identity, and
   package receipt; accept A only when all three agree.
5. E6: publish one harmless release B and update only the workload stack.
6. E7: verify B, retain A as the rollback digest, and write the receipt.

## Blast radius and recovery

The only proposed additions are named with the `kanbien-core-platform` prefix
and live in the selected private VPC. No existing service is modified. The
shared VPC receives three new private interface endpoints, so E1 must review
their DNS and security-group diff as a shared-foundation effect. If an E2
change fails, the process stops with the stack event evidence. No automated
delete, redeploy, or retry occurs. After A is accepted, B may roll back once
to retained digest A only through an explicitly approved workload-stack change
set.

## Approved controls and remaining execution input

The approved target budget ceiling is **USD 100/month**. The approved GitHub
Environment is **`kanbien-core-platform`**, with its required manual approval
owned by the repository owner. The workflow names that environment; its actual
reviewer setting remains a GitHub repository setting and is not represented as
a secret or a free-form workflow input.

The only execution-time value not stored in Git is the cost-alert recipient.
`CostAlertEmail` is a CloudFormation parameter, supplied only to the reviewed
E2 change set. It must be an address controlled by the approved cost owner and
must never be written to a receipt, log, commit, or command output.

**Current E1 blocker:** read-only account inspection found that the proposed
`Target` cost-allocation tag is not active. The target-scoped budget must not
be treated as a guard until E2a introduces the tag and E2b enables and verifies
the account-level billing control. Enabling it is a separate approved billing
setting mutation outside the foundation stack.

The exact templates are at:

```text
infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/
  foundation.yml
  bootstrap-runtime.yml
```

AWS mutation still requires a separate current-chat approval naming the stack
files, account/profile, region, parameter values, roles, and rollback path.
