<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.declare-persistence-diagnostic-mapping
version: 3
status: active
created_on: "2026-10-23"
updated_on: "2026-10-23"
layer: 04.deploy
domain: deployment.persistence-diagnostics
disciplines: [security, sre, agentic]
kind: workflow
purpose: Govern safe persistence diagnostic declaration and validation before a scope can claim dependency readiness.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.verify-health-failure-and-recovery
  path: .agentic/04.deploy/60-run/workflows/verify-health-failure-and-recovery.md
-->
# Declare Persistence Diagnostic Mapping

## Use When

Use when a scope introduces, changes, recovers, or retires a required
persistence dependency. This workflow does not create a provider resource,
retrieve a credential, read target state, or perform a live rehearsal.

## Required sequence

1. Classify persistence dependencies explicitly in `dependencies.persistence`.
   Declare `persistence_diagnostics.status: not-applicable` only with a reason,
   explicit `persistence` exclusion, an empty classification, and no migration,
   server-mediated, or declared-write persistence usage. Otherwise declare the required logical
   dependency and the controlled taxonomy for each affected workload.
2. Use only provider-neutral codes and the closed diagnostic-record shape. Use
   the controlled safe summary and next-check values; do not include raw values
   or a guessed provider cause.
3. For a dependency-bearing server, preserve liveness as the provider
   replacement signal and use readiness for dependency availability. For a
   completion task, use completion behaviour; do not add HTTP health checks.
4. Declare whether each persistence workload performs writes. For migrations,
   map timeout and uncertain completion to release block plus
   fresh state observation. Do not allow automatic replay.
5. Run the diagnostic-mapping validator and active-scope inventory. Treat a
   failure as a declaration-coverage gap. Before acceptance, separately prove
   the actual adapter mapping, target implementation, and applicable live
   failure behaviour.

## Required command

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action \
  scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.sh \
  --scope-contract infra/04.deploy/03.product/targets/<target>/20-scopes/<scope>/00-declaration/declaration-contract.yml \
  --workload-binding infra/04.deploy/03.product/targets/<target>/20-scopes/<scope>/10-workload-binding/workload-binding.yml \
  --json
```
