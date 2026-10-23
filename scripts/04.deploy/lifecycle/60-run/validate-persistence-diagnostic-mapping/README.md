<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.validate-persistence-diagnostic-mapping.readme
version: 3
status: active
created_on: "2026-10-23"
updated_on: "2026-10-23"
layer: 04.deploy
domain: deployment.persistence-diagnostics
disciplines: [security, sre, agentic]
kind: documentation
purpose: Explain deterministic validation of safe persistence diagnostic mappings in scope contracts.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.command.validate-active-workload-health-recovery
  path: scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh
-->
# Validate Persistence Diagnostic Mapping

This read-only command requires every new-framework scope to declare whether
persistence diagnostics are inapplicable or provide complete, workload-aware,
provider-neutral mappings for an explicitly classified required persistence
dependency.

```bash
bash scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.sh \
  --scope-contract infra/04.deploy/03.product/targets/<target>/20-scopes/<scope>/00-declaration/declaration-contract.yml \
  --workload-binding infra/04.deploy/03.product/targets/<target>/20-scopes/<scope>/10-workload-binding/workload-binding.yml \
  --json
```

It rejects omitted coverage, unknown or duplicate codes, unsupported record
fields, uncontrolled summaries or next checks, incomplete workload coverage,
false non-applicability claims including declared writes, a server response that would turn dependency
unavailability into replacement, and completion-task HTTP/reconnect behaviour.
It validates declaration structure only. Adapter translation, including proof
that raw provider errors cannot enter emitted diagnostics, provider access,
target routing, and live failure proof remain separate requirements.
