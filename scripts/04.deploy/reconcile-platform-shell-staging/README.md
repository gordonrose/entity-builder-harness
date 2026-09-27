<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.reconcile-platform-shell-staging.readme
version: 2
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
state, fresh passive CloudFormation drift evidence, private artifact-bucket
controls, and the tag-scoped monthly budget. Its output contains only check identifiers and a
verdict; it never prints provider responses, endpoints, resource contents,
secrets, or change-set details.

If AWS cannot be verified, the result names the owning safe control (for
example, `artifact-bucket-public-access-control-verification-unavailable`)
rather than a generic provider error. Each artifact-bucket read is an
independent check, so a failure identifies the exact control without revealing
a provider response. The command remains fail-closed: a passed neighbouring
control never masks an unavailable one.

GitHub does not start CloudFormation drift scans. AWS can require dependent
provider reads for every resource type in a stack, and assigning those reads to
the GitHub role would create a broad, hidden permission boundary. Instead this
command requires a recent `IN_SYNC` stack summary and reports whether the
evidence is missing, stale, or not in sync. A separate target-scoped detector
is planned behind the reviewed resource-read contract in
`infra/04.deploy/03.product/targets/kanbien/staging/drift-detection/`.

The check runs its AWS calls serially and each call has three bounded attempts
with short backoff. This avoids creating an avoidable burst of CloudFormation,
S3, and Budgets requests while still failing closed if the declared control
cannot be verified.

Use it in two modes:

- `continuous` is the read-only scheduled guard. A failed check makes the
  GitHub workflow fail visibly rather than silently accepting drift.
- `pre-foundation-change-set` is run immediately before a reviewed Foundation
  change set is executed. It rechecks every direct mutation prerequisite,
  including fresh passive evidence for both stacks and all artifact-bucket and
  budget controls. It then requires exactly the 22 approved additions and one
  non-replacement SNS topic-policy update. Any extra, missing, or replacement
  change blocks execution.

```bash
npm run platform:shell:deployment-reconciliation -- --validate
npm run platform:shell:deployment-reconciliation -- --mode pre-foundation-change-set --foundation-change-set reviewed-name
```

The command is a deployment control, not a substitute for review: it detects
drift and prevents scope creep, while a current approved change set still
defines the authorised mutation.

- `pre-relational-stage6-service-change-set` is run immediately before the
  isolated relational reference proof's Service-stack change set. It permits
  exactly five new non-public PostgreSQL task definitions, the three normal
  immutable-image task-definition revisions, and the two in-place service
  references. It rejects every other resource, replacement, or stack. This
  separates image publication from deployment while still making the
  deployment scope mechanically reviewable.

  It also requires two short-lived target-admin assessment records: the
  classified Foundation record (which accepts only the known RDS parameter
  normalisation) and an `IN_SYNC` record for the fixed Service stack. The
  artifact bucket itself is verified through its current encryption, ownership,
  public-access, lifecycle, and policy controls; a stale passive artifact
  stack timestamp cannot suppress those direct checks or authorize a change.

Before a Foundation change set can execute, the declared administrator profile
also compares the live GitHub inline policy with the reviewed JSON source. This
is deliberately a separate mode: GitHub proves its own usable operations in
the scheduled workflow; an administrator proves that AWS has not retained or
gained a different policy.

```bash
npm run platform:shell:deployment-reconciliation:role-policy-alignment
npm run platform:shell:deployment-reconciliation -- --mode pre-relational-stage6-service-change-set --service-change-set reviewed-name
```

- `pre-candidate-execution-preflight-onboarding-change-set` permits exactly
  one new dormant candidate task definition. When a historical service-stack
  rollback has completed, it requires a fresh candidate-baseline record that
  proves the stack is `IN_SYNC` and the fixed source service is at steady
  state. It does not authorize a routing, IAM, database, queue, or service
  change.

```bash
npm run platform:shell:service-active-drift-assessment -- \
  --candidate-onboarding \
  --execute-approved-active-service-drift-assessment \
  --evidence-file /tmp/candidate-baseline.json --json

npm run platform:shell:deployment-reconciliation -- \
  --mode pre-candidate-execution-preflight-onboarding-change-set \
  --service-change-set reviewed-name \
  --service-drift-evidence /tmp/candidate-baseline.json --json
```

- `pre-relational-stage6-bootstrap-recovery-service-change-set` is used only
  after the first Stage 6 Service composition already exists and a corrected
  immutable image must be rolled out before the one fixed bootstrap recovery.
  It permits no additions or removals. It permits only replacement revisions of
  the three normal and five already-declared relational task definitions, plus
  the two in-place ECS service references. The same fresh Foundation
  classification and in-sync Service assessment are required. Any IAM,
  queue, database, listener, routing, or other resource change fails closed.

```bash
npm run platform:shell:deployment-reconciliation -- --mode pre-relational-stage6-bootstrap-recovery-service-change-set --service-change-set reviewed-name --known-foundation-drift-evidence /tmp/fresh-foundation-evidence.json --service-drift-evidence /tmp/fresh-service-evidence.json
```
