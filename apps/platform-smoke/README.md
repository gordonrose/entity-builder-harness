# Platform Smoke App

`apps/platform-smoke` is a deliberately small app contribution used to prove
that the platform contracts, server shell, worker shell, health checks, config,
authentication, and lifecycle can work together. It is not a template for a
future product app's internal architecture.

## Boundary

Consumers import `@kanbien/app-platform-smoke` through its public package
entry point. Hosts compose the exported `PlatformApp`; they do not import the
app's private files. The app declares intent through platform contracts and
does not start a server, select a queue provider, or configure deployment
infrastructure.

## Responsibility map

| Path | Responsibility | Verification |
| --- | --- | --- |
| `src/app.manifest.ts` | Stable app identity, declared permission, route base path, job, health, and required-config metadata. | `npm run app:platform-smoke:check` |
| `src/app.mount.ts` | Public app contribution: config schema, route, job, health check, and lifecycle hooks. | `npm run app:platform-smoke:check` |
| `src/index.ts` | Deliberate public exports only. | `npm run app:platform-smoke:check` |
| `tests/platform-smoke-runtime.test.ts` | Server and worker composition proof using platform test dependencies. | `npm run app:platform-smoke:check` |

## Current semantic names

The app ID is `platform-smoke`. Its permission is
`platform-smoke.smoke:read`; its route, job, and health names use the same
owner prefix. This lets the runtime reject an accidental declaration in another
app's namespace during startup or contract testing.
