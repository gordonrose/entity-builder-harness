<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-deployment-reconciliation.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the static policy guard for staging deployment reconciliation.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-deployment-reconciliation
  path: scripts/04.deploy/verify-platform-shell-deployment-reconciliation/script.sh
-->
# Platform-Shell Deployment Reconciliation Policy Check

This static check locks the live reconciliation command to its reviewed
target, expected budget, exact PostgreSQL Foundation change-set scope,
read-only GitHub OIDC role, and validation-before-credentials workflow order.
It prevents an innocent source edit from silently broadening AWS permissions,
removing a live control, or turning a safe scheduled check into deployment.

```bash
npm run platform:shell:deployment-reconciliation:policy-check
```
