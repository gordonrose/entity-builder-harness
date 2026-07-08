<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.session-log.record-chat-commit.readme
  version: 1
  status: active
  layer: 00.chat
  domain: session-log
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain how task commits are recorded into chat session logs and metrics.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.session-log.record-chat-commit
    path: scripts/00.chat/session-log/record-chat-commit/script.sh
  - id: chat.script.session-log.record-chat-commit.smoke-test
    path: scripts/00.chat/session-log/record-chat-commit/smoke-test.sh
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
-->
# Record Chat Commit

`script.sh` records a completed task commit in the current chat session log.

It is the bridge between Git history and the durable chat record. The Git commit
contains the actual file changes. The session log explains what that commit
meant inside the conversation, when it happened, what it changed, and which chat
metrics were known at that boundary.

## Mental Model

Chat work has two kinds of commits:

- task commits, which contain the real harness, product, or documentation
  changes
- bookkeeping commits, which update the session log after the task commit is
  recorded

`record-chat-commit` runs after the task commit exists. It edits the current
session log so the log points back to the commit SHA and captures the human
summary, ADR impact, chat duration, transcript-derived token estimate, and cost
estimate.

If recording the commit leaves only the session log dirty, the normal next step
is to checkpoint that bookkeeping separately with
`checkpoint-chat-session-log.sh`.

## Inputs

```bash
record-chat-commit.sh <sha> <message> <summary> [adr-impact]
```

- `sha`: the task commit SHA to record.
- `message`: the task commit message.
- `summary`: a human explanation of what changed.
- `adr-impact`: optional note about whether the change is covered by existing
  ADRs or needs follow-up.

The script must run on a `chat/*` branch so it can derive the session id and
find the matching session log.

## Metrics

The script records chat metrics at the commit boundary.

Preferred transcript sources:

1. `CHAT_TRANSCRIPT_BYTES`, when a caller supplies a byte count directly.
2. Neutral session metadata such as `transcript_path` and `transcript_provider`.
3. An explicit assistant adapter, for example `CHAT_TRANSCRIPT_PROVIDER=codex`
   for Codex JSONL discovery.

If transcript metrics cannot be found, portable mode records the metric as
unavailable. Set `CHAT_TRANSCRIPT_METRICS_MODE=strict` when a workflow requires
exact transcript metrics before recording the commit.

When a numeric token estimate is available, the script calls
`scripts/00.chat/metrics/estimate-chat-cost/script.js` to record a cost estimate
and pricing basis.

## What It Updates

The script updates:

- `## Commits`
- `## Activity Log`
- session metadata fields such as `latest_commit_at_utc`,
  `latest_commit_sha`, `chat_duration`, `estimated_chat_tokens`,
  `estimated_chat_cost`, and `estimated_chat_cost_basis`
- visible `## Session Metrics` fields

It also upgrades older `estimated_tokens` and `Final commit` fields to the newer
chat-specific names when encountered.

## What This Does Not Do

- It does not create the task commit.
- It does not stage or commit the session-log bookkeeping.
- It does not push anything.
- It does not run the before-commit gate.
- It does not decide ADR disposition for the human.

## Validation

`smoke-test.sh` creates a throwaway chat branch and session log, then verifies:

- missing transcript metrics fail clearly
- the legacy missing-metrics escape hatch records unavailable metrics
- assistant transcript discovery records provider, path, token estimate, cost,
  and basis
- supplied transcript byte counts override discovery
- session-log file size is not used as a token source

Run the canonical smoke test with:

```bash
bash scripts/00.chat/session-log/record-chat-commit/smoke-test.sh
```

## Compatibility

The governed runner still approves the old path:

```bash
scripts/00.chat/session-log/record-chat-commit/script.sh
```

That file is now a compatibility wrapper around the canonical implementation.
Commit checklists should keep using the approved shared path until the governed
runner allowlist policy is migrated.
