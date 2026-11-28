<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standard.environment-lifecycle-policy
version: 4
status: active
created_on: "2026-11-26"
updated_on: "2026-11-27"
layer: 04.deploy
domain: deployment.environment-lifecycle
disciplines: [architecture, security, sre]
kind: standard
purpose: Separate persistent and temporary environment policy without granting resource deletion authority or weakening production defaults.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.workflow.declaration-coverage
  path: .agentic/04.deploy/workflows/declaration-coverage.md
-->
# Environment lifecycle policy

Use the selected target profile to state how long an environment should exist
and what happens to its application data. This policy belongs to deployment
composition, not application features. Both choices use the same production-
capable service definitions and delivery controls.

## Policy and compatibility

`environment_lifecycle` is an optional mapping in the existing target profile.
The [shared executable validator](../../../../scripts/04.deploy/lifecycle/00-target-alignment/capabilities/environment-lifecycle/policy/implementation.py) owns its accepted representation; callers must
consume its checked result rather than copy the conditions.

| Field | Persistent environment | Temporary environment |
| --- | --- | --- |
| `mode` | `persistent` | `temporary` |
| `data_retention` | `preserve` | `discard` |
| `max_duration_seconds` | Must be absent | Required positive integer; booleans are not integers for this contract |

An absent mapping preserves the existing persistent/preserve interpretation.
Explicit null, empty or wrong-type mappings, unknown fields, missing fields and
contradictory combinations are errors, not permission to select a default.
Neither a target name nor a label grants temporary status. Preserve ordinary
health requirements, database protection and production retention defaults.

A reusable validator does not hardcode an operator's chosen session length.
The concrete session declaration must be bounded by its approved maximum, with
the selected duration kept in its target/session binding. Policy validity does not
establish that a session has started, expired or owns any provider resource.

## Execution and cleanup boundary

### Read-only session source plans

The existing AWS preparation owner exposes `load_session_plan` separately from
its persistent-only `load` route. Its narrow session document identifies the
source target/scope, a 32-character lowercase hexadecimal session ID, integer
UTC epoch `starts_at`/`expires_at` values, and explicit temporary/discard lifecycle
settings under schema `deploy/environment-session-intent/v1`. It does not copy
the source profile or accept supplied resource names, provider identities or
source hashes. The [session reader](../../../../scripts/04.deploy/lifecycle/00-target-alignment/capabilities/environment-lifecycle/session-binding/implementation.py)
enforces an interval containing the supplied current time and bounded by both
policy and the operation's approved duration maximum. The actual preparation
consumer's [fixtures](../../../../scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime-configuration-test.py)
cover expired, future-start and excessive-duration rejection.

The source profile and dependency scopes must still pass ordinary preparation.
The planner captures each declaration's bytes once, parses and projects those
same bytes, and binds their ordered hashes into an immutable session binding.
A final reobservation rejects changed inputs during planning; this is not an
atomic filesystem snapshot or a promise of freshness after the function returns.
Controller qualification and later mutation gates must revalidate their own
exact sources and compare a fresh capture before using retained reviewed bytes.

AWS resource prefixes are derived as `s-` plus the first 19 session-ID digits,
within the existing template constraints. Stack suffixes come from checked
source-target stack names; duplicate projected names reject. Truncation does
not prove global uniqueness: later creation needs positive absence and durable
session ownership checks. The original package/source target, publication
repositories, production defaults and retained-resource policy stay unchanged.
Projected templates are source observations, not deployable instructions or
permission to create the foundation's retained/shared resources. These plans
explicitly remain `not-admitted` for execution. No remote expiry, cleanup,
resource ownership or package/live qualification is established by this API.

The [AWS preparation reader](../../../../scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py)
owns template-declared creation, activation and discard projections. Persistent
environments retain their data protections. Explicit temporary/discard instances
apply the same closed, source-declared retention/protection projection from their
first CREATE and throughout activation; activation must not restore persistent
retention. Ordinary fresh disposable functionality sessions explicitly select
integer-zero automated-backup retention from their first CREATE; production
retention remains unchanged. Use the existing exact expected/discard property
inventory, not a second projection or a later retention-lowering UPDATE. These
sessions cannot claim backup, point-in-time recovery or replication acceptance;
those tests require a separately admitted retention-enabled lifecycle and cleanup
proof. Preserve other unrelated settings. The stopped creation projection is also its discard projection;
cleanup changes only captured stop controls when they are not already selected.
The [connected session adapter](../../../../scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py)
still requires sealed admission for cleanup and accepts no arbitrary template.
These selected settings prevent avoidable retained data after partial creation;
they do not establish physical quiescence, deletion or permission to execute.

Before using zero retention as evidence that a fresh session could not replicate
automated backups, retain its original creation custody and qualify the native
instance against that custody: exact identifier/ARN and immutable database
identity, integer-zero retention, no pending enablement and no observed backup
replication. The protected workflow authority must keep every admitted update at
zero and prohibit separate replication/direct database mutations. A final zero
observation alone is not a lifetime guarantee. Detected interference, missing
identity, unknown allocation or unqualified authority remains unresolved. This
does not cover adopted/restored databases or arbitrary account administrators,
and never replaces regional manual snapshot, AWS Backup or automated-backup
leftover observations. Until lifetime exclusion is qualified, cross-region
cleanup remains unknown rather than silently absent.

For separately created instances, the same preparation reader owns optional
`provider.foundation.instance_prerequisites` in the target profile. Each named
component declares exactly `stack`, `template` and `foundation_parameters`, with
the latter mapping foundation parameter names to prerequisite output names.
Only direct foundation suppliers are supported; ordinary persistent preparation
does not select them. The captured plan binds those source files, component and
stack/template identities, dependency order and output-to-parameter rows. The
actual-reader fixtures cover malformed/escaping source references, missing
outputs/parameters, collisions, immutable bindings and unchanged persistent
selection. No component name or matching output grants resource ownership.

Network ranges and availability zones are later execution inputs, not invented
session defaults. Live preflight must bind reviewed input choices and observed
owned outputs, validate subnet containment/non-overlap and available zones, and
reject substitution of existing/shared network identifiers. Captured dependency
order alone cannot satisfy those observations or admit billable creation.

### Revalidate an existing session without reopening it

An expired intent cannot create a new source plan through `load_session_plan`.
Cleanup instead uses the session reader's named `read_existing` and preparation
owner's `revalidate_session_plan` route. Both readers share structural, explicit
temporary/discard, duration and current-clock validation. Only the new-session
reader requires the current time to precede expiry; existing-session validation
still rejects a future start and never changes the original lifetime. There is
no general expiry-bypass flag or substituted historical clock.

The [session-record owner](../../../../scripts/04.deploy/shared/provider-adapters/aws/session_records.py)
provides a read-only positive observation of the existing versioned record and
the validated current clock. Missing, mismatched or unavailable state cannot
initialize a replacement or prove cleanup authority. Its existing storage guard,
account/region, binding and readback checks remain effective.

For a fresh sealed discard preparation or execution, the connected session
adapter observes that record, requires its original binding and sealed state,
then invokes the concrete preparation revalidator before the remaining qualified
preflight and provider submission. Revalidation captures through the same source
renderer and compares the complete canonical plan, including source hashes,
templates, phase parameters, graph and output bindings. A matching-looking
caller digest cannot substitute for a matching complete plan and observed record.
The existing preparation and session fixtures cover exact-expiry success only
for revalidation, changed-source/map rejection and absence of provider submission.

Preserve the reservation owner's ordering and observation-only recovery. Failed
fresh revalidation leaves its retained intent and submits nothing; an existing
reservation may still be observed without granting replay. Neither revalidation
nor a sealed record proves controller authenticity, effective permissions,
resource ownership, expiry-worker qualification or physical removal. Creation
and activation remain closed after expiry through their existing admission gates.

### Captured execution-input provenance

The same AWS preparation owner reads optional `execution_parameters` maps on
foundation, prerequisite and workload provider bindings. Selection of this
temporary-instance route requires complete, disjoint accounting of the source
template's parameters: existing creation controls, unchanged defaults, existing
prerequisite output bindings, or a checked execution recipe. Ordinary persistent
loading does not select these recipes. A recipe declares a producer, never an
operator-supplied resource identifier or an arbitrary expression.

Recipe kinds are closed: `choice`, `package`, `source`, `output`, `provider` and
`omit-if-unused`. Choice contracts name reviewed grouped inputs; package fields
refer to the selected publication's qualified image/source facts; source fields
refer to checked repository or declared dependency facts; output rows connect
only earlier owned graph producers; provider contracts name explicit observation
owners. The actual preparation fixtures must reject incomplete/overlapping maps,
unknown fields/contracts, unselected dependencies and absent producer outputs.
Captured recipes and selected publication facts remain part of full-plan source
revalidation, not executable authorization or supplied package qualification.

An explicit `omit-if-unused` recipe supplies no value. The shared CloudFormation
projection owner may remove only that selected, non-control,
non-output-bound declaration after proving it unmentioned in the remaining
projected template. It must conservatively inspect keys and values, reject
unsupported transformation/dynamic-reference machinery before condition removal,
and preserve every other parameter. Production/default projection is unchanged.
The existing projection and preparation fixtures own the exact rejection cases;
neither guessed values nor automatic pruning of all unused inputs is allowed.
Defaulted and NoEcho declarations may be explicitly omitted only under this same
unused proof; their values are never resolved or retained. A remaining reference
still rejects the omission. Ordinary production/default projection is unchanged.

Templates may explicitly name `Metadata.TemporaryDefaultConditions` to select
existing default-false boolean equality guards for temporary projection only.
The preparation owner checks each guard against its declared non-secret String
parameter, preserves its default, and rejects overlaps with creation controls.
This does not introduce a new temporary value or change persistent projection.
The shared projection owner may select a branch of a well-formed `Fn::If` only
for an already selected literal equality decision. Unsupported condition graphs
and remaining references to removed resources still reject.

The omission proof may preserve an opaque versionless Secrets Manager
`SecretString` reference only in a resource property, in the exact scalar
`Fn::Sub` form naming a declared `AWS::SecretsManager::Secret` logical resource
and a literal JSON key. It must be independent of selected or omitted parameters;
no secret is fetched or substituted. External, constructed, versioned, misplaced
or otherwise unsupported dynamic references remain errors. Check the original
template before pruning and the surviving references after pruning; an omitted
branch cannot hide unsupported machinery or a dangling secret-resource reference.

The connected execution owner must validate the actual grouped
choices, qualified receipts, observed repository/provider facts and original-
creation-bound owned outputs, retain one immutable input envelope in the existing
conditional session record, and bind resolved arguments into operation intent.
NoEcho values and application credentials must not enter that envelope. Exact
deployed-value preservation remains required for updates. Source recipe coverage
alone cannot admit creation, activation or cleanup.

The base envelope precedes provisioning and retains checked choices and acquired
package/provider facts. Because dependent outputs exist only after creation, the
same record may append one immutable resolved entry per operation kind/stack.
Earlier requests bind the stable base and their own entry, never the changing
whole collection. Lost/conflicting retention grants no request authority. Keep
the existing size bound and omit full templates/source plans and secret values.

The draft session API derives creation parameters from that envelope and owned
upstream outputs; caller-supplied parameter lists cannot replace them. Parameter
constraints remain with the shared CloudFormation owner. Updates preserve every
unowned deployed value through the existing previous-value mechanism. Retained
prepare/execute intent does not reacquire packages, re-resolve inputs or replay.
Output consumption requires the original reserved CREATE lineage, exact provider
stack identity and successful completion, not merely a name or supplied output.
Before an update can invalidate the original change set, retain its checked
creation identity and correlated root-event evidence in the session record's
append-once ownership fields. Subsequent output reads must rebind that evidence to the original
retained preparation/execution requests and exact current stack identity; a
copied description alone is insufficient. Do not assume AWS preserves earlier
change sets after execution of another change set.
That requirement does not prohibit separate cleanup of proved-owned partial
creation. Hosted package acquisition follows the
[custody standard](../../40-package/standards/require-immutable-package-custody.md);
receipt shape or a matching digest alone cannot authenticate its origin.

### Preserve capacity for cleanup before creation

The bounded session record must leave room for teardown of every admitted stack,
including uncertain or partial creation. Discovering insufficient space during
cleanup is too late. The record owner's
[`SessionRecords._write`](../../../../scripts/04.deploy/shared/provider-adapters/aws/session_records.py)
enforces a conservative virtual completion inside each conditional write,
before a new reservation can authorize submission.
Use actual captured names and retained data, closed operation shapes and enforced
maximum sizes for unknown identities; do not estimate from a passing fixture or
reserve every untouched future graph branch. Missing cleanup slots remain reserved
while other operations are admitted; actual entries replace their allowances.

Keep one complete CREATE parameter map and derive update arguments through the
existing parameter owner. Retain checked update-observation digests and each
original incarnation/creation proof once, without duplicating whole maps or
provider evidence in every consumer. Original ownership and source/argument
binding remain mandatory. Explicitly version changed draft record shapes; no
unqualified compatibility interpretation or second store is permitted.

Before live admission, the supported reserve must also cover the controller's
bounded cleanup-completion evidence and any admitted recovery operations. Local
teardown-intent capacity alone does not qualify those unimplemented consumers,
prove effective permissions or establish physical resource absence.

### Reserved exact-stack deletion

The temporary-session adapter may expose deletion through the existing durable
reservation and single-submission owners, never a parallel retry engine. Its
closed request selects a captured stack/template pair and binds the exact full
provider stack identifier, account/region, source plan and arguments. The record
namespace admits only the deletion kind's deletion phase and requires sealed
admission. Fresh deletion revalidates the existing source plan before qualified
preflight; a retained request remains observation-only even after source loss.

Identifier syntax is not original ownership, and a successful DeleteStack
response is not physical absence. The AWS temporary-cleanup applicability rules
still require original creation custody, reconciled prior operations, protected
exclusions, reviewed effects and effective permissions. No caller role override,
force-delete or retention escape is accepted. This API alone does not implement
those live checks, independent expiry, completion or successor admission.

### Original custody and deletion admission

The connected session adapter must reconstruct original CREATE custody from its
immutable request and reservation, exact provider identities, original template,
parameters and source-derived resource set. Preserve checked custody before an
UPDATE can remove the original change set. Partial-creation custody is distinct
from successful creation evidence; it must not weaken output-readiness proof.
The same adapter must consume this custody and operation reconciliation in fresh
deletion, rather than accepting a supplied ownership claim.

Every admitted operation preceding dependent teardown needs positive terminal
evidence or a definite pre-submission rejection retained by its actual sender.
Use exact reserved tokens and operation-specific states. Missing, pending,
denied or incomplete observations remain unknown, not cancellation or absence.
The sender may record not-submitted only before invoking the provider; a lost
response or interrupted process cannot authorize that classification or replay.

Temporary execution explicitly binds preserve-on-failure policy in its immutable
non-delete request and sends the native boolean `DisableRollback=true` through
the closed execute transport. Never rely on an omitted provider default or combine
it with `OnStackFailure`. Version this changed draft record shape; older or
unbound policies cannot be reinterpreted as preserved failures. Failed CREATE or
UPDATE reconciliation additionally requires original custody, the exact reserved
execution token, a terminal root event and matching current stack state. A change
set's `EXECUTE_FAILED` status alone proves neither ownership nor terminality.

For every executed terminal state, deletion readiness checks the actual current
original template and complete stopped parameter map against the captured discard
projection. Equality of creation and discard source templates is insufficient:
a failed activation may still have active task counts. Positively unexecuted
`REVIEW_IN_PROGRESS` remains a separate case, not a failure shortcut.

The first cleanup-only discard UPDATE may follow a positively reconciled failed
activation of an originally successful CREATE. Retain that original successful
creation proof and all non-control deployed values; change only captured stop
controls with the ordinary cleanup review of exact, non-replacing modifications.
This narrow input-resolution route must not supply ordinary successful outputs
or bypass ownership, sealed admission, qualified preflight or source revalidation.
It cannot resume partial initial creation, add resources or replace them. A
failed, uncertain or already reserved discard attempt remains observation-only;
another attempt needs the separately governed predecessor/new-label recovery.

The record owner must atomically enter a one-way deleting phase with the first
delete reservation. Reconcile prerequisite discard work before this transition;
thereafter prohibit new creation, activation and discard admissions while keeping
retained observation and deletion available. Sealing cannot reopen deletion.
Check the closed operation set again before sending deletion. Recheck ordinary
admission at the creation/activation send boundary as well; a local read cannot
make its subsequent AWS call atomic. An uncertain reserved sender still blocks
teardown, and qualified server-side deadlines remain necessary.

Version changed record shapes explicitly and reserve their bounded append-once
custody/outcome slots through the existing capacity owner before admitting work.
Resource-set digests are not physical identities or completion evidence. The
later full leftover manifest and physical absence consumer remain mandatory.

Retain source-indexed physical identity observations in that same bounded record
before exact-stack deletion, bound to original CREATE custody and a complete
provider observation. Reserve every admitted source resource's maximum digest
slot before creation. Unknown allocation can become positively never allocated
or an observed identity; proved identities cannot be replaced or erased. Missing
rows, absent IDs and failed roots do not prove nonallocation. Unknowns cannot
satisfy completion, but do not bar deletion of an independently proved-owned
exact stack. Persist their unresolved status rather than abandon that cleanup.
Positively unexecuted creation proves nonallocation only after admission is closed
and no unresolved execution reservation remains. Capacity must expand unknown
slots to their eventual bounded representation, even in a partial saved manifest.

When retaining identity digests instead of raw IDs, the consuming adapter must
reconstruct the exact raw identity from original provider lineage and match its
source position and digest before use. State the provider's bounded lineage
availability; loss or incomplete recovery is unknown, never physical absence.
This handoff does not grant parent-coverage assumptions, type-specific removal,
backup/log completeness or a completed-session transition.

### Source-bound phase execution identities

Temporary source plans must bind distinct creation and cleanup CloudFormation
execution identities from the captured target declaration and session prefix.
Keep the pair once in the immutable session base and bind its phase selection
through the existing exact request digest. User intents and operation callers
cannot override roles. Creation/activation use creation authority; discard and
exact-stack deletion use cleanup authority. Version changed draft record shapes;
source revalidation and cold recovery must preserve the same pair.

Native change-set descriptions do not report the execution role. Submitted
arguments and original custody bind that selection; stable current successful
executed phases additionally require the stack's associated role to match.
A later positively observed, source/request-bound prepared phase can explain a
transition between those checked roles; a reservation alone cannot. That
transition cannot qualify runtime success. Do not invent attachment timing during
pending/failed phases or require the cleanup role to be attached before an
explicitly role-bound deletion of an independently proved-owned stack. These expected identities
never prove effective permission, server-side expiry or exclusivity. Before
live admission the protected factory must establish full-session ownership and
account-global collision absence, preserve protected/workload role separation,
restrict all stack writers and enforce phase permissions/deadlines on submitting
and CloudFormation execution identities. PassRole restrictions alone do not
prevent reuse of an already attached role. Persistent routes are unchanged.

### Concrete CLI transport is not admission

Session operations and acquisition use the existing AWS invocation mechanics
through a closed session transport: fixed profile/region/environment, exact
supported operation arguments, no caller CLI or role overrides, one attempt and
bounded timeouts. Only CloudFormation execute-change-set and delete-stack may
accept an exactly empty successful response. Reads and malformed nonempty output
remain rejected. Preserve finite known provider causes at actual callers rather
than trusting arbitrary exception attributes.

Require complete observations through the existing CLI pagination behavior;
remaining continuation tokens are incomplete evidence. A page size is not a
result cap. This transport does not qualify credentials, effective permissions,
controller custody, independently armed expiry or original resource ownership.
The final live factory and mutation preflight still own those checks.

### Live admission remains separate

Current fixed-resource deployment routes must reject temporary policy until
their own validated session bindings and operation gates support it. Returning
a checked temporary policy is never a cleanup authorization. Missing policy
remains protected and cannot be adopted into a temporary teardown.

Temporary execution needs exact independently owned resource identities,
approved effects, bounded duration, qualified deployment and cleanup controls,
and independent expiry handling before billable creation. Cleanup must exclude
production, unrelated and shared resources through both ownership checks and
execution permissions. A successful functional test is not a substitute for
cleanup observations; a failed test must not prevent cleanup of proved-owned
temporary resources.

Once a session ends or expires, its owner must prevent new provisioning and
deployment retries and reconcile in-flight effects before claiming removal.
Unknown effects are not absence and cannot authorize mutation replay. Existing
resources need their separately reviewed retirement boundary; changing a
profile cannot authorize their deletion.

These requirements do not create an execution exception. The existing
[realization gates](../../standards/operational-realization-gate.md) and
[AWS execution workflow](../../../aws/workflows/execute-approved-aws-change.md)
remain effective. General session creation/expiry/cleanup support must be
implemented and proved before use; the current restore-only exception does not
cover arbitrary environment deletion.

## Verification

Prove absence compatibility, explicit persistent and temporary interpretations,
each rejected field condition, contradictory retention/expiry and unsupported
route selection. Exercise the real target/preparation callers and ensure
rejection happens before provider work. Finite diagnostics may identify the
rejected condition, never submitted values or native exceptions.

The later lifecycle owner must prove ownership isolation, expiry races,
partial creation, lost runner, repeated cleanup, remaining-resource reporting
and unchanged production behaviour. Local policy proof is not deployment,
permission-boundary, independent-expiry or AWS cleanup proof.
