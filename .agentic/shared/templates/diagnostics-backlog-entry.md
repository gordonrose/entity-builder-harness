<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.template.diagnostics-backlog-entry
version: 1
status: active
created_on: "2026-11-01"
updated_on: "2026-11-04"
layer: 06.shared
domain: diagnostics
disciplines: [architecture, security, sre, agentic]
kind: template
purpose: Preserve the six required sections for each agreed future diagnostic task.
portability: {class: source-only, targets: []}
used_by:
- id: shared.workflow.maintain-diagnostics-backlog
  path: .agentic/shared/workflows/maintain-diagnostics-backlog.md
-->
# Diagnostics backlog entry template

Use the [maintenance workflow](../workflows/maintain-diagnostics-backlog.md).
Copy the entry below into the [canonical backlog](../plans/implementation/diagnostics-backlog.md),
replace placeholders from evidence and retain all six labelled sections.

## DIAG-<next number> — <short title>

Status: open

### 1. ID

DIAG-<next unused number; stable and never reused>

### 2. Date/time raised

<Actual ISO 8601 timestamp with explicit UTC offset and timezone; immutable.>

### 3. Summary

<The diagnostic gap and intended outcome in one or two sentences.>

### 4. Background

<Plain prose: how the issue was discovered, with whom, and during which review
or conversation. Explain the observed behavior, relevant decisions and safe
evidence references. State unknown discovery timing or facts honestly.>

### 5. User stories

- As <affected user/operator/maintainer>, I need <what changes> in <repo part
  and specific files>, so that <why it matters>. Owner: <layer/package>.
  Affected producers/wrappers/consumers: <paths or justified non-applicability>.
  Compatibility and privacy: <requirements or supported non-applicability>.

### 6. Acceptance criteria

- [ ] Code: <observable implementation/consumer outcome and proving check, or
  explicit not-applicable reason>.
- [ ] Harness: <observable workflow/rule/check change addressing the omission,
  and proving review/check, or explicit not-applicable reason>.
- [ ] Regression fixtures: <counterexample and assertion that catch recurrence,
  plus proving check, or explicit not-applicable reason>.

Evidence and update history: <Dated notes with offset/timezone, decisions, scope
or status changes and safe evidence links. Label unexecuted proof as planned.>
