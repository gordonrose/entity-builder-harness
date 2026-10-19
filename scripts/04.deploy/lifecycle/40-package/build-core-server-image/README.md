<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.command.build-core-server-image.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
- architecture
- security
- sre
kind: capability-readme
purpose: Explain the local package-stage core-server image build and payload qualification capability.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.command.smoke-test-core-server-image
  path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh
-->
# Build Core Server Image

This package-stage capability first reuses the R3 runnable-program contract
and dependency-boundary reports. It compiles the same declared program into a
temporary payload, adds only its generated runtime shims, and fails closed if
the payload contains an unapproved program or dependency.

When Docker is available it then builds the dedicated local candidate image.
It never publishes the image or selects a target.

```bash
bash scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh
```

Use `--allow-skip-without-engine` only to run the static package qualification
on a machine without a working Docker daemon. A skip does not claim an image
was built.
