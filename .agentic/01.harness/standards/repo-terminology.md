<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.standard.repo-terminology
version: 1
status: active
layer: 01.harness
domain: governance
disciplines:
- agentic
kind: standard
purpose: Define canonical repo terminology and prevent duplicate definitions across harness artifacts.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
- id: harness.standards.agentic-artifact-standards
  path: .agentic/01.harness/standards/agentic-artifact-standards.md
-->

# Repo Terminology Standard

## Purpose

This standard is the canonical glossary for repo process, harness, and
RAG/rulebook terminology.

Use it when a term needs a stable definition across layers, workflows,
standards, schemas, generated indexes, or assistant-facing instructions.

## Source Of Truth Rule

Define each repo-wide term in this file once.

Other artifacts may explain how a term is used in their local context, but they
must not create competing glossary entries or redefine the term. If local prose
conflicts with this standard, this standard wins.

When adding or changing a repo-wide term:

- update this standard first
- update affected usage docs to point here or align with this wording
- do not create a second glossary, duplicate definition table, or local
  synonym list that changes meaning
- treat aliases as references to canonical terms, not as new terms

Existing explanatory docs may keep local walkthrough prose, but when those docs
are materially edited, replace duplicate definitions with references to this
standard.

## Canonical Terms

| Term | Definition |
| --- | --- |
| agent | A bounded review or execution role with defined responsibility, inputs, outputs, authority, evidence needs, handoff rules, and stop conditions. |
| artifact | A committed file or source object that has a stable purpose in the repo, such as a workflow, standard, checklist, schema, script, rulebook file, ADR, template, or guide. |
| chat | The lifecycle container for one assistant/user work thread, including the chat branch, chat-owned worktree, session log, commit checkpoints, metrics, transcript metadata, and cleanup state. A chat is not a durable layer, mode, workflow, or corpus classification. |
| checklist | Observable milestone, readiness, completion, or safety criteria. A checklist may block completion, but it should not carry the full ordered procedure unless order is the point. |
| command | A small named shortcut for a governed user-facing action. Commands delegate to governed scripts or print prompts for agent judgment; they do not own independent policy. |
| concern | A cross-cutting rulebook topic that applies across layers or path families, such as security, persistence, generated code, dependency direction, or CI quality. |
| corpus | A separately owned, indexed, cited, and governed knowledge package for RAG/rulebook retrieval. Top-level corpus IDs align with the numbered layer system. |
| evaluation | A fixture or suite that protects behavior from regression by naming inputs, expected outcomes, banned outcomes, acceptance rules, validators, source references, and update triggers. `eval` is an alias for evaluation. |
| gate | A blocking deterministic check or explicit review decision point. A failed gate stops progress until the governed recovery path or user-approved exception is followed. |
| guide | A human-readable explanation of a mental model, field family, workflow use, or artifact interpretation. A guide teaches usage; binding rules belong in standards, workflows, schemas, gates, or checklists. |
| migration-plan | A plan for moving, renaming, retiring, removing, or changing source-of-truth locations for committed artifacts. It names source paths, target paths, stable IDs, reference updates, validation checks, and rollback or recovery approach. |
| plan | An ordered intent for future work, including assumptions, sequence, risks, validation, and open decisions. A plan is not execution approval unless a governing workflow explicitly says it is. |
| policy | Versioned selectable behavior, precedence, configuration, or decision logic that tools or agents execute or consult. Policies should remain inspectable and should not be hidden only in code. |
| profile | A named reusable configuration, lens, target, audience, retrieval hint, or environment-shaped setting that constrains behavior for a specific use. A profile must name its owner and must not override standards or policies silently. |
| prompt | One user request or assistant-facing input interpreted for the current turn. Prompt-level routing may select a layer, mode, workflow, or corpus for that turn, but it does not classify the whole chat permanently. |
| rule | A named atomic requirement, prohibition, or expectation inside a rulebook artifact. Rules should be addressable by stable IDs and traceable to source references. |
| rule-pack | A task-oriented rulebook bundle that maps a task type to required rulesets, required checks, agent steps, prohibitions, success criteria, and source references. |
| ruleset | A collection of related rules for one layer or concern. Layer rulesets own placement boundaries; concern rulesets own cross-cutting requirements. |
| schema | A machine-readable contract for fields, packets, manifests, indexes, configs, or other structured data. Schemas define required fields, allowed values, validation rules, and concise field explanations. |
| skill | A reusable model procedure that loads only when relevant. Skills define trigger conditions, required context, steps, and expected outputs; repo-wide rules belong in standards or workflows. |
| standard | Durable quality, ownership, terminology, or judgment rules. Standards define stable expectations; workflows say when to apply them and scripts or gates enforce what can be checked. |
| state | Durable factual information used to resume, reconcile, audit, or validate work. State records facts; it must not become the only home for durable process rules. |
| template | A reusable document, output, fixture, or file shape with placeholders. Templates encode structure and examples, not independent policy unless a standard or workflow explicitly gives them that role. |
| workflow | An ordered governed process with use conditions, required inputs, gates, stop conditions, recovery paths, and outputs. Workflows own procedure, not every quality rule. |

## Term Relationships

Use these relationships to avoid duplicate or conflicting definitions:

- `chat` contains session lifecycle state; `prompt` is interpreted per turn.
- `workflow` owns ordered procedure; `checklist` owns observable readiness or
  completion criteria.
- `standard` owns durable expectations; `policy` owns selectable behavior or
  precedence.
- `schema` owns machine-readable shape; `template` owns reusable document or
  output shape.
- `rule` is atomic; `ruleset` groups related rules; `rule-pack` maps a task to
  required rulesets, checks, and success criteria.
- `guide` teaches; `standard`, `workflow`, `schema`, `gate`, and `checklist`
  govern.
- `command` is the shortcut surface; `script` performs deterministic action or
  validation behind that surface.
- `plan` describes intended work; `migration-plan` is the artifact-movement
  form of plan with reference and rollback obligations.
- `state` records facts; durable rules belong in committed governance
  artifacts.

## Ownership Hints

These paths currently own the detailed rules for related terms:

| Term family | Owning source |
| --- | --- |
| artifact placement | `.agentic/01.harness/standards/agentic-artifact-standards.md` |
| artifact metadata fields | `.agentic/01.harness/artifact-metadata/standard.md` |
| controlled metadata values | `.agentic/01.harness/artifact-metadata/taxonomy.yml` |
| chat lifecycle | `.agentic/00.chat/README.md` |
| command shortcuts | `.agentic/00.chat/commands/README.md` |
| agent contracts | `.agentic/01.harness/standards/agent-contracts.md` |
| evaluation fixtures | `.agentic/01.harness/standards/evaluation-fixtures.md` |
| corpus packages | `.agentic/02.rag-rulebook/standards/domain-corpus-package.md` |
| context packets | `.agentic/02.rag-rulebook/guides/context-packet.md` |

If a definition appears to belong in one of those files instead, keep the
canonical term meaning here and put only local requirements or usage guidance
there.
