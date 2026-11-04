# Platform Testing

`platform/testing` provides deterministic fakes and builders for proving an
app's public platform contract without a real HTTP server, worker, queue,
identity provider, or cloud service.

It is a test-support package, not a production runtime or a substitute for
provider integration tests.

## Boundary

Consumers import `@kanbien/platform-testing`. Its source depends on public core
and platform-contract exports only. Production packages must not rely on it to
run an application; hosts use `@kanbien/platform-runtime` instead.

## Responsibility map

| Path | Responsibility | Verification |
| --- | --- | --- |
| `src/index.ts` | Test logger, metrics, config, contexts, queue messages, registry, mount helper, health runner, and config-schema validator. | `npm run platform:testing:check` |
| `tests/platform-testing-types.test.ts` | Public TypeScript contract proof. | `npm run platform:testing:check` |
| `tests/platform-testing-runtime.test.ts` | Valid/invalid app-mount, namespace, health, config, and fake-helper proof. | `npm run platform:testing:check` |
| `tests/platform-testing-boundaries.test.mjs` | Import-boundary proof. | `npm run platform:testing:check` |

## Matching the production registry

`mountPlatformAppForTest` validates the app ID and passes the app a scoped
registry from `registry.forApp(appId)`. That matches production mounting: a
permission, route, job, or health name must begin with `<app-id>.`, while
duplicate registrations remain global errors. A test that mounts successfully
therefore proves the same registration ownership rule that the runtime applies;
it does not merely check a looser fake.

Equivalent registration checks retain the same value-free contract diagnostic
records as the production registry, including first-match duplicate dimensions
and deferred permission/profile references. An existing policy difference remains:
production resolves resource-authorization permissions during complete-registry
validation; this test helper does not currently perform that extra check.

`validatePlatformTestConfigSchemas` accepts an optional third argument containing
additional diagnostic definitions. It selects upstream configuration evidence
against those definitions and the Core catalog, retaining validated primary and
related records separately from its existing code, message and schema-index detail.
Malformed or unselected evidence is omitted without changing schema parsing.

`mountPlatformAppForTest` also accepts optional `diagnosticDefinitions`.
When the existing app-mount catch returns a failure, it selects the thrown
primary and up to eight companions against Core, explicit definitions and
catalogs the app registered before throwing. Evidence is additive to the
historical error code, contract errors and reason. A malformed primary does not
erase valid companions; getters and nested causes are not diagnostic sources.
The historical `Error.message` projection still runs first and may itself throw.
There is no automatic sink or Runtime dependency in this test helper.
