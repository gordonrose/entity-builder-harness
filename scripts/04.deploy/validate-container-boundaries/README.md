<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.validate-container-boundaries.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Explain the read-only container boundary validator that prevents Dockerfile sprawl.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.script.validate-container-boundaries
  path: scripts/04.deploy/validate-container-boundaries/script.sh
- id: deploy.script.validate-container-boundaries.smoke-test
  path: scripts/04.deploy/validate-container-boundaries/smoke-test.sh
-->
# Validate Container Boundaries

`script.sh` checks that deployable container image definitions stay inside the
governed infra image boundary.

Allowed Dockerfile path shape:

```text
infra/<deploy-layer>/<deploy-track>/image/Dockerfile
```

Each Dockerfile must have:

- sibling `README.md`
- an effective ignore file:
  - `image/.dockerignore` when the image directory is the build context
  - `image/Dockerfile.dockerignore` or repo-root `.dockerignore` when the repo
    root is the build context

Ignore files must cover git internals, caches, `commitLogs`, env files,
credentials/secrets, logs, temporary output, dependency folders, and generated
runtime caches. The validator fails weak or empty ignore files.

The command is read-only. It does not build images, run containers, call AWS,
call GitHub, publish to ECR, or mutate files.

## Usage

```bash
bash scripts/04.deploy/validate-container-boundaries/script.sh
```

For JSON output:

```bash
bash scripts/04.deploy/validate-container-boundaries/script.sh --json
```

For smoke tests or alternate roots:

```bash
bash scripts/04.deploy/validate-container-boundaries/script.sh --root /path/to/repo
```
