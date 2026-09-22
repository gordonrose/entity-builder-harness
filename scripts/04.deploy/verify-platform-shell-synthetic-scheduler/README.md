<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-synthetic-scheduler.readme
version: 1
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the static source-policy gate for the temporary Kanbien staging protected-route synthetic scheduler.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-synthetic-scheduler
  path: scripts/04.deploy/verify-platform-shell-synthetic-scheduler/script.sh
-->
# Verify Platform-Shell Synthetic Scheduler

This read-only check keeps the temporary staging synthetic deliberately narrow.
It validates the GitHub Actions workflow, its separate OIDC trust policy, and
its one-action IAM policy against the staging target profile and readiness
manifest.

The scheduler is intentionally not a generic job runner. Once separately
activated, it can read exactly one Cognito machine-client secret, obtain an
in-memory token, and make exactly one fixed protected `GET` request. It cannot
write AWS resources, alter identities, select arbitrary URLs, use GitHub
repository secrets, or receive deployment/ECR permissions.

Its `17 */4 * * *` cadence is a best-effort GitHub Actions schedule, not a
guaranteed interval and not SLO or telemetry-coverage proof. The later platform
scheduler contract and adapter will replace this target-specific bridge.

Run the check with:

```bash
npm run platform:shell:synthetic-scheduler:check
```

The check neither contacts GitHub nor AWS. Source preparation does not create
the IAM role or activate the scheduled workflow; those are separate governed
external changes.
