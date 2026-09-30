<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-mvp-selected-path-review
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record selected MVP source integration, exact local artifact and dependency proof, passive target findings and remaining controlled-execution boundaries.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-release-control-mvp
  path: docs/04.deploy/plans/iaas-release-control-mvp.md
-->

# Selected MVP path — 2026-09-30

Three bounded source/local components are accepted: U17 selected blueprint,
U18 exact-image publication handoff, and U19 selected task/passive preflight.
The [verification summary](verification-summary.json) binds the reviewed files
and completed checks. M1–M5, the full roadmap and PostgreSQL Stage 6 remain
incomplete; these accepted components do not erase their remaining criteria.

## Concrete change

| MVP area | Before this batch | Implemented and separately evidenced |
| --- | --- | --- |
| M1 selected composition | Neutral compiler and source collectors, with no current selected-target blueprint | Three versioned target assets and a closed schema compile 13 container subjects in nine task groups into all 17 ordered gates and 221 operation bindings; source/configuration/command/identity mappings are explicit. |
| M2 exact publication | Local qualification and the staging publisher followed separate image-build routes | The existing publisher now retains, rechecks and publishes the exact image qualified in its own daemon. Manifest and configuration identities stay distinct. Selected actions and tools are fixed and changed checkouts are refused. |
| M3 task prerequisites | Database tasks only had their effect-producing entrypoints | Each existing relational task now has a fixed no-effect database preflight. The existing dependency verifier tests it using the actual qualified image and disposable PostgreSQL. |
| M3 passive AWS inspection | Relevant checks were spread across existing scripts | One strictly selected public gate mode reuses them, binds current source and exact task revisions, emits safe dated observations and refuses mismatches or stale evidence. |
| M4 exact task selection | A family could select a newer revision after inspection | The existing relational runner requires the deployed stack's exact task revision, image and command, and checks launch/poll identity. Shared durable execution is still unimplemented. |

## Recorded local execution

The fresh final-image qualification ran from 18:57:03Z to 18:59:50Z (167 seconds).
It executed the locked real compiler and payload accounting, started the actual
nonroot image, observed live/ready responses, checked graceful shutdown and
verified cleanup. The same image was reused for database checks without a rebuild.

- [Complete container receipt](local-container-result.json): passed, including current compiler-derived workspace exports.
- [Same-host handoff](qualified-image-handoff.json) and [independent publication recheck](publication-check.json): matched; nothing was pushed.
- [Database effects](dependency-effect-result.json): nine expected cases passed.
- [Separate database preflights](dependency-preflight-result.json): eight expected cases passed, including denied identities and revoked privileges; independent before/after database observations remained unchanged.
- [Actual Syft verification](sbom-validation.json): verified 1.42.3 CLI; SPDX 2.3 schema passed, 88 package entries and all 57 expected production dependency name/version pairs present. The local network-isolated scan took 27.817 seconds. Full SBOM remains in private scratch, SHA256 `3123cbe4be9320c3a4c328c331529ae83cb43fad6b489b3b221ce4ed3bdd46af`.

The image manifest is
`sha256:b4fb03d4c3b19f0983f20665f872e1ff00ee9b37d20f0b41675b9eae14e45356`;
its configuration is
`sha256:8301f035e995d795be2aad5f8fbfb7608407fe3f75a8d74f4da1180bdfdeb4a7`.
The receipt binds pre-checkpoint HEAD `2fe812edaa49d3a0352cd8d87db3ecde55517381`
and the actual working-tree content digest
`sha256:c505ecaca9b2d44a1f140a637536f928c201971a19af0326593a80e94d9e0a15`.
It is not evidence of a clean hosted main build or a later commit. The build
compiler uses Node 22.23.3; the locked runtime image reports Node 22.22.0.
These are separately recorded boundaries, not a claim of one shared version.

Local SBOM presence is not complete supply-chain admission, a vulnerability scan,
a signature or a hosted attestation. Database preflight is not AWS IAM/network
proof, queue effects, an isolated restore, task completion or permission to run.
The owned local task/database/network resources were cleaned up; the exact image
was intentionally retained for the reviewed same-host handoff.

## Target observation

The [first passive observation](passive-readiness-stale-result.json), recorded
at 19:46:51Z, confirmed the selected AWS account and artifact-stack status. It then
blocked on stale passive drift evidence. No task group was observed by that
failed attempt. Zero provider effects and zero secret-value reads were requested.
Its expiry dates the failed inspection; it does not renew the stale drift fact.
An expired or historic receipt is retained as history, never current readiness.

## Necessary fixes and limits

Two existing selected-path drift routes required bounded repair: task launches
used mutable family selection, and publisher action/tool references could move
or fetch a mutable installer. Both are now checked by focused refusal tests.
No general action interpreter, other-cloud adapter or whole-estate audit was
added. The closed source graph still has declared owner/risk/approval inputs;
full transitive caller closure and source-to-live equivalence are unproven.

The new public inspectors and preflights always retain blocked release eligibility,
operation authority and qualification. Existing approval modes remain unchanged.
The publisher remains manual/main-only with its protected environment, conditional
OIDC, zero HIGH/CRITICAL scan threshold and digest-bound attestations. The first
hosted run and registry/attestation checks remain pending explicit authorization.

## Verification and next delivery

Fresh hash-locked CPython verification passed with **2,115 tests in 66 suites**,
zero skips, and 66 canonical metadata checks. The separate actual-entrypoint
mock suite passed **67 tests**, zero failures/skips. Canonical tests include
38 blueprint, 54 publication, 42 passive adapter/CLI, 85 exact-revision, seven
preflight-schema and 55 dependency-preflight cases, alongside all prior suites.
Focused reruns are not added again to inflate the total. Existing relational
validation, publisher validation and `git diff --check` also passed.

The user accepted the [M4 operating policy](../../iaas-release-control-mvp-control-policy-proposal.md)
for source implementation. Next is its remaining M1/M4 controller integration:
versioned shared records/backend conformance, then durable intent before AWS
effects; one supported writer with unknown-outcome reconciliation; ordered live
preflight/effect observation and owned cleanup; and migration of selected callers
to the common boundary. Then M2/M3 hosted and target acceptance can make M5's
specifically approved staging rehearsal reviewable. No requirement is waived.
