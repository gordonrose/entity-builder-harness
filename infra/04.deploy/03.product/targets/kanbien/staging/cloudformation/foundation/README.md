<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.targets.kanbien.staging.cloudformation.foundation.readme
version: 6
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
| `public-ingress.yml` | How public traffic enters through the shared ALB, while the worker and on-demand relay remain non-public. | server, worker, and relay security groups; target group, host rule, DNS alias |
| `public-tls.yml` | DNS-validated certificate ownership for the `platform.kanbien.com` hostname space and a narrowly scoped SNI attachment to the shared HTTPS listener. It does not replace that listener's existing default certificate. | ACM certificate, additional listener certificate |
| `edge-protection.yml` | Host-scoped web-request protection at the shared ALB. | WAF web ACL and association |
| `workload-iam.yml` | Least-privilege identities used by the public server and deployment components. It is not end-user authorization. The server may atomically accept one bounded smoke work item but cannot query, scan, delete, or administer the persistence table. | ECS server task roles and service deployment role |
| `worker-workload-iam.yml` | Least-privilege identity for one SQS consumer and its durable processing claim state. It cannot call the public limiter, Cognito, a DLQ, or relay a new message. | ECS worker task role |
| `relay-workload-iam.yml` | Least-privilege identity for one on-demand outbox relay pass. It may query/claim only due outbox records and send only to the source queue. | ECS relay task role |
| `work-queues.yml` | Durable encrypted source and dead-letter queues with SQS-owned retry counting and non-TLS denial. | SQS source queue, DLQ, and transport policies |
| `rate-limiting.yml` | Shared, encrypted fixed-window limiter state for the public runtime. | DynamoDB table |
| `persistence.yml` | Dedicated, non-business durable-delivery table for the bounded smoke workflow. It owns the adapter-required key/index shape and data-protection posture; the separately reviewed server task policy grants only its atomic acceptance write. | DynamoDB table and two global secondary indexes |
| `logging.yml` | Short-retention operational log destinations for the server, worker, and one-pass relay. | CloudWatch application, worker, and relay log groups |
| `observability-metrics.yml` | Versioned non-secret collector configuration shared by server and worker collectors. | SSM String parameter and collector log group |
| `alerting.yml` | Shared alert delivery and ALB target-group availability alarms. Service-specific ECS alarms remain in `../service.yml`, because only that stack owns their service dimensions. | CloudWatch alarms, SNS topic, topic policy, email subscription |
| `cost-controls.yml` | The initial service-tag-scoped monthly cost guardrail. It becomes attributable only after Billing activates the user cost-allocation tag and data arrives. | AWS Budget using the existing SNS topic |
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
and then verifies the critical least-privilege, ingress, queue, WAF, logging,
alerting, and cost-budget invariants. A reviewed AWS change set is still
required before any cloud change.
