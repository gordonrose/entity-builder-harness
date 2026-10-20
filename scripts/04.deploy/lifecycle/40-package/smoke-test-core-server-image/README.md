<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.command.smoke-test-core-server-image.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
- architecture
- security
- sre
kind: capability-readme
purpose: Explain the local smoke test for the core-server image candidate and its payload rejection proof.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.command.build-core-server-image
  path: scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh
-->
# Smoke Test Core Server Image

This command runs a local-only image qualification. Before Docker is used, it
proves the exact generated image command stays listening long enough to serve
liveness, readiness, and safe release verification. It also proves a compiled
payload passes its declared boundary and that an injected forbidden persistence
dependency fails with one safe diagnostic code.

With a working Docker daemon it builds the candidate image, starts it under a
read-only filesystem and no Linux capabilities, then checks liveness,
readiness, and the safe release-verification response.

```bash
bash scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh
```

`--allow-skip-without-engine` keeps the payload proof available on a machine
without Docker. It reports a skip rather than asserting image-start success.
