<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-infrastructure.readme
version: 6
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

It prevents accidental broadening of the first public deployment: the task
must remain ALB-only, rate-limit state must remain encrypted, short-lived, and
least-privileged, the WAF must scope every rule to the new hostname, the image
must be pinned by digest, and the container must remain secret-free and
read-only. It also verifies that the target declares the governed alert-policy
standard, points to the link-only target catalogue, uses the declared severity
vocabulary, and keeps every CloudFormation alarm aligned with its canonical
target-profile definition. For the metric path it accepts only two explicit
states: `prepared-not-deployed`, or `deployed-and-query-proven`. The latter
must retain safe evidence that CloudWatch PromQL returned both reviewed series,
while still recording any SLO and exporter-loss coverage gaps. A static check
does not query AWS; it prevents source metadata from claiming a vague or
unbounded delivery state.

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

Run it with:

```bash
npm run platform:shell:infrastructure:check
```

This static check complements, rather than replaces, AWS CloudFormation
validation and a reviewed change set. Those later checks validate the rendered
template against the selected account and reveal the specific shared-ALB change
before execution.
