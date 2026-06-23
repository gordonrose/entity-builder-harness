# Concepts

## Chat Session

A chat session is one unit of agent-assisted work. The session log records the
task, branch, workflow, commits, and estimated transcript metrics.

Session logs live under:

```txt
commitLogs/<year>/<month>/<day>/<session>/README.md
```

## Chat-Owned Worktree

Implementation work happens in a chat-owned Git worktree. The root repo stays
available as the local integration console.

This lets a chat branch do real work without blocking other chats or mixing
unrelated changes.

## Governed Script

A governed script is a helper command that has a known path, metadata, and
approval boundary. The harness prefers governed scripts over ad hoc shell
commands when behavior should be repeatable.

## Local Main Refresh

Chat branches should be refreshed from local `main` before promotion. The
harness separates rehearsal from apply so conflicts can be inspected before
the branch is changed.

## Commit Log

The commit log is the work ledger for a chat. It is not a changelog for the
whole project. It records what happened in one session and preserves the
evidence needed for closeout, reporting, and future recovery.
