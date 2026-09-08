<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.targets.readme
version: 1
status: active
layer: 04.deploy
domain: infra.observability
disciplines:
- architecture
- sre
kind: target-catalogue
purpose: Index product deployment targets and their canonical alert policies without duplicating policy values.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.source-material.03-product.platform-target-alerting-policy
  path: docs/04.deploy/source-material/03.product/platform-target-alerting-policy.md
-->
# Product Deployment Targets

This is the human-scannable index of product deployment targets. It links to
each target's canonical policy rather than copying thresholds or provider
settings into a second, drifting catalogue.

## Alert Policy Catalogue

| Target | Canonical policy | Current policy IDs | IaC implementation | Operator response |
| --- | --- | --- | --- | --- |
| Kanbien / staging | [target profile](kanbien/staging/target-profile.yml) | `alb-unhealthy-targets`, `alb-5xx-spike`, `ecs-running-count-mismatch`, `ecs-high-cpu`, `ecs-high-memory` | [foundation alerting](kanbien/staging/cloudformation/foundation/alerting.yml) and [service alarms](kanbien/staging/cloudformation/service.yml) | [staging alarm runbook](../../../../docs/aws/runbooks/platform-shell-staging-alarms.md) |

When a target is added, add one row linking its `target-profile.yml`, its
implementation source, and its runbook. Keep the policy values only in that
target profile.

The reusable definition standard is
[Platform Target Alerting Policy](../../../../docs/04.deploy/source-material/03.product/platform-target-alerting-policy.md).
