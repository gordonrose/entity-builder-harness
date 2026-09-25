<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.script.run-platform-shell-persistence-admission-probe.readme
  version: 1
  status: active
  layer: 04.deploy
  domain: runtime.operations
  disciplines:
  - security
  - sre
  kind: capability-readme
  purpose: Explain the fixed non-mutating staging persistence write-admission diagnostic.
  portability:
    class: internal
    targets:
    - kanbien/staging
  used_by:
  - id: deploy.script.run-platform-shell-persistence-admission-probe
    path: scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.sh
-->
# Persistence write-admission probe

This command is a deliberately narrow diagnostic for `kanbien/staging`.

It uses the already isolated write-only Cognito client, but calls only
`POST /smoke/work-items/admission`. That route accepts no request body and
returns `204` without entering the repository, atomic writer, DynamoDB, outbox,
SQS, relay, or worker path.

Use `npm run platform:shell:persistence-admission-probe -- --validate` to check
the committed policy without a network call. `--execute` becomes available only
after an immutable server image containing the route has been deployed and
health-checked. Its output contains status and latency only.

This is not an alternate persistence-write command. A successful admission
probe establishes that the authenticated request reached the server boundary;
it does not claim a record was committed or an outbox message was delivered.
