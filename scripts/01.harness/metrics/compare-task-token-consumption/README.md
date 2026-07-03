<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.script.metrics.compare-task-token-consumption.readme
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: capability-readme
purpose: Explain the CFO token-consumption comparison script.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.agents.cfo-token-efficiency
  path: .agentic/01.harness/agents/cfo-token-efficiency.md
- id: harness.script.metrics.compare-task-token-consumption
  path: scripts/01.harness/metrics/compare-task-token-consumption/script.sh
-->

# Compare Task Token Consumption

`script.sh` compares a current task description with committed chat session logs
and emits JSON for CFO Token Efficiency review.

The script is read-only. It parses `commitLogs/**/README.md` session metadata,
computes deterministic weighted similarity against the supplied task query,
workflow, changed paths, and requested agents, keeps sessions with estimated
token metrics, and reports:

- similar task count
- min, max, mean, median, Q1, and Q3 token consumption
- weighted similarity basis, component scores, and comparable-session date range
- trend direction, slope, sample size, and confidence over time
- historical USD cost, model/pricing-basis metadata, query count, and
  per-query cost when available
- current task token, cost, and per-query comparison, when supplied
- delegation requirement, target agents, and blocking question when a trend is
  flat or rising or the current task is above historical Q3

## Usage

```bash
bash scripts/01.harness/metrics/compare-task-token-consumption/script.sh \
  --task-query "update chat startup workflow" \
  --current-tokens 1200000 \
  --current-cost-usd 14.25 \
  --current-query-count 250 \
  --workflow ".agentic/00.chat/workflows/chat-start.md" \
  --changed-path ".agentic/00.chat/workflows/chat-start.md" \
  --pricing-basis "current session metadata token estimate"
```

Useful options:

- `--commit-log-root <path>` reads a fixture or alternate commit-log root.
- `--min-score <number>` changes the similarity cutoff. Default: `0.12`.
- `--limit <count>` caps the similar session list. Default: `50`.
- `--current-cost-usd <amount>` records current estimated cost in USD.
- `--current-query-count <count>` records current query/request count so
  current per-query cost can be derived.
- `--current-cost-per-query-usd <amount>` supplies current per-query cost
  directly when query count is unavailable.
- `--workflow <id>` records the workflow under review and helps delegation.
- `--changed-path <path>` may be repeated to help identify the cost driver.
- `--agent <agent-id>` may be repeated to record agents already involved.
- `--pricing-basis <text>` records the basis for any cost interpretation.

The JSON output is intended for review agents and tests, not for direct human
editing.
