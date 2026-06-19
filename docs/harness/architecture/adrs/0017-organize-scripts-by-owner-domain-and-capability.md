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
- compatibility wrappers:
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
  `scripts/shared/chat/generate-commit-log-summary.sh`, and
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
