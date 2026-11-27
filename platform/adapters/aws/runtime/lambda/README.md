# AWS Lambda runtime bridge

A timer can wake a Lambda function once a minute, but the function must finish
before AWS stops it. This package connects that limited invocation to the
existing scheduler. It does not create timers, store reminders or execute jobs.

## Files and public names

- [src/index.ts](src/index.ts) only exposes the public names below.
- [src/deadline.ts](src/deadline.ts) implements
  `createPlatformLambdaContinuation`. It accepts a `PlatformLambdaContext`
  (the AWS object that can report remaining milliseconds) and a positive whole
  number of milliseconds to keep in reserve. It returns a function that answers
  “is there still time to start another operation?”
- [src/dispatch.ts](src/dispatch.ts) implements
  `createPlatformLambdaDispatcherHandler`. Its `PlatformLambdaDispatcherOptions`
  supplies the existing dispatcher and two reserves: one for all work, another
  for stopping due-reminder selection earlier so old waiting messages still get
  time to reach the queue.
- [src/diagnostics.ts](src/diagnostics.ts) owns
  `lambdaInvocationBudgetDiagnostic`, `lambdaDispatchOutcomeDiagnostic` and
  their selected `lambdaRuntimeDiagnosticCatalog`. These describe invalid time
  information and a returned failed queue handoff, without recording supplied
  events, provider addresses or raw errors.
- [package.json](package.json) declares the public package and dependencies.
  The three `tsconfig` files select declaration, checking and runtime-test
  builds. [tests/](tests/) contains the focused behavior proof; its runner uses
  the repository's existing workspace payload assembler.

## A small example

This illustrative caller uses the public package; it is not an extra deployed
entrypoint:

```ts
import { createPlatformLambdaContinuation } from "@kanbien/platform-adapter-aws-runtime-lambda";

const next = createPlatformLambdaContinuation(
  { getRemainingTimeInMillis: () => 10_000 },
  2_000,
);
next(); // true: 10,000 milliseconds remain, more than the 2,000 reserve
```

At exactly 2,000 milliseconds it returns `false`. A negative or non-finite
remaining time throws an error carrying a bounded diagnostic. A thrown provider
clock read remains the original thrown value; it is not permission to continue.

For dispatch, the flow is:

```text
fixed timer invocation
  → Lambda time checks
  → existing due-reminder handover
  → existing waiting-message relay
  → bounded invocation result
```

The handler ignores event contents: they cannot choose another job or scope.
It passes both time checks into the dispatcher. An ordinary stop, contention
or exhausted count returns the established result; `queue-send-failed` and
`publish-marker-failed` throw instead of pretending the handoff succeeded.
Returned persistence errors and thrown dependencies preserve their identity.
No operation is replayed merely to improve its error report.

These checks happen **between** operations. They cannot interrupt a database
query or queue call already running; composition must supply shorter connection,
query and SDK timeouts. A successful invocation also does not prove a queued
job has completed. Durable worker processing owns that separate result.

## Proof and remaining boundary

`npm run platform:adapter:aws:runtime:lambda:test` exercises the adapter with
controlled dependencies, including separate due/relay budgets and failed
handoffs. It is not an AWS invocation or finished-image qualification.

The [scheduler plan](../../../../../.agentic/03.product/plans/implementation/reusable-aws-scheduling.md)
tracks composition, packaging and live proof. The
[runnable-program standard](../../../../../.agentic/04.deploy/20-build/standards/require-runnable-program-contract.md)
owns managed-handler declarations; the README does not grant deployment
permission or replace those checks.
