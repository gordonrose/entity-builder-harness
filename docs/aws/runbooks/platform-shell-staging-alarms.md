<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.runbook.platform-shell-staging-alarms
version: 1
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- sre
- security
kind: operational-runbook
purpose: Guide safe first response to a Kanbien staging platform-shell availability alarm without placing sensitive runtime data in repository records.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
-->
# Platform-Shell Staging: Alarm Response

## Scope and safety boundary

This runbook handles the five availability alarms declared in the Kanbien
staging target profile. It is for diagnosis and safe containment. It does not
authorise a deployment, credential recovery, data change, broad log export, or
automatic rollback. Use the [rollback runbook](platform-shell-staging-rollback.md)
for a separately authorised rollback.

Do not copy tokens, request bodies, customer data, IP addresses, raw log
entries, or subscription endpoints into a commit log, issue, or chat summary.
Record only the alarm name, state, time range, deployment/task-definition
revision, safe count/percentage summaries, action taken, and result.

## What each alarm means

| Alarm | Signal and threshold | First question | Initial safe response |
| --- | --- | --- | --- |
| `kanbien-staging-platform-shell-unhealthy-targets` | Fewer than one healthy ALB target for two 60-second periods. | Is a platform-shell task running and registered healthy? | Inspect target health, ECS service events, and the deployment revision. |
| `kanbien-staging-platform-shell-target-5xx` | At least five target 5xx responses in three of five one-minute periods. | Is this a real platform failure rather than an expected test or a narrow client issue? | Check the time window, target health, service events, and redacted operational summaries. |
| `kanbien-staging-platform-shell-ecs-running-count-mismatch` | Running task count is below the desired count for two 60-second periods. | Did the task fail, fail health checks, or is ECS replacing it? | Inspect desired/running/pending counts and service events. |
| `kanbien-staging-platform-shell-ecs-high-cpu` | Average CPU is at least 80% in three of five one-minute periods. | Is demand or a deployment causing sustained saturation? | Confirm the trend and inspect bounded service/task summaries. |
| `kanbien-staging-platform-shell-ecs-high-memory` | Average memory is at least 80% in three of five one-minute periods. | Is memory use sustained and approaching task limits? | Confirm the trend and inspect the current task definition and service events. |

The running-count alarm is meaningful only after the existing `kanbien-staging`
cluster has `containerInsights=enhanced`. The service-update preflight must
verify that prerequisite before this alarm is deployed. If telemetry is absent
after it was previously verified, treat that as an observability incident: do
not mark the service healthy merely because there is no data.

## First five minutes: diagnose without changing state

1. Confirm the exact alarm name, state transition time, and whether another
   declared alarm moved at the same time. A single alarm is a symptom; a
   correlated set usually points to one cause.
2. Check ECS desired, running, and pending task counts, then inspect only the
   recent service event summaries. Do not reproduce or save full log payloads.
3. Check the ALB target-health summary. A `running-count` and an
   `unhealthy-targets` alarm together usually indicate a workload/deployment
   problem; a healthy target with `5xx` more often indicates application
   behaviour.
4. Check the current service task-definition revision and compare it with the
   most recent known-good revision. A causal timing relationship is evidence,
   not proof, so confirm service events before deciding on rollback.
5. Record the safe summary in the governed operational evidence location. If
   rollback is needed, obtain its explicit authorisation and use the linked
   rollback runbook.

## Read-only inspection commands

Run these only with the approved `kanbien-dev` read-only inspection path. Each
command intentionally asks for summaries rather than application payloads.

```bash
# Show only the state and configured condition of the five declared alarms.
aws cloudwatch describe-alarms --profile kanbien-dev --region eu-west-1 --alarm-names kanbien-staging-platform-shell-unhealthy-targets kanbien-staging-platform-shell-target-5xx kanbien-staging-platform-shell-ecs-running-count-mismatch kanbien-staging-platform-shell-ecs-high-cpu kanbien-staging-platform-shell-ecs-high-memory --query 'MetricAlarms[].{name:AlarmName,state:StateValue,updated:StateUpdatedTimestamp,reason:StateReason}' --output table

# Show the ECS service counts and recent event messages without streaming application logs.
aws ecs describe-services --profile kanbien-dev --region eu-west-1 --cluster kanbien-staging --services kanbien-staging-platform-shell --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount,taskDefinition:taskDefinition,events:events[0:5].[createdAt,message]}' --output json

# Show only ALB target-health state and reason codes for the dedicated platform-shell target group.
aws elbv2 describe-target-health --profile kanbien-dev --region eu-west-1 --target-group-arn <platform-shell-target-group-arn> --query 'TargetHealthDescriptions[].{target:Target.Id,state:TargetHealth.State,reason:TargetHealth.Reason}' --output table
```

The last command needs the dedicated platform-shell target-group ARN from the
foundation stack or an approved inventory record. Do not substitute the legacy
site target group.

## After diagnosis

- If the service is recovering and the signal returns to `OK`, record the
  bounded summary and monitor until the next evaluation window has passed.
- If a task definition or deployment is implicated, stop here and use the
  governed rollback path; do not make an improvised service update.
- If an alert action did not deliver, keep the service incident and the alert
  delivery failure as two linked records. An alarm configuration is not proof
  that a human was notified.
- If a threshold is repeatedly noisy or unhelpful, propose a target-profile
  change with evidence. Do not edit an alarm in the AWS console, because that
  creates drift from the reviewed definition.
