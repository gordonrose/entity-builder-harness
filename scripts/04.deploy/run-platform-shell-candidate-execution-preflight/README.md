# Candidate execution preflight

<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.readme.run-platform-shell-candidate-execution-preflight
  version: 2
  status: active
  layer: 04.deploy
  domain: runtime.operations
  disciplines:
  - security
  - sre
  kind: documentation
  purpose: Explain the fixed, isolated candidate execution proof for the Kanbien staging platform shell.
  portability:
    class: internal
    targets:
    - kanbien/staging
  effects:
  - read-only
  used_by:
  - id: deploy.script.run-platform-shell-candidate-execution-preflight
    path: scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py
-->

This controller is the promotion gate between image publication and an ECS
service revision. It does not deploy or route the candidate.

It derives the candidate from the deployed dormant task definition, verifies
that definition mirrors the active server except for its immutable image,
reuses the active server's `awsvpc` configuration in memory, waits for the
candidate to reach `RUNNING` and `HEALTHY`, and always stops it. There is no
ECS service, load balancer, listener, route, caller-selected image, network,
task, label, or timeout.

If an ordinary process interruption arrives after ECS accepts a task, the
controller attempts the same controlled stop before it returns a safe failure
category. A terminal digest is never replayed; recovery requires a new
immutable candidate digest.

Run source validation:

```bash
npm run platform:shell:candidate-execution-preflight -- --validate
```

The controlled execution command requires its explicit guard. It may be used
only after the reviewed dormant task-definition change set has been executed
and its candidate image is the intended immutable digest:

```bash
npm run platform:shell:candidate-execution-preflight -- --execute --approve-candidate-execution-preflight
```

Its output is a safe verdict and, on failure, one allowlisted category. It
never emits task identifiers, raw AWS responses, endpoints, logs, headers,
payloads, tokens, secrets, or image registry paths.
