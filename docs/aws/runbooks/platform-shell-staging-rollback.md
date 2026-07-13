<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.runbooks.platform-shell-staging-rollback
version: 1
status: draft
layer: 04.deploy
domain: infra.operations
disciplines:
- sre
kind: runbook
purpose: Define the Kanbien staging platform shell rollback procedure before first AWS deploy.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
- id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
  path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
-->
# Platform Shell Staging Rollback

## Scope

This runbook covers rollback for the Kanbien staging product platform shell on
ECS Fargate.

Target profile:
`infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml`

Readiness manifest:
`infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml`

This runbook does not approve AWS mutation by itself. Run mutating commands only
through `.agentic/aws/workflows/execute-approved-aws-change.md` after explicit
approval in the current chat.

## Rollback Policy

Primary rollback target: previous known-good ECS task definition revision.

Fallback rollback target: previous known-good platform-shell image digest,
registered into a new ECS task definition revision if the prior task definition
cannot be reused.

Rollback authority: Gordon Rose, with LLM-assisted command planning.

## Before First Deploy

There is no previous platform shell ECS task definition until the first
successful deployment exists. Before first deploy, record:

- current ECS service name, if created
- current ECS task definition ARN, if created
- current platform-shell image digest
- target group ARN
- ALB health-check path
- post-deploy smoke result

If the first deploy fails before a known-good revision exists, disable or remove
the platform shell ALB host rule instead of rolling back to an unknown target.

## Rollback Steps

1. Confirm the AWS target.

   - profile: `kanbien-dev` or the selected GitHub OIDC deploy role
   - region: `eu-west-1`
   - cluster: `kanbien-staging`
   - service: `kanbien-staging-platform-shell`

2. Inspect current service state.

   ```bash
   aws ecs describe-services \
     --profile kanbien-dev \
     --region eu-west-1 \
     --cluster kanbien-staging \
     --services kanbien-staging-platform-shell
   ```

3. Select the previous known-good task definition ARN from deployment evidence.

   Use the latest recorded previous task definition in the deploy evidence. If
   that value is missing, stop and use the fallback image-digest path.

4. Update the ECS service to the previous task definition.

   ```bash
   aws ecs update-service \
     --profile kanbien-dev \
     --region eu-west-1 \
     --cluster kanbien-staging \
     --service kanbien-staging-platform-shell \
     --task-definition <previous-task-definition-arn> \
     --force-new-deployment
   ```

5. Wait for service stability.

   ```bash
   aws ecs wait services-stable \
     --profile kanbien-dev \
     --region eu-west-1 \
     --cluster kanbien-staging \
     --services kanbien-staging-platform-shell
   ```

6. Verify ALB target health and application smoke proof.

   ```bash
   aws elbv2 describe-target-health \
     --profile kanbien-dev \
     --region eu-west-1 \
     --target-group-arn <platform-shell-target-group-arn>
   ```

   Then verify:

   - `https://staging.platform.kanbien.com/livez`
   - unauthenticated protected route returns `401`
   - authenticated caller without `smoke:read` returns `403`
   - authenticated caller with `smoke:read` succeeds

7. Record rollback evidence.

   Update the readiness or deployment evidence with:

   - rollback start and end time
   - previous task definition ARN
   - restored task definition ARN
   - image digest restored
   - ECS service stability result
   - ALB target health result
   - smoke proof
   - operator/approver

## Fallback Image Digest Path

Use this only when the previous task definition cannot be reused but a previous
known-good image digest exists.

1. Register a new task definition revision using the previous image digest and
   the last known-good task settings.
2. Update the ECS service to that new task definition revision.
3. Run the same stability, target-health, smoke, and evidence steps.

## Failed Rollback

If rollback cannot restore health:

1. Stop public exposure by removing or disabling the platform shell ALB host
   rule for `staging.platform.kanbien.com`.
2. Keep the existing Kanbien staging ALB and unrelated services untouched.
3. Record failed rollback evidence and the disablement action.
4. Do not attempt another mutating change until a new approved AWS change plan
   exists.
