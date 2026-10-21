<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: infra.04-deploy.03-product.targets.kanbien-core-platform.cloudformation.readme
  version: 2
  status: active
  created_on: "2026-10-20"
  updated_on: "2026-10-21"
  layer: 04.deploy
  domain: deployment.bootstrap-runtime
  disciplines:
  - architecture
  - security
  - sre
  kind: infrastructure-guide
  purpose: Explain the review-only CloudFormation boundary for the isolated core target.
  portability:
    class: internal
    targets: []
  used_by:
  - id: aws.plan.kanbien-core-platform-e1-foundation-change-set
    path: docs/aws/kanbien-core-platform-e1-foundation-change-set.md
-->
# Core Platform CloudFormation

`tag-bootstrap.yml` is E2a's only change: it creates an empty, tagged ECR
repository so AWS can activate the `Target` cost-allocation tag. `foundation.yml`
is E2c's private foundation after that activation has propagated.
`bootstrap-runtime.yml` is E4's private workload stack. It requires an E3
immutable image digest and never accepts a tag as an image identity. It creates
the server service and the dormant one-shot verifier task definition, but does
not run the verifier itself. No file may be applied without its separately
approved AWS change set.
