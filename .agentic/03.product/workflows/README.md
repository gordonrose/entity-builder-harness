<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.workflows.readme
version: 1
status: active
layer: 03.product
domain: governance
disciplines:
- agentic
kind: workflow-index
purpose: List workflows for product and platform runtime work.
portability:
  class: source-only
  targets: []
used_by:
- id: artifact.agentic.routing-policy
  path: .agentic/routing-policy.yaml
-->
# 03.product Workflows

- `default.md` - placeholder workflow used by legacy task classification tests;
  do not use for real implementation work.
- `platform-runtime-implementation.md` - govern platform runtime shell
  implementation slices before real product app work begins.
