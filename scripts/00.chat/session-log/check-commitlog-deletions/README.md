<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.session-log.check-commitlog-deletions.readme
  version: 1
  status: active
  layer: 00.chat
  domain: session-log
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain how the harness protects commit logs that record committed work.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.session-log.check-commitlog-deletions
    path: scripts/00.chat/session-log/check-commitlog-deletions/script.sh
  - id: chat.script.session-log.check-commitlog-deletions.smoke-test
    path: scripts/00.chat/session-log/check-commitlog-deletions/smoke-test.sh
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
    path: docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
-->
# Check Commit Log Deletions

`script.sh` blocks staged deletion of chat commit logs that contain durable work
history.

It protects the audit trail. Empty or unsaved session logs can be removed by an
intentional cleanup commit, but logs that record completed work or are marked for
retention should not disappear as part of an ordinary task commit.

## Mental Model

Commit logs are not scratch files once they record committed work. They explain
why a chat branch existed, what was decided, which commits landed, and what
follow-up may still matter.

This gate watches the staged deletion set. If a staged deletion targets
`commitLogs/**/README.md`, the script inspects the version from `HEAD` and
decides whether that log is protected.

## Protected Logs

A deleted log is blocked when the `HEAD` version contains either:

- recorded commit metadata, such as `latest_commit_sha`
- an entry in `## Commits` that names a commit SHA
- a retention marker such as `retain: yes`, `preserve: true`, or an
  `agentic-retain-log` style marker

## Allowed Deletions

Deletion is allowed when the staged log appears empty of committed work and has
no retention marker. This supports cleanup of abandoned startup logs or other
bookkeeping-only artifacts.

## What This Does Not Do

- It does not delete files itself.
- It does not restore protected logs.
- It does not inspect non-README files.
- It does not judge whether an allowed deletion is wise.
- It does not replace human review of cleanup commits.

## Validation

`smoke-test.sh` creates a throwaway repo with three logs:

- one with a recorded commit
- one empty log
- one retained log

It verifies that recorded and retained logs are blocked, while an empty-only log
deletion passes.

Run the canonical smoke test with:

```bash
bash scripts/00.chat/session-log/check-commitlog-deletions/smoke-test.sh
```

## Compatibility

The old shared path remains available:

```bash
scripts/00.chat/session-log/check-commitlog-deletions/script.sh
```

That file is now a compatibility wrapper around the canonical implementation.
