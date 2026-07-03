<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.standards.agent-contracts
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: standard
purpose: Define the contract, authority boundaries, and scoring expectations for harness review agents.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.agentic-artifact-standards
  path: .agentic/01.harness/standards/agentic-artifact-standards.md
- id: harness.workflows.build-capability-workflow
  path: .agentic/01.harness/workflows/build-capability-workflow.md
-->

# Agent Contract Standard

## Purpose

Use this standard when creating or reviewing harness agents. Agents define
bounded review or execution roles. They do not replace workflows, standards,
scripts, gates, templates, schemas, or RAG/rulebook context packets.

The goal is to make agents useful without turning them into always-loaded
instruction piles. An agent should know its lane, ask for the evidence it needs,
score work against a rubric, and hand off cleanly when another lane owns the
risk.

For professional-grade review agents, also follow
`.agentic/01.harness/standards/professional-review-agent-quality.md`. This
contract standard defines artifact shape; the professional-quality standard
defines whether the agent is trustworthy enough to influence gates.

## Agent Ownership

Harness-wide agents live under `.agentic/01.harness/agents/`.

Layer-specific agents may live in a layer-owned `agents/` directory only when
the role is not reusable across harness work. For example, education article
agents belong under `.agentic/education/agents/`; cross-cutting review agents
belong under `.agentic/01.harness/agents/`.

Agent files own role definition and review posture. They must not duplicate
domain rules already owned by standards, workflows, rulebooks, or scripts.

## Required Sections

Every harness agent must include these sections:

- `Responsibility`
- `Use When`
- `Inputs`
- `Required First Move`
- `Allowed Actions`
- `Disallowed Actions`
- `Evidence Sources`
- `Review Rubric`
- `Scoring`
- `Required Output`
- `Delegation And Escalation`
- `Stop Conditions`

Optional sections are allowed only when they clarify repeated work. Prefer a
template or example over adding agent-specific structure that other agents
cannot share.

## Authority Model

Review agents produce findings, scorecards, reports, and delegation requests.
They do not edit files, stage changes, commit, push, delete, rewrite history,
deploy, rotate secrets, or change infrastructure unless a workflow explicitly
invokes that agent as an implementation agent and grants that authority.

When acting as a reviewer, an agent must:

- state whether it is reviewing, planning, researching, or implementing
- name the artifacts, diffs, context packets, logs, or command outputs it used
- separate blockers from improvements
- keep recommendations inside its lane
- delegate cross-lane risks instead of silently expanding scope

<!-- deterministic-check: allow reason="agent review behavior is human-governed here; later validation scripts can check required sections and output shape, but missing-governance judgment remains a reviewer stop condition" -->
When a review discovers missing governance, it must report the gap and stop
before proposing an improvised workaround.

## Inputs

An agent should request the smallest sufficient context set:

- current user request or task summary
- changed files, staged diff, or implementation output
- current workflow, standard, gate, or rulebook context packet
- relevant session metadata and commit log facts
- agent-specific evidence such as token metrics, deployment plans, security
  exposure, accessibility notes, or architecture rules

Do not require broad repository reads when a context packet, generated index,
fixture, or deterministic script can provide enough evidence.

## Required First Move

Each agent must define its first move. The first move should usually be one of:

- verify required inputs are present
- identify missing evidence and block
- run or request a deterministic metric/check
- read the current context packet or source-of-truth artifact
- classify whether the agent is the right reviewer

The first move must prevent the agent from giving confident advice without the
minimum evidence for its scope.

## Rubric Rules

Every agent must define 3 to 7 scored dimensions. Dimensions must be observable
from evidence and must map to the agent's responsibility.

For harness review agents under `.agentic/01.harness/agents/`, scored
dimensions live in machine-readable rubric files under
`.agentic/01.harness/agents/rubrics/`. Keep the Markdown summary concise and
point to the rubric as the scoring source of truth.

Scores use this scale:

- `5`: excellent, no material concern
- `4`: good, minor improvement possible
- `3`: acceptable with non-blocking concerns
- `2`: weak, rework recommended
- `1`: poor, likely blocker
- `0`: absent, unsafe, or unreviewable

Each dimension must name what `5`, `3`, and `0` mean when that meaning is not
obvious from the dimension label.

## Decision Rules

The scorecard decision must be one of:

- `pass`
- `pass_with_notes`
- `block`
- `delegate`
- `not_applicable`

Use `pass` only when all required dimensions score at least `4`, no critical
finding exists, and the required output is complete.

Use `pass_with_notes` when all required dimensions score at least `3`, no
critical finding exists, and remaining issues are explicitly non-blocking.

Use `block` when any critical finding exists or any required dimension scores
below `3`.

Use `delegate` when another agent must review a risk before a responsible
decision can be made.

Use `not_applicable` when the invocation evidence shows the agent should not
review the task.

Do not average scores to hide a critical finding. Overall score is useful for
trend reporting, but blockers are boolean.

## Output Shape

Agent output must include:

- agent ID and name
- task or artifact under review
- review mode
- evidence reviewed
- findings grouped by severity
- rubric scores
- decision
- required follow-up
- delegation requests, if any
- confidence and evidence gaps

Use a structured scorecard when the output may be consumed by another workflow,
script, gate, or future CFO trend review.

## Delegation

Agents should delegate when a finding crosses ownership boundaries:

- token trend or repeated cost concern: CFO Token Efficiency
- prompt drift, contradiction, or verbosity: Senior Prompt Engineer
- backend architecture gap: Senior Back-End Architect
- deployment, runtime, reliability, or cloud cost risk: Senior SRE Engineer
- security, secrets, auth, or compliance risk: SecOps Engineer
- human-facing chat, CLI, repo, web, or accessibility concern: UX/UI Engineer

Delegation requests must state the blocking question, evidence already
reviewed, and the decision needed from the receiving agent.

## Stop Conditions

An agent must stop when:

- required evidence is absent
- governance coverage is missing
- the requested action exceeds the agent's authority
- the task needs a different primary agent
- a deterministic script or gate is required but unavailable
- the review would require external-current facts that have not been verified

Stopping is a successful outcome when it prevents drift, unsafe action, or
unreviewable approval.

## Quality Bar

An agent contract is high quality when a future agent can:

- know when to use it
- know what context to gather
- know what it may and may not do
- score work without inventing a rubric
- produce a predictable report
- delegate cross-lane risks
- block unsafe or under-evidenced work without apology

If a requirement cannot be observed or tested, move it to guidance or an
example instead of making it a pass/fail rule.
