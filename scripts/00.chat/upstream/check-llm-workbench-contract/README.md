<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.upstream.check-llm-workbench-contract.readme
  version: 1
  status: active
  layer: 00.chat
  domain: validation
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the static contract check for llm-workbench public-beta invariants.
  portability:
    class: reusable
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.upstream.check-llm-workbench-contract
    path: scripts/00.chat/upstream/check-llm-workbench-contract/script.sh
  - id: chat.script.upstream.validate-llm-workbench-portability
    path: scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh
-->
# Check llm-workbench Contract

`script.sh` runs fast static checks for the public-beta contract. It complements
the heavier portability suite by catching source-only path leaks, old
classification wiring, provider-specific defaults, hard-coded RAG/rulebook
gates, unsafe installer patterns, and adapter drift.

Run against the source repo:

```bash
bash scripts/00.chat/upstream/check-llm-workbench-contract/script.sh
```

Run against a generated public workbench:

```bash
bash scripts/00.chat/upstream/check-llm-workbench-contract/script.sh \
  --repo /path/to/generated/llm-workbench \
  --public
```

The public mode additionally verifies source-only trees are absent.
