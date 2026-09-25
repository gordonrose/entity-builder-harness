<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.scripts.readme
version: 9
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Index deploy-layer executable checks and helpers.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.script.verify-rag-rulebook-deploy-readiness
  path: scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh
- id: deploy.script.verify-platform-shell-deploy-readiness
  path: scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh
- id: deploy.script.validate-container-boundaries
  path: scripts/04.deploy/validate-container-boundaries/script.sh
-->
# Deploy Scripts

Deploy scripts provide executable, deploy-owned checks.

Commands in this folder must fail closed for deploy execution and must not
mutate cloud state unless their README and workflow explicitly declare a
mutating effect and require current-chat approval.

Current commands:

- `build-platform-shell-image/`: local-only Docker image build wrapper for the
  provider-neutral platform shell.
- `smoke-test-platform-shell-image/`: local-only image smoke test for platform
  shell `/livez` and `/readyz`.
- `run-platform-shell-controlled-smoke/`: locally validates, or with explicit
  target approval performs, one fixed protected staging request using an
  in-memory Cognito token and redacted status-only output.
- `provision-platform-shell-negative-authz-client/`: locally validates, or
  with explicit current-chat approval creates the one separately scoped Cognito
  machine client and its named secret for the bounded staging `403` proof.
- `run-platform-shell-negative-authz-smoke/`: locally validates, or after
  post-deployment inspection and explicit current-chat approval performs the
  one fixed valid-token, unmapped-scope staging request that must return `403`.
- `provision-platform-shell-persistence-write-client/`: locally validates, or
  with explicit current-chat approval adds the one reviewed `smoke.write`
  scope, separate confidential machine client, and target-owned secret used
  only by the bounded persistence proof.
- `run-platform-shell-persistence-smoke/`: locally validates, or after the
  reviewed target deployment and explicit current-chat approval makes exactly
  one fixed no-body work-item acceptance request with the separate write-only
  identity. It emits only a safe verdict, status, and duration.
- `run-platform-shell-rate-limit-smoke/`: locally validates, or after current
  approval waits for a fresh fixed window, performs at most the configured
  liveness rate-limit plus one sequential public request, and records
  aggregate-only `429` evidence or an explicit rollover-inconclusive result.
- `run-platform-shell-ingress-smoke/`: locally validates, or after current
  approval performs fixed read-only WAF, listener, and security-group
  inspections plus one public liveness request.
- `run-platform-shell-persistence-admission-probe/`: locally validates, or
  after the reviewed deployment performs exactly one no-body authenticated
  request to the dedicated server-admission route. It is not a persistence
  write: the route returns `204` without invoking the repository, transaction,
  DynamoDB, outbox, SQS, relay, or worker.
- `run-platform-shell-worker-smoke/`: locally validates, or after explicit
  current approval sends exactly two side-effect-free queue messages 75 seconds
  apart, starts only the dormant worker service, observes bounded settlement,
  then always returns it to desired count zero. It proves a consumer boundary
  and a fresh-counter metric observation, not an outbox.
- `run-platform-shell-metric-coverage/`: locally validates, or in a governed
  read-only operation queries only the fixed server coverage/SLO policy or the
  separately fixed worker delivery-counter observation policy. It never accepts
  a caller-supplied metric, label set, query, or alert destination.
- `verify-platform-shell-synthetic-scheduler/`: read-only policy check for the
  temporary GitHub Actions protected-route synthetic workflow and its separate
  one-secret-read IAM role source.
- `validate-container-boundaries/`: read-only Dockerfile and container image
  placement validation so deployable images stay under governed `infra/**`
  image directories.
- `verify-platform-shell-deploy-readiness/`: read-only manifest validation for
  product platform shell deployment readiness, including explicit blocker
  coverage for planning-only evidence.
- `verify-platform-shell-deployment-workflow/`: read-only supply-chain gate
  that makes the staging workflow scan, create an SPDX SBOM, and attest the
  immutable image before it can deploy the service stack.
- `verify-rag-rulebook-deploy-readiness/`: read-only manifest validation for
  RAG/rulebook GitHub-to-AWS deployment readiness.
