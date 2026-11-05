# Configuration

Before core-server can connect to its database, it needs to know where the
database is running and which numbered connection point to use. That number is
called a **port**.

These details are examples of **configuration**: information supplied to a
program to tell it how to run, without changing its code. Each individual item
is called a **setting**. The database port is one setting; the database name is
another.

This folder contains shared functions for reading that information, checking
whether it meets the program's requirements, and describing any problems found.
For example, a program might require a database port but receive no port number.

The code using these functions specifies where to read the information and which
rules to check. It can select a shared rule supplied by this module, such as the
permitted destination-port range, rather than repeat that rule itself. The
functions do not choose the database, connect to it or write the resulting
problem reports to a log.

For example, a database port might be missing. The checking code can report:

```typescript
{ setting: "database.port", reason: "missing" }
```

Here, `setting` names the item being checked and `reason` describes its problem:
the database port was not supplied. The report does not include an actual port
number or other supplied information.
The same reporting approach can be used outside databases.

## What each file does

The database example involves two different jobs:

- Describe the instruction and the answer: for example, a port must be a whole
  number, and a failure names the port and its problem. Files in `contract/`
  own those descriptions. A **contract** is the agreed shape or meaning that
  the checking code and its callers both rely on.
- Perform the work: read the supplied port, check it and return the answer.
  Files in `domain/` own those operations. Here, **domain** means this module's
  own work—not database connections or application-specific decisions.

`index.ts` makes selected names from both groups available to other code.
Callers still import from `@kanbien/core/config`, not the private folder paths.
The walkthroughs below follow this actual layout:

```text
config/
  index.ts                 What other code can import
  README.md                This guide
  contract/                Descriptions, requirements and permitted reports
    types.ts
    constraints.ts
    reporting/             What a problem report may contain
      setting-issues.ts
      sourcing-issues.ts
      errors.ts
      diagnostics.ts
      diagnostics.v1.json  Generated config-only catalogue
  domain/                  Operations
    reading/               Obtain individual supplied items
      source.ts
      value-readers.ts
    validation/            Apply checking instructions
      settings.ts
      json-object.ts
    reporting/             Collect findings and construct packets, not logs
      issue-collection.ts
      diagnostic-reporting.ts
```

| File | What it does |
| --- | --- |
| [index.ts](index.ts) | Exposes selected public functions and types; contains no implementation. |
| [contract/types.ts](contract/types.ts) | Describes supplied values, sources and instructions telling a checker what to check. |
| [contract/constraints.ts](contract/constraints.ts) | Defines named, reusable requirements for acceptable configuration values. Other code selects a rule when checking values; the destination-port rule is its first example. |
| [contract/reporting/setting-issues.ts](contract/reporting/setting-issues.ts) | Describes individual problems with supplied values or comparisons, supplies shared reason names, and retains two fixed lists for older code. |
| [contract/reporting/sourcing-issues.ts](contract/reporting/sourcing-issues.ts) | Names observations about failures obtaining information. It does not read files or infer causes. |
| [contract/reporting/errors.ts](contract/reporting/errors.ts) | Describes returned operation failures and constructs existing reader errors. An individual problem explains why work failed; this file does not discover it. |
| [contract/reporting/diagnostics.ts](contract/reporting/diagnostics.ts) | Defines four versioned reports and checked constructors. It does not establish their truth or log them. |
| [contract/reporting/diagnostics.v1.json](contract/reporting/diagnostics.v1.json) | A generated, config-only copy of the diagnostic definitions for tools that read JSON. It does not contain supplied values or run checks. |
| [domain/reading/source.ts](domain/reading/source.ts) | Copies supplied information and reads named items; preserves a thrown read and attaches the existing safe observation where possible. |
| [domain/reading/value-readers.ts](domain/reading/value-readers.ts) | Reads and checks individual values, environment names and secret references. |
| [domain/validation/settings.ts](domain/validation/settings.ts) | Applies caller-selected text/integer requirements and comparisons, returning checked values or established problems. |
| [domain/validation/json-object.ts](domain/validation/json-object.ts) | Parses supplied JSON text as an object. It does not fetch the text or validate credential policy. |
| [domain/reporting/diagnostic-reporting.ts](domain/reporting/diagnostic-reporting.ts) | Builds approved field, relationship and source-read diagnostic packets from established findings; does not perform checks or log. |
| [domain/reporting/issue-collection.ts](domain/reporting/issue-collection.ts) | Copies reports already discovered by another checker, preserving the 32-report limit and overflow flag. |

The subfolders group files by the work they belong to. For example,
`contract/reporting/` describes a permitted report, while `domain/reporting/`
constructs one from findings already established. Neither writes logs.
The reading functions can read and check one item together; there is no need
to split that cohesive operation just to give each step another file.

For the database port, the caller selects Core's shared destination-port rule
and supplies its own source name. The settings capability performs the check;
the setting-issues contract describes
its problem reports. For a failed certificate-file read, the reading code
establishes an observation and selects a sourcing-issues reason. A failed read
does not establish invalid contents.

Individual readers return `CONFIG_MISSING` or `CONFIG_INVALID`. The checker for
a list of requirements returns `CONFIGURATION_INVALID` with setting/comparison
issues. These existing answer formats remain different; the file move has not
introduced a new common response. [The error walkthrough](#reading-contractreportingerrorsts)
explains which answer a caller receives.

## Worked examples: checking one value, then several

Suppose a server is given `DATABASE_PORT` as text when it starts. It needs a
number before it can use that information to connect to a database. If the
information is missing or unusable, it also needs to say exactly what is wrong,
rather than simply report that startup failed.

These demonstrations use the module's real functions. They are not a complete
server or a replacement for core-server's existing configuration code. The
values below are invented for the example.

### Example 1: supply one value and request one check

The following snippet represents code in another file, outside
`packages/core/src/config/`. It uses the module; it is not the code that
implements the module's functions. You do not need to add this snippet to Core.

The first line imports two functions and the shared destination-port rule.
`@kanbien/core/config` is the name other code uses to access the folder through
its `index.ts` file:

- `destinationPortConstraint` is defined in `contract/constraints.ts`; it supplies
  the shared whole-number limits without running a check itself.
- `recordConfigSource()` is implemented in `domain/reading/source.ts` and exposed by `index.ts`.
- `validateConfigSettings()` is implemented in `domain/validation/settings.ts` and made available
  by `index.ts`.

```typescript
import { destinationPortConstraint, recordConfigSource, validateConfigSettings } from "@kanbien/core/config";

const supplied = { DATABASE_PORT: "5432" };
const source = recordConfigSource(supplied);

const result = validateConfigSettings(source, [
  {
    setting: "database.port",
    source: "DATABASE_PORT",
    rule: destinationPortConstraint,
  },
]);
```

The example code chooses the supplied information and the requirement. The
module provides the functions that do the reading and checking:

1. The example creates `supplied`, containing the text `"5432"`.
2. It calls `recordConfigSource(supplied)`. The function in `domain/reading/source.ts` copies
   that information and returns a way to read individual items by name. The
   example stores that returned object in `source`. It does not split anything:
   `DATABASE_PORT` was already an individually named item. No check has run yet.
3. It calls `validateConfigSettings(source, ...)`, passing the readable
   information and a list containing one requirement. The function in
   `domain/validation/settings.ts` loops through that list of requirements—not through every item
   in `supplied`. Here it has just one item to read and check: `DATABASE_PORT`.

For example, `source.get("DATABASE_PORT")` returns the text `"5432"`.
That is a lookup by name, not a check or a conversion to a number.

The example chooses what to read and which shared rule to apply:

- `setting` gives the item a name to use in problem reports: `database.port`.
- `source` says which supplied item to read: `DATABASE_PORT`.
- `rule` selects `destinationPortConstraint`: Core's shared whole-number
  requirement with limits 1 and 65535. The caller does not repeat those limits.

The example stores the returned answer in `result`. Nothing is connected to a
database or written to a log.

#### See what happens with different inputs

With `const supplied = { DATABASE_PORT: "5432" };`, the result is:

```typescript
{ ok: true, value: { "database.port": 5432 } }
```

The quotation marks around the supplied `"5432"` mean it is text. The returned
`5432` is a number. `ok: true` means this check passed, not that a database
connection has been attempted or proved to work.

Change the input to `const supplied = {};`—no port supplied—and the result is:

```typescript
{
  ok: false,
  error: {
    code: "CONFIGURATION_INVALID",
    issues: [{ setting: "database.port", reason: "missing" }]
  }
}
```

Change it to `const supplied = { DATABASE_PORT: "abc" };` and the result is:

```typescript
{
  ok: false,
  error: {
    code: "CONFIGURATION_INVALID",
    issues: [{ setting: "database.port", reason: "invalid-integer" }]
  }
}
```

There is a specific observation behind each reason: the named input is absent
for `missing`; it contains text that is not a whole-number spelling for
`invalid-integer`. Neither failure report repeats the supplied text.

### Example 2: supply four values but request only three checks

This is a separate example, also outside the Core folder. It uses exactly the
same two functions and shared constraint. There are four supplied items and
three requirements:

```typescript
import { destinationPortConstraint, recordConfigSource, validateConfigSettings } from "@kanbien/core/config";

const supplied = {
  DATABASE_HOST: "db.example.test",
  DATABASE_PORT: "5432",
  DATABASE_NAME: "orders",
  UNRELATED_LABEL: "",
};
const source = recordConfigSource(supplied);

const result = validateConfigSettings(source, [
  {
    setting: "database.host",
    source: "DATABASE_HOST",
    rule: { kind: "text" },
  },
  {
    setting: "database.port",
    source: "DATABASE_PORT",
    rule: destinationPortConstraint,
  },
  {
    setting: "database.name",
    source: "DATABASE_NAME",
    rule: { kind: "text" },
  },
]);
```

`recordConfigSource()` copies all four named items. It does not divide them
into work to do, decide which matter, or check any of them.

`validateConfigSettings()` then follows the three requirements in order:

| Requirement being processed | What it reads | What the check does |
| --- | --- | --- |
| `database.host` | `DATABASE_HOST`: `"db.example.test"` | Requires nonblank text without surrounding whitespace. It does not try to reach this address. |
| `database.port` | `DATABASE_PORT`: `"5432"` | Requires whole-number text between 1 and 65535, then converts it to a number. |
| `database.name` | `DATABASE_NAME`: `"orders"` | Requires nonblank text without surrounding whitespace. It does not check whether this database exists. |

No requirement names `UNRELATED_LABEL`, so the checking function does not read
or check it. Its empty value causes no failure, and it is not included in the
returned values. **Not checked does not mean valid.**

The result is:

```typescript
{
  ok: true,
  value: {
    "database.host": "db.example.test",
    "database.port": 5432,
    "database.name": "orders"
  }
}
```

Notice that the returned names come from each requirement's `setting` field,
not its `source` field. The former names the checked information; the latter
says where to obtain it.

#### Several problems in the same check

Keep those three requirements unchanged, but replace `supplied` with:

```typescript
const supplied = {
  DATABASE_HOST: "",
  DATABASE_PORT: "abc",
  UNRELATED_LABEL: "",
};
```

The host is blank, the port is not a whole number, and the required database
name is absent. For these ordinary value failures, the loop continues after
each problem and collects all three:

```typescript
{
  ok: false,
  error: {
    code: "CONFIGURATION_INVALID",
    issues: [
      { setting: "database.host", reason: "blank" },
      { setting: "database.port", reason: "invalid-integer" },
      { setting: "database.name", reason: "missing" }
    ]
  }
}
```

It can report a missing database name precisely because it follows the
requirements, not just the supplied items. There is no `DATABASE_NAME` item
to loop over in this input, but there is still a requirement to check it.

If any of these checks fail, the function returns a failure result, not a
partial set of successful values. This example's failures do not stop the
remaining value checks; an unexpected error thrown while reading is a different
situation and can interrupt the call.

### Where both examples use the module's files

```text
OUTSIDE packages/core/src/config/ — the example code
  Supplies the named items and a list of requirements
       |
       | calls functions imported from @kanbien/core/config
       v
INSIDE packages/core/src/config/ — the reusable implementation
  index.ts: exposes the functions; contains no checking implementation
       |
  domain/reading/source.ts: recordConfigSource() copies the supplied information
       |
       | its returned object is passed to the next function
       v
  domain/validation/settings.ts: validateConfigSettings() loops through the requirements
             and reads/checks the item named by each requirement
             For the port, it uses destinationPortConstraint selected by the
             caller from contract/constraints.ts: integer, minimum 1, maximum 65535
       |
       +-- all pass -> returns the checked values
       |
       +-- problems -> returns reports described by contract/reporting/setting-issues.ts
       |
       | the function returns its answer to the example
       v
OUTSIDE packages/core/src/config/ — the same example code
  Receives the answer in result and must decide what to do next
```

`contract/reporting/diagnostics.ts` is not needed to build the ordinary failure results above. It
would be used if, for example, the example's checking instructions instead said
minimum 100 and maximum 10. `domain/validation/settings.ts` rejects that programming mistake by
throwing an error carrying the named report defined in `contract/reporting/diagnostics.ts`, rather
than returning an ordinary missing-or-invalid-value result.

`contract/reporting/sourcing-issues.ts` is not involved in reading this in-memory collection.
It supplies names for a different situation: code tries to read information
from somewhere such as a certificate file, and that read fails.

The module has now separated usable information from a specific explanation of
failure. The code using it must act on that result: continue with checked values
when `ok` is true, or handle the failure when it is false. Core-server's existing
code uses Platform configuration to build its own diagnostic from the returned
issues. Producing that diagnostic and writing it to a log are separate from
the checks demonstrated here.

Future code can reuse the same functions with different input names and rules;
this does not require another database-specific checker inside Core.

## How this folder fits into the repo

There are two sides to this diagram: code outside this folder that needs work
done, and the reusable code inside this folder that performs that work. A
caller means the outside code using a function—such as the example above.
`@kanbien/core/config` is the import name, not another folder or service.
The files shown inside the module are not a sequence in which every file runs.

These are shared tools for existing and future code, not tools reserved for
the two files discussed below. A new service or connection to an outside system
can use them too. Its code supplies its own information, names and checking
rules, rather than putting service-specific details into this Core folder.
Adding a new file does not automatically check its configuration: that code
must call the appropriate functions.

```text
OUTSIDE THE MODULE — existing or future callers
  Supply information, logical names and checking requirements
                           |
                           v
  index.ts: exposes selected tools through @kanbien/core/config
                           |
                +----------+-----------+
                |                      |
  domain/ performs work       contract/ describes exchanges
    source: obtain a value      types: inputs/instructions
                               constraints: shared requirements
    readers/settings: check     setting-issues: value problems
    json-object: parse text     sourcing-issues: read observations
    issue-collection: collect   errors: returned failures
                |               diagnostics: allowed reports
                +---- uses those contracts ----+
                           |
                           v
OUTSIDE THE MODULE — the same caller
  Handles checked values/failures or a preserved thrown read
  Platform/entrypoint code supplies workload context and delivery

These are available tools, not a sequence that always runs.
Logging and database connections are separate operations.
```

There are also connections between the files:

- `domain/validation/settings.ts` uses the report descriptions from `contract/reporting/setting-issues.ts` to describe what
  failed. It does not use the issue collector: it builds its own problem list.
- The individual readers use `contract/reporting/diagnostics.ts` for missing or incorrectly typed values.
  Both `domain/reading/source.ts` and `domain/validation/settings.ts` use it for reading errors, and `domain/validation/settings.ts`
  also uses it for invalid checking instructions. That file uses Core's separate
  [diagnostics module](../diagnostics/index.ts) to create diagnostic records:
  reports with a defined code and permitted details.
- [Platform configuration](../../../../platform/config/src/diagnostics.ts) uses
  the reason names from `contract/reporting/setting-issues.ts` and `contract/reporting/sourcing-issues.ts` when building
  reports for its callers. The source-read names describe what was observed;
  they do not prove the underlying cause.

For a current example of this shared approach,
[kanbien-core-server-persistence-configuration.ts](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts)
supplies values and checking rules to `validateConfigSettings()` from
`domain/validation/settings.ts`. If the port is missing, it receives a problem report described by
`contract/reporting/setting-issues.ts`. That file then asks Platform configuration to turn that report
into a diagnostic for core-server. If the checks pass instead, it passes the
checked details to the PostgreSQL adapter. Core does not make that database
connection itself.

Another current example is
[platform/observability/src/configuration.ts](../../../../platform/observability/src/configuration.ts).
It checks information used to prepare monitoring—the code that records what
the system is doing—and uses the collector from `domain/reporting/issue-collection.ts` to gather problems
found by its own checks.
It does not need to use `domain/validation/settings.ts` to reuse that collector.

## When to use this module, and what the harness checks

The important question is not “does every file import Core configuration?” It
is “where is supplied information checked before the program relies on it?”

In the database examples, the code receiving the supplied text performs the
checks. Database connection code can then receive the checked number instead
of reading the original text and repeating the checks.

### Requirements already recorded by the repo

| Existing requirement | Where it is recorded | What this means here |
| --- | --- | --- |
| Check required configuration before serving requests or consuming jobs; stop startup for missing or invalid required information. Do not scatter direct environment-variable reads through business logic. | [Configuration standard](../../../../.agentic/03.product/standards/config-runtime-settings.md), requirement `config-runtime-settings.config-is-typed-and-validated`. | A required port must not remain unchecked until a request first needs the database. This is a written requirement, not proof that all code follows it. |
| Describe each safely knowable failure accurately, exclude sensitive values and test the relevant alternatives. | [Safe diagnostic standard](../../../../.agentic/shared/standards/require-safe-diagnostic-record.md), especially the requirements for new or changed configuration checks. | Report `database.port` and `missing` when supported by the check; do not copy submitted secrets into the report. |
| Review affected checks and their consumers, and link the reviewed source to definitions, tests and registered checks. | [Diagnostic coverage workflow](../../../../.agentic/shared/workflows/verify-diagnostic-coverage.md), particularly “Review responsibilities before editing” and “Implement and prove connected behavior.” | A change needs evidence about the actual checks and what happens to their results, not just a Core import. |

DIAG-002 moved configuration requirements into the harness as a standard.
This README explains those requirements and links to their owner; it does not
maintain a second authoritative copy. The remaining usage/adoption gaps below
are separate from that location correction.

### Who checks configuration and what callers do next

The [configuration checking responsibilities](../../../../.agentic/03.product/standards/config-runtime-settings.md#configuration-checking-responsibilities)
now define the policy. This guide explains it; the harness standard owns it.

Code receiving unchecked information arranges the appropriate checks. It can
call Core directly or call an existing function that performs those checks.
The latter caller does not need an otherwise unused Core import. Code receiving
already-checked configuration can use it without rereading the original source.
Certificate/TLS checks remain with security, not this generic module.

For each used input, the checking owner identifies whether it is required,
optional, given an explicit default or required only in certain circumstances.
On success, the caller uses the checked answer. On failure, it handles the
report before starting the operation that needs that information. An extra
item ignored by a checker is not automatically checked information.

### What is automatically checked—and what still needs behaviour proof

The [module-structure command](../../../../scripts/repo/module-structure/README.md#configuration-source-access)
now rejects recognised direct Node environment access in ordinary TS/TSX
Core, Platform, app and product implementation. Platform config loaders, the
existing server/worker process entrypoints and target bindings have different
source-reading responsibilities. The linked guide names the precise syntax,
paths and exclusions; adding a future file does not exempt it.

This control does not require every file to import Core. Checked-value consumers,
higher-level checking functions and specialised validators remain valid. It
also does not trace arbitrary aliases or establish that every check result is
used: caller tests and source review prove those responsibilities.

The [diagnostic adoption check](../../../../scripts/repo/diagnostic-coverage/script.py)
requires source-matched reviews and proof references for changed executable
code. It does not establish diagnostic truth or complete validation coverage.
Unchanged baseline files may remain documented legacy debt.

The existing Core, Platform and target fixtures now include proof of checking,
failure handling, omitted requirements and checked-result use. The actual target
startup fixture substitutes a checker failure and a different checked port: the
real caller must stop on the failure and pass the changed answer onwards.
These are bounded proofs, not a claim that every historical or future data path
is automatically bypass-proof. Shell/Python and unscanned access forms remain
subject to their owning checks, explicit handling and review.

### Context supplied by the consuming operation

Core can establish that a port is missing without knowing whether a server is
starting or a job is already running. The code performing that task supplies
those facts. This is **execution context**: which part of the system is doing
which task, and when the report occurred.

The existing core-server startup path supplies these fixed facts:

| Field | Actual value | Meaning |
| --- | --- | --- |
| `capability` | `persistence` | The part responsible for storing and retrieving information. |
| `operation` | `startup` | The task being attempted is starting that part of the server. |
| `stage` | `startup` | The failure occurred before normal server operation began. |

The [target configuration file](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts)
uses Platform's `bindPlatformDiagnosticContext()` to keep those facts together
with the permitted diagnostic definitions. Its `select()` method checks a
report against those definitions and returns the checked report alongside the
fixed context. A later caller does not resupply or override that context.

The [server startup file](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts)
uses it when reporting startup failure. This is an **excerpt** of the missing-port
log entry, not the whole entry or the ordinary Core checking result:

```typescript
{
  diagnostic: {
    schema: "core/diagnostic-record/v1",
    code: "kanbien-core-server.configuration-invalid",
    definitionVersion: 1,
    detail: { issues: [{ setting: "database.port", reason: "missing" }] }
  },
  diagnostic_context: {
    capability: "persistence", operation: "startup", stage: "startup"
  }
}
```

Core found the problem; Platform supplied the permitted report shape; the
target identified the actual task; the startup caller handled failure before
creating a database pool. Core did not write the log entry.

The [safe diagnostic standard](../../../../.agentic/shared/standards/require-safe-diagnostic-record.md#context-and-consumer-obligations)
owns those responsibilities. The [Platform contract](../../../../platform/contracts/src/diagnostics.ts)
checks required fields, permitted spelling and selected definitions. Tests and
source review establish that the target chose the truthful operation and stage;
a valid-looking word alone does not prove that. This one implemented path does
not complete DIAG-003's repository-wide consumer policy.

## Reading index.ts

`index.ts` lists the public names available from this module. It contains
exports only: it does not define the types or implement reading, checking,
error construction or logging.

For example, importing `validateConfigSettings` from `@kanbien/core/config`
gets the function exposed by the index, implemented in
[domain/validation/settings.ts](domain/validation/settings.ts). The index is not another checking step.

The following walkthroughs cover all 44 public names, under the files that own
them. File-level exports that are not public imports are labelled separately;
other modules do not import those private paths.

The [public module structure standard](../../../../.agentic/03.product/standards/public-module-structure.md)
owns this separation. The [existing checker](../../../../scripts/repo/module-structure/check.mjs)
and [fixtures](../../../../scripts/repo/module-structure/smoke-test.mjs) reject
implementation in governed indexes, contract-to-domain dependencies, internal
own-index imports, cycles and external private imports for adopted modules.
The standard records the exact catalog-assembly exception and remaining legacy
index debt. A structural pass does not prove that a file has a useful job or a
diagnosis is truthful; source review and behaviour tests still matter.

## Reading contract/types.ts

This file describes what callers supply and checking code accepts or returns.
For the port example, it describes a way to read `DATABASE_PORT` and an instruction
saying to check whole-number text. It performs neither the read nor the check.
Types help check programmer-written code, not information arriving at runtime.

### EnvironmentName

A TypeScript label on text that passed `environmentName()`. It lets a function
ask for a checked environment name rather than any string. Use the checking
function to obtain it; declaring the label does not itself perform a check or
create an environment. The returned value is still ordinary text when running.

### SecretReference

A TypeScript label on text that passed `secretReference()`. Use it where code
expects a checked secret-reference name. It neither contains a fetched secret
nor proves access to one. The label is a programming aid, not encryption or a
runtime security barrier.

### ConfigValue

The kinds of value these simple sources can hold: text, number, boolean or
`null`. It does not include objects, lists or the missing marker `undefined`.
Use it when describing a supplied simple value; individual checks decide which
kind is acceptable. This type does not require numbers to be finite by itself.

### ConfigRecord

A collection mapping names to `ConfigValue` or `undefined`, such as the
`supplied` collections above. Use it for input to `recordConfigSource()`.
Its `Readonly` notation tells TypeScript callers not to assign into it through
that type; it does not freeze the original object. The source function's copy
is what protects later reads from changes to the caller's collection.

### ConfigSource

Describes the object readers use: it must offer `get(key)`, which returns one
simple value or `undefined`. This lets readers work with a supplied reading
function without choosing where information originally came from.

`recordConfigSource()` is one implementation. Other implementations may obtain
information elsewhere, but those decisions remain outside this Core module.
The interface does not itself read files, contact services, validate values or
catch errors; an implementation supplies the actual reading behaviour.

### ConfigSchema

Describes a caller-written checker with a `parse(source)` function. That
function returns either checked configuration or `ConfigError`. The `TConfig`
in its declaration names the particular configuration shape that checker returns.

Use it to expose a module's own checker to a runner such as
[Platform configuration](../../../../platform/config/src/index.ts), which calls
each supplied checker's `parse()` function. The
[smoke app](../../../../apps/platform-smoke/src/app.mount.ts) provides a real
implementation. This interface is not the declaration list accepted by
`validateConfigSettings()`: it describes a function someone still has to write
and call. Declaring it alone does not check anything.

### ConfigSettingRule

Describes a supported checking instruction: `kind: "text"` requires nonblank
text without surrounding whitespace, with an optional `pattern` for permitted
spellings. A regular expression is a written pattern describing matching text.
`kind: "integer"` requires whole-number text and supplies `minimum` and `maximum`;
the checking function converts accepted text into a number.

`kind: "choice"` requires one of the exact text entries in `values`. For example,
`{ kind: "choice", values: ["apply"] }` accepts `"apply"`, but rejects `"delete"`
with `unsupported-value`. Missing, wrong-type, blank and surrounding-whitespace
checks still run first. The module that owns the job declares its allowed words;
Core supplies the reusable membership check, not the choice of jobs.

Use this type for the instruction, not the supplied value. It does not contain
every validation rule in the repo; certificate, provider and application checks
remain with their owners.

### ConfigSettingDefinition

Describes one instruction in the list: `setting` names the item in reports,
`source` names what to read, and `rule` describes the check. The port instruction
in Example 1 is a complete example. The caller chooses these names and rules;
Core does not decide which supplied items the application needs.

### ConfigSettingRelationship

Describes a requested comparison: `relationship` names it; `left` and `right`
identify two declared settings; `rule: "must-differ"` requires their checked
values to differ. It does not perform the comparison or contain actual usernames.

Use it as the third argument to `validateConfigSettings()`, for example to keep
administrator and runtime usernames different. `ConfigRelationshipIssue` describes
the answer when that comparison fails. The optional `TSetting` type parameter
can restrict participant names in TypeScript; it does not check live values.

## Reading contract/constraints.ts

This file defines named, reusable requirements for acceptable configuration
values. A **constraint** is a requirement that limits what a supplied value may
be. Giving a shared requirement one name lets other code select it without each
consumer maintaining a separate copy.

The file does not read information, perform checks or describe failures. It also
does not contain actual supplied values or names of environment variables. Its
first rule is `destinationPortConstraint`; the file's purpose is not restricted
to ports. Other rules can be added when they meet the ownership rules below.

### Why this is separate from the other contract files

`types.ts` describes what a checking instruction can contain. For example, an
integer instruction contains a minimum and a maximum. `constraints.ts` defines
particular reusable instructions using that shape: it chooses the actual limits
or permitted form for a named requirement. Neither file checks supplied values
just by being imported.

The other contract files describe failures and reports instead: `setting-issues.ts`
describes problems with supplied values, `sourcing-issues.ts` describes failures
obtaining information, `errors.ts` describes failed answers returned to callers,
and `diagnostics.ts` defines diagnostic reports. Those files describe what can
be reported, not which reusable requirement to apply. Actual checking remains
in `domain/` or in a consumer's checking code, not in the constraint declaration.

This file was added for DIAG-001; it was not part of the earlier structural move.
It provides a home for shared checking instructions, not a requirement to create
a new file for every rule or to move every application's rules into Core.

### Where future rules belong, and how the harness governs this

The authoritative placement rules are in the harness's
[reusable configuration constraint ownership section](../../../../.agentic/03.product/standards/public-module-structure.md#reusable-configuration-constraint-ownership).
The [diagnostic review workflow](../../../../.agentic/shared/workflows/verify-diagnostic-coverage.md#review-responsibilities-before-editing)
uses those rules when reviewing a change. This README explains that arrangement;
it is not a separate source of requirements.

A general configuration requirement with the same meaning across different
consumers can belong here. A PostgreSQL-specific rule belongs with PostgreSQL;
an application's chosen retry limit belongs with the code choosing that policy.
Two places using the same number does not by itself make their rules the same.
Source names and environment bindings still belong with the consuming code.

For a new or changed shared rule, the agent's existing task inventory identifies
its owner, affected consumers and any similar checks that deliberately remain
different. Review and focused tests establish that consumers use the shared
rule and retain the required behaviour. A future consumer does not adopt a rule
automatically: its code must select it through `@kanbien/core/config`.

These are implemented harness instructions, not an automatic classifier of every
rule in the repo. Existing module checks protect structural boundaries; deciding
whether a rule genuinely belongs in Core still requires source review. This
documentation change adds no new runtime rule or executable enforcement check.

### destinationPortConstraint

The shared rule for a numbered network connection destination. It describes
an integer from 1 through 65535, with `kind: "integer"`, `minimum: 1` and
`maximum: 65535`. It is frozen when created and readonly in TypeScript, so a
consumer cannot change the shared rule for another consumer.

The rule does not inspect a value by itself. In the worked examples, passing
it to `validateConfigSettings()` checks supplied text and converts accepted
whole-number text into a number. The
[PostgreSQL adapter](../../../../platform/adapters/aws/persistence/postgresql/src/configuration/index.ts)
already receives a number, so it uses this same rule's limits with its numeric
check. It does not pass that number through the text reader. Each path retains
its own missing/wrong-type/format failure distinctions.

The [core-server target](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts)
still chooses `database.port` and `PERSISTENCE_POSTGRES_PORT`; Core owns the
reused range, not those names. The two real consumers use it differently:

```text
Core: contract/constraints.ts
  destinationPortConstraint = integer, minimum 1, maximum 65535
                 |
                 +--> core-server target receives text such as "5432"
                 |      selects this rule for PERSISTENCE_POSTGRES_PORT
                 |      calls Core's validateConfigSettings()
                 |      receives the checked number 5432 or a failure
                 |
                 +--> PostgreSQL adapter receives a number such as 5432
                        reads the shared minimum and maximum
                        uses its existing numeric checker
                        returns its existing success or failure
```

Before DIAG-001, each consumer independently declared the same bounds. Now the
bounds have one owner, while the two consumers keep their different reading and
checking responsibilities. Future consumers needing this same destination-port
rule can import it through `@kanbien/core/config` too.

This is a destination rule, not a blanket rule
for every port: a server listener may legitimately use port 0 to ask the operating
system to choose a free port. Listener/default policies and test port allocation
remain with their owners.

## Reading contract/reporting/setting-issues.ts

This file describes problems found after attempting to obtain a value: for
example, an absent port or two supplied usernames that should differ but are
equal. It does not read values, run checks or maintain a problem list.
The separate [collector](#reading-domainreportingissue-collectionts) maintains that list.

An **export** is a name made available from a file. A TypeScript **type** describes
what programmer-written code is expected to pass or return; it does not check
a running server's inputs.

### configReasonNames

This is the shared collection of names for problems with configuration values.
For example, a database port check and a retry-limit check can both report
`configReasonNames.missing`, whose value is the text `"missing"`. They share the
same word without sharing their port or retry rules. The collection does not read
an input, run a check or choose which problem actually occurred.

Each name has a readable property, such as `invalidJson`, and the exact text
used in reports, such as `"invalid-json"`:

| Property | Text used in a report | Plain meaning |
| --- | --- | --- |
| `missing` | `missing` | A required value was not supplied. |
| `blank` | `blank` | Text was empty or contained only spaces. |
| `surroundingWhitespace` | `surrounding-whitespace` | Text had whitespace at its beginning or end. |
| `wrongType` | `wrong-type` | The kind of value was wrong, such as a number instead of text. |
| `invalidFormat` | `invalid-format` | Text did not follow the required pattern. |
| `unsupportedValue` | `unsupported-value` | Text passed the basic checks but was not one of the declared allowed choices. |
| `invalidInteger` | `invalid-integer` | A value did not meet the check's whole-number requirements. |
| `outOfRange` | `out-of-range` | A number was outside the allowed limits. |
| `inconsistentSettings` | `inconsistent-settings` | Values did not satisfy a rule about how they must work together. |
| `invalidJson` | `invalid-json` | Text could not be read as JSON. |
| `wrongShape` | `wrong-shape` | Data was read, but was not the kind of object expected. |
| `empty` | `empty` | A required part contained nothing. |
| `forbiddenCharacter` | `forbidden-character` | A field contained a character its check does not permit. |

A diagnostic definition separately chooses the names it can report. For example,
a check that can only find a missing or blank value selects:

`[configReasonNames.missing, configReasonNames.blank]`

That selection belongs to that diagnostic's code and version. Adding a shared
name later does **not** add it to this selection. If that same diagnostic needs
to accept another reason, it needs a new definition version while supported old
versions remain readable. This prevents yesterday's report format from silently
changing when unrelated work adds a name. The
[harness standard](../../../../.agentic/shared/standards/require-safe-diagnostic-record.md#shared-names-and-versioned-selections)
sets this rule; the README explains it rather than owning it.

Use `configReasonNames` when selecting shared wording for a new definition or
report. A capability can still own its additional, specific reasons. Do not use
all values from this collection as an automatically growing diagnostic selection.
The object is frozen: running code cannot add or change its entries. Future
shared names are added deliberately in source, with the consumer review and tests.

### configIssueReasons

This existing exported list retains the first eight report strings in the table
above, in their existing order. It stays available for older callers that import
it. It is a fixed compatibility list, not the place to add future names and not
the default selection for new definitions.

Platform's existing helper still accepts those eight reasons when a caller omits
its selection. That fixed default now lives privately with the helper; it does
not expand when Core adds a shared name. New definitions should select their
applicable names explicitly from `configReasonNames`.

### configValueIssueReasons

This existing exported list retains all twelve current strings in the table,
in their existing order. It also stays fixed for callers that already import it.
We do not create another, larger global list for each future addition.

The core-server administrator-credential definition now explicitly selects its
twelve supported reasons. It no longer inherits the entire exported list. Its
reports and the older list's values remain unchanged; the ownership of the
selection is what changed.

### ConfigIssueReason

`ConfigIssueReason` tells TypeScript which words a programmer may use as a reason.
It does not read configuration, discover a problem or choose a reason.

The distinction is between checking the word and checking what happened.

**Checking the word while checking the program's code**

`configReasonNames` supplies names such as `missing` and
`out-of-range`. `ConfigIssueReason` is a TypeScript **type**: a rule describing
which values a variable or field may hold. Here, that rule is “only the report
words from this shared collection.” The source creates it using:

```typescript
export type ConfigIssueReason = (typeof configReasonNames)[keyof typeof configReasonNames];
```

`typeof configReasonNames` obtains the object's TypeScript description.
`keyof typeof configReasonNames` means its property names, such as `missing` and
`invalidJson`. Using those names inside the square brackets selects their values:
the report words such as `"missing"` and `"invalid-json"`. This produces a type
allowing those words; none of this runs a configuration check.

For example:

```typescript
const reason: ConfigIssueReason = "missing";
```

The `: ConfigIssueReason` part tells TypeScript to check the assigned word
against that rule. `"missing"` is on the list, so this assignment is accepted.
Other files can obtain the type with
`import type { ConfigIssueReason } from "@kanbien/core/config"`.

If the programmer misspells it:

```typescript
const reason: ConfigIssueReason = "mising";
```

TypeScript reports an error because `"mising"` is not an allowed name. This
helps catch mistakes before running the program. The type itself does not add
a check that runs when the server starts.

**Checking what actually happened when the program runs**

The function examining the database port must establish whether it was supplied.
In our example, `validateConfigSettings()` in `domain/validation/settings.ts` reads the requested
item and chooses `missing` only if that read returns `undefined`—no value.

If a programmer reports `"missing"` even though the port was supplied,
`ConfigIssueReason` cannot catch that mistake: the word is allowed, but the
explanation is wrong. Behaviour tests must check that each input produces the
correct reason.

Use this type for variables, function arguments or report fields that should
accept the shared configuration reason names. It restricts the wording; it
does not replace the code that investigates the problem.

### ConfigSettingIssue

This type describes a report about one setting. It has two fields:

- `setting`: the name of the requirement, such as `database.port`.
- `reason`: one of the names allowed by `ConfigIssueReason`, such as `missing`.

Use it for the individual problems returned by
`validateConfigSettings()` in [domain/validation/settings.ts](domain/validation/settings.ts).

This is also the connection to the notation we encountered in that validator:
`ConfigSettingIssue["reason"]` means “use the type assigned to this report's
reason field.” It points back to `ConfigIssueReason` above.

The report has no field for the rejected value. Keep the actual port, username
or password separate from the description of the problem.

### ConfigCheckIssue

This type describes a report that may also identify a position in a list.
It has `setting` and `reason`, plus three optional fields:
`index`, `attributeIndex` and `relatedIndex`.

For example, a check could report that a problem belongs to the first item in
its list by including `index: 0`. Positions start at 0, so the second item is 1.
The check using these fields must explain which list or part each position refers
to. Omit a position when it is not known or does not apply.

Use this type with checks that need those extra locations, including the
[collector described later](#createconfigissuecollector). Unlike `ConfigSettingIssue`, it lets the caller choose its
own reason names. The `TReason` in the source is the TypeScript placeholder
for that choice; without a choice, its reason type is simply text.

For example, [Platform observability configuration](../../../../platform/observability/src/configuration.ts)
uses it with its own reason names to describe problems in telemetry settings.

### ConfigCheckFailure

This type describes the result of collecting several problems:

- `issues` contains the reports the collector kept.
- `truncated` says whether further reports were offered after its limit.

Use this when returning a collected set of problems to another part of the repo.
If `truncated` is true, the reader must not treat `issues` as the complete list.

### ConfigRelationshipIssue

This type describes a problem involving a comparison between settings. For
example, the administrator username and runtime username must be different.

It names the comparison using `relationship`, gives its two setting names as
`left` and `right`, and records `rule: "must-differ"`. It contains neither of
the actual usernames.

Use it for failed comparisons returned by `validateConfigSettings()` when a
caller supplies relationship rules. The
[core-server administration settings](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts)
provide a real example. If a participant setting is itself invalid, the validator
does not pretend it has successfully compared the two values.

## Reading contract/reporting/sourcing-issues.ts

This file names observations about failing to obtain information, such as
reading a certificate file. It contains no file reader. Unlike a setting issue,
a failed read does not establish what the file contains or whether it is valid.

### configSourceReadFailureReasons

A frozen list containing these five names:

| Name | Observation supported by the failed read |
| --- | --- |
| `not-found` | An item in the requested location could not be found. |
| `read-denied` | Access was denied. |
| `not-a-directory` | A part of the location that needed to be a directory was not one. |
| `is-a-directory` | A directory was identified where file content was expected. |
| `unclassified-read-failure` | The read failed, without evidence for one of the other observations. |

The [core-server certificate reader](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts)
is one consumer; other readers can reuse the meanings through
[Platform configuration reporting](../../../../platform/config/src/diagnostics.ts).
The code observing the failure selects the supported name. A generic exception
does not establish `read-denied`; even a denied-read observation does not identify
which permission or policy caused it. These names contain no actual location,
file contents or native error message.

### ConfigSourceReadFailureReason

The TypeScript type allowing one name from that list. In
`(typeof configSourceReadFailureReasons)[number]`, `typeof` obtains the list's
type and `[number]` selects any numbered entry's type. It does not mean the
reason is a number. Use it to catch misspelled reason words in code; it neither
performs the read nor proves a reported reason is true.

## Reading contract/reporting/errors.ts

An individual issue says what is wrong, such as a missing port. A returned
failure says a particular checking operation did not succeed and carries its
established issues. This file describes those answers and constructs the older
individual-reader errors; it does not discover the problems.

### ConfigErrorCode

The two outer error names for these simple readers and caller-written
`ConfigSchema` checkers: `CONFIG_MISSING` and `CONFIG_INVALID`.
Use them when constructing or handling `ConfigError`. They are not the
`CONFIGURATION_INVALID` result code used by `validateConfigSettings()`.

### ConfigError

Describes a failed simple read or caller-written schema check. It contains the
outer `code`, a nonempty `issues` list, and optional `diagnosticRecord` and
`relatedDiagnosticRecords` fields. Use it when handling those returned failures.

Here each issue is a `ValidationIssue`, defined in the
[validation module](../validation/index.ts): it has a location `path`, an error
code and explanatory message information. This is a different shape from
`ConfigSettingIssue`, which has `setting` and `reason`.

Do not assume the whole error is safe to log. Legacy message information can
include supplied names/references, and `configError()` accepts caller-provided
descriptions. The separate diagnostic record has its own permitted-detail
checks; approved reporting paths must select and validate what they deliver.

### configError

Builds a `ConfigError` from an outer error code and a nonempty list of individual
problem descriptions. The caller can also supply a diagnostic record and related
records. Use it when implementing a checker that follows `ConfigSchema` below.

It packages what the caller supplies; it does not discover failures, validate
the truth of the descriptions, sanitise arbitrary content or write a log.
TypeScript requires at least one issue in a correctly typed call. This is not a
substitute for checking values received from outside TypeScript.

### ConfigSettingsFailure

The failure from `validateConfigSettings()` without comparison instructions:
`code: "CONFIGURATION_INVALID"` and an `issues` list of `ConfigSettingIssue`
reports. Example 2 shows the complete answer. It differs from the individual
readers' `ConfigError`; it has no built-in diagnostic or logging step. The
consumer can pass these established issues to its approved diagnostic constructor.

### ConfigSettingsRelationshipFailure

The failure when comparison instructions were also supplied. It has the same
code and `issues`, plus `relationshipIssues`. A comparison-only failure can
have no individual issues: both values passed but were equal when required to
differ. Use it for the three-argument checking call. No database privileges or
actual username existence are checked here.

### Helpers used only inside this module

`missingConfigError()` packages reader-established absence.
`invalidConfigTypeError()` packages a wrong value kind or non-finite number.
`invalidConfigValueError()` packages a failed spelling check and its diagnostic.
They are file-level exports used by `domain/reading/value-readers.ts`, not public names
in `@kanbien/core/config`. Other modules use public readers or `configError()`
rather than these private paths.

## Reading contract/reporting/diagnostics.ts

A **diagnostic definition** describes a named report's permitted details.
A **diagnostic record** is one report constructed using that definition. This
file owns four definitions and two report constructors; the separate
[Core diagnostics module](../diagnostics/index.ts) provides the construction
and parsing mechanisms.

A constructor can reject wrong fields or reason words. It cannot establish
that an explanation is true: the reader/checker must observe the condition
first. This file does not read configuration or write logs.

### coreConfigPrimitiveDiagnostic

Defines `core.config.primitive-invalid`, version 1, for individual readers and
environment/secret-reference spelling checks. Its fields identify `field`,
`reader` and `reason`, not supplied values. For example, the number reader can
report `field: "value"`, `reader: "number"`, `reason: "wrong-type"`.
Use the definition to register or check reports, not to check a port itself.

### coreConfigSourceDiagnostic

Defines `core.config.source-threw`, version 1: reader, `source-read` phase,
`invocation-threw`, and an optional instruction position. Its cause classification
is unknown: a throw alone does not establish missing data, denied access or
invalid contents. Use it to recognise that limited observation, not interpret
arbitrary native error text.

### coreConfigDeclarationDiagnostic

Defines `core.config.declaration-invalid`, version 1, for faulty checking
instructions, not faulty supplied values. For example, minimum 100 and maximum
10 gives `field: "bounds"`, `reason: "reversed"`. The settings checker constructs
the report and throws `CONFIGURATION_SCHEMA_INVALID` before reading the values.

### coreConfigRelationshipDeclarationDiagnostic

Defines `core.config.relationship-declaration-invalid`, version 1, for faulty
comparison instructions. Comparing a setting with itself gives
`field: "participants"`, `reason: "self-reference"` and a thrown
`CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID`. Two valid values that happen to be
equal are different: they produce an ordinary returned comparison failure.

### coreConfigChoiceDeclarationDiagnostic

Defines `core.config.choice-declaration-invalid`, version 1. This reports a
programming mistake in the allowed-choice list, not bad supplied configuration.
The list must contain 1–32 distinct, nonblank text entries without surrounding
whitespace. It is copied before values are read, so later source reads cannot
change the accepted choices. Invalid lists throw before reading configuration;
the report contains a fixed reason and, when applicable, a list position—not
the rejected entry's text. It adds a new definition without changing older ones.

### coreConfigDiagnosticDefinitions

A frozen list of those five definitions. Both the module catalogue below and
the package's [combined catalogue](../diagnostic-catalog.ts) reuse these same
objects. Use this list for supported report registration, not a sequence of
checks to run.

### coreConfigDiagnosticCatalog

A frozen object with `owner: "core.config"` and `definitions` pointing to the
five-definition list above. It lets another module explicitly select config's
reports without also selecting every Core capability's reports.

An illustrative consumer outside this module can write:

```typescript
import { coreConfigDiagnosticCatalog } from "@kanbien/core/config";

const selectedDefinitions = coreConfigDiagnosticCatalog.definitions;
```

The import accesses the object defined in
[contract/reporting/diagnostics.ts](contract/reporting/diagnostics.ts).
The index only exposes it. This does not run configuration checks or report
a failure; it selects which report definitions a reader or registration uses.

### contract/reporting/diagnostics.v1.json

This [local JSON file](contract/reporting/diagnostics.v1.json) is a generated
copy of the module catalogue, for tools that cannot import TypeScript.
Its outer object has `schema: "core/diagnostic-catalog-export/v1"`, the existing
delivery limits, and `catalog` containing the owner and five definitions.
It is a catalogue of permitted reports, not an actual failure packet.

The public package address is
`@kanbien/core/config/diagnostics.v1.json`. For example, a Node consumer using
CommonJS can read it with:

```javascript
const catalogue = require("@kanbien/core/config/diagnostics.v1.json");
const owner = catalogue.catalog.owner; // "core.config"
```

The package export points to the JSON asset; it does not call `index.ts`.
Node's `require` reads JSON without requiring the consumer to know its private
folder path. Other runtimes use their own supported JSON loading mechanism.

The existing [whole-Core JSON file](../../contracts/diagnostics.v1.json) remains
available to current readers and readers that deliberately need all Core
capabilities. Neither file is edited to define new reasons or fields.
The existing [generator](../../../../scripts/repo/diagnostic-coverage/export-catalogs.mjs)
reads the executable definitions and produces both views; its `--check` mode
rejects stale copies. The export-format version does not force every report
definition inside it to have version 1.

The [safe-diagnostic standard](../../../../.agentic/shared/standards/require-safe-diagnostic-record.md#module-local-catalogue-exports)
owns this generation and compatibility requirement. Config is the reference;
other modules are not all migrated merely because this file exists.

### CoreConfigReader

A TypeScript type permitting `required`, `optional`, `string`, `number`,
`boolean` or `schema` in a source-read report. Here `schema` names the list-of-
requirements checker. It does not call any function; environment/secret-reference
spelling checks are separately named by the primitive definition.

### coreConfigPrimitiveRecord

Constructs a report matching the primitive definition from caller-supplied
`field`, `reader` and `reason`. Invalid report details throw
`CORE_CONFIG_DIAGNOSTIC_INVALID`; that is not a returned configuration failure.
This illustrative caller packages an already-established observation:

```typescript
import { coreConfigPrimitiveRecord } from "@kanbien/core/config";

const record = coreConfigPrimitiveRecord({
  field: "value", reader: "number", reason: "wrong-type"
});
```

The returned record is:

```typescript
{
  schema: "core/diagnostic-record/v1",
  code: "core.config.primitive-invalid",
  definitionVersion: 1,
  detail: { field: "value", reader: "number", reason: "wrong-type" }
}
```

The call did not read or check a retry limit. The real `numberConfigValue()`
checks the value first, then constructs this report after finding its wrong
kind. Neither this constructor nor its result writes a log.

### coreConfigSourceRecord

Constructs a source-threw record using a reader name and optional zero-based
instruction position. `coreConfigSourceRecord("schema", 1)` identifies a throw
while reading for the second instruction. It includes no key, native error
text or supplied value, and cannot identify the underlying cause. Invalid
report details throw `CORE_CONFIG_DIAGNOSTIC_INVALID`.

The internal reader and settings checker use it after a read throws, attaching
the report to the original thrown object where possible. Frozen objects or
primitive thrown values cannot always carry the extra field. The original
failure is not replaced simply to attach a diagnostic.

## Reading domain/reading/source.ts

This file lets checking code read information the caller already holds. It
does not choose a file, service or environment variable to load.

### recordConfigSource

Implemented in [domain/reading/source.ts](domain/reading/source.ts).

Creates a copy of a collection of named values and returns an object with a
`get(name)` method. For example, `source.get("APP_NAME")` returns `"orders"`;
an absent name returns `undefined`, meaning no value was supplied.

Use it when the caller already has a collection to read. It does not read the
operating system's environment, split items, validate them, convert them or
decide which ones matter. Changing the original collection after the call does
not change its copy. The permitted values are simple values, not nested objects.

### Internal helper: readConfigSource

Calls the supplied `get()` method. If it throws, this helper attempts to attach
a source-reading diagnostic and preserves the original thrown failure. It does
not turn every failure into `missing` or `read-denied`.

This file-level export is used by the module's individual readers, but is not
available from `@kanbien/core/config`. Other modules use public readers or supply
a `ConfigSource`, not this private helper.

## Reading domain/reading/value-readers.ts

These functions read one value at a time or check the two shared name spellings.
They do not apply a list of requirements. In particular, a number reader needs
an existing number; the settings checker can convert whole-number text.

### One-value example: read an application name

This example represents code outside Core, using two existing functions:

```typescript
import { recordConfigSource, stringConfigValue } from "@kanbien/core/config";

const supplied = { APP_NAME: "orders" };
const source = recordConfigSource(supplied);
const result = stringConfigValue(source, "APP_NAME");
```

First the caller creates the supplied information. `recordConfigSource()` copies
it and returns an object that can read an item by name. Then `stringConfigValue()`
asks that object for `APP_NAME` and checks that it exists and is text. The
returned `result` is:

```typescript
{ ok: true, value: "orders" }
```

No application has been started. The caller must inspect the result and decide
whether to proceed. This reader accepts any text, including empty text; checking
an application's naming requirements is a separate job.

### Several-value example: read different kinds of information

Here the values are already text, numbers or booleans. A **boolean** is the
program's `true` or `false` value, not the text `"true"` or `"false"`.

```typescript
import {
  recordConfigSource,
  stringConfigValue,
  numberConfigValue,
  booleanConfigValue,
} from "@kanbien/core/config";

const supplied = {
  APP_NAME: "orders",
  RETRY_LIMIT: 3,
  FEATURE_ENABLED: false,
};
const source = recordConfigSource(supplied);
const results = {
  appName: stringConfigValue(source, "APP_NAME"),
  retryLimit: numberConfigValue(source, "RETRY_LIMIT"),
  featureEnabled: booleanConfigValue(source, "FEATURE_ENABLED"),
};
```

The three calls read three named items from the same copied information. Each
returns its own answer. `results` is the caller's object collecting those
answers, not an automatically combined Core validation result:

```typescript
{
  appName: { ok: true, value: "orders" },
  retryLimit: { ok: true, value: 3 },
  featureEnabled: { ok: true, value: false }
}
```

Notice that `false` is a supplied value, not a missing one. A caller needing all
three items must handle all three results before using their values.

These simple readers do not convert text into numbers or booleans. In the
earlier `domain/validation/settings.ts` example, `"5432"` became the number `5432` because the caller
requested that supported text-to-integer check. `numberConfigValue()` instead
requires a number already to be present.

### Missing values and incorrect kinds of value

This separate example shows those differences. It deliberately extracts only
the two outer error codes, rather than displaying full error objects:

```typescript
import { recordConfigSource, numberConfigValue, requiredConfigValue } from "@kanbien/core/config";

const source = recordConfigSource({ RETRY_LIMIT: "3" });
const retryLimit = numberConfigValue(source, "RETRY_LIMIT");
const appName = requiredConfigValue(source, "APP_NAME");
let retryLimitStatus;
if (retryLimit.ok) {
  retryLimitStatus = "accepted";
} else {
  retryLimitStatus = retryLimit.error.code;
}

let appNameStatus;
if (appName.ok) {
  appNameStatus = "accepted";
} else {
  appNameStatus = appName.error.code;
}

const summary = { retryLimit: retryLimitStatus, appName: appNameStatus };
```

Each `if` looks at that call's answer. A successful answer selects `accepted`;
a failed answer selects its outer error code. `summary` gathers those two
selected words. In this example it is:

```typescript
{ retryLimit: "CONFIG_INVALID", appName: "CONFIG_MISSING" }
```

The retry limit was supplied, but as text instead of a number. The application
name was not supplied at all. Both calls complete in this example because they
return failure results; the caller still decides what happens next.

Each failed call returns `{ ok: false, error: ... }`. That `error` contains the
code, individual problem descriptions and any diagnostic information; `summary`
above deliberately shows only its code, not the complete failure result.

If reading itself throws an error instead of returning a value, the readers
try to attach a Core source-reading diagnostic and throw onward. That is
different from returning an ordinary missing-or-invalid result.

### requiredConfigValue

Reads one item and requires that it be present. It returns `{ ok: true, value }`
when the result is anything other than `undefined`, or a `ConfigError` with
code `CONFIG_MISSING` when it is absent.

Use it when presence is the check needed here. Empty text, `0`, `false` and
`null` all count as present; this function does not establish that they are
appropriate for the caller's purpose.

### optionalConfigValue

Reads one item without requiring it to exist. It returns the value directly,
or `undefined` for absence—not an object containing `ok` and `value`.

Use it when the caller owns the optional/default behaviour. A supplied `null`
is returned as `null`; the function does not choose a default or validate a
present value. Reading errors can still throw.

### stringConfigValue

Requires one item to be present and to be text. It returns a success containing
the text, `CONFIG_MISSING` for absence, or `CONFIG_INVALID` for another kind of
value. Use it when a consumer needs text without requesting further checks here.

It does not trim, reject blank text, enforce a naming pattern or turn numbers
into text. The [smoke app's configuration checker](../../../../apps/platform-smoke/src/app.mount.ts)
is an actual caller; it reads its application name with this function.

### numberConfigValue

Requires an existing number that is finite: not `NaN` (an invalid numerical
result) or positive/negative infinity. Use it for values already represented
as numbers. It returns a success, `CONFIG_MISSING` or `CONFIG_INVALID`.

Text `"3"` is rejected; number `3` is accepted. Fractions, zero and negative
finite numbers are also accepted: this reader does not require a whole number,
positivity or particular limits. Those requirements belong to further checks.

### booleanConfigValue

Requires an existing boolean, `true` or `false`. It returns a success containing
that value, `CONFIG_MISSING` for absence or `CONFIG_INVALID` for another kind.
Use it when an earlier step has already supplied an actual boolean.

It does not interpret text such as `"false"`, choose a default or treat `false`
as absence. Passing an environment string directly is not a conversion step.

### environmentName

Checks a text label identifying a program's environment, such as `staging`.
It accepts a label starting with a lowercase letter, followed by lowercase
letters/digits and optional single-hyphen-separated groups of letters/digits.
For example, `staging` passes and `Staging` fails.

On success it returns the same text with the TypeScript label `EnvironmentName`.
On failure it returns `ConfigError` with code `CONFIG_INVALID`. Use it when a
function expects that labelled environment name. It checks spelling rules, not
whether an environment is provisioned or is on an application's approved list.

### secretReference

Checks text naming where a secret can be found, not the secret itself. For
example, `kanbien/staging/db-password` could name a secret; it is not a password
and this function does not fetch one.

The name must start with a letter or digit; later characters may also be `.`,
`_`, `:`, `/` or `-`. Spaces are rejected. On success it returns the same text
with the TypeScript label `SecretReference`; otherwise it returns a
`CONFIG_INVALID` error. Use it for this provider-independent naming contract,
not as proof a reference exists or satisfies a particular provider's rules.

## Reading domain/validation/settings.ts

This file performs the port and multi-value checks illustrated earlier. Its
instructions come from `contract/types.ts`; its report shapes come from the
issue/error contracts. Unlike those descriptions, this file reads and checks.

### validateConfigSettings

Pass a `ConfigSource` and 1–32 `ConfigSettingDefinition` instructions. The
function follows those instructions in order, not every supplied item. It
checks the declarations before reading values, then reads each requested item
and applies its rule. Accepted integer text becomes a number; text is not
silently trimmed and no default is chosen.

Ordinary value failures are collected in instruction order. A failed call
returns `CONFIGURATION_INVALID`, not a partial set of successful values.
The earlier worked examples show complete success and failure answers.

The optional third argument supplies up to 32 must-differ comparisons. The
checker compares a pair only when both participants passed their individual
checks. This separate caller requests different invented usernames:

```typescript
import {
  recordConfigSource, validateConfigSettings, type ConfigSettingDefinition
} from "@kanbien/core/config";

const source = recordConfigSource({ ADMIN_USER: "same-user", RUNTIME_USER: "same-user" });
const definitions: ConfigSettingDefinition[] = [
  { setting: "administrator.username", source: "ADMIN_USER", rule: { kind: "text" } },
  { setting: "runtime.username", source: "RUNTIME_USER", rule: { kind: "text" } },
];
const result = validateConfigSettings(source, definitions, [
  {
    relationship: "administrator-runtime-separation", rule: "must-differ",
    left: "administrator.username", right: "runtime.username"
  },
]);
```

The text checks pass but the comparison fails. The result is:

```typescript
{
  ok: false,
  error: {
    code: "CONFIGURATION_INVALID",
    issues: [],
    relationshipIssues: [{
      relationship: "administrator-runtime-separation", rule: "must-differ",
      left: "administrator.username", right: "runtime.username"
    }]
  }
}
```

If a username were missing, its setting issue would be reported, but that pair
would not have a failed comparison: it did not have two valid participants.
Comparisons use checked values; integer text `"01"` and `"1"` both become 1
and therefore do not satisfy must-differ.

A thrown source read is different: it interrupts the call, preserving the
original failure and source evidence where possible. Later values are not
checked; no partial-success or combined partial-failure result is returned.
Invalid instructions throw their declaration error instead of an ordinary
value-failure answer. None of these outcomes proves a database connection works.

Use this checker when these supported rules fit the job. Specialist checkers
can instead share the report shapes or collector; certificate and provider
rules need not be forced into a generic text/integer check.

## Reading domain/validation/json-object.ts

JSON is text representing data, such as `'{"mode":"read-only"}'`. This file
interprets supplied text as an object; it does not obtain it from a file,
service or environment variable.

### parseConfigJsonObject

Checks for text, reads it as JSON, and requires an object rather than a list,
number, boolean or `null`. For this illustrative caller outside Core:

```typescript
import { parseConfigJsonObject } from "@kanbien/core/config";

const result = parseConfigJsonObject('{"mode":"read-only"}');
```

The result is `{ ok: true, value: { mode: "read-only" } }`. This establishes
an object was read, not that `mode` or its value is permitted. The consumer
still checks the expected fields and contents. That successful object can
contain secrets; success does not make it safe to log. `Readonly` is a
TypeScript restriction, not a runtime freeze here.

Failures return `{ ok: false, error: { reason: ... } }`:

| Supplied value | Reason | Why |
| --- | --- | --- |
| `undefined` | `missing` | No value supplied. |
| `false` | `wrong-type` | Not text. |
| `" "` | `blank` | No non-whitespace content. |
| `"{"` | `invalid-json` | Cannot be read as JSON. |
| `"[]"` | `wrong-shape` | JSON describes a list, not an object. |

Failures include no rejected text or native parser message.
[Core-server's credential reader](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts)
uses this parser, then PostgreSQL's credential checker checks the actual fields.
That second operation is not implemented by this parser.

## Reading domain/reporting/issue-collection.ts

Specialist checkers sometimes need to keep several problems together. This
file owns the collection mechanics; the checker owns its investigation. Report
descriptions remain in `contract/reporting/setting-issues.ts`.

### createConfigIssueCollector

This function creates a new problem list. It gives the caller two methods:
`add()` and `finish()`.

Use it when your checking code needs to gather several reports. It does not
read settings, choose reasons, log reports or connect to anything. The checking
code does the investigation; this helper keeps its reports together.

`add()` takes one report, checks its fields and stores its own copy. For example:

```typescript
import { createConfigIssueCollector } from "@kanbien/core/config";

const problems = createConfigIssueCollector();
problems.add({ setting: "database.port", reason: "missing" });
const result = problems.finish();
```

That illustrative call to `add()` records a diagnosis already made by the caller;
it does not prove the port is missing. The result is:

```typescript
{
  issues: [{ setting: "database.port", reason: "missing" }],
  truncated: false
}
```

The helper keeps at most 32 reports, in the order they arrive. A 33rd valid
report is not kept, and `truncated` becomes true. This prevents an unlimited
report while still making the omission visible.

The stored reports and returned list are protected against edits. Changing the
object originally passed to `add()` does not change the collector's copy.
Calling `finish()` returns the current result; it does not empty or close the
collector. Later additions do not change a result already returned.

The report must contain `setting` and `reason`, and only the optional position
fields described above. Names/reasons must follow the short-name spelling
checked by this function; positions must be non-negative whole numbers that
JavaScript can represent exactly. Unexpected fields or invalid report data cause
`CONFIGURATION_ISSUE_INVALID` to be thrown. A field that runs a function when
read is rejected rather than executed.

These checks do **not** prove that a diagnosis is correct or that text is free
of secrets. They also do not require the reason to appear in either shared list
in `contract/reporting/setting-issues.ts`. Callers must supply appropriate names and approved
reasons. Before sending a diagnostic, the caller must check that the report
uses the reasons allowed for that diagnostic.

An actual user of this collector is
[Platform observability configuration](../../../../platform/observability/src/configuration.ts).
The generic `validateConfigSettings()` function in `domain/validation/settings.ts` instead builds
its own list of `ConfigSettingIssue` reports; it does not call this collector.

## Following a missing setting through the files

1. The caller describes a required setting, its source name and its checking rule.
2. `validateConfigSettings()` in `domain/validation/settings.ts` reads it and observes that no value
   was supplied.
3. It adds a `ConfigSettingIssue`: `database.port` with reason `missing`.
4. The caller receives the failed result and can turn those issues into its own
   approved diagnostic record. Logging that record is a separate step.

The types and lists in `contract/reporting/setting-issues.ts` describe the reports. The code in
`domain/validation/settings.ts` performs this particular setting check. Keeping those jobs separate
lets other checks reuse the reporting shapes without using the same validator.


## Reading domain/reporting/diagnostic-reporting.ts

This file builds approved diagnostic packets from findings already established
by a checker. It does not read a source, discover a problem or decide whether
startup stops. The functions previously lived in Platform config; the old
Platform imports still expose these same functions.

### defineConfigurationDiagnostic and configurationDiagnostic

The first function declares a report code, its allowed logical setting names
and allowed reasons. The second supplies actual findings to that declaration
and returns a checked diagnostic result.

For example, calling code can declare "example.configuration-invalid" with the
allowed setting "database.port", then provide
`[{ setting: "database.port", reason: "missing" }]`.
The resulting successful construction contains a packet with that code,
definitionVersion 1 and those issues inside detail. It does not contain the
supplied database information. An undeclared setting or reason is rejected;
the caller still has to establish that the value really is missing.

These existing constructors retain their historical failureSource "platform"
classification and versioned reason selections. Moving their code does not
reinterpret old packets. New shared names do not automatically widen old definitions.

### defineConfigurationRelationshipDiagnostics and configurationRelationshipDiagnostic

The declaration function accepts allowed settings and comparisons, and supplies
separate field-only, comparison-only and combined definitions. Register each
returned definition. The construction function takes the checker's
`ConfigSettingsRelationshipFailure`, verifies each comparison matches its
declaration and serializes the permitted relationship identifier/rule, not the
compared values. Malformed evidence throws the existing fixed TypeError.

### defineConfigurationSourceReadDiagnostic and configurationSourceReadDiagnosticRecord

The declaration function names the permitted logical sources. The construction
function supplies an established finite read-failure reason, such as "not-found",
and creates a packet whose phase is configuration-source-read and effect is
not-assessed. The source reader, not this constructor, establishes the reason.
Malformed or undeclared evidence produces the existing fixed TypeError. Never
pass a file path, secret or exception message as a logical source/reason.

## Reusable requirements and concrete sources

### ConfigSettingRequirement

Defined in `contract/types.ts`, this is a logical setting name and checking
rule without an environment variable name. A dependency can export its
requirements once; each target separately binds them to actual supplied items.
`ConfigSettingDefinition` retains the original shape by adding `source` to
that same requirement. Existing bound examples above remain supported.

### validateConfigRequirements

Implemented in `domain/validation/settings.ts`, this applies the same existing checker
to a source read by logical names. Example calling code outside this module:

```typescript
const result = validateConfigRequirements(
  recordConfigSource({ "database.port": "443" }),
  [{ setting: "database.port", rule: destinationPortConstraint }],
);
// { ok: true, value: { "database.port": 443 } }
```

As with validateConfigSettings, several requirements are checked in order;
missing, "-20" and " " produce missing, out-of-range and blank findings.
Optional declared comparisons use the same relationship rules and error shapes.
A source throw keeps its identity and existing source-boundary observation.
This helper does not choose environment names or fetch provider configuration.

[Platform config](../../../../platform/config/README.md) supplies the common
process connecting dependency requirements to target bindings, invoking this
checker, then passing only accepted values to dependency-owned assembly.
Target composition selects a supported implementation; neither Core nor Platform
config becomes a service registry or starts a database client.

## Tests and remaining work

[config-runtime.test.ts](../../tests/config-runtime.test.ts) covers reading,
value checks, comparisons, JSON and collection.
[config-types.test.ts](../../tests/config-types.test.ts) covers the public types.
[foundation-diagnostics-runtime.test.ts](../../tests/foundation-diagnostics-runtime.test.ts)
covers precise evidence, preserved throws and read counts.
[Core boundary tests](../../tests/core-boundaries.test.mjs) and the
[module-structure fixtures](../../../../scripts/repo/module-structure/smoke-test.mjs)
cover indexes and dependency boundaries.

The existing [catalogue/reader tests](../../../../scripts/repo/diagnostic-coverage/smoke-test.py)
compare config's local definitions with its contribution to the whole-Core file.
Their disposable package fixture checks both public exports, included JSON bytes,
repeatable generation, stale or conflicting exports and rejected unknown/private
report detail. They do not install packages or qualify a deployed runtime.

The [actual startup fixture](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs)
checks failure before pool construction and fixed startup context. The
[Platform reporter fixture](../../../../platform/observability/tests/diagnostics-runtime.test.ts)
checks internal delivery and reporting-failure isolation.

All public config exports and internal-only file exports are covered above.
The [backlog](../../../../.agentic/shared/plans/implementation/diagnostics-backlog.md)
records the completed DIAG-004 separation of shared names from fixed diagnostic
selections and the remaining follow-up tasks. DIAG-003
establishes the checking policy and bounded access/caller proof, not universal
program analysis. DIAG-001's shared port constraint is implemented
here; DIAG-002's requirement location and DIAG-008's index cleanup are complete. This guide
does not implement the remaining tasks or qualify a deployment.
