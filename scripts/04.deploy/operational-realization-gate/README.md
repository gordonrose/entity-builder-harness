<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.script.operational-realization-gate.readme
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines:
  - architecture
  - security
  - sre
  kind: readme
  purpose: Map the source, boundary, inputs, and safe outputs of the Operational Realization Gate compiler.
  portability:
    class: reusable
    targets:
    - entity-builder
  used_by:
  - id: deploy.script.operational-realization-gate
    path: scripts/04.deploy/operational-realization-gate/script.py
-->
# Operational Realization Gate Compiler

## Source map

| File | Responsibility |
| --- | --- |
| `script.py` | Generic compiler for graph completeness, proof levels, gate order, lifecycle safety, strict normalized evidence, and provider leakage. Its compiler modes use no provider tooling; explicit selected-target inspection dispatches through a separate adapter. |
| `release_compiler.py` | Schema-backed immutable release definition and 17-stage acceptance-matrix compilation, reusing the realization contract validator. |
| `source_coverage.py` | Reconciles fresh independent inventory, reviewed adoption and composition; generates scoped source obligations. |
| `finding_triage.py` | Checks that every discovery finding has a current, policy-consistent open work assignment. |
| `caller_coverage.py` | Reconciles every discovered caller subject and edge with a reviewed source profile; keeps qualification blocked. |
| `operation_contracts.py`, `operation_contracts_cli.py` | Reconcile selected script/action/tool input contracts against freshly discovered invocation and dependency observations. |
| `result_consumption.py`, `result_consumption_cli.py` | Require fresh recomputation before accepting saved analysis and reject source results as release or operation authority. |
| `script.sh` | Repository-root command wrapper. |
| `smoke-test.sh` | Deterministic positive and negative contract fixtures plus the core-boundary scan. |
| `test_release_compiler.py` | Release binding, schema, graph, ordered gate, input/output safety and compatibility tests. |
| `test_source_coverage.py` | Source mutations, adoption, ownership, per-operation bindings and mixed-provider applicability tests. |
| `requirements.txt`, `requirements.lock` | Hash-enforcing installer entrypoint and the complete pinned validation dependency closure. |
| `verify-clean-environment.sh`, `clean_environment.py` | Create an isolated validation environment and run the ordinary public check. |
| `fixtures/` | Safe, provider-neutral examples. They are tests of compiler behavior, not live target specifications. |

## Commands

```bash
npm run deployment:realization:validate -- --contract path/to/contract.yml --validate-contract
npm run deployment:realization:validate -- --contract path/to/contract.yml --facts path/to/normalized-facts.yml --change-summary path/to/normalized-change-summary.yml --through recovery
npm run deployment:realization:validate -- --contract path/to/contract.yml --facts path/to/normalized-facts.yml --change-summary path/to/normalized-change-summary.yml --through execution-preflight
npm run deployment:realization:test
```

Use `--through execution-preflight` before a proposed controlled execution;
the compiler then requires passing evidence for every preceding gate. The
compiler emits only a stable result schema, contract ID, validation scope,
verdict, and safe finding codes. It does not open a network connection or
invoke a provider.

## Adapter boundary

A provider adapter is responsible for converting a provider inspection or plan
into one of the two normalized input documents. The compiler accepts only
generic component bindings, check IDs, UTC timestamps, gate verdicts, recovery
attempt relationships, and operation-class counts. Unknown fields—including
raw provider data and secret-like names—fail closed. Adapter code must live
outside this directory and must be tested independently.

## Source release compilation

The release mode extends this capability. Existing eight-gate contract/fact
commands retain their result schema and behavior. The seventeen release stages
are planning obligations above that protocol; compiling them does not replace
runtime verification or grant execution authority.

Python must have the dependencies in `requirements.txt` available. The compiler
loads both versioned YAML JSON Schemas from
`infra/04.deploy/contracts/release-control/v1/` on every compilation. Schema
references resolve locally; no schema or provider is fetched.

```bash
npm run deployment:realization:validate -- \
  --release scripts/04.deploy/operational-realization-gate/fixtures/valid-release.yml \
  --contract scripts/04.deploy/operational-realization-gate/fixtures/valid-contract.yml

# Detect an attempted rebind of a previously recorded source definition:
npm run deployment:realization:validate -- \
  --release candidate.yml --contract realization.yml \
  --baseline-release previous-definition.yml

npm run deployment:realization:check
```

Release mode accepts only `--release`, `--contract`, optional
`--baseline-release` and `--json`. It always emits JSON and returns 0 for
`compiled`, 1 for `failed`. Mixing runtime evidence arguments into this mode
fails. The former draft path delegates to this implementation through its
[compatibility wrapper](../release-control/README.md).

### Immutable definition and operation graph

The source definition requires a full source commit hash; immutable digests for
composition, environment and evidence policy revisions; artifact IDs/digests;
a logical target ID; a risk-tier reference; and a digest of the complete existing
realization contract. Human-readable IDs cannot substitute for these digests.
Target and risk-tier IDs are symbolic reviewed references, not provider names
or an invented risk-classification policy.

The selected operation graph lists an operation ID, realization execution unit,
profile, artifact ID, acting identity, symbolic command reference and ordered
dependencies. All realization execution units and artifacts must be bound.
The compiler checks their identities, entrypoints, immutable artifact references,
recovery and cleanup routes against the existing realization contract. A
runtime-bound artifact must receive a concrete digest in the release. Duplicate
IDs, missing references, cycles and dependencies on later operations fail.
Command references are declarative names and are never executed.

The release digest hashes canonical JSON containing the entire definition and
both loaded schema digests: sorted object keys, compact separators, ASCII JSON
escaping, UTF-8 bytes, SHA-256. Mapping order and YAML formatting do not change
identity; ordered arrays do. The realization contract digest uses the same
encoding of the parsed contract. Fixtures contain synthetic revisions and
policy references; they prove local compiler behavior only.

With `--baseline-release`, a different definition using the same release ID is
rejected. A changed definition needs a new release ID and yields a new digest.
This is a stateless compiler: it cannot establish global release-ID uniqueness,
resolve external revision existence, retain previous schema versions, or detect
an omitted/tampered baseline. The complete content digest is the immutable
identity that a later governed ledger must retain and compare.

### Matrix and safe result

The matrix schema is the authority for the exact seventeen ordered stage names.
Every row requires an owner, acting identity, operation profile and command,
selected operation IDs, nonempty evidence rules with proof level/environment
and positive expiry, invalidation rules, failure state, recovery and cleanup
routes, and a verdict. Every selected operation must occur in the matrix.
Every stage must cover **all** selected operations: omitting an operation from
one stage is an unsupported exemption. Row fields provide common defaults;
optional closed `operation_overrides` provide identity, profile, command,
evidence, recovery and cleanup requirements for a different operation. Overrides
must refer to selected operations, be unique, and leave at least one operation
using the defaults. Output expands these into explicit `operation_bindings`
for every operation at every stage. Each binding includes the exact execution
unit and artifact digest. Evidence check IDs are scoped to that operation and
stage; one operation's receipt cannot satisfy another's obligation.

The schema enforces minimum evidence proof levels and environments: unit,
integration and artifact stages need local proof or better; target inspection
stages need live-read proof or better; candidate, per-task, controlled-change
and recovery stages require live-execution proof requirements. Integration uses
a disposable environment, candidate proof uses a candidate environment, and
target gates require target evidence. Recovery can use a disposable rehearsal.
Continuous operation requires a positive observation-window declaration; a
single instantaneous proof cannot fulfill that requirement. The selected policy
must later resolve the required window, maximum ages and stronger risk-specific
obligations. Profile classification is declared here; independently proving that
classification belongs to the next discovery/coverage unit.

`release-definition` is a mandatory invalidation dependency, so any changed
binding, graph, rule or schema invalidates the compiled identity.

This source-only version accepts `not-started` verdicts. Other verdicts require
the future evidence ledger and verifier. All `not-applicable` claims are rejected
with `applicability-unsupported`; free-text explanations, claimed review and
embedded discovery facts cannot waive a gate. Independent discovery and reviewed
applicability generation must exist before exemptions can be supported.

Successful `release-control-result/v1` output contains:

| Field | Meaning |
| --- | --- |
| `scope`, `verdict`, `authorized` | `release-definition`, `compiled`, and always `false`. |
| `release_digest`, `schema_digests` | Immutable content bindings for definition and schema semantics. |
| `risk_tier`, `operation_graph` | Validated symbolic policy reference and ordered operations. |
| `acceptance_matrix` | Seventeen normalized rows with stage numbers, all earlier stage prerequisites, immutable release/target/artifact/contract bindings, and explicit per-operation requirements. |
| `findings` | Empty on success; fixed diagnostic codes on failure. |

Failure output omits source values, paths, YAML snippets and partial compilation.
Closed schemas reject unknown fields at every source boundary. Strict loading
rejects duplicate/non-string keys, YAML anchors/aliases, non-JSON types, control
characters, inputs over 1 MiB, nesting beyond 32 levels and oversized trees.
Only symbolic identifiers, digests, enums, bounded numbers and their structured
relationships reach success output. Inputs must contain no secret values;
identifier syntax validation is not a general secret-redaction service.

### Verification and next delivery unit

`deployment:realization:check` runs the existing positive/negative smoke cases,
release compiler tests, provider/network boundary scans and artifact metadata
checks for governed documentation, shell wrappers and fixtures. The release
tests validate the schemas themselves. The focused
suite can also run with `python3 -B -m unittest discover -s
scripts/04.deploy/operational-realization-gate -p 'test_release_compiler.py' -v`.

Independent discovery and composition coverage are described below. Evidence
admission, policy resolution, durable journals/locks, provider adapters, live
preflight and target qualification remain subsequent units. This compiler does
not evaluate runtime freshness or advancement.

## Independent source discovery and coverage

The existing wrapper also exposes `--discover` and `--coverage`. The collector
lives in [release-control/discovery](../release-control/discovery/README.md),
outside the generic compiler because source formats contain provider-specific
syntax. It reads files only. It never invokes discovered commands, builds an
image, retrieves a secret or calls a provider.

```bash
# Exit 1 with structured observations if any source remains unresolved.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --discover --source-root . --json

# Generates pending review entries, never approved dispositions.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --discover --source-root . --ledger-template --json

# Always recollects from disk; an inventory file cannot replace discovery.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --coverage --source-root . --composition composition.yml \
  --adoption-ledger adoption.yml --json

# Additionally bind source coverage to the first unit's immutable release.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --coverage --source-root . --composition composition.yml \
  --adoption-ledger adoption.yml --release release.yml --contract realization.yml
```

Use the direct wrapper when capturing JSON; npm prints its own command banner.
These modes accept only the options shown; duplicates, mixed legacy options
and a release without its contract fail. Coverage returns 0 for `covered`, 1
for `blocked` or `failed`, always with `authorized: false`. Discovery exit 1
can mean a complete inventory containing unresolved sources, not a tool crash.

### Contracts and reconciliation

Three additional closed v1 schemas define the inventory, source composition and
adoption ledger. Their versions and schema integrity are checked locally;
remote references are prohibited. The collector independently enumerates its
versioned roots, hashes source bytes, and records stable observation/parent
identities. Commands, environment values, resource names and secret references
are represented by digests. Safe relative source paths are included for review.

Composition binds each discovered executable to one operation and artifact,
then binds its command, configuration, secret and authority observations. A
shared task authority must bind every operation using that task. Multiple
executables cannot be collapsed into one operation, and sibling artifacts
cannot substitute for an operation's own artifact. Resource declarations
include provider boundary, owner, managed/external classification, authority
revision, permitted effects and cleanup owner. Every source dependency must
have its consumer access represented. External resources permit inspection
and consumption only; their cleanup remains externally owned.

The ledger must cover every discovered source at its current digest with a
reviewed disposition. Generated entries stay `pending`. Temporary compatibility
requires a replacement profile and future expiry; it cannot suppress unresolved
source semantics. Historical, retired and test-only claims remain blocked until
independent caller/retirement proof is implemented. An owner or review string
is a reviewed source assertion, not authenticated approval or live authority.

Changes to source content, collector, composition, ledger, schemas, rules or
evaluation date change coverage identity. Supplying an older inventory digest
blocks coverage. With `--release`, target/composition revision, operation IDs,
execution units, profiles and artifact IDs/digests must also match the existing
release definition. Artifact digests and authority revisions remain declared
source bindings: final artifact inspection and authority verification are later
evidence, not facts established by this scanner.

### Scoped obligations and compatibility

Successful coverage generates all seventeen ordered stage rows with explicit
assertion subjects:

| Stages | Assertion scope |
| --- | --- |
| 1–4, 16 | Whole release |
| 7 | Every artifact |
| 8–10 | Whole release and each managed resource/external dependency |
| 5–6, 11–15, 17 | Every operation, with its reviewed profile and artifact |

Rules reuse the matrix schema's minimum proof levels, environments and
continuous-observation requirement. They are obligations, not receipts or gate
verdicts. A container cannot be relabelled provider-native to avoid Stage 6.
The bounded v1 grammar requires an exact-command-in-artifact obligation;
provider-native execution grammar/qualification is still unresolved.

An external dependency can have a generated `not-applicable` assertion for
managed-resource effects at stages 8–9, with rule version and source basis.
Its access-authority assertion at stage 8 and dependency assertion at stage 10
remain required, as do aggregate release assertions. No entire gate is waived.
Callers cannot submit their own applicability or success verdict. The first
unit's `--release` matrix retains its strict all-operation/all-stage behavior
and rejects every submitted `not-applicable` claim. Generated scoped obligations
are a separate source result; merging them with execution receipts requires the
future evidence-admission contract.

The mixed fixture represents two hosted container operations and an externally
owned warehouse reference. It tests coverage and ownership rules applicable to
a future Snowflake integration; it does not implement or qualify Snowflake.

### Boundary and remaining queue

`covered` means reconciliation within the documented source grammar, not complete
repository discovery or target qualification. Profiles are reviewed declarations;
their runtime suitability is not inferred from arbitrary code. Unsupported
resource types, opaque scripts/actions, dynamic infrastructure and unresolved
image semantics block coverage even when declared in a composition or ledger.
The repository's initial adoption inventory therefore remains unresolved.

Next delivery unit: expand collector and caller coverage for the observed opaque
paths, with explicit profile classification, production-to-test caller proof and
adoption dispositions. Keep Phase 2 open until the actual estate reconciles.
Then implement exact-artifact qualification, followed by evidence admission and
the later approved control-plane/adapters/live work. No local source result
authorizes these external effects.

`npm run deployment:realization:check` includes legacy smoke cases, release tests,
source coverage/mutation tests, collector tests, boundary scans and metadata.
The checked-in fixture README explains reproducible local coverage. A safe
pending adoption snapshot is review work, never evidence of a successful release.

## Finding triage and caller accounting

These source modes extend the same public command. They answer which work owns
each finding and whether a selected invocation graph has been fully accounted
for. Their output cannot satisfy the existing release matrix or waive coverage.

```bash
# Generate open intake entries for the fresh source inventory.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --triage --source-root . --json

# Verify every finding is accounted for under the current routing policy.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --triage --source-root . --finding-triage finding-triage.json --json

# Discover every step and supported literal call reachable from this workflow.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --callers --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml --json

# Generate an unclassified, pending review; it cannot approve itself.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --callers --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml --review-template

# Check a source review against freshly collected callers.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --callers --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml \
  --caller-review caller-review.json --json
```

### Triage contract

`source-finding-triage/v1` binds the inventory, collector and triage policy
revisions. Each unique `(source_id, code)` finding has its current source digest,
intake owner, next action, delivery phase and `status: open`. Entries must exactly
cover findings, including observation issues promoted to their source. Duplicate,
missing, invented, stale, resolved or waived entries reject. Routing is governed
by the versioned implementation; an opaque command cannot be assigned to later
provider evidence to hide a source-discovery gap. Unknown diagnostics receive an
investigation candidate but prevent complete classification until policy supports
them. Owners are source intake assignments, not authenticated operation approvals.

The recorded 169-finding baseline routes 164 findings to Phase 2 and five to
Phase 3; none is a live-provider failure. Unsupported resource types first need
source grammar because they may conceal executable operations. Later provider
proof is an additional obligation. `classification_verdict: complete` means
every finding has an appropriate open assignment. `coverage_verdict: blocked`
continues to hold whenever findings exist; even `clear-source-findings` is not
coverage, execution or deployment authority. Triage never edits the inventory,
adoption ledger or coverage result.

### Caller contract

`caller-inventory/v1` records a selected workflow, content-bound source files,
typed subjects, invocation edges and fixed unresolved findings. Collection is
independent of `source-caller-review/v1`, which must bind every subject exactly
once to an operation ID, owner, profile and reviewed status, and acknowledge
every edge. Missing subjects/edges, collapsed operation IDs, stale graphs and
pending/unclassified entries cannot produce `accounting_verdict: accounted`.
Changes to profile/owner/target or the review/schema/policy change accounting
identity. The graph's collector revision also binds its shared source parser.

All `source-caller-result/v1` responses retain `qualification_verdict: blocked`
and `authorized: false`. Source profile assignments express reviewed intent;
they do not establish runtime behavior, caller absence elsewhere or permission
to mutate. Original opaque-terminal findings are retained with owned pending
gate-2 obligations. The existing seventeen-stage compiler remains the authority
for later release requirements; these accounting rows cannot replace its matrix.

The collector understands a deliberately narrow grammar of complete literal
blocks, root-manifest npm script fanout (including pre/post hooks), direct local
script calls and an exact repository-root Python dispatch wrapper. It hashes
arguments without emitting them. Production references to `tests/` files are
followed and content-bound. Conditional/dynamic shell, external actions, custom
working directories/shells/npm configuration and unsupported argument forwarding
remain unresolved. Tool and complex script bodies retain their own blocking
findings. The supplied stable source root is the assumed checkout root; runtime
binary resolution and ambient environment are not proved by source parsing.
See the collector README for the precise boundary and no-follow file handling.

The selected staging workflow publishes an image; it does not perform an ECS
rollout. Its literal checks reach fourteen package-command declarations. The
source map and reviewed profiles remain separate from proving those operations
behave correctly. Whole-workflow dynamic publication steps and external actions
stay explicit boundaries rather than being guessed from command names.

### Exit meanings and queue

| Command result | Exit | Meaning |
| --- | ---: | --- |
| Triage template with findings | 1 | Open work generated; coverage remains blocked. |
| Validated triage, classification complete | 0 | Complete assignment only; read the separate coverage verdict. |
| Caller graph containing unresolved findings | 1 | Graph collected, opaque behavior retained. |
| Caller review template | 1 | Pending and unclassified; review required. |
| Caller accounting complete | 0 | Exact subject/edge accounting; qualification still blocked. |
| Invalid, stale or incomplete document | 1 | Fixed diagnostics; no authority or partial approval. |

Phase 2 closes source/caller accounting gaps. Exact-artifact proof can be
implemented when its own source inputs are accounted for, without waiting for
its future receipts to satisfy discovery. Every unresolved proof continues to
block the relevant release gate. Next units extend actual script/action/import
coverage and adoption for the remaining operation families, then qualify the
exact artifacts. Source triage must not turn into an unlimited static analyzer.

## Consuming a source result

Exit zero reports success of the requested analysis. It is never a release
eligibility or operation-authorization decision. The optional consumption mode
makes that distinction executable for callers saving and later reading results.

```bash
# Save compiler output using the wrapper, avoiding npm's command banner.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --release scripts/04.deploy/operational-realization-gate/fixtures/valid-release.yml \
  --contract scripts/04.deploy/operational-realization-gate/fixtures/valid-contract.yml \
  > /tmp/release-source-result.json

# Recompute the same analysis from current inputs and compare normalized output.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --consume-result /tmp/release-source-result.json --purpose source-analysis -- \
  --release scripts/04.deploy/operational-realization-gate/fixtures/valid-release.yml \
  --contract scripts/04.deploy/operational-realization-gate/fixtures/valid-contract.yml
```

After `--`, provide an existing `--release`, `--coverage`, validated `--triage`,
reviewed `--callers` or complete `--operations` contract invocation.
Templates, discovery-only output and legacy
runtime facts are not accepted as source-analysis receipts. The command never
executes inspected commands and does not accept an expected-result file.

The closed `source-result-consumption/v1` contract emits `accepted` (exit 0)
only for successful recognized analysis with a full canonical match to the
fresh producer result. Stale bindings, changed normalized output, forged
success, unsupported scopes, unsafe fields and failed recomputation reject
(exit 1). Existing producer interfaces and exit meanings remain unchanged.
The comparison covers the producer's normalized result; a summary such as
triage does not encode every review field or prove that source files stayed
unchanged after collection. This is a local analysis check, not signed or
durable evidence admission.

Both `--purpose release-eligibility` and `--purpose operation-authorization`
always reject source results, including complete triage, accounted callers,
covered source and a compiled seventeen-stage matrix. Every decision retains
`authorized: false`, `release_eligibility: blocked` and
`operation_authorization: blocked`. No source verdict can be promoted into a
passed runtime gate. If the decision schema cannot be loaded or validated,
the command returns a safe rejection without claiming a schema digest.

The in-process helper accepts `expected_result` only from a trusted producer
rerun. Supplying two matching saved documents to that internal API is not a
trust boundary. Future orchestrators must use this guard for source analysis
and the later Phase 6 evidence-admission/authorization protocol for advancement.

## Repeatable source validation

```bash
# Fresh environment, verified dependency artifacts, full existing check:
bash scripts/04.deploy/operational-realization-gate/verify-clean-environment.sh \
  --python /path/to/python3

# Offline after obtaining the exact locked wheels from a trusted source:
bash scripts/04.deploy/operational-realization-gate/verify-clean-environment.sh \
  --python /path/to/python3 --wheelhouse /path/to/locked-wheels
```

The supported clean-check runtime is CPython 3.14.4 with the standard GIL build
on Linux x86_64 with glibc 2.17 or newer. The complete dependency closure,
including the pip bootstrap, is pinned by wheel hash in `requirements.lock`;
`requirements.txt` requires that lock, hashes and binary wheels. The wrapper
checks this contract, creates a fresh
temporary virtual environment, verifies installation, and runs
`npm run deployment:realization:check`. It cannot substitute a weaker test
command. A mismatched runtime, missing dependency or changed wheel fails the
check. Git, Bash, Node and npm are host prerequisites; the Python lock is not a
claim of a hermetic operating system or byte-identical hosted runner.

The direct wrapper is the authoritative entrypoint. The npm
`deployment:realization:clean-check` alias is a convenience subject to the
outer npm process's configuration. Inside the wrapper, validation rejects a
project `.npmrc`, isolates npm configuration and shell startup settings, and
forces the test shell and failure propagation. CI invokes the wrapper directly
so a project npm setting cannot bypass validation before the wrapper starts.

The ordinary check covers all source compiler/collector tests, consumer and
environment tests, workflow safety checks, legacy smoke cases and provider/
network boundary scans. Its metadata paths include the autonomous delivery
envelope, sustained implementation workflow, IaaS plan, source-adoption
documentation and validation workflow, alongside the existing gate docs.

The separate
[`release-control-source-validation.yml`](../../../.github/workflows/release-control-source-validation.yml)
workflow runs this same clean check on pull requests, pushes and manual
dispatches. It uses pinned action revisions and runtime versions with
read-only repository permissions. It installs validation dependencies only;
it does not invoke the staging publication workflow or obtain AWS credentials.
Adding this file locally does not publish it, run GitHub CI or enable a required
repository check. Those external activation steps remain separately governed.

The reliability slice closes local repeatability, check-coverage and safe
consumption gaps. It does not resolve the source estate's opaque execution,
artifact provenance or live-provider obligations. The next delivery unit is
selected script/action caller semantics, profile/argument contracts and build/
import closure, then broader adoption and exact-artifact proof.

## Selected operation source contracts

`--operations` extends the existing selected-workflow caller inventory. It
independently selects script entrypoints, external action instances and tool
invocations, then binds their observed arguments and dependency declarations.
For staging image publication this boundary contains nine scripts, nine action
instances and seven TypeScript build-tool invocations. The analysis never runs
an inspected command, imports repository code or retrieves an action.

```bash
# Discover current selected subjects, inputs and unresolved boundaries.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --operations --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml

# Requires an already current, complete caller review; emits pending bindings.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --operations --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml \
  --caller-review caller-review.json --operation-template

# Recollect callers and dependency observations, then check reviewed contracts.
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --operations --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml \
  --caller-review caller-review.json --operation-contracts operation-contracts.json
```

The closed `source-operation-inventory/v1` shape binds the fresh caller graph,
source bytes, collector revision, selected subjects, all observed incoming
invocations, observations and dependency edges. Build-config membership and
supported local references are independently collected; a contract cannot
provide a substitute inventory. Full source values, action inputs, arguments
and locators are represented by digests. Only safe relative paths, identities,
fixed kinds and diagnostic codes leave collection.

The closed `source-operation-contracts/v1` shape covers every selected subject
once. Owner, operation ID and profile must match its existing caller review.
Every invocation variant, observation and dependency must be acknowledged.
Generated declarations are pending; reviewed declarations require an
`observed-variants-only` argument policy, blocked unknown variants, completion/
failure/recovery rules and source, artifact, supply-chain, authority and recovery
proof requirements. Extra fields cannot assert successful effects or authority.

All nine actual script calls currently have empty trailing arguments. This is
a source-contract boundary, not a claim that the programs reject extra flags.
Eight do not inspect argv; the container-boundary script has explicit options.
A changed caller argument invalidates the old review even if a script might
ignore it at runtime.

Action observations preserve each instance separately, including both
attestations. Reference, explicit input set/values, condition, upstream output
references and inherited execution context are content-bound. Empty inputs
do not establish safe defaults. Mutable references stay unresolved, and even a
full commit pin retains implementation/default obligations. A conditional
publishing step does not reduce inherited workflow permissions.

Dependency extraction has a declared bounded grammar described in the
[collector README](../release-control/discovery/README.md). Literal references
are observed relationships, not proof that a branch executes or that all dynamic
inputs were found. Generated package shims, dynamically enumerated built tests,
computed paths/imports, arbitrary language semantics and external implementations
remain explicit source/artifact obligations. Neither contracts nor intake
assignments can waive those findings or approve an adoption exclusion.

`source-operation-result/v1` returns `contracts_verdict: complete` and exit 0
only for exact current source-contract accounting. It always keeps
`source_closure: blocked`, `qualification_verdict: blocked` and
`authorized: false`. Obligations point to source coverage, exact-artifact,
supply-chain, authority and recovery proof; they supplement the complete
seventeen-stage release matrix and never replace it. Templates and inventories
with findings return 1; stale, unsafe or incomplete contracts return 1.

Saved complete results can be consumed with the existing
`--consume-result result.json --purpose source-analysis --` followed by the
complete operation-contract invocation above. The guard recomputes all source
inputs and compares normalized results. Release-eligibility and
operation-authorization purposes still reject unconditionally. Earlier release,
coverage, triage and caller interfaces remain compatible.

Focused operation collector, action, compiler and public-command mutation suites
run in the ordinary realization check and clean environment. The next delivery
unit is deeper supported semantic/build-import coverage for remaining dynamic
boundaries, followed by exact-artifact qualification for this selected family
as its inputs become known. Whole-estate adoption and provider/live proof remain
open.

## Workspace build inputs and local artifact accounting

The existing public command exposes a read-only build mode:

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --builds --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml
```

It discovers build subjects from fresh caller analysis, resolves the supported
workspace/configuration/import grammar and emits `source-build-inventory/v1`.
Builds distinguish no-emission checks, declaration output and JavaScript output.
The source-derived expected paths are bounded predictions, not compiler output
receipts. Unsupported resolution and final-artifact obligations remain findings;
an inventory with findings exits 1. Neither a source inventory nor an empty
build selection is a passing release.

To compare a separately produced local output directory, select a build ID from
that inventory and add `--build-id <sha256-id> --artifact-root <directory>`.
The output uses `source-build-artifact/v1`. Complete local file accounting exits
0; missing/unexpected files, unsafe paths and unsupported mappings exit 1.
Generated package forwarding targets and runtime-test selection are checked
within the documented collector grammar. No script, compiler, test runner,
artifact executable or provider operation is executed by this mode.

Optional `--expect-inventory-digest <sha256-digest>` and
`--expect-artifact-digest <sha256-digest>` compare current observations with
previously recorded identities. The latter requires artifact mode. Every
invocation recollects source inputs; there is no saved-inventory input option.
Changed artifact bytes change the artifact identity even when paths are equal.
A digest comparison establishes identity, not trusted build provenance.

All local artifact results retain `authorized: false`,
`qualification_verdict: blocked` and `provenance: unproven`.
A matching directory can contain arbitrary behavior; structural accounting is
not runtime verification. This producer is deliberately not admitted by
`--consume-result`, including for source-analysis; existing supported producer
behavior is unchanged. Release eligibility and operation authorization remain
blocked. Unknown flags, mixed modes, malformed digests and duplicate options
fail with safe fixed diagnostics.

Versioned closed schemas, inert fixtures and focused positive/negative tests
cover this interface. The ordinary and isolated clean checks include both new
collectors and the public build command. The original sixth-unit evidence used synthetic artifacts only. The following
locked-build interface adds genuine local compilation and selected execution;
final-container and admitted provenance proof remain open. See the
[collector grammar](../release-control/discovery/README.md) for supported
resolution and generator limits.


## Locked local builds and selected runtime execution

`verify-local-build.sh` is execution tooling inside this existing capability.
The provider-neutral compiler and `--builds` accounting mode remain read-only.
The new wrapper freshly discovers the seven selected staging-workflow TypeScript
configurations, copies bounded repository inputs into disposable disk-backed
snapshots, installs the locked dependency closure, and invokes the real compiler.
It accepts no arbitrary executable or saved success receipt as input.

`node-toolchain.lock.json` and `local-build-toolchain.schema.yml` pin Node 22.23.3
(Linux x64), its bundled npm 10.9.9, TypeScript 5.9.3 and the exact root lockfile.
The closure contains 61 external distributions and 20 workspace links. Node's
archive SHA256 and every tarball's SHA512 are verified before extraction. Offline
`npm ci` disables lifecycle scripts, user configuration, audit and update calls;
installed package files are checked against the verified archives. Changes to the
lock, package closure or tool versions require review and a new lock binding.
The host requires Linux x86_64, glibc >=2.28 and usable bubblewrap namespaces.
This does not pin an operating-system image or qualify a final container.

Acquisition and execution are separate. Choose new absolute directories on a
persistent disk outside the checkout. The acquisition command can resume an
exact partial cache: it rehashes existing entries, refuses unrelated, mismatched
or linked files, and creates missing files without overwriting. Transient public
download failures receive at most three attempts. URLs and hashes remain locked.
For example, after creating the scratch directory:

```bash
bash scripts/04.deploy/operational-realization-gate/verify-local-build.sh \
  --source-root . --acquire-cache /persistent/path/build-package-cache
bash scripts/04.deploy/operational-realization-gate/verify-local-build.sh \
  --source-root . --package-cache /persistent/path/build-package-cache \
  --scratch-root /persistent/path/build-scratch
```

Execution refuses memory-backed scratch mounts. The owned checkout is never
mounted as a tree; only the trusted observer file is mounted read-only from it.
Host credentials are absent. Toolchain and compiler inputs are read-only; only
declared output directories are writable. A private network
namespace permits isolated loopback tests but has no external route. Environment
variables are constructed explicitly; Node hooks, credentials and provider
metadata settings are not inherited. An unavailable sandbox fails closed; there
is no host-execution fallback. Commands have time, CPU, output and file limits.
These limits support the selected reviewed programs; this is not a general
hostile-code resource scheduler.

The compiler observer retains the selected compiler options and records actual
configuration, source, dependency, type-library and module-resolution identities,
plus emitted file hashes, compiler-provided source-to-output relationships and
numeric diagnostic codes. Every configuration uses
a fresh copy, including separate incremental build information. Repository and
implementation identities are checked before and after execution. Predicted
versus emitted membership is reported explicitly; unresolved static predictions
are not silently declared complete by a successful compiler invocation.

For the two runtime-test configurations, the existing runners execute against
compiled JavaScript, generated forwarding packages and verified external
dependencies in a separate source-free snapshot. Forwarding packages are derived
from current workspace export declarations and actual compiler emission using
one shared helper, including the explicitly bound image-only server-main alias.
The three existing generators no longer maintain independent package lists. Immediate selected test files
are recorded individually. The image configuration executes its existing shim
generator only. This build result does not renew final-container or provider
qualification: changed generated bytes require fresh exact-artifact evidence.
The separate local-container interface below remains the qualification route.

New `local-typescript-emission-observation/v1` and
`local-workspace-runtime-observation/v1` observations are composed by the
`local-build-result/v1` contract. Closed schemas reject unsafe fields, stale
digests and inconsistent bindings. Previous observation identities remain
readable historical formats; they cannot supply the new emission-backed proof.
Runtime artifact membership must be the exact disjoint union of compiler outputs
and derived forwarding files. Success means the selected local checks passed; it always
retains `authorized: false`, blocked release eligibility, blocked operation
authorization, blocked source closure and blocked release qualification. These
local observations are not signed attestations or universal authority controls.
The existing result-consumption guard rejects this producer for all purposes.

`--configuration` limits a diagnostic rerun to one of the seven supported paths;
its result identifies that subset and cannot represent the full selected graph.
Use the default all-seven command for delivery acceptance. Results contain safe
paths, fingerprints and diagnostic codes, never raw compiler/runtime output.

The canonical source check includes toolchain, orchestration and runtime-helper
unit tests. Real compiler fixtures require the verified Node and TypeScript
paths in `RELEASE_CONTROL_NODE` and `RELEASE_CONTROL_TYPESCRIPT_ROOT`, with
`RELEASE_CONTROL_REQUIRE_TYPESCRIPT_TESTS=1`; run `test_typescript_observer.py`
and `test_package_exports_direct.py` explicitly. An absent toolchain is never
counted as passing real-compiler proof.
The completed-unit session record provides exact commands, results and remaining
qualification obligations. [Package-export reconciliation](package-exports-README.md)
describes the source collector, projection contracts, compatibility alias and
direct-command prerequisites. Direct generators accept no saved projection
argument: they require Linux, Python schema dependencies, Node 22.23.3 and
TypeScript 5.9.3, and freshly verify existing compiler output. That compatibility
route does not qualify the dependency closure; the locked wrapper does.

The [seventh-unit review](../../../docs/04.deploy/plans/release-control-source-adoption/2026-09-29-locked-builds/README.md)
records 710 passing tests, the all-seven successful build result, two selected
runtime-test runners and image shim generation. It preserves unresolved static
predictions and the remaining final-container/hosted/provider acceptance work.


## Exact local container qualification

The existing build and image-smoke wrappers expose `--qualify-local` as their
first argument. Both route to this capability's `local_container.py`; ordinary
legacy flags remain compatible. Qualification never accepts the legacy skip
flag, caller-selected commands, tags, images, credentials or saved success
receipts. Misordered qualification flags fail before legacy parsing.

Choose an existing persistent scratch directory outside the worktree. Public
runtime-base acquisition is explicit and separate from payload preparation:

```bash
bash scripts/04.deploy/build-platform-shell-image/script.sh --qualify-local \
  --source-root . --scratch-root /persistent/path/container-scratch --acquire-base
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh --qualify-local \
  --source-root . --scratch-root /persistent/path/container-scratch \
  --package-cache /persistent/path/verified-build-packages
```

The package cache is the verified cache from `verify-local-build.sh`. A fresh
image-only compiler run, the existing shim generator, production dependency
selection and the public database trust bundle produce an exclusively created
payload. Retained and excluded dependency fingerprints reconstruct the prior
verified runtime dependency identity; package versions are checked against a
fresh root-lock selection. Development dependencies and TypeScript source are
absent from the final payload.

`container-image.lock.json` binds the reviewed Dockerfile and a concrete Linux
amd64 Distroless runtime manifest/configuration. The existing Dockerfile accepts
this payload through `PAYLOAD_STAGE=verified`, with the same final runtime recipe
as the legacy build. No compiler, package manager or apt command runs in that
selected build path. Its context contains only the verified payload, the public
certificate and the exact recipe. Docker's built-in frontend is used instead of
a mutable external syntax image. Engine versions are recorded, not claimed as
a completely pinned OS/daemon toolchain. `--network none` disables build-step
networking and `--pull=false` avoids normal base pulling; these options do not
prove that the Docker daemon cannot query registry metadata.

Execution uses only the explicit local Docker socket and an empty Docker
configuration. The finished image's complete `/app` file inventory must exactly
match the verified payload fingerprints. Server tests use that immutable local
image identity, its default command and working directory, a nonroot user,
read-only filesystem, private loopback with no external route, no host mounts
or published ports, reduced privileges and bounded resources. Both health
endpoints must pass. SIGTERM must produce exit 0 without an out-of-memory event;
removal of only the newly created owned test containers must be verified.
The local image/cache remain available; no image pruning or shared-daemon
configuration changes are performed.

Closed `local-container-lock/v1` and `local-container-result/v1` schemas validate
safe normalized evidence. The result records actual source/build identities,
payload and image identities, command, test settings, engine/runtime versions,
health, shutdown, cleanup and timestamps. `repository_head` is the checkout's
Git checkpoint label; the nested build's source digest identifies the actual
source bytes, including reviewed uncommitted changes. Docker image IDs may name
an OCI configuration or manifest depending on the image store; the pinned base
reference and configuration identity are kept separately. These local IDs are
not a claim of registry publication or signed provenance.

The source collector accounts for the image default and every selected ECS task
container. Only `image-default` can become `local-health-passed`. AWS server,
worker/relay, PostgreSQL bootstrap/migration/relay/worker/restore and external
sidecar obligations stay pending. Unsupported product commands, duplicate YAML
keys, unsafe paths and absent packaged commands fail closed. An external image
with unresolved command/identity remains an explicit obligation. Server health
does not establish successful database initialization, AWS authority or complete
application behavior.

All result fields retain false authorization and blocked release eligibility,
operation authorization, qualification and source closure. The existing consumer
rejects this producer for every purpose. Results are unsigned local observations;
trusted admission, supply-chain scanning/signature policy, hosted CI and live
qualification remain later. The legacy workflow still uses its original build
path: it must not inherit this new mode's receipt or rebuild after qualification
and assume the new image has passed. Later adoption must promote the exact
qualified artifact with its required additional evidence.

## Finite-job execution conformance

The shared `container_engine.py` now also observes bounded finite commands.
`finite_job_contracts.py` loads the closed `finite-job-profile/v1` and
`finite-job-result/v1` schemas. A profile binds the immutable image and payload,
entrypoint, command, working directory, output/deadline bounds and required
terminal checks. The current local adapter supports Node JavaScript artifacts
in `/app` on the pinned Linux runtime; it is provider-neutral, not a claim that
all runtimes, dependencies or providers are supported.

```bash
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh --verify-finite-jobs \
  --source-root . --scratch-root /persistent/path/finite-job-scratch
```

This explicit mode uses a separate inert conformance image and the existing
local engine, pinned-base/build identity checks, payload inventory, isolation
and owned cleanup. It accepts no arbitrary image, command, environment, secret,
saved success receipt or provider target. The existing server/image mode stays
compatible. Its runtime base must first be acquired through the existing
`--qualify-local ... --acquire-base` mode; conformance never pulls a new base.
Docker daemon metadata-network and unpinned-host limitations remain as described
above. The fixture image remains local; newly created containers are removed.

Every attempt injects a fresh nonce and the digest of its profile and schemas.
A single bounded, duplicate-free `finite-job-terminal/v1` JSON envelope must
match those identities and the exact ordered checks. Exit zero alone cannot
complete the execution. Changed payload, commands, isolation or bindings,
nonzero exit, OOM, missing/extra/stale output, timeout and failed cleanup cannot
produce a completed receipt. Interrupted/uncertain jobs are never automatically
retried. `timeout_seconds` bounds the attached command execution; `elapsed_ms`
includes preparation, observation and cleanup. Each cleanup call is separately
bounded; a whole-operation deadline remains part of the later operation engine.
Cleanup independently checks ownership and absence even after the Docker client
times out. Raw stdout/stderr and exceptions are excluded from
public evidence; only accepted canonical terminal facts have a digest.

The eleven real fixture cases include two completions and nine expected
refusals. A successful conformance aggregate must contain every expected case
once, with fresh attempts and verified cleanup. Its closed safe projection
binds current implementation, fixture recipe/payload, pinned base, constructed
image and product-profile inventory, with `product_profile_updates: []`.
The nested versioned results distinguish failed execution from successful
failure detection. The common consumer rejects both new producers for source
analysis, release eligibility and operation authorization.

Terminal checks are job-reported claims: `semantic_verdict: unverified` remains
mandatory until independent profile-specific effect verification is implemented.
All source/release/operation/qualification authority stays blocked. Fixture
conformance does not qualify PostgreSQL or any other product task and does not
supply durable ownership, fencing, crash reconciliation or trusted admission.
Next continue Phase 3 with reusable independent effect/dependency verification
and required artifact admission; retain actual command-specific obligations.
Durable operation controls, AWS adapter/preflight and target qualification
follow the plan's gates. PostgreSQL Stage 6 remains paused.

## Infrastructure composition references

The existing `--discover` and `--coverage` modes now include scoped infrastructure
symbols and references. Literal `deploy/cloudformation-composition/v1` manifests
bind their exact fragment set; each standalone template has a separate symbol
table. Both branches of a supported conditional are discovered. Missing,
duplicate, cyclic, cross-scope and unsupported references remain findings.

A reviewed source composition must acknowledge all discovered references using
`infrastructure_references`. Resource endpoints must also occur in its reviewed
resource graph. Reference acknowledgement cannot exempt an executable, invent
provider ownership or bypass another source finding. Structural support for a
resource family does not validate every provider property, permission, attribute,
actual parameter value, imported export or runtime behavior. The collector and
all consuming build/caller revisions bind the structural helper's exact bytes.

## Independent packaged dependency effects

```bash
# Explicit public acquisition of the locked local dependency image:
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh \
  --verify-dependency-effects --source-root . \
  --scratch-root /persistent/path/dependency-scratch --acquire-dependency

# Fresh exact product build and independently observed command effects:
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh \
  --verify-dependency-effects --source-root . \
  --scratch-root /persistent/path/dependency-scratch \
  --package-cache /persistent/path/verified-package-cache
```

This mode runs the actual packaged bootstrap and migration commands against a
locked disposable PostgreSQL engine. It extends the same bounded container
transport, with an owned internal network and fixed read-only fixture inputs.
The ordinary server and finite-job modes retain their no-network settings.

The exact final product image supports a narrow local certificate binding:
`RELATIONAL_TLS_CA_MODE=local-qualification-v1`, a fresh qualification identifier,
the fixed dependency hostname/port, and `/run/release-control/ca.crt`. Full TLS
verification stays mandatory. Without that binding, the existing pinned RDS CA
remains the default. The production target checker rejects local binding fields
in target descriptors; independent positive/negative tests exercise that check.
The evidence identifies the local input binding and does not claim RDS/ECS/IAM
or production-secret injection proof.

Workload output supplies a bounded terminal observation. Separate database
queries verify roles, permissions, schema and migration history; repeated
operations and deliberate invalid-input/state cases must produce their expected
outcomes. Credentials and raw database/container logs are never public evidence.
The result remains local proof with release/operation permissions blocked.
Relay, worker, restore, whole-estate adoption and live qualification retain their
own pending obligations. See the dated dependency-effects acceptance record for
exact verified cases and limitations.

## Authenticated artifact evidence

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --artifact-verifier-acquire --verifier-cache /persistent/path/verifier-cache
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --artifact-verifier-conformance --verifier-cache /persistent/path/verifier-cache
```

The artifact-admission mode re-verifies raw signed provenance, SBOM and scan
bundles using a digest-locked maintained verifier and pinned trust roots inside
a process with no network access or ambient credentials. Public inputs cannot
supply an alternate executable, trust root or preverified-result file.

Production policy fixes the official repository, branch and publication workflow;
source revision, exact OCI manifest identity, platform and evidence policy must
match. A Docker image/configuration digest cannot substitute for the registry
manifest identity. Required policy values such as scan freshness and scanner
version must be reviewed inputs; absent values block admission. Existing
CRITICAL/HIGH refusal is preserved.

Real conformance verifies a public signed upstream artifact with an explicit
fixture identity. It does not qualify a platform image or prove the publication
workflow has run. A production supply-chain result remains evidence for one
acceptance gate, with release and operation authority blocked. Signed SBOM shape
and subject binding alone do not establish independent package completeness.

The existing publisher still needs actual base-material provenance and a signed
scan predicate before it can supply every required production input. Unsigned
saved scan counts and desired base-image constants cannot fill those gaps.
Publication, hosted acceptance and provider operations retain separate approval
boundaries. See the artifact-admission fixture documentation for full command
inputs, trust acquisition provenance and conformance limitations.

## Local durable operation controls

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --control-store-conformance --scratch-root /owned/private/scratch
```

This extends the existing gate with immutable operation intent, an append-only
validated journal, atomic resource-scope claims, persistent fencing generations
and full bounded typed evidence in a local SQLite reference store. Expired claims
permit reconciliation only. Unresolved effects retain their scope across release
identities; completed operations retain it until current fenced cleanup evidence
is verified. A hash alone cannot substitute for missing evidence content.

The command creates a fresh private fixture store and runs real competing and
interrupted processes. It cannot open an existing deployment database or accept
an arbitrary provider command. Fixed error output remains safe when schema or
module loading fails. Successful conformance is not release eligibility or
operation authorization, and the common source-result consumer rejects it.

The store binds its schema revision and host boot, refuses backward host time,
and uses verified SQLite DELETE journaling with FULL synchronization. It is a
single-host local reference, not distributed or authenticated production storage.
Process-crash tests do not establish power-loss, host-reboot or cloud durability.
Fixture lease/time limits are explicit test inputs, not production policy.

See [fixture and API documentation](fixtures/control-store/README.md). The next
unit connects the existing finite container engine to these records and proves
reconciliation after interruption. Provider-side effect fencing, production
storage, live preflight and release authority retain their separate gates.

## Aggregate caller coverage and adoption proposals

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --estate-callers --source-root . --json
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --adoption-migration --source-root . \
  --previous-adoption-ledger docs/04.deploy/plans/release-control-source-adoption/ledger.json --json
```

Aggregate collection starts from every root package command and discovered
workflow. Supported command bodies and complete dispatch wrappers have exact
source/edge proofs; npm lifecycle invocation contexts remain distinct. A parsed
wrapper does not establish its child implementation or tool/action semantics.
Raw source findings, structurally resolved findings and remaining graph boundaries
are reported separately. The original selected-workflow caller mode remains.

Existing `--coverage` now recollects this graph internally. It can remove only
current machine-proved structural findings, retains every unresolved boundary,
and still requires composition and adoption checks. There is no saved proof,
allowlist or reviewed-label shortcut. A successful structural result can be used
for source analysis only after fresh in-process recomputation; release and
operation authority always remain blocked.

Adoption migration produces a candidate plus an added/changed/unchanged/removed
delta. Every current row is pending, including previously reviewed unchanged rows.
Prior owner/disposition text remains a proposal. The original ledger is never
modified, paths are not retired, and the command exits 1 while review is pending.
The source-result consumer refuses this proposal. See the detailed
[caller reference](../release-control/discovery/estate-callers.README.md).

Next source coverage work must bind package exports to actual compiler emissions
and extend supported implementation/tool/action semantics. Whole-estate closure
cannot be inferred from file reachability or the intake owner label.

## Durable finite-fixture recovery

The existing public command connects durable local controls to the shared finite
container Engine. It commits immutable intent and consumes each action reservation
before dispatch. A replacement process reconciles the exact image, ownership,
resource identity and recorded observations; it cannot repeat an ambiguous create
or start request. Completion requires current terminal and cleanup evidence.

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --finite-recovery-conformance --source-root /absolute/repository \
  --scratch-root /absolute/private-scratch --image-id sha256:...
```

The image must match the source-owned previously qualified inert fixture pin.
This command never builds or pulls an image. It checks eight interruption windows,
including seven killed/reopened processes, and preserves private stores outside
Git. Success proves local protocol recovery only; all release, operation, source
closure and product qualification verdicts remain blocked. The common consumer
refuses both the aggregate and per-attempt results for every purpose.

See [the recovery contract and limits](finite-recovery.README.md) for fixed action
budgets, refusal states, local image availability, evidence and source bindings.
Provider stores, production artifact evidence, AWS preflight and target execution
remain separate delivery work. This does not resume PostgreSQL Stage 6.

## Selected staging MVP integrations

The existing public gate now accepts a source-bound selected staging blueprint.
See [selected blueprint compilation](selected-release-blueprint.README.md) for
the exact command, source invalidation, nine task groups and thirteen container
obligations. This compiles all seventeen acceptance rows; it grants no operation
authority and does not mark the proposed target policy approved.

[Qualified image publication](qualified-publication.README.md) connects the
existing final-image verifier to the existing staging publisher on the same
host. It preserves the tested manifest/configuration identity through registry
verification. Hosted execution remains a separate acceptance step.

The existing [relational task commands](../run-platform-shell-postgresql-relational-smoke/README.md)
also expose one fixed read-only database preflight mode. Its result is distinct
from task effect completion. The durable AWS controller must bind that mode to
the exact task revision and apply it in dependency order before live effects.

## Passive selected-target inspection

The existing wrapper also exposes the strictly selected, read-only AWS mode
[documented in the maintained adapter](../release-control/adapters/aws/README.md).
Both `--selected-readiness` and `--inspect-target` are required. It retains
blocked release/operation authority and never starts a task or refreshes drift.

## Selected operation/store conformance

The [selected v2 record seam](selected-operation.README.md) and
[conditional AWS store requests](../release-control/adapters/aws/selected-store.README.md)
are tested by the existing source-check command. Local v1 remains unchanged;
these new conformance records also refuse every claim of execution authority.
