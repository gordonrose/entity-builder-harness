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

The command runs locally only. It does not publish, deploy, call AWS, or mutate
GitHub.

If `DOCKER_CONFIG` is unset, the script uses
`.cache/04.deploy/docker-config` so Docker CLI metadata remains writable in
sandboxed local shells.

## Usage

```bash
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh
```

For environments without a running Docker engine:

```bash
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh --allow-skip-without-engine
```


## Bound local qualification

Use `--qualify-local` first to invoke the existing operational-realization
capability. This mode requires persistent scratch storage and the verified
package cache; explicit `--acquire-base` separately obtains the pinned public
runtime base. It freshly builds the payload, checks the exact image contents,
runs isolated local server health/shutdown checks and emits closed safe JSON.
Skipped execution cannot pass. Target tasks, including PostgreSQL bootstrap,
remain separately pending. No result grants release or operation authority.

See [qualification commands and boundaries](../operational-realization-gate/README.md#exact-local-container-qualification).
The ordinary legacy invocation retains its previous behavior and receives no
qualification credit from a different image or mode.
