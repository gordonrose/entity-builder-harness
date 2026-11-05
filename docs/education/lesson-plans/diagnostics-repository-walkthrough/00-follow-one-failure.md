<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.lesson-zero
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-02"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach one real configuration failure from predicate to safe reader.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# Lesson zero — where did the useful information go?

[Course start](README.md)

## 1. The question that started the work

You pointed at this combined guard:

```javascript
if (
  host === undefined ||
  database === undefined ||
  schema === undefined ||
  reference === undefined ||
  port === undefined ||
  !/^\d+$/.test(port)
) {
  return undefined;
}
```

The code can decide that this configuration is unusable. But its caller receives the same undefined whether host is missing, schema is missing or the port fails the digit check. The useful distinctions disappear at the return boundary. Nothing about that loss was necessary to keep the values private.

**Pause:** if only port is absent, can the caller tell which setting needs attention? No. Can we say the database rejected a connection? Also no: that call has not been observed.

This quotation is the original incident from our conversation. The exact Git baseline for the whole course is separately recorded; do not assume every historical snippet describes every file at that baseline.

## 2. Separate the requirement from the secret value

Open [the target configuration binding](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts) and find persistenceConfigurationBindings and persistenceConfigurationResult.

The logical setting database.port maps to the deployment source PERSISTENCE_POSTGRES_PORT. The source name is part of wiring; the actual supplied value is private. The target declares an integer rule with the allowed port range. Other settings use the PostgreSQL adapter's shared text rules.

A **predicate** is simply a yes/no check, such as “was a required setting supplied?” The diagnostic should describe the result of the check actually reached, not an attractive explanation guessed afterward.

**Pause:** which should travel to an agent: the actual port value, or the logical setting and the reason it failed? The latter is enough for this failure.

## 3. Let the reusable reader make the observation

Open [Core setting validation](../../../../packages/core/src/config/domain/validation/settings.ts) and [its issue collector](../../../../packages/core/src/config/contract/reporting/setting-issues.ts). Follow validateConfigSettings with a synthetic source where the other requirements are valid and database.port is absent.

The reader collects a logical setting issue. It does not need to include host, username, password, database contents or rejected source text. It preserves observed issue ordering and its bound. A source read throwing is a different event from a read succeeding with a missing value.

This is not just a better sentence. The code evaluates a condition and constructs data whose reason follows that condition. To check accuracy, inspect the branch and its positive/negative assertions together.

**Pause:** if a getter throws before giving the reader a value, may the diagnostic say the value was the wrong type? No: the type was not obtained.

## 4. Construct only the detail the selected definition allows

The target uses defineConfigurationDiagnostic from [Platform configuration diagnostics](../../../../platform/config/src/diagnostics.ts). The target supplies the closed setting list; Core supplies the common record mechanism.

For this one synthetic missing-port case, the record shape is:

```json
{
  "schema": "core/diagnostic-record/v1",
  "code": "kanbien-core-server.configuration-invalid",
  "definitionVersion": 1,
  "detail": {
    "issues": [
      { "setting": "database.port", "reason": "missing" }
    ]
  }
}
```

This is an illustration of the selected contract, not a captured deployment log. Adding an arbitrary property such as submittedValue is not allowed by that definition.

Open [definition validation](../../../../packages/core/src/diagnostics/definition.ts) and [record creation/parsing](../../../../packages/core/src/diagnostics/record.ts). Notice that a definition has classification as well as detail rules, while the serialized observation refers to that definition using code and version.

**Pause:** why keep the version? Because changing what an old code/version means can mislead an older reader. New semantics require compatible addition or a new version, not a silent edit to history.

## 5. Keep the evidence when a caller wraps the failure

Find persistenceConfigurationFailure and persistenceTaskDiagnosticFields in the target binding. Then follow the actual caller in the server, migration or administration program. The outer result may keep a historically stable task/error code while carrying a checked diagnostic alongside it. Different programs use selected envelopes; they do not all emit one universal JSON object.

| Context | Field/concept | Why it differs |
| --- | --- | --- |
| Library error evidence | diagnosticRecord / relatedDiagnosticRecords | An optional safe companion to the original result/error |
| This configuration result | error.diagnostic | The target's structured configuration result |
| Selected task serialization | diagnostic / related_diagnostics | A checked operational envelope consumed by tooling |
| Internal logger | platform.diagnostic.observed with diagnostic in fields | Delivery through the selected internal logger |

The exact consumer must understand its envelope. A new inner schema is not useful if an existing wrapper discards it. Primary failure, local boundary evidence and selected source companions may each matter; replacing all of them with one generic record would lose information again.

**Pause:** does adding a diagnostic mean the operation should be retried to get a better log? No. Reporting must not replay the work.

## 6. Select the language and deliver safely

Open [the catalog/reporter contracts](../../../../platform/contracts/src/diagnostics.ts) and [the reporter implementation](../../../../platform/observability/src/diagnostics.ts). A **catalog** is the set of definitions this caller explicitly accepts. The reporter validates records against that selection and checks context.

An error object is untrusted input. Reading an arbitrary getter can itself run code; traversing its cause or copying every field can expose secrets. The selector reads approved own-data fields and validates them rather than treating arbitrary error prose as diagnostic truth.

Reporting can be unavailable, disabled or bounded. A failed reporter must not convert a completed request into a business failure. A successful local write does not prove a collector or backend retained the event.

**Pause:** why can a schema-valid record still be false? Because matching a shape does not prove the claimed condition was observed. Source ownership and producer behavior still need review and tests.

## 7. Read the same contract from Python

Open [the generated target configuration export](../../../../infra/04.deploy/03.product/entrypoints/contracts/diagnostics.v1.json), [the strict Python reader](../../../../scripts/repo/diagnostic-coverage/runtime_contract.py) and [the operational reader](../../../../scripts/04.deploy/shared/deployment-operation-diagnostics.py).

The generated JSON is a projection of code-owned definitions. Python validates against it rather than maintaining its own list of settings/reasons. A malformed, unavailable or incomplete observation must remain so; it must not become accepted deployment evidence.

The agent can now identify the rejected requirement and an appropriate next investigation without learning the missing value. It still cannot infer who removed the setting or whether a live deployment was attempted. Those would need separate evidence.

## 8. What proves that the chain works?

Read the exact assertions in [the target configuration tests](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs), the Core/Platform tests in the matching folder lessons and the strict reader tests. Distinguish these questions:

1. Does the actual guard choose the right reason and setting?
2. Does valid input still preserve the old successful behavior?
3. Does a source failure stay distinct from a missing value?
4. Do wrappers and readers retain the checked observation?
5. Are injected throws, malformed records and sensitive canaries excluded safely?
6. Does the compiled/image payload contain every imported diagnostic module?

A good negative test is sensitive: deliberately remove or mislabel the observation in a disposable test case and the assertion should fail for the intended reason. An assertion that merely sees “some error” would repeat the original problem.

## Explain it back

Without reopening the source, complete this sentence:

> The target owns ___; Core owns ___; the adapter contributes ___; the reporter/reader checks ___; none of this proves ___.

**Answer direction:** concrete setting bindings; reusable validation/record meaning; supported PostgreSQL-specific rules/native evidence; selected schema and safe envelope; live deployment success or remote delivery.

Then continue with [L004: packages/core/src/diagnostics](lessons/004-core-src-diagnostics.md) and [L007: packages/core/src/config](lessons/007-core-src-config.md). We stop after each question until you are comfortable.
