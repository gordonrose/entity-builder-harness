# Chat Commit Workflow

## Purpose

Own chat task commits, session-log commit recording, and narrow session
bookkeeping checkpoints.

## Required Gates

Before committing approved task work, follow:

```txt
.agentic/00.chat/checklists/before-commit.md
```

## Rules

- Use the current branch session log as the first source of truth.
- Task commits must run from the chat-owned worktree recorded in the current
  session log.
- Do not create a task commit without explicit user approval in the current
  chat.
- Stage only approved repository-relative paths.
- Preserve unrelated user changes in a dirty worktree.
- Do not push, merge to `main`, rebase, delete branches, rewrite history,
  discard work, or perform destructive actions unless separately approved.
- After a task commit, record it with:

```bash
bash scripts/shared/git/record-chat-commit.sh <sha> <message> <summary> [adr-impact]
```

- The recorder must estimate chat-token metrics from `CHAT_TRANSCRIPT_BYTES`,
  `codex_session_log_path`, or a discovered Codex JSONL session log. It must not
  use the session log file size as a chat token source.
- If no transcript source can be supplied or discovered, stop before recording
  the commit unless the current workflow explicitly permits
  `ALLOW_MISSING_CHAT_TRANSCRIPT_METRICS=yes` for a legacy or recovery case.

<!-- deterministic-check: allow reason="checkpoint helper enforces narrow file scope; prose states the human-readable policy" -->
If recording a user-approved task commit leaves only session bookkeeping dirty,
the prior chat write permission authorizes creating a session-log checkpoint
commit without another prompt:

```bash
bash scripts/shared/git/checkpoint-chat-session-log.sh
```

<!-- deterministic-check: allow reason="checkpoint helper enforces file scope; prose states the human-readable policy" -->
The checkpoint commit is bookkeeping only and must contain no files except the
current chat session log. Stop and ask if any other path is staged, unstaged, or
would be committed.

## Migration Notes

The executable scripts still live under `scripts/shared/` for compatibility.
That path is implementation location, not ownership.

When migrating script paths later, preserve:

- explicit user approval before task commits
- current session log as commit evidence
- ADR disposition before task commit
- checkpoint scope limited to the current session log
- no automatic task staging outside approved paths
