<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.command.kanbien-core-platform.prepare-candidate.readme
version: 1
status: draft
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
checks only safe repository declarations for the core runnable program, image,
scope, and planned target.

While E0 facts remain unresolved it exits non-zero with a deterministic JSON
report containing `blocked-live-target-not-selected` and safe fact identifiers.
It never reads a provider, registry, credentials, or a live target.
