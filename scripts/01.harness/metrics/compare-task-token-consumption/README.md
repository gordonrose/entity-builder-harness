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
computes lexical similarity against the supplied task query, keeps sessions
with estimated token metrics, and reports:

- similar task count
- min, max, mean, median, Q1, and Q3 token consumption
- trend direction over time
- current task comparison, when `--current-tokens` is supplied

## Usage

```bash
bash scripts/01.harness/metrics/compare-task-token-consumption/script.sh \
  --task-query "update chat startup workflow" \
  --current-tokens 1200000
```

Useful options:

- `--commit-log-root <path>` reads a fixture or alternate commit-log root.
- `--min-score <number>` changes the similarity cutoff. Default: `0.12`.
- `--limit <count>` caps the similar session list. Default: `50`.

The JSON output is intended for review agents and tests, not for direct human
editing.
