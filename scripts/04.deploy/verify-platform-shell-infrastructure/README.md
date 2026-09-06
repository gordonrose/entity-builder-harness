<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-infrastructure.readme
version: 1
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

`script.sh` is a non-mutating static policy gate for the two Kanbien staging
platform-shell CloudFormation templates. It needs PyYAML and makes no AWS API
calls.

It prevents accidental broadening of the first public deployment: the task
must remain ALB-only, rate-limit state must remain encrypted, short-lived, and
least-privileged, the WAF must scope every rule to the new hostname, the image
must be pinned by digest, and the container must remain secret-free and
read-only.

Run it with:

```bash
npm run platform:shell:infrastructure:check
```

This static check complements, rather than replaces, AWS CloudFormation
validation and a reviewed change set. Those later checks validate the rendered
template against the selected account and reveal the specific shared-ALB change
before execution.
