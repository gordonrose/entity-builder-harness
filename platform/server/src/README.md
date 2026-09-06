# Platform Server Source Map

This directory implements `@kanbien/platform-server`. External consumers use
the package root. `index.ts` is the deliberate public barrel; `main.ts` and
`transport.ts` are internal process implementation details even though the
approved image build supplies a runtime shim for `main.ts`.

| File | Main question it answers | Why it is separate |
| --- | --- | --- |
| `index.ts` | “Given a valid mounted app registry, which policy steps may run a route handler?” | Request policy and app adaptation should remain readable without Node socket details. |
| `transport.ts` | “How do untrusted Node HTTP bytes become a bounded, cancellable platform request?” | Listener limits, socket state, and connection draining are transport mechanics, not route policy. |
| `main.ts` | “How does a generic server process start and stop?” | Process wiring should not force the generic HTTP layer to choose apps or providers. |

## `index.ts` — policy pipeline and route adaptation

`createPlatformServerShell` mounts the supplied apps, validates their complete
registry and configuration, checks that required tenant/authorizer seams are
available, creates lifecycle control, and compiles route patterns. It exposes
two paths: `handle` for deterministic tests or non-Node hosts, and `listen`
for the Node transport.

The request path owns request outcome logging, exact-origin CORS, standard
security headers, pre-auth rate-limit checks, health endpoints, route matching,
authentication, broad permission authorization, tenant derivation, request
context, input validation, optional resource authorization, handler execution,
and safe response/error mapping. It deliberately cannot select Cognito, Redis,
an app, or an AWS service.

Platform-owned response headers remain authoritative. This prevents an app
handler from replacing the request ID, CORS decision, content-security policy,
or other shared security header while still allowing a harmless app-specific
header.

## `transport.ts` — converting hostile network input into a bounded request

This file is the first code to see raw Node HTTP input. It limits header bytes,
header count, body bytes, header/request/handler time, in-flight work, and
requests per socket. It rejects unsupported HTTP methods rather than treating
them as `GET`, validates a declared content length before reading a body, and
accepts non-empty JSON bodies only with a JSON content type.

It runs transport admission before it reads the body. Therefore a request
rejected by the rate limiter does not consume JSON parsing or app-handler
capacity. The listener creates a request ID when the upstream value is absent
or malformed, passes an abort signal into the request context, maps transport
failures through the shared safe error path, and closes gracefully: stop new
connections, allow current work a bounded time, then abort/close remaining
connections.

A handler timeout is not permission to forget a still-running promise. The
listener aborts its signal and returns a safe timeout response, but retains the
request's concurrency slot until that handler settles. This protects capacity
when an app handler fails to honour cancellation; the handler should still
honour the signal so its own downstream work can stop promptly.

The peer address comes from Node's socket only. Proxy-header interpretation is
not safe as a generic helper because it requires target-specific proof of which
ingress is trusted.

## `main.ts` — generic lifecycle host, not product composition

`startPlatformServerProcess` supplies generic environment/config collection,
starts the lifecycle before listening, turns a listen failure into a stable
startup result, and begins lifecycle draining before listener shutdown. It also
installs signal handlers for the process host.

It takes an injected app list, authentication hook, rate limiter, and transport
options. A product/deployment entrypoint is responsible for supplying any of
those target-selected pieces. That separation lets the same server mechanics
host a different product or provider without generic platform code learning
about either one.
