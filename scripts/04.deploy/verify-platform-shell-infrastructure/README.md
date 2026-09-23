<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-infrastructure.readme
version: 9
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the static policy gate for Kanbien staging platform-shell infrastructure.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-infrastructure
  path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh
-->
# Verify Platform-Shell Infrastructure

`script.sh` is a non-mutating static policy gate for the Kanbien staging
platform-shell service template and the rendered foundation template. It first
renders the focused foundation source units into a temporary file, needs
PyYAML, and makes no AWS API calls.

It prevents accidental broadening of the first public deployment: the server
task must remain ALB-only, the worker must have no inbound network path,
rate-limit state must remain encrypted, short-lived, and least-privileged, and
the worker may receive and settle only its source SQS queue. The WAF must scope
every rule to the new hostname; the image must stay pinned by digest; and both
task containers must stay secret-free and read-only. The check also requires
an SQS-encrypted DLQ/redrive policy, the existing SNS destination's narrow
Budgets publish policy, and the $25 `service=platform-shell` budget source.

It verifies that the target declares the governed alert-policy standard,
points to the link-only target catalogue, uses the declared severity
vocabulary, and keeps every CloudFormation alarm aligned with its canonical
target-profile definition. Server metric series retain their live delivery
status; worker series retain a separately bounded consumer and fixed-query
observation record. A static check does not query AWS; it prevents source
metadata from claiming a vague or unbounded delivery state.

It also invokes the dedicated synthetic-scheduler policy check. That check
binds the one redacted controlled-token smoke command to an isolated GitHub
OIDC role that can read only its declared secret. The first manual invocation
proves the fixed controlled request path, while the first clock-triggered run
remains separately required evidence. The nominal four-hour GitHub schedule is
deliberately labelled best effort: it creates recurring boundary observations,
but cannot by itself prove telemetry coverage or a customer SLO. The wider
closure policy still requires a future metric-freshness signal and exporter-loss
rehearsal, plus bounded `403`, `429`, WAF, alert, and rollback exercises. Those
entries make the remaining work visible; they do not claim it has been run.

The same gate validates the guarded worker-consumer rehearsal source. That
rehearsal requires a separately explicit live-operation flag, insists that the
worker and both queues are empty before it starts, sends two harmless
platform-smoke jobs 75 seconds apart, and returns the worker service to desired
count zero. It establishes the fresh-counter metric observation too; it is not
permission to activate a business queue producer or to treat direct SQS
delivery as a durable outbox.

Run it with:

```bash
npm run platform:shell:infrastructure:check
```

This static check complements, rather than replaces, AWS CloudFormation
validation and a reviewed change set. Those later checks validate the rendered
template against the selected account and reveal the specific shared-ALB change
before execution.
