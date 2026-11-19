# AGENTS.md

## Purpose

This repo is governed by a layered agentic harness. Keep this file small. Do not add domain-specific or procedural rules here.

## Repo Purpose

The strategic objective of this repo is to build a software factory that can generate software in a modular and predictable way based on chat based instructions.

The long term goal is for those instructions to be delivered via MCP to a deployed software builder that can modify individual apps on multiple types of cloud vendor infrastructure. The vast majority of code changes will be done via functionality, rather than improvisded by the LLM. 

When this project is finished LLMs will act as interfaces and classifiers, but should not impelement new code - that should be done deterministically through existing code.

No short term implementation work should work against this goal unless explicitly approved.

## Before Acting

<!-- llm-workbench:start -->
## llm-workbench

Follow `.agentic/00.chat/workflows/chat-start.md` at the start of each chat.
Use `commitLogs/<session>/README.md` as the first source of truth for chat
lifecycle, branch, worktree, context-packet references, commits, and metrics.

- **Session continuity:** If this conversation already has a session log with a
  recorded `worktree`, that is the active worktree for this chat. Use it as the
  explicit working directory for all repository commands. Never treat the
  tool-provided cwd, the root checkout, a branch name, or a date change as a
  new session.

- Create or resolve a new chat worktree only when this conversation has no
  active recorded worktree or the user explicitly requests a new chat or
  worktree. If the active session is unclear, stop and ask; do not create one.

<!-- deterministic-check: allow reason="prompt routing may be manual or repo-specific; no universal script can decide whether a context router exists" -->
Do not assign the whole chat a durable layer, mode, or workflow. When a prompt
needs layer, mode, workflow, corpus, or rule context, use the current user
request, this repo's assistant instructions, and any repo-provided context
router if one exists.

Default mode after governed chat-start bootstrap is read-only until the user
explicitly grants write permission for task files.

<!-- llm-workbench:end -->

For coding changes, use `.agentic/shared/workflows/verify-diagnostic-coverage.md`
alongside the owning implementation workflow.

- Stop when repo state, branch state, task ownership, prompt-level routing, chat lifecycle state, or governance coverage is ambiguous or absent.
- Missing governance is a stop condition. If a required action, recovery path, workaround, or substitution is not governed by the current workflow, gate, script, or standard, stop before acting. Explain the governance gap and ask whether to update the harness instead of improvising.
- Follow shared git approval rules before commits or destructive actions; never push, delete branches, rewrite history, discard work, or overwrite work without explicit user approval.

## Operating Layers

* `00.chat` (`.agentic/00.chat/`) governs chat lifecycle, including sessions, worktrees, session logs, chat refresh, closeout, cleanup, shortcuts, and reporting.
* `01.harness` (`.agentic/01.harness/`) governs the agentic harness itself, including routing, workflows, standards, gates, agents, and artifact metadata.
* `02.rag-rulebook` (`.agentic/02.rag-rulebook/`) is dormant RAG/rulebook machinery retained for explicit maintenance and future rebuilding; it must not add automatic work to platform, harness, or ordinary commit flows.
* `03.product` (`.agentic/03.product/`) governs product and runtime contract work, including current `packages/core/` and `platform/contracts/` surfaces.
* `04.deploy` (`.agentic/04.deploy/`, `.agentic/aws/`, `infra/04.deploy/`, `docs/04.deploy/`, and `scripts/04.deploy/`) governs deployment, infrastructure, runtime operations, and CI/CD surfaces. `.agentic/04.deploy/` is the provider-neutral layer; `.agentic/aws/` remains the active AWS-specific governance surface during its planned transition.
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

Keep `AGENTS.md` under 100 lines unless a harness ADR approves a larger router. If a rule only applies to frontend, auth, migrations, git, deployment, testing, documentation, or chat/session setup, move it into the relevant workflow, skill, gate, or standard.

## Effiency Rule
Each change made to the repo should attempt to reduce tech debt, bloat and quality debt as part of the implementation.

All changes must be assessed against a risk of duplication, or missed opportunities for reuse. 

When updating our repo, every effort should be made to find existing code and/or instructions, rules, or checks that may confuse or contradict newly planned instructions. Changes must account for any such contradictory/confusing content when planning and performing work on the repo.

Under no circumstance must workload-specific or scope specific checks, tests, machinery be built for situations that will likely be reusable scenarios moving forward, given the strategic goal of this repo. 

Equally, code that is no longer necessary should be removed.

Where previous implementation is recognized as being incorrect, the implementation should be refactored, corrected or replaced, superceded code and conflicting instructions should be removed, and  compatibility preserved only where there is a concrete need; not simply because the old implementation exists.