<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.plan.iaas-release-control.p15-source-regression
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines: [architecture, security, sre]
  kind: record
  purpose: Record the focused local P01–P15 source regression and the next externally gated inputs.
  portability: {class: internal, targets: [kanbien/staging]}
  used_by:
  - id: deploy.plan.iaas-release-control-progress
    path: docs/04.deploy/plans/iaas-release-control-progress.md
-->
# P15 source regression record — 2026-10-01

This record covers the uncommitted P01–P15 source working tree based on Git
revision `5c437a3c14971e03a1ba63941d5aa14f109cbbc6`. It is local verification,
not a hosted, publication, target, or authority receipt.

| Area | Command result |
| --- | --- |
| P01 release definition | 29 tests passed in 64.942 seconds |
| P04 selected admission | 9 tests passed in 6.362 seconds |
| P05–P07 lifecycle | 5 tests passed in 7.116 seconds |
| P05–P07 action journal | 26 tests passed in 13.752 seconds |
| P08–P09 control plane | 6 tests passed in 0.620 seconds |
| P10 authenticated transport | 6 tests passed in 0.174 seconds |
| P10 selected store/readback | 31 tests passed in 0.617 seconds |
| P11–P13 caller route/guard | 5 tests passed in 6.800 seconds |
| P14 workflow source | 1 test passed |
| **Focused total** | **118 tests passed** |

The current diff and cached-diff checks passed. The candidate and relational
wrapper validation modes also passed without contacting AWS. Every local source
result keeps release eligibility and operation authorization blocked.

P16 is prepared by the pinned, read-only workflow source and its static test.
P17–P18 are prepared by the selected-effect route’s required-receipt contract:
a reviewed artifact publication and its admission evidence must be supplied;
the source boundary cannot synthesize either. P19 uses the existing passive
selected-readiness adapter with separately approved read-only AWS access. P20
uses the exact control-plane configuration and bound receipts to form a change,
cost, rollback and cleanup plan. None of P16–P20 was run here.

No AWS, GitHub, registry, DNS, secret, deployment, or provider action occurred.

