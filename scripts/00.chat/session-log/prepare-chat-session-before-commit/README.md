<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.session-log.prepare-chat-session-before-commit.readme
  version: 1
  status: active
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

This helper coordinates those checks. It is deliberately read-only. If anything
is missing, it stops before the commit boundary so the human and agent can fix
the session state rather than writing an incomplete audit trail.

## Checks

The script runs shared gates first:

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
- `## ADR Disposition` must have a real entry
- `ADR needed` must be `yes` or `no`
- when `ADR needed: yes`, the ADR path must point to an existing file under
  `docs/harness/architecture/adrs/`
- when `ADR needed` is `yes` or `no`, the reason must be present

## What This Does Not Do

- It does not stage files.
- It does not create the task commit.
- It does not record the task commit in the session log.
- It does not checkpoint session-log bookkeeping.
- It does not decide whether an ADR is needed.

## Typical Sequence

1. Run this readiness check.
2. Commit the task changes.
3. Run `record-chat-commit` with the task commit SHA and summary.
4. If only the session log is dirty, run `checkpoint-chat-session-log`.

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
