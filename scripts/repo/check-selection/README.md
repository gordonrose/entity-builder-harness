<!-- agentic-artifact:
schema: agentic-artifact/v3
id: repo.check-selection.readme
version: 10
status: active
created_on: '2026-10-24'
updated_on: "2026-11-09"
layer: 06.shared
domain: validation
disciplines:
- agentic
- security
- sre
kind: documentation
purpose: Explain supported impact discovery, focused checks, evidence reuse and permission-preserving
  stage boundaries.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: repo.command.check-selection
  path: scripts/repo/check-selection/script.sh
-->
# Focused Repository Verification

## Development feedback

Use one selector for three different decisions: quick development feedback,
existing staged commit verification and complete affected integration proof.
The [execution standard](../../../.agentic/shared/testing/standards/test-execution.md)
owns those boundaries. [checks.yml](checks.yml) owns each command, its inputs,
prerequisites and optional `feedback` declaration. No separate profile catalog,
scheduler or nightly suite is introduced.

[script.py](script.py) still owns impact selection and execution;
[execution_policy.py](execution_policy.py) validates scheduling metadata and
projects safe observations. [local_cache.py](local_cache.py) retains trusted
proof and its existing identity/revalidation rules.

```bash
# Read-only decision inventory; unclassified checks are shown too.
bash scripts/repo/check-selection/script.sh --inventory --explain
# Inspect full affected obligations before executing anything.
bash scripts/repo/check-selection/script.sh --paths apps/entity-smoke/features/test-entity/domain/services/update-test-entity.ts --development --explain
# Run only declared fast local checks; report all other obligations pending.
bash scripts/repo/check-selection/script.sh --paths apps/entity-smoke/features/test-entity/domain/services/update-test-entity.ts --development --execute-local --explain
# At a stable checkpoint, complete the affected local integration selection.
bash scripts/repo/check-selection/script.sh --paths apps/entity-smoke/features/test-entity/domain/services/update-test-entity.ts --execute-local --explain
```

`--development` requires path-scoped local integration selection. It cannot
combine with explicit checks, aggregate-member execution, staged/preparation or
CI modes. The full impact graph remains visible; only checks whose complete
command aliases declare `feedback.development: true` may run. Undeclared or
deferred prerequisites still block consumers. Success exits zero with verdict
`partial`, coverage `integration-pending`; it never means integration passed.
Without this flag, existing gate behavior is unchanged. `--checks` still proves
only requested identities. There is no automatic time-based skipping.

Feedback has exactly four fields: `development` (boolean), `expected_seconds`
(integer 1–86400), `isolation` (`worktree` or `disposable-fixture`) and `rationale`
(bounded single-line explanation). Development eligibility requires a local
non-aggregate command. Invalid declarations fail closed. Missing declarations
remain unclassified, not exempt. The pilot declares entity-smoke, DynamoDB and
PostgreSQL connection fixtures eligible; server/product assembly and payload
qualification stay integration-only. Other capabilities are not silently opted
in. These local persistence tests do not contact AWS or prove real databases.

JSON output adds `execution_policy`: owners, selection basis, dependencies,
declared inputs, estimates, overrun observations and pending IDs. `--explain`
renders a readable summary. Estimates are advisory command budgets, not timeouts
or total wall-time guarantees; planning and runtime identity have separate
timings in `execution_summary`. `not_selected` explains absent declared pilot
checks. Supported impact still depends on declared consumers; no heuristic can
prove an undeclared dependency safe.

Executed runs create private, unique ignored
`.cache/test-runs/<UTC-time-and-random-id>/report.json` and `summary.txt` files.
The report binds revision and actual source/runtime fingerprints, including dirty
inputs, and keeps statuses, reuse/invalidation observations and finite findings.
It excludes raw child output and runtime/environment values. Unsafe retention
paths produce a finding without rewriting check outcomes. Reports are disposable
observations: they cannot seed cache reuse or qualify integration/live proof.
No automatic retention cleanup is added. Trusted receipts remain in private
worktree Git metadata; durable bounded outcomes/evidence belong in the session
commit log. Do not copy raw private-cache reports into chat logs.

`entity-smoke-runtime` dispatches `app:entity-smoke:check`: the current feature
typecheck (including nullable/enum/branded-ID assertions), runtime compilation
and existing source-led runner. Tests remain under the app's themed/type folders.
The package compiler and runner are reused; no feature test framework is added.

## Full impact and integration

This repository extension connects existing scope declarations, artifact
`used_by` references and workspace package dependencies to existing checks. It
uses `20-scopes/scope-index.yml` for discovery and the generic scope validators
for health, secrets and persistence applicability. It does not infer unsupported
consumers or treat incomplete coverage as a pass.

Diagnostic adoption also discovers ordinary executable code independently of
deployment scopes. `diagnostic-adoption` runs at commit boundaries;
`diagnostic-runtime-contracts` runs at integration. Source-matched reviews in
`scripts/repo/diagnostic-coverage/reviews.v1.json` name registered local checks;
their sources and tests select those checks through this same selector. These
reviews add selection edges, never arbitrary commands or execution permission.

`bootstrap-payload-regression` and `persistence-payload-regression` exercise
compiled package imports and deliberately broken payloads locally, before any
container stage. Their export-map checks include shared security dependencies;
they do not replace actual container or live deployment qualification.

```bash
bash scripts/repo/check-selection/script.sh --paths platform/adapters/aws/persistence/postgresql/src/index.ts --json
bash scripts/repo/check-selection/script.sh --paths platform/adapters/aws/persistence/postgresql/src/index.ts --execute-local --json
bash scripts/repo/check-selection/script.sh --all --stage deploy --json
bash scripts/repo/check-selection/smoke-test.sh
```

`--staged` selects both sides of renames and reports deleted paths.
`--all` selects all discovered scope requirements. `--paths` accepts exact
repository-relative changed paths, including paths deleted by the change.
Directory input matching observes slash boundaries, so `src-extra` cannot
silently match an input declared as `src`.

The default is a plan, with pending checks and explicit later-stage obligations.
For focused verification of an already identified registered unit, use:

```bash
bash scripts/repo/check-selection/script.sh --checks platform-server-runtime --execute-local --json
```

`--checks` is mutually exclusive with impact, staged and CI selection. It proves
only the requested identities, not completeness of change impact. Unknown,
duplicate or scope-parameter-dependent requests fail before execution. The
normal stage, effects, contract validation and private-cache rules still apply.
Failed commands and arbitrary reports never create passing evidence.

The [shared change-completion standard](../../../.agentic/shared/standards/require-change-completion.md#verification-and-stage-boundaries)
owns when registered units must be used and the regression expectations for new
or changed aggregates. This guide owns their command syntax. Use impact selection
to identify the full obligations; use `--checks` for appropriate focused units,
then complete impact-selected verification against the final inputs. Do not add
a separate aggregate invocation when matching selected proof already covers it.

Diagnostic verification requests `diagnostic-base-runtime` (the separate
`diagnostic-catalog-readers` and eleven complete registered package units),
`platform-server-runtime` and `kanbien-platform-runtime`. The shell source
preflight requests those same server/product units plus
`platform-shell-payload`, which runs the existing compiled image-runtime check.
Both default aggregate commands retain their complete original coverage. A
focused registered pass can therefore seed the same receipt later used by either
aggregate. Direct npm runs remain useful exploratory checks but do not seed it.
Aggregate proofs bind the consumed catalog and selector; changed child contracts
invalidate an aggregate without invalidating unchanged sibling unit contracts.
Package units bind their whole owned package tree (including new tests and
tsconfig files), root npm scripts/lockfile, transitive workspace dependencies and
actual installed dependency closure. They do not bind unrelated deployment
fixtures merely because a former aggregate grouped them. Catalog compilation
and legacy subject-bound checks retain their wider actual consumer inputs.
Container and live qualification remain separate obligations.

`members` is the authoritative aggregate membership. `focused_prerequisites`
names workload-specific input conditions and required check identities; the
selector also follows affected package/metadata consumers. It validates unknown
references, cycles, stage/effect incompatibility and ambiguous scope instances,
runs applicable focused units first and checks their current identities again
before broad execution. An aggregate wrapper still executes; it requests its
catalog members through `--aggregate-members`, and consumes matching child
receipts rather than repeating their commands. Its dispatch branch is validated
against undeclared executable children. Child contracts bind parent receipts.
Caller-inherited focused prerequisites remain ordering/freshness gates, not
extra inputs to an unchanged member command's proof. A standalone member receipt
therefore remains reusable inside an applicable aggregate; the aggregate still
binds its own declared focused prerequisites and consumed member proofs.

Explicit broad/default requests require the existing matching preparation
record. `--task-paths` can identify that task, but cannot replace or disagree with
its prepared context or input identities. Missing/stale context fails before
execution; leaf focused/exploratory units remain independently usable. Impact,
staged and CI/all selection derive their context from the selected inputs.
During nested execution only, a random reference identifies a runner-written
binding in the existing private preparation record. It binds allowed members,
catalog, task paths and source/preparation identities, preserves lifecycle data,
is revalidated in the child and is removed/restored on completion or failure.
Environment paths alone and expired bindings grant no readiness authority.
Nested execution currently requires the Linux runner's `/proc` process-birth
identity. Missing/malformed process identity fails closed before writing a new
active binding; PID reuse and dead runners cannot qualify one. This does not
claim macOS support for nested execution. Ordinary planning stays read-only.
The staging deployment workflow explicitly prepares its fixed registered shell
roots on its fresh installed checkout and proves the focused payload first.
Its original npm checks retain lifecycle hooks; their pre-existing repetition
with the later source preflight remains a distinct command-identity boundary.

The default scheduling boundary is `integration`. `--boundary commit` requires
only checks scheduled for commit preparation. The catalogue's `boundary` field
is independent of `stage`, `effects` and evidence class: an integration check
does not acquire network, provider or publication permission. CI retains its
protected command and uses the integration default. Direct local-main promotion
runs the same integration selection in the clean chat worktree after confirming
that it contains the base; failure or branch/input drift blocks promotion.
Promotion also reconciles the independent current delivery census before receipt
reuse, as CI does. The structural selector regression binds repository-wide
governance, metadata and script owners because its fixtures inspect the real graph.
`--execute-local` runs only catalogued local checks whose effects agree with the
command metadata and contain only `read-only` and/or `writes-files`. This flag
requires task authorization for local execution. It never executes package,
provider, secret, publication or acceptance operations, even when `--stage`
selects a later boundary. Commands are argument arrays passed without a shell.

Checks with identical resolved argv execute once, provided their effects, stage
and evidence class agree. A scope proof must bind its program, image and applicable
target/scope, or use a genuine generic command capability. Generic owners declare
an adjacent `check-capability.yml` binding their artifact identity, exact argv,
contract schema and consumed context parameters. Appending a context argument to
an unrelated fixed command cannot make it generic. The canonical runnable
program's `local_proof` must remain a selected local check.

Ordinary `--execute-local` runs, including the repository commit hook, reuse only
successful local runner receipts under the current worktree's private Git
metadata directory, `agentic-local-checks`. The report exposes `local_report_path`
for the latest JSON report. Writes are atomic, directory/file ownership and
permissions are checked, and symlink cache paths are refused. The boundary trusts
the local operating-system user who owns that Git metadata; it is neither signed
portable evidence nor protection from that same user editing their own cache.
`--evidence` reports are explicitly rejected as authority and never create cache
receipts. Failed, pending, uncertain and nonzero results never qualify reuse.
Each report has an `execution_summary` naming reused, executed and deferred
checks, selected check IDs and elapsed/execution seconds. A rerun after a previous trusted receipt records concrete
`invalidated_checks` reasons: verified input bytes changed, the declared runtime
identity changed, or the verification contract changed. These reasons explain
why a new local run is needed; they never make an old receipt acceptable.

`execution_summary.timings` separates planning, source/semantic fingerprinting,
runtime identity, receipt validation, direct command wall time and remaining
overhead. The buckets are disjoint within one report. Nested summaries explain
executed/reused children; their elapsed time is already inside the wrapper's
wall time and must not be added again. JSON progress on stderr contains only
event/check identity, status and completed/total counts, never argv, environment
values or child output. By default stdout is one machine-readable JSON report;
`--explain` opts into the readable view instead.

Diagnostic reviews bind relevant semantic entries and their actual sources,
tests and definitions, not every other review merely through a shared ledger.
The whole ledger still receives structural validation. Ledger changes compare
both sides against HEAD or the validated CI/promotion base, retaining deleted
owners' obligations and rejecting malformed/unavailable comparisons. Initial
adoption with no ledger in a valid base legitimately selects all added owners.

`--record-preparation` stores the exact selected preparation identities in the same
private worktree cache, without executing checks. The chat pre-verification
sequence uses it before final verification. `--require-preparation` is limited
to `--staged`: it rejects a relevant commit-boundary check until its recorded
identity matches, reporting `verification-preparation-missing` or
`verification-preparation-inputs-changed` and the affected check IDs before
any execution. This prevents late lifecycle metadata edits from silently
turning commit preparation into a new verification cycle.
Preparation identities bind declared input bytes and the complete verification
contract. Deferred integration checks do not probe installed runtimes during
commit preparation; runtime identity is established at their verification
boundary. The lifecycle owner retains exact prepared artifact hashes/modes in
that same private preparation record, allowing unchanged content to retain its
date across UTC rollover. Modified content must be prepared again.

Impact references and `repository_inputs` mappings select obligations; they are
not automatically consumed proof inputs. Audited checks declare `scope_inputs:
false` and their complete `inputs`, including implementation helpers. Structural
scope validators and legacy subject-bound checks retain scope references until
their inputs are explicitly audited. Command/capability identity, runtime/config
bindings and transitive workspace package dependencies remain part of audited
proofs. Metadata consumer edges still select affected checks; consumed schemas
and contracts must be declared as proof inputs.

`--reuse-from-worktree <path>` reads only the private cache of a registered
worktree sharing the same Git common directory. It validates receipt contents
against their key and compares the target's own inputs, contract and runtime.
Matching local receipts are retained in the target's existing cache; arbitrary
JSON reports and package/live proofs remain ineligible. The refresh apply owner
uses this route before removing a clean preflight worktree. Repository-installed
tools bind their relative location plus actual bytes, modes and versions;
external installations retain absolute identity. A final identity sweep rejects
a pass invalidated by a later command in the same invocation.

Each receipt binds the complete catalog definitions of its selected check and
all aliases sharing that command. An unrelated check definition does not revoke
that receipt. Catalogue-only changes compare check contracts with staged HEAD
or the validated CI/promotion base. Existing scope and repository mappings select
the changed identities; an unchanged sibling on the same repository rule is not
selected solely by that contract change. Checks that explicitly consume the catalog still bind its complete
bytes. Every invocation validates the current catalog and selection; a catalog
change during planning or execution makes the invocation uncertain. This drift
barrier is separate from the reusable proof identity, so the next fresh plan can
reuse unaffected evidence. Staged execution still requires the catalog authority
to match the staged version.

The key includes relevant input bytes and file modes, transitive package and
metadata dependencies, owner capability, argv/effects/stage/evidence class,
resolved declared Bash/Python/PyYAML/Node/npm/TypeScript identities, declared
configuration paths and hashes of declared environment values. Missing optional
configuration files are fingerprinted, so creating one invalidates proof. The
catalog declares the supported tool/config/environment boundary; this is not
universal inference of arbitrary external tools, imports or machine settings.
Node checks explicitly declare `runtime.node_packages` (an empty list is valid
for checks using only built-in modules). The installation fingerprint resolves
each package's required, optional and peer dependency closure using bounded
Node resolution, and hashes actual installed paths, bytes and permissions.
Optional absence is recorded. In-repository workspace links include link and
target identity plus target contents; external targets, cycles and unsupported
file types fail closed. Removing or changing installed `pg`, `@types/node` or a
transitive package invalidates proof even when the lockfile is unchanged. No
installation or dependency code execution occurs during this fingerprint.
Inputs and runtime identities are recomputed after execution; changes during a
check yield uncertain evidence. Source revision is provenance, not a reuse key:
unrelated commits and session records do not invalidate unchanged local proof.

Runtime declarations share tool/PyYAML measurements and original installed-package
frames only inside a runner-owned in-memory measurement window. Package resolution
and declared environment remain specific to each declaration; replaying frames
does not change the installation digest. Retained package frames are bounded at
128 MiB; exceeding that budget falls back to measuring the uncached trees again.
This is not a persistent or timestamp-based identity cache.

Consecutive receipt-only checks can share that window. Before any actual command,
the runner discards it and freshly revalidates the command's prerequisites,
catalog and own inputs/runtime, including after receipt lookup. It discards the
window again after the command and independently before the final sweep. A later
mutation can revoke an earlier pass; receipt reuse cannot authorize execution
from an old snapshot. Nested runners own separate windows and do not trust a
parent's in-memory measurements.

`--staged` rejects relevant unstaged or untracked selected inputs before running
or reusing checks. This prevents proving working-tree bytes while committing
different index bytes. Unrelated unstaged work remains untouched. Later-stage
commands are always deferred or reported as owning-controller gaps; symbolic
runtime receipt parameters are not required during local checks and cannot be
used to execute those commands here.

Supported source impact uses explicit scope inputs and workspace package
edges. Artifact metadata consumer relationships are followed transitively for
both scope checks and repository check mappings. The catalog may declare
`dormant_impact_roots`: metadata `used_by` edges into or out of those roots are
excluded from ordinary impact traversal, while direct repository-input mappings
continue to select the owning checks when that dormant surface's code or
authoritative definitions change. Correcting ordinary governance prose within
a dormant root does not activate its runtime checks; the mandatory document
checks still apply. For example, fixing a command reference in a retained RAG
plan must not build the RAG runtime. Explicit `--checks` and `--all` requests
still include the requested dormant checks. Deleted inputs are treated
conservatively because their former headers cannot be read. Authoritative schemas,
contracts and configuration need executable coverage; an unmapped definition is
`changed-input-uncovered`. Ordinary prose and nonexecutable session records
remain covered by their mandatory metadata/process checks. Scope requirements
cannot omit mandatory inventory/runnable checks, and unsupported impact is
reported explicitly.

The repository commit hook adds inventory coverage and focused local checks.
The preparation wrapper and repository hook both declare their local-test write
effects so the governed runner requires applicable execution approval.
The portable chat hook remains the sole owner of staged header validation,
deterministic process drift and governed command drift; these three checks are
not repeated here. No checker commits or stages files.

The regression suite creates a second dependency-bearing synthetic scope under a
disposable target. Existing generic validators accept its valid persistence
non-applicability. The same selector discovers it and executes its local proof
without a target name in generic code; missing/unsupported proof requirements,
wrong program/image binding, unsupported generic arguments, unsafe effects, stale evidence and unclassified impact fail closed. A temporary repository exercises the actual commit hook twice for reuse, a relevant unstaged mismatch, and rerun after staging. The fixture also proves unrelated revision changes retain valid proof.


## Runner verification ownership

`check-selection-mechanics` proves runner behavior with disposable repositories;
`check-selection-repository-contracts` inspects actual catalog, package and scope
wiring. The latter retains conservative repository and installed-package inputs
because its real planning tests consume them. Mechanics instead binds the exact
copied bootstrap scope, provider helper, validators, runner/commit/refresh support
and tools it actually consumes; it has no installed application/SDK packages.
Temporary fixtures do not make those real source dependencies disappear.

The existing complete `check-selection-regression` identity and default
`smoke-test.sh` command remain an aggregate of both components and five registered
owner suites. The Python compatibility entrypoint also retains historical
`SelectionTests.method` focused calls, including recursive process-isolation
tests. Shared `test_support.py` contains fixture helpers, never test methods.
Collection discovery rejects unassigned or shadowed executable tests and tests
loaded into more than one component. Original test retention is audited against
the pre-split snapshot in the implementation plan, not a runtime chat-plan input.

```bash
bash scripts/repo/check-selection/script.sh --checks check-selection-mechanics check-selection-repository-contracts --execute-local --json
bash scripts/repo/check-selection/smoke-test.sh --unit mechanics
bash scripts/repo/check-selection/smoke-test.sh --unit repository-contracts
```

Direct unit commands are exploratory; use registered commands for reusable final
proof. The full default aggregate requires the normal prepared task and reuses
matching component receipts. Do not run it again after an impact-selected pass
already supplies the same complete proof.

Five fixture-only owner units expose the existing lifecycle metadata, header,
session preparation, local-merge and main-refresh smoke scripts. The fixed wrapper
branches accept no arbitrary command/path or extra argument. Those child scripts
retain broader fixture Git-operation metadata; source review confirms their Git
operations and cleanup target only self-created temporary roots. The wrapper's
existing writes-files boundary is not permission for real repository staging,
commits, branch/worktree operations or cleanup, nor a general local-effects
exception. The runner allowlist is unchanged. Their input closures bind the child
scripts and copied/read support files; parent aggregate results bind all members.

Selection mappings and evidence inputs have different jobs. Ordinary HTTP source
changes select runtime and required real-wiring proof, not mechanics or unrelated
owner suites. Runner/suite contract changes select the full aggregate. Relevant
fixture/helper changes select their consumers; an unrelated runtime body neither
selects nor invalidates mechanics. Initial worktree impact against the old
catalog/review baseline can legitimately be broader than a future ordinary edit.
Exact selection is tested through real catalog/metadata/review rules; pure-plan
tests use bounded tool identities and reference-only proof fingerprints while
retaining the real catalog-authority fingerprint, without executing child suites
or changing the actual selection wiring. Existing execution regressions prove real tools,
source/runtime/contract invalidation, reuse and failed-child propagation.


The delivery inventory regression imports `test_support.py` directly and creates
`FixtureSupport`, not an executable runner test class. Foreign spec-based imports
of the retained smoke facade still bootstrap sibling imports and expose the known
`selection` alias. An isolated external-directory import test forbids subprocess
launches, proving imports cannot silently execute the complete suite.
