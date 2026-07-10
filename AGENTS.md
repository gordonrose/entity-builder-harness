# AGENTS.md

## Purpose

This repo is governed by a layered agentic harness. Keep this file small. Do not add domain-specific or procedural rules here.

## Before Acting

<!-- llm-workbench:start -->
## llm-workbench

Follow `.agentic/00.chat/workflows/chat-start.md` at the start of each chat.
Use `commitLogs/<session>/README.md` as the first source of truth for chat
lifecycle, branch, worktree, context-packet references, commits, and metrics.

<!-- deterministic-check: allow reason="prompt routing may be manual or repo-specific; no universal script can decide whether a context router exists" -->
Do not assign the whole chat a durable layer, mode, or workflow. When a prompt
needs layer, mode, workflow, corpus, or rule context, use the current user
request, this repo's assistant instructions, and any repo-provided context
router if one exists.

Default mode after governed chat-start bootstrap is read-only until the user
explicitly grants write permission for task files.
<!-- llm-workbench:end -->

- Stop when repo state, branch state, task ownership, prompt-level routing, chat lifecycle state, or governance coverage is ambiguous or absent.
- Missing governance is a stop condition. If a required action, recovery path, workaround, or substitution is not governed by the current workflow, gate, script, or standard, stop before acting. Explain the governance gap and ask whether to update the harness instead of improvising.
- Follow shared git approval rules before commits or destructive actions; never push, delete branches, rewrite history, discard work, or overwrite work without explicit user approval.

## Operating Layers

* `00.chat` (`.agentic/00.chat/`) governs chat lifecycle, including sessions, worktrees, session logs, chat refresh, closeout, cleanup, shortcuts, and reporting.
* `01.harness` (`.agentic/01.harness/`) governs the agentic harness itself, including routing, workflows, standards, gates, agents, and artifact metadata.
* `02.rag-rulebook` (`.agentic/02.rag-rulebook/`) governs reusable RAG and rulebook machinery, including corpora, indexing, retrieval, intent, and context packets.
* `03.product` (`.agentic/product/`) governs product and runtime contract work, including current `packages/core/` and `platform/contracts/` surfaces.
* `04.deploy` (`.agentic/aws/`, `infra/04.deploy/`, `docs/04.deploy/`, and `scripts/04.deploy/`) governs deployment, infrastructure, AWS operations, runtime operations, and CI/CD surfaces.
* `05.education` (`.agentic/education/`) governs educational resources derived from repo work.
* `06.shared` (`.agentic/shared/`) governs cross-layer process primitives, including git approval rules, handoff, context compaction, and reusable standards.

## Source of Truth

* Session state: current branch’s `commitLogs/<session>/README.md`
* Governance: the owning `.agentic/...` workflow, checklist, standard, or command surface for the current prompt
* Executable checks: `scripts/<layer>/...` and `scripts/repo/`
* Human docs and corpus material: `docs/...`
* Product/runtime contracts: `packages/core/` and `platform/contracts/`
* Deployment artifacts and checks: `infra/04.deploy/`, `docs/04.deploy/`, and `scripts/04.deploy/`
* Commit/task logs: `commitLogs/`

## Size Rule

Keep `AGENTS.md` under 80 lines unless a harness ADR approves a larger router. If a rule only applies to frontend, auth, migrations, git, deployment, testing, documentation, or chat/session setup, move it into the relevant workflow, skill, gate, or standard.
