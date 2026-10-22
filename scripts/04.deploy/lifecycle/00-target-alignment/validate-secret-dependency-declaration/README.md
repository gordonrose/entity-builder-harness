<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.validate-secret-dependency-declaration.readme
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.secret-management
disciplines: [agentic, security, sre]
kind: documentation
purpose: Explain the offline validator for non-secret workload dependency declarations.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.command.validate-secret-dependency-declaration
  path: scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.sh
-->
# Validate Secret Dependency Declaration

This read-only validator checks the provider-neutral secret dependency portion
of one scope contract. It does not read a secret store, call a provider, or
print secret material. It validates declaration shape and common unsafe
formats; it is not a replacement for repository secret scanning.

Concrete provider secret references, permissions, delivery mechanisms, target
isolation, and live rotation proof remain provider-binding and target-alignment
work. An ARN is a reference, not a secret value, but it is intentionally
excluded from this portable contract.

Every active new-framework scope is checked through the active-workload
inventory gate. A future persistence scope must run this command directly
during declaration coverage and will be checked again when it enters that
target's active scope inventory.
