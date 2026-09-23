<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.run-platform-shell-metric-coverage.readme
version: 2
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded staging server metric-coverage/SLO evaluator and separate worker delivery-metric observation.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.run-platform-shell-metric-coverage
  path: scripts/04.deploy/run-platform-shell-metric-coverage/script.sh
-->
# Run Platform-Shell Metric Coverage

This command turns the target profile's reviewed metric-coverage policy into a
signed CloudWatch PromQL query. It is deliberately target-owned: generic
platform modules do not know CloudWatch, SNS, AWS credentials, the staging
hostname, or an alert topic.

Its default server `coverage` mode asks one question: did the reviewed successful
`platform-smoke.smoke.read` outcome counter increase inside the declared
bounded window? It returns only `observed`, `missing`, `query-failed`, or
`notification-failed`. An observed metric means only that the coverage check
saw its expected evidence; it never means the SLO is healthy. Every
non-observed verdict marks affected SLO confidence as `insufficient-confidence`.

The fixed `--coverage-target worker` mode asks a narrower question: did the
declared `platform-smoke.rebuild` worker-delivery counter advance with its
approved success labels after the bounded worker rehearsal? It cannot query a
caller-supplied metric or labels, calculate an HTTP SLO, or publish an alert.
It is evidence that the worker telemetry path delivered one controlled job,
not evidence that a future business outbox or workflow is duplicate-safe.

The optional `slo` mode derives the target's availability, p95, and p99 PromQL
queries from the profile. It returns aggregate values and a confidence-aware
state. It cannot create observations, add labels, query an arbitrary metric,
or write a dashboard.

The optional notification flag may publish a fixed, redacted JSON verdict to
the one existing target-owned SNS topic. It never sends a token, query,
request/response body, provider response, metric labels, or customer data.

Run an offline policy check with:

```text
npm run platform:shell:metric-coverage -- --validate
```

After a governed worker rehearsal, inspect its fixed delivery counter with:

```text
npm run platform:shell:metric-coverage -- --coverage-target worker
```

The live command requires an explicit AWS-authorised execution context. Use
the target profile's local profile only during a governed operator action, or
the isolated GitHub OIDC environment credentials in the coverage workflow.
