<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-deploy-readiness.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Explain the read-only platform shell deploy-readiness verifier.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.script.verify-platform-shell-deploy-readiness
  path: scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh
-->
# Verify Platform Shell Deploy Readiness

`script.sh` validates a product platform shell deploy-readiness manifest without
mutating GitHub or AWS.

The verifier fails closed by default. A manifest with unresolved deployment
proof must include explicit blockers and exits non-zero unless the caller uses
planning or explanation mode.

## Usage

```bash
bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
  --manifest infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
```

For planning or human explanation, allow blocked evidence explicitly:

```bash
bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
  --manifest infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml \
  --allow-blocked \
  --caller-intent planning
```

The command is read-only. It checks manifest shape, optional reusable target
profile references, target profile identity, source provider, cloud provider,
selected runtime family, adapter selection, auth provider/readiness evidence,
CORS allowlist source, health exposure policy, rate-limit keying, local file
references, local smoke evidence, blocker coverage, and whether the manifest
can be treated as ready or blocked.
