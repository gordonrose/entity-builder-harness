<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-finite-job-review
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record reusable finite-job execution conformance while preserving independent effect verification and all target qualification obligations.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Finite Execution Conformance Review — 2026-09-29

This is the ninth IaaS release-control source unit. The user's PostgreSQL
readiness question did not authorize changing the programme into PostgreSQL
feature work. This unit establishes reusable finite-execution protocol checks
before independent effect verification and later controlled provider operations.
It does not run, modify or qualify any PostgreSQL or other product job.

Two closed versioned schemas, a shared runner extension, focused tests and an
explicit mode on the existing image smoke wrapper are implemented. There is no
parallel deployment framework. The current local adapter supports reviewed
Linux/Node images and packaged JavaScript commands; provider-neutral does not
mean every runtime or dependency environment is already supported.

The [exact public-wrapper output](finite-job-conformance-result.json) binds the
fixture source, both finite-job schemas, current helper implementation, recipe,
pinned base, full image payload, constructed immutable image and each attempt.
The [server compatibility result](server-compatibility-result.json) records a
separate actual run of the previously qualified immutable product image under
the extended engine. It is a compatibility check, not a fresh full artifact
qualification or publication. The safe files are unsigned local observations;
raw subprocess logs and caches are excluded from Git.

## Acceptance results

Canonical clean validation exited 0: **1,165 tests in 29 suites**, including
232 new focused tests (102 contracts, 45 engine, 85 conformance). Legacy smoke,
provider/network core boundaries and 44 metadata headers passed. The
[verification summary](verification-summary.json) records exact suite counts,
receipt identities and the final log hash. All totals refer to the frozen
post-repair run; earlier runs are not added to inflate the count.

| Actual local fixture case | Execution result | Conformance result |
| --- | --- | --- |
| Complete terminal receipt and exit zero | Completed | Passed |
| Same completion with private stderr | Completed; diagnostic excluded | Passed |
| Valid receipt followed by nonzero exit | Failed | Passed |
| Exit zero without receipt | Failed | Passed |
| Malformed receipt | Failed | Passed |
| Stale attempt nonce | Failed | Passed |
| Wrong profile digest | Failed | Passed |
| Duplicate JSON key | Failed | Passed |
| Unknown receipt field | Failed | Passed |
| Command exceeds deadline | Timed out | Passed |
| Output exceeds bound | Failed | Passed |

All eleven cases verified owned cleanup. Negative-case conformance success
means the expected refusal happened; those nine jobs do not become completed.
The separate product-image compatibility run passed both server health checks,
SIGTERM shutdown with exit zero and cleanup. Unit tests additionally cover OOM,
interruption, unknown transport/state, ownership mismatch and cleanup failure;
those injected tests are not described as real host-crash or OOM rehearsals.

Final fixture image: `sha256:e93bfa52c2f33375b3e9c5daad2a76f10bf3e91a1a98beec155085e103ccd4c4`.
Result identity: `sha256:19e6ce477cb6d3585895610a15e3de175d1be5a1ff14e4742541f2df69efa5bd`.
Runner identity: `sha256:f0406d0621586365f8f4a9ab6dca2257ffd26d8298d6d18c32d70c9bb97e36b4`.
The pre-checkpoint HEAD is a historical label; exact reviewed source bytes and
schema versions are bound separately. A subsequent commit does not alter these
historical observations or qualify a rebuilt image.

## What the runner now establishes

A declared profile binds immutable image/payload identity, the packaged command,
entrypoint, working directory, output limit, command timeout and required checks.
A fresh random attempt and profile/schema digest are injected into a fixed safe
environment. One bounded, duplicate-free terminal envelope must match them and
the exact ordered check list. State, exit status, OOM flag and cleanup are checked
separately. A process exit alone cannot produce completed execution.

The existing image build metadata and entire `/app` inventory are checked.
The runner accepts the reviewed fixture or existing product-image default while
overriding only the explicitly validated packaged finite command. The original
server inspector remains strict. Runtime remains nonroot, read-only, without
external network, host mounts, ports or ambient credentials, and with bounded
resources. The command timeout bounds attached execution; total `elapsed_ms`
includes inventory, observation and separately bounded cleanup. A whole-operation
deadline belongs to the later operation engine. Timed-out/interrupted jobs are
not retried. Cleanup rechecks ownership and confirms the container is absent.

A returned terminal check is still a job-reported claim. Every receipt therefore
retains `semantic_verdict: unverified`; this does not establish a database,
external service or other business-state invariant. All source closure, release
eligibility, operation authority and release qualification remain blocked.
`product_profile_updates` is empty. The common consumer rejects these producers
for every purpose, including source analysis and both authorization uses.

## Reproduction and delivery queue

```bash
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh --verify-finite-jobs \
  --source-root . --scratch-root /persistent/path/finite-job-scratch
TMPDIR=/persistent/path/finite-job-scratch \
  bash scripts/04.deploy/operational-realization-gate/verify-clean-environment.sh \
  --python /usr/bin/python3
```

The existing immutable runtime base must already be acquired through the image
wrapper's explicit base-acquisition mode. The conformance mode accepts no image,
command, dependency or saved-result overrides. Both real runs used persistent
scratch outside the checkout. Build steps have networking disabled; Docker
registry metadata access is not claimed to be isolated, and host/engine versions
are observed rather than fully pinned. No image was pushed or provider state
changed. Temporary containers were removed; local images remain available.

The first actual eleven-case run passed. Final review improved generic reuse
across the two reviewed image defaults, explicitly bound both finite schemas,
and rejected blank path arguments. A fresh frozen public-wrapper run then passed.
A further review found that an alternate source checkout could supply different
helper/schema bytes from the modules actually executing. The runner now checks
those four files for exact equality before building; four mismatch regressions
and an identical-copy case cover the repair. A new eleven-case real run and a
new server compatibility check passed afterward. The earlier full clean run
passed 1,160 tests; final acceptance uses the fresh 1,165-test post-repair run recorded here.
Superseded uncommitted review artifacts are preserved outside Git. Earlier
test-only API/fixture issues were repaired before acceptance.

Next continue Phase 3 with reusable independent effect/dependency verification
and required artifact admission, preserving actual per-command proof obligations.
Open source coverage is not waived. Durable journal/locking/fencing and crash
reconciliation, AWS adapter and per-task preflight, hosted validation after
approved publication, and controlled target qualification remain later work.
The thirteen pending target-task/sidecar obligations stay pending; PostgreSQL
Stage 6 stays paused. No local stop condition exists.

Independent read-only review passed: both schema bytes, fresh source/runner,
lock, repository label and fourteen-profile inventory matched. All eleven
attempts were distinct and all eleven cleanups verified. Thirty-six consumer
checks (aggregate plus eleven executions, each for three purposes) were
rejected. Image inspection confirmed the reviewed command/settings and all
nineteen pinned base layers. No additional container was started by that audit.

The post-repair audit independently replayed all four mismatched-helper/schema
cases and confirmed refusal before execution. It revalidated the final saved
receipt, all thirty-six consumer refusals and unchanged pending product status.
The final eleven-case real conformance run took 64 seconds. No blocker remains
in the reviewed implementation boundary.
