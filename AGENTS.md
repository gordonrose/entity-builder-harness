# AGENTS.md

## Purpose

This repo is governed by a layered agentic harness. Keep this file small. Do not add domain-specific or procedural rules here.

## Before Acting

0. Skip steps 1-7 if i start a chat with 'ignore chat start'
1. Follow `.agentic/shared/workflows/chat-start-interview.md`. 
2. Use the current branch’s `commitLogs/<session>/README.md` session metadata as the first source of truth.
3. Do not reclassify unless the session metadata is missing, incomplete, or marked `unknown`.
4. Load the workflow listed in the session metadata.
5. Follow that workflow’s required gates before editing files.
6. Stop if repo state, branch state, task ownership, classification, or workflow choice is ambiguous.
7. Follow shared git approval rules before commits or destructive actions; never push, delete branches, rewrite history, discard work, or overwrite work without explicit user approval.
8. Default mode is read-only. Do not create, edit, move, delete, stage, commit, or format files unless the user explicitly grants write permission for this chat.

## Operating Layers

* `.agentic/shared/` governs chat sessions, git process, branching, commits, handoff, deployment process, and context compaction.
* `.agentic/harness/` governs changes to the agentic harness itself.
* `.agentic/product/` governs Kanbien product/code work.

## Source of Truth

* Session state: current branch’s `commitLogs/<session>/README.md`
* Shared operating process: `.agentic/shared/`
* Harness maintenance process: `.agentic/harness/`
* Product/code process: `.agentic/product/`
* Executable checks: `scripts/`
* Human documentation: `docs/`
* Code: `src/`
* Tests: `tests/`
* Commit/task logs: `commitLogs/`

## Size Rule

`AGENTS.md` must stay between 150 and 300 lines. If a rule only applies to frontend, auth, migrations, git, deployment, testing, documentation, or chat/session setup, move it into the relevant workflow, skill, gate, or standard.
