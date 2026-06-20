# AGENTS.md

## Purpose

This repo is governed by the llm-workbench chat harness. Keep this file small.
Do not add project-specific or procedural rules here.

## Before Acting

0. Skip steps 1-7 if the user starts a chat with `ignore chat start`.
1. Follow `.agentic/00.chat/workflows/chat-start.md`.
2. Use the current branch's `commitLogs/<session>/README.md` session metadata
   as the first source of truth.
3. Do not reclassify unless the session metadata is missing, incomplete, or
   marked `unknown`.
4. Load the workflow listed in the session metadata.
5. Follow that workflow's required gates before editing files.
6. Stop when repo state, branch state, task ownership, classification,
   workflow choice, or governance coverage is ambiguous or absent.
7. Missing governance is a stop condition. If a required action, recovery path,
   workaround, or substitution is not governed by the current workflow, gate,
   script, or standard, stop before acting.
8. Follow shared approval rules before commits or destructive actions; never
   push, delete branches, rewrite history, discard work, or overwrite work
   without explicit user approval.
9. Default mode is read-only. Do not create, edit, move, delete, stage, commit,
   or format files unless the user explicitly grants write permission for this
   chat.

## Operating Layers

* `.agentic/00.chat/` governs chat lifecycle, including chat sessions, chat
  worktrees, session logs, chat refresh, closeout, cleanup, shortcuts,
  reporting, and upstream reusable lessons.
* `.agentic/shared/` governs cross-layer process primitives, including git
  approval rules, handoff, context compaction, and upstream repo bootstrap
  standards.
* `.agentic/harness/` governs changes to the workbench harness itself.

## Source Of Truth

* Session state: current branch's `commitLogs/<session>/README.md`
* Chat lifecycle process: `.agentic/00.chat/`
* Shared operating process: `.agentic/shared/`
* Harness maintenance process: `.agentic/harness/`
* Executable checks: `scripts/`
* Human documentation: `docs/`
* Commit/task logs: `commitLogs/`

## Size Rule

Keep `AGENTS.md` short. If a rule only applies to a specific workflow,
checklist, standard, script, or install path, move it into that artifact.
