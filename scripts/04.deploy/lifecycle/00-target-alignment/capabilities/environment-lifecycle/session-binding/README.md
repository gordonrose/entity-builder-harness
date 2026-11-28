<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.capability.environment-lifecycle.session-binding.readme
version: 3
status: draft
created_on: "2026-11-27"
updated_on: "2026-11-27"
layer: 04.deploy
domain: deployment.environment-lifecycle
disciplines: [architecture, security, sre]
kind: documentation
purpose: Explain checked temporary-session intent and captured source bindings without implying deployment or cleanup authority.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.capability.environment-lifecycle.session-binding
  path: scripts/04.deploy/lifecycle/00-target-alignment/capabilities/environment-lifecycle/session-binding/implementation.py
-->

# Temporary-session source binding

A test run can use a production-capable build without owning the production
environment. This helper keeps the build's source target separate from the
identity and lifetime of one temporary run. A **binding** is the checked record
connecting that run to the declaration files used to plan it. It is not proof
that the run owns any AWS resource.

## Files and callers

[implementation.py](implementation.py) defines the checked records and their
validation. It reuses the [lifecycle policy reader](../policy/README.md), rather
than copying persistent/temporary policy rules.

The existing AWS [preparation reader](../../../provider-adapters/aws/preparation-inputs.py)
calls these functions through `load_session_plan`, `revalidate_session_plan`
and `recover_session_plan`.
The first plans a new run; the second checks the unchanged plan of an existing
run, including after its expiry. Its ordinary `load` function
still accepts only persistent source profiles. The session document supplies
only a temporary lifetime override; it does not copy or modify the source profile
or change the qualified package's target.

## A small example

This invented input represents a two-hour run. Times are UTC epoch seconds:
whole seconds since 1970, not local time strings.

```python
document = {
    "schema": "deploy/environment-session-intent/v1",
    "target": "example-platform",
    "scope": "example-service",
    "session_id": "a" * 32,
    "starts_at": 1000,
    "expires_at": 8200,
    "environment_lifecycle": {
        "mode": "temporary", "data_retention": "discard",
        "max_duration_seconds": 7200,
    },
}
```

`read(document, target="example-platform", scope="example-service", now=1000,
approved_max_duration_seconds=7200)` returns a frozen `SessionIntent` containing
those checked identities, times and the checked lifecycle policy. At `now=8200`
it raises `SessionFailure` with code `environment-session-expired`. A shorter
approved maximum rejects the same request instead of silently extending it.
Booleans and fractional numbers are not accepted as timestamps or limits.

Cleanup still needs to check that original request after its two hours end.
`read_existing` accepts the same document at `now=8200` and returns its original
`expires_at=8200`; it does not extend the run or allow it to start again. A future
start, invalid clock or excessive duration still fails. This is a read-only check,
not evidence that an existing record or AWS resource belongs to the session.

The calling operation supplies the expected target/scope, current time and its
approved maximum. The document cannot supply a resource name, source hash or
ownership assertion. Missing/extra fields and invalid policy fail closed.

## What the exports do

- `SessionFailure` exposes a finite `code`; rejected values and native exceptions
  are not error messages. `require` is the small assertion helper used internally.
- `SessionIntent` holds the checked request. Its nested lifecycle is also frozen;
  later edits to the input dictionary do not alter this result.
- `read` checks the request against the caller's selected target, scope, time and
  duration limit, using the existing policy reader.
- `read_existing` uses the same checks without requiring time to remain before
  the original expiry. Use it only to revalidate an existing session, never to
  choose whether new creation is allowed.
- `SessionBinding` combines an intent, sorted immutable source-identity pairs,
  selected scopes and a digest of those pairs. A digest is a content fingerprint,
  not authorization or a signature.
- `bind_sources` checks the shape of identities supplied by the trusted preparation
  adapter. It does not read files, establish their truth or admit external hashes.
  The actual adapter hashes the same bytes it parsed, not caller-provided values.

The preparation reader captures declarations once, follows validated scope
dependencies, projects names through the shared CloudFormation reader and
rechecks that captured files are unchanged before returning. This is not an atomic
filesystem snapshot and cannot establish freshness after return. Imported helper
qualification remains separate from declaration-file fingerprints.

Its `revalidate_session_plan(root, retained_plan, now,
approved_max_duration_seconds)` uses that same renderer to capture the source
again. It checks the complete resulting plan against the retained one: templates,
phase parameters, dependency order, output bindings and source fingerprints must
all agree. Changing a template while retaining its old fingerprint therefore
cannot pass. Equivalent checked records from separately loaded Python modules
are compared by their fields, not their class identity.

A replacement worker may have only the saved session record, not the original
Python plan. `recover_session_plan(root, record_document, now,
approved_max_duration_seconds)` rebuilds that plan using the original policy
maximum retained in its base. The caller supplies the document and actual
observation time from one checked `SessionRecords.observe_existing()` result.
The reader reuses `read_existing`, renders the original source, and checks both
the source fingerprint and the complete plan fingerprint. It returns an ordinary
typed, `not-admitted` plan; it does not write, reacquire packages or reopen expiry.
For example, a policy maximum of 9,000 seconds remains 9,000 even when the actual
run lasts 7,200 seconds and the operator approved at most 8,000. Recovery must not
guess the original policy from either other number. Record ownership and version
validation remain the record owner's responsibility; supplied hashes alone are
not a substitute.

The AWS result explicitly says `execution_status: not-admitted`. Its derived
prefix is bounded for the existing templates but uses only part of the session
ID: later creation must reject collisions, not adopt an existing resource.
Production source settings remain separately labelled in `source_configuration`.
The source profile's `provider.session_execution_roles` declares distinct name
suffixes for creation and cleanup. The planner combines those with the checked
account and temporary prefix, returning their AWS identity strings in
`execution_roles`. These are expected identities, not credentials or permission
claims. Names must fit IAM's 64-character limit and differ even when case is
ignored. A session document cannot override a role or AWS profile. Complete-plan
revalidation and cold recovery reject a changed or missing retained role pair;
the later protected controller must still prove ownership, permissions and
account-wide name uniqueness before use.
`stack_templates` pairs each derived stack with its exact captured template,
including dependency stacks. `creation_parameters` separately records checked
temporary settings; neither is an instruction to mutate AWS.
`stack_dependencies` lists each stack and its direct suppliers; `stack_order`
puts suppliers before consumers. Optional foundation prerequisites are declared
under `provider.foundation.instance_prerequisites` in the source profile, not
selected by a service name in Python. `prerequisite_components` records their
component names. `stack_parameter_sources` contains immutable rows of consumer
stack, parameter, producer stack and output name. For the current network binding,
these rows supply the foundation's VPC, CIDR and subnet inputs from the separately
created network. Its stack precedes foundation and workloads in `stack_order`.
Ordinary persistent preparation does not select these extra components.

Each remaining input has a small source declaration, called a recipe, in its
provider binding's `execution_parameters` map. It names a reviewed choice,
qualified package field, checked source value, owned stack output or explicit
provider observation. It cannot contain an arbitrary value or lookup expression.
Controls, preserved defaults, prerequisite mappings and recipes must account for
every parameter without overlap. Ordinary persistent loading ignores these
temporary-instance recipes.

The plan returns recipes in `execution_parameters`; `execution_output_sources`
records the additional producer/output connections, while `execution_source_values`
contains only checked repository references and dependency database names.
`publication_selections` binds each selected publication's repository, expected
package/program/candidate identities, publishing workflow, source branch and
receipt-artifact contract. Captured workflow bytes have their own fingerprint.
These are sorted tuple rows, included in
complete-plan revalidation. They contain no image qualification claim, selected
network values or credentials; the later execution owner must establish those
facts before submitting anything.

An explicit `omit-if-unused` recipe supplies no value. The shared projection
checks that the selected parameter is no longer mentioned after temporary
resource exclusions, then removes only its declaration. It rejects unsupported
template transformations and uncertain references instead of guessing. This
removes the unused publication-identity input when its delivery role is excluded,
and explicitly selected email declarations when their optional groups are absent.
The production template retains them. Every unselected parameter stays intact.
Templates can name existing default-false conditions in
`Metadata.TemporaryDefaultConditions`; temporary projection chooses those same
defaults and their conditional branches without changing persistent projection.
The database's resource-owned secret reference stays unresolved in the template;
no password is read or placed in the session record.

`activation_templates` and `activation_parameters` contain only
templates with declared service counts. They use the same captured sources and
temporary exclusions, selecting the source-owned active counts instead of zero.
Both creation and activation apply the source-declared disposable retention
settings. A temporary database therefore starts without deletion protection or
snapshot retention and activation does not restore them. Production protections
and seven-day automatic-backup retention stay unchanged. Ordinary temporary
functionality tests select zero automatic-backup retention from creation through
shutdown; they do not prove production backup recovery or replication. Such
tests need a separately admitted retention-enabled lifecycle and cleanup proof.
`discard_templates` and `discard_parameters` cover every captured template and
equal the checked stopped creation projection. No extra source read or application
setting is introduced. The reader's `discard_projection(original, projected)`
returns a copy of an original phase projection, changing only declared retention
paths. It rejects unsupported resource types, paths and source expectations,
including applying it again to already-modified database settings. It is a source
check, not a resource-removal observer.

New foundation/persistence instances also explicitly own the Container Insights
and two RDS export log groups. Production keeps their retention policies;
temporary projection selects deletion without changing log export settings or
log-retention days. Dependencies create each group before its producer. This
does not import or adopt groups belonging to an already-running deployment.

The network template's ranges and availability zones still need reviewed execution
inputs; the source plan does not invent them or resolve live outputs. The later
preflight must bind those choices and observe the exact owned producer stack
before using its outputs. A supplied VPC/subnet identifier cannot replace that
ownership proof. These captured mappings establish intent, not a completed network.

## Downstream handoff, not yet a live command

If a runner loses its connection after submitting a change, a replacement must
observe that operation rather than blindly submit it again. Two new shared AWS
helpers address that handoff, with a separate command wrapper described below.
This section covers those APIs only, not
the unrelated helpers in that directory.

[`SessionRecords`](../../../../../shared/provider-adapters/aws/session_records.py)
retains one versioned session document outside the disposable environment.
Its constructor takes the exact bucket/key, account/region/profile, child-process
environment, checked binding, clock and storage-protection validator. `binding`
returns a copy. `initialize(base)` retains the first checked input collection
without replacing a foreign one; the higher-level adapter described below
constructs this collection. `seal()` closes new creation while preserving every
operation. `observe_initialization()` checks for an existing record before any
package acquisition; absence is usable only while the original lifetime is open.
`observe_existing()` reads a positively confirmed existing record and validates
the current clock, without initializing or writing anything. Missing state is a
failure, not an empty session ready for cleanup.
`storage(kind, reconciled_operations_sha256=..., physical_manifest_sha256=...)`
supplies the existing reservation protocol with creation,
activation, cleanup-preparation or deletion retention. Creation and activation
require an open, unexpired session; cleanup preparation requires a sealed
session. The first deletion atomically moves a sealed session to `deleting`,
provided its observed set of earlier operations and that stack's retained
resource-identity record still match. Further deletion
is allowed, but no new creation, activation or cleanup-preparation operation can
enter that state. `seal()` cannot reopen it. Deletion has only a `delete` phase,
not prepare/execute phases. Retained attempts remain available for observation.
Conditional writes require the observed ETag,
an opaque comparison token. Exact version, ETag and body readback must confirm
a new reservation. The same object holds an immutable base collection and one
append-once resolved input entry per operation kind and stack, within 65,536 bytes.
`check_input_admission(kind)` checks whether new input resolution is allowed;
`retain_inputs(kind, stack, base_sha256, inputs)` saves its result before a
request can be reserved. Earlier requests bind the stable base and their own
entry, so adding a later entry does not alter earlier request identities.
`SessionRecordFailure.code` contains a finite reason, never the object body.
`CLI_FAILURE_CODES` is the shared allowlist for preserving supported provider
failure reasons, not permission to log the provider's message.

The record schema is explicitly versioned; it does not silently upgrade older
documents. Its immutable base keeps the captured creation/cleanup role pair once.
`checked_execution_roles` is the record owner's shared identity check, also used
by the session adapter: it checks the account, session prefix, closed pair,
name lengths and case-insensitive separation, then returns a copy. It does not
read IAM policies or grant permission. Non-delete requests explicitly retain
`disable_rollback: true`: an execution failure leaves resources available for
reconciliation instead of relying on an omitted AWS default. The command wrapper
requires and sends the actual boolean `DisableRollback=true`, not `1` or a text
value, and accepts no conflicting `OnStackFailure` option.
Each stack keeps one complete creation-parameter map
and one original full AWS stack identity. Later updates keep a fingerprint of
the checked deployed values instead of copying that map again. Separate original
custody fingerprints bind the creation request, change-set identity, original
template, parameters and logical-resource/type set. Successful creation evidence
additionally binds its successful event. A partially created stack can therefore
have ownership evidence without being ready to supply outputs or prove a test.

`retain_ownership(stack, stack_id, evidence=None, *, custody=None, outcomes=None,
physical=None)`
atomically appends the adapter's checked ownership and operation outcomes; an
existing proved value cannot be replaced. Its optional physical observation
uses one sorted source position per logical resource/type. Each position is
unknown, positively never allocated, or the fingerprint of its physical identity.
Only an unknown position can advance; a later missing row cannot erase an identity.
An unchanged observation does not append another record version. The bounded
observation fingerprint/time changes only when another identity is discovered.
Additional source-indexed positions retain fingerprints of checked security-rule
and ECS-service relationships, immutable database lineage, and the bounded ID of
each namespace's hosted zone. A hosted zone is the DNS resource created behind a
private namespace. These positions advance only from unknown to a checked value;
known database/zone substitutions reject a fresh deletion. Provider responses
and general raw physical identifiers are not retained in this map.
`retain_outcome(key, outcome)` separately
records authenticated terminal observations or an actual sender's definite
pre-submission rejection. An operation
outcome names its reservation, terminal state and evidence fingerprint; it does
not contain raw provider output. `operations_sha256(document)` fingerprints the
non-deletion operation set for the deletion admission check. The record owner
checks shapes and retention; the adapter supplies the actual observation proof.

Before every conditional write, the record owner calculates the size of a
possible cleanup record for every stack whose creation is already reserved,
including a newly proposed reservation. It allows space for the remaining
discard and deletion requests, custody, terminal outcomes and every resource's
identity fingerprint and relationship/database/zone positions, using the same
request constructor as the actual operations. Exceeding the limit rejects that
write before it grants submission authority. A later rejected creation therefore
cannot spend space needed to clean up earlier stacks. Actual stack identifiers
are bounded at 2,048 characters; unused identity slots reserve that maximum.
Unknown positions expand to full fingerprints in this calculation, even when
some identities are already recorded. No universal maximum for a raw physical
identifier is assumed. This allowance covers the current teardown intents,
**not yet implemented**
physical-completion reports or successor-session records.

[`SessionProvider`](../../../../../shared/provider-adapters/aws/session_cli.py)
is the separate AWS command wrapper. Its constructor takes `profile`, `region`
and a copied child-process `environment`; construction makes no AWS call.
Calling it with a supported service, operation and exact argument fields returns
a JSON object through the existing shared CLI invoker. The supported calls are
CloudFormation create/execute change set, delete stack, describe change set,
describe stack/events, get the original template and list stack resources;
EC2 availability zones and managed prefix lists; ECR repository, image and scan
observations; and the exact native resource/backup/hosted-zone reads used by the
cleanup observer below. Each operation has closed argument fields; for example,
snapshot reads select only manual, automated or AWS Backup snapshots and exclude
public/shared snapshots. The existing connected fixture uses this same wrapper with a
fake AWS executable, including package acquisition's ECR calls.

The template read accepts only `TemplateStage="Original"`, with the exact
`StackName` and optionally `ChangeSetName`. It cannot select a transformed
template or accept arbitrary extra fields. The resource-list read takes only
`StackName`; its returned inventory still needs the adapter's ownership checks.

For example, a deletion supplies `StackName`, `ClientRequestToken` and the
source-bound cleanup `RoleARN`. Change-set creation also requires its selected
role; execution takes no role override. The wrapper serializes these exact
fields into a private temporary JSON file. Missing roles, malformed role strings
and extra fields reject before a process starts. The adapter, not this transport,
checks that the role matches the captured session and operation. An exactly empty successful execute/delete
response becomes `{}`. Whitespace-only or malformed responses fail, and reads
also reject empty responses. `MAX_INPUT_BYTES` bounds the encoded request at
131,072 bytes, separately from the template limit; escaping and other fields can
make a valid-size template exceed it. The wrapper requests one AWS attempt and
uses fixed timeouts, profile and region, with configured endpoint overrides
disabled. Automatic pagination remains enabled; a remaining continuation token
is rejected. Its process timeout does not bound total response bytes or pages.

`SessionProviderFailure.code` exposes only a reason from `FAILURE_CODES`, which
includes the preserved reasons in `CLI_FAILURE_CODES`; native messages and
arguments are not diagnostic output. The adapter recognizes this concrete error
class rather than trusting an arbitrary object's `code`. This wrapper transports
requests only: it does not qualify permissions, arm expiry or prove ownership.

[`SessionOperations`](../../../../../shared/provider-adapters/aws/environment_sessions.py)
accepts the captured source plan, matching records, qualified provider and
operation validator, plus explicit `source_root` and
`approved_max_duration_seconds` context. Missing or invalid source context rejects
before remote work; there is no implicit source-directory fallback. It rejects
a production stack or wrong stack/template pair.
The directory is needed for fresh source validation, not for observing a retained
operation. Losing that directory cannot grant a retry or prevent observation-only
recovery.
Its `initialize(choices=..., publications=...)` takes grouped network choices
and a publishing run/source selection for each distinct pipeline, not a local
receipt or a list of deployment parameters. The foundation checker validates
private address ranges, non-overlapping subnets and actual available regional
zones. The package [acquisition helper](../../../../../lifecycle/40-package/package-custody-receipt/acquire.py)
reads the exact GitHub run/artifact, checks its signed image provenance, and
checks the immutable registry image and scan. Missing verifier support fails
closed; local schema validity alone cannot substitute for authentic publication.
The retained base contains checked choices, non-secret package evidence,
provider facts, source-bound cleanup shapes, the original policy maximum and
the exact captured execution-role pair.
Repeating initialization with the same selection reads the
retained base without acquiring again; changing the selection rejects it.

`prepare(kind, ...)` and `execute(kind, ...)` take only the exact stack and
template reference. They derive complete parameters
from the captured declarations, retained base and earlier owned stack outputs;
caller-supplied parameter lists are rejected. The validator sees
copies of the full proposed arguments, source plan and retained identities;
`execute` also binds the earlier preparation. The existing change-set engine
still owns submission tokens. Creation and activation select the creation role;
discard preparation and every reconstructed deletion request select cleanup.
Those selections are part of the saved request fingerprints, not caller options.
`SessionOperationFailure.code` preserves bounded
handoff/known provider reasons without raw exception text. `seal()` still checks
the operation before delegating to the record owner.

`reconcile_operation(kind=..., stack=..., phase=...)` observes the existing
reservation through concrete AWS readers; it accepts no callback or supplied
outcome. Its copied result contains `operation`, `status`, `reason`,
`request_sha256` and `provider_status`. Status distinguishes `unreserved`,
`not-submitted`, `pending`, `ready`, `succeeded`, `failed` and `unknown`.
For example, a pending change-set preparation returns `pending`; requesting
execution then rejects without consuming its execution reservation. Once ready,
execution checks readiness again immediately before sending. A result of `ready`
is an observation, not permission reusable after AWS state changes.

The observer matches the original change-set identity or the latest exact-token
root event and current stack. Missing events remain unknown. Only authenticated
terminal facts are appended; pending and unknown observations do not write.
An existing preparation's evidence is not replaced merely because AWS's later
execution-status field changes. Deletion's `succeeded`/`DELETE_COMPLETE` result
means that operation finished, not that every physical resource or backup is gone.

For example, network creation uses the checked address/zone choices. Foundation
creation then reads that network's outputs, but only after matching its original
reserved CREATE requests, full AWS stack identity and successful creation event.
The database and application follow the same rule for their suppliers. A ready
stack with a matching name is insufficient. Before updating a stack, its checked
creation evidence is retained because AWS may remove the original change set.
Later reads rebind that evidence to the retained requests and exact stack/event.
Updates preserve every non-control deployed parameter and reject unexpected
changes. Retained operations do not resolve inputs or acquire packages again.

`runtime_view(stack=..., required_outputs=...)` gives a task-binding reader the
checked current resources of one captured stack. The output selector is a list
or tuple of unique source-declared names; an empty selection requests no outputs.
It accepts no supplied template, parameters, resource IDs or phase override.
For example, a task reader can request its workload view and separately request
the foundation's declared cluster output. One stack's view does not prove the
other stack's ownership.

The method matches original successful creation and every later retained
operation, checks the current template and deployed parameters, positively
retains that evidence, then reconstructs the physical resource IDs. Every
expected resource must have a known allocated identity. A final read checks that
the operation set did not change while the view was assembled. Retention failure
or substituted resources return no usable view.

For a database, runtime qualification also checks its exact AWS identifier and
immutable identity, integer-zero automatic-backup retention and no pending
retention enablement. Missing optional replication information is not proof that
no copies exist; malformed or reported replication rejects this runtime check.
Policy failures do not prevent deletion of an independently proved-owned stack.
Identity substitution does. These observations do not establish lifetime backup
absence or change the separate cross-region cleanup result from unknown.

The copied `deploy/aws-session-runtime-view/v1` result contains the session
binding and source-plan fingerprint, account/region, component, exact stack ID,
current phase, template reference and parsed template, parameters, logical-to-
physical resource map, selected outputs, original custody fingerprints and
integer observation time. Custody means the retained evidence tying that exact
stack to its original creation. These internal resource identifiers are inputs
to the existing workload validators, not a safe diagnostic report.

A ready but unexecuted activation still returns the creation phase; it has not
changed the stack. A pending or failed executed update cannot be hidden behind
the earlier successful creation. A stable successful phase must also report its
expected attached AWS role. A later checked discard preparation can transition
between creation and cleanup roles; that ambiguous transition returns no runtime
view. It does not prevent an independently proved-owned cleanup request from
explicitly selecting the cleanup role. Change-set descriptions do not report
that role: original submitted arguments and retained custody bind it instead.
An expired or sealed session may still be
observed, but the result never reopens admission or authorizes a task launch.
Actual workload/storage/controller integration remains incomplete.

For example, the [connected fixture](../../../../../shared/provider-adapters/aws/environment-sessions-test.py)
initializes a record, prepares then executes `creation`, and repeats both calls.
Only the first calls submit; the repeated calls return fresh observations of the
retained operations. After sealing, a new creation execution fails with an
admission-closed reason; `prepare-discard` may proceed only through its own
validator. A lost storage response never grants fresh submission authority.
These examples use isolated fake AWS subprocesses, not real cloud resources.

After creation and database preparation are positively observed, the eventual
live caller can prepare and execute `activation` using its captured parameters.
For the current entity example, creation leaves the service at zero and the
activation projection selects one; the source template's production default
remains zero. Foundation has no service-count activation. The API rejects a
caller-supplied activation template or count outside the captured selection.
The adapter checks original creation, current stack readiness and parameter
preservation; database preparation and the actual reviewed change set remain the
qualified preflight validator's job. Sealing or expiry prevents a fresh activation; retained operations still
select observation, not submission.

After sealing, `prepare-discard` uses the captured discard template and the same
zero-count parameters as creation. The temporary database's two deletion policies,
deletion protection and automated-backup deletion setting were already selected
at creation and kept during activation. Shutdown therefore changes only the
captured running service counts; the already-zero temporary backup retention
and application settings stay unchanged.
There is no caller-supplied cleanup-template override. Unsupported public input
keys fail with a finite operation-inputs-invalid reason before remote access.
Before a fresh discard submission, the adapter reads the existing sealed record
and invokes the concrete source revalidator at its observed current clock. It
loads the fixed preparation owner, not executable code from `source_root`.
Changed source or a modified plan stops submission. The retained reservation
remains: retry observes that operation rather than submitting again, and a
source problem does not prevent observation-only reconciliation.
The qualified validator must still prove the deployed parameters, reviewed
changes, source/controller qualification and live ownership. Matching a source
plan does not authenticate the running controller or its permissions.
This preparation does not delete the database or prove snapshots/logs are gone.

`delete(stack=..., stack_id=...)` selects one captured stack and its
full original AWS stack identifier. Beyond its account/region/name checks, the
adapter reconstructs original CREATE custody through the reserved request,
change set, original template, parameters and resource inventory. It retains
that custody before later updates can remove the original change set.

Before the first delete reservation, it reconciles previously admitted
creation, activation and discard operations using their exact tokens and
terminal observations. Missing events, incomplete reads or an uncertain sender
block deletion. A definite `not-submitted` outcome is recorded only when the
actual sender fails its checks before invoking AWS—not after a lost response.
`CREATE_FAILED` and `UPDATE_FAILED` are reconciled only against the explicitly
bound failure policy, original ownership, exact execution token, terminal root
event and current stack. The change set's `EXECUTE_FAILED` label is not enough.
Partial creation still cannot supply successful outputs.

The current deployed template and parameters must already match the captured
discard projection. If they match without an update, no artificial no-change
update is required; retained earlier attempts still need reconciliation. This
check also applies after failed execution. Equal creation/discard template bodies
cannot excuse active service counts after a failed activation.

`reconcile_stops()` uses that same stopped-template/parameter check across a
sealed or deleting session in reverse dependency order. Its per-stack rows
distinguish work not started, never allocated, stopped, still requiring a stop,
pending, blocked, and an already-reserved deletion that may only be observed.
Earlier successful creation cannot conceal pending activation. A consumed stop
attempt never grants a replacement attempt, and every required stop must finish
before the first fresh deletion closes that phase.

An originally successful creation followed by failed activation may prepare its
first cleanup-only update after sealing. That narrow route preserves original
success evidence and every non-control value; ordinary output consumption still
requires a ready stack. Before sending the cleanup execution, the adapter checks
the actual proposed changes against the captured phase difference: only exact
static property changes, with no additions, replacements or unrelated edits.
Malformed or uncertain observations stop the send. A reserved or failed cleanup
attempt is observed, never automatically replayed under a new label.
An early delete request does not close the still-needed discard preparation.
Once ready, deletion reserves the exact request and enters the one-way deleting
state together. It rechecks both the closed operation set and retained physical
identities before sending. A newly discovered identity at that point stops the
fresh send; it does not rewrite the reserved request or permit a replay. Fresh
deletion also recaptures the original source plan. This does not make an AWS
send atomic with storage or replace effective deadlines, protected exclusions
and exact approved-removal checks in the qualified live validator.

The existing submission engine adds the saved operation token and calls
`delete-stack` once. If its response is lost, calling `delete` with the unchanged
inputs observes the retained operation; it does not submit again, even if local
source is unavailable. A different identifier conflicts with the retained
request. Caller-selected roles, retained-resource lists and forced deletion are
not accepted. The returned observation is not a claim that resources are gone.

`reconstruct_physical(stack=..., stack_id=...)` reads the original unique stack's
resource lineage and checks every recovered identifier against its source position
and retained fingerprint. It returns raw identifiers only for internal consumers;
they are not diagnostic output. It does not require the deleted stack to retain
its old CREATE/UPDATE status, re-admit a mutation, or write another record.
Changed identities, incomplete lineage and previously unknown identities newly
appearing in the response fail closed until positively retained by the method
below. AWS's deleted-stack history is available
for up to 90 days, not indefinitely; loss of it cannot mean resources are absent.

`retain_physical_observation(stack=..., stack_id=...)` is that separate retention
step. It requires closed admission and the saved original creation custody and
exact stack identity. It reads the original stack inventory and conditionally
appends newly known physical fingerprints. It neither rewrites a delete request
nor submits one. Lost/conflicting retention stays uncertain; a later positive
read can observe the retained result without replay. Finding a database's name
after deletion cannot invent its missing immutable backup lineage.

`observe_resource_cleanup(stack=..., stack_id=...)` first checks the original
delete reservation, its exact terminal root event and the current matching stack
in `DELETE_COMPLETE`. It then reconstructs the retained physical identities and
reads each resource through its native AWS API. The result contains logical IDs,
resource types and safe statuses, not raw provider bodies or identifiers. It
does not write, delete resources or mark a session complete.

Rules require saved correspondence to their target security group; disappearance
of a peer/source group does not prove the rule gone. ECS services require their
saved owning cluster and exact native service/cluster identity. Missing
correspondence remains unknown even when deletion of the independently owned
stack was allowed. `inactive` is reported separately from `absent`; it must not
silently mean physical removal or that no tasks remain.

Database checks separately count manual, automated and AWS Backup snapshots and
retained automated backups by the original immutable database identifier, not a
reusable database name. Namespace checks separately read the saved hosted zone.
For example, this deliberately shortened database result could be returned even
after the database itself disappears:

```json
{
  "status": "absent",
  "artifacts": [
    {"kind": "manual-snapshots", "status": "present", "count": 1},
    {"kind": "cross-region-backups", "status": "unknown"}
  ]
}
```

This is not successful cleanup. A regional list cannot prove cross-region backup
absence; that observation intentionally remains unknown until its separate
boundary is qualified. Denied, malformed, incomplete or unsupported reads also
remain unknown. Exact operation-specific missing-resource errors may establish
absence; a general error containing “not found” may not. A secret scheduled for
deletion still counts as present while the native API returns it.

Missing rows and empty physical IDs remain unknown. The narrow never-allocated
case requires closed admission, original creation custody, a positively
unexecuted creation and no unresolved execution reservation. A failed creation
alone does not establish it. Unknown positions do not prevent deletion of an
independently proved-owned stack, but cannot satisfy cleanup completion.

Validators must inspect actual authority, protected storage and armed expiry
evidence. Returning `None` is their success convention, not proof manufactured
by these helpers. The creation identity needs a server-enforced deadline for
both resource creation and record writes; cleanup needs access after that time.
No qualified live cleanup, provider factory, completed-session transition or
successor-session API is implemented here. The public workload commands are
not yet connected, and a successful observation does not prove cleanup.

## Proof and remaining work

The existing [preparation tests](../../../declaration-coverage/runtime-configuration-test.py)
exercise this through its real preparation consumer; the existing
`preparation-inputs-regression` check owns registered proof. Test execution and
current results belong in the task record, not this guide.

The [lifecycle standard](../../../../../../../.agentic/04.deploy/00-target-alignment/standards/require-environment-lifecycle-policy.md)
still requires durable resource ownership, effective permissions, independent
expiry, fresh mutation checks and verified cleanup. Source binding does not
establish those live guarantees. A failed test must eventually clean up its proved-owned resources,
but a valid intent or source plan alone grants no creation or deletion authority.
