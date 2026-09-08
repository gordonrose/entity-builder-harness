<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-observability-prerequisites.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- sre
- security
kind: capability-readme
purpose: Explain the read-only preflight that protects the platform-shell ECS running-task alarm from being deployed without its telemetry prerequisite.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-observability-prerequisites
  path: scripts/04.deploy/verify-platform-shell-observability-prerequisites/script.sh
-->
# Platform-Shell Observability Prerequisite Check

This read-only script is the deployment preflight for the platform-shell
running-task alarm. It checks two separate facts:

1. The existing ECS cluster has `containerInsights=enhanced`.
2. CloudWatch has actually received the `ECS/ContainerInsights`
   `RunningTaskCount` metric for the named cluster and service.

The first is configuration; the second is evidence that configuration is
producing the metric that the alarm will evaluate. Both are required. The
script does not create, update, or delete AWS resources, and it prints only a
pass/fail summary rather than metric data or application logs.

Run it under the governed AWS inspection workflow:

```bash
# Check the staging cluster and platform-shell service using the selected AWS profile.
bash scripts/04.deploy/verify-platform-shell-observability-prerequisites/script.sh --profile kanbien-dev --region eu-west-1 --cluster kanbien-staging --service kanbien-staging-platform-shell
```

The deploy workflow runs the same check after it acquires its narrowly scoped
OIDC credentials and before it changes the service stack. A failure is a
deliberate block, not a reason to weaken missing-data settings or skip the
alarm.
