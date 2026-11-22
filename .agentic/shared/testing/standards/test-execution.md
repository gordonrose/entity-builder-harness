<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.testing.standard.execution
version: 6
status: active
created_on: "2026-11-07"
updated_on: "2026-11-22"
layer: 06.shared
domain: testing
disciplines: [agentic, architecture, sre]
kind: standard
purpose: Separate fast development feedback from enforced commit, integration and deployment proof.
portability: {class: source-only, targets: []}
used_by:
- id: shared.testing.workflow.write-and-verify-tests
  path: .agentic/shared/testing/workflows/write-and-verify-tests.md
- id: repo.check-selection.readme
  path: scripts/repo/check-selection/README.md
-->
# Test execution

Applies to features, Core, Platform, adapters and deployment tooling. Test types
and physical ownership remain governed by test-design and owner requirements.
Scheduling does not grant execution effects or change what constitutes proof.

## Three feedback loops

| Boundary | Required behavior |
| --- | --- |
| Development | Inspect change impact; execute the relevant declared fast local checks. Report integration pending. |
| Commit | Enforce the existing commit-boundary selection against staged inputs and matching preparation. |
| Integration | Enforce the complete affected selection on the candidate containing the integration base. Missing or failed proof blocks promotion. |

Do not treat every conversational step as integration completion. A task may be
implemented with focused proof passed and integration verification pending; name
the remaining check IDs and blocking stage. This does not mean fully verified,
release-ready or accepted. Before integration, complete the required selection.
Package and live proof remain with their existing deployment owners.

## Decision ownership and enforcement

The existing scripts/repo/check-selection/checks.yml is the only check catalog.
Its boundary, stage, effects, inputs, runtime and dependency declarations remain
authoritative. Optional feedback metadata records development suitability,
expected seconds, isolation and a concise rationale. The selector validates all
declared feedback metadata. Absence means unclassified for development, not an
exemption from any gate. Adopt owners incrementally; do not silently relabel all
existing checks or remove dependencies to meet a timing target.

`cadence: candidate` is the default: the check is part of ordinary affected
candidate selection. `cadence: hygiene` is for broad regression or unusual-
environment checks that are not evidence required for every candidate. A
hygiene check is selected automatically only at integration when one of its
declared inputs changes; it is deferred at commit and may be run explicitly.
Its declared inputs define the changes that invalidate its result. Classifying
a check as hygiene does not waive its failure, remove it, or create a periodic
runner. A scheduled hygiene service needs separately governed authority.

Every catalogue check must declare its scheduling boundary explicitly. `commit`
means the check is required before a commit; `integration` means it is required
when the complete affected candidate is prepared for merge or promotion. There
is no implicit commit fallback: an omitted or unknown boundary is a catalogue
error and stops selection.

Development selection must retain the full impact obligations in its report.
Only declared development-local checks may execute; unmet prerequisites remain
blocking. CI, staged/prepared verification, aggregate execution and main
promotion may not opt into development selection. Existing explicit --checks
calls prove requested identities only, never complete change impact.

## Keep verification machines separate

Scheduling boundary answers *when* a check is required. Its verification
machine answers *what decision* the check supports. Do not use one machine as a
shortcut for another:

| Machine | Decision it supports | What it must not silently replace |
| --- | --- | --- |
| Local qualification | Whether the current source and artifact candidate are fit to freeze. | Provider configuration, deployment recovery or deployed-runtime proof. |
| Deployment and recovery | Whether the environment can accept, apply, observe or recover that frozen candidate. | Local source tests or acceptance proof. |
| Deployed-runtime proof | Whether the deployed identity provides the required smoke or acceptance behaviour. | Deployment repair or local qualification. |
| Periodic hygiene | Whether broad, cross-cutting or unusual-environment regression remains healthy. | Candidate evidence merely because it is available. |

Keep their owners, effects, receipts and reports separate. A deployment route
consumes matching local qualification evidence; it does not rerun local tests
as an undocumented prerequisite. A runtime smoke observes the deployed identity
and must not silently repair it. Hygiene is selected only from its declared
inputs or an explicitly governed periodic or maintenance request. A change that
needs more than one machine records each required result separately.

For a new or materially changed check, name the risk it addresses, its machine,
invalidating inputs and consuming boundary in existing owner documentation,
catalogue rationale or the task record. Do not add a second scheduler, cache or
proof store when an existing owner can carry that information.

## Cost, reuse and isolation

Aim for ordinary feature feedback near one minute and checkpoint feedback in a
few minutes. Expected durations are advisory estimates, not timeouts, permission
to skip checks, or claims already achieved. Measure planning, runtime identity,
compilation/execution and reuse before optimising. Report estimate overruns.
Preserve matching-input cache validation and original failures. Diagnose misses
before narrowing inputs; exact consumer and invalidation fixtures must reject
lost coverage. Scheduling metadata never turns a failed or stale result green.

Choose a wall-clock budget before a final broad run and record its terminal
outcome as **passed**, **failed** or **incomplete**. A timeout, cancellation or
lost terminal result is incomplete evidence, not a passing run and not proof
that the implementation failed. It is a maintenance signal: retain focused
proof that did finish, then split, measure or reclassify the broad owner through
its normal governance rather than repeatedly stretching the budget or silently
dropping the check.

Final focused evidence must invoke a registered catalogue command or that
command's declared runner wrapper. A file whose name ends in `test` is not
evidence that tests ran: importing or directly evaluating a test module counts
only when that file is itself the registered executable entry point and its
runner dispatch is verified. Exploratory direct commands remain useful, but
must be labelled exploratory and cannot replace registered final proof.

Source-aware selection may narrow a runtime suite only from declared ownership
and statically resolvable dependency evidence. Dynamic, unresolved, malformed,
unowned or unsafe relationships must retain the broader suite. Performance
pressure never authorises guessing that an unproved dependency is unaffected.

Expensive final verification uses stable inputs. An independently authorised
isolated checkout may verify a pinned checkpoint while development continues;
its outputs, dependencies and services must not share mutable state with the
development checkout. Later changes require their affected proof. No commit or
auxiliary worktree is authorised by this standard alone.

## Delivery budget accounting

The [shared completion standard](../../standards/require-change-completion.md#reuse-simplicity-and-normal-delivery)
owns the normal-delivery budget. Per-check `expected_seconds` and current
`budget_exceeded` fields describe estimate overruns only; they do not measure
or enforce that end-to-end requirement. Process/job timeouts are safety limits,
not delivery-duration claims.

Measure total wall-clock time from the first delivery invocation through
required acceptance. Include dependency installation, planning, compilation,
packaging, required checks, rollout, readiness and smoke verification, even
when they run in different jobs. Do not start the clock after expensive
preparation, add overlapping stage durations as if serial, or reset it after
an interruption. Identify the source, artifact and resumed attempt boundaries.

Show genuinely provider-controlled setup/wait intervals and separately selected
additional regression work alongside the total. An exclusion requires observed
boundaries and a reason; overlapping useful repo work cannot also be subtracted.
Cold dependency setup, duplicated work, local orchestration and manual repair
are not exclusions. Required checks cannot be relabelled optional regression
to make a delivery pass. Where time cannot be attributed reliably, report it
as unclassified rather than inventing an exclusion.

Report functional outcome separately from budget outcome: met, missed or not
established. A successful package, partial run or missing terminal timing cannot
establish successful delivery. Preserve unfinished/failed stages. Reports are
observations, not execution journals or trusted proof. Extend existing report
owners and reference their evidence rather than introducing a parallel runner
or importing reports into the local cache. Until connected timing is implemented,
explicitly report the end-to-end budget as not established.

## Result storage

- Trusted reusable local receipts remain in worktree Git metadata under
  agentic-local-checks; arbitrary reports cannot seed that cache.
- Executed local runs retain a safe, run-specific report and readable summary
  under ignored .cache/test-runs/. This is disposable observation, not an
  execution journal or live-operation reservation. Do not overwrite prior runs.
- Session commit logs retain durable bounded outcomes and evidence references;
  preserve a sanitised final snapshot when disposable evidence would be lost.
- CI reports belong to CI artifacts when upload is configured. Package/live
  receipts remain with their existing custody and target evidence owners.

Bind reports to source revision and actual input fingerprints, including dirty
working-tree inputs. Distinguish passed, failed, blocked, deferred and reused
results. Never retain raw child stdout/stderr, environment values, submitted
records or provider responses. Failed report retention remains explicit without
rewriting original check outcomes. Historical proof is not fresh target proof.

For supported structured child reports, retain bounded findings through the
producer's existing finite-code projection, bound to the registered command
owner. Preserve only recognised input locations, never arbitrary child paths,
messages or evidence URLs. The existing runner-owned run report is the evidence
reference. Unsupported, absent, invalid, oversized or failed diagnostic
processing must be explicit; none changes the child's original exit status.
Combined results identify the actual failed or stale dependency checks from
the runner's dependency graph, not identities supplied by child output.
Adding a producer format requires its owning projection and actual-caller
privacy/preservation tests; schema-shaped JSON alone is not trusted detail.

No scheduler, nightly execution or new live mutation authority is introduced.
