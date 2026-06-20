# AGENTS.md

## Purpose

This repo is governed by a layered agentic harness. Keep this file small. Do not add domain-specific or procedural rules here.

## Before Acting

0. Skip steps 1-7 if i start a chat with 'ignore chat start'
1. Follow `.agentic/00.chat/workflows/chat-start.md`.
2. Use the current branch’s `commitLogs/<session>/README.md` session metadata as the first source of truth.
3. Do not reclassify unless the session metadata is missing, incomplete, or marked `unknown`.
4. Load the workflow listed in the session metadata.
5. Follow that workflow’s required gates before editing files.
6. Stop when repo state, branch state, task ownership, classification, workflow choice, or governance coverage is ambiguous or absent.
7. Missing governance is a stop condition. If a required action, recovery path, workaround, or substitution is not governed by the current workflow, gate, script, or standard, stop before acting. Explain the governance gap and ask whether to update the harness instead of improvising.
8. Follow shared git approval rules before commits or destructive actions; never push, delete branches, rewrite history, discard work, or overwrite work without explicit user approval.
9. Default mode is read-only. Do not create, edit, move, delete, stage, commit, or format files unless the user explicitly grants write permission for this chat.

## Operating Layers

* `.agentic/00.chat/` governs chat lifecycle, including chat sessions, chat worktrees, session logs, chat refresh, chat closeout, cleanup, shortcuts, and chat reporting.
* `.agentic/shared/` governs cross-layer process primitives, including git approval rules, handoff, deployment process, and context compaction.
* `.agentic/01.harness/` governs changes to the agentic harness itself.
* `.agentic/education/` governs educational resources derived from repo work.
* `.agentic/aws/` governs AWS infrastructure, environments, runtime operations, and cloud deployment targets.
* `.agentic/product/` governs Kanbien product/code work.

## Source of Truth

* Session state: current branch’s `commitLogs/<session>/README.md`
* Chat lifecycle process: `.agentic/00.chat/`
* Shared operating process: `.agentic/shared/`
* Harness maintenance process: `.agentic/01.harness/`
* Education resources process: `.agentic/education/`
* AWS infrastructure and operations process: `.agentic/aws/`
* Product/code process: `.agentic/product/`
* Executable checks: `scripts/`
* Human documentation: `docs/`
* Code: `src/`
* Tests: `tests/`
* Commit/task logs: `commitLogs/`

## Size Rule

Keep `AGENTS.md` under 80 lines unless a harness ADR approves a larger router. If a rule only applies to frontend, auth, migrations, git, deployment, testing, documentation, or chat/session setup, move it into the relevant workflow, skill, gate, or standard.
