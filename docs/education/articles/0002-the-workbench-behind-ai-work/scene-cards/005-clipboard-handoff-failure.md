# Scene Card: Clipboard Handoff Failure

## Source

`commitLogs/2026/jun/18/2026-06-18-16-11-clipboard-copy-fallback/README.md`

## What Happened

Chat startup created the branch, worktree, and session log, then failed when
the WSL clipboard bridge returned a `clip.exe` error. The fix made clipboard
copy a best-effort convenience with retry and printed fallback.

## Human Pressure

The user could reasonably think startup failed even though the important setup
had already succeeded.

## Visible Objects

- branch
- chat-owned worktree
- session log
- clipboard command
- printed prompt fallback

## Why It Matters

This scene distinguishes core process from convenience layer. Good harnesses do
not confuse a failed handoff nicety with failed setup.

## Use In Article

Late supporting example or optional humor beat.
