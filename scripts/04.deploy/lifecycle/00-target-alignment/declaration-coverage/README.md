<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.script.declaration-coverage.readme
version: 2
status: active
created_on: "2026-10-06"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.declaration-coverage
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Explain offline declaration coverage for implementation and proof references.
portability:
  class: source-only
  targets: []
used_by:
- id: deploy.workflow.declaration-coverage
  path: .agentic/04.deploy/workflows/declaration-coverage.md
-->
# Declaration Coverage

The offline checker validates the requirement chain embedded in actual indexed
`deploy/target-scope-contract/v1` declarations as `change_impact`.

```bash
bash scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh --scope-contract infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml --json
bash scripts/repo/check-selection/smoke-test.sh
```

It checks declared implementation/consumer paths, unique requirements, owners,
expectations, check references, proof categories, valid explicit non-applicability
and existing program/workload execution sources. It emits `covered` or `gap`.
Coverage means the proof path exists; it does not mean those proofs passed.

The [schema and guide](../../../../../.agentic/04.deploy/schemas/change-impact.v1.guide.md)
bridge the existing Declaration Coverage Standard to target scope declarations.
The repository check catalog owns commands and stage/effect classifications;
existing generic health/secret/persistence validators own scope semantics.
No provider calls, secret reads or target mutations occur here.
