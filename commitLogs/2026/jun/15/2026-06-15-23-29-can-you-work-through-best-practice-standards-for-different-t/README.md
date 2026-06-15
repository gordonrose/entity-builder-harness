# Chat Session: 2026-06-15-23-29 can-you-work-through-best-practice-standards-for-different-t

<!-- agentic-session
id: 2026-06-15-23-29-can-you-work-through-best-practice-standards-for-different-t
task: can you work through best practice standards for different types of files in agentic harnesses based on openAI, Anthropic, Cursor, Mistral best practices?
branch: chat/2026-06-15-23-29-can-you-work-through-best-practice-standards-for-different-t
layer: harness
mode: discovery
workflow: .agentic/harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-15T22:29:30Z
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_tokens:
-->

## Initial Intent

can you work through best practice standards for different types of files in agentic harnesses based on openAI, Anthropic, Cursor, Mistral best practices?

## Branch

`chat/2026-06-15-23-29-can-you-work-through-best-practice-standards-for-different-t`

## Session Log

- Session started.
- Branch created.
- Commit log initialized.

## Questions Asked

- Whether hooks, evals, templates, examples, memory, and agents are still relevant to the artifact map.
- Whether the artifact decision table should live in the build capability workflow so the model knows what kind of capability to build.
- Whether the artifact standard sets up the future workflow layer.

## Issues Raised

- Dirty worktree was present at startup and before commit; user confirmed proceeding.

## Decisions Made

- Add a canonical harness artifact standard instead of expanding `AGENTS.md`.
- Keep detailed artifact placement rules in `.agentic/harness/standards/agentic-artifact-standards.md`.
- Add the compact artifact decision table to `.agentic/harness/workflows/build-capability-workflow.md`.
- Index the standard from `.agentic/harness/README.md`.
- Do not introduce hooks, evals, templates, examples, memory adapters, or agents yet; define where they fit first.

## Activity Log

### 2026-06-15T22:29:30Z - Session started

Initial intent: can you work through best practice standards for different types of files in agentic harnesses based on openAI, Anthropic, Cursor, Mistral best practices?

### 2026-06-15T22:40:00Z - Discovery and implementation

Reviewed current harness structure and vendor practices, proposed an artifact
ownership model, then implemented the standard, workflow decision table, and
harness index update after user approval.

## Commits

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This codifies artifact placement guidance and workflow routing support,
not a durable architecture decision beyond the standard itself.

## Session Metrics

Raised at UTC: 2026-06-15T22:29:30Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated tokens:

## Notes

- None recorded yet.
