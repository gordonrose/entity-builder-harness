<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.standard.require-readable-readmes
version: 1
status: active
created_on: "2026-11-01"
updated_on: "2026-11-04"
layer: 06.shared
domain: documentation
disciplines: [agentic, architecture]
kind: standard
purpose: Require source-backed README explanations a reader can follow without prior knowledge of the implementation.
portability: {class: source-only, targets: []}
used_by:
- id: shared.standard.require-change-completion
  path: .agentic/shared/standards/require-change-completion.md
- id: shared.skill.write-readme
  path: .agentic/shared/skills/write-readme.md
-->
# Readable READMEs

## Scope and ownership

Apply when creating or changing a repository README. Match the depth to the
requested change and intended reader. A small correction does not require a
whole-folder rewrite; name any deliberately unfinished coverage.

This standard owns writing quality requirements. The
[skill](../skills/write-readme.md) owns the authoring procedure and the
[module template](../templates/module-readme.md) supplies an adaptable shape.
Domain requirements remain in their owning harness artifacts, not copied here
or invented by a README. Follow existing placement and change-completion rules.

## Writing requirements

1. **Begin with a concrete need.** Explain the problem the program must solve,
   why this folder exists and what it does not do. Introduce an example before
   abstract labels such as configuration, settings or adapters.
2. **Explain unfamiliar terms before relying on them.** Define terms in the
   reader's context. Explain relevant notation, including imports, types,
   spread syntax and list positions, when it affects understanding. Do not
   replace one unexplained term with several others.
3. **Cover the agreed inventory.** For a module guide, explain the folder and
   each direct file, distinguishing subfolders. Explain each public export in
   scope: what it is, why it exists and when/how other code should use it.
   Distinguish items implemented in an entry-point file from names it merely
   makes available from another file; link an existing explanation rather than
   repeat it. List deliberate omissions, not implied complete coverage.
4. **State who does each job.** Identify who supplies information, chooses
   requirements, performs checks, creates reports and handles results. Name
   actual functions and paths where useful; define caller as the code making
   the call. Explain a meaningful division of responsibility, not just file names.
5. **Separate use from implementation.** Label example code outside the module
   and the functions inside it. Explain what an import accesses, where each
   function is implemented, what is passed in and where its result returns.
   Label invented examples; do not imply an illustrative file already exists.
6. **Show the work, not just the call.** After the file overview, use a small
   worked example, then a richer example when multiple inputs, independent
   failures or several steps matter. Explain intermediate objects, reads,
   choices and conversions. Show actual outputs; label a deliberate projection
   or excerpt as such. Include success and relevant failures, without repeating
   every possible test case or introducing unrelated features.
7. **Illustrate important relationships.** Use a small diagram when it makes
   ownership, calls or information movement clearer. Label boundaries, inputs
   and outputs. Distinguish a set of available tools from a sequence that always
   runs. Use tables for comparisons, not dense prose squeezed into wide cells.
8. **Explain behaviour and limits.** Explain method lifecycle, missing versus
   empty values, defaults, bounds, omitted reports and privacy where relevant.
   Distinguish allowed report wording from evidence of what happened, and
   checks on programmer-written code from checks when the program runs.
   Explain what a successful result does not establish. Do not invent the
   rationale for an arbitrary constant or claim raw errors are safe to log.
9. **Make examples reusable, not exclusive.** Mark current consumers as examples
   rather than the only permitted users. Explain how future consumers can reuse
   the tools and what they must provide or call themselves. Avoid automatic
   adoption or enforcement claims unsupported by implementation.
10. **Separate facts, requirements and future work.** Link to the actual owning
    requirements and executable checks. Explain their limits. Mark proposed or
    missing policy/control as **not yet implemented**, with the relevant existing
    backlog task where one exists. Flag a legacy rule location honestly; do not
    migrate it or copy its authority into the README without authorization.

Keep explanations in the README rather than adding a comment to every source
declaration. Use concrete language, introduce one idea at a time and remove
repetition. Length is justified by what the reader needs to follow, not by
filling a fixed number of headings. Adapt module-specific sections for command,
package-root or other README purposes; do not force irrelevant export guides.

## Review and proportionate proof

Review the draft against the source and its requested inventory. Ask whether a
reader can trace a supplied value through the actual calls to the returned
result, and tell what each participant does and does not establish. Check that
file names, examples, limits, error shapes and current/future labels agree.

Check relative links, anchors and export coverage where applicable. Execute or
type-check bounded illustrative code when needed to establish claimed results;
use invented non-sensitive inputs. State limits on unexecuted examples. Do not
require runtime/container suites or source-review hash refreshes solely because
prose changed. If code changes, its owning workflow determines the proof.

Valid links, complete headings and skill-format validation do not prove that
the explanation is understandable. Record a reading/source review as well as
mechanical checks, using the existing session/task record rather than a new ledger.
