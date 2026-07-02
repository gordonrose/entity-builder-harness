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
validated `rag-rulebook/context-packet/v1` packet by default. It can also emit
a compact agent-facing view with `--format compact`.

Before it answers, the command calls
`scripts/02.rag-rulebook/check-runtime-freshness/script.sh`. If retrieval
policy, recognition sources, recognition candidates, corpus gaps, or runtime
outputs have changed since the runtime was built, the freshness checker refuses
the query and asks the caller to rebuild the local runtime.

Build the runtime first:

```bash
bash scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
```

Then query it:

```bash
bash scripts/02.rag-rulebook/query-local-context/script.sh \
  --request-text "How do I update my harness so we can deploy it behind an MCP server?" \
  --focused-path .agentic/01.harness/workflows/change-harness.md \
  --pretty
```

## Options

- `--runtime-dir <path>` chooses the local runtime cache. Default:
  `.cache/02.rag-rulebook`.
- `--request-text <text>` is required.
- `--session-id`, `--session-branch`, and `--session-worktree` provide
  lifecycle provenance for the consuming chat/workbench.
- `--session-layer`, `--session-mode`, and `--session-workflow` are optional
  legacy routing hints. Omit them for prompt-first context resolution.
- `--trust-session-routing` allows a governed session resolver to treat those
  legacy routing hints as verified selector input. It fails unless
  `--session-id`, `--session-branch`, `--session-worktree`,
  `--session-layer`, `--session-mode`, and `--session-workflow` are supplied.
  Do not use it for client-supplied values; the HTTP service intentionally does
  not expose this trust path.
- `--previous-packet-id` and `--previous-routing-summary` provide continuity
  from the previous context packet without making it current routing.
- `--focused-path <path>` may be repeated.
- `--no-focused-paths` clears focused path signals.
- `--max-chunks <n>` controls packet size.
- `--format <full|compact>` chooses the output shape. `full` is the default
  debug/provenance packet. `compact` keeps selected chunk content, concise
  citations, confidence, gaps, required checks, forbidden actions, stop
  conditions, budgets, and a selector-trace summary.
- `--pretty` pretty-prints JSON.

## Output Formats

`--format full` returns the canonical `rag-rulebook/context-packet/v1` packet.
Use it for validation, selector-trace debugging, provenance review, and
evaluation failure analysis.

`--format compact` returns `rag-rulebook/context-packet-compact/v1`. It is a
derived view of the same validated packet, intended for normal agent context
augmentation. It must not contain independent retrieval behavior. If the compact
view is insufficient, rerun the same query with `--format full`.

## Git-Less Runtime Packaging

By default, the command finds the repo root through Git. Container images and
other packaged runtimes should set `RAG_REPO_ROOT` to the mounted application
root, such as `/app`, so query-time validation can run without copying `.git`
into the image.

## Effects

This command is read-only. It does not build the runtime, mutate sources, call
the network, start a server, generate embeddings, or deploy anything.
