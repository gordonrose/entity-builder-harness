<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standard.environment-lifecycle-policy
version: 2
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
owns template-declared creation, activation and discard projections. Production
and initial creation retain their data protections. Captured discard preparation
changes only supported source-declared retention/protection paths on the stopped
temporary graph; the [connected session adapter](../../../../scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py)
selects those bytes only for sealed cleanup preparation. It does not accept an
arbitrary cleanup template. Source projection is not physical deletion proof.

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
