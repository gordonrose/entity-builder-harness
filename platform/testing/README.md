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
