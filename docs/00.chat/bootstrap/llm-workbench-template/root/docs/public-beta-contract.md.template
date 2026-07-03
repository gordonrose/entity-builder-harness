# Public-Beta Contract

`llm-workbench` is a standalone, provider-neutral Git/Bash/npm chat harness for
blank or existing repos, with safe install/uninstall, assistant adapters, JSON
startup packets, and portable transcript metadata across common CLI and
code-assistant workflows.

It does not claim to work perfectly with every LLM assistant or every editor
setup. Repos can provide instruction files, command surfaces, and structured
handoffs, but each assistant decides how well it follows those instructions.

## Invariants

- No durable whole-chat `layer`, `mode`, or `workflow` classification.
- Prompt-level routing is local and optional.
- Base startup does not require RAG/rulebook, classifier scripts, or
  source-specific routers.
- Public export and target installs are self-contained.
- Transcript metadata is provider-neutral.
- Codex transcript discovery is an optional adapter, not a default assumption.
- Cost metrics are unavailable by default until a pricing profile is selected.
- Install and uninstall are manifest-backed and preserve user files.
- Assistant adapters are thin routers to the canonical chat lifecycle workflow.
- `chat:new -- --json` supports code-assistant startup handoff.

## Required Checks

Before changing public harness behavior, run the portability suite:

```bash
bash scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh
```

Public changes should also run the relevant focused smoke tests listed in the
source repo standard.
