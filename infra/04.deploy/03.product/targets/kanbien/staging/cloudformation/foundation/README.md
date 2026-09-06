<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.targets.kanbien.staging.cloudformation.foundation.readme
version: 1
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- security
- sre
kind: capability-readme
purpose: Explain the responsibility-focused source units that render the Kanbien staging platform-shell foundation template.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.cloudformation.foundation
  path: infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation.yml
-->
# Platform-Shell Foundation Source Units

These files are the human-readable source for one Kanbien staging
platform-shell CloudFormation foundation stack. They are combined by the
repository renderer; they are not independent AWS stacks.

| File | Responsibility | Main AWS resources |
| --- | --- | --- |
| `template.yml` | Template metadata and approved inputs from existing AWS infrastructure. | Parameters only |
| `public-ingress.yml` | How public traffic enters through the shared ALB and reaches healthy platform tasks. | service security group, target group, host rule, DNS alias |
| `edge-protection.yml` | Host-scoped web-request protection at the shared ALB. | WAF web ACL and association |
| `workload-iam.yml` | Least-privilege identities used by AWS workload components. It is not end-user authorization. | ECS task roles and service deployment role |
| `rate-limiting.yml` | Shared, encrypted fixed-window limiter state for the public runtime. | DynamoDB table |
| `logging.yml` | Short-retention operational log destination. | CloudWatch log group |
| `alerting.yml` | Availability alarms and their operator-notification channel. | CloudWatch alarms, SNS topic, topic policy, email subscription |
| `outputs.yml` | Values deliberately exported to the separate service stack. | Outputs only |

The division is by responsibility rather than one file per AWS resource. For
example, the ALB rule and target group remain together because they form one
traffic-entry path; the SNS topic and alarms remain together because they form
one alert-delivery path.

`foundation.yml`, one level above this directory, lists these files in the
deterministic rendering order. Run the static infrastructure check after any
change:

```bash
npm run platform:shell:infrastructure:check
```

That check renders the source units, confirms the exact reviewed resource set,
and then verifies the critical least-privilege, ingress, WAF, logging, and
alerting invariants. A reviewed AWS change set is still required before any
cloud change.
