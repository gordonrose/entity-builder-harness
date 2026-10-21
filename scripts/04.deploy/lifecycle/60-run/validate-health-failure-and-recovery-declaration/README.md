<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.validate-health-failure-and-recovery-declaration.readme
version: 1
status: active
created_on: "2026-10-21"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.runtime-safety
disciplines: [agentic, security, sre]
kind: documentation
purpose: Explain the deterministic validator for an embedded scope health, safe-failure, recovery, and proof declaration.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.verify-health-failure-and-recovery
  path: .agentic/04.deploy/60-run/workflows/verify-health-failure-and-recovery.md
-->
# Validate Health, Failure, and Recovery Declaration

Run this read-only command against a scope declaration contract:

```bash
bash scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.sh \
  --scope-contract infra/04.deploy/03.product/targets/<target>/20-scopes/<scope>/00-declaration/declaration-contract.yml
```

It checks the reusable declaration shape only. It does not call a provider,
execute a health endpoint, make a workload unhealthy, or accept a release.
The scope-specific route decides when its passed declaration and its named
proof commands are required.
