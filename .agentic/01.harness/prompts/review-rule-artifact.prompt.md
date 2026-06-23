<!-- agentic-artifact:
owner: harness
kind: prompt
purpose: Reusable prompt for reviewing one architecture rulebook artifact.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/operator-guide.md
-->

# Review Rule Artifact Prompt

Review one existing architecture rulebook artifact using
`.agentic/01.harness/workflows/review-rule-artifact.workflow.md` and the
checklists under `.agentic/01.harness/checklists`.

Check artifact type, folder, source refs, concision, unrelated changes, and YAML
parsing. Report findings first, then assumptions and validation method. Do not
edit unless explicitly asked.
