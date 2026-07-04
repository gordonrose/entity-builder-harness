<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.agents.use-cases
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: guide
purpose: Define review-agent use cases and quality bars used to test harness agent composition.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.workflows.run-agent-review
  path: .agentic/01.harness/workflows/run-agent-review.md
- id: harness.workflows.run-review-board
  path: .agentic/01.harness/workflows/run-review-board.md
- id: harness.script.agents.validate-harness-agents
  path: scripts/01.harness/agents/validate-harness-agents/script.sh
-->

# Harness Agent Use Cases

## Purpose

Use these cases to test whether harness review agents are selected, scoped, and
held to the right quality bar. A case is passing only when the selected agent
or agents produce a review that is specific, evidence-grounded, rubric-scored,
and bounded to their authority.

## Single-Agent Cases

### CFO Token Efficiency

#### Repeated Chat Workflow Change

- Trigger: A chat workflow change resembles prior chat-start or commit-gate
  work and has unusually high estimated token consumption.
- Expected agent: CFO Token Efficiency.
- Highest standard: Compare the current task with similar committed sessions,
  report count, min, max, mean, median, Q1, Q3, and token, cost, and
  cost-per-query trend, then recommend only reduction review paths that preserve
  workflow flexibility.
- Passing review: Names the metric source, comparable task set, statistical
  method, trend direction, and any delegated agent request.
- Failing review: Gives generic thrift advice without comparable-session
  evidence or asks agents to reduce safety-critical workflow context blindly.

#### Expensive RAG Query Iteration

- Trigger: A retrieval-policy task repeatedly queries broad corpora before
  narrowing to the same few artifacts.
- Expected agent: CFO Token Efficiency.
- Highest standard: Identify whether retrieval, prompt shape, or workflow
  ordering caused avoidable token spend before delegating improvement review.
- Passing review: Separates deterministic script opportunities from model
  prompt opportunities and names the safest next reviewer.
- Failing review: Treats all high token use as waste or proposes removing
  required evidence checks.

### Senior Prompt Engineer

#### New Workflow Prompt Surface

- Trigger: A workflow, skill, gate, eval, template, schema, orchestrator, or
  agent file changes the instructions an LLM will follow.
- Expected agent: Senior Prompt Engineer.
- Highest standard: Eliminate contradiction, drift, contamination, duplicated
  source-of-truth rules, unnecessary verbosity, and unclear stop conditions
  while preserving task flexibility.
- Passing review: Identifies exact instruction risks and distinguishes prose
  that should remain from behavior that should move to scripts, schemas, gates,
  or evals.
- Failing review: Rewrites style preferences without testing deterministic
  behavior or ignores how a first-time human reader will navigate the harness.

#### Harness Onboarding Clarity

- Trigger: A new operator-facing guide or README is added to a harness layer.
- Expected agent: Senior Prompt Engineer.
- Highest standard: Make the artifact learnable for a first-time human while
  keeping always-loaded and frequently-retrieved instructions concise.
- Passing review: Scores human learnability, source-of-truth clarity,
  deterministic handoff, and verbosity control.
- Failing review: Optimizes only for an expert agent and leaves the human path
  opaque.

#### Prompt Eval Gate Surface

- Trigger: A prompt, checklist, schema, gate, `*-gates` script directory, eval,
  or evaluate script changes how harness instruction quality is judged.
- Expected agent: Senior Prompt Engineer.
- Highest standard: Keep the instruction contract deterministic, rubric-bound,
  and concise while ensuring generated outputs can be scored objectively.
- Passing review: Names the prompt surface, deterministic validator or eval,
  scorecard contract, and any remaining judgment boundary.
- Failing review: Adds a prose-only quality claim without a testable gate or
  lets examples drift from the schema.

### Senior Back-End Architect

#### Platform Capability Addition

- Trigger: Product/backend work adds a platform, app, entity, feature, or
  capability boundary.
- Expected agent: Senior Back-End Architect.
- Highest standard: Confirm the solution follows the repository's
  platform/app/entity/feature/capability architecture and names any missing
  architecture rule without inventing ad hoc structure.
- Passing review: Compares implementation output to current architecture rules,
  identifies gaps, and proposes rulebook updates when durable guidance is
  missing.
- Failing review: Approves local code shape without checking architecture
  rules or adds broad rules unrelated to the observed gap.

#### Backend Rulebook Gap

- Trigger: A task exposes a repeated backend architecture ambiguity not covered
  by an existing rule.
- Expected agent: Senior Back-End Architect.
- Highest standard: Add or recommend the narrowest rule artifact consistent
  with existing layer, concern, and rule-pack structure.
- Passing review: Separates current task compliance from durable rulebook
  coverage and names the exact artifact family that should own the rule.
- Failing review: Turns a one-off preference into repository doctrine.

### Senior SRE Engineer

#### Deployment Path Change

- Trigger: GitHub Actions, AWS, ECS, ECR, RDS, Route53, CloudWatch, or deploy
  workflow behavior changes.
- Expected agent: Senior SRE Engineer.
- Highest standard: Ensure deployment control, rollback, observability,
  security boundaries, and cost per query improve or remain justified.
- Passing review: Covers blast radius, rollback, environment separation,
  runtime observability, cost controls, and operational failure modes.
- Failing review: Focuses only on successful deploy mechanics and ignores
  rollback, cost, or operator visibility.

#### Runtime Cost Investigation

- Trigger: A hosted service becomes more expensive per query or per request.
- Expected agent: Senior SRE Engineer.
- Highest standard: Identify infrastructure, scaling, logging, caching,
  deployment, and service-choice causes before recommending changes.
- Passing review: Separates AWS service cost drivers from application query
  behavior and names measurable cost signals.
- Failing review: Recommends cheaper services without preserving safety,
  reliability, or industry-standard operations.

### SecOps Engineer

#### Public Endpoint Exposure

- Trigger: A service, API, MCP endpoint, webhook, or UI becomes public or
  semi-public.
- Expected agent: SecOps Engineer.
- Highest standard: Check authentication, authorization, least privilege,
  secrets handling, audit logging, rate limiting, OWASP risk, and ISO-aligned
  governance evidence.
- Passing review: Produces blocking findings for missing critical controls and
  distinguishes security requirements from optional hardening.
- Failing review: Lists generic OWASP terms without mapping them to repo files,
  runtime paths, or concrete exposure.

#### Secret Handling Change

- Trigger: Secrets, tokens, credentials, environment variables, CI variables,
  or AWS secret retrieval behavior changes.
- Expected agent: SecOps Engineer.
- Highest standard: Ensure secrets never enter committed artifacts, logs,
  images, generated packets, or broad runtime scopes.
- Passing review: Checks source, build, deploy, runtime, logging, and retrieval
  paths for leakage or overbroad access.
- Failing review: Reviews only committed source files and misses CI or runtime
  exposure.

### UX/UI Engineer

#### Chat Or CLI Interaction Change

- Trigger: A command, prompt, blocked response, fallback, or CLI output changes
  how a human operates the harness.
- Expected agent: UX/UI Engineer.
- Highest standard: Keep the interface persona-aware, actionable, concise,
  accessible, and WCAG 2.2 AA aligned where applicable.
- Passing review: Checks whether the user can recover from failure without
  guessing, and whether output is scannable without losing safety details.
- Failing review: Treats UX as visual polish only and ignores chat, CLI, or
  repo-documentation usability.

#### Design-System Variant Review

- Trigger: A frontend-facing change affects input-based design-system variants
  or reusable frontend component boundaries.
- Expected agent: UX/UI Engineer.
- Highest standard: Preserve persona fit, accessibility, predictable controls,
  and reusable variant behavior without forcing one-off UI decisions.
- Passing review: Scores accessibility, task fit, component reuse, copy
  clarity, and interaction predictability.
- Failing review: Approves attractive UI that breaks accessibility,
  repeatability, or target-user workflow.

## Multi-Agent Cases

### Hosted RAG Service Deployment

- Trigger: A GitHub Actions to AWS deployment change exposes or modifies the
  RAG/rulebook service.
- Expected agents: Senior SRE Engineer, SecOps Engineer, Senior Back-End
  Architect, CFO Token Efficiency.
- Highest standard: The board verifies controlled deployment, secure exposure,
  architecture-rule compliance, and per-query cost visibility without adding
  redundant review prose.
- Passing review: Each agent produces a scorecard in its lane, cross-agent
  conflicts are named, and the final board decision blocks on any critical
  security, deploy, architecture, or cost regression.
- Failing review: The board averages scores to hide a critical issue or lets
  overlapping agents duplicate the same broad checklist.

### Harness Workflow Capability Build

- Trigger: A new harness workflow, skill, agent, template, schema, or gate is
  introduced.
- Expected agents: Senior Prompt Engineer, CFO Token Efficiency, UX/UI
  Engineer.
- Highest standard: The board ensures prompt surfaces are deterministic and
  learnable, token cost is justified by prior comparable work, and the human
  operating path is clear.
- Passing review: The board distinguishes always-loaded instructions from
  conditional artifacts and confirms that repeated behavior has a test or
  deterministic check where possible.
- Failing review: The board approves a verbose prompt-heavy design without
  testing whether scripts, gates, templates, or evals should own part of it.

### Product Platform Feature With Public UI

- Trigger: A backend capability adds a user-facing web or CLI surface and
  touches deployment configuration.
- Expected agents: Senior Back-End Architect, UX/UI Engineer, Senior SRE
  Engineer, SecOps Engineer.
- Highest standard: The board verifies backend architecture, user-facing
  clarity and accessibility, safe deployment, and security controls as separate
  blocking dimensions.
- Passing review: Findings are grouped by owner, each blocking issue names the
  responsible agent lane, and no agent implements changes during review.
- Failing review: One agent's approval is treated as permission to skip another
  agent's domain.

### Token Spend Regression In A Secure Workflow

- Trigger: A security-sensitive workflow grows more expensive over time due to
  repeated context loading and review-board invocation.
- Expected agents: CFO Token Efficiency, Senior Prompt Engineer, SecOps
  Engineer.
- Highest standard: The board reduces avoidable token spend only where doing so
  does not weaken security coverage or required evidence review.
- Passing review: CFO quantifies the regression, Senior Prompt Engineer finds
  prompt or artifact-structure savings, and SecOps marks which evidence cannot
  be compressed or skipped.
- Failing review: Cost savings remove a required security control, or security
  review forces broad context loading with no retrieval or script strategy.

## Test Expectations

These use cases should drive agent routing and review-board tests. A test is
complete only when it verifies:

- selected agents match the use case
- workflow routing tables select the same agents the fixtures expect
- required scorecard fields are present
- scorecard decisions agree with critical blockers, required scores, and
  delegation requests
- critical findings cannot be hidden by a high average score
- each rubric negative-fixture label has an executable blocking case
- review output names evidence and source-of-truth artifacts
- implementation and review authority remain separate unless a workflow grants
  write permission to a specific implementing agent

Executable fixtures live at:

- `scripts/01.harness/agents/validate-harness-agents/fixtures/use-case-fixtures.yml`
- `scripts/01.harness/agents/validate-harness-agents/fixtures/scorecard-fixtures.yml`
- `scripts/01.harness/agents/validate-harness-agents/fixtures/negative-review-fixtures.yml`

They are enforced by
`scripts/01.harness/agents/validate-harness-agents/script.sh`.
