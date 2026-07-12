<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.inventory.kanbien-staging-platform-shell-target-inspection
version: 1
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- sre
- architecture
kind: inventory
purpose: Record read-only Kanbien staging AWS inspection evidence for platform shell target planning.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
  path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
-->
# Kanbien Staging Platform Shell Target Inspection

## Scope

Read-only inspection for the platform shell staging target.

- Workflow: `.agentic/aws/workflows/inspect-aws-state.md`
- Profile: `kanbien-dev`
- Region: `eu-west-1`
- Inspected at UTC: `2026-07-11T22:24:12Z`
- Mutation: none

## Inspected State

The existing Kanbien staging AWS boundary is real and active:

- Account: `337159794548`
- ECS cluster: `arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-staging`
- Cluster status: `ACTIVE`
- Active services: `rag-rulebook-staging`, `service-platform`
- ALB: `arn:aws:elasticloadbalancing:eu-west-1:337159794548:loadbalancer/app/kanbien-staging-alb/29ac325385686357`
- ALB DNS: `kanbien-staging-alb-1575766066.eu-west-1.elb.amazonaws.com`
- ALB scheme: `internet-facing`
- VPC: `vpc-0063b6c3d2d781f3c`
- ALB security group: `sg-08d590b0aee6e2e60`
- ALB subnets: `subnet-05d385e4d57b18032`, `subnet-0397df802e31ff6fe`
- HTTPS certificate: `arn:aws:acm:eu-west-1:337159794548:certificate/c1e57be6-9744-471c-a390-548a3252f631`

The existing `service-platform` ECS service is not selected as the product
platform shell target:

- Service: `arn:aws:ecs:eu-west-1:337159794548:service/kanbien-staging/service-platform`
- Current task definition: `arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-staging-service-platform:12`
- Container image: `337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien/service-platform:public-site-brochure-20260529-7`
- Target group: `arn:aws:elasticloadbalancing:eu-west-1:337159794548:targetgroup/kanbien-staging-app-tg/889e44db1e0160fb`
- Target group health path: `/v1/health`
- Log group: `/ecs/kanbien-staging-service-platform`

This differs from the platform shell proof, which expects the product platform
shell image, `/livez`, `/readyz`, and the `products/kanbien-platform` smoke
composition.

Other inspected deployment facts:

- Existing ECR repositories: `rag-rulebook-service`, `kanbien/service-platform`
- No platform shell ECR repository was found during this inspection.
- Existing Route 53 aliases to the staging ALB: `kanbien.com`, `www.kanbien.com`, `rag.kanbien.com`
- HTTPS host rule exists for `rag.kanbien.com`.
- No platform shell hostname or host rule is selected.
- Cognito user pools returned by `list-user-pools`: none.

## Planning Conclusion

The product platform shell can likely reuse the existing Kanbien staging AWS
boundary as a candidate account, region, cluster, VPC, ALB, subnets, and
certificate boundary, but this inspection does not select or mutate the runtime
target.

The platform shell still needs explicit selection or creation of:

- GitHub deployment workflow and OIDC role;
- ECR repository and immutable image provenance;
- ECS server service, task definition, target group, and host rule;
- server-first, worker-capable ECS project shape with a reserved worker
  service/task-family slot and explicit worker activation condition;
- Cognito user pool, app client, issuer, and JWKS URI;
- CORS origins and product shell hostname;
- secret/config source;
- log group, alarms, budget, owner, escalation path, rollback target, rollback
  authority, and rollback runbook;
- deployed smoke proof for `/livez`, `/readyz`, protected dummy route, logs,
  routing, and rollback.
