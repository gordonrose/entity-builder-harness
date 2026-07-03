<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.standards.professional-review-agent-quality
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: standard
purpose: Define the professional-grade quality bar for harness review-agent rubrics, fixtures, and validation.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.agent-contracts
  path: .agentic/01.harness/standards/agent-contracts.md
- id: harness.script.agents.validate-harness-agents
  path: scripts/01.harness/agents/validate-harness-agents/script.sh
-->

# Professional Review Agent Quality Standard

## Purpose

Use this standard to decide whether a harness review agent is fit to influence
quality gates. A review agent is professional-grade only when its judgment is
explicit, evidence-based, scoreable, and tested against positive and negative
cases.

This standard exists because an agent can look complete while still being too
generic to catch real defects. Headings, role descriptions, and broad rubric
labels are not enough.

## Quality Bar

A professional review agent should approximate how a senior practitioner frames
the review. It does not need every fact in the profession. It does need the
review lens, evidence requirements, blocker logic, and delegation behavior that
prevent false confidence.

The agent is not ready for gate use when a weak reviewer can produce a valid
report without naming concrete evidence, scoring against anchored dimensions,
or blocking critical findings.

## Rubric Artifact Requirement

Each harness review agent has a machine-readable rubric under:

```text
.agentic/01.harness/agents/rubrics/<agent-slug>.yml
```

The rubric file is the scoring source of truth. The agent Markdown can explain
the role, but it should not be the only place where scoring logic lives.

Rubric files use JSON-compatible YAML so the validator can parse them with the
standard Node runtime. Metadata comments may appear before the JSON object.

## Rubric Fields

<!-- deterministic-check: allow reason="this is a human-authored schema-like standard; validation script enforces the fields introduced here" -->
Each rubric defines:

- `schema`
- `agent_id`
- `version`
- `minimum_dimensions`
- `decision_policy`
- `dimensions`
- `professional_standard_refs`
- `evidence_model`
- `delegation_model`
- `negative_fixtures`

Each dimension defines:

- `id`
- `name`
- `required`
- `weight`
- `evidence_required`
- `score_5`
- `score_4`
- `score_3`
- `score_2`
- `score_1`
- `score_0`
- `blocking_conditions`
- `delegation_triggers`
- `professional_standard_refs`

## Score Anchor Rules

Score anchors must be specific enough that a reviewer can distinguish excellent,
acceptable, weak, and absent evidence.

- `score_5` describes professional evidence and no material gap.
- `score_3` describes minimally acceptable evidence with bounded risk.
- `score_0` describes absent, unsafe, or unreviewable evidence.

`score_4`, `score_2`, and `score_1` should make the scale usable for trend
analysis instead of forcing all outcomes into excellent, acceptable, or absent.

## Blocking Rules

Critical findings are not averaged away.

A rubric dimension can block the agent decision when:

- required evidence is absent
- the score is below `3`
- a dimension-specific blocking condition is present
- a required delegation has not returned a terminal decision
- the review cannot name source-of-truth evidence

The scorecard decision must agree with the scores and blocker fields.

## Evidence Rules

Evidence requirements should name the kind of proof needed, not just the topic.

Good evidence requirements name:

- source artifact path or packet type
- command output or metric
- implementation diff
- runtime/deployment evidence
- security, accessibility, architecture, or cost control evidence
- explicit evidence gaps

The validator should reject rubrics whose evidence requirements are empty or
purely generic.

## Professional References

Professional-standard references may point to internal standards, rulebooks,
external frameworks, or domain bodies of knowledge. They are not decoration.
They explain why a dimension exists and what lens the agent should use.

Examples:

- OWASP, ISO 27001-style control thinking, least privilege, and threat
  modeling for SecOps
- WCAG 2.2 AA, task completion, and recovery-state usability for UX/UI
- SLOs, rollback, observability, incident response, and cloud cost controls for
  SRE
- architecture rules, dependency direction, platform/app/entity boundaries, and
  rule-gap governance for backend architecture
- prompt hierarchy, instruction conflict, deterministic boundaries, eval
  readiness, and source-of-truth ownership for prompt engineering
- statistical sample quality, trend confidence, pricing basis, and safe
  delegation for CFO token efficiency

## Use-Case Fixture Rules

Use cases become executable fixtures before the review-agent system is treated
as complete.

Each fixture defines:

- task text
- changed paths
- expected agents
- required evidence
- expected blockers
- minimum scores
- required delegation
- forbidden delegation
- expected board decision

Positive fixtures prove correct review selection. Negative fixtures prove that
shallow rubrics, missing evidence, invalid scorecards, and unblocked critical
findings fail.

## Validator Rules

The validator checks professional quality, not just file shape.

It rejects:

- missing rubric files
- too few dimensions
- missing score anchors
- empty evidence requirements
- empty blocking conditions on required dimensions
- missing professional references
- malformed scorecard data
- scorecard decisions that contradict scores or critical blockers
- use-case fixtures with missing expected agents
- review-board fixtures that omit a required lane
- CFO output with rising or flat trend but no delegation requirement

## Completion Rule

A review-agent change is not complete until:

- the relevant rubric file passes semantic validation
- use-case fixtures cover the changed behavior
- negative fixtures prove shallow work fails
- the validator is run in the commit gate or documented as a required check
- generated recognition sources are current

## Relationship To Agent Contracts

The agent contract standard defines the shape of an agent. This standard
defines the professional quality bar for trusting that agent.

Both standards apply. Passing the contract shape without passing this standard
means the agent remains scaffold-grade.
