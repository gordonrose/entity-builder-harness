<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.validate-active-workload-health-recovery.readme
version: 2
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.runtime-safety
disciplines: [agentic, security, sre]
kind: documentation
purpose: Explain the target scope inventory gate for workload-type-aware health and recovery declarations.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.command.core-platform-target-declaration
  path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh
-->
# Validate Active Workload Health and Recovery

Run this read-only command at a target's `20-scopes` directory. It checks that
every candidate active new-framework scope directory is listed, requires its
own canonical declaration and binding files, checks their target/scope
identities, invokes the generic workload-type and secret-dependency validators,
and permits legacy exceptions only for named retiring reference workloads.

```bash
bash scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh \
  --target-root infra/04.deploy/03.product/targets/<target>/20-scopes --json
```

It does not contact a provider, create workloads, or accept a release.

This command is automatically invoked today by the fixed
`kanbien-core-platform` target-declaration gate and its release-contract gate.
The package-publication GitHub Actions workflow invokes that release-contract
gate. Other targets are not covered until their target/release gates explicitly
route through an equivalent inventory command.
