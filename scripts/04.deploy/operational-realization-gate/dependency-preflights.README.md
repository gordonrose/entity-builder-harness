<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.readme.dependency-preflights
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Explain exact-image read-only PostgreSQL prerequisite proof and its remaining provider boundaries.
portability: {class: internal, targets: [entity-builder]}
used_by:
- id: deploy.script.dependency-effects
  path: scripts/04.deploy/operational-realization-gate/dependency_effects.py
-->
# Packaged PostgreSQL preflight qualification

The existing dependency-effect runner now exercises the packaged `--preflight`
mode against its owned PostgreSQL 17.11 container over certificate-verified TLS.
It uses the exact qualified product image for both prerequisite checks and the
original nine bootstrap/migration effect cases. Preflight success is never a
completed job, release decision, or permission to operate a target.

The fixed additional cases are:

| Case | Placement | Expected process result |
| --- | --- | --- |
| Bootstrap readiness | Before bootstrap | Passed |
| Bootstrap wrong password | Before bootstrap | Failed |
| Migration readiness | After bootstrap, before migration | Passed |
| Migration wrong identity | After bootstrap, before migration | Failed |
| Relay readiness | After migration | Passed |
| Worker readiness | After migration | Passed |
| Relay missing SELECT | After migration and explicit fixture grant revocation | Failed |
| Worker missing DELETE | After migration and explicit fixture grant revocation | Failed |

Before and after each check, the independent observer compares the selected
roles, memberships, schema ownership, table definitions, constraints, grants,
and migration history. It also queries row counts for all four selected runtime
tables and requires them to remain empty. The process terminal is separately
validated against `relational-task-preflight/v1`, with exact operation, verdict,
exit status, and explicit non-authority. These observations cover the selected
fixture database objects; they are not a claim about every PostgreSQL catalog or
transient writes rolled back during a session.

The runner grants/revokes fixture privileges only outside the corresponding
before/after interval. These deliberate local fault injections are never passed
to production. The product preflight code uses a read-only transaction followed
by rollback. Relay/worker receive a fixed inert queue URL for input validation;
the owned internal network and absence of cloud credentials do not prove AWS
queue permission or queue behaviour. No relay/worker effect command runs here.
Restore preflight remains pending: this fixture hostname does not satisfy the
separately required isolated restore target identity.

Use the existing public wrapper to build/qualify once and test dependencies:

```sh
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh \
  --verify-dependency-effects --source-root . \
  --scratch-root /absolute/owned/persistent-directory \
  --package-cache /absolute/verified-package-cache
```

To reuse the same host's freshly qualified image, supply the existing publication
handoff directory instead of the package cache:

```sh
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh \
  --verify-dependency-effects --source-root . \
  --scratch-root /absolute/owned/persistent-directory \
  --qualified-publication-directory /absolute/owned/persistent-directory/handoff
```

This route calls the existing publication verifier. It rejects changed source,
commit, runner, lock, receipt, actual image or payload. It accepts no image name
or tag override and does not fall back to a rebuild on a failed handoff. The
pinned PostgreSQL image must already be available through the existing acquisition
mode. The inherited container/network isolation and owned cleanup checks apply.

The existing stdout `dependency-effect-result/v1` remains unchanged. After all
checks and cleanup pass, the private `dependency-effect-evidence-<run_id>` directory
contains `build-result.json`, `effect-result.json`, and a distinct
`preflight-result.json`. The latter binds the effect receipt, profile, actual
image and payload, runner, producer/result schemas, run, TLS fixture certificate,
ordered checks and independent state digests. It retains only normalized facts
and counts, never credentials, raw SQL rows, environment values or process logs.
All authority and qualification fields remain blocked.

Focused tests: `python3 -B -m unittest discover -s
scripts/04.deploy/operational-realization-gate -p 'test_dependency*.py'`.
The focused suites mock the transport; acceptance additionally requires one real
run of the public wrapper and validation of both linked receipts. Until that
run is recorded, source tests alone do not establish real database proof.

Next delivery unit: bind these distinct prerequisite and effect receipts into
the target's ordered controller, then qualify actual target identity, injection,
network access and isolated restore obligations under explicit authorization.
