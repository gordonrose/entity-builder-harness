<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.sources
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Record the course baseline scope provenance and evidence limits.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# Sources, scope and limits

[Course start](README.md)

## Exactly what “before” and “after” mean

The course inventory was frozen on **31 October 2026**, before adding the course files. It includes the union of tracked changes against the baseline and untracked, non-ignored paths in the active October 27 chat worktree. No rename collapsing is used.

- Git baseline: `d94da2b9401d3abcf86618b5d497e9b93903490a`.
- Worktree: `/home/owner/projects/.chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-10-27-08-24-walk-through-core-server-persistence-observability-step-by-s-1803338414`.
- Branch: chat/2026-10-27-08-24-walk-through-core-server-persistence-observability-step-by-s.
- Scope: 584 paths; 408 modified existing files, 176 added files, zero deleted paths; 187 directly containing folders.
- Sorted path-list SHA-256, newline after each path: `c811b7fc9cce8d0fa762b501b3361281c90d57f50997bce1db522787d31d290b`.

Every file lesson carries its baseline/current source hash in a course-source-sha256 comment. These are comparison identities, not a security signature or semantic proof. For added files, before is explicitly absent. No content from raw qualification logs, environment files, credentials, SQL responses or provider identities is reproduced in the teaching examples.

The baseline already contains earlier observability and repo functionality. The course describes this worktree delta, not the entire lifetime of the repo. It does not claim that a new diagnostic file means a newly invented feature.

The education files themselves are intentionally outside the 584-path scope; otherwise writing a lesson would recursively create another file needing a lesson. All new course artifacts live under this course directory; the existing lesson-plan index is also updated with a navigation link. That education-index edit is course bookkeeping, not an additional diagnostic implementation file. No pre-existing runtime, test, gate or deployment file needs to change to teach the course.

## The original scope, by root

| Root | Changed file paths |
| --- | ---: |
| `.agentic` | 14 |
| `.github` | 1 |
| `AGENTS.md` | 1 |
| `apps` | 11 |
| `bin` | 2 |
| `commitLogs` | 4 |
| `docs` | 6 |
| `infra` | 37 |
| `package-lock.json` | 1 |
| `packages` | 102 |
| `platform` | 240 |
| `products` | 1 |
| `scripts` | 164 |

“Folder” in this course means a directory directly containing at least one of those paths. Ancestor directories are explained through the architecture/module introductions and navigation. Subfolders each have their own indexed lesson.

## Primary sources

- [Controlling diagnostics plan](../../../../.agentic/shared/plans/implementation/governed-diagnostic-coverage.md): the top completion/scope disposition controls; older dated handoffs preserve history and may say work was then pending.
- [Session record](../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/README.md): decisions, timings, mistakes, approvals, proof references and continuity.
- [Ownership decision](../../../03.product/adrs/0043-own-diagnostic-contracts-in-runtime-code.md): why runtime code owns the vocabulary and the harness governs adoption.
- [Source-matched owner reviews](../../../../scripts/repo/diagnostic-coverage/reviews.v1.json): scope, reviewed sources, proving checks and technical limitations. A partial/support label must be read with its actual reason; it is not automatically a defect.
- [Executable check catalog](../../../../scripts/repo/check-selection/checks.yml): actual commands, dependencies, selected inputs and execution stages.
- All 584 current source links and their individual changes in [the complete file checklist](file-index.md).

## What the final local proof says

These are retained project results, not checks rerun while writing this course. Exact reports and identities are recorded in the controlling plan/session.

| Evidence | Recorded result | What it does not prove |
| --- | --- | --- |
| Final registered correction focus | 5/5 passed; 551.533373 seconds total | Every future implementation or all live conditions |
| Final impact-selected local gate | 101/101 local results; zero findings; 19 executed, 82 matching receipts reused; 650.072098 seconds | That all 101 ran afresh, or that live deployment passed |
| Actual local bootstrap image qualification | Passed; 99.259 seconds | Published custody or target alignment |
| Actual local persistence image build | Passed; 177.533 seconds | A deployed service accepting this image |
| Actual persistence container / disposable TLS PostgreSQL qualification | Passed; 37.938 seconds | Live RDS/role/network/secret injection correctness |
| Local PostgreSQL integration | Passed; 24.662 seconds in the recorded earlier engine run | Every provider failure or current production state |
| Disposable portability bootstrap/suite | Passed; 175.804 / 179.415 seconds | Installation into the active repo or an upstream release |

The retained earlier full-gate attempt with 100/101 passing remains a failed attempt. A stale positive provider fake was corrected; strict absence classification was not weakened. The final image correction added missing diagnostic module COPY entries and omission counterexamples. These mistakes are part of the teaching material, not hidden by the later passing proof.

## Remaining work is not erased

The user assigned live deployment checks to a different chat. The four core-server identities are bootstrap-target-alignment, persistence-target-alignment, bootstrap-acceptance and persistence-acceptance. They require the proper artifact/custody identity and fresh target evidence. The local images are not published custody receipts.

Further kanbien-platform-specific deployment/AWS runtime work is excluded because that target is being deprecated. Shared Platform libraries remain part of this work. Some already-completed compatibility changes to platform-shell entrypoints remain in the inventory; exclusion was not an instruction to discard them.

Wider imported llm-workbench diagnostics remain upstream follow-up. Six bounded imported-file corrections were approved and completed locally; that exception did not authorize patching every imported file. Five maintenance command owners and the dormant rule taxonomy debt remain recorded in the controlling plan. This course does not start them.

General security capabilities and telemetry implementation findings remain in their respective follow-on plans. Certificate/TLS diagnostic migration is not a new cookie/session/CSRF/secret-rotation/tenant-isolation implementation. Metric diagnosis is not a metrics-platform rebuild.

## Technical limits to remember

- A deadline observation does not prove cancellation or cleanup completion.
- A failed invocation does not prove a remote side effect did not happen.
- Unknown cause remains unknown when only uncontrolled prose is available.
- Optional, disabled, unavailable or suppressed diagnostics do not establish complete or remote delivery.
- A checked shape does not establish producer truth, and a matching review hash does not establish good judgment.
- SDK failures swallowed inside private code cannot be claimed as observed public-boundary failures.
- Internal process-log observations are not automatically retained in every historical task receipt.
- Operator notification attestation and actual provider delivery evidence are different things.

## Reconciliation when source changes later

Open the affected lesson and compare its recorded source hash/current source. If implementation has changed, record the mismatch in learning notes and re-read the actual diff before teaching that before/after story. Do not edit the baseline, silently omit the file, or assume old proof applies to new bytes.
