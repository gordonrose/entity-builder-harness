# Platform Contracts Source Map

This directory implements the app-facing `@kanbien/platform-contracts` package.
Apps and other packages use the package root import; they do not import these
files by path. See the [package README](../README.md) for the public boundary,
dependency rules, and verification command.

`index.ts` deliberately re-exports the supported contracts from the topic
files below. It is the public front door, not a place to add unrelated contract
implementation.

| File | Owns | Why it remains separate |
| --- | --- | --- |
| `errors.ts` | Stable error codes and constructors. | Declaration and validation failures need one consistent vocabulary. |
| `identifiers.ts` | Branded app, route, job, health, and API-version names. | Name construction is a foundational check shared by later declarations. |
| `flags.ts` | Feature-flag name, context, reader, and fixed reader. | Flag evaluation is a context concern, not an app-mount or route concern. |
| `contexts.ts` | Runtime, request, and job context shapes. | Apps receive shared runtime facts without being given platform internals. |
| `routes.ts` | HTTP route declarations and their auth, tenant, and resource-policy inputs. | It describes what a route may request; it does not execute a route. |
| `jobs.ts` | Background-job declarations. | Jobs have a queue-shaped contract distinct from HTTP routes. |
| `app.ts` | App mount, registry, permission, health, lifecycle, and dependency declarations. | It is the one app-to-platform integration socket. |
| `validation.ts` | Cross-declaration checks and reserved-route rules. | It reads declarations after they are defined, avoiding declaration-to-validator cycles. |
| `index.ts` | Deliberate public exports only. | Callers remain insulated from internal source reorganisation. |

The dependency order is foundational errors and identifiers; then flags,
contexts, and declarations; then validation; then the barrel. Topic files may
import local relatives or public `@kanbien/core` exports only.

## Detailed guide to the files

The filenames answer a maintainer's first question: “Where should I look?”
They do not create nine public mini-packages. Code outside this directory still
imports from `@kanbien/platform-contracts`; the examples use that public
boundary deliberately.

### `errors.ts` — a shared language for invalid declarations

This file defines the stable error codes and the small constructors that make
them. A registry, a validator, or a test can therefore distinguish “this name
is malformed” from “this route used a reserved path” without trying to parse a
human-readable sentence.

`PLATFORM_CONTRACT_NAMESPACE_MISMATCH` is the specific error used when the
runtime is mounting one app but the app tries to register a permission, route,
job, or health name belonging to another app. It records the registration kind,
the mounting app ID, and the attempted name. That gives startup and test
failures a safe, precise explanation without turning a naming mistake into a
provider or HTTP concern.

It owns the **shape of a contract failure**, not HTTP error responses, logging,
retries, or provider error handling. Those are future runtime concerns. Its
error details are concise facts that explain the declaration problem; they are
not a place to put a request body, token, or customer data.

```ts
const error = duplicatePlatformRegistration("route", "billing.invoice.list"); // Create the standard duplicate-registration error for a route name.
const code = error.code; // Read the stable machine-readable code, rather than matching a message string.
void code; // Mark the illustrative value as intentionally used in this small example.
```

### `identifiers.ts` — checked names with a distinct TypeScript identity

This file makes app, route, job, health-check, and API-version names. It checks
the common dot-separated lowercase syntax and returns a `Result` instead of
silently accepting bad input. On success, the string receives a *brand*: a
TypeScript-only label that stops an ordinary string accidentally being passed
where a checked route name is required.

The brand does not add characters at runtime and does not authorize anything.
For example, `billing.invoice.list` says who owns a capability and what it is;
it does not say whether Bill may use it. Authorization is decided later from
the principal, tenant, permission, and resource facts.

```ts
const attemptedName = platformRouteName("billing.invoice.list"); // Ask the constructor to validate and brand a route name.
if (attemptedName.ok) { // Continue only when the name has the required syntax.
  const checkedRouteName = attemptedName.value; // Take the branded route name for a route declaration.
  void checkedRouteName; // Mark the illustrative checked value as used.
} // Leave the success-only branch; the failure case carries a PlatformContractError.
```

### `flags.ts` — a provider-neutral question about a feature

This file defines the small question an app is allowed to ask: “Is this named
flag enabled for this optional tenant, principal, correlation, and fact
context?” `FeatureFlagReader` deliberately does not reveal a vendor SDK or a
database. That lets a later runtime select a flag provider without apps being
rewritten around that provider.

`fixedFeatureFlagReader` is a deterministic implementation for tests and local
proof. It takes a snapshot, so changing the original object later does not
quietly change the reader's answer. It is not a production feature-flag
service or a policy engine.

```ts
const attemptedFlag = featureFlagName("billing.invoice.bulk-export"); // Validate and brand the stable flag name.
if (attemptedFlag.ok) { // Continue only when the flag name is valid.
  const reader = fixedFeatureFlagReader({ [attemptedFlag.value]: true }); // Create a deterministic test reader with this flag enabled.
  const enabled = reader.isEnabled(attemptedFlag.value); // Ask the provider-neutral reader for the flag state.
  void enabled; // Mark the synchronous-or-asynchronous illustrative result as used.
} // Leave the success-only branch.
```

### `contexts.ts` — the safe bundle of runtime facts an app receives

This file describes `PlatformRuntimeContext`, then adds request-specific and
job-specific facts to form `PlatformRequestContext` and `PlatformJobContext`.
The platform creates these contexts; route and job handlers consume them.
They carry facts such as correlation ID, tenant, principal, locale, logger,
metrics, config, feature flags, clock, queue message, and cancellation.

The context is intentionally **not** a service locator. It does not hand an
app every repository, billing service, provider client, or database connection.
An app constructs and owns its own business dependencies; the context supplies
the facts that genuinely come from running inside the platform.

```ts
function tenantForThisRequest(context: PlatformRequestContext): string | undefined { // Accept the request facts supplied by the platform.
  return context.tenant?.tenantId; // Read the resolved tenant when this route declared that it needs one.
} // Return only a shared runtime fact, not a product service.
```

### `routes.ts` — what an HTTP route may declare

This file is a declaration vocabulary. A route supplies a checked name, HTTP
method, relative path, optional API version, auth requirement, optional tenant
requirement, optional resource-authorization contribution, input validator,
and handler. The declaration tells the eventual server what the app needs; it
does not start a web server, parse a token, or itself decide database-backed
business authorization.

There are two related authorization layers here. `auth` describes coarse
access—public or authenticated with app-declared permissions. A
`resourceAuthorization` contribution supplies the resource and policy facts
needed for the later fine-grained authorization decision. For example,
`billing.invoice:read` says the action; the app's policy decides whether Bill
may read this particular Benelux invoice.

```ts
const route: PlatformRouteRegistration = { // Declare one route for later platform mounting.
  name: checkedRouteName, // Use a previously constructed and branded route name.
  method: "GET", // State the permitted HTTP method as part of the declaration.
  path: "/invoices/:invoiceId", // State the app-relative path, not a full provider URL.
  auth: { kind: "authenticated", permissions: ["billing.invoice:read"] }, // Require an authenticated principal with the app-declared coarse permission.
  tenant: "required", // Require the platform to resolve a verified tenant before the handler runs.
  handler: { handle: () => ({ status: 200 }) }, // Supply the app-owned handler without giving it control of the HTTP server.
}; // Finish the declarative route description.
void route; // Mark the illustrative declaration as used.
```

### `jobs.ts` — what a background job may declare

This file mirrors the route idea for background work. A job has a checked job
name, a queue message type, an optional payload validator, and a handler that
receives the message together with `PlatformJobContext`. This lets the future
worker own polling, retries, dead-letter handling, metrics, and shutdown while
the app owns the business work.

It does not promise exactly-once execution. A real job with an external effect
still needs an idempotency design: key, scope, durable claim, concurrent-worker
behaviour, expiry, reconciliation, and its atomic boundary with the effect.

```ts
const job: PlatformJobRegistration = { // Declare a background job for later worker mounting.
  name: checkedJobName, // Use a previously constructed and branded job name.
  messageType: "billing.invoice.export-requested" as QueueMessageType, // State which queue-message shape this handler accepts.
  handler: { handle: () => undefined }, // Supply only the app-owned work; platform owns delivery mechanics.
}; // Finish the declarative job description.
void job; // Mark the illustrative declaration as used.
```

### `app.ts` — the app-to-platform integration socket

This file defines what an app can contribute during mounting: permissions,
routes, jobs, health checks, config schemas, lifecycle hooks, and its declared
dependencies. `PlatformAppRegistry` is intentionally narrow. It lets an app
register intent, not call `listen`, install global middleware, configure CORS,
or access a raw server or worker loop.

`PlatformMountDeps` supplies provider-neutral runtime mechanisms, such as a
logger, metrics, config, flags, clock, optional event and audit ports, and
optional authentication or authorization ports. It does not move tenant groups,
roles, or product policy into the platform; applications retain that meaning.

During a real runtime or test mount, the registry is also scoped by the
platform to the app's already-validated ID. For example, the app with ID
`billing` may register `billing.invoice.list` and `billing.invoice:read`, but
not `customer-service.case.list`. The app cannot select or override that scope:
the runtime supplies it before calling `mount`. This keeps semantic ownership
enforcement at the composition boundary while leaving this app-facing contract
small and provider-neutral.

```ts
const app = definePlatformApp({ // State that this object is an app contribution that satisfies the public contract.
  id: checkedAppId, // Give the mounted app a checked stable identity.
  name: "Billing", // Provide the human-readable app name for operators and registries.
  mount(registry) { // Receive the narrow registry instead of a raw HTTP server.
    registry.registerPermission({ permission: "billing.invoice:read" }); // Declare the app-owned permission that its routes may reference.
  }, // Finish the mount contribution without starting a process or selecting a provider.
}); // Finish the app declaration.
void app; // Mark the illustrative app declaration as used.
```

### `validation.ts` — the inspector that checks declarations together

This file validates a permission declaration, a route registration, or a job
registration. It checks local shape—such as HTTP method, route path, auth
combination, message type, handler, and validator—and can also check a route
against the complete list of permissions that an app declared. It owns the
reserved platform paths such as `/livez` and `/readyz` because those are rules
about whether a registration is acceptable.

The important boundary is that it **consumes** declarations. `routes.ts`,
`jobs.ts`, and `app.ts` do not import a registry-wide validator into every
declaration. A declaration can describe itself; only the inspector can compare
it with what else is registered.

```ts
const outcome = validatePlatformRouteRegistration(route, { declaredPermissions: ["billing.invoice:read"] }); // Validate the route against its declared permission vocabulary.
if (!outcome.ok) { // Handle the explicit failure result instead of letting an invalid route mount silently.
  console.log(outcome.error.code); // Inspect the stable contract error code for a test, registry, or safe startup report.
} // Leave the failure-only branch; a successful result contains no error.
```

### `index.ts` — the one stable public doorway

This file is a *barrel*: a deliberate list of exports from the topic files. It
is small on purpose. A caller sees one stable package import while maintainers
can keep the implementation grouped by responsibility. The barrel re-exports
the supported app-facing types, constructors, and validators; it does not
export private helpers merely because another topic file uses them.

The practical rule is simple: if an app needs a supported contract, add it to
the explicit barrel after deciding that it is genuinely app-facing. If a helper
only helps one topic file implement itself, leave it local. That distinction is
what stops accidental implementation details becoming permanent API promises.

```ts
import { platformRouteName, validatePlatformRouteRegistration } from "@kanbien/platform-contracts"; // Use the package root rather than a source-file path.
const attemptedRouteName = platformRouteName("billing.invoice.list"); // Consume an approved public constructor through the barrel.
void validatePlatformRouteRegistration; // Show that validators are also deliberately exported through the same doorway.
void attemptedRouteName; // Mark the illustrative constructor result as used.
```
