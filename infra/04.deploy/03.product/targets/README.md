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

## Capability Metrics and SLO Catalogue

The same target profile is also the canonical location for capability metric
series and SLO policy. The entries below are discovery aids only: the target
profile owns their exact labels, buckets, populations, thresholds, retention,
and delivery state.

| Target | Canonical policy | Selected metric series | Selected SLOs | Delivery state |
| --- | --- | --- | --- | --- |
| Kanbien / staging | [target profile](kanbien/staging/target-profile.yml) | `platform-smoke-read-outcome`, `platform-smoke-read-request-response-latency` | `platform-smoke-interactive-read-availability`, `platform-smoke-interactive-read-latency-p95`, `platform-smoke-interactive-read-latency-p99` | Target composition and IaC are prepared and checked locally; no collector, IAM update, deployed metrics, dashboard, SLO query, or capability alarm exists in AWS yet. |

The initial selected AWS delivery path is the local-collector OpenTelemetry
adapter at
`platform/adapters/aws/observability/cloudwatch/`. It can only be composed by
the target after reviewed service IaC provides the collector, task-level
permissions, lifecycle wiring, coverage signal, and policy-to-IaC proof. The
prepared source is not a deployed telemetry path or a green SLO claim.
