<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.capability.environment-lifecycle.policy.readme
version: 1
status: active
created_on: "2026-11-26"
updated_on: "2026-11-27"
layer: 04.deploy
domain: deployment.environment-lifecycle
disciplines: [architecture, security, sre]
kind: documentation
purpose: Explain checked environment lifetime settings and the boundary between temporary policy and resource deletion authority.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.capability.environment-lifecycle.policy
  path: scripts/04.deploy/lifecycle/00-target-alignment/capabilities/environment-lifecycle/policy/implementation.py
-->
# Checked environment lifetime settings

A production environment should not become disposable because a setting is
missing or misspelled. [implementation.py](implementation.py) checks the
optional `environment_lifecycle` mapping in an already parsed target profile.
It neither reads AWS nor creates, changes or deletes resources.

The [owning standard](../../../../../../../.agentic/04.deploy/00-target-alignment/standards/require-environment-lifecycle-policy.md)
defines the safety boundary. This small Python module is the single executable
owner of the policy conditions; it does not add another YAML reader or a
deployment engine.

## Inputs and checked results

With no `environment_lifecycle` key, `read(profile)` returns a frozen
`LifecyclePolicy` with `mode="persistent"`, `data_retention="preserve"`,
`max_duration_seconds=None` and `explicit=False`. That is the compatibility
behaviour for existing profiles, not permission to clean them up.

This illustrative explicit production setting returns the same lifetime and
retention choices, but `explicit=True`:

```yaml
environment_lifecycle:
  mode: persistent
  data_retention: preserve
```

This illustrative temporary setting is a valid policy, not a deployable target
or a cleanup approval:

```yaml
environment_lifecycle:
  mode: temporary
  data_retention: discard
  max_duration_seconds: 7200
```

The chosen duration belongs to the target/session; `7200` is an example, not a
global constant. The result contains those checked fields and `explicit=True`.
It does not contain a start time, an expiry observation, resource identities or
a flag granting deletion authority. Actual session admission must establish
those facts separately under the approved execution boundary.

## Public interface and callers

- `read(profile)` validates a mapping and returns `LifecyclePolicy`. Explicit
  null, empty or malformed settings fail instead of falling back to production.
- `LifecyclePolicy` is a frozen value containing mode, data treatment, maximum
  duration and whether policy was explicit. Consume the result of `read`; direct
  construction is not validation or execution authority.
- `PolicyFailure.code` identifies a finite rejected condition. Actual check
  paths never copy rejected values or native exceptions into the error.
- `require_persistent(policy)` checks a policy returned by `read` for routes
  which still use fixed resource bindings. It rejects temporary mode with
  `environment-lifecycle-session-binding-unsupported`.

The existing core target checker and shared AWS preparation reader both call
this owner. The core checker preserves conditions through `DeclarationFailure`;
the preparation reader prefixes them with `preparation-inputs-` and projects
successful checked fields into its existing JSON-compatible result dictionary.
Persistence preparation, entity alignment and declaration coverage consume
that existing reader. Current fixed routes reject temporary settings before
provider work; session-specific deployment support is not implemented here.

For example, `mode: persistent` with `data_retention: discard` produces
`environment-lifecycle-persistent-data-retention-conflict`. A null mapping is
different from an absent mapping and produces `environment-lifecycle-policy-null`.
The tests check these distinctions at the real callers without exposing input
values. The helper does not authorize retry after a provider failure.

## Proof and limits

The existing [preparation input fixtures](../../../declaration-coverage/runtime-configuration-test.py)
cover defaults, valid policies, field/combination rejection, shared validator
use, immutable results, strict profile parsing, safe diagnostics and the real
preparation/coverage callers. The existing selector catalog owns test execution;
test source alone is not a passing result.

These local fixtures cannot establish AWS ownership, production isolation,
session expiry, cleanup or reduced spend. Those remain separate lifecycle
implementation and live-proof obligations.
