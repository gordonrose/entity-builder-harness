# Agentic Artifact Standards

## Purpose

Use this standard when deciding which harness artifact should own a new rule,
procedure, capability, example, automation, or enforcement point.

The goal is to keep always-loaded instructions small while giving repeatable
work a clear home.

## Core Rule

Put each instruction in the narrowest artifact that owns it.

If the behavior can be checked deterministically, prefer a script or gate over
prose. If the behavior is reusable but not always needed, prefer a skill,
template, example, eval, or adapter over always-loaded instructions.

Keep requirements lean. Every required field or section must prevent a real
failure mode; anything merely helpful belongs in guidance, a template, or an
example.

## Artifact Map

| Need | Artifact |
|---|---|
| startup routing and source-of-truth pointers | `AGENTS.md` |
| vendor compatibility shim | `CLAUDE.md`, `.codex/`, `.cursor/`, `.claude/`, or adapter file |
| layer/mode/workflow classification | `.agentic/routing-policy.yaml` |
| repeated ordered process | workflow |
| durable quality expectation | standard |
| milestone completion or safety criteria | checklist |
| deterministic action or validation | script |
| blocking safety or completion check | gate |
| reusable model procedure | skill |
| lifecycle automation | hook |
| behavior regression protection | eval |
| reusable output or document shape | template |
| canonical few-shot sample | example |
| durable session state | session log |
| durable architecture decision | ADR |
| bounded review or execution role | agent |
| coordination across multiple agents or workflows | orchestrator |

## Always-Loaded Files

Keep always-loaded files short, durable, and low-variance.

- `AGENTS.md` is a router. It may name startup rules, source-of-truth files,
  layer ownership, and safety invariants.
- `CLAUDE.md` is a vendor adapter. It should point to `AGENTS.md` and avoid
  independent rules unless Claude-specific compatibility requires them.
- Vendor rule files should not duplicate repo rules. Use them only when the
  vendor format adds necessary metadata, scoping, or enforcement.

## Cross-Artifact Authoring Rules

Every artifact should have one clear owner, one clear audience, and one clear
reason to exist.

- Define artifacts by stable purpose, not by a current vendor implementation.
- Put a rule in one place. Standards explain intent, templates provide shape,
  scripts validate mechanics, and workflows say when to consult them.
- Prefer the first useful artifact over a complete artifact family. Add
  templates, hooks, evals, agents, and orchestrators only after repeated need or
  a clear safety reason.
- Reference existing files only when they exist or when creating them is part of
  the same approved change.
- Record exceptions in the session log. Use an ADR only when the exception is a
  durable architecture or process decision.
- Add a review date when guidance depends on external vendor behavior.

## Conditional Guidance

Use conditional artifacts when guidance is only relevant for some tasks.

- Use workflows for ordered processes with decisions, gates, and stop
  conditions.
- Use standards for stable quality rules and artifact placement rules.
- Use skills for repeatable model procedures that should load only when invoked
  or matched.
- Use examples for output shape, few-shot behavior, or tricky interpretation.
- Use templates for reusable document, log, plan, ADR, or report structures.

## Executable Enforcement

Use executable artifacts when correctness can be checked by code.

- Use scripts for deterministic actions or validations.
- Use gates when a script result must block progress.
- Use hooks when an action must run at a lifecycle event.
- Use evals when agent behavior, classification, routing, or output shape needs
  regression protection.

Scripts that delete, move, commit, push, clean, or overwrite anything must
support dry-run mode first.

## Per-Artifact Requirements

### `AGENTS.md`

- Keep it as a short router and safety contract.
- Include startup source-of-truth pointers and durable invariants only.
- Move layer-specific, procedural, or domain rules into workflows, standards,
  gates, skills, or templates.

### Vendor Adapter

- Point to canonical repo instructions instead of copying them.
- Add vendor-specific metadata, scoping, or compatibility only where the vendor
  format requires it.
- Do not let vendor memory become the source of truth for repo behavior.

### Routing Policy

- Classify by layer, mode, and workflow without embedding workflow procedure.
- Add classifier fixtures when a routing miss surprises the user or agent.
- Prefer explicit examples over broad terms that would steal unrelated product
  or shared-process tasks.

### Workflow

- State when to use it, required inputs, gates, stop conditions, and output.
- Keep ordered process in the workflow; put quality rules in standards and
  deterministic checks in scripts or gates.
- Do not duplicate artifact requirements already owned by this standard.
- Include an `agentic-artifact` metadata header when created or backfilled.

### Standard

- Describe durable quality expectations and ownership rules.
- Separate requirements from guidance.
- Include source review notes when external best-practice claims affect the
  rule.
- Include an `agentic-artifact` metadata header when created or backfilled.

### Checklist

- Use for milestone, readiness, completion, or safety criteria.
- Make each item observable enough that a reviewer can answer it.
- Avoid ordered procedure unless the order itself matters; use a workflow for
  ordered procedure.

### Script

- Perform one deterministic action or validation.
- Exit non-zero on failure and print concise, actionable output.
- Support dry-run mode before any delete, move, commit, push, clean, overwrite,
  or other destructive behavior.
- Include an `agentic-script` metadata header as defined in
  `.agentic/harness/standards/artifact-metadata-headers.md`.

### Gate

- Wrap a deterministic check whose failure must block progress.
- Define the blocked response or escalation path.
- Keep judgment-heavy review out of gates unless the gate delegates to a human
  decision.

### Skill

- Capture a reusable model procedure that should load only when relevant.
- State trigger conditions, required context, steps, and outputs.
- Keep repo-wide rules in standards or workflows, not inside a skill.

### Hook

- Use only when lifecycle timing matters.
- Keep the trigger, scope, and failure behavior explicit.
- Prefer a script called by the hook for deterministic logic.

### Eval

- Protect behavior that can regress, such as routing, output shape,
  instruction-following, or agent/tool behavior.
- Include fixtures or examples with expected outcomes.
- Keep subjective evaluation criteria explicit and reviewable.

### Template

- Encode repeated document or output shape.
- Avoid embedding rules that are already owned by standards.
- Keep placeholders obvious and minimal.

### Example

- Show canonical interpretation, output shape, or few-shot behavior.
- Keep examples small and named by the behavior they protect.
- Promote repeated examples into eval fixtures when regression protection is
  needed.

### Session Log

- Record current session facts, decisions, issues, and activity.
- Do not use session logs as the only home for durable process rules.
- Keep metadata aligned with resolved layer, mode, and workflow.

### ADR

- Use for durable architecture or process decisions with meaningful tradeoffs.
- Include context, decision, consequences, and status.
- Do not create an ADR for routine implementation notes.

## Memory and State

Do not hide project process in vendor memory.

- Session facts belong in `commitLogs/<session>/README.md`.
- Durable shared process belongs in committed harness artifacts.
- Durable architecture decisions belong in ADRs.
- Personal preferences may live in user-level memory or settings, but repo
  behavior must be represented in committed files.

## Agents

Create an agent only when a bounded role improves the work more than a workflow
or skill would.

Agents should define:

- responsibility
- inputs
- outputs
- allowed scope
- review posture
- handoff expectations

Do not create an agent for a single deterministic check, a checklist, or a
simple reusable prompt.

## Orchestrators

Create an orchestrator only when multiple agents or workflows must be
coordinated.

Orchestrators should define:

- participating roles or workflows
- sequencing
- shared state
- handoff expectations
- stop conditions

Do not create an orchestrator for a single workflow with substeps.

## Source-Backed Notes

Source-reviewed guidance should be recorded at the level of stable principles,
not copied vendor procedure. Current stable principles:

- keep always-loaded instructions short and high-signal
- move conditional or task-specific guidance into scoped artifacts
- use skills for reusable procedures that should load on demand
- use scripts, gates, and hooks for deterministic enforcement
- use evals or fixtures where routing, output shape, or agent behavior can
  regress
- treat vendor files as adapters rather than duplicate rule stores

Source review note: OpenAI Codex manual, Anthropic Claude Code docs, Cursor
rules docs, and Mistral docs were reviewed from prior chat context on
2026-06-16. Refresh vendor-specific claims before adding new vendor-derived
requirements.

## Anti-Patterns

- Putting domain procedure in `AGENTS.md`.
- Duplicating the same rule across root instructions, workflows, skills, and
  vendor adapters.
- Describing deterministic checks in prose when a script or gate can enforce
  them.
- Creating a workflow when a script plus checklist is enough.
- Creating an agent when a skill is enough.
- Creating templates, hooks, evals, agents, or orchestrators before repeated
  need or a clear safety reason exists.
- Treating OpenAI, Anthropic, Cursor, Mistral, or another vendor's current file
  layout as the universal harness model.
- Making judgment-heavy artifact choices look mechanically deterministic.
- Loading examples, templates, or long standards on every task when they can be
  referenced conditionally.

## Validation Expectations

Add deterministic validation when a rule can be checked without judgment.

- Validate classifier behavior with fixtures.
- Validate required sections or metadata when artifact structure becomes
  stable enough to enforce.
- Validate destructive scripts for dry-run support.
- Validate references to scripts, gates, workflows, templates, and examples
  when broken references would block future work.

Do not add validation for subjective quality until the expected behavior can be
expressed as fixtures, examples, or clear pass/fail checks.
