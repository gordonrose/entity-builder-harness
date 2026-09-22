<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-metric-coverage.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the static policy gate for the staging metric-coverage verifier.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-metric-coverage
  path: scripts/04.deploy/verify-platform-shell-metric-coverage/script.sh
-->
# Verify Platform-Shell Metric Coverage

This static, non-mutating check locks the staging metric-coverage verifier to
one target-owned metric, five safe capability labels, one bounded query window,
and one existing SNS alert topic. It checks the target profile, readiness
manifest, GitHub workflow, role policy, trust policy, package entry points, and
command source together.

The check deliberately rejects any ability to read a Cognito secret, call a
route, change deployment resources, publish an image, query an arbitrary
metric, add a high-cardinality label, alter the schedule, or send an alert to
another destination. It complements live IAM read-back and rehearsal evidence;
it cannot prove that GitHub, CloudWatch, SNS, or the operator mailbox worked.

Run it with:

```text
npm run platform:shell:metric-coverage:policy-check
```
