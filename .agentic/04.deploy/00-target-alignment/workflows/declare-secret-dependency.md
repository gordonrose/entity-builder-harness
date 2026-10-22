<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.declare-secret-dependency
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.secret-management
disciplines: [agentic, security, sre]
kind: workflow
purpose: Govern safe declaration and validation of a workload secret dependency before target alignment.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.standard.require-secret-dependency-declaration
  path: .agentic/04.deploy/00-target-alignment/standards/require-secret-dependency-declaration.md
- id: deploy.workflow.declaration-coverage
  path: .agentic/04.deploy/workflows/declaration-coverage.md
-->
# Declare a Secret Dependency

## Use When

Use when deployable work introduces or changes secret-supplied dependency
access. Do not use this workflow to create a secret, reveal a value, or grant
a provider permission.

## Procedure

1. Select the smallest affected scope and declare whether it has no secret
   dependencies or add one entry per credential purpose and access class.
2. Name the workload IDs authorised to receive each secret and choose the
   applicable `runtime`, `migration`, or `administrative` access class.
   `runtime` may support a limited verifier task as well as a server/worker;
   migration and administrative credentials are one-shot-task-only.
3. Record only a target-neutral reference ID and expected field names. Put
   concrete provider secret resources and role mappings in the provider
   realization when separately approved.
4. Define rotation and retirement owners, policies, and conditions. The
   supported delivery route uses replacement/new start, not live refresh. For a
   server/worker name startup and readiness effects; for a completion-only task
   name the unsuccessful completion outcomes and their safe diagnostic codes.
5. Run the secret-dependency validator and the active-scope inventory. Treat
   any failure as a declaration-coverage gap.
6. Before a provider mutation, use target alignment to prove the declared
   reference and authorised access safely. Do not read or record its value.

## Required Command

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action \
  scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.sh \
  --scope-contract infra/04.deploy/03.product/targets/<target>/20-scopes/<scope>/00-declaration/declaration-contract.yml \
  --json
```
