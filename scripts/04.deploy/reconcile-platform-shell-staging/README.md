<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.reconcile-platform-shell-staging.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the fail-closed Kanbien staging deployment reconciliation command.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.reconcile-platform-shell-staging
  path: scripts/04.deploy/reconcile-platform-shell-staging/script.py
-->
# Platform-Shell Staging Deployment Reconciliation

This command is the mandatory boundary between a reviewed infrastructure plan
and an AWS mutation. It makes no provisioning change. It validates the source
policy, then checks only the declared account, Foundation and artifact-stack
state, CloudFormation drift, private artifact-bucket controls, and the
tag-scoped monthly budget. Its output contains only check identifiers and a
verdict; it never prints provider responses, endpoints, resource contents,
secrets, or change-set details.

If AWS cannot be verified, the result names the owning safe control (for
example, `artifact-bucket-controls-verification-unavailable`) rather than a
generic provider error. It remains fail-closed, but now tells the operator
which bounded reconciliation area needs investigation without revealing the
provider response.

The check runs its AWS calls serially and each call has three bounded attempts
with short backoff. This avoids creating an avoidable burst of CloudFormation,
S3, and Budgets requests while still failing closed if the declared control
cannot be verified.

Use it in two modes:

- `continuous` is the read-only scheduled guard. A failed check makes the
  GitHub workflow fail visibly rather than silently accepting drift.
- `pre-foundation-change-set` is run immediately before a reviewed Foundation
  change set is executed. It rechecks every direct mutation prerequisite,
  including the Foundation's current drift state and all artifact-bucket and
  budget controls; the scheduled mode owns the separate artifact-stack drift
  scan. It then requires exactly the 22 approved additions and one
  non-replacement SNS topic-policy update. Any extra, missing, or replacement
  change blocks execution.

```bash
npm run platform:shell:deployment-reconciliation -- --validate
npm run platform:shell:deployment-reconciliation -- --mode pre-foundation-change-set --foundation-change-set reviewed-name
```

The command is a deployment control, not a substitute for review: it detects
drift and prevents scope creep, while a current approved change set still
defines the authorised mutation.
