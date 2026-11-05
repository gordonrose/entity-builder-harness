# Worker retry instructions

A worker runs a background job, such as delivering a queued message. If that
job fails, the worker needs two instructions: how many attempts to allow, and
how long to request before trying again. This module checks those instructions.
It does not run the job, choose a queue provider, or make a queue wait.

The worker calls the startup check before selecting its queue. An omitted
`maxAttempts` means three attempts in total, including the first. A supplied
value must be a finite positive whole number; text such as `"3"` is not converted.
An omitted delay function means `attempt * 1000` milliseconds. A supplied
function is checked for callability at startup, but is not called then: its
answer can only be checked when a retry is actually needed.

## What each file does

| File | Responsibility |
| --- | --- |
| [index.ts](index.ts) | Exposes this module's public names. No checking or execution happens here. |
| [contract/requirements.ts](contract/requirements.ts) | Names the default attempt limit, permitted failure reasons and input/output shapes. |
| [contract/reporting/diagnostics.ts](contract/reporting/diagnostics.ts) | Defines the two diagnostic records and constructs records with fixed fields and allowed reasons. It does not inspect configuration. |
| [contract/reporting/errors.ts](contract/reporting/errors.ts) | Attaches the safe retry-delay record to the TypeError thrown when a calculator returns an unusable answer. |
| [contract/reporting/diagnostics.v1.json](contract/reporting/diagnostics.v1.json) | Generated definitions for tools that read diagnostics without running TypeScript. Do not edit by hand. |
| [domain/validation/startup.ts](domain/validation/startup.ts) | Reads the two instructions once, checks them, applies omitted defaults, and returns checked values or a safe report. |
| [domain/validation/retry-delay.ts](domain/validation/retry-delay.ts) | Provides the default calculation and checks an actual returned delay. |

## Worked example

Suppose a caller supplies `{ maxAttempts: 2, retryBackoffMs: () => 0.5 }`.

1. `validateWorkerRetryConfiguration` reads both properties once. Core config
   verifies that `2` really is a finite number; Core queues checks that it is a
   positive whole attempt count. The function is retained, not called.
2. The result is `{ ok: true, value: { maxAttempts: 2, retryBackoffMs: … } }`.
   `worker.ts` uses this checked copy, even if the caller changes its object later.
3. If the first job attempt fails, existing durable-processing settlement runs
   first. The selected calculator is then called once with attempt `1`.
4. `validateWorkerRetryDelay(0.5)` returns `{ ok: true, value: 0.5 }`.
   The worker passes that checked value to `queue.retry`.
5. If the second attempt fails, the worker follows its existing final-failure
   path. It does not call the delay calculator for a retry it will not request.

If the attempt limit is `0`, construction instead returns `ok: false` with
`PLATFORM_WORKER_CONFIG_INVALID` and a diagnostic naming `max-attempts` and
`not-positive`. No queue is selected. If a calculator returns `-1`, startup
can still have succeeded: the later retry throws a controlled TypeError with
`platform-worker.retry-delay-invalid`, reason `negative`, and effect
`retry-not-submitted`. No supplied value appears in either diagnostic.

```text
Caller supplies retry instructions
              |
              v
worker.ts -> startup.ts -> Core config number check + Core queues attempt check
              |
       checked limit and function
              |
       job fails and retry is allowed
              |
       settle existing durable claim -> call calculator once
              |
       retry-delay.ts checks answer
          /                    \
     valid delay          invalid answer
          |                    |
     queue.retry       reporting/errors.ts -> controlled exception + diagnostic
```

## Public names and when to use them

Import these through `@kanbien/platform-workers`, not internal file paths.

- `validateWorkerRetryConfiguration(input)` is the startup check used by
  `createPlatformWorkerShell`. Other worker construction paths should consume
  its returned values rather than copying its rules.
- `WorkerRetryConfigurationInput` describes the optional number and function.
  `CheckedWorkerRetryConfiguration` describes the required, read-only returned
  values. Type declarations help programmers; the functions perform real checks.
- `workerDefaultMaxAttempts` is `3`; `defaultWorkerRetryDelay(attempt)` computes
  the existing default. Neither schedules work.
- `validateWorkerRetryDelay(value)` checks the actual answer, accepting zero and
  fractional milliseconds but rejecting missing, nonnumeric, nonfinite or
  negative answers. Its successful result contains the value to use.
- `workerRetryConfigurationReasons` and `workerRetryDelayReasons`, with their
  corresponding `…Reason` types, name the permitted explanations. The checker
  must establish the explanation; choosing a name is not a check.
- `WorkerRetryConfigurationIssue` pairs a logical setting with its reason.
- `workerRetryConfigurationDiagnostic` and `workerRetryDelayDiagnostic` define
  record codes and fields. The corresponding `…Record` functions construct safe
  records, and `workerRetryConfigurationDiagnosticCatalog` groups their definitions.
- `workerRetryDelayError(reason)` creates the controlled exception carrying that
  record. Existing exceptions thrown by a calculator are not replaced with it.

Tools can import the generated JSON as
`@kanbien/platform-workers/configuration/diagnostics.v1.json`; the existing
combined package catalogue still includes these definitions. The worker reports
startup rejection through its optional reporter. Later delay diagnostics respect
the job's operational-log choice; reporter failure cannot replace the exception.

## Boundaries, governance and proof

Lease duration is owned by [Platform persistence leasing](../../../persistence/src/leasing/README.md),
not redefined here. The worker uses that check for durable processing. Caller
property getters are allowed to throw; those exceptions retain their identity.
Checking a function at startup cannot prove that its later invocation succeeds.

The [configuration standard](../../../../.agentic/03.product/standards/config-runtime-settings.md#worker-retry-and-persistence-leases)
governs ownership, checked-value use and future changes. Runtime definitions
remain the source of accepted values; this README explains them.
`tests/retry-configuration-runtime.test.ts` and its type companion cover actual
worker use, defaults, snapshotting, failure timing, safe output and faulty
reporters. Existing startup and delivery tests preserve surrounding behaviour.

The in-memory worker queue currently stores the requested delay but does not
wait for it in `next()`. Scheduling enforcement is recorded separately in N05
of the configuration implementation plan. These checks prove valid instructions
and retry submission, not elapsed-time scheduling or a live provider.
