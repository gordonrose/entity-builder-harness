<!-- agentic-artifact:
owner: harness
kind: workflow
purpose: Govern review of one architecture rulebook artifact.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/prompts/review-rule-artifact.prompt.md
-->

# Review Rule Artifact Workflow

Use this to review one existing layer ruleset, concern ruleset, or rule pack.

Check that:

- The artifact is in the correct folder.
- The artifact is the right type: layer, concern, or task pack.
- `source_refs` are present.
- No unrelated files changed.
- YAML parses.
- The artifact is concise enough for future agent use.
