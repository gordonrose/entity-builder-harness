<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.script.assess-platform-shell-artifact-drift.readme
  version: 1
  status: active
  layer: 04.deploy
  domain: runtime.operations
  disciplines:
  - security
  - sre
  kind: capability-readme
  purpose: Describe the safe administrator-only drift refresh for the staging deployment-artifact stack.
  portability:
    class: internal
    targets:
    - kanbien/staging
  used_by:
  - id: deploy.script.assess-platform-shell-artifact-drift
    path: scripts/04.deploy/assess-platform-shell-artifact-drift/script.py
-->
# Deployment-Artifact Active Drift Assessment

The scheduled GitHub reconciler is intentionally read-only and cannot start
CloudFormation drift detection. This target-scoped administrator command
refreshes the missing artifact-store stack fact before a reconciliation needs
it. It detects and polls only the fixed deployment-artifact stack, accepts only
an in-sync outcome, and writes a short-lived `0600` safe evidence record under
`/tmp`.

It never reads resource details, bucket policy content, object content,
credentials, or provider payloads. It does not execute a change set or alter
the stack.

```bash
npm run platform:shell:artifact-active-drift-assessment -- \
  --execute-approved-active-artifact-drift-assessment \
  --evidence-file /tmp/new-safe-evidence.json \
  --json
```
