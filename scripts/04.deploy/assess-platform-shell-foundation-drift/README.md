<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.assess-platform-shell-foundation-drift.readme
version: 3
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded administrator-only Foundation drift classifier.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.assess-platform-shell-foundation-drift.shell
  path: scripts/04.deploy/assess-platform-shell-foundation-drift/script.sh
-->
# Foundation Drift Classifier

This temporary, administrator-only command refreshes evidence for the fixed
`kanbien/staging` Foundation stack. It first starts one CloudFormation drift
assessment and waits for completion. Only if the completed assessment reports
drift does it read the minimal structural resource-drift shape needed to
distinguish only the reviewed database-egress and PostgreSQL parameter-group
representation signatures from unrelated drift. For the parameter-group
signature it also verifies the attached RDS parameter still enforces
`rds.force_ssl=1`.

It never prints a detection identifier, physical identifier, expected value,
actual value, endpoint, secret, or provider response. Its short-lived `/tmp`
evidence file contains only the account, region, fixed stack, timestamp,
classification, and—when applicable—the approved logical resource, type, and
change category. It creates no role, policy, workload, resource, change set,
or stack update; GitHub remains unable to start active detection.

```bash
npm run platform:shell:foundation-active-drift-assessment -- \
  --execute-approved-active-foundation-drift-assessment \
  --evidence-file /tmp/new-safe-evidence.json --json
```

The output `known-remediation-required` means the reported differences
match only the reviewed structural signatures and include the
`RelationalDatabaseParameterGroup` representation change. It is a
classification, not an `IN_SYNC` passive-readiness verdict or permission to
apply a change. A fresh assessment on 2026-10-02 reported only that
parameter-group `remove` category while the effective TLS setting was
verified as required. The historical security-group egress correction is
already complete. A separate reviewed treatment is needed before passive
readiness can pass.
