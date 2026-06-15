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

## Anti-Patterns

- Putting domain procedure in `AGENTS.md`.
- Duplicating the same rule across root instructions, workflows, skills, and
  vendor adapters.
- Describing deterministic checks in prose when a script or gate can enforce
  them.
- Creating a workflow when a script plus checklist is enough.
- Creating an agent when a skill is enough.
- Loading examples, templates, or long standards on every task when they can be
  referenced conditionally.
