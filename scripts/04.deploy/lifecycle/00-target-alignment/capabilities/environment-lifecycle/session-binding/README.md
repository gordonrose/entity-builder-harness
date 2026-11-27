<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.capability.environment-lifecycle.session-binding.readme
version: 2
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
calls these functions through `load_session_plan`. Its ordinary `load` function
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

The AWS result explicitly says `execution_status: not-admitted`. Its derived
prefix is bounded for the existing templates but uses only part of the session
ID: later creation must reject collisions, not adopt an existing resource.
Production source settings remain separately labelled in `source_configuration`.
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
`activation_templates` and `activation_parameters` contain only
templates with declared service counts. They use the same captured sources and
temporary exclusions, selecting the source-owned active counts instead of zero.
`discard_templates` and `discard_parameters` cover every captured template. They
start from the same stopped creation projection and apply only its declared
retention/protection changes; no extra source read or application setting is
introduced. The reader's `discard_projection(original, stopped)` returns a copy
and rejects unsupported resource types, retention paths or source expectations.
It is a source check, not a resource-removal observer.

The network template's ranges and availability zones still need reviewed execution
inputs; the source plan does not invent them or resolve live outputs. The later
preflight must bind those choices and observe the exact owned producer stack
before using its outputs. A supplied VPC/subnet identifier cannot replace that
ownership proof. These captured mappings establish intent, not a completed network.

## Downstream handoff, not yet a live command

If a runner loses its connection after submitting a change, a replacement must
observe that operation rather than blindly submit it again. Two new shared AWS
helpers address that handoff. This section covers their public API only, not
the unrelated helpers in that directory.

[`SessionRecords`](../../../../../shared/provider-adapters/aws/session_records.py)
retains one versioned session document outside the disposable environment.
Its constructor takes the exact bucket/key, account/region/profile, child-process
environment, checked binding, clock and storage-protection validator. `binding`
returns a copy. `initialize()` retains the first session without replacing a
foreign one; `seal()` closes new creation while preserving every operation.
`storage(kind)` supplies the existing reservation protocol with creation,
activation or cleanup-preparation retention. Creation and activation require an
open, unexpired session; cleanup preparation requires a sealed session.
Conditional writes require the observed ETag,
an opaque comparison token. Exact version, ETag and body readback must confirm
a new reservation.
`SessionRecordFailure.code` contains a finite reason, never the object body.
`CLI_FAILURE_CODES` is the shared allowlist for preserving supported provider
failure reasons, not permission to log the provider's message.

[`SessionOperations`](../../../../../shared/provider-adapters/aws/environment_sessions.py)
accepts the captured source plan, matching records, qualified provider and
operation validator. It rejects a production stack or wrong stack/template pair.
Its `initialize()` and `seal()` validate the operation before delegating to the
record owner. `prepare(kind, ...)` and `execute(kind, ...)` take the exact stack,
template reference, parameter rows and observation function. The validator sees
copies of the full proposed arguments, source plan and retained identities;
`execute` also binds the earlier preparation. The existing change-set engine
still owns submission tokens. `SessionOperationFailure.code` preserves bounded
handoff/known provider reasons without raw exception text.

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
Actual readiness and count-only provider changes remain the preflight validator's
job. Sealing or expiry prevents a fresh activation; retained operations still
select observation, not submission.

After sealing, `prepare-discard` uses the captured discard template and the same
zero-count parameters as creation. In the persistence example, only the database's
two snapshot policies, deletion protection and automated-backup deletion setting
change; its backup retention period and application settings stay unchanged.
There is no caller-supplied cleanup-template override. Unsupported public input
keys fail with a finite operation-inputs-invalid reason before remote access.
The qualified validator must still compare the actual source, deployed parameters
and reviewed changes; matching map keys alone does not authenticate a template.
This preparation does not delete the database or prove snapshots/logs are gone.

Validators must inspect actual authority, protected storage and armed expiry
evidence. Returning `None` is their success convention, not proof manufactured
by these helpers. The creation identity needs a server-enforced deadline for
both resource creation and record writes; cleanup needs access after that time.
No live provider factory, physical deletion, completed-session transition or
successor-session API is implemented here. The public workload commands are
not yet connected, and a successful observation does not prove cleanup.

## Proof and remaining work

The existing [preparation tests](../../../declaration-coverage/runtime-configuration-test.py)
exercise this through its real preparation consumer; the existing
`preparation-inputs-regression` check owns registered proof. Test execution and
current results belong in the task record, not this guide.

The [lifecycle standard](../../../../../../../.agentic/04.deploy/00-target-alignment/standards/require-environment-lifecycle-policy.md)
still requires durable resource ownership, effective permissions, independent
expiry, fresh mutation checks and verified cleanup. None is implemented by this
read-only helper. A failed test must eventually clean up its proved-owned resources,
but a valid intent or source plan alone grants no creation or deletion authority.
