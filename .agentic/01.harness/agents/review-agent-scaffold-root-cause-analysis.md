<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.agents.review-agent-scaffold-rca
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: guide
purpose: Analyze why the initial harness review-agent implementation delivered a scaffold instead of professional-grade reviewer judgment.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.agent-contracts
  path: .agentic/01.harness/standards/agent-contracts.md
- id: harness.agents.readme
  path: .agentic/01.harness/agents/README.md
-->

# Review Agent Scaffold Root Cause Analysis

## Problem

The first review-agent implementation created a useful scaffold, but it did
not satisfy the user's intended quality bar: agents and rubrics capable of
approximating the judgment of senior professional reviewers.

The delivered system had the right artifact families: agents, use cases,
workflows, templates, a CFO metric script, and a validator. The weak point was
depth. The validator proved only file and heading presence. It
did not prove that the rubrics contained professional judgment, concrete
evidence requirements, blocking conditions, or executable use-case behavior.

## Impact

The scaffold could produce plausible-looking review reports while allowing
shallow or invalid review logic to pass. That creates a dangerous failure mode:
the harness appears governed, but it can approve weak specialist judgment.

The highest-risk examples are:

- security review that names OWASP and ISO without mapping findings to concrete
  assets, trust boundaries, controls, and evidence
- architecture review that names platform boundaries without checking
  dependency direction, data ownership, API contracts, or rule gaps
- SRE review that mentions rollback and cost without requiring health,
  observability, blast-radius, and cost-per-query evidence
- UX review that mentions WCAG without checking task completion, recovery
  states, or accessibility criteria
- CFO review that calculates token statistics but does not require delegation
  when spend trends are flat or rising

## Root Cause

The implementation optimized for artifact completeness instead of judgment
fidelity.

The work treated the prompt as a request for a complete artifact set. It did
not sufficiently distinguish between:

- creating an agent file and creating a professional reviewer
- naming rubric dimensions and defining scoreable judgment
- validating shape and validating quality
- documenting use cases and executing use cases
- calculating CFO statistics and enforcing CFO escalation behavior

## Contributing Causes

### Structural Bias

The harness already had strong artifact-placement standards. That made it easy
to implement the correct directory structure and metadata before asking whether
the content carried enough domain judgment.

### Validation Bias

The first validator checked observable file shape because shape was cheap to
test. It did not parse a real rubric model, reject shallow score anchors, or
run negative fixtures.

### Rubric Compression

The agent files compressed expert judgment into short prose lists. That made
the agents readable, but it removed the scoring anchors, evidence requirements,
and blocker definitions required for objective review.

### Fixture Substitution

The use-case matrix was treated as test coverage. It was only source material
for future tests. No executable fixture proved agent selection, evidence
requirements, blocking behavior, delegation, or review-board composition.

### Authority Ambiguity

The original request said the Senior Back-End Architect should implement new
architecture guidance when required. The scaffold made the agent review-only,
which is safer, but it did not add a governed implementation mode or explicitly
record the deviation.

### Source-Of-Truth Drift

The new review-agent capability lives under `01.harness`, but
`.agentic/01.harness/manifest.yml` still describes the layer as an architecture
rulebook operating pack. That produces contradictory signals for future agents.

## Detection Gaps

The scaffold would still pass when:

- an agent rubric is replaced by meaningless text under the same heading
- the scorecard is syntactically or semantically weak while preserving required
  strings
- a critical finding is present but the decision remains `pass`
- a required professional-standard reference is absent
- a use case names agents but no routing fixture validates selection
- a multi-agent board omits a required lane

## Corrective Actions

The hardening work should add:

- machine-readable rubric files, one per agent
- per-dimension score anchors for `5`, `3`, and `0`
- evidence requirements for each dimension
- blocking conditions and delegation triggers
- professional-standard references for each agent
- executable use-case fixtures
- routing and review-board fixture tests
- scorecard semantic validation
- CFO trend-confidence and delegation fields
- source-of-truth cleanup for `01.harness`
- explicit Backend Architect implementation-mode governance or a recorded
  review-only decision

## Prevention Standard

Future review-agent work should not be accepted as complete until a validator
can reject shallow rubrics and invalid review outcomes. A professional review
agent is complete only when its judgment model is both human-legible and
machine-checkable.

## RCA Conclusion

The failure was not file placement. The failure was accepting structural
completeness as semantic completeness.

The next implementation slice must make professional judgment explicit,
scoreable, and testable.
