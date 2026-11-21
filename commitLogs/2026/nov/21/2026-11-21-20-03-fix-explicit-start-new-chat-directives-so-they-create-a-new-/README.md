# Chat Session: 2026-11-21-20-03 fix-explicit-start-new-chat-directives-so-they-create-a-new-

<!-- agentic-session
id: 2026-11-21-20-03-fix-explicit-start-new-chat-directives-so-they-create-a-new-
task: fix explicit start-new-chat directives so they create a new governed session instead of prompting to continue
branch: chat/2026-11-21-20-03-fix-explicit-start-new-chat-directives-so-they-create-a-new-
worktree: /home/owner/projects/.chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-11-21-20-03-fix-explicit-start-new-chat-directives-so-they-create-a-new--4211374508
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-11-21T20:03:06Z
transcript_provider:
transcript_path:
transcript_bytes:
transcript_source:
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

fix explicit start-new-chat directives so they create a new governed session instead of prompting to continue

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- `resolve-current-chat-session` reads an existing session before examining the opening prompt. An explicit `start new chat` directive therefore reaches `recorded-session-approval-required` instead of the existing new-session creator.
- Public-beta validation found an existing package-smoke mismatch: root/main rejection was asserted with `main`, but the open-window diagnostic omitted the branch. The bounded diagnostic correction is covered by the existing package and dispatcher suites.

## Decisions Made

- Reuse `resolve-current-chat-session` as the sole startup entrypoint and `start-new-chat` as the existing creator; do not add another lifecycle command or registry.
- Treat only a first non-empty line that is exactly `start new chat` (case-insensitive) as an explicit directive. Its remaining non-empty text is the required task summary. A directive without a summary must return a precise summary-required result without creating a branch/worktree.
- Preserve normal existing-session reuse, recorded-session approval, and missing-session auto-start behavior for every non-directive prompt.
- No runtime diagnostic vocabulary, configuration, deployment, or public product contract changes are applicable. The changed shell decision has exact smoke-test assertions and remains in the existing imported-session-lookup diagnostic review/check owner.
- Public-beta validation exposed a pre-existing mismatch between the package smoke assertion and the open-window diagnostic. The diagnostic now includes the already-observed branch name (for example, `main`) without exposing user-supplied paths or native failure text.

## Context Hygiene

- Bounded scope: startup resolver, its capability/workflow documentation, its smoke test, and the existing diagnostic review hash. No context router or unrelated deployment/product workflow applies.

## Task Inventory

- Producer and routing owner: `scripts/00.chat/startup/resolve-current-chat-session/script.sh`; it must recognize the directive before querying existing metadata, then delegate to `start-new-chat`.
- Reused consumer: `scripts/00.chat/startup/start-new-chat/script.sh` delegates to the existing session creator; no compatibility changes to creation mechanics are intended.
- Preserved consumers: `read-current-chat-log` and recorded-session approval, missing-session auto-start, and normal metadata return.
- Documentation consumers: `.agentic/00.chat/workflows/chat-start.md` and the resolver capability README must describe the exact directive grammar and no-summary outcome.
- Proof owner: `scripts/00.chat/startup/resolve-current-chat-session/smoke-test.sh`, selected by `chat-session-resolution-regression`; it must reject the former routing (a directive returning existing metadata or approval-required) and prove no-summary creates no branch.
- Diagnostic-review owner: `scripts/repo/diagnostic-coverage/reviews.v1.json`; refresh the resolver and open-window source hashes and review rationale after source review. The changes preserve finite, non-sensitive shell outcomes.
- Delivery impact: local startup tooling only; no package/image/cloud delivery or live verification applies.

## Activity Log

### 2026-11-21T20:03:06Z - Session started

Initial intent: fix explicit start-new-chat directives so they create a new governed session instead of prompting to continue.

## Sub-Agent Activity

- None recorded yet.

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This is a narrow correction to the existing startup routing contract. It reuses the current resolver and creator and does not change architecture, public product contracts, or deployment boundaries.

## Session Metrics

Raised at UTC: 2026-11-21T20:03:06Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- Source review completed: the explicit command is deliberately checked before session metadata; the no-summary branch returns before any creator call; non-directive paths remain in their original reader/result switch. The smoke test rejects the former recorded-session outcome, unexpected bare-command creation, incorrect task forwarding, and extra branch creation.
- Verification passed: resolver smoke test directly and through registered `chat-session-resolution-regression`; `scripts/repo/diagnostic-coverage/script.sh`; artifact headers, deterministic-process drift, governed-command drift, and whitespace diff checks.
- The full impact planner was recorded but reports an existing workspace-context/node-installation gap and over-selects unrelated bootstrap/deployment checks. The exact registered resolver proof ran successfully; no deployment or product behavior was changed.
- Public-beta portability, bootstrap, startup, session-log, package-command, dispatcher, export, and artifact-header smoke suites passed after the correction. No temporary eval files remain.
