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
      verify-local-convergence/
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

Closeout command batch result:

- canonical implementation:
  `scripts/00.chat/closeout/build-closeout-prompt/script.sh`
- command compatibility wrapper:
  `scripts/shared/chat/commands/close.sh` remains executable so the dispatcher
  can continue listing and invoking `chat-command close` from the shared command
  directory until command discovery is migrated.

New-session command batch result:

- canonical implementation:
  `scripts/00.chat/startup/start-new-chat/script.sh`
- command compatibility wrapper:
  `scripts/shared/chat/commands/new.sh` remains executable so the dispatcher can
  continue listing and invoking `chat-command new` from the shared command
  directory until command discovery is migrated.

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
  `scripts/shared/git/smoke-test-chat-worktree-session.sh` remains executable
  while callers migrate to the canonical startup smoke-test path.
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
