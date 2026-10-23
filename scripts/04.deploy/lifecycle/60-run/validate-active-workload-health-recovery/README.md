<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.validate-active-workload-health-recovery.readme
version: 3
status: active
created_on: "2026-10-22"
updated_on: "2026-10-23"
layer: 04.deploy
domain: deployment.runtime-safety
disciplines: [agentic, security, sre]
kind: documentation
purpose: Explain the target scope lifecycle and ownership gate for workload-type-aware health and recovery declarations.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.command.core-platform-target-declaration
  path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh
-->
# Validate Scope Lifecycle, Workload Health, and Recovery

Run this read-only command at a target's `20-scopes` directory. It inventories
every new-framework scope directory and requires each scope to declare its
lifecycle (`active`, `candidate`, or `accepted-historical`), canonical
declaration and binding files, and workload ownership. It validates health and
secret declarations for every indexed scope, prevents two active scopes from
owning the same bound workload, and verifies governed predecessor/successor
links for candidate and historical scopes. It permits legacy exceptions only
for named retiring reference workloads.

```bash
bash scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh \
  --target-root infra/04.deploy/03.product/targets/<target>/20-scopes --json
```

It does not contact a provider, create workloads, or accept a release.

An `accepted-historical` scope preserves its canonical declarations and
accepted evidence but is not an active deployment owner. A `candidate` may
overlap its active predecessor's intended workload ownership while it is being
proved; it cannot become active until its predecessor becomes historical in a
separately governed release transition. Do not flip lifecycle state in response
to a provider error: candidate rejection leaves the predecessor active, and a
later reversion requires the existing release/recovery authority and evidence.

This command is automatically invoked today by the fixed
`kanbien-core-platform` target-declaration gate and its release-contract gate.
The package-publication GitHub Actions workflow invokes that release-contract
gate. Other targets are not covered until their target/release gates explicitly
route through an equivalent inventory command.
