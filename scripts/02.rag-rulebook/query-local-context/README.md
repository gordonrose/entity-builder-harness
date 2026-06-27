<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.query-local-context.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: runtime
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the local context-query command for validated RAG/rulebook packets.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.query-local-context
  path: scripts/02.rag-rulebook/query-local-context/script.sh
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# Query Local Context

`script.sh` reads a built local RAG/rulebook runtime cache and emits a
validated `rag-rulebook/context-packet/v1` packet.

Before it answers, the command checks the runtime manifest fingerprints against
the current live repo inputs that selector generation still reads. If retrieval
policy, recognition sources, recognition candidates, corpus gaps, or runtime
outputs have changed since the runtime was built, the command refuses to query
and asks the caller to rebuild the local runtime.

Build the runtime first:

```bash
bash scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
```

Then query it:

```bash
bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --request-text "How do I update my harness so we can deploy it behind an MCP server?" \
  --session-layer 01.harness \
  --session-mode planning \
  --session-workflow .agentic/01.harness/workflows/change-harness.md \
  --focused-path .agentic/01.harness/workflows/change-harness.md \
  --pretty
```

## Options

- `--runtime-dir <path>` chooses the local runtime cache. Default:
  `.cache/02.rag-rulebook`.
- `--request-text <text>` is required.
- `--session-layer`, `--session-mode`, and `--session-workflow` provide
  session metadata.
- `--focused-path <path>` may be repeated.
- `--no-focused-paths` clears focused path signals.
- `--max-chunks <n>` controls packet size.
- `--pretty` pretty-prints JSON.

## Effects

This command is read-only. It does not build the runtime, mutate sources, call
the network, start a server, generate embeddings, or deploy anything.
