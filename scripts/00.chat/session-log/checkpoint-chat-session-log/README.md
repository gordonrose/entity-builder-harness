<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain when and how chat session-log bookkeeping is checkpointed as its own commit.
domain: session-log
portability: llm-workbench-required
used_by:
  - scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh
  - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
-->

# Checkpoint Chat Session Log

`script.sh` commits only the current chat session log as a narrow bookkeeping
checkpoint.

It exists because task work and session-log bookkeeping are intentionally
separate. A task commit should contain the actual implementation, documentation,
or harness change. After that commit is recorded into the session log, the log
itself becomes dirty. This helper creates the follow-up bookkeeping commit when
the session log is the only remaining change.

## Mental Model

The session log is part of the audit trail, but it is not the task change
itself.

The usual rhythm is:

1. make and commit the task change
2. run `record-chat-commit` to write that task commit into the session log
3. run `checkpoint-chat-session-log` to commit the session-log update by itself

That gives the Git history two clean boundaries: one for the work, and one for
the chat record about the work.

## Safety Rule

This helper only checkpoints when the dirty state is limited to the current
chat session log.

It refuses to run if:

- any unrelated file is staged
- any unrelated file is dirty
- the current branch is not a `chat/*` branch
- the matching session log cannot be found

That refusal is the point. A bookkeeping checkpoint should never quietly include
task files, unrelated docs, generated output, or another chat's log.

## Usage

```bash
checkpoint-chat-session-log.sh [--dry-run] [message]
```

- `--dry-run`: show what would be committed without staging or committing.
- `message`: optional commit message. The default is
  `chore(session): checkpoint chat log`.

## What This Does

- derives the session id from the current `chat/*` branch
- finds the matching session log
- verifies there are no unrelated staged or dirty files
- stages only the current session log
- commits only that session log

## What This Does Not Do

- It does not record a task commit in the session log.
- It does not inspect whether the task commit itself was good.
- It does not push anything.
- It does not merge anything.
- It does not allow mixed bookkeeping and task changes.

## Compatibility

The governed runner still approves the old path:

```bash
scripts/shared/git/checkpoint-chat-session-log.sh
```

That file is now a compatibility wrapper around the canonical implementation.
Checklists should keep using the approved shared path until the governed runner
allowlist policy is migrated.
