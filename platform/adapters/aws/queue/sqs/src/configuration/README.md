# SQS configuration

A program sending work to a queue needs to know which queue to use and which
AWS region to contact. A program receiving work also needs two timings: how long
to wait for a message and how long a received message should be temporarily hidden.
This module declares and checks that information. It does not create queues,
contact AWS or decide what the work inside a message means.

## What each file does

| File | Job |
| --- | --- |
| [index.ts](index.ts) | Makes the names described below available; contains no implementation. The adapter's root index exposes them too. |
| [contract/types.ts](contract/types.ts) | Describes the checked sender/receiver information and the trusted checker function interface. |
| [contract/requirements.ts](contract/requirements.ts) | Declares required logical names, text checks and the two SQS timing limits. Does not name environment variables. |
| [contract/reporting/diagnostics.ts](contract/reporting/diagnostics.ts) | Defines the two content-failure reports, two source-read-failure reports and returned failure shape. |
| [contract/reporting/diagnostics.v1.json](contract/reporting/diagnostics.v1.json) | Generated copy of those four definitions. Other languages can read it without importing TypeScript. Never edit it independently. |
| [domain/validation.ts](domain/validation.ts) | Calls Core to check supplied logical values, assembles successful results, and reports observed failures. |
| [domain/assembly.ts](domain/assembly.ts) | Maps already-checked values into the sender/receiver option names. Does not read sources, independently validate raw input or construct clients. |
| [domain/reporting.ts](domain/reporting.ts) | Optionally delivers the owned report and selected source evidence with fixed startup context, without letting reporting failure replace the original result. |

Reporting keeps the SQS-specific definition checks, approved accompanying
evidence and startup context here. It delegates the actual delivery attempts to
Core's `deliverDiagnosticRecords`: a supplied receiver failing on one record
does not prevent attempts for later records. Core does not diagnose the SQS
failure, choose a logger or guarantee that a report was stored. See the
[Core delivery explanation](../../../../../../../packages/core/README.md#passing-a-diagnostic-to-its-receiver).

## One supplied value: the receive wait

The receiver requirement for `queue.receive-wait` uses `sqsReceiveWaitConstraint`:
whole-number text between 0 and 20 seconds. With supplied text `"20"`, Core
returns the number `20`. With `"21"`, it reports `out-of-range`. With a space,
it reports `blank`; it does not turn the space into zero on this new path.

This one requirement is part of the receiver's four-value check below. It is not
a requirement for a program that only sends messages.

## Several values: an illustrative receiver

Code outside this module can use the public adapter import:

```typescript
import { recordConfigSource } from "@kanbien/core";
import { validateSqsWorkerConfiguration } from "@kanbien/platform-adapter-aws-queue-sqs";

const supplied = {
  "queue.address": "https://sqs.example.invalid/example",
  "queue.region": "example-region",
  "queue.receive-wait": "20",
  "queue.visibility-timeout": "120",
};
const result = validateSqsWorkerConfiguration(recordConfigSource(supplied));
```

The address is invented. The caller supplies four named values; `recordConfigSource`
makes them readable by name. The validator selects `sqsWorkerRequirements` and
asks Core's `validateConfigRequirements` to check each one. Assembly renames the
successful logical fields to the names expected by the client constructors.
The exact result is:

```typescript
{
  ok: true,
  value: {
    queueUrl: "https://sqs.example.invalid/example",
    region: "example-region",
    waitTimeSeconds: 20,
    visibilityTimeoutSeconds: 120
  }
}
```

If the region is missing and the wait is `"21"`, both checks fail. The result is:

```json
{
  "ok": false,
  "error": {
    "code": "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID",
    "defaultMessage": "AWS SQS configuration is invalid.",
    "diagnosticRecord": {
      "schema": "core/diagnostic-record/v1",
      "code": "aws-sqs.worker-configuration-invalid",
      "definitionVersion": 1,
      "detail": {
        "issues": [
          { "setting": "queue.region", "reason": "missing" },
          { "setting": "queue.receive-wait", "reason": "out-of-range" }
        ]
      }
    }
  }
}
```

No supplied address or value is copied into that report. If reading a value
throws instead, the function does not call its contents missing or invalid.
It optionally reports the logical source and `unclassified-read-failure`, then
throws the original cause. Reading stops there; it invents no findings for
later values. The source report's `not-assessed` effect does not claim knowledge
of everything the reader itself may have done.

## How programs use it

```text
TARGET / COMPOSITION                   REUSABLE CODE
chooses actual source names
and supplies readers/bindings -------> Platform config loading
                                      + SQS requirements
                                      + Core checks
                                      + SQS assembly
                                             |
                                      checked configuration
                                             |
                                      existing SQS constructor

Already-logical source -------------> SQS guarded FromConfiguration factory
                                      -> same Core checks / SQS assembly
                                      -> existing SQS constructor, only on success
```

Platform's `loadPlatformConfiguration` accepts the public requirements and
assembly callback with target-owned bindings. Future programs can use different
source names without copying the rules. The local composition test proves two
binding sets; this slice does not migrate a production target.

The new factories in [queue.ts](../queue.ts) and [worker.ts](../worker.ts) are
`createAwsSdkPlatformSqsQueueFromConfiguration` and
`createAwsSdkPlatformSqsWorkerQueueFromConfiguration`. They accept a logical
`ConfigSource`, optional diagnostics and an optional trusted checker. All required
inputs are checked before AWS client construction. A caller must handle the
failed result rather than fall back to unchecked values. Success establishes
configuration checks, not queue existence, permissions or network connectivity.

## Public names

- `sqsSenderRequirements` declares `queue.address` and `queue.region`.
  `sqsWorkerRequirements` adds `queue.receive-wait` and `queue.visibility-timeout`.
  Every input is required; neither path silently supplies a timing default.
- `sqsReceiveWaitConstraint` is the immutable 0–20-second integer rule;
  `sqsVisibilityTimeoutConstraint` is the immutable 0–43,200-second rule.
  Legacy numeric guards also read these bounds, without changing their parsing.
- `SqsSenderConfiguration` contains checked address/region; `SqsWorkerConfiguration`
  adds the checked numeric timings. These are types, not functions that check data.
- `validateSqsSenderConfiguration` and `validateSqsWorkerConfiguration` accept
  logical sources and return the successful/failed shapes illustrated above.
  Sender validation never reads receiver-only fields. Text must be nonblank and
  have no surrounding whitespace; numeric inputs must be whole-number text.
  These checks do not validate a complete URL or contact the named region.
- `SqsConfigurationCheck` describes optional **trusted composition code**, not
  a callback supplied by an untrusted user to approve their own configuration.
  Its default is Core's checker. It can connect the existing Platform loader;
  successful checked values, not original source values, are consumed.
- `assembleSqsSenderConfiguration` and `assembleSqsWorkerConfiguration` are
  assembly callbacks for an already-validated map, such as the one supplied by
  Platform loading. Calling assembly with raw input does not establish validation.
- `SqsConfigurationFailure` describes the new failed result. Historical error
  objects from the old environment factory are deliberately unchanged.
- `sqsSenderConfigurationDiagnostic` and `sqsWorkerConfigurationDiagnostic` define
  content reports; `sqsSenderConfigurationSourceDiagnostic` and
  `sqsWorkerConfigurationSourceDiagnostic` define observed read-failure reports.
  `sqsConfigurationDiagnosticCatalog` selects exactly those four definitions.
  JSON is public at
  `@kanbien/platform-adapter-aws-queue-sqs/configuration/diagnostics.v1.json`.

## Compatibility and proof limits

Existing direct constructors and `createAwsSdkPlatformSqsWorkerQueueFromEnv` keep
their earlier behavior. For example, the environment factory accepts a space as
numeric zero, while direct text guards differ from the environment text reader.
The environment factory still reads all four inputs and returns its first failed
result. Its fixed `PLATFORM_WORKER_SQS_*` bindings are compatibility behavior,
not the template for new service requirements. Its existing retiring-target
callers were not migrated. Removing that API needs their retirement or an
approved caller migration; no sibling forwarding file was added.

The [configuration runtime tests](../../tests/sqs-configuration-runtime.test.ts)
prove strict inputs, actual sender/receiver commands using checked values,
rejection before construction, source identity/read order, selected evidence,
reporter isolation and Platform composition. The
[existing runtime tests](../../tests/sqs-adapter-runtime.test.ts) retain message
operations, native observations and getter behavior. The
[type tests](../../tests/sqs-configuration-types.test.ts) prove supported shapes.
Catalogue fixtures prove public JSON resolution, freshness and explicit Python
reading. Narrow deployment readers do not automatically accept these new codes.

The harness's [configuration standard](../../../../../../../.agentic/03.product/standards/config-runtime-settings.md)
owns requirements for future work. Structure checks enforce index/dependency
boundaries, not universal diagnostic completeness; review and behavioral tests
establish the observed meanings. No new dependency installation, AWS operation,
queue provisioning, retry/DLQ policy or deployment is part of this slice.
