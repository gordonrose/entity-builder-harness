<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.fixture.finite-job-conformance
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Describe inert packaged finite-job fixtures and their intentionally limited execution proof.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.script.finite-job-conformance
  path: scripts/04.deploy/operational-realization-gate/finite_job_conformance.py
-->
# Finite-job execution fixtures

These inert commands exercise the existing container runner. They perform no
provider calls, database work or product operations. A separate image packages
`jobs/task.cjs` using the existing immutable runtime base. Its entire `/app`
payload is fingerprinted and inspected before execution; no repository code is
mounted into the runtime container.

The public wrapper builds fresh fixture bytes and runs eleven cases: success,
success with private stderr, nonzero exit despite a valid terminal envelope,
exit-zero with missing output, malformed output, stale attempt, wrong profile,
duplicate JSON field, unknown field, timeout and excessive output. Every case
requires verified owned-container cleanup. A correctly refused negative case
passes conformance while its execution remains failed/timed-out. Cleanup
failure, interruption, OOM and changed isolation have separate fake-engine
negative tests; those are not claimed as live crash or OOM rehearsals.

The fixture's terminal checks are declared claims. `semantic_verdict` remains
`unverified`: the protocol cannot independently prove a database or other
business effect. No fixture changes any product profile's qualification status.

Run through the existing image smoke wrapper with `--verify-finite-jobs`, an
explicit source root and existing persistent scratch outside the checkout.
The pinned runtime base must already be available through the existing explicit
base-acquisition mode. No alternate base, arbitrary command, custom image,
credential, dependency service or saved receipt is accepted by this command.
