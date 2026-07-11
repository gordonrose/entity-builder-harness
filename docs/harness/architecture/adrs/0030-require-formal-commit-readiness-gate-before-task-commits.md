<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.adr.0030-require-formal-commit-readiness-gate-before-task-commits
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the decision to require the formal chat commit readiness gate before task commits.
portability:
  class: source-only
  targets: []
used_by:
- id: chat.checklists.before-commit
  path: .agentic/00.chat/checklists/before-commit.md
- id: chat.script.session-log.prepare-chat-session-before-commit
  path: scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
- id: chat.script.session-log.prepare-chat-session-before-commit.readme
  path: scripts/00.chat/session-log/prepare-chat-session-before-commit/README.md
-->
# ADR 0030: Require Formal Commit Readiness Gate Before Task Commits

## Status

Accepted.

## Context

Governed chat work often ends with the user creating the Git commit in their
own terminal. That may happen because the agent sandbox cannot write Git
metadata, because the user wants to inspect the staged state directly, or
because the workflow deliberately leaves commit authority with the human.

This creates a governance risk: the agent may provide a `git commit` command
after running only focused validation, while the formal chat commit readiness
gate has not checked the actual commit boundary.

The formal readiness gate coordinates write-location checks, session-log
completeness, ADR disposition, staged deterministic-process checks, staged
artifact-header checks, governed script drift checks, commit-log deletion
checks, and repository extension gates.

If that gate is skipped, a task commit can enter the repo without the same
audit and safety checks the harness expects.

## Decision

Before a task commit proceeds, the formal chat commit readiness gate must pass
in the committing worktree:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh
```

When the agent can stage approved paths, it should stage only approved paths
and run the gate before giving the final commit command.

When the agent cannot stage because Git metadata is not writable in its
sandbox, but the user will commit in a terminal, the agent should provide the
safe terminal sequence in order:

1. stage only the approved paths;
2. run the formal readiness gate;
3. commit only if the gate passes.

The agent must report the gate result. If the gate fails, the task is not ready
for commit until the failure is fixed or a governed recovery path is chosen.

Focused checks remain useful while developing a slice, but they do not replace
the formal commit-boundary gate.

## Consequences

Terminal commits remain compatible with sandbox limits and human review, but
they keep the same governed readiness boundary as agent-created commits.

The session log ADR disposition and context hygiene must be current before the
commit command is treated as ready.

Staged process and metadata checks are evaluated against the actual commit
candidate when staging is possible in the committing environment.

Future changes to commit readiness should update the formal gate and its
checklist rather than relying on ad hoc assistant memory.

## Non-Goals

This ADR does not authorize commits without explicit user approval.

This ADR does not authorize pushes, merges, rebases, branch deletion, history
rewrite, discarded work, or destructive Git actions.

This ADR does not make focused test runs unnecessary during implementation.
