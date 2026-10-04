<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.smoke-test-platform-shell-image.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Explain the local image smoke test for the platform shell.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.script.smoke-test-platform-shell-image
  path: scripts/04.deploy/smoke-test-platform-shell-image/script.sh
-->
# Smoke Test Platform Shell Image

`script.sh` builds and runs the local platform shell image, then verifies:

- `GET /livez`
- `GET /readyz`
- that all five relational Stage 6 entrypoints load and fail only through their
  reviewed safe outcome path when isolated from their target configuration.

The command runs locally only. It does not publish, deploy, call AWS, or mutate
GitHub.

If `DOCKER_CONFIG` is unset, the script uses
`.cache/04.deploy/docker-config` so Docker CLI metadata remains writable in
sandboxed local shells.

## Usage

```bash
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh
```

To qualify an already published immutable image without rebuilding it locally:

```bash
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh \
  --image registry.example/platform-shell@sha256:<digest>
```

For environments without a running Docker engine:

```bash
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh --allow-skip-without-engine
```
