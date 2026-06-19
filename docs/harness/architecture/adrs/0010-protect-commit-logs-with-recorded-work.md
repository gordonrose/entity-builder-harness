# 0010 Protect Commit Logs With Recorded Work

Status: accepted
Date: 2026-06-16

## Context

Chat branch cleanup may remove empty branches and their empty session logs, but
commit logs are also the durable record of work that produced commits. A branch
can be superseded, merged, abandoned, or retired while its commit log remains
valuable historical evidence.

The harness needs to distinguish empty unsaved session logs from logs that
record committed work. Branch cleanup must not stage deletion of logs that
contain real commit records.

## Decision

Add a commit gate:

```bash
bash scripts/00.chat/session-log/check-commitlog-deletions/script.sh
```

The gate inspects staged deletions matching `commitLogs/**/README.md` and reads
the deleted version from `HEAD`. It blocks deletion when the log has a
non-empty `latest_commit_sha`, a real `## Commits` entry, or an explicit
retention marker. It allows deletion of empty, unsaved session logs.

Shared commit preparation runs this gate before allowing a commit.

## Consequences

Cleanup can still remove abandoned empty sessions. Commit logs that represent
committed work survive branch cleanup unless a future workflow adds a separate,
explicit archival/delete process with stronger approval.
