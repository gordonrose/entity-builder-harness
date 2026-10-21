<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.core-server-package-custody.readme
version: 2
status: active
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines: [architecture, security, sre]
kind: script-guide
purpose: Explain static verification of the target-bound core-server package-custody workflow.
portability: { class: internal, targets: [] }
used_by:
  - id: deploy.command.kanbien-core-platform.core-server-package-custody
    path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/script.sh
created_on: "2026-10-20"
updated_on: "2026-10-21"
-->
# Core Server Package Custody Workflow Check

This target-bound package check confirms the only publication workflow is manual, protected-environment-bound, main-only, digest-based, and unable to deploy a workload. It makes no provider call.
