<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.script.session-log.prepare-chat-session-before-commit.readme
  version: 3
  status: active
  created_on: "2026-06-19"
  updated_on: "2026-10-26"
  layer: 00.chat
  domain: session-log
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the chat commit-boundary readiness check before task commits.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.session-log.prepare-chat-session-before-commit
    path: scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
  - id: chat.script.session-log.prepare-chat-session-before-commit.smoke-test
    path: scripts/00.chat/session-log/prepare-chat-session-before-commit/smoke-test.sh
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
-->
# Prepare Chat Session Before Commit

`script.sh` is the readiness gate for task commits in a governed chat.

It does not create a commit. It checks whether the current chat session has
enough process context, clean enough staged state, and complete enough session
metadata for a task commit to proceed.

## Mental Model

Before a task commit, the harness needs two kinds of confidence:

- the Git state is appropriate for committing from this chat worktree
- the session log has enough context to explain the work after the commit lands

The default mode coordinates those checks without changing task files. Its
`--before-verification` mode performs the bounded lifecycle preparation needed
before final verification. If anything is missing, either mode stops before the
commit boundary so the human and agent can fix the state rather than writing an
incomplete audit trail.

## Checks

In its default commit-boundary mode, the script runs shared gates first:

- write-location check
- commit prerequisite check
- commit-log deletion check
- deterministic process drift check for staged files
- metadata header check for newly staged artifacts
- governed script command drift check
- optional repository extension hook at `scripts/repo/commit-gates/script.sh`,
  or `CHAT_REPO_COMMIT_GATES_SCRIPT` when the repo needs to override the hook

Then it validates the current chat session:

- current branch must be a `chat/*` branch
- matching session log must exist
- `## Initial Intent` must be recorded
- `## Decisions Made` must have a real entry
- `## Context Hygiene` must have a real entry
- `## ADR Disposition` must have a real entry
- `ADR needed` must be `yes` or `no`
- when `ADR needed: yes`, each ADR path must point to an existing file under a
  governed ADR root such as `docs/<numbered-layer>/adrs/`, or a legacy
  transition root such as `docs/<track>/architecture/adrs/`
- when `ADR needed` is `yes` or `no`, the reason must be present

## What This Does Not Do

- It does not stage files.
- It does not create the task commit.
- It does not record the task commit in the session log.
- It does not checkpoint session-log bookkeeping.
- It does not decide whether an ADR is needed.

## Typical Sequence

1. Before final verification or any image qualification, run:

   ```bash
   bash scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh \
     --before-verification --paths <task-path> [<task-path>...]
   ```

   It updates required lifecycle metadata for the named task paths, validates
   structure, refreshes the affected metadata index, and emits the focused
   selector plan and records its exact input identities when this repository
   supplies a selector. Run the selected final verification only after this command.
   It is idempotent and does not stage files or rebuild images. Owner-generated
   material selected by that plan must be refreshed by its owner before final
   verification; the quarantined RAG source-review records remain explicit
   maintenance work and are not rewritten by ordinary task preparation.
2. Stage only approved task paths in the committing worktree.
3. Run the default readiness check. It validates the staged prepared state and
   reuses only evidence whose selected input identity still matches.
4. Commit the task changes only if this check passes.
5. Run `record-chat-commit` with the task commit SHA and summary.
6. If only the session log is dirty, run `checkpoint-chat-session-log`.
7. If continuing the same chat into a new phase, run `/compact` so Codex keeps
   the commit summary, decisions, unresolved issues, and context hygiene instead
   of raw intermediate output.

If the agent cannot stage because Git metadata is not writable in its sandbox
and the human will commit in a terminal, the agent should provide the same
sequence to the human: stage approved paths, run this readiness check, then
commit only if the check passes.

## Repository Extensions

`00.chat` does not own repository-specific, domain-specific, product, or
deployment commit checks. A repository may provide a neutral extension hook at:

```bash
scripts/repo/commit-gates/script.sh
```

If present, this helper runs it after portable chat and harness drift checks.
Set `CHAT_REPO_COMMIT_GATES_SCRIPT` to a different repository-relative path
when a consumer repo needs to override the default hook. The older
`LLM_WORKBENCH_OPTIONAL_COMMIT_GATE` variable remains a compatibility alias.

The preparation hook declares `writes-files` because a repository extension may
run authorized local tests that create temporary outputs. Invoke preparation
through the governed runner only with the current task’s applicable local-test
authorization (`--approved-action`); it is not an always-approved read-only gate.
This metadata does not authorize committing, provider access or publication.
Package qualification remains owned by its package workflow. Commit readiness
does not rebuild an image; it defers package-stage proof and preserves its
immutable receipt requirements.
