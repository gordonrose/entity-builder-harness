<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflows.implement-backend-architecture-guideline
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- architecture
- backend
kind: workflow
purpose: Govern Senior Back-End Architect implementation mode for architecture-guideline artifacts.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.agents.senior-backend-architect
  path: .agentic/01.harness/agents/senior-backend-architect.md
- id: harness.manifest
  path: .agentic/01.harness/manifest.yml
-->

# Implement Backend Architecture Guideline

## Purpose

Use this workflow only when the Senior Back-End Architect is explicitly invoked
in implementation mode to update a bounded backend architecture guideline,
rule, rule-pack, or related harness architecture artifact.

Review mode identifies compliance and gaps. Implementation mode edits the
smallest governed artifact needed to close an accepted durable gap.

## Use When

- a review has identified a durable backend architecture gap
- the user has granted write permission for this chat
- the requested output is an architecture guideline, rule, rule-pack, or
  supporting harness documentation artifact
- the change fits the platform, app, entity, feature, and capability approach

Do not use this workflow for product code, runtime services, deployment
mutation, frontend implementation, security permission changes, or prompt-only
workflow changes.

## Inputs

- accepted review finding or user request naming the architecture gap
- current architecture rule, rule-pack, or missing-governance evidence
- target artifact path or artifact family
- relevant RAG/rulebook context packet when available
- expected validation command or gate

## Authority Boundary

Implementation mode is limited to architecture-guideline artifacts. It may
create or edit:

- `docs/harness/architecture/rules/**`
- `docs/harness/architecture/rule-packs/**`
- `.agentic/01.harness/workflows/*rule*.md`
- `.agentic/01.harness/templates/*rule*.yml`
- narrowly related harness documentation that indexes or explains those
  artifacts

It may not edit:

- product or backend runtime code
- AWS, GitHub Actions, or deployment targets
- secrets, permissions, or auth configuration
- frontend implementation files
- review-agent rubrics outside a separately governed harness-agent task

## Procedure

1. State that the Senior Back-End Architect is in implementation mode.
2. Name the accepted gap and the artifact family that owns it.
3. Verify write permission and current chat lifecycle gates are satisfied.
4. Select the narrowest artifact path.
5. If the artifact is a layer ruleset, concern ruleset, or rule pack, follow
   the matching architecture workflow:
   - `create-layer-ruleset.workflow.md`
   - `create-concern-ruleset.workflow.md`
   - `create-rule-pack.workflow.md`
6. Edit only the selected artifact and required generated/index metadata.
7. Run YAML validation for YAML artifacts.
8. Run deterministic harness and RAG/rulebook gates named by the active chat
   workflow before commit.
9. Report the implemented guideline, evidence reviewed, validation output, and
   remaining gaps.

## Quality Bar

The implemented guideline is acceptable only when it:

- names the source evidence or review finding that justified it
- is narrower than the observed durable gap
- fits existing layer, concern, and rule-pack structure
- preserves platform, app, entity, feature, and capability boundaries
- avoids turning a one-off implementation preference into doctrine
- states when another agent owns a blocking security, SRE, UX, prompt, or CFO
  decision

## Stop Conditions

Stop before editing when:

- write permission for the chat is absent
- the gap is not durable
- the target artifact family is unclear
- the requested edit would touch product/runtime/deployment/security/frontend
  implementation
- another agent owns a blocking risk
<!-- deterministic-check: allow reason="artifact-specific validators are selected by the active architecture workflow" -->
- no governed validation path exists for the target artifact
