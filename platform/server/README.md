# Platform Server

`@kanbien/platform-server` is the provider-neutral HTTP process layer. It
turns a product-composed list of public `PlatformApp` contributions into a
safe HTTP server: it validates the mounted registry, applies the shared request
pipeline, exposes health endpoints, invokes route handlers, records bounded
operational outcomes, and coordinates graceful shutdown.

Apps do not import this package to open sockets or install middleware. They
declare routes through `@kanbien/platform-contracts`; a product composition
root chooses which public app modules belong in one process; a target-specific
entrypoint supplies selected authentication and other provider adapters.

## Public boundary

Consumers import the stable shell API from `@kanbien/platform-server`.
`src/index.ts` is the deliberate public barrel. It exposes the server shell,
request/response contracts, safe transport configuration, and the Node
listener handle. It does not make implementation files a supported public
import path.

`src/main.ts` is an internal reusable process helper. The image build creates
an approved runtime shim for `@kanbien/platform-server/main`; ordinary apps
must not treat it as their composition root. The Kanbien staging target instead
uses `infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts`
to compose its product and selected Cognito adapter.

## Source map

| File | Owns | Does not own |
| --- | --- | --- |
| `src/index.ts` | Registry validation, route adaptation, request pipeline order, health responses, authentication/authorization gates, response ownership, and transport-to-platform coordination. | App business rules, provider SDK configuration, cloud topology, or durable rate-limit storage. |
| `src/transport.ts` | Node HTTP adaptation, bounded headers and bodies, allowed methods, request IDs, cancellation, listener timeouts, concurrency admission, and bounded connection draining. | App route semantics, identity-provider selection, trusting a proxy header, or product policy. |
| `src/main.ts` | Generic process startup/shutdown wiring and environment-neutral server options. | Selecting an app list, provider adapter, tenant policy, cloud account, or deployment target. |
| `tests/` | Type, runtime-listener, and dependency-boundary proof. | Production traffic or provider integration tests. |

The [source README](src/README.md) explains the three source files in more
detail.

## Request boundary in plain language

The real Node listener does more than call `shell.handle()`:

1. It accepts only supported methods and builds a safe request ID.
2. It applies pre-body admission, so a rate-limited request is rejected before
   JSON parsing or an app handler can consume capacity.
3. It bounds headers, request body bytes, headers/request/handler time, open
   requests, and requests per connection.
4. It parses only JSON bodies for methods that carry a body and maps malformed,
   too-large, or wrong-media-type input to safe error responses.
5. It passes a cancellation signal to the runtime context and drains existing
   requests during shutdown while refusing new work.

If a handler exceeds its deadline, the client receives a safe timeout response
and the cancellation signal is aborted. Crucially, that still-running handler
continues to occupy its concurrency slot until it settles, so ignoring
cancellation cannot turn the timeout into an unbounded parallel-work bypass.

The server preserves platform-owned headers such as CORS, content-security
policy, and `x-request-id`. An app may add ordinary response headers but cannot
silently weaken those shared protections.

## Rate limiting and client addresses

The in-memory limiter is intentionally a process-local baseline for tests and
private/local use. Its bucket count is bounded and bearer tokens are hashed
before becoming a key, but it is not a shared quota across replicas.

The generic Node listener uses only its real socket peer address. It never
trusts `X-Forwarded-For` or similar headers supplied by a caller. A public
multi-replica target must inject an approved shared rate-limit adapter and a
target-owned trusted-ingress client-address resolver before public exposure.
Those choices belong to an adapter, target profile, and infrastructure—not to
an app or this generic package.

## Verification

Run:

```text
npm run platform:server:check
```

The runtime suite starts a local listener and proves payload bounds, malformed
JSON handling, explicit preflight and method behavior, CORS variation,
request-ID ownership, early throttling, and the safe response path. The
boundary check prevents provider, app, or infrastructure imports from entering
the generic server package.
