<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.testing.standard.execution
version: 1
status: active
created_on: "2026-11-07"
updated_on: "2026-11-09"
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

Development selection must retain the full impact obligations in its report.
Only declared development-local checks may execute; unmet prerequisites remain
blocking. CI, staged/prepared verification, aggregate execution and main
promotion may not opt into development selection. Existing explicit --checks
calls prove requested identities only, never complete change impact.

## Cost, reuse and isolation

Aim for ordinary feature feedback near one minute and checkpoint feedback in a
few minutes. Expected durations are advisory estimates, not timeouts, permission
to skip checks, or claims already achieved. Measure planning, runtime identity,
compilation/execution and reuse before optimising. Report estimate overruns.
Preserve matching-input cache validation and original failures. Diagnose misses
before narrowing inputs; exact consumer and invalidation fixtures must reject
lost coverage. Scheduling metadata never turns a failed or stale result green.

Expensive final verification uses stable inputs. An independently authorised
isolated checkout may verify a pinned checkpoint while development continues;
its outputs, dependencies and services must not share mutable state with the
development checkout. Later changes require their affected proof. No commit or
auxiliary worktree is authorised by this standard alone.

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

No scheduler, nightly execution or new live mutation authority is introduced.
