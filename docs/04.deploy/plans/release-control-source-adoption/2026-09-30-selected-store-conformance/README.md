<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.selected-store-conformance-review
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record bounded selected operation and shared-store source conformance, exact verification and the remaining production-control boundary.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-release-control-mvp
  path: docs/04.deploy/plans/iaas-release-control-mvp.md
-->

# Selected operation and shared store — 2026-09-30

U20 is accepted within the source-conformance boundary. The final fresh clean
run passed 2,173 tests in 68 suites, zero skips, and metadata checks for 69 files.
Independent review passed. The accepted component count moves from 19 to 20.
This component belongs to the existing M4 milestone and approved source policy.
It introduces no provider effects or operation authority.

## Before and after

Previously the gate had a local SQLite journal and inert recovery model, but no
selected shared-store request contract. The new v2 record fixes the selected
operation, source, image, policy and store-generation identities. Pure transition
checks enforce ownership, lease and absolute deadlines, a single reserved effect
attempt, observation and cleanup ordering, and refusal after an unknown effect.
The existing v1 loader keeps its default behavior; v2 uses its existing bounded
schema reader, canonical encoding and closed-schema checks.

The injected AWS adapter constructs one conditional transaction for the scope,
operation and append-only event, with a store-generation check. It refuses a
stale prior snapshot instead of overwriting a newer owner. Separate safe evidence
uploads use conditional creation and exact version/checksum readback. Linking an
observation requires the expected operation, prior record, image, assertion and
time. An unlinked upload cannot advance the operation. A lost journal
acknowledgement may hide a committed transition, requiring quarantine and
reconciliation rather than replay.

This is source conformance with an explicit private fixture transport. There is
no live SDK/CLI transport or controller. The public gate's existing smoke wrapper
registers both new suites; no parallel execution command is introduced.

## Verification

The [verification summary](verification-summary.json) binds all 16 component
files and records exact results. The integrated selected-component run passed
125 tests, including 27 new record tests and 31 new store tests. Independent
review passed the 31 backend tests and 12 existing v1 journal tests; these repeat
canonical cases and must not be added to its total. The clean verifier exited 0
using CPython 3.14.4, eight hash-locked distributions and the selected Node
22.23.3/npm 10.9.9 tools. Clean log SHA256:
`c9e8b3c7354406fd9f1b750377e730fe2300187b4318015546eb1c810d7e03be`.

Positive cases include the complete inert prepare, claim, reserve, observe,
cleanup and close sequence. Negative cases exercise competing/stale writers,
changed generations and identities, spent attempts, expired deadlines, lost
responses before and after commit, corrupt or stale evidence and authority
claims. No source record can be consumed as execution permission.

Review corrected a concrete request issue: each database submission uses a fresh
transaction token, so an old cached success cannot bypass a new ownership check.
No automatic mutation retry is allowed. Future provider-effect tokens have a
different purpose and must stay bound to durable intent after an unknown response.

## Remaining boundary and next delivery

The adapter's unknown-response quarantine is process-local. Tests do not prove
recovery after controller restart, old credential exclusion, provider effect
termination, real clocks, account/role authentication, one-writer IAM, encryption,
retention or AWS durability. The source policy is a bounded projection of the
approved operating policy, not enforcement of every policy value. The scope
cannot be reused for a new operation through this component.

M4 remains partial. Next extend the existing controller with authenticated
operation authority, bounded live transport, durable unknown-outcome and
old-writer reconciliation, scope lifecycle and selected caller integration.
The actual resource templates, role permissions and cost estimate must be
reviewable before separate bootstrap approval. Hosted/target qualification and
M5 staging rehearsal follow their specific approvals. Local v1 results and these
new v2 fixtures remain unable to grant release eligibility or operation authority.

No AWS resource, GitHub setting, DNS, secret, main branch or other worktree was
changed. No push, merge or hosted publication occurred. Earlier image receipts
remain historical evidence for their recorded bytes and revision; this unit does
not requalify the later commit or turn local evidence into hosted provenance.

## Exact next M4 integration

The next acceptance target is one candidate start, health observation and
controlled stop through the existing controller. It precedes relational execution
and introduces no PostgreSQL feature work.

| Existing surface | Required integration |
| --- | --- |
| Selected blueprint, readiness adapter, release compiler and target contracts | Bind the live baseline image separately from the desired candidate. Admit a specifically approved qualification operation with its pre-execution gates satisfied and later gates pending. A blocked source receipt stays blocked. |
| `finite_recovery_controller.py`, `operation_actions.py`, selected v2 record and store | Adapt the existing local store/engine interface without widening local v1 authority. Persist separate start and stop intents, exact request identity, ownership and recovery state. Prove interruption before and after both effects without replay. |
| `run-platform-shell-candidate-execution-preflight/script.py` | Route existing start, health and stop behavior through that controller. Replace in-memory recovery authority with durable records; validate exact task, cluster, revision, image and operation bindings. Preserve existing bounded waits. |
| Existing public gate, candidate/relational wrappers and protected hosted caller | Require the same admission and ownership boundary. Refuse selected mutation paths that have not migrated; test direct legacy invocation as well as the supported command. |
| Existing target template/IAM area and AWS adapter directory | Prepare the dedicated store/role resources, exact permissions, cost evidence and bounded authenticated transport. Source acceptance precedes separate resource, hosted activation and task-execution approvals. |

Independent inspection found three specific blockers to simple wiring: the v2
reservation currently covers candidate start only; the existing recovery engine
and constructor require inert local v1 machinery; and the passive reader compares
product tasks against one image while the service has separate current and
candidate image parameters. These are unmet M4 integration requirements, not new
milestones or reasons to broaden the MVP. Actual task handles and private provider
data must retain the established private-store/public-evidence boundary.
