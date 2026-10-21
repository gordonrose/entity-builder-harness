<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.kanbien-core-platform.prepare-candidate.readme
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
kind: documentation
purpose: Explain the fixed-target candidate preparation control.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.command.kanbien-core-platform.prepare-candidate
  path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/prepare-candidate/script.sh
-->
# Prepare Core-Platform Candidate

`script.sh` is the sole operator entrypoint for preparation of
`kanbien-core-platform/bootstrap-runtime`. It accepts no target selector. It
accepts only a qualified package-custody receipt. It derives the immutable
digest from that receipt and performs the bounded AWS alignment inspection for
the fixed account, region, foundation, roles, repository and runtime stack.

It cannot create a change set or alter a provider resource. Missing, stale, or
unavailable evidence—including an expired AWS login—blocks preparation without
falling back to a manually supplied identifier.
