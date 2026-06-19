<!-- agentic-artifact:
owner: harness
kind: adr
purpose: Plan the migration from flat shared script folders to owner/domain/capability script layout.
domain: scripts
portability: llm-workbench-required
used_by:
  - .agentic/harness/standards/artifact-metadata-headers.md
  - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
-->

# 0017 Organize Scripts By Owner, Domain, And Capability

Status: accepted
Date: 2026-06-19

## Context

The current script tree grew while the harness was primarily solving chat
workbench problems. Many scripts live under `scripts/shared/git/`, but their
metadata now says they are owned by `00.chat` with `domain: git`.

That mismatch makes ownership harder to reason about:

- folder paths imply these scripts are shared Git primitives
- metadata says many are chat workbench lifecycle scripts
- smoke tests live far away from the scripts they validate
- future growth will add many more scripts, making flat folders harder to scan

The metadata backfill made the ownership boundary visible. The next step is to
make the folder layout match that boundary without breaking existing workflows.

## Decision

Move toward a script layout organized by:

1. real owner layer
2. domain
3. capability folder

The target shape is:

```txt
scripts/
  00.chat/
    git/
      cleanup-empty-chat-branches/
        script.sh
        smoke-test.sh
      verify-chat-ready-to-merge-local-main/
        script.sh
        smoke-test.sh
    session-log/
      record-chat-commit/
        script.sh
        smoke-test.sh
    startup/
      start-chat-session/
        script.sh
        smoke-test.sh

  harness/
    governance/
      run-governed-script/
        script.sh
        smoke-test.sh
      check-artifact-metadata-headers/
        script.sh
        smoke-test.sh
```

Keep executable capability files under `scripts/`, not under `.agentic/`,
because scripts are runnable implementation artifacts. Use metadata headers to
preserve owner/domain details inside each file.

Do not move the full tree in one change. Migrate by capability with
compatibility wrappers at old paths until workflows and downstream users are
updated.

## Migration Plan

### Phase 1: Govern The Layout

- Add or update the metadata header standard to name capability folders as the
  preferred long-term shape.
- Teach bootstrap/audit scripts to understand both old paths and capability
  folders.
- Require moved scripts to keep metadata headers at the new path.
- Keep old paths as wrappers that delegate to new capability scripts.

### Phase 2: Pilot One Capability

Pilot with `cleanup-empty-chat-branches` because it has:

- clear `00.chat` ownership
- `domain: git`
- a public alias under `scripts/chat/`
- a shared implementation under `scripts/shared/git/`
- a matching smoke test

Target pilot shape:

```txt
scripts/00.chat/git/cleanup-empty-chat-branches/
  script.sh
  smoke-test.sh
```

Compatibility paths remain:

```txt
scripts/chat/cleanup-empty-chat-branches.sh
scripts/shared/git/cleanup-empty-chat-branches.sh
scripts/shared/git/smoke-test-cleanup-empty-chat-branches.sh
```

The wrappers must be thin, metadata-tagged compatibility scripts.

Pilot result:

- canonical implementation:
  `scripts/00.chat/git/cleanup-empty-chat-branches/script.sh`
- canonical smoke test:
  `scripts/00.chat/git/cleanup-empty-chat-branches/smoke-test.sh`
- compatibility wrappers:
  `scripts/shared/git/cleanup-empty-chat-branches.sh` and
  `scripts/shared/git/smoke-test-cleanup-empty-chat-branches.sh`
- public alias preserved:
  `scripts/chat/cleanup-empty-chat-branches.sh`

Second pilot result:

- canonical implementation:
  `scripts/00.chat/command/dispatcher/script.sh`
- canonical smoke test:
  `scripts/00.chat/command/dispatcher/smoke-test.sh`
- capability README:
  `scripts/00.chat/command/dispatcher/README.md`
- retired shared compatibility wrappers:
  `scripts/shared/chat/chat-command.sh` and
  `scripts/shared/chat/smoke-test-chat-command.sh`
- public alias preserved:
  `scripts/chat/chat-command.sh`

Reporting batch result:

- canonical implementations:
  `scripts/00.chat/reporting/report-chat-workspaces/script.sh` and
  `scripts/00.chat/reporting/generate-commit-log-summary/script.sh`
- canonical smoke test:
  `scripts/00.chat/reporting/generate-commit-log-summary/smoke-test.sh`
- compatibility wrappers:
  `scripts/shared/chat/report-chat-workspaces.sh`,
  `scripts/shared/chat/generate-commit-log-summary.sh`
- retired shared compatibility wrapper:
  `scripts/shared/chat/smoke-test-generate-commit-log-summary.sh`
- public aliases preserved:
  `scripts/chat/report-chat-workspaces.sh` and
  `scripts/chat/generate-commit-log-summary.sh`
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  shared wrapper paths until the governed-runner path policy is migrated.

Audit batch result:

- canonical implementations:
  `scripts/00.chat/migration/audit-chat-layer-migration/script.sh` and
  `scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh`
- compatibility wrappers:
  `scripts/shared/chat/audit-chat-layer-migration.sh` and
  `scripts/shared/chat/audit-chat-bootstrap-file-set.sh`
- public alias preserved:
  `scripts/chat/audit-chat-layer-migration.sh`
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  shared wrapper paths until the governed-runner path policy is migrated.

Classification batch result:

- canonical implementation:
  `scripts/00.chat/classification/classify-task/script.sh`
- canonical fixture check:
  `scripts/00.chat/classification/classify-task/check-fixtures.sh`
- canonical fixtures:
  `scripts/00.chat/classification/classify-task/fixtures.tsv`
- compatibility wrappers:
  `scripts/shared/chat/request-initialization/classify-task.sh` and
  `scripts/shared/chat/request-initialization/check-classify-task-fixtures.sh`

Session-log executable batch result:

- canonical implementations:
  `scripts/00.chat/session-log/read-current-chat-log/script.sh`,
  `scripts/00.chat/session-log/update-chat-log/script.sh`,
  `scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh`, and
  `scripts/00.chat/session-log/record-main-refresh-conflict/script.sh`
- compatibility wrappers:
  `scripts/shared/chat/request-initialization/read-current-chat-log.sh`,
  `scripts/shared/chat/update-chat-log.sh`,
  `scripts/shared/chat/rename-current-chat-log-folder.sh`, and
  `scripts/shared/chat/record-main-refresh-conflict.sh`
- public alias preserved:
  `scripts/chat/record-main-refresh-conflict.sh`
- canonical source library:
  `scripts/00.chat/session-log/paths/lib.sh`
- source compatibility shim:
  `scripts/shared/chat/session-log-paths.sh` remains source-able for shared git,
  startup, and downstream smoke fixtures until those callers migrate in later
  batches.
- canonical worktree source library:
  `scripts/00.chat/worktree/paths/lib.sh`
- worktree source compatibility shim:
  `scripts/shared/chat/chat-worktree-paths.sh` remains source-able for shared
  startup, shared git, and downstream smoke fixtures until those callers
  migrate in later batches.
- canonical worktree helper:
  `scripts/00.chat/worktree/ensure-chat-worktree/script.sh`
- worktree helper compatibility wrapper:
  `scripts/shared/chat/ensure-chat-worktree.sh` remains executable for shared
  startup and downstream smoke fixtures until those callers migrate in later
  batches.
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  `rename-current-chat-log-folder.sh` wrapper path until the governed-runner
  path policy is migrated.

Transcript and metrics batch result:

- canonical transcript implementations:
  `scripts/00.chat/transcript/discover-codex-session-log/script.sh` and
  `scripts/00.chat/transcript/register-codex-session-log/script.sh`
- canonical metrics implementation:
  `scripts/00.chat/metrics/estimate-chat-cost/script.js`
- compatibility wrappers:
  `scripts/shared/chat/discover-codex-session-log.sh`,
  `scripts/shared/chat/register-codex-session-log.sh`, and
  `scripts/shared/chat/estimate-chat-cost.js`
- direct callers migrated:
  `scripts/00.chat/session-log/record-chat-commit/script.sh`,
  `.agentic/00.chat/workflows/chat-start.md`, and
  `scripts/00.chat/session-log/record-chat-commit/smoke-test.sh`

Record chat commit batch result:

- canonical implementation:
  `scripts/00.chat/session-log/record-chat-commit/script.sh`
- canonical smoke test:
  `scripts/00.chat/session-log/record-chat-commit/smoke-test.sh`
- capability README:
  `scripts/00.chat/session-log/record-chat-commit/README.md`
- compatibility wrappers:
  `scripts/shared/git/record-chat-commit.sh` and
  `scripts/shared/git/smoke-test-record-chat-commit-metrics.sh`
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  `scripts/shared/git/record-chat-commit.sh` wrapper path until the
  governed-runner path policy is migrated.

Checkpoint chat session log batch result:

- canonical implementation:
  `scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh`
- capability README:
  `scripts/00.chat/session-log/checkpoint-chat-session-log/README.md`
- compatibility wrapper:
  `scripts/shared/git/checkpoint-chat-session-log.sh`
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  `scripts/shared/git/checkpoint-chat-session-log.sh` wrapper path until the
  governed-runner path policy is migrated.

Prepare chat session before commit batch result:

- canonical implementation:
  `scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh`
- capability README:
  `scripts/00.chat/session-log/prepare-chat-session-before-commit/README.md`
- compatibility wrapper:
  `scripts/shared/git/prepare-chat-session-before-commit.sh`
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  `scripts/shared/git/prepare-chat-session-before-commit.sh` wrapper path until
  the governed-runner path policy is migrated.

Check commit prerequisites batch result:

- canonical implementation:
  `scripts/00.chat/session-log/check-commit-prerequisites/script.sh`
- canonical smoke test:
  `scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh`
- capability README:
  `scripts/00.chat/session-log/check-commit-prerequisites/README.md`
- compatibility wrappers:
  `scripts/shared/git/check-commit-prerequisites.sh` and
  `scripts/shared/git/smoke-test-commit-prerequisites.sh`
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  `scripts/shared/git/check-commit-prerequisites.sh` wrapper path until the
  governed-runner path policy is migrated.

Check commit log deletions batch result:

- canonical implementation:
  `scripts/00.chat/session-log/check-commitlog-deletions/script.sh`
- canonical smoke test:
  `scripts/00.chat/session-log/check-commitlog-deletions/smoke-test.sh`
- capability README:
  `scripts/00.chat/session-log/check-commitlog-deletions/README.md`
- compatibility wrappers:
  `scripts/shared/git/check-commitlog-deletions.sh` and
  `scripts/shared/git/smoke-test-commitlog-deletions.sh`
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  `scripts/shared/git/check-commitlog-deletions.sh` wrapper path until the
  governed-runner path policy is migrated.

Check write location batch result:

- canonical implementation:
  `scripts/00.chat/worktree/check-write-location/script.sh`
- capability README:
  `scripts/00.chat/worktree/check-write-location/README.md`
- compatibility wrapper:
  `scripts/shared/git/check-write-location.sh`
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  `scripts/shared/git/check-write-location.sh` wrapper path until the
  governed-runner path policy is migrated.

Dirty worktree check batch result:

- canonical implementation:
  `scripts/00.chat/worktree/dirty-worktree-check/script.sh`
- capability README:
  `scripts/00.chat/worktree/dirty-worktree-check/README.md`
- compatibility wrapper:
  `scripts/shared/git/dirty-worktree-check.sh`
- governed runner exception:
  `scripts/shared/harness/run-governed-script.sh` still allowlists the old
  `scripts/shared/git/dirty-worktree-check.sh` wrapper path until the
  governed-runner path policy is migrated.

Recovery import batch result:

- canonical implementation:
  `scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh`
- canonical smoke test:
  `scripts/00.chat/recovery/import-active-paths-to-chat-worktree/smoke-test.sh`
- capability README:
  `scripts/00.chat/recovery/import-active-paths-to-chat-worktree/README.md`
- compatibility wrapper:
  `scripts/shared/git/stage-active-worktree-paths.sh`
- superseded compatibility runner retained for retirement review:
  `scripts/shared/git/with-chat-branch.sh`
- superseded compatibility smoke test retained:
  `scripts/shared/git/smoke-test-with-chat-branch.sh`
- governed runner update:
  `scripts/shared/harness/run-governed-script.sh` narrowly allowlists the new
  canonical recovery script path.

Main refresh status/readiness batch result:

- canonical implementations:
  `scripts/00.chat/main-refresh/show-main-update-status/script.sh`,
  `scripts/00.chat/main-refresh/check-chat-is-current-with-main/script.sh`, and
  `scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh`
- canonical smoke test:
  `scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh`
- capability READMEs:
  `scripts/00.chat/main-refresh/show-main-update-status/README.md`,
  `scripts/00.chat/main-refresh/check-chat-is-current-with-main/README.md`, and
  `scripts/00.chat/main-refresh/classify-refresh-readiness/README.md`
- compatibility wrappers:
  `scripts/shared/git/main-update-status.sh`,
  `scripts/shared/git/check-chat-branch-freshness.sh`,
  `scripts/shared/git/classify-main-refresh-dirty-state.sh`, and
  `scripts/shared/git/smoke-test-main-refresh-dirty-classifier.sh`
- direct callers migrated:
  `.agentic/00.chat/workflows/chat-refresh-from-main.md`,
  `docs/harness/architecture/adrs/0011-use-chat-owned-worktrees-for-local-convergence.md`,
  `scripts/shared/git/preflight-main-refresh.sh`, and
  `scripts/shared/git/smoke-test-main-refresh-preflight.sh`
- governed runner update:
  `scripts/shared/harness/run-governed-script.sh` narrowly allowlists the new
  canonical main-refresh status/readiness script paths while retaining old
  shared wrappers for compatibility.

Main refresh rehearse/apply batch result:

- canonical implementations:
  `scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh` and
  `scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh`
- canonical smoke test:
  `scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh`
- capability READMEs:
  `scripts/00.chat/main-refresh/rehearse-refresh-from-main/README.md` and
  `scripts/00.chat/main-refresh/apply-rehearsed-refresh/README.md`
- compatibility wrappers:
  `scripts/shared/git/preflight-main-refresh.sh`,
  `scripts/shared/git/promote-preflight-refresh.sh`, and
  `scripts/shared/git/smoke-test-main-refresh-preflight.sh`
- direct callers migrated:
  `.agentic/00.chat/workflows/chat-refresh-from-main.md`,
  `.agentic/00.chat/standards/main-refresh-conflict-types.md`, and
  `.agentic/00.chat/workflows/chat-cleanup.md`
- governed runner update:
  `scripts/shared/harness/run-governed-script.sh` narrowly allowlists the
  read-only/mutating rehearsal script path while leaving the destructive apply
  path outside the always-approved runner surface.

Local merge readiness batch result:

- canonical implementation:
  `scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh`
- canonical smoke test:
  `scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/smoke-test.sh`
- capability README:
  `scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/README.md`
- compatibility wrappers:
  `scripts/shared/git/verify-local-convergence.sh` and
  `scripts/shared/git/smoke-test-local-convergence-verifier.sh`
- direct callers migrated:
  `.agentic/00.chat/workflows/chat-promote-to-main.md`
- governed runner update:
  `scripts/shared/harness/run-governed-script.sh` narrowly allowlists the new
  canonical read-only local merge readiness verifier path while retaining the
  old shared wrapper for compatibility.

Local merge visibility batch result:

- canonical implementations:
  `scripts/00.chat/local-merge/list-active-chat-branches/script.sh` and
  `scripts/00.chat/local-merge/report-chat-branch-overlaps/script.sh`
- capability READMEs:
  `scripts/00.chat/local-merge/list-active-chat-branches/README.md` and
  `scripts/00.chat/local-merge/report-chat-branch-overlaps/README.md`
- compatibility wrappers:
  `scripts/shared/git/active-chat-branches.sh` and
  `scripts/shared/git/branch-overlap-report.sh`
- direct callers migrated:
  `.agentic/00.chat/workflows/chat-refresh-from-main.md`
- governed runner update:
  `scripts/shared/harness/run-governed-script.sh` narrowly allowlists the new
  canonical read-only local merge visibility script paths while retaining old
  shared wrappers for compatibility.

Remaining shared git inventory after commit-boundary batch:

All remaining `scripts/shared/git/*.sh` files currently declare
`owner: 00.chat`. None are classified as genuinely cross-layer shared Git
primitives by metadata. They fall into three groups:

1. Compatibility wrappers for capabilities already moved:

   - `scripts/shared/git/check-commit-prerequisites.sh`
   - `scripts/shared/git/check-commitlog-deletions.sh`
   - `scripts/shared/git/check-write-location.sh`
   - `scripts/shared/git/active-chat-branches.sh`
   - `scripts/shared/git/branch-overlap-report.sh`
   - `scripts/shared/git/checkpoint-chat-session-log.sh`
   - `scripts/shared/git/cleanup-empty-chat-branches.sh`
   - `scripts/shared/git/dirty-worktree-check.sh`
   - `scripts/shared/git/prepare-chat-session-before-commit.sh`
   - `scripts/shared/git/record-chat-commit.sh`
   - `scripts/shared/git/check-chat-branch-freshness.sh`
   - `scripts/shared/git/classify-main-refresh-dirty-state.sh`
   - `scripts/shared/git/main-update-status.sh`
   - `scripts/shared/git/preflight-main-refresh.sh`
   - `scripts/shared/git/promote-preflight-refresh.sh`
   - `scripts/shared/git/verify-local-convergence.sh`

2. Superseded isolated chat branch execution helpers retained for retirement
   review:

   - `scripts/shared/git/smoke-test-with-chat-branch.sh`
   - `scripts/shared/git/stage-active-worktree-paths.sh`
   - `scripts/shared/git/with-chat-branch.sh`

   These belong to the pre-ADR-0011 commit-boundary model. Do not migrate
   `with-chat-branch.sh` into a first-class canonical capability folder unless
   a future review finds a current workflow that still needs isolated command
   execution. Keep `stage-active-worktree-paths.sh` only as a compatibility
   adapter to the canonical recovery import. Prefer
   `scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh`
   for wrong-worktree recovery imports.

Next migration recommendation:

- Keep existing shared paths as wrappers while governed runner allowlists,
  workflow docs, and old external users still reference them.
- Run a retirement pass for superseded isolated execution helpers after command
  discovery, governed runner path policy, and bootstrap install surfaces no
  longer depend on the old path.

Compatibility wrapper retirement map:

Some old paths have more than one blocker. For example, a superseded helper can
also remain in the governed runner allowlist until that runner points at a
canonical replacement.

Governed runner canonical-surface batch result:

- `scripts/shared/harness/run-governed-script.sh --list` now advertises
  canonical `scripts/00.chat/...` paths for chat-owned capabilities.
- old `scripts/shared/...` paths remain accepted by the runner as compatibility
  inputs while existing sessions and external callers migrate.
- agent-facing examples in chat start, before-commit, shared process, command
  docs, and closeout prompt text now show canonical approved-action targets.
- governed command drift detection now scans canonical `scripts/00.chat/...`
  approval-sensitive references and recognizes multiline approved-action
  commands.

Bootstrap/install compatibility audit result:

- The bootstrap audit currently treats a path as required when it is reachable
  from installed or agent-facing seed surfaces. Required does not mean the path
  is permanently canonical.
- Public terminal aliases under `scripts/chat/` remain required because they are
  the stable human-facing command surface for a bootstrapped workbench.
- Canonical `scripts/00.chat/...` implementations are now required for the
  actual chat capabilities.
- `scripts/shared/harness/run-governed-script.sh` and the deterministic harness
  checks remain required shared process primitives, not chat wrappers.
- Several `scripts/shared/chat/...` and `scripts/shared/git/...` paths remain
  required only because seeded workflows, standards, runner compatibility, or
  public aliases still reference them.
- The audit's "validation and compatibility candidates" section is not the
  install-critical path. Those files are either smoke-test wrappers, old-path
  compatibility wrappers, or validation helpers that can be retired after their
  canonical tests and public install expectations are updated.
- `scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh` owns upstream
  workbench repository availability checks for reusable-lesson promotion.

Upstream repo availability batch result:

- canonical implementation:
  `scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh`
- capability README:
  `scripts/00.chat/upstream/ensure-llm-workbench-repo/README.md`
- compatibility wrapper:
  `scripts/shared/chat/ensure-llm-workbench-repo.sh`
- governed runner update:
  `scripts/shared/harness/run-governed-script.sh --list` advertises the
  canonical upstream path while retaining the old shared path as an approved
  compatibility input.
- direct callers migrated:
  `.agentic/harness/standards/governed-script-permissions.md`

Bootstrap compatibility classifications:

1. Public install surface to keep:

   - `scripts/chat/chat-command.sh`
   - `scripts/chat/audit-chat-layer-migration.sh`
   - `scripts/chat/cleanup-empty-chat-branches.sh`
   - `scripts/chat/generate-commit-log-summary.sh`
   - `scripts/chat/record-main-refresh-conflict.sh`
   - `scripts/chat/report-chat-workspaces.sh`

2. Shared governance primitives to keep:

   - `scripts/shared/harness/run-governed-script.sh`
   - `scripts/shared/harness/check-artifact-metadata-headers.sh`
   - `scripts/shared/harness/check-deterministic-process-drift.sh`
   - `scripts/shared/harness/check-governed-script-command-drift.sh`

3. Required old-path compatibility wrappers:

   These remain reachable from seed surfaces today, but they are not canonical
   ownership paths:

   - `scripts/shared/chat/audit-chat-bootstrap-file-set.sh`
   - `scripts/shared/chat/audit-chat-layer-migration.sh`
   - `scripts/shared/chat/chat-worktree-paths.sh`
   - `scripts/shared/chat/commands/close.sh`
   - `scripts/shared/chat/commands/new.sh`
   - `scripts/shared/chat/generate-commit-log-summary.sh`
   - `scripts/shared/chat/rename-current-chat-log-folder.sh`
   - `scripts/shared/chat/report-chat-workspaces.sh`
   - `scripts/shared/chat/request-initialization/auto-start-missing-session.sh`
   - `scripts/shared/chat/session-log-paths.sh`
   - `scripts/shared/git/active-chat-branches.sh`
   - `scripts/shared/git/branch-overlap-report.sh`
   - `scripts/shared/git/check-chat-branch-freshness.sh`
   - `scripts/shared/git/check-commit-prerequisites.sh`
   - `scripts/shared/git/check-commitlog-deletions.sh`
   - `scripts/shared/git/check-write-location.sh`
   - `scripts/shared/git/checkpoint-chat-session-log.sh`
   - `scripts/shared/git/classify-main-refresh-dirty-state.sh`
   - `scripts/shared/git/dirty-worktree-check.sh`
   - `scripts/shared/git/main-update-status.sh`
   - `scripts/shared/git/preflight-main-refresh.sh`
   - `scripts/shared/git/prepare-chat-session-before-commit.sh`
   - `scripts/shared/git/record-chat-commit.sh`
   - `scripts/shared/git/stage-active-worktree-paths.sh`
   - `scripts/shared/git/verify-local-convergence.sh`

4. Required superseded legacy paths:

   These remain required only because current documentation or compatibility
   wrappers still reference the old isolated execution model:

   - `scripts/shared/git/smoke-test-with-chat-branch.sh`
   - `scripts/shared/git/with-chat-branch.sh`

5. Validation-only compatibility candidates:

   These are not currently required by the bootstrap seed graph. Keep them
   until the corresponding canonical behavior, smoke tests, or install
   expectations are explicit enough to retire old-path wrappers:

   - `scripts/shared/chat/ensure-chat-worktree.sh`
   - `scripts/shared/chat/estimate-chat-cost.js`
   - `scripts/shared/chat/record-main-refresh-conflict.sh`
   - `scripts/shared/chat/request-initialization/check-classify-task-fixtures.sh`
   - `scripts/shared/chat/request-initialization/classify-task.sh`
   - `scripts/shared/chat/request-initialization/start-chat-session.sh`
   - `scripts/shared/git/cleanup-empty-chat-branches.sh`
   - `scripts/shared/git/promote-preflight-refresh.sh`

6. Retired validation-only chat helper wrappers:

   These old `scripts/shared/chat/...` wrappers were validation-only
   compatibility paths with direct canonical replacements. They were removed
   after confirming no operative references remained and the bootstrap audit
   stayed clean:

   - `scripts/shared/chat/discover-codex-session-log.sh` wraps
     `scripts/00.chat/transcript/discover-codex-session-log/script.sh`
   - `scripts/shared/chat/register-codex-session-log.sh` wraps
     `scripts/00.chat/transcript/register-codex-session-log/script.sh`
   - `scripts/shared/chat/request-initialization/read-current-chat-log.sh`
     wraps `scripts/00.chat/session-log/read-current-chat-log/script.sh`
   - `scripts/shared/chat/update-chat-log.sh` wraps
     `scripts/00.chat/session-log/update-chat-log/script.sh`

7. Retired validation-only smoke wrappers:

   The old `scripts/shared/git/smoke-test-*.sh` wrappers below each forward to
   a canonical `scripts/00.chat/.../smoke-test.sh` file. They were validation
   compatibility wrappers, not install-critical runtime paths, and were removed
   after confirming the bootstrap audit remained clean:

   - `scripts/shared/git/smoke-test-chat-worktree-session.sh` wraps
     `scripts/00.chat/startup/start-chat-session/smoke-test.sh`
   - `scripts/shared/git/smoke-test-cleanup-empty-chat-branches.sh` wraps
     `scripts/00.chat/git/cleanup-empty-chat-branches/smoke-test.sh`
   - `scripts/shared/git/smoke-test-commit-prerequisites.sh` wraps
     `scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh`
   - `scripts/shared/git/smoke-test-commitlog-deletions.sh` wraps
     `scripts/00.chat/session-log/check-commitlog-deletions/smoke-test.sh`
   - `scripts/shared/git/smoke-test-local-convergence-verifier.sh` wraps
     `scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/smoke-test.sh`
   - `scripts/shared/git/smoke-test-main-refresh-dirty-classifier.sh` wraps
     `scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh`
   - `scripts/shared/git/smoke-test-main-refresh-preflight.sh` wraps
     `scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh`
   - `scripts/shared/git/smoke-test-record-chat-commit-metrics.sh` wraps
     `scripts/00.chat/session-log/record-chat-commit/smoke-test.sh`

| Category | Keep Until | Paths |
|---|---|---|
| Public terminal aliases | Public/bootstrap command surface is redesigned | `scripts/chat/chat-command.sh`, `scripts/chat/audit-chat-layer-migration.sh`, `scripts/chat/cleanup-empty-chat-branches.sh`, `scripts/chat/generate-commit-log-summary.sh`, `scripts/chat/record-main-refresh-conflict.sh`, `scripts/chat/report-chat-workspaces.sh` |
| Command wrapper compatibility | Public/external callers no longer use old shared command wrapper paths | `scripts/shared/chat/commands/close.sh`, `scripts/shared/chat/commands/new.sh` |
| Governed runner compatibility acceptance | `scripts/shared/harness/run-governed-script.sh` no longer accepts old compatibility paths | `scripts/shared/chat/audit-chat-bootstrap-file-set.sh`, `scripts/shared/chat/audit-chat-layer-migration.sh`, `scripts/shared/chat/generate-commit-log-summary.sh`, `scripts/shared/chat/report-chat-workspaces.sh`, `scripts/shared/chat/rename-current-chat-log-folder.sh`, `scripts/shared/chat/request-initialization/auto-start-missing-session.sh`, `scripts/shared/git/active-chat-branches.sh`, `scripts/shared/git/branch-overlap-report.sh`, `scripts/shared/git/check-chat-branch-freshness.sh`, `scripts/shared/git/check-commit-prerequisites.sh`, `scripts/shared/git/check-commitlog-deletions.sh`, `scripts/shared/git/check-write-location.sh`, `scripts/shared/git/checkpoint-chat-session-log.sh`, `scripts/shared/git/classify-main-refresh-dirty-state.sh`, `scripts/shared/git/dirty-worktree-check.sh`, `scripts/shared/git/main-update-status.sh`, `scripts/shared/git/prepare-chat-session-before-commit.sh`, `scripts/shared/git/record-chat-commit.sh`, `scripts/shared/git/stage-active-worktree-paths.sh`, `scripts/shared/git/verify-local-convergence.sh` |
| Bootstrap/install compatibility | Bootstrap audit and public install surfaces no longer include old paths as required or validation candidates | `scripts/shared/chat/ensure-chat-worktree.sh`, `scripts/shared/chat/estimate-chat-cost.js`, `scripts/shared/chat/record-main-refresh-conflict.sh`, `scripts/shared/chat/request-initialization/check-classify-task-fixtures.sh`, `scripts/shared/chat/request-initialization/classify-task.sh`, `scripts/shared/chat/request-initialization/start-chat-session.sh`, `scripts/shared/git/cleanup-empty-chat-branches.sh`, `scripts/shared/git/promote-preflight-refresh.sh` |
| Retired validation-only chat helper wrappers | Historical references may mention old paths, but operative validation should use canonical `scripts/00.chat/...` paths | `scripts/shared/chat/discover-codex-session-log.sh`, `scripts/shared/chat/register-codex-session-log.sh`, `scripts/shared/chat/request-initialization/read-current-chat-log.sh`, `scripts/shared/chat/update-chat-log.sh` |
| Retired validation-only smoke wrappers | Historical references may mention old paths, but operative validation should use canonical `scripts/00.chat/.../smoke-test.sh` paths | `scripts/shared/git/smoke-test-chat-worktree-session.sh`, `scripts/shared/git/smoke-test-cleanup-empty-chat-branches.sh`, `scripts/shared/git/smoke-test-commit-prerequisites.sh`, `scripts/shared/git/smoke-test-commitlog-deletions.sh`, `scripts/shared/git/smoke-test-local-convergence-verifier.sh`, `scripts/shared/git/smoke-test-main-refresh-dirty-classifier.sh`, `scripts/shared/git/smoke-test-main-refresh-preflight.sh`, `scripts/shared/git/smoke-test-record-chat-commit-metrics.sh` |
| Source shim compatibility | All sourced callers import canonical `scripts/00.chat/.../lib.sh` files directly | `scripts/shared/chat/chat-worktree-paths.sh`, `scripts/shared/chat/session-log-paths.sh` |
| Superseded legacy | Retirement pass proves no bootstrap, install, recovery, or audit surface needs the old isolated execution model | `scripts/shared/git/smoke-test-with-chat-branch.sh`, `scripts/shared/git/stage-active-worktree-paths.sh`, `scripts/shared/git/with-chat-branch.sh` |
| Upstream compatibility wrapper | Public/external callers no longer use the old shared upstream helper path | `scripts/shared/chat/ensure-llm-workbench-repo.sh` |

Retirement rule:

Remove an old path only when all of these are true:

- no workflow, standard, checklist, ADR, script, command dispatcher, bootstrap
  audit, public alias, or install surface references it as the operative path
- the governed runner either allows the canonical path or no longer needs to
  run the capability
- a canonical `scripts/00.chat/...` path or an explicit public alias owns the
  behavior
- bootstrap audit reports no unclassified candidates after the removal
- any removal that deletes files is proposed as its own governed slice

Closeout command batch result:

- canonical implementation:
  `scripts/00.chat/closeout/build-closeout-prompt/script.sh`
- canonical command entrypoint:
  `scripts/00.chat/command/close/script.sh`
- command compatibility wrapper:
  `scripts/shared/chat/commands/close.sh` remains executable for old external
  callers.

New-session command batch result:

- canonical implementation:
  `scripts/00.chat/startup/start-new-chat/script.sh`
- canonical command entrypoint:
  `scripts/00.chat/command/new/script.sh`
- command compatibility wrapper:
  `scripts/shared/chat/commands/new.sh` remains executable for old external
  callers.
- dispatcher migration:
  `scripts/00.chat/command/dispatcher/script.sh` now discovers commands from
  canonical `scripts/00.chat/command/<name>/script.sh` paths instead of
  `scripts/shared/chat/commands`.

Auto-start missing session batch result:

- canonical implementation:
  `scripts/00.chat/startup/auto-start-missing-session/script.sh`
- capability README:
  `scripts/00.chat/startup/auto-start-missing-session/README.md`
- request-initialization compatibility wrapper:
  `scripts/shared/chat/request-initialization/auto-start-missing-session.sh`
  remains executable because `scripts/shared/harness/run-governed-script.sh`
  still allowlists the old approved-action path until the governed-runner path
  policy is migrated.
- validation:
  `scripts/00.chat/command/dispatcher/smoke-test.sh` covers opening-prompt
  auto-start behavior, including normal session creation and the bare `new`
  guard.

Start chat session batch result:

- canonical implementation:
  `scripts/00.chat/startup/start-chat-session/script.sh`
- capability README:
  `scripts/00.chat/startup/start-chat-session/README.md`
- canonical smoke test:
  `scripts/00.chat/startup/start-chat-session/smoke-test.sh`
- request-initialization compatibility wrapper:
  `scripts/shared/chat/request-initialization/start-chat-session.sh` remains
  executable while smoke fixtures, downstream references, and any external users
  migrate to the canonical startup path.
- smoke-test compatibility wrapper:
  `scripts/shared/git/smoke-test-chat-worktree-session.sh` was retired after
  callers migrated to the canonical startup smoke-test path.
- direct callers migrated:
  `scripts/00.chat/startup/start-new-chat/script.sh`,
  `.agentic/00.chat/workflows/chat-start.md`, and related script metadata now
  point at the canonical startup path.
- follow-up:
  Revisit `CHAT_COPY_PROMPT` after the current script organization stream. It is
  terminal handoff behavior, not the chat startup contract. Consider replacing
  or wrapping it with a clearer terminal-specific startup packet interface for
  IDE extensions and app integrations.

### Phase 3: Prove Compatibility

For the pilot:

- run the new capability script directly
- run the old shared path
- run the public `scripts/chat/` alias
- run the smoke test from the new path
- run the old smoke-test path wrapper
- run the bootstrap file-set audit
- run metadata header checks

Only after all compatibility checks pass should further moves be attempted.

### Phase 4: Batch Migrations

Migrate the remaining scripts in batches:

1. `00.chat/startup`
2. `00.chat/session-log`
3. `00.chat/reporting`
4. `00.chat/git`
5. `harness/governance`
6. `harness/metadata`
7. `harness/validation`

Each batch should keep old-path wrappers until no workflow, smoke test,
bootstrap rule, or downstream repo depends on the old path.

### Phase 5: Retire Old Paths

Only remove old compatibility paths after:

- all workflows reference new paths
- all governed runner allowlist entries reference new paths
- bootstrap audits pass without old paths
- downstream upstream repo bootstraps have been updated
- a separate explicit cleanup approval is given

## Consequences

The folder tree will become more honest:

- chat workbench scripts will live under `scripts/00.chat/`
- Git will be a domain, not a fake layer
- smoke tests can sit next to the capability they validate
- open-source extraction can copy capability folders instead of guessing across
  broad shared folders

The migration adds short-term duplication because old paths must remain as
wrappers. That cost is intentional: it protects active workflows and downstream
installers while the layout changes.

The harness will need audit updates so dependency checks understand both
current flat paths and the new capability-folder shape during migration.
